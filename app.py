from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import requests
from werkzeug.utils import secure_filename
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "static/uploads"
USER_DATA_FILE = "users.json"

CUBIE_LOGIN_URL = "http://127.0.0.1:5001/login"
CUBIE_USER_INFO_URL = "http://127.0.0.1:5001/userinfo"
CUBIE_LOGOUT_URL = "http://127.0.0.1:5002/"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload folder exists


# Load user data from JSON file
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Save user data to JSON file
def save_users(users):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(users, file, indent=4)

@app.route('/')
def index():
    return render_template("index.html", username=session.get('username'), profile_image=session.get('profile_image'))

@app.route('/contact', methods=["GET", "POST"])
def contact():
    logger.debug("Contact route accessed.")
    error_message = None  # To store error messages for incorrect login

    if request.method == "POST":
        action = request.form.get("action")
        username = request.form.get("username")
        password = request.form.get("password")

        users = load_users()  # Load user data from users.json
        print("Loaded Users:", users)  # 🔍 Debugging print

        if action == "login":
            if username in users:
                print(f"User found: {username}, Stored Password: {users[username]['password']}")  # 🔍 Debugging print

            # Check if the username exists and the password matches
            if username in users and users[username]["password"] == password:
                profile_image = users[username].get("profile_image", "/static/uploads/default.png")

                session["username"] = username
                session["profile_image"] = profile_image

                return redirect(url_for("index"))
            else:
                error_message = "Invalid username or password!"

    return render_template("contact.html", error=error_message)

@app.route('/signup', methods=["POST"])
def signup():
    new_username = request.form.get("new_username")
    new_password = request.form.get("new_password")
    profile_image = request.files.get("profile_image")  # Handle profile image

    users = load_users()

    if new_username in users:
        return "Username already exists!", 400

    # Save profile image
    profile_image_filename = "/static/uploads/default.png"  # Default image
    if profile_image:
        filename = secure_filename(profile_image.filename)
        profile_image_path = os.path.join("static/uploads", filename)
        profile_image.save(profile_image_path)
        profile_image_filename = f"/static/uploads/{filename}"  # Store relative path

    users[new_username] = {"password": new_password, "profile_image": profile_image_filename}
    save_users(users)  # Save data to users.json

    session["username"] = new_username
    session["profile_image"] = profile_image_filename

    return redirect(url_for("index"))



@app.route('/login_with_cubie')
def login_with_cubie():
    return redirect(f"{CUBIE_LOGIN_URL}?redirect_uri=http://127.0.0.1:5002/auth-callback")

@app.route('/auth-callback')
def auth_callback():
    username = request.args.get('username')
    profile_image = request.args.get('profile_image')

    if not username or not profile_image:
        return "Error: Missing user data!", 400

    session['username'] = username
    session['profile_image'] = profile_image

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(CUBIE_LOGOUT_URL)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
