import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = ""
    
    DB_PATH: str = "database/reklama.db"
    
    MIN_INTERVAL: int = 5
    MAX_INTERVAL: int = 1440 
    
    MIN_DURATION: int = 5
    MAX_DURATION: int = 10080  

config = Config() 