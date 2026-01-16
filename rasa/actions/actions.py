# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, UserUtteranceReverted, EventType
from rasa_sdk.events import Restarted, ConversationPaused
import requests
from rasa_sdk.interfaces import Tracker
from typing import Any, Text, Dict, List
from dotenv import load_dotenv
import os
from Model.session_model import Session
from utils.helper import API_GetMeterReadingSchedule, area_outage, complaint_status, get_bill_history, get_order_status, get_outlet_data, get_payment_history, get_pdf_bill, insert_mobapp_data, register_ncc, registration_ebill, send_otp, update_email_in_db, update_missing_email, validate_ca, validate_mobile

# Load .env file
load_dotenv()

# FLASK_BASE_URL = "http://192.168.20.47:3000"  
FLASK_BASE_URL = os.getenv("BACKEND_URL")  
# FLASK_BASE_URL = f"{os.getenv('BASE_URL')}:{os.getenv('BACKEND_PORT')}"


def send_dynamic_messages(dispatcher, action_name, message_type, lang="en"):
    """
    Fetches utter messages dynamically from backend using action_name and language.
    """
    try:
        api_url = f"{FLASK_BASE_URL}/get_utter_messages?message_type={message_type}&lang={lang}"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        print(data, "================ send")

        # Extract data from the correct key
        messages_data = data.get("data", [])
        if not messages_data:
            dispatcher.utter_message(text="No messages found for this action.")
            return

        # Loop through each message and utter the text
        for msg in messages_data:
            text = msg.get("text")
            if text:
                dispatcher.utter_message(text=text)
    except Exception as e:
        dispatcher.utter_message(text=f"Unable to fetch messages for {action_name}. Error: {str(e)}")


def send_dynamic_messages_without_dispatcher(action_name, message_type, lang="en"):
    """
    Fetches a single utter message dynamically from backend using action_name and language.
    Returns the message text or a default message if none found.
    """
    try:
        api_url = f"{FLASK_BASE_URL}/get_utter_messages?message_type={message_type}&lang={lang}"
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Extract the first message from the 'data' key
        messages_data = data.get("data", [])
        
        if not messages_data:
            return "No messages found for this action."

        # Return the text of the first message
        first_message = messages_data[0]
        return first_message.get("text", "Message text not found.")

    except Exception as e:
        return f"Unable to fetch messages for {action_name}. Error: {str(e)}"
    


class SetLanguage(Action):
    def name(self) -> Text:
        return "action_set_language"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        lang = tracker.latest_message['intent'].get('name')
        if lang == "language_hindi_rajdhani":
            return [SlotSet("language", "hi")]
        elif lang == "language_english_rajdhani":
            return [SlotSet("language", "en")]
        if lang == "language_hindi_yamuna":
            return [SlotSet("language", "hi")]
        elif lang == "language_english_yamuna":
            return [SlotSet("language", "en")]
        return []
    
class ActionSetSubsidiary(Action):
    def name(self):
        return "action_set_subsidiary"

    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get("text", "").lower()
        print(text, "================= subsidiary text")
        if "yamuna" in text:
            return [SlotSet("subsidiary", "BSES Yamuna")]
        elif "rajdhani" or "raj" in text:
            return [SlotSet("subsidiary", "BSES Rajdhani")]
        else:
            dispatcher.utter_message(text="Please specify whether you're from Yamuna or Rajdhani.")
            return []

class ActionSetUser(Action):
    def name(self):
        return "action_set_user"

    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get("text", "").lower()

        if text:
            return [SlotSet("customer_type", "user")]
        # if "registered" or "register" in text:
        #     return [SlotSet("customer_type", "registered")]
        # elif "new" in text:
        #     return [SlotSet("customer_type", "new")]
        # else:
        #     dispatcher.utter_message(text="Please specify whether you're New consumer or Registered consumer")
        #     return []

class ActionSetNewUser(Action):
    def name(self):
        return "action_set_new_user"

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("customer_type", "new")]
    
class Subsidiary_type_english(Action):
    def name(self) -> Text:
        return "action_subsidiary"
    
    def run(self, dispatcher, tracker, domain):
        # print("Tracker state:", tracker.current_state())
        print(f"Sender ID: {tracker.sender_id}")
        dispatcher.utter_message(text="Please select user type")
        dispatcher.utter_message(text="कृपया उपयोगकर्ता प्रकार चुनें")
        dispatcher.utter_message(text="New Consumer / नया उपभोक्ता b")
        dispatcher.utter_message(text="Registered Consumer / पंजीकृत उपभोक्ता b")
        return []
    
# class Language_type(Action):
#     def name(self) -> Text:
#         return "action_language"
    
#     def run(self, dispatcher, tracker, domain)

#         dispatcher.utter_message(text='''Please select your language

# कृपया अपनी भाषा चुनें''')
#         dispatcher.utter_message(text="English b")
#         dispatcher.utter_message(text="हिंदी b")
#         return []

class Language_type(Action):
    def name(self) -> Text:
        return "action_language"
    
    def run(self, dispatcher, tracker, domain):
        try:
            # Fetch visible languages from your Flask API
            response = requests.get(f"{FLASK_BASE_URL}/visible-languages")
            data = response.json()

            # Send the initial message
            dispatcher.utter_message(text='''Please select your language

    कृपया अपनी भाषा चुनें''')

            # Check if data exists and contains languages
            if data.get("status") and "data" in data:
                languages = data["data"]
                if languages:
                    for lang in languages:
                        # Add 'b' after each language name
                        dispatcher.utter_message(text=f"{lang['name']} b")
                else:
                    dispatcher.utter_message(text="No visible languages found.")
            else:
                dispatcher.utter_message(text="Unable to fetch languages at this time.")
            return[]
        except Exception as e:
            print(f"Error fetching visible languages: {e}")
            dispatcher.utter_message(text="Something went wrong while fetching languages.")


class Customer_type_english(Action):
    def name(self) -> Text:
        return "action_customer_type_english"
    
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Please select an option to move ahead.")
        dispatcher.utter_message(text="New Consumer")
        dispatcher.utter_message(text="Registerd Consumer")
        return []
    
class Customer_type_hindi(Action):
    def name(self) -> Text:
        return "action_customer_type_hindi"
    
    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="कृपया आगे बढ़ने के लिए एक विकल्प चुनें।")
        dispatcher.utter_message(text="नया उपभोक्ता")
        dispatcher.utter_message(text="पंजीकृत उपभोक्ता")
        return []
    
    
### Dynamic options according to the choice

## Registered Consumer Options
# class Register_consumer_options_english(Action):
#     def name(self):
#         return "action_register_consumer_options_english"

#     def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="Language has been changed successfully")
#         dispatcher.utter_message(text="Hello! I'm e-MITRA, your BSES Rajdhani assistant.")
#         dispatcher.utter_message(text="Please select an option to continue. (You can click the Home icon or type 'Menu' or 'Hi' anytime to return to the main menu)")
#         dispatcher.utter_message(text=f"""1. Meter & Connection Services b 
# Meter Reading Schedule b 
# New Connection Application b  
# New Connection Status b
# Prepaid Meter - Check Balance / Recharge b
# Consumption History b

# 2. Billing & Payment Services b
# Duplicate Bill b
# Payment Status b 
# Payment History b 
# Bill History b                               
# Opt for e-bill b  

# 3. Complaints & Support Services b
# Register Complaint b 
# Complaint Status (NCC) b 
# Streetlight Complaint b
# Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL) b

# 4. Accessibility & Language Preference b
# Visually Impaired b
# Select Another CA number b  
# Change Language b

# 5. Location & FAQ Services: b 
# FAQs b 
# Branches Nearby b    
                                                                                                 

# {FLASK_BASE_URL}/view-icon/Registered_Consumers/meter-connection-service.svg i
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/meter-reading-schedule.svg i  
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/new-connection-application.svg i
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/new-connection-status.svg i 
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/prepaid-meter-check%E2%80%A8-balance-recharge.svg i
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/consumption-history.svg i 
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/billing-&-payment-services.svg i
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/duplicate-bill.svg i  
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/payment-status.svg i 
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/payment-his.svg i
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/payment-history.svg i
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/opt-in-for-paperless-bill.svg i                                
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/complaints-&-support-services.svg i                              
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/register-complaint.svg i                              
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/complaint-status-(NCC).svg i                              
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/streetlight-complaint.svg i                              
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/virtual-help-desk.svg i                                                           
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/accessibility-&-language-preference.svg i                              
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/visually-impaired.svg i                              
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/check-for-another-CA-number.svg i                              
# {FLASK_BASE_URL}/view-icon/Registered_Consumers/change-language.svg i   
# {FLASK_BASE_URL}/view-icon/New_Consumers/location-&-FAQ-services.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/faqs.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/branches-nearby.svg i                                                                 
                                 
#                                  """)
#         return []



import requests
from rasa_sdk import Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.interfaces import Tracker
from typing import Any, Text, Dict, List

class Register_consumer_options_english(Action):
    def name(self) -> Text:
        return "action_register_consumer_options_english"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        user_id = 2  # Later from tracker slot
        api_url = f"{FLASK_BASE_URL}/get_user_menus?user_id={user_id}"



        try:
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            menus = data.get("menus", [])
            if not menus:
                dispatcher.utter_message(text="No menu data available right now.")
                return []

            # --- Intro messages ---
            # dispatcher.utter_message(text="Language has been changed successfully")
            # dispatcher.utter_message(text="Hello! I'm e-MITRA, your BSES Rajdhani assistant.")
            # dispatcher.utter_message(
            #     text="Please select an option to continue. (You can click the Home icon or type 'Menu' or 'Hi' anytime to return to the main menu)"
            # )

            send_dynamic_messages(dispatcher, "", "intro", lang="en")

            text_lines = []

            # --- Build text dynamically from API response ---
            for idx, menu in enumerate(sorted(menus, key=lambda m: m.get("menu_sequence", 0)), start=1):
                if not menu.get("is_visible"):
                    continue

                # MENU label and icon
                menu_name = menu.get("name", "").strip()
                menu_icon = f"{FLASK_BASE_URL}/{menu.get('icon_path', '').strip()}"
                text_lines.append(f"{idx}. {menu_name} b")
                text_lines.append(f"{menu_icon} i")

                # SUBMENUS
                # --- Sort submenus by submenu_sequence ---
                submenus_data = menu.get("submenus", [])
                submenus = sorted(
                    [sm for sm in submenus_data if sm.get("is_visible")],
                    key=lambda sm: sm.get("submenu_sequence", 0)
                )

                print(submenus, "=================================================== submenus eng")
                for submenu in submenus:
                    if submenu.get("is_visible"):
                        sub_name = submenu.get("name", "").strip()
                        sub_icon = f"{FLASK_BASE_URL}/{submenu.get('icon_path', '').strip()}"
                        text_lines.append(f"{sub_name} b")
                        text_lines.append(f"{sub_icon} i")

                text_lines.append("")  # Blank line between menus

            # --- Final combined text ---
            final_text = "\n".join(text_lines)
            print(final_text, "=================================================== dynamic register eng")

            dispatcher.utter_message(text=final_text)

        except Exception as e:
            dispatcher.utter_message(
                text=f"Sorry, I'm unable to load menu options right now.\nError: {str(e)}"
            )

        return []


class Register_consumer_options_hindi(Action):
    def name(self) -> Text:
        return "action_register_consumer_options_hindi"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_id = 4  # Later from tracker.get_slot("user_id")
        api_url = f"{FLASK_BASE_URL}/get_user_menus?user_id={user_id}"

        try:
            # --- Fetch menu data dynamically from Flask API ---
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            menus = data.get("menus", [])
            if not menus:
                dispatcher.utter_message(text="इस समय कोई मेनू डेटा उपलब्ध नहीं है।")
                return []

            # --- Intro messages ---
            # dispatcher.utter_message(text="भाषा सफलतापूर्वक बदल दी गई है")
            # dispatcher.utter_message(text="नमस्ते! मैं आपका बीएसईएस राजधानी सहायक ई-मित्र हूं।")
            # dispatcher.utter_message(
            #     text="कृपया जारी रखने के लिए एक विकल्प चुनें। (मुख्य मेनू पर लौटने के लिए आप किसी भी समय होम आइकन पर क्लिक कर सकते हैं या 'मेनू' या 'हाय' टाइप कर सकते हैं)"
            # )

            send_dynamic_messages(dispatcher, "", "intro", lang="hi")

            text_lines = []

            # --- Build Hindi menu and submenu list dynamically ---
            for idx, menu in enumerate(sorted(menus, key=lambda m: m.get("menu_sequence", 0)), start=1):
                if not menu.get("is_visible"):
                    continue

                # MENU: name + icon
                menu_name = menu.get("name", "").strip()
                menu_icon = f"{FLASK_BASE_URL}/{menu.get('icon_path', '').strip()}"
                text_lines.append(f"{idx}. {menu_name} b")
                text_lines.append(f"{menu_icon} i")

                # SUBMENUS
                submenus = menu.get("submenus", [])
                for submenu in submenus:
                    if submenu.get("is_visible"):
                        sub_name = submenu.get("name", "").strip()
                        sub_icon = f"{FLASK_BASE_URL}/{submenu.get('icon_path', '').strip()}"
                        text_lines.append(f"{sub_name} b")
                        text_lines.append(f"{sub_icon} i")

                text_lines.append("")  # blank line between menus

            final_text = "\n".join(text_lines)
            print(final_text, "=================================================== dynamic (Hindi)")

            dispatcher.utter_message(text=final_text)

        except Exception as e:
            dispatcher.utter_message(text=f"माफ़ करें, मैं अभी मेनू विकल्प लोड नहीं कर पा रहा हूँ।\nत्रुटि: {str(e)}")

        return []

    

## New Consumer Options

class New_consumer_options_english(Action):
    def name(self) -> Text:
        return "action_new_consumer_options_english"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_id = 6  # Later can be dynamic from tracker.get_slot("user_id")
        api_url = f"{FLASK_BASE_URL}/get_user_menus?user_id={user_id}"

        try:
            # --- Fetch menu data from Flask API ---
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            menus = data.get("menus", [])
            if not menus:
                dispatcher.utter_message(text="No menu data available right now.")
                return []

            # --- Intro messages ---
            # dispatcher.utter_message(text="Language has been changed successfully")
            # dispatcher.utter_message(text="Hello! I'm e-MITRA, your BSES Rajdhani assistant.")
            # dispatcher.utter_message(
            #     text="Please select an option to continue. (You can click the Home icon or type 'Menu' or 'Hi' anytime to return to the main menu)"
            # )

            send_dynamic_messages(dispatcher, "", "intro", lang="en")

            # --- Build dynamic text for menus and submenus ---
            text_lines = []

            for idx, menu in enumerate(sorted(menus, key=lambda m: m.get("menu_sequence", 0)), start=1):
                if not menu.get("is_visible"):
                    continue

                # Menu name and icon
                menu_name = menu.get("name", "").strip()
                menu_icon = f"{FLASK_BASE_URL}/{menu.get('icon_path', '').strip()}"
                text_lines.append(f"{idx}. {menu_name} b")
                text_lines.append(f"{menu_icon} i")

                # Submenus
                # --- Sort submenus by submenu_sequence ---
                submenus_data = menu.get("submenus", [])
                submenus = sorted(
                    [sm for sm in submenus_data if sm.get("is_visible")],
                    key=lambda sm: sm.get("submenu_sequence", 0)
                )

                print(submenus, "=================================================== submenus eng")

                for submenu in submenus:
                    if submenu.get("is_visible"):
                        sub_name = submenu.get("name", "").strip()
                        sub_icon = f"{FLASK_BASE_URL}/{submenu.get('icon_path', '').strip()}"
                        text_lines.append(f"{sub_name} b")
                        text_lines.append(f"{sub_icon} i")

                text_lines.append("")  # blank line between menus

            # --- Combine final text ---
            final_text = "\n".join(text_lines)
            print(final_text, "=================================================== dynamic (New Consumer English)")

            dispatcher.utter_message(text=final_text)

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I'm unable to load menu options right now.\nError: {str(e)}")

        return []




# class New_consumer_options_hindi(Action):
#     def name(self):
#         return "action_new_consumer_options_hindi"

#     def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="भाषा सफलतापूर्वक बदल दी गई है")
#         dispatcher.utter_message(text="नमस्ते! मैं आपका बीएसईएस राजधानी सहायक ई-मित्र हूं।")
#         dispatcher.utter_message(text="कृपया जारी रखने के लिए एक विकल्प चुनें. (मुख्य मेनू पर लौटने के लिए आप किसी भी समय होम आइकन पर क्लिक कर सकते हैं या 'मेनू' या 'हाय' टाइप कर सकते हैं)")
#         dispatcher.utter_message(text=f"""1. मीटर और कनेक्शन सेवाएं b 
# नया कनेक्शन आवेदन b
# नए कनेक्शन की स्थिति b 

# 2. शिकायत और सहायता सेवाएं b
# वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL) b
# स्ट्रीटलाइट शिकायत b 

# 3. स्थान और सामान्य प्रश्न सेवाएं b
# सामान्य प्रश्न (FAQs) b 
# नज़दीकी शाखाएँ b

# 4. सुलभता सेवा और भाषा चुनें b
# दृष्टिबाधित सहायता b 
# कोई और सीए नंबर चुनें b
# भाषा बदलें b
                                 
                                
# {FLASK_BASE_URL}/view-icon/New_Consumers/meter-&-connection-service.svg i
# {FLASK_BASE_URL}/view-icon/New_Consumers/new-connection-application.svg i
# {FLASK_BASE_URL}/view-icon/New_Consumers/new-connection-status.svg i                                                                                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/complaints-&-support-services.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/virtual-help-desk.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/streetlight-complaint.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/location-&-FAQ-services.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/faqs.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/branches-nearby.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/accessibility-&-language-preference.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/visually-impaired.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/check-for-another-CA-number.svg i                              
# {FLASK_BASE_URL}/view-icon/New_Consumers/change-language.svg i                                    
#                                                                   """)
#         return []


