import pyglet
from pyglet.window import key
import random
from pyglet import shapes
from pyglet.gl import glClearColor
import pandas as pd

# background color (mid grey)
background_color = 0.5

# Create a window
window = pyglet.window.Window(800, 600)
glClearColor(background_color, background_color, background_color, 1)  # Set background color to grey


def log_trial_data():
    # Append new data to the DataFrame
    new = pd.DataFrame([{'radius': circle.radius, 
                         'contrast': circle.contrast,
                         'start_angle': circle.start_angle,
                         'end_x': circle.x,
                         'end_y': circle.y,
                         'vx': circle.vx,
                         'vy': circle.vy,
                         'angle_increment': circle.angle_increment,
                         'success': circle.success}])
    circle.trial_data = pd.concat([circle.trial_data, new], ignore_index=True)
    # Save to CSV
    circle.trial_data.to_csv('trial_data.csv', index=False)



# circle properties
class Circle:
    def __init__(self):
        self.trial_data = pd.DataFrame(columns=['radius' 
                                                'contrast'
                                                'start_angle'
                                                'end_x'
                                                'end_y'
                                                'vx'
                                                'vy'
                                                'angle_increment'
                                                'success'])
        
        self.radii = [25, 50, 100, 200]  # Four different radius sizes
        self.radius = random.choice(self.radii)
        self.x = random.randint(self.radius, window.width - self.radius)
        self.y = random.randint(self.radius, window.height - self.radius)
        self.speed = 2
        self.vx = random.uniform(-self.speed, self.speed)  # x vel
        self.vy = random.uniform(-self.speed, self.speed)  # y vel
        self.contrasts = [0.08, 0.32, 0.64, 1.0]  # contrasts
        self.set_contrast_color()
        self.start_angle = random.uniform(0, 2 * 3.14159)  # random start angle in radians
        self.lcircle = shapes.Sector(self.x, self.y, self.radius, 
                                     angle=3.14, 
                                     start_angle=self.start_angle, 
                                     color=self.color)
        self.rcircle = shapes.Sector(self.x, self.y, self.radius, 
                                     angle=3.14, start_angle=self.start_angle + 3.14, 
                                     color=(((255-self.color[0]),)*3))
        self.angle_increment = 0.01 # could do a dist of this too but static prob better
        self.visible = True
        self.success = None

    def set_contrast_color(self):
        self.contrast = random.choice(self.contrasts)
        
        # calculate the color value based on the contrast level
        # is this contrast? lol
        brightness = background_color + (self.contrast * (1 - background_color))
        
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
        if self.x - self.radius <= 0 or self.x + self.radius >= window.width:
            self.vx = -self.vx
        if self.y - self.radius <= 0 or self.y + self.radius >= window.height:
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
        self.x = random.randint(self.radius, window.width - self.radius)
        self.y = random.randint(self.radius, window.height - self.radius)
        self.vx = random.choice([-self.speed,self.speed])
        self.vy = random.choice([-self.speed,self.speed])
        self.set_contrast_color()
        self.lcircle.color = self.color
        self.lcircle.x = self.x
        self.lcircle.y = self.y
        self.rcircle.color = (((255-self.color[0]),)*3)
        self.rcircle.x = self.x
        self.rcircle.y = self.y
        self.start_angle = random.uniform(0, 2 * 3.14159)
        self.lcircle.start_angle = self.start_angle
        self.rcircle.start_angle = self.start_angle + 3.14
        print(self.color)
        print((((255-self.color[0]),)*3))

# init circle
circle = Circle()

def update(dt):
    if circle.visible:
        circle.move()

@window.event
def on_key_press(symbol, modifiers):
    if symbol == key.SPACE:
        circle.visible = False
        circle.success = True
        log_trial_data()
        pyglet.clock.unschedule(hide_circle)
        delay = random.uniform(0.5, 3) 
        pyglet.clock.schedule_once(show_circle, delay)

def show_circle(dt):
    circle.visible = True
    circle.reset_position()
    pyglet.clock.schedule_once(hide_circle, 1)  
    

def hide_circle(dt):
    pyglet.clock.unschedule(hide_circle)
    pyglet.clock.unschedule(show_circle)
    circle.visible = False
    circle.success = False
    log_trial_data()
    delay = random.uniform(0.5, 3)  
    pyglet.clock.schedule_once(show_circle, delay)
    
    

@window.event
def on_draw():
    window.clear()
    if circle.visible:
        circle.draw()
# 60fps
pyglet.clock.schedule_interval(update, 1/60.0)

pyglet.app.run()
