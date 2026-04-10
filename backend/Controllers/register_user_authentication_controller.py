

import random
from flask import jsonify, request
import requests
from Controllers.api_key_master_controller import save_api_key_count
from Models.division_model import Divisions
from Models.session_model import Session
from Controllers.rasa_webhook_controller import get_ist_time
from database import SessionLocal
from token_manager import token_manager
from Models.api_key_master_model import API_Key_Master
import xmltodict
import redis
import os

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

CA_MAX_RETRIES = 3
CA_RETRY_TTL = 600  # 10 minutes

def _increment_ca_retry(sender_id):
    """Increment Redis retry counter for CA validation. Returns (retries_left, exceeded)."""
    redis_key = f"ca_retry:{sender_id}"
    attempts = redis_client.incr(redis_key)
    if attempts == 1:
        redis_client.expire(redis_key, CA_RETRY_TTL)
    retries_left = max(CA_MAX_RETRIES - attempts, 0)
    return retries_left, attempts >= CA_MAX_RETRIES

def _reset_ca_retry(sender_id):
    redis_client.delete(f"ca_retry:{sender_id}")

def validate_ca():
    db = SessionLocal()
    try:
        try:
            sender_id = request.json.get("sender_id", "user_123")
            ca_number = request.json.get("ca_number")

            # record = API_Key_Master.find_one(api_name="CA Number Validation")
            record = db.query(API_Key_Master).filter_by(api_name="CA Number Validation").first()

            ca_validation_headers = record.api_headers or {}
            ca_validation_content_type = ca_validation_headers.get("Content-Type")
            ca_validation_soap_action = ca_validation_headers.get("SOAPAction")

            # New SOAP request URL
            # url = "https://bsesapps.bsesdelhi.com/delhiv2/ISUService.asmx?op=Z_BAPI_DSS_ISU_CA_DISPLAY"
            url = record.api_url

            # New SOAP request body (payload)
            payload = f'''<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                        xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <Z_BAPI_DSS_ISU_CA_DISPLAY xmlns="http://tempuri.org/">
                <CA_NUMBER>000{ca_number}</CA_NUMBER>
                </Z_BAPI_DSS_ISU_CA_DISPLAY>
            </soap:Body>
            </soap:Envelope>'''

            # Headers (using your token manager or JWT token)
            # headers = {
            #     'Content-Type': 'text/xml; charset=utf-8',
            #     'SOAPAction': 'http://tempuri.org/Z_BAPI_DSS_ISU_CA_DISPLAY',
            #     'Authorization': f'Bearer {token_manager.get_token("jwt")}'
            # }


            headers = {
                'Content-Type': ca_validation_content_type,
                'SOAPAction': ca_validation_soap_action,
                'Authorization': f'Bearer {token_manager.get_token("jwt")}'
            }

            # Make the SOAP request
            response = requests.post(url, headers=headers, data=payload, timeout=(10, 30))
            # response.raise_for_status()
            response_text = response.text

        except Exception as e:
            # print("======================== soap api error", e)
            retries_left, exceeded = _increment_ca_retry(sender_id)
            if exceeded:
                _reset_ca_retry(sender_id)
                return jsonify(valid=False, exceeded=True, retries_left=0,
                               message="Too many attempts. Let's start over. Click home button to start over.")
            return jsonify(valid=False, exceeded=False, retries_left=retries_left,
                           message=f"CA Validation service is unavailable. Please try again later. Retries left: {retries_left}")


        save_api_key_count("Register User Authentication","CA Number Validation", payload, response_text)

        print(response.status_code, "======================== fasouwrouask")
        if response.status_code == 500:
            print(response.status_code, "======================== fasouwrouask")
            retries_left, exceeded = _increment_ca_retry(sender_id)
            if exceeded:
                _reset_ca_retry(sender_id)
                return jsonify(valid=False, exceeded=True, retries_left=0,
                               message="Too many attempts. Let's start over. Click home button to start over.")
            return jsonify(valid=False, exceeded=False, retries_left=retries_left,
                           message=f"Please enter a valid 9 digits CA number. Retries left: {retries_left}")

        elif response.status_code == 200:
            try:
                # Parse the XML response
                parsed_dict = xmltodict.parse(response.text)

                # Extract required fields (adjust based on the new response structure)
                result_table = parsed_dict['soap:Envelope']['soap:Body']\
                    ['Z_BAPI_DSS_ISU_CA_DISPLAYResponse']['Z_BAPI_DSS_ISU_CA_DISPLAYResult']\
                    ['diffgr:diffgram']['BAPI_RESULT']['ISUSTDTable']

                tel_number = result_table.get('Tel1_Number') or result_table.get('Telephone_No')
                email = result_table.get('E_Mail')
                div_code = result_table.get('Reg_Str_Group')

                bses_user_type = result_table.get('Company_Code')

                activity = result_table.get('Move_Out_Date')
 
                if activity == '00000000' and bses_user_type == "BRPL":
                    print(response.status_code, "======================== activity")
                    retries_left, exceeded = _increment_ca_retry(sender_id)
                    if exceeded:
                        _reset_ca_retry(sender_id)
                        return jsonify(valid=False, exceeded=True, retries_left=0,
                                       message="Too many attempts. Let's start over. Click home button to start over.")
                    return jsonify(valid=False, exceeded=False, retries_left=retries_left,
                                   message=f"The provided CA number is inactive. Please enter a valid CA number. Retries left: {retries_left}")

                if bses_user_type == "BYPL":
                    print(response.status_code, "======================== fasouwrouask")
                    retries_left, exceeded = _increment_ca_retry(sender_id)
                    if exceeded:
                        _reset_ca_retry(sender_id)
                        return jsonify(valid=False, exceeded=True, retries_left=0,
                                       message="Too many attempts. Let's start over. Click home button to start over.")
                    return jsonify(valid=False, exceeded=False, retries_left=retries_left,
                                   message=f"This CA number is registered with BYPL. Kindly enter a valid CA number associated with BRPL. Retries left: {retries_left}")

                print(div_code, "=================================== division code")

                # Store data in memory and database
                # user_ca_storage[sender_id] = {
                #     "ca_number": ca_number,
                #     "tel1_no": tel_number,
                #     "email": email
                # }

                division_data = Divisions.find_one(division_code=div_code)

                division_name = None
                if division_data:
                    division_name = division_data.division_name

                print(division_name, "============================= division name")

                chat_entry = {
                    "query": ca_number,
                    # "answer": response,
                    "timestamp": get_ist_time().isoformat(),
                    # "is_fallback": is_fallback
                }

                Session.update_one(
                    {"user_id": sender_id},
                    {
                        "$push": {"chat": chat_entry},
                        "$set": {
                            "ca_number": ca_number + " BRPL",
                            "tel_no": tel_number,
                            "email": email,
                            **({"division_name": division_name} if division_name else {})  # Only include if not None
                        }
                    }
                )

                _reset_ca_retry(sender_id)
                return jsonify(valid=True)
            except KeyError:
                retries_left, exceeded = _increment_ca_retry(sender_id)
                if exceeded:
                    _reset_ca_retry(sender_id)
                    return jsonify(valid=False, exceeded=True, retries_left=0,
                                   message="Too many attempts. Let's start over. Click home button to start over.")
                return jsonify(valid=False, exceeded=False, retries_left=retries_left,
                               message=f"Please enter a valid 9 digits CA number. Retries left: {retries_left}")
        else:
            retries_left, exceeded = _increment_ca_retry(sender_id)
            if exceeded:
                _reset_ca_retry(sender_id)
                return jsonify(valid=False, exceeded=True, retries_left=0,
                               message="Too many attempts. Let's start over. Click home button to start over.")
            return jsonify(valid=False, exceeded=False, retries_left=retries_left,
                           message=f"Please enter a valid 9 digits CA number. Retries left: {retries_left}")
    except Exception as e:
        raise e
    finally:
        db.close()

