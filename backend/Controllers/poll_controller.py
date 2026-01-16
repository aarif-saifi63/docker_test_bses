from flask import Flask, request, jsonify
from datetime import datetime
import requests
from Controllers.register_user_authentication_controller import get_ca, get_ca_for_division
from Models.poll_model import Poll
from Models.poll_response_model import PollResponse
from Models.session_model import Session
from utils.input_validator import InputValidator
from database import SessionLocal
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

FLASK_BASE_URL = os.getenv("BACKEND_URL") 
# FLASK_BASE_URL = f"{os.getenv('BASE_URL')}:{os.getenv('BACKEND_PORT')}"

# --- Create a Poll ---
def create_poll():
    data = request.json
    try:
        poll = Poll(
            title=data["title"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            questions=data["questions"],
            division_list=data.get("division_list", []),
            is_active=data.get("is_active", True)  # default to active unless specified
        )

        is_valid, msg = InputValidator.validate_name(poll.title, "title")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400
        
        # ✅ Validate each question
        for idx, question in enumerate(poll.questions):
            question_text = question.get("question")

            if not question_text:
                return jsonify({
                    "status": False,
                    "message": f"Question text missing at index {idx}"
                }), 400

            is_valid, msg = InputValidator.validate_name(
                question_text, f"question {idx + 1}"
            )
            if not is_valid:
                return jsonify({"status": False, "message": msg}), 400

        result = poll.save()

        if not result["status"]:
            return jsonify(result), 400

        return jsonify({
            "status": "success",
            "poll_id": result["poll_id"],
            "message": "Poll created successfully"
        }), 201

    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)}), 500


def update_poll(poll_id):
    data = request.json
    db = SessionLocal()

    try:
        poll = db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            return jsonify({"status": "fail", "message": "Poll not found"}), 404

        poll_name = data.get('title')

        questions = data.get('questions')

        is_valid, msg = InputValidator.validate_name(poll_name, "title")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400
        

        # ✅ Validate each question
        for idx, question in enumerate(questions):
            question_text = question.get("question")

            if not question_text:
                return jsonify({
                    "status": False,
                    "message": f"Question text missing at index {idx}"
                }), 400

            is_valid, msg = InputValidator.validate_name(
                question_text, f"question {idx + 1}"
            )
            if not is_valid:
                return jsonify({"status": False, "message": msg}), 400

        # Normalize new divisions (always list)
        new_divisions = data.get("division_list", poll.division_list or [])
        if not isinstance(new_divisions, list):
            return jsonify({"status": "fail", "message": "division_list must be a list"}), 400

        # If activating this poll OR changing divisions_list while active
        is_activating = data.get("is_active", poll.is_active)

        if is_activating is True:
            # --- Rule 1: Only one default poll can be active ---
            if not new_divisions:
                existing_default_poll = db.query(Poll).filter(
                    Poll.is_active.is_(True),
                    Poll.id != poll_id,
                    (Poll.division_list == None) | (Poll.division_list == [])
                ).first()
                if existing_default_poll:
                    return jsonify({
                        "status": "fail",
                        "message": f"Another default poll ('{existing_default_poll.title}') is already active. Please deactivate it first."
                    }), 400

            # --- Rule 2: Division-based polls can coexist, but no duplicate divisions ---
            else:
                active_polls = db.query(Poll).filter(
                    Poll.is_active.is_(True),
                    Poll.id != poll_id
                ).all()

                conflicting_divisions = set()
                for existing in active_polls:
                    if existing.division_list:
                        overlap = set(existing.division_list).intersection(new_divisions)
                        if overlap:
                            conflicting_divisions.update(overlap)

                if conflicting_divisions:
                    return jsonify({
                        "status": "fail",
                        "message": f"Division(s) {', '.join(conflicting_divisions)} already exist in another active poll."
                    }), 400

        # --- Apply Updates ---
        for key, value in data.items():
            if hasattr(poll, key):
                setattr(poll, key, value)

        poll.division_list = new_divisions
        poll.updated_at = datetime.now()

        db.commit()
        db.refresh(poll)

        return jsonify({
            "status": "success",
            "poll_id": poll.id,
            "message": "Poll updated successfully"
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"status": "fail", "message": str(e)}), 500
    finally:
        db.close()
        

def delete_poll(poll_id):
    db = SessionLocal()
    try:
        poll = db.query(Poll).filter_by(id=poll_id).first()
        if not poll:
            return jsonify({
                "status": "fail",
                "message": "Poll not found"
            }), 404

        db.delete(poll)
        db.commit()

        return jsonify({
            "status": "success",
            "message": f"Poll '{poll.title}' deleted successfully",
            "poll_id": poll_id
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({
            "status": "fail",
            "message": str(e)
        }), 500
    finally:
        db.close()



def get_active_poll():
    sender_id = request.args.get("sender_id") 
    
    # data = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
    # ca_data = data.json()

    result = Session.get_division_by_user_id(sender_id)
    if result["status"] == "success":
        division_name = result["division_name"]
        print(division_name, "===============ddddddddddddddddddd")
        poll = Poll.get_active_poll(division_name)
    else:
        division_name = None
        poll = Poll.get_active_poll()

    if not poll:
        return jsonify({"status": False, "message": "No active poll found"}), 404

    return jsonify({
        "status": True,
        "poll": {
            "id": poll.id,
            "title": poll.title,
            "start_time": poll.start_time.isoformat(),
            "end_time": poll.end_time.isoformat(),
            "questions": poll.questions,
            "division_list": poll.division_list or []
        }
    })


def submit_poll_response():
    try:
        data = request.get_json()

        # Required fields check
        poll_id = data.get("poll_id")
        user_type = data.get("user_type")
        response = data.get("response")  # should be list of {question, answer}

        # Ensure response is in correct format
        if not isinstance(response, list) or not all("question" in r and "answer" in r for r in response):
            return jsonify({"error": "response must be a list of {question, answer}"}), 400

        poll = PollResponse(
            poll_id=poll_id,
            user_type=user_type,
            response=response
        )
        poll_response_id = poll.save()
        return jsonify({"status": "success", "poll_response_id": poll_response_id})
    
    except Exception as e:
        return jsonify({"status": "fail", "error": str(e)}), 500


def get_all_polls():
    db_session = None
    try:
        db_session = SessionLocal()
        polls = db_session.query(Poll).order_by(Poll.created_at.desc()).all()
        polls_list = []

        for poll in polls:
            # Determine poll type
            if not poll.division_list or len(poll.division_list) == 0:
                poll_type = "default_poll"
            else:
                poll_type = "division_poll"

            polls_list.append({
                "id": poll.id,
                "title": poll.title,
                "start_time": poll.start_time.isoformat(),
                "end_time": poll.end_time.isoformat(),
                "is_active": poll.is_active,
                "questions": poll.questions,
                "division_list": poll.division_list,
                "poll_type": poll_type,   # ✅ added this field
                "created_at": poll.created_at.isoformat(),
                "updated_at": poll.updated_at.isoformat()
            })

        return jsonify({
            "status": "success",
            "count": len(polls_list),
            "polls": polls_list
        }), 200

    except Exception as e:
        return jsonify({"status": "fail", "message": str(e)}), 500
    finally:
        if db_session:
            db_session.close()