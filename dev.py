
from imgui.integrations.pyglet import create_renderer
import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()
from pyglet.clock import schedule_once, unschedule
import imgui

from random import randint, choice, uniform


import pandas as pd
import numpy as np
import datetime, os, glob, sys

# import custom classes
from arduino_controller_jlh import ArduinoController #controls arduino w solenoid, lick spout servo, and buzzer.
from custom_timer import Timer #timer for times that start at zero and can be fed into the pyglet timing
from params import Params # params class that saves DF and holds task variables
from stimuli import Stimuli # holds stimuli infrmation
from plotter import Plotter # plots things, task live plots and summary plots, individual plots as needed

import sys
# EBS stimulator class (Am4100)
am4100_code_path = r"C:\Users\denma\Documents\GitHub\am4100_code"
sys.path.append(am4100_code_path)
from am4100 import AM4100

'''
TODO:
 - hardware interfacing
    - cameras (some work done with this but not really implemented)
    - electrical stimulus control
        - likely will use am4100 
        - have a class that interfaces with the 4100 that can send commands
        - need to just integrate this class into game logic
        - add ability to select stimuli in stimuli and params and in gui.
        - test latencies.
        - copy stimuli outputs and params and etc into classes...
        - determine if i should use game (arduino/nidaq) to external trigger stimulator or figure out how to internal trigger it
        - 
 - 

'''
# Collect user input before running the experiment
mouse_name = input("Enter the mouse name: ")
mouse_weight = input("Enter the mouse weight (g): ")

#Windows! 
#main window
window = pyglet.window.Window(width=2160, height=1920, caption="Experiment Window")
window.set_location(-2160, 0) # change this for rig setup
window.set_vsync(False)
pyglet.gl.glClearColor(0.5,0.5,0.5,1)
#settings
imgui.create_context() # Initialize ImGui context
settings_window = pyglet.window.Window(width = 500, height = 400, caption = "Settings")
settings_window.set_location(450,100)
settings_window.set_vsync(False)
imgui_renderer = create_renderer(settings_window)


#monitor stimuli
monitor_window = pyglet.window.Window(width = 400, height = 400, caption = "Monitor")
monitor_window.set_location(490, 520)
monitor_window.set_vsync(False)
pyglet.gl.glClearColor(0.5,0.5,0.5,1)

# plotting performance window
task_monitor_plot = pyglet.window.Window(1000, 800)
task_monitor_plot.set_location(900,100)
task_monitor_plot.set_vsync(False)
pyglet.gl.glClearColor(0.5,0.5,0.5,1) # Note that these are values 0.0 - 1.0 and not (0-255).



#####  game logic, loops, and functions

## window events 
@window.event
def on_draw():
    window.clear()
    # Draw stimulus if visible
    if params.stimulus_visible:
       stimuli.sprite.draw()