class New_consumer_options_hindi(Action):
    def name(self) -> Text:
        return "action_new_consumer_options_hindi"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_id = 8  # Later can be dynamic using tracker.get_slot("user_id")
        api_url = f"{FLASK_BASE_URL}/get_user_menus?user_id={user_id}"

        try:
            # --- Fetch menu data from Flask API ---
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            data = response.json()

            menus = data.get("menus", [])
            if not menus:
                dispatcher.utter_message(text="इस समय कोई मेनू डेटा उपलब्ध नहीं है।")
                return []

            # --- Intro messages ---
            # dispatcher.utter_message(text="भाषा सफलतापूर्वक बदल दी गई है")
            # dispatcher.utter_message(text="नमस्ते! मैं आपका बीएसईएस राजधानी सहायक ई-मित्र हूं।")
            # dispatcher.utter_message(
            #     text="कृपया जारी रखने के लिए एक विकल्प चुनें। (मुख्य मेनू पर लौटने के लिए आप किसी भी समय होम आइकन पर क्लिक कर सकते हैं या 'मेनू' या 'हाय' टाइप कर सकते हैं)"
            # )

            send_dynamic_messages(dispatcher, "", "intro", lang="hi")

            # --- Build dynamic Hindi menu text and icons ---
            text_lines = []

            for idx, menu in enumerate(sorted(menus, key=lambda m: m.get("menu_sequence", 0)), start=1):
                if not menu.get("is_visible"):
                    continue

                # Menu name and icon
                menu_name = menu.get("name", "").strip()
                menu_icon = f"{FLASK_BASE_URL}/{menu.get('icon_path', '').strip()}"
                text_lines.append(f"{idx}. {menu_name} b")
                text_lines.append(f"{menu_icon} i")

                # Submenus
                submenus = menu.get("submenus", [])
                for submenu in submenus:
                    if submenu.get("is_visible"):
                        sub_name = submenu.get("name", "").strip()
                        sub_icon = f"{FLASK_BASE_URL}/{submenu.get('icon_path', '').strip()}"
                        text_lines.append(f"{sub_name} b")
                        text_lines.append(f"{sub_icon} i")

                text_lines.append("")  # Blank line between menus

            # --- Combine into final message ---
            final_text = "\n".join(text_lines)
            print(final_text, "=================================================== dynamic (New Consumer Hindi)")

            dispatcher.utter_message(text=final_text)

        except Exception as e:
            dispatcher.utter_message(
                text=f"माफ़ करें, मैं अभी मेनू विकल्प लोड नहीं कर पा रहा हूँ।\nत्रुटि: {str(e)}"
            )

        return []




class New_Connection_Application_BRPL_english(Action):
    def name(self):
        return "action_new_connection_application_brpl_english"

    def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="""Please click below to apply online or request for an appointment:

# https://ncbrpl.bsesdelhi.com/BRPL/Login
# """)
        send_dynamic_messages(dispatcher, "", "new_connection_application", lang="en")
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
    
class New_Connection_Application_BYPL_english(Action):
    def name(self):
        return "action_new_connection_application_bypl_english"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="""Please click below to apply online or request for an appointment:

https://ncbypl.bsesdelhi.com/BYPL/Login
""")
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")

        return [Restarted()]
    
class New_Connection_Application_BRPL_hindi(Action):
    def name(self):
        return "action_new_connection_application_brpl_hindi"

    def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="""नए कनेक्शन के ऑनलाइन आवेदन या अपॉइंटमेंट करने के लिए कृपया नीचे क्लिक करें:

# https://ncbrpl.bsesdelhi.com/BRPL/Login
# """)
        send_dynamic_messages(dispatcher, "", "new_connection_application", lang="hi")
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")

        return [Restarted()]
    
class New_Connection_Application_BYPL_hindi(Action):
    def name(self):
        return "action_new_connection_application_bypl_hindi"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="""नए कनेक्शन के ऑनलाइन आवेदन या अपॉइंटमेंट  करने के लिए कृपया नीचे क्लिक करें:

https://ncbypl.bsesdelhi.com/BYPL/Login
""")
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")

        return [Restarted()]

    
class Virtual_Customer_Care_BYPL_english(Action):
    def name(self):
        return "action_virtual_customer_care_bypl_english"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="""Please click the link below to connect virtually with our customer care representative:

https://byplws1.bsesdelhi.com:7096/Home/Index
""")
        
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")

        return [Restarted()]
    
class Virtual_Customer_Care_BRPL_english(Action):
    def name(self):
        return "action_virtual_customer_care_brpl_english"

    def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="""Please click the link below to connect virtually with our customer care representative:

# https://bsesbrpl.co.in:7874/zoom/
# """)

        send_dynamic_messages(dispatcher, "", "virtually_connect", lang="en")  
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")

        return [Restarted()]
    

class Virtual_Customer_Care_BYPL_hindi(Action):
    def name(self):
        return "action_virtual_customer_care_bypl_hindi"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="""कृपया हमारे ग्राहक सेवा प्रतिनिधि से वर्चुअली जुड़ने के लिए नीचे दिए गए लिंक पर क्लिक करें:
                                 
https://byplws1.bsesdelhi.com:7096/Home/Index
""")
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")

        return [Restarted()]
    
# class Virtual_Customer_Care_BYPL_hindi(Action):
#     def name(self):
#         return "action_virtual_customer_care_bypl_hindi"

#     def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="""कृपया लॉन्च करने के लिए इसे क्लिक करें:

# Link to BYPL Virtual Customer Care Centre Link:
# https://byplws1.bsesdelhi.com:7096/Home/Index
# """)
#         return [Restarted()]
    
class Virtual_Customer_Care_BYPL_hindi(Action):
    def name(self):
        return "action_virtual_customer_care_brpl_hindi"

    def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="""कृपया हमारे ग्राहक सेवा प्रतिनिधि से वर्चुअली जुड़ने के लिए नीचे दिए गए लिंक पर क्लिक करें:
                                 
# https://bsesbrpl.co.in:7874/zoom/
# """)
        send_dynamic_messages(dispatcher, "", "virtually_connect", lang="hi")
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]



class Prepaid_Meter_Recharge_english(Action):
    def name(self):
        return "action_prepaid_meter_recharge_english"

    def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="""Please click the link below check the balance or to recharge  your prepaid meter:

# https://www.bsesdelhi.com/web/brpl/prepaid-meter-recharge
# """)
        send_dynamic_messages(dispatcher, "", "prepaid_meter_recharge", lang="en")
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
    
class Prepaid_Meter_Recharge_hindi(Action):
    def name(self):
        return "action_prepaid_meter_recharge_hindi"

    def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text="""कृपया शेष राशि देखने या अपने प्रीपेड मीटर को रिचार्ज करने के लिए नीचे दिए गए लिंक पर क्लिक करें:  

# https://www.bsesdelhi.com/web/brpl/prepaid-meter-recharge
# """)
        send_dynamic_messages(dispatcher, "", "prepaid_meter_recharge", lang="hi")
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]
    
    

class ActionRestartConversation(Action):
    def name(self):
        return "action_restart_conversation"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Conversation restarted. How can I help you again?")
        return [Restarted()]
    

## Register user authentication 

class ActionValidateCANumber(Action):
    def name(self):
        print("action_validate_ca_number=========================================")
        return "action_validate_ca_number"

    def run(self, dispatcher, tracker, domain):
        ca_number = tracker.latest_message.get('text')
        sender_id = tracker.sender_id
        print(ca_number, "========================= ca number")

        if ca_number == "CA VALIDATED BRPL" or ca_number == "CA VALIDATED BYPL":
            dispatcher.utter_message(text="CA number is being processed.")
            return [SlotSet("ca_number", None)]
        
        if ca_number == "ca verified BRPL" or ca_number == "CA VERIFIED BRPL":
            dispatcher.utter_message(text="CA number is being processed.")
            return [SlotSet("ca_number", None)]

        # try:
        #     # response = requests.post(f"{FLASK_BASE_URL}/validate_ca", json={"sender_id": sender_id, "ca_number": ca_number})
        #     response = validate_ca(sender_id, ca_number)
        #     print(response, "====================== response")
        #     data = response
        # except Exception as e:
        #     dispatcher.utter_message(text="CA Validation service is unavailable. Please try again later.")
        #     print("Exception:", e)
        #     return [SlotSet("ca_number", ca_number)]


        # print(data, "================================= data")

        # try:
        #     if data.get("valid") == True:
        #         dispatcher.utter_message(text="CA number is being processed.")
        #         return [SlotSet("ca_number", None)]
            
        #     else:
        #         dispatcher.utter_message(text="Please enter a valid CA number.")
        #         return [
        #             SlotSet("ca_number", ca_number)                
        #         ]
                
        # except Exception as e:
        #     dispatcher.utter_message(text="Error validating CA number. Please try again later.")
        #     print("Exception:", e)
        #     return [SlotSet("ca_number", ca_number)]


# class ActionValidateCANumber(Action):
#     def name(self):
#         print("action_validate_ca_number=========================================")
#         return "action_validate_ca_number"

#     def run(self, dispatcher, tracker, domain):
#         ca_number = tracker.latest_message.get('text')
#         sender_id = tracker.sender_id
#         retry_count = tracker.get_slot("retry_count") or 0
#         print(ca_number, "========================= ca number")

#         if ca_number == "CA VALIDATED BRPL" or ca_number == "CA VALIDATED BYPL":
#             dispatcher.utter_message(text="CA number is being processed.")
#             return [SlotSet("ca_number", None)]

#         try:
#             response = requests.post(f"{FLASK_BASE_URL}/validate_ca", json={"sender_id": sender_id, "ca_number": ca_number})
#             data = response.json()
#         except Exception as e:
#             dispatcher.utter_message(text="CA Validation service is unavailable. Please try again later.")
#             print("Exception:", e)
#             return [SlotSet("ca_number", ca_number)]


#         print(data, "================================= data")

#         try:
#             if data.get("valid") == True:
#                 dispatcher.utter_message(text="CA number is being processed.")
#                 return [SlotSet("ca_number", None)]
            
#             else:
#                 retry_count += 1

#                 if data.get('exceeded') == True:
#                     dispatcher.utter_message(text="Too many attempts. Let's start over. Click home button to start over")
#                     return [SlotSet("retry_count", 0), Restarted()]
                
#                 else:
#                     dispatcher.utter_message(text="Please enter a valid CA Number. Retries left: " + str(data.get("retries_left")))
#                     return [
#                         SlotSet("ca_number", ca_number), 
#                         SlotSet("retry_count", retry_count)                
#                     ]
                
#         except Exception as e:
#             dispatcher.utter_message(text="Error validating CA number. Please try again later.")
#             print("Exception:", e)
#             return [SlotSet("ca_number", ca_number)]

class ActionValidateCANumberHindi(Action):
    def name(self):
        print("action_validate_ca_number_hindi =========================================")
        return "action_select_another_ca_number_validate_hindi"

    def run(self, dispatcher, tracker, domain):
        ca_number = tracker.latest_message.get('text')
        sender_id = tracker.sender_id
        print(ca_number, "========================= ca number")

        if ca_number == "CA VALIDATED BRPL" or ca_number == "CA VALIDATED BYPL":
            dispatcher.utter_message(text="आपका सीए नंबर सफलतापूर्वक सत्यापित हो गया है।")
            return [SlotSet("ca_number", None)]
        
        if ca_number == "ca verified BRPL" or ca_number == "CA VERIFIED BRPL":
            dispatcher.utter_message(text="CA नंबर प्रक्रिया में है।")
            dispatcher.utter_message(text="एक 6-अंकों का वन-टाइम पासवर्ड (OTP) आपके पंजीकृत मोबाइल नंबर पर भेजा गया है।")
            dispatcher.utter_message(text="कृपया आगे बढ़ने के लिए इसे दर्ज करें।")
            return [SlotSet("ca_number", None)]


# class ActionValidateCANumberHindi(Action):
#     def name(self):
#         print("action_validate_ca_number_hindi =========================================")
#         return "action_select_another_ca_number_validate_hindi"

#     def run(self, dispatcher, tracker, domain):
#         ca_number = tracker.latest_message.get('text')
#         sender_id = tracker.sender_id
#         print(ca_number, "========================= CA नंबर")

#         if ca_number == "CA VALIDATED BRPL" or ca_number == "CA VALIDATED BYPL":
#             dispatcher.utter_message(text="आपका सीए नंबर सफलतापूर्वक सत्यापित हो गया है।")
#             return [SlotSet("ca_number", None)]

#         try:
#             # response = requests.post(f"{FLASK_BASE_URL}/validate_ca", json={"sender_id": sender_id, "ca_number": ca_number})
#             # data = response.json()
#             response = validate_ca(sender_id, ca_number)
#             print(response, "====================== response")
#             data = response
#         except Exception as e:
#             dispatcher.utter_message(text="CA नंबर सत्यापित करते समय त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।")
#             print("Exception:", e)
#             return [SlotSet("ca_number", None)]

#         print(data, "================================= डेटा")

#         try:
#             if data.get("valid") == True:

#                 # response = requests.post(f"{FLASK_BASE_URL}/send_otp", json={"sender_id": sender_id})
#                 # otp_data = response.json()
#                 otp_data = send_otp(sender_id)

#                 if otp_data.get("status") == "sent":
#                     dispatcher.utter_message(text="CA नंबर प्रक्रिया में है।")
#                     dispatcher.utter_message(text="एक 6-अंकों का वन-टाइम पासवर्ड (OTP) आपके पंजीकृत मोबाइल नंबर पर भेजा गया है।")
#                     dispatcher.utter_message(text="कृपया आगे बढ़ने के लिए इसे दर्ज करें।")
#                 else:
#                     dispatcher.utter_message(text="OTP भेजने में विफल। कृपया बाद में पुनः प्रयास करें।")
#                 # dispatcher.utter_message(text="CA नंबर सफलतापूर्वक मान्य किया गया।")
#                 # dispatcher.utter_message(text="आपके पंजीकृत मोबाइल नंबर पर एक OTP भेजा गया है।")
#                 # dispatcher.utter_message(text="कृपया 6-अंकों का ओटीपी दर्ज करें।")
#                 return [SlotSet("ca_number", None)]
#             else:
#                 dispatcher.utter_message(text="कृपया एक मान्य CA नंबर दर्ज करें।")
#                 return [SlotSet("ca_number", ca_number)]
#         except Exception as e:
#             dispatcher.utter_message(text="CA नंबर सत्यापित करते समय त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।")
#             print("Exception:", e)
#             return [SlotSet("ca_number", None)]



class ActionSendOTP(Action):
    def name(self):
        return "action_send_otp"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id

        ca_validation = tracker.latest_message.get('text')

        print(f"action_send_otp_123: ", ca_validation)

        if ca_validation == "CA VALIDATED BRPL":
            dispatcher.utter_message(text="A 6-digit One-Time Password (OTP) has been sent to the registered mobile number.")
            return [SlotSet("retry_count", 0)]
        # response = requests.post(f"{FLASK_BASE_URL}/send_otp", json={"sender_id": sender_id})
        # data = response.json()
        data = send_otp(sender_id)

        if data.get("status") == "sent":
            dispatcher.utter_message(text="A 6-digit One-Time Password (OTP) has been sent to the registered mobile number.")
        elif data.get("status") == "rate_limited":
            dispatcher.utter_message(text=f"{data.get('message')}")
            # Stop further story execution here
            return [ConversationPaused()]
        else:
            print("OTP send failed=========================================", data.get("status"))
            dispatcher.utter_message(text="Send OTP service is unavailable. Please try again later.")
            # Stop further story execution here
            return [ConversationPaused()]
        
        return [SlotSet("retry_count", 0)]
    

# class ActionSendOTPHindi(Action):
#     def name(self):
#         return "action_send_otp_hindi"

#     def run(self, dispatcher, tracker, domain):
#         sender_id = tracker.sender_id
#         response = requests.post(f"{FLASK_BASE_URL}/send_otp", json={"sender_id": sender_id})
#         data = response.json()

#         if data.get("status") == "sent":
#             dispatcher.utter_message(text="आपके पंजीकृत मोबाइल नंबर पर एक OTP भेजा गया है।")
#         else:
#             dispatcher.utter_message(text="OTP भेजने में विफल। कृपया बाद में पुनः प्रयास करें।")

#         return [SlotSet("retry_count", 0)]



# class ActionValidateOTP(Action):
#     def name(self):
#         return "action_validate_otp"

#     def run(self, dispatcher, tracker, domain):
#         otp = tracker.latest_message.get('text')
#         ca_number = tracker.get_slot("ca_number")
#         retry_count = tracker.get_slot("retry_count")

#         # Debugging line
#         print("RECEIVED retry_count:", retry_count)

#         if not otp.isdigit() or len(otp) != 6:
#             dispatcher.utter_message(template="utter_wrong_format_otp")
#             return []

#         response = requests.post(f"{FLASK_BASE_URL}/validate_otp", json={"ca_number": ca_number, "otp": otp})
#         data = response.json()

#         if data.get("valid"):
#             dispatcher.utter_message(text="OTP validated successfully.")
#             return [SlotSet("retry_count", 0)]
#         else:
#             retry_count += 1
#             if retry_count >= 3:
#                 dispatcher.utter_message(template="utter_start_over")
#                 return [SlotSet("retry_count", 0)]
#             dispatcher.utter_message(template="utter_invalid_otp")
#             print("Updated retry_count:", retry_count)
#             return [SlotSet("retry_count", retry_count)]

# class ActionValidateOTP(Action):
#     def name(self):
#         return "action_validate_otp"

#     def run(self, dispatcher, tracker, domain) -> list[EventType]:
#         otp = tracker.latest_message.get('text')
#         retry_count = tracker.get_slot("retry_count") or 0
#         sender_id = tracker.sender_id

