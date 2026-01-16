from datetime import datetime, timedelta, timezone
from datetime import time
from flask import jsonify, request
from collections import defaultdict, Counter
from sqlalchemy import func, or_
from Controllers.api_key_master_controller import IST
from Models.user_details_model import UserDetails
from database import SessionLocal
from Models.feedback_question_model import FeedbackQuestion
from Models.feedback_response_model import FeedbackResponse 



# working code

def get_feedback_summary_and_analytics():
    """
    Fetch feedback summary, analytics, and logs with optional date & language filters.
    Language filter: English or Hindi (based on FeedbackQuestion.question_type)
    """
    try:
        db = SessionLocal()

        # --- Parse filters ---
        start_date_str = request.args.get("start_date")  # YYYY-MM-DD
        end_date_str = request.args.get("end_date")      # YYYY-MM-DD
        language = request.args.get("language")          # Optional: "English" or "Hindi"

        start_dt = None
        end_dt = None

        # --- Handle date range ---
        if start_date_str or end_date_str:
            base_date_str = start_date_str or end_date_str
            base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()

            start_naive = datetime.combine(base_date, time.min)
            start_dt = IST.localize(start_naive)

            end_date_to_use = end_date_str or start_date_str or base_date_str
            end_date = datetime.strptime(end_date_to_use, "%Y-%m-%d").date()
            end_naive = datetime.combine(end_date, time.max)
            end_dt = IST.localize(end_naive)

        # --- Fetch questions of desired language & acceptance condition ---
        question_query = db.query(FeedbackQuestion).filter(
            or_(
                FeedbackQuestion.feedback_acceptance == None,
                func.lower(FeedbackQuestion.feedback_acceptance) != "true"
            )
        )
        if language and language in ("English", "Hindi"):
            question_query = question_query.filter(FeedbackQuestion.question_type == language)

        questions = question_query.all()
        valid_question_texts = {q.question for q in questions}
        valid_question_ids = {q.id for q in questions}
        total_questions = len(questions)

        # --- Fetch and filter responses ---
        response_query = db.query(FeedbackResponse)
        if start_dt:
            response_query = response_query.filter(FeedbackResponse.created_at >= start_dt)
        if end_dt:
            response_query = response_query.filter(FeedbackResponse.created_at <= end_dt)
        
        all_responses = response_query.all()

        responses = []
        for resp in all_responses:
            has_valid_answer = any(
                qa.get("question") in valid_question_texts or
                (qa.get("question_id") and int(qa.get("question_id")) in valid_question_ids)
                for qa in resp.response
            )
            if has_valid_answer:
                responses.append(resp)

        total_feedbacks = len(responses)

        # --- Per-question analytics ---
        question_stats = defaultdict(Counter)
        question_options_map = {}
        for q in questions:
            question_options_map[q.question] = {
                "question_id": q.id,
                "question_type": q.question_type,
                "options": q.options,
            }

        for resp in responses:
            for qa in resp.response:
                q_text = qa.get("question")
                a_text = qa.get("answer")
                if q_text in valid_question_texts and a_text:
                    question_stats[q_text][a_text] += 1

        analytics = []
        for q_text, answers_counter in question_stats.items():
            q_info = question_options_map.get(q_text, {})
            analytics.append({
                "question_id": q_info.get("question_id"),
                "question": q_text,
                "question_type": q_info.get("question_type"),
                "options": q_info.get("options"),
                "answers": [{"option": option, "count": count} for option, count in answers_counter.items()],
                "total_responses": sum(answers_counter.values())
            })

        # --- Daily feedback trend: only date and count ---
        date_counts = Counter(resp.created_at.date().isoformat() for resp in responses)
        trend_data = [
            {"date": date, "count": count}
            for date, count in sorted(date_counts.items())
        ]

        # --- Most / Least feedback dates ---
        most_feedbacks_date = max(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)
        least_feedbacks_date = min(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)

        # --- Feedback logs ---
        feedback_logs = [
            {
                "feedback_id": resp.id,
                "created_at": resp.created_at.isoformat(),
                "ca_number": getattr(resp, 'ca_number', None),
                "user_type": getattr(resp, 'user_type', None),
                "response": resp.response
            }
            for resp in responses
        ]

        summary = {
            "total_questions": total_questions,
            "total_feedbacks": total_feedbacks,
            "most_feedbacks_on": {"date": most_feedbacks_date[0], "count": most_feedbacks_date[1]},
            "least_feedbacks_on": {"date": least_feedbacks_date[0], "count": least_feedbacks_date[1]},
        }

        return jsonify(
            status=True,
            message="Feedback summary, analytics, and logs fetched successfully",
            summary=summary,
            analytics=analytics,
            trend_data=trend_data,
            feedback_logs=feedback_logs
        ), 200

    except Exception as e:
        return jsonify(status=False, message=f"Error: {str(e)}"), 500

    finally:
        db.close()


