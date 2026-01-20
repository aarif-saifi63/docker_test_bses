
from datetime import datetime
from dotenv import load_dotenv
import os
import requests
import redis
from sqlalchemy import Integer, func, or_
from Models.ad_model import Advertisement
from Models.fallback_model import FallbackV
from Models.intent_model import IntentV
from Models.intent_example_model import IntentExampleV
from Models.session_model import Session
from Models.sub_menu_option_model import SubMenuOptionV
from Models.submenu_fallback_model import SubmenuFallbackV
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

# Redis client for fallback count persistence
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    db=0,
    decode_responses=True
)

# Cache for submenu fallback config (loaded from database)
_SUBMENU_FALLBACK_CACHE = None
_CACHE_TIMESTAMP = None
CACHE_DURATION = 3  # 5 minutes in seconds


def load_submenu_fallback_config():
    """
    Load submenu fallback configuration from database.
    Uses caching to avoid querying database on every request.
    Returns a dictionary in the same format as SUBMENU_FALLBACK_CONFIG.
    """
    global _SUBMENU_FALLBACK_CACHE, _CACHE_TIMESTAMP

    # Check if cache is valid
    current_time = datetime.now().timestamp()
    if _SUBMENU_FALLBACK_CACHE is not None and _CACHE_TIMESTAMP is not None:
        if (current_time - _CACHE_TIMESTAMP) < CACHE_DURATION:
            return _SUBMENU_FALLBACK_CACHE

    # Load from database
    try:
        submenu_fallbacks = SubmenuFallbackV.find_all()
        config = {}

        for fallback in submenu_fallbacks:
            config[fallback.category] = {
                "intents": fallback.get_intents_list(),
                "initial_msg": fallback.initial_msg,
                "final_msg": fallback.final_msg,
                "user_type": fallback.user_type,
                "language": fallback.language,
                "option": fallback.category
            }

        # Update cache
        _SUBMENU_FALLBACK_CACHE = config
        _CACHE_TIMESTAMP = current_time

        print(f"Loaded {len(config)} submenu fallback configurations from database")
        return config

    except Exception as e:
        print(f"Error loading submenu fallback config from database: {e}")
        # Return empty config if database fails
        return {}


# Fallback to hardcoded config (for backward compatibility during migration)
# This will be removed once all data is in the database

def get_submenu_category(intent_name):
    """
    Determine which submenu category an intent belongs to.
    Returns the category key and language (english/hindi).
    Now loads from database instead of hardcoded config.
    """
    # Load config from database (uses cache)
    config = load_submenu_fallback_config()

    for category, submenu_config in config.items():
        if intent_name in submenu_config["intents"]:
            # Determine language based on intent name
            language = "hindi" if "hindi" in intent_name else "english"
            return category, language

    return None, None


def get_ist_time():
    return datetime.now(IST)


