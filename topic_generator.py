import random

def generate_topic():
    """Generate a unique, SEO-optimized outdoor topic for the next post."""
    base_topics = [
        "hunting gear",
        "country lifestyle",
        "camping essentials",
        "fishing strategies",
        "deer season preparation",
        "outdoor cooking recipes",
        "dog training for hunting",
        "off-grid living",
        "bushcraft skills",
        "rural DIY projects",
        "wildlife photography",
        "homesteading gear",
        "trail survival tips",
        "backcountry camping",
        "archery practice drills",
        "duck hunting tactics",
        "river fishing tips",
        "venison recipes",
        "firearm maintenance guide",
        "best tents for cold weather",
    ]

    modifiers = [
        "tips",
        "essentials",
        "guide",
        "for beginners",
        "on a budget",
        "mistakes to avoid",
        "every outdoorsman should know",
        "gear review",
        "safety checklist",
        "techniques for success",
    ]

    topic = f"{random.choice(base_topics)} {random.choice(modifiers)}"
    return topic.capitalize()
