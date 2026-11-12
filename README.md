# Markov Author Detector + Text Generator

A Markov chain learns the writing style of 4 authors. It can then:

1. **Write new text** in an author's style.
2. **Guess who wrote** a passage it has never seen.

Only standard Python is used. There is nothing to install.

## How to run

```
python3 main.py
```

The first run downloads the books from Project Gutenberg into `data/`. After that it works offline.

### Web interface

```
python3 server.py
```

This opens http://localhost:8000 in your browser and shows the same four features as the console menu, with
one tab each. It still uses only standard Python. To use a different port, run `python3 server.py 8080`.

## How it works

**1. Learning.** The model reads a book and counts which word comes after which word.
For example, Jane Austen writes "my" 728 times, and 124 of those are followed by "dear".
So P("dear" | "my") = 124 / 728 = 0.17. Next come "own" (0.04) and "father" (0.03).
This is a Markov chain: the next word depends only on the current word (the "state").

**2. Generating text.** Start at the beginning of a sentence. Pick the next word at random using those
probabilities, then repeat. For generation the model looks at the last **2** words (order 2), which gives
more natural sentences.

**3. Detecting the author.** For a new passage, each author's model calculates how likely it is that
*that author* wrote these words in this order. The author with the highest probability is the guess.

- **Smoothing:** a word pair the model never saw would get probability 0 and rule that author out
  completely. So every word gets a tiny extra count (0.01).
- **Shared vocabulary:** all 4 models use the same word list. Without it, the author with the smallest
  vocabulary wins unfairly. Before we fixed this, almost every passage was labelled "Jane Austen".

## Data

| Author | Book |
|---|---|
| Jane Austen | Pride and Prejudice |
| Charles Dickens | A Tale of Two Cities |
| Arthur Conan Doyle | The Adventures of Sherlock Holmes |
| Mark Twain | The Adventures of Tom Sawyer |

The first 80% of each book is used for training. The last 20% is cut into 50-word passages for testing
(1,881 passages in total). The models never see these passages during training.

## Results

| Order (previous words looked at) | Austen | Dickens | Doyle | Twain | **Average** |
|---|---|---|---|---|---|
| 1 | 96% | 85% | 75% | 79% | **84%** |
| 2 | 85% | 67% | 74% | 59% | 71% |
| 3 | 62% | 46% | 62% | 45% | 54% |

Random guessing would get 25%. Looking at more previous words makes the generated text better but the
detection worse. With longer word sequences, most of them never appeared in the training book, so the model
has less evidence to compare. That is why the program uses order 1 for detection and order 2 for generation.
Mark Twain's book is the shortest, so his model has the least training data.

(Run menu option 4 to reproduce this table.)

## Who does what

| Person | File | Part |
|---|---|---|
| 1 | `data.py` | Downloading the books, cleaning the text, splitting into words, train/test split |
| 2 | `markov.py` | The `MarkovChain` class: counting transitions, probabilities, smoothing |
| 3 | `generator.py` | Generating new text from the chain and making it readable |
| 4 | `detector.py` | Guessing the author and measuring accuracy |
| All | `main.py` | The menu that connects everything |
| All | `server.py`, `web/` | The web interface (a small local server and an HTML/CSS/JS page) |

## Possible improvements

- Use more than one book per author.
- Add more authors.
- Test how accuracy changes with shorter or longer passages (change `size` in `make_chunks`).
