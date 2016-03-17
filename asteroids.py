import logging
import math
import random
import pyglet
from pyglet.window import key
from cocos.director import director
from cocos.menu import *
from cocos.text import Label
from cocos.scene import Scene
from cocos.scenes.transitions import *
from cocos.layer import *
from cocos.sprite import Sprite
from cocos.actions import *
import cocos.euclid as eu
import cocos.collision_model as cm

WIN_W = 800
WIN_H = 600
IMG_FOLDER = 'img'
FONT_FOLDER = 'fonts'

SPEED_LIM = 200.
SPEED_LIM_2 = SPEED_LIM * SPEED_LIM
SPEED_STEP = 7.

FONT_NAME = 'ATComputer'
FONT_COLOR = (200, 0, 0, 255)

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
        self.font_title['color'] = FONT_COLOR
        self.font_item['font_name'] = FONT_NAME
        self.font_item['color'] = FONT_COLOR
        self.font_item['font_size'] = 32
        self.font_item_selected['font_name'] = FONT_NAME
        self.font_item_selected['color'] = FONT_COLOR
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
        director.push(FadeTransition(game_scene(), 0.8))

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
        super(Ship, self).__init__('spaceship.png', position=center, scale=0.6)
        self.aim = center
        self.radius = min(self.width, self.height) // 2
        # self.cshape = cm.CircleShape(eu.Vector2(self.position), radius)


class Asteroid(Sprite):
    def __init__(self, x, y):
        name = 'asteroid_' + str(random.randint(1, 4)) + '.png'
        Sprite.__init__(self, name, position=(x, y), scale=0.7)
        self.radius = min(self.width, self.height) // 2
        # self.cshape = cm.CircleShape(eu.Vector2(self.position), radius)

    def update_cshape(self):
        pass
        # self.cshape.center = eu.Vector2(self.position)


def get_default_asteroid():
    x, y = random.randint(0, 1) * WIN_W, random.randint(0, 1) * WIN_H
    asteroid = Asteroid(x, y)
    vec_x, vec_y = random.random() * 2 - 1, random.random() * 2 - 1
    speed = random.randint(50, SPEED_LIM // 1.5)
    norm = (vec_x * vec_x + vec_y * vec_y) ** 0.5
    asteroid.velocity = (speed * vec_x / norm, speed * vec_y / norm)

    asteroid_action = WrappedMove(WIN_W, WIN_H) | Repeat(RotateBy(speed, 1))
    asteroid.do(asteroid_action)
    return asteroid


class GameLayer(Layer):

    is_event_handler = True

    def __init__(self):
        super(GameLayer, self).__init__()
        self.ended = False
        self.player = Ship()
        self.player.do(ShipMove())
        self.add(self.player)

        self.asteroids = []
        for i in range(5):
            asteroid = get_default_asteroid()
            logging.info('Created new asteroid! Vec: %s', asteroid.velocity)
            self.asteroids.append(asteroid)
            self.add(asteroid)
        # self.cm = cm.CollisionManagerGrid(0, WIN_W, 0, WIN_H, 100, 100)

    def on_mouse_motion(self, mx, my, dx, dy):
        self.player.aim = (mx, my)

    def shoot(self, dt):
        logging.info("Bang! {}".format(self.player.aim))

    def on_mouse_press(self, mx, my, button, modifiers):
        pyglet.clock.schedule_interval(self.shoot, 0.5)

    def on_mouse_release(self, x, y, button, modifiers):
        pyglet.clock.unschedule(self.shoot)

    def on_mouse_drag(self, mx, my, dx, dy, buttons, modifiers):
        self.player.aim = (mx, my)

    def draw(self):
        super(Layer, self).draw()
        # self.player.update_cshape()
        # self.asteroid.update_cshape()
        if self.ended:
            return

        px, py = self.player.position
        pr = self.player.radius
        for asteroid in self.asteroids:
            ax, ay = asteroid.position
            ar = asteroid.radius
            dist = ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
            if dist - pr - ar <= 0:
                logging.info("Collision! %s", random.randint(0, 100))
                # director.replace(FadeTransition(game_over_scene(), 1.))
                director.replace(FadeTRTransition(game_over_scene(), 2.))
        # d = abs(circle.center - other.center) - circle.r - other.r
        # if d < 0.0:
        #     d = 0.0
        # return d
        # self.cm.clear()
        # self.cm.add(self.player)
        # self.cm.add(self.asteroid)


class GameOverLayer(Layer):

    is_event_handler = True

    def __init__(self):
        super(GameOverLayer, self).__init__()

        center = WIN_W // 2, WIN_H // 2
        label = Label(text="Game Over",
                      font_name=FONT_NAME,
                      font_size=72,
                      color=FONT_COLOR,
                      anchor_x="center",
                      anchor_y="center",
                      position=center)
                      # position=(center[0], WIN_H + 100))
        # label.do(MoveTo(center, 1))
        self.add(label)

        helper = Label(text="Press ant key to continue",
                       font_name=FONT_NAME,
                       font_size=30,
                       color=FONT_COLOR,
                       position=(center[0], center[1] - 200),
                       anchor_x="center",
                       anchor_y="center")
        self.add(helper)

    def next_scene(self):
        logging.info("To main menu!")
        director.pop()

    def on_mouse_press(self, mx, my, button, modifiers):
        self.next_scene()

    def on_key_press(self, k, mod):
        self.next_scene()


def menu_scene():
    scene = Scene()
    scene.add(BackgroundLayer('menu_backgroud.jpg'), z=0)
    scene.add(MultiplexLayer(
        MainMenu(),
        OptionsMenu()
    ), z=1)
    return scene


def game_over_scene():
    scene = Scene()
    scene.add(BackgroundLayer('main_background.jpg'), z=0)
    asteroid_layer = Layer()
    for i in range(5):
        asteroid_layer.add(get_default_asteroid())
        scene.add(asteroid_layer)
    scene.add(GameOverLayer(), z=2)
    return scene


def game_scene():
    scene = Scene()
    scene.add(BackgroundLayer('main_background.jpg'), z=0)
    scene.add(GameLayer(), z=1)
    return scene


def init_resources():
    pyglet.resource.path = [IMG_FOLDER, FONT_FOLDER]
    pyglet.resource.reindex()

    image = pyglet.resource.texture('cursor.png')
    cursor = pyglet.window.ImageMouseCursor(image, 24, 24)
    director.window.set_mouse_cursor(cursor)
    # icon1 = pyglet.resource.texture('icon.png')
    # icon2 = pyglet.resource.texture('icon_128.png')
    # director.window.set_icon(icon1, icon2)

    # pyglet.resource.add_font('Minecraftia.ttf')
    pyglet.resource.add_font('ATComputer.ttf')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)-5s: %(message)s')

    director.init(caption="Asteroids", width=WIN_W, height=WIN_H, resizable=False, autoscale=False)
    director.window.push_handlers(keys)

    init_resources()

    # director.window.push_handlers(pyglet.window.event.WindowEventLogger())
    director.run(menu_scene())
