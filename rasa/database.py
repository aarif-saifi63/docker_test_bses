from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
import logging

# Load .env file
load_dotenv()

logger = logging.getLogger("db.pool")

# Postgres URI -> postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv('DATABASE_CONNECTION_STRING')
# DATABASE_URL = "postgresql://bsesbot:Expediens%40123@20.40.59.245/bsesbotdb"

# engine = create_engine(DATABASE_URL, echo=True)

# Create engine with connection pool settings
engine = create_engine(
    DATABASE_URL,
    echo=False,                # Set to True only for local debugging
    pool_size=50,              # Rasa action server uses fewer concurrent DB calls
    max_overflow=5,            # Extra burst connections if pool is full
    pool_timeout=30,           # Fail fast rather than queue up (was 30s)
    pool_recycle=1800,         # Recycle connections every 30 min (avoid stale connections)
    pool_pre_ping=True         # Check connections before using them
)


def _pool_status():
    pool = engine.pool
    checked_out = pool.checkedout()
    checked_in = pool.checkedin()
    overflow = pool.overflow()
    size = pool.size()
    return checked_out, checked_in, overflow, size


@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    checked_out, checked_in, overflow, size = _pool_status()
    logger.info(
        "[POOL CHECKOUT] checked_out=%d  checked_in=%d  overflow=%d  pool_size=%d",
        checked_out, checked_in, overflow, size,
    )
    if checked_out >= size + overflow - 2:
        logger.warning(
            "[POOL WARNING] Pool nearly exhausted! checked_out=%d / max=%d",
            checked_out, size + overflow,
        )


@event.listens_for(engine, "checkin")
def on_checkin(dbapi_conn, connection_record):
    checked_out, checked_in, overflow, size = _pool_status()
    logger.info(
        "[POOL CHECKIN]   checked_out=%d  checked_in=%d  overflow=%d  pool_size=%d",
        checked_out, checked_in, overflow, size,
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()