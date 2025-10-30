# sentiment.py
from textblob import TextBlob
from nltk.sentiment.vader import SentimentIntensityAnalyzer

_vader = None

def get_sentiment(text):
    """
    Return 'positive', 'neutral', or 'negative' based on text.
    Uses TextBlob polarity and VADER as fallback.
    """
    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1..1
        if polarity > 0.2:
            return 'positive'
        if polarity < -0.15:
            return 'negative'
    except Exception:
        pass

    # fallback to VADER
    global _vader
    if _vader is None:
        _vader = SentimentIntensityAnalyzer()
    score = _vader.polarity_scores(text)['compound']
    if score >= 0.3:
        return 'positive'
    if score <= -0.25:
        return 'negative'
    return 'neutral'
