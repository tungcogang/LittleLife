"""
API Client phía frontend cho backend FastAPI của LittleLife.
Xử lý giao tiếp HTTP qua urllib (không cần thêm dependency).
Hỗ trợ:
- POST /auth/login
- POST /auth/register
- GET /auth/me (Bảo vệ bằng Bearer token)
- POST /pets/create (Bảo vệ bằng Bearer token)
- GET /pets/me (Bảo vệ bằng Bearer token)
- POST /habits/create (Bảo vệ bằng Bearer token)
- GET /habits/ (Bảo vệ bằng Bearer token)
- POST /habits/{habit_id}/complete (Bảo vệ bằng Bearer token)
- POST /care/feed (Bảo vệ bằng Bearer token)
- POST /care/play (Bảo vệ bằng Bearer token)
- POST /care/rest (Bảo vệ bằng Bearer token)
- GET /store/items (Bảo vệ bằng Bearer token)
- POST /store/buy/{item_id} (Bảo vệ bằng Bearer token)
- GET /inventory/ (Bảo vệ bằng Bearer token)
- POST /inventory/{item_id}/use (Bảo vệ bằng Bearer token)
"""
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List


class APIError(Exception):
    """Exception tùy chỉnh chứa mã trạng thái HTTP và chi tiết lỗi."""
    def __init__(self, status_code: int, message: str, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.detail = detail


class APIClient:
    """Client cho backend FastAPI của LittleLife."""
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self.access_token: Optional[str] = None
        self.token_type: str = "bearer"
        self.current_user: Optional[Dict[str, Any]] = None

    def set_token(self, token: Optional[str], token_type: str = "bearer"):
        """Lưu access token an toàn trong bộ nhớ cho phiên ứng dụng này."""
        self.access_token = token
        self.token_type = token_type

    def clear_token(self):
        """Xóa token khi đăng xuất hoặc khi phiên hết hạn."""
        self.access_token = None
        self.current_user = None

    def is_authenticated(self) -> bool:
        """Kiểm tra xem đã có token còn hiệu lực hay chưa."""
        return self.access_token is not None

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        auth_required: bool = False,
        timeout: float = 4.0
    ) -> Any:
        """Hàm phụ nội bộ để gửi HTTP request kèm JSON serialization."""
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
                    if isinstance(detail, list) and detail:
                        # Lỗi validation của FastAPI: tạo message dễ đọc.
                        first = detail[0] if isinstance(detail[0], dict) else {}
                        field = ".".join(str(part) for part in first.get("loc", [])[1:])
                        reason = first.get("msg", "Invalid value")
                        msg = f"{field}: {reason}" if field else reason
                    else:
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

    # --- Các endpoint xác thực ---

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        POST /auth/login
        Trả về: { 'access_token': str, 'token_type': 'bearer' }
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
        Trả về: { 'id': int, 'username': str, 'email': str }
        """
        payload = {"username": username, "email": email, "password": password}
        return self._request("POST", "/auth/register", data=payload, auth_required=False)

    def get_me(self) -> Dict[str, Any]:
        """
        GET /auth/me (Yêu cầu đăng nhập)
        Trả về: { 'id': int, 'username': str, 'email': str, 'coins': int }
        """
        res = self._request("GET", "/auth/me", auth_required=True)
        self.current_user = res
        return res

    # --- Các endpoint Pet ---

    def create_pet(self, pet_name: str) -> Dict[str, Any]:
        """
        POST /pets/create (Yêu cầu đăng nhập)
        Trả về: { 'message': str, 'id': int, 'pet_name': str, 'level': int, 'exp': int, ... }
        """
        payload = {"pet_name": pet_name}
        return self._request("POST", "/pets/create", data=payload, auth_required=True)

    def get_my_pet(self) -> Dict[str, Any]:
        """
        GET /pets/me (Yêu cầu đăng nhập)
        Trả về: {
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

    # --- Các endpoint Habit ---

    def get_habits(self) -> List[Dict[str, Any]]:
        """
        GET /habits/ (Yêu cầu đăng nhập)
        Trả về: list of { 'id': int, 'title': str, 'description': str, 'is_active': bool, 'completed_today': bool }
        """
        return self._request("GET", "/habits/", auth_required=True)

    def create_habit(self, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        POST /habits/create (Yêu cầu đăng nhập)
        Trả về: { 'message': str, 'id': int, 'title': str, 'description': str, 'is_active': bool }
        """
        payload = {"title": title, "description": description}
        return self._request("POST", "/habits/create", data=payload, auth_required=True)

    def complete_habit(self, habit_id: int) -> Dict[str, Any]:
        """
        POST /habits/{habit_id}/complete (Yêu cầu đăng nhập)
        Trả về: {
            'message': str,
            'habit_id': int,
            'habit_title': str,
            'coins_earned': int,
            'total_coins': int,
            'exp_earned': int,
            'pet_exp': int,
            'pet_level': int,
            'leveled_up': bool,
            'pet': dict
        }
        """
        return self._request("POST", f"/habits/{habit_id}/complete", auth_required=True)

    def delete_habit(self, habit_id: int) -> Dict[str, Any]:
        """
        DELETE /habits/{habit_id} (Yêu cầu đăng nhập)
        Trả về: {
            'message': str,
            'habit_id': int,
            'habit_title': str
        }
        """
        return self._request("DELETE", f"/habits/{habit_id}", auth_required=True)

    # --- Các endpoint chăm sóc Pet ---

    def care_feed(self) -> Dict[str, Any]:
        """
        POST /care/feed (Yêu cầu đăng nhập)
        Trả về: { 'message': str, 'pet_name': str, 'hunger': int, 'pet': dict }
        """
        return self._request("POST", "/care/feed", auth_required=True)

    def care_play(self) -> Dict[str, Any]:
        """
        POST /care/play (Yêu cầu đăng nhập)
        Trả về: { 'message': str, 'pet_name': str, 'happiness': int, 'energy': int,
                   'hunger': int, 'pet': dict }
        """
        return self._request("POST", "/care/play", auth_required=True)

    def care_rest(self) -> Dict[str, Any]:
        """
        POST /care/rest (Yêu cầu đăng nhập)
        Trả về: { 'message': str, 'pet_name': str, 'energy': int, 'health': int,
                   'pet': dict }
        """
        return self._request("POST", "/care/rest", auth_required=True)

    # --- Các endpoint Store ---

    def get_store_items(self) -> Dict[str, Any]:
        """
        GET /store/items (Yêu cầu đăng nhập)
        Trả về: {
            'coins': int,
            'items': [ { 'id': int, 'name': str, 'description': str, 'item_type': str,
                         'price': int, 'effect_type': str, 'effect_value': int,
                         'secondary_effect_type': str | None,
                         'secondary_effect_value': int | None } ]
        }
        """
        return self._request("GET", "/store/items", auth_required=True)

    def buy_item(self, item_id: int) -> Dict[str, Any]:
        """
        POST /store/buy/{item_id} (Yêu cầu đăng nhập)
        Trả về: {
            'message': str, 'item': dict, 'quantity': int,
            'coins': int, 'inventory': [ ... ]
        }
        """
        return self._request("POST", f"/store/buy/{item_id}", auth_required=True)

    # --- Các endpoint Backpack ---

    def get_inventory(self) -> Dict[str, Any]:
        """
        GET /inventory/ (Yêu cầu đăng nhập)
        Trả về: {
            'coins': int,
            'items': [ { 'item_id': int, 'name': str, 'description': str, 'item_type': str,
                         'price': int, 'effect_type': str, 'effect_value': int,
                         'secondary_effect_type': str | None,
                         'secondary_effect_value': int | None,
                         'quantity': int } ]
        }
        """
        return self._request("GET", "/inventory/", auth_required=True)

    def use_item(self, item_id: int) -> Dict[str, Any]:
        """
        POST /inventory/{item_id}/use (Yêu cầu đăng nhập)
        Trả về: {
            'message': str, 'item': dict, 'quantity': int,
            'applied_effects': [ { 'type': str, 'value': int } ],
            'pet': dict, 'coins': int, 'inventory': [ ... ]
        }
        """
        return self._request("POST", f"/inventory/{item_id}/use", auth_required=True)
