
def assign_department(category):
    """
    Assign a responsible department based on the predicted complaint category.
    This is a rule-based routing prototype.
    """

    category_text = (category or "").lower()

    department_rules = {
        "mobility - roads, footpaths and infrastructure":
            "Roads and Infrastructure Department",

        "solid waste":
            "Solid Waste Management Department",

        "garbage":
            "Solid Waste Management Department",

        "drainage":
            "Drainage Department",

        "sewage":
            "Drainage Department",

        "water supply":
            "Water Supply Department",

        "water leakage":
            "Water Supply Department",

        "street lighting":
            "Electrical Department",

        "electricity":
            "Electrical Department",

        "parks":
            "Parks and Horticulture Department",

        "public health":
            "Public Health Department"
    }

    for keyword, department in department_rules.items():
        if keyword in category_text:
            return department

    return "General Civic Grievance Department"
