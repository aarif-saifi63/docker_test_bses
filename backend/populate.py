import os
import pandas as pd
from database import engine
from sqlalchemy import text, inspect
import time
import logging
from alembic.config import Config
from alembic import command

logger = logging.getLogger(__name__)

# Folder where CSV files are stored
CSV_FOLDER = "csv_data"

# Initialization marker table
INIT_MARKER_TABLE = "system_initialization_marker"

# Map CSV file -> table name
TABLE_CSV_MAP = {
    "actions_v.csv": "actions_v",
    "api_key_master.csv": "api_key_master",
    "division_master.csv": "division_master",
    "fallback_v.csv": "fallback_v",
    "feedback_questions.csv": "feedback_questions",
    "users.csv": "users",
    "intent_v.csv": "intent_v",
    "intent_examples_v.csv": "intent_examples_v",
    "language_v.csv": "language_v",
    "menu_option_v.csv": "menu_option_v",
    "permission_matrix.csv": "permission_matrix",
    "story.csv": "story",
    "story_steps.csv": "story_steps",
    "story_steps_all.csv": "story_steps_all",
    "sub_menu_option_v.csv": "sub_menu_option_v",
    "user_roles.csv": "user_roles",
    "user_details.csv": "user_details",
    "user_permission_mapping.csv": "user_permission_mapping",
    "utter_messages.csv": "utter_messages",
    "utter_v.csv": "utter_v"
}


def run_alembic_migrations():
    """
    Run Alembic migrations to upgrade the database schema to the latest version.
    This ensures all schema changes (new columns, tables, etc.) are applied.
    """
    try:
        print("\n🔄 Running Alembic migrations...")

        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        alembic_ini_path = os.path.join(script_dir, "alembic.ini")

        # Check if alembic.ini exists
        if not os.path.exists(alembic_ini_path):
            print(f"Warning: alembic.ini not found at {alembic_ini_path}")
            print("Skipping migrations. Please ensure Alembic is properly configured.")
            return False

        # Create Alembic config
        alembic_cfg = Config(alembic_ini_path)

        # Run the upgrade command to apply all pending migrations
        command.upgrade(alembic_cfg, "head")

        print("✅ Alembic migrations completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Error running Alembic migrations: {e}", exc_info=True)
        print(f"❌ Error running Alembic migrations: {e}")
        return False


