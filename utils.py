# utils.py — вспомогательные классы для мобильной версии NeuroPix

import pygame
import random
import math
from settings import (
    WIDTH, HEIGHT,
    BG, WHITE, DARK_GRAY, MID_GRAY, DIM,
    FONT_XS, FONT_SM,
    get_font,
)


# ════════════════════════════════════════════════════════════════════════════
#  Обработка мультитач (FINGER-события Android + мышь для десктопа)
# ════════════════════════════════════════════════════════════════════════════

class TouchState:
    """
    Отслеживает позиции всех активных касаний.
    Работает через pygame.FINGER* на Android и через мышь на десктопе.
    """

    def __init__(self):
        self._fingers: dict = {}   # finger_id → (x, y) в пикселях

    def process(self, event):
        """Обновить состояние касаний по событию pygame."""
        if event.type == pygame.FINGERDOWN:
            fx = int(event.x * WIDTH)
            fy = int(event.y * HEIGHT)
            self._fingers[event.finger_id] = (fx, fy)
        elif event.type == pygame.FINGERUP:
            self._fingers.pop(event.finger_id, None)
        elif event.type == pygame.FINGERMOTION:
            fx = int(event.x * WIDTH)
            fy = int(event.y * HEIGHT)
            self._fingers[event.finger_id] = (fx, fy)

    def any_in_rect(self, rect: pygame.Rect) -> bool:
        """Есть ли хотя бы одно касание в данном прямоугольнике?"""
        return any(rect.collidepoint(pos) for pos in self._fingers.values())

    def clear(self):
        self._fingers.clear()

    def positions(self):
        return list(self._fingers.values())


# ════════════════════════════════════════════════════════════════════════════
#  Звёздное поле
# ════════════════════════════════════════════════════════════════════════════

class StarField:
    def __init__(self, count: int = 50):
        self.stars = [
            {
                'x':     random.randint(0, WIDTH),
                'y':     random.randint(0, HEIGHT),
                'size':  random.choice([1, 2]),
                'phase': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.5, 2.0),
            }
            for _ in range(count)
        ]

    def update(self, dt: float):
        for s in self.stars:
            s['phase'] += dt * s['speed']

    def draw(self, surface: pygame.Surface):
        for s in self.stars:
            b = int(100 + math.sin(s['phase']) * 80)
            b = max(30, min(220, b))
            pygame.draw.rect(surface, (b, b, b),
                             (int(s['x']), int(s['y']), s['size'], s['size']))


# ════════════════════════════════════════════════════════════════════════════
#  Вспышка экрана
# ════════════════════════════════════════════════════════════════════════════

