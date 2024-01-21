import glob, time, json, os, datetime, tqdm
from numpy import random, save, array, dstack, zeros
import numpy as np
from pyfirmata import ArduinoMega, util, INPUT, SERVO, OUTPUT
from time import sleep
import pandas as pd
from simple_pyspin import Camera
from matplotlib import pyplot as plt
# from PIL import Image

from skvideo import setFFmpegPath
setFFmpegPath(r'C:\ffmpeg-6.1-essentials_build\ffmpeg-6.1-essentials_build\bin')
from skvideo.io import vwrite

#set up image and gameplay resources===============================
import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()

camera_window = pyglet.window.Window(532, 768)
camera_window.set_location(400,100)

task_monitor = pyglet.window.Window(216, 192)
task_monitor.set_location(400,100)
task_monitor.set_vsync(False)
pyglet.gl.glClearColor(0.5,0.5,0.5,1)

game_window = pyglet.window.Window(2160, 1920)
game_window.set_vsync(False)
game_window.set_location(-2160,0)

pyglet.gl.glClearColor(0.5,0.5,0.5,1) # Note that these are values 0.0 - 1.0 and not (0-255).
grating_image = pyglet.resource.image('grating.jpg')
grating_image.anchor_x = grating_image.width // 2 #center image
sprite = pyglet.sprite.Sprite(grating_image, x = 600, y = 800)
sprite.scale = 0.4
sprite2 = pyglet.sprite.Sprite(grating_image, x = 60, y = 80)
sprite2.scale = 0.04
#====================================================================


#====================================================================
# set up simple class that does nothing but hold parameter states
# this includes a buffer for the live camera view as well as task variables.
# task variables are updated in this as the task runs
class Params():
    def __init__(self,mouse='test'):
        self.mouse = mouse
        self.basepath = r'C:\data\behavior'
        self.directory = os.path.join(self.basepath,str(self.mouse))
        if not os.path.exists(self.directory): os.makedirs(self.directory)
        self.start_time_string = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.directory = os.path.join(self.directory,self.start_time_string)
        if not os.path.exists(self.directory): os.makedirs(self.directory)                              
        self.filename = os.path.join(self.directory,self.start_time_string+'.csv')
        self.iti,self.bool_iti,self.bool_display,self.bool_reward_window,self.reward_vol,self.answer,\
        self.bool_correct,self.time_,self.last_end_time, self.stim_on = \
                                                                        2.0,True,False,False,10,'left',\
                                                                        False,0.0,0.0, False #initialize task control variables
        self.AUTOREWARD = False
        self.SPOUT_LOCK = True 
        self.ONSET_REWARD = True
        self.SHOW_CAMERA = False

        self.spout_postion = 'high'
        self.center_button, self.button_1, self.button_2 = 0,0,0
        self.frame = 0;self.camera_timestamps=[]
        self.new_trial_setup = False
        self.in_trial,self.catch = False,False

        self.stim_contrast,self.stim_orientation,self.stim_spatial_frequency,self.stim_delay,self.trial_start_time,self.stim_on_time,self.stim_off_time,self.stim_reaction_time,self.stim_rewarded,self.stim_reward_amount,self.reward_time,self.trial_AUTOREWARDED,self.spout_positions,self.spout_timestamps,self.trial_ONSET_REWARD = \
        [],[],[],[],[timer.time],[],[],[],[],[],[],[],[],[],[]
        print(self.trial_start_time)
        self.trial_already_rewarded=False

        self.lick_values = []
        self.lick_timestamps = [0]
        self.not_licking = True
        self.licked_on_this_trial = False

        #stuff for the live camera view window==================== 
        self.WIDTH = 532
        self.HEIGHT = 768
        self.RGB_CHANNELS = 3
        MAX_COLOR = 255
        screen = zeros(
            [self.HEIGHT, self.WIDTH,self. RGB_CHANNELS], dtype=np.uint8
        )
        self.IMG_FORMAT = 'RGB'
        self.pitch =self.WIDTH * self.RGB_CHANNELS

        self.image_data = pyglet.image.ImageData(
        self.WIDTH, self.HEIGHT, self.IMG_FORMAT, screen.tobytes(), self.pitch)
        #======================================
    
    def save_params(self):
        df = pd.DataFrame(list(zip(self.stim_contrast,self.stim_orientation,self.stim_spatial_frequency,
                self.stim_delay,self.trial_start_time,self.stim_on_time,self.stim_off_time,
                self.stim_reaction_time,self.stim_rewarded,self.stim_reward_amount,self.reward_time,
                self.trial_AUTOREWARDED,self.trial_ONSET_REWARD)),
            columns =['Contrast', 'Orientation','Spatial Frequency','Delay','trialstarttime','stimontime','stimofftime','reactiontime','rewarded','rewardamount','rewardtime','AUTOREWARD','ONSET_REWARD'])
        # print('saving '+str(df.shape[0])+' trials to '+self.filename)
        fa = []
        lapse = []
        for row in df.iterrows():
            if row[1].rewarded:
                fa.append(False)
                lapse.append(False)
            else:
                if row[1]['stimontime'] == -1:
                    fa.append(True)
                    lapse.append(False)
                else:
                    fa.append(False)
                    lapse.append(True)
        df['falsealarm'] = fa
        df['lapse']=lapse
        df.to_csv(self.filename)
        self.df = df

        save(os.path.join(params.directory,'lick_timestamps.npy'),params.lick_timestamps)
