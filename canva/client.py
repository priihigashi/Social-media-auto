"""Canva Connect REST API client (v1)."""
import time
from typing import Optional

import requests

CANVA_API_BASE = "https://api.canva.com/rest/v1"


class CanvaClient:
    def __init__(self, token: str):
        self._session = requests.Session()
        self._session.headers.update(
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )

    # ── Designs ───────────────────────────────────────────────────────────────

    def list_designs(self, ownership: str = "owned") -> list[dict]:
        """Return all designs the user owns (handles pagination automatically)."""
        designs: list[dict] = []
        params: dict = {"ownership": ownership, "limit": 50}
        url = f"{CANVA_API_BASE}/designs"

        while url:
            resp = self._get(url, params=params)
            data = resp.json()
            designs.extend(data.get("items", []))
            continuation = data.get("continuation")
            if continuation:
                # Subsequent pages use only the continuation token
                url = f"{CANVA_API_BASE}/designs"
                params = {"continuation": continuation}
            else:
                url = None  # type: ignore[assignment]

        return designs

    # ── Folders ───────────────────────────────────────────────────────────────

    def create_folder(self, name: str, parent_folder_id: Optional[str] = None) -> dict:
        """Create a folder and return its metadata dict."""
        payload: dict = {"name": name}
        if parent_folder_id:
            payload["parent_folder_id"] = parent_folder_id
        resp = self._post(f"{CANVA_API_BASE}/folders", json=payload)
        return resp.json()["folder"]

    def list_folder_items(self, folder_id: str) -> list[dict]:
        """Return all items inside a folder (handles pagination)."""
        items: list[dict] = []
        params: dict = {"limit": 50}
        url = f"{CANVA_API_BASE}/folders/{folder_id}/items"

        while url:
            resp = self._get(url, params=params)
            data = resp.json()
            items.extend(data.get("items", []))
            continuation = data.get("continuation")
            if continuation:
                url = f"{CANVA_API_BASE}/folders/{folder_id}/items"
                params = {"continuation": continuation}
            else:
                url = None  # type: ignore[assignment]

        return items

    def move_to_folder(self, folder_id: str, item_id: str, item_type: str = "design") -> None:
        """Move a design or sub-folder into the target folder."""
        payload = {"items": [{"type": item_type, "id": item_id}]}
        self._post(f"{CANVA_API_BASE}/folders/{folder_id}/items", json=payload)

    # ── Internal HTTP helpers ─────────────────────────────────────────────────

    def _get(self, url: str, **kwargs) -> requests.Response:
        return self._request("GET", url, **kwargs)

    def _post(self, url: str, **kwargs) -> requests.Response:
        return self._request("POST", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        for attempt in range(4):
            resp = self._session.request(method, url, **kwargs)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 2 ** attempt))
                time.sleep(retry_after)
                continue
            resp.raise_for_status()
            return resp
        resp.raise_for_status()  # raise on final attempt
        return resp  # unreachable but satisfies type checker
