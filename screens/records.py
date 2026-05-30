# screens/records.py — мобильный экран рекордов

import pygame
from settings import (
    WIDTH, HEIGHT,
    BG, WHITE, DARK_GRAY, MID_GRAY, DIM,
    BLUE, GREEN, RED,
    FONT_XS, FONT_SM, FONT_LG,
    STATE_MENU, STATE_MOZGOBLOK, STATE_ECHORAD, STATE_PROSTRANSTVO,
    get_font,
)
from utils import StarField


class RecordsScreen:
    TABS = [
        ('МОЗГОБЛОК',  STATE_MOZGOBLOK,   BLUE),
        ('ЭХОРЯД',     STATE_ECHORAD,     GREEN),
        ('ПРОСТР.',    STATE_PROSTRANSTVO, RED),
    ]
    TAB_H = 52

    def __init__(self, app):
        self.app     = app
        self.stars   = StarField(30)
        self.tab     = 0
        self.records = []
        self.font_xs = get_font(FONT_XS)
        self.font_sm = get_font(FONT_SM)
        self.font_lg = get_font(FONT_LG)

    def on_enter(self, data: dict):
        game = data.get('game', STATE_MOZGOBLOK)
        for i, (_, s, _) in enumerate(self.TABS):
            if s == game:
                self.tab = i
        self._load()

    def _load(self):
        self.records = self.app.db.get_top10(self.TABS[self.tab][1])

    def _tab_rect(self, i: int) -> pygame.Rect:
        w = WIDTH // len(self.TABS)
        return pygame.Rect(i * w, 56, w, self.TAB_H)

    def _back_rect(self):
        return pygame.Rect(WIDTH // 2 - 140, HEIGHT - 74, 280, 56)

    def handle_event(self, event):
        pos = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x * WIDTH), int(event.y * HEIGHT))

        if pos:
            for i in range(len(self.TABS)):
                if self._tab_rect(i).collidepoint(pos):
                    self.tab = i; self._load(); return
            if self._back_rect().collidepoint(pos):
                self.app.change_state(STATE_MENU)

    def update(self, dt: float):
        self.stars.update(dt)

    def draw(self, surface: pygame.Surface):
        surface.fill(BG)
        self.stars.draw(surface)

        _, _, tc = self.TABS[self.tab]

        # Заголовок
        title = self.font_lg.render('[ РЕКОРДЫ ]', False, WHITE)
        surface.blit(title, title.get_rect(centerx=WIDTH // 2, top=10))

        # Вкладки
        for i, (name, _, color) in enumerate(self.TABS):
            r      = self._tab_rect(i)
            active = (i == self.tab)
            pygame.draw.rect(surface, DARK_GRAY if active else BG, r)
            pygame.draw.rect(surface, color if active else MID_GRAY, r, 1)
            t = self.font_xs.render(name, False, color if active else MID_GRAY)
            surface.blit(t, t.get_rect(center=r.center))
            if active:
                pygame.draw.rect(surface, color,
                                 (r.x, r.bottom - 2, r.width, 2))

        # Шапка таблицы
        hy = 116
        pygame.draw.line(surface, MID_GRAY, (10, hy + 18), (WIDTH - 10, hy + 18))
        for col, txt in [(14, '#'), (40, 'ИМЯ'), (240, 'ОЧКИ'), (340, 'УР.'), (400, 'ДАТА')]:
            surface.blit(self.font_xs.render(txt, False, MID_GRAY), (col, hy))

        # Строки
        if not self.records:
            e = self.font_xs.render('РЕКОРДОВ НЕТ — ИГРАЙ ПЕРВЫМ!', False, MID_GRAY)
            surface.blit(e, e.get_rect(centerx=WIDTH // 2, top=200))
        else:
            for i, rec in enumerate(self.records):
                ry = 140 + i * 38
                bg = DARK_GRAY if i % 2 == 0 else BG
                pygame.draw.rect(surface, bg, (8, ry - 2, WIDTH - 16, 34))
                nc = tc if i == 0 else WHITE
                for col, val in [
                    (14,  str(i + 1)),
                    (40,  rec['name'][:12]),
                    (240, str(rec['score'])),
                    (340, str(rec['level'])),
                    (400, rec['date']),
                ]:
                    c = nc if col == 40 and i == 0 else (WHITE if col != 400 else MID_GRAY)
                    surface.blit(self.font_xs.render(val, False, c), (col, ry + 8))

        # Кнопка назад
        back  = self._back_rect()
        hov   = back.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, DARK_GRAY if hov else BG, back, border_radius=10)
        pygame.draw.rect(surface, WHITE if hov else MID_GRAY, back, 2, border_radius=10)
        bt = self.font_sm.render('[ НАЗАД ]', False, WHITE)
        surface.blit(bt, bt.get_rect(center=back.center))
