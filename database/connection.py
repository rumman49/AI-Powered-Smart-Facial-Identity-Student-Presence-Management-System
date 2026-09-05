import os
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# loading secrets from .env file
load_dotenv()

# getting the MySQL connection string
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:1234@localhost:3306/neuraforge")

# Helper function Automatically create the MySQL database if it doesn't exist yet
def create_database_if_not_exists():
    try:
        # Parse connection details from string
        url_parts = DATABASE_URL.replace("mysql+pymysql://", "").split("/")
        user_pass_host = url_parts[0]
        db_name = url_parts[1]
        
        user_pass, host_port = user_pass_host.split("@")
        user, password = user_pass.split(":") if ":" in user_pass else (user_pass, "")
        host = host_port.split(":")[0]
        port = int(host_port.split(":")[1]) if ":" in host_port else 3306

        # Connect to MySQL server directly (without selecting a database)
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            port=port
        )
        with connection.cursor() as cursor:
            # Create the database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`;")
        connection.close()
        print(f"✅ MySQL Database '{db_name}' is ready!")
    except Exception as e:
        print(f"⚠️ Warning during database creation check: {e}")

# Run the database auto-creation check
create_database_if_not_exists()

# 4. Create SQLAlchemy Engine for MySQL
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Keeps MySQL connection alive and prevents timeouts
    pool_recycle=3600
)

# 5. Create Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 6. Create Base class for database models
Base = declarative_base()

# 7. Dependency function for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()