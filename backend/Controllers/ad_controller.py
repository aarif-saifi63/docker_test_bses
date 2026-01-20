import json
import os
import uuid
from utils.input_validator import InputValidator
from utils.file_security_helper import FileSecurityHelper
from utils.request_security import validate_multipart_request
import magic
import re
import requests
from Models.intent_model import IntentV
from Models.sub_menu_option_model import SubMenuOptionV
from flask import request, jsonify
from werkzeug.utils import secure_filename
from Models.ad_model import Advertisement
from dotenv import load_dotenv
import os
import logging
from Models.session_model import Session
from Models.sub_menu_option_model import SubMenuOptionV
from database import SessionLocal
from sqlalchemy import func, or_, Integer
from sqlalchemy.dialects.postgresql import array

# Load .env file
load_dotenv()

RASA_API_URL = os.getenv('RASA_CORE_URL')
# RASA_API_URL = f"{os.getenv('BASE_URL')}:{os.getenv('RASA_CORE_PORT')}"

# Folder where ads will be saved - SECURE: Store outside webroot in production
UPLOAD_DIR = "Media/ad_content"
os.makedirs(UPLOAD_DIR, exist_ok=True)




# Configure logger
logging.basicConfig(
    filename='error.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)

from datetime import datetime, timedelta, timezone
import pytz

IST = pytz.timezone("Asia/Kolkata")
# IST = pytz.timezone("Asia/Kolkata")


def add_ad():
    db = None  # Initialize db to None to avoid UnboundLocalError
    try:
        # SECURITY: Validate multipart request using centralized security module
        is_valid, error_message = validate_multipart_request()
        if not is_valid:
            return jsonify({
                "status": False,
                "message": error_message
            }), 400

        db = SessionLocal()

        ad_name = request.form.get("ad_name")
        ad_type = request.form.get("ad_type")
        chatbot_options = request.form.get("chatbot_options")
        division_list = request.form.get("divisions")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        is_active = request.form.get("is_active", "true").lower() == "true"

        # ===== Input Validation =====

        is_valid, msg = InputValidator.validate_name(ad_name, "ad_name")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400

        if not ad_name:
            return jsonify({"status": False, "message": "ad_name is required"}), 400
        if not ad_type:
            return jsonify({"status": False, "message": "ad_type is required"}), 400
        if not chatbot_options:
            return jsonify({"status": False, "message": "chatbot_options is required"}), 400
        if ad_type != "on_chatbot_launch" and not division_list:
            return jsonify({"status": False, "message": "divisions is required"}), 400
        if not start_time or not end_time:
            return jsonify({"status": False, "message": "start_time and end_time are required"}), 400

        # ===== Parse and localize time fields =====
        try:
            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)

            if start_time.tzinfo is None:
                start_time = IST.localize(start_time)
            else:
                start_time = start_time.astimezone(IST)

            if end_time.tzinfo is None:
                end_time = IST.localize(end_time)
            else:
                end_time = end_time.astimezone(IST)
        except Exception:
            return jsonify({"status": False, "message": "Invalid datetime format for start_time/end_time"}), 400

        if start_time > end_time:
            return jsonify({"status": False, "message": "End time must be after start time"}), 400

        # ===== Check ad_name uniqueness =====
        if Advertisement.find_one(ad_name=ad_name):
            return jsonify({
                "status": False,
                "message": f"Advertisement with ad_name '{ad_name}' already exists"
            }), 400

        # ===== Parse chatbot_options =====
        try:
            chatbot_options_list = json.loads(chatbot_options)
            if not isinstance(chatbot_options_list, list):
                raise ValueError
        except Exception as e:
            logging.error(f"Invalid chatbot_options JSON: {e}")
            return jsonify({"status": False, "message": "chatbot_options must be a valid JSON array"}), 400

        # ===== Parse division_list =====
        divisions_list = []
        if ad_type != "on_chatbot_launch":
            try:
                divisions_list = json.loads(division_list)
                if not isinstance(divisions_list, list):
                    raise ValueError
            except Exception as e:
                logging.error(f"Invalid divisions JSON: {e}")
                return jsonify({"status": False, "message": "divisions must be a valid JSON array"}), 400

        # ===== Query existing ads of same ad_type =====
        existing_ads = db.query(Advertisement).filter(Advertisement.ad_type == ad_type).all()

        # ===== Overlap Checking =====
        for ad in existing_ads:
            if not ad.is_active:
                continue

            db_start = ad.start_time
            db_end = ad.end_time

            # Normalize DB times to IST
            if db_start.tzinfo is None:
                db_start = IST.localize(db_start)
            else:
                db_start = db_start.astimezone(IST)
            if db_end.tzinfo is None:
                db_end = IST.localize(db_end)
            else:
                db_end = db_end.astimezone(IST)

            # Case 1: on_chatbot_launch — strict single timeframe
            if ad_type == "on_chatbot_launch":
                if (start_time <= db_end) and (end_time >= db_start):
                    msg = (
                        f"Time conflict: '{ad.ad_name}' already exists "
                        f"({format_datetime_display(db_start)} → {format_datetime_display(db_end)})"
                    )
                    return jsonify({"status": False, "message": msg}), 400

            # Case 2: Other ad types — modified overlap logic
            else:
                time_conflict = (start_time <= db_end) and (end_time >= db_start)
                if not time_conflict:
                    continue

                # ✅ Allow same chatbot_options for different divisions
                overlapping_opts = [opt for opt in chatbot_options_list if opt in ad.chatbot_options]
                overlapping_divs = [div for div in divisions_list if div in ad.divisions_list]

                # Conflict only if BOTH chatbot_options AND divisions overlap
                if overlapping_opts and overlapping_divs:
                    def quoted_list(items):
                        return ', '.join([f"'{i}'" for i in items])

                    msg = (
                        f"'{ad.ad_name}' advertisement conflicts with chatbot options "
                        f"{quoted_list(overlapping_opts)} and divisions {quoted_list(overlapping_divs)} "
                        f"in timeframe \"{format_datetime_display(db_start)} → {format_datetime_display(db_end)}\""
                    )
                    return jsonify({"status": False, "message": msg}), 400

        # ===== SECURE File Upload Handling =====
        ad_image_path = None
        ad_pdf_path = None

        # SECURITY: Handle thumbnail image upload with comprehensive validation
        if "ad_image" in request.files:
            ad_image_file = request.files["ad_image"]
            if ad_image_file and ad_image_file.filename:
                success, filepath, error = FileSecurityHelper.validate_and_save_file(
                    ad_image_file,
                    upload_dir=UPLOAD_DIR,
                    allowed_categories=["image"]
                )
                if not success:
                    return jsonify({
                        "status": False,
                        "message": f"Thumbnail upload failed: {error}"
                    }), 400
                ad_image_path = filepath

        # SECURITY: Handle attachment upload with comprehensive validation
        if "ad_pdf" in request.files:
            ad_pdf_file = request.files["ad_pdf"]
            if ad_pdf_file and ad_pdf_file.filename:
                success, filepath, error = FileSecurityHelper.validate_and_save_file(
                    ad_pdf_file,
                    upload_dir=UPLOAD_DIR,
                    allowed_categories=["image", "document", "video"]
                )
                if not success:
                    return jsonify({
                        "status": False,
                        "message": f"Attachment upload failed: {error}"
                    }), 400
                ad_pdf_path = filepath

        if not ad_image_path or not ad_pdf_path:
            return jsonify({"status": False, "message": "Thumbnail or Attachment is missing"}), 400

        # ===== Save Advertisement =====
        ad = Advertisement(
            ad_name=ad_name,
            ad_type=ad_type,
            ad_image_path=ad_image_path,
            ad_pdf_path=ad_pdf_path,
            chatbot_options=chatbot_options_list,
            divisions_list=divisions_list,
            start_time=start_time,
            end_time=end_time,
            is_active=is_active
        )
        ad_id = ad.save()

        return jsonify({
            "status": True,
            "message": "Advertisement added successfully",
            "data": {
                "id": ad_id,
                "ad_name": ad_name,
                "ad_type": ad_type,
                "chatbot_options": chatbot_options_list,
                "division_list": divisions_list
            }
        }), 201

    except Exception as e:
        logging.error(f"Unexpected error in add_ad: {str(e)}", exc_info=True)
        return jsonify({"status": False, "message": str(e)}), 500
    finally:
        if db is not None:
            db.close()



