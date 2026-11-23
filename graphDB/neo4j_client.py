import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
    driver.verify_connectivity()