import os
import threading
from flask import Flask, jsonify, send_file, request, make_response
from flask_cors import CORS
from Controllers.rsa_controller import get_public_key
from Controllers.submenu_fallback_controller import create_submenu_fallback, delete_submenu_fallback, get_all_submenu_categories, get_all_submenu_fallbacks, get_submenu_fallback_by_category, update_submenu_fallback
from middlewares.auth_chatbot_middleware import chatbot_token_required
from middlewares.auth_middleware import optional_token, token_required, permission_required
# Controller Imports
from Controllers.ad_controller import ad_on_menu_click, add_ad, chatbot_intro_ad, delete_ad, get_ad, get_ad_analytics, get_all_ads, get_unique_submenus, submit_ad_tracker, update_ad
from Controllers.api_key_master_controller import api_hit_breakdown, create_api_key, get_all_api_details, get_api_details_with_breakdown, update_api_key_by_name
from Controllers.chatbot_auth_controller import chatbot_init_session, chatbot_logout, chatbot_refresh_session, chatbot_validate_session
from Controllers.bill_pay_controller import dashboard_download_duplicate_bill, dashboard_pay_bill, save_bill_pay_chat, save_duplicate_bill_chat
from Controllers.billing_payment_controller import generate_duplicate_bill_pdf
from Controllers.complaints_support_controller import complaint_status
from Controllers.dashboard_controller import average_interaction_time, chat_status, count_opt_for_ebill, dashboard_complaint_status, get_session_counts, interaction_breakdown
from Controllers.division_controller import get_divisions
from Controllers.download_controller import download_ad_content, download_file_path_user, serve_media, view_icon
from Controllers.fallback_controller import create_fallback, get_all_fallbacks, get_all_global_fallbacks, update_fallback
from Controllers.feedback_mechanism_controller import add_feedback_question, delete_feedback_question, get_feedback_acceptance, get_feedback_questions, submit_feedback, update_feedback_question
from Controllers.language_controller import create_language, delete_language, get_language, get_languages, get_visible_languages, update_language
from Controllers.admin_intent_controller import create_intent, export_intents, get_intents, get_intent_by_id, update_intent, delete_intent
from Controllers.admin_intent_examples import create_intent_example, get_examples_by_intent, get_example_by_id, update_intent_example, delete_intent_example, delete_examples_by_intent
from Controllers.menu_analysis_controller import menu_analysis
from Controllers.menu_management_controller import create_menu_with_submenu, delete_menu, delete_submenu, download_stories, export_domain, get_rajdhani_users, get_user_menu_data, get_user_menus, rebuild_intent_file, update_menu_sequence
from Controllers.meter_connection_controller import get_order_status
from Controllers.mis_report_controller import mis_avg_interaction_duration, mis_chat_completion_status, mis_interaction_breakdown, mis_pay_bill, mis_peak_hours, visually_impaired_analysis
from Controllers.poll_analytics_controller import get_poll_summary_and_analytics, get_poll_analytics
from Controllers.poll_controller import create_poll, delete_poll, get_active_poll, get_all_polls, submit_poll_response, update_poll
from Controllers.rasa_webhook_controller import ca_number_register_run_flow, handle_fallback, register_run_flow, register_run_flow_submenu_fallback, reset_fallback, run_flow, run_flow_submenu_fallback, webhook
from Controllers.speech_to_text_controller import speech_to_text
from Controllers.user_controller import login_user, register_user
from Controllers.register_user_authentication_controller import get_ca, get_session_data, validate_ca
from Controllers.utter_message_controller import create_utter_message, delete_utter_message, get_all_utter_messages, get_utter_message, update_utter_message, updated_get_utter_messages
from Controllers.validation_controller import validate_language, validate_mobile, validate_otp, validate_email
from Controllers.permission_matrix_controller import create_permission, get_permissions, get_permission_by_id, update_permission, delete_permission
from Controllers.user_permission_mapping_controller import create_mapping, get_mappings, get_mapping_by_id, update_mapping, delete_mapping, update_mapping_users
from Controllers.user_role_controller import create_role, get_roles, get_role_by_id, update_role, delete_role
from Controllers.feedback_analytics_controller import get_feedback_summary_and_analytics
from Controllers.user_details_controller import delete_user, get_user_permission, logout_user, refresh_token, register_user_detail, login_user_detail, get_all_users, update_user, verify_login
from Controllers.signed_downloads import bp as signed_downloads_bp
from populate import is_system_initialized
from database import Base, engine
from scheduler import scheduler
import werkzeug
werkzeug.__version__ = ""


