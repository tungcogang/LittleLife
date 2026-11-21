from backend.database import SessionLocal, engine
from backend.migrations import ensure_schema
from backend.models import Base
from backend.services.item_service import ensure_catalog


def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_schema(engine)

    # Khởi tạo catalog của Store và đồng bộ hiệu ứng item. Giữ nguyên user, pet,
    # inventory và giá đang có.
    db = SessionLocal()
    try:
        ensure_catalog(db)
    finally:
        db.close()

    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
