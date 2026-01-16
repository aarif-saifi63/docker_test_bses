from datetime import datetime
import os
import random
import re
from html import unescape
import requests
from Model.api_key_master_model import API_Key_Master
from Model.division_model import Divisions
from Model.session_model import Session
import xmltodict
from database import SessionLocal
from token_manager import token_manager
import xml.etree.ElementTree as ET
from utils.save_api_count import save_api_key_count
import redis
from dotenv import load_dotenv
load_dotenv()

# Redis connection
# redis_client = redis.Redis(
#     host="localhost",
#     port=6379,
#     db=0,
#     decode_responses=True
# )

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)


## Validate_ca

def validate_ca(sender_id, ca_number):
    db = SessionLocal()
    try:
        # Fetch API details for CA validation
        record = db.query(API_Key_Master).filter_by(api_name="CA Number Validation").first()
        if not record:
            return {"valid": False, "message": "CA validation API not configured."}

        # Extract headers safely
        ca_validation_headers = record.api_headers or {}
        ca_validation_content_type = ca_validation_headers.get("Content-Type")
        ca_validation_soap_action = ca_validation_headers.get("SOAPAction")

        # SOAP URL
        url = record.api_url

        # SOAP request body
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

        # Headers with auth token
        headers = {
            'Content-Type': ca_validation_content_type,
            'SOAPAction': ca_validation_soap_action,
            'Authorization': f'Bearer {token_manager.get_token("jwt")}'
        }

        try:
            response = requests.post(url, headers=headers, data=payload)
            response_text = response.text
        except Exception as e:
            print("======================== SOAP API error:", e)
            return {"valid": False, "message": "CA Validation service unavailable."}

        # Log API call
        save_api_key_count("Register User Authentication", "CA Number Validation", payload, response_text)

        # Response handling
        if response.status_code == 500:
            return {"valid": False}

        elif response.status_code == 200:
            try:
                parsed_dict = xmltodict.parse(response.text)
                result_table = parsed_dict['soap:Envelope']['soap:Body']\
                    ['Z_BAPI_DSS_ISU_CA_DISPLAYResponse']['Z_BAPI_DSS_ISU_CA_DISPLAYResult']\
                    ['diffgr:diffgram']['BAPI_RESULT']['ISUSTDTable']

                tel_number = result_table.get('Tel1_Number') or result_table.get('Telephone_No')
                email = result_table.get('E_Mail')
                div_code = result_table.get('Reg_Str_Group')

                # Fetch division name
                division = db.query(Divisions).filter_by(division_code=div_code).first()
                division_name = division.division_name if division else None

                # Update Session record
                db.query(Session).filter_by(user_id=sender_id).update({
                    "ca_number": ca_number,
                    "tel_no": tel_number,
                    "email": email,
                    **({"division_name": division_name} if division_name else {})
                })

                db.commit()
                return {"valid": True}

            except KeyError:
                db.rollback()
                return {"valid": False}

        else:
            return {"valid": False}

    except Exception as e:
        db.rollback()
        print("Unexpected error in validate_ca:", e)
        return {"valid": False, "message": "Internal error."}

    finally:
        db.close()

## Send OTP

# def send_otp(sender_id):
#     db = SessionLocal()
#     try:
#         # Fetch user session
#         data = db.query(Session).filter_by(user_id=sender_id).first()
#         if not data:
#             return {"status": "user_not_found"}

#         tell_no = data.tel_no
#         otp = random.randint(100000, 999999)

#         # Fetch API key record
#         record = db.query(API_Key_Master).filter_by(api_name="Send OTP").first()
#         if not record:
#             return {"status": "api_not_configured"}

#         url = record.api_url
#         send_otp_headers = record.api_headers or {}
#         send_otp_content_type = send_otp_headers.get("Content-Type")
#         send_otp_soap_action = send_otp_headers.get("SOAPAction")

#         # XML payload
#         payload = f'''<?xml version="1.0" encoding="utf-8"?>
#         <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
#                        xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
#                        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#             <soap:Body>
#                 <SEND_BSES_SMS_API xmlns="http://tempuri.org/">
#                     <_sAppName>CHATBOT_WEBSITE</_sAppName>
#                     <_sEncryptionKey>!!B$E$@@*SMS</_sEncryptionKey>
#                     <_sCompanyCode>BRPL</_sCompanyCode>
#                     <_sVendorCode>Karix</_sVendorCode>
#                     <_sEmpCode>YourEmpCode</_sEmpCode>
#                     <_MobileNo>{tell_no}</_MobileNo>
#                     <_sOTPMsg>{otp}</_sOTPMsg>
#                     <_sSMSType>YourSMSType</_sSMSType>
#                 </SEND_BSES_SMS_API>
#             </soap:Body>
#         </soap:Envelope>'''

#         headers = {
#             'Content-Type': send_otp_content_type,
#             'SOAPAction': send_otp_soap_action
#         }

#         try:
#             response = requests.post(url, headers=headers, data=payload)
#             response.raise_for_status()
#             response_text = response.text
#         except Exception:
#             return {"status": "unsent"}

#         # Log API hit
#         save_api_key_count("Register User Authentication", "Send OTP", payload, response_text)

#         # Update user OTP and type
#         data.otp = otp
#         data.user_type = "registered"
#         db.commit()

#         return {"status": "sent"}

#     except Exception as e:
#         db.rollback()
#         raise e
#     finally:
#         db.close()

OTP_LIMIT = 3          # 3 OTPs allowed
OTP_WINDOW_SECONDS = 60  # in 10 minutes



# def send_otp(sender_id):
#     db = SessionLocal()
#     try:
#         # Fetch user session
#         data = db.query(Session).filter_by(user_id=sender_id).first()
#         if not data:
#             return {"status": "user_not_found"}

#         tell_no = data.tel_no   
#         ca_number = data.ca_number# we will use this for OTP rate limit key
#         otp = random.randint(100000, 999999)

#         # -------------------------------
#         # 🔥 OTP RATE LIMIT CHECK (Redis)
#         # -------------------------------
#         redis_key = f"otp_rate_limit:{ca_number}"

#         attempts = redis_client.get(redis_key)
#         attempts = int(attempts) if attempts else 0

#         if attempts >= OTP_LIMIT:
#             ttl_remaining = redis_client.ttl(redis_key)
#             return {
#                 "status": "rate_limited",
#                 "message": f"OTP limit exceeded. Try again after {ttl_remaining} seconds."
#             }

