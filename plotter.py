import matplotlib.pyplot as plt
from matplotlib import gridspec

import pyglet
import pandas as pd
import os
import seaborn as sns
import numpy as np
from scipy.stats import norm

import pendulum
from datetime import datetime
import json

pyglet.resource.path = ['./models']
pyglet.resource.reindex()


class Plotter():
    def __init__(self, params):
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

        try:
            self.directory =  self.params.directory
        except:
            self.directory = self.params['directory']

        self.colors = {
                        'rewarded': '#6a8e7f',
                        'false_alarm': '#f0b67f',
                        'lapse': '#fe6b64',
                        'catch_lapse': '#266dd3',
                        'wait_time': '#03fcf8',
                    }
        plt.style.use(['dark_background', 'seaborn-talk'])
    


    def summary_plots(self, df):
        # set up figure and gridspec
        f = plt.figure(figsize=(15, 20))
        gs = gridspec.GridSpec(8, 3, height_ratios=[2, 2, 3, 0.1, 2, 2, 2.5, 2.5], width_ratios=[5, 2, 2])
        # add main title and subheadings
        mouse_name = self.params['mouse']
        session_directory = self.params['start_time_string']
        f.suptitle(f'Mouse: {mouse_name}', fontsize=28)
        f.text(0.5, 0.94, f'Session Perf: {session_directory}', ha='center',
                fontsize=22, weight = 'bold', style = 'italic')
        f.text(0.5, 0.525, 'Performance Over Last 10 Sessions', ha='center', fontsize=28,
               weight = 'bold', style = 'italic')
        
        f.text(0.05, 0.54, '----Rewarded--', ha = 'left', color = self.colors['rewarded'], 
               fontsize = 20, weight = 'bold')
        f.text(0.05, 0.52, '----False Alarm--', ha = 'left', color = self.colors['false_alarm'], 
               fontsize = 20, weight = 'bold')
        f.text(0.95, 0.54, '----Lapse--', ha = 'right', color = self.colors['lapse'], 
               fontsize = 20, weight = 'bold')
        f.text(0.95, 0.52, '----Catch Lapse--', ha = 'right', color = self.colors['catch_lapse'], 
               fontsize = 20, weight = 'bold')


        ## daily plots! 5 plots (2 left column, 3 right column)
        # First column plots
        ax0 = plt.subplot(gs[0:2, 0])  # This plot spans the first two rows of the first column
        try:
            self.plot_outcomes_by_contrast(ax0, df)
        except:
            print('outcomes by contrast did not work')
        
        ax1 = plt.subplot(gs[2, 0])  
        try:
            self.plot_wait_time_vs_starttime(ax1, df)
        except:
            print('wait times not working')
        # Second column plots,       
        ax2 = plt.subplot(gs[0, 1:3])
        try:
            self.plot_rolling_proportion(ax2, df)
        except:
            print('rolling distributions not working')

        ax3 = plt.subplot(gs[1:3, 1]) 
        try: 
            self.plot_cumulative_count(ax3, df)
            ax3.legend_.remove()
        except:
            print('cumulative counts did not work')
        ax4 = plt.subplot(gs[1:3, 2])  
        try:
            self.plot_reaction_time_vs_starttime(ax4, df)
        except:
            print('reaction time no work')
        ax4.legend_.remove()

        
        ## Summary of recent sessions (currently 10)
        combined_df = self.load_and_combine_dataframes()
        sum0 = plt.subplot(gs[4:6,0])
        try:
            self.plot_detection_curve_percent_correct(sum0, combined_df)
            sum0.set_title('Averaged detection curve')
            sum0.legend_.remove()
        except:
            print('detection curve did not plot')
        
        sum05 = plt.subplot(gs[6:8,0])
        try:
            self.plot_percent_correct_heatmap(sum05, combined_df)
        except:
            print('percent correct by day did not owkr')
        sum05.set_title('% Correct Heatmap by day')
        
        
        sum1 = plt.subplot(gs[4, 1:3])
        try: 
            self.plot_cumulative_counts(combined_df, sum1, 'rewarded')
            self.plot_cumulative_counts(combined_df, sum1, 'false_alarm')
            self.plot_cumulative_counts(combined_df, sum1, 'lapse')
        except:
            print('Oops, Cumulative Outcomes by Day plot didnt work.')
        sum1.set_title('Cumulative Outcomes by Day')
        
        sum2 = plt.subplot(gs[5, 1])
        try:
            self.plot_cumulative_counts(combined_df, sum2, 'false_alarm/rewarded')
        except:
            print('false alarm rate didnt work')
        sum2.set_title('False Alarm Rate')

        sum2half = plt.subplot(gs[5,2])
        try:
            self.plot_mean_wait_time_by_day(sum2half, combined_df)
        except:
            print('mean wait time by day didnt work')
        sum2half.set_title('Mean Wait Time by Day')

        sum4 = plt.subplot(gs[6:8, 1])
        try:
            self.plot_proportions_by_wait_time(sum4, combined_df, num_bins = 10)
        except:
            print('no high contrast waittime proportions')
        sum4.set_title('High contrast waittime props')

        sum5 = plt.subplot(gs[6, 2])
        try:
            self.plot_weight_by_day(sum5, combined_df)
        except:
            print('weight by day didnt plot')
        sum5.set_title('Weight by Day')

        sum6 = plt.subplot(gs[7, 2])
        try:
            self.plot_water_delivered_by_day(sum6, combined_df)
        except:
            print('water delivery by day no work')
        sum6.set_title('Water Delivered by Day')



        plt.tight_layout(rect=[0, 0.03, 1, 0.96]) 
        
        folder = self.params['directory']
        save_str = os.path.join(folder, 'summary_plot.png')
        plt.savefig(save_str)
    

    def update_plots(self, df):
        plt.style.use(['dark_background', 'seaborn-paper'])
        my_dpi = 82
        f = plt.figure(figsize=(1000/my_dpi, 800/my_dpi))
        gs = gridspec.GridSpec(6, 4, figure=f)  # 6 rows, 4 columns

        
        ### Set up axes using GridSpec
        #standard one! 
        if df['ESTIM_INCLUDED'].any(): #if there are any estim trials, change plotting format!
            ## row 1
            #rolling proportions
            ax0 = plt.subplot(gs[0:2, 0:2])
            self.plot_rolling_proportion(ax0, df)
            
            #plot lick rate
            #TODO
            
            #cumuluative counts
            ax1 = plt.subplot(gs[0:2, 2])
            self.plot_cumulative_count(ax1, df)
            
            # detection curves
            ax1_5 = plt.subplot(gs[0:2,3])
            if len(df) > 5:
                try:
                    self.plot_outcomes_by_contrast(ax1_5, df)
                except:
                    print('Unable to plot outcomes by contrast')

            ## row 2
            #outcomes by waittime throughout the session
            ax2 = plt.subplot(gs[2:4, 0:2])
            self.plot_wait_time_vs_starttime(ax2, df)

            #Outcomes by contrast (x) and wait_times (y)
            ax3 = plt.subplot(gs[2, 2:4])
            self.plot_wait_time_vs_contrast(ax3, df, stimuli_type = 'contrast')
            
            #Outcomes by contrast (x) and wait_times (y)
            ax3_5 = plt.subplot(gs[3, 2:4])
            self.plot_wait_time_vs_contrast(ax3_5, df, stimuli_type = 'estim_amp')            

            ## third row
            #reaction times
            ax4 = plt.subplot(gs[4:6, 0])
            self.plot_reaction_time_vs_starttime(ax4, df)
            
            ax4_5 = plt.subplot(gs[4:6, 1:3])
            self.plot_reaction_time_estim(ax4_5, df)
            
            #recent outcomes
            ax5 = plt.subplot(gs[4:6, 3])
            self.plot_recent_trial_outcomes(ax5, df, flip_axes = True)
        else: # only visual stimuli
            ## row 1
            #rolling proportions
            ax0 = plt.subplot(gs[0:2, 0:2])
            self.plot_rolling_proportion(ax0, df)
            #plot lick rate
            #TODO

            #cumuluative counts
            ax1 = plt.subplot(gs[0:2, 2])
            self.plot_cumulative_count(ax1, df)
            
            # detection curves
            ax1_5 = plt.subplot(gs[0:2,3])
            if len(df) > 5:
                try:
                    self.plot_outcomes_by_contrast(ax1_5, df)
                except:
                    print('Unable to plot outcomes by contrast')

            ## row 2
            #outcomes by waittime throughout the session
            ax2 = plt.subplot(gs[2:4, 0:2])
            self.plot_wait_time_vs_starttime(ax2, df)

            #Outcomes by contrast (x) and wait_times (y)
            ax3 = plt.subplot(gs[2:4, 2:4])
            self.plot_wait_time_vs_contrast(ax3, df)
            

            ## third row
            #reaction times
            ax4 = plt.subplot(gs[4:6, 0:2])
            self.plot_reaction_time_vs_starttime(ax4, df)
            
            #recent outcomes
            ax5 = plt.subplot(gs[4:6, 2:4])
            self.plot_recent_trial_outcomes(ax5, df)
        

        plt.tight_layout(rect=[0, 0.03, 1, 0.96]) 
        f.savefig(os.path.join(self.directory, 'progress.png'))
        f.savefig(os.path.join('./models', 'progress_tmp.png'))
        plt.close('all')

        # Sprite handling
        try:
            del(self.progress_image)
        except:
            pass

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
        ax.plot(df['rewarded'].rolling(20).mean(), self.colors['rewarded'])
        ax.plot(df['false_alarm'].rolling(20).mean(), self.colors['false_alarm'])
        ax.plot(df['lapse'].rolling(20).mean(), self.colors['lapse'])
        ax.plot(df['catch_lapse'].rolling(20).mean(), self.colors['catch_lapse'])
        ax.set_xlabel('trial')
        ax.set_ylabel('%')
        ax.set_title('rolling proportions')
        

    def plot_cumulative_count(self, ax,df):
        ax.plot(df['rewarded'].cumsum(), self.colors['rewarded'], label='rewarded')
        ax.plot(df['false_alarm'].cumsum(), self.colors['false_alarm'], label='false alarm')
        ax.plot(df['lapse'].cumsum(), self.colors['lapse'], label='lapse')
        ax.plot(df['catch_lapse'].cumsum(),self.colors['catch_lapse'], label = 'catch_lapse')
        #ax.legend()
        ax.set_xlabel('trial')
        ax.set_ylabel('trial count')
        ax.set_title('cumulative count of trials')

    def plot_wait_time_vs_starttime(self, ax, df):
        # Plot for visual stimuli where contrast is not NaN
        visual_df = df[df['contrast'].notna()]
        ax.plot(visual_df[visual_df['rewarded']]['trial_start_time'], visual_df[visual_df['rewarded']]['wait_time'], 'o', 
                color=self.colors['rewarded'], label='rewarded', markersize=6)
        ax.plot(visual_df[visual_df['false_alarm']]['trial_start_time'], visual_df[visual_df['false_alarm']]['wait_time'], 'X', 
                color=self.colors['false_alarm'], label='false alarm', markersize=6)
        ax.plot(visual_df[visual_df['lapse']]['trial_start_time'], visual_df[visual_df['lapse']]['wait_time'], 'X', 
                color=self.colors['lapse'], label='lapse', markersize=6)
        ax.plot(visual_df[visual_df['catch_lapse']]['trial_start_time'], visual_df[visual_df['catch_lapse']]['wait_time'], 'o', 
                color=self.colors['catch_lapse'], label='catch lapse', markersize=6)

        # Plot for estim trials where contrast is NaN
        estim_df = df[df['contrast'].isna()]
        ax.plot(estim_df[estim_df['rewarded']]['trial_start_time'], estim_df[estim_df['rewarded']]['wait_time'], '*', 
                color=self.colors['rewarded'], label='rewarded (estim)', markersize=6)
        ax.plot(estim_df[estim_df['false_alarm']]['trial_start_time'], estim_df[estim_df['false_alarm']]['wait_time'], '1', 
                color=self.colors['false_alarm'], label='false alarm (estim)', markersize=6)
        ax.plot(estim_df[estim_df['lapse']]['trial_start_time'], estim_df[estim_df['lapse']]['wait_time'], '1', 
                color=self.colors['lapse'], label='lapse (estim)', markersize=6)
        ax.plot(estim_df[estim_df['catch_lapse']]['trial_start_time'], estim_df[estim_df['catch_lapse']]['wait_time'], '*', 
                color=self.colors['catch_lapse'], label='catch lapse (estim)', markersize=6)

        # Adding a secondary y-axis for reaction times
        sec_ax = ax.twinx()
        ax.plot(df[df['false_alarm']]['trial_start_time'], df[df['false_alarm']]['reaction_time'], 'X', 
                    color=self.colors['wait_time'], label='false alarm reaction time', markersize=6)
        sec_ax.spines['right'].set_visible(False)
        sec_ax.set_ylabel('Actual wait time on FA')
        sec_ax.yaxis.label.set_color(self.colors['wait_time'])
        sec_ax.set_yticks([])  # Removes the y-axis ticks
        sec_ax.set_yticklabels([])  # Removes the y-axis tick labels

        ax.set_xlabel('Seconds')
        ax.set_ylabel('Target wait time')
        ax.set_title('Outcomes for wait times throughout session')
        
    def plot_wait_time_vs_contrast(self, ax, df, stimuli_type = 'contrast'):
        # Replace zero contrast with a small non-zero value, such as 1
        df = df.copy()
        df = df.dropna(subset=[stimuli_type])
        if stimuli_type == 'contrast':
            df['contrast'] = df['contrast'].replace(0, 1)
            # Define contrast levels and corresponding ticks for the x-axis
            contrast_levels = [1, 2, 4, 8, 16, 32, 64, 80, 100]
            contrast_labels = ['0', '2', '4', '8', '16', '32', '64', '80', '100']  # Use '0' label for 1
            markers = ['o','X']
        else:
            markers = ['*', '1']

        jitter_amount = 0.05  # Jitter percentage relative to the contrast value

        # Function to add jitter
        def add_jitter(values, amount):
            jitter = np.random.uniform(-amount, amount, size=values.shape) * values
            return values + jitter

        # Adding jitter to contrast values for plotting
        rewarded_contrast_jittered = add_jitter(df[df['rewarded']][stimuli_type], jitter_amount)
        false_alarm_contrast_jittered = add_jitter(df[df['false_alarm']][stimuli_type], jitter_amount)
        lapse_contrast_jittered = add_jitter(df[df['lapse']][stimuli_type], jitter_amount)
        catch_lapse_contrast_jittered = add_jitter(df[df['catch_lapse']][stimuli_type], jitter_amount)
            
        # Plotting for each condition with jitter
        ax.plot(rewarded_contrast_jittered, df[df['rewarded']]['wait_time'], markers[0], 
                color=self.colors['rewarded'], label='Rewarded', alpha=0.75, markersize=6)
        ax.plot(false_alarm_contrast_jittered, df[df['false_alarm']]['wait_time'], markers[1], 
                color=self.colors['false_alarm'], label='False Alarm', alpha=0.75, markersize=6)
        ax.plot(lapse_contrast_jittered, df[df['lapse']]['wait_time'], markers[1], 
                color=self.colors['lapse'], label='Lapse', alpha=0.75, markersize=6)
        ax.plot(catch_lapse_contrast_jittered, df[df['catch_lapse']]['wait_time'], markers[0], 
                color=self.colors['catch_lapse'], label='Catch Lapse', alpha=0.75, markersize=6)

        # Set explicit x-axis ticks and log scale
        if stimuli_type == 'contrast':
            ax.set_xscale('log')
            ax.set_xticks(contrast_levels)
            ax.set_xticklabels(contrast_labels)
            

        ax.set_xlabel(stimuli_type)
        ax.set_ylabel('Wait Time')
        ax.set_title(f'Wait Time by {stimuli_type}')
        #ax.legend()


    def plot_reaction_time_vs_starttime(self, ax, df):
        df = df.copy()
        df = df.dropna(subset=['contrast'])
        # filtering and plotting for the 'rewarded = True' condition in green
        rewarded_df = df[df['rewarded'] == True]
        ax.scatter(rewarded_df['contrast'], rewarded_df['reaction_time'], marker = '+', color=self.colors['rewarded'], label='Rewarded')

        # Filtering and plotting for the 'False Alarm = True AND catch = True' condition in yellow
        false_alarm_and_catch_df = df[(df['false_alarm'] == True) & (df['catch'] == True)]
        ax.scatter(false_alarm_and_catch_df['contrast'], false_alarm_and_catch_df['reaction_time'], marker = 'x', color=self.colors['false_alarm'], label='False Alarm & Catch')

        ax.set_xlabel('Contrast ')
        ax.set_ylabel('Reaction Time')
        ax.set_title('Reaction Times for Stimuli')
        #ax.legend()

    def plot_reaction_time_estim(self, ax, df):
        rewarded_df = df[df['rewarded'] == True]
        ax.scatter(rewarded_df['estim_amp'], rewarded_df['reaction_time'], marker = '+', color=self.colors['rewarded'], label='Rewarded')
        ax.set_xlabel('Amplitude (uA)')
        ax.set_ylabel('Reaction Time')
        ax.set_title('Reaction Times for Stimuli')


    def plot_recent_trial_outcomes(self, ax, df, flip_axes=False):
        if df.shape[0] > 5:
            last_trials = df.tail(5)  # get the last 5 trials

            # Define outcomes and corresponding colors and markers
            outcomes = ['rewarded', 'false_alarm', 'lapse', 'catch_lapse']
            colors = {'rewarded': self.colors['rewarded'], 'false_alarm': self.colors['false_alarm'], 
                    'lapse': self.colors['lapse'], 'catch_lapse': self.colors['catch_lapse']}
            # Adjusting markers based on trial type (visual or estim)
            markers = {'rewarded': {'visual': 'o', 'estim': '*'}, 
                    'false_alarm': {'visual': 'X', 'estim': '1'}, 
                    'lapse': {'visual': 'X', 'estim': '1'}, 
                    'catch_lapse': {'visual': 'o', 'estim': '*'}}
            if flip_axes:
                marker_size = 250
            else:
                marker_size = 500  # Large marker size for visibility

            # The coordinate position, depending on orientation
            fixed_value = 1  

            # Iterate over each of the last trials and plot according to outcome
            for i, trial in enumerate(last_trials.itertuples(index=True), 1):
                trial_type = 'estim' if np.isnan(getattr(trial, 'contrast')) else 'visual'
                for outcome in outcomes:
                    if getattr(trial, outcome):  # If the outcome is True for this trial
                        current_marker = markers[outcome][trial_type]
                        if flip_axes:
                            # Plot vertically
                            ax.scatter(fixed_value, i, s=marker_size, color=colors[outcome], 
                                    label=f"{outcome} ({trial_type})", marker=current_marker)
                        else:
                            # Plot horizontally
                            ax.scatter(i, fixed_value, s=marker_size, color=colors[outcome], 
                                    label=f"{outcome} ({trial_type})", marker=current_marker)

            # Simplify the plot
            if flip_axes:
                ax.set_xticks([])  # Hide x-axis as it's not meaningful for horizontal
                ax.set_yticks(range(1, 6))  # Adjust y-ticks for horizontal orientation
                ax.set_yticklabels(range(5, 0, -1))  # Most recent trial labeled "1" on the top
                ax.set_ylabel('Trials from Most Recent')
            else:
                ax.set_yticks([])  # Hide y-axis as it's not meaningful for vertical
                ax.set_xticks(range(1, 6))  # Adjust x-ticks for vertical orientation
                ax.set_xticklabels(range(5, 0, -1))  # Most recent trial labeled "1" on the right
                ax.set_xlabel('Trials from Most Recent')

            # To avoid duplicate labels in the legend
            handles, labels = ax.get_legend_handles_labels()
            unique_labels = dict(zip(labels, handles))
            #ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper left' if flip_axes else 'upper right')
            if flip_axes:
                ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper left', bbox_to_anchor=(1.05, 1), markerscale = 0.3)
            else:
                ax.legend(unique_labels.values(), unique_labels.keys(), loc='upper right', marker_scale = 0.3)

            ax.set_title('Outcomes of the Last 5 Trials')


            
    def plot_d_prime(self, df, ax, stimuli = 'contrast'):
        # Aggregate trial outcomes by contrast
        grouped = df.groupby('stimuli').agg(
            hits=('rewarded', 'sum'),
            misses=('lapse', 'sum'),
            false_alarms=('false_alarm', 'sum'),
            correct_rejections=('catch_lapse', 'sum')
        ).reset_index()

        # Apply the Hautus correction to calculate hit rates and false alarm rates
        grouped['HR'] = (grouped['hits'] + 0.5) / (grouped['hits'] + grouped['misses'] + 1)
        grouped['FAR'] = (grouped['false_alarms'] + 0.5) / (grouped['false_alarms'] + grouped['correct_rejections'] + 1)

        # Calculate d'
        grouped['d_prime'] = norm.ppf(grouped['HR']) - norm.ppf(grouped['FAR'])

        # Plotting
        ax.plot(grouped['contrast'], grouped['d_prime'], marker='o', linestyle='-', color='b')
        ax.set_xlabel('Contrast Level')
        ax.set_ylabel("d'")
        ax.set_title('d-prime Across Different Contrasts')
    
    
    def plot_outcomes_by_contrast(self, ax, df):
        # convert outcomes to boolean for easy summing/counting
        df_ = df.copy()
        df_['false_alarm'] = df_['false_alarm'] & ~df_['reaction_time'].isna()
        
        # group by 'contrast' and calculate the sum of each outcome
        grouped = df_.groupby('contrast')[['rewarded', 'false_alarm', 'lapse', 'catch_lapse']].sum()

        # filter contrasts with more than 10 trials
        total_trials = grouped.sum(axis=1)
        grouped_filtered = grouped[total_trials > 10]

        # calculate proportions for the filtered DataFrame
        for col in ['rewarded', 'false_alarm', 'lapse', 'catch_lapse']:
            df_[col] = df_[col].astype(bool)
        proportions = {
            'rewarded': [],
            'false_alarm': [],
            'lapse': [],
            'catch_lapse': []
        }
        contrast_index = []
        for contrast, group in grouped_filtered.groupby(level=0):
            if contrast == 0:
                # include 'false_alarm' and 'catch_lapse' for 0 contrast
                outcomes = group[['false_alarm', 'catch_lapse']].sum()
                outcomes['rewarded'] = 0  # set 'rewarded' to 0 for 0 contrast
                outcomes['lapse'] = 0  # set 'lapse' to 0 for 0 contrast
            else:
                # include only 'rewarded' and 'lapse' for other contrasts
                outcomes = group[['rewarded', 'lapse']].sum()
                outcomes['false_alarm'] = 0  # set 'false_alarm' to 0 for other contrasts
                outcomes['catch_lapse'] = 0  # set 'catch_lapse' to 0 for other contrasts

            total = outcomes.sum()
            if total > 0:
                for outcome in ['rewarded', 'false_alarm', 'lapse', 'catch_lapse']:
                    proportions[outcome].append(outcomes[outcome] / total)
            else:
                for outcome in ['rewarded', 'false_alarm', 'lapse', 'catch_lapse']:
                    proportions[outcome].append(0)
            contrast_index.append(contrast)

        # create a DataFrame from the proportions
        proportions_df = pd.DataFrame(proportions, index=contrast_index)

        # plot
        colors = [self.colors['rewarded'], self.colors['false_alarm'], self.colors['lapse'], self.colors['catch_lapse']]
        proportions_df.plot(kind='bar', stacked=True, color=colors, ax=ax)

        ax.set_xlabel('Contrast')
        ax.set_ylabel('Proportion')
        ax.set_title('Detection Curves for Recent Session')

        # hide the legend
        ax.get_legend().set_visible(False)

        # annotate with raw numbers
        for i, contrast in enumerate(proportions_df.index):
            cumulative_height = 0
            for outcome in ['rewarded', 'false_alarm', 'lapse', 'catch_lapse']:
                value = grouped_filtered.loc[contrast, outcome]
                proportion = proportions_df.loc[contrast, outcome]
                if value > 0:
                    y = cumulative_height + proportion / 2
                    ax.text(i, y, str(value), ha='center', va='center', color='w')
                    cumulative_height += proportion



    def plot_cumulative_counts(self, combined_df, ax, measure):
        # sort the DataFrame by session to ensure cumulative counts are correct
        df = combined_df.copy()
        df = df.sort_values(by='day')
        
        colors = {
            'rewarded': '#6a8e7f',
            'false_alarm': '#f0b67f',
            'lapse': '#fe6b64',
            'catch_lapse': '#266dd3'
        }
        
        # assign color for the current measure or use a default palette
        if measure in colors:
            color = colors[measure]


        # calculate and plot cumulative counts or ratios
        if measure == 'reward_vol':
            df['total_volume_rewarded'] = df[df['rewarded'] == 1].groupby('day')['reward_volume'].cumsum()
            sns.lineplot(data=df[df['rewarded'] == 1], x='day', y='total_volume_rewarded', ax=ax, marker='o')
        elif measure == 'false_alarm/rewarded':
            df['false_alarm_cumulative'] = df.groupby('day')['false_alarm'].cumsum()
            df['rewarded_cumulative'] = df.groupby('day')['rewarded'].cumsum()
            df['false_alarm/rewarded_ratio'] = df['false_alarm_cumulative'] / df['rewarded_cumulative'].replace(0, np.nan)
            sns.lineplot(data=df, x='day', y='false_alarm/rewarded_ratio', ax=ax, marker='o')
            ax.set_ylim(0)
            ax.axhline(1, color='gray', linestyle='--')
        else:
            df[measure + '_cumulative'] = df.groupby('day')[measure].cumsum()
            sns.lineplot(data=df, x='day', y=measure + '_cumulative', ax=ax, marker='o', color = color)
            
        ax.set_xlabel('Day')
        ax.set_ylabel('counts')
        ax.set_title(f'Cumulative {measure.capitalize()} Across Days')

        # rotate the x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45)
        plt.tight_layout()

    def plot_cumulative_and_ratio(ax1, combined_df):
        df = combined_df.copy()
        df.sort_values('session', inplace=True)

        # define colors for the various measures
        colors = {
            'rewarded': '#6a8e7f',
            'false_alarm': '#f0b67f',
            'lapse': '#fe6b64',
            'catch_lapse': '#266dd3'
        }
        
        # calculate cumulative counts
        df['rewarded_cumulative'] = df.groupby('day')['rewarded'].cumsum()
        df['false_alarm_cumulative'] = df.groupby('day')['false_alarm'].cumsum()
        df['lapse_cumulative'] = df.groupby('day')['lapse'].cumsum()
        
        # plot cumulative counts for rewards, catches, and false alarms
        sns.lineplot(data=df, x='day', y='rewarded_cumulative', ax=ax1, marker='o', color=colors['rewarded'], label='Rewards')
        sns.lineplot(data=df, x='day', y='false_alarm_cumulative', ax=ax1, marker='o', color=colors['false_alarm'], label='False Alarms')
        sns.lineplot(data=df, x='day', y='lapse_cumulative', ax=ax1, marker='o', color=colors['lapse'], label='Lapses')
        
        # create a second y-axis for the FA/reward ratio
        ax2 = ax1.twinx()
        df['false_alarm_reward_ratio'] = df['false_alarm_cumulative'] / df['rewarded_cumulative'].replace(0, np.nan)
        sns.lineplot(data=df, x='day', y='false_alarm_reward_ratio', ax=ax2, marker='o', color=colors['catch_lapse'], label='FA/Reward Ratio')
        
        # Set labels and title
        ax1.set_xlabel('Day')
        ax1.set_ylabel('Cumulative Count')
        ax2.set_ylabel('False Alarm/Reward Ratio')
        ax1.set_title('Cumulative Metrics and FA/Reward Ratio Across Days')

        # Rotate x-axis labels for better readability
        plt.setp(ax1.get_xticklabels(), rotation=45)

        # Set legend for both axes
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')

        plt.tight_layout()

    def plot_detection_curve_percent_correct(self, ax, combined_df):
        combined_df = combined_df.copy()
        
        # handle zero contrast trials (need to look at false alarms after "stim on")
        combined_df.loc[combined_df['contrast'] == 0, 'false_alarm'] = \
            combined_df['false_alarm'] & ~combined_df['reaction_time'].isna()
        
        # calculate percent correct for nonzero contrasts
        non_zero_contrast = combined_df[combined_df['contrast'] != 0]
        percent_correct_nonzero = non_zero_contrast.groupby(['day', 'contrast']).apply(
            lambda df: df['rewarded'].sum() / (df['rewarded'].sum() + df['lapse'].sum())
        ).reset_index(name='percent_correct')
        
        # calculate percent correct for zero contrast
        zero_contrast = combined_df[combined_df['contrast'] == 0]
        percent_correct_zero = zero_contrast.groupby('day').apply(
            lambda df: df['false_alarm'].sum() / (df['false_alarm'].sum() + df['catch_lapse'].sum())
        ).reset_index(name='percent_correct')
        percent_correct_zero['contrast'] = 0  # Add contrast column to keep consistency
        
        # combine both DataFrames
        percent_correct = pd.concat([percent_correct_nonzero, percent_correct_zero])
        percent_correct.reset_index(drop=True, inplace=True)
        
        # calculate mean and SEM of percent correct by contrast
        summary_stats = percent_correct.groupby('contrast')['percent_correct'].agg(['mean', 'sem']).reset_index()
        
        # generate session colors, ensuring there is a unique color for each session
        unique_sessions = percent_correct['day'].unique()
        session_colors = sns.cubehelix_palette(n_colors=len(unique_sessions), start=2.8, rot=.1, light=0.85, dark=0.35)
        color_dict = dict(zip(unique_sessions, session_colors))

        # bar plot for mean percent correct with confidence interval (CI) for SEM
        sns.barplot(x='contrast', y='mean', data=summary_stats, color='gray', capsize=1, ax=ax)

        # add jitter and use session order for the hue to get a gradient effect
        sns.stripplot(x='contrast', y='percent_correct', data=percent_correct, 
                   jitter=0.20, hue='day', palette=color_dict, size=8, ax=ax, dodge=False)

        # convert contrast to string to avoid numerical spacing on x-axis
        ax.set_xticklabels(summary_stats['contrast'].astype(str), rotation=90)

        ax.set_xlabel('Contrast')
        ax.set_ylabel('Percent Correct')
        


    def plot_percent_correct_heatmap(self, ax, combined_df):
        combined_df = combined_df.copy()
        
        # handle zero contrast uniquely 
        combined_df.loc[combined_df['contrast'] == 0, 'false_alarm'] = \
            combined_df['false_alarm'] & ~combined_df['reaction_time'].isna()
        
        # calculate percent correct for nonzero contrasts
        non_zero_contrast = combined_df[combined_df['contrast'] != 0]
        percent_correct_nonzero = non_zero_contrast.groupby(['day', 'contrast']).apply(
            lambda df: df['rewarded'].sum() / (df['rewarded'].sum() + df['lapse'].sum())
        ).reset_index(name='percent_correct')
        
        # calculate percent correct for zero contrast
        zero_contrast = combined_df[combined_df['contrast'] == 0]
        percent_correct_zero = zero_contrast.groupby('day').apply(
            lambda df: df['false_alarm'].sum() / (df['false_alarm'].sum() + df['catch_lapse'].sum())
        ).reset_index(name='percent_correct')
        percent_correct_zero['contrast'] = 0  # Add contrast column to keep consistency
        
        # combine dfs
        percent_correct = pd.concat([percent_correct_nonzero, percent_correct_zero])
        percent_correct.reset_index(drop=True, inplace=True)
        
        # calculate mean and SEM of percent correct by contrast
        summary_stats = percent_correct.groupby('contrast')['percent_correct'].agg(['mean', 'sem']).reset_index()
        
        # pivot the DataFrame to get 'day' on the y-axis and 'contrast' on the x-axis
        heatmap_data = percent_correct.pivot(index="contrast", columns="day", values="percent_correct")
        
        # reverse the order of the rows to have the top of the y-axis as older and bottom as newer
        heatmap_data = heatmap_data.iloc[::-1]

        # plot the heatmap
        sns.heatmap(heatmap_data, ax=ax, annot=True, fmt=".2f", cmap="RdYlGn", cbar_kws={'label': 'Percent Correct'})

        ax.set_xlabel('Day')
        ax.set_ylabel('Contrast')
        ax.set_title('Percent Correct by Contrast Across Days')

        plt.setp(ax.get_xticklabels(), rotation=45)
        plt.tight_layout()
    
    def plot_proportions_by_wait_time(self, ax, combined_df, num_bins=20):
        # Filter for high contrast trials
        high_contrast_df = combined_df[combined_df['contrast'] >= 32].copy()
        
        # Define bins for wait times
        wait_time_bins = np.histogram(high_contrast_df['wait_time'], bins=num_bins)[1]
        
        # Bin the wait times with precision to ensure alignment
        high_contrast_df['wait_time_bin'] = pd.cut(high_contrast_df['wait_time'], bins=wait_time_bins, precision=1)
        
        # Calculate proportions
        proportions_df = (high_contrast_df.groupby('wait_time_bin')['outcome']
                        .value_counts(normalize=True)
                        .rename('proportion')
                        .reset_index())
        
        # Pivot for plotting
        proportions_pivot = proportions_df.pivot(index='wait_time_bin', columns='outcome', values='proportion').fillna(0)
        
        # Plot a stacked bar chart
        bar_plot = proportions_pivot.plot(kind='bar', stacked=True, ax=ax,
                            color=['#f0b67f', '#fe6b64', '#6a8e7f'])
        
        # Set axis labels and title
        ax.set_xlabel('Wait Time Bins')
        ax.set_ylabel('Proportion of Outcomes')
        ax.set_title('Proportions of Outcomes by Wait Time Bins for High Contrast Trials')
        
        # Remove default legend
        ax.legend_.remove()
        
        # Customize x-axis labels to round to nearest 0.1
        rounded_labels = [f'{interval.left:.1f} - {interval.right:.1f}' for interval in proportions_pivot.index]
        bar_plot.set_xticklabels(rounded_labels, rotation=45)  # Assign labels directly to the bar plot
        
        # Ensure layout fits the plot
        plt.tight_layout()

    def plot_mean_wait_time_by_day(self,ax,combined_df):
        # Group by 'session' which should be a datetime and calculate mean and sem of wait times
        df = combined_df.copy()
        
        daily_stats = df.groupby('day')['wait_time'].agg(['mean', 'std']).reset_index()
        daily_stats.sort_values('day', inplace=True)

        # Plotting the mean wait time by day with a shaded error band
        ax.plot(daily_stats['day'], daily_stats['mean'], '-o', color='dodgerblue')
        ax.fill_between(daily_stats['day'], 
                        daily_stats['mean'] - daily_stats['std'], 
                        daily_stats['mean'] + daily_stats['std'], 
                        color='dodgerblue', alpha=0.3)

        # Formatting the plot
        ax.set_xlabel('Day')
        ax.set_ylabel('wait time')
        ax.set_title('')


        # Rotate the x-axis labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45)

        # Ensure layout is tight so labels are not cut off
        plt.tight_layout()

        # Add the legend
        ax.legend()

    
    def plot_weight_by_day(self, ax, combined_df):
        # get the weights for each day (each day will have redundant information)
        # deal with np.nans from when i previously didn't record weights
        # plot line graph 
        df = combined_df.copy()
        df = df.dropna(subset=['weight'])
        df = df.sort_values('day')
        sns.lineplot(data=df, x='day', y='weight', ax=ax, marker='o')
        ax.set_xlabel('')
        ax.set_ylabel('Weight (g)')
        ax.set_title('Weight by Day')
        plt.setp(ax.get_xticklabels(), rotation=45)
    
    def plot_water_delivered_by_day(self, ax, combined_df):
        # Filter only the rewarded trials before any processing
        rewarded_df = combined_df[combined_df['rewarded'] == True]

        # Calculate the total water delivered per day and remove days with zero volume
        daily_water = rewarded_df.groupby('day')['reward_volume'].sum()
        daily_water = daily_water[daily_water > 0]

        # Plot the sum of reward volume per day
        sns.lineplot(data=daily_water, ax=ax, marker='o')
        ax.set_title('Water Delivered')
        ax.set_xlabel('Day')
        ax.set_ylabel('time sol open (ms)')
        plt.setp(ax.get_xticklabels(), rotation=45)
        

    def load_and_combine_dataframes(self, base_path = None):
        if base_path is None:
            base_path = os.path.dirname(self.params['directory'])
        # List directories and sort them by parsing each as a pendulum instance
        sorted_dir_names = sorted(next(os.walk(base_path))[1], key=lambda x: pendulum.from_format(x, 'YYYY-MM-DD_HH-mm-ss'))

        # Take the 10 most recent directories or if less than 10 all the most recents. 
        recent_dirs = sorted_dir_names[-10:] if len(sorted_dir_names) >= 10 else sorted_dir_names

        all_data = []  # List to store individual session dataframes
        params_list = []  # List to store params from each session

        # Loop over the recent directories and load the contents
        for dir_name in recent_dirs:
            dir_path = os.path.join(base_path, dir_name)
            csv_path = os.path.join(dir_path, dir_name + ".csv")
            json_path = os.path.join(dir_path, "params.json")

            # Load the DataFrame from CSV
            df = pd.read_csv(csv_path)
            df['session'] = dir_name  # Add the session folder name as a new column
            all_data.append(df)

            # Load the params from JSON
            with open(json_path, 'r') as file:
                params = json.load(file)
            params_list.append(params)
            
            # Get weight if available, or use np.nan if not
            #check if params is a string, if so convert to a dictionary
            if isinstance(params, str):
                params = json.loads(params)
            weight = float(params.get('weight', np.nan))
            df['weight'] = weight 

        # Combine all DataFrames into one
        combined_df = pd.concat(all_data, ignore_index=True)
        def convert_date_string(date_str):
            dt_obj = datetime.strptime(date_str, '%Y-%m-%d_%H-%M-%S')
            return dt_obj.strftime('%b%d')  # Example: 'Apr03'

        # Apply the function to every row in the 'session' column
        combined_df['day'] = combined_df['session'].apply(lambda x: convert_date_string(x))


        return combined_df