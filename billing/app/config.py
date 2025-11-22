import os

class Config:
   DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
   DB_HOST = os.getenv('DB_HOST', 'localhost')
   DB_USER = os.getenv('DB_USER', 'root')
   DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
   DB_NAME = os.getenv('DB_NAME', 'billdb')
   DB_PORT = os.getenv('DB_PORT', '3036')
