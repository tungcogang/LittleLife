# LittleLife

A cozy virtual pet, daily habit tracker and mini-economy desktop game.

- **Frontend:** Pygame (`frontend/pygame_ui/`)
- **Backend:** FastAPI (`backend/`)
- **Database:** MySQL + SQLAlchemy
- **Auth:** JWT bearer tokens
- **Python:** 3.13

## Quick start

1. Create the virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root:

   ```dotenv
   DB_USER=root
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=littlelife
   SECRET_KEY=replace-with-a-long-random-string
   ```

3. Create/upgrade the tables and seed the Store catalog (idempotent):

   ```powershell
   .\.venv\Scripts\python.exe -m backend.init_db
   ```

4. Start the API:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```

5. Start the game (second terminal):

   ```powershell
   .\.venv\Scripts\python.exe frontend\pygame_ui\app.py
   ```

The login screen also offers **Create Account** and **Demo Mode** (offline play
without a backend).

## Tests

With the API running on port 8000:

```powershell
.\.venv\Scripts\python.exe -B test\e2e_integration.py   # API + database
.\.venv\Scripts\python.exe -B test\frontend_e2e.py      # headless Pygame UI
```

Both scripts create temporary `e2e_*` accounts and remove them afterwards.
See `frontend/pygame_ui/README.md` for architecture, endpoint and gameplay
details.
