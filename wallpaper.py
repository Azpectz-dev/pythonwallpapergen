import sys
import os
import time
import random
import math
import ctypes
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.columns import Columns
    from rich import box
    from rich.align import Align
except ImportError:
    sys.exit("rich is required: pip install rich")

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

WIDTH, HEIGHT = 2560, 1440
OUTPUT_DIR = Path(__file__).parent / "wallpapers"
OUTPUT_DIR.mkdir(exist_ok=True)

CONFIG_PATH = Path(__file__).parent / "config.json"

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            import json
            return json.load(f)
    return {}

CFG = load_config()
COLORS = CFG.get("colors", {})
EXTRAS = CFG.get("extras", {})

def c(key: str, fallback: str) -> str:
    """Look up a colour from config, return fallback if missing."""
    return COLORS.get(key, fallback)

console = Console()

ASCII_LOGO = r"""
 ██╗    ██╗ █████╗ ██╗     ██╗     ██████╗  █████╗ ██████╗ ███████╗██████╗  ██████╗ ███████╗███╗   ██╗
 ██║    ██║██╔══██╗██║     ██║     ██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║
 ██║ █╗ ██║███████║██║     ██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝██║  ███╗█████╗  ██╔██╗ ██║
 ██║███╗██║██╔══██║██║     ██║     ██╔═══╝ ██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗██║   ██║██╔══╝  ██║╚██╗██║
 ╚███╔███╔╝██║  ██║███████╗███████╗██║     ██║  ██║██║     ███████╗██║  ██║╚██████╔╝███████╗██║ ╚████║
  ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
"""


# ── Wallpaper sources ─────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
}

def _fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def download_prompt_wallpaper(prompt: str) -> Path:
    """Generate an image from the prompt via pollinations.ai — retries up to 3 times."""
    import io

    encoded = urllib.parse.quote(prompt)
    seed    = random.randint(0, 99999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=512&height=288&seed={seed}&model=flux&nologo=true"
    )

    last_err = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=90) as resp:
                img_bytes = resp.read()
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = "".join(ch if ch.isalnum() or ch in " _-" else "_" for ch in prompt)[:40].strip()
            dest = OUTPUT_DIR / f"{safe_name}_{timestamp}.jpg"
            img.save(dest, "JPEG", quality=95)
            return dest
        except Exception as e:
            last_err = e
            if attempt < 3:
                time.sleep(4)

    raise RuntimeError(f"Generation failed after 3 attempts: {last_err}")


def download_random_wallpaper() -> Path:
    url = f"https://picsum.photos/{WIDTH}/{HEIGHT}"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = OUTPUT_DIR / f"random_{timestamp}.jpg"
    urllib.request.urlretrieve(url, dest)
    return dest


# ── Procedural generator ──────────────────────────────────────────────────────

def random_color(min_brightness=0, max_brightness=255):
    while True:
        r, g, b = (random.randint(0, 255) for _ in range(3))
        brightness = (r * 299 + g * 587 + b * 114) // 1000
        if min_brightness <= brightness <= max_brightness:
            return (r, g, b)


def generate_gradient(img, color1, color2):
    draw = ImageDraw.Draw(img)
    for x in range(WIDTH):
        t = x / (WIDTH - 1)
        r = int(color1[0] + t * (color2[0] - color1[0]))
        g = int(color1[1] + t * (color2[1] - color1[1]))
        b = int(color1[2] + t * (color2[2] - color1[2]))
        draw.line([(x, 0), (x, HEIGHT)], fill=(r, g, b))


