#!/usr/bin/env python3
"""
Debug script using the same test environment as pytest
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import get_db, Base
from app.models import Pharmacy, Mask, User, Transaction

# Use the same test database setup as conftest.py
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency injection for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the app's database dependency
app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(app)

# Test the actual response in test environment
print("Testing mask stock update with non-existent ID...")
response = client.patch("/api/v1/masks/99999/stock", json={"quantity_change": 10})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

if response.status_code == 500:
    print("ERROR: 500 status detected in test environment!")
    print(f"Full response text: {response.text}")
elif response.status_code == 404:
    print("SUCCESS: Correct 404 status returned")
else:
    print(f"UNEXPECTED: Status code {response.status_code}")

# Clean up
Base.metadata.drop_all(bind=engine)