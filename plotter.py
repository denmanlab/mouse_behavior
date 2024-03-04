import matplotlib.pyplot as plt
import pyglet
import pandas as pd
import os

pyglet.resource.path = [r'C:\Users\hickm\Documents\github\mouse_behavior\models']#['./models']
pyglet.resource.reindex()
class Plotter():
    def __init__(self,params):
        self.params = params
        self.progress_image = pyglet.resource.image('progress_tmp.png')
        self.progress_image.anchor_x = self.progress_image.width // 2 #center image
        self.sprite_progress = pyglet.sprite.Sprite(self.progress_image, x = 310, y = 0)
        
        self.directory =  r'C:\Users\hickm\Documents\github\mouse_behavior\models'
    
    def update_plots(self, df):
        my_dpi = 82
        f, ax = plt.subplots(2, 2, figsize=(600/my_dpi, 600/my_dpi))
        
        self.plot_rolling_proportion(ax[0][0],df)
        self.plot_cumulative_count(ax[0][1],df)

        df_ = df[~df.shaping]
        if df_.shape[0] > 0:
            self.plot_wait_time_vs_starttime(ax[1][0], df)
            self.plot_wait_time_vs_contrast(ax[1][1], df)
        
        plt.tight_layout()
        f.savefig(os.path.join(self.directory, 'progress.png'))
        f.savefig(os.path.join('./models', 'progress_tmp.png'))
        plt.close('all')

        # Sprite handling
        try: del(self.progress_image)
        except: pass
        
        self.progress_image = pyglet.image.load(os.path.join(self.directory, 'progress.png'))
        self.progress_image.anchor_x = self.progress_image.width // 2  # center image
        self.sprite_progress.scale = 0.8
        self.sprite_progress = pyglet.sprite.Sprite(self.progress_image, x=310, y=0)
    
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
        ax.plot(df[df['rewarded']]['contrast'], df[df['rewarded']]['wait_time'], 'o', color='g', label='rewarded')
        ax.plot(df[df['false_alarm']]['contrast'], df[df['false_alarm']]['wait_time'], 'o', color='orange', label='false alarm')
        ax.plot(df[df['lapse']]['contrast'], df[df['lapse']]['wait_time'], 'o', color='r', label='lapse')
        ax.set_xlabel('contrast')
        ax.set_ylabel('wait time')