#         print(f"Sender ID otp: {sender_id}")

#         print(otp, "========================================== register otp")

#         # print("RECEIVED retry_count:", retry_count)
#         # print("SLOTS:", tracker.current_slot_values())

#         # if not otp.isdigit() or len(otp) != 6:
#         #     retry_count += 1
#         #     dispatcher.utter_message(template="utter_wrong_format_otp")
#         #     return [SlotSet("retry_count", retry_count)]

#         if otp == "OTP VALIDATED BRPL" or otp == "OTP VALIDATED BYPL":
#             dispatcher.utter_message(text="OTP validated successfully.")
#             return [SlotSet("retry_count", 0)]

#         # if otp != "VALIDATED":
#         response = requests.post(f"{FLASK_BASE_URL}/validate_otp", json={"otp": otp, "sender_id": sender_id})
#         data = response.json()
#         print(data, "========================= api data")

#         if data.get("valid") or otp == "VALIDATED":
#             dispatcher.utter_message(text="OTP validated successfully.")
#             return [SlotSet("retry_count", 0)]
#         else:
#             retry_count += 1
#             # print("Updated retry_count:", retry_count)
#             if data.get("exceeded") == True:
#                 dispatcher.utter_message(text="Too many attempts. Let's start over. Click home button to start over")
#                 return [SlotSet("retry_count", 0), Restarted()]
#             elif not otp.isdigit() or len(otp) != 6:
#                 # retry_count += 1
#                 dispatcher.utter_message(text="Please enter a valid 6-digit OTP. Retries left: " + str(data.get("retries_left")))
#                 return [SlotSet("retry_count", retry_count)]
#             else:
#                 dispatcher.utter_message(text="That OTP seems incorrect. Please try again. Retries left: " + str(data.get("retries_left")))
#                 return [SlotSet("retry_count", retry_count)]
            

class ActionValidateOTP(Action):
    def name(self):
        return "action_validate_otp"

    def run(self, dispatcher, tracker, domain) -> list[EventType]:
        otp = tracker.latest_message.get('text')

        sender_id = tracker.sender_id

        if otp == "OTP VALIDATED BRPL" or otp == "OTP VALIDATED BYPL":
            dispatcher.utter_message(text="OTP validated successfully.")
            return [SlotSet("retry_count", 0)]

        existing_chat = Session.find_one(user_id=sender_id)

        print(f"Sender ID otp:", existing_chat.otp_is_verified)

        if existing_chat.otp_is_verified == "yes":
            
            if otp == "otp verified BRPL" or otp == "OTP VERIFIED BYPL":
                dispatcher.utter_message(text="OTP validated successfully.")
        else:
            dispatcher.utter_message(text="No existing session found. Please start over.")
            return [ConversationPaused()]




# class ActionValidateOTP_Hindi(Action):
    # def name(self):
    #     return "action_validate_otp_hindi"

    # def run(self, dispatcher, tracker, domain) -> list[EventType]:
    #     otp = tracker.latest_message.get('text')
    #     ca_number = tracker.get_slot("ca_number")
    #     retry_count = tracker.get_slot("retry_count") or 0
    #     sender_id = tracker.sender_id

    #     print(f"Sender ID otp: {sender_id}")
    #     print(otp, "========================================== register otp")

    #     if otp == "VALIDATED":
    #         dispatcher.utter_message(text="ओटीपी सफलतापूर्वक सत्यापित हो गया है।")
    #         return [SlotSet("retry_count", 0)]

    #     response = requests.post(
    #         f"{FLASK_BASE_URL}/validate_otp",
    #         json={"ca_number": 123456789, "otp": otp, "sender_id": sender_id}
    #     )
    #     data = response.json()
    #     print(data, "========================= api data")

    #     if data.get("valid") or otp == "VALIDATED":
    #         dispatcher.utter_message(text="ओटीपी सफलतापूर्वक सत्यापित हो गया है।")
    #         return [SlotSet("retry_count", 0)]
    #     else:
    #         retry_count += 1
    #         if data.get("exceeded") == True:
    #             dispatcher.utter_message(text="आपने बहुत अधिक बार प्रयास किया है। कृपया होम बटन पर क्लिक करके फिर से शुरू करें।")
    #             return [SlotSet("retry_count", 0), Restarted()]
    #         elif not otp.isdigit() or len(otp) != 6:
    #             dispatcher.utter_message(text=f"कृपया मान्य 6-अंकों का ओटीपी दर्ज करें। शेष प्रयास: {data.get('retries_left')}")
    #             return [SlotSet("retry_count", retry_count)]
    #         else:
    #             dispatcher.utter_message(text=f"दर्ज किया गया ओटीपी गलत है। कृपया पुनः प्रयास करें। शेष प्रयास: {data.get('retries_left')}")
    #             return [SlotSet("retry_count", retry_count)]

class ActionValidateOTP_Hindi(Action):
    def name(self):
        return "action_validate_otp_hindi"

    def run(self, dispatcher, tracker, domain) -> list[EventType]:
        otp = tracker.latest_message.get('text')

        print(otp, "========================================== register otp")

        sender_id = tracker.sender_id

        if otp == "OTP VALIDATED BRPL" or otp == "OTP VALIDATED BYPL":
            dispatcher.utter_message(text="ओटीपी सफलतापूर्वक सत्यापित हो गया है।")
            return [SlotSet("retry_count", 0)]

        existing_chat = Session.find_one(user_id=sender_id)


        # if otp == "VALIDATED":
        #     dispatcher.utter_message(text="ओटीपी सफलतापूर्वक सत्यापित हो गया है।")
        #     # return [SlotSet("retry_count", 0)]
        
        # if otp == "otp verified BRPL" or otp == "OTP VERIFIED BYPL":
        #     dispatcher.utter_message(text="ओटीपी सफलतापूर्वक सत्यापित हो गया है।")
        #     # return [SlotSet("retry_count", 0)]

        if existing_chat.otp_is_verified == "yes":
            
            if otp == "otp verified BRPL" or otp == "OTP VERIFIED BYPL":
                dispatcher.utter_message(text="ओटीपी सफलतापूर्वक सत्यापित हो गया है।")
        else:
            dispatcher.utter_message(text="कोई मौजूदा सेशन नहीं मिला। कृपया दोबारा शुरू करें।")
            return [ConversationPaused()]   

## New Connection Status

def extract_order_id(text):
    parts = text.strip().split()
    if parts and parts[0].isdigit():
        return int(parts[0])
    return None

class ActionNewConnectionStatusEnglish(Action):
    def name(self):
        return "action_new_connection_status_english"

    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="Please enter your Order ID. The Order ID starts with ‘8’, ‘AN’, or ‘ON’")
        send_dynamic_messages(dispatcher, "", "new_connection_status_step_1", lang="en")
        return []


def extract_order_number(text):
    # Remove leading symbols and spaces
    cleaned = text.strip().lstrip("-").strip()
    # Remove BRPL or BYPL at the end
    cleaned = re.sub(r"\s+(BRPL|BYPL)$", "", cleaned)
    return cleaned


class ActionGetConnectionStatus(Action):
    def name(self):
        return "action_get_connection_status"

    def run(self, dispatcher, tracker, domain):
        ord_id = tracker.latest_message.get("text")

        print(ord_id, " =============================== action_get_connection_status")

        if ord_id == "order verified BRPL" or ord_id == "ORDER VERIFIED BRPL":
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        


# class ActionGetConnectionStatus(Action):
#     def name(self):
#         return "action_get_connection_status"

#     def run(self, dispatcher, tracker, domain):
#         ord_id = tracker.latest_message.get("text")
#         order_id = extract_order_number(ord_id)

#         print(order_id, " =============================== action_get_connection_status")

#         data = get_order_status(order_id)

#         # response = requests.post(f"{FLASK_BASE_URL}/get_order_status", json={"order_id": order_id})

#         # data = response.json()

#         print(data, "================================= order data")

#         try:
#             if data.get("valid") == True:
#                 # dispatcher.utter_message(text="Here is the Status of your new connection: ")
#                 # send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="en")
#                 # dispatcher.utter_message(text=f"{data.get('order_status')}")

#                 if data.get('order_status') == "Deficiency issued for Technical Feasibility":
#                     TYPE_OF_DEFICIENCY = "BTFR"
#                     # dispatcher.utter_message(text="New connection request on hold due to deficiency")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="en")
#                     dispatcher.utter_message(text=f"Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Auto cancelled":
#                     TYPE_OF_DEFICIENCY = "AC"
#                     # dispatcher.utter_message(text="New connection request on hold due to deficiency")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="en")
#                     dispatcher.utter_message(text=f"Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Document Deficiency issued":
#                     TYPE_OF_DEFICIENCY = "DR"
#                     # dispatcher.utter_message(text="New connection request on hold due to deficiency")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="en")
#                     dispatcher.utter_message(text=f"Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Deficiency issued for Commercial Feasibility":
#                     TYPE_OF_DEFICIENCY = "CFR"
#                     # dispatcher.utter_message(text="New connection request on hold due to deficiency")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="en")
#                     dispatcher.utter_message(text=f"Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Deficiency issued for Commercial Feasibility/Technical Feasibility":
#                     TYPE_OF_DEFICIENCY = "BTFR+CFR"
#                     # dispatcher.utter_message(text="New connection request on hold due to deficiency")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="en")
#                     dispatcher.utter_message(text=f"Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")
                    
#                 #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
#                 send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
#                 dispatcher.utter_message(text="Yes menu b")
#                 dispatcher.utter_message(text="No menu b")
#                 return [SlotSet("order_id", None), Restarted()]
            
#             else:
#                 dispatcher.utter_message(text="The Order ID entered is not valid. Please recheck and try again.")
#                 return [
#                     SlotSet("order_id", order_id)                
#                 ]
                
#         except Exception as e:
#             dispatcher.utter_message(text="Error validating order ID. Please try again later.")
#             print("Exception:", e)
#             return [SlotSet("order_id", order_id), Restarted()]


class ActionUploadDocument(Action):
    def name(self):
        return "action_upload_document"

    def run(self, dispatcher, tracker, domain):
        # Simulated file upload (in real case, handle file upload from frontend)
        order_id = tracker.get_slot("order_id")
        print(order_id, " =============================== action_upload_document")
        response = requests.post(f"{FLASK_BASE_URL}/application/upload-doc", json={"order_id": order_id})

        if response.status_code == 200:
            dispatcher.utter_message(text="Document uploaded successfully.")
        else:
            dispatcher.utter_message(text="Failed to upload document. Please try again.")

        dispatcher.utter_message(text="Thank you! Your application will be processed further.")
        return []
    


class ActionNewConnectionStatusHindi(Action):
    def name(self):
        return "action_new_connection_status_hindi"

    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="कृपया अपना ऑर्डर आईडी दर्ज करें। आपका ऑर्डर आईडी '8', 'AN' या 'ON' से शुरू होता है।")
        send_dynamic_messages(dispatcher, "", "new_connection_status_step_1", lang="hi")
        return []


class ActionGetConnectionStatusHindi(Action):
    def name(self):
        return "action_get_connection_status_hindi"

    def run(self, dispatcher, tracker, domain):
        ord_id = tracker.latest_message.get("text")

        if ord_id == "order verified BRPL" or ord_id == "ORDER VERIFIED BRPL":
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]

# class ActionGetConnectionStatusHindi(Action):
#     def name(self):
#         return "action_get_connection_status_hindi"

#     def run(self, dispatcher, tracker, domain):
#         ord_id = tracker.latest_message.get("text")
#         order_id = extract_order_number(ord_id)

#         print(order_id, " =============================== action_get_connection_status_hindi")

#         data = get_order_status(order_id)

#         # response = requests.post(f"{FLASK_BASE_URL}/get_order_status", json={"order_id": order_id})
#         # data = response.json()

#         print(data, "================================= order data")

#         try:
#             if data.get("valid") == True:
#                 # dispatcher.utter_message(text="आपके नए कनेक्शन अनुरोध की स्थिति है:")
#                 # send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="hi")
#                 # dispatcher.utter_message(text=f"{data.get('order_status')}")

#                 if data.get('order_status') == "Deficiency issued for Technical Feasibility":
#                     TYPE_OF_DEFICIENCY = "BTFR"
#                     # dispatcher.utter_message(text="कमी देखने के लिए यहाँ क्लिक करें")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="hi")
#                     dispatcher.utter_message(text=f"कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Auto cancelled":
#                     TYPE_OF_DEFICIENCY = "AC"
#                     # dispatcher.utter_message(text="कमी देखने के लिए यहाँ क्लिक करें")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="hi")
#                     dispatcher.utter_message(text=f"कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Document Deficiency issued":
#                     TYPE_OF_DEFICIENCY = "DR"
#                     # dispatcher.utter_message(text="कमी देखने के लिए यहाँ क्लिक करें")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="hi")
#                     dispatcher.utter_message(text=f"कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Deficiency issued for Commercial Feasibility":
#                     TYPE_OF_DEFICIENCY = "CFR"
#                     # dispatcher.utter_message(text="कमी देखने के लिए यहाँ क्लिक करें")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="hi")
#                     dispatcher.utter_message(text=f"कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 elif data.get('order_status') == "Deficiency issued for Commercial Feasibility/Technical Feasibility":
#                     TYPE_OF_DEFICIENCY = "BTFR+CFR"
#                     # dispatcher.utter_message(text="कमी देखने के लिए यहाँ क्लिक करें")
#                     send_dynamic_messages(dispatcher, "", "new_connection_status_step_2", lang="hi")
#                     dispatcher.utter_message(text=f"कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_id}&TYPE={TYPE_OF_DEFICIENCY}")

#                 #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
#                 send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
#                 dispatcher.utter_message(text="हाँ menu b")
#                 dispatcher.utter_message(text="नहीं menu b")
#                 return [SlotSet("order_id", None), Restarted()]
#             else:
#                 dispatcher.utter_message(text="आपने जो ऑर्डर आईडी दर्ज की है वह मान्य नहीं है। कृपया दोबारा जांचें और फिर प्रयास करें।")
#                 return [
#                     SlotSet("order_id", order_id)
#                 ]
#         except Exception as e:
#             dispatcher.utter_message(text="ऑर्डर आईडी की पुष्टि करते समय त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।")
#             print("Exception:", e)
#             return [SlotSet("order_id", order_id), Restarted()]


class ActionUploadDocumentHindi(Action):
    def name(self):
        return "action_upload_document_hindi"

    def run(self, dispatcher, tracker, domain):
        # Simulated file upload (in real case, handle file upload from frontend)
        order_id = tracker.get_slot("order_id")
        print(order_id, " =============================== action_upload_document_hindi")
        response = requests.post(f"{FLASK_BASE_URL}/application/upload-doc", json={"order_id": order_id})

        if response.status_code == 200:
            dispatcher.utter_message(text="दस्तावेज़ सफलतापूर्वक अपलोड हो गया है।")
        else:
            dispatcher.utter_message(text="दस्तावेज़ अपलोड करने में विफल रहा। कृपया पुनः प्रयास करें।")

        dispatcher.utter_message(text="धन्यवाद! आपका आवेदन आगे की प्रक्रिया के लिए भेज दिया गया है।")
        return []


## FAQ'S 

class New_consumer_faqs_brpl_english(Action):
    def name(self):
        return "action_new_consumer_faqs_brpl_english"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id

        # Fetch CA number from your database or API
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")

        print(ca, "================ ca number in faq's")

        if not ca:
    #         dispatcher.utter_message(text="""1. Mobile App (Android & iOS) b""")
    #         dispatcher.utter_message(text="""1. BSES Rajdhani Power Limited brings essential services to your fingertips through its official app — BRPL Power App. From bill payments and consumption tracking to complaint registration and account management, access everything in one place. Available on both Google Play and Apple App Store.
    # Click  to download:
    # Google Play Store:  https://rml.fm/BSESRP/vokflp 
    # Apple App Store: https://rml.fm/BSESRP/NEkflp""")

    #         dispatcher.utter_message(text="""2. Quick Pay b""")
    #         dispatcher.utter_message(text="""2. Use Quick Pay to conveniently pay your electricity bill- no login required. Select from multiple secure payment methods such as Net Banking, Debit/Credit Cards, or UPI for a smooth and hassle-free transaction.
    # Click here to pay: https://www.bsesdelhi.com/web/brpl/quick-pay""")
            
    #         dispatcher.utter_message(text="""3. New Connection b""")
    #         dispatcher.utter_message(text="""3. To apply online for a new connection, request an appointment, or view checklist of required documents, please click given below link:
    # https://ncbrpl.bsesdelhi.com/BRPL/Login""")

    #         dispatcher.utter_message(text="""4. Change Request b""")
    #         dispatcher.utter_message(text="""4. To submit a request for changes to your existing connection—such as name change, load change, or category change—please click the link provided below:
    # https://ncbrpl.bsesdelhi.com/BRPL/ChangeRequestLogin""")

            send_dynamic_messages(dispatcher, "", "faqs_new", lang="en")
            
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")

            return [Restarted()]

        else:
            ca_number = extract_ca_number(ca)

            dispatcher.utter_message(text="""1. Mobile App (Android & iOS) b""")
            dispatcher.utter_message(text="""1. BSES Rajdhani Power Limited brings essential services to your fingertips through its official app — BRPL Power App. From bill payments and consumption tracking to complaint registration and account management, access everything in one place. Available on both Google Play and Apple App Store.
    Click  to download:
    Google Play Store:  https://rml.fm/BSESRP/vokflp 
    Apple App Store: https://rml.fm/BSESRP/NEkflp""")

            dispatcher.utter_message(text="""2. Quick Pay b""")
            dispatcher.utter_message(text=f"""2. Use Quick Pay to conveniently pay your electricity bill- no login required. Select from multiple secure payment methods such as Net Banking, Debit/Credit Cards, or UPI for a smooth and hassle-free transaction.
    Click here to pay: https://www.bsesdelhi.com/web/brpl/quick-pay-payment?p_p_id=com_bses_pay_now_portlet_BsesPayNowWebPortlet&p_p_lifecycle=0&_com_bses_pay_now_portlet_BsesPayNowWebPortlet_caNo={ca_number}""")
            
            dispatcher.utter_message(text="""3. New Connection b""")
            dispatcher.utter_message(text="""3. To apply online for a new connection, request an appointment, or view checklist of required documents, please click given below link:
    https://ncbrpl.bsesdelhi.com/BRPL/Login""")

            dispatcher.utter_message(text="""4. Change Request b""")
            dispatcher.utter_message(text="""4. To submit a request for changes to your existing connection—such as name change, load change, or category change—please click the link provided below:
    https://ncbrpl.bsesdelhi.com/BRPL/ChangeRequestLogin""")
            
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")

            return [Restarted()]
    