#====================================================================

# set up global timer for session. simply starts right before the game loop starts and runs up forever. 
# access using `timer.time`
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
#====================================================================

# on draw events. ==========================
# this is the main game loop
@game_window.event      
def on_draw():   
    game_window.clear()     # clear the window

    if not params.new_trial_setup: #check to see if we need to update params for a new trial. this only happens if the previous trial ended, and the animal hasn't licked for some amount of time that is currently hardcoded below. if not, execute the current trial. 
        if timer.time - params.lick_timestamps[-1] > 2.:
            setup_trial()
        else:
            pass #wait until animal hasn't licked for 2 seconds
    else: #we're ready for a new trial
        if timer.time > params.trial_start_time[-1]:#if enough time has passed since the end of the last trial, start a trial
            if not params.in_trial:
                start_trial()
            else: #we're in a trial, but before the stim has come on. start checking for false alarm licks
                if check_response():
                    if not params.stim_on:
                        params.stim_on_time.append(-1);params.stim_off_time.append(-1)
                        params.stim_rewarded.append(False);params.stim_reward_amount.append(-1)
                        params.reward_time.append(-1)
                        end_trial()
                        params.spout_postion = 'low'
                        if not params.SPOUT_LOCK:
                            task_io.move_spout(270); params.spout_positions.append(270);params.spout_timestamps.append(timer.time)

                #we've made it past the variable amount of time from the start of the trial to the start of the stim, so start showing the stimulus
                if timer.time > params.trial_start_time[-1] + params.stim_delay[-1]:
                    if not params.stim_on: 
                        print('stim on at '+str(timer.time))
                        if params.ONSET_REWARD:
                            task_io.s.rotate(20,'dispense');params.stim_rewarded.append(True);params.stim_reward_amount.append(20)

                        params.stim_on=True
                        params.stim_on_time.append(timer.time)
                    if not params.AUTOREWARD:
                       if check_lick_response():
                            print('lick detected')
                            task_io.s.rotate(20,'dispense');params.stim_rewarded.append(True);params.stim_reward_amount.append(20)
                            params.reward_time.append(timer.time)
                            params.stim_off_time.append(timer.time)
                            end_trial()
                    
        if params.stim_on:
            sprite.draw()
            if timer.time > params.trial_start_time[-1] + params.stim_delay[-1] + 5.:
                if params.AUTOREWARD:
                    print('giving reward at tend of ')
                    task_io.s.rotate(20,'dispense');params.stim_rewarded.append(True);params.stim_reward_amount.append(20)
                    params.reward_time.append(timer.time)
                else:
                    params.stim_rewarded.append(False);params.stim_reward_amount.append(-1)
                    params.reward_time.append(-1)
                params.stim_off_time.append(timer.time)
                end_trial()

        else:
            if params.stim_on: 
                pass

#the small window that shows the stimulus on the other PC screen for epxerimenter monitoring
@task_monitor.event      
def on_draw():   
    task_monitor.clear()     # clear the window       
    if params.stim_on: sprite2.draw() #draw if logic from game_window on_draw() says we should

