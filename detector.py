"""
Person 4: Author detector and evaluation
Guesses who wrote a passage and measures how often the guess is right.
"""


def detect_author(models, words):
    """
    Ask every author's model how likely the passage is.
    The author whose model gives the highest probability is our guess.
    """
    scores = {author: model.log_probability(words) for author, model in models.items()}
    ranking = sorted(scores, key=scores.get, reverse=True)
    return ranking, scores


def evaluate(models, test_passages):
    """Return the accuracy for each author on passages the models have never seen."""
    accuracy = {}
    for author, passages in test_passages.items():
        correct = sum(detect_author(models, words)[0][0] == author for words in passages)
        accuracy[author] = correct / len(passages)
    return accuracy
