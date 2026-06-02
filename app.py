from flask import Flask, render_template, jsonify
import json
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

CARD_DATABASE = {
    "Stunky": {
        "name": "Stunky",
        "type": "Dark / Poison",
        "rarity": "Common / depends on set",
        "value": "$0.20 - $2 estimate",
        "power": "Usually uses poison or dark-style attacks.",
        "description": "Stunky is a skunk-like Pokémon known for poison gas attacks."
    },
    "Pumkaboo": {
        "name": "Pumpkaboo",
        "type": "Ghost / Grass",
        "rarity": "Common / depends on set",
        "value": "$0.20 - $3 estimate",
        "power": "Often uses ghost or grass-style moves.",
        "description": "Pumpkaboo is a pumpkin-like Ghost-type Pokémon."
    },
    "Zubat": {
        "name": "Zubat",
        "type": "Poison / Flying",
        "rarity": "Common",
        "value": "$0.20 - $2 estimate",
        "power": "Often uses bite, confusion, or poison-style attacks.",
        "description": "Zubat is a bat Pokémon that attacks using sound and poison."
    },
    "Garbodor": {
        "name": "Garbodor",
        "type": "Poison",
        "rarity": "Rare / depends on set",
        "value": "$0.50 - $5 estimate",
        "power": "Uses poison and trash-based attacks.",
        "description": "Garbodor is a Poison-type Pokémon made from compressed garbage."
    },
    "Vulpix": {
        "name": "Vulpix",
        "type": "Fire",
        "rarity": "Common / depends on set",
        "value": "$0.50 - $5 estimate",
        "power": "Often uses fire moves such as Ember.",
        "description": "Vulpix is a fox-like Fire-type Pokémon with curled tails."
    },
    "Litleo": {
        "name": "Litleo",
        "type": "Fire / Normal",
        "rarity": "Common",
        "value": "$0.20 - $2 estimate",
        "power": "Uses fire and basic physical attacks.",
        "description": "Litleo is a young lion Pokémon with Fire-type abilities."
    },
    "Mareep": {
        "name": "Mareep",
        "type": "Electric",
        "rarity": "Common",
        "value": "$0.20 - $3 estimate",
        "power": "Uses electric attacks and static electricity.",
        "description": "Mareep is an Electric-type sheep Pokémon."
    },
    "Meowstic": {
        "name": "Meowstic",
        "type": "Psychic",
        "rarity": "Uncommon / Rare depending on set",
        "value": "$0.50 - $5 estimate",
        "power": "Uses psychic moves and mental energy.",
        "description": "Meowstic is a Psychic-type Pokémon known for powerful hidden abilities."
    },
    "Froakie": {
        "name": "Froakie",
        "type": "Water",
        "rarity": "Common",
        "value": "$0.50 - $4 estimate",
        "power": "Uses water attacks and quick movement.",
        "description": "Froakie is a Water-type starter Pokémon."
    },
    "Phantump": {
        "name": "Phantump",
        "type": "Ghost / Grass",
        "rarity": "Common",
        "value": "$0.20 - $3 estimate",
        "power": "Uses ghost and forest-based attacks.",
        "description": "Phantump is a haunted tree-stump Pokémon."
    },
    "Ninetails": {
        "name": "Ninetales",
        "type": "Fire",
        "rarity": "Rare / depends on set",
        "value": "$1 - $10 estimate",
        "power": "Uses strong fire and mystical attacks.",
        "description": "Ninetales is the evolved form of Vulpix and is known for its nine tails."
    },
    "Philippe": {
        "name": "Philippe",
        "type": "Unknown",
        "rarity": "Unknown",
        "value": "Check online",
        "power": "Information not added yet.",
        "description": "This may be a typo or custom card label."
    },
    "Bergmite": {
        "name": "Bergmite",
        "type": "Ice",
        "rarity": "Common",
        "value": "$0.20 - $2 estimate",
        "power": "Uses ice attacks and defensive moves.",
        "description": "Bergmite is an Ice-type Pokémon with a hard icy body."
    },
    "Delibird": {
        "name": "Delibird",
        "type": "Ice / Flying",
        "rarity": "Common / Uncommon",
        "value": "$0.20 - $3 estimate",
        "power": "Uses present-based and ice-style moves.",
        "description": "Delibird is a bird Pokémon known for carrying gifts."
    },
    "Donphan": {
        "name": "Donphan",
        "type": "Ground",
        "rarity": "Rare / depends on set",
        "value": "$0.50 - $6 estimate",
        "power": "Uses rolling and ground-based attacks.",
        "description": "Donphan is a strong Ground-type Pokémon with armour-like skin."
    },
    "Avalugg": {
        "name": "Avalugg",
        "type": "Ice",
        "rarity": "Rare / depends on set",
        "value": "$0.50 - $5 estimate",
        "power": "Uses heavy ice defence and freezing attacks.",
        "description": "Avalugg is an Ice-type Pokémon with a huge glacier-like body."
    },
    "Baltoy": {
        "name": "Baltoy",
        "type": "Ground / Psychic",
        "rarity": "Common",
        "value": "$0.20 - $2 estimate",
        "power": "Uses spinning and psychic-style attacks.",
        "description": "Baltoy is a clay doll Pokémon that spins on one foot."
    },
    "Quilladin": {
        "name": "Quilladin",
        "type": "Grass",
        "rarity": "Uncommon",
        "value": "$0.30 - $4 estimate",
        "power": "Uses grass attacks and defensive shell moves.",
        "description": "Quilladin is the evolved form of Chespin."
    },
    "Ho-Oh": {
        "name": "Ho-Oh",
        "type": "Fire / Flying",
        "rarity": "Rare / Legendary",
        "value": "$2 - $30+ estimate",
        "power": "Uses powerful fire and legendary flying attacks.",
        "description": "Ho-Oh is a Legendary Pokémon known for its rainbow wings."
    }
}

