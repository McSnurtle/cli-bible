# imports, widgets.py - by Mc_Snurtle
import curses
import curses.textpad
import textwrap

from typing import Any

# ===== Constants =====
HORIZONTAL: int = 0
VERTICAL: int = 1


# ===== Classes =====
class Widget:
    x: int
    y: int
    widget_type: str
    focused: bool = False
    stdscr: Any
    binds: list[int]

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
        if not self.focused or event not in self.binds:
            return False

        return True

    def focus(self) -> None:
        self.focused = True

    def unfocus(self) -> None:
        self.focused = False


class Entry(Widget):
    width: int
    title: str
    prompt: str
    widget_type = "Entry"
    binds = [curses.KEY_ENTER, 9, 10, 13, 27]

    def __init__(self, stdscr: Any, x: int, y: int, width: int, title: str, prompt: str = "i.e. A Squirrel"):
        super().__init__(stdscr, x, y)
        self.width = width
        self.title = f"{title}: "
        self.prompt = prompt
        self.contents: str = ("" if not self.prompt else self.prompt)

        self.editing: bool = False

        self.title_win = curses.newwin(1, len(self.title) + 1, self.y + 1, self.x)
        self.title_win.addstr(0, 0, self.title)
        # TODO: add truncation to title and content to ensure no out of bounds errors
        self.outer_win = curses.newwin(3, self.width + 2,
                                       self.y, self.x + len(self.title))
        self.edit_win = curses.newwin(1, self.width,
                                      self.y + 1, self.x + 1 + len(self.title))
        self.edit_win.keypad(True)
        self.textbox = curses.textpad.Textbox(self.edit_win, insert_mode=True)

    def __len__(self):
        """Returns the length in cols the entire textbox will take up including titles and borders."""
        return len(self.title) + len(self.contents) + 2

    def update(self) -> None:
        self.title_win.noutrefresh()
        # self.outer_win.erase()
        self.outer_win.border()
        display = self.prompt if not self.contents else self.contents
        self.outer_win.addstr(1, 1, display[:self.width].ljust(self.width))
        self.outer_win.noutrefresh()

    def focus(self) -> str:
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
        return self.contents

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


class ScrollableFrame(Widget):
    offset: int
    lines: list[str] = []
    widget_type = "ScrollableFrame"
    binds = [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_PPAGE, curses.KEY_NPAGE]
    width: int
    height: int

    def __init__(self, stdscr, x: int, y: int, width: int, height: int, lines: list[str]):
        super().__init__(stdscr, x, y)

        self.width, self.height = width, height
        self.wrapper = textwrap.TextWrapper(width=self.width - 2)
        self.lines = lines

        # self.lines = []
        # for line in lines:
        #     for f_line in self.wrapper.wrap(line):
        #         self.lines.append(f_line)
        self.offset = 1
        self._window = curses.newwin(height, width)
        # TODO: make this ^^^ a `curses.newpad()` instead, see: https://docs.python.org/3/library/curses.html#curses.newpad

    def update(self) -> None:
        self._window.erase()
        self._window.border()

        idx = 0
        for line in self.lines:
            f_lines = self.wrapper.wrap(text=line)
            try:

                for f_idx, f_line in enumerate(f_lines):
                    idx += f_idx
                    y_dest = idx + self.offset
                    if self.height - 1 > y_dest > 0:  # don't render over window borders
                        self._window.addstr(idx + self.offset,
                                            1, f_line)

            except curses.error:  # if outside screen bounds
                pass

            idx += 2

        self._window.noutrefresh()
        # self._window.noutrefresh(self.offset - 1, 0, self.y, self.x, self.y + self.height - 1, self.x + self.width - 1 )

    def handle_event(self, event: int) -> bool:

        if not self.focused or event not in self.binds:
            return False

        if event == curses.KEY_UP:
            self.scroll_up(1)
        elif event == curses.KEY_DOWN:
            self.scroll_down(1)
        elif event == curses.KEY_PPAGE:  # pg up
            self.scroll_up(self.height - 2)
        elif event == curses.KEY_NPAGE:  # pg down
            self.scroll_down(self.height - 2)
        return True

    # TODO: make these have a limit, so that at least one line is always visible
    def scroll_up(self, lines: int) -> None:
        if len(self.lines) * 2 > self.height - 2:
            self.offset = min(self.offset + lines, 1)
            self.update()

    def scroll_down(self, lines: int) -> None:
        if len(self.lines) * 2 > self.height - 2:   # if the lines even exceed the page...
            self.offset = max(self.offset - lines, -len(self.lines) * 2 + self.height)
            self.update()


class Screen:
    widgets: list[Widget] = []
    windows: list[dict[str, Any]] = []
    current_widget: int = 0
    widget_type = "Screen"

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
        for window in self.windows:
            window["object"].border()
            window["object"].noutrefresh()
        # [window["object"].noutrefresh() for window in self.windows]
        [widget.update() for widget in self.widgets]

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

    def focus_to(self, widget: Widget) -> Any:
        if widget not in self.widgets:
            raise IndexError(f"Application does not have widget '{widget}' registered!")

        self.widgets[self.current_widget].unfocus()
        return self.widgets[self.widgets.index(widget)].focus()

    def focus_next(self, index: int | None = None) -> Any:
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
        return self.widgets[self.current_widget].focus()