class New_consumer_faqs_brpl_hindi(Action):
    def name(self):
        return "action_new_consumer_faqs_brpl_hindi"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id

        # Fetch CA number from your database or API
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")

        if not ca:
    #         dispatcher.utter_message(text="""1. मोबाइल ऐप (Android और iOS) b""")
    #         dispatcher.utter_message(text="""1. बीएसईएस राजधानी पावर लिमिटेड अपने आधिकारिक ऐप - बीआरपीएल पावर ऐप के माध्यम से कई सेवाएं प्रदान करता है। बिल भुगतान और बिजली खपत ट्रैकिंग से लेकर शिकायत पंजीकरण और अपना खाता प्रबंधित करने तक, सब कुछ एक ही स्थान पर एक्सेस करें। हमारी ऐप Google Play और Apple App Store दोनों पर उपलब्ध है।
    # डाउनलोड करने के लिए क्लिक करें:
    # गूगल प्ले स्टोर: https://rml.fm/BSESRP/vokflp 
    # ऐप्पल ऐप स्टोर: https://rml.fm/BSESRP/NEkflp""")

    #         dispatcher.utter_message(text="""2. क्विक पे b""")
    #         dispatcher.utter_message(text="""2. अपने बिजली बिल का आसानी से भुगतान करने के लिए क्विक पे करें - किसी लॉगिन की आवश्यकता नहीं है।  नेट बैंकिंग, डेबिट/क्रेडिट कार्ड या यूपीआई जैसे कई सुरक्षित भुगतानों में से चुनें।
    # भुगतान करने के लिए यहां क्लिक करें: https://www.bsesdelhi.com/web/brpl/quick-pay""")

    #         dispatcher.utter_message(text="""3. नया कनेक्शन b""")
    #         dispatcher.utter_message(text="""3. नए कनेक्शन के लिए ऑनलाइन आवेदन करने, अपॉइंटमेंट का अनुरोध करने या आवश्यक दस्तावेजों की चेकलिस्ट देखने के लिए कृपया नीचे दिए गए लिंक पर क्लिक करें:
    # https://ncbrpl.bsesdelhi.com/BRPL/Login""")

    #         dispatcher.utter_message(text="""4. कनेक्शन परिवर्तन अनुरोध b""")
    #         dispatcher.utter_message(text="""4. अपने मौजूदा कनेक्शन में परिवर्तन के लिए अनुरोध सबमिट करने के लिए - जैसे नाम परिवर्तन, लोड परिवर्तन, या श्रेणी परिवर्तन - कृपया नीचे दिए गए लिंक पर क्लिक करें:
    # https://ncbrpl.bsesdelhi.com/BRPL/ChangeRequestLogin""")

            send_dynamic_messages(dispatcher, "", "faqs_new", lang="hi")
            
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")

            return [Restarted()]

        else:
            ca_number = extract_ca_number(ca)

            dispatcher.utter_message(text="""1. मोबाइल ऐप (Android और iOS) b""")
            dispatcher.utter_message(text="""1. बीएसईएस राजधानी पावर लिमिटेड अपने आधिकारिक ऐप - बीआरपीएल पावर ऐप के माध्यम से कई सेवाएं प्रदान करता है। बिल भुगतान और बिजली खपत ट्रैकिंग से लेकर शिकायत पंजीकरण और अपना खाता प्रबंधित करने तक, सब कुछ एक ही स्थान पर एक्सेस करें। हमारी ऐप Google Play और Apple App Store दोनों पर उपलब्ध है।
    डाउनलोड करने के लिए क्लिक करें:
    गूगल प्ले स्टोर: https://rml.fm/BSESRP/vokflp 
    ऐप्पल ऐप स्टोर: https://rml.fm/BSESRP/NEkflp""")

            dispatcher.utter_message(text="""2. क्विक पे b""")
            dispatcher.utter_message(text=f"""2. अपने बिजली बिल का आसानी से भुगतान करने के लिए क्विक पे करें - किसी लॉगिन की आवश्यकता नहीं है।  नेट बैंकिंग, डेबिट/क्रेडिट कार्ड या यूपीआई जैसे कई सुरक्षित भुगतानों में से चुनें।
    भुगतान करने के लिए यहां क्लिक करें: https://www.bsesdelhi.com/web/brpl/quick-pay-payment?p_p_id=com_bses_pay_now_portlet_BsesPayNowWebPortlet&p_p_lifecycle=0&_com_bses_pay_now_portlet_BsesPayNowWebPortlet_caNo={ca_number}""")

            dispatcher.utter_message(text="""3. नया कनेक्शन b""")
            dispatcher.utter_message(text="""3. नए कनेक्शन के लिए ऑनलाइन आवेदन करने, अपॉइंटमेंट का अनुरोध करने या आवश्यक दस्तावेजों की चेकलिस्ट देखने के लिए कृपया नीचे दिए गए लिंक पर क्लिक करें:
    https://ncbrpl.bsesdelhi.com/BRPL/Login""")

            dispatcher.utter_message(text="""4. कनेक्शन परिवर्तन अनुरोध b""")
            dispatcher.utter_message(text="""4. अपने मौजूदा कनेक्शन में परिवर्तन के लिए अनुरोध सबमिट करने के लिए - जैसे नाम परिवर्तन, लोड परिवर्तन, या श्रेणी परिवर्तन - कृपया नीचे दिए गए लिंक पर क्लिक करें:
    https://ncbrpl.bsesdelhi.com/BRPL/ChangeRequestLogin""")
            
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")

            return [Restarted()]


class New_consumer_faqs_bypl_english(Action):
    def name(self):
        return "action_new_consumer_faqs_bypl_english"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="""1. Mobile App (Android & iOS) b""")
        dispatcher.utter_message(text="""1. BSES Yamuna power Ltd offers a range of services through its official mobile app, “BYPL Connect,” available on both Google Play Store and Apple/iOS App Store. The app enables you to easily view and pay your electricity bills, monitor your consumption, manage your account , register complaint and much more.     
Download on Google Play Store: https://play.google.com/store/apps/details?id=com.bses.bypl.prod 
Download on Apple App Store: https://apps.apple.com/us/app/id1524511018""")
 
        dispatcher.utter_message(text="""2. Quick Pay b""")
        dispatcher.utter_message(text="""2. Quick Pay allows you to pay your electricity bill instantly without the need to log in. Choose from multiple payment options including net banking, debit/credit cards, or UPI for a quick and hassle-free payment experience.
Pay your bill here: https://www.bsesdelhi.com/web/bypl/quick-pay""")
        
        dispatcher.utter_message(text="""3. New Connection b""")
        dispatcher.utter_message(text="""3. To apply for a new connection & to view checklist, please visit:
https://ncbypl.bsesdelhi.com/BYPL/Login""")

        dispatcher.utter_message(text="""4. Change Request b""")
        dispatcher.utter_message(text="""4. For change requests such as Name Change, Load Change, or Category Change , please apply online at:
https://ncbypl.bsesdelhi.com/BYPL/ChangeRequestLogin""")

        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")

        return [Restarted()]
    

class New_consumer_faqs_bypl_hindi(Action):
    def name(self):
        return "action_new_consumer_faqs_bypl_hindi"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="""1. मोबाइल ऐप (Android और iOS) b""")
        dispatcher.utter_message(text="""1. बीएसईएस यमुना पावर लिमिटेड अपने आधिकारिक मोबाइल ऐप “BYPL Connect” के माध्यम से विभिन्न सेवाएं प्रदान करता है, जो गूगल प्ले स्टोर और एप्पल/आईओएस ऐप स्टोर दोनों पर उपलब्ध है। इस ऐप के माध्यम से आप आसानी से अपनी बिजली बिल देख और भुगतान कर सकते हैं, अपनी खपत की निगरानी कर सकते हैं, अपने खाते का प्रबंधन कर सकते हैं, शिकायत दर्ज कर सकते हैं और बहुत कुछ कर सकते हैं।
Google Play Store से डाउनलोड करें: https://play.google.com/store/apps/details?id=com.bses.bypl.prod 
Apple App Store से डाउनलोड करें: https://apps.apple.com/us/app/id1524511018""")

        dispatcher.utter_message(text="""2. क्विक पे b""")
        dispatcher.utter_message(text="""2. क्विक पे की सहायता से आप बिना लॉगिन किए तुरंत अपना बिजली बिल चुका सकते हैं। नेट बैंकिंग, डेबिट/क्रेडिट कार्ड या यूपीआई जैसे कई भुगतान विकल्पों में से चुनें और तेज़ व बिना झंझट के भुगतान का अनुभव प्राप्त करें।
यहाँ बिल का भुगतान करें: https://www.bsesdelhi.com/web/bypl/quick-pay""")

        dispatcher.utter_message(text="""3. नया कनेक्शन b""")
        dispatcher.utter_message(text="""3. नए कनेक्शन के लिए आवेदन करने और चेकलिस्ट देखने हेतु कृपया इस लिंक पर जाएँ:
https://ncbypl.bsesdelhi.com/BYPL/Login""")

        dispatcher.utter_message(text="""4. बदलाव के अनुरोध b""")
        dispatcher.utter_message(text="""4. नाम परिवर्तन, लोड परिवर्तन या श्रेणी परिवर्तन जैसे बदलावों के लिए कृपया ऑनलाइन आवेदन करें:
https://ncbypl.bsesdelhi.com/BYPL/ChangeRequestLogin""")
        
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")

        return [Restarted()]
    

## Change Language

# class Change_Language_module(Action):
#     def name(self) -> Text:
#         return "action_change_language"
    
#     def run(self, dispatcher, tracker, domain):
#         dispatcher.utter_message(text='''Please select your preferred language

# कृपया अपनी पसंदीदा भाषा चुनें''')
#         dispatcher.utter_message(text="English b")
#         dispatcher.utter_message(text="हिंदी b")
#         return [Restarted()]

class Change_Language_module(Action):
    def name(self) -> Text:
        return "action_change_language"
    
    def run(self, dispatcher, tracker, domain):
        try:
            response = requests.get(f"{FLASK_BASE_URL}/visible-languages")
            data = response.json()

    #         dispatcher.utter_message(text='''Please select your preferred language

    # कृपया अपनी पसंदीदा भाषा चुनें''')
            # dispatcher.utter_message(text='Please select your preferred language')
            send_dynamic_messages(dispatcher, "", "change_language_en", lang="en")
            # dispatcher.utter_message(text='कृपया अपनी पसंदीदा भाषा चुनें')
            send_dynamic_messages(dispatcher, "", "change_language_hi", lang="hi")
            # Check if data exists and contains languages
            if data.get("status") and "data" in data:
                languages = data["data"]
                if languages:
                    for lang in languages:
                        # Add 'b' after each language name
                        dispatcher.utter_message(text=f"{lang['name']} b")
                else:
                    dispatcher.utter_message(text="No visible languages found.")
            else:
                dispatcher.utter_message(text="Unable to fetch languages at this time.")
            return[Restarted()]
        except Exception as e:
            print(f"Error fetching visible languages: {e}")
        dispatcher.utter_message(text="Something went wrong while fetching languages.")
    

## Visually Impaired

import re

class Visually_Impaired_module_english(Action):
    def name(self) -> Text:
        return "action_visually_impaired_english"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="Please enter your 10-digit valid mobile number to receive a call back for further assistance.")
        send_dynamic_messages(dispatcher, "", "visually_impaired_step_1", lang="en")
        return []


    
def extract_number(text):
    match = re.search(r'\d+', text)
    if match:
        return match.group()
    return None  # or raise an error if you prefer

class ActionGetMobile_english(Action):
    def name(self) -> Text:
        return "action_validate_mobile_number_english"

    def run(self, dispatcher, tracker, domain):
        mo_number = tracker.latest_message.get('text')
        sender_id = tracker.sender_id

        if mo_number == "mobile verified BRPL" or mo_number == "MOBILE VERIFIED BRPL":
            # dispatcher.utter_message(text="A 6-digit One-Time Password (OTP) has been sent to the provided mobile number.")
            send_dynamic_messages(dispatcher, "", "visually_impaired_step_2", lang="en")
            return []
    
# class ActionGetMobile_english(Action):
#     def name(self) -> Text:
#         return "action_validate_mobile_number_english"

#     def run(self, dispatcher, tracker, domain):
#         mo_number = tracker.latest_message.get('text')
#         sender_id = tracker.sender_id

#         mobile_number = extract_number(mo_number)

#         if not mobile_number.strip():
#             dispatcher.utter_message(text="Input cannot be blank. Please provide your mobile number.")
#             return []

#         if not mobile_number.isdigit():
#             dispatcher.utter_message(text="Only numbers are allowed. Please enter a valid mobile number.")
#             return []

#         if len(mobile_number) < 10:
#             dispatcher.utter_message(text="Number too short. Please enter a 10-digit mobile number.")
#             return []

#         if len(mobile_number) > 10:
#             dispatcher.utter_message(text="Number too long. Please enter a 10-digit mobile number.")
#             return []
        
#         data = validate_mobile(mobile_number, sender_id)

#         # response = requests.post(f"{FLASK_BASE_URL}/validate_mobile", json={"mobile_number": mobile_number, "sender_id": sender_id})
#         # data = response.json()

#         if data.get("valid") == True:
#             # dispatcher.utter_message(text="A 6-digit One-Time Password (OTP) has been sent to the provided mobile number.")
#             send_dynamic_messages(dispatcher, "", "visually_impaired_step_2", lang="en")
#             return [SlotSet("mobile_number", None)]
        
#         else:
#             dispatcher.utter_message(text="Please enter a valid mobile number.")
#             return [SlotSet("mobile_number", mobile_number)]


class Visually_Impaired_module_final_english(Action):
    def name(self) -> Text:
        return "action_visually_impaired_final_english"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id

        response = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        data = response.json()

        tel_no = data.get("tel_no")

        data2 = insert_mobapp_data(tel_no)

        # response2 = requests.post(f"{FLASK_BASE_URL}/alert_mobapp_data", json={"MobileNo": tel_no})
        # data2 = response2.json()

        if(data2.get('status') == True):
            # dispatcher.utter_message(text="Your request number has been successfully registered. Our helpdesk team will contact you shortly.")
            dispatcher.utter_message(text=f"Request Number: {tel_no}")
            send_dynamic_messages(dispatcher, "", "visually_impaired_step_3", lang="en")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        
        else:
            dispatcher.utter_message(text="Sorry, Having issues in visually impaired service. Try after sometime.")
        
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
    

class Visually_Impaired_module_hindi(Action):
    def name(self) -> Text:
        return "action_visually_impaired_hindi"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        # dispatcher.utter_message(text="कॉलबैक प्राप्त करने और आगे की सहायता के लिए कृपया अपना वैध 10 अंकों वाला मोबाइल नंबर दर्ज करें।")
        send_dynamic_messages(dispatcher, "", "visually_impaired_step_1", lang="hi")
        return []


class ActionGetMobile_hindi(Action):
    def name(self) -> Text:
        return "action_validate_mobile_number_hindi"

    def run(self, dispatcher, tracker, domain):
        mo_number = tracker.latest_message.get('text')
        sender_id = tracker.sender_id

        if mo_number == "mobile verified BRPL" or mo_number == "MOBILE VERIFIED BRPL":
            # dispatcher.utter_message(text="आपके द्वारा दर्ज किए गए मोबाइल नंबर पर एक ओटीपी भेजा गया है।")
            send_dynamic_messages(dispatcher, "", "visually_impaired_step_2", lang="hi")
            return []



class Visually_Impaired_module_final_hindi(Action):
    def name(self) -> Text:
        return "action_visually_impaired_final_hindi"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id

        response = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        data = response.json()

        tel_no = data.get("tel_no")

        data2 = insert_mobapp_data(tel_no)

        # response2 = requests.post(f"{FLASK_BASE_URL}/alert_mobapp_data", json={"MobileNo": tel_no})
        # data2 = response2.json()

        if(data2.get('status') == True):
            dispatcher.utter_message(text=f"अनुरोध नंबर: {tel_no}")
            dispatcher.utter_message(text=f"{data2.get('message')}")

            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        
        else:
            dispatcher.utter_message(text="क्षमा करें, दृष्टिबाधित सेवा में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")

            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]


## Meter reading schedule 

