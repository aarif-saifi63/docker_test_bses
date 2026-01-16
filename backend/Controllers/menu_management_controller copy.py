
import json
import uuid
from utils.input_validator import InputValidator
from utils.file_security_helper import FileSecurityHelper
import magic
from utils.request_security import validate_multipart_request
import re
from flask import app, request, jsonify
from Models.action_model import ActionsV
from Models.intent_example_model import IntentExampleV
from Models.intent_model import IntentV
from Models.language_model import Language
from Models.menu_option_model import MenuOptionV
from Models.story_model import Story
from Models.story_steps_all_model import StoryStepsAll
from Models.sub_menu_option_model import SubMenuOptionV
from Models.users_model import User
from Models.utter_model import UtterV
from database import SessionLocal
import os
import logging
from flask import request, jsonify
from sqlalchemy.orm import joinedload
from sqlalchemy import any_
import yaml
from flask import Response
from sqlalchemy import distinct
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.utils import secure_filename
from sqlalchemy.sql import func
import logging


logger = logging.getLogger(__name__)


def get_user_menu_data():
    db = SessionLocal()
    try:
        user_name = request.args.get("user_name")
        if not user_name:
            return jsonify({"error": "user_name parameter is required"}), 400

        user = db.query(User).filter_by(name=user_name).first()
        if not user:
            return jsonify({"error": f"User '{user_name}' not found"}), 404

        menus = (
            db.query(MenuOptionV)
            .filter_by(user_id=user.id)
            .options(joinedload(MenuOptionV.submenus))
            .order_by(MenuOptionV.menu_sequence.asc())
            .all()
        )   

        response_data = []
        total_sub_menus = 0

        for menu in menus:
            sub_menu_list = []

            for sub_menu in menu.submenus:
                total_sub_menus += 1

                # Fetch intents for this submenu
                intents = (
                    db.query(IntentV)
                    .filter(IntentV.submenu_id.contains([sub_menu.id]))
                    .options(joinedload(IntentV.examples))
                    .all()
                )

                intents_list = []
                for intent in intents:
                    # Determine response type
                    has_utter = db.query(UtterV)\
                        .filter_by(submenu_id=sub_menu.id)\
                        .first()
                    has_action = db.query(ActionsV)\
                        .filter_by(submenu_id=sub_menu.id)\
                        .first()

                    response_type = "none"
                    if has_utter:
                        response_type = "static"
                    elif has_action:
                        response_type = "dynamic"

                    # Actions for this intent
                    actions = (
                        db.query(ActionsV)
                        .filter_by(submenu_id=sub_menu.id)
                        .all()
                    )
                    actions_list = [{"id": a.id, "name": a.name} for a in actions]

                    # Utters for this intent
                    utters = (
                        db.query(UtterV)
                        .filter_by(submenu_id=sub_menu.id)
                        .all()
                    )
                    utters_list = [{"id": u.id, "name": u.name, "response": u.response} for u in utters]

                    intents_list.append({
                        "intent_id": intent.id,
                        "name": intent.name,
                        "examples": [{"id": ex.id, "example": ex.example} for ex in intent.examples],
                        "response_type": response_type,
                        "actions": actions_list,
                        "utters": utters_list
                    })

                # Fetch story for this submenu
                story = db.query(Story).filter_by(submenu_id=sub_menu.id).first()
                story_dict = {"id": story.id, "story_name": story.story_name} if story else None

                sub_menu_list.append({
                    "sub_menu_id": sub_menu.id,
                    "submenu_sequence": sub_menu.submenu_sequence,
                    "name": sub_menu.name,
                    "lang": sub_menu.lang,
                    "is_visible": sub_menu.is_visible,
                    "icon_path": sub_menu.icon_path,  # Added submenu icon path
                    "intents": intents_list,
                    "story": story_dict
                })

                # Sort submenus in ascending order before adding to response
                # sub_menu_list = sorted(sub_menu_list, key=lambda x: x["submenu_sequence"])
                # Safely sort submenus (handles None values)
                sub_menu_list = sorted(
                    sub_menu_list,
                    key=lambda x: (x["submenu_sequence"] is None, x["submenu_sequence"] or 0)
                )


            response_data.append({
                "menu_id": menu.id,
                "menu_sequence": menu.menu_sequence,
                "name": menu.name,
                "lang": menu.lang,
                "is_visible": menu.is_visible,
                "icon_path": menu.icon_path,  # Added menu icon path
                "submenus": sub_menu_list
            })

        result = {
            "user_name": user.name,
            "user_id": user.id,
            "total_menu_options": len(menus),
            "total_sub_menu_options": total_sub_menus,
            "menu_options": response_data
        }

        return jsonify({
            "data": result,
            "status": True,
            "message": "Data fetched successfully"
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

def get_rajdhani_users():
    try:
        db = SessionLocal()
        # Fetch only Rajdhani users
        rajdhani_users = db.query(User).filter(User.name.ilike('%Rajdhani%')).all()

        if not rajdhani_users:
            return jsonify({"message": "No Rajdhani users found"}), 404

        # Format response
        result = [
            {
                "id": user.id,
                "name": user.name,
                "lang": user.lang,
                "subsidiary_type": user.subsidiary_type
            }
            for user in rajdhani_users
        ]

        return jsonify({
            "data": result,
            "total_rajdhani_users": len(result),
            "status": True
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()




# --- Endpoint ---
# def create_menu_with_submenu():
#     """
#     Expected JSON payload:
#     {
#         "user_id": 42,
#         "name": "Main Support",
#         "lang": "en",
#         "is_visible": true,
#         "submenus": [
#             {
#                 "name": "Billing Help",
#                 "lang": "en",
#                 "is_visible": true,
#                 "intents": [
#                     {
#                         "name": "billing_inquiry",
#                         "examples": ["How much do I owe?", "billing amount"],
#                         "actions": ["show_balance", "send_invoice"]
#                     },
#                     {
#                         "name": "refund_request",
#                         "examples": ["I want a refund", "refund policy"],
#                         "actions": ["start_refund"]
#                     }
#                 ],
#                 "story_name": "Billing New Help Auto Story"
#             }
#         ]
#     }
#     """
#     payload = request.get_json(force=True)

#     db = SessionLocal()

#     try:
#         # Extract main menu info directly
#         user_id = int(payload["user_id"])
#         menu_name = payload.get("name")
#         lang = payload.get("lang")
#         is_visible = bool(payload.get("is_visible", True))
#         submenus_payload = payload.get("submenus", [])

#         if not menu_name:
#             return jsonify({"error": "menu name is required"}), 400
#         if not submenus_payload:
#             return jsonify({"error": "at least one submenu is required"}), 400

#         created_submenus_summary = []

#         # ✅ Begin transaction
#         with db.begin():
#             # 1️⃣ Create main menu
#             menu = MenuOptionV(
#                 user_id=user_id,
#                 name=menu_name,
#                 lang=lang,
#                 is_visible=is_visible
#             )
#             db.add(menu)
#             db.flush()  # get menu.id

#             # 2️⃣ Loop through submenus
#             for submenu_data in submenus_payload:
#                 submenu = SubMenuOptionV(
#                     menu_id=menu.id,
#                     user_id=user_id,
#                     name=submenu_data.get("name"),
#                     lang=submenu_data.get("lang"),
#                     is_visible=bool(submenu_data.get("is_visible", True))
#                 )
#                 db.add(submenu)
#                 db.flush()

#                 created_intents = []
#                 created_actions = []
#                 created_story_steps = []

#                 # 3️⃣ Handle intents, examples, and actions
#                 for intent_data in submenu_data.get("intents", []):
#                     intent_name = intent_data.get("name")
#                     if not intent_name:
#                         continue

#                     # Create intent
#                     intent = IntentV(name=intent_name, submenu_id=[submenu.id])
#                     db.add(intent)
#                     db.flush()
#                     created_intents.append(intent)

#                     # Add examples
#                     for ex in intent_data.get("examples", []):
#                         if ex:
#                             db.add(IntentExampleV(example=ex, intent_id=intent.id))

#                     # Create actions
#                     for action_name in intent_data.get("actions", []):
#                         if not action_name:
#                             continue
#                         action = ActionsV(name=action_name, submenu_id=submenu.id)
#                         db.add(action)
#                         db.flush()
#                         created_actions.append(action)

#                         # Story step (intent name + action name)
#                         created_story_steps.append(
#                             StoryStepsAll(
#                                 story_id=None,  # will link later
#                                 intent=intent_name,
#                                 action=action_name
#                             )
#                         )

#                     # Intent-only step if no actions
#                     if not intent_data.get("actions"):
#                         created_story_steps.append(
#                             StoryStepsAll(
#                                 story_id=None,
#                                 intent=intent_name,
#                                 action=None
#                             )
#                         )

#                 # 4️⃣ Create story for this submenu
#                 story_name = submenu_data.get("story_name") or f"Story for {submenu.name}"
#                 story = Story(story_name=story_name, user_id=user_id)
#                 db.add(story)
#                 db.flush()

#                 # 5️⃣ Attach story_id to story steps
#                 for step in created_story_steps:
#                     step.story_id = story.id
#                     db.add(step)

#                 # Collect all created data
#                 created_submenus_summary.append({
#                     "submenu": {"id": submenu.id, "name": submenu.name},
#                     "intents": [{"id": it.id, "name": it.name} for it in created_intents],
#                     "actions": [{"id": a.id, "name": a.name} for a in created_actions],
#                     "story": {"id": story.id, "story_name": story.story_name},
#                     "story_steps": [{"intent": s.intent, "action": s.action} for s in created_story_steps]
#                 })

#         # ✅ Transaction automatically commits here if successful
#         return jsonify({
#             "message": "Created successfully",
#             "status": True,
#             "data": {"id": menu.id, "name": menu.name},
#         }), 201

#     except Exception as e:
#         db.rollback()
#         app.logger.error(f"Transaction failed: {str(e)}")
#         return jsonify({"error": "Transaction failed", "details": str(e)}), 500
#     finally:
#         db.close()


# def create_menu_with_submenu():
#     """
#     Extended version: now also maps UtterV (utter responses) with each intent.
#     """
#     payload = request.get_json(force=True)
#     db = SessionLocal()

#     try:
#         # Extract main menu info directly
#         user_id = int(payload["user_id"])
#         menu_name = payload.get("name")
#         lang = payload.get("lang")
#         is_visible = bool(payload.get("is_visible", True))
#         submenus_payload = payload.get("submenus", [])

#         if not menu_name:
#             return jsonify({"error": "menu name is required"}), 400
#         if not submenus_payload:
#             return jsonify({"error": "at least one submenu is required"}), 400

#         created_submenus_summary = []

#         with db.begin():

#             # 🔹 Get count of menus for this user_id
#             existing_count = (
#                 db.query(MenuOptionV)
#                 .filter(MenuOptionV.user_id == user_id)
#                 .count()
#             )

#             # 1️⃣ Create main menu
#             menu = MenuOptionV(
#                 user_id=user_id,
#                 name=menu_name,
#                 lang=lang,
#                 is_visible=is_visible,
#                 menu_sequence=existing_count+1
#             )
#             db.add(menu)
#             db.flush()

#             # 2️⃣ Loop through submenus
#             for submenu_data in submenus_payload:
#                 submenu = SubMenuOptionV(
#                     menu_id=menu.id,
#                     user_id=user_id,
#                     name=submenu_data.get("name"),
#                     lang=submenu_data.get("lang"),
#                     is_visible=bool(submenu_data.get("is_visible", True))
#                 )
#                 db.add(submenu)
#                 db.flush()

#                 created_intents = []
#                 created_actions = []
#                 created_utters = []
#                 created_story_steps = []

#                 # 3️⃣ Handle intents
#                 for intent_data in submenu_data.get("intents", []):
#                     intent_name = intent_data.get("name")
#                     if not intent_name:
#                         continue

#                     # Create intent
#                     intent = IntentV(name=intent_name, submenu_id=[submenu.id])
#                     db.add(intent)
#                     db.flush()
#                     created_intents.append(intent)

#                     # Add examples
#                     for ex in intent_data.get("examples", []):
#                         if ex:
#                             db.add(IntentExampleV(example=ex, intent_id=intent.id))

#                     # 4️⃣ Create actions
#                     for action_name in intent_data.get("actions", []):
#                         if not action_name:
#                             continue
#                         action = ActionsV(name=action_name, submenu_id=submenu.id)
#                         db.add(action)
#                         db.flush()
#                         created_actions.append(action)

#                         # Story step: intent → action
#                         created_story_steps.append(
#                             StoryStepsAll(
#                                 story_id=None,
#                                 intent=intent_name,
#                                 action=action_name
#                             )
#                         )

#                     # 5️⃣ Create utters
#                     for utter_data in intent_data.get("utters", []):
#                         utter_name = utter_data.get("name")
#                         response = utter_data.get("response")
#                         if not utter_name or not response:
#                             continue

#                         utter = UtterV(
#                             name=utter_name,
#                             response=response,
#                             submenu_id=submenu.id
#                         )
#                         db.add(utter)
#                         db.flush()
#                         created_utters.append(utter)

#                         # Story step: intent → utter
#                         created_story_steps.append(
#                             StoryStepsAll(
#                                 story_id=None,
#                                 intent=intent_name,
#                                 action=utter_name  # treat utter name like action name
#                             )
#                         )

#                     # Intent-only step (no actions or utters)
#                     if not intent_data.get("actions") and not intent_data.get("utters"):
#                         created_story_steps.append(
#                             StoryStepsAll(
#                                 story_id=None,
#                                 intent=intent_name,
#                                 action=None
#                             )
#                         )

#                 # 6️⃣ Create story for this submenu
#                 story_name = submenu_data.get("story_name") or f"Story for {submenu.name}"
#                 story = Story(story_name=story_name, user_id=user_id)
#                 db.add(story)
#                 db.flush()

#                 # 7️⃣ Attach story_id to story steps
#                 for step in created_story_steps:
#                     step.story_id = story.id
#                     db.add(step)

#                 created_submenus_summary.append({
#                     "submenu": {"id": submenu.id, "name": submenu.name},
#                     "intents": [{"id": it.id, "name": it.name} for it in created_intents],
#                     "actions": [{"id": a.id, "name": a.name} for a in created_actions],
#                     "utters": [{"id": u.id, "name": u.name, "response": u.response} for u in created_utters],
#                     "story": {"id": story.id, "story_name": story.story_name},
#                     "story_steps": [{"intent": s.intent, "action": s.action} for s in created_story_steps]
#                 })

#         # ✅ Commit success
#         return jsonify({
#             "message": "Created successfully",
#             "status": True,
#             "data": {"id": menu.id, "name": menu.name},
#             "details": created_submenus_summary
#         }), 201

#     except Exception as e:
#         db.rollback()
#         # app.logger.error(f"Transaction failed: {str(e)}")
#         return jsonify({"error": "Transaction failed", "details": str(e)}), 500
#     finally:
#         db.close()

# Where to store icons - SECURE: Store outside webroot in production
UPLOAD_BASE_PATH = "Media/BSES_ICONS"

def create_menu_with_submenu():
    db = SessionLocal()
    try:
        # SECURITY: Validate multipart request using centralized security module
        is_valid, error_message = validate_multipart_request()
        if not is_valid:
            return jsonify({"status": False, "message": error_message}), 400

        form = request.form

        try:
            user_id = int(form.get("user_id"))
        except (ValueError, TypeError):
            return jsonify({"error": "user_id is required and must be integer"}), 400

        menu_id = form.get("menu_id")
        menu_name = form.get("name")
        lang = form.get("lang")
        is_visible = form.get("is_visible", "true").lower() in ("1", "true", "yes")

        is_valid, msg = InputValidator.validate_name(menu_name, "menu name")
        if not is_valid:
            return jsonify({"status": False, "message": msg}), 400

        # --- parse submenus safely ---
        raw_submenus = form.get("submenus", "[]")
        try:
            submenus_payload = json.loads(raw_submenus)
        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON in 'submenus' field"}), 400

        if not menu_name:
            return jsonify({"error": "menu name is required"}), 400
        if not submenus_payload:
            return jsonify({"error": "at least one submenu is required"}), 400

        # --- create folder ---
        menu_folder_path = os.path.join(UPLOAD_BASE_PATH)
        try:
            os.makedirs(menu_folder_path, exist_ok=True)
        except OSError:
            logger.error(f"Failed to create menu folder for user {user_id}")
            return jsonify({"error": "Failed to create storage directory"}), 500

        menu_icon_file = request.files.get("menu_icon")
        created_or_updated_summary = []

        try:
            with db.begin():
                # ---------------- MENU ----------------
                if menu_id:
                    try:
                        menu = db.query(MenuOptionV).filter_by(id=menu_id, user_id=user_id).first()
                    except SQLAlchemyError as e:
                        logger.error(f"Database query error for user {user_id}: {type(e).__name__}")
                        return jsonify({"error": "Failed to retrieve menu"}), 500
                    
                    if not menu:
                        return jsonify({"error": f"Menu with id {menu_id} not found"}), 404
                    
                    menu.name = menu_name
                    menu.lang = lang
                    menu.is_visible = is_visible
                    
                    if menu_icon_file and menu_icon_file.filename:
                        success, icon_path, error = FileSecurityHelper.validate_and_save_file(
                            menu_icon_file,
                            upload_dir=menu_folder_path,
                            allowed_categories=["image"]
                        )
                        if not success:
                            return jsonify({
                                "status": False,
                                "message": f"Menu icon upload failed: {error}"
                            }), 400
                        menu.icon_path = icon_path
                else:
                    menu_icon_path = None
                    if menu_icon_file and menu_icon_file.filename:
                        success, icon_path, error = FileSecurityHelper.validate_and_save_file(
                            menu_icon_file,
                            upload_dir=menu_folder_path,
                            allowed_categories=["image"]
                        )
                        if not success:
                            return jsonify({
                                "status": False,
                                "message": f"Menu icon upload failed: {error}"
                            }), 400
                        menu_icon_path = f"Media/{icon_path}"

                    try:
                        # FIXED: Use max sequence instead of count to avoid conflicts
                        max_sequence = db.query(func.max(MenuOptionV.menu_sequence)).filter(MenuOptionV.user_id == user_id).scalar()
                        next_sequence = (max_sequence or 0) + 1
                    except SQLAlchemyError as e:
                        logger.error(f"Database sequence error for user {user_id}: {type(e).__name__}")
                        return jsonify({"error": "Failed to calculate menu sequence"}), 500

                    menu = MenuOptionV(
                        user_id=user_id,
                        name=menu_name,
                        lang=lang,
                        is_visible=is_visible,
                        menu_sequence=next_sequence,
                        icon_path=menu_icon_path,
                    )
                    db.add(menu)
                    
                    try:
                        db.flush()
                    except IntegrityError:
                        logger.error(f"Integrity constraint violation for user {user_id}")
                        return jsonify({"error": "Menu creation failed due to constraint violation"}), 409
                    except SQLAlchemyError as e:
                        logger.error(f"Database flush error for user {user_id}: {type(e).__name__}")
                        return jsonify({"error": "Failed to create menu"}), 500

                # ---------------- SUBMENUS ----------------
                try:
                    existing_submenus = {
                        sm.id: sm for sm in db.query(SubMenuOptionV)
                        .filter_by(menu_id=menu.id, user_id=user_id)
                        .all()
                    }
                except SQLAlchemyError as e:
                    logger.error(f"Failed to query submenus for user {user_id}: {type(e).__name__}")
                    return jsonify({"error": "Failed to retrieve existing submenus"}), 500

                existing_count = len(existing_submenus)
                new_sequence_start = existing_count + 1

                for idx, submenu_data in enumerate(submenus_payload):
                    submenu_id = submenu_data.get("sub_menu_id") or submenu_data.get("id")
                    submenu_name = submenu_data.get("name")
                    submenu_lang = submenu_data.get("lang")
                    submenu_visible = bool(submenu_data.get("is_visible", True))
                    submenu_icon_file = request.files.get(f"submenu_icon_{idx}")

                    submenu_icon_path = None
                    if submenu_icon_file and submenu_icon_file.filename:
                        success, icon_path, error = FileSecurityHelper.validate_and_save_file(
                            submenu_icon_file,
                            upload_dir=menu_folder_path,
                            allowed_categories=["image"]
                        )
                        if not success:
                            return jsonify({
                                "status": False,
                                "message": f"Submenu icon upload failed: {error}",
                                "error": f"Submenu icon upload failed for '{submenu_name}'",
                                "file": submenu_icon_file.filename,
                                "submenu_index": idx
                            }), 400
                        submenu_icon_path = f"Media/{icon_path}"

                    is_valid, msg = InputValidator.validate_name(submenu_name, "submenu name")
                    if not is_valid:
                        return jsonify({"status": False, "message": msg}), 400


                    if submenu_id and submenu_id in existing_submenus:
                        submenu = existing_submenus[submenu_id]
                        submenu.name = submenu_name
                        submenu.lang = submenu_lang
                        submenu.is_visible = submenu_visible
                        if submenu_icon_path:
                            submenu.icon_path = submenu_icon_path
                    else:
                        submenu = SubMenuOptionV(
                            menu_id=menu.id,
                            user_id=user_id,
                            name=submenu_name,
                            lang=submenu_lang,
                            is_visible=submenu_visible,
                            icon_path=submenu_icon_path,
                            submenu_sequence=new_sequence_start
                        )
                        db.add(submenu)
                        new_sequence_start += 1

                    try:
                        db.flush()
                    except IntegrityError:
                        logger.error(f"Integrity constraint violation for submenu of user {user_id}")
                        return jsonify({"error": f"Submenu '{submenu_name}' creation failed"}), 409
                    except SQLAlchemyError as e:
                        logger.error(f"Database error creating submenu for user {user_id}: {type(e).__name__}")
                        return jsonify({"error": "Failed to process submenu"}), 500

                    # --- Manage Intents / Actions / Utters ---
                    created_intents, created_actions, created_utters, created_story_steps = [], [], [], []

                    for intent_data in submenu_data.get("intents", []):
                        if not isinstance(intent_data, dict):
                            continue

                        intent_name = intent_data.get("name")
                        if not intent_name:
                            continue

                        # --- validate intent name ---
                        is_valid, msg = InputValidator.validate_name(intent_name, "intent name")
                        if not is_valid:
                            return jsonify({"status": False, "message": msg}), 400

                        intent_id = intent_data.get("intent_id") or intent_data.get("id")
                        intent = None
                        
                        try:
                            if intent_id:
                                intent = db.query(IntentV).filter(IntentV.id == intent_id).first()
                                if intent:
                                    intent.name = intent_name
                                else:
                                    intent = IntentV(name=intent_name, submenu_id=[submenu.id])
                                    db.add(intent)
                                    db.flush()
                            else:
                                intent = IntentV(name=intent_name, submenu_id=[submenu.id])
                                db.add(intent)
                                db.flush()
                        except SQLAlchemyError as e:
                            logger.error(f"Intent creation error for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to process intent"}), 500
                        
                        created_intents.append(intent)

                        # ---- EXAMPLES ----
                        try:
                            existing_examples = {ex.id: ex for ex in db.query(IntentExampleV).filter_by(intent_id=intent.id).all()}
                        except SQLAlchemyError as e:
                            logger.error(f"Failed to query examples for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to retrieve intent examples"}), 500

                        sent_example_ids = []
                        for ex_data in intent_data.get("examples", []):
                            if not isinstance(ex_data, dict):
                                continue
                            example_text = ex_data.get("example")
                            ex_id = ex_data.get("id")
                            if not example_text:
                                continue

                            # Validate example text
                            is_valid, msg = InputValidator.validate_name(example_text, "example")
                            if not is_valid:
                                return jsonify({"status": False, "message": msg}), 400
                            
                            try:
                                if ex_id and ex_id in existing_examples:
                                    existing_examples[ex_id].example = example_text
                                    sent_example_ids.append(ex_id)
                                else:
                                    new_ex = IntentExampleV(example=example_text, intent_id=intent.id)
                                    db.add(new_ex)
                                    db.flush()
                                    sent_example_ids.append(new_ex.id)
                            except SQLAlchemyError as e:
                                logger.error(f"Example processing error for user {user_id}: {type(e).__name__}")
                                return jsonify({"error": "Failed to process intent examples"}), 500

                        try:
                            for ex_id in set(existing_examples.keys()) - set(sent_example_ids):
                                db.query(IntentExampleV).filter_by(id=ex_id).delete()
                        except SQLAlchemyError as e:
                            logger.error(f"Example deletion error for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to clean up examples"}), 500

                        # ---- ACTIONS ----
                        try:
                            existing_actions = {a.id: a for a in db.query(ActionsV).filter_by(submenu_id=submenu.id).all()}
                        except SQLAlchemyError as e:
                            logger.error(f"Failed to query actions for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to retrieve actions"}), 500

                        sent_action_ids = []
                        for action_data in intent_data.get("actions", []):
                            if isinstance(action_data, str):
                                action_name = action_data.strip()
                                action_id = None
                            elif isinstance(action_data, dict):
                                action_name = action_data.get("name")
                                action_id = action_data.get("id")
                            else:
                                continue

                            if not action_name:
                                continue

                            # SECURITY: Validate action name
                            is_valid, msg = InputValidator.validate_name(action_name, "action name")
                            if not is_valid:
                                return jsonify({"status": False, "message": msg}), 400

                            try:
                                if action_id and action_id in existing_actions:
                                    existing_actions[action_id].name = action_name
                                    sent_action_ids.append(action_id)
                                else:
                                    new_action = ActionsV(name=action_name, submenu_id=submenu.id)
                                    db.add(new_action)
                                    db.flush()
                                    sent_action_ids.append(new_action.id)
                                    created_actions.append(new_action)
                                    created_story_steps.append(StoryStepsAll(story_id=None, intent=intent_name, action=action_name))
                            except SQLAlchemyError as e:
                                logger.error(f"Action processing error for user {user_id}: {type(e).__name__}")
                                return jsonify({"error": "Failed to process actions"}), 500

                        try:
                            for a_id in set(existing_actions.keys()) - set(sent_action_ids):
                                db.query(ActionsV).filter_by(id=a_id).delete()
                        except SQLAlchemyError as e:
                            logger.error(f"Action deletion error for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to clean up actions"}), 500

                        # ---- UTTERS ----
                        try:
                            existing_utters = {u.id: u for u in db.query(UtterV).filter_by(submenu_id=submenu.id).all()}
                        except SQLAlchemyError as e:
                            logger.error(f"Failed to query utters for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to retrieve utters"}), 500

                        sent_utter_ids = []
                        for utter_data in intent_data.get("utters", []):
                            if isinstance(utter_data, str):
                                utter_name = utter_data.strip()
                                response = ""
                                utter_id = None
                            elif isinstance(utter_data, dict):
                                utter_name = utter_data.get("name")
                                response = utter_data.get("response", "")
                                utter_id = utter_data.get("id")
                            else:
                                continue

                            if not utter_name:
                                continue

                            # SECURITY: Validate utter name
                            is_valid, msg = InputValidator.validate_name(utter_name, "utter name")
                            if not is_valid:
                                return jsonify({"status": False, "message": msg}), 400

                            # SECURITY: Validate utter response (allows more text but blocks HTML/JS)
                            if response:
                                is_valid, msg = InputValidator.validate_text_content(response, "utter response")
                                if not is_valid:
                                    return jsonify({"status": False, "message": msg}), 400

                            try:
                                if utter_id and utter_id in existing_utters:
                                    existing_utters[utter_id].name = utter_name
                                    existing_utters[utter_id].response = response
                                    sent_utter_ids.append(utter_id)
                                else:
                                    new_utter = UtterV(name=utter_name, response=response, submenu_id=submenu.id)
                                    db.add(new_utter)
                                    db.flush()
                                    sent_utter_ids.append(new_utter.id)
                                    created_utters.append(new_utter)
                                    created_story_steps.append(StoryStepsAll(story_id=None, intent=intent_name, action=utter_name))
                            except SQLAlchemyError as e:
                                logger.error(f"Utter processing error for user {user_id}: {type(e).__name__}")
                                return jsonify({"error": "Failed to process utters"}), 500

                        try:
                            for u_id in set(existing_utters.keys()) - set(sent_utter_ids):
                                db.query(UtterV).filter_by(id=u_id).delete()
                        except SQLAlchemyError as e:
                            logger.error(f"Utter deletion error for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to clean up utters"}), 500

                        # ---- STORY ----
                        story_info = submenu_data.get("story") or {}
                        story_name = story_info.get("story_name") or f"Story for {submenu.name}"
                        story_id = story_info.get("id")

                        # SECURITY: Validate story name
                        is_valid, msg = InputValidator.validate_text_content(story_name, "story name", max_length=200)
                        if not is_valid:
                            return jsonify({"status": False, "message": msg}), 400

                        try:
                            if story_id:
                                story = db.query(Story).filter_by(id=story_id, user_id=user_id).first()
                                if story:
                                    story.story_name = story_name
                                else:
                                    story = Story(story_name=story_name, user_id=user_id, submenu_id=submenu.id)
                                    db.add(story)
                                    db.flush()
                            else:
                                story = Story(story_name=story_name, user_id=user_id, submenu_id=submenu.id)
                                db.add(story)
                                db.flush()
                        except SQLAlchemyError as e:
                            logger.error(f"Story creation error for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to process story"}), 500

                        # --- Handle StoryStepsAll incrementally ---
                        try:
                            existing_steps = {
                                (step.intent, step.action): step
                                for step in db.query(StoryStepsAll).filter_by(story_id=story.id).all()
                            }

                            incoming_steps = {(s.intent, s.action): s for s in created_story_steps}

                            for key in set(existing_steps.keys()) - set(incoming_steps.keys()):
                                db.delete(existing_steps[key])

                            for key, step in incoming_steps.items():
                                if key not in existing_steps:
                                    step.story_id = story.id
                                    db.add(step)
                        except SQLAlchemyError as e:
                            logger.error(f"Story steps processing error for user {user_id}: {type(e).__name__}")
                            return jsonify({"error": "Failed to process story steps"}), 500

                    created_or_updated_summary.append({
                        "submenu": {"id": submenu.id, "name": submenu.name},
                        "intents": [{"id": it.id, "name": it.name} for it in created_intents],
                        "actions": [{"id": a.id, "name": a.name} for a in created_actions],
                        "utters": [{"id": u.id, "name": u.name} for u in created_utters],
                        "story": {"id": story.id, "name": story.story_name},
                    })

            return jsonify({
                "message": "Updated successfully" if menu_id else "Created successfully",
                "status": True,
                "data": {"id": menu.id, "name": menu.name},
                "details": created_or_updated_summary
            }), 200 if menu_id else 201

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Transaction error for user {user_id}: {type(e).__name__}")
            return jsonify({"error": "Database transaction failed"}), 500

    except Exception as e:
        db.rollback()
        # Log the actual error securely for debugging
        logger.exception(f"Unexpected error in create_menu_with_submenu for user_id={form.get('user_id', 'unknown')}")
        # Return generic error to client
        return jsonify({"error": "An unexpected error occurred while processing your request"}), 500
    finally:
        db.close()



