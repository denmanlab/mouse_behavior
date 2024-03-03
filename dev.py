
from imgui.integrations.pyglet import create_renderer
import pyglet
from random import randint, choice
from pyglet.clock import schedule_once, unschedule
import imgui
import pandas as pd
import datetime, os, glob
'''
TODO:
 - Implement real licking
 - Actual stimuli and orientations
 - hardware interfacing
    - lickometer logic to read actual
    - spout control
    - stimulus control --
        - i think i need to save out several ASCII files. 
        - then stimulate across.
 - timeout logic for excessive False Alarms
 - 

'''

class Params:
    def __init__(self, mouse = 'test'):
        self.mouse = mouse
        self.setup_directories()
        self.init_task_variables()
        #camera
        #load previous params

    def setup_directories(self):
        ''' setup base and specific session directories.'''
        self.basepath = r'C:\data\behavior'
        self.directory = os.path.join(self.basepath, str(self.mouse))
        #os.makedirs(self.directory, exist_ok = True

    def init_task_variables(self): 
        #trial variables
        self.stimuli = ['red', 'blue'] #ToDO: replace this with real stimuli! 
        self.trial_running = False 
        self.stimulus_visible = False
        self.stim_on_time = None
        self.lick_detected_during_trial = False
        self.trial_outcome = None
        self.last_lick_time = None # last lick time -- used to check quiet period
        self.lick_times = [] # list for full lick times 
        self.current_stim = None
        self.batch = pyglet.graphics.Batch()
        self.stimulus_rect = pyglet.shapes.Rectangle(x=350, y=250, width=100, height=100, color=(255, 255, 255), batch=self.batch)
        
        #to be able to modulate
        self.reward_vol = 50
        self.min_wait_time = 1
        self.max_wait_time = 5
        self.wait_time = None
        self.quiet_period = 2 #time required of no licking between trials
        self.stim_duration = 5
        
        self.autoreward = False
        self.shaping = False

        #buttons = [self.shaping, self.autoreward] #toggles
    
        #dataframe to be saved
        self.trials_df = pd.DataFrame(columns=['trial_number', 
                                                'stimulus', 
                                                'outcome',
                                                'false_alarm',
                                                'rewarded',
                                                'lapse',
                                                'stimulus_visible', 
                                                'lick_detected', 
                                                'trial_start_time', 
                                                'last_lick_time'])
    def update_df(self): # called after every trial to update the DF
        self.false_alarm = self.trial_outcome == 'False Alarm'
        self.rewarded = self.trial_outcome == 'Reward'
        self.lapse = self.trial_outcome == 'Lapse'

        new_index = len(params.trials_df)
        # Add a new row at the end of the DataFrame
        self.trials_df.loc[new_index] = {
            'trial_number': new_index + 1,
            'stimulus': self.current_stim,
            'outcome': self.trial_outcome,
            'false_alarm': self.false_alarm,
            'rewarded': self.rewarded,
            'lapse': self.lapse,
            'Stimulus Visible': self.stimulus_visible,
            'Lick Detected': self.lick_detected_during_trial,
            'Trial Start Time': self.stim_on_time,
            'Last Lick Time': self.last_lick_time,
            'Autoreward': self.autoreward
        }
        #self.trials_df.to_csv(self.path)
        
        # plotting! 
            # create figure
            # subplot 1: Rolling proportion
            # subblot 2: cumulutive counts
            # subplot 3: seconds x wait_time scatter (color coded)
            # subplot 4: stimuli x waittime (color coded)
            # subplot 5: "Success": True Lapses + Rewarded

class Timer:
    def __init__(self):
        self.reset()
    def reset(self):
        self.time = 0
        self.running = False
    def start(self):
        self.running = True
    def update(self, dt):
        if self.running:
            self.time += dt 

# Default settings (now part of Params)
params = Params(mouse = 'Test')
timer = Timer()
timer.start()

#Windows! 
#main window
window = pyglet.window.Window(width=600, height=600, caption="Experiment Window")
window.set_location(500, 200) # change this for rig setup
#settings
imgui.create_context() # Initialize ImGui context
settings_window = pyglet.window.Window(width = 500, height = 216, caption = "Settings")
settings_window.set_location(0,50)
imgui_renderer = create_renderer(settings_window)

# plotting performance window



####Hardware!
#spout
#lickometer
# stimulator 


## game logic, loops, and functions
@window.event
def on_draw():
    window.clear()
    # Draw stimulus if visible
    if params.stimulus_visible:
        params.stimulus_rect.draw()