def webhook():
    db = None  # define here so we can safely close it in finally

    try:
        user_message = request.json.get('message')
        sender_id = request.json.get('sender_id', 'default_user')
        chatbot_type = request.json.get('chatbot_type')
        source = request.json.get('source')
        is_menu_visible = request.json.get('is_menu_visible', False)
        user_type_from_payload = request.json.get('type_of_user', None)
        print("User Message:", user_message)
        print("Is Menu Visible:", is_menu_visible)
        print("User Type from Payload:", user_type_from_payload)

        # Send message to Rasa
        rasa_response = requests.post(f"{RASA_API_URL}/webhooks/rest/webhook", json={'sender': sender_id, 'message': user_message})
        rasa_response_json = rasa_response.json()
        print("Rasa Response:", rasa_response_json)

        # if rasa_response_json[0].get("text", "").strip() != "Sorry, I didn’t understand that. Can you rephrase?":
        #     fallback_counts[sender_id] = 0

        print(rasa_response_json and rasa_response_json[0].get("text", "").strip(), "=============== fallback")

        # Fetch record with ID = 1
        fallback = FallbackV.find_one(id=1)

        if fallback:
            initial = fallback.initial_msg
            final = fallback.final_msg

        # Detect fallback
        is_fallback = False
        is_submenu_fallback = False  # Initialize here to use later
        submenu_intent_name = None
        submenu_intent_example = None
        submenu_fallback_language = None
        # if (rasa_response_json and rasa_response_json[0].get("text", "").strip() == "Sorry, I didn't understand that. Can you rephrase?") or rasa_response_json and rasa_response_json[0].get("text", "").strip().startswith("Thanks for reaching out! I'm having trouble understanding your request. Our team is ready to assist:"):
        #     is_fallback = True
        # else:
        #     fallback_counts[sender_id] = 0
        if (rasa_response_json and rasa_response_json[0].get("text", "").strip() == initial) or rasa_response_json and rasa_response_json[0].get("text", "").strip().startswith(final):
            is_fallback = True

            response_intent = requests.post(
                f"{RASA_API_URL}/model/parse",
                json={"text": user_message}
            )

            data = response_intent.json()

            # First intent (same as data["intent"])
            first_intent = data.get("intent_ranking", [None])[0]

            # Second intent
            second_intent = data.get("intent_ranking", [None, None])[1]

            print(first_intent, second_intent, "================================ intent ranking")

            # Check for submenu-specific fallback
            submenu_category = None
            submenu_language = None
            detected_intent = None

            # if first_intent and first_intent["name"] != "nlu_fallback":
            #     # First intent is not fallback, check if it's a submenu intent
            #     detected_intent = first_intent["name"]
            #     submenu_category, submenu_language = get_submenu_category(detected_intent)
            #     print(f"First intent: {detected_intent}, Submenu: {submenu_category}, Language: {submenu_language}")
            # elif second_intent and second_intent["name"] != "nlu_fallback":
            #     # First intent is fallback, check second intent
            #     detected_intent = second_intent["name"]
            #     submenu_category, submenu_language = get_submenu_category(detected_intent)
            #     print(f"Second intent: {detected_intent}, Submenu: {submenu_category}, Language: {submenu_language}")

            # Check if first intent is fallback
            if first_intent["name"] == "nlu_fallback":
                # Only check second intent
                detected_intent = second_intent["name"]
                submenu_category, submenu_language = get_submenu_category(detected_intent)
                print(
                    f"Second intent: {detected_intent}, "
                    f"Submenu: {submenu_category}, "
                    f"Language: {submenu_language}"
                )
            else:
                # Check first intent
                detected_intent = first_intent["name"]
                submenu_category, submenu_language = get_submenu_category(detected_intent)
                print(
                    f"First intent: {detected_intent}, "
                    f"Submenu: {submenu_category}, "
                    f"Language: {submenu_language}"
                )

                # Check second intent as well
                if submenu_category is None and second_intent and second_intent["name"] != "nlu_fallback":
                    detected_intent = second_intent["name"]
                    submenu_category, submenu_language = get_submenu_category(detected_intent)
                    print(
                        f"Second intent: {detected_intent}, "
                        f"Submenu: {submenu_category}, "
                        f"Language: {submenu_language}"
                    )


            # Handle submenu-specific fallback (only if menu is visible)
            submenu_fallback_message = None
            if is_menu_visible and submenu_category and submenu_language:
                print(f"Submenu fallback detected for: {submenu_category} in {submenu_language}")

                # Get submenu-specific messages from database (uses cache)
                submenu_config_all = load_submenu_fallback_config()
                submenu_config = submenu_config_all.get(submenu_category)

                if submenu_config:
                    # Check user type permission
                    allowed_user_types = submenu_config.get("user_type")
                    option = submenu_config.get("option")
                    submenu_fallback_language = submenu_config.get("language")

                    # Validate if user has permission for this submenu
                    if allowed_user_types and user_type_from_payload:
                        # Normalize user_type_from_payload to match stored format
                        # "new" or "new_consumer" -> "new"
                        # "registered" or "registered_consumer" -> "registered"
                        normalized_user_type = user_type_from_payload.replace("_consumer", "")

                        if normalized_user_type not in allowed_user_types:
                            # User doesn't have permission
                            user_type_display = "New Consumer" if normalized_user_type == "new" else "Registered Consumer"

                            if submenu_fallback_language == "English":
                                permission_denied_msg = f"You are a {user_type_display} and you don't have permission to use {option} option."
                            else:
                                permission_denied_msg = f"आप एक {user_type_display} हैं और आपके पास {option} विकल्प का उपयोग करने की अनुमति नहीं है।"
                                
                            # Set the permission denied message
                            initial = permission_denied_msg
                            rasa_response_json = [{"text": permission_denied_msg}]
                            print(f"Permission denied: {user_type_display} not allowed for {submenu_category}")

                            # Skip the rest of submenu fallback logic
                        else:
                            print(f"User type '{normalized_user_type}' is allowed for {submenu_category}")

                            # Redis key for submenu fallback count
                            submenu_redis_key = f"submenu_fallback:{sender_id}:{submenu_category}"

                            # Get current submenu fallback count
                            submenu_attempts = redis_client.get(submenu_redis_key)
                            submenu_attempts = int(submenu_attempts) if submenu_attempts else 0

                            # Increment submenu fallback count
                            pipe = redis_client.pipeline()
                            pipe.incr(submenu_redis_key)
                            if submenu_attempts == 0:  # Set TTL when first attempt starts
                                pipe.expire(submenu_redis_key, 3600)  # 1 hour
                            pipe.execute()

                            submenu_attempts += 1
                            print(f"Submenu fallback count for {submenu_category}: {submenu_attempts}")
                    else:
                        # No user type restriction or no user type from payload, proceed normally
                        print(f"No user type restriction for {submenu_category}, proceeding normally")

                        # Redis key for submenu fallback count
                        submenu_redis_key = f"submenu_fallback:{sender_id}:{submenu_category}"

                        # Get current submenu fallback count
                        submenu_attempts = redis_client.get(submenu_redis_key)
                        submenu_attempts = int(submenu_attempts) if submenu_attempts else 0

                        # Increment submenu fallback count
                        pipe = redis_client.pipeline()
                        pipe.incr(submenu_redis_key)
                        if submenu_attempts == 0:  # Set TTL when first attempt starts
                            pipe.expire(submenu_redis_key, 3600)  # 1 hour
                        pipe.execute()

                        submenu_attempts += 1
                        print(f"Submenu fallback count for {submenu_category}: {submenu_attempts}")

                    # Only continue with fallback message logic if user has permission
                    if allowed_user_types is None or user_type_from_payload is None or normalized_user_type in allowed_user_types:
                        is_submenu_fallback = True
                        # Determine which message to show
                        # Note: Database only stores English messages, language detection is for future use
                        if submenu_attempts >= 3:  # After 3rd attempt (attempts = 3), show final message
                            submenu_fallback_message = submenu_config["final_msg"]
                            redis_client.delete(submenu_redis_key)  # Reset count
                            print(f"Showing final submenu message for {submenu_category} (attempt #{submenu_attempts})")
                        else:
                            submenu_fallback_message = submenu_config["initial_msg"]
                            print(f"Showing initial submenu message for {submenu_category} (attempt #{submenu_attempts})")

                            # Get intent details and first example
                            if detected_intent:
                                db_session = SessionLocal()
                                try:
                                    intent_record = db_session.query(IntentV).filter(IntentV.name == detected_intent).first()
                                    if intent_record:
                                        first_example = db_session.query(IntentExampleV).filter(
                                            IntentExampleV.intent_id == intent_record.id
                                        ).first()

                                        if first_example:
                                            submenu_intent_name = detected_intent
                                            submenu_intent_example = first_example.example
                                            print(f"Stored intent name and example for response")
                                except Exception as e:
                                    print(f"Error fetching intent example: {e}")
                                finally:
                                    db_session.close()

                        # Replace the Rasa response with our custom submenu fallback message
                        initial = submenu_fallback_message
                        rasa_response_json = [{"text": submenu_fallback_message}]
                        print(f"Replaced Rasa response with submenu fallback: {submenu_fallback_message}")
                else:
                    print(f"Warning: No submenu config found for category '{submenu_category}' in database")
            else:
                # Global fallback (menu not visible or no specific submenu detected)
                if not is_menu_visible:
                    print("Global fallback - menu not visible, skipping submenu fallback")
                else:
                    print("Global fallback - no specific submenu detected")
                # Keep the original global fallback message
                # The global fallback will be handled by handle_fallback() function
                # We just keep the initial message as is from the database

        else:
            # Reset fallback count in Redis on successful response
            redis_key = f"fallback_count:{sender_id}"
            redis_client.delete(redis_key)

            # Also reset all submenu fallback counts
            # Get all keys matching the pattern
            submenu_keys = redis_client.keys(f"submenu_fallback:{sender_id}:*")
            if submenu_keys:
                redis_client.delete(*submenu_keys)

        heading = []
        buttons = []
        icons = []
        main_menu_heading = None
        main_menu_buttons = []
        type_of_user = None

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

            # Check for standalone user type text (exact match with lowercase)
            if text.strip() == "new":
                type_of_user = "new"
                continue  # Skip adding this to heading
            elif text.strip() == "registered":
                type_of_user = "registered"
                continue  # Skip adding this to heading

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
        # if len(heading) > 1 and heading[1].strip() == "Sorry, I didn't understand that. Can you rephrase?":
        #     heading.pop(1)

        print(initial, "======================== initial")

        print(fallback.initial_msg, "======================== fallback initial")

        # Only remove duplicate fallback message for GLOBAL fallback, not submenu fallback
        # Submenu fallback messages should be kept in the response
        if len(heading) > 1 and heading[1].strip() == initial and not is_submenu_fallback:
            heading.pop(1)
            print("Removed duplicate global fallback message from heading")
        elif is_submenu_fallback:
            print("Keeping submenu fallback message in heading")


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

        # Add type of user if detected
        if type_of_user:
            response['response']['type_of_user'] = type_of_user

        # Add submenu fallback intent details if available
        if submenu_intent_name:
            response['response']['intent_name'] = submenu_intent_name
        if submenu_intent_example:
            response['response']['intent_example'] = submenu_intent_example
        if submenu_fallback_language:
            response['response']['fallback_language'] = submenu_fallback_language

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
        type_of_user = None

        for item in rasa_response_json:
            text = item.get("text", "")
            lines = text.splitlines()

            # Check for standalone user type text (exact match with lowercase)
            if text.strip() == "new":
                type_of_user = "new"
                continue  # Skip adding this to heading
            elif text.strip() == "registered":
                type_of_user = "registered"
                continue  # Skip adding this to heading

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

        # Add type of user if detected
        if type_of_user:
            response['response']['type_of_user'] = type_of_user

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
    

