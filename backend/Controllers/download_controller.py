
import os
from flask import abort, send_file, send_from_directory
from werkzeug.utils import safe_join
from urllib.parse import unquote

BASE_DIR = os.path.join(os.getcwd(), "BSES_Chat_Icon", "Chat_Icon")


BSES_ICON = os.path.join(os.getcwd(), "BSES_ICONS")
# Folder to store PDFs
PDF_FOLDER = os.path.join(os.getcwd(), "generated_pdfs")
os.makedirs(PDF_FOLDER, exist_ok=True)

def download_file_path_user(filename):
    try:
        folderpath = f"{PDF_FOLDER}"
        if filename:
            return send_file(f"{folderpath}/{filename}", as_attachment=False)
        else:
            return False
    except FileNotFoundError:
        return "File not found!", 404
    

AD_CONTENT_FOLDER = os.path.join(os.getcwd(), "ad_content")
os.makedirs(AD_CONTENT_FOLDER, exist_ok=True)

def download_ad_content(filename):
    try:
        folderpath = f"{AD_CONTENT_FOLDER}"
        if filename:
            return send_file(f"{folderpath}/{filename}", as_attachment=False)
        else:
            return False
    except FileNotFoundError:
        return "File not found!", 404
    

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Media"))


def serve_media(relative_path):
    try:
        full_path = safe_join(BASE_MEDIA_DIR, relative_path)
        print(f"BASE_MEDIA_DIR: {BASE_MEDIA_DIR}")
        print(f"Requested: {relative_path}")
        print(f"Resolved full path: {full_path}")
        print(f"Exists: {os.path.exists(full_path)}")

        if not full_path or not os.path.isfile(full_path):
            abort(404, description=f"File not found: {relative_path}")

        # SECURITY: Force download for SVG files to prevent XSS attacks
        filename = os.path.basename(full_path)
        if filename.lower().endswith('.svg'):
            response = send_file(full_path, as_attachment=True, download_name=filename)
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response
        
        print(f"Serving file: {full_path} as attachment: False")

        return send_file(full_path, as_attachment=False)

    except Exception as e:
        abort(400, description=f"Error serving file: {str(e)}")

## Download Icons

def view_icon(filename):
    try:
        # Decode %20 and other URL characters
        safe_filename = unquote(filename)

        # Full path to requested file
        full_path = os.path.abspath(os.path.join(BASE_DIR, safe_filename))

        # Make sure it's inside BASE_DIR to prevent path traversal
        if not full_path.startswith(BASE_DIR):
            abort(403, description="Forbidden: Attempted path traversal")

        if not os.path.isfile(full_path):
            return {"error": f"File not found at {full_path}"}, 404

        # Extract folder and filename for Flask
        directory = os.path.dirname(full_path)
        file_only = os.path.basename(full_path)

        # SECURITY: Force download for SVG files to prevent XSS attacks
        if file_only.lower().endswith('.svg'):
            response = send_from_directory(directory, file_only, as_attachment=True)
            response.headers['Content-Disposition'] = f'attachment; filename="{file_only}"'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            return response

        return send_from_directory(directory, file_only)
    except Exception as e:
        return {"error": str(e)}, 500