class Meter_Reading_Schedule_english(Action):
    def name(self):
        return "action_meter_reading_schedule_english"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")

        ca_number = extract_ca_number(ca)

        data2 = API_GetMeterReadingSchedule(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/meter_reading", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        if data2.get("status") == True:
            # dispatcher.utter_message(text="Your meter reading schedule is as follows:")
            dispatcher.utter_message(text=f"{data2.get('message')}")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        else:
            dispatcher.utter_message(text="Sorry, Having issues in meter reading schedule service. Try after sometime.")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
    

class Meter_Reading_Schedule_hindi(Action):
    def name(self):
        return "action_meter_reading_schedule_hindi"
    

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")

        ca_number = extract_ca_number(ca)

        data2 = API_GetMeterReadingSchedule(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/meter_reading", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        if data2.get("status") == True:
            # dispatcher.utter_message(text="आपका मीटर रीडिंग शेड्यूल निम्नलिखित है:")
            dispatcher.utter_message(text=f"{data2.get('message')}")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        else:
            dispatcher.utter_message(text="क्षमा करें, मीटर रीडिंग शेड्यूल सेवा में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]


## Select for another CA number

class Check_for_ca_number_module_english(Action):
    def name(self) -> Text:
        return "action_check_for_ca_number_english"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="Please enter new CA number")
        send_dynamic_messages(dispatcher, "", "select_another_ca_step_1", lang="en")
        return []
    

class ActionValidateOTPCANumber(Action):
    def name(self):
        return "action_validate_ca_number_otp"

    def run(self, dispatcher, tracker, domain) -> list[EventType]:    
        otp = tracker.latest_message.get('text')

        print(otp, "========================================== register otp")

        if otp == "VALIDATED BRPL":
            dispatcher.utter_message(text="OTP validated successfully.")
            return [SlotSet("retry_count", 0)]
        
        if otp == "otp verified BRPL" or otp == "OTP VERIFIED BYPL":
            # dispatcher.utter_message(text="OTP validated for new CA number successfully")
            send_dynamic_messages(dispatcher, "", "select_another_ca_step_2", lang="en")
            return [Restarted()]
        
    

# class ActionValidateOTPCANumber(Action):
#     def name(self):
#         return "action_validate_ca_number_otp"

#     def run(self, dispatcher, tracker, domain) -> list[EventType]:
#         otp = tracker.latest_message.get('text')
#         retry_count = tracker.get_slot("retry_count") or 0
#         sender_id = tracker.sender_id

#         print(f"Sender ID otp: {sender_id}")

#         print(otp, "========================================== register otp")

#         if otp == "VALIDATED BRPL":
#             dispatcher.utter_message(text="OTP validated successfully.")
#             return [SlotSet("retry_count", 0)]

#         # if otp != "VALIDATED":
#         response = requests.post(f"{FLASK_BASE_URL}/validate_otp", json={"otp": otp, "sender_id": sender_id})
#         data = response.json()
#         print(data, "========================= api data")

#         if data.get("valid") or otp == "VALIDATED":
#             # dispatcher.utter_message(text="OTP validated for new CA number successfully")
#             send_dynamic_messages(dispatcher, "", "select_another_ca_step_2", lang="en")
#             return [SlotSet("retry_count", 0), Restarted()]
#         else:
#             retry_count += 1
#             # print("Updated retry_count:", retry_count)
#             if data.get("exceeded") == True:
#                 dispatcher.utter_message(text="Too many attempts. Let's start over. Click home button to start over")
#                 return [SlotSet("retry_count", 0), Restarted()]
#             elif not otp.isdigit() or len(otp) != 6:
#                 # retry_count += 1
#                 dispatcher.utter_message(text="Please enter a valid 6-digit OTP. Retries left: " + str(data.get("retries_left")))
#                 return [SlotSet("retry_count", retry_count)]

#             else:
#                 dispatcher.utter_message(text="That OTP seems incorrect. Please try again. Retries left: " + str(data.get("retries_left")))
#                 return [SlotSet("retry_count", retry_count)]
            

class Check_for_ca_number_module_hindi(Action):
    def name(self) -> Text:
        return "action_check_for_ca_number_hindi"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="कृपया नया CA नंबर दर्ज करें।")
        send_dynamic_messages(dispatcher, "", "select_another_ca_step_1", lang="hi")
        return []


class ActionValidateOTPCANumberHindi(Action):
    def name(self):
        return "action_validate_ca_number_otp_hindi"

    def run(self, dispatcher, tracker, domain) -> list[EventType]:
        otp = tracker.latest_message.get('text')

        print(otp, "========================================== register otp")

        if otp == "VALIDATED":
            dispatcher.utter_message(text="OTP सफलतापूर्वक मान्य किया गया।")
            # return [SlotSet("retry_count", 0)]
        
        if otp == "otp verified BRPL" or otp == "OTP VERIFIED BYPL":
            send_dynamic_messages(dispatcher, "", "select_another_ca_step_2", lang="hi")
            return [Restarted()]

        # otp = tracker.latest_message.get('text')
        # retry_count = tracker.get_slot("retry_count") or 0
        # sender_id = tracker.sender_id

        # print(f"Sender ID otp: {sender_id}")
        # print(otp, "========================================== register otp")

        # if otp == "VALIDATED BRPL":
        #     dispatcher.utter_message(text="OTP सफलतापूर्वक मान्य किया गया।")
        #     return [SlotSet("retry_count", 0)]

        # response = requests.post(f"{FLASK_BASE_URL}/validate_otp", json={"otp": otp, "sender_id": sender_id})
        # data = response.json()
        # print(data, "========================= api data")

        # if data.get("valid") or otp == "VALIDATED":
        #     # dispatcher.utter_message(text="नए सीए नंबर के लिए ओटीपी सफलतापूर्वक सत्यापित किया गया।")
        #     send_dynamic_messages(dispatcher, "", "select_another_ca_step_2", lang="hi")
        #     return [SlotSet("retry_count", 0), Restarted()]
        # else:
        #     retry_count += 1
        #     if data.get("exceeded") == True:
        #         dispatcher.utter_message(text="बहुत अधिक प्रयास हो गए हैं। कृपया होम बटन पर क्लिक करके पुनः शुरू करें।")
        #         return [SlotSet("retry_count", 0), Restarted()]
        #     elif not otp.isdigit() or len(otp) != 6:
        #         dispatcher.utter_message(text=f"कृपया एक मान्य 6 अंकों का OTP दर्ज करें। शेष प्रयास: {data.get('retries_left')}")
        #         return [SlotSet("retry_count", retry_count)]
        #     else:
        #         dispatcher.utter_message(text=f"OTP सही नहीं है। कृपया पुनः प्रयास करें। शेष प्रयास: {data.get('retries_left')}")
        #         return [SlotSet("retry_count", retry_count)]


## Payment History

import re

def extract_ca_number(text):
    text = text.replace(" ", "")  # Remove all whitespaces
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return None

class payment_history_module_english(Action):
    def name(self) -> Text:
        return "action_payment_history_english"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)
        # ca_number = "123456789"

        data2 = get_payment_history(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_payment_history", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        print(data2 , "=========================================== data message")

        if data2.get('status') == False:
            dispatcher.utter_message(text="Sorry, Having issues to fetch your payment history right now. Try after sometime.")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]

        else:
            # billing_entries = data2 if isinstance(data2, list) else data2.get("data", [])
            # ✅ Fix: use "entries" key instead of "data"
            billing_entries = data2.get("entries", []) if isinstance(data2, dict) else []


            if not billing_entries:
                message = data2.get("message", "No payment history available at the moment.") \
                        if isinstance(data2, dict) else "No payment history available at the moment."
                dispatcher.utter_message(text="No Payment history found for the provided CA number. Please try again later.")
                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
                dispatcher.utter_message(text="Yes menu b")
                dispatcher.utter_message(text="No menu b")
                return [Restarted()]

            dispatcher.utter_message(text="Here is your recent payment history:\n")

            for idx, entry in enumerate(billing_entries, start=1):
                bill_month = entry.get("Bill Month", "")
                invoice_date = entry.get("Date of Invoice", "")
                due_date = entry.get("Due Date", "N/A")
                net_amount = entry.get("Net Amount to be Paid", "")
                payment_amount = entry.get("Payment Amount", "")
                payment_date = entry.get("Payment Date", "N/A")
                units = entry.get("Units Consumed", "")

                message = f"""{idx}.Bill Month - {bill_month}  b
    {idx}. • Invoice Date: {invoice_date}
    • Due Date: {due_date}
    • Net Amount: ₹{net_amount}
    • Payment Made: ₹{payment_amount}
    • Payment Date: {payment_date}
    • Units Consumed: {units}
    """
                # print(message, "================= message")
                dispatcher.utter_message(text=message)

                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")

            return [Restarted()]
    
class payment_history_module_hindi(Action):
    def name(self) -> Text:
        return "action_payment_history_hindi"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        data2 = get_payment_history(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_payment_history", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        if data2.get('status') == False:
            dispatcher.utter_message(text="क्षमा करें, अभी आपकी भुगतान हिस्ट्री प्राप्त करने में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]

        else:
            print(data2, "=========================================== डेटा संदेश")
            # billing_entries = data2 if isinstance(data2, list) else data2.get("data", [])
            billing_entries = data2.get("entries", []) if isinstance(data2, dict) else []

            if not billing_entries:
                message = data2.get("message", "इस समय कोई भुगतान इतिहास उपलब्ध नहीं है।") \
                    if isinstance(data2, dict) else "इस समय कोई भुगतान इतिहास उपलब्ध नहीं है।"
                dispatcher.utter_message(text="प्रदान किए गए CA नंबर के लिए कोई भुगतान इतिहास नहीं मिला। कृपया बाद में पुनः प्रयास करें।")
                
                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
                dispatcher.utter_message(text="हाँ menu b")
                dispatcher.utter_message(text="नहीं menu b")
                return [Restarted()]

            dispatcher.utter_message(text="यहाँ आपके हाल के भुगतान का विवरण दिया गया है:\n")

            for idx, entry in enumerate(billing_entries, start=1):
                bill_month = entry.get("Bill Month", "")
                invoice_date = entry.get("Date of Invoice", "")
                due_date = entry.get("Due Date", "उपलब्ध नहीं")
                net_amount = entry.get("Net Amount to be Paid", "")
                payment_amount = entry.get("Payment Amount", "")
                payment_date = entry.get("Payment Date", "उपलब्ध नहीं")
                units = entry.get("Units Consumed", "")

                message = f"""{idx}.बिल माह - {bill_month} b
    {idx}. • बिल इनवॉइस दिनांक: {invoice_date}
    • देय तिथि: {due_date}
    • कुल राशि: ₹{net_amount}
    • प्राप्त भुगतान: ₹{payment_amount}
    • भुगतान तिथि: {payment_date}
    • उपभोग की गई यूनिट्स: {units}
    """
                print(message, "================= संदेश")
                dispatcher.utter_message(text=message)

                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")

            return [Restarted()]


## Bill History

class bill_history_module_english(Action):
    def name(self) -> Text:
        return "action_bill_history_english"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)
        # ca_number = "123456789"

        data2 = get_bill_history(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_bill_history", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        if data2.get("status") == False:
            dispatcher.utter_message(text="Sorry, Having issues to fetch your bill history right now. Try after sometime.")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        
        else:

            print(data2 , "=========================================== data message")
            billing_entries = data2.get("entries", []) if isinstance(data2, dict) else []
            # billing_entries = data2 if isinstance(data2, list) else data2.get("data", [])

            if not billing_entries:
                message = data2.get("message", "No payment history available at the moment.") \
                        if isinstance(data2, dict) else "No payment history available at the moment."
                dispatcher.utter_message(text="No Payment history found for the provided CA number. Please try again later.")
                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
                dispatcher.utter_message(text="Yes menu b")
                dispatcher.utter_message(text="No menu b")
                return [Restarted()]

            dispatcher.utter_message(text="Here is your recent payment history:\n")

            for idx, entry in enumerate(billing_entries, start=1):
                bill_month = entry.get("Bill Month", "")
                invoice_date = entry.get("Date of Invoice", "")
                due_date = entry.get("Due Date", "").strip()
                net_amount = entry.get("Net Amount to be Paid", "")
                payment_amount = entry.get("Payment Amount", "")
                payment_date = entry.get("Payment Date", "").strip()
                units = entry.get("Units Consumed", "")
                invoice_no = entry.get("Invoice No", "")
                current_bill_amount = entry.get("Current Bill Amount", "")

                # Replace empty or whitespace-only values with N/A
                if not due_date:
                    due_date = "N/A"
                if not payment_date:
                    payment_date = "N/A"

                message = f"""{idx}.Bill Month - {bill_month}, Bill Date: {invoice_date}  b
    {idx}. • Invoice Date: {invoice_date}
    • INVOICE NO: {invoice_no}
    • Current Bill Amount: ₹{current_bill_amount}
    • Units Consumed: {units}
    • Due Date: {due_date}
    • Net Amount: ₹{net_amount}
    • Payment Made: ₹{payment_amount}
    • Payment Date: {payment_date}
    """
                # print(message, "================= message")
                dispatcher.utter_message(text=message)

                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")

            return [Restarted()]
    
class bill_history_module_hindi(Action):
    def name(self) -> Text:
        return "action_bill_history_hindi"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        data2 = get_bill_history(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_bill_history", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        if data2.get("status") == False:
            dispatcher.utter_message(text="क्षमा करें, अभी आपकी बिल हिस्ट्री प्राप्त करने में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")           
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        
        else:

            print(data2, "=========================================== डेटा संदेश")
            billing_entries = data2.get("entries", []) if isinstance(data2, dict) else []
            # billing_entries = data2 if isinstance(data2, list) else data2.get("data", [])

            if not billing_entries:
                message = data2.get("message", "इस समय कोई भुगतान इतिहास उपलब्ध नहीं है।") \
                    if isinstance(data2, dict) else "इस समय कोई भुगतान इतिहास उपलब्ध नहीं है।"
                dispatcher.utter_message(text="प्रदान किए गए CA नंबर के लिए कोई भुगतान इतिहास नहीं मिला। कृपया बाद में पुनः प्रयास करें।")
                
                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
                dispatcher.utter_message(text="हाँ menu b")
                dispatcher.utter_message(text="नहीं menu b")
                return [Restarted()]

            dispatcher.utter_message(text="यहाँ आपके हाल के भुगतान का विवरण दिया गया है:\n")

            for idx, entry in enumerate(billing_entries, start=1):
                bill_month = entry.get("Bill Month", "")
                invoice_date = entry.get("Date of Invoice", "")
                due_date = entry.get("Due Date", "").strip()
                net_amount = entry.get("Net Amount to be Paid", "")
                payment_amount = entry.get("Payment Amount", "")
                payment_date = entry.get("Payment Date", "").strip()
                units = entry.get("Units Consumed", "")
                invoice_no = entry.get("Invoice No", "")
                current_bill_amount = entry.get("Current Bill Amount", "")

                # Replace empty or whitespace-only values with N/A
                if not due_date:
                    due_date = "N/A"
                if not payment_date:
                    payment_date = "N/A"

                message = f"""{idx}. बिल माह - {bill_month}, बिल तिथि: {invoice_date} b
    {idx}. • बिल इनवॉइस दिनांक: {invoice_date}
    • चालान संख्या: {invoice_no}
    • वर्तमान बिल राशि: ₹{current_bill_amount}
    • उपभोग की गई यूनिट्स: {units}
    • देय तिथि: {due_date}
    • कुल राशि: ₹{net_amount}
    • प्राप्त भुगतान: ₹{payment_amount}
    • भुगतान तिथि: {payment_date}
    """
                print(message, "================= संदेश")
                dispatcher.utter_message(text=message)

                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")

            return [Restarted()]




## Payment Status

# class payment_status_module_english(Action):
#     def name(self) -> Text:
#         return "action_check_for_payment_status_english"
    
#     def run(self, dispatcher, tracker, domain):
#         sender_id = tracker.sender_id

#         # Fetch CA number from your database or API
#         response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
#         data = response.json()

#         ca = data.get("ca_number")
#         ca_number = extract_ca_number(ca)

#         # dispatcher.utter_message(text=f"Check you payment status here: https://www.bsesdelhi.com/web/brpl/quick-pay-payment?p_p_id=com_bses_pay_now_portlet_BsesPayNowWebPortlet&p_p_lifecycle=0&_com_bses_pay_now_portlet_BsesPayNowWebPortlet_caNo={ca_number}")
#         dispatcher.utter_message(text=f'{send_dynamic_messages_without_dispatcher("", "payment_status", lang="en")} https://www.bsesdelhi.com/web/brpl/quick-pay-payment?p_p_id=com_bses_pay_now_portlet_BsesPayNowWebPortlet&p_p_lifecycle=0&_com_bses_pay_now_portlet_BsesPayNowWebPortlet_caNo={ca_number}')

#         #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
#         send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
#         dispatcher.utter_message(text="Yes menu b")
#         dispatcher.utter_message(text="No menu b")
#         return [Restarted()]

from datetime import datetime

class payment_status_module_english(Action):
    def name(self) -> Text:
        return "action_check_for_payment_status_english"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)
        # ca_number = "123456789"

        data2 = get_payment_history(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_payment_history", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        print(data2 , "=========================================== data message")

        if data2.get('status') == False:
            dispatcher.utter_message(text="Sorry, Having issues to fetch your payment status right now. Try after sometime.")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]

        else:
            # billing_entries = data2 if isinstance(data2, list) else data2.get("data", [])
            # ✅ Fix: use "entries" key instead of "data"
            billing_entries = data2.get("entries", []) if isinstance(data2, dict) else []


            if not billing_entries:
                message = data2.get("message", "No payment status available at the moment.") \
                        if isinstance(data2, dict) else "No payment status available at the moment."
                dispatcher.utter_message(text="No Payment status found for the provided CA number.")
                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
                dispatcher.utter_message(text="Yes menu b")
                dispatcher.utter_message(text="No menu b")
                return [Restarted()]

            dispatcher.utter_message(text="Here is your recent payment status:\n")

            for idx, entry in enumerate(billing_entries, start=1):

                payment_date_str = entry.get("Payment Date", "N/A")
                total_bill_amt = entry.get("Total Bill Amt", "N/A")

                # if total_bill_amt < 0:
                #     dispatcher.utter_message(text="No Payment Status found")

                # ✅ Determine if the bill is paid or unpaid
                status = "Unpaid"
                if payment_date_str:
                    try:
                        payment_date = datetime.strptime(payment_date_str, "%d-%m-%Y")
                        current_date = datetime.now()
                        if payment_date <= current_date:
                            status = "Paid"
                    except ValueError:
                        status = "Unpaid"  # in case of invalid date format

                if status == "Paid":

                    bill_month = entry.get("Bill Month", "")
                    invoice_date = entry.get("Date of Invoice", "")
                    payment_amount = entry.get("Payment Amount", "")
                    payment_date = entry.get("Payment Date", "N/A")

                    message = f"""{idx}.Current Bill Month Name - {bill_month}  b
        {idx}. • Date of Invoice: {invoice_date}
        • Amount paid: ₹{payment_amount}
        • Payment date: {payment_date}
        • Source of Payment: "N/A"
        • Transaction Number: "N/A"
        • Status: {status}
        """
                    # print(message, "================= message")
                    dispatcher.utter_message(text=message)
                    dispatcher.utter_message(text=f"Kindly ignore, if you have paid the {bill_month} month’s bill")

                else:
                    bill_month = entry.get("Bill Month", "")
                    invoice_date = entry.get("Date of Invoice", "")
                    due_date = entry.get("Due Date", "N/A")
                    net_amount = entry.get("Net Amount to be Paid", "")
                    units = entry.get("Units Consumed", "")

                    message = f"""{idx}.Current Bill Month Name - {bill_month}  b
        {idx}. • Date of Invoice: {invoice_date}
        • Amount to be paid: ₹{net_amount}
        • Due Date: {due_date}
        • Number of Units Consumed: {units}
        • Status: {status}
        """
                    # print(message, "================= message")
                    dispatcher.utter_message(text=message)

                break

                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")

            return [Restarted()]
    

# class payment_status_module_hindi(Action):
#     def name(self) -> Text:
#         return "action_check_for_payment_status_hindi"
    
#     def run(self, dispatcher, tracker, domain):
#         sender_id = tracker.sender_id

#         # Fetch CA number from your database or API
#         response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
#         data = response.json()

#         ca = data.get("ca_number")
#         ca_number = extract_ca_number(ca)

#         dispatcher.utter_message(text=f'{send_dynamic_messages_without_dispatcher("", "payment_status", lang="hi")} https://www.bsesdelhi.com/web/brpl/quick-pay-payment?p_p_id=com_bses_pay_now_portlet_BsesPayNowWebPortlet&p_p_lifecycle=0&_com_bses_pay_now_portlet_BsesPayNowWebPortlet_caNo={ca_number}')
        
#         #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
#         send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
#         dispatcher.utter_message(text="हाँ menu b")
#         dispatcher.utter_message(text="नहीं menu b")
#         return [Restarted()]

class payment_status_module_hindi(Action):
    def name(self) -> Text:
        return "action_check_for_payment_status_hindi"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        data2 = get_payment_history(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_payment_history", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        print(data2, "=========================================== डेटा संदेश")

        if data2.get('status') == False:
            dispatcher.utter_message(text="माफ़ कीजिए, इस समय आपके भुगतान की स्थिति प्राप्त करने में समस्या हो रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]

        else:
            billing_entries = data2.get("entries", []) if isinstance(data2, dict) else []

            if not billing_entries:
                message = data2.get("message", "इस समय कोई भुगतान स्थिति उपलब्ध नहीं है।") \
                        if isinstance(data2, dict) else "इस समय कोई भुगतान स्थिति उपलब्ध नहीं है।"
                dispatcher.utter_message(text="प्रदान किए गए CA नंबर के लिए कोई भुगतान स्थिति नहीं मिली।")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
                dispatcher.utter_message(text="हाँ menu b")
                dispatcher.utter_message(text="नहीं menu b")
                return [Restarted()]

            dispatcher.utter_message(text="यह रही आपकी हाल की भुगतान स्थिति:\n")

            for idx, entry in enumerate(billing_entries, start=1):

                payment_date_str = entry.get("Payment Date", "N/A")
                total_bill_amt = entry.get("Total Bill Amt", "N/A")

                # if total_bill_amt < 0:
                #     dispatcher.utter_message(text="कोई भुगतान स्थिति नहीं मिली।")

                # ✅ बिल भुगतान हुआ या नहीं यह जांचें
                status = "भुगतान नहीं किया गया"
                if payment_date_str:
                    try:
                        payment_date = datetime.strptime(payment_date_str, "%d-%m-%Y")
                        current_date = datetime.now()
                        if payment_date <= current_date:
                            status = "भुगतान किया गया"
                    except ValueError:
                        status = "भुगतान नहीं किया गया"

                if status == "भुगतान किया गया":

                    bill_month = entry.get("Bill Month", "")
                    invoice_date = entry.get("Date of Invoice", "")
                    payment_amount = entry.get("Payment Amount", "")
                    payment_date = entry.get("Payment Date", "N/A")

                    message = f"""{idx}.वर्तमान बिल माह - {bill_month} b
        {idx}. • चालान की तारीख: {invoice_date}
        • भुगतान की राशि: ₹{payment_amount}
        • भुगतान की तारीख: {payment_date}
        • भुगतान का स्रोत: "N/A"
        • लेनदेन संख्या: "N/A"
        • स्थिति: {status}
        """
                    dispatcher.utter_message(text=message)
                    dispatcher.utter_message(text=f"यदि आपने {bill_month} महीने का बिल पहले ही चुका दिया है, तो कृपया इस संदेश को अनदेखा करें।")

                else:
                    bill_month = entry.get("Bill Month", "")
                    invoice_date = entry.get("Date of Invoice", "")
                    due_date = entry.get("Due Date", "N/A")
                    net_amount = entry.get("Net Amount to be Paid", "")
                    units = entry.get("Units Consumed", "")

                    message = f"""{idx}.वर्तमान बिल माह - {bill_month} b
        {idx}. • चालान की तारीख: {invoice_date}
        • भुगतान की जाने वाली राशि: ₹{net_amount}
        • अंतिम तिथि: {due_date}
        • खपत की गई यूनिट्स: {units}
        • स्थिति: {status}
        """
                    dispatcher.utter_message(text=message)

                break

            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")

            return [Restarted()]



## Consumption History

class consumption_history_module_english(Action):
    def name(self) -> Text:
        return "action_consumption_history_english"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)
        # ca_number = "123456789"

        data2 = get_pdf_bill(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_consumption_history_pdf", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        if data2.get('status') == True:
            print("Consumtion history ======================================")

            if data2.get("message").startswith("Details not available for CA"):
                dispatcher.utter_message(text=f'{data2.get("message")}')
            else:
                # dispatcher.utter_message(text=f"Here is the link of your consumption history: {data2.get('message')}")
                dispatcher.utter_message(text=f'{send_dynamic_messages_without_dispatcher("", "consumption_history", lang="en")} {data2.get("message")}')
        else:
            dispatcher.utter_message(text="Sorry, currently having trouble to fetch your consumption history. Please try after some time.")

        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")

        return [Restarted()]



class consumption_history_module_hindi(Action):
    def name(self) -> Text:
        return "action_consumption_history_hindi"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        data2 = get_pdf_bill(ca_number)

        # reading_data = requests.post(f"{FLASK_BASE_URL}/get_consumption_history_pdf", json={"ca_number": ca_number})
        # data2 = reading_data.json()

        if data2.get('status') == True:
            if data2.get("message").startswith("Details not available for CA"):
                dispatcher.utter_message(text=f'CA नंबर {ca_number} के लिए विवरण उपलब्ध नहीं है। कृपया हमें 19123 (टोल-फ्री) पर कॉल करें या brpl.customercare@relianceada.com पर हमें लिखें। धन्यवाद।')
            else:
                # dispatcher.utter_message(text=f"यह रहा आपके उपभोग इतिहास का लिंक: {data2.get('message')}")
                dispatcher.utter_message(text=f'{send_dynamic_messages_without_dispatcher("", "consumption_history", lang="hi")} {data2.get("message")}')
        else:
            dispatcher.utter_message(text="क्षमा करें, अभी आपकी खपत का इतिहास प्राप्त करने में समस्या हो रही है। कृपया कुछ समय बाद पुनः प्रयास करें।" )

        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")

        return [Restarted()]



## Streetlight Complaint

class streetlight_complaint_module_english(Action):
    def name(self) -> Text:
        return "action_streetlight_complaint_english"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="Register your complain here: https://www.bsesdelhi.com/web/brpl/street-light-complaint")
        send_dynamic_messages(dispatcher, "", "streetlight_complaint", lang="en")
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
    

class streetlight_complaint_module_hindi(Action):
    def name(self) -> Text:
        return "action_streetlight_complaint_hindi"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="अपनी स्ट्रीट लाइट की शिकायत यहां दर्ज करें: https://www.bsesdelhi.com/web/brpl/street-light-complaint")
        send_dynamic_messages(dispatcher, "", "streetlight_complaint", lang="hi")
        
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]


## Branches Nearby

class branches_nearby_module_english(Action):
    def name(self) -> Text:
        return "action_branches_nearby_english"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="What centres would you like me to locate?")
        send_dynamic_messages(dispatcher, "", "branch_nearby_step_1", lang="en")
        dispatcher.utter_message(text="Payment Centres b")
        dispatcher.utter_message(text="Complaint Centres b")
        return []
    
