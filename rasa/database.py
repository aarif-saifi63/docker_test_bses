from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()


# Postgres URI -> postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv('DATABASE_CONNECTION_STRING') 
# DATABASE_URL = "postgresql://bsesbot:Expediens%40123@20.40.59.245/bsesbotdb"

# engine = create_engine(DATABASE_URL, echo=True)

# Create engine with connection pool settings
engine = create_engine(
    DATABASE_URL,
    echo=True,                 # Logs SQL for debugging
    pool_size=50,              # Number of connections in the pool
    max_overflow=5,            # Extra connections if pool is full
    pool_timeout=30,           # Seconds to wait for a connection
    pool_recycle=1800,         # Recycle connections every 30 min (avoid stale connections)
    pool_pre_ping=True         # Check connections before using them
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()