from collections import defaultdict
from flask import json, jsonify, request
import requests
from Models.session_model import Session
from Models.utter_messages_model import UtterMessage
from database import SessionLocal
from datetime import date, datetime, timedelta
# from sqlalchemy import func, cast, Date, extract
from sqlalchemy import and_
from pytz import timezone
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


flask_url = os.getenv('BACKEND_URL')

# ====================== Get Session Counts ======================
def get_session_counts():
    try:
        db = SessionLocal()

        # --- Query params ---
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")  # NEW: YYYY-MM format
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
        grouped_submenus = defaultdict(lambda: {"en": [], "hi": []})
        for item in submenu_data:
            name = item.get("name")
            lang = item.get("lang")
            menu_id = item.get("menu_id")
            if not name or not menu_id:
                continue
            name_with_brpl = f"{name.strip()} BRPL"
            grouped_submenus[menu_id][lang].append(name_with_brpl)

        valid_service_options = set()
        for _, group in grouped_submenus.items():
            valid_service_options.update(group["en"])
            valid_service_options.update(group["hi"])

        # --- Date range logic ---
        is_single_day = False
        is_multi_day = False
        is_monthly = False
        month_filter = None

        if date_str:
            # Single day filter
            start_time = ist.localize(datetime.strptime(date_str, "%Y-%m-%d"))
            end_time = start_time + timedelta(days=1)
            is_single_day = True
        elif start_date_str and end_date_str:
            # Date range filter
            start_time = ist.localize(datetime.strptime(start_date_str, "%Y-%m-%d"))
            end_time = ist.localize(datetime.strptime(end_date_str, "%Y-%m-%d")) + timedelta(days=1)
            if start_date_str == end_date_str:
                is_single_day = True
            else:
                is_multi_day = True
        elif month_str:
            # Monthly filter
            month_filter = datetime.strptime(month_str, "%Y-%m").date()
            start_time = ist.localize(datetime(month_filter.year, month_filter.month, 1))
            # Calculate last day of month
            if month_filter.month == 12:
                end_time = ist.localize(datetime(month_filter.year + 1, 1, 1))
            else:
                end_time = ist.localize(datetime(month_filter.year, month_filter.month + 1, 1))
            is_monthly = True
        else:
            # Default: last 24 hours
            now = datetime.now(ist)
            start_time = now - timedelta(hours=24)
            end_time = now
            is_single_day = True

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

        # --- Helper: convert timestamp to IST ---
        def to_ist(dt):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            if dt.tzinfo is None:
                dt = ist.localize(dt)
            else:
                dt = dt.astimezone(ist)
            return dt

        # --- Aggregation data structures ---
        bucket_data = defaultdict(lambda: {
            "total_interactions": 0,
            "unique_users": set(),
            "services_called": defaultdict(int)
        })
        
        daily_data = defaultdict(lambda: {
            "total_interactions": 0,
            "unique_users": set(),
            "services_called": defaultdict(int)
        })
        
        weekly_data = defaultdict(lambda: {
            "total_interactions": 0,
            "unique_users": set(),
            "services_called": defaultdict(int)
        })

        # --- Process sessions ---
        for session in all_sessions:
            if not session.chat:
                continue

            for entry in session.chat:
                ts_str = entry.get("timestamp")
                if not ts_str:
                    continue

                try:
                    ts = to_ist(ts_str)
                except Exception:
                    continue

                if not (start_time <= ts < end_time):
                    continue

                query_text = entry.get("query", "").strip()
                user_id = session.user_id
                
                # Count valid chatbot service calls
                is_valid_service = query_text in valid_service_options

                # --- Hourly bucket (for single day) ---
                if is_single_day:
                    hour = ts.hour
                    bucket = (hour // 2) * 2
                    bucket_data[bucket]["total_interactions"] += 1
                    bucket_data[bucket]["unique_users"].add(user_id)
                    if is_valid_service:
                        bucket_data[bucket]["services_called"][query_text] += 1

                # --- Daily aggregation (for multi-day or monthly) ---
                if is_multi_day or is_monthly:
                    day_key = ts.strftime("%Y-%m-%d")
                    daily_data[day_key]["total_interactions"] += 1
                    daily_data[day_key]["unique_users"].add(user_id)
                    if is_valid_service:
                        daily_data[day_key]["services_called"][query_text] += 1

                # --- Weekly aggregation (for monthly) ---
                if is_monthly:
                    ts_date = ts.date()
                    week_num = ((ts_date.day - 1) // 7) + 1
                    week_num = min(week_num, 4)
                    week_key = f"week{week_num}"
                    weekly_data[week_key]["total_interactions"] += 1
                    weekly_data[week_key]["unique_users"].add(user_id)
                    if is_valid_service:
                        weekly_data[week_key]["services_called"][query_text] += 1

        # --- Build response based on filter type ---
        response = {
            "filters": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "division_name": division_name if division_name else "all",
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source
            }
        }

        if is_single_day:
            # --- Single day: return 2-hourly buckets ---
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

            # Peak 2-hour block
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

            response["peak_time"] = f"{peak_start_label} - {peak_end_label}"
            response["hourly_report"] = report

        elif is_multi_day:
            # --- Multi-day: return daily breakdown with peak date ---
            daily_report = []
            for day_key in sorted(daily_data.keys()):
                data = daily_data[day_key]
                daily_report.append({
                    "date": day_key,
                    "total_interactions": data["total_interactions"],
                    "unique_users": len(data["unique_users"]),
                    "services_called": dict(data["services_called"])
                })

            # Peak date
            if daily_data:
                peak_date = max(daily_data, key=lambda d: daily_data[d]["total_interactions"])
                peak_data = daily_data[peak_date]
                peak_day = {
                    "date": peak_date,
                    "total_interactions": peak_data["total_interactions"],
                    "unique_users": len(peak_data["unique_users"]),
                    "services_called": dict(peak_data["services_called"])
                }
            else:
                peak_day = {
                    "date": None,
                    "total_interactions": 0,
                    "unique_users": 0,
                    "services_called": {}
                }

            response["peak_time"] = peak_date
            response["daily_report"] = daily_report

        elif is_monthly:
            # --- Monthly: return daily breakdown + weekly summary ---
            daily_report = []
            for day_key in sorted(daily_data.keys()):
                data = daily_data[day_key]
                daily_report.append({
                    "date": day_key,
                    "total_interactions": data["total_interactions"],
                    "unique_users": len(data["unique_users"]),
                    "services_called": dict(data["services_called"])
                })

            # Weekly summary
            weekly_summary = {}
            total_monthly_interactions = 0
            for week_key in ["week1", "week2", "week3", "week4"]:
                data = weekly_data.get(week_key)
                
                if data:
                    interactions = data["total_interactions"]
                    weekly_summary[week_key] = interactions
                    total_monthly_interactions += interactions
                else:
                    weekly_summary[week_key] = 0

            # Peak date
            if daily_data:
                peak_date = max(daily_data, key=lambda d: daily_data[d]["total_interactions"])
                peak_data = daily_data[peak_date]
                peak_day = {
                    "date": peak_date,
                    "total_interactions": peak_data["total_interactions"],
                    "unique_users": len(peak_data["unique_users"]),
                    "services_called": dict(peak_data["services_called"])
                }
            else:
                peak_day = {
                    "date": None,
                    "total_interactions": 0,
                    "unique_users": 0,
                    "services_called": {}
                }

            response["monthly"] = {
                "total_interactions": total_monthly_interactions,
                "weeks": weekly_summary
            }
            response["peak_time"] = peak_date
            response["daily_report"] = daily_report

        return jsonify(response)

    except Exception as e:
        print("MIS Peak Hours Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500

    finally:
        db.close()





# ====================== Interaction Breakdown ======================

def interaction_breakdown():
    try:
        db = SessionLocal()
        sessions = db.query(Session).all()

        # Query params
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        page = int(request.args.get("page", 1))
        per_page = 5

        ist = timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

        # --- Date filters ---
        date_filter = start_date = end_date = month_start = month_end = None
        if date_str:
            date_filter = datetime.strptime(date_str, "%Y-%m-%d").date()
        elif start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        elif month_str:
            month_filter = datetime.strptime(month_str, "%Y-%m").date()
            month_start = month_filter.replace(day=1)
            month_end = (month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
                         if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1))

        # --- Helper: Convert to IST ---
        def to_ist(dt):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            if dt.tzinfo is None:
                dt = ist.localize(dt)
            else:
                dt = dt.astimezone(ist)
            return dt

        # --- Apply division and other filters ---
        sessions = [
            s for s in sessions
            if (not division_name or getattr(s, "division_name", None) == division_name)
            and (not ca_number or getattr(s, "ca_number", None) == ca_number)
            and (not tel_no or getattr(s, "tel_no", None) == tel_no)
            and (not source or getattr(s, "source", None) == source)
        ]

        # --- Chatbot menu options ---
        chatbot_options = {
            "new_consumer": [
                "New Connection Application BRPL", "नया कनेक्शन आवेदन BRPL",
                "New Connection Status BRPL", "नए कनेक्शन की स्थिति BRPL",
                "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL) BRPL",
                "वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL) BRPL",
                "Streetlight Complaint BRPL", "स्ट्रीटलाइट शिकायत BRPL",
                "FAQs BRPL", "सामान्य प्रश्न (FAQs) BRPL",
                "Branches Nearby BRPL", "नज़दीकी शाखाएँ BRPL",
                "Visually Impaired BRPL", "दृष्टिबाधित सहायता BRPL",
                "Select Another CA number BRPL", "कोई और सीए नंबर चुनें BRPL",
                "Change Language BRPL", "भाषा बदलें BRPL"
            ],
            "registered_consumer": [
                "Meter Reading Schedule BRPL", "मीटर रीडिंग शेड्यूल BRPL",
                "New Connection Application BRPL", "नया कनेक्शन आवेदन BRPL",
                "New Connection Status BRPL", "नए कनेक्शन की स्थिति BRPL",
                "Prepaid Meter - Check Balance / Recharge BRPL", "प्रीपेड मीटर - बैलेंस जांचें / रिचार्ज करें BRPL",
                "Consumption History BRPL", "खपत का इतिहास BRPL",
                "Duplicate Bill BRPL", "डुप्लिकेट बिल BRPL",
                "Payment Status BRPL", "भुगतान की स्थिति BRPL",
                "Payment History BRPL", "भुगतान इतिहास BRPL",
                "Opt for e-bill BRPL", "ई-बिल के लिए ऑप्ट-इन करें BRPL",
                "Register Complaint BRPL", "शिकायत दर्ज करें BRPL",
                "Complaint Status (NCC) BRPL", "शिकायत की स्थिति (NCC) BRPL",
                "Streetlight Complaint BRPL", "स्ट्रीटलाइट शिकायत BRPL",
                "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL) BRPL",
                "वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL) BRPL",
                "Visually Impaired BRPL", "दृष्टिबाधित सहायता BRPL",
                "Select Another CA number BRPL", "कोई और सीए नंबर चुनें BRPL",
                "Change Language BRPL", "भाषा बदलें BRPL",
                "FAQs BRPL", "सामान्य प्रश्न (FAQs) BRPL",
                "Branches Nearby BRPL", "नज़दीकी शाखाएँ BRPL"
            ]
        }

        # completion_messages = [
        #     "Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)",
        #     "धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)"
        # ]

        thank_eng = db.query(UtterMessage).filter(
            UtterMessage.id == 10,
        ).first()

        thank_hin = db.query(UtterMessage).filter(
            UtterMessage.id == 11,
        ).first()

        completion_messages = [
            thank_eng.text,
            thank_hin.text
        ]

        # completion_messages = [
        #     "Thank you. Would you like to return to the main menu? Select Yes or type ‘menu’ or ‘hi’ to continue.",
        #     "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए ‘हाँ’, ‘menu’ या ‘hi’ टाइप करें।"
        # ]


        breakdown = {opt: {"count": 0, "logs": []}
                     for group in chatbot_options.values() for opt in group}
        option_keys = list(breakdown.keys())
        option_keys_lower = [ok.lower() for ok in option_keys]

        # --- Sort sessions by latest chat ---
        sessions = sorted(
            sessions,
            key=lambda s: max(
                [to_ist(chat.get("timestamp")) for chat in (s.chat or []) if "timestamp" in chat] or
                [datetime.min.replace(tzinfo=ist)]
            ),
            reverse=True
        )

        completed_sessions_data = []   # full session data
        incomplete_sessions_data = []

        for session in sessions:
            if not session.chat:
                continue

            timestamps = [to_ist(chat.get("timestamp")) for chat in session.chat if "timestamp" in chat]
            if not timestamps:
                continue

            session_start = min(timestamps)
            session_end = max(timestamps)
            session_date = session_start.date()

            # --- Apply date filters ---
            if last_hour and session_end < one_hour_ago:
                continue
            if date_filter and session_date != date_filter:
                continue
            if start_date and end_date and not (start_date <= session_date <= end_date):
                continue
            if month_str and not (month_start <= session_date <= month_end):
                continue

            active_option = None
            current_group_key = None
            current_group_messages = []
            chat_completed = False

            def finalize_group():
                nonlocal active_option, current_group_key, current_group_messages
                if active_option and current_group_messages:
                    breakdown[active_option]["logs"].append({
                        "session_id": current_group_key,
                        "entries": current_group_messages
                    })
                    breakdown[active_option]["count"] += 1
                active_option = None
                current_group_key = None
                current_group_messages = []

            for chat in session.chat:
                query = chat.get("query", "") or ""
                answer = chat.get("answer", "") or ""
                timestamp = chat.get("timestamp", "")

                answer_text = json.dumps(answer, ensure_ascii=False) if isinstance(answer, dict) else str(answer)
                combined = (query + " " + answer_text).lower()

                matched_option = None
                for idx, opt_lower in enumerate(option_keys_lower):
                    if opt_lower in combined:
                        matched_option = option_keys[idx]
                        break

                if matched_option:
                    finalize_group()
                    active_option = matched_option
                    group_idx = len(breakdown[active_option]["logs"]) + 1
                    current_group_key = f"logs_{group_idx}"
                    current_group_messages = [{"query": query, "answer": answer, "timestamp": timestamp}]
                elif active_option:
                    current_group_messages.append({"query": query, "answer": answer, "timestamp": timestamp})

                for cm in completion_messages:
                    if cm in query or cm in answer_text:
                        chat_completed = True
                        finalize_group()
                        break

            if current_group_messages:
                finalize_group()

            # ✅ Store full session data
            session_data = {
                "session_id": session.id,
                "division_name": getattr(session, "division_name", None),
                "ca_number": getattr(session, "ca_number", None),
                "tel_no": getattr(session, "tel_no", None),
                "source": getattr(session, "source", None),
                "user_type": getattr(session, "user_type", None),
                "chat": session.chat
            }

            if chat_completed:
                completed_sessions_data.append(session_data)
            else:
                incomplete_sessions_data.append(session_data)

        # --- Transform breakdown for display ---
        formatted_data = []
        for option, details in breakdown.items():
            if details["count"] > 0:
                sorted_logs = sorted(
                    details["logs"],
                    key=lambda log: max(
                        [to_ist(entry["timestamp"]) for entry in log["entries"] if "timestamp" in entry] or
                        [datetime.min.replace(tzinfo=ist)]
                    ),
                    reverse=True
                )
                formatted_data.append({
                    "option": option,
                    "logs": sorted_logs
                })

        # --- Pagination ---
        total_records = len(formatted_data)
        total_pages = (total_records + per_page - 1) // per_page
        paginated_data = formatted_data[(page - 1) * per_page: (page * per_page)]

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_records": total_records,
            "data": paginated_data,
            "session_info": {
                "completed_sessions": completed_sessions_data,
                "incomplete_sessions": incomplete_sessions_data
            }
        })

    except Exception as e:
        print("Error in interaction_breakdown:", e)
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500

    finally:
        db.close()


