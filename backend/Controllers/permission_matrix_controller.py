import math
from flask import request, jsonify
from Models.permission_matrix_model import PermissionMatrix

# --- Create a new Permission ---
def create_permission():
    try:
        data = request.get_json()
        module = data.get("module")
        crud_action = data.get("crud_action")
        permission_name = data.get("permission_name")
        description = data.get("description", "")
        label = data.get("label", "")

        if not module or not crud_action or not permission_name:
            return jsonify(status=False, message="module, crud_action, and permission_name are required"), 400

        # Check if permission already exists
        existing = PermissionMatrix.find_one(permission_name=permission_name)
        if existing:
            return jsonify(status=False, message="Permission already exists"), 400

        permission = PermissionMatrix(
            module=module,
            crud_action=crud_action,
            permission_name=permission_name,
            description=description,
            label=label
        )
        permission_id = permission.save()
        return jsonify(status=True, message="Permission created successfully", permission_id=permission_id), 201

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Get Permissions with pagination and search ---
def get_permissions():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 100))
        search = request.args.get("permission_name", "")

        permissions = PermissionMatrix.find()
        if search:
            permissions = [p for p in permissions if search.lower() in p.permission_name.lower()]

        total_items = len(permissions)
        total_pages = math.ceil(total_items / limit)
        start = (page - 1) * limit
        end = start + limit
        paginated = permissions[start:end]

        data = [
            {
                "id": p.id,
                "module": p.module,
                "crud_action": p.crud_action,
                "permission_name": p.permission_name,
                "description": p.description,
                "label": p.label
            } for p in paginated
        ]

        return jsonify(
            status=True,
            message="Permissions fetched successfully",
            data=data,
            total_items=total_items,
            total_pages=total_pages,
            page=page,
            limit=limit
        ), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Get Permission by ID ---
def get_permission_by_id(permission_id):
    try:
        permission = PermissionMatrix.find_by_id(permission_id)
        if not permission:
            return jsonify(status=False, message="Permission not found"), 404

        data = {
            "id": permission.id,
            "module": permission.module,
            "crud_action": permission.crud_action,
            "permission_name": permission.permission_name,
            "description": permission.description,
            "label": permission.label
        }

        return jsonify(status=True, message="Permission fetched successfully", data=data), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Update Permission ---
def update_permission(permission_id):
    try:
        data = request.get_json()
        update_values = {}

        for field in ["module", "crud_action", "permission_name", "description", "label"]:
            if field in data:
                update_values[field] = data[field]

        if not update_values:
            return jsonify(status=False, message="No fields to update"), 400

        updated = PermissionMatrix.update(permission_id, update_values)
        if not updated:
            return jsonify(status=False, message="Permission not found"), 404

        return jsonify(status=True, message="Permission updated successfully"), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Delete Permission ---
def delete_permission(permission_id):
    try:
        deleted = PermissionMatrix.delete(permission_id)
        if not deleted:
            return jsonify(status=False, message="Permission not found"), 404

        return jsonify(status=True, message="Permission deleted successfully"), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
