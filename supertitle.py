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
    if 'italic' in style:
        codes.append('3')
    if 'underline' in style:
        codes.append('4')
    return '\033[' + ';'.join(codes) + 'm'


# ── Language → ISO-639 code map ──────────────────────────────────────────────
LANGUAGE_CODES = {
    'english': 'en', 'french': 'fr', 'spanish': 'es', 'german': 'de',
    'italian': 'it', 'portuguese': 'pt', 'dutch': 'nl', 'russian': 'ru',
    'chinese': 'zh-CN', 'japanese': 'ja', 'korean': 'ko', 'arabic': 'ar',
    'hindi': 'hi', 'bengali': 'bn', 'turkish': 'tr', 'polish': 'pl',
    'swedish': 'sv', 'norwegian': 'no', 'danish': 'da', 'finnish': 'fi',
    'greek': 'el', 'czech': 'cs', 'romanian': 'ro', 'hungarian': 'hu',
    'thai': 'th', 'vietnamese': 'vi', 'indonesian': 'id', 'malay': 'ms',
    'hebrew': 'he', 'ukrainian': 'uk', 'urdu': 'ur', 'persian': 'fa',
    'swahili': 'sw', 'tagalog': 'tl', 'malay': 'ms',
}


# ── Font map (matches numbering in config.ini) ────────────────────────────────
FONTS = {
    1:  'Consolas',
    2:  'Courier New',
    3:  'Lucida Console',
    4:  'Lucida Sans Typewriter',
    5:  'Terminal',
    6:  'Cascadia Mono',
    7:  'Cascadia Code',
    8:  'DejaVu Sans Mono',
    9:  'Ubuntu Mono',
    10: 'Roboto Mono',
}


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


def set_console_font(size, bold, face_name='Consolas'):
    font = _CONSOLE_FONT_INFOEX()
    font.cbSize       = ctypes.sizeof(_CONSOLE_FONT_INFOEX)
    font.dwFontSize.X = 0                # let Windows auto-calculate width
    font.dwFontSize.Y = max(8, int(size))
    font.FontFamily   = 48              # FF_MODERN (fixed-pitch TrueType)
    font.FontWeight   = 700 if bold else 400
    font.FaceName     = face_name
    handle = ctypes.windll.kernel32.GetStdHandle(-11)
    ok = ctypes.windll.kernel32.SetCurrentConsoleFontEx(handle, False, ctypes.byref(font))
    if not ok:
        err = ctypes.windll.kernel32.GetLastError()
        print(f"[warning] SetCurrentConsoleFontEx failed (error {err}). "
              "Font change only works in a real Windows console (cmd.exe), "
              "not in VSCode or Windows Terminal.")


# ── Config ────────────────────────────────────────────────────────────────────
def load_config(script_dir):
    cfg = configparser.RawConfigParser()
    cfg.read(os.path.join(script_dir, 'config.ini'), encoding='utf-8')
    d = cfg['display'] if 'display' in cfg else {}
    return {
        'color':       d.get('font_color',   'white'),
        'style':       d.get('font_style',   'bold'),
        'font_select': int(d.get('font_select', '1')),
        'size':        int(d.get('font_size',   '24')),
        'start_line': int(d.get('start_line',  '1')),
        'top_margin':   int(d.get('top_margin',    '0')),
        'line_spacing': int(d.get('line_spacing',  '0')),
        'left_margin':  int(d.get('left_margin',   '0')),
        'max_lines':    int(d.get('max_lines',     '0')),
        'language':         d.get('language',     'English'),
    }


# ── Screen ────────────────────────────────────────────────────────────────────
def clear_screen():
    os.system('cls')


def display_super_title(text, ansi_code, top_blank_lines=0, line_gap=0, left_spaces=0):
    clear_screen()
    indent = ' ' * left_spaces
    for _ in range(top_blank_lines):
        print()
    raw_lines = text.strip().splitlines()
    # Expand '**' markers into a blank line between surrounding content
    lines = []
    for raw in raw_lines:
        if '**' in raw:
            parts = raw.split('**')
            for j, part in enumerate(parts):
                if part:
                    lines.append(part)
                if j < len(parts) - 1:
                    lines.append('')          # blank line at each '**' position
        else:
            lines.append(raw)
    for i, line in enumerate(lines):
        if line == '':
            print()
        else:
            print(ansi_code + indent + line + RESET)
        if line_gap > 0 and line != '' and i < len(lines) - 1:
            for _ in range(line_gap):
                print()


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
def paginate_paragraphs(paragraphs, max_lines):
    """Split any paragraph whose line count exceeds max_lines into chunks."""
    if max_lines <= 0:
        return paragraphs
    result = []
    for para in paragraphs:
        lines = para.splitlines()
        for i in range(0, len(lines), max_lines):
            result.append('\n'.join(lines[i:i + max_lines]))
    return result


def load_paragraphs(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    raw_blocks = content.split('\n\n')
    return [b.strip() for b in raw_blocks if b.strip()]


# ── Translation ───────────────────────────────────────────────────────────────
def translate_paragraphs(paragraphs, language):
    """Translate all paragraphs to the target language using deep-translator."""
    lang = language.lower().strip()
    if lang in ('english', 'en', ''):
        return paragraphs

    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print("\n[error] Translation requires the 'deep-translator' package.")
        print("        Run:  pip install deep-translator\n")
        sys.exit(1)

    target_code = LANGUAGE_CODES.get(lang, lang)   # fallback: treat value as an ISO code
    translator  = GoogleTranslator(source='en', target=target_code)

    print(f"Translating to {language.title()} ...", end='', flush=True)
    translated = []
    for para in paragraphs:
        try:
            translated.append(translator.translate(para) or para)
        except Exception:
            translated.append(para)   # keep original if a single paragraph fails
    print(" done.")
    return translated


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    enable_ansi()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = load_config(script_dir)

    face_name = FONTS.get(cfg['font_select'], 'Consolas')
    set_console_font(cfg['size'], bold='bold' in cfg['style'].lower(), face_name=face_name)
    ansi_code = build_ansi(cfg['color'], cfg['style'])

    input_file = os.path.join(script_dir, 'input.txt')
    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found.")
        sys.exit(1)

    paragraphs = translate_paragraphs(
        paginate_paragraphs(load_paragraphs(input_file), cfg['max_lines']),
        cfg['language']
    )
    if not paragraphs:
        print("input.txt is empty or has no paragraphs.")
        sys.exit(1)

    total = len(paragraphs)
    index = max(0, min(cfg['start_line'] - 1, total - 1))
    top_blank_lines = max(0, round(cfg['top_margin'] / cfg['size']))
    line_gap        = max(0, round(cfg['line_spacing'] / cfg['size']))
    left_spaces     = max(0, round(cfg['left_margin'] / (cfg['size'] / 2)))

    while True:
        display_super_title(paragraphs[index], ansi_code, top_blank_lines, line_gap, left_spaces)

        while True:
            key = get_key()
            if key in ('right', '>') and index + 1 < total:
                index += 1
                break
            elif key in ('left', '<') and index > 0:
                index -= 1
                break
            elif key == 'esc':
                clear_screen()
                sys.exit(0)


if __name__ == '__main__':
    main()
