from datetime import datetime, timedelta, timezone
from flask import jsonify, request
from Models.api_key_master_model import API_Key_Master
from utils.input_validator import InputValidator
from database import SessionLocal
import pytz

IST = pytz.timezone("Asia/Kolkata")

def get_ist_time():
    return datetime.now(IST)

from database import SessionLocal

def sanitize_for_csv(value):
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def create_api_key():
    try:
        data = request.get_json()

        # Expecting JSON body like:
        # {
        #   "menu_option": "SMS_API",
        #   "api_url": "http://tempuri.org/SEND_BSES_SMS_API",
        #   "api_headers": {
        #       "Content-Type": "text/xml; charset=utf-8",
        #       "SOAPAction": "\"http://tempuri.org/SEND_BSES_SMS_API\""
        #   }
        # }

        record = API_Key_Master(
            menu_option=data.get("menu_option"),
            api_url=data.get("api_url"),
            api_name=data.get("api_name"),
            api_headers=data.get("api_headers")  # dict goes directly into JSON column
        )

        record_id = record.save()

        return jsonify({"status": True, "id": record_id}), 201

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500
    

def update_api_key_by_name():
    try:
        data = request.get_json()
        api_name = data.get("api_name")

        if not api_name:
            return jsonify({"status": False, "message": "api_name is required"}), 400

        db = SessionLocal()
        records = db.query(API_Key_Master).filter_by(api_name=api_name).all()

        if not records:
            return jsonify({"status": False, "message": "No records found"}), 404

        # Update all matching records
        for record in records:
            if "api_url" in data:

                is_valid, msg = InputValidator.validate_no_csv_injection(data["api_url"], "api_url")
                if not is_valid:
                    return jsonify({"status": False, "message": msg}), 400

                is_valid, msg = InputValidator.validate_fallback(data["api_url"], "api_url")
                if not is_valid:
                    return jsonify({"status": False, "message": msg}), 400
                
                api_url = sanitize_for_csv(data["api_url"])
                
                record.api_url = api_url

            if "api_headers" in data:

                is_valid, msg = InputValidator.validate_no_csv_injection(data["api_url"], "api_url")
                if not is_valid:
                    return jsonify({"status": False, "message": msg}), 400

                is_valid, msg = InputValidator.validate_fallback(data["api_headers"], "api_headers")
                if not is_valid:
                    return jsonify({"status": False, "message": msg}), 400
                
                api_headers = sanitize_for_csv(data["api_headers"])
                
                record.api_headers = api_headers

        db.commit()

        return jsonify({
            "status": True,
            "message": f"{len(records)} record(s) updated successfully",
            "updated_records": [
                {
                    "id": r.id,
                    "api_url": r.api_url,
                    "api_headers": r.api_headers
                }
                for r in records
            ]
        }), 200

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500
    finally:
        db.close()
    

def get_all_api_details():
    try:
        db = SessionLocal()
        records = db.query(API_Key_Master).all()

        if not records:
            return jsonify({"status": False, "message": "No records found"}), 404

        return jsonify({
            "status": True,
            "total_records": len(records),
            "data": [
                {
                    "id": r.id,
                    "menu_option": r.menu_option,
                    "api_name": r.api_name,
                    "api_url": r.api_url,
                    "api_headers": r.api_headers,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None
                }
                for r in records
            ]
        }), 200

    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500
    finally:
        db.close()
     

# def save_api_key_count(menu_option, api_name, payload, response):
#     """
#     Save or update a chat entry in the Session collection.

#     Args:
#         api_name (str): Name of the API or chatbot instance.
#         sender_id (str): Unique identifier for the user.
#         user_message (str): User's input message.
#         response (str): Chatbot's response.
#         get_ist_time (function): Function that returns current IST time.
#     """
#     existing_chat = SessionLocal().query(API_Key_Master).filter_by(
#         menu_option=menu_option,
#         api_name=api_name
#     ).first()

#     chat_entry = {
#         "user_request": payload,
#         "api_response": response,
#         "api_name": api_name,
#         "timestamp": get_ist_time().isoformat()
#     }

#     if existing_chat:
#         API_Key_Master.update_one(
#             {"menu_option": menu_option, "api_name": api_name},
#             {
#                 "$push": {"api_hit": chat_entry},
#                 "$set": {
#                     "updated_at": get_ist_time().isoformat()
#                 }
#             }
#         )
#     else:
#         chat_output = API_Key_Master(
#             menu_option=menu_option,
#             api_name=api_name,
#             api_hit=[chat_entry],
#         )
#         chat_output.save()


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