#         # If under limit, increment the counter
#         pipe = redis_client.pipeline()
#         pipe.incr(redis_key)
#         if attempts == 0:
#             pipe.expire(redis_key, OTP_WINDOW_SECONDS)
#         pipe.execute()
#         # -------------------------------


#         # Fetch API key record
#         record = db.query(API_Key_Master).filter_by(api_name="Send OTP").first()
#         if not record:
#             return {"status": "api_not_configured"}

#         url = record.api_url
#         send_otp_headers = record.api_headers or {}
#         send_otp_content_type = send_otp_headers.get("Content-Type")
#         send_otp_soap_action = send_otp_headers.get("SOAPAction")

#         # XML payload
#         payload = f'''<?xml version="1.0" encoding="utf-8"?>
#         <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
#                        xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
#                        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#             <soap:Body>
#                 <SEND_BSES_SMS_API xmlns="http://tempuri.org/">
#                     <_sAppName>CHATBOT_WEBSITE</_sAppName>
#                     <_sEncryptionKey>!!B$E$@@*SMS</_sEncryptionKey>
#                     <_sCompanyCode>BRPL</_sCompanyCode>
#                     <_sVendorCode>Karix</_sVendorCode>
#                     <_sEmpCode>YourEmpCode</_sEmpCode>
#                     <_MobileNo>{tell_no}</_MobileNo>
#                     <_sOTPMsg>{otp}</_sOTPMsg>
#                     <_sSMSType>YourSMSType</_sSMSType>
#                 </SEND_BSES_SMS_API>
#             </soap:Body>
#         </soap:Envelope>'''

#         headers = {
#             'Content-Type': send_otp_content_type,
#             'SOAPAction': send_otp_soap_action
#         }

#         # Send OTP through API
#         try:
#             response = requests.post(url, headers=headers, data=payload)
#             response.raise_for_status()
#             response_text = response.text
#         except Exception:
#             return {"status": "unsent"}

#         # Log API hit
#         save_api_key_count("Register User Authentication", "Send OTP", payload, response_text)

#         # Update user OTP and type
#         data.otp = otp
#         data.user_type = "registered"
#         data.otp_is_verified = "no"
#         db.commit()

#         return {"status": "sent"}

#     except Exception as e:
#         db.rollback()
#         raise e
#     finally:
#         db.close()


def send_otp(sender_id):
    db = SessionLocal()
    try:
        # Fetch user session
        data = db.query(Session).filter_by(user_id=sender_id).first()
        if not data:
            return {"status": "user_not_found"}
 
        tell_no = data.tel_no   
        ca_number = data.ca_number# we will use this for OTP rate limit key
        otp = random.randint(100000, 999999)
 
        # -------------------------------
        # 🔥 OTP RATE LIMIT CHECK (Redis)
        # -------------------------------
        redis_key = f"otp_rate_limit:{ca_number}"
 
        attempts = redis_client.get(redis_key)
        attempts = int(attempts) if attempts else 0
 
        if attempts >= OTP_LIMIT:
            ttl_remaining = redis_client.ttl(redis_key)
            return {
                "status": "rate_limited",
                "message": f"OTP limit exceeded. Try again after {ttl_remaining} seconds."
            }
 
        # If under limit, increment the counter
        pipe = redis_client.pipeline()
        pipe.incr(redis_key)
        if attempts == 0:
            pipe.expire(redis_key, OTP_WINDOW_SECONDS)
        pipe.execute()
        # -------------------------------
 
 
        # Fetch API key record
        record = db.query(API_Key_Master).filter_by(api_name="Send OTP").first()
        if not record:
            return {"status": "api_not_configured"}
 
        url = record.api_url
        send_otp_headers = record.api_headers or {}
        send_otp_content_type = send_otp_headers.get("Content-Type")
        send_otp_soap_action = send_otp_headers.get("SOAPAction")
 
        # XML payload
        payload = f'''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <SEND_BSES_SMS_API xmlns="http://tempuri.org/">
                    <_sAppName>CHATBOT_WEBSITE</_sAppName>
                    <_sEncryptionKey>!!B$E$@@*SMS</_sEncryptionKey>
                    <_sCompanyCode>BRPL</_sCompanyCode>
                    <_sVendorCode>Karix</_sVendorCode>
                    <_sEmpCode>YourEmpCode</_sEmpCode>
                    <_MobileNo>{tell_no}</_MobileNo>
                    <_sOTPMsg>{otp}</_sOTPMsg>
                    <_sSMSType>YourSMSType</_sSMSType>
                </SEND_BSES_SMS_API>
            </soap:Body>
        </soap:Envelope>'''
 
        headers = {
            'Content-Type': send_otp_content_type,
            'SOAPAction': send_otp_soap_action
        }
 
        response_text = ""

        # Send OTP through API
        try:
            response = requests.post(url, headers=headers, data=payload)
        
            response.raise_for_status()
            response_text = response.text

        except Exception:
            return {"status": "unsent", "message": response_text}

        root = ET.fromstring(response_text)

        # Find FLAG ignoring namespaces
        flag = root.find(".//{*}Table1/{*}FLAG")

        if flag.text != "S":
            print("FLAG:", flag.text)
            return {"status": "unsent", "message": response_text}
        
        print("OTP API Response Text:", response_text)

 
        # Log API hit
        save_api_key_count("Register User Authentication", "Send OTP", payload, response_text)
 
        # Update user OTP and type
        data.otp = otp
        data.user_type = "registered"
        data.otp_is_verified = "no"
        db.commit()
 
        return {"status": "sent"}
 
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


## Consumption History

