from flask import Blueprint, request, jsonify
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from utils.input_validator import InputValidator
from database import SessionLocal
from Models.utter_messages_model import UtterMessage
import requests


# utter_message_bp = Blueprint("utter_message_bp", __name__, url_prefix="/utter_messages")


def send_dynamic_messages(dispatcher, action_name, message_type, lang="en"):
    """
    Fetches utter messages dynamically from backend using action_name and language.
    """
    try:
        api_url = f"127.0.0.1:5000/get_utter_messages?message_type={message_type}&lang={lang}"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        messages = data.get("messages", [])
        if not messages:
            dispatcher.utter_message(text="No messages found for this action.")
            return

        for msg in messages:
            dispatcher.utter_message(text=msg)
    except Exception as e:
        dispatcher.utter_message(text=f"Unable to fetch messages for {action_name}. Error: {str(e)}")



# =========================================================
# 🟢 CREATE
# =========================================================
# @utter_message_bp.route("/", methods=["POST"])
def create_utter_message():
    data = request.json
    db = SessionLocal()

    try:
        # --- Validation ---
        required_fields = ["action_name", "text", "class_name"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "status": "fail",
                    "message": f"'{field}' is required."
                }), 400

        if "sequence" in data and not isinstance(data["sequence"], int):
            return jsonify({"status": "fail", "message": "Sequence must be an integer"}), 400

        # --- Check duplicate (optional) ---
        existing = db.query(UtterMessage).filter_by(
            action_name=data["action_name"],
            class_name=data["class_name"],
            language=data.get("language", "en"),
            sequence=data.get("sequence", 0)
        ).first()

        if existing:
            return jsonify({
                "status": "fail",
                "message": "Utter message with same action_name, language, and sequence already exists."
            }), 400

        # --- Create record ---
        new_utter = UtterMessage(
            action_name=data["action_name"],
            class_name=data["class_name"],
            language=data.get("language", "en"),
            sequence=data.get("sequence", 0),
            text=data["text"],
            message_type=data.get("message_type", "text"),  # NEW FIELD
            is_active=data.get("is_active", True),
        )
        db.add(new_utter)
        db.commit()
        db.refresh(new_utter)

        return jsonify({
            "status": "success",
            "message": "Utter message created successfully",
            "data": new_utter.to_dict()
        }), 201

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"status": "fail", "message": str(e.__cause__ or e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"status": "fail", "message": str(e)}), 500
    finally:
        db.close()


# =========================================================
# 🟡 READ ALL / FILTER
# =========================================================

# def get_all_utter_messages():
#     db = SessionLocal()
#     try:
#         query_db = db.query(UtterMessage).filter(UtterMessage.is_active == True)

#         # Optional Filters
#         action_name = request.args.get("action_name")
#         class_name = request.args.get("class_name")
#         language = request.args.get("language")
#         message_type = request.args.get("message_type")

#         if action_name:
#             query_db = query_db.filter(UtterMessage.action_name == action_name)
#         if class_name:
#             query_db = query_db.filter(UtterMessage.class_name == class_name)
#         if language:
#             query_db = query_db.filter(UtterMessage.language == language)
#         if message_type:
#             query_db = query_db.filter(UtterMessage.message_type == message_type)

#         # Get search query
#         search = request.args.get("search", "").strip()
#         has_search = bool(search)

#         q_upper = search.upper() if has_search else None

#         # Fetch all records BEFORE pagination (search needs full set)
#         records = query_db.order_by(UtterMessage.created_at.asc()).all()

#         filtered = []

#         for r in records:
#             if not has_search:
#                 filtered.append(r)
#                 continue

#             action_up = (r.action_name or "").upper()
#             class_up = (r.class_name or "").upper()
#             text_up = (r.text or "").upper()

#             score = 0

#             # === Search Rules ===
#             # Exact match
#             if action_up == q_upper or class_up == q_upper or text_up == q_upper:
#                 score = 100

#             # Starts-with
#             elif action_up.startswith(q_upper) or class_up.startswith(q_upper) or text_up.startswith(q_upper):
#                 score = 80

#             # Contains anywhere
#             elif q_upper in action_up or q_upper in class_up or q_upper in text_up:
#                 score = 60