#the live camera view window. 
@camera_window.event
def on_draw():
    if params.SHOW_CAMERA:
        if len(params.camera_timestamps) % 3 == 0:
            camera_window.clear()
            try:
                params.image_data.blit(0,0) #this updates the image with whatever has been stored in params.image_data
            except: print('cannot show live camera view')
#====================================================================

#functions used by the @game_window.event on_draw() to execute the task==================
def setup_trial():
    params.trial_start_time.append(timer.time + params.iti)

    if random.random() > 0.5: params.answer = 'left'
    else:                     params.answer = 'right'

    if params.answer == 'left': 
        sprite.rotation = 0
        params.stim_orientation.append(0)
        #TODO: need to set the x and y along with ori because origin is not in the center
    else:                       
        sprite.rotation = 90
        params.stim_orientation.append(90)

    params.stim_spatial_frequency.append(0.08)

    # params.trial_start_time.append(timer.time)
    #TODO: implement distribution here
    # as it is, random flat distro to 5 seconds
    params.stim_delay.append(random.random() * 5 ) 
    print(params.stim_delay[-1])

    contrasts = [0,0.05,0.1,0.2,0.4,0.8,1.0]
    contrast = contrasts[random.randint(7)]
    if contrast == 0: params.catch=True
    else: 
        params.catch=False
        #TODO: set sprite image manually based on contrast
        #sprite = pyglet.sprite.Sprite(grating_image, x = 300, y = 300)
        #sprint.set_scale(0.2)
    params.stim_contrast.append(contrast)
    # sprite.color = (int(255*contrast),int(255*contrast),int(255*contrast)) #don't do this anymore it doesn't work

    
    # params.stim_on_time.append(params.trial_start_time[-1] + params.stim_delay[-1])
    
    params.trial_AUTOREWARDED.append(params.AUTOREWARD)
    params.trial_ONSET_REWARD.append(params.ONSET_REWARD)

    params.new_trial_setup=True

def start_trial():
    print('start of trial at '+str(timer.time))
    trial_start = timer.time
    params.in_trial = True
    if params.spout_postion == 'low':
        if not params.SPOUT_LOCK:
            task_io.move_spout(90);params.spout_positions.append(90);params.spout_timestamps.append(timer.time)
            time.sleep(0.6)

def end_trial():
    print('end of trial at '+str(timer.time))
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
    params.stim_on=False #update boolean so we have the option to try again
    params.in_trial=False #reset
    params.licked_on_this_trial = False #reset
    params.new_trial_setup = False

    #update plots on disk
    f, ax = plt.subplots(1,1)
    ax.plot(params.df['rewarded'].rolling(10,step=3).mean(),'g',label='rewarded')
    ax.plot(params.df['falsealarm'].rolling(10,step=3).mean(),'orange',label='false alarm')
    ax.plot(params.df['lapse'].rolling(10,step=3).mean(),'r',label='lapse')
    ax.legend()
    f.savefig(os.path.join(params.directory,'progress.png'))
    plt.close('all')
    #make a lick plot
    
    # task_io.move_spout(270)

def check_response():
    lickometer_read = task_io.board.digital[task_io.lick_opto_pin].read()
    if not lickometer_read: # this flips the logic because the lickomter returns False when a lick is happening
        # print('lickedlickedlicked')
        params.licked_on_this_trial = True
        return True
    else: return False

#TODO check the recent history to see if there has been a lick since the stimulus turned on
#returns True or False
def check_lick_response():
    if len(np.where(np.array(params.lick_timestamps) > params.stim_on_time[-1])[0]) > 0:
        return True
    else:
        return False

#TODO calculate the reaction time, even if this was a false alarm. use check lick response, or at least use the relative timing of lick_stimstamps and trial start
def check_reaction_time(reaction_time):
        params.stim_rewarded.append(True)
        params.stim_reward_amount.append(25) #currently in rotation units
    # min_catch_hold_time  = 5.0
    # max_reaction_time = 1.0
    # if params.catch:
    #     if reaction_time > min_catch_hold_time:
    #         # task_io.move_servo(90)
    #         # task_io.move_servo(270)
    #         params.stim_rewarded.append(True)
    #         params.stim_reward_amount.append(180)
    #     else:
    #         params.stim_rewarded.append(False)
    #         params.stim_reward_amount.append(0)
    # else: 
    #     if reaction_time < max_reaction_time:
    #         # task_io.move_servo(90)
    #         # task_io.move_servo(270)
    #         params.stim_rewarded.append(True)
    #         params.stim_reward_amount.append(180)
    #     else:
    #         params.stim_rewarded.append(False)
    #         params.stim_reward_amount.append(0)

        #optionally add timeout here. 

