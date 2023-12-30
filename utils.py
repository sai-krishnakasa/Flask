from functools import wraps
from flask import session, jsonify


def check_required_fields_exist(required_fields, data):
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")


def user_to_dict(user):
    # Convert a single user to a dictionary
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
        # Add more attributes as needed
    }


def post_to_dict(post):
    # Convert a single user to a dictionary
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content
        # Add more attributes as needed
    }


def user_logged_in(func):
    @wraps(func)
    def inner(*args, **kwargs):
        print(session.get("email"))
        if not session.get("email"):
            return jsonify({"error": "User Not Authenticated"}), 401  # Unauthorized
        return func(*args, **kwargs)

    return inner
