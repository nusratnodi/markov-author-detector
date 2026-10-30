"""
Author Detector + Text Generator using Markov chains.
Run with:  python3 main.py
"""

import random

from data import BOOKS, download_books, load_words, split_train_test, make_chunks, tokenize
from markov import MarkovChain
from generator import generate_text
from detector import detect_author, evaluate

AUTHORS = list(BOOKS)


def train_models(order):
    """Train one Markov chain per author and keep the unseen part of each book for testing."""
    models = {}
    test_passages = {}
    for author in AUTHORS:
        train_words, test_words = split_train_test(load_words(author))
        models[author] = MarkovChain(order)
        models[author].train(train_words)
        test_passages[author] = make_chunks(test_words)

    # All models must use the same vocabulary. Otherwise the author with the
    # smallest vocabulary gets an unfair advantage on words they never used.
    all_words = set().union(*(model.vocabulary for model in models.values()))
    for model in models.values():
        model.vocabulary = all_words

    return models, test_passages


def choose_author():
    for number, author in enumerate(AUTHORS, start=1):
        print(f"  {number}. {author}")
    choice = input("Choose an author: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(AUTHORS):
        return AUTHORS[int(choice) - 1]
    print("Invalid choice.")
    return None


def show_guess(models, words):
    ranking, scores = detect_author(models, words)
    print(f"\n  Guess: {ranking[0]}\n")
    print("  Ranking (score: higher = closer match)")
    for place, author in enumerate(ranking, start=1):
        print(f"    {place}. {author:<20} {scores[author]:.1f}")


def generate_menu(generation_models):
    author = choose_author()
    if author:
        print(f"\n  {author} (generated):\n")
        print("  " + generate_text(generation_models[author], sentences=3))


def guess_typed_menu(detection_models):
    print("Paste a passage (press Enter on an empty line to finish):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    words = tokenize(" ".join(lines))
    if len(words) < 5:
        print("Please enter at least a few words.")
        return
    show_guess(detection_models, words)


def guess_random_menu(detection_models, test_passages):
    true_author = random.choice(AUTHORS)
    words = random.choice(test_passages[true_author])
    print(f'\n  Passage: "{" ".join(words)}"')
    show_guess(detection_models, words)
    print(f"\n  Real author: {true_author}")


def accuracy_menu():
    print("\nTesting on passages of 50 words the models have never seen...")
    for order in (1, 2, 3):
        models, test_passages = train_models(order)
        accuracy = evaluate(models, test_passages)
        average = sum(accuracy.values()) / len(accuracy)
        print(f"\n  Order {order} (looks at the last {order} word(s)): average accuracy {average:.0%}")
        for author in AUTHORS:
            print(f"    {author:<20} {accuracy[author]:.0%}")


def main():
    download_books()
    print("Training models...")
    detection_models, test_passages = train_models(order=1)  # order 1 is best for detection
    generation_models, _ = train_models(order=2)              # order 2 writes more natural text

    while True:
        print("\n===== Markov Author Detector =====")
        print("1. Write new text in an author's style")
        print("2. Guess the author of a passage you paste")
        print("3. Guess the author of a random unseen passage")
        print("4. Measure accuracy")
        print("5. Quit")
        choice = input("Choose: ").strip()

        if choice == "1":
            generate_menu(generation_models)
        elif choice == "2":
            guess_typed_menu(detection_models)
        elif choice == "3":
            guess_random_menu(detection_models, test_passages)
        elif choice == "4":
            accuracy_menu()
        elif choice == "5":
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
