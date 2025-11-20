import os
class Config:
   DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