app.secret_key = "pokemon_scanner_secret_key"

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db():
    return sqlite3.connect("pokemon_scanner.db")


def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_image TEXT DEFAULT ''
        )
    """)

    try:
        db.execute("ALTER TABLE users ADD COLUMN profile_image TEXT DEFAULT '/static/uploads/default_profile.jpg'")
    except sqlite3.OperationalError:
        pass

    db.commit()
    db.close()


def load_card_labels():
    with open("static/model/metadata.json", "r") as file:
        data = json.load(file)
        return data["labels"]


def make_card_details(card_id):
    clean_name = card_id.replace("_", " ")

    card = CARD_DATABASE.get(card_id)

    if card is None:
        card = {
            "name": clean_name,
            "type": "Unknown",
            "rarity": "Unknown",
            "value": "Check online",
            "power": "Power information not added yet.",
            "description": f"{clean_name} was recognised by the scanner."
        }

    card["search_url"] = f"https://www.google.com/search?q={clean_name}+pokemon+card+value"
    return card


@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            db.commit()
            db.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return render_template("register.html", error="Username already exists.")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect(url_for("index"))

        return render_template("login.html", error="Incorrect username or password.")

    return render_template("login.html")


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user = db.execute(
        "SELECT username, profile_image FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    db.close()

    return render_template(
        "profile.html",
        username=user[0],
        profile_image=user[1]
    )

@app.route("/profile")
def old_profile():
    return redirect(url_for("library"))


@app.route("/library")
def library():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "library.html",
        username=session["username"]
    )


@app.route("/account")
def account():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user = db.execute(
        "SELECT username, profile_image FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()
    db.close()

    return render_template(
        "account.html",
        username=user[0],
        profile_image=user[1]
    )

@app.route("/trades")
def trades():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "trades.html",
        username=session["username"]
    )

@app.route("/card/<card_name>")
def card_detail(card_name):

    if "user_id" not in session:
        return redirect(url_for("login"))

    card = make_card_details(card_name)

    return render_template(
        "card_detail.html",
        card=card,
        card_name=card_name
    )

@app.route("/upload-profile", methods=["POST"])
def upload_profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    image = request.files.get("profile_image")

    if image and image.filename != "":
        filename = secure_filename(image.filename)
        filename = f"user_{session['user_id']}_{filename}"

        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(path)

        image_url = "/" + path.replace("\\", "/")

        db = get_db()
        db.execute(
            "UPDATE users SET profile_image = ? WHERE id = ?",
            (image_url, session["user_id"])
        )
        db.commit()
        db.close()

    return redirect(url_for("account"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/card/<card_id>")
def get_card(card_id):
    labels = load_card_labels()

    if card_id not in labels:
        return jsonify({
            "success": False,
            "message": "Card not found"
        })

    card = make_card_details(card_id)

    return jsonify({
        "success": True,
        "card": card
    })

@app.route("/users")
def users():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    users = db.execute(
        "SELECT username, profile_image FROM users ORDER BY username"
    ).fetchall()
    db.close()

    return render_template(
        "users.html",
        users=users,
        username=session["username"]
    )


@app.route("/user/<profile_username>")
def user_profile(profile_username):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()
    user = db.execute(
        "SELECT username, profile_image FROM users WHERE username = ?",
        (profile_username,)
    ).fetchone()
    db.close()

    if user is None:
        return redirect(url_for("users"))

    return render_template(
        "user_profile.html",
        profile_username=user[0],
        profile_image=user[1],
        username=session["username"]
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="127.0.0.1", port=5051)