def run_flow_submenu_fallback():
    try:
        data = request.json
        subsidiary = data.get('subsidiary')
        user = data.get('user', 'New Consumer / नया उपभोक्ता')
        language = data.get('language')
        sender_id = data.get('sender_id', 'default_user')
        user_message = data.get('message')

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

        if language:
            send_to_rasa(language)

        # Step 3: Run 'language' (returns response)
        rasa_response_json = send_to_rasa(user_message)
        print("Rasa Language Response:", rasa_response_json)

        heading = []
        buttons = []
        icons = []
        main_menu_heading = None
        main_menu_buttons = []

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

        if main_menu_heading:
            response['response']['main_menu_heading'] = main_menu_heading

        if main_menu_buttons:
            response['response']['main_menu_buttons'] = main_menu_buttons

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
        type_of_user = None

        for item in rasa_response_json:
            text = item.get("text", "")
            lines = text.splitlines()

            # Check for standalone user type text (exact match with lowercase)
            if text.strip() == "new":
                type_of_user = "new"
                continue  # Skip adding this to heading
            elif text.strip() == "registered":
                type_of_user = "registered"
                continue  # Skip adding this to heading

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

        # Add type of user if detected
        if type_of_user:
            response['response']['type_of_user'] = type_of_user

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
    

def register_run_flow_submenu_fallback():
    try:
        data = request.json
        subsidiary = data.get('subsidiary')
        user = data.get('user', 'Registered Consumer / पंजीकृत उपभोक्ता')
        language = data.get('language')
        ca_number = data.get('ca_number', 'CA VALIDATED BRPL')
        otp = data.get('otp', 'OTP VALIDATED BRPL')
        sender_id = data.get('sender_id', 'default_user')
        user_message = data.get('message')

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

        if language:
            print(send_to_rasa(language))

        # Step 5: Run 'language' (returns response)
        if language == "English BRPL":
            language += " BRPL"
        rasa_response_json = send_to_rasa(user_message)
        print("Rasa Language Response:", rasa_response_json)

        heading = []
        buttons = []
        icons = []
        main_menu_heading = None
        main_menu_buttons = []

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

        if main_menu_heading:
            response['response']['main_menu_heading'] = main_menu_heading

        if main_menu_buttons:
            response['response']['main_menu_buttons'] = main_menu_buttons

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

