from datetime import datetime, timedelta
from html import unescape
import re
import xml.etree.ElementTree as ET
import requests
from Controllers.api_key_master_controller import save_api_key_count
from Models.session_model import Session
from Controllers.ad_controller import generate_signed_url_for_file
from database import SessionLocal
from token_manager import token_manager
from flask import jsonify, request
from Models.api_key_master_model import API_Key_Master
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Folder to store PDFs
BASE_MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Media"))
PDF_FOLDER = os.path.join(os.getcwd(), f"/{BASE_MEDIA_DIR}/generated_pdfs")
os.makedirs(PDF_FOLDER, exist_ok=True)

# flask_url = "http://192.168.20.47:3000"
flask_url = os.getenv('BACKEND_URL')
# flask_url = f"{os.getenv('BASE_URL')}:{os.getenv('BACKEND_PORT')}"


def cleanup_old_pdfs(folder, hours=24):
    """Delete PDF files older than `hours` in the specified folder."""
    now = datetime.now()
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if filename.endswith(".pdf") and os.path.isfile(filepath):
            file_age = now - datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_age > timedelta(hours=hours):
                os.remove(filepath)


def generate_duplicate_bill_pdf():
    db = SessionLocal()
    try:
        # data = request.json
        ca_number = request.json.get("ca_number")
        ebsk_no = request.json.get("ebsk_no", "")

        print(ca_number, "====================== ca number")

        # record = API_Key_Master.find_one(api_name="Duplicate Bill PDF")
        record = db.query(API_Key_Master).filter_by(api_name="Duplicate Bill PDF").first()

        if not ca_number:
            return jsonify({"error": "Missing CA Number", "status": False}), 400
        
        # DUPLICATE_BILL_SOAP_URL = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx?op=ZBAPI_ONLINE_BILL_PDF"
        # DUPLICATE_BILL_SOAP_ACTION = "http://tempuri.org/ZBAPI_ONLINE_BILL_PDF"

        DUPLICATE_BILL_SOAP_URL = record.api_url

        duplicate_bill_headers = record.api_headers or {}
        duplicate_bill_content_type = duplicate_bill_headers.get("Content-Type")
        duplicate_bill_soap_action = duplicate_bill_headers.get("SOAPAction")

        # SOAP Request Body
        soap_body = f'''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ZBAPI_ONLINE_BILL_PDF xmlns="http://tempuri.org/">
      <strCANumber>000{ca_number}</strCANumber>
      <strEBSKNO>{ebsk_no}</strEBSKNO>
    </ZBAPI_ONLINE_BILL_PDF>
  </soap:Body>
</soap:Envelope>'''

        # headers = {
        #     "Content-Type": "text/xml; charset=utf-8",
        #     "SOAPAction": DUPLICATE_BILL_SOAP_ACTION,
        #     "Authorization": f'Bearer {token_manager.get_token("jwt")}'
        # }

        headers = {
            "Content-Type": duplicate_bill_content_type,
            "SOAPAction": duplicate_bill_soap_action,
            "Authorization": f'Bearer {token_manager.get_token("jwt")}'
        }

        # Send SOAP Request
        response = requests.post(DUPLICATE_BILL_SOAP_URL, headers=headers, data=soap_body, timeout=30)
        response.raise_for_status()
        response_text = response.text

        save_api_key_count("Duplicate Bill","Duplicate Bill PDF", soap_body, response_text)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from SOAP API", "status_code": response.status_code, "status": False}), 500

        # Clean invalid XML characters (e.g., &#x0;)
        cleaned_xml = re.sub(r'&#x0;|[\x00-\x08\x0B\x0C\x0E-\x1F]', '', response.text)

        # Parse XML
        root = ET.fromstring(cleaned_xml)

        # Extract Tdline elements
        tdlines = []
        for elem in root.findall('.//ZPDFTable/Tdline'):
            if elem.text:
                tdlines.append(unescape(elem.text))

        if not tdlines:
            return jsonify({"error": "No valid Tdline content found", "status": False}), 400

        # Create PDF content
        pdf_content = "\n".join(tdlines)
        pdf_bytes = pdf_content.encode('latin1', errors='ignore')

        # Save PDF with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bill_{timestamp}.pdf"
        filepath = os.path.join(PDF_FOLDER, filename)

        with open(filepath, "wb") as f:
            f.write(pdf_bytes)

        print(filepath, "========================= filepath")

        file_path = generate_signed_url_for_file(f'/Media/generated_pdfs/{filename}', expires_in=60)
        file_url = f'{flask_url}{file_path}'

        # Return URL to access the file
        # file_url = url_for('serve_pdf', filename=filename, _external=True)

        return jsonify({
            "message": "PDF generated successfully",
            "pdf_url": file_url,
            "status": True
        })

    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500
    finally:
        db.close()
    