@monitor_window.event
def on_draw():
    monitor_window.clear()
    # Draw stimulus if visible
    if params.stimulus_visible:
        if params.stim_contrast is not None: # its a visual trial
            stimuli.sprite2.draw()
        else: # its an estim trial
            #stimuli.estim_circle.draw()
            stimuli.estim_label.draw()        

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
    changed_quiet_period, new_quiet_period = imgui.slider_float("Quiet Period (ITI w no licking)", 
                                                              params.quiet_period, 1.0, 5.0, 
                                                              "%.1f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_quiet_period:
        params.quiet_period = new_quiet_period
        print(f'Quiet Period: {params.quiet_period}')

    # Slider for Reward Volume
    changed_reward_vol, new_reward_vol = imgui.slider_int("Reward volume", 
                                                          params.reward_vol, 10, 200, 
                                                          "%.0f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_reward_vol:
        params.reward_vol = new_reward_vol
        print(f'Reward Volume: {params.reward_vol}')

    
    changed_stim_dur, new_stim_dur = imgui.slider_float('Stim Duration', params.stim_duration, 1.0, 10.0, '%.1f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_stim_dur:
        params.stim_duration = new_stim_dur
        print(f'Stim Duration {params.stim_duration}')

    '''
    changed_catch_freq, new_catch_freq = imgui.slider_int('Catch Frequency', params.catch_frequency, 0,10,'%.0f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_catch_freq:
        params.catch_frequency = new_catch_freq
        print(f'Catch Frequency {params.catch_frequency}')
    '''

    changed_FA_penalty, new_FA_penalty = imgui.slider_int('FA Penalty', params.FA_penalty, 0,10,'%.0f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_FA_penalty:
        params.FA_penalty = new_FA_penalty
        print(f'FA Penalty {params.FA_penalty}')
    
    changed_timeout_dur, new_timeout_dur = imgui.slider_int('Timeout Duration', params.timeout_duration, 0,30,'%.0f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_timeout_dur:
        params.timeout_duration = new_timeout_dur
        print(f'Timeout Duration {params.timeout_duration}')

    
    changed_buzzer_volume, new_buzzer_volume_raw = imgui.slider_float('Buzzer Volume', params.buzzer_volume, 0.00, 1.00, '%.2f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)

    # Scale and snap the value to the nearest increment of 0.05
    new_buzzer_volume = round(new_buzzer_volume_raw / 0.05) * 0.05

    if changed_buzzer_volume:
        params.buzzer_volume = new_buzzer_volume
        print(f'Buzzer Volume {params.buzzer_volume:.2f}')

    
    #####BUTTONS
    
    # Determine button colors based on whether the stimuli are included
    visual_button_color = (0, 0.5, 0) if params.VISUAL_INCLUDED else (0.5, 0, 0)  # Green if included, red if not
    
    # Push style color for visual stimuli toggle button
    imgui.push_style_color(imgui.COLOR_BUTTON, *visual_button_color)
    if imgui.button("Toggle Visual Stimuli"):
        params.VISUAL_INCLUDED = not params.VISUAL_INCLUDED  # Toggle the boolean
        if params.VISUAL_INCLUDED:
            params.contrasts = list(stimuli.grating_images.keys())  # Reset the list to all keys
            print("Visual stimuli enabled")
        else:
            params.contrasts = []  # Clear the list
            print("Visual stimuli disabled")
    imgui.pop_style_color(1)  # Pop the button color style to return to default

    
    button_width = 30  
    button_height = 20  

    #### visual contrast buttons
    if params.VISUAL_INCLUDED:
        first_button = True
        for contrast in stimuli.grating_images.keys():
            button_label = f"{contrast}"
            button_color = (0, 0.5, 0) if contrast in params.contrasts else (0.5, 0, 0) # Dark green if IN, dark red if OUT

            # Adjust the button color based on its state
            imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)

            if not first_button:
                imgui.same_line()
            else:
                first_button = False

            if imgui.button(button_label, button_width, button_height):
                if contrast in params.contrasts:
                    params.contrasts.remove(contrast)
                    print(f'Removed {contrast} from contrasts')
                else:
                    params.contrasts.append(contrast)
                    print(f'Added {contrast} to contrasts')

            # Pop the button color style to return to default
            imgui.pop_style_color(1)

    #### estim amplitude buttons

    estim_button_color = (0, 0.5, 0) if params.ESTIM_INCLUDED else (0.5, 0, 0)

    # Push style color for electrical stimuli toggle button
    imgui.push_style_color(imgui.COLOR_BUTTON, *estim_button_color)
    if imgui.button("Toggle Electrical Stimuli"):
        params.ESTIM_INCLUDED = not params.ESTIM_INCLUDED  # Toggle the boolean
        if params.ESTIM_INCLUDED:
            params.estim_amps = list(stimuli.estim_params.keys())  # Reset the list to all keys
            print("Electrical stimuli enabled")
        else:
            params.estim_amps = []  # Clear the list
            print("Electrical stimuli disabled")
    imgui.pop_style_color(1)  # Pop the button color style to return to default
    button_width = 50  
    button_height = 20  
    
    if params.ESTIM_INCLUDED:
        # Handle positive values
        first_button = True  # Ensure first button does not call same_line()
        for amp in sorted(stimuli.estim_params.keys(), key=lambda x: int(x.rstrip('ua'))):  # Sort keys to ensure order
            if int(amp.rstrip('ua')) > 0:
                button_label = f"{amp}"
                button_color = (0, 0.5, 0) if amp in params.estim_amps else (0.5, 0, 0)  # Dark green if IN, dark red if OUT

                # Adjust the button color based on its state
                imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)

                if not first_button:
                    imgui.same_line()
                else:
                    first_button = False

                if imgui.button(button_label, button_width, button_height):
                    if amp in params.estim_amps:
                        params.estim_amps.remove(amp)
                        print(f'Removed {amp} from estim_amps')
                    else:
                        params.estim_amps.append(amp)
                        print(f'Added {amp} to estim_amps')

                # Pop the button color style to return to default
                imgui.pop_style_color(1)

        # Handle negative values separately
        first_button = True  # Reset for negative values
        for amp in sorted(stimuli.estim_params.keys(), key=lambda x: int(x.rstrip('ua')), reverse = True):
            if int(amp.rstrip('ua')) < 0:
                button_label = f"{amp}"
                button_color = (0, 0.5, 0) if amp in params.estim_amps else (0.5, 0, 0)  # Dark green if IN, dark red if OUT

                # Adjust the button color based on its state
                imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)

                if not first_button:
                    imgui.same_line()
                else:
                    first_button = False

                if imgui.button(button_label, button_width, button_height):
                    if amp in params.estim_amps:
                        params.estim_amps.remove(amp)
                        print(f'Removed {amp} from estim_amps')
                    else:
                        params.estim_amps.append(amp)
                        print(f'Added {amp} to estim_amps')

                # Pop the button color style to return to default
                imgui.pop_style_color(1)


    button_color = (0.5, 0, 0) if params.PAUSED else (0, 0.5, 0) # Dark green if playing, dark red if paused
    imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)
    if imgui.button(f"Pause Button: {'PAUSED' if params.PAUSED else 'Playing'}"):
        if params.PAUSED:
            unpause(params)
            print('Unpaused')
        else:
            pause(params)
            print('Paused')

    imgui.pop_style_color(1)
    
    '''
    imgui.same_line()
    button_color = (0, 0.5, 0) if params.shaping else (0.5, 0, 0) # Dark green if shaping, dark red if not
    imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)
    if imgui.button(f"Shaping: {'True' if params.shaping else 'False'}"):
        params.shaping = not params.shaping  # Toggle the shaping state
        print(f'Shaping: {"On" if params.shaping else "Off"}')

    imgui.pop_style_color(1)
    '''
    # autoreward
    imgui.same_line()
    button_color = (0, 0.5, 0) if params.autoreward else (0.5, 0, 0) # Dark green if autoreward, dark red if not
    imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)
    if imgui.button(f"AutoReward: {'True' if params.autoreward else 'False'}"):
        params.autoreward = not params.autoreward  # Toggle the autoreward state
        print(f'AutoReward: {"On" if params.autoreward else "Off"}')

    imgui.pop_style_color(1)

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

@task_monitor_plot.event
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
        deliver_reward(params, task_io)
    
    elif symbol == pyglet.window.key.Q:
        # try:
        print('cleaning up...')
        print('saving lick data...')
        
        # save(os.path.join(params.directory,'lick_values.npy'),params.lick_values)
        np.save(os.path.join(params.directory,'lick_timestamps.npy'),params.lick_times)
        np.save(os.path.join(params.directory,'estim_timestamps_software.npy'), params.estim_times_software)
        np.save(os.path.join(params.directory,'estim_timestamps_digital.npy'), params.estim_times_digital)
        #np.save(os.path.join(params.directory,'spout_positions.npy'),params.spout_positions)
        #np.save(os.path.join(params.directory,'spout_timestamps.npy'),params.spout_timestamps)
        print('closing devices')
        task_io.board.exit()
        stimulator.close_connection()
        pyglet.app.exit()


    elif symbol == pyglet.window.key.R:
        print('R: up')
        task_io.move_spout(90) #this is up and lickable

    elif symbol == pyglet.window.key.T:
        print('T: down')
        task_io.move_spout(270) #this is down and unlickable

    elif symbol == pyglet.window.key.S:
        print('Solenoid droplet')
        task_io.droplet(0.1)
    elif symbol == pyglet.window.key.P:
        if params.PAUSED:
            unpause(params)
            print('Unpaused, setup trial scheduled')
        else:
            pause(params)
            print('Paused: all events unscheduled')
    elif symbol == pyglet.window.key.M:
        manual_stim(params)
            

## task functions 
def hide_stimulus(dt, params):  
    params.stimulus_visible = False

def manual_stim(params):
    if not params.PAUSED:
        pause(params)
        resume = True
    else: 
        resume = False
    select_stimuli(params, stimuli)
    params.stimulus_visible = True
    schedule_once(scheduled_reward, 0.1, params, task_io)
    # Schedule to turn the stimulus off after 1 second
    schedule_once(hide_stimulus, params.stim_duration, params)
    if resume:
        unpause(params)
        
def scheduled_reward(dt, params, task_io): #wrapper for this that takes a dt for edge cases where you may want to schedule
    deliver_reward(params, task_io)
def pause(params):
    unschedule(setup_trial)
    unschedule(start_trial) 
    unschedule(end_trial) 
    unschedule(hide_stimulus)
    params.trial_running = False
    params.stimulus_visible = False 
    params.PAUSED = True

def unpause(params):
    params.PAUSED = False
    setup_trial(params)

def setup_trial(params):
    if params.trial_running:  # Check if a trial is already running
        return  # Exit if a trial is in progress
    
    current_time = timer.time
    if (current_time - params.last_lick_time) >= params.quiet_period and not params.timeout:
        select_stimuli(params, stimuli)
        params.wait_time = uniform(params.min_wait_time, params.max_wait_time)
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

def select_stimuli(Params, Stimuli): 
    ## select a contrast
    contrasts = Params.contrasts #create a copy just to not mess with logic below
    estim_amps = Params.estim_amps
    
    '''
    if Params.catch_frequency > 0:
        for _ in range(Params.catch_frequency):
            contrasts.append('0')
    '''
    
    if Params.VISUAL_INCLUDED and not Params.ESTIM_INCLUDED:
        contrast = choice(contrasts)
        params.stim_contrast = int(contrast)
        amp = None 
        params.estim_amp = None
    if Params.ESTIM_INCLUDED and not Params.VISUAL_INCLUDED:
        amp = choice(estim_amps)
        params.estim_amp = int(amp.strip('ua'))
        contrast = None
        params.stim_contrast = None
    if Params.ESTIM_INCLUDED and Params.VISUAL_INCLUDED:
        combined = contrasts + estim_amps
        stimuli = choice(combined)
        
        if 'ua' in stimuli:
            amp = stimuli
            params.estim_amp = int(amp.strip('ua'))
            contrast = None
            params.stim_contrast = None
        else:
            contrast = stimuli
            amp = None
            params.estim_amp = None
            params.stim_contrast = int(contrast)
    
    if contrast is not None:
        if contrast == '0':
            Params.catch = True
            Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.blank_image, x = 1000, y = 450)
            Stimuli.sprite.scale = 4.8
            Stimuli.sprite.visible = False

            Stimuli.sprite2 = pyglet.sprite.Sprite(Stimuli.blank_image, x = 200, y = 400)
            # Set the anchor point to the center of sprite2 for true centering
            Stimuli.sprite2.x = monitor_window.width // 2
            Stimuli.sprite2.y = monitor_window.height // 2
            Stimuli.sprite2.scale = 0.5
            Stimuli.sprite2.anchor_x = Stimuli.sprite2.width // 2
            Stimuli.sprite2.anchor_y = Stimuli.sprite2.height // 2
        else: 
            Params.catch=False
            Stimuli.grating_image = Stimuli.grating_images[contrast]
            Stimuli.grating_image.anchor_x = Stimuli.grating_image.width // 2 #center image
            Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.grating_image, x = 1000, y = 450)
            Stimuli.sprite.scale = 4.8
            Stimuli.sprite.visible = True
            
            Stimuli.sprite2 = pyglet.sprite.Sprite(Stimuli.grating_image, x = 200, y = 400)
            # Set the anchor point to the center of sprite2 for true centering
            Stimuli.sprite2.x = monitor_window.width // 2
            Stimuli.sprite2.y = monitor_window.height // 2
            Stimuli.sprite2.scale = 0.5
            Stimuli.sprite2.anchor_x = Stimuli.sprite2.width // 2
            Stimuli.sprite2.anchor_y = Stimuli.sprite2.height // 2
    
    elif amp is not None: #that is its an estim trial
        Params.catch = False
        # sprite logic just to keep consistent for "drawing" but sets it to invisible like a catch trial
        Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.blank_image, x = 1000, y = 450)
        Stimuli.sprite.scale = 4.8
        Stimuli.sprite.visible = False
        #monitor window

        Stimuli.estim_label = pyglet.text.Label(f'Estim Amp: {amp}', font_name='Arial', font_size=20,
                                      x=monitor_window.width // 2, y=monitor_window.height // 2 - 70,
                                      anchor_x='center')
        
        update_estim_params(stimulator, int(amp.strip('ua')))

    def select_stimuli2(Params, Stimuli): 
        
        tasks = []
        if Params.VISUAL_INCLUDED:
            tasks.append('visual')
        if Params.ESTIM_INCLUDED:
            tasks.append('estim')
        if Params.MOVING_CIRCLE_INCLUDED:
            tasks.append('moving_circle')
                
        task = choice(tasks)
        params.task = task 
        if task == 'visual':
            contrast = choice(Params.contrasts)
            Params.stim_contrast = int(contrast)
            Params.estim_amp = None
            if contrast == '0': #catch trial
                Params.catch = True
                Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.blank_image, x = 1000, y = 450)
                Stimuli.sprite.scale = 4.8
                Stimuli.sprite.visible = False

                Stimuli.sprite2 = pyglet.sprite.Sprite(Stimuli.blank_image, x = 200, y = 400)
                # Set the anchor point to the center of sprite2 for true centering
                Stimuli.sprite2.x = monitor_window.width // 2
                Stimuli.sprite2.y = monitor_window.height // 2
                Stimuli.sprite2.scale = 0.5
                Stimuli.sprite2.anchor_x = Stimuli.sprite2.width // 2
                Stimuli.sprite2.anchor_y = Stimuli.sprite2.height // 2
            else: # not a catch trial
                Params.catch=False
                Stimuli.grating_image = Stimuli.grating_images[contrast]
                Stimuli.grating_image.anchor_x = Stimuli.grating_image.width // 2 #center image
                Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.grating_image, x = 1000, y = 450)
                Stimuli.sprite.scale = 4.8
                Stimuli.sprite.visible = True
                
                Stimuli.sprite2 = pyglet.sprite.Sprite(Stimuli.grating_image, x = 200, y = 400)
                # Set the anchor point to the center of sprite2 for true centering
                Stimuli.sprite2.x = monitor_window.width // 2
                Stimuli.sprite2.y = monitor_window.height // 2
                Stimuli.sprite2.scale = 0.5
                Stimuli.sprite2.anchor_x = Stimuli.sprite2.width // 2
                Stimuli.sprite2.anchor_y = Stimuli.sprite2.height // 2
             
        elif task == 'estim':
            amp = choice(Params.estim_amps)
            Params.estim_amp = int(amp.strip('ua'))
            Params.stim_contrast = None
            Params.catch = False
            # sprite logic just to keep consistent for "drawing" but sets it to invisible like a catch trial
            Stimuli.sprite = pyglet.sprite.Sprite(Stimuli.blank_image, x = 1000, y = 450)
            Stimuli.sprite.scale = 4.8
            Stimuli.sprite.visible = False
            #monitor window
            Stimuli.estim_label = pyglet.text.Label(f'Estim Amp: {amp}', font_name='Arial', font_size=20,
                                        x=monitor_window.width // 2, y=monitor_window.height // 2 - 70,
                                        anchor_x='center')
            
            update_estim_params(stimulator, int(amp.strip('ua'))) #updates the stimulator with chosen estim param
        
        elif task == 'moving_circle':
            pass
            ''' contrast and radius size are chosen randomly in the moving circle class... 
                speed and angle incrementer are static.           
            '''
            #circle.reset_position update the circle (should be circle.reset_position)
            #Params.circle_contrast = circle.contrast
            #Params.circle_size = circle.radius 
            
            

