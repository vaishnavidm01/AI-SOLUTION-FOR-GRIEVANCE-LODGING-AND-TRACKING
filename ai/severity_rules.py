
def predict_severity(description, category, has_photo=False):
    """
    Estimate complaint severity using transparent risk rules.
    This is a rule-based estimate, not a trained ML prediction.
    """

    text = (description or "").lower().replace("-", " ")
    category_text = (category or "").lower()

    # Immediate-danger indicators
    critical_keywords = [
        "life threatening",
        "person injured",
        "people injured",
        "building collapse",
        "electric shock",
        "live wire",
        "open manhole",
        "major fire",
        "flooding inside homes",
        "gas leak",
        "fallen electric pole"
    ]

    high_keywords = [
        "dangerous",
        "severe",
        "large pothole",
        "pipe burst",
        "large pothole",
        "pothole",
        "road damage",
        "overflow",
        "road blocked",
        "water entering house",
        "fallen tree",
        "no water supply",
        "exposed wire",
        "sewage overflowing",
        "street completely flooded"
    ]

    if any(keyword in text for keyword in critical_keywords):
        return "Critical"

    score = 0

    # Description-based risk indicators
    if any(keyword in text for keyword in high_keywords):
        score += 2

        # Explicit high-risk descriptions should be High
        return "High"

    # Category-based risk indicators
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

    # Photo evidence does not independently increase severity.
    # It can help authorities assess the complaint.

    if score >= 3:
        return "High"
    elif score >= 1:
        return "Medium"
    else:
        return "Low"
