# games/echorad.py — ЭхоРяд (мобильная версия, большие плитки)

import pygame
import random
from settings import (
    WIDTH, HEIGHT,
    BG, WHITE, DARK_GRAY, MID_GRAY, DIM,
    GREEN, GREEN_DIM, GREEN_DARK, GREEN_BRIGHT,
    RED, YELLOW,
    FONT_XS, FONT_SM, FONT_MD, FONT_LG,
    STATE_MENU, STATE_NAME_INPUT,
    get_font,
)
from utils import StarField, Flash, ConfirmDialog, HUD, TouchState

# Плитка 116×116, зазор 8 → 3×116 + 2×8 = 364px (влезает в 480)
TILE_SIZE = 116
TILE_GAP  = 8
GRID_TOTAL = 3 * TILE_SIZE + 2 * TILE_GAP   # 364
GRID_OX   = (WIDTH - GRID_TOTAL) // 2        # 58
GRID_OY   = 120   # y начала сетки (ниже HUD)


def tile_rect(idx: int) -> pygame.Rect:
    row = idx // 3; col = idx % 3
    x = GRID_OX + col * (TILE_SIZE + TILE_GAP)
    y = GRID_OY + row * (TILE_SIZE + TILE_GAP)
    return pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)


def tile_at(pos) -> int:
    for i in range(9):
        if tile_rect(i).collidepoint(pos): return i
    return -1