def generate_wallpaper(style: str = None) -> Path:
    if not style:
        style = random.choice(["gradient_circles", "geometric", "waves", "galaxy"])

    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)
    bg1 = random_color(max_brightness=100)
    bg2 = random_color(max_brightness=120)
    generate_gradient(img, bg1, bg2)

    if style == "gradient_circles":
        for _ in range(random.randint(8, 20)):
            cx = random.randint(0, WIDTH)
            cy = random.randint(0, HEIGHT)
            r_max = random.randint(100, 600)
            color = random_color(min_brightness=80)
            for r in range(r_max, 0, -4):
                t = r / r_max
                alpha = int(255 * (1 - t) * 0.6)
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(overlay)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
                img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    elif style == "geometric":
        for _ in range(random.randint(20, 60)):
            color = random_color(min_brightness=60)
            pts = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(3)]
            draw = ImageDraw.Draw(img)
            draw.polygon(pts, fill=color)

    elif style == "waves":
        for i in range(0, HEIGHT, random.randint(6, 14)):
            color = random_color(min_brightness=70)
            amplitude = random.randint(20, 80)
            freq = random.uniform(0.002, 0.01)
            phase = random.uniform(0, math.tau)
            pts = [(x, i + int(amplitude * math.sin(freq * x + phase))) for x in range(0, WIDTH + 1, 4)]
            draw = ImageDraw.Draw(img)
            if len(pts) >= 2:
                draw.line(pts, fill=color, width=random.randint(1, 4))

    elif style == "galaxy":
        draw = ImageDraw.Draw(img)
        for _ in range(4000):
            x, y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
            r = random.randint(0, 1)
            b = random.randint(150, 255)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, b))
        for _ in range(5):
            cx = random.randint(200, WIDTH - 200)
            cy = random.randint(200, HEIGHT - 200)
            color = random_color(min_brightness=60)
            blob = Image.new("RGBA", img.size, (0, 0, 0, 0))
            bd = ImageDraw.Draw(blob)
            for r in range(300, 0, -10):
                alpha = int(40 * (1 - r / 300))
                bd.ellipse([cx - r, cy - r // 2, cx + r, cy + r // 2], fill=(*color, alpha))
            img = Image.alpha_composite(img.convert("RGBA"), blob).convert("RGB")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = OUTPUT_DIR / f"{style}_{timestamp}.png"
    img.save(dest)
    return dest


# ── Set wallpaper ─────────────────────────────────────────────────────────────

def set_wallpaper(path: Path) -> bool:
    abs_path = str(path.resolve())
    result = ctypes.windll.user32.SystemParametersInfoW(20, 0, abs_path, 3)
    return bool(result)


# ── UI ────────────────────────────────────────────────────────────────────────

def print_header():
    console.clear()
    console.print(Text(ASCII_LOGO, style=f"bold {c('logo', 'cyan')}"), justify="center")
    console.print(
        Align.center(Text("2560×1440 · AI prompt · procedural · random photo", style="dim white"))
    )
    console.print()


def get_active_wallpaper() -> str:
    """Return the path of the currently active desktop wallpaper."""
    buf = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.SystemParametersInfoW(0x0073, len(buf), buf, 0)
    return buf.value.lower()


def print_menu():
    p  = c("prompt_option",    "cyan")
    r  = c("random_option",    "magenta")
    pr = c("procedural_option","yellow")
    cl = c("clear_option",     "green")
    q  = c("quit_option",      "red")
    options = [
        Panel(f"[bold {p}]1[/] · Prompt search\n[dim]AI-generate from your description[/]",
              border_style=p, box=box.ROUNDED),
        Panel(f"[bold {r}]2[/] · Random photo\n[dim]Pull from picsum.photos[/]",
              border_style=r, box=box.ROUNDED),
        Panel(f"[bold {pr}]3[/] · Procedural art\n[dim]Generate abstract art locally[/]",
              border_style=pr, box=box.ROUNDED),
        Panel(f"[bold {cl}]4[/] · Clear folder\n[dim]Delete saved wallpapers (keeps active)[/]",
              border_style=cl, box=box.ROUNDED),
        Panel(f"[bold {q}]q[/] · Quit\n[dim] [/]",
              border_style=q, box=box.ROUNDED),
    ]
    console.print(Columns(options, equal=True, expand=True))
    console.print()


def run_with_spinner(label: str, fn):
    spin_color = c("spinner", "cyan")
    with Progress(
        SpinnerColumn(style=spin_color),
        TextColumn(f"[{spin_color}]{{task.description}}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(label, total=None)
        result = fn()
    return result


def handle_result(path: Path):
    saved_color = c("saved_text", "green")
    if EXTRAS.get("show_file_path", True):
        console.print(f"\n[bold {saved_color}]  Saved:[/] {path}")

    auto_set = EXTRAS.get("auto_set_wallpaper", False)
    confirm  = EXTRAS.get("confirm_before_set", True)

    do_set = True
    if not auto_set and confirm:
        answer = Prompt.ask(
            f"\n[{c('prompt_option','cyan')}]  Set as wallpaper?[/] [bold][Y/n][/]",
            default="y", console=console
        ).strip().lower()
        do_set = answer in ("", "y", "yes")

    if do_set:
        ok = set_wallpaper(path)
        if ok:
            console.print(f"[bold {saved_color}]  Wallpaper applied![/]\n")
        else:
            console.print("[bold red]  Could not set wallpaper.[/]\n")


def prompt_mode():
    console.print(Panel(
        "[bold]Describe the wallpaper you want[/]\n"
        "[dim]e.g. 'a misty mountain range at golden hour' or 'neon cyberpunk city rain'[/]",
        border_style="cyan", box=box.ROUNDED
    ))
    user_prompt = Prompt.ask("[bold cyan]  Prompt[/]", console=console).strip()
    if not user_prompt:
        console.print("[dim]  No prompt entered.[/]\n")
        return

    console.print()
    try:
        path = run_with_spinner(f'Generating "{user_prompt}" …', lambda: download_prompt_wallpaper(user_prompt))
        handle_result(path)
    except Exception as e:
        console.print(f"[bold red]  Failed:[/] {e}\n")


def random_mode():
    try:
        path = run_with_spinner("Fetching random photo …", download_random_wallpaper)
        handle_result(path)
    except Exception as e:
        console.print(f"[bold red]  Failed:[/] {e}\n")
        console.print("[dim]  Falling back to procedural …[/]\n")
        procedural_mode(silent=True)


def procedural_mode(silent=False):
    styles = ["gradient_circles", "geometric", "waves", "galaxy"]
    if not silent:
        console.print(Panel(
            "\n".join(f"[bold yellow]{i+1}[/] · {s}" for i, s in enumerate(styles))
            + "\n[bold yellow]5[/] · Random",
            title="[bold yellow]Style[/]", border_style="yellow", box=box.ROUNDED
        ))
        choice = Prompt.ask("[bold yellow]  Pick a style[/]", default="5", console=console).strip()
        try:
            idx = int(choice) - 1
            style = styles[idx] if 0 <= idx < len(styles) else None
        except ValueError:
            style = None
    else:
        style = None

    try:
        path = run_with_spinner("Generating art …", lambda: generate_wallpaper(style))
        handle_result(path)
    except Exception as e:
        console.print(f"[bold red]  Failed:[/] {e}\n")


def clear_wallpapers_mode():
    files = list(OUTPUT_DIR.iterdir())
    images = [f for f in files if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp")]

    if not images:
        console.print("[dim]  Wallpapers folder is already empty.[/]\n")
        return

    active = get_active_wallpaper()

    kept = [f for f in images if str(f.resolve()).lower() == active]
    to_delete = [f for f in images if str(f.resolve()).lower() != active]

    console.print(f"  Found [bold]{len(images)}[/] wallpaper(s).")
    if kept:
        console.print(f"  [bold green]Keeping[/] active wallpaper: [dim]{kept[0].name}[/]")
    console.print(f"  [bold red]Will delete[/] {len(to_delete)} file(s).\n")

    if not to_delete:
        console.print("[dim]  Nothing to delete (only the active wallpaper is in the folder).[/]\n")
        return

    if not Confirm.ask("  [bold red]Confirm delete?[/]", default=False, console=console):
        console.print("[dim]  Cancelled.[/]\n")
        return

    deleted = 0
    for f in to_delete:
        try:
            f.unlink()
            deleted += 1
        except Exception as e:
            console.print(f"  [red]Could not delete {f.name}:[/] {e}")

    console.print(f"\n  [bold green]Deleted {deleted} file(s).[/]\n")


def main():
    while True:
        print_header()
        print_menu()
        default_choice = EXTRAS.get("default_menu_choice", "1")
        choice = Prompt.ask("[bold white]  Choose[/]", default=default_choice, console=console).strip().lower()
        console.print()

        if choice == "1":
            prompt_mode()
        elif choice == "2":
            random_mode()
        elif choice == "3":
            procedural_mode()
        elif choice == "4":
            clear_wallpapers_mode()
        elif choice in ("q", "quit", "exit"):
            console.print("[dim]  bye[/]\n")
            break
        else:
            console.print("[dim]  Unknown option.[/]\n")

        input("  Press Enter to continue …")


if __name__ == "__main__":
    main()
