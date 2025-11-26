# cli-bible main.py - by Mc_Snurtle

# ===== Imports =====
import curses
import sys

from widgets import (Screen, Entry, HORIZONTAL, VERTICAL)

# ===== Variables =====
RUNNING: bool = True


# ===== Functions =====
class Main(Screen):
    def __init__(self, stdscr):
        super().__init__(stdscr)

        height, width = stdscr.getmaxyx()
        # top search bar
        self.search_bar = curses.newwin(3, width, 0, 0)
        self.add_window(self.search_bar, fill=[HORIZONTAL])
        self.add_widget(Entry(self.search_bar, 1, 0, width=10, title="Version", prompt="i.e. NIV"))
        self.update()

        try:
            while RUNNING:
                height, width = stdscr.getmaxyx()
                # [win["object"].border() for win in self.windows]
                # self.search_bar.border()

                event = stdscr.getch()
                self.event_loop(event)

                self.update()
        except KeyboardInterrupt:
            stop()

    def event_loop(self, key: int) -> None:
        if not key or key == -1:
            pass
        elif key == 9:
            self.focus_next()
        elif key == ord("q"):
            stop()
        # elif key == curses.KEY_RESIZE:
        #     self.resize_all()
        elif len(self.widgets) > 0:
            self.widgets[self.current_widget].handle_event(key)


def stop(code: int = 0) -> None:
    if code != 0: curses.beep()
    sys.exit(code)


def launch() -> None:
    curses.wrapper(Main)


if __name__ == "__main__":
    launch()