app = Flask(__name__)

# Configure signed download settings
app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "fallback-secret-key")
app.config["FILES_ROOT"] = os.path.join(os.getcwd(), "Media")
app.config["DEFAULT_EXPIRY"] = 300  # 5 minutes default
app.config["MAX_EXPIRY"] = 3600     # 1 hour maximum
app.config["SIGNED_DOWNLOAD_PATH"] = "/files/download"

# 🔒 SECURITY: Configure Flask Session for Session Fixation Protection
# These settings enable server-side session management to prevent session hijacking
app.config["SESSION_COOKIE_NAME"] = "flask_session"  # Name of the session cookie
app.config["SESSION_COOKIE_HTTPONLY"] = True  # Prevent JavaScript access to session cookie
app.config["SESSION_COOKIE_SECURE"] = True  # Only send cookie over HTTPS
app.config["SESSION_COOKIE_SAMESITE"] = "None"  # CSRF protection (use 'Lax' for local dev)
app.config["PERMANENT_SESSION_LIFETIME"] = 900  # 15 minutes (matches ACCESS_EXPIRES_MINUTES)
app.config["SESSION_TYPE"] = "filesystem"  # Store sessions on server filesystem (can be changed to Redis)

# Register signed downloads blueprint
app.register_blueprint(signed_downloads_bp, url_prefix="/files")

scheduler_lock = threading.Lock()

# @app.before_request
# def before_request():
#     if not request.is_secure:
#         return jsonify(status=False, message="Use HTTPS for all requests"), 403


# SECURITY: Add security headers to prevent XSS and other attacks
@app.after_request
def add_security_headers(response):
    """
    SECURITY: Implement security headers to mitigate XSS attacks
    Addresses CWE-79: Cross-Site Scripting from VAPT findings
    """
    # Content Security Policy - Prevents XSS by controlling resource loading
    # NOTE: Adjust this policy based on your application's needs
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "media-src 'self'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy

    # X-Content-Type-Options - Prevents MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # X-Frame-Options - Prevents clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # X-XSS-Protection - Browser XSS protection (legacy but still useful)
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Referrer-Policy - Controls referrer information
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions-Policy - Controls browser features
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    return response
 


print("Creating tables...")
Base.metadata.create_all(bind=engine)   
print("Tables created successfully!")


# ==========================================
# PUBLIC ENDPOINTS (No Authentication Required)
# ==========================================

## Chatbot Authentication Services (Public - SECURITY: Secure session management)
app.route('/chatbot/init-session', methods=['POST'])(chatbot_init_session)
app.route('/chatbot/refresh-session', methods=['POST'])(chatbot_refresh_session)
app.route('/chatbot/validate-session', methods=['GET'])(chatbot_validate_session)
app.route('/chatbot/logout', methods=['POST'])(chatbot_logout)

## Rasa Webhook Services (Public - for chatbot)

@app.route('/webhook', methods=['POST'])
@chatbot_token_required
def protected_webhook():
    return webhook()


@app.route('/register_menu_run_flow', methods=['POST'])
@chatbot_token_required
def protected_register_run_flow():
    return register_run_flow()


@app.route('/register_menu_run_flow_submenu_fallback', methods=['POST'])
@chatbot_token_required
def protected_register_run_flow_submenu_fallback():
    return register_run_flow_submenu_fallback()


@app.route('/menu_run_flow', methods=['POST'])
@chatbot_token_required
def protected_menu_run_flow():
    return run_flow()

@app.route('/menu_run_flow_submenu_fallback', methods=['POST'])
@chatbot_token_required
def protected_run_flow_submenu_fallback():
    return run_flow_submenu_fallback()


@app.route('/validate-language', methods=['POST'])
@chatbot_token_required
def protected_validate_language():
    return validate_language()


@app.route('/validate_ca', methods=['POST'])
@chatbot_token_required
def protected_validate_ca():
    return validate_ca()


@app.route('/get_order_status', methods=['POST'])
@chatbot_token_required
def protected_get_order_status():
    return get_order_status()


@app.route('/validate_otp', methods=['POST'])
@chatbot_token_required
def protected_validate_otp():
    return validate_otp()

@app.route('/validate_email', methods=['POST'])
@chatbot_token_required
def protected_validate_email():
    return validate_email()

@app.route('/validate_mobile', methods=['POST'])
@chatbot_token_required
def protected_validate_mobile():
    return validate_mobile()