def api_hit_breakdown():
    try:
        db = SessionLocal()

        # Fetch query parameters
        date_str = request.args.get("date")  # YYYY-MM-DD
        start_date_str = request.args.get("start_date")  # YYYY-MM-DD
        end_date_str = request.args.get("end_date")      # YYYY-MM-DD
        month_str = request.args.get("month")  # YYYY-MM
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")  # if you have this field in table

        # Time calculations
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # Parse filters
        date_filter = None
        start_date = None
        end_date = None
        month_start = None
        month_end = None

        if date_str:
            date_filter = datetime.strptime(date_str, "%Y-%m-%d").date()
        elif start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        elif month_str:
            month_filter = datetime.strptime(month_str, "%Y-%m").date()
            month_start = month_filter.replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

        # Fetch data from DB
        records = db.query(API_Key_Master).all()

        breakdown = {}

        for record in records:
            # Optional division filter
            if division_name and getattr(record, "division_name", None) != division_name:
                continue

            api_hits = record.api_hit or []
            for hit in api_hits:
                api_name = hit.get("api_name")
                timestamp_str = hit.get("timestamp")

                if not api_name or not timestamp_str:
                    continue

                try:
                    ts = datetime.fromisoformat(timestamp_str).astimezone(timezone.utc)
                except Exception:
                    continue

                ts_date = ts.date()

                # Apply filters
                if last_hour and ts < one_hour_ago:
                    continue
                elif date_filter and ts_date != date_filter:
                    continue
                elif start_date and end_date and not (start_date <= ts_date <= end_date):
                    continue
                elif month_str and not (month_start <= ts_date <= month_end):
                    continue

                if api_name not in breakdown:
                    breakdown[api_name] = {"count": 0, "timestamps": []}

                breakdown[api_name]["count"] += 1
                breakdown[api_name]["timestamps"].append(timestamp_str)

        # Format output
        formatted_data = [
            {"api_name": api_name, "count": details["count"], "timestamps": details["timestamps"]}
            for api_name, details in breakdown.items()
        ]

        return jsonify({
            "total_records": sum(d["count"] for d in formatted_data),
            "data": formatted_data
        })

    except Exception as e:
        print("Error in api_hit_breakdown:", e)
        return jsonify({"error": "Something went wrong"}), 500

    finally:
        db.close()



# def get_api_details_with_breakdown():
#     try:
#         db = SessionLocal()

#         # Fetch query parameters
#         date_str = request.args.get("date")  # YYYY-MM-DD
#         start_date_str = request.args.get("start_date")  # YYYY-MM-DD
#         end_date_str = request.args.get("end_date")      # YYYY-MM-DD
#         month_str = request.args.get("month")  # YYYY-MM
#         last_hour = request.args.get("last_hour", "false").lower() == "true"
#         division_name = request.args.get("division_name")  # optional filter

#         # Time calculations
#         now = datetime.now(timezone.utc)
#         one_hour_ago = now - timedelta(hours=1)

#         # Parse filters
#         date_filter = None
#         start_date = None
#         end_date = None
#         month_start = None
#         month_end = None

#         if date_str:
#             date_filter = datetime.strptime(date_str, "%Y-%m-%d").date()
#         elif start_date_str and end_date_str:
#             start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
#             end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
#         elif month_str:
#             month_filter = datetime.strptime(month_str, "%Y-%m").date()
#             month_start = month_filter.replace(day=1)
#             if month_start.month == 12:
#                 month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
#             else:
#                 month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

#         # Fetch all records
#         records = db.query(API_Key_Master).all()

#         if not records:
#             return jsonify({"status": False, "message": "No records found"}), 404

#         breakdown = {}

#         result_data = []
#         for r in records:
#             # Optional division filter
#             if division_name and getattr(r, "division_name", None) != division_name:
#                 continue

#             # --- API HIT BREAKDOWN ---
#             api_hits = r.api_hit or []
#             filtered_hits = []

#             for hit in api_hits:
#                 api_name = hit.get("api_name")
#                 timestamp_str = hit.get("timestamp")

#                 if not api_name or not timestamp_str:
#                     continue

#                 try:
#                     ts = datetime.fromisoformat(timestamp_str).astimezone(timezone.utc)
#                 except Exception:
#                     continue

#                 ts_date = ts.date()

#                 # Apply filters
#                 if last_hour and ts < one_hour_ago:
#                     continue
#                 elif date_filter and ts_date != date_filter:
#                     continue
#                 elif start_date and end_date and not (start_date <= ts_date <= end_date):
#                     continue
#                 elif month_str and not (month_start <= ts_date <= month_end):
#                     continue

#                 filtered_hits.append(timestamp_str)