## CA Validation with retries

# retry_store_ca = {}  # {sender_id: {ca_number: retry_count}}
# MAX_CA_RETRIES = 3

# def validate_ca():
#     sender_id = request.json.get("sender_id", "user_123")
#     ca_number = request.json.get("ca_number")

#     if not ca_number:
#         return jsonify({"valid": False, "error": "ca_number is required"}), 400

#     # Initialize retry store (track retries per user)
#     if sender_id not in retry_store_ca:
#         retry_store_ca[sender_id] = 0

#     record = API_Key_Master.find_one(api_name="CA Number Validation")
#     if not record:
#         return jsonify({"valid": False, "error": "API record not found"}), 500

#     ca_validation_headers = record.api_headers or {}
#     headers = {
#         "Content-Type": ca_validation_headers.get("Content-Type"),
#         "SOAPAction": ca_validation_headers.get("SOAPAction"),
#         "Authorization": f"Bearer {token_manager.get_token('jwt')}"
#     }

#     url = record.api_url
#     payload = f'''<?xml version="1.0" encoding="utf-8"?>
#     <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
#                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#       <soap:Body>
#         <Z_BAPI_DSS_ISU_CA_DISPLAY xmlns="http://tempuri.org/">
#           <CA_NUMBER>000{ca_number}</CA_NUMBER>
#         </Z_BAPI_DSS_ISU_CA_DISPLAY>
#       </soap:Body>
#     </soap:Envelope>'''

