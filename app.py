from flask import Flask, jsonify, render_template, session, redirect, request
from flask_session import Session
from sqlalchemy.exc import IntegrityError
import requests
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quotes.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

app.config["TEMPLATES_AUTO_RELOAD"] = True

class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<Users {self.username}>"

class Favorites(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quote = db.Column(db.String(1000), unique=True, nullable=False)
    author = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return f"<Favorites {self.id}: {self.quote} by {self.author}>"

with app.app_context():
    db.create_all()

API_KEY = "L0G2M5pDJCbsZ6mD26CLtg==xOiqMbRG6ZUuGwOL"
HEADERS = {
    "X-Api-Key": API_KEY
}

@app.route("/")
@login_required
def index():
    response = requests.get("https://api.api-ninjas.com/v1/quotes", headers=HEADERS)
    if response.status_code == 200:
        quote_data = response.json()  # Parse the JSON response
        quote = quote_data[0]["quote"]
        author = quote_data[0]["author"]
    else:
        return render_template("error.html")
    return render_template("index.html", quote=quote, author=author)

@app.route("/quote")
@login_required
def quote():
    response = requests.get("https://api.api-ninjas.com/v1/quotes", headers=HEADERS)
    if response.status_code == 200:
        quote_data = response.json()  # Parse the JSON response
        quote = quote_data[0]["quote"]
        author = quote_data[0]["author"]
        return jsonify({"quote": quote, "author": author})
    else:
        return jsonify({"error": "Error fetching quote"}), 500


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = db.session.execute(text("SELECT id, hash FROM users WHERE username = :username;"), 
            {"username": username}).fetchone()
        if user is None:
            return render_template("login.html", error="Invalid username and/or password")
        
        id = user[0]
        hash = user[1]

        if not check_password_hash(hash, password):
            return render_template("login.html", error="Invalid username and/or password")

        session["user_id"] = id

        return redirect("/")

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if not username or not password:
            return render_template("register.html", error="Missing username/password")

        elif not password == confirmation:
            return render_template("register.html", error="Passwords do not match")

        hash = generate_password_hash(password, method="pbkdf2:sha256:600000")

        try:
            db.session.execute(text("INSERT INTO users (username, hash) VALUES (:username, :hash);"),
                {"username": username, "hash": hash})
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template("register.html", error="Username taken")

        user_id = db.session.execute(text("SELECT id FROM users WHERE username = :username;"), 
            {"username": username}).fetchone().id

        session["user_id"] = user_id

        return redirect("/")

    return render_template("register.html")


@app.route("/toggle_favorite", methods=["POST"])
@login_required
def toggle_favorite():
    data = request.get_json()
    quote = data.get("quote")
    author = data.get("author")
    action = data.get("action")

    print(f"Quote sent from frontend: {quote}")

    stored_favorite = Favorites.query.filter_by(
        user_id=session["user_id"],
        quote=quote
    ).first()
    
    print(f"Stored favorite in database: {stored_favorite.quote if stored_favorite else 'None'}")


    if action == "add":
        try:    
            new_favorite = Favorites(
                user_id=session["user_id"],
                quote=quote,
                author=author
            )
            db.session.add(new_favorite)
            db.session.commit()
            return jsonify({"success": True}), 200
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "Quote already in favorites"}), 400
    else:
        try:
            if stored_favorite:
                print("Deleting favorite...")
                db.session.delete(stored_favorite)
                db.session.commit()
                print("Favorite deleted successfully.")
            else:
                print("Favorite not found.")
            return jsonify({"success": True}), 200
        except Exception as e:
            db.session.rollback()
            print(f"Error occurred: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route("/favorites")
@login_required
def favorites():
    user_favorites = Favorites.query.filter_by(user_id=session["user_id"]).all()
    return render_template("favorites.html", favorites=user_favorites)


if __name__ == "__main__":
    app.run(debug=True)