@settings_window.event
def on_draw():
    settings_window.clear()
    imgui.new_frame()

    imgui.begin("Settings", True, flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)

    # Slider for Minimum Wait Time
    changed_min_wait, new_min_wait = imgui.slider_int("Minimum Wait Time", 
                                                      params.min_wait_time, 1, 30, 
                                                    "%.0f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_min_wait:
        params.min_wait_time = new_min_wait
        print(f'Minimum Wait Time: {params.min_wait_time}')

    # Slider for Maximum Wait Time
    changed_max_wait, new_max_wait = imgui.slider_int("Maximum Wait Time", 
                                                      params.max_wait_time, 1, 30, 
                                                      "%.0f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_max_wait:
        params.max_wait_time = new_max_wait
        print(f'Maximum Wait Time: {params.max_wait_time}')

    # Slider for Quiet Period (ITI with no licking)
    changed_quiet_period, new_quiet_period = imgui.slider_int("Quiet Period (ITI w no licking)", 
                                                              params.quiet_period, 1, 30, 
                                                              "%.0f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_quiet_period:
        params.quiet_period = new_quiet_period
        print(f'Quiet Period: {params.quiet_period}')

    # Slider for Reward Volume
    changed_reward_vol, new_reward_vol = imgui.slider_int("Reward volume", 
                                                          params.reward_vol, 1, 100, 
                                                          "%.0f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_reward_vol:
        params.reward_vol = new_reward_vol
        print(f'Reward Volume: {params.reward_vol}')

    
    changed_stim_dur, new_stim_dur = imgui.slider_int('Stim Duration', params.stim_duration, 1,10,'%.0f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_stim_dur:
        params.stim_duration = new_stim_dur
        print(f'Stim Duration {params.stim_duration}')
    #####BUTTONS
    # shaping
    if imgui.button(f"Shaping: {'True' if params.shaping else 'False'}"):
        params.shaping = not params.shaping  # Toggle the shaping state
        print(f'Shaping: {"On" if params.shaping else "Off"}')

    # autoreward
    if imgui.button(f"AutoReward: {'True' if params.autoreward else 'False'}"):
        params.autoreward = not params.autoreward  # Toggle the autoreward state
        print(f'AutoReward: {"On" if params.autoreward else "Off"}')
    imgui.end()
    imgui.render()
    imgui_renderer.render(imgui.get_draw_data())

@settings_window.event
def on_close():
    imgui_renderer.shutdown()

@window.event
def on_close():
    pass

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        current_time = timer.time #pyglet.clock.get_default().time()
        params.lick_times.append(current_time)  # Log the lick time
        params.last_lick_time = current_time
        print(f'Fake lick at {current_time}')
        process_lick(params)  # Process the lick based on current experiment state
    
    elif symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()
    elif symbol == pyglet.window.key.D:
        deliver_reward()

def setup_trial(params):
    if params.trial_running:  # Check if a trial is already running
        return  # Exit if a trial is in progress
    
    current_time = pyglet.clock.get_default().time()
    if params.last_lick_time is None or (current_time - params.last_lick_time) >= params.quiet_period:
        params.current_stim = choice(params.stimuli)
        params.wait_time = randint(params.min_wait_time, params.max_wait_time)
        params.trial_running = True
        params.stimulus_visible = False
        params.lick_detected_during_trial = False
        params.trial_outcome = None  # Reset trial outcome
        print(f"Trial starting now with {params.current_stim}, wait time is {params.wait_time} seconds.")
        
        # Unschedule to avoid overlaps
        unschedule(start_trial)
        unschedule(end_trial)
        
        schedule_once(start_trial, params.wait_time, params)
    else:
        # Reschedule the setup_trial check after a short delay, ensuring no overlap
        unschedule(setup_trial)  # Unschedule previous setup_trial calls
        schedule_once(lambda dt: setup_trial(params), 0.5)

def start_trial(dt, params):
    if params.current_stim == 'red':
        params.stimulus_rect.color = (255, 0, 0)
    else:
        params.stimulus_rect.color = (0, 0, 255)
    params.stimulus_visible = True
    params.stim_on_time = timer.time #pyglet.clock.get_default().time()
    print(f"Stimulus {params.current_stim} on")
    if params.autoreward: 
        deliver_reward()
    schedule_once(end_trial, params.stim_duration, params)

def process_lick(params): #processes lick events detected by read_lickometer for task relevancy
    if params.trial_running:
        if not params.stimulus_visible and params.trial_outcome == None: # stim off and no trial outcome
            params.trial_outcome = "False Alarm"
            print("False Alarm (FA): Lick detected before stimulus.")
            unschedule(end_trial)
            schedule_once(end_trial,0,params)   
        elif params.stimulus_visible and params.trial_outcome == None:
            params.trial_outcome = "Reward"
            #dispense(params.reward_vol)
            print("Reward: Lick detected after stimulus.")
        params.lick_detected_during_trial = True

def end_trial(dt, params):
    if not params.lick_detected_during_trial:
        params.trial_outcome = "Lapse"
        print("Lapse: No lick detected during the trial.")
    else:
        print(f"Trial outcome: {params.trial_outcome}")
    print("Trial ended")
    
    # Reset trial parameters for the next trial
    params.trial_running = False
    params.stimulus_visible = False
    
    # Update and save DF
    params.update_df()
    
    #schedule setup trial once mouse stops licking (quiet period)
    unschedule(start_trial) #just for safety
    unschedule(end_trial) # just for safety
    schedule_once(lambda dt: setup_trial(params), params.quiet_period)

def read_lickometer(dt):
    # Placeholder for hardware check logic
    lickometer = False # actually read digital pin
    # If a lick is detected:
    if lickometer:  
        current_time = timer.time #pyglet.clock.get_default().time()
        params.lick_times.append(current_time)
        params.last_lick_time = current_time
        print(f'Lick at {current_time}')
        process_lick(params)

def deliver_reward():
    pass 
    # put reward logic 

def run_experiment():
    setup_trial(params)
    # Schedule this function to be called every tick of the event loop
    pyglet.clock.schedule(read_lickometer) 
    pyglet.clock.schedule(timer.update)
    pyglet.app.run()

if __name__ == "__main__":
    run_experiment()
