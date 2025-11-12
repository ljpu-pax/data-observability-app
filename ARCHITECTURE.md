# Architecture Documentation

## Overview

This data observability application follows a three-tier architecture with real-time data streaming capabilities:

```
┌──────────────┐      HTTP POST        ┌──────────────┐      WebSocket      ┌──────────────┐
│   Producer   │ ───────────────────> │   Backend    │ <────────────────── │   Frontend   │
│   (Python)   │                       │   (Flask)    │      HTTP GET       │   (React)    │
└──────────────┘                       └──────┬───────┘                     └──────────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │   SQLite DB  │
                                       └──────────────┘
```

## Components

### 1. Producer (`producer/`)

**Purpose**: Simulates telemetry data generation from multiple signal sources.

**Design Patterns**:
- **Signal Generator Class**: Encapsulates signal generation logic with pure mathematical functions
- **Time-based Generation**: Uses elapsed time for deterministic signal reproduction
- **Resilient Communication**: Implements retry logic with exponential backoff for backend connectivity

**Signal Types**:
1. **Sine Wave**: `A * sin(2π * f * t) + offset`
   - Demonstrates periodic behavior
   - Frequency: 0.1 Hz, Amplitude: 10

2. **Cosine Wave**: `A * cos(2π * f * t) + offset`
   - Phase-shifted periodic signal
   - Frequency: 0.15 Hz, Amplitude: 8

3. **Random Noise**: Uniform distribution
   - Simulates measurement noise
   - Range: ±5

4. **Random Walk**: Brownian motion
   - Cumulative random steps
   - Step size: ±0.5

5. **Damped Oscillation**: `A * e^(-decay*t) * sin(2π * f * t)`
   - Demonstrates transient behavior
   - Initial amplitude: 15, Decay: 0.01

**Data Flow**:
```
SignalGenerator → JSON Payload → HTTP POST → Backend API
     |
     ├─ sine_wave: float
     ├─ cosine_wave: float
     ├─ random_noise: float
     ├─ random_walk: float
     └─ damped_oscillation: float
```

### 2. Backend (`backend/`)

**Purpose**: Centralized API server for data ingestion, storage, and distribution.

**Technology Stack**:
- **Flask**: Lightweight WSGI framework
- **Flask-SocketIO**: WebSocket support for real-time updates
- **SQLite**: Embedded relational database
- **Threading**: Concurrent request handling with locks for database safety

**API Design**:

**REST Endpoints**:
```
POST /api/telemetry
- Accepts: { timestamp: ISO8601, signals: { [name]: value } }
- Returns: { status: "success" }
- Side effects: Broadcasts to WebSocket clients

GET /api/telemetry?hours=1
- Returns: { [signal_name]: [{ timestamp, value }] }
- Optimized with indexed queries

GET /api/signals
- Returns: [signal_name_1, signal_name_2, ...]
- Cached via DISTINCT query

GET /health
- Returns: { status: "healthy" }
```

**WebSocket Events**:
```
connect → connection_response
telemetry_update → { timestamp, signals }
disconnect → cleanup
```

**Database Schema**:
```sql
CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    signal_name TEXT NOT NULL,
    value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_timestamp ON telemetry(timestamp);
CREATE INDEX idx_signal_name ON telemetry(signal_name);
```

**Design Decisions**:
- **Normalized Schema**: One row per signal-timestamp pair for flexible querying
- **Indexed Queries**: Optimized for time-range filtering (most common query pattern)
- **Thread-Safe Operations**: Database lock prevents race conditions
- **Dual Communication**: REST for historical data, WebSocket for live updates

**Scalability Considerations**:
- Current: Single-threaded, suitable for ~1000 data points/second
- Future: Could add connection pooling, Redis cache, or TimescaleDB for time-series optimization
- Data retention: Consider TTL or partitioning for long-running deployments

### 3. Frontend (`frontend/`)

**Purpose**: Interactive dashboard for real-time telemetry visualization.

**Technology Stack**:
- **React 18**: Component-based UI framework
- **Vite**: Fast development server and bundler
- **Recharts**: Declarative charting library
- **Socket.io-client**: WebSocket client for real-time updates

**Component Architecture**:
```
App (main component)
├── State Management
│   ├── data: { [signal]: [{ timestamp, value }] }
│   ├── signals: [string]
│   └── connected: boolean
│
├── Effects
│   ├── Initial Data Fetch (useEffect)
│   └── WebSocket Connection (useEffect)
│
└── UI Components
    ├── Header (title + connection status)
    ├── Stats Cards (signals, data points, time range)
    ├── Chart Container
    │   └── LineChart (Recharts)
    │       ├── CartesianGrid
    │       ├── XAxis (time)
    │       ├── YAxis (value)
    │       ├── Tooltip
    │       ├── Legend
    │       └── Line (per signal)
    └── Signals List (current values)
```

**Data Flow**:
```
1. Mount → fetch('/api/telemetry?hours=1') → setData()
2. WebSocket → on('telemetry_update') → append to data → filter old points
3. Data transformation → recharts format → render
```

**State Management Strategy**:
- **Local State (useState)**: Simple enough to avoid Redux
- **Immutable Updates**: Spread operators for React reconciliation
- **Sliding Window**: Keep only last hour of data in memory
- **Auto-cleanup**: Remove points older than 1 hour to prevent memory growth