#     try:
#         response = requests.post(url, headers=headers, data=payload, timeout=10)
#     except requests.RequestException:
#         retry_store_ca[sender_id] += 1
#         retries = retry_store_ca[sender_id]
#         if retries >= MAX_CA_RETRIES:
#             retry_store_ca[sender_id] = 0
#             return jsonify({"valid": False, "exceeded": True})
#         return jsonify({
#             "valid": False,
#             "error": "Connection error",
#             "retries_left": MAX_CA_RETRIES - retries,
#             "exceeded": False
#         })

#     save_api_key_count("Register User Authentication", "CA Number Validation", payload, response.text)

#     if response.status_code == 500:
#         retry_store_ca[sender_id] += 1
#         retries = retry_store_ca[sender_id]
#         print(f"Retry {retries} =================== sender {sender_id}")
#         if retries >= MAX_CA_RETRIES:
#             retry_store_ca[sender_id] = 0
#             return jsonify({"valid": False, "exceeded": True})
#         return jsonify({
#             "valid": False,
#             "retries_left": MAX_CA_RETRIES - retries,
#             "exceeded": False
#         })

#     if response.status_code != 200:
#         retry_store_ca[sender_id] += 1
#         retries = retry_store_ca[sender_id]
#         if retries >= MAX_CA_RETRIES:
#             retry_store_ca[sender_id] = 0
#             return jsonify({"valid": False, "exceeded": True})
#         return jsonify({
#             "valid": False,
#             "error": f"Unexpected status {response.status_code}",
#             "retries_left": MAX_CA_RETRIES - retries,
#             "exceeded": False
#         })

#     try:
#         parsed_dict = xmltodict.parse(response.text)
#         result_table = parsed_dict['soap:Envelope']['soap:Body'] \
#             ['Z_BAPI_DSS_ISU_CA_DISPLAYResponse']['Z_BAPI_DSS_ISU_CA_DISPLAYResult'] \
#             ['diffgr:diffgram']['BAPI_RESULT']['ISUSTDTable']

#         tel_number = result_table.get('Tel1_Number') or result_table.get('Telephone_No')
#         email = result_table.get('E_Mail')
#         div_code = result_table.get('Reg_Str_Group')

#         division_data = Divisions.find_one(division_code=div_code)
#         division_name = division_data.division_name if division_data else None

#         Session.update_one(
#             {"user_id": sender_id},
#             {"$set": {
#                 "ca_number": ca_number,
#                 "tel_no": tel_number,
#                 "email": email,
#                 **({"division_name": division_name} if division_name else {})
#             }}
#         )

#         # Reset retries on success
#         retry_store_ca[sender_id] = 0
#         return jsonify({"valid": True})

#     except (KeyError, AttributeError):
#         retry_store_ca[sender_id] += 1
#         retries = retry_store_ca[sender_id]
#         if retries >= MAX_CA_RETRIES:
#             retry_store_ca[sender_id] = 0
#             return jsonify({"valid": False, "exceeded": True})
#         return jsonify({
#             "valid": False,
#             "retries_left": MAX_CA_RETRIES - retries,
#             "exceeded": False
#         })

def get_ca_number(sender_id):
    # sender_id = request.json.get("sender_id")
    # data = user_ca_storage.get(sender_id)

    # data = Session.find_one({'user_id': sender_id})
    data = Session.find_one(user_id=sender_id)

    # ca_number = data.get('ca_number')
    ca_number = data.ca_number

    print(ca_number, "============================ ca_number")

    if ca_number:
        return {"found":True, "ca_number":ca_number}
    else:
        return {"found":True, "message":"CA number not found for this sender_id"}

def get_ca():
    sender_id = request.json.get("sender_id")
    # data = user_ca_storage.get(sender_id)
    db = SessionLocal()
    try:
        # data = Session.find_one({'user_id': sender_id})
        # data = Session.find_one(user_id=sender_id)
        data = db.query(Session).filter_by(user_id=sender_id).first()

        # ca_number = data.get('ca_number')
        ca_number = data.ca_number

        print(ca_number, "============================ ca_number")

        if ca_number:
            return jsonify(found=True, ca_number=ca_number)
        else:
            return jsonify(found=False, message="CA number not found for this sender_id")
    except Exception as e:
        print("Error fetching CA number:", e)
        return jsonify({"found": False, "error": "something went wrong"}), 500

    finally:
        db.close()
    