def create_initialization_marker_table(connection):
    """Create the initialization marker table if it doesn't exist."""
    try:
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {INIT_MARKER_TABLE} (
            id SERIAL PRIMARY KEY,
            initialization_status VARCHAR(50) NOT NULL,
            initialized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        """
        connection.execute(text(create_query))
        print(f"Ensured marker table exists: {INIT_MARKER_TABLE}")
    except Exception as e:
        print(f"Error creating marker table: {e}")


def is_system_initialized(connection):
    """Check if system initialization has already been completed."""
    try:
        inspector = inspect(connection)
        if INIT_MARKER_TABLE not in inspector.get_table_names():
            return False
        
        result = connection.execute(
            text(f"SELECT COUNT(*) FROM {INIT_MARKER_TABLE} WHERE initialization_status = 'COMPLETED'")
        ).scalar()
        
        return result > 0
    except Exception as e:
        print(f"Error checking initialization status: {e}")
        return False


def mark_initialization_started(connection):
    """Mark that initialization is starting (acquires lock)."""
    try:
        connection.execute(
            text(f"INSERT INTO {INIT_MARKER_TABLE} (initialization_status) VALUES ('IN_PROGRESS')")
        )
        print("Initialization lock acquired")
        return True
    except Exception as e:
        print(f"Failed to acquire initialization lock: {e}")
        return False


def mark_initialization_completed(connection):
    """Mark that initialization is completed."""
    try:
        connection.execute(
            text(f"""
            UPDATE {INIT_MARKER_TABLE} 
            SET initialization_status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP 
            WHERE id = (
                SELECT id FROM {INIT_MARKER_TABLE} 
                WHERE initialization_status = 'IN_PROGRESS'
                LIMIT 1
            )
            """)
        )
        print("Initialization marked as COMPLETED")
        return True
    except Exception as e:
        print(f"Error marking initialization as completed: {e}")
        return False


def create_story_steps_table(connection):
    """Create story_steps table if it does not exist."""
    try:
        create_query = """
        CREATE TABLE IF NOT EXISTS story_steps (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            step_type VARCHAR(50) NOT NULL,
            step_name VARCHAR(255) NOT NULL,
            slot_value VARCHAR(255)
        );
        """
        connection.execute(text(create_query))
        print("Ensured table exists: story_steps")
    except Exception as e:
        print(f"Error creating story_steps table: {e}")


def reset_sequences_safely(connection, table_names, start_value=5500, mode="auto"):
    """
    Reset sequences only for tables that have a serial/identity primary key.
    mode = "auto"  → set to MAX(id) + 1
    mode = "fixed" → force all to start from given start_value
    """
    for table in table_names:
        # Detect serial or identity columns
        seq_name_query = f"SELECT pg_get_serial_sequence('{table}', 'id');"
        seq_name = connection.execute(text(seq_name_query)).scalar()

        # Skip if no sequence (non-auto-increment table)
        if not seq_name:
            print(f"Skipping {table} (no auto-increment id column).")
            continue

        # Determine restart value
        if mode == "auto":
            max_id = connection.execute(text(f"SELECT COALESCE(MAX(id), 0) FROM {table};")).scalar()
            new_value = max_id + 1
        else:
            new_value = start_value

        try:
            connection.execute(text(f"ALTER SEQUENCE {seq_name} RESTART WITH {new_value};"))
            print(f"Reset sequence for {table} → next id = {new_value}")
        except Exception as e:
            print(f"Failed to reset sequence for {table}: {e}")


def populate_tables(reset_mode="auto"):
    """
    Populate database tables from CSV files with distributed locking.
    Only runs once during system initialization.

    reset_mode:
        "auto"  → align each id sequence with MAX(id) + 1
        "fixed" → start all sequences at 5500

    Returns:
        True if initialization was performed or already completed
        False if another process is initializing (retry later)
    """
    try:
        # Step 0: ALWAYS run migrations first (before checking initialization)
        # This ensures schema changes are applied even if data already exists
        print("\n" + "="*60)
        print("STEP 0: Running Database Migrations")
        print("="*60)
        run_alembic_migrations()

        with engine.begin() as connection:
            inspector = inspect(connection)

            # Step 1: Create marker table if it doesn't exist
            create_initialization_marker_table(connection)

            # Step 2: Check if already initialized
            if is_system_initialized(connection):
                print("\n" + "="*60)
                print("System already initialized. Skipping data seeding.")
                print("Note: Migrations were still applied (if any were pending).")
                print("="*60)
                return True

            # Step 3: Try to acquire initialization lock
            if not mark_initialization_started(connection):
                print("Another worker is initializing. Waiting...")
                return False

            # Commit the lock before proceeding with long operation
            # This ensures other workers see that initialization is in progress
            
        # Step 4: Perform initialization in a separate transaction
        with engine.begin() as connection:
            inspector = inspect(connection)
            
            # Ensure story_steps table exists
            if "story_steps" not in inspector.get_table_names():
                create_story_steps_table(connection)
            else:
                print("Table 'story_steps' already exists.")

            # Insert CSV data
            for csv_file, table_name in TABLE_CSV_MAP.items():
                csv_path = os.path.join(CSV_FOLDER, csv_file)
                if not os.path.exists(csv_path):
                    print(f"CSV file not found: {csv_path}")
                    continue

                df = pd.read_csv(csv_path)
                if df.empty:
                    print(f"Skipping {table_name}: CSV is empty.")
                    continue

                # Check if table exists
                if table_name not in inspector.get_table_names():
                    print(f"Table '{table_name}' not found in database — skipping.")
                    continue

                # Check if table already has data
                try:
                    existing = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                except Exception as e:
                    print(f"Could not count rows in {table_name}: {e}")
                    continue

                if existing == 0:
                    print(f"Inserting data into {table_name} from {csv_file}...")
                    df.to_sql(table_name, con=connection, if_exists="append", index=False)
                    print(f"Successfully populated {table_name}")
                else:
                    print(f"Skipping {table_name} (already has data).")

            # Reset sequences robustly
            print("\n🔧 Resetting sequences safely...\n")
            reset_sequences_safely(
                connection,
                table_names=TABLE_CSV_MAP.values(),
                start_value=5500,
                mode=reset_mode
            )
        
        # Step 5: Mark initialization as completed
        with engine.begin() as connection:
            mark_initialization_completed(connection)
        
        print("System initialization completed successfully!")
        
        # Step 6: Dispose all connections for better connection pooling
        engine.dispose()
        print("Database connection pool cleaned up (disposed)")
        
        return True
        
    except Exception as e:
        logger.error(f"Fatal error during initialization: {e}", exc_info=True)
        print(f"Error during populate_tables: {e}")
        # Dispose connections even on error for cleanup
        engine.dispose()
        print("Database connection pool cleaned up (error recovery)")
        return False