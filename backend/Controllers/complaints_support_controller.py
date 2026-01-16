import re
from flask import jsonify, request
import requests
import xml.etree.ElementTree as ET

from Controllers.api_key_master_controller import save_api_key_count
from Models.api_key_master_model import API_Key_Master
from Models.session_model import Session
from database import SessionLocal

# AREA_OUTAGE_SOAP_URL = "https://bsesbrpl.co.in:7860/GISServices/WebGISService.asmx?op=AreaUnderOutageByCA_VoiceBot"
# AREA_OUTAGE_SOAP_ACTION = "http://tempuri.org/AreaUnderOutageByCA_VoiceBot"
# AREA_OUTAGE_HEADERS = {
#     "Content-Type": "text/xml; charset=utf-8",
#     "SOAPAction": AREA_OUTAGE_SOAP_ACTION
# }

# def area_outage():
#     try:
#         ca_number = request.json.get("ca_number")
#         if not ca_number:
#             return jsonify({"status": False, "message": "Missing ca_number"}), 400
        
#         record = API_Key_Master.find_one(api_name="Check Area Outage")

#         url = record.api_url

#         # Extract values safely
#         area_outage_headers = record.api_headers or {}
#         area_outage_content_type = area_outage_headers.get("Content-Type")
#         area_outage_soap_action = area_outage_headers.get("SOAPAction")

#         # SOAP Request Body
#         soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
#         <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
#                        xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
#                        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#           <soap:Body>
#             <AreaUnderOutageByCA_VoiceBot xmlns="http://tempuri.org/">
#               <CA>{ca_number}</CA>
#             </AreaUnderOutageByCA_VoiceBot>
#           </soap:Body>
#         </soap:Envelope>"""

#         AREA_OUTAGE_HEADERS = {
#             "Content-Type": area_outage_content_type,
#             "SOAPAction": area_outage_soap_action
#         }

#         # Send SOAP request
#         response = requests.post(url, data=soap_body, headers=AREA_OUTAGE_HEADERS, verify=False)
#         response.raise_for_status()
#         response_text = response.text


#         if response.status_code != 200:
#             return jsonify({"status": False, "message": "Failed to connect to outage service"}), 500

#         # Parse XML Response
#         root = ET.fromstring(response.content)
#         namespace = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}

#         save_api_key_count("Register Complaint","Check Area Outage", soap_body, response_text)

#         # Navigate to Comment and Code
#         comment = None
#         code = None
#         for elem in root.iter():
#             if "Code" in elem.tag:
#                 code = elem.text
#             if "Comment" in elem.tag:
#                 comment = elem.text

#         if not code or not comment:
#             return jsonify({"status": False, "message": "Invalid response from outage service"}), 500

#         # Handle cases
#         if code == "1":
#             return jsonify({
#                 "status": True,
#                 "outage": True,
#                 "message": comment,
#                 "valid": True
#             }), 200
#         elif code == "2":
#             return jsonify({
#                 "status": True,
#                 "outage": False,
#                 "message": comment,
#                 "valid": False
#             }), 200
#         else:
#             return jsonify({
#                 "status": False,
#                 "message": f"Unknown response code: {code}"
#             }), 500

#     except Exception as e:
#         return jsonify({"status": False, "message": str(e)}), 500




# # CURRENT_COMPLAINT_SOAP_URL = "https://test.bsesbrpl.co.in/NCC_Registration_vendor/CMSService.asmx?op=NCC_REGISTRATION_BY_VENDOR"
# # CURRENT_COMPLAINT_SOAP_ACTION = "http://tempuri.org/NCC_REGISTRATION_BY_VENDOR"

# # Static values
# KEY = "@$3$2#$"
# CODE = "NC"
# SOURCE = "CHATBOT"
# VENDOR = "CHATBOT"

# def register_ncc():
#     try:
#         # Extract user input
#         # data = request.get_json()
#         sender_id = request.json.get("sender_id")
#         ca_number = request.json.get("ca_number")
#         mobile_no = request.json.get("mobile_no")
#         # ca_number = data.get("ca_number")
#         # mobile_no = data.get("mobile_no")

