# settings.py — константы мобильной версии NeuroPix
# Портретная ориентация 480×854 (базовое разрешение, масштабируется на устройстве)

import pygame

WIDTH  = 480
HEIGHT = 854
FPS    = 60
TITLE  = "NeuroPix"

# ─── Цвета ───────────────────────────────────────────────────────────────────
BG        = (10,  10,  15)
WHITE     = (255, 255, 255)
DARK_GRAY = (30,  30,  40)
MID_GRAY  = (60,  60,  70)
DIM       = (40,  40,  50)
YELLOW    = (255, 220,  40)

BLUE        = (17,  102, 255)
BLUE_DIM    = (26,  74,  138)
BLUE_DARK   = (6,   13,  26)
BLUE_BRIGHT = (136, 187, 255)

RED        = (255, 34,  51)
RED_DIM    = (138, 26,  34)
RED_DARK   = (26,  6,   8)
RED_BRIGHT = (255, 136, 136)

GREEN        = (34,  204, 34)
GREEN_DIM    = (26,  90,  26)
GREEN_DARK   = (6,   13,  8)
GREEN_BRIGHT = (136, 255, 136)

# ─── Шрифты — увеличены для мобильного экрана ───────────────────────────────
FONT_XS = 10   # был 8
FONT_SM = 14   # был 12
FONT_MD = 20   # был 16
FONT_LG = 28   # был 24
FONT_XL = 38   # был 32

# ─── Минимальный размер touch-цели (px) ─────────────────────────────────────
TOUCH_MIN = 60

# ─── Состояния ───────────────────────────────────────────────────────────────
STATE_MENU         = "menu"
STATE_MOZGOBLOK    = "mozgoblok"
STATE_ECHORAD      = "echorad"
STATE_PROSTRANSTVO = "prostranstvo"
STATE_RECORDS      = "records"
STATE_NAME_INPUT   = "name_input"


def get_font(size: int) -> pygame.font.Font:
    """Пиксельный шрифт или системный запасной."""
    try:
        return pygame.font.Font("assets/font_pixel.ttf", size)
    except Exception:
        return pygame.font.SysFont("couriernew", size, bold=True)
