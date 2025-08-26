# app/database.py
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./weather.db"  # file in project root

engine = create_engine(DATABASE_URL, echo=True)

# Create tables
def init_db():
    SQLModel.metadata.create_all(engine)

# Dependency for DB sessions
def get_session():
    with Session(engine) as session:
        yield session
