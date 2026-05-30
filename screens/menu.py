# screens/menu.py — главное меню мобильной версии (вертикальный макет)

import pygame
import math
from settings import (
    WIDTH, HEIGHT,
    BG, WHITE, DARK_GRAY, MID_GRAY, DIM,
    BLUE, BLUE_DIM, BLUE_DARK, BLUE_BRIGHT,
    RED,  RED_DIM,  RED_DARK,
    GREEN, GREEN_DIM, GREEN_DARK, GREEN_BRIGHT,
    FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL,
    STATE_MOZGOBLOK, STATE_ECHORAD, STATE_PROSTRANSTVO,
    STATE_RECORDS,
    get_font,
)
from utils import StarField, ConfirmDialog, TouchState


class MenuScreen:
    """Главное меню — вертикальные карточки, управление касаниями."""

    CARDS = [
        {
            'key': STATE_MOZGOBLOK,
            'label': 'GAME 01', 'name': 'МОЗГОБЛОК',
            'desc': 'Лови блоки. Продолжи числовой ряд.',
            'color': BLUE, 'dim': BLUE_DIM, 'dark': BLUE_DARK,
        },
        {
            'key': STATE_ECHORAD,
            'label': 'GAME 02', 'name': 'ЭХОРЯД',
            'desc': 'Запомни последовательность плиток.',
            'color': GREEN, 'dim': GREEN_DIM, 'dark': GREEN_DARK,
        },
        {
            'key': STATE_PROSTRANSTVO,
            'label': 'GAME 03', 'name': 'ПРОСТРАНСТВО ИКС',
            'desc': 'Поворот или отражение фигуры?',
            'color': RED, 'dim': RED_DIM, 'dark': RED_DARK,
        },
    ]

    CARD_W  = WIDTH - 40
    CARD_H  = 100
    CARD_X  = 20
    CARD_Y0 = 280    # y первой карточки

    def __init__(self, app):
        self.app         = app
        self.stars       = StarField(40)
        self.logo_angle  = 0.0
        self.quit_dialog: ConfirmDialog | None = None
        self.seen_this_session: set = set()

        self.font_xs = get_font(FONT_XS)
        self.font_sm = get_font(FONT_SM)
        self.font_md = get_font(FONT_MD)
        self.font_lg = get_font(FONT_LG)
        self.font_xl = get_font(FONT_XL)

    def on_enter(self, data: dict):
        self.quit_dialog = None
        last = self.app.db.get_last_player()
        self.player_name  = last or '---'
        self.player_total = self.app.db.get_player_total(self.player_name) if last else 0

    def _card_rect(self, i: int) -> pygame.Rect:
        gap = 14
        y   = self.CARD_Y0 + i * (self.CARD_H + gap)
        return pygame.Rect(self.CARD_X, y, self.CARD_W, self.CARD_H)

    def _records_rect(self):
        return pygame.Rect(WIDTH // 2 - 160, HEIGHT - 130, 320, 56)

    def _exit_rect(self):
        return pygame.Rect(WIDTH // 2 - 120, HEIGHT - 62, 240, 48)

    # ── Обработка событий ────────────────────────────────────────────────────

    def handle_event(self, event):
        if self.quit_dialog:
            self.quit_dialog.handle_event(event)
            return

        pos = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x * WIDTH), int(event.y * HEIGHT))

        if pos:
            for i, card in enumerate(self.CARDS):
                if self._card_rect(i).collidepoint(pos):
                    self._start_game(card['key'])
                    return
            if self._records_rect().collidepoint(pos):
                self.app.change_state(STATE_RECORDS)
            elif self._exit_rect().collidepoint(pos):
                self._ask_quit()

    def _start_game(self, state: str):
        self.seen_this_session.add(state)
        self.app.change_state(state)

    def _ask_quit(self):
        import sys
        self.quit_dialog = ConfirmDialog(
            'ВЫЙТИ ИЗ ИГРЫ?',
            on_yes=lambda: (pygame.quit(), sys.exit()),
            on_no=lambda: setattr(self, 'quit_dialog', None),
        )

    # ── Обновление ───────────────────────────────────────────────────────────

    def update(self, dt: float):
        self.stars.update(dt)
        self.logo_angle = (self.logo_angle + 25 * dt) % 360

    # ── Отрисовка ────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        surface.fill(BG)
        self.stars.draw(surface)
        self._draw_logo(surface)
        self._draw_player_bar(surface)
        self._draw_cards(surface)
        self._draw_bottom_btns(surface)

        vs = self.font_xs.render('v1.0 mobile', False, (30, 30, 40))
        surface.blit(vs, vs.get_rect(right=WIDTH - 6, bottom=HEIGHT - 4))

        if self.quit_dialog:
            self.quit_dialog.draw(surface)

    def _draw_logo(self, surface: pygame.Surface):
        cx, cy = WIDTH // 2, 100
        r      = 50
        offset = math.radians(self.logo_angle)
        arc_r  = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        for i, color in enumerate([BLUE, RED, GREEN]):
            s = math.radians(i * 120) + offset
            pygame.draw.arc(surface, color, arc_r, s, s + math.radians(120), 12)
        pygame.draw.circle(surface, BG, (cx, cy), 32)
        t1 = self.font_xs.render('NEURO', False, WHITE)
        t2 = self.font_xs.render('PIX',   False, WHITE)
        surface.blit(t1, t1.get_rect(centerx=cx, centery=cy - 7))
        surface.blit(t2, t2.get_rect(centerx=cx, centery=cy + 7))

        sub = self.font_xs.render('BRAIN  TRAINING  COLLECTION', False, MID_GRAY)
        surface.blit(sub, sub.get_rect(centerx=cx, top=cy + r + 10))

    def _draw_player_bar(self, surface: pygame.Surface):
        y   = 210
        txt = f'{self.player_name:<10}   TOTAL: {self.player_total:06d}'
        s   = self.font_xs.render(txt, False, MID_GRAY)
        surface.blit(s, s.get_rect(centerx=WIDTH // 2, centery=y))

    def _draw_cards(self, surface: pygame.Surface):
        mx, my = pygame.mouse.get_pos()
        for i, card in enumerate(self.CARDS):
            rect   = self._card_rect(i)
            hovered = rect.collidepoint(mx, my)
            color  = card['color']
            dim    = card['dim']
            dark   = card['dark']

            pygame.draw.rect(surface, dark, rect, border_radius=8)
            pygame.draw.rect(surface, color if hovered else dim, rect,
                             2, border_radius=8)

            # Иконка (3 полоски ≈ пиксельная иконка)
            icon_x = rect.x + 14
            icon_y = rect.y + rect.h // 2 - 12
            for j in range(3):
                w = [28, 20, 14][j]
                c = color if j == 0 else (dim if j == 1 else MID_GRAY)
                pygame.draw.rect(surface, c,
                                 (icon_x, icon_y + j * 10, w, 7), border_radius=2)

            # Текст карточки
            tx = icon_x + 40
            lbl = self.font_xs.render(card['label'], False, color)
            surface.blit(lbl, (tx, rect.y + 20))

            nm = self.font_sm.render(card['name'], False, WHITE)
            surface.blit(nm, (tx, rect.y + 36))

            ds = self.font_xs.render(card['desc'], False, DIM)
            surface.blit(ds, (tx, rect.y + 56))

            # Полоска снизу карточки
            pygame.draw.rect(surface, color,
                             (rect.x + 2, rect.bottom - 4, int(rect.w * 0.6), 3),
                             border_radius=2)

    def _draw_bottom_btns(self, surface: pygame.Surface):
        mx, my = pygame.mouse.get_pos()

        rec_r = self._records_rect()
        ext_r = self._exit_rect()

        for rect, label, color in [
            (rec_r, '[ РЕКОРДЫ ]',  MID_GRAY),
            (ext_r, '[ ВЫХОД ]',    DIM),
        ]:
            hov = rect.collidepoint(mx, my)
            pygame.draw.rect(surface, DARK_GRAY if hov else BG, rect, border_radius=8)
            pygame.draw.rect(surface, MID_GRAY if hov else DIM, rect, 1, border_radius=8)
            t = self.font_sm.render(label, False, WHITE if hov else color)
            surface.blit(t, t.get_rect(center=rect.center))
