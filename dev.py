


from imgui.integrations.pyglet import create_renderer
import pyglet
from random import randint, choice
from pyglet.clock import schedule_once, unschedule
import imgui
import pandas as pd

class Params:
    def __init__(self):
        self.stimuli = ['red', 'blue'] #ToDO: replace this with real stimuli! 
        self.trial_running = False
        self.stimulus_visible = False
        self.stim_on_time = None
        self.lick_detected_during_trial = False
        self.last_lick_time = None # last lick time -- used to check quiet period
        self.lick_times = [] # list for full lick times 
        self.current_stim = None
        self.batch = pyglet.graphics.Batch()
        self.stimulus_rect = pyglet.shapes.Rectangle(x=350, y=250, width=100, height=100, color=(255, 255, 255), batch=self.batch)
        self.reward_vol = 50


        
        self.min_wait_time = 1
        self.max_wait_time = 5
        self.quiet_period = 2 #time required of no licking between trials
        self.trial_outcome = None
        
        self.autoreward = False
        self.shaping = False
        # settings lists to be updated with ImGUI
        self.sliders = [self.min_wait_time, self.max_wait_time, self.quiet_period, self.reward_vol]
        #buttons = [self.shaping, self.autoreward] #toggles
        
        #dataframe to be saved
        self.trials_df = pd.DataFrame(columns=['Trial Number', 'Stimulus', 'Outcome', 'Stimulus Visible', 'Lick Detected', 'Trial Start Time', 'Last Lick Time'])
        def update_df(self): # called after every trial to update the DF
            new_index = len(params.trials_df)
            # Add a new row at the end of the DataFrame
            self.trials_df.loc[new_index] = {
                'Trial Number': new_index + 1,
                'Stimulus': self.current_stim,
                'Outcome': self.trial_outcome,
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
        
# Default settings (now part of Params)
params = Params()

#Windows! 
#main window
window = pyglet.window.Window(width=800, height=600, caption="Experiment Window")

#settings
imgui.create_context() # Initialize ImGui context
settings_window = pyglet.window.Window(width = 500, height = 216, caption = "Settings")
settings_window.set_location(100,100)
imgui_renderer = create_renderer(settings_window)
# plotting window


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

    # Begin a new ImGui window
    imgui.begin("Settings", True, flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)

    # Sliders for settings 
    slider_names = ['Minimum Wait Time', 'Maximum Wait Time', 'Quiet Period (ITI w no licking)', 'Reward volume']
    for slider, slider_name in zip(params.sliders, slider_names):
        changed, new_value = imgui.slider_int(slider_name, 
                                                params.min_wait_time, 1, 100 if slider_name == 'Reward volume' else 30, 
                                                "%.0f",
                                                imgui.SLIDER_FLAGS_ALWAYS_CLAMP)
        if changed: 
            slider = new_value
            print(f'{slider_name} {slider}')

    #buttons = [self.shaping, self.autoreward] #toggles

    # TODO: Make sure the min/max settings are logically consistent


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
        lickometer_read = True
        schedule_once(lickometer_read = False, 0.1)
        #check_lick(params)
    elif symbol == pyglet.window.key.ESCAPE:
        pyglet.app.exit()
    elif symbol == pyglet.window.key.D:
        #dispense(reward_vol)

def setup_trial(params):
    if params.trial_running:  # Check if a trial is already running
        return  # Exit if a trial is in progress
    
    current_time = pyglet.clock.get_default().time()
    if params.last_lick_time is None or (current_time - params.last_lick_time) >= params.quiet_period:
        params.current_stim = choice(params.stimuli)
        wait_time = randint(params.min_wait_time, params.max_wait_time)
        params.trial_running = True
        params.stimulus_visible = False
        params.lick_detected_during_trial = False
        params.trial_outcome = None  # Reset trial outcome
        print(f"Trial starting now with {params.current_stim}, wait time is {wait_time} seconds.")
        
        # Unschedule to avoid overlaps
        unschedule(start_trial)
        unschedule(end_trial)
        
        schedule_once(start_trial, wait_time, params)
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
    params.stim_on_time = pyglet.clock.get_default().time()
    print(f"Stimulus {params.current_stim} on")
    if params.autoreward: 
        # dispense
    schedule_once(end_trial, 5, params)

def check_lick(params): 
    params.last_lick_time = pyglet.clock.get_default().time()
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
        else:
            print("Lick")
        params.lick_detected_during_trial = True

def end_trial(dt, params):
    if not params.lick_detected_during_trial:
        params.trial_outcome = "Lapse"
        print("Lapse: No lick detected during the trial.")
    else:
        print(f"Trial outcome: {params.trial_outcome}")
    print("Trial ended")


    # Append trial data to the DataFrame
    params.update_df()

    
    # Reset trial parameters for the next trial
    params.trial_running = False
    params.stimulus_visible = False
    unschedule(start_trial)
    unschedule(end_trial)
    schedule_once(lambda dt: setup_trial(params), params.quiet_period)


def run_experiment():
    setup_trial(params)
    pyglet.app.run()

if __name__ == "__main__":
    run_experiment()