## Payment Hisotry


# def create_soap_request(ca_number):
#     return f"""<?xml version="1.0" encoding="utf-8"?>
#     <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#                    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
#                    xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#       <soap:Body>
#         <ZBI_WEBBILL_HIST xmlns="http://tempuri.org/">
#           <CA_NUMBER>000{ca_number}</CA_NUMBER>
#         </ZBI_WEBBILL_HIST>
#       </soap:Body>
#     </soap:Envelope>"""

# def get_payment_history():
#     ca_number = request.json.get("ca_number")
#     if not ca_number:
#         return jsonify({"error": "Missing CA number"}), 400
    

#     record = API_Key_Master.find_one(api_name="Payment History Data")
    
#     # SOAP_URL = "https://bsesapps.bsesdelhi.com/delhiv2/ISUService.asmx?op=ZBI_WEBBILL_HIST"
#     # SOAP_ACTION = "http://tempuri.org/ZBI_WEBBILL_HIST"

#     SOAP_URL = record.api_url

#     # Extract values safely
#     payment_his_headers = record.api_headers or {}
#     payment_his_content_type = payment_his_headers.get("Content-Type")
#     payment_his_soap_action = payment_his_headers.get("SOAPAction")

#     # headers = {
#     #     "Content-Type": "text/xml; charset=utf-8",
#     #     "SOAPAction": SOAP_ACTION,
#     #     "Authorization": f'Bearer {token_manager.get_token("jwt")}'
#     # }

#     headers = {
#         "Content-Type": payment_his_content_type,
#         "SOAPAction": payment_his_soap_action,
#         "Authorization": f'Bearer {token_manager.get_token("jwt")}'
#     }

#     try:
#         response = requests.post(SOAP_URL, headers=headers, data=create_soap_request(ca_number))
#         response.raise_for_status()
#         response_text = response.text

#         save_api_key_count("Payment History","Payment History Data", create_soap_request(ca_number), response_text)

#         if response.status_code != 200:
#             return jsonify({"error": "SOAP request failed", "status": False}), 500

#         # Parse XML
#         root = ET.fromstring(response.content)

#         # Get all bill history entries
#         ns = {'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'}
#         tables = root.findall('.//diffgr:diffgram//webBillHistoryTable', ns)

#         # Handle invalid CA number (no billing data)
#         if not tables:
#             return jsonify({
#                 "message": "Invalid CA number or no billing history available.",
#                 "data": []
#             }), 200

#         bill_data = []

#         for table in tables:
#             bill_month = table.findtext("BILL_MONTH", default="")
#             date_of_invoice = table.findtext("DATE_OF_INVOICE", default="")
#             due_date = table.findtext("DUE_DATE", default="")
#             net_amount = table.findtext("NET_AMNT", default="")
#             payment_date = table.findtext("PAYMENT_DATE", default="")
#             payment_amount = table.findtext("PAYMENT_AMOUNT", default="")
#             units = table.findtext("UNITS", default="")
#             total_bill_amt = table.findtext("TOT_BIL_AMT", default="")

#             bill_data.append({
#                 "Bill Month": bill_month,
#                 "Date of Invoice": format_date(date_of_invoice),
#                 "Due Date": format_date(due_date),
#                 "Net Amount to be Paid": net_amount,
#                 "Payment Date": format_date(payment_date),
#                 "Payment Amount": payment_amount,
#                 "Units Consumed": units,
#                 "Total Bill Amt": total_bill_amt
#             })

