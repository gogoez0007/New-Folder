import sys
from datetime import datetime

# Ensure standard output and error streams handle UTF-8 / emojis on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_header(title: str):
    """Print an eye-catching section banner."""
    line = "=" * 70
    print(f"\n{Colors.CYAN}{Colors.BOLD}{line}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}  >>  {title.upper()}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}{line}{Colors.RESET}\n")



def log_step(step_num: int, total_steps: int, title: str):
    """Print a step progress indicator, e.g. [Step 1/5]."""
    prefix = f"[{_timestamp()}] [Step {step_num}/{total_steps}]"
    print(
        f"\n{Colors.MAGENTA}{Colors.BOLD}{prefix} {Colors.RESET}"
        f"{Colors.BOLD}{title}{Colors.RESET}"
    )


def log_info(msg: str):
    """Print an informational message."""
    print(f"{Colors.DIM}[{_timestamp()}]{Colors.RESET} {Colors.BLUE}[*]{Colors.RESET}  {msg}")


def log_success(msg: str):
    """Print a success message."""
    print(
        f"{Colors.DIM}[{_timestamp()}]{Colors.RESET} {Colors.GREEN}{Colors.BOLD}[+] SUCCESS:{Colors.RESET} {msg}"
    )


def log_warning(msg: str):
    """Print a warning message."""
    print(
        f"{Colors.DIM}[{_timestamp()}]{Colors.RESET} {Colors.YELLOW}{Colors.BOLD}[!] WARNING:{Colors.RESET} {msg}"
    )


def log_error(msg: str):
    """Print an error message."""
    print(
        f"{Colors.DIM}[{_timestamp()}]{Colors.RESET} {Colors.RED}{Colors.BOLD}[X] ERROR:{Colors.RESET} {msg}",
        file=sys.stderr,
    )


def log_scene(scene_num: int, duration: float, motion: str, narration: str):
    """Pretty-print a scene storyboard summary."""
    print(
        f"   {Colors.CYAN}> Scene {scene_num:02d}{Colors.RESET} "
        f"({duration:.1f}s | {Colors.YELLOW}{motion}{Colors.RESET}): "
        f'"{Colors.WHITE}{narration}{Colors.RESET}"'
    )