class branches_module_english(Action):
    def name(self) -> Text:
        return "action_branches_payment_centres_english"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="Share your live location or type your address manually")
        send_dynamic_messages(dispatcher, "", "branch_nearby_step_2", lang="en")
        dispatcher.utter_message(text="Share Live Location b")
        # dispatcher.utter_message(text="Type address b")
        return []
    
def extract_location_info(text):
    pattern = r'(\d+\.\d+),(\d+\.\d+)\s+([A-Z]{2})\s+BRPL'
    match = re.search(pattern, text)
    if match:
        lon = float(match.group(1))
        lat = float(match.group(2))
        filter_code = match.group(3)
        return lon, lat, filter_code
    else:
        raise ValueError("Input does not match the expected format.")

# class branches_lang_long_module(Action):
#     def name(self) -> Text:
#         return "action_branches_lang_long"
    
#     def run(self, dispatcher, tracker, domain):
#         text = tracker.latest_message.get("text")
#         latitude, longitude, filter_code = extract_location_info(text)

#         try:
#             response = requests.post(
#                 f"{FLASK_BASE_URL}/get_outlet_data", 
#                 json={"latitude": latitude, "longitude": longitude, "filter_code": filter_code}
#             )
#             data = response.json()
#         except Exception as e:
#             dispatcher.utter_message(text="Error locating nearby branches. Please share your location again.")
#             print("Exception:", e)
#             #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            #send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
#             dispatcher.utter_message(text="Yes menu b")
#             dispatcher.utter_message(text="No menu b")
#             return [Restarted()]
        
#         nearest_branches = data.get("nearest_branches", [])
        
#         if not nearest_branches:
#             dispatcher.utter_message(text="No nearby branches found.")
#             return []

#         def parse_distance(distance_str):
#             try:
#                 # Convert to string, strip leading/trailing spaces
#                 distance_str = str(distance_str).strip()

#                 # Extract first numeric value (supports commas, decimals)
#                 match = re.search(r"[\d,]+(?:\.\d+)?", distance_str)
#                 if not match:
#                     return 0.0

#                 # Remove commas and convert to float
#                 cleaned_number = match.group(0).replace(",", "")
#                 return float(cleaned_number)
#             except:
#                 return 0.0

#         branches_3km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 3]
#         branches_5km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 5]
#         branches_10km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 10]

#         def format_branch_details(branches, radius_label, mapping):
#             details = f"{mapping} Branches within {radius_label}:\n\n"
#             for branch in branches:
#                 name = branch.get("NAME", "N/A")
#                 address = branch.get("ADDRESS", "N/A")
#                 distance = parse_distance(branch.get("distance_km", 0))
#                 link = branch.get("navigation_link", "N/A")
#                 details += (
#                     f"• name: {name}\n"
#                     f"• Address: {address}\n"
#                     f"• Distance: {distance} km\n"
#                     f"• Navigate: {link}\n"
#                 )
#             return details

#         # Build the final message with proper grouping
#         final_message = (
#             "1. Branches within 3 km b\n"
#             "2. Branches within 5 km b\n"
#             "3. Branches within 10 km b\n" +
#             format_branch_details(branches_3km, "3 km", "1.") +
#             format_branch_details(branches_5km, "5 km", "2.") +
#             format_branch_details(branches_10km, "10 km", "3.")
#         )

#         dispatcher.utter_message(text=final_message)

#         #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        #send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
#         dispatcher.utter_message(text="Yes menu b")
#         dispatcher.utter_message(text="No menu b")
#         return [Restarted()]


class branches_lang_long_module(Action):
    def name(self) -> Text:
        return "action_branches_lang_long"
    
    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get("text")
        latitude, longitude, filter_code = extract_location_info(text)

        try:
            # response = requests.post(
            #     f"{FLASK_BASE_URL}/get_outlet_data", 
            #     json={"latitude": latitude, "longitude": longitude, "filter_code": filter_code}
            # )
            # data = response.json()
            data = get_outlet_data(latitude, longitude, filter_code)
        except Exception as e:
            dispatcher.utter_message(text="Error locating nearby branches. Please share your location again.")
            print("Exception:", e)
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        
        nearest_branches = data.get("nearest_branches", [])

        print(nearest_branches, "===================== nearest branches")
        
        if not nearest_branches:
            dispatcher.utter_message(text="No nearby branches found.")
            return []

        def parse_distance(distance_str):
            try:
                # Convert to string, strip leading/trailing spaces
                distance_str = str(distance_str).strip()

                # Extract first numeric value (supports commas, decimals)
                match = re.search(r"[\d,]+(?:\.\d+)?", distance_str)
                if not match:
                    return 0.0

                # Remove commas and convert to float
                cleaned_number = match.group(0).replace(",", "")
                return float(cleaned_number)
            except:
                return 0.0

        branches_3km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 3]
        branches_5km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 5]
        branches_10km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 10]

        print(branches_10km, branches_5km, branches_3km, "=====================")

        if not branches_10km:
            dispatcher.utter_message(
                text="The location provided by you is not within the BRPL serviceable area."
                    # "You can try sharing a nearby landmark or pin location for better results."
            )
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]

        def format_branch_details(branches, radius_label, mapping):
            details = f"{mapping} Branches within {radius_label}:\n\n"
            for branch in branches:
                name = branch.get("NAME", "N/A")
                address = branch.get("ADDRESS", "N/A")
                # distance = parse_distance(branch.get("distance_km", 0))
                link = branch.get("navigation_link", "N/A")
                details += (
                    f"• name: {name}\n"
                    f"• Address: {address}\n"
                    # f"• Distance: {distance} km\n"
                    f"• Track Location: {link}\n"
                )
            return details

        # Build the final message with proper grouping
        final_message = (
            "1. Branches within 3 km b\n"
            "2. Branches within 5 km b\n"
            "3. Branches within 10 km b\n" +
            format_branch_details(branches_3km, "3 km", "1.") +
            format_branch_details(branches_5km, "5 km", "2.") +
            format_branch_details(branches_10km, "10 km", "3.")
        )

        dispatcher.utter_message(text=final_message)

        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]



class branches_nearby_module_hindi(Action):
    def name(self) -> Text:
        return "action_branches_nearby_hindi"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="आप किस प्रकार के केंद्र का पता लगाना चाहेंगे?")
        send_dynamic_messages(dispatcher, "", "branch_nearby_step_1", lang="hi")
        dispatcher.utter_message(text="भुगतान केंद्र b")
        dispatcher.utter_message(text="शिकायत केंद्र b")
        return []
    

class branches_module_hindi(Action):
    def name(self) -> Text:
        return "action_branches_payment_centres_hindi"
    
    def run(self, dispatcher, tracker, domain):
        # dispatcher.utter_message(text="अपना लाइव लोकेशन साझा करें या अपना पता मैन्युअली टाइप करें")
        send_dynamic_messages(dispatcher, "", "branch_nearby_step_2", lang="hi")
        dispatcher.utter_message(text="लाइव लोकेशन साझा करें b")
        return []


class branches_lang_long_module_hindi(Action):
    def name(self) -> Text:
        return "action_branches_lang_long_hindi"
    
    def run(self, dispatcher, tracker, domain):
        text = tracker.latest_message.get("text")
        latitude, longitude, filter_code = extract_location_info(text)

        try:
            # response = requests.post(
            #     f"{FLASK_BASE_URL}/get_outlet_data", 
            #     json={"latitude": latitude, "longitude": longitude, "filter_code": filter_code}
            # )
            # data = response.json()
            data = get_outlet_data(latitude, longitude, filter_code)
        except Exception as e:
            dispatcher.utter_message(text="निकटतम शाखाओं का पता लगाने में त्रुटि हुई। कृपया अपना लोकेशन फिर से साझा करें।")
            print("Exception:", e)
            
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        
        nearest_branches = data.get("nearest_branches", [])
        
        if not nearest_branches:
            dispatcher.utter_message(text="कोई निकटतम शाखा नहीं मिली।")
            return []

        def parse_distance(distance_str):
            try:
                return float(str(distance_str).replace("km", "").strip())
            except:
                return 0.0

        branches_3km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 3]
        branches_5km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 5]
        branches_10km = [b for b in nearest_branches if parse_distance(b.get("distance_km", 0)) <= 10]

        if not branches_10km:
            dispatcher.utter_message(
                text="आपके द्वारा साझा किया गया स्थान BRPL की सेवा क्षेत्र में नहीं आता है।"
                # "आप पास के किसी लैंडमार्क या पिन लोकेशन को साझा करके दोबारा प्रयास कर सकते हैं।"
            )
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]


        def format_branch_details(branches, radius_label, mapping):
            details = f"{mapping} भीतर शाखाएँ {radius_label}:\n\n"
            for branch in branches:
                name = branch.get("NAME", "N/A")
                address = branch.get("ADDRESS", "N/A")
                # distance = parse_distance(branch.get("distance_km", 0))
                link = branch.get("navigation_link", "N/A")
                details += (
                    f"• नाम: {name}\n"
                    f"• पता: {address}\n"
                    # f"• दूरी: {distance} km\n"
                    f"• लोकेशन ट्रैक करें: {link}\n"
                )
            return details

        # Build the final message with proper grouping
        final_message = (
            "1. भीतर शाखाएँ 3 km b\n"
            "2. भीतर शाखाएँ 5 km b\n"
            "3. भीतर शाखाएँ 10 km b\n" +
            format_branch_details(branches_3km, "3 km", "1.") +
            format_branch_details(branches_5km, "5 km", "2.") +
            format_branch_details(branches_10km, "10 km", "3.")
        )

        dispatcher.utter_message(text=final_message)

        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]