def give_reward(self,volume):
    print("reward!")
    # self.rewardData.extend([globalClock.getFrameTime()])
    if have_nidaq:
        self.do.WriteBit(3,0)
        time.sleep(self.reward_time)
        self.do.WriteBit(3,1) # put a TTL on a line to indicate that a reward was given
        s.dispense(volume)#pass # not yet implemented
        self.do.WriteBit(3,0)
#====================================================================


# key bindings for experimenter control of task parameters in real time
#includes backup keyboard version for testing if harware not connected
@game_window.event 
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.A:
        print('A')
        params.center_button = True

    if symbol == pyglet.window.key.R:
        print('R')
        task_io.move_spout(90); params.spout_positions.append(90);params.spout_timestamps.append(timer.time) #this is up and lickable

    if symbol == pyglet.window.key.T:
        print('T')
        task_io.move_spout(270); params.spout_positions.append(270);params.spout_timestamps.append.append.append.append(timer.time) #this is down and unlickable

    if symbol == pyglet.window.key.W:
        print('w: dispense')
        # task_io.s.dispense(0.1)
        task_io.board.digital[task_io.water_reward_pin].write(1)
    if symbol == pyglet.window.key.V:
        if params.SPOUT_LOCK: params.SPOUT_LOCK= False
        else: params.SPOUT_LOCK= True
        print('SPOUT LOCK is now: '+str(params.SPOUT_LOCK))

    if symbol == pyglet.window.key.E:
        print('e: retract')
        task_io.s.rotate(20,'retract')
    if symbol == pyglet.window.key.D:
        print('d: dispense')
        task_io.s.rotate(20,'dispense')
    if symbol == pyglet.window.key.K:
        print(task_io.board.digital[task_io.lick_opto_pin].read())
    if symbol == pyglet.window.key.C:
        if params.SHOW_CAMERA: 
            params.SHOW_CAMERA = False
            print('turning off live view')
        else: 
            params.SHOW_CAMERA = True
            print('turning on live view')

    if symbol == pyglet.window.key.K:
        if params.ONSET_REWARD: 
            params.ONSET_REWARD = False
            print('Switching to lick sensing during image for reward')
        else: 
            params.ONSET_REWARD = True
            print('Switching automatic rewards at start of image on')

    if symbol == pyglet.window.key.L:
        if params.AUTOREWARD: 
            params.AUTOREWARD = False
            print('Switching to lick sensing during image for reward')
        else: 
            params.AUTOREWARD = True
            print('Switching automatic rewards at end of image on')

    if symbol == pyglet.window.key.Q:
        # try:
        print('cleaning up...')
        print('saving camera timestamps')
        save(os.path.join(params.directory,'camera_timestamps.npy'),params.camera_timestamps)
        print('saving camera movie as mp4')
        # print(np.shape(array(imgs).astype(np.uint8)))
        # vwrite(os.path.join(params.directory,"camera_frames.mp4"), array(imgs).astype(np.uint8))
        try:
            vwrite(os.path.join(params.directory,"camera_frames.mp4"), array(imgs).astype(np.uint8))
        except: print('failed to save cameras as mp4')
        # save(os.path.join(params.directory,'camera_frames.npy'),array(imgs))
        print('saving lick data...')
        # save(os.path.join(params.directory,'lick_values.npy'),params.lick_values)
        save(os.path.join(params.directory,'lick_timestamps.npy'),params.lick_timestamps)
        save(os.path.join(params.directory,'spout_positions.npy'),params.spout_positions)
        save(os.path.join(params.directory,'spout_timestamps.npy'),params.spout_timestamps)

        # except: print('failed saving camera frmaes')
        # for i,img in tqdm.tqdm(enumerate(imgs)):
            # Image.fromarray(img).save(os.path.join(params.directory, '%08d.png' % i))
        # exit()
        pyglet.app.exit()

    if symbol == pyglet.window.key.Z:
        print(params.not_licking)
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
#====================================================================

