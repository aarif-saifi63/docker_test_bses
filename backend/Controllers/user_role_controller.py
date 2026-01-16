import math
from flask import request, jsonify
from Models.user_role_model import UserRole
from Models.user_permission_mapping_model import UserPermissionMapping
from utils.input_validator import InputValidator
from database import SessionLocal

# --- Create a new Role ---
# def create_role():
#     try:
#         data = request.get_json()
#         role_name = data.get("role_name")
#         description = data.get("description", "")

#         if not role_name:
#             return jsonify(status=False, message="Role name is required"), 400

#         existing = UserRole.find_one(role_name=role_name)
#         if existing:
#             return jsonify(status=False, message="Role already exists"), 400

#         role = UserRole(role_name=role_name, description=description)
#         role_id = role.save()
#         return jsonify(status=True, message="Role created successfully", role_id=role_id), 201

#     except Exception as e:
#         return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


def create_role():
    try:
        data = request.get_json()
        role_name = data.get("role_name")
        description = data.get("description", "For testing")
        permissions = data.get("permissions", [])

        is_valid, msg = InputValidator.validate_name(role_name, "role name")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400

        if not role_name:
            return jsonify(status=False, message="Role name is required"), 400

        existing = UserRole.find_one(role_name=role_name)
        if existing:
            return jsonify(status=False, message="Role already exists"), 400

        role = UserRole(role_name=role_name, description=description)
        user_role_id = role.save()


        # Validate input
        if not user_role_id or not isinstance(permissions, list):
            return jsonify(status=False, message="Invalid data format"), 400

        db = SessionLocal()

        # Step 1: Delete all existing permissions for this role
        db.query(UserPermissionMapping).filter_by(user_role_id=user_role_id).delete()
        db.commit()

        # Step 2: Add only those permissions with has_permission = True
        for perm in permissions:
            if perm.get("has_permission"):
                new_mapping = UserPermissionMapping(
                    user_role_id=user_role_id,
                    permission_id=perm["id"]
                )
                db.add(new_mapping)

        db.commit()
        db.close()

        return jsonify(
            status=True,
            message="Role with permissions created successfully",
            updated_role_id=user_role_id
        ), 200

        # return jsonify(status=True, message="Role created successfully", role_id=role_id), 201

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500




# --- Get Roles with pagination and search ---
def get_roles():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        search = request.args.get("role_name", "")

        roles = UserRole.find()
        if search:
            roles = [r for r in roles if search.lower() in r.role_name.lower()]

        total_items = len(roles)
        total_pages = math.ceil(total_items / limit)
        start = (page - 1) * limit
        end = start + limit
        paginated = roles[start:end]

        data = [
            {
                "id": r.id,
                "role_name": r.role_name,
                "description": r.description
            } for r in paginated
        ]

        return jsonify(
            status=True,
            message="Roles fetched successfully",
            data=data,
            total_items=total_items,
            total_pages=total_pages,
            page=page,
            limit=limit
        ), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

# --- Get Role by ID ---
def get_role_by_id(role_id):
    try:
        role = UserRole.find_by_id(role_id)
        if not role:
            return jsonify(status=False, message="Role not found"), 404

        data = {
            "id": role.id,
            "role_name": role.role_name,
            "description": role.description
        }

        return jsonify(status=True, message="Role fetched successfully", data=data), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

# --- Update Role ---
def update_role(role_id):
    try:
        data = request.get_json()
        update_values = {}

        if "role_name" in data:
            update_values["role_name"] = data["role_name"]
        if "description" in data:
            update_values["description"] = data["description"]

        if not update_values:
            return jsonify(status=False, message="No fields to update"), 400

        updated = UserRole.update(role_id, update_values)
        if not updated:
            return jsonify(status=False, message="Role not found"), 404

        return jsonify(status=True, message="Role updated successfully"), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

# --- Delete Role ---
# def delete_role(role_id):
#     try:
#         deleted = UserRole.delete(role_id)
#         if not deleted:
#             return jsonify(status=False, message="Role not found"), 404

#         return jsonify(status=True, message="Role deleted successfully"), 200

#     except Exception as e:
#         return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

def delete_role(role_id):
    db = SessionLocal()
    try:

        # Step 1: Delete all existing permissions for this role
        db.query(UserPermissionMapping).filter_by(user_role_id=role_id).delete()
        db.commit()

        deleted = UserRole.delete(role_id)
        if not deleted:
            return jsonify(status=False, message="Role not found"), 404

        return jsonify(status=True, message="Role deleted successfully"), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
    finally:
        db.close()