import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()

from moving_circle import Circle

# load visual stimuli
class Stimuli():
    def __init__(self, params, 
                 game_window_width, game_window_height, 
                 monitor_window_width, monitor_window_height):
        self.params = params
        
        pyglet.gl.glClearColor(0.5,0.5,0.5,1) # Note that these are values 0.0 - 1.0 and not (0-255).
        self.game_window_width = game_window_width
        self.game_window_height = game_window_height
        self.monitor_window_width = monitor_window_width
        self.monitor_window_height = monitor_window_height
        
        # load static contrast images, variables, and set the sprites
        self.load_contrast_images()
        self.set_contrast_sprites()
        
        # load estim params and estim variables
        self.load_estim_params()
        
        # load in moving circle (maybe need to refine this logic..idk yet)
        self.circle = Circle(self.game_window_width, self.game_window_height)
    
    
    def load_contrast_images(self):
        self.grating_image = pyglet.resource.image('grating.jpg')
        self.grating_image.anchor_x = self.grating_image.width // 2 #center image
        self.grating_image.anchor_x = self.grating_image.width // 2 #center image
        self.blank_image = pyglet.resource.image('grating_0.jpg')
        
        self.grating_images = {'100': pyglet.resource.image('grating_100.jpg'),
                        '80': pyglet.resource.image('grating_80.jpg'),
                        '64': pyglet.resource.image('grating_64.jpg'),
                        '32': pyglet.resource.image('grating_32.jpg'),
                        '16': pyglet.resource.image('grating_16.jpg'),
                        '8' : pyglet.resource.image('grating_8.jpg'),
                        '4' : pyglet.resource.image('grating_4.jpg'),
                        '2' : pyglet.resource.image('grating_2.jpg'),
                        '0' : self.blank_image}
        
        for grating in self.grating_images.values():
            grating.anchor_x = grating.width // 2
            #grating.anchor_y = grating.height // 2
        self.contrasts = list(self.grating_images.keys())
        
    
    def set_contrast_sprites(self):
        ## creates sprite (game window) and sprite 2 (monitor_window)
        
        #game window sprite
        self.sprite = pyglet.sprite.Sprite(self.grating_image, x = 1000, y = 450)
        self.sprite.scale = 4.8
        
        #monitor sprite
        self.sprite2 = pyglet.sprite.Sprite(self.grating_image, x = 200, y = 400)
        self.sprite2.scale = 0.5
        self.sprite2.x = self.monitor_window_width // 2
        self.sprite2.y = self.monitor_window_height // 2
        self.sprite2.anchor_x = self.sprite2.width // 2
        self.sprite2.anchor_y = self.sprite2.height // 2
    
    def update_contrast_image(self, contrast):
        '''
        updates and sets the sprite details for sprite (game window) and sprite2 (monitorwindow)
        contrast is the string key for the image
        '''
        if contrast == '0':
            self.params.catch = True
            #game sprite
            self.sprite.visible = False
            self.sprite.image = self.grating_images[contrast]
            #monitor sprite
            self.sprite2.image = self.grating_images[contrast]
        else: #contrast not zero
            self.params.catch = False
            self.sprite.visible = True
            self.sprite.image = self.grating_images[contrast]
            self.sprite2.image = self.grating_images[contrast]
            
    def load_estim_params(self):
        self.estim_params = {   '-5ua': -5,
                                '5ua': 5,
                                '25ua': 25,
                                '-25ua': -25,
                                '50ua': 50,
                                '-50ua': -50,
                                '100ua': 100,
                                '-100ua': -100}
        self.estim_amps = list(self.estim_params.keys())
        self.estim_label = None
    
    def estim_drawings(self, amp):
        self.params.catch = False
        # for safety, set sprites to be invisible
        self.sprite.visible = False
        self.estim_label = pyglet.text.Label(f'Estim Amp: {amp}', font_name='Arial', font_size=20,
                                      x=self.monitor_window_width // 2, 
                                      y=self.monitor_window_height // 2 - 70,
                                      anchor_x='center')
        

        
        
        
        
            
