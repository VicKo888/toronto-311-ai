
import re

SERVICE_RULES = {
    "Pothole": [
        "pothole", "road damage", "hole in road",
        "broken pavement"
    ],
    "Tree Maintenance": [
        "tree", "branch", "pruning", "fallen limb"
    ],
    "Waste Collection": [
        "garbage", "trash", "recycling", "green bin",
        "missed collection", "waste"
    ],
    "Noise Complaint": [
        "noise", "loud", "construction noise",
        "party", "disturbance"
    ],
    "Graffiti": [
        "graffiti", "vandalism", "spray paint"
    ],
    "Streetlight": [
        "streetlight", "street light", "lamp post",
        "street lighting"
    ],
    "Sidewalk": [
        "sidewalk", "broken sidewalk",
        "uneven pavement"
    ],
}

EMERGENCY_TERMS = [
    "fire", "heart attack", "not breathing",
    "unconscious", "gunshot", "active shooter",
    "gas leak", "severe bleeding"
]


def classify_message(message, df=None):
    """Classify a resident's issue using keyword rules."""
    text = message.lower().strip()

    if any(term in text for term in EMERGENCY_TERMS):
        return {
            "service_type": None,
            "division": None,
            "method": "emergency safety rule",
            "emergency": True,
        }

    for category, keywords in SERVICE_RULES.items():
        if any(
            re.search(r"\b" + re.escape(word) + r"\b", text)
            for word in keywords
        ):
            result = {
                "service_type": category,
                "division": "Not verified",
                "method": "keyword baseline",
                "emergency": False,
            }

            if df is not None and not df.empty:
                if "service_type" in df.columns:
                    matches = df[
                        df["service_type"].astype(str).str.contains(
                            category.split()[0],
                            case=False,
                            regex=False,
                            na=False,
                        )
                    ]
                    if not matches.empty:
                        result["service_type"] = (
                            matches["service_type"].mode().iloc[0]
                        )
                        if "division" in matches.columns:
                            divisions = matches["division"].dropna()
                            if not divisions.empty:
                                result["division"] = (
                                    divisions.mode().iloc[0]
                                )

            return result

    return {
        "service_type": None,
        "division": None,
        "method": "keyword baseline",
        "emergency": False,
    }


def build_reply(message, classification, df=None):
    """Build a safe response for the 311 prototype."""
    if classification.get("emergency"):
        return (
            "This may be an emergency. If anyone is in "
            "immediate danger, call **911**. This prototype "
            "cannot contact emergency services."
        )

    category = classification.get("service_type")

    if not category:
        return (
            "I can help identify a Toronto 311 service category. "
            "Could you describe the issue in more detail? "
            "For example, is it related to roads, trees, "
            "waste collection, noise, or another City service?"
        )

    division = classification.get("division", "Not verified")

    return (
        f"Based on your description, the likely issue category "
        f"is **{category}**.\n\n"
        f"**Division in historical data:** {division}\n\n"
        "To help narrow down the issue, could you tell me "
        "the nearest intersection or general area, and "
        "when you first noticed the problem?\n\n"
        "You can contact the City through "
        "[Toronto 311](https://www.toronto.ca/home/311-toronto-at-your-service/). "
        "This student prototype does not submit requests "
        "or verify official service eligibility."
    )
