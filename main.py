from kivy.config import Config
import random

Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '480')

from kivy.core.window import Window
from kivy import platform
from kivy.graphics import Quad
from kivy.graphics import Triangle
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
from kivy.core.audio import SoundLoader

from kivy.uix.relativelayout import RelativeLayout
from kivy.app import App
from kivy.properties import NumericProperty
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line
from kivy.properties import Clock

Builder.load_file("menu.kv")


class MainWidget(RelativeLayout):
    perspective_point_x = NumericProperty(0)
    perspective_point_y = NumericProperty(0)
    menu_widget = ObjectProperty()

    V_NB_LINES = 8
    V_LINES_SPACING = .4
    vertical_lines = []

    H_NB_LINES = 30
    H_LINES_SPACING = .1
    horizontal_lines = []

    current_offset_y = 0
    SPEED = 0.5
    current_offset_x = 0
    current_speed_x = 0
    current_y_loop = 0
    SPEED_X = 3.0

    NB_TILES = 16
    tiles = []
    tiles_coordinates = []

    SHIP_WIDTH = .1
    SHIP_HEIGHT = .035
    SHIP_BASE_Y = 0.04
    ship = None
    ship_coordinates = [(0, 0), (0, 0), (0, 0)]

    state_game_over = False
    state_game_has_started = False

    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_button_title = StringProperty("START")
    score_txt = StringProperty()

    sound_begin = None
    sound_galaxy = None
    sound_gameover_impact = None
    sound_gameover_voice = None
    sound_music1 = None
    sound_restart = None

    state_game_paused = False
    state_game_play = True

    SCORE = NumericProperty(0)
    HI_SCORE = NumericProperty(0)

    accelaration = 1

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        # print("INIT W:" + str(self.width) + "H:" + str(self.height))
        self.HI_SCORE = self.load_hi_score()
        self.init_audio()
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()
        self.reset_game()

        if self.is_desktop():
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)
        Clock.schedule_interval(self.update, 1.0 / 60.0)
        self.sound_galaxy.play()

    def reset_game(self):
        self.SPEED = 0.5
        self.current_offset_x = 0
        self.current_offset_y = 0
        self.current_speed_x = 0
        self.current_y_loop = 0
        self.SCORE = 0
        self.score_txt = "SCORE: " + str(self.SCORE)

        self.tiles_coordinates = []
        self.pre_fill_tiles_coordinates()
        self.generate_tiles_coordinates()

        self.state_game_over = False

    def init_audio(self):
        self.sound_begin = SoundLoader.load("audio/begin.wav")
        self.sound_galaxy = SoundLoader.load("audio/galaxy.wav")
        self.sound_gameover_impact = SoundLoader.load("audio/gameover_impact.wav")
        self.sound_gameover_voice = SoundLoader.load("audio/gameover_voice.wav")
        self.sound_music1 = SoundLoader.load("audio/galaxy_believer.mp3")
        self.sound_restart = SoundLoader.load("audio/restart.wav")

        self.sound_music1.volume = 1
        self.sound_galaxy.volume = .25
        self.sound_begin.volume = .25
        self.sound_gameover_voice.volume = .25
        self.sound_gameover_impact.volume = .6
        self.sound_restart.volume = .25

    def init_ship(self):
        with self.canvas:
            Color(0, 0, 0)
            self.ship = Triangle()

    def update_ship(self):
        center_x = self.width / 2
        base_y = self.SHIP_BASE_Y * self.height
        ship_half_width = self.SHIP_WIDTH * self.width / 2
        ship_height = self.SHIP_HEIGHT * self.height

        self.ship_coordinates[0] = (center_x - ship_half_width, base_y)
        self.ship_coordinates[1] = (center_x, base_y + ship_height)
        self.ship_coordinates[2] = (center_x + ship_half_width, base_y)

        x1, y1 = self.transform(*self.ship_coordinates[0])
        x2, y2 = self.transform(*self.ship_coordinates[1])
        x3, y3 = self.transform(*self.ship_coordinates[2])

        self.ship.points = [x1, y1, x2, y2, x3, y3]

    def check_ship_collision(self):
        for i in range(0, len(self.tiles_coordinates)):
            ti_x, ti_y = self.tiles_coordinates[i]
            if ti_y > self.current_y_loop + 1:
                return False
            if self.check_ship_collision_with_tile(ti_x, ti_y):
                return True
        return False

    def check_ship_collision_with_tile(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x + 1, ti_y + 1)
        for i in range(0, 3):
            px, py = self.ship_coordinates[i]
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False

    def on_pause(self):
        if (not self.state_game_over and self.state_game_play) and self.state_game_has_started:
            self.state_game_paused = True
            self.sound_music1.stop()

    def on_play(self):
        if (not self.state_game_over and self.state_game_play) and self.state_game_has_started:
            self.sound_music1.play()
            self.state_game_paused = False

    def keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self.on_keyboard_down)
        self._keyboard.unbind(on_key_up=self.on_keyboard_up)
        self._keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text=None, modifiers=None):
        if keycode[1] == "left":
            self.current_speed_x = self.SPEED_X
        elif keycode[1] == "right":
            self.current_speed_x = -self.SPEED_X
        elif keycode[1] == "up":
            self.on_play()
        elif keycode[1] == "down":
            self.on_pause()
        return True

    def on_keyboard_up(self, keyboard, keycode):
        self.current_speed_x = 0
        return True

    def on_touch_down(self, touch):
        if not self.state_game_over and self.state_game_has_started:
            if touch.x < self.width / 2:
                # print("<-")
                self.current_speed_x = self.SPEED_X
            else:
                # print("->")
                self.current_speed_x = -self.SPEED_X
        return super(MainWidget, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        # print("UP")
        self.current_speed_x = 0

    def is_desktop(self):
        if platform in ('linux', 'win', 'macosx'):
            return True
        return False

    def init_tiles(self):
        with self.canvas:
            Color(1, 1, 1, 1)
            for i in range(0, self.NB_TILES):
                self.tiles.append(Quad())

    def pre_fill_tiles_coordinates(self):
        for i in range(0, 10):
            self.tiles_coordinates.append((0, i))

    def generate_tiles_coordinates(self):
        last_x = 0
        last_y = 0
        for i in range(len(self.tiles_coordinates) - 1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]
        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]
            last_x = last_coordinates[0]
            last_y = last_coordinates[1] + 1

        for i in range(len(self.tiles_coordinates), self.NB_TILES):
            r = random.randint(0, 2)

            start_index = -int(self.V_NB_LINES / 2) + 1
            end_index = start_index + self.V_NB_LINES - 1

            if last_x <= start_index:
                r = 1
            if last_x >= end_index:
                r = 2

            self.tiles_coordinates.append((last_x, last_y))
            if r == 1:
                last_x += 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            if r == 2:
                last_x -= 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            last_y += 1

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            # self.line = Line(points=[100, 0, 100, 100])
            for i in range(0, self.V_NB_LINES):
                self.vertical_lines.append(Line())

    def get_line_x_from_index(self, index):
        central_line_x = self.perspective_point_x
        spacing = self.V_LINES_SPACING * self.width
        offset = index - 0.5
        line_x = central_line_x + offset * spacing + self.current_offset_x
        return line_x

    def get_line_y_from_index(self, index):
        spacing_y = self.H_LINES_SPACING * self.height
        line_y = index * spacing_y - self.current_offset_y
        return line_y

    def get_tile_coordinates(self, ti_x, ti_y):
        ti_y = ti_y - self.current_y_loop
        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    def update_tiles(self):
        for i in range(0, self.NB_TILES):
            tile = self.tiles[i]
            tile_coordinates = self.tiles_coordinates[i]
            xmin, ymin = self.get_tile_coordinates(tile_coordinates[0], tile_coordinates[1])
            xmax, ymax = self.get_tile_coordinates(tile_coordinates[0] + 1, tile_coordinates[1] + 1)

            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

    def update_vertical_lines(self):
        start_index = -int(self.V_NB_LINES / 2) + 1
        for i in range(start_index, start_index + self.V_NB_LINES):
            line_x = self.get_line_x_from_index(i)
            x1, y1 = self.transform(line_x, 0)
            x2, y2 = self.transform(line_x, self.height)
            self.vertical_lines[i].points = [x1, y1, x2, y2]

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            # self.line = Line(points=[100, 0, 100, 100])
            for i in range(0, self.H_NB_LINES):
                self.horizontal_lines.append(Line())

    def update_horizontal_lines(self):
        start_index = -int(self.V_NB_LINES / 2) + 1
        end_index = start_index + self.V_NB_LINES - 1
        xmin = self.get_line_x_from_index(start_index)
        xmax = self.get_line_x_from_index(end_index)

        for i in range(0, self.H_NB_LINES):
            line_y = self.get_line_y_from_index(i)
            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]

    def transform(self, x, y):
        # return self.transform_2D(x, y)
        return self.transform_perspective(x, y)

    def transform_2D(self, x, y):
        return int(x), int(y)

    def transform_perspective(self, x, y):
        lin_y = y * self.perspective_point_y / self.height
        if lin_y > self.perspective_point_y:
            lin_y = self.perspective_point_y
        diff_x = x - self.perspective_point_x
        diff_y = self.perspective_point_y - lin_y
        factor_y = diff_y / self.perspective_point_y
        factor_y = pow(factor_y, 4)

        tr_x = self.perspective_point_x + diff_x * factor_y
        tr_y = self.perspective_point_y - factor_y * self.perspective_point_y

        return int(tr_x), int(tr_y)

    def update(self, dt):
        # print("dt:" + str(dt*60))
        time_factor = dt * 60
        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()
        self.SPEED += self.accelaration * dt / 100

        if self.SCORE > self.HI_SCORE:
            self.HI_SCORE = self.SCORE
            file = open("hi_score.pkl", "wb")
            import pickle
            pickle.dump(self.HI_SCORE, file)
            file.close()

        if not self.state_game_over and self.state_game_has_started and not self.state_game_paused:
            speed_y = self.SPEED * self.height / 100
            self.current_offset_y += speed_y * time_factor
            spacing_y = self.H_LINES_SPACING * self.height

            while self.current_offset_y >= spacing_y:
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                self.SCORE += int(self.SPEED / dt)
                self.score_txt = "SCORE:" + str(self.SCORE)
                self.generate_tiles_coordinates()
                print("loop" + str(self.current_y_loop))

            speed_x = self.current_speed_x * self.width
            self.current_offset_x += speed_x * time_factor / 100

        if not self.check_ship_collision() and not self.state_game_over:
            self.state_game_over = True
            self.menu_title = "G  A  M  E    O  V  E  R"
            self.menu_button_title = "RESTART"
            self.menu_widget.opacity = 1
            self.sound_music1.stop()
            self.sound_gameover_impact.play()
            Clock.schedule_once(self.play_game_over_voice_sound, 3)

    def play_game_over_voice_sound(self, dt):
        if self.state_game_over:
            self.sound_gameover_voice.play()

    def on_menu_button_pressed(self):
        print("Button")
        if self.state_game_over:
            self.sound_restart.play()
        else:
            self.sound_begin.play()
        self.sound_music1.play()

        self.reset_game()
        self.state_game_has_started = True
        self.menu_widget.opacity = 0

    def load_hi_score(self):
        file = open("hi_score.pkl", "rb")
        import pickle
        temp = pickle.load(file)
        file.close()
        return temp

    def on_high_score_button_pressed(self):
        print(self.HI_SCORE)


class GalaxyApp(App):
    pass


GalaxyApp().run()
