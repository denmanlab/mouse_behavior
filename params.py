import os, datetime, json
import matplotlib.pyplot as plt
import pyglet
import pandas as pd
import numpy as np


class Params:
    """Class to hold parameter states for a behavioral experiment, including a buffer for the live camera view and various task variables."""

    def __init__(self, mouse='test'):
        self.mouse = mouse
        self.setup_directories()
        self.init_task_variables()
        self.load_previous_session_params()
        self.setup_camera_view()

    def setup_directories(self):
        """Setup base and specific session directories."""
        self.basepath = r'C:\data\behavior'
        self.directory = os.path.join(self.basepath, str(self.mouse))
        os.makedirs(self.directory, exist_ok=True)

        self.start_time_string = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.directory = os.path.join(self.directory, self.start_time_string)
        os.makedirs(self.directory, exist_ok=True)

        self.filename = os.path.join(self.directory, f"{self.start_time_string}.csv")

    def init_task_variables(self):
        """Initialize default values for task-related variables."""
        self.iti = np.random.uniform(3,15)
        self.WAIT_TIME_WINDOW = 2.5

       
        self.answer = None # setup trial sets this to left or right to determine stim orientation

        self.time_ = 0.0
        self.last_end_time = 0.0
        self.stim_on = False
        
        # Additional default settings
        self.SHAPING = False
        self.AUTOREWARD = False
        self.SPOUT_LOCK = False
        self.SHOW_CAMERA = False
       
        self.PLAY_TRIAL_SOUND = True

        self.progress_image = pyglet.resource.image('progress_tmp.png')
        self.progress_image.anchor_x = self.progress_image.width // 2
        self.sprite_progress = pyglet.sprite.Sprite(self.progress_image, x=310, y=0)
        


        self.not_licking = True # what the fck does this do
        self.licked_on_this_trial = False
        
        #stuff for tracking performance in task
        self.FA_max_count = 5 # how many FAs before a timeout. 
        #TODO: not currently working fix this. 
        self.FA_count = 0 # how many FAs since the last timeout. this resets if correct rate is > 50%

        self.sprite = sprite
        
        # Initialize lists for storing trial data
        self.init_lists()

    def init_lists(self):
        """Initialize lists for storing dynamic task and trial data."""
        self.stim_contrast = []
        self.stim_orientation = []
        self.stim_spatial_frequency = []
        self.stim_delay = []
        self.trial_start_time = []
        self.stim_on_time = []
        self.stim_off_time = []
        self.stim_reaction_time = [] #TODO make this work. currently -1
        self.stim_rewarded = []
        self.stim_reward_amount = [] #not accurate. need to make reward amount consistent variable
        self.reward_time = []
        self.trial_AUTOREWARDED = []
        
        self.spout_positions = []
        self.spout_timestamps = []
        
        self.trialendtime = []
        self.shaping = []

        self.falsealarm = []
        self.lapse = []
        self.lick_values = []
        self.lick_timestamps = []


    def load_previous_session_params(self):
        """Load parameters from the last session, if available."""
        try:
            sessions = sorted(os.listdir(os.path.dirname(self.directory)))
            yesterday_directory = sessions[-2]  # Second to last should be yesterday
            with open(os.path.join(os.path.dirname(self.directory), yesterday_directory, 'params.json'), 'rb') as f:
                yesterday_params = json.load(f)
            self.shaping_wait_time = yesterday_params.get('shaping_wait_time', 1.0)  # Default to 1 second
            self.SHAPING = yesterday_params.get('SHAPING', False)
            # Load additional parameters as needed...
        except Exception as e:
            self.shaping_wait_time = 1.0
            print("Defaulting to start parameters due to error:", e)

    def setup_camera_view(self):
        """Setup the buffer for the live camera view."""
        self.WIDTH = 532
        self.HEIGHT = 384
        self.RGB_CHANNELS = 3
        self.IMG_FORMAT = 'RGB'
        self.pitch = self.WIDTH * self.RGB_CHANNELS
        screen = np.zeros([self.HEIGHT, self.WIDTH, self.RGB_CHANNELS], dtype=np.uint8)
        self.image_data = pyglet.image.ImageData(self.WIDTH, self.HEIGHT, self.IMG_FORMAT, screen.tobytes(), pitch=self.pitch)


        #======================================

    def save_params(self):
        # Save trial data to CSV
        df = pd.DataFrame(list(zip(self.stim_contrast, self.stim_orientation, self.stim_spatial_frequency,
                                self.stim_delay, self.trial_start_time, self.stim_on_time, self.stim_off_time,
                                self.stim_reaction_time, self.stim_rewarded, self.stim_reward_amount, self.reward_time,
                                self.trial_AUTOREWARDED, self.trial_ONSET_REWARD, self.falsealarm, self.lapse, self.trialendtime, self.shaping)),
                        columns=['Contrast', 'Orientation', 'Spatial Frequency',
                                'Delay', 'trialstarttime', 'stimontime', 'stimofftime',
                                'reactiontime', 'rewarded', 'rewardamount', 'rewardtime',
                                'AUTOREWARD', 'ONSET_REWARD', 'falsealarm', 'lapse', 'trialendtime', 'SHAPING'])
        try:
            df.to_csv(self.filename)
            self.df = df
            self.plot_to_be_updated = True  # Use self to reference instance variable
            
            # Save lick timestamps and spout positions to .npy files
            np.save(os.path.join(self.directory, 'lick_timestamps.npy'), self.lick_timestamps)
            np.save(os.path.join(self.directory, 'spout_positions.npy'), self.spout_positions)
            np.save(os.path.join(self.directory, 'spout_timestamps.npy'), self.spout_timestamps)
            
            # Serialize class attributes to JSON
            default = lambda o: f"<<non-serializable: {type(o).__qualname__}>>"
            class_dict = {k: v for k, v in self.__dict__.items() if not k.startswith('__') and not callable(v)}
            with open(os.path.join(self.directory, 'params.json'), "w") as write_file:
                json.dump(class_dict, write_file, default=default)
        except Exception as e:
            print(f"Error saving parameters: {e}")
    def update_session_performance(self):
        self.update_false_alarm_count()
        self.calculate_percent_correct()
        if self.SHAPING:
            self.adjust_shaping_wait_time()
        self.shaping_wait_times.append(self.shaping_wait_time)
        self.update_plots()

    def update_false_alarm_count(self):
        try:
            if np.array(self.df.tail(1).stimontime)[-1] == -1:
                self.FA_count += 1
        except Exception as e:
            print(f"Error updating FA count: {e}")
        if self.df.shape[0] > 6 and self.df.tail(6).rewarded.mean() > 0.48:
            self.FA_count = 0

    #worthless get rid of this
    def calculate_percent_correct(self):
        self.percent_correct = self.df[~self.df.AUTOREWARD & ~self.df.ONSET_REWARD].rewarded.mean()

    def adjust_shaping_wait_time(self):
        # Simplified for readability; encapsulates the logic for adjusting shaping wait time
        pass  # Implement your shaping logic here

    def update_plots(self):
        dpi = 82
        fig, ax = plt.subplots(2, 2, figsize=(600/dpi, 600/dpi), dpi=dpi)

        # First subplot: Rolling proportion of trials
        self.plot_rolling_proportion(ax[0][0])

        # Second subplot: Cumulative count of trials
        self.plot_cumulative_counts(ax[0][1])

        # Third subplot: Delay vs. Time for non-shaping trials
        self.plot_delay_vs_time(ax[1][0])

        # Fourth subplot: Delay vs. Contrast for non-shaping trials
        self.plot_delay_vs_contrast(ax[1][1])

        plt.tight_layout()
        fig_path = os.path.join(self.directory, 'progress.png')
        fig.savefig(fig_path)
        fig.savefig(os.path.join('./models', 'progress_tmp.png'))
        plt.close(fig)

        # Update the sprite for the Pyglet window
        self.update_progress_sprite(fig_path)

    def plot_rolling_proportion(self, axis):
        # Using rolling window to calculate means
        rolling_window = 10  # Define your rolling window size
        self.df['rewarded'].rolling(rolling_window, min_periods=1).mean().plot(ax=axis, color='g', label='rewarded')
        self.df['falsealarm'].rolling(rolling_window, min_periods=1).mean().plot(ax=axis, color='orange', label='false alarm')
        self.df['lapse'].rolling(rolling_window, min_periods=1).mean().plot(ax=axis, color='r', label='lapse')
        axis.set_xlabel('Trial')
        axis.set_ylabel('Rolling Proportion')
        axis.legend()

    def plot_cumulative_counts(self, axis):
        self.df['rewarded'].cumsum().plot(ax=axis, color='g', label='rewarded')
        self.df['falsealarm'].cumsum().plot(ax=axis, color='orange', label='false alarm')
        self.df['lapse'].cumsum().plot(ax=axis, color='r', label='lapse')
        axis.set_xlabel('Trial')
        axis.set_ylabel('Cumulative Count')
        axis.legend()

    def plot_delay_vs_time(self, axis):
        df_ = self.df[~self.df['SHAPING']]
        if not df_.empty:
            axis.scatter(df_[df_['rewarded']]['trialstarttime'], df_[df_['rewarded']]['Delay'], color='g', label='rewarded')
            axis.scatter(df_[df_['falsealarm']]['trialstarttime'], df_[df_['falsealarm']]['Delay'], color='orange', label='false alarm')
            axis.scatter(df_[df_['lapse']]['trialstarttime'], df_[df_['lapse']]['Delay'], color='r', label='lapse')
            axis.set_xlabel('Seconds')
            axis.set_ylabel('Wait Time')
            axis.legend()

    def plot_delay_vs_contrast(self, axis):
        df_ = self.df[~self.df['SHAPING']]
        if not df_.empty:
            axis.scatter(df_[df_['rewarded']]['Contrast'], df_[df_['rewarded']]['Delay'], color='g', label='rewarded')
            axis.scatter(df_[df_['falsealarm']]['Contrast'], df_[df_['falsealarm']]['Delay'], color='orange', label='false alarm')
            axis.scatter(df_[df_['lapse']]['Contrast'], df_[df_['lapse']]['Delay'], color='r', label='lapse')
            axis.set_xlabel('Contrast')
            axis.set_ylabel('Wait Time')
            axis.legend()
    
    def update_progress_sprite(self, image_path):
        try:
            progress_image = pyglet.image.load(image_path)
            progress_image.anchor_x = progress_image.width // 2
            self.sprite_progress.scale = 0.8
            self.sprite_progress = pyglet.sprite.Sprite(progress_image, x=310, y=0)
        except Exception as e:
            print(f"Error updating progress sprite: {e}")






