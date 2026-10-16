
from severity_rules import predict_severity

test_cases = [
    (
        "There is a live wire hanging over the road.",
        "Mobility - Roads, Footpaths and Infrastructure",
        False,
        "Critical"
    ),
    (
        "A person was injured due to an electric shock.",
        "Electrical",
        False,
        "Critical"
    ),
    (
        "There is a large pothole on the main road.",
        "Mobility - Roads, Footpaths and Infrastructure",
        False,
        "High"
    ),
    (
        "Sewage overflowing near the street.",
        "Drainage Overflow",
        False,
        "High"
    ),
    (
        "Garbage has not been collected from our street.",
        "Sanitation",
        False,
        "Low"
    ),
    (
        "A streetlight is not working.",
        "Street Lighting",
        True,
        "Low"
    ),
]

for description, category, has_photo, expected in test_cases:
    predicted = predict_severity(description, category, has_photo)

    result = "PASS" if predicted == expected else "FAIL"

    print(f"Description: {description}")
    print(f"Expected: {expected} | Predicted: {predicted} | {result}")
    print("-" * 60)
