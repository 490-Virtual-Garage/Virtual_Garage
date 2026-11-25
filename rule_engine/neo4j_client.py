import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

ENV_PATH = Path(__file__).resolve().parent / "neo4j.env"
load_dotenv(ENV_PATH)
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

if __name__ == "__main__":
    with get_driver() as driver:
        driver.verify_connectivity()
        print("connected")
   