def get_pdf_bill(ca_number):
    # data = request.json
    # ca_number = data.get("ca_number")

    if not ca_number:
        return {"error": "Missing CA number"}
    
    db = SessionLocal()
    try:
    
        # record = API_Key_Master.find_one(api_name="Consumption History PDF")
        record = db.query(API_Key_Master).filter_by(api_name="Consumption History PDF").first()

        # CONSUMPTION_HISTORY_URL = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx"

        CONSUMPTION_HISTORY_URL = record.api_url


        # Extract values safely
        cons_history_headers = record.api_headers or {}
        cons_history_content_type = cons_history_headers.get("Content-Type")
        cons_history_soap_action = cons_history_headers.get("SOAPAction")

        # Construct the SOAP XML payload
        soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <ZBAPI_BILL_DET_API_PDF xmlns="http://tempuri.org/">
        <CA_NUMBER>{ca_number}</CA_NUMBER>
        <_sMobileNo></_sMobileNo>
        </ZBAPI_BILL_DET_API_PDF>
    </soap:Body>
    </soap:Envelope>'''

        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": "http://tempuri.org/ZBAPI_BILL_DET_API_PDF",
        #     "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'  # Replace with valid token
        # }

        headers = {
            "Content-Type": cons_history_content_type,
            "SOAPAction": cons_history_soap_action,
            "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'  # Replace with valid token
        }

        try:
            # Step 1: Get the PDF link
            response = requests.post(CONSUMPTION_HISTORY_URL, data=soap_body, headers=headers)
            response.raise_for_status()
            response_text = response.text

            save_api_key_count("Consumption History","Consumption History PDF", soap_body, response_text)

            root = ET.fromstring(response.text)
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'
            }

            output_text = root.find(".//diffgr:diffgram//NewDataSet//Table1//OUT_PUT", namespaces)

            return {"message": output_text.text, "status": True}
        
        except Exception as e:
            return {"message": "Error in fetching consumption history", "status": False}
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

## Meter Reading

def API_GetMeterReadingSchedule(ca_number):
    db = SessionLocal()
    try:
        # ca_number = request.json.get("ca_number")

        print(ca_number, "CA NUMBER========>>")

        if not ca_number:
            return {"found":False, "message":"CA number is required"}
        
        # record = API_Key_Master.find_one(api_name="Get Meter Reading")
        record = db.query(API_Key_Master).filter_by(api_name="Get Meter Reading").first()
        
        url = record.api_url

        # Extract values safely
        meter_reading_headers = record.api_headers or {}
        meter_reading_content_type = meter_reading_headers.get("Content-Type")
        meter_reading_authorization = meter_reading_headers.get("Authorization")
        

        # External API details
        # url = "https://bsesbrpl.co.in:7876/PMRAPI/API/Values/GetCAData_WA"
        # headers = {
        #     "Content-Type": "application/json",
        #     "Authorization": "Basic YiRlJGcwMGdsZUBwcDpCU0VTR09PR0xFQVBQ"
        # }

        headers = {
            "Content-Type": meter_reading_content_type,
            "Authorization": meter_reading_authorization
        }

        payload = {"CANO": ca_number}

        # Call external API
        response = requests.post(url, headers=headers, json=payload, verify=False)  # verify=False to ignore SSL
        response.raise_for_status()
        response_text = response.text

        save_api_key_count("Meter Reading Schedule","Get Meter Reading", payload, response_text)

        if response.status_code != 200:
            return {"status":False, "found":False, "message":"Unable to fetch data from BSES server"}

        data = response.json()

        # Handle cases based on API response
        if data.get("Key") == "No Data Found" or not data.get("Result"):
            return {"status":True, "found":True, "message":"No meter reading scheduled currently. Please try again later."}

        result = data["Result"][0]

        # Case: Solar net meter
        if result.get("Msg"):

            if result["Msg"] == "This is Solar Net Meter CA Number, Self Meter Reading is currently not allowed for this category. The meter reading will be done as per schedule":
                return {"status":True, "found":True, "message":"No record found."}
            
            return {"status":True, "found":True, "message":result["Msg"]}

        # Case: Normal CA number with schedule
        actual_start = result.get("ActualStartDate")
        actual_end = result.get("ActualEndDate")

        if actual_start and actual_end:
            return {
                "status":True,
                "found":"True",
                "message":f"Your meter reading date lies between {actual_start.split(' ')[0]} to {actual_end.split(' ')[0]}."
            }
        else:
            return {"status":True, "found":False, "message":"No valid meter reading schedule found."}

    except Exception as e:
        db.rollback()
        return {"status":False, "found":False, "message":f"Error: {str(e)}"}
    finally:
        db.close()

## New Connection Status

def get_order_status(order_number):
    db = SessionLocal()
    try:
        # data = request.json
        # order_number = data.get("order_id")
        if not order_number:
            return {"error": "Missing order_number"}
        

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

        response = requests.post(
            url=record.api_url,
            headers={
                'Content-Type': order_status_content_type,
                'SOAPAction': order_status_soap_action,
                'Authorization': f'Bearer {token_manager.get_token("jwt")}'
            },
            data=soap_body
        )
        response.raise_for_status()
        response_text = response.text

        save_api_key_count("New Application Status","Get Order Status", soap_body, response_text)

        if response.status_code != 200:
            return {"error": "Failed to fetch data from SOAP service", "status": False}

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

        # Determine validity
        is_valid = order_status.upper() != "N/A"

        return {
            "order_status": order_status,
            "valid": is_valid,
            "status": True
        }

    except Exception as e:
        return {"error": str(e), "status": False}
    finally:
        db.close()
    


## Duplicate Bill


# def generate_duplicate_bill_pdf(ca_number):
#     try:
#         # data = request.json
#         # ca_number = request.json.get("ca_number")
#         # ebsk_no = request.json.get("ebsk_no", "")

#         ebsk_no = ""

#         print(ca_number, "====================== ca number")

#         record = API_Key_Master.find_one(api_name="Duplicate Bill PDF")

#         if not ca_number:
#             return {"error": "Missing CA Number", "status": False}
        
#         # DUPLICATE_BILL_SOAP_URL = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx?op=ZBAPI_ONLINE_BILL_PDF"
#         # DUPLICATE_BILL_SOAP_ACTION = "http://tempuri.org/ZBAPI_ONLINE_BILL_PDF"

#         DUPLICATE_BILL_SOAP_URL = record.api_url

#         duplicate_bill_headers = record.api_headers or {}
#         duplicate_bill_content_type = duplicate_bill_headers.get("Content-Type")
#         duplicate_bill_soap_action = duplicate_bill_headers.get("SOAPAction")

#         # SOAP Request Body
#         soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
# <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#   <soap:Body>
#     <ZBAPI_ONLINE_BILL_PDF xmlns="http://tempuri.org/">
#       <strCANumber>000{ca_number}</strCANumber>
#       <strEBSKNO>{ebsk_no}</strEBSKNO>
#     </ZBAPI_ONLINE_BILL_PDF>
#   </soap:Body>
# </soap:Envelope>'''

#         # headers = {
#         #     "Content-Type": "text/xml; charset=utf-8",
#         #     "SOAPAction": DUPLICATE_BILL_SOAP_ACTION,
#         #     "Authorization": f'Bearer {token_manager.get_token("jwt")}'
#         # }

#         headers = {
#             "Content-Type": duplicate_bill_content_type,
#             "SOAPAction": duplicate_bill_soap_action,
#             "Authorization": f'Bearer {token_manager.get_token("jwt")}'
#         }