FALLBACK_LIMIT = 2  # Show final message after 2 consecutive fallbacks (when count > 2)
FALLBACK_WINDOW_SECONDS = 3600  # Reset count after 1 hour of inactivity

def handle_fallback():
    data = request.json
    sender_id = data.get("sender_id")

    if not sender_id:
        return jsonify({"error": "sender_id is required"}), 400

    db = None
    try:
        # Redis key for this sender's fallback count
        redis_key = f"fallback_count:{sender_id}"

        # Get current count from Redis
        attempts = redis_client.get(redis_key)
        attempts = int(attempts) if attempts else 0

        # Increment count in Redis
        pipe = redis_client.pipeline()
        pipe.incr(redis_key)
        if attempts == 0:  # Set TTL when first attempt starts
            pipe.expire(redis_key, FALLBACK_WINDOW_SECONDS)
        pipe.execute()

        # Update attempts to reflect the increment
        attempts += 1

        # Fetch fallback messages from database
        fallback = FallbackV.find_one(id=1)

        if fallback:
            initial = fallback.initial_msg
            final = fallback.final_msg

        # If count exceeds 2 (i.e., 3rd consecutive fallback), send final message
        if attempts > FALLBACK_LIMIT:
            redis_client.delete(redis_key)  # Reset count
            print(f"Fallback count for {sender_id}: {attempts} - EXCEEDED LIMIT, showing final message")
            return jsonify({
                "action": final
            })
        else:
            print(f"Fallback count for {sender_id}: {attempts} - showing initial message")
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

    # Reset fallback count in Redis
    redis_key = f"fallback_count:{sender_id}"
    redis_client.delete(redis_key)
    return jsonify({"message": f"Fallback count reset for {sender_id}"})
