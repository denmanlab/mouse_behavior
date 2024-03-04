import pandas as pd 
import os


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
        self.trial_running = False 
        self.stimulus_visible = False
        self.trial_start_time = None
        self.stim_on_time = None
        self.rewarded_lick_time = None
        self.lick_detected_during_trial = False
        self.trial_outcome = None
        
        self.last_lick_time = None # last lick time -- used to check quiet period
        self.lick_times = [] # list for full lick times 
        self.current_stim = None
        

        # stimuli information for data frame (rest is stored in stimuli class)
        self.stim_contrast = None 
        self.orientation = None # not currently implemented
        self.catch = None # catch trials are where contrast is 0
        
        #to be able to modulate
        self.reward_vol = 50 # arbitrary units
        self.min_wait_time = 1 # lower number in np.randint
        self.max_wait_time = 5 # upper number in np.randint
        self.wait_time = None # how long after trial starts before stim is on
        self.quiet_period = 2 #time required of no licking between trials
        self.stim_duration = 5 # how long (s) that the stimuli is on
        self.catch_frequency = 1 # number of catch trials to append to the stimuli list
        
        self.autoreward = False
        self.shaping = False

        #buttons = [self.shaping, self.autoreward] #toggles
    
        #dataframe to be saved
        self.trials_df = pd.DataFrame(columns=['trial_number', 
                                                'contrast', 'orientation', 'catch', 
                                                'outcome','false_alarm','rewarded','lapse',
                                                'quiet_period',
                                                'wait_time', 
                                                'trial_start_time','stim_on_time', 'reaction_time',
                                                'autoreward', 'shaping'
                                                ])
    def update_df(self): # called after every trial to update the DF
        self.false_alarm = self.trial_outcome == 'False Alarm'
        self.rewarded = self.trial_outcome == 'Reward'
        self.lapse = self.trial_outcome == 'Lapse'

        if self.rewarded:
            reaction_time = self.rewarded_lick_time - self.stim_on_time
        else:
            reaction_time = None
        
        new_index = len(self.trials_df)
        # Add a new row at the end of the DataFrame
        self.trials_df.loc[new_index] = {
            'trial_number': new_index + 1,
            'orientation': self.orientation,
            'catch': self.catch,
            'contrast': self.stim_contrast,
            'outcome': self.trial_outcome,
            'false_alarm': self.false_alarm,
            'rewarded': self.rewarded,
            'lapse': self.lapse,
            'quiet_period': self.quiet_period,
            'wait_time': self.wait_time,
            'trial_start_time': self.trial_start_time,
            'reaction_time': reaction_time,
            'stim_on_time': self.stim_on_time,
            'autoreward': self.autoreward,
            'shaping': self.shaping
        }
        #self.trials_df.to_csv(self.path)
        
        # plotting! 
            # create figure
            # subplot 1: Rolling proportion
            # subblot 2: cumulutive counts
            # subplot 3: seconds x wait_time scatter (color coded)
            # subplot 4: stimuli x waittime (color coded)
            # subplot 5: "Success": True Lapses + Rewarded