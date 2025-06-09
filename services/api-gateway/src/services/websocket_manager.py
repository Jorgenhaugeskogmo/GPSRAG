"""
WebSocket Manager for sanntidskommunikasjon
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Håndterer WebSocket-tilkoblinger og meldinger"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> [session_ids]
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Koble til en ny WebSocket-klient"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket klient {client_id} koblet til")
    
    async def disconnect(self, client_id: str):
        """Koble fra en WebSocket-klient"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket klient {client_id} koblet fra")
    
    async def send_personal_message(self, message: str, client_id: str):
        """Send melding til en spesifikk klient"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Feil ved sending av melding til {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def send_json_message(self, data: dict, client_id: str):
        """Send JSON-melding til en spesifikk klient"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Feil ved sending av JSON-melding til {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast_message(self, message: str):
        """Send melding til alle tilkoblede klienter"""
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Feil ved broadcasting til {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Fjern frakoblede klienter
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def notify_chat_update(self, session_id: str, message_data: dict):
        """Varsle alle klienter om chat-oppdatering"""
        notification = {
            "type": "chat_update",
            "session_id": session_id,
            "data": message_data
        }
        
        # Send til alle tilkoblede klienter (i en ekte app ville du filtrere på bruker)
        for client_id in self.active_connections:
            await self.send_json_message(notification, client_id)
    
    def get_connected_count(self) -> int:
        """Få antall tilkoblede klienter"""
        return len(self.active_connections) 