"""
Daily Buddy - a simple chatbot for everyday questions.
It needs NO API key and NO paid service. It works by looking for
keywords in what you type and picking a ready-made answer.
"""
import os
import random
import re
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# India time (UTC + 5:30)
IST = timezone(timedelta(hours=5, minutes=30))

JOKES = [
    "Mela Paaru Vaanam Keela paaru thara",
    "Onekellam Ethukuda Joke Neeye periya...",
    "Professional platform da macha illana etha solliduven",
    "நாங்க அடி வாங்காத ஏரியா-வெ கெடையாது.",
    "Why can't you trust stairs? They are always up to something.",
]

FACTS = [
    "நாம எது பண்ணாலும் இந்த உலகம் நம்ம ஓடனே ஊது பாக்கணும். நாதாரி தனம் பண்ணாலும் நாசூக்க பணனும்.",
    "நீ பேசாம இருந்தாலே பாதி பிரச்சினை தீர்ந்துரும்!",
    "Bananas are slightly radioactive, but totally safe to eat.",
    "A day on Venus is longer than a year on Venus.",
    "Your heart beats about 100,000 times every day.",
]

TIPS = [
    "Drink a glass of water now. Most of us don't drink enough.",
    "Take 5 deep breaths. In through the nose, out through the mouth.",
    "Look away from your screen for 20 seconds. Your eyes will thank you.",
    "Stand up and stretch for one minute.",
    "Write down one thing you are happy about today.",
]

FALLBACKS = [
    "Hmm, I did not understand that. Try asking about time, date, a joke, a recipe, or a simple sum like 12 + 8.",
    "I'm still learning! You can type 'help' to see what I can do.",
    "Sorry, I don't know that one yet. Type 'help' and I will show you what I know.",
]

HELP_TEXT = (
    "I can help with:\n"
    "- Time and date (say 'what time is it')\n"
    "- Jokes (say 'tell me a joke')\n"
    "- Fun facts (say 'fun fact')\n"
    "- Recipes: tea, coffee, rice, boiled egg, omelette\n"
    "- Simple maths (say '25 * 4')\n"
    "- Health tips (say 'give me a tip')"
)

RECIPES = {
    "tea": "Tea: Boil 1 cup of water. Add 1 tsp tea powder and let it boil 1 minute. "
           "Add half a cup of milk and sugar. Boil 2 more minutes, then strain.",
    "coffee": "Coffee: Heat 1 cup of milk. Mix 1 tsp coffee powder and 1 tsp sugar in a cup. "
              "Pour the hot milk over it and stir well.",
    "rice": "Rice: Wash 1 cup of rice 2-3 times. Add 2 cups of water. "
            "Cook on medium heat until the water is absorbed (about 15-20 minutes), then rest 5 minutes.",
    "egg": "Boiled egg: Put the egg in boiling water. 6 minutes = soft, 10 minutes = hard. "
           "Then put it in cold water and peel.",
    "omelette": "Omelette: Beat 2 eggs with a pinch of salt, chopped onion and chilli. "
                "Pour on a hot oiled pan. Cook 2 minutes each side.",
}


def has_any(text, words):
    """True if any word/phrase appears in the text."""
    return any(re.search(r"\b" + re.escape(w) + r"\b", text) for w in words)


def try_math(text):
    """Handles things like '12 + 8', '25*4', '10 divided by 2'."""
    t = text.replace("x", "*").replace("plus", "+").replace("minus", "-")
    t = t.replace("times", "*").replace("multiplied by", "*").replace("divided by", "/")
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", t)
    if not m:
        return None
    a, op, b = float(m.group(1)), m.group(2), float(m.group(3))
    if op == "+":
        r = a + b
    elif op == "-":
        r = a - b
    elif op == "*":
        r = a * b
    else:
        if b == 0:
            return "I can't divide by zero. Nobody can!"
        r = a / b
    r = int(r) if r == int(r) else round(r, 4)
    return f"The answer is {r}."


def get_reply(message):
    text = message.lower().strip()
    if not text:
        return "Please type something and I will reply."

    # 1. Maths first (it has numbers and symbols)
    math_answer = try_math(text)
    if math_answer:
        return math_answer

    # 2. Greetings
    if has_any(text, ["hi", "hello", "hey", "vanakkam", "namaste"]):
        return "Vanakkam! I'm Daily Buddy. Type 'help' to see what I can do."
    if "good morning" in text:
        return "Good morning! Have a great day."
    if "good night" in text:
        return "Good night! Sleep well."
    if has_any(text, ["how are you"]):
        return "I'm doing great, thanks for asking! How can I help you?"
    if has_any(text, ["your name", "who are you"]):
        return "I'm Daily Buddy, a small chatbot that answers simple everyday questions."

    # 3. Time and date
    now = datetime.now(IST)
    if has_any(text, ["time"]):
        return "The time now is " + now.strftime("%I:%M %p") + " (India time)."
    if has_any(text, ["date", "today", "day"]):
        return "Today is " + now.strftime("%A, %d %B %Y") + "."

    # 4. Fun stuff
    if has_any(text, ["joke", "funny", "laugh"]):
        return random.choice(JOKES)
    if has_any(text, ["fact", "interesting"]):
        return random.choice(FACTS)
    if has_any(text, ["tip", "advice", "health"]):
        return random.choice(TIPS)

    # 5. Recipes
    for key, recipe in RECIPES.items():
        if has_any(text, [key]) or (key == "egg" and has_any(text, ["eggs"])):
            return recipe
    if has_any(text, ["recipe", "cook", "cooking"]):
        return "I know recipes for: tea, coffee, rice, boiled egg, omelette. Which one do you want?"

    # 6. Help and goodbye
    if has_any(text, ["help", "what can you do", "menu"]):
        return HELP_TEXT
    if has_any(text, ["thanks", "thank you", "thx"]):
        return "You're welcome!"
    if has_any(text, ["bye", "goodbye", "see you"]):
        return "Bye! Come back soon."

    return random.choice(FALLBACKS)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", ""))[:300]  # limit length
    return jsonify({"reply": get_reply(message)})


@app.route("/health")
def health():
    return "ok"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