## task functions
    def is_new_trial_ready(self):
        # Placeholder for checking if a new trial setup is needed
        # Return True if a new trial needs to be set up, False otherwise
        return not self.new_trial_setup

    def draw_stimulus(self):
        # Code to draw the stimulus if stim_on is True
        if self.stim_on:
            self.sprite.draw()

    def should_setup_trial(self):
        # Determine if it's time to set up a new trial based on ITI and other conditions
        # Example condition: Check if the ITI has passed since the last lick
        if len(self.stim_delay) > 0 and (self.current_time() - self.lick_timestamps[-1] > self.iti + 0.5):
            return True
        return False

    def setup_trial(self):
        # Placeholder for trial setup logic
        # This would typically involve resetting trial-specific parameters, selecting stimuli, etc.
        print("Setting up trial...")  # Placeholder action
        self.new_trial_setup = True

    def is_time_for_new_trial(self):
        # Check if the current time exceeds the start time of the last trial + ITI
        return self.current_time() > self.trial_start_time[-1] + self.iti

    def start_new_trial(self):
        # Logic to start a new trial
        print("Starting new trial...")  # Placeholder action
        self.in_trial = True
        self.new_trial_setup = False


## 
        
    def check_for_false_alarm(self):
        # Check for licks that occur before the stimulus onset, indicating a false alarm
        # This method would return True if a false alarm lick is detected, False otherwise
        return False  # Placeholder return value

    def handle_false_alarm(self):
        # Handle the logic when a false alarm lick is detected
        print("Handling false alarm...")  # Placeholder action

    def is_time_for_stimulus(self):
        # Check if it's the correct time to display the stimulus based on trial timing
        return False  # Placeholder return value

    def activate_stimulus(self):
        # Activate the stimulus, setting stim_on to True and recording the time
        print("Activating stimulus...")  # Placeholder action
        self.stim_on = True


## 
    def check_and_handle_shaping_or_reward(self):
        # Check conditions for shaping or rewarding and handle accordingly
        # This might involve adjusting wait times, dispensing rewards, etc.
        print("Checking and handling shaping or reward...")  # Placeholder action

    def should_end_trial(self):
        # Determine if the trial should end based on current conditions
        # For example, this could check if the stimulus has been on for a certain duration
        return False  # Placeholder return value

    def end_trial(self):
        # Handle the ending of a trial, including resetting parameters and preparing for the next trial
        print("Ending trial...")  # Placeholder action
        self.stim_on = False
        self.in_trial = False