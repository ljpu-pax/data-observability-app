#!/usr/bin/env python3
"""
Backend API - Ingests telemetry data, stores in SQLite, and serves via REST + WebSocket
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime, timedelta
import json
from threading import Lock

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DB_PATH = "telemetry.db"
db_lock = Lock()


def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            signal_name TEXT NOT NULL,
            value REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_timestamp ON telemetry(timestamp)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_signal_name ON telemetry(signal_name)
    """)

    conn.commit()
    conn.close()
    print("Database initialized")


def store_telemetry(timestamp, signals):
    """Store telemetry data in database"""
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for signal_name, value in signals.items():
            cursor.execute(
                "INSERT INTO telemetry (timestamp, signal_name, value) VALUES (?, ?, ?)",
                (timestamp, signal_name, value)
            )

        conn.commit()
        conn.close()


def get_recent_telemetry(hours=1):
    """Retrieve telemetry data from the last N hours"""
    cutoff_time = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT timestamp, signal_name, value
            FROM telemetry
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (cutoff_time,))

        rows = cursor.fetchall()
        conn.close()

    # Group by signal name
    data = {}
    for timestamp, signal_name, value in rows:
        if signal_name not in data:
            data[signal_name] = []
        data[signal_name].append({
            "timestamp": timestamp,
            "value": value
        })

    return data


@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    """Endpoint to receive telemetry data from producer"""
    try:
        payload = request.get_json()
        timestamp = payload.get('timestamp')
        signals = payload.get('signals', {})

        if not timestamp or not signals:
            return jsonify({"error": "Invalid payload"}), 400

        # Store in database
        store_telemetry(timestamp, signals)

        # Broadcast to connected WebSocket clients
        socketio.emit('telemetry_update', payload)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Error receiving telemetry: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    """Endpoint to retrieve historical telemetry data"""
    try:
        hours = request.args.get('hours', default=1, type=float)
        data = get_recent_telemetry(hours)
        return jsonify(data), 200

    except Exception as e:
        print(f"Error retrieving telemetry: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/signals', methods=['GET'])
def get_signals():
    """Endpoint to get list of available signals"""
    try:
        with db_lock:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT signal_name
                FROM telemetry
                ORDER BY signal_name
            """)

            signals = [row[0] for row in cursor.fetchall()]
            conn.close()

        return jsonify(signals), 200

    except Exception as e:
        print(f"Error retrieving signals: {e}")
        return jsonify({"error": str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f"Client connected: {request.sid}")
    emit('connection_response', {"status": "connected"})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print(f"Client disconnected: {request.sid}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    print("Initializing backend...")
    init_db()
    print("Starting Flask server on http://localhost:5000")
    print("-" * 50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