# def update_ad():
#     try:
#         ad_id = request.args.get("ad_id")
#         if not ad_id:
#             return jsonify({"status": False, "message": "ad_id is required"}), 400
#         ad_id = str(ad_id)

#         with SessionLocal() as db:
#             ad = Advertisement.find_one(db=db, id=ad_id)
#             if not ad:
#                 return jsonify({"status": False, "message": "Advertisement not found"}), 404

#             # ===== Get updated fields or fallback =====
#             ad_name = request.form.get("ad_name") or ad.ad_name
#             ad_type = request.form.get("ad_type") or ad.ad_type
#             chatbot_options = request.form.get("chatbot_options")
#             division_list = request.form.get("divisions") or ad.divisions_list
#             start_time = request.form.get("start_time") or ad.start_time
#             end_time = request.form.get("end_time") or ad.end_time
#             is_active = request.form.get("is_active")
#             if is_active is not None:
#                 is_active = is_active.lower() == "true"

#             if start_time > end_time:
#                 return jsonify({"status": False, "message": "Time Conflict: End time of Advertisement is less than Start time"}), 400
            

#             # # ===== Check ad_name uniqueness =====
#             # if Advertisement.find_one(ad_name=ad_name):
#             #     return jsonify({
#             #         "status": False,
#             #         "message": f"Advertisement with ad_name '{ad_name}' already exists"
#             #     }), 400

#             # ===== Check ad_name uniqueness =====
#             existing_ad_with_name = db.query(Advertisement).filter(
#                 Advertisement.ad_name == ad_name,
#                 Advertisement.id != ad_id  # exclude the current ad being updated
#             ).first()

#             if existing_ad_with_name:
#                 return jsonify({
#                     "status": False,
#                     "message": f"Advertisement with ad_name '{ad_name}' already exists"
#                 }), 400

#             # ===== Validate JSON inputs =====
#             if chatbot_options:
#                 try:
#                     chatbot_options_list = json.loads(chatbot_options)
#                     if not isinstance(chatbot_options_list, list):
#                         raise ValueError
#                 except Exception:
#                     return jsonify({"status": False, "message": "chatbot_options must be a JSON array"}), 400
#             else:
#                 chatbot_options_list = ad.chatbot_options

#             if isinstance(division_list, str):
#                 try:
#                     division_list = json.loads(division_list)
#                     if not isinstance(division_list, list):
#                         raise ValueError
#                 except Exception:
#                     return jsonify({"status": False, "message": "divisions must be a JSON array"}), 400

#             # ===== Parse datetime fields =====
#             try:
#                 start_time = datetime.fromisoformat(str(start_time)) if isinstance(start_time, str) else start_time
#                 end_time = datetime.fromisoformat(str(end_time)) if isinstance(end_time, str) else end_time
#             except Exception:
#                 return jsonify({"status": False, "message": "Invalid datetime format"}), 400

#             # ===== Fetch other ads of same type =====
#             existing_ads = db.query(Advertisement).filter(
#                 Advertisement.ad_type == ad_type,
#                 Advertisement.id != ad_id
#             ).all()

#             # ===== Validation Rules =====
#             if ad_type == "on_chatbot_launch":
#                 # Only one ad per timeframe — no overlaps
#                 for existing_ad in existing_ads:
#                     if not existing_ad.is_active:
#                         continue
#                     if (start_time <= existing_ad.end_time) and (end_time >= existing_ad.start_time):
#                         msg = (
#                             f"Time conflict: '{existing_ad.ad_name}' already exists "
#                             f"({existing_ad.start_time.isoformat()} → {existing_ad.end_time.isoformat()})"
#                         )
#                         return jsonify({"status": False, "message": msg}), 400

