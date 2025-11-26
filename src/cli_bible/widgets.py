# imports, widgets.py - by Mc_Snurtle
import curses
import curses.textpad

from typing import (Any, Union)

# ===== Constants =====
HORIZONTAL: int = 0
VERTICAL: int = 1


# ===== Classes =====
class Widget:
    x: int
    y: int
    focused: bool = False
    stdscr: Any

    def __init__(self, stdscr, x: int, y: int):
        self.stdscr = stdscr
        self.x = x
        self.y = y

    def update(self) -> None:
        pass

    def handle_event(self, event: int) -> bool:
        """Custom event handler meant to be overwritten.

        Return:
            :returns bool: whether the event was used or not."""
        pass

    def focus(self) -> None:
        self.focused = True

    def unfocus(self) -> None:
        self.focused = False


class Entry(Widget):
    width: int
    title: str
    prompt: str

    def __init__(self, stdscr: Any, x: int, y: int, width: int, title: str, prompt: str = "i.e. A Squirrel"):
        super().__init__(stdscr, x, y)
        self.width = width
        self.title = f"{title}: "
        self.prompt = prompt
        self.contents: str = self.title + ("" if not self.prompt else self.prompt)

        self.editing: bool = False

        self.title_win = curses.newwin(1, len(self.title) + 1, self.y + 1, self.x)
        self.title_win.addstr(0, 0, self.title)
        self.outer_win = curses.newwin(3, self.width + 2,
                                       self.y, self.x + len(self.title))
        self.edit_win = curses.newwin(1, self.width,
                                      self.y + 1, self.x + 1 + len(self.title))
        self.edit_win.keypad(True)
        self.textbox = curses.textpad.Textbox(self.edit_win, insert_mode=True)

    def update(self) -> None:
        self.title_win.noutrefresh()
        # self.outer_win.erase()
        self.outer_win.border()
        display = self.prompt if not self.contents else self.contents
        self.outer_win.addstr(1, 1, display[:self.width].ljust(self.width))
        self.outer_win.noutrefresh()

    def focus(self) -> None:
        self.focused = True
        self.editing = True
        if self.contents == self.prompt:
            self.contents = ""
        self.edit_win.clear()
        self.edit_win.addstr(0, 0, self.contents)
        self.edit_win.move(0, len(self.contents))
        curses.curs_set(1)
        self.update()

        self.contents = self.textbox.edit(validate=self._enter_validator).strip()

        self.editing = False
        curses.curs_set(0)
        self.update()

    @classmethod
    def _enter_validator(cls, ch: int) -> int:
        """Allow TAB, ENTER, ESC, or CTRL+G to exit focus of an Entry()."""
        if ch in (curses.KEY_ENTER, 10, 13, 9):
            return 7  # Ctrl + G
        return ch

    def unfocus(self) -> None:
        self.focused = False
        self.editing = False
        self.contents = self.get()
        if not self.contents:
            self.contents = self.prompt
        curses.curs_set(0)
        self.update()

    def handle_event(self, event: int) -> bool:
        if self.editing and event in [curses.KEY_ENTER, 10, 13, 9, 27]:  # Grok AI told me these keycodes
            self.unfocus()
            return True
        return False

    def get(self) -> str:
        """Return the contents of the window as a stripped string"""
        return self.textbox.gather().strip()


class Screen:
    widgets: list[Widget] = []
    windows: list[dict[str, Any]] = []
    current_widget: int = 0

    def __init__(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)

    def add_window(self, window: Any, fill: list[int]):
        """Register a _CursesWindow to the class"""
        self.windows.append({
            "object": window,
            "fill": fill
        })

    def add_widget(self, widget: Widget):
        """Register a Widget to the class"""
        self.widgets.append(widget)

    def update(self):
        """Call `.update()` on all registered `Widget` objects, and refresh the screen."""
        [window["object"].noutrefresh() for window in self.windows]

        self.stdscr.noutrefresh()
        curses.doupdate()

    def resize_all(self) -> None:
        for winfo in self.windows:
            window: Any = winfo["object"]
            fill: list[int] = winfo["fill"]

            win_height, win_width = window.getmaxyx()
            scr_height, scr_width = self.stdscr.getmaxyx()
            if HORIZONTAL in fill:
                win_width = scr_width
            if VERTICAL in fill:
                win_height = scr_height

                window.resize(win_height, win_width)

    def focus_next(self, index: Union[int, None] = None) -> None:
        """Focus the next registered widget in order of registry.

        Params:
            :param index: the index of the widget to switch to (optional)
            :type index: int"""

        if not len(self.widgets) > 0:
            return
        self.widgets[self.current_widget].unfocus()
        if index is None:
            self.current_widget = (self.current_widget + 1) % len(self.widgets)
        elif isinstance(index, int):
            if index <= len(self.widgets):
                self.current_widget = index
            else:
                raise IndexError(f"{index} is outside of bounds of registered widgets.")
        self.widgets[self.current_widget].focus()
