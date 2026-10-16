
import unittest
from unittest.mock import patch

import tools


class TestTraceFixTools(unittest.TestCase):

    @patch("tools.get_incident_details")
    @patch("tools.find_affected_services")
    @patch("tools.get_dependency_chain")
    @patch("tools.get_runbooks")
    def test_missing_incident_stops_investigation(
        self,
        mock_runbooks,
        mock_chains,
        mock_affected,
        mock_incident,
    ):
        mock_incident.return_value = None

        result = tools.investigate_incident("INC-999")

        self.assertIsNotNone(result)
        self.assertIn("error", result)
        self.assertEqual(
            result["error"],
            "Incident not found in FalkorDB.",
        )

        mock_affected.assert_not_called()
        mock_chains.assert_not_called()
        mock_runbooks.assert_not_called()

    @patch("tools.get_incident_details")
    @patch("tools.find_affected_services")
    @patch("tools.get_dependency_chain")
    @patch("tools.get_runbooks")
    def test_valid_incident_returns_graph_evidence(
        self,
        mock_runbooks,
        mock_chains,
        mock_affected,
        mock_incident,
    ):
        mock_incident.return_value = {
            "incident_id": "INC-001",
            "title": "Database connection failures",
            "service": "Database",
        }
        mock_affected.return_value = [
            "API Gateway",
            "Payment Service",
        ]
        mock_chains.return_value = [
            ["API Gateway", "Payment Service", "Database"],
            ["Payment Service", "Database"],
        ]
        mock_runbooks.return_value = [
            {
                "id": "RB-001",
                "title": "Database Connection Troubleshooting",
                "steps": "Check database health.",
                "status": None,
            }
        ]

        result = tools.investigate_incident("INC-001")

        self.assertEqual(
            result["incident"]["service"],
            "Database",
        )
        self.assertIn(
            ["Payment Service", "Database"],
            result["dependency_chains"],
        )
        self.assertIn(
            ["API Gateway", "Payment Service", "Database"],
            result["dependency_chains"],
        )
        self.assertEqual(len(result["runbooks"]), 1)

    def test_dependency_direction_is_interpreted_correctly(self):
        # These are the paths returned by the current graph.
        paths = [
            ["API Gateway", "Payment Service", "Database"],
            ["Payment Service", "Database"],
        ]

        direct_dependents = {
            path[-2] for path in paths if len(path) == 2
        }
        indirect_dependents = {
            path[0] for path in paths if len(path) > 2
        }

        self.assertEqual(direct_dependents, {"Payment Service"})
        self.assertEqual(indirect_dependents, {"API Gateway"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