#             if score > 0:
#                 r.__dict__["score"] = score  # attach score dynamically
#                 filtered.append(r)

#         # Sort by relevance when searching
#         if has_search:
#             filtered.sort(key=lambda x: x.__dict__.get("score", 0), reverse=True)

#         # === Pagination ===
#         page = int(request.args.get("page", 1))
#         per_page = 10
#         start = (page - 1) * per_page
#         end = start + per_page

#         paginated = filtered[start:end]

#         return jsonify({
#             "status": "success",
#             "page": page,
#             "per_page": per_page,
#             "count": len(filtered),
#             "data": [r.to_dict() for r in paginated]
#         }), 200

#     except SQLAlchemyError as e:
#         return jsonify({"status": "fail", "message": str(e.__cause__ or e)}), 500

#     finally:
#         db.close()

import re

def get_all_utter_messages():
    db = SessionLocal()
    try:
        query_db = db.query(UtterMessage).filter(UtterMessage.is_active == True)

        # Optional Filters
        action_name = request.args.get("action_name")
        class_name = request.args.get("class_name")
        language = request.args.get("language")
        message_type = request.args.get("message_type")

        if action_name:
            query_db = query_db.filter(UtterMessage.action_name == action_name)
        if class_name:
            query_db = query_db.filter(UtterMessage.class_name == class_name)
        if language:
            query_db = query_db.filter(UtterMessage.language == language)
        if message_type:
            query_db = query_db.filter(UtterMessage.message_type == message_type)

        # Search
        search = request.args.get("search", "").strip()
        has_search = bool(search)
        q_upper = search.upper() if has_search else None

        # Fetch all before pagination
        records = query_db.order_by(UtterMessage.created_at.asc()).all()

        filtered = []

        for r in records:
            if not has_search:
                filtered.append(r)
                continue

            action_up = (r.action_name or "").upper()
            class_up = (r.class_name or "").upper()
            text_up = (r.text or "").upper()

            score = 0

            # Exact match
            if action_up == q_upper or class_up == q_upper or text_up == q_upper:
                score = 100
            # Starts-with
            elif action_up.startswith(q_upper) or class_up.startswith(q_upper) or text_up.startswith(q_upper):
                score = 80
            # Contains anywhere
            elif q_upper in action_up or q_upper in class_up or q_upper in text_up:
                score = 60

            if score > 0:
                r.__dict__["score"] = score
                filtered.append(r)

        if has_search:
            filtered.sort(key=lambda x: x.__dict__.get("score", 0), reverse=True)

        # Pagination
        page = int(request.args.get("page", 1))
        per_page = 10
        start = (page - 1) * per_page
        end = start + per_page

        paginated = filtered[start:end]

        # Prepare final data
        data_list = []

        for r in paginated:
            d = r.to_dict()

            text = d.get("text", "").strip()

            # CASE 1: Starts with serial number "1.", "2.", "10." etc.
            starts_with_serial = bool(re.match(r"^\d+\.\s*", text))

            # CASE 2: Starts with serial number and ends with "b"
            starts_with_serial_and_b = bool(re.match(r"^\d+\..*b$", text))

            if starts_with_serial or starts_with_serial_and_b:
                d["protection_note"] = (
                    "Do NOT change or remove the serial number (e.g., '1.' or '2.') "
                    "or the trailing 'b' when present. Only update the inner text."
                )

            data_list.append(d)

        return jsonify({
            "status": "success",
            "page": page,
            "per_page": per_page,
            "count": len(filtered),
            "data": data_list
        }), 200

    except SQLAlchemyError as e:
        return jsonify({"status": "fail", "message": str(e.__cause__ or e)}), 500

    finally:
        db.close()
 


# =========================================================
# 🟢 READ SINGLE
# =========================================================
# @utter_message_bp.route("/<uuid:uid>", methods=["GET"])
def get_utter_message(uid):
    db = SessionLocal()
    try:
        record = db.query(UtterMessage).filter_by(uid=uid).first()
        if not record:
            return jsonify({
                "status": "fail",
                "message": "Utter message not found"
            }), 404

        return jsonify({
            "status": "success",
            "data": record.to_dict()
        }), 200

    except SQLAlchemyError as e:
        return jsonify({"status": "fail", "message": str(e.__cause__ or e)}), 500
    finally:
        db.close()

