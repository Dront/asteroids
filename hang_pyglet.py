import pyglet

window = pyglet.window.Window()

@window.event
def on_key_press(symbol, modifiers):
    print 'A key was pressed'

@window.event
def on_draw():
    window.clear()

@window.event
def on_mouse_move(x, y, b, m):
    window.clear()

# image = pyglet.resource.texture('img/cursor.png')
# cursor = pyglet.window.ImageMouseCursor(image, 24, 24)
# window.set_mouse_cursor(cursor)

window.push_handlers(pyglet.window.event.WindowEventLogger())
pyglet.app.run()
