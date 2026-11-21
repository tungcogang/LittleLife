"""
Kiểm thử tích hợp API end-to-end của LittleLife.

Chạy với máy chủ FastAPI đang hoạt động và database MySQL thật:

    # terminal 1
    .\\.venv\\Scripts\\python.exe -B -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

    # terminal 2
    .\\.venv\\Scripts\\python.exe -B test\\e2e_integration.py

Bao gồm xác thực, nhận nuôi pet, giới hạn chăm sóc, suy giảm Happiness/Health hằng ngày,
thưởng habit và lên cấp, kinh tế Store, vật phẩm đa hiệu ứng, lưu trữ dữ liệu,
cô lập giữa các user và request đồng thời. Tài khoản tạm ``e2e_*`` được
tạo rồi xóa lại; dữ liệu có sẵn chỉ được đọc.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import jwt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import SessionLocal
from backend.models import (  # noqa: E402
    Habit,
    HabitCompletion,
    Inventory,
    Item,
    Pet,
    Transaction,
    User,
)
from backend.services.token_service import ALGORITHM, SECRET_KEY  # noqa: E402

BASE_URL = os.getenv("LITTLELIFE_API_URL", "http://127.0.0.1:8000").rstrip("/")
CHECKED = 0


# ----------------------------------------------------------------------
# Hàm hỗ trợ
# ----------------------------------------------------------------------
def api(method, path, token=None, payload=None):
    """Thực hiện một request JSON và trả về (status_code, body đã parse)."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        f"{BASE_URL}{path}", data=data, headers=headers, method=method.upper()
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            return response.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return error.code, parsed


def check(condition, label, extra=""):
    """Ghi nhận một assertion."""
    global CHECKED
    CHECKED += 1
    if not condition:
        raise AssertionError(f"FAILED: {label}{(' -> ' + str(extra)) if extra else ''}")
    print(f"  PASS  {label}")


def expect_status(response, expected, label):
    status, body = response
    check(status == expected, label, f"expected HTTP {expected}, got {status}: {body}")
    return body


def login(username, password):
    status, body = api("POST", "/auth/login", payload={"username": username, "password": password})
    check(status == 200 and "access_token" in body, f"login {username}", body)
    return body["access_token"]


def create_habits(token, count, prefix):
    habit_ids = []
    for index in range(count):
        status, body = api(
            "POST",
            "/habits/create",
            token=token,
            payload={
                "title": f"{prefix} task {index + 1}",
                "description": f"E2E habit number {index + 1}",
            },
        )
        if status != 200 or not body.get("id"):
            raise AssertionError(f"create habit {index + 1} failed: {status} {body}")
        habit_ids.append(body["id"])

    check(len(habit_ids) == count, f"{count} habits created", len(habit_ids))
    return habit_ids


def complete(token, habit_id):
    return api("POST", f"/habits/{habit_id}/complete", token=token)


def delete(token, habit_id):
    return api("DELETE", f"/habits/{habit_id}", token=token)


def find_item(items, name):
    for item in items:
        if item["name"] == name:
            return item
    raise AssertionError(f"Item {name!r} not found in catalog: {items}")


def effects_of(body):
    """Trích xuất {stat: applied_value} từ phản hồi khi dùng vật phẩm."""
    return {
        entry["type"]: entry["value"]
        for entry in body.get("applied_effects", [])
    }


