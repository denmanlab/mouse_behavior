import matplotlib.pyplot as plt
import pyglet
import pandas as pd
import os

pyglet.resource.path = [r'C:\Users\hickm\Documents\github\mouse_behavior\models']#['./models']
pyglet.resource.reindex()
class Plotter():
    def __init__(self,params):
        self.params = params
        #windows widths and heights
        self.window_width = 1000
        self.window_height = 800

        # Load the progress image and create the sprite
        self.progress_image = pyglet.resource.image('progress_tmp.png')
        self.sprite_progress = pyglet.sprite.Sprite(self.progress_image)

        # Set the anchor points to the center of the image
        self.sprite_progress.anchor_x = self.sprite_progress.width // 2
        self.sprite_progress.anchor_y = self.sprite_progress.height // 2

        # Calculate the sprite's position to center it in the window
        self.sprite_progress.x = 10
        self.sprite_progress.y = 10
        self.sprite_progress.scale = 0.8

        self.directory =  r'C:\Users\hickm\Documents\github\mouse_behavior\models'
    
    def update_plots(self, df):
        my_dpi = 82
        f, ax = plt.subplots(3, 2, figsize=(1000/my_dpi, 800/my_dpi))
        
        self.plot_rolling_proportion(ax[0][0],df)
        self.plot_cumulative_count(ax[0][1],df)

        df_ = df[~df.shaping]
        if df_.shape[0] > 0:
            self.plot_wait_time_vs_starttime(ax[1][0], df)
            self.plot_wait_time_vs_contrast(ax[1][1], df)
        
        self.plot_reaction_time_vs_starttime(ax[2][0], df)
        self.plot_recent_trial_outcomes(ax[2][1], df)

        plt.tight_layout()
        f.savefig(os.path.join(self.directory, 'progress.png'))
        f.savefig(os.path.join('./models', 'progress_tmp.png'))
        plt.close('all')

        # Sprite handling
        try: del(self.progress_image)
        except: pass
        
        # Load the progress image and create the sprite
        self.progress_image = pyglet.image.load(os.path.join(self.directory, 'progress.png'))
        self.sprite_progress = pyglet.sprite.Sprite(self.progress_image)

        # Set the anchor points to the center of the image
        self.sprite_progress.anchor_x = self.sprite_progress.width // 2
        self.sprite_progress.anchor_y = self.sprite_progress.height // 2

        # Calculate the sprite's position to center it in the window
        self.sprite_progress.x = 10
        self.sprite_progress.y = 10
        self.sprite_progress.scale = 0.8
    
    def plot_rolling_proportion(self, ax, df):
        ax.plot(df['rewarded'].rolling(10).mean(), 'g', label='rewarded')
        ax.plot(df['false_alarm'].rolling(10).mean(), 'orange', label='false alarm')
        ax.plot(df['lapse'].rolling(10).mean(), 'r', label='lapse')
        ax.set_xlabel('trial')
        ax.set_ylabel('rolling proportion of trials')
        ax.legend()

    def plot_cumulative_count(self, ax,df):
        ax.plot(df['rewarded'].cumsum(), 'g', label='rewarded')
        ax.plot(df['false_alarm'].cumsum(), 'orange', label='false alarm')
        ax.plot(df['lapse'].cumsum(), 'r', label='lapse')
        ax.legend()
        ax.set_xlabel('trial')
        ax.set_ylabel('cumulative count of trials')

    def plot_wait_time_vs_starttime(self, ax, df):
        ax.plot(df[df['rewarded']]['trial_start_time'], df[df['rewarded']]['wait_time'], 'o', color='g', label='rewarded')
        ax.plot(df[df['false_alarm']]['trial_start_time'], df[df['false_alarm']]['wait_time'], 'o', color='orange', label='false alarm')
        ax.plot(df[df['lapse']]['trial_start_time'], df[df['lapse']]['wait_time'], 'o', color='r', label='lapse')
        ax.set_xlabel('seconds')
        ax.set_ylabel('wait time')
    
    def plot_wait_time_vs_contrast(self, ax, df):
        # Plotting for the 'rewarded' condition in green
        ax.plot(df[df['rewarded']]['contrast'], df[df['rewarded']]['wait_time'], 'o', color='g', label='Rewarded')
        
        # Plotting for the 'false_alarm' condition in orange
        ax.plot(df[df['false_alarm']]['contrast'], df[df['false_alarm']]['wait_time'], 'o', color='orange', label='False Alarm')
        
        # Plotting for the 'lapse' condition when contrast is not 0, in red
        ax.plot(df[df['lapse']]['contrast'], df[df['lapse']]['wait_time'], 'o', color='r', label='Lapse')
        
        # Plotting for the 'lapse' condition when contrast is 0, in blue-green
        ax.plot(df[df['catch_lapse']]['contrast'], df[df['catch_lapse']]['wait_time'], 'o', color='cyan', label='Catch Lapse')


        ax.set_xlabel('Contrast')
        ax.set_ylabel('Wait Time')
        ax.legend()


    def plot_reaction_time_vs_starttime(self, ax, df):
        # Filtering and plotting for the 'rewarded = True' condition in green
        rewarded_df = df[df['rewarded'] == True]
        ax.scatter(rewarded_df['trial_start_time'], rewarded_df['reaction_time'], color='g', label='Rewarded')

        # Filtering and plotting for the 'False Alarm = True AND catch = True' condition in yellow
        false_alarm_and_catch_df = df[(df['false_alarm'] == True) & (df['catch'] == True)]
        ax.scatter(false_alarm_and_catch_df['trial_start_time'], false_alarm_and_catch_df['reaction_time'], color='orange', label='False Alarm & Catch')

        ax.set_xlabel('Trial Start Time (seconds)')
        ax.set_ylabel('Reaction Time')
        ax.legend()



    def plot_recent_trial_outcomes(self, ax, df):
        # Assuming df is sorted in ascending order of trials
        last_trials = df.tail(5)  # Get the last 5 trials
        
        # Define outcomes and corresponding colors and markers
        outcomes = ['rewarded', 'false_alarm', 'lapse', 'catch_lapse']
        colors = {'rewarded': 'g', 'false_alarm': 'orange', 'lapse': 'r', 'catch_lapse': 'cyan'}
        markers = {'rewarded': 'o', 'false_alarm': 'o', 'lapse': 'o', 'catch_lapse': 'o'}
        marker_size = 500  # Large marker size for visibility
        
        # The y-value is arbitrary since it doesn't matter for this visualization
        y_value = 1
        
        # Iterate over each of the last trials and plot according to outcome
        for i, trial in enumerate(last_trials.itertuples(index=True), 1):
            for outcome in outcomes:
                if getattr(trial, outcome):  # If the outcome is True for this trial
                    # Plot with specific color and marker
                    # Adjusting the scatter plot position so the most recent is on the right
                    ax.scatter(i, y_value, s=marker_size, color=colors[outcome], label=outcome, marker=markers[outcome])

        # Simplify the plot
        ax.set_yticks([])  # Hide y-axis as it's not meaningful
        # Set x-ticks to correspond to the last 5 trials, with the most recent on the right
        ax.set_xticks(range(1, 6))  
        # Adjust x-tick labels so the most recent trial is labeled "1" and appears on the right
        ax.set_xticklabels(range(5, 0, -1))  
        ax.set_xlabel('Trials from Most Recent')
        
        # To avoid duplicate labels in legend
        handles, labels = ax.get_legend_handles_labels()
        unique_labels = dict(zip(labels, handles))
        ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper left')
        
        ax.set_title('Outcomes of the Last 5 Trials')
            
  
