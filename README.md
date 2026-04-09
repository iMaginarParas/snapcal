# FitSnap AI

A production-ready full-stack mobile health application with AI food detection and step tracking.

## Features

- **AI Food Detection**: Take a photo of your food and get instant nutritional info (Calories, Macros).
- **Step Tracking**: Real-time step counting using device motion sensors.
- **Health Dashboard**: Visualize your daily health statistics.
- **Production Architecture**: Modular FastAPI backend with PostgreSQL, Redis, and PyTorch.

## Tech Stack

- **Frontend**: Flutter
- **Backend**: FastAPI (Python)
- **AI**: PyTorch
- **Infrastructure**: Docker, PostgreSQL, Redis

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Flutter SDK (for mobile development)

### Running the Backend
1. Open a terminal in the project root.
2. Run:
   ```bash
   docker-compose up --build
   ```
3. The API will be available at `http://localhost:8000`.
4. Documentation (Swagger) is at `http://localhost:8000/docs`.

### Running the Mobile App
1. Navigate to the `mobile/` directory.
2. Ensure a device/emulator is connected.
3. Install dependencies:
   ```bash
   flutter pub get
   ```
4. Run the app:
   ```bash
   flutter run
   ```

## Folder Structure

- `mobile/`: Flutter source code.
- `backend/`: FastAPI source code and AI models.
- `docker-compose.yml`: Infrastructure orchestration.

## License
MIT
