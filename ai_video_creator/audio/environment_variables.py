"""
This module loads environment variables from a .env file.
"""

import os
from dotenv import load_dotenv


load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

