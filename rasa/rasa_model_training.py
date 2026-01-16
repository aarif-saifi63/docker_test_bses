from flask import Flask, jsonify
from flask_cors import CORS
import requests, subprocess, os, threading, time
from datetime import datetime
import pytz
import json
from statistics import mean
from dotenv import load_dotenv
import os
import redis

# Load .env file
load_dotenv()

app = Flask(__name__)
# CORS(app) 

RASA_SERVER_URL = os.getenv("RASA_CORE_URL") 
# RASA_SERVER_URL = f"{os.getenv('BASE_URL')}:{os.getenv('RASA_CORE_PORT')}"
MODEL_DIR = "models"
RASA_TRAIN_COMMAND = ["rasa", "train"]
REMOTE_API_BASE = os.getenv("BACKEND_URL") 
# REMOTE_API_BASE = f"{os.getenv('BASE_URL')}:{os.getenv('BACKEND_PORT')}"

TRAINING_HISTORY_FILE = "training_history.json"

# Redis connection (update host if needed)
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    db=0
)

# training_lock = redis_client.lock("training_lock", timeout=7200)

def set_training_status_redis(data):
    # convert datetime objects to isoformat strings
    for k, v in data.items():
        if isinstance(v, datetime):
            data[k] = v.isoformat()
    redis_client.set("training_status", json.dumps(data))

def initialize_training_status():
    if not redis_client.exists("training_status"):
        set_training_status_redis({
            "status": "idle",
            "message": "",
            "start_time": None,
            "end_time": None,
            "eta_seconds": None,
            "model_path": None
        })

initialize_training_status()


def get_training_status_redis():
    data = redis_client.get("training_status")
    if not data:
        # default structure
        return {
            "status": "idle",
            "message": "",
            "start_time": None,
            "end_time": None,
            "eta_seconds": None,
            "model_path": None
        }
    return json.loads(data)





def update_training_status(**kwargs):
    data = get_training_status_redis()
    data.update(kwargs)
    set_training_status_redis(data)



def get_average_training_time():
    """Return average training duration (seconds) from previous runs."""
    if not os.path.exists(TRAINING_HISTORY_FILE):
        return 300  # default if no history
    try:
        with open(TRAINING_HISTORY_FILE, "r") as f:
            data = json.load(f)
        runs = data.get("runs", [])
        if not runs:
            return 300
        return int(mean(runs))
    except Exception:
        return 300


