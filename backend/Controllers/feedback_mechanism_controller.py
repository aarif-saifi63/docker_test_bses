import json
import os
from flask import jsonify, request
import requests
from Models.ad_model import Advertisement
from Models.feedback_question_model import FeedbackQuestion
from Models.feedback_response_model import FeedbackResponse
from Models.intent_model import IntentV
from Models.session_model import Session
from Models.sub_menu_option_model import SubMenuOptionV
from utils.input_validator import InputValidator
from database import SessionLocal
from sqlalchemy import func, or_, Integer
from sqlalchemy.dialects.postgresql import array
from dotenv import load_dotenv

load_dotenv()

RASA_API_URL = os.getenv('RASA_CORE_URL')
# RASA_API_URL = f"{os.getenv('BASE_URL')}:{os.getenv('RASA_CORE_PORT')}"

def add_feedback_question():
    db = None
    try:
        data = request.json
        question = data.get("question")
        options = data.get("options")  # Can be list or None
        question_type = data.get("question_type")
        feedback_acceptance = data.get("feedback_acceptance")

        is_valid, msg = InputValidator.validate_name(question, "question")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400

        is_valid_options, msg_options = InputValidator.validate_name(question, "options")
        if not is_valid_options:
            return jsonify({"status": False, "message": msg_options}), 400

        if not question:
            return jsonify({"status": "error", "message": "Question is required"}), 400

        # Check for duplicate question based on question text and question_type
        db = SessionLocal()
        existing_question = db.query(FeedbackQuestion).filter(
            func.lower(FeedbackQuestion.question) == question.lower().strip(),
            func.lower(FeedbackQuestion.question_type) == question_type.lower().strip()
        ).first()

        if existing_question:
            return jsonify({
                "status": "error",
                "message": f"Question already exists for question_type '{question_type}'"
            }), 400

        # Store options only if provided
        options_str = json.dumps(options) if options else None

        new_question = FeedbackQuestion(question=question, options=options_str, question_type=question_type, feedback_acceptance=feedback_acceptance)
        new_question.save()

        return jsonify({
            "status": "success",
            "message": "Feedback question added successfully",
            "data": {
                "id": new_question.id,
                "question": new_question.question,
                "options": options if options else [],
                "question_type": new_question.question_type,
                "feedback_acceptance": new_question.feedback_acceptance
            }
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()



def update_feedback_question(question_id):
    db = None
    try:
        data = request.json
        question = data.get("question")
        options = data.get("options")  # Can be list or None

        is_valid, msg = InputValidator.validate_name(question, "question")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400

        is_valid_options, msg_options = InputValidator.validate_name(question, "options")
        if not is_valid_options:
            return jsonify({"status": False, "message": msg_options}), 400

        db = SessionLocal()

        # Fetch the current feedback question
        current_question = db.query(FeedbackQuestion).filter(FeedbackQuestion.id == question_id).first()

        if not current_question:
            return jsonify({"status": "error", "message": "Feedback question not found"}), 404

        # If question text is being updated, check for duplicates
        if question:
            # Check for duplicate question based on question text and question_type
            # Exclude the current question from the duplicate check
            existing_question = db.query(FeedbackQuestion).filter(
                func.lower(FeedbackQuestion.question) == question.lower().strip(),
                func.lower(FeedbackQuestion.question_type) == current_question.question_type.lower().strip(),
                FeedbackQuestion.id != question_id
            ).first()

            if existing_question:
                return jsonify({
                    "status": "error",
                    "message": f"Question already exists for question_type '{current_question.question_type}'"
                }), 400

        update_data = {}
        if question:
            update_data["question"] = question
        if options is not None:  # if provided, even empty list []
            update_data["options"] = json.dumps(options) if options else None

        if not update_data:
            return jsonify({"status": "error", "message": "No valid fields to update"}), 400

        updated = FeedbackQuestion.update_one({"id": question_id}, update_data)

        if updated:
            return jsonify({
                "status": "success",
                "message": "Feedback question updated successfully",
                "data": {
                    "id": question_id,
                    "question": update_data.get("question"),
                    "options": options if options is not None else "unchanged"
                }
            }), 200
        else:
            return jsonify({"status": "error", "message": "Feedback question not found"}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()
    
def delete_feedback_question(question_id):
    db = None
    try:
        db = SessionLocal()
        # Fetch the question first
        question = db.query(FeedbackQuestion).filter(FeedbackQuestion.id == question_id).first()

        if not question:
            return jsonify({"status": "error", "message": "Feedback question not found"}), 404

        # Delete the question
        db.delete(question)
        db.commit()

        return jsonify({
            "status": "success",
            "message": f"Feedback question with id {question_id} deleted successfully"
        }), 200

    except Exception as e:
        if db:
            db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if db:
            db.close()


def get_feedback_acceptance():
    db = None
    try:
        db = SessionLocal()
        # Filter only questions where feedback_acceptance string is 'True'
        questions = db.query(FeedbackQuestion).filter(FeedbackQuestion.feedback_acceptance == 'true').all()

        print(questions, "====================== acceptanced")
        response = []
        for q in questions:
            print(q.feedback_acceptance, "====================== acceptanced")
            response.append({
                "id": q.id,
                "question": q.question,
                "options": json.loads(q.options) if q.options else [],
                "question_type": q.question_type,
                "feedback_acceptance": q.feedback_acceptance
            })

        return jsonify({
            "status": "success",
            "data": response,
            "disable": True
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()


def get_feedback_questions():
    db = None
    try:
        question_type = request.args.get("question_type")
        if not question_type:
            return jsonify({"status": "error", "message": "question_type is required"}), 400

        db = SessionLocal()

        # Include rows where feedback_acceptance is NULL or not "True"
        questions = db.query(FeedbackQuestion).filter(
            func.lower(FeedbackQuestion.question_type) == question_type.lower(),
            or_(
                FeedbackQuestion.feedback_acceptance.is_(None),
                func.lower(FeedbackQuestion.feedback_acceptance) != 'true'
            )
        ).all()

        response = []
        for q in questions:
            response.append({
                "id": q.id,
                "question": q.question,
                "options": json.loads(q.options) if q.options else [],
                "question_type": q.question_type
            })

        return jsonify({
            "status": "success",
            "count": len(response),
            "disable": True,
            "data": response
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()
    

def submit_feedback():
    try:
        data = request.get_json()

        # Required fields check
        user_id = data.get("user_id")
        # user_type = data.get("user_type")
        # ca_number = data.get("ca_number")
        response = data.get("response")  # should be list of {question, answer}
        trigger_msg = data.get("lastSelectedOption", None)

        session_data = Session.find_one(user_id=user_id)

        # if not user_id or not user_type or not response:
        #     return jsonify({"error": "user_id, user_type, and response are required"}), 400

        # Ensure response is in correct format
        if not isinstance(response, list) or not all("question" in r and "answer" in r for r in response):
            return jsonify({"error": "response must be a list of {question, answer}"}), 400

        feedback = FeedbackResponse(
            user_id=user_id,
            user_type=session_data.user_type,
            ca_number=session_data.ca_number,
            response=response
        )
        feedback_id = feedback.save()


        response_intent = requests.post(
                f"{RASA_API_URL}/model/parse",
                json={"text": f'{trigger_msg} BRPL'}
            )

        data = response_intent.json()
        intent =  data["intent"]["name"]

        print(intent, "================================ intent")

        db = SessionLocal()

        # --- Step 1: Get submenu_id array from intent_v ---
        intent_record = db.query(IntentV).filter(IntentV.name == intent).first()

        if not intent_record:
            return jsonify({"error": f"No intent found for name: {intent}"}), 404
        
        print(intent_record, "===================================== intent_record")

        submenu_ids = intent_record.submenu_id

        # --- Step 2: Normalize submenu_ids ---
        if not submenu_ids:
            return jsonify({
                "intent_name": intent,
                "message": "No submenu_ids associated with this intent.",
                "submenus": []
            }), 200

        # Handle Postgres-style "{2,20}" string arrays
        if isinstance(submenu_ids, str):
            submenu_ids = submenu_ids.strip("{}")
            submenu_ids = [int(x) for x in submenu_ids.split(",") if x.strip().isdigit()]

        # Ensure proper list
        if not isinstance(submenu_ids, (list, tuple)):
            submenu_ids = [submenu_ids]

        if not submenu_ids:
            return jsonify({
                "intent_name": intent,
                "message": "No valid submenu IDs found.",
                "submenus": []
            }), 200

        # --- Step 3: Safe query using ANY() ---
        # Instead of .in_(), use PostgreSQL ANY operator to compare
        submenus = (
            db.query(SubMenuOptionV)
            .filter(
                SubMenuOptionV.id == func.any(array(submenu_ids, type_=Integer))
            )
            .filter(or_(SubMenuOptionV.is_visible == True, SubMenuOptionV.is_visible == None))
            .all()
        )

        print(submenus, "====================================== submenus")

        submenu_name = submenus[0].name

        print(submenu_name, "=================================== submenu data")


        ad_option = "show_feedback_ad"
        ad_option_submenu_name = submenu_name,
        ad_option_type = "after_feedback_ad"

        print(ad_option_submenu_name, "================= ad in submenu")


        # Prepare response
        response = {
            "message": "Thank you for giving your valuable feedback!",
            "message_hindi": "आपकी बहुमूल्य प्रतिक्रिया देने के लिए धन्यवाद!",
            "feedback_id": feedback_id,
            "ad_option_submenu_name":submenu_name
        }

        # Only add `show_ad` if it was set
        if ad_option == "show_feedback_ad":
            response["ad_option"] = ad_option
            # response["ad_option_submenu_name"] = ad_option_submenu_name
            response["ad_option_type"] = ad_option_type

        return jsonify(response), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500