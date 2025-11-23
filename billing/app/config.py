import os

class Config:
   DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

   DB_HOST = os.getenv('DB_HOST')
   DB_USER = os.getenv('DB_USER')
   DB_PASSWORD = os.getenv('DB_PASSWORD')
   DB_NAME = os.getenv('DB_NAME')
   DB_PORT = os.getenv('DB_PORT')