# def get_feedback_summary_and_analytics():
#     """
#     Enhanced analytics with:
#     - Skipping feedback_acceptance=True questions
#     - Full-day end_date filter
#     - User category and CA number in logs
#     - Oct–Nov 2025 range check
#     """
#     try:
#         db = SessionLocal()

#         # --- Parse filters ---
#         start_date_str = request.args.get("start_date")
#         end_date_str = request.args.get("end_date")

#         start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=IST) if start_date_str else None
#         end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=IST) if end_date_str else None
#         if end_dt:
#             end_dt = end_dt + timedelta(hours=23, minutes=59, seconds=59)

#         # --- Static date check for missing feedbacks ---
#         check_start = datetime(2025, 10, 1, tzinfo=IST)
#         check_end = datetime(2025, 11, 2, 23, 59, 59, tzinfo=IST)

#         # --- Fetch filtered responses ---
#         response_query = db.query(FeedbackResponse)
#         if start_dt:
#             response_query = response_query.filter(FeedbackResponse.created_at >= start_dt)
#         if end_dt:
#             response_query = response_query.filter(FeedbackResponse.created_at <= end_dt)
#         responses = response_query.all()

#         # --- Question Filtering (exclude feedback_acceptance=True) ---
#         question_ids = {
#             qa["question_id"]
#             for resp in responses
#             for qa in resp.response
#             if "question_id" in qa
#         }

#         question_query = db.query(FeedbackQuestion)
#         if question_ids:
#             question_query = question_query.filter(
#                 FeedbackQuestion.id.in_(question_ids),
#                 (FeedbackQuestion.feedback_acceptance.is_(None)) |
#                 (FeedbackQuestion.feedback_acceptance == "false") |
#                 (FeedbackQuestion.feedback_acceptance == "False")
#             )
#         questions = question_query.all()
#         valid_question_ids = {q.id for q in questions}

#         # --- Filter responses based on valid question IDs ---
#         filtered_responses = []
#         for resp in responses:
#             filtered_qa = [qa for qa in resp.response if qa.get("question_id") in valid_question_ids]
#             if filtered_qa:
#                 resp.response = filtered_qa
#                 filtered_responses.append(resp)

#         # --- Basic counts ---
#         total_questions = len(questions)
#         total_feedbacks = len(filtered_responses)

#         # --- Per-question analytics ---
#         question_stats = defaultdict(Counter)
#         question_options_map = {}

#         for q in questions:
#             question_options_map[q.question] = {
#                 "question_id": q.id,
#                 "question_type": q.question_type,
#                 "options": q.options,
#             }

#         for resp in filtered_responses:
#             for qa in resp.response:
#                 q_text = qa.get("question")
#                 a_text = qa.get("answer")
#                 if q_text and a_text:
#                     question_stats[q_text][a_text] += 1

#         analytics = [
#             {
#                 "question_id": q_info.get("question_id"),
#                 "question": q_text,
#                 "question_type": q_info.get("question_type"),
#                 "options": q_info.get("options"),
#                 "answers": [{"option": opt, "count": cnt} for opt, cnt in answers_counter.items()],
#                 "total_responses": sum(answers_counter.values())
#             }
#             for q_text, answers_counter in question_stats.items()
#             if (q_info := question_options_map.get(q_text))
#         ]

