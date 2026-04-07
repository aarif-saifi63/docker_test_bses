

from flask import jsonify, request
import requests
from Controllers.api_key_master_controller import save_api_key_count
from Models.session_model import Session
from Controllers.rasa_webhook_controller import get_ist_time
from Models.utter_messages_model import UtterMessage
from database import SessionLocal
from token_manager import token_manager
import xml.etree.ElementTree as ET
from Models.api_key_master_model import API_Key_Master
from datetime import datetime
import pdfplumber
import re
import redis
import os

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

ORDER_ID_MAX_RETRIES = 3
ORDER_ID_RETRY_TTL = 600  # 10 minutes

## Meter Reading API
# def API_GetMeterReadingSchedule():

#     ca_number = request.json.get("ca_number")

#     if ca_number == "123456798":
#         return jsonify(found=True, message="Your meter reading schedule date lies between 20th June 2025 to 26th June 2025. Thank you.")
#     else: 
#         return jsonify(found=True, message="No meter reading scheduled currently. Please try again later.")

# def API_GetMeterReadingSchedule():
#     try:
#         ca_number = request.json.get("ca_number")

#         print(ca_number, "CA NUMBER========>>")

#         if not ca_number:
#             return jsonify(found=False, message="CA number is required"), 400
        
#         record = API_Key_Master.find_one(api_name="Get Meter Reading")
        
#         url = record.api_url

#         # Extract values safely
#         meter_reading_headers = record.api_headers or {}
#         meter_reading_content_type = meter_reading_headers.get("Content-Type")
#         meter_reading_authorization = meter_reading_headers.get("Authorization")
        

#         # External API details
#         # url = "https://bsesbrpl.co.in:7876/PMRAPI/API/Values/GetCAData_WA"
#         # headers = {
#         #     "Content-Type": "application/json",
#         #     "Authorization": "Basic YiRlJGcwMGdsZUBwcDpCU0VTR09PR0xFQVBQ"
#         # }

#         headers = {
#             "Content-Type": meter_reading_content_type,
#             "Authorization": meter_reading_authorization
#         }

#         payload = {"CANO": ca_number}

#         # Call external API
#         response = requests.post(url, headers=headers, json=payload, verify=False)  # verify=False to ignore SSL
#         response.raise_for_status()
#         response_text = response.text

#         save_api_key_count("Meter Reading Schedule","Get Meter Reading", payload, response_text)

#         if response.status_code != 200:
#             return jsonify(status=False, found=False, message="Unable to fetch data from BSES server"), 502

#         data = response.json()

#         # Handle cases based on API response
#         if data.get("Key") == "No Data Found" or not data.get("Result"):
#             return jsonify(status=True, found=True, message="No meter reading scheduled currently. Please try again later.")

#         result = data["Result"][0]

#         # Case: Solar net meter
#         if result.get("Msg"):
#             return jsonify(status=True, found=True, message=result["Msg"])

#         # Case: Normal CA number with schedule
#         actual_start = result.get("ActualStartDate")
#         actual_end = result.get("ActualEndDate")

#         if actual_start and actual_end:
#             return jsonify(
#                 status=True,
#                 found=True,
#                 message=f"Your meter reading schedule date lies between {actual_start.split(' ')[0]} to {actual_end.split(' ')[0]}. Thank you."
#             )
#         else:
#             return jsonify(status=True, found=False, message="No valid meter reading schedule found.")

#     except Exception as e:
#         return jsonify(status=False, found=False, message=f"Error: "something went wrong""), 500
    

def _increment_order_id_retry(sender_id):
    """Increment Redis retry counter for order ID. Returns (retries_left, exceeded)."""
    redis_key = f"order_id_retry:{sender_id}"
    attempts = redis_client.incr(redis_key)
    if attempts == 1:
        redis_client.expire(redis_key, ORDER_ID_RETRY_TTL)
    retries_left = max(ORDER_ID_MAX_RETRIES - attempts, 0)
    return retries_left, attempts >= ORDER_ID_MAX_RETRIES

def _reset_order_id_retry(sender_id):
    redis_client.delete(f"order_id_retry:{sender_id}")


