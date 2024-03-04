
from imgui.integrations.pyglet import create_renderer
import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()
from pyglet.clock import schedule_once, unschedule
import imgui

from random import randint, choice


import pandas as pd
import datetime, os, glob

# import custom classes
from arduino_controller import ArduinoController
from custom_timer import Timer
from params import Params
from stimuli import Stimuli
from plotter import Plotter

'''
TODO:
 - Implement real licking
 - hardware interfacing
    - lickometer logic to read actual
    - spout control
    - cameras
    - electrical stimulus control --
        - i think i need to save out several ASCII files. 
        - then stimulate across.
 - timeout logic for excessive False Alarms
 - 

'''
# Default settings (now part of Params)
params = Params(mouse = 'Test')

plotter = Plotter(params) # plotting functions and tools for performance window

stimuli = Stimuli(params) #keeps track of stimuli settings and sprites. 

timer = Timer()
timer.start()

#set up arduino
board_port = 'COM4'
#task_io = ArduinoController(board_port)

#Windows! 
#main window
window = pyglet.window.Window(width=2160, height=1920, caption="Experiment Window")
window.set_location(-2160, 0) # change this for rig setup
window.set_vsync(False)
#settings
imgui.create_context() # Initialize ImGui context
settings_window = pyglet.window.Window(width = 500, height = 216, caption = "Settings")
settings_window.set_location(0,50)
settings_window.set_vsync(False)
imgui_renderer = create_renderer(settings_window)

#monitor stimuli
monitor_window = pyglet.window.Window(width = 400, height = 400, caption = "Monitor")
monitor_window.set_location(0, 400)
monitor_window.set_vsync(False)

# plotting performance window
task_monitor_plot = pyglet.window.Window(600, 600)
task_monitor_plot.set_location(1148,100)
task_monitor_plot.set_vsync(False)
pyglet.gl.glClearColor(0.5,0.5,0.5,1)


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
       stimuli.sprite.draw()

@monitor_window.event
def on_draw():
    window.clear()
    # Draw stimulus if visible
    if params.stimulus_visible:
       stimuli.sprite2.draw()

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

@task_monitor_plot.event
def on_draw():
    task_monitor_plot.clear()
    plotter.sprite_progress.scale = 0.8
    plotter.sprite_progress.draw()

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
        select_stimuli(params, stimuli, catch_frequency = params.catch_frequency)
        params.wait_time = randint(params.min_wait_time, params.max_wait_time)
        params.trial_running = True
        params.stimulus_visible = False
        params.lick_detected_during_trial = False
        params.trial_outcome = None  # Reset trial outcome
        
        params.trial_start_time = timer.time
        print(f"Trial Started, wait time is {params.wait_time} seconds.")
        
        # Unschedule to avoid overlaps
        unschedule(start_trial)
        unschedule(end_trial)
        
        schedule_once(start_trial, params.wait_time, params)
    else:
        # Reschedule the setup_trial check after a short delay, ensuring no overlap
        unschedule(setup_trial)  # Unschedule previous setup_trial calls
        schedule_once(lambda dt: setup_trial(params), 0.5)

def start_trial(dt, params):
    params.stimulus_visible = True
    params.stim_on_time = timer.time #pyglet.clock.get_default().time()
    print(f"Stimulus Contrast {params.stim_contrast} on")
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
            if params.catch: # that is stim contrast is off 
                params.trial_outcome = "False Alarm"
                print("Catch: Lick detected after 0 Contrast.")
            else:
                params.rewarded_lick_time = timer.time
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
    plotter.update_plots(params.trials_df)
    
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

def select_stimuli(Params, Stimuli, catch_frequency = 1): 
    '''
    this randomly selects which stimuli to show based on stimuli present in stimuli class
    TODO: add logic for choosing electrical stim
    Inputs: instance of params and stimuli
    catch_frequency changes how likely a null trial is.. int: the actual number of zero contrasts added to selection pool
    '''
    ## select a contrast
    contrasts = list(Stimuli.grating_images.keys())
    for _ in range(catch_frequency):
        contrasts.append('0')
    
    contrast = choice(contrasts)

    if contrast == '0':
        Params.catch = True
        Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.blank_image, x = 1000, y = 450)
        Stimuli.sprite.scale = 4.8
    else: 
        Params.catch=False
        Stimuli.grating_image = Stimuli.grating_images[contrast]
        Stimuli.grating_image.anchor_x = Stimuli.grating_image.width // 2 #center image
        Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.grating_image, x = 1000, y = 450)
        Stimuli.sprite.scale = 4.8
        
        Stimuli.sprite2 = pyglet.sprite.Sprite(Stimuli.grating_image, x = 200, y = 400)
        # Set the anchor point to the center of sprite2 for true centering
        Stimuli.sprite2.x = monitor_window.width // 2
        Stimuli.sprite2.y = monitor_window.height // 2
        Stimuli.sprite2.scale = 0.5
        Stimuli.sprite2.anchor_x = Stimuli.sprite2.width // 2
        Stimuli.sprite2.anchor_y = Stimuli.sprite2.height // 2

    Params.stim_contrast = int(contrast)

    ## select an orientation... ignoring for now
    # if random.random() > 0.5: 
    #     Params.stim_orientation = '0'
    #     Stimuli.sprite.rotation = 0
    # else:                     
    #     params.stim_orientation = '90'
    #     Stimuli.sprite.rotation = 90
    #params.stim_spatial_frequency.append(0.08) # what the heck is this, it doesn't do anything?

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
