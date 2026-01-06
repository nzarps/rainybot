import config
import os
from dotenv import load_dotenv

print(f"Loading .env from: {os.getcwd()}")
load_dotenv()

key = os.getenv("GAS_SOURCE_PRIVATE_KEY")
print(f"Raw os.getenv: {key[:5]}..." if key else "Raw os.getenv: None")

print(f"Config.GAS_SOURCE_PRIVATE_KEY: {config.GAS_SOURCE_PRIVATE_KEY[:5]}..." if config.GAS_SOURCE_PRIVATE_KEY else "Config.GAS_SOURCE_PRIVATE_KEY: None")