def start_trial(dt, params):
    params.stimulus_visible = True
    params.stim_on_time = timer.time #pyglet.clock.get_default().time()
    
    if params.stim_contrast is not None: # visual trial
        print(f"Stimulus Contrast {params.stim_contrast} on")
    elif params.estim_amp is not None: # estim trial
        print('estim trial')
        stimulator.flush_serial_port() # flushes the port so it runs better
        stimulator.send_command_and_read_response('1001 set trigger one')  # trigger the stim!!!
        params.estim_times_software.append(timer.time)
        params.estim_params = stimulator.get_params() #track the parameters from the stimulator
        print(params.estim_params)
    
    if params.autoreward == True and params.stim_contrast != 0:
        schedule_once(scheduled_reward, 0.25, params, task_io)
    schedule_once(end_trial, params.stim_duration, params)

def process_lick(params): #processes lick events detected by read_lickometer for task relevancy
    if params.trial_running:
        if not params.stimulus_visible and params.trial_outcome == None: # stim off and no trial outcome
            task_io.buzz(volume = params.buzzer_volume) # buzz for an auditory learning cue
            params.trial_outcome = "False Alarm"
            params.rewarded_lick_time = None 
            params.stimulus_visible = False
            params.FA_lick_time = timer.time
            unschedule(start_trial)
            print("False Alarm (FA): Lick detected before stimulus.")
            unschedule(end_trial)
            schedule_once(end_trial,0,params)   
        elif params.stimulus_visible and params.trial_outcome == None:
            if params.catch: # that is stim contrast is off 
                task_io.buzz(volume = params.buzzer_volume) # buzz for an auditory learning cue
                params.trial_outcome = "False Alarm"
                params.rewarded_lick_time = timer.time # rewarded_lick_time is bad variable name for this but its fine. i don't want to create new variable
                print("Catch: Lick detected after 0 Contrast.")
            else:
                params.rewarded_lick_time = timer.time
                params.trial_outcome = "Reward"
                deliver_reward(params, task_io)
                print("Reward: Lick detected after stimulus.")
        params.lick_detected_during_trial = True

