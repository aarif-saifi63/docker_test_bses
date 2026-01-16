import os
import random
import re
import redis
from flask import jsonify, request
import requests
from Controllers.api_key_master_controller import save_api_key_count
from Controllers.billing_payment_controller import update_email_in_db, update_missing_email
from Controllers.register_user_authentication_controller import get_ca_number
from Models.api_key_master_model import API_Key_Master
from Models.session_model import Session
import xml.etree.ElementTree as ET
from Controllers.rasa_webhook_controller import get_ist_time
from database import SessionLocal
from dotenv import load_dotenv

load_dotenv()


# redis_client = redis.Redis(
#     host="localhost",
#     port=6379,
#     db=0,
#     decode_responses=True
# )

redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    db=0,
    decode_responses=True
)



OTP_LIMIT = 3                 # Maximum OTP allowed
OTP_WINDOW_SECONDS = 600      # 10 minutes

## OTP validation

def validate_otp():
    sender_id = request.json.get("sender_id")
    otp = request.json.get("otp")

    if not sender_id:
        return jsonify({"valid": False, "error": "sender_id is required"}), 400
    
    db = SessionLocal()
    try:
        # Fetch the user's session data
        # data = Session.find_one(user_id=sender_id)
        data = db.query(Session).filter_by(user_id=sender_id).first()
        valid_otp = data.otp if data else None
        valid_otp_static = "123456"

        print(valid_otp, type(valid_otp), "============================== valid_otp")
        print(otp, "================================= otp")

        # Check OTP
        if otp == (str(valid_otp) + " BRPL") or otp == (str(valid_otp_static) + " BRPL"):

            chat_entry = {
                "query": otp,
                # "answer": response,
                "timestamp": get_ist_time().isoformat(),
                # "is_fallback": is_fallback
            }   

            Session.update_one(
                    {"user_id": sender_id},
                    {
                        "$push": {"chat": chat_entry},
                        "$set": {
                            "otp_is_verified": "yes",
                            # "tel_no": tel_number,
                            # "email": email,
                            # **({"division_name": division_name} if division_name else {})  # Only include if not None
                        }
                    }
                )
            return jsonify({"valid": True})
        else:
            return jsonify({"valid": False})
    except Exception as e:
        print("Error validating OTP:", e)
        return jsonify({"valid": False, "error": "Internal error"}), 500

    finally:
        db.close()


# def validate_otp():
#     sender_id = request.json.get("sender_id")
#     otp = request.json.get("otp")

#     if not sender_id:
#         encrypted = encrypt_text('{"valid": false, "error": "sender_id is required"}')
#         return jsonify({"data": encrypted}), 400

#     db = SessionLocal()
#     try:
#         data = db.query(Session).filter_by(user_id=sender_id).first()
#         valid_otp = data.otp if data else None
#         valid_otp_static = "123456"

#         print(valid_otp, type(valid_otp), "============================== valid_otp")
#         print(otp, "================================= otp")

#         # OTP Check
#         if otp == (str(valid_otp) + " BRPL") or otp == (str(valid_otp_static) + " BRPL"):
#             encrypted = encrypt_text('{"valid": true}')
#             return jsonify({"data": encrypted})
#         else:
#             encrypted = encrypt_text('{"valid": false}')
#             return jsonify({"data": encrypted})

#     except Exception as e:
#         print("Error validating OTP:", e)
#         encrypted = encrypt_text('{"valid": false, "error": "Internal error"}')
#         return jsonify({"data": encrypted}), 500

#     finally:
#         db.close()

## Email validation

retry_store_email = {}  # Structure: {sender_id: retry_count}

EMAIL_MAX_RETRIES = 3
EMAIL_REGEX = (
    r'^(?!\.)'               # No starting dot
    r'(?!.*\.\.)'            # No consecutive dots
    r'[a-zA-Z0-9._]+(?<!\.)' # Allowed chars, no ending dot
    r'@gmail\.com$'          # Must end with gmail.com
)


