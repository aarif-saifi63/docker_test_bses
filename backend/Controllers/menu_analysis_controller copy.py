from flask import request, jsonify
from datetime import datetime, timedelta, timezone
import json
from Models.session_model import Session
from database import SessionLocal
from pytz import timezone
from dotenv import load_dotenv
import os
import requests
from flask import jsonify, request
from datetime import datetime, timedelta
from pytz import timezone
import json


# Load .env file
load_dotenv()

flask_url = os.getenv('BACKEND_URL')
# flask_url = f"{os.getenv('BASE_URL')}:{os.getenv('BACKEND_PORT')}"

def menu_analysis():
    try:
        db = SessionLocal()
        sessions = db.query(Session).all()

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
        menu_option = request.args.get("menu_option")

        page = max(int(request.args.get("page", 1)), 1)
        per_page = 5

        # --- Fetch dynamic submenus ---
        submenu_url = f"{flask_url}/submenus"
        submenu_response = requests.get(submenu_url, timeout=10)
        submenu_data = submenu_response.json().get("data", [])

        # --- Build canonical option map dynamically ---
        # Group submenus by menu_id to pair English & Hindi equivalents
        grouped_submenus = {}
        for item in submenu_data:
            menu_id = item.get("menu_id")
            name = item.get("name")
            lang = item.get("lang")
            if not menu_id or not name:
                continue
            # ✅ Append " BRPL" to every menu/submenu name
            name_with_brpl = f"{name.strip()} BRPL"
            grouped_submenus.setdefault(menu_id, {"en": [], "hi": []})
            grouped_submenus[menu_id][lang].append(name_with_brpl)

        # Create option_map similar to your previous hardcoded structure
        menu_groups = []
        for _, group in grouped_submenus.items():
            english_variants = group.get("en", [])
            hindi_variants = group.get("hi", [])
            if not english_variants:
                continue
            canonical_name = english_variants[0]  # first English variant as canonical
            all_variants = english_variants + hindi_variants
            menu_groups.append((canonical_name, all_variants))

        # Flatten to canonical lookup
        option_map = {v.lower(): canonical for canonical, variants in menu_groups for v in variants}

        # --- Validate menu option ---
        if not menu_option or menu_option.lower() not in option_map:
            return jsonify({"error": "Invalid or missing menu_option"}), 400

        canonical_option = option_map[menu_option.lower()]

        # --- Timezone setup ---
        ist = timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

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

        breakdown = {
            canonical_option: {
                "selected_count": 0,
                "completed_count": 0,
                "incomplete_count": 0,
                "logs": [],
                "user_type": {"new": 0, "registered": 0}
            }
        }

        def to_ist(dt):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)
            if dt.tzinfo is None:
                dt = ist.localize(dt)
            else:
                dt = dt.astimezone(ist)
            return dt

        session_ids = []
        completed_sessions = []
        incomplete_sessions = []

        for session in sessions:
            if division_name and getattr(session, "division_name", None) != division_name:
                continue
            if ca_number and getattr(session, "ca_number", None) != ca_number:
                continue
            if tel_no and getattr(session, "tel_no", None) != tel_no:
                continue
            if source and getattr(session, "source", None) != source:
                continue
            if not session.chat:
                continue

            try:
                timestamps = [to_ist(chat.get("timestamp")) for chat in session.chat if "timestamp" in chat]
            except Exception:
                continue

            if not timestamps:
                continue

            session.chat.sort(key=lambda x: to_ist(x.get("timestamp")), reverse=False)
            session_start = min(timestamps)
            session_end = max(timestamps)
            session_date = session_start.date()

            if last_hour and session_end < one_hour_ago:
                continue
            if date_filter and session_date != date_filter:
                continue
            if start_date and end_date and not (start_date <= session_date <= end_date):
                continue
            if month_str and not (month_start <= session_date <= month_end):
                continue

            full_session_messages = []
            matched = False
            completed = False
            end_index = None

            for idx, chat in enumerate(session.chat):
                query = chat.get("query", "") or ""
                answer = chat.get("answer", "") or ""
                timestamp = chat.get("timestamp", "")
                user_id = getattr(session, "user_id", None)

                answer_text = json.dumps(answer, ensure_ascii=False) if isinstance(answer, dict) else str(answer)
                combined = (query + " " + answer_text).lower()

                log_entry = {
                    "user_id": user_id,
                    "query": query,
                    "answer": answer,
                    "timestamp": timestamp
                }

                full_session_messages.append(log_entry)

                # Detect menu option
                if not matched and any(v.lower() in combined for v in option_map if option_map[v] == canonical_option):
                    matched = True

                # Detect completion
                if matched:
                    for cm in completion_messages:
                        if cm in query or cm in answer_text:
                            completed = True
                            end_index = idx
                            break
                if completed:
                    break

            if matched:
                if completed:
                    truncated_logs = full_session_messages[: end_index + 1]
                else:
                    truncated_logs = full_session_messages

                session_record = {
                    "session_id": f"logs_{len(breakdown[canonical_option]['logs']) + 1}",
                    "entries": truncated_logs,
                    "user_id": getattr(session, "user_id", None),
                    "user_type": session.user_type,
                    "is_complete": completed
                }

                breakdown[canonical_option]["logs"].append(session_record)
                breakdown[canonical_option]["selected_count"] += 1

                if completed:
                    breakdown[canonical_option]["completed_count"] += 1
                    completed_sessions.append(session_record)
                else:
                    breakdown[canonical_option]["incomplete_count"] += 1
                    incomplete_sessions.append(session_record)

                if session.user_type and session.user_type.lower() in ["new", "registered"]:
                    breakdown[canonical_option]["user_type"][session.user_type.lower()] += 1

                session_ids.append(session_record["session_id"])

        # Sort logs by latest message timestamp
        logs_sorted = sorted(
            breakdown[canonical_option]["logs"],
            key=lambda x: to_ist(x["entries"][-1]["timestamp"]) if x["entries"] else datetime.min,
            reverse=True
        )

        breakdown[canonical_option]["logs"] = logs_sorted

        # Pagination
        total_records = len(logs_sorted)
        total_pages = (total_records + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_logs = logs_sorted[start_idx:end_idx]

        formatted_data = []
        if total_records > 0:
            formatted_data.append({
                "option": canonical_option,
                "selected_count": breakdown[canonical_option]["selected_count"],
                "completed_count": breakdown[canonical_option]["completed_count"],
                "incomplete_count": breakdown[canonical_option]["incomplete_count"],
                "logs": paginated_logs,
                "user_type": breakdown[canonical_option]["user_type"]
            })

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_records": total_records,
            "data": formatted_data,
            "session_ids": session_ids,
            "completed_sessions": completed_sessions,
            "incomplete_sessions": incomplete_sessions
        })

    except Exception as e:
        print("Error in menu_analysis:", e)
        return jsonify({"error": "Something went wrong"}), 500

    finally:
        db.close()
