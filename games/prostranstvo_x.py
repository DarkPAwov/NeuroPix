# games/prostranstvo_x.py — ПространствоИкс (мобильная версия)
# Большие кнопки A/B/C/D внизу экрана

import pygame
import random
import copy
from settings import (
    WIDTH, HEIGHT,
    BG, WHITE, DARK_GRAY, MID_GRAY, DIM,
    RED, RED_DIM, RED_DARK, RED_BRIGHT,
    GREEN, GREEN_DIM, GREEN_DARK, GREEN_BRIGHT,
    FONT_XS, FONT_SM, FONT_MD, FONT_LG,
    STATE_MENU, STATE_NAME_INPUT,
    get_font,
)
from utils import StarField, Flash, ConfirmDialog, HUD, TouchState

FIGURES = [
    [[1,1,0,0,0],[0,1,0,0,0],[0,1,1,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    [[1,1,1,0,0],[1,0,0,0,0],[1,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    [[0,1,1,0,0],[0,1,0,0,0],[1,1,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    [[1,1,0,0,0],[0,1,0,0,0],[0,1,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    [[1,0,0,0,0],[1,1,0,0,0],[0,1,0,0,0],[0,1,0,0,0],[0,0,0,0,0]],
    [[1,1,1,0,0],[0,1,0,0,0],[0,1,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    [[1,1,0,0,0],[1,0,0,0,0],[1,1,0,0,0],[0,0,0,0,0],[0,0,0,0,0]],
    [[1,0,0,0,0],[1,0,0,0,0],[1,1,0,0,0],[0,1,0,0,0],[0,0,0,0,0]],
]

def _t5(g): r=[list(row) for row in g]; [r[i].extend([0]*(5-len(r[i]))) for i in range(len(r))]; r.extend([[0]*5]*(5-len(r))); return [row[:5] for row in r[:5]]
def rotate90(g):  return _t5(list(zip(*g[::-1])))
def rotate180(g): return rotate90(rotate90(g))
def rotate270(g): return rotate90(rotate90(rotate90(g)))
def mirror_h(g):  return _t5([row[::-1] for row in g])

TRANSFORMS = {'rotate90': rotate90, 'rotate180': rotate180,
               'rotate270': rotate270, 'mirror_h': mirror_h}
LABELS = {'rotate90': 'ПОВОРОТ 90°', 'rotate180': 'ПОВОРОТ 180°',
          'rotate270': 'ПОВОРОТ 270°', 'mirror_h': 'ОТРАЖЕНИЕ'}
KEYS   = ['rotate90', 'rotate180', 'rotate270', 'mirror_h']
ABCD   = ['A', 'B', 'C', 'D']

# Зона фигур (верхняя часть экрана)
FIG_ZONE_Y  = 60    # ниже HUD
FIG_ZONE_H  = 280
# Зона кнопок ответа (внизу)
BTN_ZONE_Y  = FIG_ZONE_Y + FIG_ZONE_H + 20
BTN_H       = 68
BTN_GAP     = 10
BTN_W       = WIDTH - 30


def _btn_rect(i: int) -> pygame.Rect:
    y = BTN_ZONE_Y + i * (BTN_H + BTN_GAP)
    return pygame.Rect(15, y, BTN_W, BTN_H)


CELL = 28; GAP = 2

def draw_fig(surf, fig, ox, oy, color, offset_x=0):
    for r in range(5):
        for c in range(5):
            if fig[r][c]:
                pygame.draw.rect(surf, color,
                                 (int(ox+offset_x)+c*(CELL+GAP),
                                  int(oy)+r*(CELL+GAP), CELL, CELL))


class ProstranstvoX:
    GAME_KEY = 'prostranstvo'
    COLOR    = RED

    def __init__(self, app):
        self.app   = app
        self.hud   = HUD()
        self.touch = TouchState()
        self.font_xs = get_font(FONT_XS)
        self.font_sm = get_font(FONT_SM)
        self.font_lg = get_font(FONT_LG)
        self._reset()

    def _reset(self):
        self.stars    = StarField(30)
        self.score    = 0; self.lives = 3; self.level = 1
        self.current_fig  = None; self.transformed = None
        self.correct_answer = ''; self.options = []
        self.answered     = False; self.chosen = -1
        self.answer_timer = 0.0
        self.slide_x      = 0.0; self.sliding = False
        self.timer        = 0.0; self.max_time = 8.0
        self.screen_flash: Flash | None = None
        self.confirm: ConfirmDialog | None = None
        self.game_over = False
        self._gen()

    def on_enter(self, data): self._reset()

    def _gen(self):
        for _ in range(20):
            fig = copy.deepcopy(random.choice(FIGURES))
            key = random.choice(KEYS)
            tfig = TRANSFORMS[key](fig)
            if tfig != fig: break
        self.current_fig    = fig
        self.transformed    = tfig
        self.correct_answer = key
        self.options        = list(KEYS)
        self.answered = False; self.chosen = -1
        self.timer    = self._max_time(); self.max_time = self.timer
        self.slide_x  = float(WIDTH); self.sliding = True

    def _max_time(self):
        if self.level <= 3: return 8.0
        if self.level <= 6: return 6.0
        return 4.0

    def handle_event(self, event):
        self.touch.process(event)
        if self.confirm:
            self.confirm.handle_event(event); return
        if self.answered: return

        pos = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: pos = event.pos
        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x*WIDTH), int(event.y*HEIGHT))

        if pos:
            if pygame.Rect(0, 0, 60, 55).collidepoint(pos):
                self._show_confirm(); return
            for i in range(len(self.options)):
                if _btn_rect(i).collidepoint(pos):
                    self._check(i); return

    def _show_confirm(self):
        self.confirm = ConfirmDialog(
            'ВЫЙТИ В МЕНЮ?',
            on_yes=lambda: self.app.change_state(STATE_MENU),
            on_no=lambda: setattr(self, 'confirm', None),
        )

    def _check(self, idx):
        if self.answered or idx >= len(self.options): return
        self.answered = True; self.chosen = idx
        if self.options[idx] == self.correct_answer:
            self.score  += 20 + int(self.timer * 3)
            self.level   = self.score // 100 + 1
            self.screen_flash = Flash(GREEN_BRIGHT, 70, 0.3)
        else:
            self.lives -= 1
            self.screen_flash = Flash(RED, 90, 0.3)
            if self.lives <= 0: self.lives = 0; self.game_over = True
        self.answer_timer = 0.8

    def update(self, dt):
        if self.confirm: return
        self.stars.update(dt)
        if self.screen_flash:
            self.screen_flash.update(dt)
            if self.screen_flash.is_done(): self.screen_flash = None
        if self.sliding:
            self.slide_x -= 600 * dt
            if self.slide_x <= 0: self.slide_x = 0; self.sliding = False
        if self.answered:
            self.answer_timer -= dt
            if self.answer_timer <= 0:
                if self.game_over: self._end()
                else: self._gen()
        else:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = 0; self.answered = True; self.chosen = -1
                self.lives -= 1; self.screen_flash = Flash(RED, 80, 0.3)
                self.answer_timer = 0.8
                if self.lives <= 0: self.lives = 0; self.game_over = True

    def _end(self):
        self.app.change_state(STATE_NAME_INPUT,
            {'game': self.GAME_KEY, 'score': self.score,
             'level': self.level,   'color': self.COLOR})

    def draw(self, surface):
        surface.fill(BG)
        self.stars.draw(surface)

        ox = int(self.slide_x)

        # Заголовки зон фигур
        label_y = FIG_ZONE_Y + 2
        lf = self.font_xs
        ls = lf.render('[ ИСХОДНАЯ ]', False, RED)
        rs = lf.render('[ РЕЗУЛЬТАТ ]', False, WHITE)
        surface.blit(ls, ls.get_rect(centerx=WIDTH//4 + ox, top=label_y))
        surface.blit(rs, rs.get_rect(centerx=3*WIDTH//4 + ox, top=label_y))

        # Рамки зон
        fig_w = 5*(CELL+GAP)
        zone_w = WIDTH//2 - 20
        zone_h = FIG_ZONE_H - 24
        lzone = pygame.Rect(10 + ox, FIG_ZONE_Y + 18, zone_w, zone_h)
        rzone = pygame.Rect(WIDTH//2 + 10 + ox, FIG_ZONE_Y + 18, zone_w, zone_h)
        pygame.draw.rect(surface, DARK_GRAY, lzone, border_radius=4)
        pygame.draw.rect(surface, WHITE, lzone, 1, border_radius=4)
        pygame.draw.rect(surface, DARK_GRAY, rzone, border_radius=4)
        pygame.draw.rect(surface, WHITE, rzone, 1, border_radius=4)

        # Фигуры (центрированы в зонах)
        if self.current_fig:
            fig_x = lzone.x + (zone_w - fig_w) // 2
            fig_y = lzone.y + (zone_h - fig_w) // 2
            draw_fig(surface, self.current_fig, fig_x, fig_y, WHITE)

            fig_x2 = rzone.x + (zone_w - fig_w) // 2
            draw_fig(surface, self.transformed, fig_x2, fig_y, RED_BRIGHT)

        # Пунктирная ось между зонами
        ax = WIDTH // 2
        for y in range(FIG_ZONE_Y + 18, FIG_ZONE_Y + 18 + zone_h, 10):
            pygame.draw.line(surface, RED_DIM, (ax, y), (ax, min(y+6, FIG_ZONE_Y+18+zone_h)))

        # Кнопки ответа
        ci = self.options.index(self.correct_answer) if self.answered else -1
        for i, key in enumerate(self.options):
            r      = _btn_rect(i)
            label  = f'{ABCD[i]}: {LABELS[key]}'
            hov    = r.collidepoint(pygame.mouse.get_pos()) and not self.answered

            if self.answered and i == ci:
                bg_c, bd_c, tc = GREEN_DARK, GREEN, GREEN_BRIGHT
            elif self.answered and i == self.chosen and i != ci:
                bg_c, bd_c, tc = (40,6,6), RED_BRIGHT, RED_BRIGHT
            elif hov:
                bg_c, bd_c, tc = RED_DARK, RED, WHITE
            else:
                bg_c, bd_c, tc = RED_DARK, RED_DIM, MID_GRAY

            pygame.draw.rect(surface, bg_c, r, border_radius=8)
            pygame.draw.rect(surface, bd_c, r, 2, border_radius=8)
            t = self.font_sm.render(label, False, tc)
            surface.blit(t, t.get_rect(center=r.center))

        # Таймер-полоска
        timer_y = _btn_rect(3).bottom + 14
        bw  = WIDTH - 30
        rat = max(0.0, self.timer / max(self.max_time, 0.001))
        pygame.draw.rect(surface, DARK_GRAY, (15, timer_y, bw, 8))
        if rat > 0:
            tc = WHITE if rat > 0.5 else RED_DIM if rat > 0.2 else RED
            pygame.draw.rect(surface, tc, (15, timer_y, int(bw*rat), 8))

        if self.screen_flash: self.screen_flash.draw(surface)

        self.hud.draw(surface, self.score, self.lives, self.level,
                      self.COLOR, f'УРОВЕНЬ {self.level}')
        ms = self.font_xs.render('◄ МЕНЮ', False, MID_GRAY)
        surface.blit(ms, (6, 34))

        if self.confirm: self.confirm.draw(surface)
