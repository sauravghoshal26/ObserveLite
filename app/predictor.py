from opentelemetry import trace

tracer = trace.get_tracer(__name__)


POSITIVE_WORDS = {
    "amazing",
    "awesome",
    "excellent",
    "fantastic",
    "good",
    "great",
    "happy",
    "love",
    "nice",
    "reliable",
    "simple",
    "wonderful",
}

NEGATIVE_WORDS = {
    "awful",
    "bad",
    "broken",
    "confusing",
    "hate",
    "poor",
    "sad",
    "slow",
    "terrible",
    "unreliable",
    "worst",
}


def predict_sentiment(text: str) -> tuple[str, float]:
    """Return a tiny rule-based sentiment prediction and confidence score."""

    with tracer.start_as_current_span("prediction logic") as span:
        tokens = {token.strip(".,!?;:()[]{}\"'").lower() for token in text.split()}
        positive_hits = len(tokens & POSITIVE_WORDS)
        negative_hits = len(tokens & NEGATIVE_WORDS)
        score = positive_hits - negative_hits

        if score > 0:
            label = "positive"
        elif score < 0:
            label = "negative"
        else:
            label = "neutral"

        confidence = min(0.5 + abs(score) * 0.2, 0.99)
        if label == "neutral":
            confidence = 0.5

        span.set_attribute("prediction.label", label)
        span.set_attribute("prediction.confidence", confidence)
        span.set_attribute("prediction.positive_hits", positive_hits)
        span.set_attribute("prediction.negative_hits", negative_hits)

        return label, round(confidence, 2)

