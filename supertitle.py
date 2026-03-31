import os
import sys
import msvcrt
import ctypes
import configparser
from ctypes import wintypes


# ── ANSI colour / style maps ──────────────────────────────────────────────────
COLORS = {
    'black': '30', 'red': '31', 'green': '32', 'yellow': '33',
    'blue': '34', 'magenta': '35', 'cyan': '36', 'white': '97',
}
RESET = '\033[0m'


def build_ansi(color, style):
    codes = []
    color_code = COLORS.get(color.lower(), '97')
    codes.append(color_code)
    style = style.lower()
    if 'bold' in style:
        codes.append('1')
    if 'underline' in style:
        codes.append('4')
    return '\033[' + ';'.join(codes) + 'm'


# ── Windows console helpers ───────────────────────────────────────────────────
def enable_ansi():
    """Enable ANSI escape processing on Windows 10+."""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetStdHandle(-11)          # STD_OUTPUT_HANDLE
    mode = wintypes.DWORD()
    kernel32.GetConsoleMode(handle, ctypes.byref(mode))
    kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING


class _COORD(ctypes.Structure):
    _fields_ = [('X', wintypes.SHORT), ('Y', wintypes.SHORT)]


class _CONSOLE_FONT_INFOEX(ctypes.Structure):
    _fields_ = [
        ('cbSize',      wintypes.ULONG),
        ('nFont',       wintypes.DWORD),
        ('dwFontSize',  _COORD),
        ('FontFamily',  wintypes.UINT),
        ('FontWeight',  wintypes.UINT),
        ('FaceName',    wintypes.WCHAR * 32),
    ]


def set_console_font(size, bold):
    font = _CONSOLE_FONT_INFOEX()
    font.cbSize       = ctypes.sizeof(_CONSOLE_FONT_INFOEX)
    font.dwFontSize.Y = max(8, int(size))
    font.FontFamily   = 54          # FF_MODERN | TMPF_TRUETYPE
    font.FontWeight   = 700 if bold else 400
    font.FaceName     = 'Consolas'
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    ctypes.windll.kernel32.SetCurrentConsoleFontEx(handle, False, ctypes.byref(font))


# ── Config ────────────────────────────────────────────────────────────────────
def load_config(script_dir):
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(script_dir, 'config.ini'), encoding='utf-8')
    d = cfg['display'] if 'display' in cfg else {}
    return {
        'color':      d.get('font_color',  'white'),
        'style':      d.get('font_style',  'bold'),
        'size':       int(d.get('font_size',   '24')),
        'start_line': int(d.get('start_line',  '1')),
    }


# ── Screen ────────────────────────────────────────────────────────────────────
def clear_screen():
    os.system('cls')


def display_super_title(text, ansi_code):
    clear_screen()
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:
        terminal_width = 80

    lines = text.strip().splitlines()
    max_len = max((len(line) for line in lines), default=0)
    box_width = max(max_len + 4, 40)

    border     = '=' * box_width
    empty_line = '|' + ' ' * (box_width - 2) + '|'

    print('\n' * 2)
    print(ansi_code + border.center(terminal_width) + RESET)
    print(ansi_code + empty_line.center(terminal_width) + RESET)
    for line in lines:
        padded = '|  ' + line.ljust(box_width - 4) + '  |'
        print(ansi_code + padded.center(terminal_width) + RESET)
    print(ansi_code + empty_line.center(terminal_width) + RESET)
    print(ansi_code + border.center(terminal_width) + RESET)
    print('\n')


# ── Input ─────────────────────────────────────────────────────────────────────
def get_key():
    ch = msvcrt.getwch()
    if ch in ('\x00', '\xe0'):
        ch2 = msvcrt.getwch()
        if ch2 == 'M': return 'right'
        if ch2 == 'K': return 'left'
        return 'other'
    if ch == '\x1b': return 'esc'
    return ch.lower()


# ── Paragraphs ────────────────────────────────────────────────────────────────
def load_paragraphs(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    raw_blocks = content.split('\n\n')
    return [b.strip() for b in raw_blocks if b.strip()]


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    enable_ansi()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = load_config(script_dir)

    set_console_font(cfg['size'], bold='bold' in cfg['style'].lower())
    ansi_code = build_ansi(cfg['color'], cfg['style'])

    input_file = os.path.join(script_dir, 'input.txt')
    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found.")
        sys.exit(1)

    paragraphs = load_paragraphs(input_file)
    if not paragraphs:
        print("input.txt is empty or has no paragraphs.")
        sys.exit(1)

    total = len(paragraphs)
    index = max(0, min(cfg['start_line'] - 1, total - 1))

    while True:
        display_super_title(paragraphs[index], ansi_code)

        while True:
            key = get_key()
            if key == 'right' and index + 1 < total:
                index += 1
                break
            elif key == 'esc':
                clear_screen()
                sys.exit(0)


if __name__ == '__main__':
    main()
