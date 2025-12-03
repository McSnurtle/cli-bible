# imports - getter.py, by McSnurtle
import requests
import time
import curses

from typing import Optional

# ===== Variables =====
MIN_DELAY: float = 0.6  # 15 requests / 30 seconds = 0.5 theoretical limit, +0.1 for variation
MAX_RETRIES: int = 5
_last_request_time: float = time.time()


def get(url: str, params: Optional[dict] = None) -> requests.Response:
    global _last_request_time

    elapsed: float = time.time() - _last_request_time
    if elapsed < MIN_DELAY:
        time.sleep(MIN_DELAY - elapsed)

    delay: float = 1
    notified: bool = False
    for attempt in range(MAX_RETRIES):
        response = requests.get(url, params=params)

        if response.status_code != 429:  # handle HTTP rate limit error
            return response

        if not notified:
            curses.beep()
            notified = True
        delay = min(delay * 2,
                    30)  # exponential backoff with a max limit of the 30 seconds if somehow you requested 15 chapters in under 1 second
        time.sleep(delay)


def available_bibles() -> tuple[int, list[dict]]:
    response: requests.Response = get("https://bible-api.com/data")
    return response.status_code, response.json() if response.status_code == 200 else {}


def available_books(translation: str) -> tuple[int, list[dict]]:
    response: requests.Response = get(f"https://bible-api.com/data/{translation}")
    return response.status_code, response.json()["books"] if response.status_code == 200 else {}


def _book_ids(translation: str) -> list[str]:
    """Returns a list of canonical book IDs for all available books in `translation`."""
    return [book["id"] for book in available_books(translation)[1]]


def _book_aliases(translation: str) -> tuple[int, dict[str, str]]:
    """Returns the status code of the request and a dictionary of all valid / possible book names to their respective canonical IDs for the `translation`."""
    code, book_data = available_books(translation)
    aliases: dict[str, str] = {}
    for book in book_data:
        aliases[book["id"].lower()] = book["id"]
        aliases[book["name"].lower()] = book["id"]
        aliases[book["name"].lower().replace(" ", "")] = book["id"]

    return code, aliases


def get_canonical_of_book(translation: str, book: str) -> str:
    code, aliases = _book_aliases(translation)
    book = book.lower()
    if book not in aliases:
        raise KeyError(f"No book {book} in {translation} translation.")
    return aliases[book]


def get_final_chapter_id(translation: str, book: str) -> int:
    """Returns the largest chapter number of all chapters found in `book` in `translation`.

    :param translation: The translation identifier to search in.
    :type translation: str
    :param book: The book to search in.

    :returns: The last chapter number in the `book` specified in `translation`.
    :rtype int:
    """
    book: str = get_canonical_of_book(translation=translation, book=book)
    code, response = get_book(translation, book)
    if code != 200:
        raise ValueError(f"No book {book} found in {translation} translation")
    return max(
        [chapter["chapter"] for chapter in response["chapters"]])  # return the largest ID from the returned chapters


def get_random_verse(translation: str) -> tuple[int, dict]:
    response: requests.Response = get(
        f"https://bible-api.com/data/{translation}/random"
    )
    return response.status_code, response.json() if response.status_code == 200 else {}


def get_book(translation: str, book: str) -> tuple[int, dict]:
    response: requests.Response = get(
        f"https://bible-api.com/data/{translation}/{book}"
    )
    return response.status_code, response.json() if response.status_code == 200 else {}


def get_chapter(translation: str, book: str, chapter: int) -> tuple[int, dict]:
    response: requests.Response = get(
        f"https://bible-api.com/{book}+{chapter}?translation={translation}&single_chapter_book_matching=indifferent")
    return response.status_code, response.json() if response.status_code == 200 else {}


def get_next_chapter(translation: str, book: str, chapter: int, steps: int) -> tuple[int, dict]:
    """Returns the status code of the request and the dictionary of the next chapter if present.

    :param translation: The translation identifier to use when searching for books / chapters.
    :type translation: str
    :param book: The book identifier (any valid identifier) for the current book.
    :type book: str
    :param chapter: The current chapter number within the book.
    :type chapter: int
    :param steps: The amount of chapters to skip. I.e. steps=1 would go to the next chapter, steps=-1 would go to the previous.
    :type steps: int

    :returns: Status code of the final request, along with the dictionary response of the new chapter if applicable.
    :rtype tuple[int, dict]:

    Returns status code 404 for chapter not available, and 200 if chapter exists.
    """
    chapter += steps
    book_ids = _book_ids(translation)
    book = get_canonical_of_book(translation, book)
    code, response = get_chapter(translation=translation, book=book, chapter=chapter)
    if code == 200:
        return code, response

    try:
        new_book = book_ids[book_ids.index(book) + steps]
        new_chapter = 1 if steps > 0 else get_final_chapter_id(translation, new_book)
        return get_chapter(translation=translation, book=new_book, chapter=new_chapter)
    except (ValueError, IndexError):
        return 404, {}  # no more books!


def get_raw(translation: str, raw: str) -> tuple[int, dict]:
    """Uses the bible-api's User Input API to allow shorthand and verse ranges. May return a chapter or specific verses.

    :param translation: The translation identifier to search in.
    :type translation: str
    :param raw: The user input to search for. May be 'Matthew 6', 'matt6', 'matt 6:3-5,8'
    :type raw: str

    :returns: The status code of the request and the JSON response if applicable.

    Status code 404 if the query is invalid or could not be found, and 200 if request was successful.
    """
    response: requests.Response = get(
        f"https://bible-api.com/{raw}?translation={translation}&single_chapter_book_matching=indifferent"
    )
    return response.status_code if raw != "" else 404, response.json() if response.status_code == 200 and raw != "" else {}


def chapter_to_lines(data: list[dict], include_numbers: bool = True) -> list[str]:
    lines = [f"{data[0]['book_name']} {data[0]['chapter']}:"]
    for verse in data:
        lines.append(verse_to_string(verse, include_numbers))
    return lines


def verse_to_string(data: dict, include_number: bool = True) -> str:
    prefix: str = ""
    if include_number:
        prefix = f"{data['verse']} "
    return f"{prefix}{data['text'].strip()}"


def get_verse(translation: str, book: str, chapter: int, verse: int) -> tuple[int, dict]:
    response: requests.Response = get(
        f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/{translation}/books/{book}/chapters/{chapter}/verses/{verse}.json")
    return response.status_code, response.json() if response.status_code == 200 else {}