#         # Send SOAP Request
#         response = requests.post(DUPLICATE_BILL_SOAP_URL, headers=headers, data=soap_body, timeout=30)
#         response.raise_for_status()
#         response_text = response.text

#         save_api_key_count("Duplicate Bill","Duplicate Bill PDF", soap_body, response_text)

#         if response.status_code != 200:
#             return {"error": "Failed to fetch data from SOAP API", "status_code": response.status_code, "status": False}

#         # Clean invalid XML characters (e.g., &#x0;)
#         cleaned_xml = re.sub(r'&#x0;|[\x00-\x08\x0B\x0C\x0E-\x1F]', '', response.text)

#         # Parse XML
#         root = ET.fromstring(cleaned_xml)

#         # Extract Tdline elements
#         tdlines = []
#         for elem in root.findall('.//ZPDFTable/Tdline'):
#             if elem.text:
#                 tdlines.append(unescape(elem.text))

#         if not tdlines:
#             return {"error": "No valid Tdline content found", "status": False}

#         # Create PDF content
#         pdf_content = "\n".join(tdlines)
#         pdf_bytes = pdf_content.encode('latin1', errors='ignore')

#         # Save PDF with timestamp
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         filename = f"bill_{ca_number}_{timestamp}.pdf"
#         filepath = os.path.join(PDF_FOLDER, filename)

#         with open(filepath, "wb") as f:
#             f.write(pdf_bytes)

#         print(filepath, "========================= filepath")

#         file_url = f'{flask_url}/Media/generated_pdfs/{filename}'

#         # Return URL to access the file
#         # file_url = url_for('serve_pdf', filename=filename, _external=True)

#         return {
#             "message": "PDF generated successfully",
#             "pdf_url": file_url,
#             "status": True
#         }

#     except Exception as e:
#         return {"error": str(e), "status": False}


## Payment Hisotry


def create_soap_request(ca_number):
    return f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                   xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <ZBI_WEBBILL_HIST xmlns="http://tempuri.org/">
          <CA_NUMBER>000{ca_number}</CA_NUMBER>
        </ZBI_WEBBILL_HIST>
      </soap:Body>
    </soap:Envelope>"""

def get_payment_history(ca_number):
    # ca_number = request.json.get("ca_number")
    if not ca_number:
        return {"error": "Missing CA number"}
    
    db = SessionLocal()
    
    try:
        # record = API_Key_Master.find_one(api_name="Payment History Data")
        record = db.query(API_Key_Master).filter_by(api_name="Payment History Data").first()
        
        # SOAP_URL = "https://bsesapps.bsesdelhi.com/delhiv2/ISUService.asmx?op=ZBI_WEBBILL_HIST"
        # SOAP_ACTION = "http://tempuri.org/ZBI_WEBBILL_HIST"

        SOAP_URL = record.api_url

        # Extract values safely
        payment_his_headers = record.api_headers or {}
        payment_his_content_type = payment_his_headers.get("Content-Type")
        payment_his_soap_action = payment_his_headers.get("SOAPAction")

        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": SOAP_ACTION,
        #     "Authorization": f'Bearer {token_manager.get_token("jwt")}'
        # }

        headers = {
            "Content-Type": payment_his_content_type,
            "SOAPAction": payment_his_soap_action,
            "Authorization": f'Bearer {token_manager.get_token("jwt")}'
        }

        try:
            response = requests.post(SOAP_URL, headers=headers, data=create_soap_request(ca_number))
            response.raise_for_status()
            response_text = response.text

            save_api_key_count("Payment History","Payment History Data", create_soap_request(ca_number), response_text)

            if response.status_code != 200:
                return {"error": "SOAP request failed", "status": False}

            # Parse XML
            root = ET.fromstring(response.content)

            # Get all bill history entries
            ns = {'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'}
            tables = root.findall('.//diffgr:diffgram//webBillHistoryTable', ns)

            # Handle invalid CA number (no billing data)
            if not tables:
                return {
                    "message": "Invalid CA number or no billing history available.",
                    "data": []
                }

            bill_data = []

            for table in tables:
                bill_month = table.findtext("BILL_MONTH", default="")
                date_of_invoice = table.findtext("DATE_OF_INVOICE", default="")
                due_date = table.findtext("DUE_DATE", default="")
                net_amount = table.findtext("NET_AMNT", default="")
                payment_date = table.findtext("PAYMENT_DATE", default="")
                payment_amount = table.findtext("PAYMENT_AMOUNT", default="")
                units = table.findtext("UNITS", default="")
                total_bill_amt = table.findtext("TOT_BIL_AMT", default="")

                bill_data.append({
                    "Bill Month": bill_month,
                    "Date of Invoice": format_date(date_of_invoice),
                    "Due Date": format_date(due_date),
                    "Net Amount to be Paid": net_amount,
                    "Payment Date": format_date(payment_date),
                    "Payment Amount": payment_amount,
                    "Units Consumed": units,
                    "Total Bill Amt": total_bill_amt
                })

            # Sort bills by month in descending order
            sorted_bills = sorted(bill_data, key=lambda x: parse_bill_month(x["Bill Month"]), reverse=True)

            # Collect up to 6 bills skipping ones with payment_amount == 0.00
            recent_six = []
            for bill in sorted_bills:
                if bill["Payment Amount"] != "0.00":
                    recent_six.append(bill)
                if len(recent_six) == 6:
                    break

            return {"entries": recent_six, "status": True}
        
        except Exception as e:
            return {"message": "Error in fetching payment history", "status": False}
    except Exception as e:
        raise e
    finally:
        db.close()


def parse_bill_month(bill_month):
    try:
        return datetime.strptime(bill_month, "%b-%y")
    except:
        return datetime.min

def format_date(raw_date):
    if raw_date and raw_date != "00000000":
        try:
            return datetime.strptime(raw_date, "%Y%m%d").strftime("%d-%m-%Y")
        except:
            return raw_date
    return ""


## Bill History

def get_bill_history(ca_number):
    # ca_number = request.json.get("ca_number")
    if not ca_number:
        return {"error": "Missing CA number"}
    
    db = SessionLocal()
    try:
        # record = API_Key_Master.find_one(api_name="Bill History Data")
        record = db.query(API_Key_Master).filter_by(api_name="Bill History Data").first()

        SOAP_URL = record.api_url

        # Extract values safely
        bill_his_headers = record.api_headers or {}
        bill_his_content_type = bill_his_headers.get("Content-Type")
        bill_his_soap_action = bill_his_headers.get("SOAPAction")

        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": SOAP_ACTION,
        #     "Authorization": f'Bearer {token_manager.get_token("jwt")}'
        # }

        headers = {
            "Content-Type": bill_his_content_type,
            "SOAPAction": bill_his_soap_action,
            "Authorization": f'Bearer {token_manager.get_token("jwt")}'
        }

        try:

            response = requests.post(SOAP_URL, headers=headers, data=create_soap_request(ca_number))
            response.raise_for_status()
            response_text = response.text

            save_api_key_count("Bill History","Bill History Data", create_soap_request(ca_number), response_text)

            if response.status_code != 200:
                return {"error": "SOAP request failed", "status": False}

            # Parse XML
            root = ET.fromstring(response.content)

            # Get all bill history entries
            ns = {'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'}
            tables = root.findall('.//diffgr:diffgram//webBillHistoryTable', ns)

            # Handle invalid CA number (no billing data)
            if not tables:
                return {
                    "message": "Invalid CA number or no billing history available.",
                    "data": []
                }

            bill_data = []

            for table in tables:
                bill_month = table.findtext("BILL_MONTH", default="")
                date_of_invoice = table.findtext("DATE_OF_INVOICE", default="")
                due_date = table.findtext("DUE_DATE", default="")
                net_amount = table.findtext("NET_AMNT", default="")
                payment_date = table.findtext("PAYMENT_DATE", default="")
                payment_amount = table.findtext("PAYMENT_AMOUNT", default="")
                units = table.findtext("UNITS", default="")
                invoice_no = table.findtext("INVOICE_NO", default="")
                current_bill_amount = table.findtext("CUR_MTH_BILL_AMT", default="")


                bill_data.append({
                    "Bill Month": bill_month,
                    "Date of Invoice": format_date(date_of_invoice),
                    "Due Date": format_date(due_date),
                    "Net Amount to be Paid": net_amount,
                    "Payment Date": format_date(payment_date),
                    "Payment Amount": payment_amount,
                    "Units Consumed": units,
                    "Invoice No": invoice_no,
                    "Current Bill Amount": current_bill_amount
                })

            # Sort bills by month in descending order
            sorted_bills = sorted(bill_data, key=lambda x: parse_bill_month(x["Bill Month"]), reverse=True)

            # Collect up to 6 bills skipping ones with payment_amount == 0.00
            # recent_six = []
            # for bill in sorted_bills:
            #     if bill["Payment Amount"] != "0.00":
            #         recent_six.append(bill)
            #     if len(recent_six) == 6:
            #         break

            recent_six = sorted_bills[:6]

            return {"entries": recent_six, "status": True}

        except Exception as e:
            return {"message": "Error in fetching bill history", "status": False}
    except Exception as e:
        raise e
    finally:
        db.close()

## Opt for e-bill

def update_missing_email(ca_number, email):
    # data = request.json
    # ca_number = data.get("ca_number")
    # email = data.get("email")
    
    if not ca_number or not email:
        return {"error": "Both ca_number and email are required"}
    
    record = API_Key_Master.find_one(api_name="Update Missing Email")
    
    # SOAP_URL_EBILL = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx?op=ZBAPI_UPDATE_TNO"
    # SOAP_ACTION_EBILL = "http://tempuri.org/ZBAPI_UPDATE_TNO"

    SOAP_URL_EBILL = record.api_url

    # Extract values safely
    update_email_headers = record.api_headers or {}
    update_email_content_type = update_email_headers.get("Content-Type")
    update_email_soap_action = update_email_headers.get("SOAPAction")

    # Build SOAP request dynamically
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
      <soap:Body>
        <ZBAPI_UPDATE_TNO xmlns="http://tempuri.org/">
          <strCA_no>{ca_number}</strCA_no>
          <strTelephone></strTelephone>
          <strMobile></strMobile>
          <strEmail>{email}</strEmail>
          <strLandmark></strLandmark>
          <strDISPATCH_CTRL>Z021</strDISPATCH_CTRL>
        </ZBAPI_UPDATE_TNO>
      </soap:Body>
    </soap:Envelope>"""

    # headers = {
    #     "SOAPAction": SOAP_ACTION_EBILL,
    #     "Content-Type": "text/xml",
    #     "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'
    # }

    headers = {
        "SOAPAction": update_email_soap_action,
        "Content-Type": update_email_content_type,
        "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'
    }

    try:
        response = requests.post(SOAP_URL_EBILL, data=soap_body, headers=headers)
        response.raise_for_status()
        response_text = response.text

        save_api_key_count("Opt for e-bill","Update Missing Email", soap_body, response_text)
        
        return {
            "status_code": response.status_code,
            "response": response.text,
            "status": True
        }
    except Exception as e:
        return {"error": str(e), "status": False}
    

