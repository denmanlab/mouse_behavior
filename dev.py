
from imgui.integrations.pyglet import create_renderer
import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()
from pyglet.clock import schedule_once, unschedule
import imgui
import threading

from random import randint, choice, uniform


import time
import pandas as pd
import numpy as np
import datetime, os, glob, sys, json

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
from am4100 import AM4100 # type: ignore

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
        if params.task == 'gratings':
           stimuli.sprite.draw()
        elif params.task == 'estim':
            pass
        elif params.task == 'moving_circle':
            stimuli.circle.draw()
            stimuli.circle.move()

@monitor_window.event
def on_draw():
    monitor_window.clear()
    # Draw stimulus if visible
    if params.stimulus_visible:
        if params.task == 'gratings': # its a visual trial
            stimuli.sprite2.draw()
        elif params.task == 'estim': # its an estim trial
            stimuli.estim_label.draw()        
        elif params.task == 'moving_circle':
            stimuli.circle.draw()
            #stimuli.circle.move()

@settings_window.event
def on_draw():
    settings_window.clear()
    imgui.new_frame()

    imgui.begin("Settings", True, flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)

    # Slider for Minimum Wait Time
    changed_min_wait, new_min_wait = imgui.slider_float("Minimum Wait Time", 
                                                        params.min_wait_time, 1.0, 30.0, 
                                                        "%.1f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_min_wait:
        params.min_wait_time = new_min_wait
        print(f'Minimum Wait Time: {params.min_wait_time:.1f}')

    # Slider for Maximum Wait Time
    changed_max_wait, new_max_wait = imgui.slider_float("Maximum Wait Time", 
                                                        params.max_wait_time, 1.0, 30.0, 
                                                        "%.1f", imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_max_wait:
        params.max_wait_time = new_max_wait
        print(f'Maximum Wait Time: {params.max_wait_time:.1f}')

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

    changed_FA_penalty, new_FA_penalty = imgui.slider_int('FA Penalty (11=No Penalty)', params.FA_penalty, 0,12,'%.0f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_FA_penalty:
        
        params.FA_penalty = new_FA_penalty
        print(f'FA Penalty {params.FA_penalty}')
    
    
    changed_timeout_dur, new_timeout_dur = imgui.slider_int('Timeout Duration', params.timeout_duration, 0,30,'%.0f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_timeout_dur:
        
        params.timeout_duration = new_timeout_dur
        print(f'Timeout Duration {params.timeout_duration}')

    changed_shock_duration, new_shock_duration = imgui.slider_float('FA shock duration', params.shock_duration, 0.00,1.00,'%.2f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
    if changed_shock_duration:
        # new_shock_duration = round(new_shock_duration / 0.05) * 0.05
        params.shock_duration = new_shock_duration
        print(f'Shock Duration {params.shock_duration}')
    
    changed_buzzer_volume, new_buzzer_volume_raw = imgui.slider_float('Buzzer Volume', params.buzzer_volume, 0.00, 1.00, '%.2f', imgui.SLIDER_FLAGS_ALWAYS_CLAMP)

    # Scale and snap the value to the nearest increment of 0.05
    new_buzzer_volume = round(new_buzzer_volume_raw / 0.05) * 0.05

    if changed_buzzer_volume:
        
        params.buzzer_volume = new_buzzer_volume
        print(f'Buzzer Volume {params.buzzer_volume:.2f}')

    
    #####BUTTONS
    button_width = 30  
    button_height = 20  

    #### gratings contrast buttons
    if params.GRATINGS_INCLUDED or params.MOVING_CIRCLE_INCLUDED:
        first_button = True
        stimuli.circle.contrasts = [int(contrast) / 100 if contrast != '0' else int(contrast) for contrast in params.contrasts]
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
            stimuli.circle.contrasts = [int(contrast) / 100 if contrast != '0' else int(contrast) for contrast in params.contrasts]

            # Pop the button color style to return to default
            imgui.pop_style_color(1)
    
    
    
    # Determine button colors based on whether the stimuli are included
    gratings_button_color = (0, 0.5, 0) if params.GRATINGS_INCLUDED else (0.5, 0, 0)  # Green if included, red if not
    
    # Push style color for gratings stimuli toggle button
    imgui.push_style_color(imgui.COLOR_BUTTON, *gratings_button_color)
    if imgui.button("Toggle gratings Stimuli"):
        
        params.GRATINGS_INCLUDED = not params.GRATINGS_INCLUDED  # Toggle the boolean
        if params.GRATINGS_INCLUDED:
            #params.contrasts = list(stimuli.grating_images.keys())  # Reset the list to all keys
            print("Gratings stimuli enabled")
        else:
            #params.contrasts = []  # Clear the list
            print("Gratings stimuli disabled")
    imgui.pop_style_color(1)  # Pop the button color style to return to default

    


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

    ## moving cirlce task button
    moving_circle_button_color = (0, 0.5, 0) if params.MOVING_CIRCLE_INCLUDED else (0.5, 0, 0)  # Green if included, red if not
    
    # Push style color for moving circle stimuli toggle button
    imgui.push_style_color(imgui.COLOR_BUTTON, *moving_circle_button_color)
    if imgui.button("Toggle Moving Circle Task"):
        
        params.MOVING_CIRCLE_INCLUDED = not params.MOVING_CIRCLE_INCLUDED  # Toggle the boolean
        if params.MOVING_CIRCLE_INCLUDED:
            stimuli.circle.contrasts = [int(contrast) / 100 if contrast != '0' else int(contrast) for contrast in params.contrasts]
            
            print("Moving Circle stimuli enabled")
        else:
            print("Moving Circle stimuli disabled")
    imgui.pop_style_color(1)  # Pop the button color style to return to default
    
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

    # autoreward
    imgui.same_line()
    button_color = (0, 0.5, 0) if params.autoreward else (0.5, 0, 0) # Dark green if autoreward, dark red if not
    imgui.push_style_color(imgui.COLOR_BUTTON, *button_color)
    if imgui.button(f"AutoReward: {'True' if params.autoreward else 'False'}"):
        
        params.autoreward = not params.autoreward  # Toggle the autoreward state
        print(f'AutoReward: {"On" if params.autoreward else "Off"}')

    imgui.pop_style_color(1)
    
    # timing distribution button
    imgui.same_line()
    if imgui.button(f"Timing Dist: {'Uniform' if params.timing_distribution == 'uniform' else 'Exponential'}"):
        # Toggle between 'uniform' and 'exponential'
        if params.timing_distribution == 'uniform':
            params.timing_distribution = 'exponential'
        else:
            params.timing_distribution = 'uniform'
        
        print(f'Wait time distribution: {params.timing_distribution.capitalize()}')

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
        if params.stimulator_connected:
            stimulator.close_connection()
        pyglet.app.exit()


    elif symbol == pyglet.window.key.R:
        print('R: up')
        task_io.move_spout(160) #this is up and lickable

    elif symbol == pyglet.window.key.T:
        print('T: down')
        task_io.move_spout(140) #this is down and unlickable

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
        
    elif symbol == pyglet.window.key.I: # if somehow it gets out of the game loop, this schedules a new trial
        if params.df_updated == False:
            params.df_updated = True
        setup_trial(params)
            

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
    if (current_time - params.last_lick_time) >= params.quiet_period and not params.timeout and params.df_updated:
        params.df_updated = False #reset this so next setup trial doesn't occur until df saved
        #select_stimuli(params, stimuli)
        select_stimuli2(params, stimuli)
        if params.timing_distribution == 'uniform':
            params.wait_time = uniform(params.min_wait_time, params.max_wait_time)
        else:
            params.wait_time = params.min_wait_time + np.random.exponential(params.max_wait_time / 10.)
        params.trial_running = True
        params.stimulus_visible = False
        params.lick_detected_during_trial = False
        params.trial_outcome = None  # Reset trial outcome
        
        #electrify spout
        if params.FA_penalty == 12: # hack so penalty can be motor down time (0-10), none (11), or shock spout (12)
            pass #electrify_spout(params,task_io)
        
        # Unschedule to avoid overlaps
        unschedule(start_trial)
        unschedule(end_trial)
        
        params.trial_start_time = timer.time
        params.stim_on_time = params.trial_start_time + params.wait_time #this is reset to the actual stim_on_time later if the mouse doens't FA before
        schedule_once(start_trial, params.wait_time, params)
        print(f"Trial Started, wait time is {params.wait_time} seconds.")
        
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
    
    if Params.GRATINGS_INCLUDED and not Params.ESTIM_INCLUDED:
        contrast = choice(contrasts)
        params.stim_contrast = int(contrast)
        amp = None 
        params.estim_amp = None
    if Params.ESTIM_INCLUDED and not Params.GRATINGS_INCLUDED:
        amp = choice(estim_amps)
        params.estim_amp = int(amp.strip('ua'))
        contrast = None
        params.stim_contrast = None
    if Params.ESTIM_INCLUDED and Params.GRATINGS_INCLUDED:
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
        Stimuli.update_contrast_image(contrast)

    elif amp is not None: #that is its an estim trial
        Stimuli.estim_drawings(amp)
        update_estim_params(stimulator, int(amp.strip('ua')))

def select_stimuli2(Params, Stimuli): 
    tasks = []
    if Params.GRATINGS_INCLUDED:
        tasks.append('gratings')
    if Params.ESTIM_INCLUDED:
        tasks.append('estim')
    if Params.MOVING_CIRCLE_INCLUDED:
        tasks.append('moving_circle')
            
    task = choice(tasks)
    print(f'{task} task selected for this trial')
    params.task = task 
    if task == 'gratings':
        contrast = choice(Params.contrasts)
        Params.stim_contrast = int(contrast)
        if contrast == '0':
            params.catch = True
        else:
            params.catch = False
        Stimuli.update_contrast_image(contrast)
        
        # set other task variables to none
        Params.estim_amp = None
        Params.circle_contrast = None
        Params.circle_radius = None
        Params.circle_startx = None
        Params.circle_starty = None
            
    elif task == 'estim':
        amp = choice(Params.estim_amps)
        Params.estim_amp = int(amp.strip('ua'))
        Stimuli.estim_drawings(amp)
        update_estim_params(stimulator, int(amp.strip('ua'))) #updates the stimulator with chosen estim param
        
        #set other task variables to none
        Params.stim_contrast = None
        Params.circle_contrast = None
        Params.circle_radius = None
        Params.circle_startx = None
        Params.circle_starty = None
        Params.catch = False
        
    elif task == 'moving_circle':
        ''' contrast and radius size are chosen randomly in the moving circle class... 
            speed and angle incrementer are static.           
        '''
        Stimuli.circle.reset_position() #update the circle (should be circle.reset_position)
        Params.circle_contrast = Stimuli.circle.contrast
        Params.circle_radius = Stimuli.circle.radius 
        Params.circle_startx = Stimuli.circle.x
        Params.circle_starty = Stimuli.circle.y
        
        #set other task variables to none
        Params.stim_contrast = None
        Params.estim_amp = None

        if Params.circle_contrast == 0:
            print('yes this catch worked')
            Params.catch = True
        else: 
            Params.catch = False
            
def start_trial(dt, params):
    if params.FA_penalty == 12: # hack so penalty can be motor down time (0-10), none (11), or shock spout (12)
        pass #deelectrify_spout(params,task_io) # unelectrify spout
    
    params.stimulus_visible = True
    params.stim_on_time = timer.time #pyglet.clock.get_default().time()
    
    if params.task == 'gratings':
        print(f"Stimulus Contrast {params.stim_contrast} on")
    elif params.task == 'moving_circle':
        print(f'Moving circle: contrast: {params.circle_contrast}, radius: {params.circle_radius}')
    elif params.task == 'estim':    
        print(f'Estim: Amplitude: {params.estim_amp}')
        stimulator.flush_serial_port() # flushes the port so it runs better
        stimulator.send_command_and_read_response('1001 set trigger one')  # trigger the stim!!!
        params.estim_times_software.append(timer.time)

    
    if params.autoreward == True and params.stim_contrast != 0:
        schedule_once(scheduled_reward, 0.1, params, task_io)
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
            if params.FA_penalty == 12: # hack so penalty can be motor down time (0-10), none (11), or shock spout (12)
                unschedule(give_shock)
                schedule_once(give_shock, 0.0, params, task_io)
                
            unschedule(end_trial)
            schedule_once(end_trial,0,params)   
        elif params.stimulus_visible and params.trial_outcome == None:
            if params.catch: # that is stim contrast is off 
                task_io.buzz(volume = params.buzzer_volume) # buzz for an auditory learning cue
                params.trial_outcome = "Catch False Alarm"
                params.rewarded_lick_time = timer.time # rewarded_lick_time is bad variable name for this but its fine. i don't want to create new variable
                print("Catch: Lick detected after 0 Contrast.")

            else:
                params.rewarded_lick_time = timer.time
                params.trial_outcome = "Reward"
                deliver_reward(params, task_io)
                print("Reward: Lick detected after stimulus.")

            params.stimulus_visible = False
            unschedule(start_trial)
            unschedule(end_trial)
            schedule_once(end_trial,0,params)
        
        params.lick_detected_during_trial = True

def end_trial(dt, params):
    params.stimulus_visible = False
    if not params.lick_detected_during_trial:
        params.trial_outcome = "Lapse"
        params.rewarded_lick_time = None
        print("Lapse: No lick detected during the trial.")
    else:
        print(f"Trial outcome: {params.trial_outcome}")
    print("Trial ended")
    
    # Reset trial parameters for the next trial
    params.trial_running = False
    if params.task == 'estim':
        params.estim_params = stimulator.get_params() #track the parameters from the stimulator
        print(params.estim_params)
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
    else:   #schedule setup trial once mouse stops licking (quiet period)
        unschedule(start_trial) #just for safety
        unschedule(end_trial) # just for safety
        schedule_once(lambda dt: setup_trial(params), params.quiet_period)
    
    # Update and save DF
    ## this has caused some lag and I don't want it to mess with timing so trying to add threading
    #params.update_df()
    #plotter.update_plots(params.trials_df)
    pyglet.clock.schedule_once(update_df_and_plots, 0.05)
    
def update_df_and_plots(dt):
    params.update_df()
    plotter.update_plots(params.trials_df)
    params.df_updated = True
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
    if estimometer and timer.time - params.last_estim_dig > 1: 
        current_time = timer.time
        params.estim_times_digital.append(current_time)
        params.last_estim_dig = current_time
        print(f'estim digital event detected:{params.last_estim_dig}')
def electrify_spout(params, task_io):
    if not params.spout_charged:
        task_io.spout_charge_pin.write(1) # set the arduino pin connected to the relay high
        params.spout_charged = True
        print('spout charged for FAs')   
def deelectrify_spout(params, task_io):
    if params.spout_charged:
        task_io.spout_charge_pin.write(0) # set the arduino pin connected to the relay low
        params.spout_charged = False
        print('spout decharged for rewards')

def give_shock(dt, params,task_io):
    electrify_spout(params,task_io)
    time.sleep(params.shock_duration)
    deelectrify_spout(params, task_io)
             
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
        task_io.move_spout(160)
        params.spout_position = 'down'
        print(f"spout {params.spout_position}")
    else: #unlickable
        # move spout up
        task_io.move_spout(140)
        params.spout_position = 'up'
        print(f"spout {params.spout_position}")
            
def run_experiment():
    setup_trial(params)
    # Schedule this function to be called every tick of the event loop
    pyglet.clock.schedule_interval(read_lickometer, 1/1000, params)
    if params.stimulator_connected:
        pyglet.clock.schedule_interval(read_estim_digital_copy, 1/1000, params) 
    pyglet.clock.schedule(timer.update)
    task_io.move_spout(160) # move spout back up to lickable position
    pyglet.app.run()



# Create Params instance with user inputs
params = Params(mouse=mouse_name, weight=mouse_weight) #these variables are set at the top of the script w an input so they occur before drawn windows

# load in rig parameters (things that are rig specific like ports and solenoid measurments) 
        # other things like specific digital lines etc can be used as well in the future
with open('rig_json.json', 'r') as file:
    rig_params = json.load(file)

# create stimulator class
stimulator = AM4100(com_port = rig_params['stimulator_port'])
if stimulator.serial_port == None:
    params.stimulator_connected = False
else:
    params.stimulator_connected = True

plotter = Plotter(params) # plotting functions and tools for performance window
stimuli = Stimuli(params, window.width, window.height, 
                  monitor_window.width, monitor_window.height) #keeps track of stimuli settings and sprites. 

if len(params.contrasts) < 1: #this is set to None by default in PARAMS but loaded by previous params if they exist
    params.contrasts = stimuli.contrasts #set contrasts to the default contrasts in the stimuli class


timer = Timer()
timer.start()

#set up arduino
task_io = ArduinoController(rig_params['arduino_port'])
task_io.move_spout(140) # this moves spout down bc sometimes when turning on the spout moves and hits the mouse. 



if __name__ == "__main__":
    run_experiment()
