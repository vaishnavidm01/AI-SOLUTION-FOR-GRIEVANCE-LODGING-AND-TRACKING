
def predict_severity(description, category, has_photo=False):
    """
    Estimate complaint severity using transparent risk rules.
    This is a rule-based estimate, not a trained ML prediction.
    """

    text = (description or "").lower()
    category_text = (category or "").lower()

    score = 0

    # Explicit emergency or immediate-danger indicators
    critical_keywords = [
        "life threatening",
        "life-threatening",
        "person injured",
        "people injured",
        "building collapse",
        "electric shock",
        "live wire",
        "open manhole",
        "major fire",
        "flooding inside homes"
    ]

    high_keywords = [
        "dangerous",
        "severe",
        "large pothole",
        "pipe burst",
        "overflow",
        "road blocked",
        "water entering house",
        "fallen tree",
        "no water supply",
        "exposed wire"
    ]

    if any(keyword in text for keyword in critical_keywords):
        return "Critical"

    if any(keyword in text for keyword in high_keywords):
        score += 2

    # Category-level risk indicators
    high_risk_categories = [
        "drainage overflow",
        "flooding",
        "water leakage",
        "pipe burst",
        "pothole",
        "road damage",
        "tree fallen",
        "dangerous tree"
    ]

    if any(item in category_text for item in high_risk_categories):
        score += 1

    if has_photo:
        score += 1

    if score >= 3:
        return "High"
    elif score >= 1:
        return "Medium"
    else:
        return "Low"
