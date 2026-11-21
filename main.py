"""Điểm khởi động của backend.

Được giữ như một lớp re-export mỏng của ``backend.main`` để cả ``uvicorn main:app``
lẫn ``uvicorn backend.main:app`` đều mở ra đúng cùng một bộ route.
"""

from backend.main import app
__all__ = ["app"]