def update_email_in_db(sender_id, email):
    # data = request.json
    # sender_id = data.get("sender_id")
    # email = data.get("email")

    try:
        Session.update_one(
                {"user_id": sender_id},
                {
                    "$set": {
                        "email": email,
                        # "user_type": "registered"
                    }
                }
            )
        
        return {
                "status": True,
                "response": "email updated in database"
            }
    except Exception as e:
        return {"error": str(e)}


def registration_ebill(ca_number):
    # data = request.json
    # ca_number = data.get("ca_number")
    
    if not ca_number:
        return {"error": "ca_number is required"}
    
    db = SessionLocal()
    try:
        # record = API_Key_Master.find_one(api_name="E-bill Registration")
        record = db.query(API_Key_Master).filter_by(api_name="E-bill Registration").first()
        
        # EBILL_REGISTRATION_SOAP_URL = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx"
        # EBILL_REGISTRATION_SOAP_ACTION = "http://tempuri.org/ZBAPI_UPD_DISPATCH"

        EBILL_REGISTRATION_SOAP_URL = record.api_url


        # Extract values safely
        registration_headers = record.api_headers or {}
        registration_content_type = registration_headers.get("Content-Type")
        registration_soap_action = registration_headers.get("SOAPAction")

        # Build SOAP request dynamically
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <ZBAPI_UPD_DISPATCH xmlns="http://tempuri.org/">
            <CA_NUMBER>{ca_number}</CA_NUMBER>
            <DISPATCH_CONTROL>Z017</DISPATCH_CONTROL>
            </ZBAPI_UPD_DISPATCH>
        </soap:Body>
        </soap:Envelope>"""

        # headers = {
        #     "SOAPAction": EBILL_REGISTRATION_SOAP_ACTION,
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'
        # }


        headers = {
            "SOAPAction": registration_soap_action,
            "Content-Type": registration_content_type,
            "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'
        }

        try:
            response = requests.post(EBILL_REGISTRATION_SOAP_URL, data=soap_body, headers=headers)
            response.raise_for_status()
            response_text = response.text

            save_api_key_count("Opt for e-bill","E-bill Registration", soap_body, response_text)

            return {
                "status_code": response.status_code,
                "response": response.text,
                "status": True
            }
        except Exception as e:
            return {"error": str(e), "status": False}
    except Exception as e:
        raise e
    finally:
        db.close()
    

## Register Complaint

def area_outage(ca_number):
    db = SessionLocal()
    try:
        # ca_number = request.json.get("ca_number")
        if not ca_number:
            return {"status": False, "message": "Missing ca_number"}
        
        # record = API_Key_Master.find_one(api_name="Check Area Outage")
        record = db.query(API_Key_Master).filter_by(api_name="Check Area Outage").first()

        url = record.api_url

        # Extract values safely
        area_outage_headers = record.api_headers or {}
        area_outage_content_type = area_outage_headers.get("Content-Type")
        area_outage_soap_action = area_outage_headers.get("SOAPAction")

        # SOAP Request Body
        soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <AreaUnderOutageByCA_VoiceBot xmlns="http://tempuri.org/">
              <CA>{ca_number}</CA>
            </AreaUnderOutageByCA_VoiceBot>
          </soap:Body>
        </soap:Envelope>"""

        AREA_OUTAGE_HEADERS = {
            "Content-Type": area_outage_content_type,
            "SOAPAction": area_outage_soap_action
        }

        # Send SOAP request
        response = requests.post(url, data=soap_body, headers=AREA_OUTAGE_HEADERS, verify=False)
        response.raise_for_status()
        response_text = response.text


        if response.status_code != 200:
            return {"status": False, "message": "Failed to connect to outage service"}

        # Parse XML Response
        root = ET.fromstring(response.content)
        namespace = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}

        save_api_key_count("Register Complaint","Check Area Outage", soap_body, response_text)

        # Navigate to Comment and Code
        comment = None
        code = None
        for elem in root.iter():
            if "Code" in elem.tag:
                code = elem.text
            if "Comment" in elem.tag:
                comment = elem.text

        if not code or not comment:
            return {"status": False, "message": "Invalid response from outage service"}

        # Handle cases
        if code == "1":
            return {
                "status": True,
                "outage": True,
                "message": comment,
                "valid": True
            }
        elif code == "2":
            return {
                "status": True,
                "outage": False,
                "message": comment,
                "valid": False
            }
        else:
            return {
                "status": False,
                "message": f"Unknown response code: {code}"
            }

    except Exception as e:
        return {"status": False, "message": str(e)}
    finally:
        db.close()