#                 if api_name not in breakdown:
#                     breakdown[api_name] = {"count": 0, "timestamps": []}

#                 breakdown[api_name]["count"] += 1
#                 breakdown[api_name]["timestamps"].append(timestamp_str)

#             # Append record with breakdown info
#             result_data.append({
#                 "id": r.id,
#                 "menu_option": r.menu_option,
#                 "api_name": r.api_name,
#                 "api_url": r.api_url,
#                 "api_headers": r.api_headers,
#                 "created_at": r.created_at.isoformat() if r.created_at else None,
#                 "updated_at": r.updated_at.isoformat() if r.updated_at else None,
#                 "hit_count": len(filtered_hits),
#                 "hit_timestamps": filtered_hits
#             })

#         # Format global breakdown summary
#         formatted_breakdown = [
#             {"api_name": api_name, "count": details["count"], "timestamps": details["timestamps"]}
#             for api_name, details in breakdown.items()
#         ]

#         return jsonify({
#             "status": True,
#             "total_records": len(result_data),
#             "total_hits": sum(d["count"] for d in formatted_breakdown),
#             "data": result_data,
#             "breakdown": formatted_breakdown
#         }), 200

#     except Exception as e:
#         print("Error in get_api_details_with_breakdown:", e)
#         return jsonify({"status": False, "error": "Something went wrong"}), 500

#     finally:
#         db.close()


def get_api_details_with_breakdown():
    try:
        db = SessionLocal()

        # --- Fetch query parameters ---
        date_str = request.args.get("date")  # YYYY-MM-DD
        start_date_str = request.args.get("start_date")  # YYYY-MM-DD
        end_date_str = request.args.get("end_date")      # YYYY-MM-DD
        month_str = request.args.get("month")  # YYYY-MM
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")  # optional filter

        # --- Time calculations ---
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # --- Parse filters ---
        date_filter = None
        start_date = None
        end_date = None
        month_start = None
        month_end = None

        if date_str:
            date_filter = datetime.strptime(date_str, "%Y-%m-%d").date()
        elif start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        elif month_str:
            month_filter = datetime.strptime(month_str, "%Y-%m").date()
            month_start = month_filter.replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

        # --- Fetch all records ---
        records = db.query(API_Key_Master).all()
        if not records:
            return jsonify({"status": False, "message": "No records found"}), 404

        breakdown = {}
        result_data = []

        for r in records:
            # Optional division filter
            if division_name and getattr(r, "division_name", None) != division_name:
                continue

            api_hits = r.api_hit or []
            filtered_hits = []

            for hit in api_hits:
                api_name = hit.get("api_name")
                timestamp_str = hit.get("timestamp")
                user_request = hit.get("user_request")
                api_response = hit.get("api_response")

                if not api_name or not timestamp_str:
                    continue

                try:
                    ts = datetime.fromisoformat(timestamp_str).astimezone(timezone.utc)
                except Exception:
                    continue

                ts_date = ts.date()

                # --- Apply filters ---
                if last_hour and ts < one_hour_ago:
                    continue
                elif date_filter and ts_date != date_filter:
                    continue
                elif start_date and end_date and not (start_date <= ts_date <= end_date):
                    continue
                elif month_str and not (month_start <= ts_date <= month_end):
                    continue

                # Append filtered hit (with details)
                hit_details = {
                    "timestamp": timestamp_str,
                    "user_request": user_request,
                    "api_response": api_response
                }
                filtered_hits.append(hit_details)

                # --- Global breakdown aggregation ---
                if api_name not in breakdown:
                    breakdown[api_name] = {"count": 0, "hits": []}

                breakdown[api_name]["count"] += 1
                breakdown[api_name]["hits"].append(hit_details)

            # --- Add record-level info ---
            result_data.append({
                "id": r.id,
                "menu_option": r.menu_option,
                "api_name": r.api_name,
                "api_url": r.api_url,
                "api_headers": r.api_headers,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "hit_count": len(filtered_hits),
                "hits": filtered_hits
            })

        # --- Format breakdown summary ---
        formatted_breakdown = [
            {
                "api_name": api_name,
                "count": details["count"],
                "hits": details["hits"]
            }
            for api_name, details in breakdown.items()
        ]

        # --- Final Response ---
        return jsonify({
            "status": True,
            "total_records": len(result_data),
            "total_hits": sum(d["count"] for d in formatted_breakdown),
            "data": result_data,
            "breakdown": formatted_breakdown
        }), 200

    except Exception as e:
        print("Error in get_api_details_with_breakdown:", e)
        return jsonify({"status": False, "error": "Something went wrong"}), 500

    finally:
        db.close()
