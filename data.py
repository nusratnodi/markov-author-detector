"""
Person 1: Data
Downloads the books and turns them into lists of words.
"""

import os
import re
import urllib.request

# One free book per author from Project Gutenberg (author -> book id)
BOOKS = {
    "Jane Austen": 1342,         # Pride and Prejudice
    "Charles Dickens": 98,       # A Tale of Two Cities
    "Arthur Conan Doyle": 1661,  # The Adventures of Sherlock Holmes
    "Mark Twain": 74,            # The Adventures of Tom Sawyer
}

DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def book_path(author):
    return os.path.join(DATA_FOLDER, author.replace(" ", "_") + ".txt")


def download_books():
    """Download each book once and save it in the data folder."""
    os.makedirs(DATA_FOLDER, exist_ok=True)
    for author, book_id in BOOKS.items():
        if os.path.exists(book_path(author)):
            continue
        url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        print(f"Downloading {author}...")
        urllib.request.urlretrieve(url, book_path(author))


def remove_gutenberg_header(text):
    """Keep only the story, without the Project Gutenberg licence text."""
    start = text.find("*** START")
    end = text.find("*** END")
    start = text.find("\n", start) + 1  # skip the START line itself
    return text[start:end]


def tokenize(text):
    """Split text into lowercase words. Sentence endings (. ! ?) are kept as their own tokens."""
    text = text.lower().replace("’", "'")
    text = re.sub(r"\b(mr|mrs|dr|st)\.", r"\1", text)  # "Mr." is not the end of a sentence
    return re.findall(r"[a-z]+(?:'[a-z]+)*|[.!?]", text)


def load_words(author):
    with open(book_path(author), encoding="utf-8") as f:
        text = f.read()
    return tokenize(remove_gutenberg_header(text))


def split_train_test(words, test_part=0.2):
    """First 80% of the book is used for training, last 20% for testing."""
    cut = int(len(words) * (1 - test_part))
    return words[:cut], words[cut:]


def make_chunks(words, size=50):
    """Cut the test words into small passages of `size` words each."""
    return [words[i:i + size] for i in range(0, len(words) - size + 1, size)]
