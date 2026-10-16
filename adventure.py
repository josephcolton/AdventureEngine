"""Adventure Engine -- start here.

    python adventure.py                 open the window
    python adventure.py --text [FILE]   play in the terminal instead
    python adventure.py --check FILE    check an adventure file for mistakes
"""

import sys


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in ("--text", "--check"):
        from engine import textmode
        textmode.main(args[1:] if args[0] == "--text" else args)
        return
    from gui.app import main as run_window
    run_window()


if __name__ == "__main__":
    main()
