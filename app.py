import os
from flask import Flask, render_template, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.event import listens_for
from flask_migrate import Migrate
from utils import (
    check_required_fields_exist,
    user_to_dict,
    user_logged_in,
    post_to_dict,
)

load_dotenv()

app = Flask(__name__)

# Replace these values with your PostgreSQL credentials
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f'postgresql://{os.getenv("DB_USERNAME")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "abcdekbdajbdjsbjbdsbh"
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Define a simple User model
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200))

    def __repr__(self):
        return f"<User {self.username}>"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


def is_email_exists(email):
    return User.query.filter_by(email=email).first()


# Use the `before_insert` event to hash the password before inserting into the database
@listens_for(User, "before_insert")
def hash_password_before_insert(mapper, connection, target):
    print(mapper, connection)
    target.password = generate_password_hash(target.password)


# Use the `before_update` event to hash the password before updating the database
@listens_for(User, "before_update")
def hash_password_before_update(mapper, connection, target):
    target.password = generate_password_hash(target.password)


# Route to display user data
@app.route("/users")
@user_logged_in
def users():
    try:
        users = User.query.all()
    except Exception as e:
        print(f"Error: {str(e)}")
    users = [user_to_dict(user) for user in users]
    return jsonify({"users": users}), 200


# Route to display user data
@app.route("/users/<int:user_id>")
@user_logged_in
def user_detail(user_id):
    user = User.query.get(user_id)
    return user_to_dict(user)


# @app.route("/", methods=["GET"])
# def home():
#     return render_template("index.html")


@app.route("/auth/login", methods=["GET", "POST"])
def login():
    # if request.method == "GET":
    #     return render_template("login.html")
    # else:
    try:
        required_fields = ["email", "password"]
        body = request.get_json()
        check_required_fields_exist(required_fields, body)
        user = User.query.filter_by(email=body.get("email")).first()
        if check_password_hash(user.password, body.get("password")):
            session["user_id"] = user.id
            session["email"] = user.email
            return {"success": "User logged in  Successfully"}
        return {"error": "Invalid Username / Password "}
    except Exception as e:
        return {"error": str(e)}


@app.route("/auth/register", methods=["POST"])
def register():
    try:
        required_fields = ["username", "email", "password"]
        data = request.get_json()
        check_required_fields_exist(required_fields, data)
        if not is_email_exists(data.get("email")):
            new_user = User(**data)
            db.session.add(new_user)
            db.session.commit()
            return {"success": "User Created Successfully"}
        return {"error": "User with this email already exist"}
    except Exception as e:
        return {"error": str(e)}


@app.route("/post/create", methods=["GET", "POST"])
@user_logged_in
def create_post():
    if request.method == "GET":
        return {"info": "return the form to create the post"}
    else:
        try:
            data = request.get_json()
            data["user_id"] = session.get("user_id", None)
            new_post = Post(**data)
            db.session.add(new_post)
            db.session.commit()
            return {"success": "Post Created Successfully"}
        except Exception as e:
            return {"error": str(e)}


@app.route("/myposts", methods=["GET"])
@user_logged_in
def myposts():
    posts = Post.query.filter_by(user_id=session.get("user_id", None))
    posts = [post_to_dict(post) for post in posts]
    return jsonify({"data": posts}), 200


@app.route("/post/<int:post_id>", methods=["GET"])
@user_logged_in
def post_detail(post_id):
    post = Post.query.filter_by(id=post_id, user_id=session.get("user_id", None))
    post = post_to_dict(post) if post else "You don't have any posts"
    return jsonify({"data": post}), 200


if __name__ == "__main__":
    # Create tables if they do not exist
    try:
        # Try to create all tables
        with app.app_context():
            db.create_all()
        print("Connection to the database established successfully.")
    except Exception as e:
        print(f"Error: {str(e)}")
    app.run(debug=True)
