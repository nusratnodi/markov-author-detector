"""
Person 2: The Markov model
Learns which word usually comes after which.
"""

import math
from collections import Counter, defaultdict


class MarkovChain:
    def __init__(self, order=1, smoothing=0.01):
        self.order = order                       # how many previous words the model looks at
        self.smoothing = smoothing               # small extra count given to every word (see probability)
        self.transitions = defaultdict(Counter)  # state -> how many times each next word followed it
        self.sentence_starts = []                # states that begin a sentence (used by the generator)
        self.vocabulary = set()

    def train(self, words):
        """Count every 'state -> next word' pair in the training text."""
        for i in range(len(words) - self.order):
            state = tuple(words[i:i + self.order])
            next_word = words[i + self.order]
            self.transitions[state][next_word] += 1

            if i > 0 and words[i - 1] in ".!?" and not any(w in ".!?" for w in state):
                self.sentence_starts.append(state)

        self.vocabulary.update(words)

    def probability(self, state, next_word):
        """
        P(next_word | state) with smoothing.
        Smoothing gives unseen words a small chance instead of zero,
        otherwise one new word would make a whole passage 'impossible'.
        """
        counts = self.transitions.get(state, Counter())
        k = self.smoothing
        return (counts[next_word] + k) / (sum(counts.values()) + k * (len(self.vocabulary) + 1))

    def log_probability(self, words):
        """How likely is it that this model produced these words? (higher = more likely)"""
        total = 0.0
        for i in range(len(words) - self.order):
            state = tuple(words[i:i + self.order])
            total += math.log(self.probability(state, words[i + self.order]))
        return total