def db_set_pet(username, **fields):
    """Thiết lập trạng thái chỉ dành cho test cho các kịch bản guard/decay cụ thể."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).one()
        pet = db.query(Pet).filter(Pet.user_id == user.id).one()

        for name, value in fields.items():
            if not hasattr(pet, name):
                raise AttributeError(f"Pet has no field {name}")
            setattr(pet, name, value)

        db.commit()
    finally:
        db.close()


def db_get_pet(username):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).one()
        pet = db.query(Pet).filter(Pet.user_id == user.id).one()
        return {
            "level": pet.level,
            "exp": pet.exp,
            "hunger": pet.hunger,
            "happiness": pet.happiness,
            "energy": pet.energy,
            "health": pet.health,
            "last_decay_date": pet.last_decay_date,
        }
    finally:
        db.close()


def db_snapshot():
    """Ảnh chụp chỉ đọc của dữ liệu có sẵn, không bao giờ được thay đổi."""
    db = SessionLocal()
    try:
        tung = db.query(User).filter(User.username == "tung").first()
        e2e_users = db.query(User).filter(User.username.like("e2e_%"))
        e2e_ids = [user.id for user in e2e_users]

        def count_non_e2e(query, column):
            return query.filter(~column.in_(e2e_ids)).count() if e2e_ids else query.count()

        return {
            "users": db.query(User).filter(~User.username.like("e2e_%")).count(),
            "pets": count_non_e2e(db.query(Pet), Pet.user_id),
            "habits": count_non_e2e(db.query(Habit), Habit.user_id),
            "completions": db.query(HabitCompletion).count(),
            "inventory": count_non_e2e(db.query(Inventory), Inventory.user_id),
            "transactions": count_non_e2e(db.query(Transaction), Transaction.user_id),
            "tung_coins": tung.coins if tung else None,
            "tung_pet": (
                (tung.pet.level, tung.pet.exp, tung.pet.hunger, tung.pet.happiness,
                 tung.pet.energy, tung.pet.health)
                if tung and tung.pet else None
            ),
        }
    finally:
        db.close()


def cleanup_test_users():
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.username.like("e2e_%")).all()
        usernames = [user.username for user in users]
        for user in users:
            # User.pet không có cascade xóa ở ORM, nên phải xóa tường minh trước.
            db.query(Pet).filter(Pet.user_id == user.id).delete(synchronize_session=False)
            db.delete(user)
        db.commit()
        return usernames
    finally:
        db.close()


# ----------------------------------------------------------------------
# Kịch bản test
# ----------------------------------------------------------------------
def run():
    started = time.time()
    suffix = str(int(started))
    user_a = f"e2e_a_{suffix}"
    user_b = f"e2e_b_{suffix}"
    user_c = f"e2e_c_{suffix}"
    password = "TestPass123!"
    email_domain = "e2e.invalid"
    today = date.today()
    yesterday = today - timedelta(days=1)

    print("\n[1] Health & registration")
    status, body = api("GET", "/health")
    check(status == 200 and body.get("status") == "healthy", "health endpoint", body)

    status, body = api(
        "POST", "/auth/register",
        payload={"username": user_a, "email": f"{user_a}@{email_domain}", "password": password},
    )
    user_a_id = expect_status((status, body), 201, "register new user").get("id")

    status, body = api(
        "POST", "/auth/register",
        payload={"username": user_a, "email": f"other_{user_a}@{email_domain}", "password": password},
    )
    expect_status((status, body), 409, "duplicate username rejected")

    status, body = api(
        "POST", "/auth/register",
        payload={"username": f"{user_a}_x", "email": f"{user_a}@{email_domain}", "password": password},
    )
    expect_status((status, body), 409, "duplicate email rejected")

    status, body = api(
        "POST", "/auth/register",
        payload={"username": "ab", "email": "bad", "password": "short"},
    )
    check(status == 422, "invalid registration payload rejected", f"got {status}: {body}")

    status, body = api(
        "POST", "/auth/register",
        payload={"username": "", "email": "", "password": ""},
    )
    check(status == 422, "empty registration fields rejected", f"got {status}: {body}")

    print("\n[2] Login & profile")
    token_a = login(user_a, password)
    status, me = api("GET", "/auth/me", token=token_a)
    check(status == 200 and me.get("coins") == 0, "new account starts with 0 coins", me)

    status, body = api("POST", "/auth/login", payload={"username": "", "password": ""})
    check(status == 422, "empty login fields rejected", f"got {status}: {body}")

    status, body = api(
        "POST", "/auth/login",
        payload={"username": user_a, "password": "WrongPass123!"},
    )
    check(status == 401, "login with wrong password rejected", f"got {status}: {body}")

    status, body = api(
        "POST", "/auth/login",
        payload={"username": "no_such_user_xyz", "password": "Password123!"},
    )
    check(status == 401, "login with nonexistent account rejected", f"got {status}: {body}")

    status, body = api("GET", "/auth/me")
    check(status in (401, 403), "protected endpoint rejects missing token", f"got {status}")
    status, body = api("GET", "/auth/me", token="not-a-real-token")
    check(status == 401, "protected endpoint rejects invalid token", f"got {status}")

    expired_token = jwt.encode(
        {
            "sub": str(user_a_id),
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    status, body = api("GET", "/auth/me", token=expired_token)
    check(status == 401, "expired token rejected", f"got {status}: {body}")

    print("\n[3] Pet adoption & same-day baseline")
    status, body = api("GET", "/pets/me", token=token_a)
    expect_status((status, body), 404, "no pet before adoption")

    status, pet = api("POST", "/pets/create", token=token_a, payload={"pet_name": "TestPal"})
    expect_status((status, pet), 200, "create pet")
    check(
        (pet["hunger"], pet["happiness"], pet["energy"], pet["health"]) == (75, 80, 60, 95),
        "new pet starts below maximum vitals",
        pet,
    )
    check(
        pet["level"] == 1 and pet["exp"] == 0 and pet["exp_to_next_level"] == 100,
        "new pet progression values",
        pet,
    )
    check(pet["last_decay_date"] == today.isoformat(), "new pet is baselined for today", pet)

    status, body = api("POST", "/pets/create", token=token_a, payload={"pet_name": "Second"})
    expect_status((status, body), 409, "second pet rejected")

    status, pet = api("GET", "/pets/me", token=token_a)
    check(
        (pet["happiness"], pet["health"]) == (80, 95),
        "first pet request on adoption day does not decay",
        pet,
    )

    print("\n[4] Store catalog & affordability")
    status, body = api("GET", "/store/items", token=token_a)
    expect_status((status, body), 200, "fetch store catalog")
    check(body.get("coins") == 0, "store reports wallet balance", body)
    check(len(body.get("items", [])) == 6, "catalog exposes the 6 canonical items", body)
    catalog = body["items"]

    expected_catalog = {
        "Crispy Biscuit": (30, 15, None, None),
        "Gourmet Salmon": (55, 40, None, None),
        "Squeaky Ball": (30, 25, None, None),
        "Herbal Tonic": (30, 35, None, None),
        "Energy Elixir": (30, 50, None, None),
        "Cozy Pillow": (20, 40, "health", 10),
    }
    for name, (value, price, secondary_type, secondary_value) in expected_catalog.items():
        item = find_item(catalog, name)
        check(
            (
                item["effect_value"], item["price"],
                item["secondary_effect_type"], item["secondary_effect_value"],
            ) == (value, price, secondary_type, secondary_value),
            f"catalog definition for {name}",
            item,
        )

    biscuit = find_item(catalog, "Crispy Biscuit")
    toy = find_item(catalog, "Squeaky Ball")
    tonic = find_item(catalog, "Herbal Tonic")
    elixir = find_item(catalog, "Energy Elixir")
    pillow = find_item(catalog, "Cozy Pillow")
    salmon = find_item(catalog, "Gourmet Salmon")

    status, body = api("POST", f"/store/buy/{biscuit['id']}", token=token_a)
    expect_status((status, body), 400, "purchase blocked without enough coins")
    status, wallet = api("GET", "/auth/me", token=token_a)
    check(wallet["coins"] == 0, "failed purchase did not deduct coins", wallet)
    status, inventory = api("GET", "/inventory/", token=token_a)
    check(inventory.get("items") == [], "failed purchase did not add items", inventory)

    status, body = api("POST", "/store/buy/999999", token=token_a)
    expect_status((status, body), 404, "unknown item rejected")

    print("\n[5] Habits, daily dedupe and rewards")
    status, habits = api("GET", "/habits/", token=token_a)
    check(status == 200 and habits == [], "habit list starts empty", habits)

    status, body = api("POST", "/habits/create", token=token_a, payload={"title": "   "})
    expect_status((status, body), 400, "blank habit title rejected")

    habit_ids = create_habits(token_a, 24, "E2E")
    status, habits = api("GET", "/habits/", token=token_a)
    check(len(habits) == 24, "all created habits are listed", len(habits))
    for habit in habits:
        check(
            habit["reward_coins"] == 10 and habit["reward_exp"] == 20
            and habit["completed_today"] is False,
            f"habit {habit['id']} reward metadata",
            habit,
        )

    status, first = complete(token_a, habit_ids[0])
    expect_status((status, first), 200, "complete a habit")
    check(
        first["coins_earned"] == 10 and first["total_coins"] == 10
        and first["exp_earned"] == 20 and first["pet_exp"] == 20
        and first["pet_level"] == 1,
        "first habit rewards",
        first,
    )
    check(
        first["pet"]["happiness"] == 80 and first["pet"]["health"] == 95,
        "habit response contains an un-decayed pet snapshot",
        first.get("pet"),
    )

    status, duplicate = complete(token_a, habit_ids[0])
    expect_status((status, duplicate), 409, "duplicate completion rejected")
    status, wallet = api("GET", "/auth/me", token=token_a)
    check(wallet["coins"] == 10, "duplicate completion granted no coins", wallet)

    level_ups = []
    total_coins = first["total_coins"]
    for habit_id in habit_ids[1:]:
        status, body = complete(token_a, habit_id)
        if status != 200:
            raise AssertionError(f"habit completion failed: {status} {body}")
        total_coins += body["coins_earned"]
        if body["leveled_up"]:
            level_ups.append(body["pet_level"])

    check(total_coins == 240, "24 habit rewards add up to 240 coins", total_coins)
    check(level_ups == [2, 3, 4, 5], "level ups triggered every 100 EXP", level_ups)

    status, pet = api("GET", "/pets/me", token=token_a)
    check(pet["level"] == 5 and pet["exp"] == 80, "EXP overflow carried into level 5", pet)

    status, habits = api("GET", "/habits/", token=token_a)
    check(all(habit["completed_today"] for habit in habits), "completed flags persisted", len(habits))

    print("\n[6] Care actions & limits")
    status, played = api("POST", "/care/play", token=token_a)
    expect_status((status, played), 200, "play with pet")
    check(
        (played["hunger"], played["energy"], played["happiness"]) == (65, 50, 95),
        "play costs 10 Hunger and 10 Energy, gives 15 Happiness",
        played,
    )

    status, played = api("POST", "/care/play", token=token_a)
    check(
        (played["hunger"], played["energy"], played["happiness"]) == (55, 40, 100),
        "happiness clamps at 100 on a second play",
        played,
    )

    for expected in (70, 85, 100):
        status, fed = api("POST", "/care/feed", token=token_a)
        expect_status((status, fed), 200, f"feed at hunger {expected - 15}")
        check(fed["hunger"] == expected, f"feed adds 15 Hunger (now {expected})", fed)

    status, body = api("POST", "/care/feed", token=token_a)
    expect_status((status, body), 400, "feeding a full pet rejected")

    status, rested = api("POST", "/care/rest", token=token_a)
    expect_status((status, rested), 200, "rest with room to recover")
    check(rested["energy"] == 70, "rest adds 30 Energy", rested)
    check(rested["health"] == 100, "rest adds 5 Health (clamped at 100)", rested)

    status, rested = api("POST", "/care/rest", token=token_a)
    check(rested["energy"] == 100, "second rest fills energy", rested)

    status, body = api("POST", "/care/rest", token=token_a)
    expect_status((status, body), 400, "rest rejected when fully rested and healthy")

    db_set_pet(user_a, energy=100, health=90)
    status, rested = api("POST", "/care/rest", token=token_a)
    expect_status((status, rested), 200, "rest allowed when only Health can improve")
    check(
        rested["energy"] == 100 and rested["health"] == 95,
        "health-only rest applies the +5 Health benefit",
        rested,
    )

    db_set_pet(user_a, hunger=5, energy=50, happiness=80)
    status, body = api("POST", "/care/play", token=token_a)
    expect_status((status, body), 400, "play rejected without enough Hunger")
    check("hungry" in str(body.get("detail", "")).lower(), "clear hunger message", body)

    db_set_pet(user_a, hunger=50, energy=5)
    status, body = api("POST", "/care/play", token=token_a)
    expect_status((status, body), 400, "play rejected without enough Energy")
    check("tired" in str(body.get("detail", "")).lower(), "clear energy message", body)

    status, pet = api("GET", "/pets/me", token=token_a)
    check(
        all(0 <= pet[field] <= 100 for field in ("hunger", "happiness", "energy", "health")),
        "all vitals stay within 0..100 after care",
        pet,
    )

    print("\n[7] Daily decay")
    status, pet = api("GET", "/pets/me", token=token_a)
    check(pet["happiness"] == 80 and pet["health"] == 95, "same-day fetch does not decay", pet)

    db_set_pet(user_a, last_decay_date=yesterday)
    status, decayed = api("GET", "/pets/me", token=token_a)
    expect_status((status, decayed), 200, "pet fetch on a new day")
    check(
        decayed["happiness"] == 70 and decayed["health"] == 90,
        "new-day decay subtracts 10 Happiness and 5 Health",
        decayed,
    )
    check(decayed["last_decay_date"] == today.isoformat(), "decay date is recorded", decayed)

    status, again = api("GET", "/pets/me", token=token_a)
    check(
        again["happiness"] == 70 and again["health"] == 90,
        "second same-day fetch does not decay again",
        again,
    )

    print("\n[8] Item purchasing, effects & multi-stat rules")
    db_set_pet(user_a, hunger=50, happiness=60, energy=50, health=60)

    for item in (biscuit, biscuit, biscuit, toy, tonic, elixir, pillow, pillow):
        status, body = api("POST", f"/store/buy/{item['id']}", token=token_a)
        expect_status((status, body), 200, f"buy {item['name']}")

    status, wallet = api("GET", "/auth/me", token=token_a)
    check(wallet["coins"] == 5, "8 purchases deducted the correct amount (5 coins left)", wallet)

    status, inventory = api("GET", "/inventory/", token=token_a)
    quantities = {entry["item_id"]: entry["quantity"] for entry in inventory["items"]}
    check(
        quantities[biscuit["id"]] == 3 and quantities[toy["id"]] == 1
        and quantities[tonic["id"]] == 1 and quantities[elixir["id"]] == 1
        and quantities[pillow["id"]] == 2,
        "purchased items appear in the Backpack with correct quantities",
        quantities,
    )

    status, used = api("POST", f"/inventory/{biscuit['id']}/use", token=token_a)
    expect_status((status, used), 200, "use a biscuit")
    check(
        effects_of(used) == {"hunger": 30} and used["pet"]["hunger"] == 80
        and used["quantity"] == 2,
        "biscuit adds 30 Hunger and consumes one unit",
        used,
    )

    status, used = api("POST", f"/inventory/{biscuit['id']}/use", token=token_a)
    check(
        effects_of(used) == {"hunger": 20} and used["pet"]["hunger"] == 100
        and used["quantity"] == 1,
        "biscuit clamps at 100 and reports the applied amount",
        used,
    )

    status, body = api("POST", f"/inventory/{biscuit['id']}/use", token=token_a)
    expect_status((status, body), 400, "item usage blocked when the stat is full")
    check("Hunger" in str(body.get("detail", "")), "clear full-stat message", body)
    status, inventory = api("GET", "/inventory/", token=token_a)
    check(
        {entry["item_id"]: entry["quantity"] for entry in inventory["items"]}[biscuit["id"]] == 1,
        "blocked usage consumed nothing",
        inventory,
    )

    status, used = api("POST", f"/inventory/{toy['id']}/use", token=token_a)
    check(
        effects_of(used) == {"happiness": 30} and used["pet"]["happiness"] == 90
        and used["quantity"] == 0,
        "toy adds 30 Happiness and is removed when empty",
        used,
    )

    status, used = api("POST", f"/inventory/{tonic['id']}/use", token=token_a)
    check(
        effects_of(used) == {"health": 30} and used["pet"]["health"] == 90,
        "tonic adds 30 Health",
        used,
    )

    status, used = api("POST", f"/inventory/{elixir['id']}/use", token=token_a)
    check(
        effects_of(used) == {"energy": 30} and used["pet"]["energy"] == 80,
        "elixir adds 30 Energy",
        used,
    )

    # Ngày thứ hai: decay chạy trước, sau đó gối cải thiện cả hai chỉ số của nó.
    db_set_pet(user_a, last_decay_date=yesterday)
    status, pet = api("GET", "/pets/me", token=token_a)
    check(
        pet["happiness"] == 80 and pet["health"] == 85,
        "decay applies before item usage",
        pet,
    )

    status, used = api("POST", f"/inventory/{pillow['id']}/use", token=token_a)
    expect_status((status, used), 200, "use Cozy Pillow when both stats can improve")
    check(
        effects_of(used) == {"energy": 20, "health": 10}
        and used["pet"]["energy"] == 100 and used["pet"]["health"] == 95
        and used["quantity"] == 1,
        "Cozy Pillow applies both effects and consumes one unit",
        used,
    )

    db_set_pet(user_a, energy=100, health=100)
    status, body = api("POST", f"/inventory/{pillow['id']}/use", token=token_a)
    expect_status((status, body), 400, "multi-effect item blocked when every stat is full")
    check(
        "Energy" in str(body.get("detail", "")) and "Health" in str(body.get("detail", "")),
        "full multi-stat message names both stats",
        body,
    )
    status, inventory = api("GET", "/inventory/", token=token_a)
    check(
        {entry["item_id"]: entry["quantity"] for entry in inventory["items"]}[pillow["id"]] == 1,
        "blocked multi-effect usage consumed nothing",
        inventory,
    )

    status, body = api("POST", f"/inventory/{salmon['id']}/use", token=token_a)
    expect_status((status, body), 404, "usage of an unowned item rejected")

    status, body = api("POST", f"/store/buy/{biscuit['id']}", token=token_a)
    expect_status((status, body), 400, "purchase blocked at 5 coins")

    print("\n[9] Persistence after logout/login")
    token_a2 = login(user_a, password)
    status, me = api("GET", "/auth/me", token=token_a2)
    check(me["coins"] == 5, "coins persisted after re-login", me)

    status, pet = api("GET", "/pets/me", token=token_a2)
    check(
        (pet["level"], pet["exp"], pet["hunger"], pet["happiness"],
         pet["energy"], pet["health"]) == (5, 80, 100, 80, 100, 100),
        "pet progression, vitals and decay state persisted",
        pet,
    )
    check(pet["last_decay_date"] == today.isoformat(), "decay date persisted", pet)

    status, habits = api("GET", "/habits/", token=token_a2)
    check(len(habits) == 24 and all(h["completed_today"] for h in habits), "habits persisted", len(habits))

    status, inventory = api("GET", "/inventory/", token=token_a2)
    final_quantities = {entry["item_id"]: entry["quantity"] for entry in inventory["items"]}
    check(
        final_quantities == {biscuit["id"]: 1, pillow["id"]: 1},
        "backpack persisted (one biscuit and one pillow left)",
        inventory,
    )

    status, again = api("GET", "/pets/me", token=token_a2)
    check(
        again["happiness"] == 80 and again["health"] == 100,
        "re-login on the same day does not decay again",
        again,
    )

    print("\n[10] Cross-user isolation")
    status, body = api(
        "POST", "/auth/register",
        payload={"username": user_b, "email": f"{user_b}@{email_domain}", "password": password},
    )
    expect_status((status, body), 201, "register second user")
    token_b = login(user_b, password)

    status, body = api("GET", "/pets/me", token=token_b)
    expect_status((status, body), 404, "second user has no pet")
    status, body = api("GET", "/habits/", token=token_b)
    check(body == [], "second user sees no habits from first user", body)
    status, body = api("GET", "/inventory/", token=token_b)
    check(body["items"] == [] and body["coins"] == 0, "second user has an empty wallet/backpack", body)
    status, body = api("POST", f"/inventory/{pillow['id']}/use", token=token_b)
    expect_status((status, body), 404, "second user cannot use first user's items")
    status, body = api("POST", f"/habits/{habit_ids[0]}/complete", token=token_b)
    expect_status((status, body), 404, "second user cannot complete first user's habit")
    status, body = api("POST", f"/store/buy/{biscuit['id']}", token=token_b)
    expect_status((status, body), 400, "second user cannot buy without coins")
    status, body = api("GET", "/store/items", token=token_b)
    check(len(body["items"]) == 6, "second user sees the same 6-item catalog", body)

    print("\n[10.1] Delete habit")
    status, body = api("POST", "/pets/create", token=token_b, payload={"pet_name": "DeletePal"})
    expect_status((status, body), 200, "create delete-test pet")

    delete_habit_ids = create_habits(token_b, 3, "DEL")
    status, completed = complete(token_b, delete_habit_ids[0])
    expect_status((status, completed), 200, "complete a habit before deleting it")
    check(
        completed["total_coins"] == 10 and completed["pet_exp"] == 20,
        "delete-test rewards were granted",
        completed,
    )

    status, body = delete(token_b, 999999)
    expect_status((status, body), 404, "deleting a nonexistent habit rejected")

    status, body = delete(token_b, habit_ids[1])
    expect_status((status, body), 404, "deleting another user's habit rejected")
    status, habits_a = api("GET", "/habits/", token=token_a)
    check(any(h["id"] == habit_ids[1] for h in habits_a), "other user's habit still exists", len(habits_a))
    check(len(habits_a) == 24, "first user's habit list is unchanged", len(habits_a))

    status, deleted = delete(token_b, delete_habit_ids[0])
    expect_status((status, deleted), 200, "delete own completed habit")
    check(
        deleted["habit_id"] == delete_habit_ids[0]
        and deleted["habit_title"] == "DEL task 1",
        "delete response identifies the habit",
        deleted,
    )

    status, habits_b = api("GET", "/habits/", token=token_b)
    check(all(h["id"] != delete_habit_ids[0] for h in habits_b), "deleted habit no longer appears", habits_b)
    check(len(habits_b) == 2, "unrelated habits remain after deletion", len(habits_b))

    db = SessionLocal()
    try:
        check(
            db.query(Habit).filter(Habit.id == delete_habit_ids[0]).count() == 0,
            "habit row removed from database",
        )
        check(
            db.query(HabitCompletion).filter(HabitCompletion.habit_id == delete_habit_ids[0]).count() == 0,
            "completion rows removed with the habit (no orphans)",
        )
    finally:
        db.close()

    status, me_b = api("GET", "/auth/me", token=token_b)
    check(me_b["coins"] == 10, "deleting a habit does not refund Coins", me_b)
    status, pet_b = api("GET", "/pets/me", token=token_b)
    check(
        pet_b["exp"] == 20 and pet_b["level"] == 1,
        "deleting a habit does not remove earned EXP/level",
        pet_b,
    )

    status, body = delete(token_b, delete_habit_ids[1])
    expect_status((status, body), 200, "delete another own habit without completions")
    status, habits_b = api("GET", "/habits/", token=token_b)
    check(
        len(habits_b) == 1 and habits_b[0]["id"] == delete_habit_ids[2],
        "only the selected habits were deleted",
        habits_b,
    )

    status, body = delete(token_b, delete_habit_ids[1])
    expect_status((status, body), 404, "deleting an already deleted habit rejected")

    status, body = api("DELETE", f"/habits/{delete_habit_ids[2]}")
    check(status in (401, 403), "delete requires authentication", f"got {status}")
    status, body = api("DELETE", f"/habits/{delete_habit_ids[2]}", token="not-a-real-token")
    check(status == 401, "delete rejects an invalid token", f"got {status}")

    print("\n[11] Concurrent purchases, usage and decay")
    status, body = api(
        "POST", "/auth/register",
        payload={"username": user_c, "email": f"{user_c}@{email_domain}", "password": password},
    )
    expect_status((status, body), 201, "register concurrency user")
    token_c = login(user_c, password)
    status, body = api("POST", "/pets/create", token=token_c, payload={"pet_name": "RacePal"})
    expect_status((status, body), 200, "create concurrency pet")

    db = SessionLocal()
    try:
        user_c_row = db.query(User).filter(User.username == user_c).one()
        user_c_row.coins = biscuit["price"]
        db.commit()
        user_c_id = user_c_row.id
    finally:
        db.close()

    def buy_once(_):
        return api("POST", f"/store/buy/{biscuit['id']}", token=token_c)[0]

    with ThreadPoolExecutor(max_workers=2) as pool:
        purchase_statuses = list(pool.map(buy_once, range(2)))

    check(
        sorted(purchase_statuses) == [200, 400],
        "only one of two concurrent purchases succeeds",
        purchase_statuses,
    )

    db = SessionLocal()
    try:
        user_row = db.get(User, user_c_id)
        check(user_row.coins == 0, "concurrent purchase deducted coins once", user_row.coins)
        concurrency_inventory = (
            db.query(Inventory)
            .filter(Inventory.user_id == user_c_id, Inventory.item_id == biscuit["id"])
            .one()
        )
        check(concurrency_inventory.quantity == 1, "concurrent purchase added one item", concurrency_inventory.quantity)
        purchase_tx_count = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_c_id, Transaction.transaction_type == "purchase")
            .count()
        )
        check(purchase_tx_count == 1, "concurrent purchase wrote one transaction", purchase_tx_count)
    finally:
        db.close()

    def use_once(_):
        return api("POST", f"/inventory/{biscuit['id']}/use", token=token_c)[0]

    with ThreadPoolExecutor(max_workers=2) as pool:
        usage_statuses = list(pool.map(use_once, range(2)))

    check(
        sorted(usage_statuses) == [200, 404],
        "only one of two concurrent usages succeeds",
        usage_statuses,
    )

    db = SessionLocal()
    try:
        user_row = db.get(User, user_c_id)
        check(user_row.pet.hunger == 100, "concurrent usage applied the effect once", user_row.pet.hunger)
        remaining = (
            db.query(Inventory)
            .filter(Inventory.user_id == user_c_id, Inventory.item_id == biscuit["id"])
            .count()
        )
        check(remaining == 0, "concurrent usage removed the stack once", remaining)
    finally:
        db.close()

    db_set_pet(user_c, happiness=50, health=50, last_decay_date=yesterday)

    def get_pet_once(_):
        return api("GET", "/pets/me", token=token_c)

    with ThreadPoolExecutor(max_workers=2) as pool:
        decay_responses = list(pool.map(get_pet_once, range(2)))

    check(
        all(status == 200 for status, _ in decay_responses),
        "both concurrent pet fetches succeed",
        [status for status, _ in decay_responses],
    )
    check(
        all(body["happiness"] == 40 and body["health"] == 45 for _, body in decay_responses),
        "concurrent fetches all observe exactly one decay",
        [body for _, body in decay_responses],
    )

    concurrency_pet = db_get_pet(user_c)
    check(
        concurrency_pet["happiness"] == 40 and concurrency_pet["health"] == 45,
        "concurrent decay was persisted exactly once",
        concurrency_pet,
    )
    check(
        concurrency_pet["last_decay_date"] == today,
        "concurrent decay recorded today's date",
        concurrency_pet,
    )

    db_set_pet(user_c, happiness=4, health=2, last_decay_date=yesterday)
    status, bounded = api("GET", "/pets/me", token=token_c)
    check(
        bounded["happiness"] == 0 and bounded["health"] == 0,
        "daily decay never pushes vitals below zero",
        bounded,
    )
    status, bounded_again = api("GET", "/pets/me", token=token_c)
    check(
        bounded_again["happiness"] == 0 and bounded_again["health"] == 0,
        "zeroed vitals stay stable for the rest of the day",
        bounded_again,
    )

    print("\n[11.1] Daily habit reset")
    status, body = api(
        "POST", "/habits/create",
        token=token_c,
        payload={"title": "Reset Habit"},
    )
    expect_status((status, body), 200, "create daily-reset habit")
    reset_habit_id = body["id"]

    status, body = complete(token_c, reset_habit_id)
    expect_status((status, body), 200, "complete habit on day 1")
    check(
        body["total_coins"] == 10 and body["pet_exp"] == 20,
        "day-1 habit rewards",
        body,
    )

    db = SessionLocal()
    try:
        updated = (
            db.query(HabitCompletion)
            .filter(HabitCompletion.habit_id == reset_habit_id)
            .update({HabitCompletion.completed_date: yesterday})
        )
        db.commit()
        check(updated == 1, "moved completion to yesterday for reset test", updated)
    finally:
        db.close()

    status, habits_c = api("GET", "/habits/", token=token_c)
    check(
        any(h["id"] == reset_habit_id and h["completed_today"] is False for h in habits_c),
        "habit becomes incomplete after the daily reset",
        habits_c,
    )

    status, body = complete(token_c, reset_habit_id)
    expect_status((status, body), 200, "complete habit again on the new day")
    check(
        body["total_coins"] == 20 and body["pet_exp"] == 40,
        "rewards are granted again after the daily reset",
        body,
    )

    print("\n[12] Database consistency")
    db = SessionLocal()
    try:
        user_a_row = db.get(User, user_a_id)
        check(user_a_row.coins == 5, "database coins match API", user_a_row.coins)
        check(
            user_a_row.pet.level == 5 and user_a_row.pet.exp == 80,
            "database pet level/EXP match API",
            (user_a_row.pet.level, user_a_row.pet.exp),
        )

        completions = (
            db.query(HabitCompletion)
            .join(Habit, HabitCompletion.habit_id == Habit.id)
            .filter(Habit.user_id == user_a_id)
            .all()
        )
        check(len(completions) == 24, "one completion row per habit", len(completions))
        check(
            all(c.coins_earned == 10 and c.exp_earned == 20 for c in completions),
            "completion rewards stored correctly",
            [(c.coins_earned, c.exp_earned) for c in completions],
        )

        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_a_id, Transaction.transaction_type == "purchase")
            .all()
        )
        check(len(transactions) == 8, "one transaction row per successful purchase", len(transactions))
        check(
            sum(t.amount for t in transactions) == 235,
            "transaction amounts match prices",
            [t.amount for t in transactions],
        )

        inventory_rows = (
            db.query(Inventory)
            .filter(Inventory.user_id == user_a_id)
            .all()
        )
        inventory_map = {row.item_id: row.quantity for row in inventory_rows}
        check(
            inventory_map == {biscuit["id"]: 1, pillow["id"]: 1},
            "database inventory matches the API (no empty rows)",
            inventory_map,
        )

        catalog_rows = db.query(Item).order_by(Item.id).all()
        check(len(catalog_rows) == 6, "catalog seeding is idempotent (6 items)", len(catalog_rows))
        pillow_row = next(item for item in catalog_rows if item.name == "Cozy Pillow")
        check(
            pillow_row.effect_type == "energy" and pillow_row.effect_value == 20
            and pillow_row.secondary_effect_type == "health"
            and pillow_row.secondary_effect_value == 10,
            "Cozy Pillow multi-effect definition stored correctly",
            (pillow_row.effect_type, pillow_row.effect_value,
             pillow_row.secondary_effect_type, pillow_row.secondary_effect_value),
        )
    finally:
        db.close()

    return {
        "duration": round(time.time() - started, 2),
        "checks": CHECKED,
        "users": [user_a, user_b, user_c],
    }


def main():
    before = db_snapshot()
    result = None
    failure = None

    try:
        result = run()
    except Exception as error:  # noqa: BLE001 - reported after cleanup
        failure = error

    removed = cleanup_test_users()
    after = db_snapshot()

    print("\n[13] Existing data safety")
    safety_keys = (
        "users", "pets", "habits", "completions",
        "inventory", "transactions", "tung_coins", "tung_pet",
    )
    mismatches = {key: (before[key], after[key]) for key in safety_keys if before[key] != after[key]}
    print(f"  INFO  test accounts removed: {removed or 'none'}")

    if mismatches:
        print(f"  FAIL  existing data changed: {mismatches}")
        failure = failure or AssertionError(f"Existing user data changed: {mismatches}")
    else:
        print("  PASS  existing data unchanged after test run")

    if failure:
        raise failure

    print("\n" + "=" * 62)
    print(f"ALL {result['checks']} CHECKS PASSED in {result['duration']}s")
    print(f"Temporary accounts cleaned up: {', '.join(result['users'])}")
    print("=" * 62)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - test harness reports and exits non-zero
        print("\n" + "=" * 62)
        print(f"INTEGRATION TEST FAILED after {CHECKED} checks")
        print(f"{type(error).__name__}: {error}")
        print("=" * 62)
        sys.exit(1)
