# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026, Mark LaPointe <mark@cloudbsd.org>
#
# See LICENSE file for full license text.

"""Mock doll client for testing the server without hardware."""

import asyncio
import json
import random
import time

import websockets


class MockDollClient:
    """A mock doll client that connects to the server and simulates a doll."""

    def __init__(self, doll_id: str, name: str, server_url: str = "ws://localhost:8000") -> None:
        self.doll_id = doll_id
        self.name = name
        self.server_url = server_url
        self.ws = None
        self.running = False
        self._tasks: list[asyncio.Task] = []

    async def connect(self) -> None:
        """Connect to the server."""
        uri = f"{self.server_url}/ws/doll/{self.doll_id}"
        self.ws = await websockets.connect(uri)
        self.running = True
        print(f"[MockDoll {self.doll_id}] Connected to {uri}")

        # Start background tasks
        self._tasks.append(asyncio.create_task(self._heartbeat_loop()))
        self._tasks.append(asyncio.create_task(self._sensor_loop()))
        self._tasks.append(asyncio.create_task(self._receive_loop()))

    async def disconnect(self) -> None:
        """Disconnect from the server."""
        self.running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        if self.ws:
            await self.ws.close()
        print(f"[MockDoll {self.doll_id}] Disconnected")

    async def _heartbeat_loop(self) -> None:
        """Send periodic pings."""
        while self.running:
            try:
                await self.ws.send(json.dumps({"type": "ping"}))
                await asyncio.sleep(5)
            except Exception:
                break

    async def _sensor_loop(self) -> None:
        """Send periodic sensor data."""
        while self.running:
            try:
                battery = 3.5 + random.random() * 0.8
                rssi = -30 - int(random.random() * 40)
                await self.ws.send(json.dumps({
                    "type": "sensor_data",
                    "data": {
                        "battery": round(battery, 2),
                        "wifi_rssi": rssi,
                        "temperature": round(25 + random.random() * 10, 1),
                    },
                }))
                await asyncio.sleep(10)
            except Exception:
                break

    async def _receive_loop(self) -> None:
        """Handle incoming messages from server."""
        while self.running:
            try:
                raw = await self.ws.recv()
                data = json.loads(raw)
                msg_type = data.get("type")

                if msg_type == "text_message":
                    text = data.get("text", "")
                    print(f"[MockDoll {self.doll_id}] Received text: {text}")
                    # Echo back a response
                    await self.ws.send(json.dumps({
                        "type": "conversation",
                        "role": "assistant",
                        "text": f"You said: {text}",
                    }))

                elif msg_type == "servo_command":
                    print(f"[MockDoll {self.doll_id}] Servo command: ch={data.get('channel')} angle={data.get('angle')}")

                elif msg_type == "expression":
                    print(f"[MockDoll {self.doll_id}] Expression: {data.get('name')}")

                elif msg_type == "action":
                    print(f"[MockDoll {self.doll_id}] Action: {data.get('name')}")

                elif msg_type == "stop_speaking":
                    print(f"[MockDoll {self.doll_id}] Stop speaking")

            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                print(f"[MockDoll {self.doll_id}] Error: {e}")
                break

    async def send_video_frame(self, frame_data: str) -> None:
        """Send a video frame (base64 encoded JPEG)."""
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "video_frame",
                "format": "jpeg_720p",
                "data": frame_data,
            }))

    async def send_audio_chunk(self, audio_data: str) -> None:
        """Send an audio chunk (base64 encoded PCM)."""
        if self.ws:
            await self.ws.send(json.dumps({
                "type": "audio_chunk",
                "format": "pcm_s16le_16khz_mono",
                "data": audio_data,
            }))


async def run_mock_client() -> None:
    """Run a single mock doll client."""
    client = MockDollClient(doll_id="mock-teddy-01", name="Mock Doll")
    await client.connect()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(run_mock_client())