# CURRENT_COMPLAINT_SOAP_URL = "https://test.bsesbrpl.co.in/NCC_Registration_vendor/CMSService.asmx?op=NCC_REGISTRATION_BY_VENDOR"
# CURRENT_COMPLAINT_SOAP_ACTION = "http://tempuri.org/NCC_REGISTRATION_BY_VENDOR"

# Static values
KEY = "@$3$2#$"
CODE = "NC"
SOURCE = "CHATBOT"
VENDOR = "CHATBOT"

def register_ncc(sender_id, ca_number, mobile_no):
    db = SessionLocal()
    try:
        # Extract user input
        # data = request.get_json()
        # sender_id = request.json.get("sender_id")
        # ca_number = request.json.get("ca_number")
        # mobile_no = request.json.get("mobile_no")
        # ca_number = data.get("ca_number")
        # mobile_no = data.get("mobile_no")

        if not ca_number or not mobile_no:
            return {"error": "Missing required fields: ca_number and mobile_no"}
        

        # record = API_Key_Master.find_one(api_name="Registration of No Current Complaint")
        record = db.query(API_Key_Master).filter_by(api_name="Registration of No Current Complaint").first()

        CURRENT_COMPLAINT_SOAP_URL = record.api_url

        # Extract values safely
        current_complaint_headers = record.api_headers or {}
        current_complaint_content_type = current_complaint_headers.get("Content-Type")
        current_complaint_soap_action = current_complaint_headers.get("SOAPAction")

        # Construct SOAP payload
        soap_payload = f'''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                       xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                       xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <NCC_REGISTRATION_BY_VENDOR xmlns="http://tempuri.org/">
              <Key>{KEY}</Key>
              <CA>{ca_number}</CA>
              <CODE>{CODE}</CODE>
              <Mobile>{mobile_no}</Mobile>
              <Source>{SOURCE}</Source>
              <Vendor>{VENDOR}</Vendor>
            </NCC_REGISTRATION_BY_VENDOR>
          </soap:Body>
        </soap:Envelope>'''

        # Send SOAP request
        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": CURRENT_COMPLAINT_SOAP_ACTION
        # }

        headers = {
            "Content-Type": current_complaint_content_type,
            "SOAPAction": current_complaint_soap_action
        }

        response = requests.post(CURRENT_COMPLAINT_SOAP_URL, data=soap_payload, headers=headers)
        response.raise_for_status()
        response_text = response.text
        save_api_key_count("Register Complaint","Registration of No Current Complaint", soap_payload, response_text)

        if response.status_code != 200:
            return {"error": "Failed to communicate with SOAP service", "status": False}

        # Parse XML response
        root = ET.fromstring(response.text)
        namespace = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}

        comment = None
        comment_hindi = None

        for elem in root.iter():
            if elem.tag.endswith("Comment"):
                comment = elem.text
            if elem.tag.endswith("Comment_Hindi"):
                comment_hindi = elem.text

        print(comment, comment_hindi, "================================= comments")



        # Regex to capture complaint number and check status
        pattern = r"Complaint No\.\s*(\d+)\s*is (already )?registered\. Thank you"

        match = re.match(pattern, comment, re.IGNORECASE)

        if match:
            complaint_no = match.group(1)  # Extracted complaint number
            already_registered = match.group(2)  # Will be 'already ' if present, else None
            
            if not already_registered:  # Only run if not already registered
                print(complaint_no, "================================= registring comp")
                Session.update_one(
                    {"user_id": sender_id},
                    {
                        "$set": {
                            "complain_no": complaint_no,
                            "complain_status": "pending"
                        }
                    }
                )

        return {
            "status": True,
            "comment": comment,
            "comment_hindi": comment_hindi
        }

    except Exception as e:
        return {"error": str(e), "status": False}
    finally:
        db.close()
    

## Visually Impaired

