from datetime import datetime
from Model.api_key_master_model import API_Key_Master
from database import SessionLocal
import pytz

IST = pytz.timezone("Asia/Kolkata")

def get_ist_time():
    return datetime.now(IST)



def save_api_key_count(menu_option, api_name, payload, response):
    """
    Save or update a chat entry in the Session collection.

    Args:
        menu_option (str): Menu option related to the API.
        api_name (str): Name of the API or chatbot instance.
        payload (dict): Request payload sent to the API.
        response (str): API response.
    """
    db = SessionLocal()
    try:
        existing_chat = db.query(API_Key_Master).filter_by(
            menu_option=menu_option,
            api_name=api_name
        ).first()

        chat_entry = {
            "user_request": payload,
            "api_response": response,
            "api_name": api_name,
            "timestamp": get_ist_time().isoformat()
        }

        if existing_chat:
            # Update existing record
            db.query(API_Key_Master).filter_by(
                menu_option=menu_option,
                api_name=api_name
            ).update({
                "api_hit": existing_chat.api_hit + [chat_entry],
                "updated_at": get_ist_time()
            })
        else:
            # Create a new record
            chat_output = API_Key_Master(
                menu_option=menu_option,
                api_name=api_name,
                api_hit=[chat_entry],
            )
            db.add(chat_output)

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

