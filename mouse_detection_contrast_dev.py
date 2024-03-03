import glob, time, json, os, datetime, tqdm
from numpy import random, save, array, dstack, zeros
import numpy as np
from pyfirmata import ArduinoMega, util, INPUT, SERVO, OUTPUT
from time import sleep
import pandas as pd
from simple_pyspin import Camera
from matplotlib import pyplot as plt
from params import Params

from skvideo import setFFmpegPath
setFFmpegPath(r'C:\ffmpeg-6.1-essentials_build\ffmpeg-6.1-essentials_build\bin')
from skvideo.io import vwrite

#set up image and gameplay resources===============================
import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()
# music = pyglet.resource.media('beep-07a.wav')
from playsound import playsound
BEEP_PATH = './models/beep-07a.mp3'
ERROR_BEEP_PATH = './models/beep-03.mp3'

task_monitor = pyglet.window.Window(216, 192)
task_monitor.set_location(932,100)
task_monitor.set_vsync(False)
pyglet.gl.glClearColor(0.5,0.5,0.5,1)

task_monitor_plot = pyglet.window.Window(600, 600)
task_monitor_plot.set_location(1148,100)
task_monitor_plot.set_vsync(False)
pyglet.gl.glClearColor(0.5,0.5,0.5,1)

game_window = pyglet.window.Window(2160, 1920)
game_window.set_vsync(False)
game_window.set_location(-2160,0)

pyglet.gl.glClearColor(0.5,0.5,0.5,1) # Note that these are values 0.0 - 1.0 and not (0-255).
grating_image = pyglet.resource.image('grating.jpg')
grating_image.anchor_x = grating_image.width // 2 #center image
blank_image = pyglet.resource.image('grating_0.jpg')
grating_image.anchor_x = grating_image.width // 2 #center image
grating_images = {'100': pyglet.resource.image('grating_100.jpg'),
                  '80': pyglet.resource.image('grating_80.jpg'),
                  '64': pyglet.resource.image('grating_64.jpg'),
                  '32': pyglet.resource.image('grating_32.jpg'),
                  '16': pyglet.resource.image('grating_16.jpg'),
                  '8' : pyglet.resource.image('grating_8.jpg'),
                  '4' : pyglet.resource.image('grating_4.jpg'),
                  '2' : pyglet.resource.image('grating_4.jpg'),}
sprite = pyglet.sprite.Sprite(grating_image, x = 600, y = 800)
sprite.scale = 0.8

sprite2 = pyglet.sprite.Sprite(grating_image, x = 60, y = 80)
sprite2.scale = 0.04


class Timer:
        def __init__(self):
            self.reset()

        def reset(self):
            self.time = 0
            self.running = False
        
        def start(self):
            self.running=True

        def update(self, dt):
            if self.running:
                self.time += dt
