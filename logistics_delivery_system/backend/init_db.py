from backend.database import Base, engine
from backend import models

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("All logistics tables created successfully.")
