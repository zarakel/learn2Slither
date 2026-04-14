"""
display.py — Nokia 3310-style UI for Learn2Slither
Drop this file at the root of your project alongside main.py.
Usage: replace Pygame logic in main.py with NokiaUI.
"""

import pygame
import os
from dataclasses import dataclass, field
from typing import List
from environment.board import Cell

# ---------------------------------------------------------------------------
# PALETTE — faithful Nokia 3310 4-shade green
# ---------------------------------------------------------------------------
BG = (155, 188, 15)  # lightest — screen background
LITE = (139, 172, 15)  # grid lines / muted text
MID = (48, 98, 48)  # secondary text / borders
DARK = (15, 56, 15)  # primary foreground

# ---------------------------------------------------------------------------
# PIXEL-ART SPRITES  (8×8, 1 = DARK, 0 = transparent, 2 = LITE accent)
# ---------------------------------------------------------------------------

HEAD_R = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 2, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [1, 1, 2, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

BODY_H = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 0],
    [0, 1, 0, 1, 1, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 1, 0],
    [0, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 1, 1, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

BODY_V = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 0, 1, 0],
    [0, 1, 1, 1, 0, 1, 1, 0],
    [0, 1, 1, 0, 1, 1, 1, 0],
    [0, 1, 0, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

APPLE = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
]

SHROOM = [
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 1, 1, 0, 0, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
]

# ---------------------------------------------------------------------------
# SPRITE RENDERING
# ---------------------------------------------------------------------------


def _blit_sprite(
    surface: pygame.Surface, pattern: list, ox: int, oy: int, scale: int = 1
):
    """Draw an 8×8 pixel-art pattern onto surface at (ox, oy)."""
    for ry, row in enumerate(pattern):
        for rx, c in enumerate(row):
            if c == 0:
                continue
            color = LITE if c == 2 else DARK
            rect = pygame.Rect(ox + rx * scale, oy + ry * scale, scale, scale)
            pygame.draw.rect(surface, color, rect)


def _make_sprite(pattern: list, scale: int = 1) -> pygame.Surface:
    size = 8 * scale
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    _blit_sprite(surf, pattern, 0, 0, scale)
    return surf


def _flip_h(surf: pygame.Surface) -> pygame.Surface:
    return pygame.transform.flip(surf, True, False)


# ---------------------------------------------------------------------------
# BITMAP FONT (5×7 uppercase + digits + punctuation)
# ---------------------------------------------------------------------------

_FONT_DATA = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10011", "10101", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "00110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "00100", "00100", "00100"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    ">": ["10000", "01000", "00100", "00010", "00100", "01000", "10000"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00100", "01000", "10000", "00000", "00000"],
    "[": ["01110", "01000", "01000", "01000", "01000", "01000", "01110"],
    "]": ["01110", "00010", "00010", "00010", "00010", "00010", "01110"],
    "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"],
    "%": ["11001", "11010", "00100", "01000", "10110", "01110", "00000"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
}


def draw_text(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    color=DARK,
    scale: int = 1,
):
    """Render pixel-art text, uppercase only."""
    cx = x
    for ch in text.upper():
        glyph = _FONT_DATA.get(ch, _FONT_DATA[" "])
        for ry, row in enumerate(glyph):
            for rx, bit in enumerate(row):
                if bit == "1":
                    pygame.draw.rect(
                        surface,
                        color,
                        (cx + rx * scale, y + ry * scale, scale, scale),
                    )
        cx += (5 + 1) * scale
    return cx


def text_width(text: str, scale: int = 1) -> int:
    return len(text) * 6 * scale


# ---------------------------------------------------------------------------
# SESSION STATS
# ---------------------------------------------------------------------------


@dataclass
class SessionRecord:
    session: int
    length: int
    duration: int
    epsilon: float


@dataclass
class Stats:
    records: List[SessionRecord] = field(default_factory=list)

    def push(self, session, length, duration, epsilon):
        self.records.append(SessionRecord(session, length, duration, epsilon))

    @property
    def max_length(self):
        return max((r.length for r in self.records), default=0)

    @property
    def max_duration(self):
        return max((r.duration for r in self.records), default=0)

    @property
    def avg_length(self):
        if not self.records:
            return 0.0
        return sum(r.length for r in self.records) / len(self.records)

    @property
    def total_sessions(self):
        return len(self.records)


# ---------------------------------------------------------------------------
# NOKIA UI
# ---------------------------------------------------------------------------

CELL_PX = 8  # pixels per cell (unscaled)
SCALE = 2  # window scale factor  → effective cell = 16px
HUD_TOP = 12  # rows reserved for top HUD
HUD_BOT = 12  # rows reserved for bottom HUD