timer = Timer()
timer.start()
# on draw events. ==========================
# this is the main game loop
@game_window.event      
def on_draw():   
    game_window.clear()     # clear the window

    if not params.new_trial_setup: #check to see if we need to update params for a new trial. this only happens if the previous trial ended, and the animal hasn't licked for some amount of time that is currently hardcoded below. if not, execute the current trial. 
        if params.stim_on:    params.sprite.draw()
        if len(params.stim_delay) > 0:
            if timer.time - params.lick_timestamps[-1] > params.iti + 0.5:
                setup_trial()
            else:
                pass #wait until animal hasn't licked for hardcoded number of seconds above
        else: setup_trial()
    else: #we're ready for a new trial
        if timer.time > params.trial_start_time[-1]:#if enough time has passed since the end of the last trial, start a trial
            if not params.in_trial:
                # if lick has happend since water delivered to prevent confusion of leftover reward with tht is going on
                start_trial()
            else: #we're in a trial, but before the stim has come on. start checking for false alarm licks
                if check_lick_response(params.trial_start_time[-1]):
                    if not params.stim_on:
                        params.stim_on_time.append(-1);params.stim_off_time.append(-1)
                        params.stim_rewarded.append(False);params.stim_reward_amount.append(-1)
                        params.reward_time.append(-1)
                        params.falsealarm.append(True);params.lapse.append(False)
                        playsound(ERROR_BEEP_PATH)
                        end_trial()
                        # params.spout_postion = 'low'
                        if not params.SPOUT_LOCK:
                            task_io.move_spout(45)
                            task_io.move_spout(90)
                            # time.sleep(2.0)

                        #this is a code block for a timeout if there have been a bunch of FAs
                            #if params.FA_count > params.FA_max_count:
                            #     params.FA_count = 0
                            #     task_io.move_spout(270); params.spout_positions.append(270);params.spout_timestamps.append(timer.time)
                            #     time.sleep(11.)
                            #     task_io.move_spout(90); params.spout_positions.append(90);params.spout_timestamps.append(timer.time)

                #we've made it past the amount of time from the start of the trial to the start of the stim, so start showing the stimulus
                if timer.time > params.trial_start_time[-1] + params.stim_delay[-1]:
                    if not params.stim_on: 
                        print('stim on at '+str(timer.time))
                        params.stim_on=True
                        params.stim_on_time.append(timer.time)

                    if params.SHAPING:
                        if timer.time > params.trial_start_time[-1] + params.stim_delay[-1] + 3.5:
                            if not params.this_trial_has_been_rewarded:
                                params.shaping_amount = int(params.shaping_wait_time * 10 * 0.75 )#SCALE FOR LONGER WAIT TIMES
                                if params.shaping_amount > 26: params.shaping_amount = 25
                                task_io.s.rotate(params.shaping_amount,'dispense')
                                params.stim_rewarded.append(True);params.falsealarm.append(False);params.lapse.append(False)
                                params.stim_reward_amount.append(params.shaping_amount)
                                params.reward_time.append(timer.time)
                                params.this_trial_has_been_rewarded = True

                            else:
                                if timer.time > params.reward_time[-1] + params.stim_delay[-1] + 3.4:
                                    params.stim_off_time.append(timer.time)
                                    end_trial()
                    else:
                       if check_lick_response(params.stim_on_time[-1]):
                            print('lick detected after stim on')
                            if params.stim_contrast[-1] != 0:
                                reward = 100 #int(10 + 5 * params.stim_delay[-1])
                                task_io.s.rotate(reward,'dispense')
                                print('Reward!')
                                params.stim_rewarded.append(True);params.stim_reward_amount.append(reward)
                                params.reward_time.append(timer.time)
                                params.stim_off_time.append(timer.time)
                                params.falsealarm.append(False);params.lapse.append(False)
                                end_trial()
                            else:
                                print('Contrast was zero and this if statement worked')
                                params.stim_rewarded.append(False);params.stim_reward_amount.append(-1)
                                params.reward_time.append(-1)
                                params.stim_off_time.append(timer.time)
                                params.falsealarm.append(True);params.lapse.append(False)
                                end_trial()

                    
        if params.stim_on:
            params.sprite.draw()
            if timer.time > params.trial_start_time[-1] + params.stim_delay[-1] + params.stim_duration:
                params.stim_off_time.append(timer.time)
                if params.SHAPING:
                    if params.this_trial_has_been_rewarded: 
                        pass
                    else: 
                        params.stim_rewarded.append(False);params.falsealarm.append(False);params.lapse.append(True)
                        params.stim_reward_amount.append(-1)
                        params.reward_time.append(-1)

                else:
                    params.stim_rewarded.append(False);params.falsealarm.append(False);params.lapse.append(True)
                    params.stim_reward_amount.append(-1)
                    params.reward_time.append(-1)
                end_trial()

@task_monitor.event      
def on_draw():   
    task_monitor.clear()     # clear the window       
    if params.stim_on: sprite2.draw() #draw if logic from game_window on_draw() says we should

#
@task_monitor_plot.event
def on_draw():
    task_monitor_plot.clear()
    params.sprite_progress.scale = 0.8
    params.sprite_progress.draw()

#functions used by the @game_window.event on_draw() to execute the task==================
def setup_trial():
    params.trial_start_time.append(timer.time)

    if random.random() > 0.5: params.answer = 'left'
    else:                     params.answer = 'right'

    if params.answer == 'left': 
        params.sprite.rotation = 0
        params.stim_orientation.append(0)
        #TODO: need to set the x and y along with ori because origin is not in the center
    else:                       
        params.sprite.rotation = 0
        params.stim_orientation.append(90)

    params.stim_spatial_frequency.append(0.08)

    # params.trial_start_time.append(timer.time)

    if params.SHAPING:
        params.stim_delay.append(params.shaping_wait_time) 
    else:
        #TODO: implement distribution here
        # as it is, random flat distro to 5 seconds   
        # if len(params.stim_delay) > 0:
        #     adjuster = random.random() * 0.5 * params.stim_rewarded[-1] 
        #     next_delay = params.stim_delay[-1] +  adjuster
        #     if next_delay > 5.0: random.random() * 5. + 1
        #     if next_delay < 1.0: 1.1
        #     params.stim_delay.append(next_delay) 
        # else: params.stim_delay.append(1.5) 
        params.stim_delay.append(random.random() * params.WAIT_TIME_WINDOW+1)
    print('required wait with no licking is '+str(params.stim_delay[-1])+' and should come on at '+str(params.trial_start_time[-1] + params.stim_delay[-1]))

    contrasts = list(grating_images.keys())
    for _ in range(1):
        contrasts.append('0') # increase the liklihood of a 0 contrast
    contrast = contrasts[random.randint(len(contrasts))]
    if contrast == '0': 
        params.catch=True
        params.sprite = pyglet.sprite.Sprite(blank_image, x = 1000, y = 450)
        params.sprite.scale = 4.8
    else: 
        params.catch=False
        #TODO: set sprite image manually based on contrast
        grating_image = grating_images[contrast]
        grating_image.anchor_x = grating_image.width // 2 #center image
        params.sprite = pyglet.sprite.Sprite(grating_image, x = 1000, y = 450)
        params.sprite.scale = 4.8
    params.stim_contrast.append(int(contrast))

    
    # params.stim_on_time.append(params.trial_start_time[-1] + params.stim_delay[-1])
    
    params.trial_AUTOREWARDED.append(params.AUTOREWARD)
    params.trial_ONSET_REWARD.append(params.ONSET_REWARD)
    params.shaping.append(params.SHAPING)

    params.this_trial_has_been_rewarded = False
    params.new_trial_setup=True
    params.iti = random.uniform(3,15)
    params.stim_on=False

