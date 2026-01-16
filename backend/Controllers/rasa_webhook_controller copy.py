
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
from sqlalchemy import Integer, func, or_
from Models.ad_model import Advertisement
from Models.fallback_model import FallbackV
from Models.intent_model import IntentV
from Models.session_model import Session
from Models.sub_menu_option_model import SubMenuOptionV
from database import SessionLocal
from sqlalchemy.dialects.postgresql import array
from database import SessionLocal
# Load .env file
load_dotenv()

# RASA_API_URL = "http://localhost:5005/webhooks/rest/webhook"  # Update if different
RASA_API_URL = os.getenv('RASA_CORE_URL') 
# RASA_API_URL = f"{os.getenv('BASE_URL')}:{os.getenv('RASA_CORE_PORT')}"

from flask import jsonify, request
import pytz

IST = pytz.timezone("Asia/Kolkata")

# Dictionary to store fallback count per sender_id
fallback_counts = {}

def get_ist_time():
    return datetime.now(IST)


def webhook():
    db = None  # define here so we can safely close it in finally

    try:
        user_message = request.json.get('message')
        sender_id = request.json.get('sender_id', 'default_user')
        chatbot_type = request.json.get('chatbot_type')
        source = request.json.get('source')
        print("User Message:", user_message)

        # Send message to Rasa
        rasa_response = requests.post(f"{RASA_API_URL}/webhooks/rest/webhook", json={'sender': sender_id, 'message': user_message})
        rasa_response_json = rasa_response.json()
        print("Rasa Response:", rasa_response_json)

        # if rasa_response_json[0].get("text", "").strip() != "Sorry, I didn’t understand that. Can you rephrase?":
        #     fallback_counts[sender_id] = 0

        print(rasa_response_json and rasa_response_json[0].get("text", "").strip(), "=============== fallback")

        # if sender_id not in fallback_counts:
        #     fallback_counts[sender_id] = fallback_counts.get(sender_id, 0)

        # Fetch record with ID = 1
        fallback = FallbackV.find_one(id=1)

        if fallback:
            initial = fallback.initial_msg
            final = fallback.final_msg

        # Detect fallback
        is_fallback = False
        # if (rasa_response_json and rasa_response_json[0].get("text", "").strip() == "Sorry, I didn’t understand that. Can you rephrase?") or rasa_response_json and rasa_response_json[0].get("text", "").strip().startswith("Thanks for reaching out! I’m having trouble understanding your request. Our team is ready to assist:"):
        #     is_fallback = True
        # else:
        #     fallback_counts[sender_id] = 0

        if (rasa_response_json and rasa_response_json[0].get("text", "").strip() == initial) or rasa_response_json and rasa_response_json[0].get("text", "").strip().startswith(final):
            is_fallback = True
        else:
            fallback_counts[sender_id] = 0
            

        heading = []
        buttons = []
        icons = []
        main_menu_heading = None
        main_menu_buttons = []

        # main_menu_texts = [
        #     "Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)",
        #     "धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)"
        # ]

        main_menu_texts = [
            "Thank you. Would you like to return to the main menu? Select Yes or type ‘menu’ or ‘hi’ to continue.",
            "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए ‘हाँ’, ‘menu’ या ‘hi’ टाइप करें।"
        ]
        

        for item in rasa_response_json:
            text = item.get("text", "")
            lines = text.splitlines()

            for line in lines:
                stripped_line = line.strip()

                if not stripped_line:
                    continue

                if stripped_line in main_menu_texts:
                    main_menu_heading = stripped_line
                elif stripped_line.endswith('menu b'):
                    # remove "menu" and add only "Yes" or "No"
                    main_menu_buttons.append(stripped_line.replace('menu', '').replace('b', '').strip())
                elif stripped_line.endswith(' i'):
                    icons.append(stripped_line[:-1].strip())
                elif stripped_line.endswith(' b'):
                    buttons.append(stripped_line[:-1].strip())
                else:
                    heading.append(stripped_line)
                    

        # After the for loops and before creating the response dict
        # if len(heading) > 1 and heading[1].strip() == "Sorry, I didn’t understand that. Can you rephrase?":
        #     heading.pop(1)

        print(initial, "======================== initial")

        print(fallback.initial_msg, "======================== fallback initial")

        if len(heading) > 1 and heading[1].strip() == initial:
            heading.pop(1)


        response = {
            'response': {
                'heading': heading,
                'buttons': buttons,
            }
        }

        # ad = Advertisement.find_one(ad_name="Payment Offers")

        # Dynamically add keys based on the first heading
        if heading:
            first_message = heading[0].strip()
            # Safely get second message if it exists
            # second_message = heading[1].strip() if len(heading) > 1 else None
            if first_message == "Please select user type":
                response['response']['subsidiary'] = user_message
            # elif first_message in ["Please select your language", "Please enter your CA number."]:
            #     response['response']['user_type'] = user_message
            elif first_message in ["Please select your language"]:
                response['response']['user_type'] = user_message
            elif first_message in ["Please select your preferred language"]:
                response['response']['change_language'] = user_message
            elif first_message in ["Please enter your CA number."]:
                response['response']['user_type'] = user_message
            # elif first_message == "Language has been changed successfully":
            elif first_message == "Language updated successfully":
                response['response']['language'] = user_message
            elif first_message == "भाषा सफलतापूर्वक बदल दी गई है":
                response['response']['language'] = user_message

        if icons:
            response['response']['icons'] = icons

        if main_menu_heading:
            response['response']['main_menu_heading'] = main_menu_heading
            
            response_intent = requests.post(
                f"{RASA_API_URL}/model/parse",
                json={"text": user_message}
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

            

            # if submenu_name in ad.chatbot_options:
            response['response']['ad_option'] = "show_payment_ad"
            response['response']['ad_option_submenu_name'] = submenu_name
            response['response']['ad_option_type'] = "after_submenu_ad"


            # print(ad, "================ Advertisement fetched ==================")


        if main_menu_buttons:
            response['response']['main_menu_buttons'] = main_menu_buttons

        # existing_chat = Session.find_one({'user_id': sender_id})
        existing_chat = Session.find_one(user_id=sender_id)

        if user_message.lower() in ["ca verified brpl", "otp verified brpl", "order verified brpl", "mobile verified brpl", "email verified brpl"]:
            chat_entry = {
                # "query": user_message,
                "answer": response,
                "timestamp": get_ist_time().isoformat(),
                # "is_fallback": is_fallback
            }

        else:
            chat_entry = {
                "query": user_message,
                "answer": response,
                "timestamp": get_ist_time().isoformat(),
                "is_fallback": is_fallback
            }

        if existing_chat:
            print(existing_chat, "====================================== existing chat")
            Session.update_one(
                {"user_id": sender_id},
                {
                    "$push": {"chat": chat_entry},
                    "$set": {
                        "updated_at": get_ist_time().isoformat()
                    }
                }
            )
            print(existing_chat, "====================================== existing chat 2")
        else:
            chat_output = Session(
                user_id=sender_id,
                chat=[chat_entry],
                source=source,
                created_at=get_ist_time().isoformat(),
                updated_at=get_ist_time().isoformat()
            )
            chat_output.save()

        return jsonify(response)

    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500
    finally:
        # ✅ Safely close DB session if it was opened
        if db is not None:
            db.close()       



def run_flow():
    try:
        data = request.json
        subsidiary = data.get('subsidiary')
        user = data.get('user', 'New Consumer / नया उपभोक्ता')
        language = data.get('language')
        sender_id = data.get('sender_id', 'default_user')

        # Helper function to send message to Rasa
        def send_to_rasa(message):
            response = requests.post(f"{RASA_API_URL}/webhooks/rest/webhook", json={'sender': sender_id, 'message': message})
            return response.json()
        
        ## Restart the current session for menu flow
        send_to_rasa("restart")

        # Step 1: Run 'subsidiary' (no return)
        if subsidiary:
            send_to_rasa(subsidiary)

        # Step 2: Run 'user' (no return)
        if user:
            send_to_rasa(user)

        # Step 3: Run 'language' (returns response)
        rasa_response_json = send_to_rasa(language)
        print("Rasa Language Response:", rasa_response_json)

        heading = []
        buttons = []
        icons = []

        for item in rasa_response_json:
            text = item.get("text", "")
            lines = text.splitlines()

            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                if stripped_line.endswith('i'):
                    icons.append(stripped_line[:-1].strip())
                elif stripped_line.endswith('b'):
                    buttons.append(stripped_line[:-1].strip())
                else:
                    heading.append(stripped_line)

        # # Filter out unwanted success messages from heading
        unwanted_headings = {
            # "Language has been changed successfully",
            "Language updated successfully",
            "भाषा सफलतापूर्वक बदल दी गई है"
        }
        heading = [h for h in heading if h not in unwanted_headings]

        response = {
            'response': {
                'heading': heading,
                'buttons': buttons
            }
        }

        if icons:
            response['response']['icons'] = icons

        return jsonify(response)

    except Exception as e:
        print("Error:", e)
        return jsonify({
            'response': {
                "heading": ["Something went wrong."],
                "buttons": []
            }
        }), 500
    

def register_run_flow():
    try:
        data = request.json
        subsidiary = data.get('subsidiary')
        user = data.get('user', 'Registered Consumer / पंजीकृत उपभोक्ता')
        language = data.get('language')
        ca_number = data.get('ca_number', 'CA VALIDATED BRPL')
        otp = data.get('otp', 'OTP VALIDATED BRPL')
        sender_id = data.get('sender_id', 'default_user')

        # Helper function to send message to Rasa
        def send_to_rasa(message):
            response = requests.post(f"{RASA_API_URL}/webhooks/rest/webhook", json={'sender': sender_id, 'message': message})
            return response.json()
        
        ## Restart the current session for menu flow
        send_to_rasa("restart")

        # Step 1: Run 'subsidiary' (no return)
        if subsidiary:
            print(send_to_rasa(subsidiary))

        # Step 2: Run 'user' (no return)
        if user:
            print(send_to_rasa(user))

        # Step 3: Run 'ca_number' (no return)
        if ca_number:
            print(send_to_rasa(ca_number))

        # Step 4: Run 'otp' (no return)
        if otp:
            print(send_to_rasa(otp))

        # Step 5: Run 'language' (returns response)
        if language == "English BRPL":
            language += " BRPL"
        rasa_response_json = send_to_rasa(language)
        print("Rasa Language Response:", rasa_response_json)

        heading = []
        buttons = []
        icons = []

        for item in rasa_response_json:
            text = item.get("text", "")
            lines = text.splitlines()

            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                if stripped_line.endswith('i'):
                    icons.append(stripped_line[:-1].strip())
                elif stripped_line.endswith('b'):
                    buttons.append(stripped_line[:-1].strip())
                else:
                    heading.append(stripped_line)

        # # Filter out unwanted success messages from heading
        unwanted_headings = {
            # "Language has been changed successfully",
            "Language updated successfully",
            "भाषा सफलतापूर्वक बदल दी गई है"
        }
        heading = [h for h in heading if h not in unwanted_headings]

        response = {
            'response': {
                'heading': heading,
                'buttons': buttons
            }
        }

        if icons:
            response['response']['icons'] = icons

        return jsonify(response)

    except Exception as e:
        print("Error:", e)
        return jsonify({
            'response': {
                "heading": ["Something went wrong."],
                "buttons": []
            }
        }), 500
    

def ca_number_register_run_flow():
    try:
        data = request.json
        subsidiary = data.get('subsidiary')
        user = "Registered Consumer / पंजीकृत उपभोक्ता BRPL"
        sender_id = data.get('sender_id', 'default_user')

        # Helper function to send message to Rasa
        def send_to_rasa(message):
            response = requests.post(f"{RASA_API_URL}/webhooks/rest/webhook", json={'sender': sender_id, 'message': message + " BRPL"})
            return response.json()

        # Step 1: Run 'subsidiary' (no return)
        if subsidiary:
            print(send_to_rasa(subsidiary))

        # Step 5: Run 'language' (returns response)
        rasa_response_json =  print(send_to_rasa(user))
        print("Rasa Language Response:", rasa_response_json)

        heading = []
        buttons = []
        icons = []

        for item in rasa_response_json:
            text = item.get("text", "")
            lines = text.splitlines()

            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                if stripped_line.endswith('i'):
                    icons.append(stripped_line[:-1].strip())
                elif stripped_line.endswith('b'):
                    buttons.append(stripped_line[:-1].strip())
                else:
                    heading.append(stripped_line)

        response = {
            'response': {
                'heading': heading,
                'buttons': buttons
            }
        }

        if icons:
            response['response']['icons'] = icons

        return jsonify(response)

    except Exception as e:
        print("Error:", e)
        return jsonify({
            'response': {
                "heading": ["Something went wrong."],
                "buttons": []
            }
        }), 500




## Fallback mechanism

def handle_fallback():
    data = request.json
    sender_id = data.get("sender_id")

    if not sender_id:
        return jsonify({"error": "sender_id is required"}), 400

    db = None
    try:
        # Increment count for the sender
        fallback_counts[sender_id] = fallback_counts.get(sender_id, 0) + 1

        # Fetch record with ID = 1
        fallback = FallbackV.find_one(id=1)

        if fallback:
            initial = fallback.initial_msg
            final = fallback.final_msg

        # If count exceeds 3, reset and send link
        if fallback_counts[sender_id] > 2:
            fallback_counts[sender_id] = 0
            print(fallback_counts, "======================= fallback exceeded")
        #     return jsonify({
        # "action": (
        #     "Thanks for reaching out! I’m having trouble understanding your request. Our team is ready to assist:\n"
        #     "Call: 19123 (24x7 Toll-Free)\n"
        #     "WhatsApp: 8800919123\n"
        #     "Email: brpl.customercare@reliancegroupindia.com\n"
        #     "Website: https://www.bsesdelhi.com/web/brpl/home"
        # )
            return jsonify({
                "action": (
                    final
                )
            })

        else:
            print(fallback_counts, "======================= fallback not exceeded")
            # return jsonify({"action": "Sorry, I didn’t understand that. Can you rephrase?"})
            return jsonify({"action": initial})
    except Exception as e:
        raise e
    finally:
        # ✅ Safely close DB session if it was opened
        if db is not None:
            db.close() 


        
def reset_fallback():
    data = request.json
    sender_id = data.get("sender_id")

    if not sender_id:
        return jsonify({"error": "sender_id is required"}), 400

    fallback_counts[sender_id] = 0
    return jsonify({"message": f"Fallback count reset for {sender_id}"})