def validate_mobile(mobile_number, sender_id):
    # mobile_number = request.json.get("mobile_number")
    # sender_id = request.json.get("sender_id")

    otp = random.randint(100000, 999999)

    record = API_Key_Master.find_one(api_name="Send OTP")

    # SOAP request URL
    # url = "https://bsesapps.bsesdelhi.com/DelhiV2/ISUService.asmx?op=SEND_BSES_SMS_API"
    url = record.api_url

    # Extract values safely
    send_otp_headers = record.api_headers or {}
    send_otp_content_type = send_otp_headers.get("Content-Type")
    send_otp_soap_action = send_otp_headers.get("SOAPAction")

    # XML payload
    payload = f'''<?xml version="1.0" encoding="utf-8"?>
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <SEND_BSES_SMS_API xmlns="http://tempuri.org/">
                <_sAppName>CHATBOT_WEBSITE</_sAppName>
                <_sEncryptionKey>!!B$E$@@*SMS</_sEncryptionKey>
                <_sCompanyCode>BRPL</_sCompanyCode>
                <_sVendorCode>Karix</_sVendorCode>
                <_sEmpCode>YourEmpCode</_sEmpCode>
                <_MobileNo>{mobile_number}</_MobileNo>
                <_sOTPMsg>{otp}</_sOTPMsg>
                <_sSMSType>YourSMSType</_sSMSType>
            </SEND_BSES_SMS_API>
        </soap:Body>
    </soap:Envelope>'''

    # Headers
    # headers = {
    #     'Content-Type': 'text/xml; charset=utf-8',
    #     'SOAPAction': '"http://tempuri.org/SEND_BSES_SMS_API"'
    # }

    headers = {
        'Content-Type': send_otp_content_type,
        'SOAPAction': send_otp_soap_action
    }

    # Make the request
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    response_text = response.text

    save_api_key_count("Visually Impaired","Send OTP", payload, response_text)

    # --- Parse XML response to extract FLAG ---
    flag = None
    output = None
    try:
        root = ET.fromstring(response.text)
        ns = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}

        # Find FLAG and OUT_PUT inside the response
        for elem in root.findall(".//FLAG"):
            flag = elem.text
        for elem in root.findall(".//OUT_PUT"):
            output = elem.text
    except Exception as e:
        print("Error parsing SOAP response:", e)

    if flag == "S":
        # # Store OTP if success
        # if sender_id in user_ca_storage:
        #     user_ca_storage[sender_id].update({"otp": otp})
        # else:
        #     user_ca_storage[sender_id] = {"otp": otp}

        Session.update_one(
            {"user_id": sender_id},
            {
                "$set": {
                    "otp": otp,
                    "tel_no": mobile_number
                }
            }
        )
        # print(user_ca_storage, "========================== validate mobile")
        return {"valid":True, "message":"OTP sent successfully"}
    else:
        return {"valid":False, "message": output or "Failed to send OTP"}
    

import xml.etree.ElementTree as ET

def insert_mobapp_data(mobile_no):
    db = SessionLocal()
    try:
        # Extract data from request JSON
        # data = request.get_json()
        # mobile_no = request.json.get("MobileNo", "")
        # date_time = request.json.get("DateTime", "")
        # source = request.json.get("Source", "")
        # request_type = request.json.get("RequestType", "")
        # language_type = request.json.get("LanguageType", "")

        date_time = ""
        source = ""
        request_type = ""
        language_type = ""

        print(mobile_no, "========================= mobile_no")

        # record = API_Key_Master.find_one(api_name="Alert Data to BRPL CRM")
        record = db.query(API_Key_Master).filter_by(api_name="Alert Data to BRPL CRM").first()

        # Extract values safely
        alert_data_headers = record.api_headers or {}
        alert_data_content_type = alert_data_headers.get("Content-Type")
        alert_data_soap_action = alert_data_headers.get("SOAPAction")

        # Convert to int safely
        try:
            mobile_no = int(mobile_no)
        except (ValueError, TypeError):
            return {"error": "Invalid MobileNo provided", "status": False}
        

        # SOAP request body
        soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Insert_MobApp_DataToBRPLCRM xmlns="http://tempuri.org/">
      <MobileNo>{mobile_no}</MobileNo>
      <DateTime>{date_time}</DateTime>
      <Source>{source}</Source>
      <RequestType>{request_type}</RequestType>
      <LanguageType>{language_type}</LanguageType>
    </Insert_MobApp_DataToBRPLCRM>
  </soap:Body>