def start_trial():
    print('start of trial at '+str(timer.time))
    trial_start = timer.time
    params.in_trial = True
    try:
        if params.PLAY_TRIAL_SOUND:
            playsound(BEEP_PATH)
        if params.spout_postion == 'low':
            if not params.SPOUT_LOCK:
                task_io.move_spout(90);params.spout_positions.append(90);params.spout_timestamps.append(timer.time)
                # time.sleep(0.6)
        # music.play()

        # while data:  
        #     stream.write(data)  
        #     data = BEEP.readframes(chunk)  
    except: print('failed to play trial start audio cue at '+str(timer.time))

def end_trial():
    print('end of trial at '+str(timer.time))
    params.trialendtime.append(timer.time)
    #log trial info
    # print(timer.time)
    # print(params.last_end_time + params.iti)
    # print(params.answer + '   '+answered)
    params.last_end_time = timer.time
    # params.stim_off_time.append(params.last_end_time) #store trial end in params
    

    reaction_time= -1 #params.last_end_time - params.stim_on_time[-1]
    params.stim_reaction_time.append(reaction_time)  #store reaction time in params
    # check_reaction_time(reaction_time)

        
    params.save_params() #record the last trial on disk
    params.update_session_performance()
    # params.stim_on=False #update boolean so we have the option to try again
    params.in_trial=False #reset
    params.licked_on_this_trial = False #reset
    params.new_trial_setup = False


    # task_io.move_spout(270)

def check_response():
    lickometer_read = task_io.board.digital[task_io.lick_opto_pin].read()
    if not lickometer_read: # this flips the logic because the lickomter returns False when a lick is happening
        print('lickedlickedlicked')
        params.licked_on_this_trial = True
        return True
    else: return False

#returns True or False
def check_lick_response(reference_time):
    if np.array(params.lick_timestamps).shape[0] > 0:
        if len(np.where(np.array(params.lick_timestamps) > reference_time)[0]) > 0:
            # print('lick recorded at '+str(params.lick_timestamps[-1])+' which is after '+str(reference_time))
            return True
        else:
            return False
    else: return False


@game_window.event 
def on_key_press(symbol, modifiers):

    if symbol == pyglet.window.key.R:
        print('R')
        task_io.move_spout(90); params.spout_positions.append(90);params.spout_timestamps.append(timer.time) #this is up and lickable

    if symbol == pyglet.window.key.T:
        print('T')
        task_io.move_spout(270); params.spout_positions.append(270);params.spout_timestamps.append.append.append.append(timer.time) #this is down and unlickable


    if symbol == pyglet.window.key.E:
        print('e: retract')
        task_io.s.rotate(20,'retract')
    if symbol == pyglet.window.key.D:
        print('d: dispense')
        task_io.s.rotate(20,'dispense')

    if symbol == pyglet.window.key.O:
        if params.PLAY_TRIAL_SOUND: 
            params.PLAY_TRIAL_SOUND = False
            print('Switching trial sound off')
        else: 
            params.PLAY_TRIAL_SOUND = True
            print('Switching trial sound on')

    if symbol == pyglet.window.key.NUM_ADD:
        params.WAIT_TIME_WINDOW += 0.25
        print('window for wait times is '+str(params.WAIT_TIME_WINDOW)+' seconds')
    if symbol == pyglet.window.key.NUM_SUBTRACT:
        params.WAIT_TIME_WINDOW -= 0.25
        print('window for wait times is '+str(params.WAIT_TIME_WINDOW)+' seconds')
        pyglet.app.exit()

def on_key_release(symbol, modifiers):
    if symbol == pyglet.window.key.A:
        params.center_button = False
#====================================================================



