from flask import request, jsonify
from Models.intent_example_model import IntentExampleV
from Controllers.api_key_master_controller import sanitize_for_csv
from utils.input_validator import InputValidator
from database import SessionLocal

# --- Create a new Intent Example ---
def create_intent_example():
    try:
        data = request.get_json()
        example_text = data.get("example")
        intent_id = data.get("intent_id")

        if not example_text or not intent_id:
            return jsonify(status=False, message="Example text and intent_id are required"), 400

        new_example = IntentExampleV(example=example_text, intent_id=intent_id)
        example_id = new_example.save()

        return jsonify(status=True, message="Intent example created successfully", example_id=example_id), 201

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Get all Examples for an Intent ---
def get_examples_by_intent(intent_id):
    try:
        examples = IntentExampleV.find_by_intent(intent_id)
        data = [{"id": ex.id, "example": ex.example} for ex in examples]

        return jsonify(status=True, message="Examples fetched successfully", data=data), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Get Example by ID ---
def get_example_by_id(example_id):
    try:
        example = IntentExampleV.find_one(example_id)
        if not example:
            return jsonify(status=False, message="Example not found"), 404

        data = {
            "id": example.id,
            "example": example.example,
            "intent_id": example.intent_id
        }

        return jsonify(status=True, message="Example fetched successfully", data=data), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Update Example ---
# def update_intent_example(intent_id):
#     """
#     Sync intent examples for a given intent_id.
#     - Updates existing examples if 'id' is provided.
#     - Inserts new examples if 'id' is missing.
#     - Deletes old examples that are not in the incoming list.
#     """
#     try:
#         data = request.get_json()
#         if not data or "examples" not in data:
#             return jsonify(status=False, message="No examples provided"), 400

#         incoming_examples = data["examples"]

#         # 1️⃣ Get all current examples for this intent
#         existing_examples = IntentExampleV.find_by_intent(intent_id)
#         existing_ids = {ex.id for ex in existing_examples}

#         # 2️⃣ Track incoming IDs
#         incoming_ids = set()

#         results = []

#         for example in incoming_examples:
#             ex_id = example.get("id")
#             ex_text = example.get("example")

#             if not ex_text:
#                 continue

#             if ex_id and ex_id in existing_ids:
#                 # Update existing
#                 updated = IntentExampleV.update(ex_id, {"example": ex_text})
#                 results.append({"id": ex_id, "example": ex_text, "action": "updated"})
#                 incoming_ids.add(ex_id)
#             else:
#                 # Insert new
#                 new_example = IntentExampleV(example=ex_text, intent_id=intent_id)
#                 new_id = new_example.save()
#                 results.append({"id": new_id, "example": ex_text, "action": "created"})
#                 incoming_ids.add(new_id)

#         # 3️⃣ Delete examples not in incoming list
#         for ex in existing_examples:
#             if ex.id not in incoming_ids:
#                 IntentExampleV.delete(ex.id)
#                 results.append({"id": ex.id, "example": ex.example, "action": "deleted"})

#         return jsonify(
#             status=True,
#             message="Intent examples synced successfully",
#             results=results
#         ), 200

#     except Exception as e:
#         return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500

def update_intent_example(intent_id):
    """
    Add or delete intent examples for a given intent_id.
    - Adds new examples by name.
    - Deletes existing examples by name.
    - Does NOT update existing examples.
    - Uses safe DB session handling.
    """
    db = SessionLocal()
    try:
        data = request.get_json()
        if not data:
            return jsonify(status=False, message="No data provided"), 400
 
        added_examples = data.get("added_examples", [])
        deleted_examples = data.get("deleted_examples", [])
 
        results = []
 
        # Add new examples
        for example_text in added_examples:

            is_valid, msg = InputValidator.validate_no_csv_injection(example_text, "example_text")
            if not is_valid:
                return jsonify({"status": False, "message": msg}), 400
            
            is_valid, msg = InputValidator.validate_fallback(example_text, "example_text")
            if not is_valid:
                return jsonify({"status": False, "message": msg}), 400
            
            example_text = sanitize_for_csv(example_text)

            ex_text = (example_text or "").strip()
            if not ex_text:
                continue
 
            # Check if example already exists for this intent (avoid duplicates)
            existing = IntentExampleV.find_by_example(intent_id, ex_text)
            if existing:
                results.append({"example": ex_text, "action": "already_exists"})
                continue
 
            new_example = IntentExampleV(example=ex_text, intent_id=intent_id)
            new_id = new_example.save()
            results.append({"id": new_id, "example": ex_text, "action": "created"})
 
        # Delete examples by name
        for example_text in deleted_examples:
            ex_text = (example_text or "").strip()
            if not ex_text:
                continue
 
            existing = IntentExampleV.find_by_example(intent_id, ex_text)
            if existing:
                IntentExampleV.delete(existing.id)
                results.append({"id": existing.id, "example": ex_text, "action": "deleted"})
            else:
                results.append({"example": ex_text, "action": "not_found"})
 
        db.close()
 
        return jsonify(
            status=True,
            message="Intent examples updated successfully",
            results=results
        ), 200
 
    except Exception as e:
        db.close()
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Delete Example ---
def delete_intent_example(example_id):
    try:
        deleted = IntentExampleV.delete(example_id)
        if not deleted:
            return jsonify(status=False, message="Example not found"), 404

        return jsonify(status=True, message="Example deleted successfully"), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500


# --- Delete all Examples for an Intent ---
def delete_examples_by_intent(intent_id):
    try:
        IntentExampleV.delete_by_intent(intent_id)
        return jsonify(status=True, message="All examples for the intent deleted"), 200

    except Exception as e:
        return jsonify(status=False, message=f"An error occurred: {str(e)}"), 500
