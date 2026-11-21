# LittleLife - Pygame Frontend & FastAPI Backend Integration

A cozy virtual pet and habit tracker UI built with Pygame and fully connected to
the FastAPI backend at `http://127.0.0.1:8000`. Online Mode always treats the
backend as the source of truth; Offline/Demo Mode keeps the same gameplay rules
with local in-memory data.

---

## 1. Project Overview & Architecture

```
frontend/pygame_ui/
├── __init__.py           # Package exports
├── app.py                # Main loop, screen manager, auth & API dispatch, data sync
├── api_client.py         # HTTP client for FastAPI (urllib, no extra dependencies)
├── text_input.py         # Text input with focus, cursor, masking and IME/TEXTINPUT
├── theme.py              # Cozy warm palette, dimensions, font helper
├── components.py         # Button, ProgressBar, Card, CoinDisplay, Banner, text helpers
├── mock_data.py          # Demo data models and offline simulation
├── README.md             # This guide
└── screens/
    ├── login_screen.py       # Sign in, Create Account, Demo Mode
    ├── pet_screen.py         # Vitals, adoption, Feed/Play/Sleep
    ├── habit_screen.py       # Habit list, completion, creation, scrolling, delete dialog
    ├── shop_screen.py        # Store catalog, owned counts, Buy buttons
    └── inventory_screen.py   # Backpack grid and Use buttons
```

Backend modules added for the Store/Inventory economy and pet progression:

```
backend/
├── constants.py              # Care/reward/level/decay values shared by all routes
├── migrations.py             # Idempotent column upgrades for existing databases
├── routes/store.py           # GET /store/items, POST /store/buy/{item_id}
├── routes/inventory.py       # GET /inventory/, POST /inventory/{item_id}/use
├── services/item_service.py  # Catalog seed, serializers, item effect rules
└── services/pet_service.py   # Daily decay, pet snapshots
```

---

## 2. Connected Backend API Endpoints

| Category | Method & Endpoint | Auth | `api_client.py` | UI Binding |
| :--- | :--- | :---: | :--- | :--- |
| **Auth** | `POST /auth/register` | No | `register(username, email, password)` | Login screen "Create Account" form |
| **Auth** | `POST /auth/login` | No | `login(username, password)` | Login screen "Sign In" |
| **Auth** | `GET /auth/me` | Yes | `get_me()` | Username + Coin wallet |
| **Pet** | `POST /pets/create` | Yes | `create_pet(pet_name)` | "Adopt Pet" form |
| **Pet** | `GET /pets/me` | Yes | `get_my_pet()` | Vitals, level, EXP bar |
| **Habits** | `GET /habits/` | Yes | `get_habits()` | Habit checklist + reward badges |
| **Habits** | `POST /habits/create` | Yes | `create_habit(title, note)` | "Add Habit" form |
| **Habits** | `POST /habits/{id}/complete` | Yes | `complete_habit(habit_id)` | "Complete" button (+10 Coins, +20 EXP) |
| **Habits** | `DELETE /habits/{id}` | Yes | `delete_habit(habit_id)` | Trash icon + confirmation dialog |
| **Pet Care** | `POST /care/feed` | Yes | `care_feed()` | Feed (+15 Hunger) |
| **Pet Care** | `POST /care/play` | Yes | `care_play()` | Play (+15 Happiness, -10 Energy, -10 Hunger) |
| **Pet Care** | `POST /care/rest` | Yes | `care_rest()` | Sleep (+30 Energy, +5 Health) |
| **Store** | `GET /store/items` | Yes | `get_store_items()` | Catalog + current Coins |
| **Store** | `POST /store/buy/{item_id}` | Yes | `buy_item(item_id)` | Buy button |
| **Inventory** | `GET /inventory/` | Yes | `get_inventory()` | Backpack grid |
| **Inventory** | `POST /inventory/{item_id}/use` | Yes | `use_item(item_id)` | Use button |

All protected endpoints require `Authorization: Bearer <access_token>`.

---

## 3. Store & Inventory Rules

**Catalog** (seeded automatically, ids 101-106 by default; existing ids and
prices are preserved):

| Item | Type | Price | Effect |
| :--- | :--- | ---: | :--- |
| Crispy Biscuit | Food | 15 | +30 Hunger |
| Gourmet Salmon | Food | 40 | +55 Hunger |
| Squeaky Ball | Toy | 25 | +30 Happiness |
| Herbal Tonic | Medicine | 35 | +30 Health |
| Energy Elixir | Potion | 50 | +30 Energy |
| Cozy Pillow | Comfort | 40 | +20 Energy, +10 Health |

