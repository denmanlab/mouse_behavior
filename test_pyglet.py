import pyglet

window = pyglet.window.Window()

@window.event
def on_draw():
    window.clear()
    #pyglet.shapes.Circle(100, 100, radius = 50, color = 'red')
    # Minimal rendering code here

pyglet.app.run()