from flask import jsonify, request
from Models.submenu_fallback_model import SubmenuFallbackV
from utils.input_validator import InputValidator
from database import SessionLocal


def create_submenu_fallback():
    """
    Create a new submenu fallback configuration.

    Request Body:
    {
        "category": "faqs",
        "intent_names": "faq_1, faq_2, faq_3",
        "initial_msg": "Initial fallback message",
        "final_msg": "Final fallback message",
        "user_type": ["new_consumer", "registered_consumer"],  # Optional
        "language": "en"  # Optional
    }
    """
    try:
        data = request.get_json()
        category = data.get("category")
        intent_names = data.get("intent_names")
        initial_msg = data.get("initial_msg")
        final_msg = data.get("final_msg", "default final message")
        user_type = data.get("user_type")  # Optional
        language = data.get("language")  # Optional

        is_valid, msg = InputValidator.validate_name(category, "menu name")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400
        
        is_valid, msg = InputValidator.validate_name(intent_names, "intent names")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400
        
        is_valid, msg = InputValidator.validate_name(initial_msg, "initial message")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400
        
        is_valid, msg = InputValidator.validate_name(language, "language")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400
        
        is_valid, msg = InputValidator.validate_name(user_type, "user type")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400

        # Validate required fields
        if not category or not intent_names or not initial_msg:
            return jsonify({
                "error": "Fields 'category', 'intent_names', 'initial_msg' are required"
            }), 400

        # Validate category (no special characters at start for CSV injection prevention)
        if category.startswith(("=", "+", "-", "@")):
            return jsonify({
                "error": "category cannot start with special characters"
            }), 400

        # Validate messages
        for field in ("initial_msg", "final_msg"):
            if not isinstance(data[field], str):
                return jsonify({
                    "error": f"{field} must be a string"
                }), 400

            # Prevent CSV / formula injection
            if data[field].startswith(("=", "+", "-", "@")):
                return jsonify({
                    "error": f"{field} cannot start with special characters"
                }), 400

            is_valid, msg = InputValidator.validate_fallback(data[field], field)
            if not is_valid:
                return jsonify({
                    "error": msg
                }), 400

        # Check if category already exists
        existing = SubmenuFallbackV.find_one(category=category)
        if existing:
            return jsonify({
                "error": f"Submenu fallback with category '{category}' already exists"
            }), 409

        # Create new submenu fallback
        submenu_fallback = SubmenuFallbackV(
            category=category,
            intent_names=intent_names,
            initial_msg=initial_msg,
            final_msg=final_msg,
            user_type=user_type,
            language=language
        )
        submenu_fallback_id = submenu_fallback.save()

        return jsonify({
            "message": "Submenu fallback created successfully",
            "id": submenu_fallback_id
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_all_submenu_fallbacks():
    """
    Get all submenu fallback configurations.

    Returns:
    [
        {
            "id": 1,
            "category": "faqs",
            "intents": ["faq_1", "faq_2"],
            "initial_msg": "...",
            "final_msg": "...",
            "user_type": ["new_consumer"],
            "language": "en"
        }
    ]
    """
    try:
        fallbacks = SubmenuFallbackV.find_all()

        result = [fallback.to_dict() for fallback in fallbacks]
        result_with_id = [
            {"id": f.id, **f.to_dict()}
            for f in fallbacks
        ]

        return jsonify(result_with_id), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_submenu_fallback_by_category(category):
    """
    Get submenu fallback configuration by category.

    Path Parameter:
    - category: The category name (e.g., "faqs", "payment_history")

    Returns:
    {
        "id": 1,
        "category": "faqs",
        "intents": ["faq_1", "faq_2"],
        "initial_msg": "...",
        "final_msg": "...",
        "user_type": ["new_consumer"],
        "language": "en"
    }
    """
    try:
        fallback = SubmenuFallbackV.find_one(category=category)
        if not fallback:
            return jsonify({
                "error": f"Submenu fallback with category '{category}' not found"
            }), 404

        return jsonify({
            "id": fallback.id,
            **fallback.to_dict()
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_submenu_fallback(category):
    """
    Update submenu fallback configuration by category.

    Path Parameter:
    - category: The category name

    Request Body (all fields optional):
    {
        "intent_names": "updated_intent_1, updated_intent_2",
        "initial_msg": "Updated initial message",
        "final_msg": "Updated final message",
        "user_type": ["registered_consumer"],
        "language": "hi"
    }
    """
    try:
        data = request.get_json()

        # Validate messages if provided
        for field in ("initial_msg", "final_msg"):
            if field in data:
                if not isinstance(data[field], str):
                    return jsonify({
                        "error": f"{field} must be a string"
                    }), 400

                # Prevent CSV / formula injection
                if data[field].startswith(("=", "+", "-", "@")):
                    return jsonify({
                        "error": f"{field} cannot start with special characters"
                    }), 400

                is_valid, msg = InputValidator.validate_fallback(data[field], field)
                if not is_valid:
                    return jsonify({
                        "error": msg
                    }), 400

        # Update the record
        success = SubmenuFallbackV.update_one({"category": category}, data)

        if not success:
            return jsonify({
                "error": f"Submenu fallback with category '{category}' not found or not updated"
            }), 404

        return jsonify({
            "message": "Submenu fallback updated successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_submenu_fallback(category):
    """
    Delete submenu fallback configuration by category.

    Path Parameter:
    - category: The category name
    """
    try:
        db = SessionLocal()
        fallback = db.query(SubmenuFallbackV).filter_by(category=category).first()

        if not fallback:
            db.close()
            return jsonify({
                "error": f"Submenu fallback with category '{category}' not found"
            }), 404

        db.delete(fallback)
        db.commit()
        db.close()

        return jsonify({
            "message": "Submenu fallback deleted successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_all_submenu_categories():
    """
    Get list of all submenu fallback categories.

    Returns:
    [
        {
            "category": "faqs",
            "intent_count": 3
        },
        {
            "category": "payment_history",
            "intent_count": 2
        }
    ]
    """
    try:
        fallbacks = SubmenuFallbackV.find_all()

        result = [
            {
                "category": f.category,
                "initial_msg": f.initial_msg,
                "intent_count": len(f.get_intents_list())
            }
            for f in fallbacks
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