#         # --- Trend data ---
#         date_counts = Counter(resp.created_at.date().isoformat() for resp in filtered_responses)
#         trend_data = [{"date": date, "count": count} for date, count in sorted(date_counts.items())]

#         most_feedbacks_date = max(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)
#         least_feedbacks_date = min(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)

#         # --- Include user data in logs ---
#         feedback_logs = []
#         for resp in filtered_responses:
#             user = db.query(UserDetails).filter_by(id=resp.user_id).first()
#             feedback_logs.append({
#                 "feedback_id": resp.id,
#                 "created_at": resp.created_at.isoformat(),
#                 "user_type": user.user_type if user else None,
#                 "ca_number": user.ca_number if user else None,
#                 "response": resp.response
#             })

#         # --- Check if data exists between 2025-10-01 and 2025-11-02 ---
#         oct_nov_data_exists = (
#             db.query(FeedbackResponse)
#             .filter(FeedbackResponse.created_at >= check_start)
#             .filter(FeedbackResponse.created_at <= check_end)
#             .first()
#             is not None
#         )

#         summary = {
#             "total_questions": total_questions,
#             "total_feedbacks": total_feedbacks,
#             "most_feedbacks_on": {"date": most_feedbacks_date[0], "count": most_feedbacks_date[1]},
#             "least_feedbacks_on": {"date": least_feedbacks_date[0], "count": least_feedbacks_date[1]},
#             "data_exists_in_oct_nov_range": oct_nov_data_exists,
#         }

#         return jsonify(
#             status=True,
#             message="Feedback summary, analytics, and logs fetched successfully",
#             summary=summary,
#             analytics=analytics,
#             trend_data=trend_data,
#             feedback_logs=feedback_logs
#         ), 200

#     except Exception as e:
#         return jsonify(status=False, message=f"Error: {str(e)}"), 500

#     finally:
#         db.close()



# def get_feedback_summary_and_analytics():
#     """
#     Enhanced feedback analytics:
#     - Excludes questions with feedback_acceptance=True
#     - Includes user_type & ca_number from FeedbackResponse
#     - Handles full-day date filtering correctly
#     - Normalizes timezone to match DB (UTC-safe)
#     - Checks for data between Oct–Nov 2025
#     """
#     try:
#         db = SessionLocal()

#         # --- Parse and normalize date filters ---
#         start_date_str = request.args.get("start_date")
#         end_date_str = request.args.get("end_date")

#         start_dt = None
#         end_dt = None

#         if start_date_str:
#             start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
#         if end_date_str:
#             # include full day till 23:59:59
#             end_dt = datetime.strptime(end_date_str, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)

#         # Convert to UTC-safe naive datetime for DB comparison
#         if start_dt:
#             start_dt = IST.localize(start_dt).astimezone(timezone.utc).replace(tzinfo=None)
#         if end_dt:
#             end_dt = IST.localize(end_dt).astimezone(timezone.utc).replace(tzinfo=None)

#         # --- Define fixed check range (Oct–Nov 2025) ---
#         check_start = datetime(2025, 10, 1, tzinfo=IST).astimezone(timezone.utc).replace(tzinfo=None)
#         check_end = datetime(2025, 11, 2, 23, 59, 59, tzinfo=IST).astimezone(timezone.utc).replace(tzinfo=None)

#         # --- Fetch filtered responses ---
#         response_query = db.query(FeedbackResponse)
#         if start_dt:
#             response_query = response_query.filter(FeedbackResponse.created_at >= start_dt)
#         if end_dt:
#             response_query = response_query.filter(FeedbackResponse.created_at <= end_dt)
#         responses = response_query.all()

#         # --- Debug log ---
#         print(f"[DEBUG] Start filter: {start_dt}, End filter: {end_dt}")
#         if responses:
#             print(f"[DEBUG] Sample created_at from DB: {responses[0].created_at}")

