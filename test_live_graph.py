
import unittest

from tools import (
    get_incident_details,
    find_affected_services,
    get_dependency_chain,
    get_runbooks,
)


class TestLiveFalkorDB(unittest.TestCase):

    def test_incident_exists(self):
        incident = get_incident_details("INC-001")

        self.assertIsNotNone(incident)
        self.assertEqual(incident["service"], "Database")

    def test_unknown_incident_is_missing(self):
        incident = get_incident_details("INC-999")

        self.assertIsNone(incident)

    def test_affected_services(self):
        services = find_affected_services("Database")

        self.assertEqual(
            set(services),
            {"API Gateway", "Payment Service"},
        )

    def test_dependency_paths(self):
        paths = get_dependency_chain("Database")

        self.assertIn(
            ["Payment Service", "Database"],
            paths,
        )
        self.assertIn(
            ["API Gateway", "Payment Service", "Database"],
            paths,
        )

    def test_linked_runbook(self):
        runbooks = get_runbooks("Database")

        self.assertTrue(
            any(
                runbook["id"] == "RB-001"
                and runbook["title"]
                == "Database Connection Troubleshooting"
                and runbook["steps"]
                for runbook in runbooks
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