#         # Sort bills by month in descending order
#         sorted_bills = sorted(bill_data, key=lambda x: parse_bill_month(x["Bill Month"]), reverse=True)

#         # Collect up to 6 bills skipping ones with payment_amount == 0.00
#         recent_six = []
#         for bill in sorted_bills:
#             if bill["Payment Amount"] != "0.00":
#                 recent_six.append(bill)
#             if len(recent_six) == 6:
#                 break

#         return jsonify({"entries": recent_six, "status": True})
    
#     except Exception as e:
#         return jsonify({"message": "Error in fetching payment history", "status": False}), 500


# def parse_bill_month(bill_month):
#     try:
#         return datetime.strptime(bill_month, "%b-%y")
#     except:
#         return datetime.min

# def format_date(raw_date):
#     if raw_date and raw_date != "00000000":
#         try:
#             return datetime.strptime(raw_date, "%Y%m%d").strftime("%d-%m-%Y")
#         except:
#             return raw_date
#     return ""


## Bill History

# def get_bill_history():
#     ca_number = request.json.get("ca_number")
#     if not ca_number:
#         return jsonify({"error": "Missing CA number"}), 400
    
#     record = API_Key_Master.find_one(api_name="Bill History Data")

#     SOAP_URL = record.api_url

#     # Extract values safely
#     bill_his_headers = record.api_headers or {}
#     bill_his_content_type = bill_his_headers.get("Content-Type")
#     bill_his_soap_action = bill_his_headers.get("SOAPAction")

#     # headers = {
#     #     "Content-Type": "text/xml; charset=utf-8",
#     #     "SOAPAction": SOAP_ACTION,
#     #     "Authorization": f'Bearer {token_manager.get_token("jwt")}'
#     # }

#     headers = {
#         "Content-Type": bill_his_content_type,
#         "SOAPAction": bill_his_soap_action,
#         "Authorization": f'Bearer {token_manager.get_token("jwt")}'
#     }

#     try:

#         response = requests.post(SOAP_URL, headers=headers, data=create_soap_request(ca_number))
#         response.raise_for_status()
#         response_text = response.text

#         save_api_key_count("Bill History","Bill History Data", create_soap_request(ca_number), response_text)

#         if response.status_code != 200:
#             return jsonify({"error": "SOAP request failed", "status": False}), 500

#         # Parse XML
#         root = ET.fromstring(response.content)

#         # Get all bill history entries
#         ns = {'diffgr': 'urn:schemas-microsoft-com:xml-diffgram-v1'}
#         tables = root.findall('.//diffgr:diffgram//webBillHistoryTable', ns)

#         # Handle invalid CA number (no billing data)
#         if not tables:
#             return jsonify({
#                 "message": "Invalid CA number or no billing history available.",
#                 "data": []
#             }), 200

#         bill_data = []

#         for table in tables:
#             bill_month = table.findtext("BILL_MONTH", default="")
#             date_of_invoice = table.findtext("DATE_OF_INVOICE", default="")
#             due_date = table.findtext("DUE_DATE", default="")
#             net_amount = table.findtext("NET_AMNT", default="")
#             payment_date = table.findtext("PAYMENT_DATE", default="")
#             payment_amount = table.findtext("PAYMENT_AMOUNT", default="")
#             units = table.findtext("UNITS", default="")
#             invoice_no = table.findtext("INVOICE_NO", default="")
#             current_bill_amount = table.findtext("CUR_MTH_BILL_AMT", default="")


#             bill_data.append({
#                 "Bill Month": bill_month,
#                 "Date of Invoice": format_date(date_of_invoice),
#                 "Due Date": format_date(due_date),
#                 "Net Amount to be Paid": net_amount,
#                 "Payment Date": format_date(payment_date),
#                 "Payment Amount": payment_amount,
#                 "Units Consumed": units,
#                 "Invoice No": invoice_no,
#                 "Current Bill Amount": current_bill_amount
#             })

#         # Sort bills by month in descending order
#         sorted_bills = sorted(bill_data, key=lambda x: parse_bill_month(x["Bill Month"]), reverse=True)

#         # Collect up to 6 bills skipping ones with payment_amount == 0.00
#         # recent_six = []
#         # for bill in sorted_bills:
#         #     if bill["Payment Amount"] != "0.00":
#         #         recent_six.append(bill)
#         #     if len(recent_six) == 6:
#         #         break