**Purchasing**
- Coins are deducted, the inventory stack is increased and a `transactions`
  row is written in **one database transaction**; a failure changes nothing.
- Purchases are rejected when Coins are insufficient, the item is unknown or
  unavailable, and the wallet is re-locked (`SELECT ... FOR UPDATE`) so two
  concurrent purchases cannot overspend.
- The UI replaces its Coin balance and whole backpack with the backend response,
  then refreshes from the backend when the screen is reopened.
- The Store keeps showing **all** catalog items regardless of the wallet. Buy
  buttons are disabled for unaffordable items and become enabled again when the
  balance grows (this is the existing affordability behaviour, preserved).

**Using items**
- The item is consumed only after its effect is applied; an empty stack is
  deleted immediately.
- Multi-effect items are usable while **at least one** targeted stat can improve.
  If every targeted stat is already 100, usage is rejected (HTTP 400) and
  nothing is consumed, keeping the item for later.
- The response returns the applied effects (with clamped amounts), the full pet
  snapshot and the refreshed backpack, which the UI applies immediately.
- Concurrent usages are serialized with row locks; exactly one can consume a
  single-unit stack.

---

## 3.1 Pet Care & Daily Decay

| Action | Effect |
| :--- | :--- |
| Feed | Hunger +15 |
| Sleep | Energy +30, Health +5 |
| Play | Happiness +15, Hunger -10, Energy -10 |

- Every vital is clamped to `0..100`; Play is rejected when Hunger or Energy is
  below the 10-point cost. Sleep is allowed when only Health can improve.
- **Daily decay:** on the first pet-related request (login, Pet screen, care,
  habit completion or item usage) of a new calendar day, Happiness drops by 10
  and Health by 5. `pets.last_decay_date` records the processed day.
- Decay happens at most once per pet per day. Repeated screen switches, game
  restarts, logout/login and concurrent requests do not apply it twice.
- If several days pass without playing, only one decay is applied on the next
  interaction (missed days are not accumulated), keeping a returning pet usable.
- Existing databases are upgraded in place: `last_decay_date` is added with a
  baseline of yesterday, so the first pet request after the upgrade applies one
  day of decay without touching any other data.

---

## 4. Habits and Rewards

- The Habit screen has an "Add a Daily Habit" form (title + optional note). In
  Online Mode habits are saved to the account; Demo Mode adds them locally.
- Every active habit is listed with its own reward badge and today's completion
  state. Lists longer than the card scroll with the mouse wheel.
- Completing a habit grants `+10 Coins` and `+20 EXP` exactly once per day. The
  `habit_completions` table has a `(habit_id, completed_date)` unique constraint,
  and duplicate requests return HTTP 409.
- EXP levels up the pet every 100 EXP with overflow carried into the next level.
  Level-ups are reported by the API and shown in the UI notification.
- Each habit row has a small trash icon. Clicking it opens a modal confirmation
  ("Are you sure you want to delete this habit?") with **Cancel** and **Delete**.
  The dialog blocks the other habit controls until it is closed.
- Deleting a habit permanently removes it and its `habit_completions` rows via
  the existing relationship cascade. Coins and EXP already earned are **not**
  refunded. Only the habit owner can delete it; other users receive HTTP 404
  and the habit remains intact.
- Deletion works in Demo Mode locally and never touches online account data.

---

## 5. How to Run

### 5.1 Prerequisites
- Python 3.13 with the project virtual environment
- A running MySQL server with the `littlelife` database
- `.env` in the project root (see the root `README.md`)

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m backend.init_db
```

`backend.init_db` is safe to run repeatedly: it creates missing tables, adds the
optional columns introduced by upgrades (`pets.last_decay_date`,
`items.secondary_effect_*`), synchronizes catalog effects and adds missing items
without touching users, pets, habits, inventories or prices. The API performs
the same upgrade automatically at startup.

### 5.2 Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
Interactive API docs: <http://127.0.0.1:8000/docs>

### 5.3 Frontend
```powershell
.\.venv\Scripts\python.exe frontend\pygame_ui\app.py
# or
.\.venv\Scripts\python.exe -m frontend.pygame_ui.app
```

Set `LITTLELIFE_API_URL` to point the client (and the login hint) at another
backend instance, for example an isolated test server:

```powershell
$env:LITTLELIFE_API_URL = "http://127.0.0.1:8001"
```

The default remains `http://127.0.0.1:8000`.