def end_trial(dt, params):
    if not params.lick_detected_during_trial:
        params.trial_outcome = "Lapse"
        params.rewarded_lick_time = None
        print("Lapse: No lick detected during the trial.")
    else:
        print(f"Trial outcome: {params.trial_outcome}")
    print("Trial ended")
    
    # Reset trial parameters for the next trial
    params.trial_running = False
    params.stimulus_visible = False
    
    # check if mouse needs a timeout!!! i.e., FA streak greater than FA penalty threshold
    if params.FA_penalty_check():
        print(f"FA streak of {params.FA_streak} greater than FA penalty of {params.FA_penalty}. Timeout!")
        params.FA_streak = 0
        params.timeout = True
        unschedule(setup_trial)
        unschedule(start_trial) #just for safety
        unschedule(end_trial) # just for safety
        move_spout(params, task_io) # move spout down/unlickable
        schedule_once(lambda dt: move_spout(params, task_io), params.timeout_duration) #move spout up/lickable after timeout
        schedule_once(lambda dt: setup_trial(params), params.timeout_duration)
        schedule_once(set_timeout_false, params.timeout_duration)
    else:   #schedule setup trial once mouse stops licking (qquiet period)
        unschedule(start_trial) #just for safety
        unschedule(end_trial) # just for safety
        schedule_once(lambda dt: setup_trial(params), params.quiet_period)
    
    # Update and save DF
    params.update_df()
    #try:
    plotter.update_plots(params.trials_df)
    #except Exception as e:
    #    print(f"Unable to update the plotter: {e}")
    

