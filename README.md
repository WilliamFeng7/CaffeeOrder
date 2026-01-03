# ☕ CoffeeOrder System

A comprehensive Coffee Ordering System designed for campus environments, featuring separate interfaces for Students, Baristas, and Administrators.

## 🌟 Features

- **Student Interface**: Browse menu, place orders, and track order history.
- **Barista Interface (KDS)**: Real-time order management, status updates (Pending -> Making -> Ready).
- **Admin Dashboard**: Product management, user management, financial analysis, and system settings.
- **Security**: Role-based authentication (Admin, Barista, User).

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: SQLite with [SQLModel](https://sqlmodel.tiangolo.com/)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Authentication**: JWT (JSON Web Tokens) with `python-jose`

### Frontend
- **Framework**: [Vue.js 3](https://vuejs.org/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Apps**: Multi-app structure (Student, Admin, Barista)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or pnpm

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database (if needed):
   ```bash
   alembic upgrade head
   ```

5. Run the server:
   ```bash
   python main.py
   # OR
   uvicorn main.app:app --reload
   ```
   The API will be available at `http://localhost:8000`. API Docs at `http://localhost:8000/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development servers:
   ```bash
   npm run dev
   ```
   - **Student App**: `http://localhost:5173` (default)
   - **Admin App**: Check console for specific port
   - **Barista App**: Check console for specific port

## 📚 Documentation

- [API Documentation](docs/API.md)