#             else:
#                 # Other ad types → check overlap + division/option conflict
#                 for existing_ad in existing_ads:
#                     if not existing_ad.is_active:
#                         continue

#                     # Overlap check
#                     time_conflict = (start_time <= existing_ad.end_time) and (end_time >= existing_ad.start_time)
#                     if not time_conflict:
#                         continue  # Non-overlapping timeframe → no issue

#                     # If time overlaps, check for shared chatbot_options or divisions
#                     overlapping_opts = []
#                     overlapping_divs = []

#                     if existing_ad.chatbot_options:
#                         overlapping_opts = [
#                             opt for opt in chatbot_options_list if opt in existing_ad.chatbot_options
#                         ]

#                     if existing_ad.divisions_list:
#                         overlapping_divs = [
#                             div for div in division_list if div in existing_ad.divisions_list
#                         ]

#                     if overlapping_opts or overlapping_divs:
#                         conflict_items = []
#                         if overlapping_opts:
#                             conflict_items.append(f"{overlapping_opts}")
#                         if overlapping_divs:
#                             conflict_items.append(f"{overlapping_divs}")

#                         # msg = (
#                         #     f"Conflict: {', '.join(conflict_items)} already exist in '{existing_ad.ad_name}' "
#                         #     f"during overlapping timeframe ({existing_ad.start_time.isoformat()} → {existing_ad.end_time.isoformat()})"
#                         # )

#                         def quoted_list(items):
#                             return ', '.join([f"'{i}'" for i in items])

#                         msg = (
#                             f"'{ad.ad_name}' advertisement for chatbot options "
#                             f"{quoted_list(conflict_items)}, "
#                             f"divisions and timeframe "
#                             f"\"{ad.start_time.isoformat()} → {ad.end_time.isoformat()}\" already exists"
#                         )

#                         return jsonify({"status": False, "message": msg}), 400

#             # # ===== File Upload Handling =====
#             # if "ad_image" in request.files:
#             #     file = request.files["ad_image"]
#             #     if file and allowed_file(file.filename):
#             #         filename = secure_filename(file.filename)
#             #         filepath = os.path.join(UPLOAD_FOLDER, filename)
#             #         file.save(filepath)
#             #         ad.ad_image_path = os.path.join("Media/ad_content", filename)

#             # if "ad_pdf" in request.files:
#             #     file = request.files["ad_pdf"]
#             #     if file and allowed_file(file.filename):
#             #         filename = secure_filename(file.filename)
#             #         filepath = os.path.join(UPLOAD_FOLDER, filename)
#             #         file.save(filepath)
#             #         ad.ad_pdf_path = os.path.join("Media/ad_content", filename)


#             # ---- Handle ad_image ----
#             if "ad_image" in request.files:
#                 file = request.files["ad_image"]
#                 if file and allowed_file_type(file.filename, "image"):
#                     filename = secure_filename(file.filename)
#                     filepath = os.path.join(UPLOAD_FOLDER, filename)
#                     file.save(filepath)
#                     ad_image_path = os.path.join("/Media/ad_content", filename)
#                 else:
#                     return jsonify({
#                         "status": False,
#                         "message": "Invalid ad_image format. Only png, jpg, jpeg allowed."
#                     }), 400

#             # ---- Handle ad_pdf (can be image, document, or video) ----
#             if "ad_pdf" in request.files:
#                 file = request.files["ad_pdf"]
#                 filename = file.filename
#                 if not filename:
#                     return jsonify({"status": False, "message": "No file provided for ad_pdf"}), 400

#                 ext = filename.rsplit('.', 1)[1].lower()

#                 # Determine category based on extension
#                 if ext in ALLOWED_EXTENSIONS["image"]:
#                     category = "image"
#                 elif ext in ALLOWED_EXTENSIONS["document"]:
#                     category = "document"
#                 elif ext in ALLOWED_EXTENSIONS["video"]:
#                     category = "video"
#                 else:
#                     return jsonify({
#                         "status": False,
#                         "message": "Invalid file type. "
#                                 "Allowed Format: Images (png, jpg, jpeg), "
#                                 "Documents (pdf, doc, docx), Videos (mp4, mkv, webm, avi)."
#                     }), 400

#                 filename = secure_filename(filename)
#                 filepath = os.path.join(UPLOAD_FOLDER, filename)
#                 file.save(filepath)
#                 ad_pdf_path = os.path.join("/Media/ad_content", filename)

#             if not ad.ad_image_path or not ad.ad_pdf_path:
#                 return jsonify({"status": False, "message": "Thumbnail or Attachment is missing"}), 400

#             # ===== Apply updates =====
#             ad.ad_name = ad_name
#             ad.ad_type = ad_type
#             ad.chatbot_options = chatbot_options_list
#             ad.divisions_list = division_list
#             ad.start_time = start_time
#             ad.end_time = end_time
#             if is_active is not None:
#                 ad.is_active = is_active

#             ad.save(db=db)
#             db.commit()

#             return jsonify({
#                 "status": True,
#                 "message": "Advertisement updated successfully",
#                 "data": {
#                     "id": ad.id,
#                     "ad_name": ad.ad_name,
#                     "ad_type": ad.ad_type,
#                     "chatbot_options": ad.chatbot_options,
#                     "division_list": ad.divisions_list
#                 }
#             }), 200

#     except Exception as e:
#         logging.error(f"Unexpected error in update_ad for ad_id {ad_id}: {str(e)}", exc_info=True)
#         return jsonify({"status": False, "message": str(e)}), 500


