import logging
import math
import pyglet
from pyglet.window import key
from cocos.director import director
from cocos.menu import *
from cocos.scene import Scene
from cocos.layer import *
from cocos.sprite import Sprite
from cocos.actions import *

WIN_W = 800
WIN_H = 600
IMG_FOLDER = 'img'
FONT_FOLDER = 'fonts'

SPEED_LIM = 200.
SPEED_LIM_2 = SPEED_LIM * SPEED_LIM
SPEED_STEP = 7.
FONT_NAME = 'Minecraftia'

keys = key.KeyStateHandler()

# def constrain(x, minx, maxx):
#     return minx if x < minx else maxx if x > maxx else x

class BackgroundLayer(Layer):
    def __init__(self, img_name):
        super(BackgroundLayer, self).__init__()
        self.img = pyglet.resource.image(img_name)

    def draw(self):
        glPushMatrix()
        self.transform()
        self.img.blit(0, 0)
        glPopMatrix()


class BaseMenu(Menu):
    def __init__(self, name):
        super(BaseMenu, self).__init__(name)
        self.font_title['font_name'] = FONT_NAME
        self.font_title['font_size'] = 72
        self.font_title['color'] = (200, 0, 0, 255)
        self.font_item['font_name'] = FONT_NAME
        self.font_item['color'] = (200, 0, 0, 255)
        self.font_item['font_size'] = 32
        self.font_item_selected['font_name'] = FONT_NAME
        self.font_item_selected['color'] = (200, 0, 0, 255)
        self.font_item_selected['font_size'] = 46
        self.menu_valign = CENTER
        self.menu_halign = CENTER


class MainMenu(BaseMenu):
    def __init__(self):
        super(MainMenu, self).__init__("Asteroids")
        menu_items = [
            MenuItem("Start", self.start_game),
            MenuItem("Scores", self.to_scores),
            MenuItem("Options", self.to_options),
            MenuItem("Exit", pyglet.app.exit)
        ]
        self.create_menu(menu_items, zoom_in(), zoom_out())

    def start_game(self):
        logging.info('Starting Game!')
        director.push(get_new_game())

    def to_options(self):
        logging.info('To the options menu!')
        self.parent.switch_to(1)

    def to_scores(self):
        logging.info('To the scores menu!')

    def on_quit(self):
        logging.info('Exiting')
        pyglet.app.exit()


class OptionsMenu(BaseMenu):

    is_event_handler = True

    def __init__(self):
        super(OptionsMenu, self).__init__("Options")
        items = [ToggleMenuItem('Show FPS:', self.on_show_fps, director.show_FPS),
                 MenuItem('Toggle fullscreen', self.on_toggle_fullscreen),
                 MenuItem('Back', self.on_quit)]
        self.create_menu(items, zoom_in(), zoom_out())

    def on_key_press(self, k, mod):
        if k == key.ESCAPE:
            self.parent.switch_to(0)
            logging.info("To main menu")
            return True

    def on_show_fps(self, value):
        director.show_FPS = value

    def on_toggle_fullscreen(self):
        director.window.set_fullscreen(not director.window.fullscreen)

    def on_quit(self):
        logging.info("To main menu")
        self.parent.switch_to(0)


class ShipMove(WrappedMove):
    def init(self):
        super(ShipMove, self).init(WIN_W, WIN_H)

    def start(self):
        self.target.velocity = (0., 0.)

    def step(self, dt):
        # wrapping ship by window borders
        super(ShipMove, self).step(dt)
        # changing ship's velocity according to the pressed keys
        vel_x, vel_y = self.target.velocity
        vel_x += (keys[key.D] - keys[key.A]) * SPEED_STEP
        vel_y += (keys[key.W] - keys[key.S]) * SPEED_STEP
        norm = vel_x * vel_x + vel_y * vel_y
        if norm > SPEED_LIM_2:
            k = SPEED_LIM_2 / norm
            vel_x *= k
            vel_y *= k
        self.target.velocity = vel_x, vel_y
        # rotating sprite according to mouse pointer
        px, py = self.target.position
        mx, my = self.target.aim
        x, y = mx - px, my - py
        if x == 0 and y == 0:
            return
        angle = 90 - math.degrees(math.atan2(y, x))
        self.target.rotation = angle


# class AsteroidMove(WrappedMove):
#     def init(self, dx, dy):
#         super(AsteroidMove, self).init(WIN_W, WIN_H)
#         self.vec = dx, dy

#     def start(self):
#         self.target.velocity = self.vec


class Ship(Sprite):
    def __init__(self):
        center = (WIN_W / 2., WIN_H / 2.)
        super(Ship, self).__init__('spaceship.png', position=center, scale=0.2)
        self.aim = center

class Asteroid(Sprite):
    def __init__(self, x, y):
        Sprite.__init__(self, 'asteroid.png', position=(x, y), scale=0.7)


class GameLayer(Layer):

    is_event_handler = True

    def __init__(self):
        super(GameLayer, self).__init__()
        self.player = Ship()
        self.player.do(ShipMove())
        self.add(self.player)
        self.asteroid = Asteroid(0, 0)
        self.asteroid.velocity = (50, 50)
        asteroid_action = WrappedMove(WIN_W, WIN_H) | Repeat(RotateBy(90, 1))
        self.asteroid.do(asteroid_action)
        self.add(self.asteroid)

    def on_mouse_motion(self, mx, my, dx, dy):
        self.player.aim = (mx, my)

    def shoot(self, dt, who, point):
        logging.info("{} shoot aiming to {}".format(who, point))

    def on_mouse_press(self, mx, my, button, modifiers):
        pyglet.clock.schedule_interval(self.shoot, 0.5, "Player", (mx, my))

    def on_mouse_release(self, x, y, button, modifiers):
        pyglet.clock.unschedule(self.shoot)

    def on_mouse_drag(self, mx, my, dx, dy, buttons, modifiers):
        self.player.aim = (mx, my)


def get_new_game():
    scene = Scene()
    bg = BackgroundLayer('main_background.jpg')
    game = GameLayer()
    scene.add(bg, z=0)
    scene.add(game, z=1)
    return scene


def load_font(filename):
    from pyglet.font.ttf import TruetypeInfo
    p = TruetypeInfo(filename)
    name = p.get_name("name")
    p.close()
    pyglet.font.add_file(filename)
    got = pyglet.font.have_font(name)
    logging.debug("Font {} loaded? - {}".format(name, got))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-5s: %(message)s')

    director.init(caption="Asteroids", width=800, height=600, resizable=False, autoscale=True)
    director.window.push_handlers(keys)

    pyglet.resource.path = [IMG_FOLDER, FONT_FOLDER]
    pyglet.resource.reindex()

    image = pyglet.resource.texture('cursor.png')
    cursor = pyglet.window.ImageMouseCursor(image, 24, 24)
    director.window.set_mouse_cursor(cursor)
    icon1 = pyglet.resource.texture('icon.png')
    icon2 = pyglet.resource.texture('icon_128.png')
    director.window.set_icon(icon1, icon2)

    pyglet.resource.add_font('Minecraftia.ttf')
    got = pyglet.font.have_font('Minecraftia')
    logging.debug("Have font? : {}".format(got))

    menu_scene = Scene()
    menu_scene.add(BackgroundLayer('menu_backgroud.jpg'), z=0)
    menu_scene.add(MultiplexLayer(
        MainMenu(),
        OptionsMenu()
    ), z=1)

    # director.window.push_handlers(pyglet.window.event.WindowEventLogger())
    director.run(menu_scene)
