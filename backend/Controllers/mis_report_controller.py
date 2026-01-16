from flask import json, request, jsonify
from collections import defaultdict
from dateutil import parser
from datetime import datetime, timedelta
import requests
from flask import request, jsonify
from datetime import datetime, timedelta, date
from pytz import timezone
from collections import defaultdict
from sqlalchemy import func
from dateutil.parser import isoparse
import json, calendar, traceback
from Models.session_model import Session
from database import SessionLocal
from pytz import timezone
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

flask_url = os.getenv('BACKEND_URL')

## Peak Hours
def mis_peak_hours():
    try:
        db = SessionLocal()

        # --- Query params ---
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        # --- IST timezone ---
        ist = timezone('Asia/Kolkata')

        # --- Fetch submenu data dynamically ---
        submenu_url = f"{flask_url}/submenus"
        submenu_response = requests.get(submenu_url, timeout=10)
        submenu_data = submenu_response.json().get("data", [])

        # --- Build valid_service_options dynamically ---
        # Group by menu_id to link English/Hindi variants
        grouped_submenus = defaultdict(lambda: {"en": [], "hi": []})
        for item in submenu_data:
            name = item.get("name")
            lang = item.get("lang")
            menu_id = item.get("menu_id")
            if not name or not menu_id:
                continue
            # ✅ Append " BRPL" to every submenu name
            name_with_brpl = f"{name.strip()} BRPL"
            grouped_submenus[menu_id][lang].append(name_with_brpl)

        # Combine into a single flat set of valid options
        valid_service_options = set()
        for _, group in grouped_submenus.items():
            valid_service_options.update(group["en"])
            valid_service_options.update(group["hi"])

        # --- Date range logic ---
        if date_str:
            start_time = ist.localize(datetime.strptime(date_str, "%Y-%m-%d"))
            end_time = start_time + timedelta(days=1)
        elif start_date_str and end_date_str:
            start_time = ist.localize(datetime.strptime(start_date_str, "%Y-%m-%d"))
            end_time = ist.localize(datetime.strptime(end_date_str, "%Y-%m-%d")) + timedelta(days=1)
        else:
            now = datetime.now(ist)
            start_time = now - timedelta(hours=24)
            end_time = now

        # --- Query sessions ---
        query = db.query(Session)
        if division_name:
            query = query.filter(Session.division_name == division_name)
        if ca_number:
            query = query.filter(Session.ca_number == ca_number)
        if tel_no:
            query = query.filter(Session.tel_no == tel_no)
        if source:
            query = query.filter(Session.source == source)

        all_sessions = query.all()

        # --- 2-hour bucket aggregation ---
        bucket_data = defaultdict(lambda: {
            "total_interactions": 0,
            "unique_users": set(),
            "services_called": defaultdict(int)
        })

        for session in all_sessions:
            if not session.chat:
                continue

            for entry in session.chat:
                ts_str = entry.get("timestamp")
                if not ts_str:
                    continue

                try:
                    ts = parser.isoparse(ts_str)
                    if ts.tzinfo is None:
                        ts = ist.localize(ts)
                    else:
                        ts = ts.astimezone(ist)
                except Exception:
                    continue

                if not (start_time <= ts < end_time):
                    continue

                hour = ts.hour
                bucket = (hour // 2) * 2  # Group by 2-hour block

                query_text = entry.get("query", "").strip()
                user_id = session.user_id

                bucket_data[bucket]["total_interactions"] += 1
                bucket_data[bucket]["unique_users"].add(user_id)

                # ✅ Count valid chatbot service calls (English + Hindi, both with BRPL suffix)
                if query_text in valid_service_options:
                    bucket_data[bucket]["services_called"][query_text] += 1

        # --- Build 2-hourly report ---
        report = []
        for bucket in range(0, 24, 2):
            start_label = f"{bucket:02d}:00"
            end_label = f"{(bucket + 2) % 24:02d}:00"
            bucket_label = f"{start_label} - {end_label}"

            data = bucket_data.get(bucket)
            if data:
                report.append({
                    "hour_range": bucket_label,
                    "total_interactions": data["total_interactions"],
                    "unique_users": len(data["unique_users"]),
                    "services_called": dict(data["services_called"])
                })
            else:
                report.append({
                    "hour_range": bucket_label,
                    "total_interactions": 0,
                    "unique_users": 0,
                    "services_called": {}
                })

        # --- Peak 2-hour block ---
        peak_bucket_num = max(bucket_data, key=lambda h: bucket_data[h]["total_interactions"], default=None)
        if peak_bucket_num is not None:
            peak_data = bucket_data[peak_bucket_num]
            peak_start_label = f"{peak_bucket_num:02d}:00"
            peak_end_label = f"{(peak_bucket_num + 2) % 24:02d}:00"
            peak_hour = {
                "hour_range": f"{peak_start_label} - {peak_end_label}",
                "total_interactions": peak_data["total_interactions"],
                "unique_users": len(peak_data["unique_users"]),
                "services_called": dict(peak_data["services_called"])
            }
        else:
            peak_hour = {
                "hour_range": None,
                "total_interactions": 0,
                "unique_users": 0,
                "services_called": {}
            }

        response = {
            "filters": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "division_name": division_name if division_name else "all",
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source
            },
            "peak_hour": peak_hour,
            "hourly_report": report
        }

        return jsonify(response)

    except Exception as e:
        print("MIS Peak Hours Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500

    finally:
        db.close()


## Average Duration
def mis_avg_interaction_duration():
    db = None
    try:
        db = SessionLocal()

        # --- Query Params ---
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        # --- Hourly range filter ---
        hourly_range = request.args.get("hourly_range")
        start_hour = request.args.get("start_hour")
        end_hour = request.args.get("end_hour")

        # --- Time setup ---
        ist = timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

        # --- Parse hourly range ---
        filter_start_hour = None
        filter_end_hour = None

        if hourly_range:
            try:
                start_time_str, end_time_str = hourly_range.split('-')
                filter_start_hour = int(start_time_str.split(':')[0])
                filter_end_hour = int(end_time_str.split(':')[0])
            except Exception:
                return jsonify({"error": "Invalid hourly_range format. Use HH:MM-HH:MM (e.g., 09:00-17:00)"}), 400
        elif start_hour is not None and end_hour is not None:
            try:
                filter_start_hour = int(start_hour)
                filter_end_hour = int(end_hour)
            except ValueError:
                return jsonify({"error": "Invalid start_hour or end_hour. Must be integers (0-23)"}), 400

        # Validate hour range
        if filter_start_hour is not None and filter_end_hour is not None:
            if not (0 <= filter_start_hour <= 23 and 0 <= filter_end_hour <= 23):
                return jsonify({"error": "Hours must be between 0 and 23"}), 400
            if filter_start_hour > filter_end_hour:
                return jsonify({"error": "start_hour must be less than or equal to end_hour"}), 400

        # --- Date filters ---
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
            year, month = month_filter.year, month_filter.month
            last_day = calendar.monthrange(year, month)[1]
            month_start = date(year, month, 1)
            month_end = date(year, month, last_day)

        # --- Build query ---
        query = db.query(Session)
        if division_name:
            query = query.filter(Session.division_name == division_name)
        if ca_number:
            query = query.filter(Session.ca_number == ca_number)
        if tel_no:
            query = query.filter(Session.tel_no == tel_no)
        if source:
            query = query.filter(func.lower(Session.source) == source.lower())

        sessions = query.all()
        print(f"Fetched sessions: {len(sessions)}")

        # --- Daily aggregation ---
        daily_data = defaultdict(lambda: {"total_duration": 0, "sessions": 0})

        for session in sessions:
            chat_data = session.chat
            if not chat_data:
                continue
            if isinstance(chat_data, str):
                try:
                    chat_data = json.loads(chat_data)
                except Exception:
                    continue

            if not isinstance(chat_data, list) or len(chat_data) < 1:
                continue

            timestamps = []
            for chat in chat_data:
                if isinstance(chat, dict) and "timestamp" in chat:
                    try:
                        ts = isoparse(chat["timestamp"])
                        if ts.tzinfo is None:
                            ts = ist.localize(ts)
                        else:
                            ts = ts.astimezone(ist)
                        timestamps.append(ts)
                    except Exception:
                        continue

            if not timestamps:
                continue

            start = min(timestamps)
            end = max(timestamps)
            duration = (end - start).total_seconds()
            session_date = start.date()

            # --- Apply date filters ---
            if last_hour:
                if not (one_hour_ago <= start <= now or one_hour_ago <= end <= now):
                    continue
            elif date_filter:
                if session_date != date_filter:
                    continue
            elif start_date and end_date:
                if not (start_date <= session_date <= end_date):
                    continue
            elif month_start and month_end:
                if not (month_start <= session_date <= month_end):
                    continue

            # --- Apply hourly range filter ---
            if filter_start_hour is not None and filter_end_hour is not None:
                session_in_range = False
                for ts in timestamps:
                    hour = ts.hour
                    if filter_start_hour <= hour < filter_end_hour:
                        session_in_range = True
                        break
                if not session_in_range:
                    continue

            daily_data[session_date]["total_duration"] += duration
            daily_data[session_date]["sessions"] += 1

        # --- Helper: format duration ---
        def format_duration(seconds):
            minutes = int(seconds // 60)
            sec = int(seconds % 60)
            return f"{minutes} minutes {sec} seconds" if minutes else f"{sec} seconds"

        # --- Build response ---
        report = []
        for day, data in sorted(daily_data.items()):
            if data["sessions"] > 0:
                avg_duration = data["total_duration"] / data["sessions"]
                formatted_duration = format_duration(avg_duration)
            else:
                avg_duration = 0
                formatted_duration = "0 seconds"

            report.append({
                "date": str(day),
                "total_sessions": data["sessions"],
                "total_duration_seconds": data["total_duration"],
                "average_duration_seconds": avg_duration,
                "average_duration": formatted_duration
            })

        # --- Build hourly range display string ---
        hourly_range_display = None
        if filter_start_hour is not None and filter_end_hour is not None:
            hourly_range_display = f"{filter_start_hour:02d}:00-{filter_end_hour:02d}:00"

        response = {
            "filters": {
                "date": date_str,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "month": month_str,
                "last_hour": last_hour,
                "hourly_range": hourly_range_display,
                "division_name": division_name or "all",
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source
            },
            "daily_avg_interaction_duration": report if report else "No sessions found for given filters."
        }

        return jsonify(response)

    except Exception as e:
        print("MIS Avg Interaction Duration Error:", e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
    finally:
        if db:
            db.close()


## Chat Left and Completed
def mis_chat_completion_status():
    try:
        db = SessionLocal()

        # --- Optional filters ---
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        # --- Hourly range filter ---
        hourly_range = request.args.get("hourly_range")
        start_hour = request.args.get("start_hour")
        end_hour = request.args.get("end_hour")

        ist = timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

        # --- Parse hourly range ---
        filter_start_hour = None
        filter_end_hour = None

        if hourly_range:
            try:
                start_time_str, end_time_str = hourly_range.split('-')
                filter_start_hour = int(start_time_str.split(':')[0])
                filter_end_hour = int(end_time_str.split(':')[0])
            except Exception:
                return jsonify({"error": "Invalid hourly_range format. Use HH:MM-HH:MM (e.g., 09:00-17:00)"}), 400
        elif start_hour is not None and end_hour is not None:
            try:
                filter_start_hour = int(start_hour)
                filter_end_hour = int(end_hour)
            except ValueError:
                return jsonify({"error": "Invalid start_hour or end_hour. Must be integers (0-23)"}), 400

        # Validate hour range
        if filter_start_hour is not None and filter_end_hour is not None:
            if not (0 <= filter_start_hour <= 23 and 0 <= filter_end_hour <= 23):
                return jsonify({"error": "Hours must be between 0 and 23"}), 400
            if filter_start_hour > filter_end_hour:
                return jsonify({"error": "start_hour must be less than or equal to end_hour"}), 400

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

        # thank_you_messages = [
        #     "Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)",
        #     "धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)"
        # ]

        thank_you_messages = [
            "Thank you. Would you like to return to the main menu? Select Yes or type ‘menu’ or ‘hi’ to continue.",
            "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए ‘हाँ’, ‘menu’ या ‘hi’ टाइप करें।"
        ]

        # --- Fetch sessions with optional filters ---
        query = db.query(Session)
        if division_name:
            query = query.filter(Session.division_name == division_name)
        if ca_number:
            query = query.filter(Session.ca_number == ca_number)
        if tel_no:
            query = query.filter(Session.tel_no == tel_no)
        if source:
            query = query.filter(Session.source == source)

        sessions = query.all()

        # --- Data containers ---
        daily_data = defaultdict(lambda: {
            "completed": 0,
            "left": 0,
            "new_user_sessions": 0,
            "registered_user_sessions": 0,
            "english_sessions": 0,
            "hindi_sessions": 0
        })
        combined_data = {
            "completed": 0,
            "left": 0,
            "new_user_sessions": 0,
            "registered_user_sessions": 0,
            "english_sessions": 0,
            "hindi_sessions": 0
        }

        for s in sessions:
            if not s.created_at:
                continue
            if s.created_at.tzinfo is None:
                session_created_at = ist.localize(s.created_at) 
            else:
                session_created_at = s.created_at.astimezone(ist)
            session_date = session_created_at.date()

            if last_hour:
                if not (one_hour_ago <= session_created_at <= now):
                    continue
            elif date_filter:
                if session_date != date_filter:
                    continue
            elif start_date and end_date:
                if not (start_date <= session_date <= end_date):
                    continue
            elif month_str:
                if not (month_start <= session_date <= month_end):
                    continue

            if not s.chat:
                continue

            # --- Apply hourly range filter ---
            if filter_start_hour is not None and filter_end_hour is not None:
                # Extract timestamps from chat to check hourly range
                session_in_range = False
                if isinstance(s.chat, list):
                    for chat in s.chat:
                        ts_str = chat.get("timestamp")
                        if ts_str:
                            try:
                                ts = datetime.fromisoformat(ts_str)
                                if ts.tzinfo is None:
                                    ts = ist.localize(ts)
                                else:
                                    ts = ts.astimezone(ist)
                                hour = ts.hour
                                if filter_start_hour <= hour < filter_end_hour:
                                    session_in_range = True
                                    break
                            except Exception:
                                continue
                if not session_in_range:
                    continue

            # --- Identify user type ---
            user_type = getattr(s, "user_type", None)
            if not user_type and isinstance(s.chat, list) and len(s.chat) > 0:
                first_message = s.chat[0].get("query", "").lower()
                if "new consumer" in first_message or "नया उपभोक्ता" in first_message:
                    user_type = "new"
                elif "registered" in first_message or "पंजीकृत" in first_message:
                    user_type = "registered"

            target = daily_data[session_date] if (date_filter or last_hour) else combined_data

            if user_type == "new":
                target["new_user_sessions"] += 1
            elif user_type == "registered":
                target["registered_user_sessions"] += 1

            # --- Detect language selection ---
            language_selected = None
            for chat in s.chat:
                answer = chat.get("answer", {}).get("response", {})
                heading = answer.get("heading", [])
                if isinstance(heading, list) and any(
                    "Please select your language" in h or "कृपया अपनी भाषा चुनें" in h for h in heading
                ):
                    buttons = answer.get("buttons", [])
                    if any("English" in b for b in buttons):
                        idx = s.chat.index(chat) + 1
                        if idx < len(s.chat):
                            next_query = s.chat[idx].get("query", "").lower()
                            if "english" in next_query:
                                language_selected = "english"
                            elif "हिंदी" in next_query:
                                language_selected = "hindi"
                    break

            if language_selected == "english":
                target["english_sessions"] += 1
            elif language_selected == "hindi":
                target["hindi_sessions"] += 1

            # --- Determine completion status ---
            try:
                last_message = s.chat[-1]
                main_menu_heading = (
                    last_message
                    .get("answer", {})
                    .get("response", {})
                    .get("main_menu_heading")
                )
                if main_menu_heading and main_menu_heading.strip() in thank_you_messages:
                    target["completed"] += 1
                else:
                    target["left"] += 1
            except Exception:
                target["left"] += 1

        # --- Build report ---
        if date_filter or last_hour:
            report = []
            for day, stats in sorted(daily_data.items()):
                report.append({
                    "date": str(day),
                    "completed_chats": stats["completed"],
                    "left_chats": stats["left"],
                    "new_user_sessions": stats["new_user_sessions"],
                    "registered_user_sessions": stats["registered_user_sessions"],
                    "english_sessions": stats["english_sessions"],
                    "hindi_sessions": stats["hindi_sessions"],
                    "total_sessions": stats["completed"] + stats["left"]
                })
        else:
            report = [dict(
                completed_chats=combined_data["completed"],
                left_chats=combined_data["left"],
                new_user_sessions=combined_data["new_user_sessions"],
                registered_user_sessions=combined_data["registered_user_sessions"],
                english_sessions=combined_data["english_sessions"],
                hindi_sessions=combined_data["hindi_sessions"],
                total_sessions=combined_data["completed"] + combined_data["left"]
            )]

        # --- Build hourly range display string ---
        hourly_range_display = None
        if filter_start_hour is not None and filter_end_hour is not None:
            hourly_range_display = f"{filter_start_hour:02d}:00-{filter_end_hour:02d}:00"

        response = {
            "filters": {
                "date": date_str,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "month": month_str,
                "last_hour": last_hour,
                "hourly_range": hourly_range_display,
                "division_name": division_name if division_name else "all",
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source
            },
            "stats": report
        }

        return jsonify(response)

    except Exception as e:
        print("MIS Chat Completion Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500
    finally:
        db.close()

## Till working


## Pay Bill

def mis_pay_bill():
    try:
        db = SessionLocal()

        # --- Optional filters ---
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")  # YYYY-MM
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        # --- Hourly range filter ---
        hourly_range = request.args.get("hourly_range")
        start_hour = request.args.get("start_hour")
        end_hour = request.args.get("end_hour")

        # --- IST timezone ---
        ist = timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

        # --- Parse hourly range ---
        filter_start_hour = None
        filter_end_hour = None

        if hourly_range:
            try:
                start_time_str, end_time_str = hourly_range.split('-')
                filter_start_hour = int(start_time_str.split(':')[0])
                filter_end_hour = int(end_time_str.split(':')[0])
            except Exception:
                return jsonify({"error": "Invalid hourly_range format. Use HH:MM-HH:MM (e.g., 09:00-17:00)"}), 400
        elif start_hour is not None and end_hour is not None:
            try:
                filter_start_hour = int(start_hour)
                filter_end_hour = int(end_hour)
            except ValueError:
                return jsonify({"error": "Invalid start_hour or end_hour. Must be integers (0-23)"}), 400

        # Validate hour range
        if filter_start_hour is not None and filter_end_hour is not None:
            if not (0 <= filter_start_hour <= 23 and 0 <= filter_end_hour <= 23):
                return jsonify({"error": "Hours must be between 0 and 23"}), 400
            if filter_start_hour > filter_end_hour:
                return jsonify({"error": "start_hour must be less than or equal to end_hour"}), 400

        # --- Parse date filters ---
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

        # --- Fetch sessions with optional filters ---
        query = db.query(Session)
        if division_name:
            query = query.filter(Session.division_name == division_name)
        if ca_number:
            query = query.filter(Session.ca_number == ca_number)
        if tel_no:
            query = query.filter(Session.tel_no == tel_no)
        if source:
            query = query.filter(Session.source == source)

        all_sessions = query.all()

        # --- Data containers ---
        daily_data = defaultdict(lambda: {"pay_bill_count": 0, "unique_users": set(), "user_details": {}})
        combined_data = {"pay_bill_count": 0, "unique_users": set(), "user_details": {}}

        for session in all_sessions:
            if not session.chat:
                continue

            for entry in session.chat:
                ts_str = entry.get("timestamp")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=ist)
                    else:
                        ts = ts.astimezone(ist)
                except Exception:
                    continue

                session_date = ts.date()

                # --- Apply date filters ---
                if last_hour and not (one_hour_ago <= ts <= now):
                    continue
                if date_filter and session_date != date_filter:
                    continue
                if start_date and end_date and not (start_date <= session_date <= end_date):
                    continue
                if month_str and not (month_start <= session_date <= month_end):
                    continue

                # --- Apply hourly range filter ---
                if filter_start_hour is not None and filter_end_hour is not None:
                    hour = ts.hour
                    if not (filter_start_hour <= hour < filter_end_hour):
                        continue

                query_text = entry.get("query", "").lower()
                answer = entry.get("answer", "")

                if query_text == "pay the bill" and answer == "https://www.bsesdelhi.com/web/brpl/quick-pay":
                    target = daily_data[session_date] if (date_filter or last_hour) else combined_data
                    target["pay_bill_count"] += 1
                    target["unique_users"].add(session.user_id)
                    target["user_details"][session.user_id] = {
                        "user_id": session.user_id,
                        "division_name": session.division_name,
                        "session_id": session.id,
                        "ca_number": session.ca_number,
                        "user_type": session.user_type,
                        "name": getattr(session, "first_name", None),
                        "phone_number": session.tel_no
                    }

        # --- Build report ---
        if date_filter or last_hour:
            report = [
                {
                    "date": str(day),
                    "pay_bill_count": stats["pay_bill_count"],
                    "unique_users_initiated_pay_bill": len(stats["unique_users"]),
                    "user_details": list(stats["user_details"].values())
                }
                for day, stats in sorted(daily_data.items())
            ]
        else:
            report = [{
                "pay_bill_count": combined_data["pay_bill_count"],
                "unique_users_initiated_pay_bill": len(combined_data["unique_users"]),
                "user_details": list(combined_data["user_details"].values())
            }]

        # --- Build hourly range display string ---
        hourly_range_display = None
        if filter_start_hour is not None and filter_end_hour is not None:
            hourly_range_display = f"{filter_start_hour:02d}:00-{filter_end_hour:02d}:00"

        response = {
            "filters": {
                "date": date_str,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "month": month_str,
                "last_hour": last_hour,
                "hourly_range": hourly_range_display,
                "division_name": division_name if division_name else "all",
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source
            },
            "stats": report
        }
        return jsonify(response)

    except Exception as e:
        print("MIS Pay Bill Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500

    finally:
        db.close()
        
## MIS Total Interactions

def mis_interaction_breakdown():
    try:
        db = SessionLocal()

        # --- Fetch query parameters ---
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")
        week_str = request.args.get("week")
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        # --- NEW: Hourly range filter ---
        # Format: "09:00-17:00" or "start_hour=9&end_hour=17"
        hourly_range = request.args.get("hourly_range")  # e.g., "09:00-17:00"
        start_hour = request.args.get("start_hour")      # e.g., 9
        end_hour = request.args.get("end_hour")          # e.g., 17

        page = int(request.args.get("page", 1))
        per_page = 5  # records per page

        # --- IST timezone ---
        ist = timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

        # --- Parse hourly range ---
        filter_start_hour = None
        filter_end_hour = None

        if hourly_range:
            try:
                # Parse format "09:00-17:00"
                start_time_str, end_time_str = hourly_range.split('-')
                filter_start_hour = int(start_time_str.split(':')[0])
                filter_end_hour = int(end_time_str.split(':')[0])
            except Exception:
                return jsonify({"error": "Invalid hourly_range format. Use HH:MM-HH:MM (e.g., 09:00-17:00)"}), 400
        elif start_hour is not None and end_hour is not None:
            try:
                filter_start_hour = int(start_hour)
                filter_end_hour = int(end_hour)
            except ValueError:
                return jsonify({"error": "Invalid start_hour or end_hour. Must be integers (0-23)"}), 400

        # Validate hour range
        if filter_start_hour is not None and filter_end_hour is not None:
            if not (0 <= filter_start_hour <= 23 and 0 <= filter_end_hour <= 23):
                return jsonify({"error": "Hours must be between 0 and 23"}), 400
            if filter_start_hour > filter_end_hour:
                return jsonify({"error": "start_hour must be less than or equal to end_hour"}), 400

        # --- Parse filters ---
        date_filter = None
        start_date = None
        end_date = None
        month_start = None
        month_end = None
        week_start = None
        week_end = None

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
        elif week_str:
            year, week_num = map(int, week_str.split('-'))
            week_start = datetime.fromisocalendar(year, week_num, 1).date()
            week_end = datetime.fromisocalendar(year, week_num, 7).date()

        # --- Fetch sessions with optional filters ---
        query = db.query(Session)
        if division_name:
            query = query.filter(Session.division_name == division_name)
        if ca_number:
            query = query.filter(Session.ca_number == ca_number)
        if tel_no:
            query = query.filter(Session.tel_no == tel_no)
        if source:
            query = query.filter(Session.source == source)

        sessions = query.all()
        total_interactions = 0
        session_logs = []

        for session in sessions:
            if not session.chat:
                continue

            try:
                timestamps = []
                for chat in session.chat:
                    ts_str = chat.get("timestamp")
                    if ts_str:
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=ist)
                        else:
                            ts = ts.astimezone(ist)
                        timestamps.append(ts)
            except Exception:
                continue

            if not timestamps:
                continue

            session_start = min(timestamps)
            session_end = max(timestamps)
            session_date = session_start.date()

            # --- Apply date filters ---
            if last_hour and not (one_hour_ago <= session_end <= now or one_hour_ago <= session_start <= now):
                continue
            elif date_filter and session_date != date_filter:
                continue
            elif start_date and end_date and not (start_date <= session_date <= end_date):
                continue
            elif month_str and not (month_start <= session_date <= month_end):
                continue
            elif week_str and not (week_start <= session_date <= week_end):
                continue

            # --- Apply hourly range filter ---
            if filter_start_hour is not None and filter_end_hour is not None:
                # Check if any interaction falls within the specified hour range
                session_in_range = False
                for ts in timestamps:
                    hour = ts.hour
                    if filter_start_hour <= hour < filter_end_hour:
                        session_in_range = True
                        break
                if not session_in_range:
                    continue

            # --- Determine if chat is complete ---
            is_complete = False
            if isinstance(session.chat, list) and session.chat:
                last_message = session.chat[-1]
                message_text = last_message.get("message", "").lower()
                if any(x in message_text for x in ["thank you", "resolved", "goodbye", "bye", "done", "issue resolved"]):
                    is_complete = True

            total_interactions += 1
            session_logs.append({
                "session_id": session.id,
                "session_start": session_start.isoformat(),
                "session_end": session_end.isoformat(),
                "is_complete": is_complete,
                "logs": session.chat
            })

        # --- Sort and paginate ---
        session_logs.sort(key=lambda x: x["session_end"], reverse=True)
        total_records = len(session_logs)
        total_pages = (total_records + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_logs = session_logs[start_idx:end_idx]

        # --- Separate complete/incomplete session data ---
        completed_sessions = [s for s in session_logs if s["is_complete"]]
        incomplete_sessions = [s for s in session_logs if not s["is_complete"]]

        # --- Build hourly range display string ---
        hourly_range_display = None
        if filter_start_hour is not None and filter_end_hour is not None:
            hourly_range_display = f"{filter_start_hour:02d}:00-{filter_end_hour:02d}:00"

        return jsonify({
            "filters": {
                "date": date_str,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "month": month_str,
                "week": week_str,
                "last_hour": last_hour,
                "hourly_range": hourly_range_display,
                "division_name": division_name if division_name else "all",
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source
            },
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_records": total_records,
            "total_interactions": total_interactions,
            "data": paginated_logs,
            "session_ids": [s["session_id"] for s in paginated_logs],
            "completed_sessions": completed_sessions,
            "incomplete_sessions": incomplete_sessions
        })

    except Exception as e:
        print("Error in mis_interaction_breakdown:", e)
        return jsonify({"error": "Something went wrong"}), 500

    finally:
        db.close()



## Visually Impaired

def visually_impaired_analysis():
    try:
        db = SessionLocal()

        # --- Query parameters ---
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        # --- Hourly range filter ---
        hourly_range = request.args.get("hourly_range")
        start_hour = request.args.get("start_hour")
        end_hour = request.args.get("end_hour")

        # --- Time calculations ---
        ist = timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

        # --- Parse hourly range ---
        filter_start_hour = None
        filter_end_hour = None

        if hourly_range:
            try:
                start_time_str, end_time_str = hourly_range.split('-')
                filter_start_hour = int(start_time_str.split(':')[0])
                filter_end_hour = int(end_time_str.split(':')[0])
            except Exception:
                return jsonify({"error": "Invalid hourly_range format. Use HH:MM-HH:MM (e.g., 09:00-17:00)"}), 400
        elif start_hour is not None and end_hour is not None:
            try:
                filter_start_hour = int(start_hour)
                filter_end_hour = int(end_hour)
            except ValueError:
                return jsonify({"error": "Invalid start_hour or end_hour. Must be integers (0-23)"}), 400

        # Validate hour range
        if filter_start_hour is not None and filter_end_hour is not None:
            if not (0 <= filter_start_hour <= 23 and 0 <= filter_end_hour <= 23):
                return jsonify({"error": "Hours must be between 0 and 23"}), 400
            if filter_start_hour > filter_end_hour:
                return jsonify({"error": "start_hour must be less than or equal to end_hour"}), 400

        # --- Date filters ---
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

        # --- Completion messages ---
        # completion_messages = [
        #     "Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)",
        #     "धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)"
        # ]

        completion_messages = [
            "Thank you. Would you like to return to the main menu? Select Yes or type ‘menu’ or ‘hi’ to continue.",
            "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए ‘हाँ’, ‘menu’ या ‘hi’ टाइप करें।"
        ]

        visually_impaired_variants = [
            "Visually Impaired BRPL",
            "दृष्टिबाधित सहायता BRPL"
        ]

        # --- Fetch sessions with filters ---
        query = db.query(Session)
        if division_name:
            query = query.filter(Session.division_name == division_name)
        if ca_number:
            query = query.filter(Session.ca_number == ca_number)
        if tel_no:
            query = query.filter(Session.tel_no == tel_no)
        if source:
            query = query.filter(Session.source == source)

        sessions = query.all()
        completed_users = []

        for session in sessions:
            if not session.chat:
                continue

            # --- Extract timestamps ---
            timestamps = []
            for chat in session.chat:
                ts_str = chat.get("timestamp")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ist.localize(ts)
                    else:
                        ts = ts.astimezone(ist)
                    timestamps.append(ts)
                except:
                    continue
            if not timestamps:
                continue

            session_date = min(timestamps).date()

            # --- Apply date filters ---
            if last_hour and max(timestamps) < one_hour_ago:
                continue
            if date_filter and session_date != date_filter:
                continue
            if start_date and end_date and not (start_date <= session_date <= end_date):
                continue
            if month_str and not (month_start <= session_date <= month_end):
                continue

            # --- Apply hourly range filter ---
            if filter_start_hour is not None and filter_end_hour is not None:
                session_in_range = False
                for ts in timestamps:
                    hour = ts.hour
                    if filter_start_hour <= hour < filter_end_hour:
                        session_in_range = True
                        break
                if not session_in_range:
                    continue

            active_option = False
            option_completed = False

            for chat in session.chat:
                query_text = (chat.get("query") or "").lower()
                answer = (chat.get("answer") or "")
                answer_text = json.dumps(answer, ensure_ascii=False).lower() if isinstance(answer, dict) else str(answer).lower()

                # Check menu option selection
                if any(v.lower() in query_text + " " + answer_text for v in visually_impaired_variants):
                    active_option = True

                # Check completion
                if active_option and any(cm.lower() in query_text + " " + answer_text for cm in completion_messages):
                    option_completed = True
                    break

            if option_completed:
                completed_users.append({
                    "user_id": session.user_id,
                    "phone_number": session.tel_no,
                    "ca_number": session.ca_number,
                    "user_type": session.user_type,
                    "date": str(session_date),
                    "division_name": session.division_name
                })

        # --- Build hourly range display string ---
        hourly_range_display = None
        if filter_start_hour is not None and filter_end_hour is not None:
            hourly_range_display = f"{filter_start_hour:02d}:00-{filter_end_hour:02d}:00"

        response = {
            "filters": {
                "date": date_str,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "month": month_str,
                "last_hour": last_hour,
                "hourly_range": hourly_range_display,
                "division_name": division_name if division_name else "all",
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source
            },
            "total_completed": len(completed_users),
            "users": completed_users
        }

        return jsonify(response)

    except Exception as e:
        print("Error in visually_impaired_analysis:", e)
        return jsonify({"error": "Something went wrong"}), 500

    finally:
        db.close()
