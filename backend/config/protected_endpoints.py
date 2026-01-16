"""
Configuration file defining which endpoints require authentication and authorization.

This file maps endpoint paths to their required permissions.
Format: {
    "endpoint_path": {
        "auth_required": True/False,  # Whether authentication is required
        "module": "Module Name",       # Module name for permission check
        "action": "crud_action"        # CRUD action (create, read, update, delete)
    }
}

Endpoints not listed here will be accessible without authentication.
"""

PROTECTED_ENDPOINTS = {
    # Dashboard Features - Read access
    "/dashboard/sessions": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },
    "/dashboard/interactions-breakdown": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },
    "/dashboard/average-interaction-time": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },
    "/dashboard/chat-status": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },
    "/dashboard/opt-for-ebill": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },
    "/dashboard/pay-bill": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },
    "/dashboard/download-duplicate-bill": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },
    "/dashboard/complaint-status": {
        "auth_required": True,
        "module": "Dashboard",
        "action": "read"
    },

    # MIS Report Features - Read access
    "/mis/peak-hours": {
        "auth_required": True,
        "module": "MIS_Reports",
        "action": "read"
    },
    "/mis/avg-interaction-duration": {
        "auth_required": True,
        "module": "MIS_Reports",
        "action": "read"
    },
    "/mis/chat-completion-status": {
        "auth_required": True,
        "module": "MIS_Reports",
        "action": "read"
    },
    "/mis/pay-bill": {
        "auth_required": True,
        "module": "MIS_Reports",
        "action": "read"
    },
    "/mis/interactions-breakdown": {
        "auth_required": True,
        "module": "MIS_Reports",
        "action": "read"
    },
    "/mis/visually-impaired-analysis": {
        "auth_required": True,
        "module": "MIS_Reports",
        "action": "read"
    },

    # Menu Analysis
    "/menu/menu-analysis": {
        "auth_required": True,
        "module": "Menu_Analysis",
        "action": "read"
    },

    # API Key Master
    "/api-key-master": {
        "auth_required": True,
        "module": "API_Key_Master",
        "action": "create"
    },
    "/api-key-master-update": {
        "auth_required": True,
        "module": "API_Key_Master",
        "action": "update"
    },
    "/get-api-keys-data": {
        "auth_required": True,
        "module": "API_Key_Master",
        "action": "read"
    },
    "/api-hit-breakdown": {
        "auth_required": True,
        "module": "API_Key_Master",
        "action": "read"
    },
    "/get-api-keys-breakdown": {
        "auth_required": True,
        "module": "API_Key_Master",
        "action": "read"
    },

    # Advertisements
    "/add_ad": {
        "auth_required": True,
        "module": "Advertisements",
        "action": "create"
    },
    "/update_ad": {
        "auth_required": True,
        "module": "Advertisements",
        "action": "update"
    },
    "/get_ad": {
        "auth_required": True,
        "module": "Advertisements",
        "action": "read"
    },
    "/ads/get-ads": {
        "auth_required": True,
        "module": "Advertisements",
        "action": "read"
    },
    "/delete-ad": {
        "auth_required": True,
        "module": "Advertisements",
        "action": "delete"
    },
    "/get-ad-analytics": {
        "auth_required": True,
        "module": "Advertisements",
        "action": "read"
    },

    # Feedback Mechanism
    "/feedback/add": {
        "auth_required": True,
        "module": "Feedback",
        "action": "create"
    },
    "/feedback/update/<string:question_id>": {
        "auth_required": True,
        "module": "Feedback",
        "action": "update"
    },
    "/feedback/delete/<string:question_id>": {
        "auth_required": True,
        "module": "Feedback",
        "action": "delete"
    },
    "/feedback/get-questions": {
        "auth_required": True,
        "module": "Feedback",
        "action": "read"
    },
    "/get_feedback_acceptance": {
        "auth_required": True,
        "module": "Feedback",
        "action": "read"
    },

    # Polling System
    "/poll/create": {
        "auth_required": True,
        "module": "Polls",
        "action": "create"
    },
    "/admin/poll/<poll_id>": {
        "auth_required": True,
        "module": "Polls",
        "action": "update"
    },
    "/polls": {
        "auth_required": True,
        "module": "Polls",
        "action": "read"
    },

    # Intent Management
    "/intent/create": {
        "auth_required": True,
        "module": "Intents",
        "action": "create"
    },
    "/intents": {
        "auth_required": True,
        "module": "Intents",
        "action": "read"
    },
    "/intents/export": {
        "auth_required": True,
        "module": "Intents",
        "action": "read"
    },
    "/intent/<int:intent_id>": {
        "auth_required": True,
        "module": "Intents",
        "action": "update"
    },

    # User Role
    "/role/create": {
        "auth_required": True,
        "module": "User_Roles",
        "action": "create"
    },
    "/roles": {
        "auth_required": True,
        "module": "User_Roles",
        "action": "read"
    },
    "/role/<int:role_id>": {
        "auth_required": True,
        "module": "User_Roles",
        "action": "update"
    },

    # Permission Matrix
    "/permission/create": {
        "auth_required": True,
        "module": "Permissions",
        "action": "create"
    },
    "/permissions": {
        "auth_required": True,
        "module": "Permissions",
        "action": "read"
    },
    "/permission/<int:permission_id>": {
        "auth_required": True,
        "module": "Permissions",
        "action": "update"
    },

    # User Permission Mapping
    "/mappings/create": {
        "auth_required": True,
        "module": "User_Permissions",
        "action": "create"
    },
    "/mappings": {
        "auth_required": True,
        "module": "User_Permissions",
        "action": "read"
    },
    "/mappings/<int:mapping_id>": {
        "auth_required": True,
        "module": "User_Permissions",
        "action": "update"
    },
    "/user-mappings": {
        "auth_required": True,
        "module": "User_Permissions",
        "action": "update"
    },

    # Poll Analytics
    "/poll-analytics": {
        "auth_required": True,
        "module": "Poll_Analytics",
        "action": "read"
    },
    "/poll-analytics-details": {
        "auth_required": True,
        "module": "Poll_Analytics",
        "action": "read"
    },

    # Feedback Analytics
    "/feedback-analytics": {
        "auth_required": True,
        "module": "Feedback_Analytics",
        "action": "read"
    },

    # User Module
    "/users/register": {
        "auth_required": True,
        "module": "Users",
        "action": "create"
    },
    "/users": {
        "auth_required": True,
        "module": "Users",
        "action": "read"
    },
    "/update-user/<string:user_id>": {
        "auth_required": True,
        "module": "Users",
        "action": "update"
    },
    "/get-user-permission/<int:user_id>": {
        "auth_required": True,
        "module": "Users",
        "action": "read"
    },

    # Menu Management
    "/get_user_menu_data": {
        "auth_required": True,
        "module": "Menu_Management",
        "action": "read"
    },
    "/get_rajdhani_users": {
        "auth_required": True,
        "module": "Menu_Management",
        "action": "read"
    },
    "/api/create_menu_with_submenu": {
        "auth_required": True,
        "module": "Menu_Management",
        "action": "create"
    },
    "/get_user_menus": {
        "auth_required": True,
        "module": "Menu_Management",
        "action": "read"
    },
    "/menu/update-sequence": {
        "auth_required": True,
        "module": "Menu_Management",
        "action": "update"
    },
    "/delete_submenu/<int:submenu_id>": {
        "auth_required": True,
        "module": "Menu_Management",
        "action": "delete"
    },
    "/delete_menu/<int:menu_id>": {
        "auth_required": True,
        "module": "Menu_Management",
        "action": "delete"
    },

    # Rasa Dynamic Files Builder
    "/export_domain": {
        "auth_required": True,
        "module": "Rasa_Builder",
        "action": "read"
    },
    "/download_stories": {
        "auth_required": True,
        "module": "Rasa_Builder",
        "action": "read"
    },
    "/rebuild_intent_file": {
        "auth_required": True,
        "module": "Rasa_Builder",
        "action": "update"
    },

    # Language Master
    "/add-language": {
        "auth_required": True,
        "module": "Languages",
        "action": "create"
    },
    "/get-languages": {
        "auth_required": True,
        "module": "Languages",
        "action": "read"
    },
    "/language/<int:language_id>": {
        "auth_required": True,
        "module": "Languages",
        "action": "update"
    },

    # UtterMessage CRUD
    "/create_utter_message": {
        "auth_required": True,
        "module": "Utter_Messages",
        "action": "create"
    },
    "/utter_messages": {
        "auth_required": True,
        "module": "Utter_Messages",
        "action": "read"
    },
    "/utter_messages/<uuid:uid>": {
        "auth_required": True,
        "module": "Utter_Messages",
        "action": "update"
    },
    "/get_utter_messages": {
        "auth_required": True,
        "module": "Utter_Messages",
        "action": "read"
    },

    # Fallback CRUD
    "/create-fallback": {
        "auth_required": True,
        "module": "Fallback",
        "action": "create"
    },
    "/get-fallback": {
        "auth_required": True,
        "module": "Fallback",
        "action": "read"
    },
    "/update-fallback/<int:fallback_id>": {
        "auth_required": True,
        "module": "Fallback",
        "action": "update"
    },
}

# Endpoints that should be accessible without authentication
PUBLIC_ENDPOINTS = [
    "/webhook",
    "/menu_run_flow",
    "/register_menu_run_flow",
    "/ca_number_register_run_flow",
    "/fallback",
    "/reset_fallback",
    "/validate_ca",
    "/get_ca",
    "/get_session_data",
    "/validate-language",
    "/validate_otp",
    "/validate_email",
    "/validate_mobile",
    "/get_order_status",
    "/generate_duplicate_bill_pdf",
    "/complaint_status",
    "/speech-to-text",
    "/view-icon/<path:filename>",
    "/generated_pdfs/<filename>",
    "/ad_content/<filename>",
    "/Media/<path:relative_path>",
    "/Media/BSES_ICONS/<filename>",
    "/register",
    "/login",
    "/users/login",  # Login endpoint should be public
    "/save-bill-pay-chat",
    "/save-duplicate-bill",
    "/submenus",
    "/chatbot-intro-ad",
    "/ad-on-menu-click",
    "/submit-ad-tracker",
    "/feedback/submit",
    "/polls/active",
    "/poll/submit",
    "/divisions",
    "/visible-languages",
]