</soap:Envelope>'''

        # Headers
        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": "http://tempuri.org/Insert_MobApp_DataToBRPLCRM",
        #     "Authorization": f'Bearer {token_manager.get_token("jwt")}'

        # }

        headers = {
            "Content-Type": alert_data_content_type,
            "SOAPAction": alert_data_soap_action,
            "Authorization": f'Bearer {token_manager.get_token("jwt")}'

        }

        # SOAP endpoint
        # url = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx?op=Insert_MobApp_DataToBRPLCRM"
        url = record.api_url

        # Send SOAP request
        response = requests.post(url, data=soap_body, headers=headers)
        response.raise_for_status()
        response_text = response.text

        save_api_key_count("Visually Impaired","Alert Data to BRPL CRM", soap_body, response_text)

        # Parse the XML response
        root = ET.fromstring(response.content)
        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns': 'http://tempuri.org/'
        }
        result_text = root.find('.//ns:Insert_MobApp_DataToBRPLCRMResult', namespaces).text

        print(result_text, "================================= result text")

        return {
            "status": True,
            "message": result_text
        }

    except Exception as e:
        return {
            "status": False,
            "error": str(e)
        }
    finally:
        db.close()


## Branches Nearby

import math
from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 10

def generate_google_maps_navigation_link(origin_lat, origin_lon, dest_lat, dest_lon, travel_mode="driving"):
        return (
            f"https://www.google.com/maps/dir/?api=1"
            f"&origin={origin_lat},{origin_lon}"
            f"&destination={dest_lat},{dest_lon}"
            f"&travelmode={travel_mode}"
        )


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points using the Haversine formula."""
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_meters = R * c
    return round(distance_meters)

def get_outlet_data(latitude, longitude, filter_code):
    # data = request.json
    # latitude = data.get("latitude")
    # longitude = data.get("longitude")
    # filter_code = data.get("filter_code")

    if not all([latitude, longitude, filter_code]):
        return {"error": "Missing latitude, longitude, or filter_code"}
    
    db = SessionLocal()
    try:
    
        # record = API_Key_Master.find_one(api_name="BRPL Outlet Data")
        record = db.query(API_Key_Master).filter_by(api_name="BRPL Outlet Data").first()

        # Extract values safely
        outlet_headers = record.api_headers or {}
        outlet_content_type = outlet_headers.get("Content-Type")
        outlet_soap_action = outlet_headers.get("SOAPAction")

        # SOAP_URL_OUTLET = "https://bsesbrpl.co.in:7860/GISServices/WebGISService.asmx"
        # SOAP_ACTION_OUTLET = "http://tempuri.org/BRPL_Outlet"

        SOAP_URL_OUTLET = record.api_url

        SOAP_BODY_OUTLET = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <BRPL_Outlet xmlns="http://tempuri.org/" />
        </soap:Body>
        </soap:Envelope>"""

        # headers = {
        #     "Content-Type": "text/xml",
        #     "SOAPAction": SOAP_ACTION_OUTLET
        # }

        headers = {
            "Content-Type": outlet_content_type,
            "SOAPAction": outlet_soap_action
        }

        response = requests.post(SOAP_URL_OUTLET, data=SOAP_BODY_OUTLET, headers=headers)
        response.raise_for_status()
        response_text = response.text

        save_api_key_count("Branches Nearby","BRPL Outlet Data", SOAP_BODY_OUTLET, response_text)

        if response.status_code != 200:
            return {"error": "Failed to fetch SOAP data"}

        namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1',
            'msdata': 'urn:schemas-microsoft-com:xml-msdata'
        }

        root = ET.fromstring(response.content)
        tables = root.findall(".//diffgr:diffgram/NewDataSet/Table", namespaces)

        filtered_items = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []

            for table in tables:
                facility = table.find("FACILITYCO")
                if facility is not None and facility.text == filter_code:
                    item = {child.tag: child.text for child in table}

                    try:
                        branch_lat = float(item["POINT_Y"])  # latitude
                        branch_lon = float(item["POINT_X"])  # longitude

                        future = executor.submit(
                            get_distance_info, branch_lat, branch_lon,
                            float(latitude), float(longitude), item
                        )
                        futures.append(future)

                    except (ValueError, KeyError):
                        continue

            for future in as_completed(futures):
                result = future.result()
                if result:
                    filtered_items.append(result)

        # Sort by distance and take top 5
        filtered_items.sort(key=lambda x: x["distance_meters"])
        filtered_items = filtered_items[:5]

        return {
            "input_lon": longitude,
            "input_lat": latitude,
            "filter_code": filter_code,
            "nearest_branches": filtered_items
        }
    except Exception as e:
        raise e
    finally:
        db.close()


def get_distance_info(branch_lat, branch_lon, latitude, longitude, item):
    """Compute distance using haversine formula and add navigation link."""
    try:
        distance_meters = haversine(latitude, longitude, branch_lat, branch_lon)
        item["distance_meters"] = distance_meters
        item["distance_km"] = f"{distance_meters / 1000:.2f} km"
        item["navigation_link"] = generate_google_maps_navigation_link(
            latitude, longitude, branch_lat, branch_lon
        )
        return item
    except Exception as e:
        print(f"Failed for: {branch_lat},{branch_lon} | Error: {e}")
    return None



## Complaint Status

# Complaint_Status_SOAP_URL = "https://test.bsesbrpl.co.in/NCC_Registration_vendor/CMSService.asmx?op=ComplaintStatusDetails"
# Complaint_Status_SOAP_ACTION = "http://tempuri.org/ComplaintStatusDetails"
Complaint_Status_KEY = "@$3$2#$"
Complaint_Status_VENDOR = "Chatbot"

def complaint_status(ca_number, sender_id):
    # ca_number = request.json.get("ca_number")
    # sender_id = request.json.get("sender_id")

    if not ca_number:
        return {"error": "Missing CA number"}
    
    db = SessionLocal()
    try:
    
        # record = API_Key_Master.find_one(api_name="No Current Complaint Status")
        record = db.query(API_Key_Master).filter_by(api_name="No Current Complaint Status").first()

        Complaint_Status_SOAP_URL = record.api_url

        # Extract values safely
        complaint_status_headers = record.api_headers or {}
        complaint_status_content_type = complaint_status_headers.get("Content-Type")
        complaint_status_soap_action = complaint_status_headers.get("SOAPAction")

        # SOAP Request Body
        soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <ComplaintStatusDetails xmlns="http://tempuri.org/">
            <Key>{Complaint_Status_KEY}</Key>
            <CA>{ca_number}</CA>
            <Vendor>{Complaint_Status_VENDOR}</Vendor>
            </ComplaintStatusDetails>
        </soap:Body>
        </soap:Envelope>'''

        # headers = {
        #     "Content-Type": "text/xml",
        #     "SOAPAction": Complaint_Status_SOAP_ACTION
        # }

        headers = {
            "Content-Type": complaint_status_content_type,
            "SOAPAction": complaint_status_soap_action
        }

        try:
            response = requests.post(Complaint_Status_SOAP_URL, data=soap_body, headers=headers, timeout=30)
            response.raise_for_status()
            response_text = response.text

            save_api_key_count("Complaint Status (NCC)","No Current Complaint Status", soap_body, response_text)

            print(response.text, "================================= complaint status response")

            # Parse the XML response
            root = ET.fromstring(response.text)
            ns = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'
            }

            # Case 1: Check for "No Data Found"
            no_data = root.findall(".//Comment")
            status_code = root.findall(".//Status")
            if status_code and status_code[0].text == "101":

                Session.update_one(
                    {"user_id": sender_id},
                    {
                        "$set": {
                            "complain_status": "resolved"
                        }
                    }
                )
                return {"message": "No complaint found"}

            # Case 2: Extract multiple complaints
            complaints = []
            complaint_nodes = root.findall(".//CMS_x0020_Compliants_x0020_Status")
            
            for comp in complaint_nodes:
                complaints.append({
                    "opening_time": comp.findtext("OPENING_TIME", default=""),
                    "status": comp.findtext("STATUS", default=""),
                    # "comp_cnt_24hr": comp.findtext("COMP_CNT_24HR", default=""),
                    # "comment": comp.findtext("Comment", default=""),
                    # "comment_hindi": comp.findtext("Comment_Hindi", default="").strip()
                })

            if not complaints:
                return {"message": "No complaint found"}

            return {"complaints": complaints, "status": True}

        except Exception as e:
            return {"error": "Failed to parse SOAP response", "status": False}
    except Exception as e:
        raise e
    finally:
        db.close()


## Detect language