def get_ca_for_division(sender_id):
    db = SessionLocal()
    try:
        # data = Session.find_one({'user_id': sender_id})
        # data = Session.find_one(user_id=sender_id)
        data = db.query(Session).filter_by(user_id=sender_id).first()

        # ca_number = data.get('ca_number')
        ca_number = data.ca_number

        print(ca_number, "============================ ca_number")

        if ca_number:
            return jsonify(found=True, ca_number=ca_number)
        else:
            return jsonify(found=False, message="CA number not found for this sender_id")
    except Exception as e:
        print("Error fetching CA number:", e)
        return jsonify({"found": False, "message": "something went wrong"}), 500

    finally:
        db.close()
    

def get_session_data():
    sender_id = request.json.get("sender_id")
    # data = user_ca_storage.get(sender_id)
    db = SessionLocal()
    try:
        # data = Session.find_one({'user_id': sender_id})
        # data = Session.find_one(user_id=sender_id)
        data = db.query(Session).filter_by(user_id=sender_id).first()

        # email = data.get('email')

        # tel_no = data.get('tel_no')
        email = data.email

        tel_no = data.tel_no

        if data:
            return jsonify(found=True, email=email, tel_no=tel_no)
        else:
            return jsonify(found=False, message="Data not found")
    except Exception as e:
        print("Error fetching session data:", e)
        return jsonify({"found": False, "message": "something went wrong"}), 500

    finally:
        db.close()

# def send_otp():
#     # Send OTP logic here
#     sender_id = request.json.get("sender_id")

#     # data = user_ca_storage.get(sender_id)

#     # data = Session.find_one({'user_id': sender_id})
#     data = Session.find_one(user_id=sender_id)

#     # tell_no = data.get('tel1_no')
#     tell_no = data.tel_no

#     otp = random.randint(100000, 999999)

#     record = API_Key_Master.find_one(api_name="Send OTP")

#     # SOAP request URL
#     # url = "https://bsesapps.bsesdelhi.com/DelhiV2/ISUService.asmx?op=SEND_BSES_SMS_API"
#     url = record.api_url

#     # Extract values safely
#     send_otp_headers = record.api_headers or {}
#     send_otp_content_type = send_otp_headers.get("Content-Type")
#     send_otp_soap_action = send_otp_headers.get("SOAPAction")

#     # XML payload
#     payload = f'''<?xml version="1.0" encoding="utf-8"?>
#     <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
#                 xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
#                 xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#         <soap:Body>
#             <SEND_BSES_SMS_API xmlns="http://tempuri.org/">
#                 <_sAppName>CHATBOT_WEBSITE</_sAppName>
#                 <_sEncryptionKey>!!B$E$@@*SMS</_sEncryptionKey>
#                 <_sCompanyCode>BRPL</_sCompanyCode>
#                 <_sVendorCode>Karix</_sVendorCode>
#                 <_sEmpCode>YourEmpCode</_sEmpCode>
#                 <_MobileNo>{tell_no}</_MobileNo>
#                 <_sOTPMsg>{otp}</_sOTPMsg>
#                 <_sSMSType>YourSMSType</_sSMSType>
#             </SEND_BSES_SMS_API>
#         </soap:Body>
#     </soap:Envelope>'''

#     # Headers
#     # headers = {
#     #     'Content-Type': 'text/xml; charset=utf-8',
#     #     'SOAPAction': '"http://tempuri.org/SEND_BSES_SMS_API"'
#     # }

#     headers = {
#         'Content-Type': send_otp_content_type,
#         'SOAPAction': send_otp_soap_action
#     }

#     # Make the request
#     response = requests.post(url, headers=headers, data=payload)
#     response.raise_for_status()
#     response_text = response.text

#     save_api_key_count("Register User Authentication","Send OTP", payload, response_text)

#     # for key in user_ca_storage:
#     #     user_ca_storage[key].update({"otp":otp})

#     Session.update_one(
#             {"user_id": sender_id},
#             {
#                 "$set": {
#                     "otp": otp,
#                     "user_type": "registered"
#                 }
#             }
#         )

#     # print(user_ca_storage, "================================ user_storage")

#     # user_ca_storage[sender_id] = {"otp":otp}

#     return jsonify(status="sent")