class NokiaUI:
    """
    Full-screen Nokia 3310 Pygame UI for Learn2Slither.

    Screens:
      'lobby'   title screen
      'config'  parameter editor
      'game'    live game view
      'results' post-session statistics
    """

    # --- public config (can be mutated before run()) ---
    sessions: int = 100
    board_size: int = 10
    visual_on: bool = True
    learn_on: bool = True
    save_path: str = ""
    step_by_step: bool = False

    def __init__(self, board_size: int = 10):
        self.board_size = board_size
        self.stats = Stats()
        self._screen_id = "lobby"
        self._config_idx = 0
        self._surface = None
        self._clock = None
        self._sprites = {}

        # game-loop state updated by caller
        self.current_session = 0
        self.current_length = 0
        self.current_duration = 0
        self.current_epsilon = 1.0
        self.current_score = 0

    # ------------------------------------------------------------------
    # INIT / TEARDOWN
    # ------------------------------------------------------------------

    def init(self):
        pygame.init()
        pygame.display.set_caption("Learn2Slither")
        w = self.board_size * CELL_PX * SCALE
        h = self.board_size * CELL_PX * SCALE + (HUD_TOP + HUD_BOT) * SCALE
        self._surface = pygame.display.set_mode((w, h))
        self._clock = pygame.time.Clock()
        self._build_sprites()

    def quit(self):
        pygame.quit()

    def _build_sprites(self):
        s = SCALE
        self._sprites["head_r"] = _make_sprite(HEAD_R, s)
        self._sprites["head_l"] = _flip_h(self._sprites["head_r"])
        head_u = pygame.transform.rotate(self._sprites["head_r"], 90)
        head_d = pygame.transform.rotate(self._sprites["head_r"], -90)
        self._sprites["head_u"] = head_u
        self._sprites["head_d"] = head_d
        self._sprites["body_h"] = _make_sprite(BODY_H, s)
        self._sprites["body_v"] = _make_sprite(BODY_V, s)
        self._sprites["apple"] = _make_sprite(APPLE, s)
        self._sprites["SHROOM"] = _make_sprite(SHROOM, s)

    # ------------------------------------------------------------------
    # SCREEN ROUTER
    # ------------------------------------------------------------------

    def draw(self, env=None):
        """Call each frame. Returns True if the window was closed."""
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return True
            self._handle_event(ev)

        self._surface.fill(BG)

        if self._screen_id == "lobby":
            self._draw_lobby()
        elif self._screen_id == "config":
            self._draw_config()
        elif self._screen_id == "game" and env is not None:
            self._draw_game(env)
        elif self._screen_id == "results":
            self._draw_results()

        pygame.display.flip()
        return False

    # ------------------------------------------------------------------
    # INPUT
    # ------------------------------------------------------------------

    def _handle_event(self, ev):
        if ev.type != pygame.KEYDOWN:
            return
        k = ev.key

        if self._screen_id == "lobby":
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                self._screen_id = "config"

        elif self._screen_id == "config":
            params = self._config_params()
            if k == pygame.K_UP:
                self._config_idx = (self._config_idx - 1) % len(params)
            elif k == pygame.K_DOWN:
                self._config_idx = (self._config_idx + 1) % len(params)
            elif k in (pygame.K_LEFT, pygame.K_RIGHT):
                self._config_adjust(
                    params[self._config_idx][0],
                    1 if k == pygame.K_RIGHT else -1,
                )
            elif k in (pygame.K_RETURN, pygame.K_SPACE):
                self._screen_id = "game"
            elif k == pygame.K_ESCAPE:
                self._screen_id = "lobby"

        elif self._screen_id == "game":
            if self.step_by_step and k == pygame.K_SPACE:
                self._step_ack = True
            elif k == pygame.K_ESCAPE:
                self._screen_id = "lobby"

        elif self._screen_id == "results":
            if k in (pygame.K_RETURN, pygame.K_SPACE):
                self._screen_id = "game"
            elif k == pygame.K_ESCAPE:
                self._screen_id = "lobby"

    def wait_step(self) -> bool:
        """Wait for SPACE in step mode. Returns True if quit."""
        self._step_ack = False
        while not self._step_ack:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    return True
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_SPACE:
                        self._step_ack = True
                    elif ev.key == pygame.K_ESCAPE:
                        return True
        return False

    def _config_params(self):
        return [
            ("sessions", self.sessions),
            ("board", self.board_size),
            ("visual", "ON" if self.visual_on else "OFF"),
            ("learn", "ON" if self.learn_on else "OFF"),
            ("step", "ON" if self.step_by_step else "OFF"),
            (
                "save",
                os.path.basename(self.save_path) if self.save_path else "OFF",
            ),
        ]

    def _config_adjust(self, key, direction):
        if key == "sessions":
            self.sessions = max(1, self.sessions + direction * 1)
        elif key == "board":
            self.board_size = max(5, min(40, self.board_size + direction * 1))
        elif key == "visual":
            self.visual_on = not self.visual_on
        elif key == "learn":
            self.learn_on = not self.learn_on
        elif key == "step":
            self.step_by_step = not self.step_by_step

    # ------------------------------------------------------------------
    # SCREEN: LOBBY
    # ------------------------------------------------------------------

    def _draw_lobby(self):
        surf = self._surface
        W, H = surf.get_size()
        sc = SCALE

        # outer border
        pygame.draw.rect(surf, DARK, (4, 4, W - 8, H - 8), sc)

        # title
        title = "L2S"
        tx = (W - text_width(title, sc)) // 2
        draw_text(surf, title, tx, 10 * sc, DARK, sc)

        # separator
        pygame.draw.line(surf, MID, (8, 19 * sc), (W - 8, 19 * sc), 1)

        # sprite strip
        sprite_y = 20 * sc
        sx = 10 * sc
        surf.blit(self._sprites["head_r"], (sx, sprite_y))
        surf.blit(self._sprites["body_h"], (sx + 8 * sc, sprite_y))
        surf.blit(self._sprites["body_h"], (sx + 16 * sc, sprite_y))
        surf.blit(self._sprites["apple"], (sx + 32 * sc, sprite_y))
        surf.blit(self._sprites["SHROOM"], (sx + 48 * sc, sprite_y))

        pygame.draw.line(surf, MID, (8, 29 * sc), (W - 8, 29 * sc), 1)

        # menu items
        items = ["> GAME"]
        for i, item in enumerate(items):
            color = DARK if i == 0 else MID
            y = 32 * sc + i * 9 * sc
            draw_text(surf, item, 10 * sc, y, color, sc)

        pygame.draw.line(surf, MID, (8, H - 12 * sc), (W - 8, H - 12 * sc), 1)
        draw_text(
            surf,
            "PRESS SPACE",
            (W - text_width("PRESS SPACE", sc)) // 2,
            H - 9 * sc,
            MID,
            sc,
        )

    # ------------------------------------------------------------------
    # SCREEN: CONFIG
    # ------------------------------------------------------------------

    def _draw_config(self):
        surf = self._surface
        W, H = surf.get_size()
        sc = SCALE

        # header bar
        pygame.draw.rect(surf, DARK, (0, 0, W, 10 * sc))
        draw_text(
            surf,
            "CONFIGURE",
            (W - text_width("CONFIGURE", sc)) // 2,
            2 * sc,
            BG,
            sc,
        )
        pygame.draw.line(surf, DARK, (0, 10 * sc), (W, 10 * sc), sc)

        params = self._config_params()
        for i, (key, val) in enumerate(params):
            y = 13 * sc + i * 10 * sc
            selected = i == self._config_idx
            if selected:
                pygame.draw.rect(surf, MID, (2, y - 1 * sc, W - 4, 9 * sc))

            fc = BG if selected else DARK
            draw_text(surf, key.upper(), 5 * sc, y, fc, sc)
            vs = str(val)
            draw_text(
                surf,
                vs,
                W - 5 * sc - text_width(vs, sc),
                y,
                LITE if selected else MID,
                sc,
            )

        pygame.draw.line(surf, DARK, (0, H - 10 * sc), (W, H - 10 * sc), 1)
        draw_text(surf, "[GO]", 5 * sc, H - 7 * sc, DARK, sc)
        draw_text(surf, "[BACK]", W // 2, H - 7 * sc, MID, sc)

    # ------------------------------------------------------------------
    # SCREEN: GAME
    # ------------------------------------------------------------------

    def _draw_game(self, env):
        surf = self._surface
        W, H = surf.get_size()
        sc = SCALE
        bs = env.board_size
        cell = CELL_PX * sc

        # --- HUD top ---
        pygame.draw.rect(surf, DARK, (0, 0, W, HUD_TOP * sc))
        score_str = f"t:{self.current_duration:01d}s"
        len_str = f"scr:{self.current_length:02d}"
        draw_text(surf, score_str, 2 * sc, 2 * sc, BG, sc)
        draw_text(
            surf, len_str, W - 2 * sc - text_width(len_str, sc), 2 * sc, BG, sc
        )

        # Center grid
        grid_w = bs * cell
        grid_h = bs * cell
        off_x = (W - grid_w) // 2
        off_y = HUD_TOP * sc + (H - HUD_TOP * sc - HUD_BOT * sc - grid_h) // 2

        # --- Grid ---
        for gx in range(bs):
            for gy in range(bs):
                cell_type = env.board.get_cell_type(gx, gy)
                px = off_x + gx * cell
                py = off_y + gy * cell

                # subtle grid lines
                pygame.draw.rect(surf, LITE, (px, py, cell, cell), 1)

                if cell_type == Cell.HEAD.value:
                    # determine direction from snake deque
                    snake = env.board.snake  # list/deque of (x,y)
                    if len(snake) >= 2:
                        head = snake[0]
                        neck = snake[1]
                        dx = head[0] - neck[0]
                        dy = head[1] - neck[1]
                        if dx == 1:
                            key = "head_r"
                        elif dx == -1:
                            key = "head_l"
                        elif dy == -1:
                            key = "head_u"
                        else:
                            key = "head_d"
                    else:
                        key = "head_r"
                    surf.blit(self._sprites[key], (px, py))

                elif cell_type == Cell.BODY.value:
                    snake = env.board.snake
                    # find segment index
                    seg_idx = next(
                        (
                            i
                            for i, s in enumerate(snake)
                            if s[0] == gx and s[1] == gy
                        ),
                        None,
                    )
                    horiz = True
                    if seg_idx is not None and seg_idx > 0:
                        prev = snake[seg_idx - 1]
                        horiz = prev[1] == gy
                    key = "body_h" if horiz else "body_v"
                    surf.blit(self._sprites[key], (px, py))

                elif cell_type == Cell.GREEN.value:
                    surf.blit(self._sprites["apple"], (px, py))

                elif cell_type == Cell.RED.value:
                    surf.blit(self._sprites["SHROOM"], (px, py))

        # --- HUD bottom ---
        bot_y = H - HUD_BOT * sc
        pygame.draw.rect(surf, DARK, (0, bot_y, W, HUD_BOT * sc))
        ses_str = f"sess:{self.current_session:01d}/{self.sessions:01d}"
        draw_text(surf, ses_str, 2 * sc, bot_y + 2 * sc, BG, sc)

    # ------------------------------------------------------------------
    # SCREEN: RESULTS
    # ------------------------------------------------------------------

    def _draw_results(self):
        surf = self._surface
        W, H = surf.get_size()
        sc = SCALE

        # header
        pygame.draw.rect(surf, DARK, (0, 0, W, 10 * sc))
        draw_text(
            surf,
            "SESS RESULTS",
            (W - text_width("SESS RESULTS", sc)) // 2,
            2 * sc,
            BG,
            sc,
        )
        pygame.draw.line(surf, DARK, (0, 10 * sc), (W, 10 * sc), sc)

        rows = [
            ("MAX LEN", str(self.stats.max_length)),
            ("MAX DUR", str(self.stats.max_duration)),
            ("AVG LEN", f"{self.stats.avg_length:.1f}"),
            ("SESSIONS", str(self.stats.total_sessions)),
        ]
        if self.stats.records:
            last = self.stats.records[-1]
            rows.append(("LAST E", f"{last.epsilon:.2f}"))

        for i, (label, val) in enumerate(rows):
            y = 13 * sc + i * 10 * sc
            draw_text(surf, label, 5 * sc, y, DARK, sc)
            draw_text(surf, val, W - 5 * sc - text_width(val, sc), y, MID, sc)
            pygame.draw.line(
                surf, LITE, (4, y + 8 * sc), (W - 4, y + 8 * sc), 1
            )

        # spark bar (last 20 sessions lengths)
        recent = self.stats.records[-20:]
        if len(recent) > 1:
            bar_y = H - 20 * sc
            bar_h = 10 * sc
            pygame.draw.line(
                surf, MID, (4, bar_y + bar_h), (W - 4, bar_y + bar_h), 1
            )
            mx = max(r.length for r in recent) or 1
            bw = (W - 8) // len(recent)
            for j, r in enumerate(recent):
                bh = int((r.length / mx) * bar_h)
                bx = 4 + j * bw
                pygame.draw.rect(
                    surf, DARK, (bx, bar_y + bar_h - bh, bw - 1, bh)
                )

        # footer
        pygame.draw.line(surf, DARK, (0, H - 10 * sc), (W, H - 10 * sc), 1)
        surf.blit(self._sprites["head_r"], (5 * sc, H - 9 * sc))
        draw_text(surf, "CONTINUE?", 14 * sc, H - 7 * sc, DARK, sc)

    # ------------------------------------------------------------------
    # PUBLIC API for main.py integration
    # ------------------------------------------------------------------

    @property
    def screen(self):
        return self._screen_id

    def go_game(self):
        self._screen_id = "game"

    def go_results(self):
        self._screen_id = "results"

    def reset(self):
        """Reset the UI state to start a new game completely fresh."""
        self.stats = Stats()
        self.current_session = 0
        self.current_length = 0
        self.current_duration = 0
        self.current_epsilon = 1.0
        self.current_score = 0
        self._screen_id = "lobby"

    def record_session(self, session, length, duration, epsilon):
        self.stats.push(session, length, duration, epsilon)
        self.current_session = session
        self.current_length = length
        self.current_duration = duration
        self.current_epsilon = epsilon

    def tick(self, fps: int = 10):
        self._clock.tick(fps)
