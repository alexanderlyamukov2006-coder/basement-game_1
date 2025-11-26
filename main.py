from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.metrics import dp
from kivy.core.audio import SoundLoader
from kivy.core.image import Image as CoreImage
import random
import os


class GameWidget(Widget):
    player_pos = ListProperty([400, 200])
    player_size = NumericProperty(40)
    lives = NumericProperty(3)
    level = NumericProperty(1)
    time_left = NumericProperty(60)
    game_state = StringProperty('story')
    story_text = StringProperty('')
    bricks = ListProperty([])
    collision_cooldown = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_music = None
        self.background_textures = {}  # Текстуры для фонов
        self.load_backgrounds()  # Загружаем фоны
        self.setup_game()

    def load_backgrounds(self):
        """Загрузка фоновых изображений"""
        try:
            # Загружаем твои фоны с именами lav_1, lav_2, lav_3
            background_files = {
                1: 'images/lav_1.png',
                2: 'images/lav_2.png',
                3: 'images/lav_3.png'
            }

            for level, filename in background_files.items():
                if os.path.exists(filename):
                    self.background_textures[level] = CoreImage(filename).texture
                    print(f"✅ Загружен фон для уровня {level}: {filename}")
                else:
                    print(f"⚠️ Фон не найден: {filename}")
                    self.background_textures[level] = None

        except Exception as e:
            print(f"❌ Ошибка загрузки фонов: {e}")
            # Создаем пустые текстуры если ошибка
            self.background_textures = {1: None, 2: None, 3: None}

    def setup_game(self):
        """Инициализация игры"""
        self.start_story()

    def play_music(self, filename, volume=0.5):
        """Воспроизведение музыки"""
        if self.background_music:
            self.background_music.stop()

        if os.path.exists(filename):
            self.background_music = SoundLoader.load(filename)
            if self.background_music:
                self.background_music.volume = volume
                self.background_music.loop = True
                self.background_music.play()
                print(f"🎵 Включена музыка: {filename}")
        else:
            print(f"⚠️ Файл {filename} не найден! Проверь папку sounds/")

    def stop_music(self):
        """Остановка музыки"""
        if self.background_music:
            self.background_music.stop()
            self.background_music = None
            print("🔇 Музыка остановлена")

    def start_story(self):
        """Начало сюжета"""
        self.game_state = 'story'
        self.story_text = "Странно, похоже я давно здесь...               Разраб - Лямуков А.С."

        Clock.schedule_once(self.next_story, 2)

    def next_story(self, dt):
        """Следующий текст сюжета"""
        self.story_text = "Это место не выпускает меня...        Разраб - Лямуков А.С."
        Clock.schedule_once(self.start_level, 2)

    def start_level(self, dt):
        """Запуск уровня"""
        self.game_state = 'playing'
        self.reset_player()
        self.bricks = []
        self.collision_cooldown = 0

        # Включаем музыку
        self.play_music('sounds/background.mp3', volume=0.5)

        Clock.schedule_interval(self.game_loop, 1.0 / 60.0)
        Clock.schedule_interval(self.update_timer, 1.0)
        Clock.schedule_interval(self.spawn_bricks, 1.5)

    def reset_player(self):
        """Сброс позиции игрока"""
        self.player_pos = [400, 200]
        self.lives = 3
        self.time_left = 60

    def spawn_bricks(self, dt):
        """Создание падающих кирпичей"""
        if self.game_state != 'playing':
            return

        x = random.randint(50, 750)
        speed = 2 + self.level
        self.bricks.append([x, 600, 40, 40, speed])

    def game_loop(self, dt):
        """Основной игровой цикл"""
        if self.game_state != 'playing':
            return

        self.update_bricks()
        self.check_collisions()
        self.update_cooldown()
        self.canvas.ask_update()

    def update_cooldown(self):
        """Обновление времени защиты от столкновений"""
        if self.collision_cooldown > 0:
            self.collision_cooldown -= 1

    def update_bricks(self):
        """Обновление позиций кирпичей"""
        new_bricks = []
        for brick in self.bricks:
            brick[1] -= brick[4]
            if brick[1] > -50:
                new_bricks.append(brick)
        self.bricks = new_bricks

    def check_collisions(self):
        """Проверка столкновений"""
        if self.collision_cooldown > 0:
            return

        for brick in self.bricks:
            if self.is_collision(brick):
                self.handle_collision()
                break

    def handle_collision(self):
        """Обработка столкновения с кирпичом"""
        self.lives -= 1
        self.collision_cooldown = 30

        # Мигание игрока при получении урона
        self.player_pos = [self.player_pos[0] - 5, self.player_pos[1] - 5]
        Clock.schedule_once(self.reset_player_position, 0.1)

        if self.lives <= 0:
            self.game_over()
        else:
            self.story_text = f"Осталось жизней: {self.lives}"
            Clock.schedule_once(self.clear_story_text, 1.5)

    def reset_player_position(self, dt):
        """Возврат игрока в нормальное положение после мигания"""
        self.player_pos = [self.player_pos[0] + 5, self.player_pos[1] + 5]

    def clear_story_text(self, dt):
        """Очистка текста о жизнях"""
        if self.game_state == 'playing':
            self.story_text = ""

    def is_collision(self, brick):
        """Проверка столкновения игрока с кирпичом"""
        px, py = self.player_pos
        ps = self.player_size
        bx, by, bw, bh, bs = brick

        return (px < bx + bw and
                px + ps > bx and
                py < by + bh and
                py + ps > by)

    def update_timer(self, dt):
        """Обновление таймера"""
        if self.game_state != 'playing':
            return

        self.time_left -= 1
        if self.time_left <= 0:
            self.next_level()

    def next_level(self):
        """Переход на следующий уровень"""
        self.level += 1
        if self.level > 3:
            self.game_win()
        else:
            self.start_level(None)

    def game_over(self):
        """Конец игры при потере всех жизней"""
        self.game_state = 'game_over'
        self.story_text = "Игра окончена... Потеряны все жизни"
        self.stop_music()
        self.cleanup_clocks()
        Clock.schedule_once(self.restart_game, 3)

    def game_win(self):
        """Победа в игре"""
        self.game_state = 'story'
        self.story_text = "Что ж, это всегда была пустота, и лишь на миг этот мрак стал жизнью..."
        self.stop_music()
        self.cleanup_clocks()
        Clock.schedule_once(self.exit_game, 4)

    def restart_game(self, dt):
        """Перезапуск игры после проигрыша"""
        self.level = 1
        self.start_story()

    def exit_game(self, dt):
        """Выход из игры"""
        self.stop_music()
        App.get_running_app().stop()

    def cleanup_clocks(self):
        """Очистка всех таймеров"""
        Clock.unschedule(self.game_loop)
        Clock.unschedule(self.update_timer)
        Clock.unschedule(self.spawn_bricks)

    def move_player(self, dx, dy):
        """Движение игрока"""
        if self.game_state != 'playing':
            return

        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        if 0 <= new_x <= 800 - self.player_size:
            self.player_pos[0] = new_x
        if 100 <= new_y <= 500 - self.player_size:
            self.player_pos[1] = new_y

    def on_draw(self):
        """Отрисовка игровых элементов с твоими фонами"""
        self.canvas.clear()

        with self.canvas:
            # РИСУЕМ ТВОИ ФОНЫ
            current_texture = self.background_textures.get(self.level)
            if current_texture:
                # Если фон загружен - рисуем его
                Rectangle(texture=current_texture, pos=(0, 150), size=(800, 400))
            else:
                # Запасной вариант - цветные фоны
                if self.level == 1:
                    Color(0.2, 0.2, 0.3)
                elif self.level == 2:
                    Color(0.3, 0.2, 0.2)
                else:
                    Color(0.1, 0.1, 0.1)
                Rectangle(pos=(0, 150), size=(800, 400))

            # Игрок (мигает красным при получении урона)
            if self.collision_cooldown > 0 and self.collision_cooldown % 6 < 3:
                Color(1, 0.2, 0.2)
            else:
                Color(0, 0.8, 1)

            Rectangle(pos=self.player_pos, size=(self.player_size, self.player_size))

            # Кирпичи
            Color(0.8, 0.2, 0.2)
            for brick in self.bricks:
                Rectangle(pos=(brick[0], brick[1]), size=(brick[2], brick[3]))


