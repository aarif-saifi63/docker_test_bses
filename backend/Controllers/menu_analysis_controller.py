from flask import request, jsonify
from datetime import datetime, timedelta
import json
from Models.session_model import Session
from database import SessionLocal
from pytz import timezone as pytz_timezone
from dotenv import load_dotenv
import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file
load_dotenv()

flask_url = os.getenv('BACKEND_URL')

def menu_analysis():
    db = None
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
        menu_option = request.args.get("menu_option")

        page = max(int(request.args.get("page", 1)), 1)
        per_page = int(request.args.get("per_page", 5))

        logger.info(f"Menu analysis request - menu_option: {menu_option}, filters: division={division_name}, ca={ca_number}, tel={tel_no}, source={source}")

        # --- Fetch dynamic submenus ---
        try:
            submenu_url = f"{flask_url}/submenus"
            submenu_response = requests.get(submenu_url, timeout=10)
            submenu_response.raise_for_status()
            submenu_data = submenu_response.json().get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch submenus: {str(e)}")
            return jsonify({"error": "Failed to fetch menu options"}), 500

        # --- Build canonical option map dynamically ---
        # Group submenus by submenu_id (NOT menu_id) to pair English & Hindi equivalents
        # menu_id represents parent category, submenu_id represents individual options
        grouped_submenus = {}
        for item in submenu_data:
            submenu_id = item.get("id")  # Use submenu's unique ID, not parent menu_id
            name = item.get("name")
            lang = item.get("lang")
            if submenu_id is None or not name:
                continue
            # Append " BRPL" to every menu/submenu name
            name_with_brpl = f"{name.strip()} BRPL"
            grouped_submenus.setdefault(submenu_id, {"en": [], "hi": []})
            grouped_submenus[submenu_id][lang].append(name_with_brpl)

        # Create option_map for each unique submenu
        menu_groups = []
        for submenu_id, group in grouped_submenus.items():
            english_variants = group.get("en", [])
            hindi_variants = group.get("hi", [])

            # Use English name as canonical if available, otherwise use first available
            if english_variants:
                canonical_name = english_variants[0]
            elif hindi_variants:
                canonical_name = hindi_variants[0]
            else:
                continue

            all_variants = english_variants + hindi_variants
            menu_groups.append((canonical_name, all_variants))

        # Flatten to canonical lookup
        option_map = {v.lower(): canonical for canonical, variants in menu_groups for v in variants}

        logger.info(f"Built option map with {len(option_map)} variants for {len(menu_groups)} menu groups")

        # --- Validate menu option ---
        if not menu_option:
            return jsonify({"error": "Missing required parameter: menu_option"}), 400

        if menu_option.lower() not in option_map:
            logger.warning(f"Invalid menu_option: {menu_option}")
            available_options = list(set(option_map.values()))
            return jsonify({
                "error": "Invalid menu_option",
                "message": f"The menu option '{menu_option}' is not valid",
                "available_options": available_options[:10]  # Show first 10 as examples
            }), 400

        canonical_option = option_map[menu_option.lower()]
        logger.info(f"Canonical option: {canonical_option}")

        # --- Timezone setup ---
        ist = pytz_timezone('Asia/Kolkata')
        now = datetime.now(ist)
        one_hour_ago = now - timedelta(hours=1)

        # --- Date filters ---
        date_filter = None
        start_date = None
        end_date = None
        month_start = None
        month_end = None

        if date_str:
            try:
                date_filter = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        elif start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                if start_date > end_date:
                    return jsonify({"error": "start_date must be before or equal to end_date"}), 400
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        elif month_str:
            try:
                month_filter = datetime.strptime(month_str, "%Y-%m").date()
                month_start = month_filter.replace(day=1)
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
            except ValueError:
                return jsonify({"error": "Invalid month format. Use YYYY-MM"}), 400

        # --- Completion messages ---
        completion_messages = [
            "Thank you. Would you like to return to the main menu? Select Yes or type 'menu' or 'hi' to continue.",
            "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए 'हाँ', 'menu' या 'hi' टाइप करें।"
        ]

        # --- Build database query with filters ---
        query = db.query(Session)

        if division_name:
            query = query.filter(Session.division_name == division_name)
        if ca_number:
            query = query.filter(Session.ca_number == ca_number)
        if tel_no:
            query = query.filter(Session.tel_no == tel_no)
        if source:
            query = query.filter(Session.source == source)

        # Filter out sessions without chat
        query = query.filter(Session.chat.isnot(None))

        sessions = query.all()
        logger.info(f"Found {len(sessions)} sessions matching basic filters")

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
                try:
                    dt = datetime.fromisoformat(dt)
                except ValueError:
                    # Handle alternative formats if needed
                    return None
            if dt.tzinfo is None:
                dt = ist.localize(dt)
            else:
                dt = dt.astimezone(ist)
            return dt

        # Get all variants for the canonical option
        selected_option_variants = [v for v, canonical in option_map.items() if canonical == canonical_option]
        logger.info(f"Searching for variants: {selected_option_variants}")

        session_ids = []
        completed_sessions = []
        incomplete_sessions = []

        for session in sessions:
            if not session.chat or not isinstance(session.chat, list):
                continue

            try:
                timestamps = []
                for chat in session.chat:
                    if "timestamp" in chat:
                        ts = to_ist(chat.get("timestamp"))
                        if ts:
                            timestamps.append(ts)
            except Exception as e:
                logger.warning(f"Error parsing timestamps for session {session.id}: {str(e)}")
                continue

            if not timestamps:
                continue

            # Sort chat by timestamp
            try:
                session.chat.sort(key=lambda x: to_ist(x.get("timestamp")) if x.get("timestamp") else datetime.min, reverse=False)
            except Exception as e:
                logger.warning(f"Error sorting chat for session {session.id}: {str(e)}")
                continue

            session_start = min(timestamps)
            session_end = max(timestamps)
            session_date = session_start.date()

            # Apply date filters
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
                query_text = chat.get("query", "") or ""
                answer = chat.get("answer", "") or ""
                timestamp = chat.get("timestamp", "")
                user_id = getattr(session, "user_id", None)

                # Convert answer to string for searching
                answer_text = json.dumps(answer, ensure_ascii=False) if isinstance(answer, dict) else str(answer)
                combined = (query_text + " " + answer_text).lower()

                log_entry = {
                    "user_id": user_id,
                    "query": query_text,
                    "answer": answer,
                    "timestamp": timestamp
                }

                full_session_messages.append(log_entry)

                # Detect menu option - check if any variant appears as a whole word/phrase
                if not matched:
                    for variant in selected_option_variants:
                        # Use word boundary search for better matching
                        if variant in combined:
                            matched = True
                            logger.debug(f"Matched variant '{variant}' in session {session.id}")
                            break

                # Detect completion
                if matched:
                    for cm in completion_messages:
                        if cm in query_text or cm in answer_text:
                            completed = True
                            end_index = idx
                            break
                if completed:
                    break

            if matched:
                # Truncate logs at completion point if completed
                if completed:
                    truncated_logs = full_session_messages[: end_index + 1]
                else:
                    truncated_logs = full_session_messages

                session_record = {
                    "session_id": f"logs_{len(breakdown[canonical_option]['logs']) + 1}",
                    "original_session_id": session.id,
                    "entries": truncated_logs,
                    "user_id": getattr(session, "user_id", None),
                    "user_type": session.user_type,
                    "is_complete": completed,
                    "ca_number": session.ca_number,
                    "tel_no": session.tel_no,
                    "division_name": session.division_name,
                    "source": session.source
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
            key=lambda x: to_ist(x["entries"][-1]["timestamp"]) if x["entries"] and to_ist(x["entries"][-1]["timestamp"]) else datetime.min,
            reverse=True
        )

        breakdown[canonical_option]["logs"] = logs_sorted

        logger.info(f"Found {len(logs_sorted)} sessions with selected menu option")

        # Pagination
        total_records = len(logs_sorted)
        total_pages = (total_records + per_page - 1) // per_page if per_page > 0 else 1
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
            "filters_applied": {
                "menu_option": canonical_option,
                "division_name": division_name,
                "ca_number": ca_number,
                "tel_no": tel_no,
                "source": source,
                "date": date_str,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "month": month_str,
                "last_hour": last_hour
            }
        }), 200

    except Exception as e:
        logger.error(f"Error in menu_analysis: {str(e)}", exc_info=True)
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500

    finally:
        if db:
            db.close()