def get_user_menus():
    """
    Fetch all menus and their submenus for a given user_id, ordered by menu_sequence.
    Includes icon_path for both menu and submenu.
    """
    db = SessionLocal()
    try:
        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # 1️⃣ Fetch all menus
        menus = (
            db.query(
                MenuOptionV.id,
                MenuOptionV.name,
                MenuOptionV.lang,
                MenuOptionV.is_visible,
                MenuOptionV.menu_sequence,
                MenuOptionV.icon_path
            )
            .filter(MenuOptionV.user_id == user_id)
            .order_by(MenuOptionV.menu_sequence)
            .all()
        )

        if not menus:
            return jsonify({"user_id": user_id, "menus": []}), 200

        menu_ids = [m.id for m in menus]

        # 2️⃣ Fetch all submenus in a single query
        submenus = (
            db.query(
                SubMenuOptionV.id,
                SubMenuOptionV.menu_id,
                SubMenuOptionV.name,
                SubMenuOptionV.lang,
                SubMenuOptionV.is_visible,
                SubMenuOptionV.submenu_sequence,
                SubMenuOptionV.icon_path
            )
            .filter(SubMenuOptionV.menu_id.in_(menu_ids))
            .order_by(SubMenuOptionV.id)
            .all()
        )

        # 3️⃣ Group submenus by menu_id
        submenu_map = {}
        for sm in submenus:
            submenu_map.setdefault(sm.menu_id, []).append({
                "id": sm.id,
                "name": sm.name,
                "lang": sm.lang,
                "is_visible": sm.is_visible,
                "icon_path": sm.icon_path,
                "submenu_sequence": sm.submenu_sequence
            })

        # 4️⃣ Assemble final menu data
        all_menu_data = []
        for m in menus:
            all_menu_data.append({
                "id": m.id,
                "name": m.name,
                "lang": m.lang,
                "is_visible": m.is_visible,
                "menu_sequence": m.menu_sequence,
                "icon_path": m.icon_path,
                "submenus": submenu_map.get(m.id, [])
            })

        # 5️⃣ Return response
        return jsonify({
            "user_id": user_id,
            "menus": all_menu_data
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        db.close()


    

## Export domain.yml

DOMAIN_FILE = "domain_test.yml"
EXCLUDED_ACTIONS = {
    "utter_ask_ca_number",
    "utter_ask_otp",
    "utter_ask_otp_hindi"
}

def export_domain():
    db = SessionLocal()
    try:
        # --- Load existing domain.yml safely ---
        with open(DOMAIN_FILE, "r") as f:
            domain_data = yaml.safe_load(f) or {}

        # Ensure top-level keys exist
        domain_data["intents"] = domain_data.get("intents") or []
        domain_data["actions"] = domain_data.get("actions") or []
        domain_data["responses"] = domain_data.get("responses") or {}

        # --- Get unique intents from DB ---
        intents_from_db = db.query(distinct(IntentV.name)).all()
        for i in intents_from_db:
            intent_name = i[0]
            if intent_name and intent_name not in domain_data["intents"]:
                domain_data["intents"].append(intent_name)

        # --- Get unique actions from DB ---
        actions_from_db = db.query(distinct(ActionsV.name)).all()
        actions_set = set(domain_data["actions"])
        for a in actions_from_db:
            action_name = a[0]
            if action_name and action_name not in EXCLUDED_ACTIONS:
                actions_set.add(action_name)
        domain_data["actions"] = sorted(list(actions_set))
        domain_data["intents"] = sorted(domain_data["intents"])

        # --- Add utterances (responses) ---
        utters_from_db = db.query(UtterV).all()
        for utter in utters_from_db:
            utter_name = utter.name.strip()
            response_text = utter.response.strip() if utter.response else ""

            if not utter_name or not response_text:
                continue  # skip invalid rows

            # Ensure key exists
            if utter_name not in domain_data["responses"]:
                domain_data["responses"][utter_name] = []

            # Avoid duplicates
            if not any(r.get("text") == response_text for r in domain_data["responses"][utter_name]):
                domain_data["responses"][utter_name].append({"text": response_text})

        # --- Dump YAML with indentation ---
        yaml_str = yaml.dump(
            domain_data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            width=None
        )

        # --- Ensure version key format is consistent ---
        yaml_str = yaml_str.replace("version: '3.1'", 'version: "3.1"')
        yaml_str = yaml_str.replace("- ", "  - ")

        # --- Return downloadable YAML file ---
        return Response(
            yaml_str,
            headers={
                "Content-Disposition": "attachment; filename=domain_generated.yml",
                "Content-Type": "application/x-yaml"
            }
        )

    except Exception as e:
        return {"error": str(e)}, 500

    finally:
        db.close()

## Download Stories

# def download_stories():
#     try:
#         db = SessionLocal()
#         user_id = request.args.get('user_id')
#         query = db.query(Story)
#         if user_id:
#             query = query.filter(Story.user_id == user_id)

#         stories = query.all()
#         yaml_stories = []

#         for story in stories:
#             # --- Fetch StoryStepsAll steps ---
#             steps_all = (
#                 db.query(StoryStepsAll)
#                 .filter(StoryStepsAll.story_id == story.id)
#                 .order_by(StoryStepsAll.id)
#                 .all()
#             )

#             # --- Detect whether it's a NEW format ---
#             # New format = multiple rows with both intent & action populated
#             new_format_rows = [s for s in steps_all if s.intent and s.action]
#             is_new_format = len(new_format_rows) > 0

#             formatted_user_steps_yaml = []

#             # --- Fetch user-specific steps ---
#             user_steps = db.execute(
#                 text("""
#                     SELECT step_type, step_name, slot_value
#                     FROM story_steps
#                     WHERE user_id = :user_id
#                     ORDER BY step_order
#                 """),
#                 {"user_id": story.user_id}
#             ).fetchall()

#             for step in user_steps:
#                 if step.step_type == "intent":
#                     formatted_user_steps_yaml.append({"intent": step.step_name})
#                 elif step.step_type == "action":
#                     formatted_user_steps_yaml.append({"action": step.step_name})
#                 elif step.step_type == "slot":
#                     formatted_user_steps_yaml.append({"slot_was_set": [{step.step_name: step.slot_value}]})

#             # ==========================
#             # 🧩 OLD FORMAT HANDLING
#             # ==========================
#             if not is_new_format:
#                 paired_steps_all = []
#                 current_intent = None
#                 for step in steps_all:
#                     if step.intent:
#                         current_intent = step.intent
#                     elif step.action:
#                         if current_intent:
#                             paired_steps_all.append({"intent": current_intent, "action": step.action})
#                             current_intent = None
#                         else:
#                             paired_steps_all.append({"action": step.action})

#                 # Add paired StoryStepsAll steps
#                 for s in paired_steps_all:
#                     if "intent" in s:
#                         formatted_user_steps_yaml.append({"intent": s["intent"]})
#                     formatted_user_steps_yaml.append({"action": s["action"]})

#             # ==========================
#             # 🆕 NEW FORMAT HANDLING
#             # ==========================
#             else:
#                 # Group actions under same intent (sort ascending by ID)
#                 steps_sorted = sorted(steps_all, key=lambda s: s.id)
#                 intent_actions_map = {}
#                 intent_order = []

#                 for s in steps_sorted:
#                     if s.intent:
#                         if s.intent not in intent_actions_map:
#                             intent_actions_map[s.intent] = []
#                             intent_order.append(s.intent)
#                         if s.action:
#                             intent_actions_map[s.intent].append(s.action)

#                 # Build formatted steps
#                 for intent in intent_order:
#                     formatted_user_steps_yaml.append({"intent": intent})
#                     for action in intent_actions_map[intent]:
#                         formatted_user_steps_yaml.append({"action": action})

#             # --- Build YAML entry ---
#             yaml_stories.append({
#                 "story": story.story_name,
#                 "steps": formatted_user_steps_yaml
#             })

#         # --- Generate YAML string ---
#         stories_yaml_str = yaml.dump(
#             {"version": "3.1", "stories": yaml_stories},
#             sort_keys=False,
#             allow_unicode=True
#         )

#         # --- Return downloadable file ---
#         return Response(
#             stories_yaml_str,
#             mimetype="application/x-yaml",
#             headers={"Content-Disposition": 'attachment;filename=stories.yml'}
#         )

#     except Exception as e:
#         return {"error": str(e)}, 500
#     finally:
#         db.close()

def download_stories():
    try:
        db = SessionLocal()
        user_id = request.args.get('user_id')
        langs = (
            db.query(Language)
            .filter(Language.is_visible == True)
            .distinct()
            .all()
        )
        lang_codes = [l.code for l in langs]
       
 
        users = (
            db.query(User)
            .filter(User.lang.in_(lang_codes))
            .order_by(User.id.asc())
            .all()
        )
        user_ids = [u.id for u in users]
        # user_ids = ["1"]
       
 
        query = db.query(Story)
        # if user_id:
            # query = query.filter(Story.user_id == user_id)
        query = query.filter(Story.user_id.in_(user_ids))
 
 
        stories = query.all()
        yaml_stories = []
 
        for story in stories:
            steps_all = (
                db.query(StoryStepsAll)
                .filter(StoryStepsAll.story_id == story.id)
                .order_by(StoryStepsAll.id)
                .all()
            )
 
            new_format_rows = [s for s in steps_all if s.intent and s.action]
            is_new_format = len(new_format_rows) > 0
 
            formatted_user_steps_yaml = []
 
            # --- Fetch user-specific steps ---
            user_steps = db.execute(
                text("""
                    SELECT step_type, step_name, slot_value
                    FROM story_steps
                    WHERE user_id = :user_id
                    ORDER BY step_order
                """),
                {"user_id": story.user_id}
            ).fetchall()
 
            for step in user_steps:
                if step.step_type == "intent":
                    formatted_user_steps_yaml.append({"intent": step.step_name})
                elif step.step_type == "action":
                    formatted_user_steps_yaml.append({"action": step.step_name})
                elif step.step_type == "slot":
                    formatted_user_steps_yaml.append(
                        {"slot_was_set": [{step.step_name: step.slot_value}]}
                    )
 
            # ==========================
            # OLD FORMAT HANDLING
            # ==========================
            if not is_new_format:
                paired_steps_all = []
                current_intent = None
                for step in steps_all:
                    if step.intent:
                        current_intent = step.intent
                    elif step.action:
                        if current_intent:
                            paired_steps_all.append(
                                {"intent": current_intent, "action": step.action}
                            )
                            current_intent = None
                        else:
                            paired_steps_all.append({"action": step.action})
 
                for s in paired_steps_all:
                    if "intent" in s:
                        formatted_user_steps_yaml.append({"intent": s["intent"]})
                    formatted_user_steps_yaml.append({"action": s["action"]})
 
            # ==========================
            # NEW FORMAT HANDLING
            # ==========================
            else:
                steps_sorted = sorted(steps_all, key=lambda s: s.id)
                intent_action_utter_map = {}
                intent_order = []
 
                for s in steps_sorted:
                    if s.intent:
                        if s.intent not in intent_action_utter_map:
                            intent_action_utter_map[s.intent] = []
                            intent_order.append(s.intent)
                        if s.action:
                            intent_action_utter_map[s.intent].append(s.action)
 
                utter_names = {u.name for u in db.query(UtterV).all()}
 
                for intent in intent_order:
                    formatted_user_steps_yaml.append({"intent": intent})
                    for action in intent_action_utter_map[intent]:
                        formatted_user_steps_yaml.append({"action": action})
 
            # ==========================
            # NEW LOGIC: Language-based thank-you message
            # ==========================
            if formatted_user_steps_yaml:
                # Detect language slot if available
                language_slot = None
                for step in formatted_user_steps_yaml:
                    if "slot_was_set" in step:
                        for slot_pair in step["slot_was_set"]:
                            if "language" in slot_pair:
                                language_slot = slot_pair["language"]
                                break
 
                last_step = formatted_user_steps_yaml[-1]
                if (
                    "action" in last_step
                    and isinstance(last_step["action"], str)
                    and last_step["action"].startswith("utter_")
                ):
                    if language_slot == "hi":
                        thank_you_action = "action_thank_you_message_hindi"
                    else:
                        thank_you_action = "action_thank_you_message_english"
 
                    formatted_user_steps_yaml.append({"action": thank_you_action})
 
            # --- Build YAML entry ---
            yaml_stories.append({
                "story": story.story_name,
                "steps": formatted_user_steps_yaml
            })
 
        # --- Generate YAML string ---
        stories_yaml_str = yaml.dump(
            {"version": "3.1", "stories": yaml_stories},
            sort_keys=False,
            allow_unicode=True
        )
 
        return Response(
            stories_yaml_str,
            mimetype="application/x-yaml",
            headers={"Content-Disposition": 'attachment;filename=stories.yml'}
        )
 
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        db.close()


    

## Rebuild Intent file    

def rebuild_intent_file():
    """
    Reads all intents and examples from the database and returns
    a clean YAML response in Rasa NLU format with:
      - examples: |  (not |-)
      - one blank line between intents
    """
    db = SessionLocal()
    try:
        intents = db.query(IntentV).all()
        if not intents:
            return Response(
                'version: "3.1"\nnlu: []\n',
                mimetype="application/x-yaml",
                headers={"Content-Disposition": 'attachment; filename=nlu.yml'}
            )

        nlu_data = {"version": "3.1", "nlu": []}

        for intent in intents:
            examples = db.query(IntentExampleV).filter_by(intent_id=intent.id).all()
            example_lines = [f"- {ex.example}" for ex in examples] if examples else ["- (no examples found)"]

            # Ensure each block ends with a newline to force '|' and not '|-'
            examples_block = "\n".join(example_lines).rstrip() + "\n"

            nlu_data["nlu"].append({
                "intent": intent.name,
                "examples": examples_block
            })

        # --- Force literal block style ---
        class LiteralStr(str): pass

        def literal_str_representer(dumper, data):
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')

        yaml.add_representer(LiteralStr, literal_str_representer)

        for item in nlu_data["nlu"]:
            item["examples"] = LiteralStr(item["examples"])

        # Dump YAML normally
        nlu_yaml_str = yaml.dump(
            nlu_data,
            sort_keys=False,
            allow_unicode=True,
            width=None,
            default_flow_style=False
        )

        # Replace version quotes and add one blank line between each intent
        nlu_yaml_str = nlu_yaml_str.replace("version: '3.1'", 'version: "3.1"')

        # Add exactly one blank line between intents
        nlu_yaml_str = nlu_yaml_str.replace("\n- intent:", "\n\n- intent:")

        return Response(
            nlu_yaml_str,
            mimetype="application/x-yaml",
            headers={"Content-Disposition": 'attachment; filename=nlu.yml'}
        )

    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        db.close()



def delete_submenu(submenu_id):
    db = SessionLocal()
    try:
        submenu = db.query(SubMenuOptionV).get(submenu_id)
        if not submenu:
            return jsonify({"error": "Submenu not found"}), 404

        # Manual delete only for intents (ARRAY-based)
        intents_to_delete = db.query(IntentV).filter(IntentV.submenu_id.any(submenu_id)).all()
        for intent in intents_to_delete:
            db.delete(intent)

        # ORM delete triggers DB cascades for all related data
        db.delete(submenu)
        db.commit()

        return jsonify({
            "message": f"Submenu {submenu_id} and all related records deleted successfully"
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


def delete_menu(menu_id):
    db = SessionLocal()
    try:
        menu = db.query(MenuOptionV).get(menu_id)
        if not menu:
            return jsonify({"error": "Menu not found"}), 404

        # ✅ Step 1. Manually delete intents linked to submenus (ARRAY field, no FK)
        submenu_ids = [sm.id for sm in menu.submenus]
        if submenu_ids:
            intents_to_delete = (
                db.query(IntentV)
                .filter(
                    IntentV.submenu_id.overlap(submenu_ids)  # ARRAY overlap
                )
                .all()
            )
            for intent in intents_to_delete:
                db.delete(intent)

        # ✅ Step 2. Delete the menu (ORM + DB will cascade submenus and their related records)
        db.delete(menu)
        db.commit()

        return jsonify({
            "message": f"Menu {menu_id} and all related submenus, actions, utters, stories, and intents deleted successfully"
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()



# def update_menu_sequence():
#     db = SessionLocal()
#     try:
#         data = request.get_json()
#         user_id = data.get("user_id")
#         menu_order = data.get("menu_order", [])

#         if not user_id or not menu_order:
#             return jsonify({"error": "Missing user_id or menu_order", "status": False}), 400

#         # Build CASE WHEN query dynamically
#         case_statements = " ".join(
#             f"WHEN {item['id']} THEN {item['menu_sequence']}" for item in menu_order
#         )
#         ids = [str(item["id"]) for item in menu_order]

#         query = text(f"""
#             UPDATE "menu_option_v"
#             SET menu_sequence = CASE id
#                 {case_statements}
#             END
#             WHERE id IN ({','.join(ids)}) AND user_id = :user_id;
#         """)

#         db.execute(query, {"user_id": user_id})
#         db.commit()

#         return jsonify({"status": True, "message": "Menu sequence updated successfully"}), 200

#     except SQLAlchemyError as e:
#         db.rollback()
#         return jsonify({"error": str(e), "status": False}), 500
#     except Exception as e:
#         db.rollback()
#         return jsonify({"error": f"Unexpected error: {str(e)}", "status": True}), 500
#     finally:
#         db.close()



def update_menu_sequence():
    db = SessionLocal()
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        menu_order = data.get("menu_order", [])
        submenu_order = data.get("submenu_order", [])

        if not user_id:
            return jsonify({"error": "Missing user_id", "status": False}), 400

        # ----------------------------
        # 1. Update MENU SEQUENCE
        # ----------------------------
        if menu_order:
            case_statements = " ".join(
                f"WHEN {item['id']} THEN {item['menu_sequence']}" for item in menu_order
            )
            ids = [str(item["id"]) for item in menu_order]

            query = text(f"""
                UPDATE "menu_option_v"
                SET menu_sequence = CASE id
                    {case_statements}
                END
                WHERE id IN ({','.join(ids)}) AND user_id = :user_id;
            """)

            db.execute(query, {"user_id": user_id})

        # ----------------------------
        # 2. Update SUBMENU SEQUENCE
        # ----------------------------
        # Expecting submenu_order as a list of dicts like:
        # [
        #   { "menu_id": 1, "submenu_items": [{ "id": 1, "submenu_sequence": 2 }, ...] },
        #   { "menu_id": 2, "submenu_items": [...] }
        # ]
        if submenu_order:
            for group in submenu_order:
                menu_id = group.get("menu_id")
                submenu_items = group.get("submenu_items", [])

                if not menu_id or not submenu_items:
                    continue

                submenu_case = " ".join(
                    f"WHEN {item['id']} THEN {item['submenu_sequence']}" for item in submenu_items
                )
                submenu_ids = [str(item["id"]) for item in submenu_items]

                submenu_query = text(f"""
                    UPDATE "sub_menu_option_v"
                    SET submenu_sequence = CASE id
                        {submenu_case}
                    END
                    WHERE id IN ({','.join(submenu_ids)})
                    AND user_id = :user_id
                    AND menu_id = :menu_id;
                """)

                db.execute(submenu_query, {"user_id": user_id, "menu_id": menu_id})

        db.commit()

        return jsonify({"status": True, "message": "Menu and submenu sequences updated successfully"}), 200

    except SQLAlchemyError as e:
        db.rollback()
        return jsonify({"error": str(e), "status": False}), 500
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Unexpected error: {str(e)}", "status": False}), 500
    finally:
        db.close()