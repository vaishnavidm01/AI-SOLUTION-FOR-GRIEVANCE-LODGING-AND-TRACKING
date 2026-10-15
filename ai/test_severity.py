
from severity_rules import predict_severity

test_cases = [
    {
        "description": "There is a live wire hanging over the road.",
        "category": "Street Light Failure",
        "has_photo": False
    },
    {
        "description": "There is a large pothole on the main road.",
        "category": "Pothole / Road Damage",
        "has_photo": True
    },
    {
        "description": "Garbage has not been collected from our street.",
        "category": "Solid Waste / Garbage",
        "has_photo": False
    }
]

for case in test_cases:
    severity = predict_severity(
        case["description"],
        case["category"],
        case["has_photo"]
    )

    print("Description:", case["description"])
    print("Predicted severity:", severity)
    print("-" * 40)
