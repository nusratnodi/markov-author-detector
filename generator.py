"""
Person 3: Text generator
Writes new sentences in an author's style by walking through the Markov chain.
"""

import random


def generate_text(model, sentences=3, max_words=150):
    state = random.choice(model.sentence_starts)
    words = list(state)

    while len(words) < max_words:
        counts = model.transitions.get(state)
        if not counts:
            break

        # pick the next word randomly, but common next words are picked more often
        next_word = random.choices(list(counts.keys()), weights=list(counts.values()))[0]
        words.append(next_word)

        if next_word in ".!?":
            sentences -= 1
            if sentences == 0:
                break

        state = tuple(words[-model.order:])

    return make_readable(words)


def make_readable(words):
    """Join the words back into normal text: capital letters and no space before full stops."""
    text = ""
    capitalize_next = True
    for word in words:
        if word in ".!?":
            text += word
            capitalize_next = True
        else:
            if word == "i":
                word = "I"
            if capitalize_next:
                word = word.capitalize()
                capitalize_next = False
            text += " " + word
    return text.strip()