def update_ad():
    try:
        # SECURITY: Validate multipart request using centralized security module
        is_valid, error_message = validate_multipart_request()
        if not is_valid:
            return jsonify({
                "status": False,
                "message": error_message
            }), 400

        ad_id = request.args.get("ad_id")
        if not ad_id:
            return jsonify({"status": False, "message": "ad_id is required"}), 400
        ad_id = str(ad_id)

        with SessionLocal() as db:
            ad = Advertisement.find_one(db=db, id=ad_id)
            if not ad:
                return jsonify({"status": False, "message": "Advertisement not found"}), 404

            # ===== Get updated fields or fallback =====
            ad_name = request.form.get("ad_name") or ad.ad_name
            ad_type = request.form.get("ad_type") or ad.ad_type
            chatbot_options = request.form.get("chatbot_options")
            division_list = request.form.get("divisions") or ad.divisions_list
            start_time = request.form.get("start_time") or ad.start_time
            end_time = request.form.get("end_time") or ad.end_time
            is_active = request.form.get("is_active")
            if is_active is not None:
                is_active = is_active.lower() == "true"

            # ===== Parse and validate time =====
            try:
                start_time = datetime.fromisoformat(str(start_time)) if isinstance(start_time, str) else start_time
                end_time = datetime.fromisoformat(str(end_time)) if isinstance(end_time, str) else end_time
            except Exception:
                return jsonify({"status": False, "message": "Invalid datetime format"}), 400

            is_valid, msg = InputValidator.validate_name(ad_name, "ad_name")
            if not is_valid:
                return jsonify({"status": False, "message": msg}), 400


            if start_time > end_time:
                return jsonify({"status": False, "message": "End time must be after Start time"}), 400

            # ===== ad_name uniqueness (excluding current ad) =====
            existing_ad_with_name = db.query(Advertisement).filter(
                Advertisement.ad_name == ad_name,
                Advertisement.id != ad_id
            ).first()

            if existing_ad_with_name:
                return jsonify({
                    "status": False,
                    "message": f"Advertisement with ad_name '{ad_name}' already exists"
                }), 400

            # ===== Validate and parse JSON inputs =====
            if chatbot_options:
                try:
                    chatbot_options_list = json.loads(chatbot_options)
                    if not isinstance(chatbot_options_list, list):
                        raise ValueError
                except Exception:
                    return jsonify({"status": False, "message": "chatbot_options must be a JSON array"}), 400
            else:
                chatbot_options_list = ad.chatbot_options

            if isinstance(division_list, str):
                try:
                    division_list = json.loads(division_list)
                    if not isinstance(division_list, list):
                        raise ValueError
                except Exception:
                    return jsonify({"status": False, "message": "divisions must be a JSON array"}), 400

            # ===== Fetch other ads of same type =====
            existing_ads = db.query(Advertisement).filter(
                Advertisement.ad_type == ad_type,
                Advertisement.id != ad_id
            ).all()

            # ===== Validation Rules =====
            if ad_type == "on_chatbot_launch":
                # Only one ad per timeframe — no overlaps
                for existing_ad in existing_ads:
                    if not existing_ad.is_active:
                        continue
                    if (start_time <= existing_ad.end_time) and (end_time >= existing_ad.start_time):
                        msg = (
                            f"Time conflict: '{existing_ad.ad_name}' already exists "
                            f"({format_datetime_display(existing_ad.start_time)} → {format_datetime_display(existing_ad.end_time)})"
                        )
                        return jsonify({"status": False, "message": msg}), 400

            else:
                # Other ad types — allow same chatbot_options for different divisions
                for existing_ad in existing_ads:
                    if not existing_ad.is_active:
                        continue

                    time_conflict = (start_time <= existing_ad.end_time) and (end_time >= existing_ad.start_time)
                    if not time_conflict:
                        continue

                    overlapping_opts = []
                    overlapping_divs = []

                    if existing_ad.chatbot_options:
                        overlapping_opts = [
                            opt for opt in chatbot_options_list if opt in existing_ad.chatbot_options
                        ]

                    if existing_ad.divisions_list:
                        overlapping_divs = [
                            div for div in division_list if div in existing_ad.divisions_list
                        ]

                    # ✅ Conflict only if BOTH chatbot_options and divisions overlap
                    if overlapping_opts and overlapping_divs:
                        def quoted_list(items):
                            return ', '.join([f"'{i}'" for i in items])

                        msg = (
                            f"Conflict: '{existing_ad.ad_name}' already uses chatbot options "
                            f"{quoted_list(overlapping_opts)} and divisions {quoted_list(overlapping_divs)} "
                            f"in timeframe ({format_datetime_display(existing_ad.start_time)} → {format_datetime_display(existing_ad.end_time)})"
                        )
                        return jsonify({"status": False, "message": msg}), 400

            # ===== SECURE File Upload Handling =====
            ad_image_path = ad.ad_image_path
            ad_pdf_path = ad.ad_pdf_path

            # SECURITY: Handle thumbnail image upload with comprehensive validation
            if "ad_image" in request.files:
                ad_image_file = request.files["ad_image"]
                if ad_image_file and ad_image_file.filename:
                    success, filepath, error = FileSecurityHelper.validate_and_save_file(
                        ad_image_file,
                        upload_dir=UPLOAD_DIR,
                        allowed_categories=["image"]
                    )
                    if not success:
                        return jsonify({
                            "status": False,
                            "message": f"Thumbnail upload failed: {error}"
                        }), 400
                    ad_image_path = filepath

            # SECURITY: Handle attachment upload with comprehensive validation
            if "ad_pdf" in request.files:
                ad_pdf_file = request.files["ad_pdf"]
                if ad_pdf_file and ad_pdf_file.filename:
                    success, filepath, error = FileSecurityHelper.validate_and_save_file(
                        ad_pdf_file,
                        upload_dir=UPLOAD_DIR,
                        allowed_categories=["image", "document", "video"]
                    )
                    if not success:
                        return jsonify({
                            "status": False,
                            "message": f"Attachment upload failed: {error}"
                        }), 400
                    ad_pdf_path = filepath

            if not ad_image_path or not ad_pdf_path:
                return jsonify({"status": False, "message": "Thumbnail or Attachment is missing"}), 400

            # ===== Apply updates =====
            ad.ad_name = ad_name
            ad.ad_type = ad_type
            ad.chatbot_options = chatbot_options_list
            ad.divisions_list = division_list
            ad.start_time = start_time
            ad.end_time = end_time
            ad.ad_image_path = ad_image_path
            ad.ad_pdf_path = ad_pdf_path
            if is_active is not None:
                ad.is_active = is_active

            ad.save(db=db)
            db.commit()

            return jsonify({
                "status": True,
                "message": "Advertisement updated successfully",
                "data": {
                    "id": ad.id,
                    "ad_name": ad.ad_name,
                    "ad_type": ad.ad_type,
                    "chatbot_options": ad.chatbot_options,
                    "division_list": ad.divisions_list
                }
            }), 200

    except Exception as e:
        logging.error(f"Unexpected error in update_ad for ad_id {ad_id}: {str(e)}", exc_info=True)
        return jsonify({"status": False, "message": str(e)}), 500
    finally:
        db.close()



