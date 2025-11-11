# Data Observability App

A real-time telemetry monitoring system with a Python backend and React frontend. The system generates multiple signal types, stores them in a database, and displays them on a live-updating dashboard.

## Features

- **Telemetry Producer**: Generates 5 different signal types (sine wave, cosine wave, random noise, random walk, damped oscillation)
- **Backend API**: Flask server with SQLite database, REST endpoints, and WebSocket support for real-time updates
- **Frontend Dashboard**: React application with live plotting using Recharts
- **Unit Tests**: Comprehensive test suite for backend API

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│  Producer   │────────>│   Backend    │<────────│   Frontend   │
│  (Python)   │  HTTP   │   (Flask)    │ WebSocket│   (React)    │
└─────────────┘         └──────┬───────┘         └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │   SQLite DB  │
                        └──────────────┘
```

## Project Structure

```
.
├── producer/           # Telemetry data generator
│   ├── producer.py     # Main producer script
│   └── requirements.txt
├── backend/            # Flask API server
│   ├── app.py          # Main application
│   ├── test_app.py     # Unit tests
│   └── requirements.txt
└── frontend/           # React dashboard
    ├── src/
    │   ├── App.jsx     # Main app component
    │   ├── App.css     # Styling
    │   ├── main.jsx    # Entry point
    │   └── index.css   # Global styles
    ├── index.html
    ├── vite.config.js
    └── package.json
```

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ljpu-pax/data-observability-app.git
cd data-observability-app
```

2. **Set up the backend**
```bash
cd backend
pip install -r requirements.txt
```

3. **Set up the frontend**
```bash
cd ../frontend
npm install
```

4. **Set up the producer**
```bash
cd ../producer
pip install -r requirements.txt
```

### Running the Application

You'll need three terminal windows to run all components:

**Terminal 1 - Backend:**
```bash
cd backend
python app.py
```
The backend will start on `http://localhost:5000`

**Terminal 2 - Producer:**
```bash
cd producer
python producer.py
```
The producer will start sending data to the backend every second

**Terminal 3 - Frontend:**
```bash
cd frontend
npm start
```
The dashboard will open at `http://localhost:3000`

### Running Tests

To run the backend unit tests:
```bash
cd backend
python -m pytest test_app.py -v
```

## API Endpoints

### REST API

- `GET /health` - Health check endpoint
- `POST /api/telemetry` - Receive telemetry data from producer
- `GET /api/telemetry?hours=<n>` - Get historical telemetry data (default: 1 hour)
- `GET /api/signals` - Get list of available signals

### WebSocket Events

- `connect` - Client connection established
- `disconnect` - Client disconnected
- `telemetry_update` - Real-time telemetry data broadcast

## Signal Types

The producer generates the following signals:

1. **Sine Wave**: `A * sin(2π * f * t) + offset`
2. **Cosine Wave**: `A * cos(2π * f * t) + offset`
3. **Random Noise**: Uniform random distribution
4. **Random Walk**: Brownian motion simulation
5. **Damped Oscillation**: Exponentially decaying sine wave

## Design Decisions

### Backend
- **Flask**: Lightweight and easy to set up for a prototype
- **SQLite**: Simple, file-based database perfect for local development
- **Flask-SocketIO**: Enables real-time WebSocket communication
- **Indexed database queries**: Optimized for time-range queries

### Frontend
- **React**: Component-based architecture for maintainable UI
- **Vite**: Fast development server and build tool
- **Recharts**: Responsive charting library with good React integration
- **WebSocket client**: Receives live updates without polling

### Producer
- **Multiple signal types**: Demonstrates various telemetry patterns
- **Configurable intervals**: Easy to adjust data emission rate
- **Error handling**: Gracefully handles backend downtime

## Future Improvements

- Add data aggregation/downsampling for longer time ranges
- Implement data persistence beyond SQLite (PostgreSQL, TimescaleDB)
- Add authentication and multi-user support
- Create Docker containers for easy deployment
- Add more signal processing capabilities (FFT, filtering, etc.)
- Implement data export functionality

## License

MIT