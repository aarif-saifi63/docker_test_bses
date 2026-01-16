from flask import jsonify, request
from numpy import extract
from sqlalchemy import func
from database import SessionLocal
from Models.poll_model import Poll
from Models.poll_response_model import PollResponse
from collections import Counter, defaultdict
from datetime import datetime, time
import pytz
import math

IST = pytz.timezone("Asia/Kolkata")



# def get_poll_summary_and_analytics():
#     """
#     Fetch poll summary and analytics in a single response.
#     Combines all responses per question and provides overall statistics.
#     """
#     try:
#         db = SessionLocal()

#         # --- Fetch all polls and responses ---
#         polls = db.query(Poll).all()
#         responses = db.query(PollResponse).all()

#         total_polls = len(polls)
#         total_responses = len(responses)

#         # --- Prepare summary data per poll question ---
#         question_stats = defaultdict(Counter)
#         question_options_map = {}

#         # Map poll questions to their options and types
#         for poll in polls:
#             for q in poll.questions:  # assuming poll.questions stores the list of questions like your example
#                 question_options_map[q["question"]] = {
#                     "question_type": q["type"],
#                     "options": q["options"],
#                     "slider_min": q.get("slider_min"),
#                     "slider_max": q.get("slider_max")
#                 }

#         # Aggregate responses per question
#         for resp in responses:
#             for qa in resp.response:  # assuming resp.response is a list of {question, answer}
#                 q_text = qa["question"]
#                 a_text = qa["answer"]
#                 question_stats[q_text][a_text] += 1

#         # Build analytics per question
#         analytics = []
#         for q_text, answers_counter in question_stats.items():
#             q_info = question_options_map.get(q_text, {})
#             analytics.append({
#                 "question": q_text,
#                 "question_type": q_info.get("question_type"),
#                 "options": q_info.get("options"),
#                 "slider_min": q_info.get("slider_min"),
#                 "slider_max": q_info.get("slider_max"),
#                 "answers": [{"option": option, "count": count} for option, count in answers_counter.items()],
#                 "total_responses": sum(answers_counter.values())
#             })

#         # --- Overall poll summary ---
#         active_count = sum(1 for poll in polls if poll.is_active)
#         inactive_count = total_polls - active_count

#         summary = {
#             "total_polls": total_polls,
#             "total_responses": total_responses,
#             "active_polls": active_count,
#             "inactive_polls": inactive_count
#         }

#         # --- Daily trend for all poll responses ---
#         date_counts = Counter()
#         for resp in responses:
#             date_str = resp.created_at.date().isoformat()
#             date_counts[date_str] += 1

#         trend_data = [{"date": date, "count": count} for date, count in sorted(date_counts.items())]

#         if date_counts:
#             most_responses_date = max(date_counts.items(), key=lambda x: x[1])
#             least_responses_date = min(date_counts.items(), key=lambda x: x[1])
#         else:
#             most_responses_date = (None, 0)
#             least_responses_date = (None, 0)

#         summary.update({
#             "most_responses_on": {"date": most_responses_date[0], "count": most_responses_date[1]},
#             "least_responses_on": {"date": least_responses_date[0], "count": least_responses_date[1]}
#         })

#         return jsonify(
#             status=True,
#             message="Poll summary and analytics fetched successfully",
#             summary=summary,
#             analytics=analytics,
#             trend_data=trend_data
#         ), 200

#     except Exception as e:
#         return jsonify(status=False, message=f"Error: {str(e)}"), 500
#     finally:
#         db.close()

# def get_poll_summary_and_analytics():
#     """
#     Fetch poll summary and analytics with optional date filters.
#     """
#     try:
#         db = SessionLocal()
        
#         # --- Get date filters from frontend ---
#         start_date_str = request.args.get("start_date")  # YYYY-MM-DD
#         end_date_str = request.args.get("end_date")      # YYYY-MM-DD

#         start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").replace(tzinfo=IST) if start_date_str else None
#         end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(tzinfo=IST) if end_date_str else None

#         # --- Fetch polls and responses using filters ---
#         poll_query = db.query(Poll)
#         if start_dt:
#             poll_query = poll_query.filter(Poll.start_time >= start_dt)
#         if end_dt:
#             poll_query = poll_query.filter(Poll.end_time <= end_dt)
#         polls = poll_query.all()

#         resp_query = db.query(PollResponse)
#         if start_dt:
#             resp_query = resp_query.filter(PollResponse.created_at >= start_dt)
#         if end_dt:
#             resp_query = resp_query.filter(PollResponse.created_at <= end_dt)
#         responses = resp_query.all()

#         total_polls = len(polls)
#         total_responses = len(responses)