def delete_ad():
    try:
        # Validate ad_id
        ad_id = request.args.get("ad_id")
        if not ad_id:
            return jsonify({"status": False, "message": "ad_id is required"}), 400

        # Use a single session for all database operations
        with SessionLocal() as db:
            logging.debug(f"Starting delete_ad with session {id(db)} for ad_id {ad_id}")

            # Find the advertisement
            ad = Advertisement.find_one(db=db, id=ad_id)
            if not ad:
                return jsonify({"status": False, "message": "Advertisement not found"}), 404

            # Optionally delete associated files
            if ad.ad_image_path and os.path.exists(os.path.join(UPLOAD_DIR, ad.ad_image_path)):
                try:
                    os.remove(os.path.join(UPLOAD_DIR, ad.ad_image_path))
                    logging.debug(f"Deleted file {ad.ad_image_path} for ad_id {ad_id}")
                except Exception as e:
                    logging.warning(f"Failed to delete file {ad.ad_image_path}: {str(e)}")
            if ad.ad_pdf_path and os.path.exists(os.path.join(UPLOAD_DIR, ad.ad_pdf_path)):
                try:
                    os.remove(os.path.join(UPLOAD_DIR, ad.ad_pdf_path))
                    logging.debug(f"Deleted file {ad.ad_pdf_path} for ad_id {ad_id}")
                except Exception as e:
                    logging.warning(f"Failed to delete file {ad.ad_pdf_path}: {str(e)}")

            # Delete the advertisement
            ad.delete(db=db)

            logging.debug(f"Successfully deleted Advertisement {ad_id} with session {id(db)}")

            return jsonify({
                "status": True,
                "message": "Advertisement deleted successfully"
            }), 200

    except Exception as e:
        logging.error(f"Unexpected error in delete_ad for ad_id {ad_id}: {str(e)}", exc_info=True)
        return jsonify({"status": False, "message": str(e)}), 500
    finally:
        db.close()






def current_time_ist():
    return datetime.now(IST)


def format_datetime_display(dt):
    """
    Format datetime for user-friendly display
    Format: DD-MM-YYYY, HH:MM
    """
    if dt is None:
        return "N/A"
    return dt.strftime("%d-%m-%Y, %H:%M")


def generate_signed_url_for_file(file_path, expires_in=300):
    """
    Generate a signed URL for secure file download

    Args:
        file_path: Relative path to the file (e.g., "ad_content/xxx.pdf")
        expires_in: Expiration time in seconds (default: 5 minutes)

    Returns:
        Signed URL string or original path if signing fails
    """
    try:
        import hmac
        import hashlib
        import base64
        import time
        import urllib.parse
        from flask import current_app, request

        # Handle both old and new file path formats
        # Old format: /Media/ad_content/xxx.pdf or Media/ad_content/xxx.pdf
        # New format: ad_content/xxx.pdf
        file_rel = file_path.lstrip("/")  # Remove leading slash

        # Remove 'Media/' prefix if present (for backward compatibility)
        if file_rel.startswith("Media/"):
            file_rel = file_rel[6:]  # Remove 'Media/' prefix

        # Get secret key from app config
        secret_key = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")

        # Generate expiry timestamp
        expires_ts = int(time.time()) + expires_in

        # Create HMAC signature
        msg = f"{file_rel}|{expires_ts}".encode("utf-8")
        mac = hmac.new(secret_key.encode("utf-8"), msg, hashlib.sha256).digest()
        sig = base64.urlsafe_b64encode(mac).rstrip(b"=").decode("ascii")

        # Build signed URL
        host = request.host_url.rstrip("/")
        download_path = "/files/download"
        qs = urllib.parse.urlencode({
            "file": file_rel,
            "expires": str(expires_ts),
            "sig": sig
        })

        return f"{download_path}?{qs}"

    except Exception as e:
        logging.error(f"Error generating signed URL: {str(e)}")
        # Fallback to original path if signing fails
        return file_path


