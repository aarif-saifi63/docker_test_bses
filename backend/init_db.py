from database import Base, engine
from Models.session_model import Session
from Models.bses_token_model import BSES_Token
from populate import populate_tables

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")

print("\n" + "="*60)
print("Starting system initialization...")
print("="*60 + "\n")

success = populate_tables(reset_mode="auto")

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


