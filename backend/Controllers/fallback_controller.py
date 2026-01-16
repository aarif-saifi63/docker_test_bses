from flask import jsonify, request
from Models.fallback_model import FallbackV
from utils.input_validator import InputValidator
from database import SessionLocal


def create_fallback():
    try:
        data = request.get_json()
        initial_msg = data.get("initial_msg")
        final_msg = data.get("final_msg")

        if not initial_msg or not final_msg:
            return jsonify({"error": "Both 'initial_msg' and 'final_msg' are required"}), 400

        fallback = FallbackV(initial_msg=initial_msg, final_msg=final_msg)
        fallback.save()

        return jsonify({"message": "Fallback created successfully", "id": fallback.id}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_all_fallbacks():
    try:
        db = SessionLocal()
        fallbacks = db.query(FallbackV).all()

        result = [
            {"id": f.id, "initial_msg": f.initial_msg, "final_msg": f.final_msg}
            for f in fallbacks
        ]
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



def get_fallback(fallback_id):
    try:
        fallback = FallbackV.find_one(id=fallback_id)
        if not fallback:
            return jsonify({"error": "Fallback not found"}), 404

        return jsonify({
            "id": fallback.id,
            "initial_msg": fallback.initial_msg,
            "final_msg": fallback.final_msg
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def update_fallback(fallback_id):
    try:
        data = request.get_json()

        # --- Validation for fallback messages ---
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


        success = FallbackV.update_one({"id": fallback_id}, data)

        if not success:
            return jsonify({"error": "Fallback not found or not updated"}), 404

        return jsonify({"message": "Fallback updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def delete_fallback(fallback_id):
    try:
        db = SessionLocal()
        fallback = db.query(FallbackV).filter_by(id=fallback_id).first()
        if not fallback:
            return jsonify({"error": "Fallback not found"}), 404

        db.delete(fallback)
        db.commit()
        return jsonify({"message": "Fallback deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500