#====================================================================
#this class connects to the Arduino used for the task and creates functions to be used read various hardware and write to various other hardware for task control. 
class ArduinoController():
    def __init__(self,board_string,horizontal=0,vertical=1,digital_channels=[53,51,49,47,45,43],food_reward_pin=8):
        self.board =  ArduinoMega(board_string)
        self.horizontal_channel = horizontal
        self.vertical_channel = vertical
        self.digital_channels = digital_channels
        self.food_reward_pin = food_reward_pin
        self.water_reward_pin = 7
        self.lick_opto_pin_low_when_licked = 31
        self.lick_opto_pin_high_when_licked = 35
        self.lick_opto_pin = self.lick_opto_pin_low_when_licked

        #set up reward delivery====================================================================
        # try:
        import sys
        sys.path.append('C:\github\syringe_pump') # https://github.com/dougollerenshaw/syringe_pump
        from stepper import Stepper
        self.s = Stepper(mode='arduino',port='COM4',syringe='3mL',board=self .board)
        # s.enable()
        # except:
        #     print("Error:", sys.exc_info()[0])
        #     print('WARNING: no reward hardware set up')
        REWARD_VOLUME=50#in µL
        REWARD_WINDOW=0.5#in seconds

        self.init()

    def init(self):
        it = util.Iterator(self.board)
        it.start()
        self.board.analog[self.horizontal_channel].enable_reporting()#horizontal
        self.board.analog[self.vertical_channel].enable_reporting()#vertical

        # for channel in self.digital_channels:
        #     self.board.digital[channel].mode=INPUT

        #set up servo motor ouput
        # set up pin D9 as Servo Output
        self.reward_food_pin = self.board.digital[self.food_reward_pin]
        self.reward_food_pin.mode = SERVO
  
        self.board.digital[self.water_reward_pin].mode=OUTPUT
        self.board.digital[43].mode=OUTPUT
        self.board.digital[44].mode=OUTPUT

        self.board.digital[self.lick_opto_pin_low_when_licked].mode=INPUT
        self.board.digital[self.lick_opto_pin_high_when_licked].mode=INPUT
        # self.board.analog[self.].enable_reporting()


    # joystick 
    def start_joystick(self):
        #make an infinite loop
        print('ready to listen to joystick')
        while True:
            pass
            h = self.board.analog[0].read()
            v = self.board.analog[1].read()
            if h == None or v==None :pass
            else:
                if h < 0.4: #went left
                    self.left()
                if h > 0.6: #went right
                    self.right()
                if v < 0.4: #went up
                    self.up()
                if v > 0.6: #went down
                    self.down()


    # reward spout motor
    def move_spout(self,a):
        self.reward_food_pin.write(a)


    #reward delivery motor

    def button_state(self,channel):
        return self.board.digital[channel].read()
        #     print('down')
        # if self.board.digital[channel].read():
        #     print('up')

    def left(self):
        print('left')
    def right(self):
        print('right')
    def up(self):
        print('up')
    def down(self):
        print('down')


#function that the pyglet scheduler calls to constantly monitor for licks independent of what is happening with the task
def read_licks(dt):
    lickometer_read = task_io.board.digital[task_io.lick_opto_pin].read()
    # print(lickometer_read)
    if not lickometer_read and timer.time - params.spout_timestamps[-1] > 0.5 :
        # print(params.not_licking)
        # params.lick_timestamps.append(timer.time)  #save all times. this will mean more than one time per lick
        if params.not_licking:
            # if len(params.stim_on_time)>0:
                # if timer.time > params.stim_on_time[-1]+4.: 
                #     try: music.play()
                #     except: pass
            print('lick at '+str(timer.time))
            params.lick_timestamps.append(timer.time)  #save just the first time a lick is sensed
            params.not_licking = False
            if not params.in_trial:
                if params.lick_timestamps[-1] - params.stim_on_time[-1] > 6.:
                    playsound(ERROR_BEEP_PATH)
                    params.stim_on=False #update boolean so we have the option to try again

    else:
        params.not_licking = True


# start the joystick listening
# try:
board_port = 'COM4'
task_io=ArduinoController(board_port) # use the default pins as set up by the class definite above. if needed, specify different pins when creating this object. 
# task_io.init()
# task_io.move_spout(90)

#set up parameters
params = Params(mouse = 'jlh47')
task_io.move_spout(90);params.spout_positions.append(270);params.spout_timestamps.append(timer.time)

#start the game loop

pyglet.clock.schedule(timer.update) # as fast as possible
# pyglet.clock.schedule_interval(grab_frame,1/30.)
pyglet.clock.schedule_interval(read_licks,1/1000.)
#FYI the on_draw() functions above run at frame rate, so should be 60Hz. might be 30? maybe the card can't keep up with the big monitors?
pyglet.app.run()
    