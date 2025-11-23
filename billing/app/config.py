import os

class Config:
   DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

   DB_HOST = os.environ['DB_HOST']
   DB_USER = os.environ['DB_USER']
   DB_PASSWORD = os.environ['DB_PASSWORD']
   DB_NAME = os.environ['DB_NAME']
   DB_PORT = os.environ['DB_PORT']
