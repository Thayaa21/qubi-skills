"""
client.py — HTTP client for qubi Agentic Flows API.

Thin wrapper around the REST endpoints. Uses session cookies for auth.
"""

import json
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from qcli.auth import load_session, require_login, DEFAULT_AGENTHUB


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class QubiClient:
    """HTTP client for qubi AgentHub API."""

    def __init__(self, base_url: str | None = None):
        if requests is None:
            raise ImportError("'requests' library required. pip install requests")

        session_data = require_login()
        self.base_url = base_url or session_data.get("server_url", DEFAULT_AGENTHUB)
        self.session = requests.Session()
        self.session.verify = False

        # Load cookies from stored session
        cookies = session_data.get("cookies", {})
        for name, value in cookies.items():
            self.session.cookies.set(name, value, domain=self.base_url.split("//")[1].split("/")[0])

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    # ----- Workflows -----

    def list_workflows(self, search: str = "") -> list:
        """Search/list workflows."""
        resp = self.session.post(
            self._url("/api/v1/workflow/search"),
            json={"search": search},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_graph(self, workflow_id: str) -> dict:
        """Get workflow graph (nodes + edges)."""
        resp = self.session.get(
            self._url(f"/api/v1/workflow/{workflow_id}/graph"),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # The response might be a string or an object with graphJson
        if isinstance(data, str):
            return json.loads(data)
        if isinstance(data, dict) and "graphJson" in data:
            graph_json = data["graphJson"]
            if isinstance(graph_json, str):
                return json.loads(graph_json)
            return graph_json
        return data

    def save_graph(self, workflow_id: str, graph: dict) -> dict:
        """Save workflow graph to qubi."""
        payload = {"graphJson": json.dumps(graph)}
        resp = self.session.post(
            self._url(f"/api/v1/workflow/{workflow_id}/graph"),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            return {"status": resp.status_code, "text": resp.text}

    # ----- Agents -----

    def list_agents(self) -> list:
        """Get all available agents."""
        resp = self.session.get(
            self._url("/api/v1/getallagents"),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ----- RPA -----

    def list_rpa_automations(self) -> list:
        """Get all available RPA automations."""
        resp = self.session.get(
            self._url("/api/v1/getrpaautomations"),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    # ----- Execution -----

    def run_workflow(self, workflow_id: str, input_data: dict | None = None) -> dict:
        """Execute a workflow (trigger a job)."""
        payload = {"workflowId": workflow_id}
        if input_data:
            payload["input"] = input_data
        resp = self.session.post(
            self._url("/api/v1/job/run"),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_job_status(self, job_id: str) -> dict:
        """Check job execution status."""
        resp = self.session.get(
            self._url(f"/api/v1/job/{job_id}"),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