#         recent_six = sorted_bills[:6]

#         return jsonify({"entries": recent_six, "status": True})

#     except Exception as e:
#         return jsonify({"message": "Error in fetching bill history", "status": False}), 500


## Opt for e-bill

def update_missing_email(ca_number, email):
    # data = request.json
    # ca_number = data.get("ca_number")
    # email = data.get("email")
    
    if not ca_number or not email:
        return jsonify({"error": "Both ca_number and email are required"}), 400
    
    db = SessionLocal()
    try:
        # record = API_Key_Master.find_one(api_name="Update Missing Email")
        record = db.query(API_Key_Master).filter_by(api_name="Update Missing Email").first()
        
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
    except Exception as e:
        raise e
    finally:
        db.close()
        

# def update_email_in_db(sender_id, email):
#     data = request.json
#     sender_id = data.get("sender_id")
#     email = data.get("email")

#     try:
#         Session.update_one(
#                 {"user_id": sender_id},
#                 {
#                     "$set": {
#                         "email": email,
#                         # "user_type": "registered"
#                     }
#                 }
#             )
        
#         return {
#                 "status": True,
#                 "response": "email updated in database"
#             }
#     except Exception as e:
#         return {"error": str(e)}

def update_email_in_db(sender_id=None, email=None):
    # data = request.json
    # sender_id = data.get("sender_id") or sender_id
    # email = data.get("email") or email

    if not sender_id or not email:
        return {"status": False, "error": "sender_id and email are required"}

    db = SessionLocal()
    try:
        # Update user record safely
        result = db.query(Session).filter_by(user_id=sender_id).update({
            "email": email
        })

        if result == 0:
            return {"status": False, "error": "No matching record found"}

        db.commit()

        return {
            "status": True,
            "response": "Email updated in database"
        }

    except Exception as e:
        db.rollback()
        return {"status": False, "error": str(e)}

    finally:
        db.close()



# def registration_ebill():
#     data = request.json
#     ca_number = data.get("ca_number")
    
#     if not ca_number:
#         return jsonify({"error": "ca_number is required"}), 400
    
#     record = API_Key_Master.find_one(api_name="E-bill Registration")
    
#     # EBILL_REGISTRATION_SOAP_URL = "https://test.bsesbrpl.co.in/DBTest_Delhiv2/ISUService.asmx"
#     # EBILL_REGISTRATION_SOAP_ACTION = "http://tempuri.org/ZBAPI_UPD_DISPATCH"

#     EBILL_REGISTRATION_SOAP_URL = record.api_url


#     # Extract values safely
#     registration_headers = record.api_headers or {}
#     registration_content_type = registration_headers.get("Content-Type")
#     registration_soap_action = registration_headers.get("SOAPAction")

#     # Build SOAP request dynamically
#     soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
#     <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#       <soap:Body>
#         <ZBAPI_UPD_DISPATCH xmlns="http://tempuri.org/">
#           <CA_NUMBER>{ca_number}</CA_NUMBER>
#           <DISPATCH_CONTROL>Z017</DISPATCH_CONTROL>
#         </ZBAPI_UPD_DISPATCH>
#       </soap:Body>
#     </soap:Envelope>"""

#     # headers = {
#     #     "SOAPAction": EBILL_REGISTRATION_SOAP_ACTION,
#     #     "Content-Type": "text/xml; charset=utf-8",
#     #     "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'
#     # }


#     headers = {
#         "SOAPAction": registration_soap_action,
#         "Content-Type": registration_content_type,
#         "Authorization": f'Bearer {token_manager.get_token("delhiv2")}'
#     }

#     try:
#         response = requests.post(EBILL_REGISTRATION_SOAP_URL, data=soap_body, headers=headers)
#         response.raise_for_status()
#         response_text = response.text

#         save_api_key_count("Opt for e-bill","E-bill Registration", soap_body, response_text)

#         return jsonify({
#             "status_code": response.status_code,
#             "response": response.text,
#             "status": True
#         })
#     except Exception as e:
#         return jsonify({"error": str(e), "status": False}), 500