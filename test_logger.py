
import sys
import os

# Ensure we can import 'app'
sys.path.append("/home/aryangp/code/fi_app/f1_race_backend")

try:
    from app.services.mongo_logger import mongo_logger
    print(f"Logger Enabled: {mongo_logger.enabled}")
    if mongo_logger.enabled:
        mongo_logger.info("Test log from setup script")
        print("Logged test message")
    else:
        print("Logger disabled, check settings")
except Exception as e:
    print(f"Error: {e}")