def get_ad():
    try:
        ad_type = request.args.get("ad_type")
        chat_option = request.args.get("chat_option")
        sender_id = request.args.get("senderId")

        if not ad_type or not chat_option:
            return jsonify({"error": "Both ad_type and chat_option are required", "status": False}), 200


        now = current_time_ist()

        if now.tzinfo:
            now = now.replace(tzinfo=None)

        db = SessionLocal()
        division_name = None
        result = Session.get_division_by_user_id(sender_id)
        if result["status"] == "success":
            division_name = result["division_name"]

        # Fetch only active ads with the given ad_type

        if division_name:
            print("================================ division_name")
            ads = db.query(Advertisement).filter(
                Advertisement.ad_type == ad_type,
                Advertisement.is_active == True,
                Advertisement.start_time <= now,
                Advertisement.end_time >= now,
                Advertisement.divisions_list.contains([division_name])
            ).all()

            if not ads:
                print("================================ division_name no ad")
                ads = db.query(Advertisement).filter(
                Advertisement.ad_type == ad_type,
                Advertisement.is_active == True,
                (Advertisement.divisions_list == None) | (Advertisement.divisions_list == [])
                # Advertisement.start_time <= now,
                # Advertisement.end_time >= now,
                # Advertisement.divisions_list.contains([division_name])
            ).all()
        else:
            ads = db.query(Advertisement).filter(
                Advertisement.ad_type == ad_type,
                Advertisement.is_active == True,
                (Advertisement.divisions_list == None) | (Advertisement.divisions_list == [])
                # Advertisement.start_time <= now,
                # Advertisement.end_time >= now,
                # Advertisement.divisions_list.contains([division_name])
            ).all()

        if not ads:
            return jsonify({"data": {}, "status": False}), 200

        # Find ad that contains the given chat_option in chatbot_options
        matched_ad = None
        for ad in ads:
            if ad.chatbot_options:
                # chatbot_options is stored as JSON (list or dict)
                if isinstance(ad.chatbot_options, (list, dict)):
                    if chat_option in ad.chatbot_options:
                        matched_ad = ad
                        break
                elif isinstance(ad.chatbot_options, str):
                    # In case it's stored as a JSON string
                    import json
                    try:
                        options = json.loads(ad.chatbot_options)
                        if chat_option in options:
                            matched_ad = ad
                            break
                    except Exception:
                        pass

        if not matched_ad:
            return jsonify({
                "error": "No active advertisement found for the given ad_type and chat_option",
                "status": False
            }), 200

        # SECURITY: Generate signed URLs for files instead of exposing direct paths
        ad_image_signed = generate_signed_url_for_file(matched_ad.ad_image_path, expires_in=60)
        ad_pdf_signed = generate_signed_url_for_file(matched_ad.ad_pdf_path, expires_in=60)

        result = {
            "id": matched_ad.id,
            "poll": "show_poll",
            "ad_name": matched_ad.ad_name,
            "ad_image_path": ad_image_signed,
            "ad_pdf_path": ad_pdf_signed,
            "chatbot_options": matched_ad.chatbot_options,
            "ad_type": matched_ad.ad_type,
            "created_at": matched_ad.created_at.isoformat() if matched_ad.created_at else None,
            "updated_at": matched_ad.updated_at.isoformat() if matched_ad.updated_at else None
        }

        return jsonify({"data": result, "message": "Ad fetch success", "status": True}), 200

    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500

    finally:
        db.close()
    
# def chatbot_intro_ad():
#     db = SessionLocal()
#     try:
#         # Current UTC time
#         current_time = datetime.now()

#         # Fetch all ads of type 'on_chatbot_launch'
#         ads = (
#             db.query(Advertisement)
#             .filter(Advertisement.ad_type == "on_chatbot_launch")
#             .all()
#         )

#         if not ads:
#             return jsonify({
#                 "status": False,
#                 "message": "No advertisements found for ad_type 'on_chatbot_launch'"
#             }), 200

#         # Find ad where current time lies between start_time and end_time
#         active_ad = next(
#             (
#                 ad for ad in ads
#                 if ad.start_time and ad.end_time
#                 and ad.start_time <= current_time <= ad.end_time
#             ),
#             None
#         )

#         if not active_ad:
#             return jsonify({
#                 "status": False,
#                 "message": "No active advertisement found at the current time"
#             }), 200

#         # SECURITY: Generate signed URLs for files instead of exposing direct paths
#         ad_image_signed = generate_signed_url_for_file(active_ad.ad_image_path, expires_in=60)
#         ad_pdf_signed = generate_signed_url_for_file(active_ad.ad_pdf_path, expires_in=60)

#         # Prepare response
#         result = {
#             "id": active_ad.id,
#             "poll": "show_poll",
#             "ad_name": active_ad.ad_name,
#             "ad_image_path": ad_image_signed,
#             "ad_pdf_path": ad_pdf_signed,
#             "chatbot_options": active_ad.chatbot_options,
#             "ad_type": active_ad.ad_type,
#             "start_time": active_ad.start_time.isoformat() if active_ad.start_time else None,
#             "end_time": active_ad.end_time.isoformat() if active_ad.end_time else None,
#             "created_at": active_ad.created_at.isoformat() if active_ad.created_at else None,
#             "updated_at": active_ad.updated_at.isoformat() if active_ad.updated_at else None
#         }

#         return jsonify({
#             "status": True,
#             "message": "Active chatbot intro ad fetched successfully",
#             "data": result
#         }), 200

#     except Exception as e:
#         logging.error(f"Unexpected error in chatbot_intro_ad: {str(e)}", exc_info=True)
#         return jsonify({
#             "status": False,
#             "message": "Internal server error"
#         }), 500

#     finally:
#         db.close()


def chatbot_intro_ad():
    db = SessionLocal()
    try:
        # Current IST time
        current_time = current_time_ist()

        # Remove timezone info for comparison with database times
        if current_time.tzinfo:
            current_time = current_time.replace(tzinfo=None)

        # Fetch all ads of type 'on_chatbot_launch'
        ads = (
            db.query(Advertisement)
            .filter(Advertisement.ad_type == "on_chatbot_launch")
            .all()
        )

        if not ads:
            return jsonify({
                "status": False,
                "message": "No advertisements found for ad_type 'on_chatbot_launch'"
            }), 200

        # Find ad where current time lies between start_time and end_time
        active_ad = next(
            (
                ad for ad in ads
                if ad.start_time and ad.end_time
                and ad.start_time <= current_time <= ad.end_time
            ),
            None
        )

        if not active_ad:
            return jsonify({
                "status": False,
                "message": "No active advertisement found at the current time"
            }), 200

        # SECURITY: Generate signed URLs for files instead of exposing direct paths
        ad_image_signed = generate_signed_url_for_file(active_ad.ad_image_path, expires_in=60)
        ad_pdf_signed = generate_signed_url_for_file(active_ad.ad_pdf_path, expires_in=60)

        # Prepare response
        result = {
            "id": active_ad.id,
            "poll": "show_poll",
            "ad_name": active_ad.ad_name,
            "ad_image_path": ad_image_signed,
            "ad_pdf_path": ad_pdf_signed,
            "chatbot_options": active_ad.chatbot_options,
            "ad_type": active_ad.ad_type,
            "start_time": active_ad.start_time.isoformat() if active_ad.start_time else None,
            "end_time": active_ad.end_time.isoformat() if active_ad.end_time else None,
            "created_at": active_ad.created_at.isoformat() if active_ad.created_at else None,
            "updated_at": active_ad.updated_at.isoformat() if active_ad.updated_at else None
        }

        return jsonify({
            "status": True,
            "message": "Active chatbot intro ad fetched successfully",
            "data": result
        }), 200

    except Exception as e:
        logging.error(f"Unexpected error in chatbot_intro_ad: {str(e)}", exc_info=True)
        return jsonify({
            "status": False,
            "message": "Internal server error"
        }), 500

    finally:
        db.close()