# app.route('/webhook', methods=['POST'])(webhook)
# app.route('/menu_run_flow', methods=['POST'])(run_flow)
# app.route('/register_menu_run_flow', methods=['POST'])(register_run_flow)
app.route('/ca_number_register_run_flow', methods=['POST'])(ca_number_register_run_flow)
app.route("/fallback", methods=["POST"])(handle_fallback)
app.route("/reset_fallback", methods=["POST"])(reset_fallback)

## Register User Authentication (Public)
# app.route('/validate_ca', methods=['POST'])(validate_ca)
app.route('/get_ca', methods=['POST'])(get_ca)
app.route('/get_session_data', methods=['POST'])(get_session_data)
# app.route("/validate-language", methods=["POST"])(validate_language)

## Validation Services (Public)
# app.route('/validate_otp', methods=['POST'])(validate_otp)
# app.route('/validate_email', methods=['POST'])(validate_email)
# app.route('/validate_mobile', methods=['POST'])(validate_mobile)

## Meter & Connection Services (Public)
# app.route('/get_order_status', methods=['POST'])(get_order_status)

## Billing & Payment Services (Public)
app.route('/generate_duplicate_bill_pdf', methods=['POST'])(generate_duplicate_bill_pdf)

## Complaints & Support Services (Public)
app.route('/complaint_status', methods=['POST'])(complaint_status)

## Speech to Text Services (Public)
app.route("/speech-to-text", methods=["POST"])(speech_to_text)

## Download Services (Public)
app.route('/view-icon/<path:filename>')(view_icon)
app.route('/generated_pdfs/<filename>')(download_file_path_user)
app.route('/ad_content/<filename>')(download_ad_content)
app.route('/Media/<path:relative_path>')(serve_media)

# @app.route('/Media/<path:relative_path>', methods=['GET'])
# # @token_required
# # @permission_required(module_name="Dashboard", crud_action="view")
# def auth_serve_media():
#     return serve_media()

@app.route("/Media/BSES_ICONS/<filename>")
def download_file_path_thumbnails(filename):
    try:
        folderpath = f"Media/BSES_ICONS"
        if filename:
            return send_file(f"{folderpath}/{filename}", as_attachment=False)
        else:
            return False
    except FileNotFoundError:
        return "File not found!", 404

## Admin Credentials (Login is Public)
app.route('/register', methods=['POST'])(register_user)
app.route('/login', methods=['POST'])(login_user)
app.route('/users/logout', methods=['POST'])(logout_user)
app.route("/refresh", methods=["POST"])(refresh_token)

## RSA Public Key (Public - for encrypting login credentials)
app.route("/rsa/public-key", methods=["GET"])(get_public_key)

## User Login (Public - NEW AUTH SYSTEM - supports RSA encryption)
app.route("/users/login", methods=["POST"])(login_user_detail)

## Verify Login (Public - SECURITY: One-time token verification to prevent replay attacks)
app.route("/users/verify-login", methods=["POST"])(verify_login)

## Procteded Public User-Facing Endpoints

@app.route('/chatbot-intro-ad', methods=['GET'])
# @chatbot_token_required
def protected_chatbot_intro_ad():
    return chatbot_intro_ad()

@app.route('/submit-ad-tracker', methods=['POST'])
@chatbot_token_required
def protected_submit_ad_tracker():
    return submit_ad_tracker()


@app.route('/polls/active', methods=['GET'])
@chatbot_token_required
def protected_get_active_poll():
    return get_active_poll()


@app.route('/poll/submit', methods=['POST'])
@chatbot_token_required
def protected_submit_poll_response():
    return submit_poll_response()

@app.route('/feedback/submit', methods=['POST'])
@chatbot_token_required
def protected_submit_feedback():
    return submit_feedback()


@app.route('/ad-on-menu-click', methods=['POST'])
# @chatbot_token_required
def protected_ad_on_menu_click():
    return ad_on_menu_click()


## Public User-Facing Endpoints
app.route('/save-bill-pay-chat', methods=['POST'])(save_bill_pay_chat)
app.route('/save-duplicate-bill', methods=['POST'])(save_duplicate_bill_chat)
app.route('/submenus', methods=['GET'])(get_unique_submenus)
# app.route("/chatbot-intro-ad", methods=["GET"])(chatbot_intro_ad)
# app.route("/ad-on-menu-click", methods=["POST"])(ad_on_menu_click)
# app.route("/submit-ad-tracker", methods=["POST"])(submit_ad_tracker)
# app.route("/feedback/submit", methods=["POST"])(submit_feedback)
# app.route("/polls/active", methods=["GET"])(get_active_poll)
# app.route("/poll/submit", methods=["POST"])(submit_poll_response)
app.route('/divisions', methods=['GET'])(get_divisions)
app.route('/visible-languages', methods=['GET'])(get_visible_languages)

