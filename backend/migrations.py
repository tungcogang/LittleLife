"""Các bước nâng cấp schema nhỏ, idempotent cho database LittleLife hiện có.

Dự án dùng ``Base.metadata.create_all``, lệnh này chỉ tạo bảng còn thiếu chứ
không bao giờ sửa bảng đã tồn tại. Các hàm bên dưới thêm những cột tùy chọn được
đưa vào sau bản phát hành đầu tiên, không xóa hay tạo lại bất cứ thứ gì.
Chúng an toàn để chạy ở mỗi lần khởi động.
"""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError


def _column_exists(engine: Engine, table: str, column: str) -> bool:
    return column in {col["name"] for col in inspect(engine).get_columns(table)}


def _add_column(engine: Engine, table: str, column: str, ddl: str) -> bool:
    """Thêm ``column`` nếu còn thiếu. Trả về True khi lời gọi này đã thêm cột."""
    if _column_exists(engine, table, column):
        return False

    try:
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
    except OperationalError:
        # Tiến trình khác có thể đã thêm cột trong khoảng giữa lúc kiểm tra và
        # lúc chạy ALTER; chỉ ném lại lỗi khi cột thực sự vẫn còn thiếu.
        if _column_exists(engine, table, column):
            return False
        raise

    return True


def ensure_schema(engine: Engine) -> None:
    """Áp dụng các nâng cấp cột tối thiểu mà các model hiện tại cần."""
    tables = set(inspect(engine).get_table_names())

    if "pets" in tables:
        added_decay_date = _add_column(
            engine,
            "pets",
            "last_decay_date",
            "last_decay_date DATE NULL",
        )

        if added_decay_date:
            # Các pet đang có chưa biết ngày "xử lý lần cuối". Lấy hôm qua làm
            # mốc để request pet đầu tiên của chúng chỉ bị trừ đúng một ngày
            # (thay vì trừ cho một khoảng trống không xác định).
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "UPDATE pets "
                        "SET last_decay_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY) "
                        "WHERE last_decay_date IS NULL"
                    )
                )

    if "items" in tables:
        _add_column(
            engine,
            "items",
            "secondary_effect_type",
            "secondary_effect_type VARCHAR(30) NULL",
        )
        _add_column(
            engine,
            "items",
            "secondary_effect_value",
            "secondary_effect_value INTEGER NULL",
        )
