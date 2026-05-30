# games/mozgoblok.py — МозгоБлок (мобильная версия с сенсорным управлением)
# Управление: два больших касания ← / → внизу экрана

import pygame
import random
import math
from settings import (
    WIDTH, HEIGHT,
    BG, WHITE, DARK_GRAY, MID_GRAY, DIM,
    BLUE, BLUE_DIM, BLUE_BRIGHT, RED, RED_BRIGHT,
    FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL,
    STATE_MENU, STATE_NAME_INPUT,
    get_font,
)
from utils import StarField, Flash, ConfirmDialog, HUD, TouchState, draw_touch_btn

# Высота зоны сенсорных кнопок внизу экрана
CTRL_H   = 120
CTRL_Y   = HEIGHT - CTRL_H
LEFT_BTN = pygame.Rect(0,        CTRL_Y, WIDTH // 2, CTRL_H)
RIGHT_BTN= pygame.Rect(WIDTH//2, CTRL_Y, WIDTH // 2, CTRL_H)


# ── PatternGenerator ─────────────────────────────────────────────────────────

class PatternGenerator:
    def generate(self, level: int) -> dict:
        types = ['arithmetic', 'even_odd', 'multiples']
        if level >= 3: types.append('geometric')
        if level >= 5: types.append('fibonacci')
        kind = random.choice(types)
        seq, ans = getattr(self, f'_gen_{kind}')(level)
        return {'sequence': seq, 'answer': ans, 'wrongs': self._wrongs(ans, seq)}

    def _gen_arithmetic(self, lv):
        step = random.randint(1, max(1, 1 + lv // 3 * 4))
        s    = random.randint(1, 20)
        n    = random.randint(3, 4)
        seq  = [s + step * i for i in range(n)]
        return seq, s + step * n

    def _gen_geometric(self, lv):
        r = random.choice([2, 3])
        s = random.randint(1, 4)
        n = random.randint(3, 4)
        seq = [s * r ** i for i in range(n)]
        return seq, s * r ** n

    def _gen_even_odd(self, lv):
        s = random.randint(1, 18)
        if random.random() < 0.5 and s % 2 != 0: s += 1
        n = random.randint(3, 4)
        return [s + 2 * i for i in range(n)], s + 2 * n

    def _gen_multiples(self, lv):
        b = random.choice([2, 3, 4, 5])
        n = random.randint(3, 4)
        return [b * (i + 1) for i in range(n)], b * (n + 1)

    def _gen_fibonacci(self, lv):
        a, b = random.randint(1, 4), random.randint(1, 4)
        return [a, b, a + b, a + 2 * b], 2 * a + 3 * b

    def _wrongs(self, ans, seq):
        forbidden = set(seq) | {ans}
        ws = set()
        for _ in range(300):
            if len(ws) == 3: break
            c = ans + random.randint(1, 5) * random.choice([-1, 1])
            if c > 0 and c not in forbidden:
                ws.add(c); forbidden.add(c)
        f = 1
        while len(ws) < 3:
            if f not in forbidden: ws.add(f)
            f += 1
        return list(ws)


# ── Block ─────────────────────────────────────────────────────────────────────

class Block:
    W, H = 66, 48

    def __init__(self, x, value, speed, is_correct):
        self.x, self.y = float(x), float(-self.H - random.randint(0, 30))
        self.value, self.speed, self.is_correct = value, speed, is_correct
        self.active = True

    @property
    def rect(self): return pygame.Rect(int(self.x), int(self.y), self.W, self.H)

    def update(self, dt):
        self.y += self.speed * dt
        if self.y > HEIGHT: self.active = False

    def draw(self, surface, font):
        if not self.active: return
        r = self.rect
        pygame.draw.rect(surface, BG,       r, border_radius=4)
        pygame.draw.rect(surface, BLUE_DIM, r, 2, border_radius=4)
        t = font.render(str(self.value), False, WHITE)
        surface.blit(t, t.get_rect(center=r.center))


# ── Platform ──────────────────────────────────────────────────────────────────

class Platform:
    W, H  = 110, 14
    SPEED = 300
    MIN_X = 10
    MAX_X = WIDTH - 10 - W
    Y     = CTRL_Y - 20

    def __init__(self):
        self.x = float(WIDTH // 2 - self.W // 2)
        self.shake_t = 0.0

    @property
    def rect(self):
        dx = int(5 * math.sin(self.shake_t * 35)) if self.shake_t > 0 else 0
        return pygame.Rect(int(self.x) + dx, self.Y, self.W, self.H)

    def move(self, direction, dt):
        self.x = max(self.MIN_X, min(self.MAX_X, self.x + direction * self.SPEED * dt))

    def shake(self): self.shake_t = 0.3

    def update(self, dt):
        if self.shake_t > 0: self.shake_t = max(0.0, self.shake_t - dt)

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, WHITE, r, border_radius=4)
        for i in range(3):
            pygame.draw.rect(surface, BLUE_BRIGHT,
                             (r.x + 10 + i * (r.w // 3), r.y - 5, 5, 5))


# ── MozgoBlok ────────────────────────────────────────────────────────────────

class MozgoBlok:
    GAME_KEY = 'mozgoblok'
    COLOR    = BLUE

    def __init__(self, app):
        self.app = app
        self.hud = HUD()
        self.gen = PatternGenerator()
        self.touch = TouchState()
        self.font_md = get_font(FONT_MD)
        self.font_lg = get_font(FONT_LG)
        self.font_xs = get_font(FONT_XS)
        self._reset()

    def _reset(self):
        self.stars    = StarField(35)
        self.platform = Platform()
        self.blocks   = []
        self.score = 0; self.lives = 3; self.level = 1; self.combo = 1
        self.pattern  = {}
        self.flash: Flash | None    = None
        self.confirm: ConfirmDialog | None = None
        self.combo_text  = ''; self.combo_timer = 0.0
        self.paused    = False
        self.game_over = False
        self._spawn()

    def on_enter(self, data): self._reset()

    def _spawn(self):
        self.pattern = self.gen.generate(self.level)
        speed        = 100 + (self.level - 1) * 22
        vals = [(self.pattern['answer'], True)] + [(w, False) for w in self.pattern['wrongs']]
        random.shuffle(vals)
        margin = 8
        zw     = (WIDTH - 2 * margin) // 4
        xs     = [margin + i * zw + random.randint(0, max(0, zw - Block.W))
                  for i in range(4)]
        self.blocks = [Block(xs[i], v, speed, f) for i, (v, f) in enumerate(vals)]

    def handle_event(self, event):
        # Сенсор для мультитач
        self.touch.process(event)

        if self.confirm:
            self.confirm.handle_event(event)
            return

        pos = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x * WIDTH), int(event.y * HEIGHT))

        if pos:
            # Кнопка паузы (верхний правый угол)
            if pygame.Rect(WIDTH - 60, 0, 60, 55).collidepoint(pos):
                self.paused = not self.paused
            # Кнопка «назад» (верхний левый)
            if pygame.Rect(0, 0, 60, 55).collidepoint(pos):
                self._show_confirm()

    def _show_confirm(self):
        self.paused = True
        self.confirm = ConfirmDialog(
            'ВЫЙТИ В МЕНЮ?',
            on_yes=lambda: self.app.change_state(STATE_MENU),
            on_no=self._close_confirm,
        )

    def _close_confirm(self):
        self.confirm = None; self.paused = False

    def update(self, dt):
        self.touch.process(pygame.event.Event(pygame.NOEVENT))  # обновление не нужно
        if self.confirm or self.paused or self.game_over: return

        self.stars.update(dt)
        self.platform.update(dt)

        # Сенсорное движение платформы
        if self.touch.any_in_rect(LEFT_BTN)  or pygame.key.get_pressed()[pygame.K_LEFT]:
            self.platform.move(-1, dt)
        if self.touch.any_in_rect(RIGHT_BTN) or pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.platform.move(1, dt)

        if self.flash:
            self.flash.update(dt)
            if self.flash.is_done(): self.flash = None

        if self.combo_timer > 0: self.combo_timer -= dt

        pr = self.platform.rect
        for block in self.blocks:
            if not block.active: continue
            block.update(dt)
            if block.rect.colliderect(pr):
                block.active = False
                (self._on_correct if block.is_correct else self._on_wrong)()
            elif not block.active and block.is_correct:
                self._on_wrong()

        if all(not b.active for b in self.blocks) and not self.game_over:
            self._spawn()

    def _on_correct(self):
        self.score += 10 * self.combo; self.combo += 1
        self.level  = self.score // 300 + 1
        self.flash  = Flash(BLUE_BRIGHT, 70, 0.2)
        if self.combo > 2:
            self.combo_text  = f'x{self.combo-1} COMBO!'
            self.combo_timer = 1.0
        for b in self.blocks: b.active = False

    def _on_wrong(self):
        self.lives -= 1; self.combo = 1
        self.flash  = Flash(RED, 90, 0.25)
        self.platform.shake()
        if self.lives <= 0:
            self.lives = 0; self.game_over = True
            self.app.change_state(STATE_NAME_INPUT,
                {'game': self.GAME_KEY, 'score': self.score,
                 'level': self.level,   'color': self.COLOR})
        else:
            for b in self.blocks: b.active = False

    def draw(self, surface):
        surface.fill(BG)
        self.stars.draw(surface)

        # Боковые рамки
        pygame.draw.line(surface, BLUE_DIM, (4, 50), (4, CTRL_Y))
        pygame.draw.line(surface, BLUE_DIM, (WIDTH-4, 50), (WIDTH-4, CTRL_Y))

        for b in self.blocks: b.draw(surface, self.font_md)
        self.platform.draw(surface)

        # HUD
        seq_s = '  '.join(str(n) for n in self.pattern.get('sequence', [])) + '  ?'
        self.hud.draw(surface, self.score, self.lives, self.level, self.COLOR, seq_s)

        # Кнопки навигации в HUD
        self.font_xs.render('◄', False, MID_GRAY)
        back_s  = self.font_xs.render('◄ МЕНЮ', False, MID_GRAY)
        pause_s = self.font_xs.render('II' if not self.paused else '▶', False, MID_GRAY)
        surface.blit(back_s,  (6,  34))
        surface.blit(pause_s, (WIDTH - pause_s.get_width() - 6, 34))

        # Сенсорные кнопки движения
        f_left  = get_font(FONT_XL)
        f_right = get_font(FONT_XL)
        lact = self.touch.any_in_rect(LEFT_BTN)
        ract = self.touch.any_in_rect(RIGHT_BTN)
        draw_touch_btn(surface, LEFT_BTN,  '←', BLUE, f_left,  lact)
        draw_touch_btn(surface, RIGHT_BTN, '→', BLUE, f_right, ract)

        # Разделитель между кнопками
        pygame.draw.line(surface, BLUE_DIM,
                         (WIDTH//2, CTRL_Y), (WIDTH//2, HEIGHT), 1)

        if self.flash: self.flash.draw(surface)

        if self.combo_timer > 0:
            ct = self.font_lg.render(self.combo_text, False, BLUE_BRIGHT)
            ct.set_alpha(int(255 * min(1.0, self.combo_timer / 0.5)))
            surface.blit(ct, ct.get_rect(centerx=WIDTH//2, centery=HEIGHT//2))

        if self.paused and not self.confirm:
            self._draw_pause(surface)
        if self.confirm:
            self.confirm.draw(surface)

    def _draw_pause(self, surface):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        surface.blit(ov, (0, 0))
        pt = get_font(FONT_LG).render('[ ПАУЗА ]', False, BLUE)
        surface.blit(pt, pt.get_rect(centerx=WIDTH//2, centery=HEIGHT//2 - 40))
        # Большие кнопки
        cont_r = pygame.Rect(WIDTH//2 - 140, HEIGHT//2 + 10, 280, 60)
        menu_r = pygame.Rect(WIDTH//2 - 140, HEIGHT//2 + 84, 280, 60)
        fs = get_font(FONT_SM)
        for r, lbl in [(cont_r, '[ ПРОДОЛЖИТЬ ]'), (menu_r, '[ В МЕНЮ ]')]:
            pygame.draw.rect(surface, DARK_GRAY, r, border_radius=10)
            pygame.draw.rect(surface, BLUE, r, 2, border_radius=10)
            t = fs.render(lbl, False, WHITE)
            surface.blit(t, t.get_rect(center=r.center))

        pos = pygame.mouse.get_pos()
        if event := getattr(self, '_pause_event', None):
            pass
        # Обрабатываем клик по кнопкам паузы через handle_event