### 5.4 Offline / Demo Mode
Click **Demo Mode** on the login screen. No backend or database is required;
state is in memory and resets on logout. The demo follows the same care values,
item effects and reward rules as Online Mode.

---

## 6. Key Gameplay Flows

1. **Register / Sign In** - "Create Account" calls `POST /auth/register` then
   signs in automatically. Login loads profile, Coins, pet, habits, catalog and
   backpack before showing the Pet screen.
2. **Pet Adoption** - If `GET /pets/me` returns 404 the Egg Incubator panel is
   shown. A new pet starts at Hunger 75, Happiness 80, Energy 60, Health 95,
   level 1 with 0 EXP, so every Store item has something to restore.
3. **Daily Habits** - Create habits, complete each once per day, watch Coins and
   EXP update, and see the pet level-up notification at each 100 EXP.
4. **Pet Care** - Feed/Play/Sleep call the care endpoints. Feed gives +15 Hunger,
   Sleep gives +30 Energy and +5 Health, Play gives +15 Happiness and costs 10
   Hunger + 10 Energy. Full-stat or insufficient-resource actions are rejected
   with a clear message, matching Demo Mode.
5. **Daily Decay** - On the first pet interaction of a new day, Happiness -10 and
   Health -5 are applied once and recorded in `last_decay_date`.
6. **Store & Backpack** - Buy items (the Store shows owned quantities), then use
   them from the Backpack. Multi-effect items such as the Cozy Pillow apply every
   stat that can still improve. Stats, Coins and quantities update immediately
   and persist across logout/login.

### Text input / Vietnamese IME

- Register, Habit and Pet Adoption fields all use the shared `TextInput`
  component in `text_input.py`.
- Committed text is received through Pygame `TEXTINPUT` events (the path used by
  VNI, Telex and other IMEs); the composition preview uses `TEXTEDITING`.
  `KEYDOWN` is only used for Enter, Backspace, Delete and Escape, so characters
  are not lost or inserted twice.
- The app calls `pygame.key.start_text_input()` and keeps
  `pygame.key.set_text_input_rect()` on the focused field so the IME candidate
  window follows it.
- Enter is ignored while the IME is composing; Backspace does not delete committed
  text while a composition is active.

---

## 7. Tests

With the API running on port 8000:

```powershell
.\.venv\Scripts\python.exe -B test\e2e_integration.py
.\.venv\Scripts\python.exe -B test\frontend_e2e.py
```

- `test/e2e_integration.py` drives the real HTTP API and database: registration,
  login, pet creation, care values and limits, daily decay (including concurrent
  requests and zero-clamping), habit rewards and daily dedupe, habit deletion
  (ownership, completion cascade, no Coin/EXP refund, auth), level-up/EXP
  overflow, purchases, single- and multi-effect items, persistence, cross-user
  isolation and concurrent purchase/usage locking. It cleans up its `e2e_*`
  accounts and verifies pre-existing rows were not modified.
- `test/frontend_e2e.py` runs the real Pygame app with the SDL dummy driver,
  drives the same callbacks the buttons use against the live backend, covers
  Demo Mode, habit deletion with Cancel/Confirm and a simulated backend failure,
  shared `TextInput` Vietnamese/IME cases (`TEXTINPUT`, `TEXTEDITING`, Backspace,
  focus switching, max length, duplicate prevention), and writes screenshots to
  `%TEMP%\littlelife_screenshots` (override with `LITTLELIFE_SCREENSHOT_DIR`).

---

## 8. Known Limitations

- Daily decay is applied once on the first pet interaction of a new day. If
  several days are missed, the decay is **not** multiplied per missed day. Demo
  Mode has no persistent dates and therefore no daily decay.
- The Store shows every catalog item and disables unaffordable Buy buttons; it
  does not filter items by the current Coin balance. This preserves the existing
  economy UI.
- Item purchases are atomic and guarded against concurrent requests, but a
  network-level retry of an already-processed purchase has no idempotency key
  (no schema change was made to the existing `transactions` table). The client
  blocks double clicks from a single input burst.
- JWT access tokens expire after 30 minutes; there is no refresh token, so an
  expired session returns to the login screen.
- Text fields are append-only: there is no cursor movement or selection, so
  arrow-key editing in the middle of a value is not supported. Backspace/Delete
  and focus switching work at the end of the text.
- Automated UI tests inject Pygame `TEXTINPUT`/`TEXTEDITING` events (the same
  contract SDL uses). The OS-level VNI/Unikey composition should still be
  verified manually on the target Windows machine.
- Some emoji characters in pre-existing labels may render as empty boxes when
  the selected system font has no emoji glyph.