## New Application Status API
def get_order_status():
    db = SessionLocal()
    try:
        data = request.json
        order_number = data.get("order_id")
        sender_id = data.get("sender_id")

        if not order_number:
            return jsonify({"error": "Missing order_number"}), 400


        print("Order Number Received:", order_number)

        allowed_prefixes = ("008", "8", "AN", "ON")
        if not order_number.startswith(allowed_prefixes):
            print("Order Number Received 1:", order_number)
            retries_left, exceeded = _increment_order_id_retry(sender_id)
            if exceeded:
                return jsonify({
                    "valid": False,
                    "status": False,
                    "exceeded": True,
                    "retries_left": 0,
                    "message": "Too many attempts. Let's start over. Click home button to start over",
                    "message_hindi": "बहुत अधिक प्रयास हो गए हैं। कृपया होम बटन पर क्लिक करके पुनः शुरू करें।"
                })
            return jsonify({
                "valid": False,
                "status": False,
                "exceeded": False,
                "retries_left": retries_left,
                "message": f"The Order ID entered is not valid. Please recheck and try again. Retries left: {retries_left}",
                "message_hindi": f"आपने जो ऑर्डर आईडी दर्ज की है वह मान्य नहीं है। कृपया दोबारा जांचें और फिर प्रयास करें। शेष प्रयास: {retries_left}"
            })
        
        print("Order Number Received 2:", order_number)

        # if order_number and str(order_number).startswith("8"):
        #     order_number = "00" + str(order_number)

        # record = API_Key_Master.find_one(api_name="Get Order Status")
        record = db.query(API_Key_Master).filter_by(api_name="Get Order Status").first()

        # Extract values safely
        order_status_headers = record.api_headers or {}
        order_status_content_type = order_status_headers.get("Content-Type")
        order_status_soap_action = order_status_headers.get("SOAPAction")

        # SOAP request body
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <ZBAPI_CS_ORD_STAT xmlns="http://tempuri.org/">
              <strAufnr>{order_number}</strAufnr>
            </ZBAPI_CS_ORD_STAT>
          </soap:Body>
        </soap:Envelope>"""

        # Make the POST request to the SOAP service
        # response = requests.post(
        #     url='https://bsesapps.bsesdelhi.com/Delhiv2/ISUService.asmx?op=ZBAPI_CS_ORD_STAT',
        #     headers={
        #         'Content-Type': 'text/xml; charset=utf-8',
        #         'SOAPAction': 'http://tempuri.org/ZBAPI_CS_ORD_STAT',
        #         'Authorization': f'Bearer {token_manager.get_token("jwt")}'
        #     },
        #     data=soap_body
        # )
        try:
            response = requests.post(
                url=record.api_url,
                headers={
                    'Content-Type': order_status_content_type,
                    'SOAPAction': order_status_soap_action,
                    'Authorization': f'Bearer {token_manager.get_token("jwt")}'
                },
                data=soap_body
            )
        except Exception as e:
            print("======================== soap api error", e)
            return jsonify({"status":False, "message":"Connection Status service is unavailable. Please try again later.", "message_hindi": "कनेक्शन स्थिति सेवा उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।","valid": False}), 200

        response.raise_for_status()
        response_text = response.text

        save_api_key_count("New Application Status","Get Order Status", soap_body, response_text)

        if response.status_code != 200:
            retries_left, exceeded = _increment_order_id_retry(sender_id)
            if exceeded:
                return jsonify({
                    "valid": False,
                    "status": False,
                    "exceeded": True,
                    "retries_left": 0,
                    "message": "Too many attempts. Let's start over. Click home button to start over",
                    "message_hindi": "बहुत अधिक प्रयास हो गए हैं। कृपया होम बटन पर क्लिक करके पुनः शुरू करें।"
                }), 200
            return jsonify({
                "valid": False,
                "status": False,
                "exceeded": False,
                "retries_left": retries_left,
                "message": f"The Order ID entered is not valid. Please recheck and try again. Retries left: {retries_left}",
                "message_hindi": f"आपने जो ऑर्डर आईडी दर्ज की है वह मान्य नहीं है। कृपया दोबारा जांचें और फिर प्रयास करें। शेष प्रयास: {retries_left}"
            }), 200

        # Parse XML to extract ORDER_STATUS
        root = ET.fromstring(response.content)

        # Find the ORDER_STATUS element
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'
        }

        order_status_elem = root.find(
            './/diffgr:diffgram//Result//ORDER_STATUS', namespaces)

        order_status = order_status_elem.text if order_status_elem is not None else "N/A"

        if order_status is None:
            _reset_order_id_retry(sender_id)

            thank_eng = db.query(UtterMessage).filter(
                UtterMessage.id == 10,
            ).first()

            return jsonify({
                "order_status": order_status,
                "valid": False,
                "status": False,
                "message": "There is no status available for the provided Order ID.",
                "message_hindi": "इस ऑर्डर आईडी के लिए कोई स्टेटस नहीं मिला।",
                "response": {
                    "main_menu_buttons": [
                                            "Yes",
                                            "No"
                                            ],
                    "main_menu_heading": thank_eng.text
                }
            })

        # Determine validity
        is_valid = order_status.upper() != "N/A"

        # --- Deficiency Doc API ---
        website_status = None
        def_upload = None
        try:
            def_record = db.query(API_Key_Master).filter_by(api_name="Deficiency Doc").first()
            if def_record:
                def_headers = def_record.api_headers or {}
                def_soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <CHECK_DSKDEF_VIEWUPLOAD xmlns="http://tempuri.org/">
      <_sReqNo>{order_number}</_sReqNo>
    </CHECK_DSKDEF_VIEWUPLOAD>
  </soap:Body>
</soap:Envelope>"""
                def_response = requests.post(
                    url=def_record.api_url,
                    headers={
                        'Content-Type': def_headers.get("Content-Type", "text/xml; charset=utf-8"),
                        'SOAPAction': def_headers.get("SOAPAction", ""),
                        'Authorization': f'Bearer {token_manager.get_token("jwt")}'
                    },
                    data=def_soap_body
                )
                def_root = ET.fromstring(def_response.content)
                website_status_elem = def_root.find('.//WEBSITE_STATUS')
                def_upload_elem = def_root.find('.//DEF_UPLOAD')
                # .text is None when tag is self-closing/empty e.g. <WEBSITE_STATUS />
                website_status = (website_status_elem.text or "").strip() or None
                def_upload = (def_upload_elem.text or "").strip() or None
                print("WEBSITE_STATUS:", website_status)
                print("DEF_UPLOAD:", def_upload)
                save_api_key_count("New Application Status", "Deficiency Doc", def_soap_body, def_response.text)
            else:
                print("Deficiency Doc API record not found in database")
        except Exception as def_err:
            print("Deficiency Doc API error:", def_err)
        # --- End Deficiency Doc API ---

        result = ""
        result_hindi = ""

        result_msg_eng = db.query(UtterMessage).filter(
                UtterMessage.id == 51,
            ).first()
        
        result_msg_hin = db.query(UtterMessage).filter(
                UtterMessage.id == 53,
            ).first()
        

        if order_status == "New Connection Processed":
            result = "New Connection Processed"

        elif website_status != None and def_upload != None:
            result = f"""{result_msg_eng.text}

            Click here to view deficiency: {def_upload}"""

        else:
            result = order_status


        if order_status == "New Connection Processed":
            result_hindi = "नया कनेक्शन प्रोसेस हो गया"

        elif website_status != None:
            result_hindi = f"""{result_msg_hin.text}

            कमी देखने के लिए यहाँ क्लिक करें: {def_upload}"""

        else:
            result_hindi = order_status

        

        # if order_status == "Deficiency issued for Technical Feasibility":
        #     TYPE_OF_DEFICIENCY = "BTFR"
        #     result = f"""{result_msg_eng.text}

        #     Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Auto cancelled":
        #     TYPE_OF_DEFICIENCY = "AC"
        #     result = f"""{result_msg_eng.text}
            
        #     Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Document Deficiency issued":
        #     TYPE_OF_DEFICIENCY = "DR"
        #     result = f"""{result_msg_eng.text}
            
        #     Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Deficiency issued for Commercial Feasibility":
        #     TYPE_OF_DEFICIENCY = "CFR"
        #     result = f"""{result_msg_eng.text}
            
        #     Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Deficiency issued for Commercial Feasibility/Technical Feasibility":
        #     TYPE_OF_DEFICIENCY = "BTFR+CFR"
        #     result = f"""{result_msg_eng.text}
            
        #     Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        
        # elif order_status == "Deficiency document received and Application under Process":
        #     TYPE_OF_DEFICIENCY = "DR"
        #     result = f"""{result_msg_eng.text}
            
        #     Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""

        # elif order_status == "New Connection Processed":
        #     result = "New Connection Processed"

        # else:
        #     result = order_status

        # result_hindi = ""

        # if order_status == "Deficiency issued for Technical Feasibility":
        #     TYPE_OF_DEFICIENCY = "BTFR"
        #     result_hindi = f"""{result_msg_hin.text}
            
        #     कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Auto cancelled":
        #     TYPE_OF_DEFICIENCY = "AC"
        #     result_hindi = f"""{result_msg_hin.text}
            
        #     कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Document Deficiency issued":
        #     TYPE_OF_DEFICIENCY = "DR"
        #     result_hindi = f"""{result_msg_hin.text}
            
        #     कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Deficiency issued for Commercial Feasibility":
        #     TYPE_OF_DEFICIENCY = "CFR"
        #     result_hindi = f"""{result_msg_hin.text}
            
        #     कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        # elif order_status == "Deficiency issued for Commercial Feasibility/Technical Feasibility":
        #     TYPE_OF_DEFICIENCY = "BTFR+CFR"
        #     result_hindi = f"""{result_msg_hin.text}
            
        #     कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""

        # elif order_status == "Deficiency document received and Application under Process":
        #     TYPE_OF_DEFICIENCY = "DR"
        #     result_hindi = f"""{result_msg_hin.text}
        #     कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""

        # elif order_status == "New Connection Processed":
        #     result_hindi = "नया कनेक्शन प्रोसेस हो गया"

        # # elif order_status == "Deficiency document received and Application under Process":
        # #     result_hindi = "कमी (डिफ़िशिएंसी) दस्तावेज़ प्राप्त हो गए हैं और आवेदन प्रक्रिया में है।"

        # else:
        #     result_hindi = order_status

        if is_valid == False:
            _reset_order_id_retry(sender_id)

            thank_eng = db.query(UtterMessage).filter(
                UtterMessage.id == 10,
            ).first()

            return jsonify({
                "order_status": order_status,
                "valid": is_valid,
                "status": False,
                "message": "Currently, the Status is not available. Please reach out to the concerned authorities for any questions.",
                "message_hindi": "वर्तमान में स्थिति उपलब्ध नहीं है। किसी भी प्रश्न के लिए कृपया संबंधित अधिकारियों से संपर्क करें।",
                "response": {
                    "main_menu_buttons": [
                                            "Yes",
                                            "No"
                                            ],
                    "main_menu_heading": thank_eng.text
                }
            })
        
        print("Order Status:", order_status, "Is Valid:", is_valid)

        existing_chat = Session.find_one(user_id=sender_id)

        if existing_chat:
            last_item = existing_chat.chat[-1]
            heading_list = last_item["answer"]["response"].get("heading", [])

            last_heading = heading_list[-1] if heading_list else None
        else:
            last_heading = None

        print("Last Heading:", last_heading)

        order_stat_msg = db.query(UtterMessage).filter(
                UtterMessage.id == 50,
            ).first()

        if last_heading == f"{order_stat_msg.text}":

            print("Inside last heading condition", result)

            response = {
                'response': {
                    "heading": [
                        result
                    ],
                    "buttons": []
                }
            }
            chat_entry = {
                    "query": order_number,
                    "answer": response,
                    "timestamp": get_ist_time().isoformat()
                }
            
        else:
            chat_entry = {
                    "query": order_number,
                    "answer": result_hindi,
                    "timestamp": get_ist_time().isoformat()
                }

        Session.update_one(
            {"user_id": sender_id},
            {
                "$push": {"chat": chat_entry},
                "$set": {
                    "updated_at": get_ist_time().isoformat()
                }
            }
        )

        _reset_order_id_retry(sender_id)

        uttter_message_id = [
            51,53
        ]

        return jsonify({
            "order_status": order_status,
            "valid": is_valid,
            "status": True,
            "message": result,
            "message_hindi": result_hindi,
            "uttter_message_id": uttter_message_id
        })

    except Exception as e:
        return jsonify({"message": "Connection Status service is unavailable. Please try again later.", "message_hindi": "कनेक्शन स्टेटस सेवा उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।","status": False, "valid": False}), 200
    finally:
        db.close()

