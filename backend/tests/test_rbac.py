"""
SecureRAG RBAC and Filter Logic Test Suite.

Covers all security requirements:
- Correct role access
- Wrong department denied
- Typo-style department mismatch (distinct from null)
- Insufficient clearance denied
- Mismatched boolean logic protection (no OR leak)
- Admin clearance overrides department restriction
- Missing metadata on document chunks fails closed (must_not isEmpty)
- Null/unset user properties fail closed
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend root is in import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rbac import User, build_qdrant_filter, retrieve_authorized_chunks
from qdrant_client.http.models import Filter, FieldCondition, Range, MatchValue, IsEmptyCondition


class TestRBACFilterBuilder(unittest.TestCase):
    """Unit tests for build_qdrant_filter pure function."""

    def test_admin_sees_everything_up_to_clearance(self):
        """Verify that an admin has no department constraints but is limited by clearance."""
        user = User(role="admin", clearance_level=2)
        q_filter = build_qdrant_filter(user)

        # Admins should not have a department condition in must clause
        self.assertEqual(len(q_filter.must), 1)
        self.assertEqual(q_filter.must[0].key, "sensitivity_level")
        self.assertEqual(q_filter.must[0].range.lte, 2)

        # Verify missing metadata is excluded
        self.assertEqual(len(q_filter.must_not), 2)
        self.assertTrue(isinstance(q_filter.must_not[0], IsEmptyCondition))

    def test_non_admin_department_and_clearance_logic(self):
        """Verify non-admin queries must match BOTH clearance and department rules (AND logic)."""
        user = User(role="engineer", department="engineering", clearance_level=1)
        q_filter = build_qdrant_filter(user)

        # Must contain both conditions
        self.assertEqual(len(q_filter.must), 2)

        # First condition: sensitivity range check
        self.assertEqual(q_filter.must[0].key, "sensitivity_level")
        self.assertEqual(q_filter.must[0].range.lte, 1)

        # Second condition: department match OR 'all'
        dept_filter = q_filter.must[1]
        self.assertEqual(len(dept_filter.should), 2)
        self.assertEqual(dept_filter.should[0].key, "department")
        self.assertEqual(dept_filter.should[0].match.value, "engineering")
        self.assertEqual(dept_filter.should[1].match.value, "all")

    def test_typo_style_department_mismatch(self):
        """Verify typo-style department mismatch fails closed.
        
        A typo like 'engineerng' (distinct from null) must build a filter matching
        strictly 'engineerng' or 'all' (which fails to match 'engineering' chunks).
        """
        user = User(role="engineer", department="engineerng", clearance_level=1)
        q_filter = build_qdrant_filter(user)

        # Must build a filter that matches the typo department
        dept_filter = q_filter.must[1]
        self.assertEqual(dept_filter.should[0].match.value, "engineerng")
        self.assertEqual(dept_filter.should[1].match.value, "all")

    def test_fail_closed_on_unset_user_clearance(self):
        """Verify that if the user's clearance_level is null/unset, they get zero results."""
        user = User(role="engineer", department="engineering", clearance_level=None)
        q_filter = build_qdrant_filter(user)

        # Should return an impossible match filter
        self.assertEqual(len(q_filter.must), 1)
        self.assertEqual(q_filter.must[0].key, "sensitivity_level")
        self.assertEqual(q_filter.must[0].range.lt, 0)

    def test_fail_closed_on_unset_user_department_non_admin(self):
        """Verify that if a non-admin's department is null/unset, they get zero results."""
        user = User(role="engineer", department=None, clearance_level=2)
        q_filter = build_qdrant_filter(user)

        # Should return an impossible match filter
        self.assertEqual(len(q_filter.must), 1)
        self.assertEqual(q_filter.must[0].key, "sensitivity_level")
        self.assertEqual(q_filter.must[0].range.lt, 0)


class TestRBACRetrievalIntegration(unittest.TestCase):
    """Integration/Mock tests for retrieve_authorized_chunks function."""

    @patch("app.rbac.embed_chunks")
    @patch("app.rbac._get_client")
    def test_retrieve_authorized_chunks_with_correct_rbac(self, mock_get_client, mock_embed_chunks):
        """Verify retrieve_authorized_chunks enforces correct filters and builds trace."""
        mock_embed_chunks.return_value = [[0.1] * 384]

        # Mock Qdrant client and query responses
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Define mock response points
        allowed_point = MagicMock()
        allowed_point.score = 0.95
        allowed_point.payload = {
            "text": "Engineering guideline content",
            "document_id": "doc-1234",
            "department": "engineering",
            "sensitivity_level": 0,
            "chunk_index": 1
        }

        denied_point = MagicMock()
        denied_point.score = 0.92
        denied_point.payload = {
            "text": "Confidential Strategic Report",
            "document_id": "doc-5678",
            "department": "admin",
            "sensitivity_level": 3,
            "chunk_index": 2
        }

        # Query with filter returns only allowed point
        mock_auth_response = MagicMock()
        mock_auth_response.points = [allowed_point]

        # Unfiltered query returns both points
        mock_unfiltered_response = MagicMock()
        mock_unfiltered_response.points = [allowed_point, denied_point]

        # Configure mock client query results
        mock_client.query_points.side_effect = [mock_auth_response, mock_unfiltered_response]

        # Execute authorized retrieval for L0 engineering user
        user = User(role="engineer", department="engineering", clearance_level=0)
        result = retrieve_authorized_chunks(query="How to push code?", user=user)

        # Assert allowed set
        self.assertEqual(len(result.chunks), 1)
        self.assertEqual(result.chunks[0].text, "Engineering guideline content")
        self.assertEqual(result.chunks[0].score, 0.95)

        # Assert audit trace
        self.assertEqual(result.excluded_count, 1)
        self.assertIn("insufficient clearance", result.denial_reason)
        self.assertIn("required L3", result.denial_reason)


if __name__ == "__main__":
    unittest.main()
