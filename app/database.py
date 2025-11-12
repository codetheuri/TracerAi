from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Define the database URL. This tells SQLAlchemy we are using

SQLALCHEMY_DATABASE_URL = "sqlite:///./smart-trace.db"

# 2. Create the SQLAlchemy 'engine'. This is the main connection point.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a 'SessionLocal' class. Each instance of this

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a 'Base' class. Our database 'models' (the tables)
Base = declarative_base()