def set_timeout_false(dt): 
    params.timeout = False

def read_lickometer(dt, params):
    # Placeholder for hardware check logic
    lickometer = task_io.ir_pin.read()
    #lickometer = task_io.board.digital[10].read() #high is licking, low is not licking
    
    # If a lick is detected and its been at least 0.5s since last lick:
    if not lickometer and timer.time - params.last_lick_time > 0.5:
        current_time = timer.time #pyglet.clock.get_default().time()
        params.lick_times.append(current_time)
        params.last_lick_time = current_time
        print(f'Lick at {current_time}')
        process_lick(params)

def read_estim_digital_copy(dt, params):
    estimometer = task_io.estim_pin.read() 
    if estimometer and timer.time - params.last_estim_dig > 0.5: 
        current_time = timer.time
        params.estim_times_digital.append(current_time)
        params.last_estim_dig = current_time
    

        

def deliver_reward(params, task_io):
    #task_io.s.rotate(params.reward_vol,'dispense') this was for Stepper!
    task_io.droplet(params.reward_vol/1000) #divide by 1000 to convert to seconds
    print(f"solenoid open for {params.reward_vol} ms")

def update_estim_params(AM4100, amp): #for now only going to change amplitude but can change others
    AM4100.stop() # sets the stimulator to read changes 
    
    AM4100.set_amplitude(amp)
    
    AM4100.run() # sets to waiting for trigger

