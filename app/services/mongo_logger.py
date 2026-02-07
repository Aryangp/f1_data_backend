
import logging
from pymongo import MongoClient
from datetime import datetime
from app.config import settings
import traceback

class MongoLogger:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.enabled = False
        
        if hasattr(settings, "MONGO_URI") and settings.MONGO_URI:
            try:
                self.client = MongoClient(settings.MONGO_URI)
                db_name = getattr(settings, "MONGO_DB_NAME", "f1_logs")
                self.db = self.client[db_name]
                self.collection = self.db["application_logs"]
                self.enabled = True
                print(f"MongoDB Logging Enabled: Connected to {db_name}")
            except Exception as e:
                print(f"Failed to initialize MongoDB Logger: {e}")

    def log(self, level: str, message: str, context: dict = None, error: Exception = None):
        if not self.enabled:
            print(f"[{level}] {message} (MongoDB Logging Disabled)")
            return

        log_entry = {
            "timestamp": datetime.utcnow(),
            "level": level.upper(),
            "message": message,
            "context": context or {},
        }

        if error:
            log_entry["error"] = str(error)
            log_entry["traceback"] = traceback.format_exc()

        try:
            self.collection.insert_one(log_entry)
        except Exception as e:
            print(f"Failed to write log to MongoDB: {e}")

    def info(self, message: str, context: dict = None):
        self.log("INFO", message, context)

    def error(self, message: str, error: Exception = None, context: dict = None):
        self.log("ERROR", message, context, error)

    def warning(self, message: str, context: dict = None):
        self.log("WARNING", message, context)

    def debug(self, message: str, context: dict = None):
        self.log("DEBUG", message, context)

# Global instance
mongo_logger = MongoLogger()