# behavior camera====================================================================
# connect to a flir camera and take frames with times that are on the same clock as the task
cam = Camera(index='20442803')#change to proper SN
cam.init()
cam.start()
imgs = []
#function that the pyglet scheduler calls to grab a frame from the FLIR
def grab_frame(dt):
    if params.SHOW_CAMERA:
        try:
            img = cam.get_array()
            imgs.append(img)
            params.camera_timestamps.append(timer.time)
        except:(print('camera image failed at '+str(timer.time)))
        # save(os.path.join(params.directory,'timestamps.npy'),params.camera_timestamps)
        # Image.fromarray(img).save(os.path.join(params.directory, '%08d.png' % params.frame))
        
        #every third frame update the image data in params so it can be drawn in the live view window.
        #TODO: check if it hurts to do this faster?
        if len(params.camera_timestamps) % 3 == 0:
            screen = np.zeros([params.HEIGHT, params.WIDTH, params.RGB_CHANNELS], dtype=np.uint8)
            for j in range(params.RGB_CHANNELS):
                screen[:, :, j] = np.array(imgs[-1]).astype(np.uint8)
            data = np.flipud(screen).tobytes()
            params.image_data.set_data(params.IMG_FORMAT,params.pitch,data)
        #     ax.imshow(img);plt.show()
        params.frame+=1
#====================================================================

#function that the pyglet scheduler calls to constantly monitor for licks independent of what is happening with the task
def read_licks(dt):
    lickometer_read = task_io.board.digital[task_io.lick_opto_pin].read()
    # print(lickometer_read)
    if not lickometer_read and timer.time - params.spout_timestamps[-1] > 0.5 :
        # print(params.not_licking)
        # params.lick_timestamps.append(timer.time)  #save all times. this will mean more than one time per lick
        if params.not_licking:
            print('lick at '+str(timer.time))
            params.lick_timestamps.append(timer.time)  #save just the first time a lick is sensed
            params.not_licking = False
    else:
        params.not_licking = True

#TODO
# sync pulse
# put out a pulse for synchronizing physiology hardware, like triggering the camera or marking task clock on the Neuropixles master clock
#this would be triggered by a scheduler, and the timestamps of the pulses saved in an npy. 

#====================================================================
# start the joystick listening
# try:
board_port = 'COM4'
task_io=ArduinoController(board_port) # use the default pins as set up by the class definite above. if needed, specify different pins when creating this object. 
# task_io.init()
# task_io.move_spout(90)

#set up parameters
params = Params(mouse = 'C104')
task_io.move_spout(90);params.spout_positions.append(270);params.spout_timestamps.append(timer.time)

#start the game loop

pyglet.clock.schedule(timer.update) # as fast as possible
pyglet.clock.schedule_interval(grab_frame,1/60.)
pyglet.clock.schedule_interval(read_licks,1/1000.)
#FYI the on_draw() functions above run at frame rate, so should be 60Hz. might be 30? maybe the card can't keep up with the big monitors?
pyglet.app.run()
    































    # def _lickSensorSetup(self):
    #     """ Attempts to set up lick sensor NI task. """
    #     ##TODO: Make lick sensor object if necessary. Let user select port and line.
    #     if have_nidaq:
    #         if self.di:
    #             self.lickSensor = self.di  # just use DI for now
    #             licktest = []
    #             for i in range(30):
    #                 licktest.append(self.di.Read()[self.lickline])
    #                 time.sleep(0.01)
    #             licktest = np.array(licktest, dtype=np.uint8)
    #             if len(licktest[np.where(licktest > 0)]) > 25:
    #                 self.lickSensor = None
    #                 self.lickData = [np.zeros(len(self.rewardlines))]
    #                 print("Lick sensor failed startup test.")
    #             else: print('lick sensor setup succeeded.')
    #             self.keycontrol = True
    #         else:
    #             print("Could not initialize lick sensor.  Ensure that NIDAQ is connected properly.")
    #             self.keycontrol = True
    #             self.lickSensor = None
    #             self.lickData = [np.zeros(len(self.rewardlines))]
    #             self.keys = key.KeyStateHandler()
    #             # self.window.winHandle.push_handlers(self.keys)
    #     else:
    #         print("Could not initialize lick sensor.  Ensure that NIDAQ is connected properly.")
    #         self.keycontrol = True
    #         self.lickSensor = None
    #         self.lickData = [np.zeros(len(self.rewardlines))]
    #         self.keys = key.KeyStateHandler()