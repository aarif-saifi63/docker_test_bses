

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
#         return jsonify(status=False, found=False, message=f"Error: {str(e)}"), 500
    

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
            return jsonify({
                # "order_status": order_status,
                "valid": False,
                "status": False,
                "message": "The Order ID entered is not valid. Please recheck and try again.",
                "message_hindi": "आपने जो ऑर्डर आईडी दर्ज की है वह मान्य नहीं है। कृपया दोबारा जांचें और फिर प्रयास करें।"
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
            return jsonify({"message": "The Order ID entered is not valid. Please recheck and try again.", "message_hindi": "आपने जो ऑर्डर आईडी दर्ज की है वह मान्य नहीं है। कृपया दोबारा जांचें और फिर प्रयास करें।", "status": False}), 200

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
            # order_status = "There is no status available for the provided Order ID."
            # return jsonify({"message": "There is no status available for the provided Order ID.", "message_hindi": "इस ऑर्डर आईडी के लिए कोई स्टेटस नहीं मिला।", "status": False}), 200

            thank_eng = db.query(UtterMessage).filter(
                UtterMessage.id == 10,
            ).first()

            # thank_hin = db.query(UtterMessage).filter(
            #     UtterMessage.id == 11,
            # ).first()

            # main_menu_texts = [
            #     thank_eng.text,
            #     thank_hin.text
            # ]
            
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

        result = ""

        result_msg_eng = db.query(UtterMessage).filter(
                UtterMessage.id == 51,
            ).first()
        
        result_msg_hin = db.query(UtterMessage).filter(
                UtterMessage.id == 53,
            ).first()

        if order_status == "Deficiency issued for Technical Feasibility":
            TYPE_OF_DEFICIENCY = "BTFR"
            result = f"""{result_msg_eng.text}

            Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Auto cancelled":
            TYPE_OF_DEFICIENCY = "AC"
            result = f"""{result_msg_eng.text}
            
            Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Document Deficiency issued":
            TYPE_OF_DEFICIENCY = "DR"
            result = f"""{result_msg_eng.text}
            
            Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Deficiency issued for Commercial Feasibility":
            TYPE_OF_DEFICIENCY = "CFR"
            result = f"""{result_msg_eng.text}
            
            Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Deficiency issued for Commercial Feasibility/Technical Feasibility":
            TYPE_OF_DEFICIENCY = "BTFR+CFR"
            result = f"""{result_msg_eng.text}
            
            Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        
        elif order_status == "Deficiency document received and Application under Process":
            TYPE_OF_DEFICIENCY = "DR"
            result = f"""{result_msg_eng.text}
            
            Click here to view deficiency: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""

        elif order_status == "New Connection Processed":
            result = "New Connection Processed"

        else:
            result = order_status

        result_hindi = ""

        if order_status == "Deficiency issued for Technical Feasibility":
            TYPE_OF_DEFICIENCY = "BTFR"
            result_hindi = f"""{result_msg_hin.text}
            
            कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Auto cancelled":
            TYPE_OF_DEFICIENCY = "AC"
            result_hindi = f"""{result_msg_hin.text}
            
            कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Document Deficiency issued":
            TYPE_OF_DEFICIENCY = "DR"
            result_hindi = f"""{result_msg_hin.text}
            
            कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Deficiency issued for Commercial Feasibility":
            TYPE_OF_DEFICIENCY = "CFR"
            result_hindi = f"""{result_msg_hin.text}
            
            कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""
        elif order_status == "Deficiency issued for Commercial Feasibility/Technical Feasibility":
            TYPE_OF_DEFICIENCY = "BTFR+CFR"
            result_hindi = f"""{result_msg_hin.text}
            
            कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""

        elif order_status == "Deficiency document received and Application under Process":
            TYPE_OF_DEFICIENCY = "DR"
            result_hindi = f"""{result_msg_hin.text}
            कमी देखने के लिए यहाँ क्लिक करें: https://test.bsesbrpl.co.in/DSK_Web/BRPLDeficiency.aspx?ORDNO={order_number}&TYPE={TYPE_OF_DEFICIENCY}"""

        elif order_status == "New Connection Processed":
            result_hindi = "नया कनेक्शन प्रोसेस हो गया"

        # elif order_status == "Deficiency document received and Application under Process":
        #     result_hindi = "कमी (डिफ़िशिएंसी) दस्तावेज़ प्राप्त हो गए हैं और आवेदन प्रक्रिया में है।"

        else:
            result_hindi = order_status

        if is_valid == False:

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

## Consumption History

# def get_pdf_bill():
#     data = request.json
#     ca_number = data.get("ca_number")

#     if not ca_number:
#         return jsonify({"error": "Missing CA number"}), 400
    
#     record = API_Key_Master.find_one(api_name="Consumption History PDF")

#     # CONSUMPTION_HISTORY_URL = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx"

#     CONSUMPTION_HISTORY_URL = record.api_url


#     # Extract values safely
#     cons_history_headers = record.api_headers or {}
#     cons_history_content_type = cons_history_headers.get("Content-Type")
#     cons_history_soap_action = cons_history_headers.get("SOAPAction")

#     # Construct the SOAP XML payload
#     soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
# <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#                xmlns:xsd="http://www.w3.org/2001/XMLSchema"
#                xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#   <soap:Body>
#     <ZBAPI_BILL_DET_API_PDF xmlns="http://tempuri.org/">
#       <CA_NUMBER>{ca_number}</CA_NUMBER>
#       <_sMobileNo></_sMobileNo>
#     </ZBAPI_BILL_DET_API_PDF>
#   </soap:Body>
# </soap:Envelope>'''

#     # headers = {
#     #     "Content-Type": "text/xml; charset=utf-8",
#     #     "SOAPAction": "http://tempuri.org/ZBAPI_BILL_DET_API_PDF",
#     #     "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'  # Replace with valid token
#     # }

#     headers = {
#         "Content-Type": cons_history_content_type,
#         "SOAPAction": cons_history_soap_action,
#         "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'  # Replace with valid token
#     }

#     try:
#         # Step 1: Get the PDF link
#         response = requests.post(CONSUMPTION_HISTORY_URL, data=soap_body, headers=headers)
#         response.raise_for_status()
#         response_text = response.text

#         save_api_key_count("Consumption History","Consumption History PDF", soap_body, response_text)

#         root = ET.fromstring(response.text)
#         namespaces = {
#             'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
#             'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'
#         }

#         output_text = root.find(".//diffgr:diffgram//NewDataSet//Table1//OUT_PUT", namespaces)

#         return jsonify({"message": output_text.text, "status": True}), 200
    
#     except Exception as e:
#         return jsonify({"message": "Error in fetching consumption history", "status": False}), 500


# def extract_last_6_months_data(text):

#     # Pattern for lines that begin with a posting date
#     row_pattern = re.compile(r"^\d{2}\.\d{2}\.\d{4}")
#     rows = []
    
#     # Extract data lines
#     for line in text.strip().splitlines():
#         if row_pattern.match(line):
#             line = re.sub(r'\s*\|\s*', '|', line.strip())
#             rows.append(line)
    
#     # Parse rows
#     parsed = []
#     for row in rows:
#         cols = row.split('|')
#         if len(cols) >= 17:
#             bill_month_str = cols[2].strip()
#             try:
#                 # Convert BILL-MONTH like "JUL-25" to datetime (e.g. 01-07-2025)
#                 bill_month_dt = datetime.strptime(bill_month_str, "%b-%y")
#             except:
#                 continue  # skip if format is bad
    
#             parsed.append({
#                 "posting_date": cols[0].strip(),
#                 "bill_month": bill_month_str,
#                 "bill_month_dt": bill_month_dt,
#                 "reading_date": cols[3].strip(),
#                 "kwh": cols[4].strip(),
#                 "kw": cols[5].strip(),
#                 "units_billed": cols[8].strip(),
#                 "total_payable": cols[14].strip(),
#                 "payment_amount": cols[15].strip(),
#                 "payment_date": cols[16].strip() if len(cols) > 16 else None
#             })
    
#     # Sort by bill_month descending and keep only latest 6 months
#     latest_six = sorted(parsed, key=lambda x: x['bill_month_dt'], reverse=True)
#     latest_six_unique = []
#     seen_months = set()
    
#     for item in latest_six:
#         if item['bill_month'] not in seen_months:
#             latest_six_unique.append({k: v for k, v in item.items() if k != 'bill_month_dt'})
#             seen_months.add(item['bill_month'])
#         if len(latest_six_unique) == 6:
#             break
 
#     return latest_six_unique

# def parse_bill_month_consumption(month_str):
#     # print(month_str, "month str===========>>")
#     month_str = month_str.strip().upper()  # Normalize like "JUL-25"
#     try:
#         month_part, year_part = month_str.split("-")
#         if len(year_part) == 2:  # assume 20xx for 2-digit years
#             year = int("20" + year_part)
#         else:
#             year = int(year_part)
#         month = datetime.strptime(month_part, "%b").month
#         return datetime(year, month, 1)
#     except Exception:
#         return None


# def extract_tables_from_pdf(pdf_path):
#     """Extract table data from PDF files."""
#     tables_text = ""
#     print("extract_tables_from_pdf")
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             tables = page.extract_tables()
#             for table in tables:
#                 for row in table:
#                     tables_text += " | ".join(row) + "\n"
#     return tables_text