def record_training_time(duration_seconds):
    """Append a completed run’s duration and keep only the last 10 runs."""
    data = {"runs": []}
    if os.path.exists(TRAINING_HISTORY_FILE):
        try:
            with open(TRAINING_HISTORY_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            pass
    data["runs"].append(int(duration_seconds))
    data["runs"] = data["runs"][-10:]  # keep last 10 runs
    with open(TRAINING_HISTORY_FILE, "w") as f:
        json.dump(data, f)


# def update_training_status(**kwargs):
#     training_status.update(kwargs)


def fetch_remote_yaml(endpoint_url):
    r = requests.get(endpoint_url)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch from {endpoint_url}: {r.text}")
    return r.text


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def train_rasa_model():
    try:
        update_training_status(status="running", message="Training started...")
        result = subprocess.run(RASA_TRAIN_COMMAND, capture_output=True, text=True, check=True)
        files = sorted(
            [f for f in os.listdir(MODEL_DIR) if f.endswith(".tar.gz")],
            key=lambda x: os.path.getmtime(os.path.join(MODEL_DIR, x)),
            reverse=True
        )
        latest_model = files[0] if files else None
        if not latest_model:
            raise Exception("No model file found after training.")
        model_path = os.path.join(MODEL_DIR, latest_model)
        update_training_status(status="running", message="Training complete, loading model...", model_path=model_path)
        return model_path
    except subprocess.CalledProcessError as e:
        update_training_status(status="error", message="Training failed", model_path=None)
        raise Exception(f"Training failed: {e.stderr}")


def load_model_to_rasa(model_path):
    with open(model_path, "rb") as f:
        # files = {"model_file": (os.path.basename(model_path), f, "application/gzip")}
        r = requests.put(f"{RASA_SERVER_URL}/model", json={"model_file": model_path})
    if r.status_code in [200, 204]:
        # store end_time as UTC-aware datetime to avoid timezone mismatches
        update_training_status(status="success", message="Model loaded successfully", end_time=datetime.now(pytz.UTC))
    else:
        update_training_status(status="error", message=f"Failed to load model: {r.text}")


def run_training_pipeline():
    try:
        avg_eta = get_average_training_time()
        # store start_time as UTC-aware datetime to avoid timezone mismatches
        update_training_status(
            status="running",
            message="Fetching files from remote...",
            start_time=datetime.now(pytz.UTC),
            eta_seconds=avg_eta
        )

        nlu = fetch_remote_yaml(f"{REMOTE_API_BASE}/rebuild_intent_file")
        stories = fetch_remote_yaml(f"{REMOTE_API_BASE}/download_stories")
        domain = fetch_remote_yaml(f"{REMOTE_API_BASE}/export_domain")

        write_file("data/nlu.yml", nlu)
        write_file("data/stories.yml", stories)
        write_file("domain.yml", domain)

        update_training_status(message="Files updated. Training model...")

        start = time.time()
        model_path = train_rasa_model()
        duration = time.time() - start
        record_training_time(duration)

        update_training_status(message="Training complete, loading model...")
        load_model_to_rasa(model_path)

    except Exception as e:
        update_training_status(status="error", message=str(e))
        print("Training error:", e)


@app.route("/rasa-model-training", methods=["POST"])
def start_training():
    # Try to acquire lock → if false, training already running
    # if not training_lock.acquire(blocking=False):
    #     return jsonify({"status": "error", "message": "Training already in progress"}), 400

    # Start training in background thread
    threading.Thread(target=run_training_with_lock).start()

    return jsonify({
        "status": "started",
        "message": "Training started"
    })


# def run_training_with_lock():
#     try:
#         run_training_pipeline()
#     finally:
#         training_lock.release()

def run_training_with_lock():
    lock = redis_client.lock("training_lock", timeout=7200)

    try:
        acquired = lock.acquire(blocking=False)

        if not acquired:
            print("Training already running by another worker.")
            update_training_status(status="error", message="Training already running by another worker.")
            return

        # Lock acquired successfully — now run training
        run_training_pipeline()
        print("Training pipeline completed.")

    except Exception as e:
        print("Training error:", e)
        update_training_status(status="error", message=str(e))

    finally:
        # Release lock ONLY if this thread holds it
        try:
            lock.release()
        except redis.exceptions.LockError:
            pass


@app.route("/rasa-training-status", methods=["GET"])
def get_training_status():
    # Load status once from Redis
    status = get_training_status_redis()

    # If running, compute elapsed/remaining in seconds
    if status["status"] == "running" and status.get("start_time"):
        start_dt = status["start_time"]

        try:
            if isinstance(start_dt, datetime):
                dt = start_dt
            else:
                dt = datetime.fromisoformat(str(start_dt))

            # Normalize naive datetime to UTC
            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                dt = dt.replace(tzinfo=pytz.UTC)

            now_utc = datetime.now(pytz.UTC)
            elapsed = (now_utc - dt).total_seconds()
        except Exception:
            elapsed = 0

        avg_eta = status.get("eta_seconds") or get_average_training_time()
        remaining = max(avg_eta - elapsed, 0)

        # Attach new fields to status (not written to Redis)
        status["remaining_seconds"] = round(remaining, 1)
        status["elapsed_seconds"] = round(elapsed, 1)

    # Prepare response copy
    resp = status.copy()

    def _format_dt_to_ist(val):
        if not val:
            return None
        try:
            if isinstance(val, str):
                dt = datetime.fromisoformat(val)
            elif isinstance(val, datetime):
                dt = val
            else:
                return str(val)

            if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
                dt = dt.replace(tzinfo=pytz.UTC)

            ist = dt.astimezone(pytz.timezone("Asia/Kolkata"))
            return ist.strftime("%a, %d %b %Y %H:%M:%S %Z")
        except Exception:
            return str(val)

    # Convert to IST for response only
    resp["start_time"] = _format_dt_to_ist(resp.get("start_time"))
    resp["end_time"] = _format_dt_to_ist(resp.get("end_time"))

    return jsonify(resp)



if __name__ == "__main__":
    app.run(port=8001, host="0.0.0.0", debug=False)
 