#         # --- Extract question IDs from responses ---
#         question_ids = {
#             qa.get("question_id")
#             for resp in responses
#             for qa in (resp.response or [])
#             if qa.get("question_id")
#         }

#         # --- Fetch valid questions (exclude feedback_acceptance=True) ---
#         question_query = db.query(FeedbackQuestion)
#         if question_ids:
#             question_query = question_query.filter(
#                 FeedbackQuestion.id.in_(question_ids),
#                 (FeedbackQuestion.feedback_acceptance.is_(None)) |
#                 (FeedbackQuestion.feedback_acceptance == "false") |
#                 (FeedbackQuestion.feedback_acceptance == "False")
#             )
#         questions = question_query.all()
#         valid_question_ids = {q.id for q in questions}

#         # --- Filter responses to only include valid question answers ---
#         filtered_responses = []
#         for resp in responses:
#             filtered_qa = [qa for qa in (resp.response or []) if qa.get("question_id") in valid_question_ids]
#             if filtered_qa:
#                 resp.response = filtered_qa
#                 filtered_responses.append(resp)

#         # --- Basic counts ---
#         total_questions = len(questions)
#         total_feedbacks = len(filtered_responses)

#         # --- Prepare question info map ---
#         question_info_map = {
#             q.question: {
#                 "question_id": q.id,
#                 "question_type": q.question_type,
#                 "options": q.options,
#             }
#             for q in questions
#         }

#         # --- Build analytics per question ---
#         question_stats = defaultdict(Counter)
#         for resp in filtered_responses:
#             for qa in resp.response:
#                 q_text = qa.get("question")
#                 a_text = qa.get("answer")
#                 if q_text and a_text:
#                     question_stats[q_text][a_text] += 1

#         analytics = []
#         for q_text, answers_counter in question_stats.items():
#             q_info = question_info_map.get(q_text)
#             if q_info:
#                 analytics.append({
#                     "question_id": q_info["question_id"],
#                     "question": q_text,
#                     "question_type": q_info["question_type"],
#                     "options": q_info["options"],
#                     "answers": [{"option": opt, "count": cnt} for opt, cnt in answers_counter.items()],
#                     "total_responses": sum(answers_counter.values())
#                 })

#         # --- Trend data ---
#         date_counts = Counter(resp.created_at.date().isoformat() for resp in filtered_responses)
#         trend_data = [{"date": d, "count": c} for d, c in sorted(date_counts.items())]

#         most_feedbacks_date = max(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)
#         least_feedbacks_date = min(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)

#         # --- Include user info from FeedbackResponse ---
#         feedback_logs = [
#             {
#                 "feedback_id": resp.id,
#                 "created_at": resp.created_at.isoformat() if resp.created_at else None,
#                 "user_type": getattr(resp, "user_type", None),
#                 "ca_number": getattr(resp, "ca_number", None),
#                 "response": resp.response,
#             }
#             for resp in filtered_responses
#         ]

#         # --- Check Oct–Nov data existence ---
#         oct_nov_data_exists = (
#             db.query(FeedbackResponse)
#             .filter(FeedbackResponse.created_at >= check_start)
#             .filter(FeedbackResponse.created_at <= check_end)
#             .first()
#             is not None
#         )

#         summary = {
#             "total_questions": total_questions,
#             "total_feedbacks": total_feedbacks,
#             "most_feedbacks_on": {"date": most_feedbacks_date[0], "count": most_feedbacks_date[1]},
#             "least_feedbacks_on": {"date": least_feedbacks_date[0], "count": least_feedbacks_date[1]},
#             "data_exists_in_oct_nov_range": oct_nov_data_exists,
#         }

#         return jsonify(
#             status=True,
#             message="Feedback summary, analytics, and logs fetched successfully",
#             summary=summary,
#             analytics=analytics,
#             trend_data=trend_data,
#             feedback_logs=feedback_logs
#         ), 200

#     except Exception as e:
#         print(f"[ERROR] Feedback summary error: {e}")
#         return jsonify(status=False, message=f"Error: {str(e)}"), 500

#     finally:
#         db.close()