#         # --- Prepare summary data per poll question ---
#         question_stats = defaultdict(Counter)
#         question_options_map = {}

#         for poll in polls:
#             for q in poll.questions:
#                 question_options_map[q["question"]] = {
#                     "question_type": q["type"],
#                     "options": q["options"],
#                     "slider_min": q.get("slider_min"),
#                     "slider_max": q.get("slider_max")
#                 }

#         for resp in responses:
#             for qa in resp.response:
#                 q_text = qa["question"]
#                 a_text = qa["answer"]
#                 question_stats[q_text][a_text] += 1

#         analytics = []
#         for q_text, answers_counter in question_stats.items():
#             q_info = question_options_map.get(q_text, {})
#             analytics.append({
#                 "question": q_text,
#                 "question_type": q_info.get("question_type"),
#                 "options": q_info.get("options"),
#                 "slider_min": q_info.get("slider_min"),
#                 "slider_max": q_info.get("slider_max"),
#                 "answers": [{"option": option, "count": count} for option, count in answers_counter.items()],
#                 "total_responses": sum(answers_counter.values())
#             })

#         # --- Overall summary ---
#         active_count = sum(1 for poll in polls if poll.is_active)
#         inactive_count = total_polls - active_count

#         summary = {
#             "total_polls": total_polls,
#             "total_responses": total_responses,
#             "active_polls": active_count,
#             "inactive_polls": inactive_count
#         }

#         # --- Daily trend ---
#         date_counts = Counter()
#         for resp in responses:
#             date_str = resp.created_at.date().isoformat()
#             date_counts[date_str] += 1

#         trend_data = [{"date": date, "count": count} for date, count in sorted(date_counts.items())]

#         most_responses_date = max(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)
#         least_responses_date = min(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)

#         summary.update({
#             "most_responses_on": {"date": most_responses_date[0], "count": most_responses_date[1]},
#             "least_responses_on": {"date": least_responses_date[0], "count": least_responses_date[1]}
#         })

#         return jsonify(
#             status=True,
#             message="Poll summary and analytics fetched successfully",
#             summary=summary,
#             analytics=analytics,
#             trend_data=trend_data
#         ), 200

#     except Exception as e:
#         return jsonify(status=False, message=f"Error: {str(e)}"), 500
#     finally:
#         db.close()

def get_poll_summary_and_analytics():
    """
    Fetch poll summary and analytics with optional date filters.
    Polls are included if their time range overlaps with the selected dates.
    """
    try:
        db = SessionLocal()

        # --- Parse filters ---
        start_date_str = request.args.get("start_date")  # YYYY-MM-DD
        end_date_str = request.args.get("end_date")      # YYYY-MM-DD

        start_dt = None
        end_dt = None

        # --- Handle date range: full days in IST ---
        if start_date_str or end_date_str:
            base_date_str = start_date_str or end_date_str
            base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()

            start_naive = datetime.combine(base_date, time.min)
            start_dt = IST.localize(start_naive)

            end_date_to_use = end_date_str or start_date_str or base_date_str
            end_date = datetime.strptime(end_date_to_use, "%Y-%m-%d").date()
            end_naive = datetime.combine(end_date, time.max)
            end_dt = IST.localize(end_naive)

        # --- Fetch PollResponses (filtered by created_at) ---
        resp_query = db.query(PollResponse)
        if start_dt:
            resp_query = resp_query.filter(PollResponse.created_at >= start_dt)
        if end_dt:
            resp_query = resp_query.filter(PollResponse.created_at <= end_dt)
        responses = resp_query.all()

        # --- Get poll IDs from responses ---
        poll_ids_from_responses = {resp.poll_id for resp in responses if resp.poll_id}

        # --- Fetch Polls: either from responses OR all active/overlapping ---
        poll_query = db.query(Poll)

        if start_dt and end_dt:
            # Include polls that *overlap* with the date range
            poll_query = poll_query.filter(
                Poll.start_time <= end_dt,
                Poll.end_time >= start_dt
            )
        # If no date filter, fetch all polls
        polls = poll_query.all()

        # Optional: further filter to only polls that have responses in range
        if poll_ids_from_responses:
            polls = [p for p in polls if p.id in poll_ids_from_responses]

        print(len(polls), '===================================== Polls fetched')

        total_polls = len(polls)
        total_responses = len(responses)

        # --- Prepare question metadata ---
        question_stats = defaultdict(Counter)
        question_options_map = {}

        for poll in polls:
            if not poll.questions:
                continue
            for q in poll.questions:
                q_text = q.get("question")
                if not q_text:
                    continue
                question_options_map[q_text] = {
                    "question_type": q.get("type"),
                    "options": q.get("options", []),
                    "slider_min": q.get("slider_min"),
                    "slider_max": q.get("slider_max")
                }

        # --- Aggregate response data ---
        for resp in responses:
            if not resp.response:
                continue
            for qa in resp.response:
                q_text = qa.get("question")
                a_text = qa.get("answer")
                if q_text and a_text is not None:
                    question_stats[q_text][str(a_text)] += 1

        # --- Prepare analytics per question ---
        analytics = []
        for q_text, answers_counter in question_stats.items():
            q_info = question_options_map.get(q_text, {})
            analytics.append({
                "question": q_text,
                "question_type": q_info.get("question_type"),
                "options": q_info.get("options", []),
                "slider_min": q_info.get("slider_min"),
                "slider_max": q_info.get("slider_max"),
                "answers": [{"option": option, "count": count} for option, count in answers_counter.items()],
                "total_responses": sum(answers_counter.values())
            })

        # --- Active/Inactive count ---
        active_count = sum(
            1 for poll in polls
            if poll.is_active  # Now Boolean → direct check
        )
        inactive_count = total_polls - active_count

        summary = {
            "total_polls": total_polls,
            "total_responses": total_responses,
            "active_polls": active_count,
            "inactive_polls": inactive_count
        }

        # --- Trend data ---
        date_counts = Counter(resp.created_at.date().isoformat() for resp in responses)
        trend_data = [{"date": date, "count": count} for date, count in sorted(date_counts.items())]

        most_responses_date = max(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)
        least_responses_date = min(date_counts.items(), key=lambda x: x[1]) if date_counts else (None, 0)

        summary.update({
            "most_responses_on": {"date": most_responses_date[0], "count": most_responses_date[1]},
            "least_responses_on": {"date": least_responses_date[0], "count": least_responses_date[1]}
        })

        return jsonify(
            status=True,
            message="Poll summary and analytics fetched successfully",
            summary=summary,
            analytics=analytics,
            trend_data=trend_data
        ), 200

    except Exception as e:
        print("Error in get_poll_summary_and_analytics:", str(e))
        return jsonify(status=False, message=f"Error: {str(e)}"), 500

    finally:
        db.close()


