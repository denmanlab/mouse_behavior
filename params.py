import pandas as pd 
import os, json
import datetime
from numpy import save

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
        if not os.path.exists(self.directory): os.makedirs(self.directory)
        self.start_time_string = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.directory = os.path.join(self.directory,self.start_time_string)
        if not os.path.exists(self.directory): os.makedirs(self.directory)                              
        self.filename = os.path.join(self.directory,self.start_time_string+'.csv')

    def init_task_variables(self): 
        #trial variables
        self.trial_running = False 
        self.stimulus_visible = False
        self.trial_start_time = None
        self.stim_on_time = None
        self.rewarded_lick_time = None
        self.lick_detected_during_trial = False
        self.trial_outcome = None
        self.FA_streak = 0
        self.timeout = False
        
        self.last_lick_time = 0 # last lick time -- used to check quiet period
        self.lick_times = [] # list for full lick times 
        self.current_stim = None
        
        self.spout_position = 'up' #up is lickable, down is unlickable

        # stimuli information for data frame (rest is stored in stimuli class)
        self.stim_contrast = None 
        self.orientation = None # not currently implemented
        self.catch = None # catch trials are where contrast is 0
        
        #to be able to modulate
        self.reward_vol = 25 # arbitrary units
        self.min_wait_time = 1 # lower number in np.randint
        self.max_wait_time = 5 # upper number in np.randint
        self.wait_time = None # how long after trial starts before stim is on
        self.quiet_period = 2 #time required of no licking between trials
        self.stim_duration = 2.5 # how long (s) that the stimuli is on
        self.catch_frequency = 1 # number of catch trials to append to the stimuli list
        self.FA_penalty = 5  # number of FAs in a row before timeout 
        self.timeout_duration = 15 # duration of the timeout
        self.autoreward = False
        self.shaping = False

        #buttons = [self.shaping, self.autoreward] #toggles
    
        #dataframe to be saved
        self.trials_df = pd.DataFrame(columns=['trial_number', 
                                                'contrast', 'orientation', 'catch', 
                                                'outcome','false_alarm','rewarded','lapse', 'catch_lapse',
                                                'quiet_period',
                                                'wait_time', 
                                                'trial_start_time','stim_on_time', 'reaction_time',
                                                'autoreward', 'shaping'
                                                ])
    def update_df(self): # called after every trial to update the DF
        self.false_alarm = self.trial_outcome == 'False Alarm'
        self.rewarded = self.trial_outcome == 'Reward'
        self.lapse = self.trial_outcome == 'Lapse'
        
        if self.catch and self.lapse:
            self.catch_lapse = True
            self.lapse = False
        else:
            self.catch_lapse = False

        if self.rewarded:
            reaction_time = self.rewarded_lick_time - self.stim_on_time
        elif self.catch and self.rewarded_lick_time is not None: # if the FA happened after stim-on time
            reaction_time = self.rewarded_lick_time - self.stim_on_time #rewarded lick time is bad name, lick was not rewarded but oh well. 
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
            'catch_lapse': self.catch_lapse,
            'quiet_period': self.quiet_period,
            'wait_time': self.wait_time,
            'trial_start_time': self.trial_start_time,
            'reaction_time': reaction_time,
            'stim_on_time': self.stim_on_time,
            'autoreward': self.autoreward,
            'shaping': self.shaping
        }
        self.trials_df.to_csv(self.filename)
        save(os.path.join(self.directory,'lick_timestamps.npy'), self.lick_times)
        default = lambda o: f"<<non-serializable: {type(o).__qualname__}>>"
        j=json.dumps(self.__dict__,default=default)
        with open(os.path.join(self.directory,'params.json'), "w") as write_file:
            json.dump(j, write_file)
    
    def FA_penalty_check(self):
        ''' Check if the number of false alarms in a row is greater than the FA_penalty'''
        if self.trial_outcome == 'False Alarm':
            self.FA_streak += 1
        else:
            self.FA_streak = 0
        if self.FA_streak > self.FA_penalty:
            return True
        else:
            return False
