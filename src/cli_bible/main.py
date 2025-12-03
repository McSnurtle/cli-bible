# cli-bible main.py - by Mc_Snurtle

# ===== Imports =====
import curses
import sys

from utils.config import get_config, set_config
from utils.getter import get_chapter, chapter_to_lines, get_raw, get_random_verse, verse_to_string, \
    get_book, get_next_chapter
from widgets import (Screen, ScrollableFrame, Entry)

# ===== Variables =====
RUNNING: bool = True
config = get_config()
books: list[str] = []


# ===== Functions =====
class Main(Screen):
    def __init__(self, stdscr):
        super().__init__(stdscr)

        height, width = self.stdscr.getmaxyx()
        tips: list[str] = ["[Q]uit", "[F]ind", "[N]ext", "[P]revious"]
        tip_str = "     ".join(tips)
        self.frame = ScrollableFrame(stdscr, 0, 0, width, height - 3,
                                     [verse_to_string(get_random_verse(config["translation"])[1]["random_verse"])])
        tips_win = curses.newwin(3, width, height - 3, 0)
        try:
            tips_win.addstr(
                1, (width // 2) - (len(tip_str) // 2), tip_str
            )
        except curses.error:
            pass
        tips_win.border()

        self.search = Entry(stdscr=stdscr, title="", width=20, y=height // 2, x=width // 2 - 10, prompt="i.e. John 3")

        self.add_window(tips_win, fill=[])
        self.add_widget(self.search)
        self.add_widget(self.frame)

        self.focus_next()
        self.update()

        try:
            while RUNNING:
                event = self.stdscr.getch()
                self.event_loop(event)

        except KeyboardInterrupt:
            stop()

    def event_loop(self, key: int) -> None:
        # print(key)
        if not key or key == -1:
            pass
        elif key == 9:
            self.focus_next()
            self.update()
        elif key == ord("f"):
            self.find_prompt()
        elif key == ord("n"):
            self._next_chapter(steps=1)
        elif key == ord("p"):
            self._next_chapter(steps=-1)
        elif key == ord("q"):
            stop()
        elif key == curses.KEY_RESIZE:
            self.update()
        elif len(self.widgets) > 0:
            self.widgets[self.current_widget].handle_event(key)
        self.update()

    def find_prompt(self) -> bool:
        # This is actually the most disgusting code I've ever written other than the 200 if statements that one time
        # I kind of can't believe I'm including this in this project
        result: str = self.focus_to(self.search)
        if not 3 > len(result.split(" ")):
            return self._end_search(success=False)

        code, response = get_raw(translation=config["translation"], raw=result)
        if code != 200:
            if len(result.split(" ")) == 1:
                code, response = get_book(translation=config["translation"], book=result)
                if code != 200:
                    return self._end_search(success=False)
                else:
                    self.frame.lines.clear()
                    for chapter in response["chapters"]:
                        self.frame.lines.append(f"Chapter {chapter['chapter']}")
                        code, verses = get_chapter(translation=config["translation"], book=chapter["book"],
                                                   chapter=chapter["chapter"])
                        if "verses" in verses.keys():
                            for verse in chapter_to_lines(verses["verses"]):
                                self.frame.lines.append(verse)
                    config["book"] = result
                    config["chapter"] = None
                    config["verse"] = None
                    set_config(config)
            else:
                return self._end_search(success=False)
                # I'm physically cringing right now
        else:
            self.frame.lines = chapter_to_lines(response["verses"])
            new_data = result.split(" ")
            config["book"] = new_data[0]
            config["chapter"] = int(new_data[1])
            set_config(config)
        return self._end_search(success=True)

    def _end_search(self, success: bool = False) -> bool:
        if not success:
            curses.beep()
        else:
            self.frame.offset = 1  # scroll to top of new page if successful
        self.focus_to(self.frame)
        self.search.contents = ""
        return success

    def _next_chapter(self, steps: int = 1) -> None:
        code, response = get_next_chapter(translation=config["translation"], book=config["book"],
                                          chapter=config["chapter"], steps=steps)
        if code == 200:
            book, chapter = response["reference"].split(" ")
            config["book"], config["chapter"] = book, int(chapter)
            self.frame.lines = chapter_to_lines(response["verses"])
            self.update()


def stop(code: int = 0) -> None:
    if code != 0: curses.beep()
    set_config(config)
    sys.exit(code)


def launch() -> None:
    curses.wrapper(Main)


if __name__ == "__main__":
    launch()
