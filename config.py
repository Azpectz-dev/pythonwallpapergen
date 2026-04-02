"""
WallpaperGen config editor.
Run with: python config.py
"""

import json
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.columns import Columns
    from rich.align import Align
    from rich import box
except ImportError:
    sys.exit("rich is required: pip install rich")

CONFIG_PATH = Path(__file__).parent / "config.json"
console = Console()

ASCII_LOGO = r"""
  ██████╗ ██████╗ ███╗   ██╗███████╗██╗ ██████╗
 ██╔════╝██╔═══██╗████╗  ██║██╔════╝██║██╔════╝
 ██║     ██║   ██║██╔██╗ ██║█████╗  ██║██║  ███╗
 ██║     ██║   ██║██║╚██╗██║██╔══╝  ██║██║   ██║
 ╚██████╗╚██████╔╝██║ ╚████║██║     ██║╚██████╔╝
  ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝     ╚═╝ ╚═════╝
"""

COLORS = [
    "cyan", "magenta", "yellow", "green", "red", "blue",
    "white", "bright_cyan", "bright_magenta", "bright_yellow",
    "bright_green", "bright_red", "bright_blue", "purple",
    "orange1", "deep_pink1", "gold1", "spring_green1",
]

COLOR_DESCRIPTIONS = {
    "logo":             "ASCII logo colour",
    "prompt_option":    "Prompt search card",
    "random_option":    "Random photo card",
    "procedural_option":"Procedural art card",
    "clear_option":     "Clear folder card",
    "quit_option":      "Quit card",
    "spinner":          "Loading spinner",
    "saved_text":       "Saved / success messages",
}

EXTRA_DESCRIPTIONS = {
    "auto_set_wallpaper":  "Skip 'set as wallpaper?' prompt and apply automatically",
    "default_menu_choice": "Which option is pre-selected when the menu opens (1-5)",
    "show_file_path":      "Show the saved file path after generating",
    "confirm_before_set":  "Ask for confirmation before setting wallpaper",
}


# ── Config I/O ────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)


# ── UI helpers ────────────────────────────────────────────────────────────────

def print_header():
    console.clear()
    console.print(Text(ASCII_LOGO, style="bold magenta"), justify="center")
    console.print(Align.center(Text("wallpapergen · settings", style="dim white")))
    console.print()


def color_swatch(name: str) -> str:
    """Return a coloured block to preview the colour inline."""
    return f"[{name}]███[/{name}]"


def show_current(cfg: dict):
    colors = cfg.get("colors", {})
    extras = cfg.get("extras", {})

    color_table = Table(box=box.SIMPLE, show_header=True, header_style="bold white",
                        title="[bold]Colors[/]", title_style="bold magenta")
    color_table.add_column("Key", style="dim")
    color_table.add_column("Value")
    color_table.add_column("Preview")
    color_table.add_column("Description", style="dim")
    for k, desc in COLOR_DESCRIPTIONS.items():
        v = colors.get(k, "—")
        swatch = color_swatch(v) if v in COLORS else "[dim]?[/]"
        color_table.add_row(k, f"[bold]{v}[/]", swatch, desc)

    extra_table = Table(box=box.SIMPLE, show_header=True, header_style="bold white",
                        title="[bold]Extras[/]", title_style="bold cyan")
    extra_table.add_column("Key", style="dim")
    extra_table.add_column("Value")
    extra_table.add_column("Description", style="dim")
    for k, desc in EXTRA_DESCRIPTIONS.items():
        v = extras.get(k, "—")
        display = f"[bold green]{v}[/]" if v is True else (f"[bold red]{v}[/]" if v is False else f"[bold]{v}[/]")
        extra_table.add_row(k, display, desc)

    console.print(Columns([color_table, extra_table], expand=True))
    console.print()


def pick_color(current: str) -> str:
    console.print()
    rows = []
    for i, c in enumerate(COLORS, 1):
        rows.append(f"[bold]{i:>2}[/]  {color_swatch(c)}  [{c}]{c}[/{c}]")

    # Print in 3 columns manually
    col_size = len(rows) // 3 + 1
    cols = [rows[i:i+col_size] for i in range(0, len(rows), col_size)]
    max_rows = max(len(c) for c in cols)
    for row_i in range(max_rows):
        line = ""
        for col in cols:
            line += (col[row_i] if row_i < len(col) else "").ljust(36)
        console.print(line)

    console.print()
    choice = Prompt.ask(
        f"[dim]Enter number or colour name (current: [{current}]{current}[/{current}])[/]",
        console=console
    ).strip()

    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(COLORS):
            return COLORS[idx]
    elif choice in COLORS:
        return choice

    console.print("[dim]  Invalid — keeping current value.[/]")
    return current


