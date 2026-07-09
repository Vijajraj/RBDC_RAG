"""
SecureRAG Unit Test Suite.

Uses the built-in unittest library to verify core functions of
the application (auth, token generation, chunking logic).
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.services.ingestion import chunk_text


class TestAuthentication(unittest.TestCase):
    """Test suites for user authentication and token creation."""

    def test_password_hashing(self):
        """Verify that password hashing and checkpw verification work correctly."""
        password = "mySecretPassword123"
        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_jwt_generation_and_decoding(self):
        """Verify that JWT tokens can be created and decoded correctly."""
        payload = {
            "sub": "test-uuid-1234",
            "email": "user@securerag.com",
            "role": "engineer",
            "department": "engineering",
            "clearance_level": 0
        }

        token = create_access_token(payload)
        self.assertIsInstance(token, str)

        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], payload["sub"])
        self.assertEqual(decoded["email"], payload["email"])
        self.assertEqual(decoded["role"], payload["role"])
        self.assertEqual(decoded["department"], payload["department"])
        self.assertEqual(decoded["clearance_level"], payload["clearance_level"])


class TestIngestion(unittest.TestCase):
    """Test suites for ingestion service functions."""

    def test_text_chunking(self):
        """Verify text chunking behaves correctly with specified size and overlap."""
        text = "This is a sample document for testing the text chunking mechanism. It should split this string properly."
        
        # Test basic chunking with size 20 and overlap 5
        chunks = chunk_text(text, chunk_size=20, overlap=5)
        
        self.assertTrue(len(chunks) > 0)
        # Ensure no chunk exceeds the maximum character count
        for chunk in chunks:
            self.assertTrue(len(chunk) <= 20)

    def test_empty_text_chunking(self):
        """Verify empty or whitespace-only inputs return an empty list."""
        self.assertEqual(chunk_text(""), [])
        self.assertEqual(chunk_text("   \n   "), [])


if __name__ == "__main__":
    unittest.main()
