import glob, time, json, os, datetime, tqdm
from numpy import random, save, array, dstack, zeros
import numpy as np
from pyfirmata import ArduinoMega, util, INPUT, SERVO, OUTPUT
from time import sleep
import pandas as pd
from simple_pyspin import Camera
from PIL import Image

#set up image and gameplay resources===============================
import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()

camera_window = pyglet.window.Window(1024, 768)
camera_window.set_location(400,100)

game_window = pyglet.window.Window(2160, 1920)
game_window.set_vsync(False)
game_window.set_location(-2160,0)
pyglet.gl.glClearColor(0.5,0.5,0.5,1) # Note that these are values 0.0 - 1.0 and not (0-255).
grating_image = pyglet.resource.image('grating.jpg')
grating_image.anchor_x = grating_image.width // 2 #center image
sprite = pyglet.sprite.Sprite(grating_image, x = 600, y = 800)
sprite.scale = 0.2
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
                                                                        7.0,True,False,False,10,'left',\
                                                                        False,0.0,0.0, False #initialize task control variables

        self.center_button, self.button_1, self.button_2 = 0,0,0
        self.frame = 0;self.camera_timestamps=[]
        self.in_trial,self.catch = False,False

        self.stim_contrast,self.stim_orientation,self.stim_spatial_frequency,self.stim_delay,self.button_down_time,self.stim_on_time,self.stim_off_time,self.stim_reaction_time,self.stim_rewarded,self.stim_reward_amount,self.trial_start_time = \
        [],[],[],[],[],[],[],[],[],[],[]

        self.trial_already_rewarded=False

        self.lick_values = []
        self.lick_timestamps = []
        self.not_licking = True
        self.licked_on_this_trial = False

        #stuff for the live camera view window==================== 
        self.WIDTH = 1024
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
                self.stim_delay,self.button_down_time,self.stim_on_time,self.stim_off_time,
                self.stim_reaction_time,self.stim_rewarded,self.stim_reward_amount)),
            columns =['Contrast', 'Orientation','Spatial Frequency','Delay','button down time','stim on time','stim off time','reaction time','rewarded','reward amount'])
        df.to_csv(self.filename)

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

# on draw event. this is the main game loop==========================
@game_window.event      
def on_draw():   
    game_window.clear()     # clear the window
    # 
    # sprite.draw()

    try:
        params.center_button = task_io.button_state(53)
        params.button_1 = task_io.button_state(43) #"blue"
        params.button_2 = task_io.button_state(45) #"green"
    except:pass
    # print(params.button_1)


    #check to see if we are in an ITI. if we are at the end of it, start a trial
    # if timer.time > params.last_end_time + params.iti:
    #     if params.bool_iti:

    if not params.in_trial: # 
        setup_trial()
    else:
        if timer.time > params.trial_start_time[-1] + params.stim_delay[-1]:
            if not params.stim_on:
                start_trial()
        if params.stim_on:
            sprite.draw()
            # if timer.time > params.trial_start_time[-1] + params.stim_delay[-1] + 0.1: #delay between stim and reward
            #     if not params.trial_already_rewarded:
            #        
            #         params.trial_already_rewarded = True
            if check_response():
                end_trial()
            if timer.time > params.trial_start_time[-1] + params.stim_delay[-1] + random.exponential(2.5) + 1.:
                end_trial()

        # if not params.in_trial:#start drawing if stimulus is not already on
        #     params.button_down_time.append(timer.time)
        #     setup_trial()
        # else: #keep drawing if stimulus is already on
        #     if timer.time - params.button_down_time[-1] < params.stim_delay[-1]: #TODO: implement distribution here
        #         pass
        #     else:
        #         if not params.stim_on:
        #             start_trial()
        #         else:
        #             sprite.scale = 0.2
        #             sprite.draw()
        else:
            if params.stim_on: 
                pass
            #end_trial()   #check to see if the button is still down, if not stop drawing
    #     params.bool_iti=False
    # else: params.bool_iti=True

    # img = cam.get_array()
    # camera_timestamps.append(timer.time)
    # print(camera_timestamps)
    # save(os.path.join(params.directory,'timestamps.npy'),camera_timestamps)
    # Image.fromarray(img).save(os.path.join(params.directory, '%08d.png' % frame))
    # if frame % 3 == 0:
    #     ax.imshow(img);plt.show()
    # frame+1
    
    # print(timer.time)
    if params.button_1:
        print('blue')
    if params.button_2:
        print('green')

def setup_trial():
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
    params.button_down_time.append(-1)
    params.trial_start_time.append(timer.time)
    #TODO: implement distribution here
    # as it is, random flat distro to 5 seconds
    params.stim_delay.append(random.random() * 5+ params.iti) 
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

    params.trial_start_time.append(timer.time)
    # params.stim_on_time.append(params.trial_start_time[-1] + params.stim_delay[-1])
    
    #play sound
    #move motor

    params.in_trial=True

def start_trial():
    print('start vis stim of new trial')
    trial_start = timer.time
    params.stim_on_time.append(trial_start)

    params.stim_on=True
    # task_io.move_spout(90)

