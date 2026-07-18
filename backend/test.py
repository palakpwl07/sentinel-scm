# test_connection.py — run from backend/ with: python test_connection.py
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = "neo4j+s://210b6db6.databases.neo4j.io"
user = "210b6db6"
password = "QBf4Y6Y0mNbV7E24eeuDBmgsd5lLurYCXQY9zqXC3xc"

print(f"URI: {uri}")
print(f"User: {user}")

driver = GraphDatabase.driver(uri, auth=(user, password))
try:
    driver.verify_connectivity()
    print("✅ Connected successfully")
except Exception as e:
    print(f"❌ Failed: {e}")
driver.close()