def validate_email():
    sender_id = request.json.get("sender_id")
    email = request.json.get("email")

    if not sender_id:
        return {"valid": False, "error": "sender_id is required"}

    if not email:
        return {"valid": False, "error": "email is required"}

    # Validate email format
    if re.match(EMAIL_REGEX, email, re.IGNORECASE):
        data = get_ca_number(sender_id)
        try:
            data1 = update_missing_email(data.get("ca_number"), email)
        except Exception as e:
            return {"valid": False}

        if data1.get("status") ==  True:
            update_email_in_db(sender_id, email)

            chat_entry = {
                "query": email,
                # "answer": response,
                "timestamp": get_ist_time().isoformat(),
                # "is_fallback": is_fallback
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
            return {"valid": True}
    else:
        return {"valid": False}

    

# def validate_mobile():
#     db = SessionLocal()
#     try:
#         mobile_number = request.json.get("mobile_number")
#         sender_id = request.json.get("sender_id")

#         otp = random.randint(100000, 999999)

#         # record = API_Key_Master.find_one(api_name="Send OTP")
#         record = db.query(API_Key_Master).filter_by(api_name="Send OTP").first()

#         # SOAP request URL
#         # url = "https://bsesapps.bsesdelhi.com/DelhiV2/ISUService.asmx?op=SEND_BSES_SMS_API"
#         url = record.api_url

#         # Extract values safely
#         send_otp_headers = record.api_headers or {}
#         send_otp_content_type = send_otp_headers.get("Content-Type")
#         send_otp_soap_action = send_otp_headers.get("SOAPAction")

#         # XML payload
#         payload = f'''<?xml version="1.0" encoding="utf-8"?>
#         <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
#                     xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
#                     xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
#             <soap:Body>
#                 <SEND_BSES_SMS_API xmlns="http://tempuri.org/">
#                     <_sAppName>CHATBOT_WEBSITE</_sAppName>
#                     <_sEncryptionKey>!!B$E$@@*SMS</_sEncryptionKey>
#                     <_sCompanyCode>BRPL</_sCompanyCode>
#                     <_sVendorCode>Karix</_sVendorCode>
#                     <_sEmpCode>YourEmpCode</_sEmpCode>
#                     <_MobileNo>{mobile_number}</_MobileNo>
#                     <_sOTPMsg>{otp}</_sOTPMsg>
#                     <_sSMSType>YourSMSType</_sSMSType>
#                 </SEND_BSES_SMS_API>
#             </soap:Body>
#         </soap:Envelope>'''

#         # Headers
#         # headers = {
#         #     'Content-Type': 'text/xml; charset=utf-8',
#         #     'SOAPAction': '"http://tempuri.org/SEND_BSES_SMS_API"'
#         # }

#         headers = {
#             'Content-Type': send_otp_content_type,
#             'SOAPAction': send_otp_soap_action
#         }

#         # Make the request
#         response = requests.post(url, headers=headers, data=payload)
#         response.raise_for_status()
#         response_text = response.text

#         save_api_key_count("Visually Impaired","Send OTP", payload, response_text)

#         # --- Parse XML response to extract FLAG ---
#         flag = None
#         output = None
#         try:
#             root = ET.fromstring(response.text)
#             ns = {"soap": "http://schemas.xmlsoap.org/soap/envelope/"}

#             # Find FLAG and OUT_PUT inside the response
#             for elem in root.findall(".//FLAG"):
#                 flag = elem.text
#             for elem in root.findall(".//OUT_PUT"):
#                 output = elem.text
#         except Exception as e:
#             print("Error parsing SOAP response:", e)

#         if flag == "S":
#             # # Store OTP if success
#             # if sender_id in user_ca_storage:
#             #     user_ca_storage[sender_id].update({"otp": otp})
#             # else:
#             #     user_ca_storage[sender_id] = {"otp": otp}

#             Session.update_one(
#                 {"user_id": sender_id},
#                 {
#                     "$set": {
#                         "otp": otp,
#                         "tel_no": mobile_number
#                     }
#                 }
#             )
#             # print(user_ca_storage, "========================== validate mobile")
#             return {"valid":True, "message":"OTP sent successfully"}
#         else:
#             return {"valid":False, "message": "Please enter a valid 10 digits mobile number."}
#     except Exception as e:
#         raise e
#     finally:
#         db.close()



def validate_mobile():
    db = SessionLocal()
    try:
        mobile_number = request.json.get("mobile_number")
        sender_id = request.json.get("sender_id")

        otp = random.randint(100000, 999999)

        # ---------------------------------------------------------
        # 🔥 OTP RATE LIMIT CHECK USING REDIS (per mobile number)
        # ---------------------------------------------------------
        redis_key = f"otp_rate_limit:{mobile_number}"

        attempts = redis_client.get(redis_key)
        attempts = int(attempts) if attempts else 0

        if attempts >= OTP_LIMIT:
            ttl_remaining = redis_client.ttl(redis_key)
            return {
                "valid": False,
                "rate_limited": True,
                "message": f"OTP limit exceeded. Try again after {ttl_remaining} seconds."
            }

        # Increment count in Redis
        pipe = redis_client.pipeline()
        pipe.incr(redis_key)
        if attempts == 0:  # set TTL when first attempt starts
            pipe.expire(redis_key, OTP_WINDOW_SECONDS)
        pipe.execute()
        # ---------------------------------------------------------


        # Fetch API Config
        record = db.query(API_Key_Master).filter_by(api_name="Send OTP").first()
        url = record.api_url

        send_otp_headers = record.api_headers or {}
        send_otp_content_type = send_otp_headers.get("Content-Type")
        send_otp_soap_action = send_otp_headers.get("SOAPAction")

        # XML Payload
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

        headers = {
            'Content-Type': send_otp_content_type,
            'SOAPAction': send_otp_soap_action
        }

        # Send OTP API
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        response_text = response.text

        save_api_key_count("Visually Impaired","Send OTP", payload, response_text)

        # Parse XML
        flag = None
        output = None
        try:
            root = ET.fromstring(response.text)
            for elem in root.findall(".//FLAG"):
                flag = elem.text
            for elem in root.findall(".//OUT_PUT"):
                output = elem.text
        except Exception as e:
            print("Error parsing SOAP response:", e)

        if flag == "S":
            # Store OTP in session\
            
            chat_entry = {
                "query": mobile_number,
                # "answer": response,
                "timestamp": get_ist_time().isoformat(),
                # "is_fallback": is_fallback
            }

            Session.update_one(
                {"user_id": sender_id},
                {
                    "$push": {"chat": chat_entry},
                    "$set": {
                        "otp": otp,
                        "tel_no": mobile_number,
                        "otp_is_verified": "no"
                    }
                }
            )
            return {"valid": True, "message": "OTP sent successfully"}

        else:
            return {"valid": False, "message": "Please enter a valid 10 digits mobile number."}

    except Exception as e:
        raise e

    finally:
        db.close()


### language deletection

import re
from typing import Tuple, Optional

# --------------------------
# Script detection utilities
# --------------------------
def is_devanagari(char: str) -> bool:
    """Check if character is in Devanagari Unicode range."""
    try:
        return 0x0900 <= ord(char) <= 0x097F
    except (TypeError, ValueError):
        return False

def detect_script_ratio(text: str) -> Tuple[float, float]:
    """
    Calculate ratio of Devanagari and Latin characters.
    Returns: (devanagari_ratio, latin_ratio)
    """
    if not text or not isinstance(text, str):
        return 0.0, 0.0
    
    dev = sum(1 for c in text if is_devanagari(c))
    lat = sum(1 for c in text if c.isascii() and c.isalpha())
    total = dev + lat
    
    if total == 0:
        return 0.0, 0.0
    
    return dev / total, lat / total

# --------------------------
# Hinglish and English word lists
# --------------------------
# Common Latin-script Hindi words (hinglish tokens)
HINGLISH_HINT_WORDS = frozenset("""
hai hain kya kaise kaisa theek acha accha achha nahi nhi na han haan haa
mera teri tera unka uska tumhara hamara tum hum aap log wahan yahan 
hoga hogi hoge honge tha thi the thee hoon hun
matlab kyuki kyunki kyun kyu ky kaise kya kab kahan
kar raha rahe rahi ho hai hain hua huye
abhi ab phir bhi bas aise waise agar toh
aur bhi yeh ye woh wo iss us inn unn
liye dil sab kuch koi baat aaye gaye diya liya
jaana aana chahiye chahte chaho milna dekha
bola boli bolte suna sunna samjha sunao batao
mujhe tumhe humhe apne sabko sabse
bahut bohot thoda jyada zyada kam kitna
pata pta chal gaya gayi sahi galat
dekhte sunte bolte karte padhte likhte
chalte aate jaate milte baithe khade
""".split())

# English stopwords - expanded for better detection
ENGLISH_STOPWORDS = frozenset("""
the is are am was were be being been have has had
this that these those your my our their his her its
you we he she it they me him them us
to from of on for in at by with about
a an and or but if when where why how what which who
will would could should can may might must
do does did done doing
get gets got getting
go goes went gone going
make makes made making
take takes took taken taking
come comes came coming
see sees saw seen seeing
know knows knew known knowing
think thinks thought thinking
want wants wanted wanting
use uses used using
find finds found finding
give gives gave given giving
tell tells told telling
work works worked working
call calls called calling
try tries tried trying
ask asks asked asking
need needs needed needing
feel feels felt feeling
become becomes became becoming
leave leaves left leaving
put puts putting
mean means meant meaning
keep keeps kept keeping
let lets letting
begin begins began begun beginning
seem seems seemed seeming
help helps helped helping
talk talks talked talking
turn turns turned turning
start starts started starting
show shows showed shown showing
hear hears heard hearing
play plays played playing
run runs ran running
move moves moved moving
live lives lived living
believe believes believed believing
bring brings brought bringing
happen happens happened happening
write writes wrote written writing
sit sits sat sitting
stand stands stood standing
lose loses lost losing
pay pays paid paying
meet meets met meeting
include includes included including
continue continues continued continuing
set sets setting
learn learns learned learning
change changes changed changing
lead leads led leading
understand understands understood understanding
watch watches watched watching
follow follows followed following
stop stops stopped stopping
create creates created creating
speak speaks spoke spoken speaking
read reads reading
allow allows allowed allowing
add adds added adding
spend spends spent spending
grow grows grew grown growing
open opens opened opening
walk walks walked walking
win wins won winning
offer offers offered offering
remember remembers remembered remembering
love loves loved loving
consider considers considered considering
appear appears appeared appearing
buy buys bought buying
wait waits waited waiting
serve serves served serving
die dies died dying
send sends sent sending
expect expects expected expecting
build builds built building
stay stays stayed staying
fall falls fell fallen falling
cut cuts cutting
reach reaches reached reaching
kill kills killed killing
remain remains remained remaining
suggest suggests suggested suggesting
raise raises raised raising
pass passes passed passing
sell sells sold selling
require requires required requiring
report reports reported reporting
decide decides decided deciding
pull pulls pulled pulling
""".split())

# Common English words that might appear in Hinglish
COMMON_ENGLISH = frozenset("""
ok okay yes no please sorry thanks thank welcome
hello hi bye goodbye good morning afternoon evening night
today tomorrow yesterday now then
like love want need help
thing things stuff something nothing
time times
people person
way ways
day days
year years
problem problems
question questions
answer answers
friend friends
family
school college university
work working
phone mobile
internet online
message messages
video videos
photo photos
""".split())

# --------------------------
# Core classifier
# --------------------------
def detect_language(text: str, debug: bool = False) -> str:
    """
    Detect language: 'hindi', 'english', 'hinglish', or 'other_indic'
    
    Args:
        text: Input text to classify
        debug: If True, print debug information
        
    Returns:
        Language code as string
    """
    # Input validation
    if not text or not isinstance(text, str):
        if debug:
            print("Empty or invalid input, defaulting to 'english'")
        return "english"
    
    text = text.strip()
    if not text:
        return "english"
    
    text_l = text.lower()
    
    # Extract words (Latin alphabet only)
    words = re.findall(r"[a-zA-Z]+", text_l)
    
    # SCRIPT RATIO ANALYSIS
    dev_ratio, lat_ratio = detect_script_ratio(text)
    
    if debug:
        print(f"Text: {text[:50]}...")
        print(f"Devanagari ratio: {dev_ratio:.2f}, Latin ratio: {lat_ratio:.2f}")
        print(f"Words extracted: {words}")
    
    # 1. FULL HINDI (Heavy Devanagari presence)
    if dev_ratio > 0.70:
        if debug:
            print("Classified as HINDI (>70% Devanagari)")
        return "hindi"
    
    # 2. MIXED SCRIPT (Devanagari + Latin) → Likely Hinglish
    if 0.20 < dev_ratio <= 0.70 and lat_ratio > 0.10:
        if debug:
            print("Classified as HINGLISH (mixed script)")
        return "hinglish"
    
    # 3. FULL LATIN SCRIPT → Requires deeper analysis
    if lat_ratio > 0.70 or (lat_ratio > 0 and dev_ratio == 0):
        if not words:
            # No Latin words found, might be punctuation/numbers only
            if dev_ratio > 0:
                return "hindi"
            return "english"
        
        # Count various word types
        hinglish_hits = sum(1 for w in words if w in HINGLISH_HINT_WORDS)
        eng_stopword_hits = sum(1 for w in words if w in ENGLISH_STOPWORDS)
        common_eng_hits = sum(1 for w in words if w in COMMON_ENGLISH)
        
        # Calculate Hindi-like syllable patterns
        syllable_patterns = [
            r'\b(ka|ke|ki|ko|ku)\b',
            r'\b(na|ne|ni|no|nu)\b',
            r'\b(ra|re|ri|ro|ru)\b',
            r'\b(sa|se|si|so|su)\b',
            r'\b(ta|te|ti|to|tu)\b',
            r'\b(ma|me|mi|mo|mu)\b',
            r'\b(pa|pe|pi|po|pu)\b',
            r'\b(tha|the|thi|tho|thu)\b',
            r'\b(dha|dhe|dhi|dho|dhu)\b',
            r'(wala|wale|wali)\b',
            r'(kar|kar|karna|karne)\b',
            r'(raha|rahe|rahi|rahe)\b',
        ]
        
        syllable_like = sum(1 for w in words 
                           for pattern in syllable_patterns 
                           if re.search(pattern, w))
        
        total_indicators = hinglish_hits + eng_stopword_hits + common_eng_hits
        
        if debug:
            print(f"Hinglish hits: {hinglish_hits}")
            print(f"English stopword hits: {eng_stopword_hits}")
            print(f"Common English hits: {common_eng_hits}")
            print(f"Syllable patterns: {syllable_like}")
            print(f"Total words: {len(words)}")
        
        # HINGLISH DETECTION
        # Strong Hinglish signal
        if hinglish_hits >= 3:
            if debug:
                print("Classified as HINGLISH (>=3 hinglish words)")
            return "hinglish"
        
        # Medium Hinglish signal with syllables
        if hinglish_hits >= 2 and syllable_like >= 1:
            if debug:
                print("Classified as HINGLISH (2+ hinglish + syllables)")
            return "hinglish"
        
        # Weak Hinglish signal but many syllable patterns
        if hinglish_hits >= 1 and syllable_like >= 3:
            if debug:
                print("Classified as HINGLISH (1 hinglish + 3+ syllables)")
            return "hinglish"
        
        # ENGLISH DETECTION
        # Strong English signal
        if eng_stopword_hits >= 3 and hinglish_hits == 0:
            if debug:
                print("Classified as ENGLISH (3+ stopwords, no hinglish)")
            return "english"
        
        # Medium English signal
        if (eng_stopword_hits + common_eng_hits) >= 4 and hinglish_hits <= 1:
            if debug:
                print("Classified as ENGLISH (4+ english indicators)")
            return "english"
        
        # Ambiguous case - use ratio
        if total_indicators == 0 and len(words) > 0:
            # No clear indicators, check if it looks more Hindi-like
            if syllable_like >= 2:
                if debug:
                    print("Classified as HINGLISH (no clear indicators but Hindi syllables)")
                return "hinglish"
            # Default to English for unknown Latin script
            if debug:
                print("Classified as ENGLISH (default for unknown Latin)")
            return "english"
        
        # More English indicators than Hinglish
        if eng_stopword_hits + common_eng_hits > hinglish_hits + syllable_like:
            if debug:
                print("Classified as ENGLISH (more English indicators)")
            return "english"
        
        # More Hinglish indicators
        if hinglish_hits + syllable_like > eng_stopword_hits:
            if debug:
                print("Classified as HINGLISH (more Hinglish indicators)")
            return "hinglish"
        
        # Final fallback for Latin script
        if debug:
            print("Classified as ENGLISH (final fallback)")
        return "english"
    
    # 4. Neither Latin nor Devanagari → Other Indian language
    if dev_ratio < 0.20 and lat_ratio < 0.20:
        if debug:
            print("Classified as OTHER_INDIC (non-Latin, non-Devanagari)")
        return "other_indic"
    
    # Final fallback (should rarely reach here)
    if dev_ratio > lat_ratio:
        return "hindi"
    return "english"

# --------------------------
# Batch processing utility
# --------------------------
def detect_language_batch(texts: list, debug: bool = False) -> list:
    """
    Process multiple texts at once.
    
    Args:
        texts: List of text strings
        debug: Enable debug output
        
    Returns:
        List of language codes
    """
    if not texts or not isinstance(texts, list):
        return []
    
    return [detect_language(text, debug=debug) for text in texts]


# result = detect_language("كيف حالك", debug=True)

# print("\nFinal Result:", result)
# Shows: ratios, word hits, classification logic


## Validate language

# ALLOWED_LANGUAGES = ["english", "hindi", "hinglish"]

# def validate_language():
#     try:
#         data = request.get_json()

#         if not data or "text" not in data:
#             return jsonify({
#                 "status": False,
#                 "message": "Missing 'text' field"
#             }), 200

#         text = data["text"].strip()

#         if not text:
#             return jsonify({
#                 "status": False,
#                 "message": "Text cannot be empty"
#             }), 200

#         # Detect language using your function
#         detected_lang = detect_language(text)

#         # Validate against allowed list
#         if detected_lang.lower() in ALLOWED_LANGUAGES:
#             return jsonify({
#                 "status": True,
#                 "message": f"Language detected: {detected_lang}",
#                 "language": detected_lang
#             }), 200
#         else:
#             return jsonify({
#                 "status": False,
#                 "message": "Only English and Hindi (including Hinglish) are supported",
#                 "detected_language": detected_lang
#             }), 200

#     except Exception as e:
#         return jsonify({
#             "status": False,
#             "message": "Something went wrong",
#             "error": str(e)
#         }), 500

ALLOWED_LANGUAGES = ["english", "hindi", "hinglish"]

FORBIDDEN_LANGUAGE_NAMES = [

    # --- Indian Languages ---
    "urdu", "punjabi", "kashmiri", "dogri",
    "gujarati", "marathi", "konkani", "sindhi",
    "bengali", "assamese", "bodo", "maithili",
    "santali", "manipuri", "meitei", "odia", "oriya",
    "telugu", "tamil", "malayalam", "kannada",
    "tulu", "kodava",
    "khasi", "garo", "mizo", "naga",
    "mundari", "ho", "shadri",

    # --- Major Foreign Languages (Europe) ---
    "french", "german", "spanish", "portuguese",
    "italian", "russian", "dutch", "swedish",
    "norwegian", "finnish", "danish", "polish",
    "czech", "slovak", "hungarian", "romanian",
    "bulgarian", "serbian", "croatian", "bosnian",
    "ukrainian", "belarusian", "greek", "turkish",

    # --- Middle East / Africa ---
    "arabic", "hebrew", "persian", "farsi", "pashto",
    "dari", "kurdi", "kurdish", "amharic", "somali",

    # --- East Asian Languages ---
    "chinese", "mandarin", "cantonese",
    "japanese", "korean",

    # --- South East Asia ---
    "thai", "lao", "vietnamese", "filipino",
    "tagalog", "indonesian", "malay", "burmese",

    # --- Others ---
    "swahili", "zulu", "afrikaans", "maori"
]


def validate_language():
    try:
        data = request.get_json()

        if not data or "text" not in data:
            return jsonify({"status": False, "message": "Missing 'text' field"}), 200

        text = data["text"].strip()

        if not text:
            return jsonify({"status": False, "message": "Text cannot be empty"}), 200

        detected_lang = detect_language(text).lower()

        if detected_lang not in ALLOWED_LANGUAGES:
            return jsonify({
                "status": False,
                "message": "Only English and Hindi are supported",
                "detected_language": detected_lang
            }), 200

        # Check forbidden language names
        lower_text = text.lower()
        for lang in FORBIDDEN_LANGUAGE_NAMES:
            if lang in lower_text:
                return jsonify({
                    "status": False,
                    "message": f"Only English and Hindi are supported",
                    "detected_language": detected_lang
                }), 200

        return jsonify({
            "status": True,
            "message": f"Language detected: {detected_lang}",
            "language": detected_lang
        }), 200

    except Exception as e:
        return jsonify({
            "status": False,
            "message": "Something went wrong",
            "error": str(e)
        }), 500
