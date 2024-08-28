import pyglet
from pyglet.window import key
import random
from pyglet import shapes
from pyglet.gl import glClearColor


class Circle:
    def __init__(self, window_width, window_height):
        self.background_color = 0.5
        self.window_width = window_width
        self.window_height = window_height
        self.radii = [100, 200, 300, 400]  # Four different radius sizes
        self.radius = random.choice(self.radii)
        self.x = random.randint(self.radius, self.window_width - self.radius)
        self.y = random.randint(self.radius, (self.window_height - 500) - self.radius) #- self.radius)
        self.speed = 0.5
        self.vx = random.choice([-self.speed, self.speed])  # x vel #do choice
        self.vy = random.choice([-self.speed, self.speed])  # y vel do choice
        self.contrasts = [0, 0.02, 0.04, 0.08, 0.16, 0.32, 0.64, 0.8, 1.0]  # contrasts
        self.set_contrast_color()
        self.start_angle = random.uniform(0, 2 * 3.14159)  # random start angle in radians
        self.lcircle = shapes.Sector(self.x, self.y, self.radius, 
                                     angle=3.14, 
                                     start_angle=self.start_angle, 
                                     color=self.color)
        self.rcircle = shapes.Sector(self.x, self.y, self.radius, 
                                     angle=3.14, start_angle=self.start_angle + 3.14, 
                                     color=(((255-self.color[0]),)*3))
        self.angle_increment = 0.005 # could do a dist of this too but static prob better


    def set_contrast_color(self):
        self.contrast = random.choice(self.contrasts)
        self.int_contrast = int(self.contrast * 100)
        # calculate the color value based on the contrast level
        brightness = self.background_color + (self.contrast * (1 - self.background_color))
        
        brightness = max(0, min(1, brightness))
        self.color = (int(brightness * 255), int(brightness * 255), int(brightness * 255))

        print(self.color)
    
    def draw(self):
        self.lcircle.draw()
        self.rcircle.draw()

    def move(self):
        self.x += self.vx
        self.y += self.vy
        # reverse direction if hitting the boundary
        if self.x - self.radius <= 0 or self.x + self.radius >= self.window_width:
            self.vx = -self.vx
        if self.y - self.radius <= 0 or self.y + self.radius >= self.window_height-500:
            self.vy = -self.vy
        # update  position
        self.lcircle.x = self.x
        self.lcircle.y = self.y
        self.rcircle.x = self.x
        self.rcircle.y = self.y  
        
        # rotate?
        self.start_angle += self.angle_increment
        # ensure the start angle stays within 0 to 2*pi range
        if self.start_angle >= 2 * 3.14159:
            self.start_angle -= 2 * 3.14159
        # update sector positions and start angles
        self.lcircle.start_angle = self.start_angle
        self.rcircle.start_angle = self.start_angle + 3.14      

    def reset_position(self):
        self.radius = random.choice(self.radii)
        self.lcircle.radius = self.radius
        self.rcircle.radius = self.radius
        self.x = random.randint(self.radius, self.window_width - self.radius)
        self.y = random.randint(self.radius, (self.window_height-500) - self.radius)
        self.vx = random.choice([-self.speed,self.speed])
        self.vy = random.choice([-self.speed,self.speed])
        self.set_contrast_color()
        self.int_contrast = int(self.contrast * 100)
        print(self.int_contrast)
        if self.int_contrast == 0:
            self.lcircle.visible = False
            self.rcircle.visible = False
        else: 
            self.lcircle.visible = True
            self.rcircle.visible = True
        
        self.lcircle.color = self.color
        self.lcircle.x = self.x
        self.lcircle.y = self.y
        self.rcircle.color = (((255-self.color[0]),)*3)
        self.rcircle.x = self.x
        self.rcircle.y = self.y
        self.start_angle = random.uniform(0, 2 * 3.14159)
        self.lcircle.start_angle = self.start_angle
        self.rcircle.start_angle = self.start_angle + 3.14
        
        #print(self.color)
        #print((((255-self.color[0]),)*3))