from flask import request, jsonify
from datetime import datetime, timedelta, date
from pytz import timezone
from collections import defaultdict
from dateutil.parser import isoparse
from sqlalchemy import func
import calendar, json, traceback

def average_interaction_time():
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
        ist = timezone("Asia/Kolkata")
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

        # --- Parse dates ---
        date_filter = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else None
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

        month_start = month_end = None
        if month_str:
            month_filter = datetime.strptime(month_str, "%Y-%m").date()
            year, month = month_filter.year, month_filter.month
            last_day = calendar.monthrange(year, month)[1]
            month_start = date(year, month, 1)
            month_end = date(year, month, last_day)

        # --- Build Query ---
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

        # --- Convert timestamps safely ---
        def to_ist(dt):
            if isinstance(dt, str):
                dt = isoparse(dt)
            if dt.tzinfo is None:
                dt = ist.localize(dt)
            else:
                dt = dt.astimezone(ist)
            return dt

        durations = []
        weekly_durations = defaultdict(list)

        # --- Process sessions ---
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
                        timestamps.append(to_ist(chat["timestamp"]))
                    except Exception:
                        continue

            if not timestamps:
                continue

            start = min(timestamps)
            end = max(timestamps)
            duration = (end - start).total_seconds()
            session_date = start.date()

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

            # --- Apply date filters ---
            if last_hour:
                if start >= one_hour_ago or end >= one_hour_ago:
                    durations.append(duration)
            elif date_filter:
                if session_date == date_filter:
                    durations.append(duration)
            elif start_date and end_date:
                if start_date <= session_date <= end_date:
                    durations.append(duration)
            elif month_start and month_end:
                if month_start <= session_date <= month_end:
                    durations.append(duration)
                    week_num = min(((session_date.day - 1) // 7) + 1, 4)
                    weekly_durations[f"week{week_num}"].append(duration)
            else:
                durations.append(duration)

        # --- Duration formatting helper ---
        def format_duration(seconds):
            minutes = int(seconds // 60)
            sec = int(seconds % 60)
            return f"{minutes} minutes {sec} seconds" if minutes else f"{sec} seconds"

        # --- Build hourly range display string ---
        hourly_range_display = None
        if filter_start_hour is not None and filter_end_hour is not None:
            hourly_range_display = f"{filter_start_hour:02d}:00-{filter_end_hour:02d}:00"

        # --- Build result ---
        if durations:
            avg_seconds = sum(durations) / len(durations)
            result = {
                "avg_duration": format_duration(avg_seconds),
                "total_sessions": len(durations),
                "filter_applied": (
                    "last_hour" if last_hour else
                    f"date={date_str}" if date_str else
                    f"range={start_date_str} to {end_date_str}" if start_date and end_date else
                    f"month={month_str}" if month_str else
                    "all"
                ),
                "hourly_range": hourly_range_display,
                "division_name": division_name or "all"
            }

            if month_start and month_end:
                result["weekly"] = {
                    f"week{i}": (
                        format_duration(sum(weekly_durations[f"week{i}"]) / len(weekly_durations[f"week{i}"]))
                        if weekly_durations[f"week{i}"] else "0 seconds"
                    )
                    for i in range(1, 5)
                }

        else:
            result = {
                "message": "No sessions found for the given filters.",
                "division_name": division_name or "all"
            }
            if month_start and month_end:
                result["weekly"] = {f"week{i}": "0 seconds" for i in range(1, 5)}

        return jsonify(result)

    except Exception as e:
        print("Error in average_interaction_time:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

    finally:
        if db:
            db.close()

# ====================== Chat Status ======================
def chat_status():
    try:
        db = SessionLocal()

        # Extract query parameters
        last_hour = request.args.get("last_hour", "").lower() == "true"
        date_str = request.args.get("date")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        month_str = request.args.get("month")  # YYYY-MM
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

        # --- Hourly range filter ---
        hourly_range = request.args.get("hourly_range")
        start_hour = request.args.get("start_hour")
        end_hour = request.args.get("end_hour")

        filters = []

        # --- use IST timezone ---
        ist = timezone("Asia/Kolkata")
        now = datetime.now(ist).replace(tzinfo=None)  # naive IST to match DB

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

        month_start = None
        month_end = None
        month_filter = False

        # --- last hour filter ---
        if last_hour:
            cutoff = now - timedelta(hours=1)
            filters.append(and_(
                Session.created_at >= cutoff,
                Session.created_at <= now
            ))

        # --- single day filter ---
        elif date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                filters.append(and_(
                    Session.created_at >= datetime.combine(date_obj, datetime.min.time()),
                    Session.created_at <= datetime.combine(date_obj, datetime.max.time())
                ))
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        # --- date range filter ---
        elif start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                filters.append(and_(
                    Session.created_at >= datetime.combine(start_date, datetime.min.time()),
                    Session.created_at <= datetime.combine(end_date, datetime.max.time())
                ))
            except ValueError:
                return jsonify({"error": "Invalid date range format. Use YYYY-MM-DD"}), 400

        # --- month filter ---
        elif month_str:
            try:
                month_date = datetime.strptime(month_str, "%Y-%m").date()
                month_start = datetime.combine(month_date.replace(day=1), datetime.min.time())
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(seconds=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(seconds=1)
                filters.append(and_(
                    Session.created_at >= month_start,
                    Session.created_at <= month_end
                ))
                month_filter = True
            except ValueError:
                return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400

        # --- optional filters ---
        if division_name:
            filters.append(Session.division_name == division_name)
        if ca_number:
            filters.append(Session.ca_number == ca_number)
        if tel_no:
            filters.append(Session.tel_no == tel_no)
        if source:
            filters.append(Session.source == source)

        # --- query ---
        if filters:
            sessions = db.query(Session).filter(*filters).all()
        else:
            sessions = db.query(Session).all()

        # Don't calculate total_sessions yet - will count after hourly filter
        completed_count = 0
        left_count = 0

        # Weekly buckets
        weekly_stats = {
            "week1": {"completed": 0, "left": 0, "total": 0},
            "week2": {"completed": 0, "left": 0, "total": 0},
            "week3": {"completed": 0, "left": 0, "total": 0},
            "week4": {"completed": 0, "left": 0, "total": 0},
        }

        # thank_you_messages = [
        #     "Thank you! Would you like to go back to main menu. (You can type 'menu' or 'hi' to come back to main options)",
        #     "धन्यवाद! क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? (आप 'menu' या 'hi' लिखकर मुख्य विकल्पों पर वापस आ सकते हैं)"
        # ]

        thank_eng = db.query(UtterMessage).filter(
            UtterMessage.id == 10,
        ).first()

        thank_hin = db.query(UtterMessage).filter(
            UtterMessage.id == 11,
        ).first()

        thank_you_messages = [
            thank_eng.text,
            thank_hin.text
        ]

        # thank_you_messages = [
        #     "Thank you. Would you like to return to the main menu? Select Yes or type ‘menu’ or ‘hi’ to continue.",
        #     "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए ‘हाँ’, ‘menu’ या ‘hi’ टाइप करें।"
        # ]


        # --- process sessions ---
        for s in sessions:
            if not s.chat or len(s.chat) == 0:
                continue

            # --- Apply hourly range filter ---
            if filter_start_hour is not None and filter_end_hour is not None:
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

            try:
                last_message = s.chat[-1]
                main_menu_heading = last_message.get("answer", {}).get("response", {}).get("main_menu_heading")

                is_completed = main_menu_heading and main_menu_heading.strip() in thank_you_messages

                if is_completed:
                    completed_count += 1
                else:
                    left_count += 1

                # Assign to weekly bucket if month filter is applied
                if month_filter:
                    session_date = s.created_at.date()
                    if month_start.date() <= session_date <= month_end.date():
                        week_num = ((session_date.day - 1) // 7) + 1
                        if week_num > 4:
                            week_num = 4
                        key = f"week{week_num}"
                        weekly_stats[key]["total"] += 1
                        if is_completed:
                            weekly_stats[key]["completed"] += 1
                        else:
                            weekly_stats[key]["left"] += 1

            except Exception:
                left_count += 1

        # --- Calculate total_sessions from filtered counts ---
        total_sessions = completed_count + left_count

        # --- Build hourly range display string ---
        hourly_range_display = None
        if filter_start_hour is not None and filter_end_hour is not None:
            hourly_range_display = f"{filter_start_hour:02d}:00-{filter_end_hour:02d}:00"

        response = {
            "total_sessions": total_sessions,
            "completed_chats": completed_count,
            "left_chats": left_count,
            "hourly_range": hourly_range_display,
            "division_name": division_name if division_name else "all",
            "ca_number": ca_number if ca_number else "all",
            "tel_no": tel_no if tel_no else "all",
            "source": source if source else "all"
        }

        if month_filter:
            response["weekly"] = weekly_stats

        return jsonify(response)

    except Exception as e:
        print("Error in chat_status:", e)
        return jsonify({"error": "Something went wrong"}), 500

    finally:
        db.close()




# ====================== Count Opt For E-Bill ======================
def count_opt_for_ebill():
    try:
        db = SessionLocal()
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

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

        opt_for_ebill_success_texts = [
            "You’ve successfully opted for E-Bill. Future bills will be emailed to you.",
            "आपने सफलतापूर्वक ई-बिल के लिए पंजीकरण कर लिया है। भविष्य के बिल आपके ईमेल पर भेजे जाएंगे।"
        ]

        opt_for_ebill_click_texts = [
            "Opt for e-bill BRPL",
            "ई-बिल के लिए ऑप्ट-इन करें BRPL"
        ]

        opt_for_ebill_count = 0
        users_opted_ebill = set()
        opt_for_ebill_click_count = 0
        users_clicked_ebill = set()

        for session in all_sessions:
            chat_data = session.chat
            if not chat_data:
                continue

            if isinstance(chat_data, str):
                try:
                    chat_data = json.loads(chat_data)
                except json.JSONDecodeError:
                    continue

            if not isinstance(chat_data, list):
                continue

            for entry in chat_data:
                if not isinstance(entry, dict):
                    continue

                query_text = entry.get("query", "")
                if query_text in opt_for_ebill_click_texts:
                    opt_for_ebill_click_count += 1
                    users_clicked_ebill.add(session.user_id)

                answer = entry.get("answer")
                if not isinstance(answer, dict):
                    continue

                response_data = answer.get("response")
                if not isinstance(response_data, dict):
                    continue

                heading = response_data.get("heading", [])
                if isinstance(heading, str):
                    heading = [heading]

                if any(success_text in heading for success_text in opt_for_ebill_success_texts):
                    opt_for_ebill_count += 1
                    users_opted_ebill.add(session.user_id)
                    break

        response = {
            "stats": {
                "total_users": len(all_sessions),
                "opt_for_ebill_clicks": opt_for_ebill_click_count,
                "unique_users_clicked_ebill": len(users_clicked_ebill),
                "opt_for_ebill_completed": opt_for_ebill_count,
                "unique_users_opted_ebill": len(users_opted_ebill),
                "conversion_rate": (
                    round((len(users_opted_ebill) / len(users_clicked_ebill) * 100), 2)
                    if users_clicked_ebill else 0
                )
            }
        }

        return jsonify(response)

    except Exception as e:
        import traceback
        print("Dashboard Error:", e)
        traceback.print_exc()
        return jsonify({'error': 'Something went wrong'}), 500

    finally:
        db.close()


# ====================== Dashboard Complaint Status ======================
def dashboard_complaint_status():
    try:
        db = SessionLocal()
        division_name = request.args.get("division_name")
        ca_number = request.args.get("ca_number")
        tel_no = request.args.get("tel_no")
        source = request.args.get("source")

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

        total_complaints = 0
        resolved_complaints = 0
        unique_users_with_complaints = set()

        all_complaints_list = []
        resolved_complaints_list = []
        user_details = {}  # user_id -> { user info + complaints list }

        for session in all_sessions:
            complaint_no = session.complain_no
            status = session.complain_status

            if not complaint_no:
                continue

            total_complaints += 1
            all_complaints_list.append(complaint_no)
            unique_users_with_complaints.add(session.user_id)

            if status == "resolved":
                resolved_complaints += 1
                resolved_complaints_list.append(complaint_no)

            # Build user detail map
            user_id = session.user_id
            if user_id not in user_details:
                user_details[user_id] = {
                    "user_id": user_id,
                    "ca_number": session.ca_number,
                    "tel_no": session.tel_no,
                    "division_name": session.division_name,
                    "source": session.source,
                    "complaints": []
                }

            user_details[user_id]["complaints"].append({
                "complaint_no": complaint_no,
                "status": status
            })

        response = {
            "stats": {
                "total_complaints": total_complaints,
                "resolved_complaints": resolved_complaints,
                "unique_users_with_complaints": len(unique_users_with_complaints)
            },
            "data": {
                "all_complaints": all_complaints_list,
                "resolved_complaints_list": resolved_complaints_list,
                "users": list(user_details.values())
            }
        }

        return jsonify(response)

    except Exception as e:
        print("Dashboard Complaint Status Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500

    finally:
        db.close()