## Opt for e-bill

class Opt_For_Ebill_english(Action):
    def name(self):
        return "action_opt_for_ebill_english"

    def run(self, dispatcher, tracker, domain):

        print("action_opt_for_ebill_english ==================================== ")
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        data = response.json()

        email = data.get("email")

        print(email, "================================ email")

        if email:
            dispatcher.utter_message(text=f"Your email is {email}. Do you want to use this for e-bill?")
            dispatcher.utter_message(text="Yes, agree b")
            dispatcher.utter_message(text="No, Update Email ID b")
            return []
        else:
            dispatcher.utter_message(text="Please enter your email ID.")
            return []
        
# def extract_email(text):
#     # Regex pattern for email
#     pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
#     match = re.search(pattern, text)
#     if match:
#         return match.group()
#     return None

def extract_email(text):
    """
    Extract a single email-like string from text.
    Captures valid and invalid emails (including multiple '@', missing domain parts, etc.).
    Returns the first match found as a string, or None if not found.
    """
    # Very permissive regex for email-like patterns
    pattern = r'[A-Za-z0-9._%+-]+(?:@+[A-Za-z0-9._%+-]*)+'
    
    match = re.search(pattern, text)
    if match:
        return match.group()
    return None

class Opt_For_Ebill_Email_english(Action):
    def name(self):
        return "action_opt_for_ebill_email_english"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        email_text = tracker.latest_message.get('text')
        
        

        if email_text == "email verified BRPL" or email_text == "EMAIL VERIFIED BRPL":
            # dispatcher.utter_message(text="Would you like to opt in for e-bills?")
            # requests.post(f"{FLASK_BASE_URL}/update_email_in_db", json={"sender_id": sender_id, "email": email})
            # update_email_in_db(sender_id, email)

            dispatcher.utter_message(text="New Email ID has been successfully registered. Would you like to opt for e-bill on the ID registered?")
            dispatcher.utter_message(text="Yes, agree b")
            dispatcher.utter_message(text="No, disagree b")
            return []
        else:
            dispatcher.utter_message(text="Opt for E-bill service is unavailable right now. Try after some time.")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]

# class Opt_For_Ebill_Email_english(Action):
    # def name(self):
    #     return "action_opt_for_ebill_email_english"

    # def run(self, dispatcher, tracker, domain):
    #     sender_id = tracker.sender_id
    #     email_text = tracker.latest_message.get('text')
    #     retry_count = tracker.get_slot("retry_count") or 0
    #     email = extract_email(email_text)

    #     print(email, "=================================== extracted_email")

    #     email_validate_response = requests.post(f"{FLASK_BASE_URL}/validate_email", json={"email": email, "sender_id": sender_id})
    #     email_validate_data = email_validate_response.json()

       
    #     response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
    #     data = response.json()

    #     ca_number = data.get("ca_number")

    #     if email_validate_data.get("valid"):
    #         data1 = update_missing_email(ca_number, email)
    #         # response_data = requests.post(f"{FLASK_BASE_URL}/update_missing_email", json={"ca_number": ca_number, "email": email})
    #         # data1 = response_data.json()
    #     else:
    #         retry_count += 1
    #         # print("Updated retry_count:", retry_count)
    #         if email_validate_data.get("exceeded") == True:
    #             dispatcher.utter_message(text="Too many attempts. Let's start over. Click home button to start over")
    #             return [SlotSet("retry_count", 0), Restarted()]
    #         else:
    #             dispatcher.utter_message(text="Please enter valid email. Retries left: " + str(email_validate_data.get("retries_left")))
    #             return [SlotSet("retry_count", retry_count)]
        

    #     if data1.get("status") == True:
    #         # dispatcher.utter_message(text="Would you like to opt in for e-bills?")
    #         # requests.post(f"{FLASK_BASE_URL}/update_email_in_db", json={"sender_id": sender_id, "email": email})
    #         update_email_in_db(sender_id, email)

    #         dispatcher.utter_message(text="New Email ID has been successfully registered. Would you like to opt for e-bill on the ID registered?")
    #         dispatcher.utter_message(text="Yes, agree b")
    #         dispatcher.utter_message(text="No, disagree b")
    #         return []
    #     else:
    #         dispatcher.utter_message(text="Opt for E-bill service is unavailable right now. Try after some time.")
    #         #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
    #         send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
    #         dispatcher.utter_message(text="Yes menu b")
    #         dispatcher.utter_message(text="No menu b")
    #         return [Restarted()]
        

class Opt_For_Ebill_Email_Registration_Yes_english(Action):
    def name(self):
        return "action_opt_for_ebill_registration_yes_english"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca_number = data.get("ca_number")

        data1 = registration_ebill(ca_number)
 
        # response_data = requests.post(f"{FLASK_BASE_URL}/registration_ebill", json={"ca_number": ca_number})
        # data1 = response_data.json()


        if data1.get("status") == True:
            dispatcher.utter_message(text="You’ve successfully opted for E-Bill. Future bills will be emailed to you.")
            
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        else:
            dispatcher.utter_message(text="Opt for E-bill service is unavailable right now. Try after some time.")

            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        

class Opt_For_Ebill_Email_Registration_No_english(Action):
    def name(self):
        return "action_opt_for_ebill_registration_no_english"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Sure, no problem")
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
        

class Opt_For_Ebill_Existing_Email_english(Action):
    def name(self):
        return "action_opt_for_ebill_existing_email_english"

    def run(self, dispatcher, tracker, domain):
        
        # dispatcher.utter_message(text="Would you like to opt in for e-bills?")
        dispatcher.utter_message(text="Email ID has been successfully registered. Would you like to opt for e-bill on the ID registered?")
        dispatcher.utter_message(text="Yes, agree b")
        dispatcher.utter_message(text="No, disagree b")
        return []

class Opt_For_Ebill_Existing_Ask_New_Email_english(Action):
    def name(self):
        return "action_opt_for_ebill_ask_new_email_english"

    def run(self, dispatcher, tracker, domain):        
        dispatcher.utter_message(text="Please enter new email ID.")
        return []
    

class Opt_For_Ebill_hindi(Action):
    def name(self):
        return "action_opt_for_ebill_hindi"

    def run(self, dispatcher, tracker, domain):

        print("action_opt_for_ebill_hindi ==================================== ")
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        data = response.json()

        email = data.get("email")

        print(email, "================================ email")

        if email:
            dispatcher.utter_message(text=f"आपका ईमेल {email} है। क्या आप इसे ई-बिल के लिए उपयोग करना चाहते हैं?")
            dispatcher.utter_message(text="हाँ, सहमत b")
            dispatcher.utter_message(text="नहीं, ईमेल अपडेट करें b")
            return []
        else:
            dispatcher.utter_message(text="कृपया अपना ईमेल आईडी दर्ज करें।")
            return []
        

class Opt_For_Ebill_Email_hindi(Action):
    def name(self):
        return "action_opt_for_ebill_email_hindi"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        email_text = tracker.latest_message.get('text')

        if email_text == "email verified BRPL" or email_text == "EMAIL VERIFIED BRPL":

            dispatcher.utter_message(text="नई ईमेल आईडी सफलतापूर्वक पंजीकृत हो गई है। क्या आप पंजीकृत आईडी पर ई-बिल प्राप्त करना चाहेंगे?")
            dispatcher.utter_message(text="हाँ, सहमत b")
            dispatcher.utter_message(text="नहीं, असहमति b")
            return []
        else:
            dispatcher.utter_message(text="ई-बिल सेवा अभी उपलब्ध नहीं है। कृपया कुछ समय बाद पुनः प्रयास करें।")
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        

        
# class Opt_For_Ebill_Email_hindi(Action):
#     def name(self):
#         return "action_opt_for_ebill_email_hindi"

#     def run(self, dispatcher, tracker, domain):
#         sender_id = tracker.sender_id
#         email_text = tracker.latest_message.get('text')
#         retry_count = tracker.get_slot("retry_count") or 0
#         email = extract_email(email_text)

#         email_validate_response = requests.post(f"{FLASK_BASE_URL}/validate_email", json={"email": email, "sender_id": sender_id})
#         email_validate_data = email_validate_response.json()

#         response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
#         data = response.json()

#         ca_number = data.get("ca_number")
    
#         if email_validate_data.get("valid"):
#             data1 = update_missing_email(ca_number, email)
#             # response_data = requests.post(f"{FLASK_BASE_URL}/update_missing_email", json={"ca_number": ca_number, "email": email})
#             # data1 = response_data.json()
#         else:
#             retry_count += 1
#             # print("Updated retry_count:", retry_count)
#             if email_validate_data.get("exceeded") == True:
#                 dispatcher.utter_message(text="बहुत अधिक प्रयास किए गए हैं। कृपया फिर से शुरू करें। पुनः प्रारंभ करने के लिए होम बटन पर क्लिक करें।")
#                 return [SlotSet("retry_count", 0), Restarted()]
#             else:
#                 dispatcher.utter_message(text="कृपया मान्य ईमेल दर्ज करें। बचे हुए प्रयास: " + str(email_validate_data.get("retries_left")))
#                 return [SlotSet("retry_count", retry_count)]


#         if data1.get("status") == True:
#             # requests.post(f"{FLASK_BASE_URL}/update_email_in_db", json={"sender_id": sender_id, "email": email})
#             # dispatcher.utter_message(text="क्या आप ई-बिल के लिए पंजीकरण करना चाहते हैं?")
#             update_email_in_db(sender_id, email)

#             dispatcher.utter_message(text="नई ईमेल आईडी सफलतापूर्वक पंजीकृत हो गई है। क्या आप पंजीकृत आईडी पर ई-बिल प्राप्त करना चाहेंगे?")
#             dispatcher.utter_message(text="हाँ, सहमत b")
#             dispatcher.utter_message(text="नहीं, असहमति b")
#             return []
#         else:
#             dispatcher.utter_message(text="ई-बिल सेवा अभी उपलब्ध नहीं है। कृपया कुछ समय बाद पुनः प्रयास करें।")
#             #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
#             send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
#             dispatcher.utter_message(text="हाँ menu b")
#             dispatcher.utter_message(text="नहीं menu b")
#             return [Restarted()]
        

class Opt_For_Ebill_Email_Registration_Yes_hindi(Action):
    def name(self):
        return "action_opt_for_ebill_registration_yes_hindi"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca_number = data.get("ca_number")

        data1 = registration_ebill(ca_number)
 
        # response_data = requests.post(f"{FLASK_BASE_URL}/registration_ebill", json={"ca_number": ca_number})
        # data1 = response_data.json()

        if data1.get("status") == True:
            dispatcher.utter_message(text="आपने सफलतापूर्वक ई-बिल के लिए पंजीकरण कर लिया है। भविष्य के बिल आपके ईमेल पर भेजे जाएंगे।")
            
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        else:
            dispatcher.utter_message(text="ई-बिल सेवा अभी उपलब्ध नहीं है। कृपया कुछ समय बाद पुनः प्रयास करें।")
            
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        

class Opt_For_Ebill_Email_Registration_No_hindi(Action):
    def name(self):
        return "action_opt_for_ebill_registration_no_hindi"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="ठीक है, कोई समस्या नहीं")
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]
        

class Opt_For_Ebill_Existing_Email_hindi(Action):
    def name(self):
        return "action_opt_for_ebill_existing_email_hindi"

    def run(self, dispatcher, tracker, domain):
        
        # dispatcher.utter_message(text="क्या आप ई-बिल के लिए पंजीकरण करना चाहते हैं?")
        dispatcher.utter_message(text="ईमेल आईडी सफलतापूर्वक पंजीकृत हो गई है। क्या आप पंजीकृत आईडी पर ई-बिल प्राप्त करना चाहेंगे?")
        dispatcher.utter_message(text="हाँ, सहमत b")
        dispatcher.utter_message(text="नहीं, असहमति b")
        return []

class Opt_For_Ebill_Existing_Ask_New_Email_hindi(Action):
    def name(self):
        return "action_opt_for_ebill_ask_new_email_hindi"

    def run(self, dispatcher, tracker, domain):        
        dispatcher.utter_message(text="कृपया नया ईमेल आईडी दर्ज करें।")
        return []


## Complaint Status

class Complaint_Status_english(Action):
    def name(self):
        return "action_complaint_status_english"

    def run(self, dispatcher, tracker, domain):  
        sender_id = tracker.sender_id
        print("======================== action_complaint_status_english")
        # Fetch CA number from your database or API
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        if not ca_number:
            dispatcher.utter_message(text="Unable to retrieve your CA number. Please try again.")
            return []

        # Call complaint_status API
        data1 = complaint_status(ca_number, sender_id)
        # response_data = requests.post(f"{FLASK_BASE_URL}/complaint_status", json={"ca_number": ca_number, "sender_id": sender_id})
        # data1 = response_data.json()

        if data1.get("status") == False:
            dispatcher.utter_message(text="Sorry, Having issues to fetch the status of your complain right now. Try after sometime.")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        
        else:

            print(data1, "=================================== data1")

            # Handle "No complaint found" scenario
            if "message" in data1 and data1["message"] == "No complaint found":
                dispatcher.utter_message(text="There are no active complaints for your account.")
                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
                dispatcher.utter_message(text="Yes menu b")
                dispatcher.utter_message(text="No menu b")
                return [Restarted()]

            # Handle multiple complaints
            complaints = data1.get("complaints", [])
            if not complaints:
                dispatcher.utter_message(text="There are no active complaints for your account.")
                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
                dispatcher.utter_message(text="Yes menu b")
                dispatcher.utter_message(text="No menu b")
                return [Restarted()]

            # Build a user-friendly message
            # message = "Here are your complaint details:\n"
            message = f'{send_dynamic_messages_without_dispatcher("", "complaint_status", lang="en")}\n'
            for idx, comp in enumerate(complaints, start=1):
                message += (
                    # f"\nComplaint {idx}:\n"
                    f"🔹 Opening Time: {comp.get('opening_time', 'N/A')}\n"
                    f"🔹 Status: {comp.get('status', 'N/A')}\n"
                    # f"🔹 24 Hr Count: {comp.get('comp_cnt_24hr', 'N/A')}\n"
                )
                # if comp.get("comment"):
                #     message += f"🔹 Comment: {comp['comment']}\n"
                # if comp.get("comment_hindi"):
                #     message += f"🔹 Comment (Hindi): {comp['comment_hindi']}\n"

            dispatcher.utter_message(text=message.strip())
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        

class Complaint_Status_hindi(Action):
    def name(self):
        return "action_complaint_status_hindi"

    def run(self, dispatcher, tracker, domain):  
        sender_id = tracker.sender_id
        print("======================== action_complaint_status_hindi")
        # Fetch CA number from your database or API
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        if not ca_number:
            dispatcher.utter_message(text="आपका CA नंबर प्राप्त करने में असमर्थ। कृपया दोबारा प्रयास करें।")
            return []

        # Call complaint_status API
        data1 = complaint_status(ca_number, sender_id)
        # response_data = requests.post(f"{FLASK_BASE_URL}/complaint_status", json={"ca_number": ca_number, "sender_id": sender_id})
        # data1 = response_data.json()

        if data1.get("status") == False:
            dispatcher.utter_message(text="क्षमा करें, अभी आपकी शिकायत की स्थिति प्राप्त करने में समस्या हो रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        
        else:

            print(data1, "=================================== data1")

            # Handle "No complaint found" scenario
            if "message" in data1 and data1["message"] == "No complaint found":
                dispatcher.utter_message(text="आपके खाते के लिए कोई सक्रिय शिकायत नहीं है।")
                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
                dispatcher.utter_message(text="हाँ menu b")
                dispatcher.utter_message(text="नहीं menu b")
                return [Restarted()]

            # Handle multiple complaints
            complaints = data1.get("complaints", [])
            if not complaints:
                dispatcher.utter_message(text="आपके खाते के लिए कोई सक्रिय शिकायत नहीं है।")
                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
                dispatcher.utter_message(text="हाँ menu b")
                dispatcher.utter_message(text="नहीं menu b")
                return [Restarted()]

            # Build a user-friendly message
            # message = "आपकी शिकायत का विवरण यहां दिया गया है:\n"
            message = f'{send_dynamic_messages_without_dispatcher("", "complaint_status", lang="hi")}\n'
            for idx, comp in enumerate(complaints, start=1):
                message += (
                    f"🔹 खुलने का समय: {comp.get('opening_time', 'N/A')}\n"
                    f"🔹 स्थिति: {comp.get('status', 'N/A')}\n"
                )

            dispatcher.utter_message(text=message.strip())
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]



# class Complaint_Status_hindi(Action):
#     def name(self):
#         return "action_complaint_status_hindi"

#     def run(self, dispatcher, tracker, domain):  
#         sender_id = tracker.sender_id
#         print("======================== action_complaint_status_hindi")
#         # डेटाबेस या API से CA नंबर प्राप्त करें
#         response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
#         data = response.json()

#         ca = data.get("ca_number")
#         ca_number = extract_ca_number(ca)
        
#         if not ca_number:
#             dispatcher.utter_message(text="आपका CA नंबर प्राप्त करने में असमर्थ। कृपया पुनः प्रयास करें।")
#             return []

