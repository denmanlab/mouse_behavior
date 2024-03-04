import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()

# load visual stimuli
class Stimuli():
    def __init__(self, params):
        self.params = params
        
        pyglet.gl.glClearColor(0.5,0.5,0.5,1) # Note that these are values 0.0 - 1.0 and not (0-255).
        self.grating_image = pyglet.resource.image('grating.jpg')
        self.grating_image.anchor_x = self.grating_image.width // 2 #center image
        self.blank_image = pyglet.resource.image('grating_0.jpg')
        self.grating_image.anchor_x = self.grating_image.width // 2 #center image
        self.grating_images = {'100': pyglet.resource.image('grating_100.jpg'),
                        '80': pyglet.resource.image('grating_80.jpg'),
                        '64': pyglet.resource.image('grating_64.jpg'),
                        '32': pyglet.resource.image('grating_32.jpg'),
                        '16': pyglet.resource.image('grating_16.jpg'),
                        '8' : pyglet.resource.image('grating_8.jpg'),
                        '4' : pyglet.resource.image('grating_4.jpg'),
                        '2' : pyglet.resource.image('grating_4.jpg'),}
        
        self.sprite = pyglet.sprite.Sprite(self.grating_image, x = 600, y = 800)
        self.sprite.scale = 0.8

        self.sprite2 = pyglet.sprite.Sprite(self.grating_image, x = 60, y = 80)
        self.sprite2.scale = 0.04