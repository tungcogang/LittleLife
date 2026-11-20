"""
Frontend API Client for LittleLife FastAPI Backend.
Handles HTTP communication via urllib (no extra dependencies required).
Supports:
- POST /auth/login
- POST /auth/register
- GET /auth/me (Protected with Bearer token)
- POST /pets/create (Protected with Bearer token)
- GET /pets/me (Protected with Bearer token)
- POST /habits/create (Protected with Bearer token)
- GET /habits/ (Protected with Bearer token)
- POST /habits/{habit_id}/complete (Protected with Bearer token)
- POST /care/feed (Protected with Bearer token)
- POST /care/play (Protected with Bearer token)
- POST /care/rest (Protected with Bearer token)
"""
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List


class APIError(Exception):
    """Custom exception holding HTTP status code and error details."""
    def __init__(self, status_code: int, message: str, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.detail = detail


class APIClient:
    """Client for LittleLife FastAPI backend."""
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.token_type: str = "bearer"
        self.current_user: Optional[Dict[str, Any]] = None

    def set_token(self, token: Optional[str], token_type: str = "bearer"):
        """Store the access token safely in memory for this application session."""
        self.access_token = token
        self.token_type = token_type

    def clear_token(self):
        """Clear token on logout or session expiration."""
        self.access_token = None
        self.current_user = None

    def is_authenticated(self) -> bool:
        """Check if an active token is set."""
        return self.access_token is not None

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        auth_required: bool = False,
        timeout: float = 4.0
    ) -> Any:
        """Internal helper to dispatch HTTP requests with JSON serialization."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if auth_required:
            if not self.access_token:
                raise APIError(401, "Authentication required. Please log in.")
            headers["Authorization"] = f"Bearer {self.access_token}"

        body_bytes = None
        if data is not None:
            body_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            url=url,
            data=body_bytes,
            headers=headers,
            method=method.upper()
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                resp_data = response.read().decode("utf-8")
                if resp_data:
                    return json.loads(resp_data)
                return {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            detail = err_body
            msg = f"HTTP {e.code}"
            try:
                parsed = json.loads(err_body)
                if isinstance(parsed, dict) and "detail" in parsed:
                    detail = parsed["detail"]
                    msg = str(detail)
            except Exception:
                pass

            if e.code == 401 and auth_required:
                self.clear_token()
                raise APIError(401, "Session expired or invalid credentials. Please log in again.", detail)
            elif e.code == 404:
                raise APIError(404, msg if msg != f"HTTP {e.code}" else "Resource not found.", detail)
            else:
                raise APIError(e.code, msg, detail)

        except urllib.error.URLError as e:
            reason = getattr(e, "reason", str(e))
            raise APIError(0, f"Cannot connect to backend server ({reason}). Ensure FastAPI is running at {self.base_url}.", str(reason))
        except Exception as e:
            raise APIError(0, f"Unexpected network error: {str(e)}", str(e))

    # --- Authentication Endpoints ---

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        POST /auth/login
        Returns: { 'access_token': str, 'token_type': 'bearer' }
        """
        payload = {"username": username, "password": password}
        res = self._request("POST", "/auth/login", data=payload, auth_required=False)
        token = res.get("access_token")
        token_type = res.get("token_type", "bearer")
        self.set_token(token, token_type)
        return res

    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """
        POST /auth/register
        Returns: { 'id': int, 'username': str, 'email': str }
        """
        payload = {"username": username, "email": email, "password": password}
        return self._request("POST", "/auth/register", data=payload, auth_required=False)

    def get_me(self) -> Dict[str, Any]:
        """
        GET /auth/me (Protected)
        Returns: { 'id': int, 'username': str, 'email': str, 'coins': int }
        """
        res = self._request("GET", "/auth/me", auth_required=True)
        self.current_user = res
        return res

    # --- Pet Endpoints ---

    def create_pet(self, pet_name: str) -> Dict[str, Any]:
        """
        POST /pets/create (Protected)
        Returns: { 'message': str, 'id': int, 'pet_name': str, 'level': int, 'exp': int, ... }
        """
        payload = {"pet_name": pet_name}
        return self._request("POST", "/pets/create", data=payload, auth_required=True)

    def get_my_pet(self) -> Dict[str, Any]:
        """
        GET /pets/me (Protected)
        Returns: {
            'id': int,
            'pet_name': str,
            'level': int,
            'exp': int,
            'hunger': int,
            'happiness': int,
            'energy': int,
            'health': int
        }
        """
        return self._request("GET", "/pets/me", auth_required=True)

    # --- Habit Endpoints ---

    def get_habits(self) -> List[Dict[str, Any]]:
        """
        GET /habits/ (Protected)
        Returns: list of { 'id': int, 'title': str, 'description': str, 'is_active': bool, 'completed_today': bool }
        """
        return self._request("GET", "/habits/", auth_required=True)

    def create_habit(self, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        POST /habits/create (Protected)
        Returns: { 'message': str, 'id': int, 'title': str, 'description': str, 'is_active': bool }
        """
        payload = {"title": title, "description": description}
        return self._request("POST", "/habits/create", data=payload, auth_required=True)

    def complete_habit(self, habit_id: int) -> Dict[str, Any]:
        """
        POST /habits/{habit_id}/complete (Protected)
        Returns: {
            'message': str,
            'habit_id': int,
            'habit_title': str,
            'coins_earned': int,
            'total_coins': int,
            'exp_earned': int,
            'pet_exp': int,
            'pet_level': int,
            'leveled_up': bool
        }
        """
        return self._request("POST", f"/habits/{habit_id}/complete", auth_required=True)

    # --- Pet Care Endpoints ---

    def care_feed(self) -> Dict[str, Any]:
        """
        POST /care/feed (Protected)
        Returns: { 'message': str, 'pet_name': str, 'hunger': int }
        """
        return self._request("POST", "/care/feed", auth_required=True)

    def care_play(self) -> Dict[str, Any]:
        """
        POST /care/play (Protected)
        Returns: { 'message': str, 'pet_name': str, 'happiness': int, 'energy': int }
        """
        return self._request("POST", "/care/play", auth_required=True)

    def care_rest(self) -> Dict[str, Any]:
        """
        POST /care/rest (Protected)
        Returns: { 'message': str, 'pet_name': str, 'energy': int }
        """
        return self._request("POST", "/care/rest", auth_required=True)