#         # complaint_status API कॉल करें
#         response_data = requests.post(f"{FLASK_BASE_URL}/complaint_status", json={"ca_number": ca_number, "sender_id": sender_id})
#         data1 = response_data.json()

#         if data1.get("status") == False:
#             dispatcher.utter_message(text="क्षमा करें, अभी आपकी शिकायत की स्थिति प्राप्त करने में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")
#             #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        #send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
#             dispatcher.utter_message(text="हाँ menu b")
#             dispatcher.utter_message(text="नहीं menu b")
#             return [Restarted()]

#         else:
#             print(data1, "=================================== data1")

#             # "No complaint found" स्थिति संभालें
#             if "message" in data1 and data1["message"] == "No complaint found":
#                 dispatcher.utter_message(text="आपके खाते में कोई सक्रिय शिकायत नहीं है।")
#                 #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        #send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
#                 dispatcher.utter_message(text="हाँ menu b")
#                 dispatcher.utter_message(text="नहीं menu b")
#                 return [Restarted()]

#             # यदि कई शिकायतें हों
#             complaints = data1.get("complaints", [])
#             if not complaints:
#                 dispatcher.utter_message(text="आपके खाते में कोई सक्रिय शिकायत नहीं है।")
#                 #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        #send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
#                 dispatcher.utter_message(text="हाँ menu b")
#                 dispatcher.utter_message(text="नहीं menu b")
#                 return [Restarted()]

#             # उपयोगकर्ता-अनुकूल संदेश बनाएं
#             message = "आपकी शिकायतों का विवरण इस प्रकार है:\n"
#             for idx, comp in enumerate(complaints, start=1):
#                 message += (
#                     # f"\nशिकायत {idx}:\n"
#                     f"🔹 खोलने का समय: {comp.get('opening_time', 'N/A')}\n"
#                     f"🔹 स्थिति: {comp.get('status', 'N/A')}\n"
#                     # f"🔹 24 घंटे की गिनती: {comp.get('comp_cnt_24hr', 'N/A')}\n"
#                 )
#                 # if comp.get("comment"):
#                 #     message += f"🔹 टिप्पणी: {comp['comment']}\n"
#                 # if comp.get("comment_hindi"):
#                 #     message += f"🔹 टिप्पणी (हिंदी): {comp['comment_hindi']}\n"

#             dispatcher.utter_message(text=message.strip())

#             #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        #send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
#             dispatcher.utter_message(text="हाँ menu b")
#             dispatcher.utter_message(text="नहीं menu b")
#             return [Restarted()]



## Register Complaint

class Register_Complaint_english(Action):
    def name(self):
        return "action_register_complaint_english"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(text="1. No Current Complaint b")
        dispatcher.utter_message(text="2. Low Voltage or Fluctuation b")
        dispatcher.utter_message(text="2.1. Low Voltage b")
        dispatcher.utter_message(text="2.2. Voltage Fluctuation b")
        dispatcher.utter_message(text="3. Fire Complaint b")
        dispatcher.utter_message(text="4. Current Leakage b")
        return []
    

class No_Current_Complaint_english(Action):
    def name(self):
        return "action_no_current_complaint_english"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)
        
        data1 = area_outage(ca_number)
        
        # response_data = requests.post(f"{FLASK_BASE_URL}/area_outage", json={"ca_number": ca_number})
        # data1 = response_data.json()

        if data1.get('status') == True:
            dispatcher.utter_message(text=data1.get('message'))  
            dispatcher.utter_message(text="Do you still want to register a complaint?")  
            dispatcher.utter_message(text="Yes, register b")
            dispatcher.utter_message(text="No, don't register b")    

        else:
            dispatcher.utter_message(text="Sorry, Having issues to fetch the status of outage right now. Try after sometime.")
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        
        return []


class No_Current_Complaint_Register_english(Action):
    def name(self):
        return "action_no_current_complaint_register_english"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        data1 = response_mobile.json()

        tel_no = data1.get("tel_no")

        data2 = register_ncc(sender_id, ca_number, tel_no)
        
        # response_data = requests.post(f"{FLASK_BASE_URL}/register_complaint", json={"sender_id": sender_id, "ca_number": ca_number, "mobile_no": tel_no})
        # data2 = response_data.json()

        if data2.get('status') == True:

            if data2.get('comment').startswith("Dear Customer"):
                dispatcher.utter_message(text=f"{data2.get('comment')}")   
                # dispatcher.utter_message(text="Thank you for registering your complaint. Our team will respond shortly.")    
                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
                dispatcher.utter_message(text="Yes menu b")
                dispatcher.utter_message(text="No menu b")
                return [Restarted()]
            else:
                dispatcher.utter_message(text=f"{data2.get('comment')}")   
                dispatcher.utter_message(text="Thank you for registering your complaint. Our team will respond shortly.")    
                #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
                dispatcher.utter_message(text="Yes menu b")
                dispatcher.utter_message(text="No menu b")
                return [Restarted()]
        
        else:
            dispatcher.utter_message(text="Sorry, Having issues in registering your complaint right now. Try after sometime.")     
            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
            
    
class Do_Not_Register_No_Current_Complaint_Register_english(Action):
    def name(self):
        return "action_do_not_register_no_current_complaint_register_english"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(text="Sure, no problem")
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]



class Register_Complaint_hindi(Action):
    def name(self):
        return "action_register_complaint_hindi"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(text="1. कोई वर्तमान शिकायत नहीं b")
        dispatcher.utter_message(text="2. कम वोल्टेज या उतार-चढ़ाव b")
        dispatcher.utter_message(text="2.1. कम वोल्टेज b")
        dispatcher.utter_message(text="2.2. वोल्टेज उतार-चढ़ाव b")
        dispatcher.utter_message(text="3. आग से संबंधित शिकायत b")
        dispatcher.utter_message(text="4. करंट लीकेज b")
        return []



class No_Current_Complaint_hindi(Action):
    def name(self):
        return "action_no_current_complaint_hindi"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)
        
        data1 = area_outage(ca_number)

        # response_data = requests.post(f"{FLASK_BASE_URL}/area_outage", json={"ca_number": ca_number})
        # data1 = response_data.json()

        if data1.get('status') == True:
            dispatcher.utter_message(text=data1.get('message'))
            dispatcher.utter_message(text="क्या आप फिर भी शिकायत दर्ज करना चाहते हैं?")  
            dispatcher.utter_message(text="हाँ, शिकायत दर्ज करें b")
            dispatcher.utter_message(text="नहीं, शिकायत दर्ज न करें b")    

        else:
            dispatcher.utter_message(text="क्षमा करें, अभी आउटेज की स्थिति प्राप्त करने में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        
        return []


class No_Current_Complaint_Register_hindi(Action):
    def name(self):
        return "action_no_current_complaint_register_hindi"

    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        data1 = response_mobile.json()

        tel_no = data1.get("tel_no")

        data2 = register_ncc(sender_id, ca_number, tel_no)
        
        # response_data = requests.post(f"{FLASK_BASE_URL}/register_complaint", json={"sender_id": sender_id, "ca_number": ca_number, "mobile_no": tel_no})
        # data2 = response_data.json()

        if data2.get('status') == True:

            if data2.get('comment_hindi').startswith("प्रिय ग्राहक"):
                dispatcher.utter_message(text=f"{data2.get('comment_hindi')}")   
                # dispatcher.utter_message(text="Thank you for registering your complaint. Our team will respond shortly.")    
                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
                dispatcher.utter_message(text="हाँ menu b")
                dispatcher.utter_message(text="नहीं menu b")
                return [Restarted()]
            else:
                dispatcher.utter_message(text=f"{data2.get('comment_hindi')}")   
                dispatcher.utter_message(text="आपकी शिकायत दर्ज करने के लिए धन्यवाद। हमारी टीम शीघ्र ही जवाब देगी।")    

                #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
                send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
                dispatcher.utter_message(text="हाँ menu b")
                dispatcher.utter_message(text="नहीं menu b")
                return [Restarted()]
        
        else: 
            dispatcher.utter_message(text="क्षमा करें, आपकी शिकायत दर्ज करने में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")      
            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
    

class Do_Not_Register_No_Current_Complaint_Register_hindi(Action):
    def name(self):
        return "action_do_not_register_no_current_complaint_register_hindi"

    def run(self, dispatcher, tracker, domain):

        dispatcher.utter_message(text="ठीक है, कोई समस्या नहीं")
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]



class Fire_Complaint_Register_english(Action):
    def name(self):
        return "action_fire_complaint_register_english"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(f"{FLASK_BASE_URL}/register_complaint", json={"ca_number": ca_number, "tel_no": tel_no})
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"Complaint Reference Number: {data2.get('complaint_no')}")   
        # dispatcher.utter_message(text="Fault Category: Fire Complaint")
        # dispatcher.utter_message(text="Thank you for registering your complaint. Our team will respond shortly.")    


        dispatcher.utter_message(text="""Please click below to register your complain:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")

        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
    

class Fire_Complaint_Register_hindi(Action):
    def name(self):
        return "action_fire_complaint_register_hindi"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(
        #     f"{FLASK_BASE_URL}/register_complaint",
        #     json={"ca_number": ca_number, "tel_no": tel_no}
        # )
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"शिकायत संदर्भ संख्या: {data2.get('complaint_no')}")
        # dispatcher.utter_message(text="दोष श्रेणी: आग से संबंधित शिकायत")
        # dispatcher.utter_message(text="आपकी शिकायत दर्ज करने के लिए धन्यवाद। हमारी टीम शीघ्र ही प्रतिक्रिया देगी।")    

        dispatcher.utter_message(text="""कृपया अपनी शिकायत दर्ज करने के लिए नीचे दिए गए लिंक पर क्लिक करें:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")


        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]


class Current_Leakage_Complaint_Register_english(Action):
    def name(self):
        return "action_current_leakage_complaint_register_english"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(f"{FLASK_BASE_URL}/register_complaint", json={"ca_number": ca_number, "tel_no": tel_no})
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"Complaint Reference Number: {data2.get('complaint_no')}")   
        # dispatcher.utter_message(text="Fault Category: Current Leakage")
        # dispatcher.utter_message(text="Thank you for registering your complaint. Our team will respond shortly.")    

        dispatcher.utter_message(text="""Please click below to register your complain:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")

        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
    

class Current_Leakage_Complaint_Register_hindi(Action):
    def name(self):
        return "action_current_leakage_complaint_register_hindi"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(
        #     f"{FLASK_BASE_URL}/register_complaint",
        #     json={"ca_number": ca_number, "tel_no": tel_no}
        # )
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"शिकायत संदर्भ संख्या: {data2.get('complaint_no')}")
        # dispatcher.utter_message(text="दोष श्रेणी: करंट लीकेज")
        # dispatcher.utter_message(text="आपकी शिकायत दर्ज करने के लिए धन्यवाद। हमारी टीम शीघ्र ही प्रतिक्रिया देगी।")    

        dispatcher.utter_message(text="""कृपया अपनी शिकायत दर्ज करने के लिए नीचे दिए गए लिंक पर क्लिक करें:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")


        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]


class Low_Voltage_Complaint_Register_english(Action):
    def name(self):
        return "action_low_voltage_complaint_register_english"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(f"{FLASK_BASE_URL}/register_complaint", json={"ca_number": ca_number, "tel_no": tel_no})
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"Complaint Reference Number: {data2.get('complaint_no')}")   
        # dispatcher.utter_message(text="Fault Category: Low Voltage")
        # dispatcher.utter_message(text="Thank you for registering your complaint. Our team will respond shortly.")    

        dispatcher.utter_message(text="""Please click below to register your complain:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")

        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
    

class Low_Voltage_Complaint_Register_hindi(Action):
    def name(self):
        return "action_low_voltage_complaint_register_hindi"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(
        #     f"{FLASK_BASE_URL}/register_complaint",
        #     json={"ca_number": ca_number, "tel_no": tel_no}
        # )
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"शिकायत संदर्भ संख्या: {data2.get('complaint_no')}")
        # dispatcher.utter_message(text="दोष श्रेणी: कम वोल्टेज")
        # dispatcher.utter_message(text="आपकी शिकायत दर्ज करने के लिए धन्यवाद। हमारी टीम शीघ्र ही प्रतिक्रिया देगी।")  
        
          
        dispatcher.utter_message(text="""कृपया अपनी शिकायत दर्ज करने के लिए नीचे दिए गए लिंक पर क्लिक करें:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")

        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]
    

class Voltage_Fluctuation_Complaint_Register_english(Action):
    def name(self):
        return "action_voltage_fluctuation_complaint_register_english"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(f"{FLASK_BASE_URL}/register_complaint", json={"ca_number": ca_number, "tel_no": tel_no})
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"Complaint Reference Number: {data2.get('complaint_no')}")   
        # dispatcher.utter_message(text="Fault Category: Voltage Fluctuation")
        # dispatcher.utter_message(text="Thank you for registering your complaint. Our team will respond shortly.")    

        dispatcher.utter_message(text="""Please click below to register your complain:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")

        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")
        return [Restarted()]
    

class Voltage_Fluctuation_Complaint_Register_hindi(Action):
    def name(self):
        return "action_voltage_fluctuation_complaint_register_hindi"

    def run(self, dispatcher, tracker, domain):
        # sender_id = tracker.sender_id
        # response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        # data = response.json()

        # ca = data.get("ca_number")
        # ca_number = extract_ca_number(ca)

        # response_mobile = requests.post(f"{FLASK_BASE_URL}/get_session_data", json={"sender_id": sender_id})
        # data1 = response_mobile.json()

        # tel_no = data1.get("tel_no")
        
        # response_data = requests.post(
        #     f"{FLASK_BASE_URL}/register_complaint",
        #     json={"ca_number": ca_number, "tel_no": tel_no}
        # )
        # data2 = response_data.json()

        # dispatcher.utter_message(text=f"शिकायत संदर्भ संख्या: {data2.get('complaint_no')}")
        # dispatcher.utter_message(text="दोष श्रेणी: वोल्टेज उतार-चढ़ाव")
        # dispatcher.utter_message(text="आपकी शिकायत दर्ज करने के लिए धन्यवाद। हमारी टीम शीघ्र ही प्रतिक्रिया देगी।")    

        dispatcher.utter_message(text="""कृपया अपनी शिकायत दर्ज करने के लिए नीचे दिए गए लिंक पर क्लिक करें:

https://www.bsesdelhi.com/web/brpl/no-supply-complaint
""")

        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]



## Duplicate Bill 

class Duplicate_Bill_module_english(Action):
    def name(self) -> Text:
        return "action_duplicate_bill_english"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        response2 = requests.post(f"{FLASK_BASE_URL}/generate_duplicate_bill_pdf", json={"ca_number": ca_number})
        data2 = response2.json()

        if data2.get('status') == True:
            dispatcher.utter_message(text=f'{send_dynamic_messages_without_dispatcher("", "duplicate_bill", lang="en")} {data2.get("pdf_url")}')

            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]
        
        else: 
            dispatcher.utter_message(text="Sorry, Having issues to generate your duplicate bill. Try after sometime.")

            #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
            dispatcher.utter_message(text="Yes menu b")
            dispatcher.utter_message(text="No menu b")
            return [Restarted()]


class Duplicate_Bill_module_hindi(Action):
    def name(self) -> Text:
        return "action_duplicate_bill_hindi"
    
    def run(self, dispatcher, tracker, domain):
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/get_ca", json={"sender_id": sender_id})
        data = response.json()

        ca = data.get("ca_number")
        ca_number = extract_ca_number(ca)

        response2 = requests.post(f"{FLASK_BASE_URL}/generate_duplicate_bill_pdf", json={"ca_number": ca_number})
        data2 = response2.json()

        if data2.get('status') == True:
            # dispatcher.utter_message(text=f"यह रहा आपके डुप्लीकेट बिल का लिंक: {data2.get('pdf_url')}")
            dispatcher.utter_message(text=f'{send_dynamic_messages_without_dispatcher("", "duplicate_bill", lang="hi")} {data2.get("pdf_url")}')

            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]
        
        else:
            dispatcher.utter_message(text="क्षमा करें, आपकी डुप्लिकेट बिल जनरेट करने में समस्या आ रही है। कृपया कुछ समय बाद पुनः प्रयास करें।")

            #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
            send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
            dispatcher.utter_message(text="हाँ menu b")
            dispatcher.utter_message(text="नहीं menu b")
            return [Restarted()]


class billing_english(Action):
    def name(self):
        return "action_sdfg"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="""This is the balance:""")
        
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")

        return [Restarted()]
    

## Thank You Message

class thank_you_message_English(Action):
    def name(self):
        return "action_thank_you_message_english"

    def run(self, dispatcher, tracker, domain):
        #dispatcher.utter_message(text="Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="en")
        dispatcher.utter_message(text="Yes menu b")
        dispatcher.utter_message(text="No menu b")

        return [Restarted()]
    

class thank_you_message_Hindi(Action):
    def name(self):
        return "action_thank_you_message_hindi"

    def run(self, dispatcher, tracker, domain):
        #dispatcher.utter_message(text="धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)")
        send_dynamic_messages(dispatcher, "", "general_thankyou", lang="hi")
        dispatcher.utter_message(text="हाँ menu b")
        dispatcher.utter_message(text="नहीं menu b")
        return [Restarted()]


## Fallback Meahanism

from rasa_sdk.events import SlotSet, UserUtteranceReverted

class ActionCustomFallback(Action):
    def name(self):
        print("============================ action_custom_fallback")
        return "action_custom_fallback"

    def run(self, dispatcher, tracker, domain):
        print("============================ action_custom_fallback")
        sender_id = tracker.sender_id
        response = requests.post(f"{FLASK_BASE_URL}/fallback", json={"sender_id": sender_id})
        data = response.json()

        dispatcher.utter_message(text=data.get('action'))

        return [UserUtteranceReverted()]
    