def get_poll_analytics():
    try:
        with SessionLocal() as db:
            polls = db.query(Poll).all()
            print([polls,'pollllslslslsls'])
            result = []

            for poll in polls:
                poll_id = str(poll.id)
                poll_questions = poll.questions
                print(poll,'pollll')

                total_responses = db.query(PollResponse).filter(
                    PollResponse.poll_id == poll_id
                ).count()

                analytics = []

                # Prepare response map for this poll
                responses = db.query(PollResponse).filter(
                    PollResponse.poll_id == poll_id
                ).all()

                for q in poll_questions:
                    question_text = q.get("question")
                    question_type = q.get("type")
                    options = q.get("options", [])

                    # Initialize counts per option
                    answer_counts = {opt: 0 for opt in options}

                    # For text or slider type, we still store answers individually
                    if question_type in ["text", "slider"]:
                        answer_counts = {}

                    # Count responses
                    for resp in responses:
                        resp_list = resp.response
                        for r in resp_list:
                            if r.get("question") == question_text:
                                ans = r.get("answer")
                                # Map answer to options if exists
                                if question_type not in ["text", "slider"] and ans in answer_counts:
                                    answer_counts[ans] += 1
                                else:
                                    # For free text or unmatched answers
                                    if ans in answer_counts:
                                        answer_counts[ans] += 1
                                    else:
                                        answer_counts[ans] = 1

                    # Convert counts to list
                    answers_list = [{"option": opt, "count": cnt} for opt, cnt in answer_counts.items()]

                    analytics.append({
                        "question": question_text,
                        "type": question_type,
                        "options": options,
                        "answers": answers_list,
                        "total_responses": sum(answer_counts.values())
                    })

                # Trend data per day
                trend_query = db.query(
                    func.date(PollResponse.created_at).label("date"),
                    func.count(PollResponse.id).label("count")
                ).filter(PollResponse.poll_id == poll_id).group_by(func.date(PollResponse.created_at)).all()

                trend_data = [{"date": str(row.date), "count": row.count} for row in trend_query]

                result.append({
                    "poll_id": poll_id,
                    "title": poll.title,
                    "start_time": poll.start_time,
                    "end_time": poll.end_time,
                    "is_active": poll.is_active,
                    "analytics": analytics,
                    "total_responses": total_responses,
                    "trend_data": trend_data
                })

        return jsonify({
            "status": True,
            "message": "Polls fetched successfully",
            "data": result
        }), 200

    except Exception as e:
        return jsonify({
            "status": False,
            "message": f"An error occurred: {str(e)}"
        }), 500
    
    # finally:
    #     db.close()