## Updated get utter message

def updated_get_utter_messages():
    message_type = request.args.get("message_type")
    lang = request.args.get("lang")

    if not message_type or not lang:
        return jsonify({
            "status": "fail",
            "message": "Both 'message_type' and 'lang' query parameters are required"
        }), 400
    
    print("under the utter meesage")

    db = SessionLocal()
    try:
        records = (
            db.query(UtterMessage)
            .filter_by(message_type=message_type, language=lang)
            .all()
        )

        if not records:
            return jsonify({
                "status": "fail",
                "message": "No utter messages found for the given filters"
            }), 404

        return jsonify({
            "status": "success",
            "data": [r.to_dict() for r in records]
        }), 200

    except SQLAlchemyError as e:
        return jsonify({
            "status": "fail",
            "message": str(e.__cause__ or e)
        }), 500

    finally:
        db.close()


# =========================================================
# 🟠 UPDATE
# =========================================================
# @utter_message_bp.route("/<uuid:uid>", methods=["PUT"])
def update_utter_message(uid):
    data = request.json
    db = SessionLocal()

    try:
        utter = db.query(UtterMessage).filter_by(uid=uid).first()
        if not utter:
            return jsonify({
                "status": "fail",
                "message": "Utter message not found"
            }), 404
        

        # --- Validation ---
        if "text" in data:
            if not isinstance(data["text"], str):
                return jsonify({"status": "fail", "message": "Text must be a string"}), 400

            is_valid, msg = InputValidator.validate_fallback(
                data["text"], "utter_message_text"
            )
            if not is_valid:
                return jsonify({"status": "fail", "message": msg}), 400

        # --- Validation ---
        if "sequence" in data and not isinstance(data["sequence"], int):
            return jsonify({"status": "fail", "message": "Sequence must be an integer"}), 400
        if "language" in data and not isinstance(data["language"], str):
            return jsonify({"status": "fail", "message": "Language must be a string"}), 400
        if "message_type" in data and not isinstance(data["message_type"], str):
            return jsonify({"status": "fail", "message": "message_type must be a string"}), 400  # NEW VALIDATION

        # --- Unique constraint on activation ---
        if data.get("is_active") is True:
            duplicate_active = db.query(UtterMessage).filter(
                UtterMessage.uid != uid,
                UtterMessage.action_name == data.get("action_name", utter.action_name),
                UtterMessage.class_name == data.get("class_name", utter.class_name),
                UtterMessage.language == data.get("language", utter.language),
                UtterMessage.sequence == data.get("sequence", utter.sequence),
                UtterMessage.is_active.is_(True)
            ).first()
            if duplicate_active:
                return jsonify({
                    "status": "fail",
                    "message": (
                        f"Another active utter message already exists for "
                        f"action '{duplicate_active.action_name}', "
                        f"class_name '{duplicate_active.class_name}', "
                        f"language '{duplicate_active.language}', "
                        f"sequence '{duplicate_active.sequence}'."
                    )
                }), 400

        # --- Apply updates ---
        for key, value in data.items():
            if hasattr(utter, key):
                setattr(utter, key, value)

        utter.updated_at = datetime.now()

        db.commit()
        db.refresh(utter)

        return jsonify({
            "status": "success",
            "message": "Utter message updated successfully",
            "data": utter.to_dict()
        }), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"status": "fail", "message": str(e.__cause__ or e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"status": "fail", "message": str(e)}), 500
    finally:
        db.close()


# =========================================================
# 🔴 DELETE
# =========================================================
# @utter_message_bp.route("/<uuid:uid>", methods=["DELETE"])
def delete_utter_message(uid):
    db = SessionLocal()
    try:
        record = db.query(UtterMessage).filter_by(uid=uid).first()
        if not record:
            return jsonify({
                "status": "fail",
                "message": "Utter message not found"
            }), 404

        db.delete(record)
        db.commit()

        return jsonify({
            "status": "success",
            "message": "Utter message deleted successfully"
        }), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"status": "fail", "message": str(e.__cause__ or e)}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"status": "fail", "message": str(e)}), 500
    finally:
        db.close()
