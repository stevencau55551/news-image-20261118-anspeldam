#!/usr/bin/env python3
"""news-image-20261118: draw one newspaper front page summing up the world
news of Wednesday 18 November 2026, and write it to $MAKEFUN_OUTPUT_DIR/entry.png.

Pure Python 3 standard library, fully deterministic, no network, no fonts
from disk: a hand-drawn 5x7 bitmap font and a hand-rolled PNG encoder
(zlib + struct). The six stories were verified against at least two news
sources each; see NOTES.md for the sources.
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 232)
INK = (24, 24, 28)
NAVY = (18, 42, 84)
RED = (178, 34, 34)
WHITE = (255, 255, 255)
GREY = (90, 90, 92)
LIGHT = (232, 226, 210)
CARD = (255, 255, 255)

PANELS = [
    {
        "kicker": "ASIA-PACIFIC - DIPLOMACY",
        "accent": (18, 42, 84),
        "pic": "quad",
        "headline": "TRUMP IN MANILA FOR QUAD SUMMIT",
        "deck": "First Quad leaders' meeting in two years. Marcos talks today; then Shenzhen and historic Xi-Putin meeting.",
    },
    {
        "kicker": "UKRAINE - WAR",
        "accent": (120, 20, 20),
        "pic": "bridge",
        "headline": "CRIMEA BRIDGE CRIPPLED",
        "deck": "Road arch falls into Kerch Strait after second strike. Russia hits Kyiv bridges in reply.",
    },
    {
        "kicker": "GULF - MIDDLE EAST",
        "accent": (146, 90, 10),
        "pic": "drone",
        "headline": "IRAN DRONES TARGET US RADAR IN BAHRAIN",
        "deck": "Drones intercepted, no damage, US says. Third claimed attack in five days.",
    },
    {
        "kicker": "TECH - MARKETS",
        "accent": (16, 110, 60),
        "pic": "chip",
        "headline": "NVIDIA SALES DOUBLE TO $115.8BN",
        "deck": "Record quarter beats forecasts. Board: ousted chief Huang will not return.",
    },
    {
        "kicker": "BRITAIN - MIDDLE EAST",
        "accent": (96, 44, 120),
        "pic": "sanction",
        "headline": "UK SANCTIONS SETTLEMENT FIRMS",
        "deck": "Eight builders frozen over West Bank homes; Gaza aid-blocking group also hit.",
    },
    {
        "kicker": "WEATHER - ASIA",
        "accent": (10, 96, 130),
        "pic": "cyclone",
        "headline": "CYCLONE AKVAN BEARS DOWN ON INDIA",
        "deck": "Severe storm in Bay of Bengal. Landfall due Friday with winds to 145 km/h.",
    },
]

# ------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, written as strings of '0'/'1'.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
}


def text_width(text, scale):
    """Pixel width of text drawn at the given scale (6 px per char cell)."""
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i], self.px[i + 1], self.px[i + 2] = c

    def hline(self, x, y, w, c, t=1):
        self.fill(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill(x, y, t, h, c)

    def rect(self, x, y, w, h, c, t=1):
        self.hline(x, y, w, c, t)
        self.hline(x, y + h - t, w, c, t)
        self.vline(x, y, h, c, t)
        self.vline(x + w - t, y, h, c, t)

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= r * r:
                    self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        while True:
            self.fill(x - t // 2, y - t // 2, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def arc(self, cx, cy, r, a0, a1, c, t=3):
        import math
        steps = max(8, int(r * (a1 - a0) * 1.5))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.fill(int(cx + r * math.cos(a)) - t // 2,
                      int(cy + r * math.sin(a)) - t // 2, t, t, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, y, s, scale, c, x0=0, x1=None):
        x1 = self.w if x1 is None else x1
        w = text_width(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)

    def para(self, x, y, s, scale, c, max_width, leading):
        yy = y
        for line in wrap_text(s, max_width, scale):
            self.text(x, yy, line, scale, c)
            yy += 7 * scale + leading
        return yy


# ------------------------------------------------------------- pictograms
def pic_quad(cv, x, y, w, h):
    """Four flags over a skyline: the Quad leaders meet in Manila."""
    sky = (168, 200, 232)
    cv.fill(x, y, w, h, sky)
    cv.fill(x, y + h - 34, w, 34, (96, 110, 128))
    # buildings
    for bx, bw, bh in ((8, 34, 46), (52, 26, 66), (88, 40, 40),
                       (140, 30, 58), (180, 36, 44), (226, 28, 62),
                       (264, 30, 48)):
        cv.fill(x + bx, y + h - 34 - bh, bw, bh, (70, 82, 100))
    # four flag poles with simple striped flags (US, Japan, India, Australia)
    flag_cols = [
        [(178, 34, 34), (255, 255, 255), (18, 42, 84)],
        [(255, 255, 255), (178, 34, 34), (255, 255, 255)],
        [(255, 153, 51), (255, 255, 255), (19, 136, 8)],
        [(18, 42, 84), (255, 255, 255), (178, 34, 34)],
    ]
    for i, cols in enumerate(flag_cols):
        fx = x + 34 + i * 68
        fy = y + 22
        cv.vline(fx, fy, 74, INK, 3)
        for s, col in enumerate(cols):
            cv.fill(fx + 3, fy + s * 12, 44, 12, col)
        cv.disc(fx + 25, fy + 18, 6, RED if i == 1 else cols[1])


def pic_bridge(cv, x, y, w, h):
    """A bridge with its middle span collapsed into the water."""
    cv.fill(x, y, w, h, (196, 214, 228))
    cv.fill(x, y + h - 46, w, 46, (52, 110, 150))
    # waves
    for wx in range(x + 6, x + w - 6, 26):
        cv.arc(wx + 8, y + h - 30, 9, 3.14159, 6.28318, WHITE, 3)
    # deck: left and right spans, gap in the middle
    cv.fill(x + 6, y + 78, 108, 10, (90, 60, 40))
    cv.fill(x + w - 114, y + 78, 108, 10, (90, 60, 40))
    # fallen span in the water, tilted
    cv.line(x + 118, y + 88, x + 168, y + h - 30, (90, 60, 40), 8)
    # pillars
    cv.fill(x + 20, y + 88, 10, h - 88 - 46, (70, 48, 32))
    cv.fill(x + w - 30, y + 88, 10, h - 88 - 46, (70, 48, 32))
    # arch stubs
    cv.arc(x + 60, y + 78, 52, 3.14159, 6.28318, (120, 80, 55), 5)
    cv.arc(x + w - 60, y + 78, 52, 3.14159, 6.28318, (120, 80, 55), 5)
    # explosion star over the gap
    cx, cy = x + w // 2, y + 66
    for ang in range(0, 360, 30):
        import math
        r = 26 if ang % 60 == 0 else 12
        cv.line(cx, cy,
                int(cx + r * math.cos(math.radians(ang))),
                int(cy + r * math.sin(math.radians(ang))),
                (232, 140, 20), 4)
    cv.disc(cx, cy, 8, (232, 140, 20))


def pic_drone(cv, x, y, w, h):
    """Radar dish sweeping, drones above, one crossed out: intercepted."""
    cv.fill(x, y, w, h, (24, 34, 52))
    # radar dish
    cx, cy = x + 76, y + h - 52
    cv.arc(cx, cy, 62, 3.14159, 6.28318, (120, 200, 120), 4)
    cv.line(cx - 62, cy, cx + 62, cy, (120, 200, 120), 4)
    cv.line(cx, cy, cx + 44, cy - 44, (120, 200, 120), 3)
    cv.line(cx, cy, cx + 58, cy - 12, (90, 170, 90), 3)
    cv.disc(cx, cy, 6, (120, 200, 120))
    # two drones (quadcopters), drawn larger so they read at small size
    for dx, dy in ((x + 186, y + 40), (x + 250, y + 78)):
        cv.fill(dx - 22, dy - 4, 44, 8, (220, 220, 220))
        cv.fill(dx - 4, dy - 22, 8, 44, (220, 220, 220))
        cv.disc(dx - 24, dy - 22, 9, (200, 200, 200))
        cv.disc(dx + 24, dy - 22, 9, (200, 200, 200))
        cv.disc(dx - 24, dy + 22, 9, (200, 200, 200))
        cv.disc(dx + 24, dy + 22, 9, (200, 200, 200))
        cv.disc(dx, dy, 8, (232, 60, 40))
    # intercept cross over the nearer drone
    cv.line(x + 222, y + 50, x + 278, y + 106, RED, 6)
    cv.line(x + 278, y + 50, x + 222, y + 106, RED, 6)


def pic_chip(cv, x, y, w, h):
    """A chip with rising bars: record sales, no return for the old chief."""
    cv.fill(x, y, w, h, (232, 240, 232))
    # rising bars
    bars = (34, 56, 84, 118)
    for i, bh in enumerate(bars):
        bx = x + 168 + i * 34
        cv.fill(bx, y + h - 26 - bh, 22, bh, (16, 110, 60))
    cv.line(x + 160, y + h - 30, x + 300, y + h - 30, INK, 2)
    # chip
    cx, cy = x + 84, y + h // 2 + 6
    for px in range(-2, 3):
        cv.fill(cx + px * 26 - 3, cy - 62, 6, 14, (60, 60, 64))
        cv.fill(cx + px * 26 - 3, cy + 48, 6, 14, (60, 60, 64))
        cv.fill(cx - 62, cy + px * 26 - 3, 14, 6, (60, 60, 64))
        cv.fill(cx + 48, cy + px * 26 - 3, 14, 6, (60, 60, 64))
    cv.fill(cx - 48, cy - 48, 96, 96, (18, 42, 84))
    cv.fill(cx - 34, cy - 34, 68, 68, (30, 64, 120))
    cv.text(cx - 30, cy - 12, "AI", 3, WHITE)


def pic_sanction(cv, x, y, w, h):
    """Settlement houses under a red ban stamp."""
    cv.fill(x, y, w, h, (238, 228, 210))
    # houses
    for hx in (x + 22, x + 92, x + 162):
        cv.fill(hx, y + 78, 56, 62, (150, 110, 70))
        cv.line(hx - 4, y + 78, hx + 28, y + 46, (120, 80, 50), 6)
        cv.line(hx + 60, y + 78, hx + 28, y + 46, (120, 80, 50), 6)
        cv.fill(hx + 22, y + 108, 12, 32, (80, 52, 30))
    # crane silhouette
    cv.fill(x + 232, y + 30, 6, 110, (90, 90, 92))
    cv.fill(x + 232, y + 30, 66, 6, (90, 90, 92))
    cv.line(x + 232, y + 36, x + 292, y + 78, (90, 90, 92), 3)
    # red prohibition ring
    cx, cy = x + w - 52, y + 46
    cv.ring(cx, cy, 34, RED, 6)
    cv.line(cx - 24, cy + 24, cx + 24, cy - 24, RED, 6)


def pic_cyclone(cv, x, y, w, h):
    """Spiral storm over a coastline."""
    cv.fill(x, y, w, h, (168, 196, 220))
    cv.fill(x, y + h - 30, w, 30, (70, 120, 90))
    cx, cy = x + w // 2, y + h // 2 - 6
    for r in (18, 34, 50, 66):
        cv.arc(cx, cy, r, 0.4 + r * 0.02, 5.6, WHITE, 5)
    cv.disc(cx, cy, 12, (240, 244, 248))
    # rain
    for rx, ry in ((x + 24, y + 30), (x + 52, y + 58), (x + 268, y + 34),
                   (x + 288, y + 66), (x + 40, y + 100), (x + 276, y + 104)):
        cv.line(rx, ry, rx - 5, ry + 14, (60, 100, 150), 3)
    # wind arrows
    cv.line(x + 18, y + h - 56, x + 66, y + h - 56, INK, 3)
    cv.line(x + 66, y + h - 56, x + 56, y + h - 64, INK, 3)
    cv.line(x + 66, y + h - 56, x + 56, y + h - 48, INK, 3)


PICS = {
    "quad": pic_quad,
    "bridge": pic_bridge,
    "drone": pic_drone,
    "chip": pic_chip,
    "sanction": pic_sanction,
    "cyclone": pic_cyclone,
}


# ------------------------------------------------------------------ page
def draw_panel(cv, px, py, pw, ph, panel):
    cv.fill(px, py, pw, ph, CARD)
    cv.rect(px, py, pw, ph, (200, 192, 172), 2)
    accent = panel["accent"]
    # kicker strip
    cv.fill(px, py, pw, 28, accent)
    cv.text(px + 12, py + 7, panel["kicker"], 2, WHITE)
    # pictogram
    PICS[panel["pic"]](cv, px + 10, py + 38, pw - 20, 168)
    # headline
    y = py + 38 + 168 + 14
    y = cv.para(px + 12, y, panel["headline"], 3, INK, pw - 24, 5)
    # divider
    cv.hline(px + 12, y + 2, pw - 24, (210, 202, 182), 2)
    # deck
    cv.para(px + 12, y + 12, panel["deck"], 2, (52, 52, 56),
            pw - 24, 4)


def draw_page():
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.text_center(26, "THE WORLD IN ONE DAY", 6, NAVY)
    cv.hline(40, 78, W - 80, RED, 4)
    cv.text_center(92, "WEDNESDAY 18 NOVEMBER 2026", 4, RED)
    cv.text_center(128, "SIX STORIES THAT DEFINED THE DAY", 2, GREY)
    # panels: 2 rows x 3 columns
    mx, gutter = 20, 14
    pw = (W - 2 * mx - 2 * gutter) // 3
    ph = 396
    y0 = 164
    for i, panel in enumerate(PANELS):
        col, row = i % 3, i // 3
        px = mx + col * (pw + gutter)
        py = y0 + row * (ph + gutter)
        draw_panel(cv, px, py, pw, ph, panel)
    # footer
    fy = y0 + 2 * ph + gutter + 8
    cv.hline(40, fy, W - 80, INK, 2)
    cv.text_center(fy + 10,
                   "SOURCES: AP - REUTERS - BBC - CNN - AL JAZEERA - IMD",
                   2, GREY)
    return cv


# ------------------------------------------------------------ PNG writer
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    cv = draw_page()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
