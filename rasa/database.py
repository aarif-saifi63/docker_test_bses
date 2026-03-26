from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool  # noqa: F401 (kept for reference)
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
# Connecting through PgBouncer (transaction mode):
# pool_size here = SQLAlchemy → PgBouncer connections (cheap)
# PgBouncer maintains only 50 real PostgreSQL connections total
# engine = create_engine(
#     DATABASE_URL,
#     echo=False,
#     pool_size=10,              # SQLAlchemy → PgBouncer connections for rasa_actions
#     max_overflow=5,            # Burst slots
#     pool_timeout=30,
#     pool_recycle=1800,
#     pool_pre_ping=True,
# )

engine = create_engine(
    DATABASE_URL,   # points to PgBouncer host:6432
    echo=False,
    poolclass=NullPool,
)



def _pool_status():
    # NullPool creates/destroys a connection per request — no pool state to track
    pool = engine.pool
    if not hasattr(pool, 'checkedout'):
        return None, None, None, None
    checked_out = pool.checkedout()
    checked_in = pool.checkedin()
    overflow = pool.overflow()
    size = pool.size()
    return checked_out, checked_in, overflow, size


@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    checked_out, checked_in, overflow, size = _pool_status()
    if checked_out is None:
        logger.debug("[POOL CHECKOUT] NullPool — new connection created")
        return
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
    if checked_out is None:
        logger.debug("[POOL CHECKIN] NullPool — connection closed")
        return
    logger.info(
        "[POOL CHECKIN]   checked_out=%d  checked_in=%d  overflow=%d  pool_size=%d",
        checked_out, checked_in, overflow, size,
    )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()