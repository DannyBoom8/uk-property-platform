import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load variables from .env into this script's environment
load_dotenv()

# Read the DATABASE_URL we stored in .env
database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise ValueError("DATABASE_URL not found — check your .env file exists and has the right key name")

# Create a SQLAlchemy engine — this is the object that manages connections to the database
engine = create_engine(database_url)

# Try an actual connection and run a trivial query
with engine.connect() as connection:
    result = connection.execute(text("SELECT version();"))
    version = result.scalar()
    print("Connected successfully!")
    print("Postgres version:", version)