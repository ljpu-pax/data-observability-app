#!/usr/bin/env python3
"""
Telemetry Producer - Generates and streams time-series signals to the backend
"""
import time
import math
import random
import requests
from datetime import datetime
import numpy as np

BACKEND_URL = "http://localhost:5001/api/telemetry"
EMIT_INTERVAL = 1.0  # seconds


class SignalGenerator:
    """Generates various types of time-series signals"""

    def __init__(self):
        self.start_time = time.time()
        self.noise_offset = random.uniform(0, 100)

    def sine_wave(self, frequency=0.1, amplitude=10, offset=0):
        """Generate sine wave signal"""
        t = time.time() - self.start_time
        return amplitude * math.sin(2 * math.pi * frequency * t) + offset

    def cosine_wave(self, frequency=0.15, amplitude=8, offset=0):
        """Generate cosine wave signal"""
        t = time.time() - self.start_time
        return amplitude * math.cos(2 * math.pi * frequency * t) + offset

    def random_noise(self, amplitude=5):
        """Generate random noise signal"""
        return random.uniform(-amplitude, amplitude)

    def random_walk(self, step_size=0.5):
        """Generate random walk signal"""
        if not hasattr(self, 'walk_value'):
            self.walk_value = 0
        self.walk_value += random.uniform(-step_size, step_size)
        return self.walk_value

    def damped_oscillation(self, frequency=0.2, amplitude=15, decay=0.01):
        """Generate damped oscillation signal"""
        t = time.time() - self.start_time
        return amplitude * math.exp(-decay * t) * math.sin(2 * math.pi * frequency * t)


def main():
    """Main producer loop"""
    generator = SignalGenerator()

    print("Starting telemetry producer...")
    print(f"Sending data to: {BACKEND_URL}")
    print(f"Emit interval: {EMIT_INTERVAL}s")
    print("-" * 50)

    while True:
        try:
            timestamp = datetime.utcnow().isoformat()

            # Generate signals
            signals = {
                "sine_wave": generator.sine_wave(),
                "cosine_wave": generator.cosine_wave(),
                "random_noise": generator.random_noise(),
                "random_walk": generator.random_walk(),
                "damped_oscillation": generator.damped_oscillation()
            }

            # Prepare payload
            payload = {
                "timestamp": timestamp,
                "signals": signals
            }

            # Send to backend
            response = requests.post(BACKEND_URL, json=payload, timeout=2)

            if response.status_code == 200:
                print(f"✓ [{timestamp}] Sent: {', '.join([f'{k}={v:.2f}' for k, v in signals.items()])}")
            else:
                print(f"✗ [{timestamp}] Error: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"✗ [{datetime.utcnow().isoformat()}] Backend not available, retrying...")
        except Exception as e:
            print(f"✗ [{datetime.utcnow().isoformat()}] Error: {e}")

        time.sleep(EMIT_INTERVAL)


if __name__ == "__main__":
    main()
