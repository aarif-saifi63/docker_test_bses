from datetime import datetime
from flask import jsonify, request
from Models.session_model import Session
from database import SessionLocal
from dotenv import load_dotenv
import os
 
# Load .env file
load_dotenv()

def save_bill_pay_chat():
    try:
        data = request.json
        sender_id = data.get("sender_id")
        response = data.get("response")

        if not sender_id or not response:
            return jsonify({"error": "sender_id and response are required"}), 400

        existing_chat = Session.find_one(user_id=sender_id)

        chat_entry = {
            "query": "pay the bill",
            "answer": response,
            "timestamp": datetime.now().isoformat()
        }

        if existing_chat:
            Session.update_one(
                {"user_id": sender_id},
                {
                    "$push": {"chat": chat_entry},
                    "$set": {"updated_at": datetime.now()}
                }
            )
        else:
            Session.insert_one({
                "user_id": sender_id,
                "chat": [chat_entry],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })

        return jsonify({"message": "Bill Pay Chat saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def save_duplicate_bill_chat():
    try:
        data = request.json
        sender_id = data.get("sender_id")
        response = data.get("response")

        if not sender_id or not response:
            return jsonify({"error": "sender_id and response are required"}), 400

        existing_chat = Session.find_one(user_id=sender_id)

        chat_entry = {
            "query": "download the duplicate bill",
            "answer": response,
            "timestamp": datetime.now().isoformat()
        }

        if existing_chat:
            Session.update_one(
                {"user_id": sender_id},
                {
                    "$push": {"chat": chat_entry},
                    "$set": {"updated_at": datetime.now()}
                }
            )
        else:
            Session.insert_one({
                "user_id": sender_id,
                "chat": [chat_entry],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })

        return jsonify({"message": "Duplicate Bill Chat saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def dashboard_pay_bill():
    try:
        db = SessionLocal()
        all_sessions = db.query(Session).all()

        pay_bill_count = 0
        users_initiated_pay_bill = set()

        for session in all_sessions:
            if session.chat:
                for entry in session.chat:
                    query = entry.get("query", "").lower()
                    answer = entry.get("answer", "")

                    # Match both query and answer
                    if query == "pay the bill" and answer == "https://www.bsesdelhi.com/web/brpl/quick-pay":
                        pay_bill_count += 1
                        users_initiated_pay_bill.add(session.user_id)

        response = {
            "stats": {
                "pay_bill_count": pay_bill_count,
                "unique_users_initiated_pay_bill": len(users_initiated_pay_bill)
            }
        }
        return jsonify(response)

    except Exception as e:
        print("Dashboard Pay Bill Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500
    


def dashboard_download_duplicate_bill():
    try:
        db = SessionLocal()
        all_sessions = db.query(Session).all()

        pay_bill_count = 0
        users_initiated_pay_bill = set()

        flask_url = os.getenv('BACKEND_URL')
        # flask_url = f"{os.getenv('BASE_URL')}:{os.getenv('BACKEND_PORT')}"
        base_url = f"{flask_url}/Media/generated_pdfs/"
        # base_url = "https://uat-bsesapi.superaip.com/generated_pdfs/"

        for session in all_sessions:
            if session.chat:
                for entry in session.chat:
                    query = entry.get("query", "").lower()
                    answer = entry.get("answer", "")

                    # Match both query and dynamic answer link
                    if query == "download the duplicate bill" and answer.startswith(base_url):
                        pay_bill_count += 1
                        users_initiated_pay_bill.add(session.user_id)

        response = {
            "stats": {
                "duplicate_bill_download": pay_bill_count,
                "unique_users_initiated_duplicate_bill_download": len(users_initiated_pay_bill)
            }
        }
        return jsonify(response)

    except Exception as e:
        print("Dashboard Pay Bill Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500