class GameApp(App):
    def build(self):
        """Создание интерфейса"""
        Window.size = (800, 600)

        main_layout = FloatLayout()

        self.game_widget = GameWidget()
        main_layout.add_widget(self.game_widget)

        top_panel = self.create_top_panel()
        main_layout.add_widget(top_panel)

        text_panel = self.create_text_panel()
        main_layout.add_widget(text_panel)

        control_panel = self.create_control_panel()
        main_layout.add_widget(control_panel)

        Clock.schedule_interval(lambda dt: self.game_widget.on_draw(), 1.0 / 60.0)

        return main_layout

    def create_top_panel(self):
        """Создание верхней панели с информацией"""
        panel = BoxLayout(
            size_hint=(1, 0.08),
            pos_hint={'top': 1},
            orientation='horizontal'
        )

        level_label = Label(text='Уровень: 1', font_size=dp(16))
        lives_label = Label(text='Жизни: 3', font_size=dp(16))
        time_label = Label(text='Время: 60', font_size=dp(16))

        self.game_widget.bind(level=lambda obj, value: setattr(level_label, 'text', f'Уровень: {value}'))
        self.game_widget.bind(lives=lambda obj, value: setattr(lives_label, 'text', f'Жизни: {value}'))
        self.game_widget.bind(time_left=lambda obj, value: setattr(time_label, 'text', f'Время: {value}'))

        panel.add_widget(level_label)
        panel.add_widget(lives_label)
        panel.add_widget(time_label)

        return panel

    def create_text_panel(self):
        """Создание панели для текста"""
        panel = Label(
            text='',
            size_hint=(1, 0.12),
            pos_hint={'y': 0},
            text_size=(800, None),
            halign='center',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(18)
        )
        self.game_widget.bind(story_text=lambda obj, value: setattr(panel, 'text', value))
        return panel

    def create_control_panel(self):
        """Создание компактной панели управления в правом нижнем углу"""
        control_layout = FloatLayout(size_hint=(None, None), size=(200, 200))
        control_layout.pos_hint = {'right': 1, 'bottom': 1}

        up_btn = Button(
            text='^',
            font_size=dp(25),
            size_hint=(None, None),
            size=(60, 60),
            pos=(70, 130),
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        up_btn.bind(on_press=lambda x: self.game_widget.move_player(0, 30))

        left_btn = Button(
            text='<',
            font_size=dp(25),
            size_hint=(None, None),
            size=(60, 60),
            pos=(10, 70),
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        left_btn.bind(on_press=lambda x: self.game_widget.move_player(-30, 0))

        down_btn = Button(
            text='_',
            font_size=dp(25),
            size_hint=(None, None),
            size=(60, 60),
            pos=(70, 10),
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        down_btn.bind(on_press=lambda x: self.game_widget.move_player(0, -30))

        right_btn = Button(
            text='>',
            font_size=dp(25),
            size_hint=(None, None),
            size=(60, 60),
            pos=(130, 70),
            background_color=(0.3, 0.3, 0.3, 0.8)
        )
        right_btn.bind(on_press=lambda x: self.game_widget.move_player(30, 0))

        control_layout.add_widget(up_btn)
        control_layout.add_widget(left_btn)
        control_layout.add_widget(down_btn)
        control_layout.add_widget(right_btn)

        return control_layout

    def on_stop(self):
        """Очистка при закрытии приложения"""
        self.game_widget.cleanup_clocks()
        self.game_widget.stop_music()


if __name__ == '__main__':
    GameApp().run()