#         if not ca_number or not mobile_no:
#             return jsonify({"error": "Missing required fields: ca_number and mobile_no"}), 400
        

#         record = API_Key_Master.find_one(api_name="Registration of No Current Complaint")

#         CURRENT_COMPLAINT_SOAP_URL = record.api_url

#         # Extract values safely
#         current_complaint_headers = record.api_headers or {}
#         current_complaint_content_type = current_complaint_headers.get("Content-Type")
#         current_complaint_soap_action = current_complaint_headers.get("SOAPAction")

#         # Construct SOAP payload
#         soap_payload = f'''<?xml version="1.0" encoding="utf-8"?>
#         <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
#                        xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
#                        xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#           <soap:Body>
#             <NCC_REGISTRATION_BY_VENDOR xmlns="http://tempuri.org/">
#               <Key>{KEY}</Key>
#               <CA>{ca_number}</CA>
#               <CODE>{CODE}</CODE>
#               <Mobile>{mobile_no}</Mobile>
#               <Source>{SOURCE}</Source>
#               <Vendor>{VENDOR}</Vendor>
#             </NCC_REGISTRATION_BY_VENDOR>
#           </soap:Body>
#         </soap:Envelope>'''

#         # Send SOAP request
#         # headers = {
#         #     "Content-Type": "text/xml; charset=utf-8",
#         #     "SOAPAction": CURRENT_COMPLAINT_SOAP_ACTION
#         # }

#         headers = {
#             "Content-Type": current_complaint_content_type,
#             "SOAPAction": current_complaint_soap_action
#         }

#         response = requests.post(CURRENT_COMPLAINT_SOAP_URL, data=soap_payload, headers=headers)
#         response.raise_for_status()
#         response_text = response.text
#         save_api_key_count("Register Complaint","Registration of No Current Complaint", soap_payload, response_text)

#         if response.status_code != 200:
#             return jsonify({"error": "Failed to communicate with SOAP service", "status": False}), 500

#         # Parse XML response
#         root = ET.fromstring(response.text)
#         namespace = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}

#         comment = None
#         comment_hindi = None

#         for elem in root.iter():
#             if elem.tag.endswith("Comment"):
#                 comment = elem.text
#             if elem.tag.endswith("Comment_Hindi"):
#                 comment_hindi = elem.text

#         print(comment, comment_hindi, "================================= comments")



#         # Regex to capture complaint number and check status
#         pattern = r"Complaint No\.\s*(\d+)\s*is (already )?registered\. Thank you"

#         match = re.match(pattern, comment, re.IGNORECASE)

#         if match:
#             complaint_no = match.group(1)  # Extracted complaint number
#             already_registered = match.group(2)  # Will be 'already ' if present, else None
            
#             if not already_registered:  # Only run if not already registered
#                 print(complaint_no, "================================= registring comp")
#                 Session.update_one(
#                     {"user_id": sender_id},
#                     {
#                         "$set": {
#                             "complain_no": complaint_no,
#                             "complain_status": "pending"
#                         }
#                     }
#                 )

#         return jsonify({
#             "status": True,
#             "comment": comment,
#             "comment_hindi": comment_hindi
#         })

#     except Exception as e:
#         return jsonify({"error": str(e), "status": False}), 500
    

## Complaint Status

# Complaint_Status_SOAP_URL = "https://test.bsesbrpl.co.in/NCC_Registration_vendor/CMSService.asmx?op=ComplaintStatusDetails"
# Complaint_Status_SOAP_ACTION = "http://tempuri.org/ComplaintStatusDetails"
Complaint_Status_KEY = "@$3$2#$"
Complaint_Status_VENDOR = "Chatbot"

def complaint_status():
    db = SessionLocal()
    try:
        ca_number = request.json.get("ca_number")
        sender_id = request.json.get("sender_id")

        if not ca_number:
            return jsonify({"error": "Missing CA number"}), 400
        
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
                return jsonify({"message": "No complaint found"}), 200

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
                return jsonify({"message": "No complaint found"}), 200

            return jsonify({"complaints": complaints, "status": True}), 200

        except Exception as e:
            return jsonify({"error": "Failed to parse SOAP response", "status": False}), 500
    except Exception as e:
        raise e
    finally:
        db.close()