class Flash:
    def __init__(self, color, alpha: int = 120, duration: float = 0.25,
                 rect: pygame.Rect = None):
        self.color     = color
        self.alpha     = float(alpha)
        self.max_alpha = float(alpha)
        self.duration  = duration
        self.elapsed   = 0.0
        self.rect      = rect

    def update(self, dt: float):
        self.elapsed += dt
        p = min(self.elapsed / max(self.duration, 0.001), 1.0)
        self.alpha = self.max_alpha * (1.0 - p)

    def draw(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
        target = self.rect or pygame.Rect(0, 0, WIDTH, HEIGHT)
        s = pygame.Surface((target.width, target.height), pygame.SRCALPHA)
        s.fill((*self.color, int(self.alpha)))
        surface.blit(s, target.topleft)

    def is_done(self) -> bool:
        return self.elapsed >= self.duration


# ════════════════════════════════════════════════════════════════════════════
#  Диалог подтверждения (сенсорный)
# ════════════════════════════════════════════════════════════════════════════

class ConfirmDialog:
    """Большие кнопки «ДА» / «НЕТ» — удобно для пальца."""

    BTN_W = 160
    BTN_H = 60

    def __init__(self, text: str, on_yes, on_no):
        self.text   = text
        self.on_yes = on_yes
        self.on_no  = on_no

    def _box(self):
        bw, bh = 380, 180
        return pygame.Rect(WIDTH // 2 - bw // 2, HEIGHT // 2 - bh // 2, bw, bh)

    def _btn_yes(self):
        box = self._box()
        return pygame.Rect(box.x + 20, box.bottom - self.BTN_H - 12,
                           self.BTN_W, self.BTN_H)

    def _btn_no(self):
        box = self._box()
        return pygame.Rect(box.right - self.BTN_W - 20, box.bottom - self.BTN_H - 12,
                           self.BTN_W, self.BTN_H)

    def handle_event(self, event):
        pos = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x * WIDTH), int(event.y * HEIGHT))

        if pos:
            if self._btn_yes().collidepoint(pos): self.on_yes()
            elif self._btn_no().collidepoint(pos):  self.on_no()

    def draw(self, surface: pygame.Surface):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 170))
        surface.blit(ov, (0, 0))

        box = self._box()
        pygame.draw.rect(surface, DARK_GRAY, box, border_radius=10)
        pygame.draw.rect(surface, WHITE, box, 2, border_radius=10)

        font = get_font(FONT_SM)
        ts   = font.render(self.text, False, WHITE)
        surface.blit(ts, ts.get_rect(centerx=WIDTH // 2, top=box.y + 20))

        for rect, label, color in [
            (self._btn_yes(), '[ ДА ]',  WHITE),
            (self._btn_no(),  '[ НЕТ ]', MID_GRAY),
        ]:
            pygame.draw.rect(surface, DARK_GRAY, rect, border_radius=8)
            pygame.draw.rect(surface, color, rect, 2, border_radius=8)
            t = font.render(label, False, color)
            surface.blit(t, t.get_rect(center=rect.center))


# ════════════════════════════════════════════════════════════════════════════
#  HUD — верхняя панель
# ════════════════════════════════════════════════════════════════════════════

class HUD:
    HUD_H = 50   # высота HUD-полоски

    def draw(self, surface: pygame.Surface,
             score: int, lives: int, level: int,
             color: tuple, extra_text: str = "", max_lives: int = 3):
        dark = tuple(max(0, c // 4) for c in color)
        pygame.draw.rect(surface, dark, (0, 0, WIDTH, self.HUD_H))
        pygame.draw.rect(surface, color, (0, self.HUD_H - 2, WIDTH, 2))

        font = get_font(FONT_XS)

        # Счёт
        sc = font.render(f'СЧЁТ: {score:05d}', False, WHITE)
        surface.blit(sc, (10, 18))

        # Extra по центру
        if extra_text:
            et = font.render(extra_text, False, color)
            surface.blit(et, et.get_rect(centerx=WIDTH // 2, centery=25))

        # Жизни
        hx = WIDTH - 10 - max_lives * 16
        for i in range(max_lives):
            c = WHITE if i < lives else DIM
            pygame.draw.rect(surface, c, (int(hx + i * 16), 20, 10, 10))

        # Уровень
        lvl = font.render(f'УР.{level:02d}', False, MID_GRAY)
        surface.blit(lvl, lvl.get_rect(right=hx - 8, centery=25))


# ════════════════════════════════════════════════════════════════════════════
#  Вспомогательные функции
# ════════════════════════════════════════════════════════════════════════════

def draw_touch_btn(surface, rect: pygame.Rect, label: str,
                   color: tuple, font, active: bool = False):
    """Нарисовать большую сенсорную кнопку."""
    bg = tuple(min(255, c + 30) for c in color) if active else tuple(c // 3 for c in color)
    pygame.draw.rect(surface, bg,    rect, border_radius=10)
    pygame.draw.rect(surface, color, rect, 2, border_radius=10)
    ts = font.render(label, False, WHITE)
    surface.blit(ts, ts.get_rect(center=rect.center))
