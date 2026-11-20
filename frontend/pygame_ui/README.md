# LittleLife - Pygame Frontend & FastAPI Backend Integration

A cozy virtual pet and habit tracker UI built with Pygame and fully connected to the FastAPI backend at `http://127.0.0.1:8000`.

---

## 1. Project Overview & Architecture

The frontend is located inside `frontend/pygame_ui/` and is strictly decoupled from backend database code:

```
frontend/pygame_ui/
├── __init__.py           # Package exports
├── app.py                # Main application loop, screen manager, routing, auth & API dispatch
├── api_client.py         # HTTP client communicating with FastAPI endpoints via urllib
├── text_input.py         # Text input field component with focus, cursor & masking
├── theme.py              # Cozy warm palette, dimensions, and font helper
├── components.py         # Reusable UI widgets (Button, ProgressBar, Card, CoinDisplay, Banner)
├── mock_data.py          # Data models (PetState, HabitItem, ShopItem, InventoryItem) & fallback simulator
├── README.md             # Integration guide and documentation
└── screens/              # Modular screen views
    ├── __init__.py
    ├── login_screen.py   # Authentication screen (POST /auth/login)
    ├── pet_screen.py     # Pet vitals, adoption interface (POST /pets/create), Feed/Play/Sleep care actions
    ├── habit_screen.py   # Daily habit checklist (GET /habits/) and completion (POST /habits/{id}/complete)
    ├── shop_screen.py    # General store catalog & purchasing (local simulation)
    └── inventory_screen.py # Backpack grid, item quantities & item usage (local simulation)
```

---

## 2. Connected Backend API Endpoints

| Category | Method & Endpoint | Auth Required | Function in `api_client.py` | UI Binding |
| :--- | :--- | :---: | :--- | :--- |
| **Auth** | `POST /auth/login` | No | `login(username, password)` | `LoginScreen` "Sign In" button |
| **Auth** | `POST /auth/register` | No | `register(username, email, password)` | Helper method ready for registration |
| **Auth** | `GET /auth/me` | Yes (`Bearer`) | `get_me()` | Synchronizes user profile and `coins` counter |
| **Pet** | `POST /pets/create` | Yes (`Bearer`) | `create_pet(pet_name)` | `PetScreen` "Adopt Pet" form |
| **Pet** | `GET /pets/me` | Yes (`Bearer`) | `get_my_pet()` | `PetScreen` profile & vitals meters |
| **Habits** | `GET /habits/` | Yes (`Bearer`) | `get_habits()` | `HabitScreen` daily checklist |
| **Habits** | `POST /habits/{id}/complete`| Yes (`Bearer`)| `complete_habit(habit_id)` | `HabitScreen` "Complete" button |
| **Pet Care** | `POST /care/feed` | Yes (`Bearer`) | `care_feed()` | `PetScreen` "Feed" button (+30 Hunger) |
| **Pet Care** | `POST /care/play` | Yes (`Bearer`) | `care_play()` | `PetScreen` "Play" button (+20 Joy, -20 Energy) |
| **Pet Care** | `POST /care/rest` | Yes (`Bearer`) | `care_rest()` | `PetScreen` "Sleep" button (+30 Energy) |

*Note on Shop & Inventory*: As the backend does not currently expose `/shop` or `/inventory` routes, these two screens remain functional as a local economy simulation.

---

## 3. How to Run the Application

### Running with Backend (Live Integration)
1. In a terminal, run the FastAPI server:
   ```powershell
   .\.venv\Scripts\uvicorn.exe backend.main:app --reload --host 127.0.0.1 --port 8000
   ```
2. In another terminal, run the Pygame frontend:
   ```powershell
   .\.venv\Scripts\python.exe frontend\pygame_ui\app.py
   # Or using module invocation:
   .\.venv\Scripts\python.exe -m frontend.pygame_ui.app
   ```

### Running in Offline / Demo Mode
- Click **"Continue in Offline / Demo Mode"** on the login screen to explore the UI with local mock data without a database or backend server.

---

## 4. Key Gameplay Flows

1. **User Sign In**:
   - Submits credentials to `POST /auth/login`.
   - On success, stores JWT token in memory for the session.
   - Automatically loads user coins (`GET /auth/me`), pet status (`GET /pets/me`), and daily habits (`GET /habits/`).
2. **Pet Adoption**:
   - If the user account has no pet yet (backend returns 404), the `PetScreen` presents a cozy "Egg Incubator" adoption panel.
   - Entering a pet name and clicking "Adopt Pet" calls `POST /pets/create` and immediately populates the pet profile and vitals.
3. **Daily Habit Completion**:
   - `HabitScreen` displays active daily habits with badges showing `+10 Coin +20 EXP`.
   - Clicking "Complete" calls `POST /habits/{id}/complete`.
   - Updates backend database, grants rewards, synchronizes the top coin wallet, increments pet EXP, and triggers level-up celebration when reaching 100 EXP.
   - Disables button to `Done ✓` and prevents duplicate clicks.
4. **Pet Care Actions**:
   - Clicking **Feed** calls `POST /care/feed` (recovers +30 Hunger).
   - Clicking **Play** calls `POST /care/play` (recovers +20 Joy, costs 20 Energy). If Energy < 20, gracefully displays an error notice.
   - Clicking **Sleep** calls `POST /care/rest` (recovers +30 Energy).
