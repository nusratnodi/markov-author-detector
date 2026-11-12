"""
Web interface for the Author Detector + Text Generator.
Run with:  python3 server.py   (then open http://localhost:8000)

Uses only the standard library, like the rest of the project.
The page itself lives in the web/ folder; this file answers its requests
by calling the same functions the console menu in main.py uses.
"""

import json
import os
import random
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from data import download_books, tokenize
from detector import detect_author, evaluate
from generator import generate_text, make_readable
from main import AUTHORS, train_models

WEB_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
MAX_BODY_BYTES = 200_000  # a pasted passage never needs more than this
MIN_WORDS = 5

BOOK_TITLES = {
    "Jane Austen": "Pride and Prejudice",
    "Charles Dickens": "A Tale of Two Cities",
    "Arthur Conan Doyle": "The Adventures of Sherlock Holmes",
    "Mark Twain": "The Adventures of Tom Sawyer",
}

_accuracy_cache = None
_accuracy_lock = threading.Lock()


def ranking_json(ranking, scores):
    return [{"author": author, "score": scores[author]} for author in ranking]


def accuracy_results():
    """Same test as menu option 4. Computed once, then reused."""
    global _accuracy_cache
    with _accuracy_lock:
        if _accuracy_cache is None:
            results = []
            for order in (1, 2, 3):
                models, test_passages = train_models(order)
                accuracy = evaluate(models, test_passages)
                results.append({
                    "order": order,
                    "authors": accuracy,
                    "average": sum(accuracy.values()) / len(accuracy),
                    "passages": sum(len(p) for p in test_passages.values()),
                })
            _accuracy_cache = results
    return _accuracy_cache


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_FOLDER, **kwargs)

    # ---------- routing ----------

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/info":
            self.send_json({
                "authors": [{"name": a, "book": BOOK_TITLES.get(a, "")} for a in AUTHORS],
                "minWords": MIN_WORDS,
            })
        elif path == "/api/random":
            self.random_passage()
        elif path == "/api/accuracy":
            self.send_json({"orders": accuracy_results()})
        elif path.startswith("/api/"):
            self.send_json({"error": "Not found."}, 404)
        else:
            super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        body = self.read_json()
        if body is None:
            return
        if path == "/api/generate":
            self.generate(body)
        elif path == "/api/detect":
            self.detect(body)
        else:
            self.send_json({"error": "Not found."}, 404)

    # ---------- API ----------

    def generate(self, body):
        author = body.get("author")
        if author not in AUTHORS:
            self.send_json({"error": "Unknown author."}, 400)
            return
        try:
            sentences = max(1, min(5, int(body.get("sentences", 3))))
        except (TypeError, ValueError):
            sentences = 3
        model = self.server.generation_models[author]
        self.send_json({
            "author": author,
            "order": model.order,
            "text": generate_text(model, sentences=sentences),
        })

    def detect(self, body):
        text = body.get("text")
        if not isinstance(text, str):
            self.send_json({"error": "Missing text."}, 400)
            return
        words = tokenize(text)
        if len(words) < MIN_WORDS:
            self.send_json({"error": f"Please enter at least {MIN_WORDS} words."}, 400)
            return
        ranking, scores = detect_author(self.server.detection_models, words)
        self.send_json({"wordCount": len(words), "ranking": ranking_json(ranking, scores)})

    def random_passage(self):
        true_author = random.choice(AUTHORS)
        words = random.choice(self.server.test_passages[true_author])
        ranking, scores = detect_author(self.server.detection_models, words)
        self.send_json({
            "passage": make_readable(words),
            "wordCount": len(words),
            "realAuthor": true_author,
            "ranking": ranking_json(ranking, scores),
        })

    # ---------- helpers ----------

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            length = 0
        if length > MAX_BODY_BYTES:
            self.send_json({"error": "Text is too long."}, 413)
            return None
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            body = None
        if not isinstance(body, dict):
            self.send_json({"error": "Invalid request."}, 400)
            return None
        return body

    def send_json(self, data, status=200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        pass  # keep the console quiet


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    download_books()
    print("Training models...")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.detection_models, server.test_passages = train_models(order=1)  # best for detection
    server.generation_models, _ = train_models(order=2)                    # more natural text

    url = f"http://localhost:{port}"
    print(f"Open {url} in your browser (Ctrl+C to stop).")
    threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
