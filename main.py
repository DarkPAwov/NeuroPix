# main.py — точка входа мобильной версии NeuroPix
# Поддерживает Android (FINGER-события) и десктоп (мышь) для тестирования

import sys
import os
import urllib.request
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE, BG,
    STATE_MENU, STATE_MOZGOBLOK, STATE_ECHORAD,
    STATE_PROSTRANSTVO, STATE_RECORDS, STATE_NAME_INPUT,
)
from database import Database


def _is_android() -> bool:
    """Определить, запущено ли приложение на Android."""
    try:
        import android  # noqa — доступен только на Android через p4a
        return True
    except ImportError:
        return False


def _ensure_font():
    """Скачать шрифт Press Start 2P если отсутствует."""
    path = os.path.join('assets', 'font_pixel.ttf')
    if not os.path.exists(path):
        url = ('https://github.com/google/fonts/raw/main/'
               'ofl/pressstart2p/PressStart2P-Regular.ttf')
        try:
            os.makedirs('assets', exist_ok=True)
            urllib.request.urlretrieve(url, path)
        except Exception:
            pass   # используем системный шрифт


class App:
    """Главный класс мобильного приложения."""

    def __init__(self):
        _ensure_font()
        pygame.init()

        self._android = _is_android()

        if self._android:
            # На Android — полный экран с масштабированием
            self.screen = pygame.display.set_mode(
                (WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED
            )
        else:
            # На десктопе — обычное окно для тестирования
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)

        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.db    = Database()
        self.state = STATE_MENU
        self.data  = {}

        self._init_screens()
        self.screens[STATE_MENU].on_enter({})

    def _init_screens(self):
        from screens.menu        import MenuScreen
        from screens.records     import RecordsScreen
        from screens.name_input  import NameInputScreen
        from games.mozgoblok     import MozgoBlok
        from games.echorad       import EchoRad
        from games.prostranstvo_x import ProstranstvoX

        self.screens = {
            STATE_MENU:         MenuScreen(self),
            STATE_RECORDS:      RecordsScreen(self),
            STATE_NAME_INPUT:   NameInputScreen(self),
            STATE_MOZGOBLOK:    MozgoBlok(self),
            STATE_ECHORAD:      EchoRad(self),
            STATE_PROSTRANSTVO: ProstranstvoX(self),
        }

    def change_state(self, new_state: str, data: dict = None):
        self.state = new_state
        self.data  = data or {}
        screen = self.screens.get(new_state)
        if screen and hasattr(screen, 'on_enter'):
            screen.on_enter(self.data)

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            screen = self.screens[self.state]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                # На Android аппаратная кнопка «Назад»
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.state == STATE_MENU:
                        pygame.quit(); sys.exit()
                    else:
                        self.change_state(STATE_MENU)
                    continue
                screen.handle_event(event)

            screen.update(dt)
            self.screen.fill(BG)
            screen.draw(self.screen)
            pygame.display.flip()


if __name__ == '__main__':
    App().run()
