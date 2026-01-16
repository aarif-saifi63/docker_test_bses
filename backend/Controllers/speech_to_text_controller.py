import re
from flask import jsonify, request
import speech_recognition as sr
import os
import tempfile
from pydub import AudioSegment


from faster_whisper import WhisperModel

TEMP_UPLOAD = "Media/temp_audio"
os.makedirs(TEMP_UPLOAD, exist_ok=True)

# model = WhisperModel("base", device="cpu", compute_type="int8")

from threading import Lock

_whisper_model = None
_whisper_lock = Lock()

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        with _whisper_lock:
            if _whisper_model is None:
                _whisper_model = WhisperModel(
                    "medium",
                    device="cpu",
                    compute_type="int8"
                )
    return _whisper_model


def speech_to_text():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]

    # Save original file in custom temp folder
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".tmp",
        dir=TEMP_UPLOAD
    ) as tmp:
        audio_file.save(tmp.name)
        original_path = tmp.name

    wav_path = original_path + ".wav"

    try:
        AudioSegment.from_file(original_path).export(wav_path, format="wav")
    except Exception as e:
        cleanup([original_path])
        return jsonify({"error": f"Audio conversion failed: {str(e)}"}), 400

    try:
        model = get_whisper_model()   # ← initialized AFTER fork
        segments, info = model.transcribe(wav_path, beam_size=5)

        text = " ".join(segment.text for segment in segments)

        cleanup([original_path, wav_path])

        return jsonify({
            "text": text.strip(),
            "language": info.language
        })

    except Exception as e:
        cleanup([original_path, wav_path])
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500


def cleanup(paths):
    for p in paths:
        try:
            if os.path.exists(p):
                os.remove(p)
        except:
            pass


# import json
# import os
# import re
# from flask import Flask, request, jsonify
# from openai import OpenAI
# import hashlib
# import mimetypes
# import tempfile
# from pydub import AudioSegment
# import redis


# app = Flask(__name__)

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# redis_client = redis.Redis(
#     host=os.getenv('REDIS_HOST'),
#     port=os.getenv('REDIS_PORT'),
#     db=0,
#     decode_responses=True
# )


# MAX_FILE_SIZE_MB = 25
# MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ALLOWED_MIME_TYPES = {
#     "audio/wav",
#     "audio/x-wav",
#     "audio/mpeg",
#     "audio/mp3",
#     "audio/mp4",
#     "audio/m4a",
#     "audio/flac",
#     "audio/ogg",
#     "audio/webm"
# }

# CHUNK_DURATION_MS = 5 * 60 * 1000  # 5 minutes


# def normalize_text(text: str) -> str:
#     text = text.lower()
#     text = re.sub(r"[^\w\s]", "", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     return text

# def get_file_hash(file_bytes: bytes) -> str:
#     return hashlib.sha256(file_bytes).hexdigest()

# def get_text_hash(text: str) -> str:
#     return hashlib.sha256(text.encode("utf-8")).hexdigest()


# def split_audio(file_path):
#     audio = AudioSegment.from_file(file_path)
#     chunks = []

#     for i in range(0, len(audio), CHUNK_DURATION_MS):
#         chunk = audio[i:i + CHUNK_DURATION_MS]
#         temp_chunk = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
#         chunk.export(temp_chunk.name, format="wav")
#         chunks.append(temp_chunk.name)

#     return chunks

# def serialize_segments(segments):
#     return [
#         {
#             "id": s.id,
#             "start": s.start,
#             "end": s.end,
#             "text": s.text
#         }
#         for s in segments
#     ]


# def speech_to_text():
#     if "audio" not in request.files:
#         return jsonify({"status": False, "message": "No audio file provided"}), 400

#     audio_file = request.files["audio"]

#     # ---------- Size validation ----------
#     audio_file.seek(0, os.SEEK_END)
#     file_size = audio_file.tell()
#     audio_file.seek(0)

#     if file_size > MAX_FILE_SIZE_BYTES:
#         return jsonify({"status": False, "message": "File size exceeds 25MB"}), 413

#     # ---------- MIME validation ----------
#     if audio_file.mimetype not in ALLOWED_MIME_TYPES:
#         return jsonify({"status": False, "message": "Invalid file type"}), 400

#     file_bytes = audio_file.read()
#     audio_hash = get_file_hash(file_bytes)

#     # =====================================================
#     # L1 CACHE — AUDIO HASH (CHECK BEFORE WHISPER)
#     # =====================================================
#     audio_cache_key = f"stt:audio:{audio_hash}"
#     cached_audio = redis_client.get(audio_cache_key)

#     if cached_audio:
#         return jsonify({
#             "status": True,
#             "cached": True,
#             "cached_by": "audio",
#             "result": json.loads(cached_audio)
#         })

#     try:
#         # Save audio temporarily
#         with tempfile.NamedTemporaryFile(delete=False) as tmp:
#             tmp.write(file_bytes)
#             audio_path = tmp.name

#         chunk_files = split_audio(audio_path)

#         full_text = ""
#         all_segments = []

#         for chunk_path in chunk_files:
#             with open(chunk_path, "rb") as chunk_audio:
#                 response = client.audio.transcriptions.create(
#                     file=chunk_audio,
#                     model="whisper-1",
#                     response_format="verbose_json"
#                 )

#                 full_text += response.text + " "
#                 all_segments.extend(serialize_segments(response.segments))

#         result = {
#             "text": full_text.strip(),
#             "segments": all_segments
#         }

#         # =====================================================
#         # STORE L1 AUDIO CACHE
#         # =====================================================
#         redis_client.setex(
#             audio_cache_key,
#             86400,
#             json.dumps(result, ensure_ascii=False)
#         )

#         # =====================================================
#         # L2 CACHE — TEXT HASH (AFTER TRANSCRIPTION)
#         # =====================================================
#         normalized_text = normalize_text(result["text"])
#         text_hash = get_text_hash(normalized_text)
#         text_cache_key = f"stt:text:{text_hash}"

#         redis_client.setex(
#             text_cache_key,
#             86400,
#             json.dumps(result, ensure_ascii=False)
#         )

#         return jsonify({
#             "status": True,
#             "cached": False,
#             "result": result
#         })

#     except Exception as e:
#         return jsonify({"status": False, "error": str(e)}), 500

#     finally:
#         if "audio_path" in locals() and os.path.exists(audio_path):
#             os.remove(audio_path)
#         for p in locals().get("chunk_files", []):
#             if os.path.exists(p):
#                 os.remove(p)

