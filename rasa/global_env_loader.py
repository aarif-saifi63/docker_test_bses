# global_env_loader.py
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)
print("[INFO] .env loaded from:", env_path)
