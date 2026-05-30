# screens/name_input.py — мобильный экран ввода имени (через IME Android)

import pygame
from settings import (
    WIDTH, HEIGHT,
    BG, WHITE, DARK_GRAY, MID_GRAY, DIM,
    FONT_XS, FONT_SM, FONT_MD, FONT_LG,
    STATE_MENU, STATE_RECORDS,
    get_font,
)
from utils import StarField


class NameInputScreen:
    MAX_LEN = 10

    def __init__(self, app):
        self.app    = app
        self.stars  = StarField(30)
        self.name   = ''
        self.cursor_t = 0.0
        self.game  = ''; self.score = 0; self.level = 1; self.color = WHITE
        self.font_xs = get_font(FONT_XS)
        self.font_sm = get_font(FONT_SM)
        self.font_md = get_font(FONT_MD)
        self.font_lg = get_font(FONT_LG)

    def on_enter(self, data: dict):
        self.game  = data.get('game', '')
        self.score = data.get('score', 0)
        self.level = data.get('level', 1)
        self.color = data.get('color', WHITE)
        last = self.app.db.get_last_player()
        self.name = last or ''
        self.cursor_t = 0.0
        # Запрашиваем клавиатуру Android через IME
        pygame.key.start_text_input()

    def _save_rect(self):
        return pygame.Rect(WIDTH // 2 - 170, HEIGHT // 2 + 100, 340, 64)

    def _skip_rect(self):
        return pygame.Rect(WIDTH // 2 - 130, HEIGHT // 2 + 180, 260, 50)

    def _input_rect(self):
        return pygame.Rect(WIDTH // 2 - 180, HEIGHT // 2 + 10, 360, 56)

    def handle_event(self, event):
        pos = None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
        elif event.type == pygame.FINGERDOWN:
            pos = (int(event.x * WIDTH), int(event.y * HEIGHT))

        if pos:
            if self._save_rect().collidepoint(pos): self._save()
            elif self._skip_rect().collidepoint(pos): self._skip()
            return

        # Ввод текста (физическая клавиатура или Android IME)
        if event.type == pygame.TEXTINPUT:
            for ch in event.text:
                if ch.isprintable() and len(self.name) < self.MAX_LEN:
                    self.name += ch.upper()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._save()

    def _save(self):
        pygame.key.stop_text_input()
        self.app.db.save_record(self.name, self.game, self.score, self.level)
        self.app.change_state(STATE_RECORDS, {'game': self.game})

    def _skip(self):
        pygame.key.stop_text_input()
        self.app.change_state(STATE_MENU)

    def update(self, dt: float):
        self.stars.update(dt)
        self.cursor_t += dt

    def draw(self, surface: pygame.Surface):
        surface.fill(BG)
        self.stars.draw(surface)

        # Заголовок
        title = self.font_lg.render('[ ИГРА ОКОНЧЕНА ]', False, WHITE)
        surface.blit(title, title.get_rect(centerx=WIDTH // 2, top=HEIGHT // 2 - 200))

        score_s = self.font_md.render(f'СЧЁТ:   {self.score:05d}', False, self.color)
        surface.blit(score_s, score_s.get_rect(centerx=WIDTH // 2, top=HEIGHT // 2 - 140))

        lvl_s = self.font_sm.render(f'УРОВЕНЬ: {self.level}', False, MID_GRAY)
        surface.blit(lvl_s, lvl_s.get_rect(centerx=WIDTH // 2, top=HEIGHT // 2 - 100))

        pygame.draw.line(surface, DIM,
                         (40, HEIGHT // 2 - 60), (WIDTH - 40, HEIGHT // 2 - 60))

        lbl = self.font_xs.render('ВВЕДИ ИМЯ (нажми на поле):', False, MID_GRAY)
        surface.blit(lbl, lbl.get_rect(centerx=WIDTH // 2, top=HEIGHT // 2 - 30))

        # Поле ввода
        ir = self._input_rect()
        pygame.draw.rect(surface, DARK_GRAY, ir, border_radius=8)
        pygame.draw.rect(surface, WHITE, ir, 2, border_radius=8)
        cursor = '|' if int(self.cursor_t * 2) % 2 == 0 else ''
        ns = self.font_md.render(self.name + cursor, False, WHITE)
        surface.blit(ns, ns.get_rect(center=ir.center))

        # Кнопка Сохранить
        save_r = self._save_rect()
        hov1   = save_r.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, self.color if hov1 else tuple(c//3 for c in self.color),
                         save_r, border_radius=10)
        pygame.draw.rect(surface, self.color, save_r, 2, border_radius=10)
        st = self.font_sm.render('[ СОХРАНИТЬ ]', False, WHITE)
        surface.blit(st, st.get_rect(center=save_r.center))

        # Кнопка Пропустить
        skip_r = self._skip_rect()
        hov2   = skip_r.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, MID_GRAY if hov2 else BG, skip_r, border_radius=8)
        pygame.draw.rect(surface, MID_GRAY, skip_r, 1, border_radius=8)
        skt = self.font_xs.render('[ ПРОПУСТИТЬ ]', False, MID_GRAY)
        surface.blit(skt, skt.get_rect(center=skip_r.center))