class EchoRad:
    GAME_KEY = 'echorad'
    COLOR    = GREEN

    def __init__(self, app):
        self.app   = app
        self.hud   = HUD()
        self.touch = TouchState()
        self.font_xs = get_font(FONT_XS)
        self.font_sm = get_font(FONT_SM)
        self.font_lg = get_font(FONT_LG)
        self._reset()

    def _reset(self):
        self.stars       = StarField(30)
        self.round_num   = 1
        self.score       = 0
        self.lives       = 3
        self.sequence    = []
        self.player_input= []
        self.phase       = 'prepare'
        self.phase_timer = 0.0
        self.show_index  = 0
        self.show_timer  = 0.0
        self.lit: set    = set()
        self.input_time  = 0.0
        self.max_input_t = 0.0
        self.tile_flashes: dict = {}
        self.screen_flash: Flash | None = None
        self.blink_t     = 0.0
        self.confirm: ConfirmDialog | None = None
        self.game_over   = False
        self._gen_seq()

    def on_enter(self, data): self._reset()

    def _gen_seq(self):
        length = min(2 + self.round_num - 1, 9)
        self.sequence     = [random.randint(0, 8) for _ in range(length)]
        self.player_input = []
        self.show_index   = 0
        self.lit          = set()
        self.phase        = 'prepare'
        self.phase_timer  = 1.5
        self.max_input_t  = len(self.sequence) * 2.8
        self.input_time   = self.max_input_t

    @property
    def _show_speed(self): return max(0.25, 0.8 - (self.round_num-1)*0.05)

    def handle_event(self, event):
        self.touch.process(event)
        if self.confirm:
            self.confirm.handle_event(event); return

        pos = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: pos = event.pos
        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x*WIDTH), int(event.y*HEIGHT))

        if pos:
            # Кнопка меню (верхний левый)
            if pygame.Rect(0, 0, 60, 55).collidepoint(pos):
                self._show_confirm(); return
            if self.phase == 'input':
                idx = tile_at(pos)
                if idx >= 0: self._check(idx)

    def _show_confirm(self):
        self.confirm = ConfirmDialog(
            'ВЫЙТИ В МЕНЮ?',
            on_yes=lambda: self.app.change_state(STATE_MENU),
            on_no=lambda: setattr(self, 'confirm', None),
        )

    def _check(self, idx):
        expected = self.sequence[len(self.player_input)]
        if idx == expected:
            self.player_input.append(idx)
            self.tile_flashes[idx] = Flash(GREEN_BRIGHT, 130, 0.25, tile_rect(idx))
            if len(self.player_input) == len(self.sequence):
                bonus = 50 if self.input_time > self.max_input_t * 0.5 else 0
                self.score += 10 * len(self.sequence) + bonus
                self.screen_flash = Flash(GREEN, 60, 0.3)
                self.phase = 'result'; self.phase_timer = 0.7
        else:
            self.tile_flashes[idx] = Flash(RED, 130, 0.3, tile_rect(idx))
            self.screen_flash = Flash(RED, 60, 0.25)
            self.lives -= 1
            self.phase = 'result'; self.phase_timer = 0.8
            if self.lives <= 0: self.lives = 0; self.game_over = True

    def update(self, dt):
        if self.confirm: return
        self.stars.update(dt); self.blink_t += dt

        done = [k for k, f in self.tile_flashes.items() if f.update(dt) or f.is_done()]
        for k in done: del self.tile_flashes[k]
        if self.screen_flash:
            self.screen_flash.update(dt)
            if self.screen_flash.is_done(): self.screen_flash = None

        if self.phase == 'prepare':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.phase = 'show'; self.show_index = 0
                self.show_timer = self._show_speed
                self.lit = {self.sequence[0]}

        elif self.phase == 'show':
            self.show_timer -= dt
            if self.show_timer <= 0:
                self.lit = set(); self.show_index += 1
                if self.show_index >= len(self.sequence):
                    self.phase = 'input'; self.input_time = self.max_input_t
                else:
                    self.show_timer = 0.15 + self._show_speed
                    self.lit = {self.sequence[self.show_index]}

        elif self.phase == 'input':
            self.input_time -= dt
            if self.input_time <= 0:
                self.lives -= 1; self.screen_flash = Flash(RED, 80, 0.3)
                self.phase = 'result'; self.phase_timer = 0.8
                if self.lives <= 0: self.lives = 0; self.game_over = True

        elif self.phase == 'result':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                if self.game_over: self._end()
                else: self.round_num += 1; self._gen_seq()

    def _end(self):
        self.app.change_state(STATE_NAME_INPUT,
            {'game': self.GAME_KEY, 'score': self.score,
             'level': self.round_num, 'color': self.COLOR})

    def draw(self, surface):
        surface.fill(BG)
        self.stars.draw(surface)

        # Сетка плиток
        font = self.font_xs
        for i in range(9):
            r      = tile_rect(i)
            active = i in self.lit
            pygame.draw.rect(surface, GREEN if active else DARK_GRAY, r, border_radius=6)
            pygame.draw.rect(surface,
                             GREEN_BRIGHT if active else MID_GRAY, r, 2, border_radius=6)
            # Номер плитки
            ns = font.render(str(i+1), False, DIM)
            surface.blit(ns, (r.x + 6, r.y + 6))
            if i in self.tile_flashes:
                self.tile_flashes[i].draw(surface)

        # Метка фазы
        label_y = GRID_OY - 32
        blink   = int(self.blink_t * 2) % 2 == 0
        if self.phase == 'prepare':
            t = self.font_xs.render(f'[ ГОТОВЬСЯ... {max(0,int(self.phase_timer)+1)} ]', False, DIM)
        elif self.phase == 'show':
            t = self.font_sm.render('[ ЗАПОМИНАЙ... ]', False, GREEN if blink else GREEN_DIM)
        elif self.phase == 'input':
            t = self.font_sm.render('[ ПОВТОРЯЙ! ]', False, WHITE)
        else:
            t = self.font_xs.render('', False, DIM)
        surface.blit(t, t.get_rect(centerx=WIDTH//2, centery=label_y))

        # Прогресс и таймер
        grid_bottom = GRID_OY + GRID_TOTAL
        if self.phase == 'input':
            prog = self.font_xs.render(
                f'{len(self.player_input)} / {len(self.sequence)}', False, MID_GRAY)
            surface.blit(prog, prog.get_rect(centerx=WIDTH//2, top=grid_bottom + 12))

            ratio = max(0.0, self.input_time / max(self.max_input_t, 0.001))
            bw    = WIDTH - 40
            color = GREEN if ratio > 0.5 else YELLOW if ratio > 0.2 else RED
            pygame.draw.rect(surface, DARK_GRAY, (20, grid_bottom + 36, bw, 8))
            if ratio > 0:
                pygame.draw.rect(surface, color,
                                 (20, grid_bottom + 36, int(bw * ratio), 8))

        if self.screen_flash: self.screen_flash.draw(surface)

        self.hud.draw(surface, self.score, self.lives, self.round_num,
                      self.COLOR, f'РАУНД {self.round_num}')
        # Кнопка меню
        ms = self.font_xs.render('◄ МЕНЮ', False, MID_GRAY)
        surface.blit(ms, (6, 34))

        if self.confirm: self.confirm.draw(surface)