user_ca_storage = {}


# ==========================================
# PROTECTED ENDPOINTS WITH AUTHENTICATION & AUTHORIZATION
# ==========================================

## Dashboard Features (Protected)
@app.route('/dashboard/sessions', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_get_session_counts():
    return get_session_counts()

@app.route('/dashboard/interactions-breakdown', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_interaction_breakdown():
    return interaction_breakdown()

@app.route('/dashboard/average-interaction-time', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_average_interaction_time():
    return average_interaction_time()

@app.route('/dashboard/chat-status', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_chat_status():
    return chat_status()

@app.route('/dashboard/opt-for-ebill', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_count_opt_for_ebill():
    return count_opt_for_ebill()

@app.route('/dashboard/pay-bill', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_dashboard_pay_bill():
    return dashboard_pay_bill()

@app.route('/dashboard/download-duplicate-bill', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_dashboard_download_duplicate_bill():
    return dashboard_download_duplicate_bill()

@app.route('/dashboard/complaint-status', methods=['GET'])
@token_required
@permission_required(module_name="Dashboard", crud_action="view")
def protected_dashboard_complaint_status():
    return dashboard_complaint_status()


## MIS Report Features (Protected)
@app.route('/mis/peak-hours', methods=['GET'])
@token_required
@permission_required(module_name="MIS Report", crud_action="view")
def protected_mis_peak_hours():
    return mis_peak_hours()

@app.route('/mis/avg-interaction-duration', methods=['GET'])
@token_required
@permission_required(module_name="MIS Report", crud_action="view")
def protected_mis_avg_interaction_duration():
    return mis_avg_interaction_duration()

@app.route('/mis/chat-completion-status', methods=['GET'])
@token_required
@permission_required(module_name="MIS Report", crud_action="view")
def protected_mis_chat_completion_status():
    return mis_chat_completion_status()

@app.route('/mis/pay-bill', methods=['GET'])
@token_required
@permission_required(module_name="MIS Report", crud_action="view")
def protected_mis_pay_bill():
    return mis_pay_bill()

@app.route('/mis/interactions-breakdown', methods=['GET'])
@token_required
@permission_required(module_name="MIS Report", crud_action="view")
def protected_mis_interaction_breakdown():
    return mis_interaction_breakdown()

@app.route('/mis/visually-impaired-analysis', methods=['GET'])
@token_required
@permission_required(module_name="MIS Report", crud_action="view")
def protected_visually_impaired_analysis():
    return visually_impaired_analysis()


## Menu Analysis (Protected)
@app.route('/menu/menu-analysis', methods=['GET'])
@token_required
@permission_required(module_name="Chatbot Menu", crud_action="view")
def protected_menu_analysis():
    return menu_analysis()


## API Key Master (Protected)
@app.route("/api-key-master", methods=["POST"])
@token_required
@permission_required(module_name="api-key", crud_action="create")
def protected_create_api_key():
    return create_api_key()

@app.route("/api-key-master-update", methods=["PUT"])
@token_required
@permission_required(module_name="api-key", crud_action="update")
def protected_update_api_key_by_name():
    return update_api_key_by_name()

@app.route("/get-api-keys-data", methods=["GET"])
@token_required
@permission_required(module_name="api-key", crud_action="read")
def protected_get_all_api_details():
    return get_all_api_details()

@app.route("/api-hit-breakdown", methods=["GET"])
@token_required
@permission_required(module_name="api-key", crud_action="read")
def protected_api_hit_breakdown():
    return api_hit_breakdown()

@app.route("/get-api-keys-breakdown", methods=["GET"])
@token_required
@permission_required(module_name="api-key", crud_action="read")
def protected_get_api_details_with_breakdown():
    return get_api_details_with_breakdown()


## Advertisements (Protected) - Using "Language" module as per permissions
@app.route("/add_ad", methods=["POST"])
@token_required
@permission_required(module_name="Language", crud_action="create")
def protected_add_ad():
    return add_ad()

@app.route("/update_ad", methods=["PUT"])
@token_required
@permission_required(module_name="Language", crud_action="update")
def protected_update_ad():
    return update_ad()

# @app.route("/get_ad", methods=["GET"])
# @token_required
# @permission_required(module_name="Language", crud_action="read")
# def protected_get_ad():
#     return get_ad()

@app.route("/get_ad", methods=["GET"])
@optional_token()
def protected_get_ad():
    return get_ad()

@app.route("/ads/get-ads", methods=["GET"])
@token_required
@permission_required(module_name="Language", crud_action="read")
def protected_get_all_ads():
    return get_all_ads()

@app.route('/delete-ad', methods=['DELETE'])
@token_required
@permission_required(module_name="Language", crud_action="delete")
def protected_delete_ad():
    return delete_ad()

@app.route("/get-ad-analytics", methods=["GET"])
@token_required
@permission_required(module_name="Analytics", crud_action="view")
def protected_get_ad_analytics():
    return get_ad_analytics()


## Feedback Mechanism (Protected) - Using "feedbacks" module
@app.route("/feedback/add", methods=["POST"])
@token_required
@permission_required(module_name="feedbacks", crud_action="create")
def protected_add_feedback_question():
    return add_feedback_question()

@app.route("/feedback/update/<string:question_id>", methods=["PUT"])
@token_required
@permission_required(module_name="feedbacks", crud_action="update")
def protected_update_feedback_question(question_id):
    return update_feedback_question(question_id)

@app.route("/feedback/delete/<string:question_id>", methods=['DELETE'])
@token_required
@permission_required(module_name="feedbacks", crud_action="delete")
def protected_delete_feedback_question(question_id):
    return delete_feedback_question(question_id)

@app.route("/feedback/get-questions", methods=["GET"])
@optional_token()
# @permission_required(module_name="feedbacks", crud_action="read")
def protected_get_feedback_questions():
    return get_feedback_questions()

@app.route('/get_feedback_acceptance', methods=['GET'])
@optional_token()
# @permission_required(module_name="feedbacks", crud_action="read")
def protected_get_feedback_acceptance():
    return get_feedback_acceptance()


## Polling System (Protected) - Using "polls" module
@app.route("/poll/create", methods=["POST"])
@token_required
@permission_required(module_name="polls", crud_action="create")
def protected_create_poll():
    return create_poll()

@app.route("/admin/poll/<poll_id>", methods=["PUT"])
@token_required
@permission_required(module_name="polls", crud_action="update")
def protected_update_poll(poll_id):
    return update_poll(poll_id)

@app.route("/admin/poll/<poll_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="polls", crud_action="delete")
def protected_delete_poll(poll_id):
    return delete_poll(poll_id)

@app.route("/polls", methods=["GET"])
@token_required
@permission_required(module_name="polls", crud_action="read")
def protected_get_all_polls():
    return get_all_polls()


## Intent Routes (Protected) - Using "Intent" module
@app.route("/intent/create", methods=["POST"])
@token_required
@permission_required(module_name="Intent", crud_action="create")
def protected_create_intent():
    return create_intent()

@app.route("/intents", methods=["GET"])
@token_required
@permission_required(module_name="Intent", crud_action="view")
def protected_get_intents():
    return get_intents()

@app.route("/intents/export", methods=["GET"])
@token_required
@permission_required(module_name="Intent", crud_action="view")
def protected_export_intents():
    return export_intents()

@app.route("/intent/<int:intent_id>", methods=["GET"])
@token_required
@permission_required(module_name="Intent", crud_action="view")
def protected_get_intent_by_id(intent_id):
    return get_intent_by_id(intent_id)

@app.route("/intent/<int:intent_id>", methods=["PUT"])
@token_required
@permission_required(module_name="Intent", crud_action="update")
def protected_update_intent(intent_id):
    return update_intent(intent_id)

@app.route("/intent/<int:intent_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="Intent", crud_action="delete")
def protected_delete_intent(intent_id):
    return delete_intent(intent_id)


## Intent Examples Routes (Protected) - Using "Intent" module
@app.route("/intent-examples", methods=["POST"])
@token_required
@permission_required(module_name="Intent", crud_action="create")
def protected_create_intent_example():
    return create_intent_example()

@app.route("/intent-examples", methods=["GET"])
@token_required
@permission_required(module_name="Intent", crud_action="view")
def protected_get_examples_by_intent():
    return get_examples_by_intent()

@app.route("/intent-examples/<int:intent_id>", methods=["GET"])
@token_required
@permission_required(module_name="Intent", crud_action="view")
def protected_get_example_by_id(intent_id):
    return get_example_by_id(intent_id)

@app.route("/update-intent-examples/<int:intent_id>", methods=["PUT"])
@token_required
@permission_required(module_name="Intent", crud_action="update")
def protected_update_intent_example(intent_id):
    return update_intent_example(intent_id)

@app.route("/intent-examples/<int:example_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="Intent", crud_action="delete")
def protected_delete_intent_example(example_id):
    return delete_intent_example(example_id)

@app.route("/all-intent-examples/<int:intent_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="Intent", crud_action="delete")
def protected_delete_examples_by_intent(intent_id):
    return delete_examples_by_intent(intent_id)


## User Role (Protected) - Using "roles" module
@app.route("/role/create", methods=["POST"])
@token_required
@permission_required(module_name="roles", crud_action="create")
def protected_create_role():
    return create_role()

@app.route("/roles", methods=["GET"])
@token_required
@permission_required(module_name="roles", crud_action="read")
def protected_get_roles():
    return get_roles()

@app.route("/role/<int:role_id>", methods=["GET"])
@token_required
@permission_required(module_name="roles", crud_action="read")
def protected_get_role_by_id(role_id):
    return get_role_by_id(role_id)

@app.route("/role/<int:role_id>", methods=["PUT"])
@token_required
@permission_required(module_name="roles", crud_action="update")
def protected_update_role(role_id):
    return update_role(role_id)

@app.route("/delete/role/<int:role_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="roles", crud_action="delete")
def protected_delete_role(role_id):
    return delete_role(role_id)


## Permission Matrix (Protected) - Note: No "Permissions" module in your list, keeping original
@app.route("/permission/create", methods=["POST"])
@token_required
def protected_create_permission():
    return create_permission()

@app.route("/role/permissions", methods=["GET"])
@token_required
@permission_required(module_name="roles", crud_action="read")
def protected_get_role_permissions():
    return get_permissions()

@app.route("/user/permissions", methods=["GET"])
@token_required
@permission_required(module_name="users", crud_action="read")
def protected_get_user_permissions():
    return get_permissions()

@app.route("/permission/<int:permission_id>", methods=["GET"])
@token_required
def protected_get_permission_by_id(permission_id):
    return get_permission_by_id(permission_id)

@app.route("/permission/<int:permission_id>", methods=["PUT"])
@token_required
def protected_update_permission(permission_id):
    return update_permission(permission_id)

@app.route("/permission/<int:permission_id>", methods=["DELETE"])
@token_required
def protected_delete_permission(permission_id):
    return delete_permission(permission_id)


## User Permission Mapping (Protected) - Note: No "User_Permissions" module in your list, keeping token_required only
@app.route("/mappings/create", methods=["POST"])
@token_required
def protected_create_mapping():
    return create_mapping()

@app.route("/role/mappings", methods=["GET"])
@token_required
@permission_required(module_name="roles", crud_action="read")
def protected_get_role_mappings():
    return get_mappings()

@app.route("/user/mappings", methods=["GET"])
@token_required
@permission_required(module_name="users", crud_action="read")
def protected_get_user_mappings():
    return get_mappings()

@app.route("/mappings/<int:mapping_id>", methods=["GET"])
@permission_required(module_name="role", crud_action="read")
@token_required
def protected_get_mapping_by_id(mapping_id):
    return get_mapping_by_id(mapping_id)

@app.route("/update/mappings/<int:mapping_id>", methods=["PUT"])
# @permission_required(module_name="roles", crud_action="update")
@token_required
def protected_update_mapping(mapping_id):
    return update_mapping(mapping_id)

@app.route("/user-mappings", methods=["PUT"])
@token_required
@permission_required(module_name="users", crud_action="update")
def protected_update_mapping_users():
    return update_mapping_users()

@app.route("/mapping/<int:mapping_id>", methods=["DELETE"])
@token_required
def protected_delete_mapping(mapping_id):
    return delete_mapping(mapping_id)


## Poll Analytics (Protected)
@app.route("/poll-analytics", methods=["GET"])
@token_required
@permission_required(module_name="Analytics", crud_action="view")
def protected_get_poll_summary_and_analytics():
    return get_poll_summary_and_analytics()

@app.route("/poll-analytics-details", methods=["GET"])
@token_required
@permission_required(module_name="Analytics", crud_action="view")
def protected_get_poll_analytics():
    return get_poll_analytics()


## Feedback Analytics (Protected)
@app.route("/feedback-analytics", methods=["GET"])
@token_required
@permission_required(module_name="Analytics", crud_action="view")
def protected_get_feedback_summary_and_analytics():
    return get_feedback_summary_and_analytics()


## User Module (Protected) - Using "users" module
@app.route("/users/register", methods=["POST"])
@token_required
@permission_required(module_name="users", crud_action="create")
def protected_register_user_detail():
    return register_user_detail()

@app.route("/users", methods=["GET"])
@token_required
@permission_required(module_name="users", crud_action="read")
def protected_get_all_users():
    return get_all_users()

@app.route("/update-user/<string:user_id>", methods=["PUT"])
@token_required
@permission_required(module_name="users", crud_action="update")
def protected_update_user(user_id):
    return update_user(user_id)


@app.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="users", crud_action="delete")
def protected_delete_user(user_id):
    return delete_user(user_id)

# @app.route("/get-user-permission/<int:user_id>", methods=["GET"])
# @token_required
# @permission_required(module_name="users", crud_action="read")
# def protected_get_user_permission(user_id):
#     return get_user_permission(user_id)

@app.route("/get-user-permission", methods=["GET"])
@token_required
# @permission_required(module_name="users", crud_action="read")
def protected_get_user_permission():
    return get_user_permission()


## Menu Management (Protected) - Using "menus" module
@app.route("/get_user_menu_data", methods=["GET"])
@token_required
@permission_required(module_name="menus", crud_action="read")
def protected_get_user_menu_data():
    return get_user_menu_data()

@app.route("/get_rajdhani_users", methods=["GET"])
@token_required
@permission_required(module_name="menus", crud_action="read")
def protected_get_rajdhani_users():
    return get_rajdhani_users()

@app.route('/api/create_menu_with_submenu', methods=['POST'])
@token_required
@permission_required(module_name="menus", crud_action="create")
def protected_create_menu_with_submenu():
    return create_menu_with_submenu()

# @app.route('/get_user_menus', methods=['GET'])
# @token_required
# @permission_required(module_name="menus", crud_action="read")
# def protected_get_user_menus():
#     return get_user_menus()


@app.route('/get_user_menus', methods=['GET'])
@optional_token()
def protected_get_user_menus():
    return get_user_menus()

@app.route('/menu/update-sequence', methods=['POST'])
@token_required
@permission_required(module_name="menus", crud_action="update")
def protected_update_menu_sequence():
    return update_menu_sequence()

@app.route('/delete_submenu/<int:submenu_id>', methods=['DELETE'])
@token_required
@permission_required(module_name="menus", crud_action="delete")
def protected_delete_submenu(submenu_id):
    return delete_submenu(submenu_id)

@app.route("/delete_menu/<int:menu_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="menus", crud_action="delete")
def protected_delete_menu(menu_id):
    return delete_menu(menu_id)


## Rasa Dynamic Files Builder (Protected) - Note: No "Rasa_Builder" in permissions, using token_required only
# @app.route('/export_domain', methods=['GET'])
# @token_required
# def protected_export_domain():
#     return export_domain()

@app.route('/export_domain', methods=['GET'])
@optional_token()
def protected_export_domain():
    return export_domain()

# @app.route('/download_stories', methods=['GET'])
# @token_required
# def protected_download_stories():
#     return download_stories()

@app.route('/download_stories', methods=['GET'])
@optional_token()
def protected_download_stories():
    return download_stories()

# @app.route('/rebuild_intent_file', methods=['GET'])
# @token_required
# def protected_rebuild_intent_file():
#     return rebuild_intent_file()

@app.route('/rebuild_intent_file', methods=['GET'])
@optional_token()
def protected_rebuild_intent_file():
    return rebuild_intent_file()


## Language Master (Protected) - Using specific language modules
@app.route("/add-language", methods=["POST"])
@token_required
@permission_required(module_name="language-create", crud_action="create")
def protected_create_language():
    return create_language()

@app.route("/get-languages", methods=["GET"])
@token_required
@permission_required(module_name="language-read", crud_action="read")
def protected_get_languages():
    return get_languages()

@app.route("/language/<int:language_id>", methods=["GET"])
@token_required
@permission_required(module_name="language-read", crud_action="read")
def protected_get_language(language_id):
    return get_language(language_id)

@app.route("/update/language/<int:language_id>", methods=["PUT"])
@token_required
@permission_required(module_name="language-update", crud_action="update")
def protected_update_language(language_id):
    return update_language(language_id)

@app.route("/delete/language/<int:language_id>", methods=["DELETE"])
@token_required
@permission_required(module_name="language-delete", crud_action="delete")
def protected_delete_language(language_id):
    return delete_language(language_id)


## UtterMessage CRUD Routes (Protected) - Using "utter" module
@app.route("/create_utter_message", methods=["POST"])
@token_required
@permission_required(module_name="utter", crud_action="create")
def protected_create_utter_message():
    return create_utter_message()

@app.route("/get_all/utter_messages", methods=["GET"])
@token_required
@permission_required(module_name="utter", crud_action="read")
def protected_get_all_utter_messages():
    return get_all_utter_messages()

@app.route("/get/utter_messages/<uuid:uid>", methods=["GET"])
@token_required
@permission_required(module_name="utter", crud_action="read")
def protected_get_utter_message(uid):
    return get_utter_message(uid)

@app.route("/update/utter_messages/<uuid:uid>", methods=["PUT"])
@token_required
@permission_required(module_name="utter", crud_action="update")
def protected_update_utter_message(uid):
    return update_utter_message(uid)

@app.route("/delete/utter_messages/<uuid:uid>", methods=["DELETE"])
@token_required
@permission_required(module_name="utter", crud_action="delete")
def protected_delete_utter_message(uid):
    return delete_utter_message(uid)

# @app.route("/get_utter_messages", methods=["GET"])
# @token_required
# @permission_required(module_name="utter", crud_action="read")
# def protected_updated_get_utter_messages():
#     return updated_get_utter_messages()

@app.route("/get_utter_messages", methods=["GET"])
@optional_token()
def protected_updated_get_utter_messages():
    return updated_get_utter_messages()


## Fallback CRUD (Protected) - Using "fallback" module
@app.route("/create-fallback", methods=["POST"])
@token_required
@permission_required(module_name="fallback", crud_action="create")
def protected_create_fallback():
    return create_fallback()

@app.route("/get-fallback", methods=["GET"])
@token_required
@permission_required(module_name="fallback", crud_action="read")
def protected_get_all_fallbacks():
    return get_all_fallbacks()

@app.route("/update-fallback/<int:fallback_id>", methods=["PUT"])
@token_required
@permission_required(module_name="fallback", crud_action="update")
def protected_update_fallback(fallback_id):
    return update_fallback(fallback_id)


## Submenu Fallback CRUD (Protected) - Using "fallback" module

@app.route("/create/submenu-fallback", methods=["POST"])
@token_required
@permission_required(module_name="fallback", crud_action="update")
def protected_create_submenu_fallback():
    return create_submenu_fallback()

@app.route("/get-all/submenu-fallback", methods=["GET"])
@token_required
@permission_required(module_name="fallback", crud_action="read")
def protected_get_all_submenu_fallbacks():
    return get_all_submenu_fallbacks()

@app.route("/get-all/submenu-fallback/categories", methods=["GET"])
@token_required
@permission_required(module_name="fallback", crud_action="read")
def protected_get_all_submenu_categories():
    return get_all_submenu_categories()

@app.route("/get/submenu-fallback/<string:category>", methods=["GET"])
@token_required
@permission_required(module_name="fallback", crud_action="read")
def protected_get_submenu_fallback_by_category(category):
    return get_submenu_fallback_by_category(category)


@app.route("/get-global-fallback", methods=["GET"])
@chatbot_token_required
def protected_get_all_global_fallback():
    return get_all_global_fallbacks()

# app.route("/get-global-fallback", methods=["GET"])(get_all_global_fallbacks)

@app.route("/update/submenu-fallback/<string:category>", methods=["PUT"])
@token_required
@permission_required(module_name="fallback", crud_action="update")
def protected_update_submenu_fallback(category):
    return update_submenu_fallback(category)

@app.route("/delete/submenu-fallback/<string:category>", methods=["DELETE"])
@token_required
@permission_required(module_name="fallback", crud_action="update")
def protected_delete_submenu_fallback(category):
    return delete_submenu_fallback(category)


# ==========================================
# APPLICATION STARTUP
# ==========================================

# from database import Base
# print(Base.metadata.tables.keys(), "---------------------=============")

# with app.app_context():
#     populate_tables(reset_mode="auto")

# ==========================================
# APPLICATION STARTUP
# ==========================================

from database import Base
print(Base.metadata.tables.keys(), "---------------------=============")

# Check if system is initialized instead of running populate_tables on each worker startup
system_initialized = False
with app.app_context():
    try:
        with engine.begin() as connection:
            if is_system_initialized(connection):
                print("System already initialized. Worker is ready to serve requests.")
                system_initialized = True
            else:
                print("System not initialized. Run 'python init_db.py' before starting workers.")
                system_initialized = False
    except Exception as e:
        print(f"Could not check initialization status: {e}")
        system_initialized = False

# Start scheduler ONLY after system is initialized
if system_initialized:
    with scheduler_lock:
        # Double-check locking pattern: verify again after acquiring lock
        if not scheduler.running:
            scheduler.start()
            print("Background scheduler started successfully")
else:
    print("Background scheduler will start after system initialization")

if __name__ == "__main__":
    app.run(debug=False, port=3000, host="0.0.0.0")

