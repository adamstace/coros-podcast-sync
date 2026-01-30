"""WebSocket handlers for real-time updates."""

import logging
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "downloads": set(),
            "sync": set()
        }

    async def connect(self, websocket: WebSocket, channel: str):
        """Connect a client to a channel."""
        await websocket.accept()
        self.active_connections[channel].add(websocket)
        logger.info(f"Client connected to {channel} channel. Total: {len(self.active_connections[channel])}")

    def disconnect(self, websocket: WebSocket, channel: str):
        """Disconnect a client from a channel."""
        self.active_connections[channel].discard(websocket)
        logger.info(f"Client disconnected from {channel} channel. Total: {len(self.active_connections[channel])}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")

    async def broadcast(self, channel: str, message: dict):
        """Broadcast a message to all clients in a channel."""
        disconnected = set()

        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections[channel].discard(connection)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/downloads")
async def websocket_downloads(websocket: WebSocket):
    """WebSocket endpoint for download progress updates."""
    await manager.connect(websocket, "downloads")

    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()

            # Client can send ping messages to keep connection alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, "downloads")
    except Exception as e:
        logger.error(f"WebSocket downloads error: {e}")
        manager.disconnect(websocket, "downloads")


@router.websocket("/ws/sync")
async def websocket_sync(websocket: WebSocket):
    """WebSocket endpoint for sync progress updates."""
    await manager.connect(websocket, "sync")

    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()

            # Client can send ping messages to keep connection alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, "sync")
    except Exception as e:
        logger.error(f"WebSocket sync error: {e}")
        manager.disconnect(websocket, "sync")


# Helper functions to broadcast messages from other parts of the app

async def broadcast_download_progress(episode_id: int, bytes_downloaded: int, total_bytes: int):
    """Broadcast download progress update."""
    progress = int((bytes_downloaded / total_bytes) * 100) if total_bytes > 0 else 0

    message = {
        "type": "download_progress",
        "episode_id": episode_id,
        "bytes_downloaded": bytes_downloaded,
        "total_bytes": total_bytes,
        "progress": progress
    }

    await manager.broadcast("downloads", message)


async def broadcast_download_complete(episode_id: int, success: bool, error: str = None):
    """Broadcast download completion."""
    message = {
        "type": "download_complete",
        "episode_id": episode_id,
        "success": success,
        "error": error
    }

    await manager.broadcast("downloads", message)


async def broadcast_sync_progress(current: int, total: int, episode_title: str, status: str):
    """Broadcast sync progress update."""
    message = {
        "type": "sync_progress",
        "current": current,
        "total": total,
        "episode_title": episode_title,
        "status": status,
        "progress": int((current / total) * 100) if total > 0 else 0
    }

    await manager.broadcast("sync", message)


async def broadcast_sync_complete(success: bool, episodes_added: int, episodes_removed: int, error: str = None):
    """Broadcast sync completion."""
    message = {
        "type": "sync_complete",
        "success": success,
        "episodes_added": episodes_added,
        "episodes_removed": episodes_removed,
        "error": error
    }

    await manager.broadcast("sync", message)
