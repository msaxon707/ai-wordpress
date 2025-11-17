import random

def generate_topic():
    """
    Randomly selects a blog topic alternating between outdoors and decor content.
    Ensures a 50/50 balance across posts.
    """

    outdoors_topics = [
        "Deer hunting strategies for beginners",
        "Essential camping gear checklist for 2025",
        "Top fishing techniques to catch more bass",
        "Duck hunting tactics on a budget",
        "How to prep for deer season like a pro",
        "Backyard fire pit safety and setup tips",
        "Choosing the best boots for long hunting trips",
        "Hiking essentials for rugged terrain",
        "How to cook outdoors: cast iron recipes",
        "Survival gear every outdoorsman should carry"
    ]

    decor_topics = [
        "Farmhouse kitchen decor ideas for a cozy home",
        "Rustic living room design trends for 2025",
        "How to create a country-style bedroom retreat",
        "DIY reclaimed wood wall art project",
        "Cozy cabin decorating ideas for fall",
        "Rustic entryway inspiration for small spaces",
        "Affordable country decor finds on Amazon",
        "Tips for mixing modern and farmhouse style",
        "How to decorate a porch for year-round charm",
        "Best rustic lighting ideas for your home"
    ]

    # 50/50 category choice
    category_type = random.choice(["outdoors", "decor"])
    topic = random.choice(outdoors_topics if category_type == "outdoors" else decor_topics)

    print(f"[topic_generator] Selected '{category_type}' topic: {topic}")
    return topic
