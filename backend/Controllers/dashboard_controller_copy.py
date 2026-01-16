from collections import defaultdict
from flask import json, jsonify, request
from Models.session_model import Session
from database import SessionLocal
from datetime import date, datetime, timedelta, timezone
# from sqlalchemy import func, cast, Date, extract
from sqlalchemy import and_

def get_session_counts():
    try:
        db = SessionLocal()
        queryset = db.query(Session)

        # Query params
        date_str = request.args.get("date")              # YYYY-MM-DD
        start_date_str = request.args.get("start_date")  # YYYY-MM-DD
        end_date_str = request.args.get("end_date")      # YYYY-MM-DD
        month_str = request.args.get("month")            # YYYY-MM
        division_name = request.args.get("division_name")  # new filter

        # Apply division filter if given
        if division_name:
            queryset = queryset.filter(Session.division_name == division_name)

        sessions = queryset.all()

        # Parse filters
        date_filter = None
        start_date = None
        end_date = None
        month_filter = None

        if date_str:
            date_filter = datetime.strptime(date_str, "%Y-%m-%d").date()
        elif start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        elif month_str:
            month_filter = datetime.strptime(month_str, "%Y-%m").date()

        # Time anchors (UTC)
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        today_utc = now.date()

        # Helper to normalize timestamp to UTC
        def to_utc(dt):
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt)  # handles tz if present
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        # Chatbot options
        chatbot_options = [
            "New Connection Application BRPL", "नया कनेक्शन आवेदन BRPL",
            "New Connection Status BRPL", "नए कनेक्शन की स्थिति BRPL",
            "Virtual Customer Care Centre (BYPL) / Connect Virtually (BRPL) BRPL",
            "वर्चुअल कस्टमर केयर सेंटर (BYPL) / वर्चुअली कनेक्ट करें (BRPL) BRPL",
            "Streetlight Complaint BRPL", "स्ट्रीटलाइट शिकायत BRPL",
            "FAQs BRPL", "सामान्य प्रश्न (FAQs) BRPL",
            "Branches Nearby BRPL", "नज़दीकी शाखाएँ BRPL",
            "Visually Impaired BRPL", "दृष्टिबाधित सहायता BRPL",
            "Select Another CA number BRPL", "कोई और सीए नंबर चुनें BRPL",
            "Change Language BRPL", "भाषा बदलें BRPL",
            "Meter Reading Schedule BRPL", "मीटर रीडिंग शेड्यूल BRPL",
            "Prepaid Meter - Check Balance / Recharge BRPL", "प्रीपेड मीटर - बैलेंस जांचें / रिचार्ज करें BRPL",
            "Consumption History BRPL", "खपत का इतिहास BRPL",
            "Duplicate Bill BRPL", "डुप्लिकेट बिल BRPL",
            "Payment Status BRPL", "भुगतान की स्थिति BRPL",
            "Payment History BRPL", "भुगतान इतिहास BRPL",
            "Opt for e-bill BRPL", "ई-बिल के लिए ऑप्ट-इन करें BRPL",
            "Register Complaint BRPL", "शिकायत दर्ज करें BRPL",
            "Complaint Status (NCC) BRPL", "शिकायत की स्थिति (NCC) BRPL"
        ]

        # Allowed months
        allowed_months = set()
        if date_filter:
            allowed_months.add(date_filter.strftime("%Y-%m"))
        elif start_date and end_date:
            m = date(start_date.year, start_date.month, 1)
            end_m = date(end_date.year, end_date.month, 1)
            while m <= end_m:
                allowed_months.add(m.strftime("%Y-%m"))
                m = date(m.year + 1, 1, 1) if m.month == 12 else date(m.year, m.month + 1, 1)
        elif month_filter:
            allowed_months.add(month_filter.strftime("%Y-%m"))
        else:
            allowed_months.add(now.strftime("%Y-%m"))

        # Counters
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        monthly_counts = defaultdict(int)
        weekly_counts = defaultdict(int)   # NEW - for monthly filter weeks

        # For peak time tracking
        hourly_breakdown = defaultdict(int)
        daily_breakdown = defaultdict(int)
        monthly_breakdown = defaultdict(int)

        last_hour_key = now.strftime("%Y-%m-%d %H:00")

        for session in sessions:
            for chat in getattr(session, "chat", []) or []:
                ts_utc = to_utc(chat.get("timestamp"))
                ts_date = ts_utc.date()
                month_key = ts_utc.strftime("%Y-%m")
                day_key = ts_utc.strftime("%Y-%m-%d")
                hour_key = ts_utc.strftime("%Y-%m-%d %H:00")

                query = chat.get("query", "") or ""
                answer = chat.get("answer", "")
                if isinstance(answer, dict):
                    answer_text = " ".join(answer.get("heading", []) + answer.get("buttons", []))
                else:
                    answer_text = str(answer)
                text_to_check = f"{query} {answer_text}"

                if not any(opt in text_to_check for opt in chatbot_options):
                    continue

                # Monthly
                if month_key in allowed_months:
                    monthly_counts[month_key] += 1
                    monthly_breakdown[month_key] += 1

                    # if user asked for month filter -> calculate week breakdown
                    if month_filter and ts_date.strftime("%Y-%m") == month_filter.strftime("%Y-%m"):
                        # Week of month (1–4)
                        week_num = ((ts_date.day - 1) // 7) + 1
                        if week_num > 4:   # force week4 for days beyond 28th
                            week_num = 4
                        weekly_counts[f"week{week_num}"] += 1

                # Daily
                if date_filter:
                    if ts_date == date_filter:
                        daily_counts[day_key] += 1
                        hourly_breakdown[hour_key] += 1
                elif start_date and end_date:
                    if start_date <= ts_date <= end_date:
                        daily_counts[day_key] += 1
                        daily_breakdown[day_key] += 1
                elif month_filter:
                    if ts_date.strftime("%Y-%m") == month_filter.strftime("%Y-%m"):
                        daily_counts[day_key] += 1
                        daily_breakdown[day_key] += 1
                else:
                    if ts_date == today_utc:
                        daily_counts[day_key] += 1
                        hourly_breakdown[hour_key] += 1
                        daily_breakdown[day_key] += 1

                # Hourly (last 60 minutes)
                if ts_utc >= one_hour_ago:
                    hourly_counts[last_hour_key] += 1

        # Determine peak time
        peak_time = None
        if date_filter:
            if hourly_breakdown:
                peak_hour = max(hourly_breakdown, key=hourly_breakdown.get)
                start_hour = datetime.strptime(peak_hour, "%Y-%m-%d %H:00")
                peak_time = f"{start_hour.strftime('%H:00')} - {(start_hour + timedelta(hours=1)).strftime('%H:00')}"
        elif start_date and end_date:
            if daily_breakdown:
                peak_day = max(daily_breakdown, key=daily_breakdown.get)
                peak_time = peak_day
        elif month_filter:
            if daily_breakdown:
                peak_day = max(daily_breakdown, key=daily_breakdown.get)
                peak_time = peak_day
        else:
            # Default: today's peak hour + current month's peak day
            if hourly_breakdown:
                peak_hour = max(hourly_breakdown, key=hourly_breakdown.get)
                start_hour = datetime.strptime(peak_hour, "%Y-%m-%d %H:00")
                peak_time = f"{start_hour.strftime('%H:00')} - {(start_hour + timedelta(hours=1)).strftime('%H:00')}"
            elif daily_breakdown:
                peak_time = max(daily_breakdown, key=daily_breakdown.get)

        hourly_out = {}
        if hourly_counts:
            hourly_out[last_hour_key] = hourly_counts[last_hour_key]

        # Format monthly output with weeks if month filter is applied
        monthly_out = dict(monthly_counts)
        if month_filter:
            month_key = month_filter.strftime("%Y-%m")
            monthly_out = {
                "total": monthly_counts.get(month_key, 0),
                "weeks": {
                    "week1": weekly_counts.get("week1", 0),
                    "week2": weekly_counts.get("week2", 0),
                    "week3": weekly_counts.get("week3", 0),
                    "week4": weekly_counts.get("week4", 0),
                }
            }

        return jsonify({
            "daily": dict(daily_counts),
            "hourly": hourly_out,
            "monthly": monthly_out,
            "peak_time": peak_time,
            "division": division_name if division_name else "All"
        })

    except Exception as e:
        print("Error in get_session_counts:", e)
        return jsonify({"error": "Something went wrong"}), 500
    
    finally:
        db.close()





def interaction_breakdown():
    try:
        db = SessionLocal()
        sessions = db.query(Session).all()

        # Fetch query parameters
        date_str = request.args.get("date")  # YYYY-MM-DD
        start_date_str = request.args.get("start_date")  # YYYY-MM-DD
        end_date_str = request.args.get("end_date")      # YYYY-MM-DD
        month_str = request.args.get("month")  # YYYY-MM
        last_hour = request.args.get("last_hour", "false").lower() == "true"
        division_name = request.args.get("division_name")
        page = int(request.args.get("page", 1))
        per_page = 5  # records per page

        # Use timezone-aware UTC datetime
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # Parse date filters
        date_filter = None
        start_date = None
        end_date = None
        month_filter = None
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

        # chatbot options
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

        completion_messages = [
            "Thank you. Would you like to return to the main menu? Select Yes or type ‘menu’ or ‘hi’ to continue.",
            "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए ‘हाँ’, ‘menu’ या ‘hi’ टाइप करें।"
        ]

        breakdown = {opt: {"count": 0, "logs": []}
                     for group in chatbot_options.values() for opt in group}

        option_keys = list(breakdown.keys())
        option_keys_lower = [ok.lower() for ok in option_keys]

        # Sort sessions: latest first
        sessions = sorted(
            sessions,
            key=lambda s: max(
                [
                    datetime.fromisoformat(chat.get("timestamp")).astimezone(timezone.utc)
                    for chat in (s.chat or [])
                    if "timestamp" in chat
                ] or [datetime.min.replace(tzinfo=timezone.utc)]
            ),
            reverse=True
        )

        for session in sessions:
            if division_name and getattr(session, "division_name", None) != division_name:
                continue
            if not session.chat:
                continue

            try:
                timestamps = [
                    datetime.fromisoformat(chat.get("timestamp")).astimezone(timezone.utc)
                    if "timestamp" in chat else None
                    for chat in session.chat
                ]
                timestamps = [ts for ts in timestamps if ts is not None]
            except Exception:
                continue

            if not timestamps:
                continue

            session_start = min(timestamps)
            session_end = max(timestamps)
            session_date = session_start.date()

            # Apply filters
            if last_hour and session_end < one_hour_ago:
                continue
            elif date_filter and session_date != date_filter:
                continue
            elif start_date and end_date and not (start_date <= session_date <= end_date):
                continue
            elif month_str and not (month_start <= session_date <= month_end):
                continue

            active_option = None
            current_group_key = None
            current_group_messages = []

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

                try:
                    if isinstance(answer, dict):
                        answer_text = json.dumps(answer, ensure_ascii=False)
                    else:
                        answer_text = str(answer)
                except Exception:
                    answer_text = str(answer)

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
                    current_group_messages = [{
                        "query": query,
                        "answer": answer,
                        "timestamp": timestamp
                    }]
                else:
                    if active_option:
                        current_group_messages.append({
                            "query": query,
                            "answer": answer,
                            "timestamp": timestamp
                        })

                for cm in completion_messages:
                    if cm in query or cm in answer_text:
                        finalize_group()
                        break

            if current_group_messages:
                last_chat = current_group_messages[-1]
                last_answer_text = (
                    json.dumps(last_chat["answer"], ensure_ascii=False)
                    if isinstance(last_chat["answer"], dict)
                    else str(last_chat["answer"])
                )
                if any(cm in last_answer_text or cm in last_chat["query"] for cm in completion_messages):
                    finalize_group()

        # Transform breakdown with latest logs first
        formatted_data = []
        for option, details in breakdown.items():
            if details["count"] > 0:
                sorted_logs = sorted(
                    details["logs"],
                    key=lambda log: max(
                        [
                            datetime.fromisoformat(entry["timestamp"]).astimezone(timezone.utc)
                            for entry in log["entries"]
                            if "timestamp" in entry
                        ] or [datetime.min.replace(tzinfo=timezone.utc)]
                    ),
                    reverse=True
                )
                formatted_data.append({
                    "option": option,
                    "logs": sorted_logs
                })

        # Pagination
        total_records = len(formatted_data)
        total_pages = (total_records + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_data = formatted_data[start_idx:end_idx]

        return jsonify({
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_records": total_records,
            "data": paginated_data
        })

    except Exception as e:
        print("Error in interaction breakdown:", e)
        return jsonify({"error": "Something went wrong"}), 500

    finally:
        db.close()

    

def average_interaction_time():
    try:
        db = SessionLocal()

        # Fetch query parameters
        date_str = request.args.get("date")  # YYYY-MM-DD
        start_date_str = request.args.get("start_date")  # YYYY-MM-DD
        end_date_str = request.args.get("end_date")      # YYYY-MM-DD
        month_str = request.args.get("month")  # YYYY-MM
        last_hour = request.args.get("last_hour", "false").lower() == "true"  # ?last_hour=true
        division_name = request.args.get("division_name")

        # Use timezone-aware UTC datetime
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        # Parse filters
        date_filter = None
        start_date = None
        end_date = None
        month_filter = None
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

        # Fetch sessions
        query = db.query(Session)
        if division_name:
            query = query.filter(Session.division_name == division_name)
        sessions = query.all()

        durations = []
        weekly_durations = defaultdict(list)  # store durations per week if month filter is applied

        for session in sessions:
            if session.chat and len(session.chat) >= 1:
                try:
                    timestamps = [
                        datetime.fromisoformat(chat["timestamp"]).astimezone(timezone.utc)
                        for chat in session.chat if "timestamp" in chat
                    ]
                except Exception:
                    continue

                if not timestamps:
                    continue

                start = min(timestamps)
                end = max(timestamps)
                duration = (end - start).total_seconds()
                session_date = start.date()

                # Apply filters
                if last_hour:
                    if start >= one_hour_ago or end >= one_hour_ago:
                        durations.append(duration)
                elif date_filter:
                    if session_date == date_filter:
                        durations.append(duration)
                elif start_date and end_date:
                    if start_date <= session_date <= end_date:
                        durations.append(duration)
                elif month_filter:
                    if month_start <= session_date <= month_end:
                        durations.append(duration)
                        # also assign to week bucket
                        week_num = ((session_date.day - 1) // 7) + 1
                        if week_num > 4:
                            week_num = 4
                        weekly_durations[f"week{week_num}"].append(duration)
                else:
                    durations.append(duration)

        # Helper: format seconds -> "Xm Ys"
        def format_duration(seconds):
            minutes = int(seconds // 60)
            sec = int(seconds % 60)
            if minutes > 0:
                return f"{minutes} minutes {sec} seconds" if sec > 0 else f"{minutes} minutes"
            else:
                return f"{sec} seconds"

        result = {}
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
                "division_name": division_name if division_name else "all"
            }

            # Add weekly averages if month filter applied
            if month_filter:
                result["weekly"] = {
                    "week1": format_duration(sum(weekly_durations["week1"]) / len(weekly_durations["week1"])) if weekly_durations["week1"] else "0 seconds",
                    "week2": format_duration(sum(weekly_durations["week2"]) / len(weekly_durations["week2"])) if weekly_durations["week2"] else "0 seconds",
                    "week3": format_duration(sum(weekly_durations["week3"]) / len(weekly_durations["week3"])) if weekly_durations["week3"] else "0 seconds",
                    "week4": format_duration(sum(weekly_durations["week4"]) / len(weekly_durations["week4"])) if weekly_durations["week4"] else "0 seconds",
                }

        else:
            result = {
                "message": "No sessions found for the given filters.",
                "division_name": division_name if division_name else "all"
            }

            # Still include weeks if month filter
            if month_filter:
                result["weekly"] = {
                    "week1": "0 seconds",
                    "week2": "0 seconds",
                    "week3": "0 seconds",
                    "week4": "0 seconds"
                }

        return jsonify(result)

    except Exception as e:
        print("Error in average_interaction_time:", e)
        return jsonify({"error": "Something went wrong"}), 500
    
    finally:
        db.close()



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

        # Build filters
        filters = []
        now = datetime.utcnow()

        month_start = None
        month_end = None
        month_filter = False

        if last_hour:
            filters.append(Session.created_at >= now - timedelta(hours=1))
        elif date_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                filters.append(and_(
                    Session.created_at >= datetime.combine(date, datetime.min.time()),
                    Session.created_at <= datetime.combine(date, datetime.max.time())
                ))
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
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

        # Add division filter
        if division_name:
            filters.append(Session.division_name == division_name)

        # Query sessions
        if filters:
            sessions = db.query(Session).filter(*filters).all()
        else:
            sessions = db.query(Session).all()

        total_sessions = len(sessions)
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


        thank_you_messages = [
            "Thank you. Would you like to return to the main menu? Select Yes or type ‘menu’ or ‘hi’ to continue.",
            "धन्यवाद। क्या आप मुख्य मेनू पर वापस जाना चाहेंगे? जारी रखने के लिए ‘हाँ’, ‘menu’ या ‘hi’ टाइप करें।"
        ]

        for s in sessions:
            if not s.chat or len(s.chat) == 0:
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

        response = {
            "total_sessions": total_sessions,
            "completed_chats": completed_count,
            "left_chats": left_count,
            "division_name": division_name if division_name else "all"
        }

        if month_filter:
            response["weekly"] = weekly_stats

        return jsonify(response)

    except Exception as e:
        print("Error in chat_status:", e)
        return jsonify({"error": "Something went wrong"}), 500

    finally:
        db.close()



    

def count_opt_for_ebill():
    try:
        db = SessionLocal()
        all_sessions = db.query(Session).all()

        opt_for_ebill_success_texts = [
            "You’ve successfully opted for E-Bill. Future bills will be emailed to you.",
            "आपने सफलतापूर्वक ई-बिल के लिए पंजीकरण कर लिया है। भविष्य के बिल आपके ईमेल पर भेजे जाएंगे।"
        ]

        opt_for_ebill_click_texts = [
            "Opt for e-bill BRPL",
            "ई-बिल के लिए ऑप्ट-इन करें BRPL"
        ]

        opt_for_ebill_count = 0  # users who successfully opted in
        users_opted_ebill = set()

        opt_for_ebill_click_count = 0  # total clicks on the option
        users_clicked_ebill = set()

        for session in all_sessions:
            chat_data = session.chat
            if not chat_data:
                continue

            # Decode JSON string if needed
            if isinstance(chat_data, str):
                import json
                try:
                    chat_data = json.loads(chat_data)
                except json.JSONDecodeError:
                    print(f"Invalid JSON for session {session.user_id}: {chat_data}")
                    continue

            if not isinstance(chat_data, list):
                continue

            for entry in chat_data:
                if not isinstance(entry, dict):
                    continue

                # --- Check if user clicked "Opt for e-bill" option ---
                query_text = entry.get("query", "")
                if query_text in opt_for_ebill_click_texts:
                    opt_for_ebill_click_count += 1
                    users_clicked_ebill.add(session.user_id)

                # --- Check if user successfully opted for e-bill ---
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
                    break  # only count success once per user

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



def dashboard_complaint_status():
    try:
        db = SessionLocal()
        all_sessions = db.query(Session).all()

        total_complaints = 0
        resolved_complaints = 0
        unique_users_with_complaints = set()

        for session in all_sessions:
            # if session.chat:
            #     for entry in session.chat:
            complaint_no = session.complain_no
            status = session.complain_status

            # Check if complaint_no is present
            if complaint_no:
                print(complaint_no, "================================")
                total_complaints += 1
                unique_users_with_complaints.add(session.user_id)

                # Check if status is resolved
                if status == "resolved":
                    resolved_complaints += 1

        response = {
            "stats": {
                "total_complaints": total_complaints,
                "resolved_complaints": resolved_complaints,
                "unique_users_with_complaints": len(unique_users_with_complaints)
            }
        }
        return jsonify(response)

    except Exception as e:
        print("Dashboard Complaint Status Error:", e)
        return jsonify({'error': 'Something went wrong'}), 500