def edit_colors(cfg: dict) -> dict:
    colors = cfg.setdefault("colors", {})
    keys = list(COLOR_DESCRIPTIONS.keys())

    for i, k in enumerate(keys, 1):
        console.print(f"  [bold]{i:>2}[/]  [dim]{k}[/]  — {COLOR_DESCRIPTIONS[k]}")
    console.print(f"  [bold]{len(keys)+1:>2}[/]  [dim]back[/]")
    console.print()

    choice = Prompt.ask("[bold magenta]  Which colour to change[/]", console=console).strip()
    if not choice.isdigit():
        return cfg
    idx = int(choice) - 1
    if idx < 0 or idx >= len(keys):
        return cfg

    key = keys[idx]
    new_val = pick_color(colors.get(key, "cyan"))
    colors[key] = new_val
    console.print(f"\n  [bold green]Set[/] [bold]{key}[/] → [{new_val}]{new_val}[/{new_val}]\n")
    return cfg


def edit_extras(cfg: dict) -> dict:
    extras = cfg.setdefault("extras", {})
    keys = list(EXTRA_DESCRIPTIONS.keys())

    for i, k in enumerate(keys, 1):
        v = extras.get(k, "—")
        console.print(f"  [bold]{i:>2}[/]  [dim]{k}[/] = [bold]{v}[/]  — {EXTRA_DESCRIPTIONS[k]}")
    console.print(f"  [bold]{len(keys)+1:>2}[/]  [dim]back[/]")
    console.print()

    choice = Prompt.ask("[bold cyan]  Which setting to change[/]", console=console).strip()
    if not choice.isdigit():
        return cfg
    idx = int(choice) - 1
    if idx < 0 or idx >= len(keys):
        return cfg

    key = keys[idx]
    current = extras.get(key)

    if isinstance(current, bool):
        new_val = Confirm.ask(f"  [bold]{key}[/]", default=current, console=console)
    elif key == "default_menu_choice":
        new_val = Prompt.ask(f"  [dim]Current: {current}[/]  Enter 1–4", console=console).strip()
        if new_val not in ("1", "2", "3", "4"):
            console.print("[dim]  Invalid — keeping current.[/]")
            new_val = current
    else:
        new_val = Prompt.ask(f"  [dim]Current: {current}[/]  New value", console=console).strip()

    extras[key] = new_val
    console.print(f"\n  [bold green]Set[/] [bold]{key}[/] → [bold]{new_val}[/]\n")
    return cfg


def reset_defaults(cfg: dict) -> dict:
    if Confirm.ask("  [bold red]Reset ALL settings to defaults?[/]", default=False, console=console):
        CONFIG_PATH.unlink(missing_ok=True)
        console.print("  [bold green]Reset done.[/]\n")
        return load_config()
    console.print("[dim]  Cancelled.[/]\n")
    return cfg


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    cfg = load_config()

    while True:
        print_header()
        show_current(cfg)

        options = [
            Panel("[bold magenta]1[/] · Edit colors\n[dim]Change UI element colours[/]",
                  border_style="magenta", box=box.ROUNDED),
            Panel("[bold cyan]2[/] · Edit extras\n[dim]Behaviour settings[/]",
                  border_style="cyan", box=box.ROUNDED),
            Panel("[bold yellow]3[/] · Reset defaults\n[dim]Restore original config[/]",
                  border_style="yellow", box=box.ROUNDED),
            Panel("[bold red]q[/] · Back / quit\n[dim] [/]",
                  border_style="red", box=box.ROUNDED),
        ]
        console.print(Columns(options, equal=True, expand=True))
        console.print()

        choice = Prompt.ask("[bold white]  Choose[/]", default="1", console=console).strip().lower()
        console.print()

        if choice == "1":
            cfg = edit_colors(cfg)
            save_config(cfg)
        elif choice == "2":
            cfg = edit_extras(cfg)
            save_config(cfg)
        elif choice == "3":
            cfg = reset_defaults(cfg)
        elif choice in ("q", "quit", "exit", "b", "back"):
            console.print("[dim]  bye[/]\n")
            break
        else:
            console.print("[dim]  Unknown option.[/]\n")

        input("  Press Enter to continue …")


if __name__ == "__main__":
    main()
