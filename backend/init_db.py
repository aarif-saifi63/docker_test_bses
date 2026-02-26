from database import Base, engine
from sqlalchemy import inspect as sa_inspect

# Import all models so Base.metadata knows about every table
from Models import (
    action_model, api_key_master_model,
    division_model, fallback_model, feedback_question_model,
    intent_example_model, intent_model, language_model, menu_option_model,
    permission_matrix_model, story_model, story_steps_all_model, story_steps_model, sub_menu_option_model,
    user_details_model, user_permission_mapping_model, user_role_model,
    users_model, utter_messages_model, utter_model, feedback_response_model,
    ad_model, poll_model, poll_response_model, session_model, bses_token_model,
    token_blacklist_model, submenu_fallback_model, admin_model, active_session_model
)
from populate import populate_tables, run_alembic_migrations

print("\n" + "="*60)
print("Starting system initialization...")
print("="*60 + "\n")

# Check if the database already has tables
inspector = sa_inspect(engine)
existing_tables = inspector.get_table_names()

if not existing_tables:
    # Fresh database: create all tables first, then migrate, then seed
    print("Fresh database detected.")
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    success = populate_tables(reset_mode="auto")
else:
    # Tables already exist: only run new migrations
    print(f"Database already has {len(existing_tables)} table(s). Running migrations only...")
    run_alembic_migrations()
    success = True

# Ensure database connections are properly closed
engine.dispose()

if success:
    print("\n" + "="*60)
    print("Initialization completed. Ready to start workers!")
    print("="*60)
else:
    print("\n" + "="*60)
    print("Initialization in progress or failed. Check logs.")
    print("="*60)
