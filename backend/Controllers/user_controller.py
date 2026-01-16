from flask import request, jsonify
from werkzeug.security import check_password_hash
from Models.admin_model import Admin

def register_user():
    try:
        data = request.get_json()
        email_id = data.get("email_id")
        password = data.get("password")
        confirm_password = data.get("confirm_password")
        user_type = data.get("user_type", "admin")

        if not email_id:
            return jsonify(status=False, message="Email is required"), 400
        
        if password != confirm_password:
            return jsonify(status=False, message="Password and confirm password do not match"), 400

        existing_user = Admin.find_by_email(email_id=email_id)
        if existing_user:
            return jsonify(status=False, message="Email already exists"), 400

        # Corrected constructor
        user = Admin(email_id=email_id, role=user_type, password=password)
        user_id = user.save()

        return jsonify(status=True, message="User registered successfully", user_id=user_id), 201

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 400


# user login
def login_user():
    try:
        data = request.get_json()
        email_id = data.get("email_id")
        password = data.get("password")

        # Email and password login
        if email_id and password:
            user = Admin.find_by_email(email_id=email_id)

            if not user:
                return jsonify(status=False, message="Not found"), 404

            # Use dot notation for object attributes
            if not check_password_hash(user.password, password):
                return jsonify(status=False, message="Invalid credentials"), 400

            if user.role != 'admin':
                return jsonify(status=False, message="Unauthorized access"), 403

            # Convert _id to string if it's an ObjectId
            user_details = {
                "id": str(user.id),
                "email_id": user.email_id,
                "role": user.role
            }

            return jsonify(status=True, message="Login successful", data={"user_details": user_details}), 200

        else:
            return jsonify(status=False, message="Invalid login details"), 400

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
