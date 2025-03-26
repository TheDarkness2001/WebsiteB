from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import json
import os
import requests
import logging
from werkzeug.utils import secure_filename
from hashlib import sha256

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # More secure secret key

UPLOAD_FOLDER = "static/uploads"
USER_DATA_FILE = "users.json"

CUBIE_LOGIN_URL = "http://127.0.0.1:5001/login"
CUBIE_USER_INFO_URL = "http://127.0.0.1:5001/userinfo"
CUBIE_LOGOUT_URL = "http://127.0.0.1:5002"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload folder exists

SECRET_API_KEY = "super_secret_key_123"  # 🔥 Only Website B knows this key

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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

@app.route("/")
def index():
    return render_template("index.html", username=session.get("username"), profile_image=session.get("profile_image"), coins=session.get("coins"))

@app.route("/contact", methods=["GET", "POST"])
def contact():
    logger.debug("Contact route accessed.")
    error_message = None

    if request.method == "POST":
        username = request.form.get("username")
        password = sha256(request.form.get("password").encode()).hexdigest()
        users = load_users()

        if username in users and users[username]["password"] == password:
            session["username"] = username
            session["profile_image"] = users[username].get("profile_image", "/static/uploads/default.png")
            session["coins"] = users[username].get("coins", 0)
            return redirect(url_for("index"))
        else:
            error_message = "Invalid username or password!"

    return render_template("contact.html", error=error_message)

@app.route("/signup", methods=["POST"])
def signup():
    new_username = request.form.get("new_username")
    new_password = sha256(request.form.get("new_password").encode()).hexdigest()
    profile_image = request.files.get("profile_image")

    users = load_users()

    if new_username in users:
        return "Username already exists!", 400

    profile_image_filename = "/static/uploads/default.png"
    if profile_image and allowed_file(profile_image.filename):
        filename = secure_filename(profile_image.filename)
        profile_image_path = os.path.join(UPLOAD_FOLDER, filename)
        profile_image.save(profile_image_path)
        profile_image_filename = f"/static/uploads/{filename}"

    users[new_username] = {"password": new_password, "profile_image": profile_image_filename, "coins": 0}
    save_users(users)

    session["username"] = new_username
    session["profile_image"] = profile_image_filename
    session["coins"] = 0

    return redirect(url_for("index"))

@app.route("/login_with_cubie")
def login_with_cubie():
    return redirect(f"{CUBIE_LOGIN_URL}?redirect_uri=http://127.0.0.1:5002/auth-callback")


@app.route('/auth-callback')
def auth_callback():
    username = request.args.get('username')
    profile_image = request.args.get('profile_image')  # ✅ Get profile image

    if not username:
        return "Error: Missing user data!", 400

    # 🔥 Send request to Website A securely
    headers = {
        "Authorization": SECRET_API_KEY,  # ✅ Send secret API key
        "Referer": "http://127.0.0.1:5002"  # ✅ Verify Website B as source
    }
    response = requests.post(CUBIE_USER_INFO_URL, json={"username": username}, headers=headers)

    if response.status_code == 200:
        user_data = response.json()

        session["username"] = user_data["username"]
        session["profile_image"] = profile_image or user_data["profile_image"]
        session["coins"] = user_data.get("coins", 0)  # Default coins to 0 if missing

        return redirect(url_for("index"))

    return f"Error: Unauthorized access! Status: {response.status_code}, Message: {response.text}", 403


@app.route("/logout")
def logout():
    session.clear()
    return redirect(CUBIE_LOGOUT_URL)

if __name__ == "__main__":
    app.run(debug=True, port=5002)