def get_all_ads():
    try:
        db = SessionLocal()

        # Get pagination parameters from query string
        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=5, type=int)

        # Validate pagination parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 5

        # Get total count of ads
        total_ads = db.query(Advertisement).count()

        if total_ads == 0:
            return jsonify({
                "status": False,
                "message": "No advertisements found",
                "data": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "total_records": 0
                }
            }), 200

        # Calculate pagination
        total_pages = (total_ads + page_size - 1) // page_size
        offset = (page - 1) * page_size

        # Fetch paginated ads
        ads = db.query(Advertisement).offset(offset).limit(page_size).all()

        response = []
        for ad in ads:
            # Deserialize divisions_list if it's a string
            divisions_list = ad.divisions_list
            if isinstance(divisions_list, str):
                divisions_list = json.loads(divisions_list) if divisions_list else []
            else:
                divisions_list = divisions_list or []

            ad_image_signed = generate_signed_url_for_file(ad.ad_image_path, expires_in=60)
            ad_pdf_signed = generate_signed_url_for_file(ad.ad_pdf_path, expires_in=60)

            response.append({
                "id": ad.id,
                "ad_name": ad.ad_name,
                "ad_image_path": ad_image_signed,
                "ad_pdf_path": ad_pdf_signed,
                "chatbot_options": ad.chatbot_options or [],
                "ad_type": ad.ad_type or "",
                "divisions_list": divisions_list,
                "is_active": ad.is_active,
                "start_time": ad.start_time,
                "end_time": ad.end_time,
                "created_at": ad.created_at.isoformat() if ad.created_at else None,
                "updated_at": ad.updated_at.isoformat() if ad.updated_at else None
            })

        return jsonify({
            "status": True,
            "count": len(response),
            "data": response,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_records": total_ads
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


def get_unique_submenus():
    try:
        db = SessionLocal()

        # Fetch all submenus
        submenus = db.query(SubMenuOptionV).all()

        if not submenus:
            return jsonify({"message": "No submenus found"}), 404

        # Use a set to remove duplicates by submenu name + language
        unique_submenus = {}
        for submenu in submenus:
            key = (submenu.name.strip().lower(), submenu.lang.strip().lower() if submenu.lang else "")
            if key not in unique_submenus:
                unique_submenus[key] = {
                    "id": submenu.id,
                    "menu_id": submenu.menu_id,
                    "user_id": submenu.user_id,
                    "name": submenu.name,
                    "lang": submenu.lang,
                    "is_visible": submenu.is_visible,
                }

        # Convert unique submenu values to a list
        unique_list = list(unique_submenus.values())

        return jsonify({"data": unique_list, "message": "Sub-menus fetch success", "status": True, "count": len(unique_list)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
    


def get_unique_submenus():
    try:
        db = SessionLocal()

        # Fetch all submenus
        submenus = db.query(SubMenuOptionV).all()

        if not submenus:
            return jsonify({"message": "No submenus found"}), 404

        # Use a set to remove duplicates by submenu name + language
        unique_submenus = {}
        for submenu in submenus:
            key = (submenu.name.strip().lower(), submenu.lang.strip().lower() if submenu.lang else "")
            if key not in unique_submenus:
                unique_submenus[key] = {
                    "id": submenu.id,
                    "menu_id": submenu.menu_id,
                    "user_id": submenu.user_id,
                    "name": submenu.name,
                    "lang": submenu.lang,
                    "is_visible": submenu.is_visible,
                }

        # Convert unique submenu values to a list
        unique_list = list(unique_submenus.values())

        return jsonify({"data": unique_list, "message": "Sub-menus fetch success", "status": True, "count": len(unique_list)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()
    

def ad_on_menu_click():
    try:
        data = request.get_json()
        trigger_msg = data.get("lastSelectedOption", None)


        response_intent = requests.post(
                f"{RASA_API_URL}/model/parse",
                json={"text": f'{trigger_msg} BRPL'}
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


        ad_option = "show_on_menu_ad"
        ad_option_submenu_name = submenu_name,
        ad_option_type = "on_menu_ad"

        print(ad_option_submenu_name, "================= ad in submenu")

        # Prepare response

        response = {
            "ad_option" : ad_option,
            "ad_option_type": ad_option_type,
            "ad_option_submenu_name":submenu_name
        }


        return jsonify({"data":response, "message": "Successfull","status": True}), 200
    
    except Exception as e:
        return jsonify({"error": str(e), "status": False}), 500
    finally:
        db.close()
    


from sqlalchemy.orm.attributes import flag_modified

# def submit_ad_tracker():
#     db: Session = SessionLocal()
#     try:
#         sender_id = request.args.get("senderId")
#         ad_id = request.args.get("ad_id")

#         if not sender_id or not ad_id:
#             return jsonify({"error": "senderId and ad_id are required", "status": False}), 400

#         now = current_time_ist()
#         if now.tzinfo:
#             now = now.replace(tzinfo=None)

#         # ---- Fetch sender info ----
#         session_entry = db.query(Session).filter(Session.user_id == sender_id).first()
#         if not session_entry:
#             return jsonify({"error": "Sender not found", "status": False}), 404

#         user_id = session_entry.user_id
#         ca_number = session_entry.ca_number
#         division_name = session_entry.division_name
#         tel_no = session_entry.tel_no
#         user_type = session_entry.user_type

#         # ---- Fetch Ad ----
#         ad_entry = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
#         if not ad_entry:
#             return jsonify({"error": "Ad not found", "status": False}), 404

#         # ---- New tracker entry ----
#         new_entry = {
#             "timestamp": now.isoformat(),
#             "user_id": user_id,
#             "ca_number": ca_number,
#             "division_name": division_name,
#             "tel_no": tel_no,
#             "user_type": user_type
#         }

#         # ---- Append safely ----
#         current_trackers = ad_entry.ad_tracker or []
#         if not isinstance(current_trackers, list):
#             current_trackers = []

#         current_trackers.append(new_entry)
#         ad_entry.ad_tracker = current_trackers  # reassign to trigger update
#         flag_modified(ad_entry, "ad_tracker")    # explicitly mark as modified

#         db.commit()

#         return jsonify({
#             "message": "Ad tracker updated successfully",
#             "status": True,
#             "data": {
#                 "ad_id": ad_id,
#                 "tracker_entry": new_entry
#             }
#         }), 200

#     except Exception as e:
#         db.rollback()
#         return jsonify({"error": str(e), "status": False}), 500

#     finally:
#         db.close()


def submit_ad_tracker():
    db: Session = SessionLocal()
    try:
        sender_id = request.args.get("senderId")
        ad_id = request.args.get("ad_id")

        if not sender_id or not ad_id:
            return jsonify({"error": "senderId and ad_id are required", "status": False}), 400

        now = current_time_ist()
        if now.tzinfo:
            now = now.replace(tzinfo=None)

        # ---- Fetch sender info ----
        session_entry = db.query(Session).filter(Session.user_id == sender_id).first()
        # if not session_entry:
        #     return jsonify({"error": "Sender not found", "status": False}), 404

        # Use safe defaults if session_entry not found
        user_id = session_entry.user_id if session_entry else sender_id
        ca_number = getattr(session_entry, "ca_number", None)
        division_name = getattr(session_entry, "division_name", None)
        tel_no = getattr(session_entry, "tel_no", None)
        user_type = getattr(session_entry, "user_type", None)

        # ---- Fetch Ad ----
        ad_entry = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
        if not ad_entry:
            return jsonify({"error": "Ad not found", "status": False}), 404

        # ---- New tracker entry ----
        new_entry = {
            "timestamp": now.isoformat(),
            "user_id": user_id,
            "ca_number": ca_number,
            "division_name": division_name,
            "tel_no": tel_no,
            "user_type": user_type,
            "session_found": bool(session_entry)
        }

        # ---- Append safely ----
        current_trackers = ad_entry.ad_tracker or []
        if not isinstance(current_trackers, list):
            current_trackers = []

        current_trackers.append(new_entry)
        ad_entry.ad_tracker = current_trackers
        flag_modified(ad_entry, "ad_tracker")

        db.commit()

        return jsonify({
            "message": "Ad tracker updated successfully",
            "status": True,
            "data": {
                "ad_id": ad_id,
                "tracker_entry": new_entry
            }
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e), "status": False}), 500

    finally:
        db.close()


def get_ad_analytics():
    db: Session = SessionLocal()
    try:
        # ---- Step 1: Parse query parameters ----
        ad_id = request.args.get("ad_id")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        page = request.args.get("page", default=1, type=int)

        if not ad_id or not start_date or not end_date:
            return jsonify({
                "error": "ad_id, start_date, and end_date are required (format: YYYY-MM-DD)",
                "status": False
            }), 400

        # ---- Step 2: Convert to datetime and include full end day ----
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD", "status": False}), 400

        # ---- Step 3: Fetch Advertisement ----
        ad_entry = db.query(Advertisement).filter(Advertisement.id == ad_id).first()
        if not ad_entry:
            return jsonify({"error": "Ad not found", "status": False}), 404

        trackers = ad_entry.ad_tracker or []
        if not isinstance(trackers, list):
            return jsonify({"error": "Invalid ad_tracker format", "status": False}), 500

        # ---- Step 4: Filter trackers by date range ----
        filtered_trackers = []
        for entry in trackers:
            ts = entry.get("timestamp")
            if not ts:
                continue
            try:
                t = datetime.fromisoformat(ts)
                if start_dt <= t < end_dt:
                    filtered_trackers.append(entry)
            except Exception:
                continue

        # ---- Step 5: Compute analytics ----
        total_views = len(filtered_trackers)
        division_counts, user_counts, ca_numbers = {}, {}, set()
        new_users = 0
        registered_users = 0

        for t in filtered_trackers:
            # Division counts (skip None/empty)
            div = t.get("division_name")
            if div and div.strip():
                division_counts[div] = division_counts.get(div, 0) + 1

            # Unique users
            user = t.get("user_id")
            if user:
                user_counts[user] = user_counts.get(user, 0) + 1

            # CA numbers
            ca = t.get("ca_number")
            if ca:
                ca_numbers.add(ca)

            # User type classification
            user_type = (t.get("user_type") or "").lower().strip()
            if user_type == "new":
                new_users += 1
            elif user_type == "registered":
                registered_users += 1

        # ---- Step 6: Generate insights ----
        top_division = max(division_counts, key=division_counts.get, default=None)
        top_user = max(user_counts, key=user_counts.get, default=None)

        insights = {
            "total_count": total_views,
            "unique_users": len(user_counts),
            "unique_ca_numbers": len(ca_numbers),
            "divisions_involved": len(division_counts),
            "top_division": top_division,
            "top_user": top_user,
            "new_users": new_users,
            "registered_users": registered_users
        }

        # ---- Step 7: Apply pagination ----
        page_size = 5
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_logs = filtered_trackers[start_index:end_index]

        total_pages = (len(filtered_trackers) + page_size - 1) // page_size  # ceiling division

        return jsonify({
            "message": "Ad analytics fetched successfully",
            "status": True,
            "data": {
                "ad_id": ad_id,
                "ad_type": ad_entry.ad_type,
                "date_range": {"start": start_date, "end": end_date},
                "insights": insights,
                "division_breakdown": division_counts,
                "division_list": ad_entry.divisions_list,  # <-- Added line
                "division_count": len(ad_entry.divisions_list),
                "pagination": {
                    "page": page,
                    "per_page": page_size,
                    "total_pages": total_pages,
                    "total_records": len(filtered_trackers)
                },
                "tracker_logs": paginated_logs
            }
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e), "status": False}), 500

    finally:
        db.close()