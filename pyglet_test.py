import pyglet
pyglet.resource.path = ['./models']
pyglet.resource.reindex()
# Create a window
window = pyglet.window.Window(width=800, height=600, caption='Pyglet Sprite Example')

# Load an image file
image = pyglet.resource.image('grating_100.jpg')

# Create a sprite from the image
sprite = pyglet.sprite.Sprite(image)

@window.event
def on_draw():
    window.clear()  # Clear the window
    sprite.draw()  # Draw the sprite

if __name__ == '__main__':
    pyglet.app.run()  # Run the application
