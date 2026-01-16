from flask import jsonify, request
from Models.language_model import Language
from Models.session_model import Session
from utils.input_validator import InputValidator
from database import SessionLocal
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)


def create_language():
    data = request.json
    name = data.get("name")
    code = data.get("code")
    is_visible = data.get("is_visible", True)

    is_valid, msg = InputValidator.validate_name(name, "name")
    if not is_valid:
        return jsonify({"status": False, "message": msg}), 400

    if not name or not code:
        return jsonify({"error": "Both 'name' and 'code' are required", "status": False}), 400

    try:
        db = SessionLocal()

        # Case-insensitive check for duplicate language name
        existing_language_name = db.query(Language).filter(
            Language.name.ilike(name)
        ).first()

        if existing_language_name:
            return jsonify({
                "error": f"Language with name '{name}' already exists.",
                "status": False
            }), 400

        # Case-insensitive check for duplicate language code
        existing_language_code = db.query(Language).filter(
            Language.code.ilike(code)
        ).first()

        if existing_language_code:
            return jsonify({
                "error": f"Language with code '{code}' already exists.",
                "status": False
            }), 400

        language = Language(name=name, code=code, is_visible=is_visible)
        db.add(language)
        db.commit()
        db.refresh(language)

        return jsonify({
            "message": "Language created successfully",
            "id": language.id,
            "status": True
        }), 201

    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500

    finally:
        db.close()




# Get all languages or filter by query params

def get_languages():
    filters = request.args.to_dict()
    try:
        languages = Language.find(**filters)
        result = [
            {"id": l.id, "name": l.name, "code": l.code, "is_visible": l.is_visible,
             "created_at": l.created_at, "updated_at": l.updated_at}
            for l in languages
        ]
        return jsonify({"data":result, "message": "Fetch successfully", "status": True})
    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500


# Get a single language by ID
def get_language(language_id):
    try:
        language = Language.find_one(id=language_id)
        if not language:
            return jsonify({"error": "Language not found", "status": False}), 404
        result = {
            "id": language.id,
            "name": language.name,
            "code": language.code,
            "is_visible": language.is_visible,
            "created_at": language.created_at,
            "updated_at": language.updated_at
        }
        return jsonify({"data":result, "message": "Fetch successfully", "status": True})
    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500


# Update a language by ID
def update_language(language_id):
    data = request.json
    name = data.get("name")
    code = data.get("code")

    is_valid, msg = InputValidator.validate_name(name, "name")
    if not is_valid:
        return jsonify({"status": False, "message": msg}), 400

    try:
        db = SessionLocal()

        # Fetch the language to update
        language = db.query(Language).filter_by(id=language_id).first()
        if not language:
            return jsonify({"error": "Language not found", "status": False}), 404

        # Check for duplicate name (case-insensitive, excluding current record)
        if name:
            existing_language_name = db.query(Language).filter(
                Language.name.ilike(name),
                Language.id != language_id
            ).first()
            if existing_language_name:
                return jsonify({
                    "error": f"Language with name '{name}' already exists.",
                    "status": False
                }), 400

        # Check for duplicate code (case-insensitive, excluding current record)
        if code:
            existing_language_code = db.query(Language).filter(
                Language.code.ilike(code),
                Language.id != language_id
            ).first()
            if existing_language_code:
                return jsonify({
                    "error": f"Language with code '{code}' already exists.",
                    "status": False
                }), 400

        # Update allowed fields dynamically
        for key, value in data.items():
            if hasattr(language, key):
                setattr(language, key, value)

        language.updated_at = current_time_ist()
        db.commit()
        db.refresh(language)

        return jsonify({
            "message": "Language updated successfully",
            "status": True
        }), 200

    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500

    finally:
        db.close()


# Delete a language by ID

def delete_language(language_id):
    try:
        success = Language.delete(language_id)
        if success:
            return jsonify({"message": "Language deleted successfully", "status": True})
        else:
            return jsonify({"error": "Language not found", "status": False}), 404
    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500
    

def get_visible_languages():
    db: Session = SessionLocal()
    try:
        langs = (
            db.query(Language)
            .filter(Language.is_visible == True)
            .distinct()
            .all()
        )

        # Convert to list of dicts
        langs_list = [
            {"id": lang.id, "name": lang.name, "is_visible": lang.is_visible}
            for lang in langs
        ]

        # Move "English" to the first position if present
        langs_list.sort(key=lambda x: 0 if x["name"].lower() == "english" else 1)

        return jsonify({"status": True, "data": langs_list})
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500
    finally:
        db.close()