def move_spout(params, task_io):
    if params.spout_position == 'up': #lickable
        # move spout down
        task_io.move_spout(270)
        params.spout_position = 'down'
        print(f"spout {params.spout_position}")
    else: #unlickable
        # move spout up
        task_io.move_spout(90)
        params.spout_position = 'up'
        print(f"spout {params.spout_position}")
            
def run_experiment():
    setup_trial(params)
    # Schedule this function to be called every tick of the event loop
    
    pyglet.clock.schedule_interval(read_lickometer, 1/1000, params) 
    pyglet.clock.schedule(timer.update)
    task_io.move_spout(90) # move spout back up to lickable position
    pyglet.app.run()



# Create Params instance with user inputs
params = Params(mouse=mouse_name, weight=mouse_weight) #these variables are set at the top of the script w an input so they occur before drawn windows

# create stimulator class
try:
    stimulator = AM4100(com_port = 'COM4')
    params.stimulator_connected = True
except: 
    params.stimulator_connected = False

plotter = Plotter(params) # plotting functions and tools for performance window
stimuli = Stimuli(params) #keeps track of stimuli settings and sprites. 

if len(params.contrasts) < 1: #this is set to None by default in PARAMS but loaded by previous params if they exist
    params.contrasts = stimuli.contrasts #set contrasts to the default contrasts in the stimuli class


timer = Timer()
timer.start()

#set up arduino
task_io = ArduinoController('COM7')
task_io.move_spout(270) # this moves spout down bc sometimes when turning on the spout moves and hits the mouse. 



if __name__ == "__main__":
    run_experiment()
