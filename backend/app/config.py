import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

class Settings:
    PROJECT_NAME: str = "OdoShield API"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database configuration (Defaults to Docker postgres settings)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgrespassword@localhost:5432/odoshield"
    )
    
    # Hugging Face API configuration
    HF_API_KEY: str = os.getenv("HF_API_KEY", "")
    HF_MODEL_ID: str = os.getenv("HF_MODEL_ID", "meta-llama/Meta-Llama-3-8B-Instruct")
    
    # Models storage
    MODEL_DIR: str = os.getenv("MODEL_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "models")))

settings = Settings()
