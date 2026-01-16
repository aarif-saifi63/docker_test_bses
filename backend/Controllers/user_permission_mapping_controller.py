import math
from flask import request, jsonify
from Models.user_permission_mapping_model import UserPermissionMapping
from Models.user_role_model import UserRole
from Models.permission_matrix_model import PermissionMatrix
from database import SessionLocal

def create_mapping():
    try:
        data = request.get_json()
        user_role_id = data.get("user_role_id")
        permission_id = data.get("permission_id")

        if not user_role_id or not permission_id:
            return jsonify(status=False, message="user_role_id and permission_id are required"), 400

        existing = UserPermissionMapping.find_one(user_role_id=user_role_id, permission_id=permission_id)
        if existing:
            return jsonify(status=False, message="Mapping already exists"), 400

        mapping = UserPermissionMapping(user_role_id=user_role_id, permission_id=permission_id)
        mapping_id = mapping.save()
        return jsonify(status=True, message="Mapping created successfully", mapping_id=mapping_id), 201

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

def get_mappings():
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 15))

        with SessionLocal() as db:
            # Fetch all roles
            roles = db.query(UserRole).all()

            # Fetch all permissions
            all_permissions = db.query(PermissionMatrix).all()

            # Fetch all mappings
            mappings = db.query(UserPermissionMapping).all()

            # Build a dict for quick lookup: role_id -> set(permission_id)
            role_permission_map = {}
            for m in mappings:
                if m.user_role_id not in role_permission_map:
                    role_permission_map[m.user_role_id] = set()
                role_permission_map[m.user_role_id].add(m.permission_id)

            # Build data
            data = []
            for role in roles:
                role_permissions = []
                for perm in all_permissions:
                    has_permission = False
                    if role.id in role_permission_map and perm.id in role_permission_map[role.id]:
                        has_permission = True
                    role_permissions.append({
                        "id": perm.id,
                        "name": perm.permission_name,
                        "has_permission": has_permission
                    })
                data.append({
                    "user_role_id": role.id,
                    "user_role_name": role.role_name,
                    "permissions": role_permissions
                })

            # Pagination
            total_items = len(data)
            total_pages = math.ceil(total_items / limit)
            start = (page - 1) * limit
            end = start + limit
            paginated = data[start:end]

        return jsonify(
            status=True,
            message="Mappings fetched successfully",
            data=paginated,
            total_items=total_items,
            total_pages=total_pages,
            page=page,
            limit=limit
        ), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

def get_mapping_by_id(mapping_id):
    try:
        mapping = UserPermissionMapping.find_by_id(mapping_id)
        if not mapping:
            return jsonify(status=False, message="Mapping not found"), 404

        data = {
            "id": mapping.id,
            "user_role_id": mapping.user_role_id,
            "permission_id": mapping.permission_id
        }

        return jsonify(status=True, message="Mapping fetched successfully", data=data), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

def update_mapping(mapping_id):
    try:
        data = request.get_json()
        user_role_id = data.get("user_role_id")
        permissions = data.get("permissions", [])

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
            message="Permissions updated successfully for the role",
            updated_role_id=user_role_id
        ), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

def update_mapping_users():
    try:
        data = request.get_json()

        user_details_id = data.get("user_details_id")
        user_role_id = data.get("user_role_id")  # needed for DB insert
        user_permissions = data.get("user_permissions", [])

        if not user_details_id or not isinstance(user_permissions, list):
            return jsonify(
                status=False,
                message="Provide user_details_id and user_permissions list"
            ), 400

        db = SessionLocal()

        # Step 1: Fetch existing user-specific permissions
        existing_mappings = db.query(UserPermissionMapping)\
            .filter_by(user_details_id=user_details_id)\
            .all()
        existing_permission_ids = {m.permission_id for m in existing_mappings}

        # Step 2: Delete unchecked permissions
        permissions_to_delete = [
            perm.get("id") for perm in user_permissions
            if perm.get("has_permission") is False and perm.get("id") in existing_permission_ids
        ]
        if permissions_to_delete:
            db.query(UserPermissionMapping)\
                .filter(
                    UserPermissionMapping.user_details_id == user_details_id,
                    UserPermissionMapping.permission_id.in_(permissions_to_delete)
                ).delete(synchronize_session=False)

        # Step 3: Add new permissions (has_permission=True)
        for perm in user_permissions:
            perm_id = perm.get("id")
            has_perm = perm.get("has_permission", True)

            if has_perm and perm_id not in existing_permission_ids:
                mapping = UserPermissionMapping(
                    user_details_id=user_details_id,
                    user_role_id=user_role_id,  # required for DB
                    permission_id=perm_id
                )
                db.add(mapping)

        db.commit()
        db.close()

        return jsonify(
            status=True,
            message=f"User permissions updated successfully for user {user_details_id}"
        ), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


def delete_mapping(mapping_id):
    try:
        deleted = UserPermissionMapping.delete(mapping_id)
        if not deleted:
            return jsonify(status=False, message="Mapping not found"), 404

        return jsonify(status=True, message="Mapping deleted successfully"), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
