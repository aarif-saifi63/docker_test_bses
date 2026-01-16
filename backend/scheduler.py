from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from datetime import datetime
import pytz
import requests
from database import SessionLocal
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Define IST timezone
IST = pytz.timezone("Asia/Kolkata")

flask_url = os.getenv('BACKEND_URL')
# flask_url = f"{os.getenv('BASE_URL')}:{os.getenv('BACKEND_PORT')}"

# Scheduler job function
def check_pending_complaints():
    print(f"Scheduler started at {datetime.now(IST)}")

    # Create a database session
    db = SessionLocal()
    try:
        # Fetch pending complaints with complain_no present
        result = db.execute("""
            SELECT user_id, ca_number 
            FROM session_data
            WHERE complain_no IS NOT NULL 
              AND complain_status = 'pending'
        """)
        pending_records = result.fetchall()

        if not pending_records:
            print("No pending complaints found.")
            return

        for record in pending_records:
            sender_id = record.user_id
            ca_number = record.ca_number

            try:
                response = requests.post(
                    f"{flask_url}/complaint_status",  # Change to your API URL if deployed
                    json={"ca_number": ca_number, "sender_id": sender_id},
                    timeout=50
                )
                print(f"Processed CA: {ca_number}, Sender: {sender_id}, Status: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed for CA: {ca_number}, Sender: {sender_id}, Error: {e}")

    finally:
        db.close()


def deactivate_expired_polls():
    print(f"{datetime.now(IST)} - Poll scheduler running")

    db = SessionLocal()
    try:
        # Wrap your raw SQL in text()
        result = db.execute(text("""
            UPDATE polls
            SET is_active = False
            WHERE is_active = True AND end_time < NOW()
            RETURNING id, title;
        """))

        expired_polls = result.fetchall()
        db.commit()

        if expired_polls:
            for poll in expired_polls:
                print(f"Poll ID {poll.id} ('{poll.title}') marked as inactive")
        else:
            print("No polls expired at this time.")

    except Exception as e:
        print(f"Error while deactivating polls: {e}")
        db.rollback()
    finally:
        db.close()


def deactivate_expired_ads():
    print(f"{datetime.now(IST)} - Ad scheduler running")

    db = SessionLocal()
    try:
        # Deactivate ads that have expired
        result = db.execute(text("""
            UPDATE ad_content
            SET is_active = False
            WHERE is_active = True AND end_time < NOW()
            RETURNING id, ad_name;
        """))

        expired_ads = result.fetchall()
        db.commit()

        if expired_ads:
            for ad in expired_ads:
                print(f"Ad ID {ad.id} ('{ad.ad_name}') marked as inactive")
        else:
            print("No ads expired at this time.")

    except Exception as e:
        print(f"Error while deactivating ads: {e}")
        db.rollback()
    finally:
        db.close()

# Initialize scheduler BUT DON'T START IT YET
# It will be started in app.py after system initialization
scheduler = BackgroundScheduler(timezone=IST)
scheduler.add_job(check_pending_complaints, "interval", hours=1)
scheduler.add_job(deactivate_expired_polls, "interval", minutes=10)
scheduler.add_job(deactivate_expired_ads, "interval", minutes=10)
# scheduler.start() is called in app.py after initialization completes
