# cli-bible main.py - by Mc_Snurtle

# ===== Imports =====
import curses
import sys


# ===== Variables =====
RUNNING: bool = True



# ===== Functions =====
def main(stdscr) -> None:
    curses.curs_set(False)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    try:
        while RUNNING:
            event_loop(stdscr)
    except KeyboardInterrupt:
        stop()

def stop(code: int) -> None:
    curses.beep()
    sys.exit(code)

