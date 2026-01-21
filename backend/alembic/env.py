from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool, create_engine

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from database import Base  # Import your Base (from your database.py)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None


from Models import (
    action_model, api_key_master_model,
    division_model, fallback_model, feedback_question_model,
    intent_example_model, intent_model, language_model, menu_option_model, 
    permission_matrix_model, story_model, story_steps_all_model, story_steps_model, sub_menu_option_model, 
    user_details_model, user_permission_mapping_model, user_role_model, 
    users_model, utter_messages_model, utter_model, feedback_response_model, ad_model, poll_model, poll_response_model, session_model, bses_token_model, token_blacklist_model, submenu_fallback_model
)

config = context.config
fileConfig(config.config_file_name)

print(Base.metadata.tables.keys(), "dfgdfg")

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


import os

def get_url():
    return os.getenv("DATABASE_CONNECTION_STRING")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
  # Or your own config loader

    url = get_url()
    # url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    url = get_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not set")

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