def end_trial():
    #log trial info
    # print(timer.time)
    # print(params.last_end_time + params.iti)
    # print(params.answer + '   '+answered)
    params.last_end_time = timer.time
    params.stim_off_time.append(params.last_end_time) #store trial end in params
    

    reaction_time= params.last_end_time - params.stim_on_time[-1]
    params.stim_reaction_time.append(reaction_time)  #store reaction time in params
    
    check_reaction_time(reaction_time)


    if not params.licked_on_this_trial:
        task_io.s.rotate(20,'dispense')
        
    params.save_params() #record the last trial on disk
    params.stim_on=False #update boolean so we have the option to try again
    params.in_trial=False #reset
    params.licked_on_this_trial = False #reset
    # time.sleep(1.5)
    # task_io.move_spout(270)

def check_response():
    lickometer_read = task_io.board.digital[task_io.lick_opto_pin].read()

    if not lickometer_read: # this flips the logic because the lickomter returns False when a lick is happening
        params.licked_on_this_trial = True
        return True
    else: return False
    

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

#backup keyboard version for testing if harware not connected
@game_window.event 
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.A:
        print('A')
        params.center_button = True

    if symbol == pyglet.window.key.R:
        print('R')
        task_io.move_spout(90) #this is up and lickable

    if symbol == pyglet.window.key.T:
        print('T')
        task_io.move_spout(270) #this is down and unlickable

    if symbol == pyglet.window.key.W:
        print('w: dispense')
        # task_io.s.dispense(0.1)
        task_io.board.digital[task_io.water_reward_pin].write(1)
        
    if symbol == pyglet.window.key.E:
        print('e: retract')
        task_io.s.rotate(20,'retract')
    if symbol == pyglet.window.key.D:
        print('d: dispense')
        task_io.s.rotate(20,'dispense')

    if symbol == pyglet.window.key.Q:
        print('cleaning up...')
        print('saving camera timestamps')
        save(os.path.join(params.directory,'camera_timestamps.npy'),params.camera_timestamps)
        print('saving camera movie as npy')
        save(os.path.join(params.directory,'camera_frames.npy'),array(imgs))
        print('saving lick data...')
        save(os.path.join(params.directory,'lick_values.npy'),params.lick_values)
        save(os.path.join(params.directory,'lick_timestamps.npy'),params.lick_timestamps)

        # for i,img in tqdm.tqdm(enumerate(imgs)):
            # Image.fromarray(img).save(os.path.join(params.directory, '%08d.png' % i))
        # exit()
        pyglet.app.exit()
def on_key_release(symbol, modifiers):
    if symbol == pyglet.window.key.A:
        params.center_button = False

#the live camera view window. 
@camera_window.event
def on_draw():
    camera_window.clear()
    try:
        params.image_data.blit(0,0) #this updates the image with whatever has been stored in params.image_data
    except: print('cannot show live camera view')
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
        self.lick_opto_pin = 31

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

        self.board.digital[self.lick_opto_pin].mode=INPUT
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
    img = cam.get_array()
    imgs.append(img)
    params.camera_timestamps.append(timer.time)
    # save(os.path.join(params.directory,'timestamps.npy'),params.camera_timestamps)
    # Image.fromarray(img).save(os.path.join(params.directory, '%08d.png' % params.frame))
    
    #every third frame update the image data in params so it can be drawn in the live view window.
    #TODO: check if it hurts to do this faster?
    if len(params.camera_timestamps) % 3 == 0:
        screen = np.zeros([params.HEIGHT, params.WIDTH, params.RGB_CHANNELS], dtype=np.uint8)
        for j in range(params.RGB_CHANNELS):
            screen[:, :, j] = imgs[-1]
        data = np.flipud(screen).tobytes()
        params.image_data.set_data(params.IMG_FORMAT,params.pitch,data)
    # #     ax.imshow(img);plt.show()
    # params.frame+=1
#====================================================================

def read_licks(dt):
    lickometer_read = task_io.board.digital[task_io.lick_opto_pin].read()

    if not lickometer_read:
        if params.not_licking:
            print('lick at '+str(timer.time))
            params.not_licking = False
            params.lick_timestamps.append(timer.time)  
    else: params.not_licking = True

#TODO
# sync pulse
# put out a pulse for synchronizing physiology hardware, like triggering the camera or marking task clock on the Neuropixles master clock

#====================================================================
# start the joystick listening
# try:
board_port = 'COM4'
task_io=ArduinoController(board_port) # use the default pins as set up by the class definite above. if needed, specify different pins when creating this object. 
# task_io.init()
# task_io.move_spout(90)

#set up parameters
params = Params(mouse = 'test')
task_io.move_spout(90)

#start the game loop
# pyglet.clock.schedule_interval(timer.update, 1/500.0)
# print(pyglet.clock.get_frequency())
pyglet.clock.schedule(timer.update)
pyglet.clock.schedule_interval(grab_frame,1/60.)
pyglet.clock.schedule_interval(read_licks,1/1000.)
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