**Performance Optimizations**:
- **No prop drilling**: Flat component structure
- **Memoization opportunity**: Could add `useMemo` for chartData transformation if needed
- **Virtual scrolling**: Not needed at current data volumes
- **Chart re-renders**: Recharts handles efficiently with `connectNulls` and `dot={false}`

## Data Flow

### Normal Operation Flow

```
1. Producer generates signal values
   └─> POST /api/telemetry

2. Backend receives data
   ├─> Store in SQLite
   └─> Broadcast via WebSocket

3. Frontend receives update
   ├─> Update local state
   ├─> Filter old data (>1 hour)
   └─> Re-render chart
```

### Cold Start Flow

```
1. User opens frontend
   └─> GET /api/telemetry?hours=1
       └─> Load historical data

2. WebSocket connection established
   └─> on('connect')
       └─> Set connected=true

3. Incremental updates
   └─> on('telemetry_update')
       └─> Append new data points
```

## Testing Strategy

### Backend Tests (`backend/test_app.py`)

**Test Coverage**:
- HTTP endpoints (POST, GET)
- Database operations (CRUD)
- Time-based filtering
- Error handling (invalid payloads)
- Signal enumeration

**Testing Pattern**: Isolated database per test
```python
setUp() → Create temp DB → Monkey-patch DB_PATH
test_*() → Run test
tearDown() → Cleanup temp DB
```

### Frontend Tests (`frontend/src/App.test.jsx`)

**Test Coverage**:
- Component rendering
- Initial data fetch
- UI elements presence
- WebSocket mocking

**Testing Pattern**: Mock external dependencies
```javascript
Mock socket.io-client → Mock fetch → Test UI rendering
```

## Design Trade-offs

### Why SQLite?
**Pros**:
- Zero configuration
- Embedded (no separate process)
- ACID compliance
- Good enough for 10k-100k rows

**Cons**:
- Limited concurrency (single writer)
- Not suitable for distributed systems

**Alternative**: PostgreSQL with TimescaleDB for production

### Why WebSocket + REST?
**Pros**:
- REST for historical data (cacheable, simple)
- WebSocket for live updates (low latency)
- Fallback: REST polling if WebSocket fails

**Cons**:
- Two communication channels to maintain

**Alternative**: Server-Sent Events (SSE) for simpler one-way streaming

### Why Recharts?
**Pros**:
- Declarative React API
- Responsive by default
- Good documentation

**Cons**:
- Heavier than canvas-based solutions (e.g., Chart.js)
- Less control over rendering

**Alternative**: D3.js for more customization

### Why No State Management Library?
**Pros**:
- Simpler codebase
- Faster development
- Sufficient for single-component state

**Cons**:
- Would need refactoring if app grows

**Alternative**: Zustand or Redux for complex state

## Performance Characteristics

### Current Limits
- **Producer**: 1 sample/second × 5 signals = 5 data points/second
- **Backend**: ~1000 requests/second (single-threaded Flask)
- **Database**: ~10,000 INSERTs/second (SQLite)
- **Frontend**: Renders smoothly up to ~10,000 points

### Bottlenecks
1. **Database writes**: Single-threaded SQLite writer
2. **Frontend re-renders**: Chart re-draws on every update
3. **Memory**: Frontend keeps 1 hour of data in memory

### Scaling Approaches
1. **Horizontal**: Multiple producers → Load balancer → Multiple backend instances → Shared DB
2. **Vertical**: Batch inserts, connection pooling, async I/O
3. **Data aggregation**: Downsample old data (e.g., 1-second → 1-minute resolution after 1 hour)

## Security Considerations

### Current State (Development)
- No authentication
- No HTTPS
- No rate limiting
- CORS wide open

### Production Recommendations
- Add API keys or JWT tokens
- Enable HTTPS (Let's Encrypt)
- Implement rate limiting (Flask-Limiter)
- Restrict CORS to specific origins
- Add input validation (marshmallow/pydantic)
- Sanitize database queries (parameterized - already done)

## Deployment Strategy

### Local Development (Current)
```bash
Terminal 1: python backend/app.py
Terminal 2: python producer/producer.py
Terminal 3: npm start (in frontend/)
```

### Docker Deployment (Future)
```yaml
services:
  backend:
    build: ./backend
    ports: ["5001:5001"]
    volumes: ["./data:/data"]

  producer:
    build: ./producer
    depends_on: [backend]

  frontend:
    build: ./frontend
    ports: ["3000:80"]
```

### Cloud Deployment Options
1. **AWS**: ECS (backend) + S3 (frontend) + RDS (database)
2. **Heroku**: Web dyno (backend + frontend) + Postgres
3. **Railway**: Simple git push deployment

## Future Improvements

### Feature Enhancements
1. **Alerts**: Threshold-based notifications
2. **Annotations**: Mark events on timeline
3. **Multi-tenancy**: Support multiple users/organizations
4. **Data export**: CSV/JSON download
5. **Signal configuration**: Add/remove signals dynamically

### Technical Improvements
1. **Caching**: Redis for frequently accessed data
2. **Batch processing**: Aggregate producer sends (10 points → 1 request)
3. **Compression**: gzip transport encoding
4. **Downsampling**: LTTB algorithm for chart rendering
5. **E2E tests**: Cypress or Playwright
6. **CI/CD**: GitHub Actions for automated testing and deployment
