"""
Enterprise AI System - WebSocket Real-time Communication Server
Provides real-time updates, notifications, and live data streaming
"""

import os
import sys
import json
import asyncio
import websockets
import logging
from datetime import datetime
from typing import Dict, Set, List, Optional
import jwt
import requests
from dataclasses import dataclass, asdict
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client"""
    websocket: websockets.WebSocketServerProtocol
    client_id: str
    user_id: Optional[str] = None
    subscriptions: Set[str] = None
    connected_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()
        if self.connected_at is None:
            self.connected_at = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()

class WebSocketManager:
    """Manages WebSocket connections and real-time communication"""
    
    def __init__(self):
        self.clients: Dict[str, WebSocketClient] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel -> set of client_ids
        self.message_history: Dict[str, List[Dict]] = {}  # channel -> messages
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "channels_created": 0,
            "start_time": datetime.utcnow()
        }
    
    async def register_client(self, websocket: websockets.WebSocketServerProtocol, client_id: str) -> WebSocketClient:
        """Register a new WebSocket client"""
        client = WebSocketClient(
            websocket=websocket,
            client_id=client_id
        )
        
        self.clients[client_id] = client
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1
        
        logger.info(f"Client {client_id} connected. Active connections: {self.stats['active_connections']}")
        
        # Send welcome message
        await self.send_to_client(client_id, {
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "server_info": {
                "name": "Enterprise AI WebSocket Server",
                "version": "2.0.0",
                "features": ["real_time_updates", "channel_subscriptions", "notifications", "live_analytics"]
            }
        })
        
        return client
    
    async def unregister_client(self, client_id: str):
        """Unregister a WebSocket client"""
        if client_id in self.clients:
            client = self.clients[client_id]
            
            # Remove from all channels
            for channel in list(client.subscriptions):
                await self.unsubscribe_from_channel(client_id, channel)
            
            del self.clients[client_id]
            self.stats["active_connections"] -= 1
            
            logger.info(f"Client {client_id} disconnected. Active connections: {self.stats['active_connections']}")
    
    async def authenticate_client(self, client_id: str, token: str) -> bool:
        """Authenticate client using JWT token"""
        try:
            if not token:
                return False
            
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # For demo purposes, accept any valid-looking token
            # In production, verify against your auth service
            if len(token) > 20:
                if client_id in self.clients:
                    # Extract user_id from token (simplified)
                    self.clients[client_id].user_id = f"user_{client_id[:8]}"
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Authentication error for client {client_id}: {e}")
            return False
    
    async def subscribe_to_channel(self, client_id: str, channel: str):
        """Subscribe client to a channel"""
        if client_id not in self.clients:
            return False
        
        # Create channel if it doesn't exist
        if channel not in self.channels:
            self.channels[channel] = set()
            self.message_history[channel] = []
            self.stats["channels_created"] += 1
        
        # Add client to channel
        self.channels[channel].add(client_id)
        self.clients[client_id].subscriptions.add(channel)
        
        logger.info(f"Client {client_id} subscribed to channel '{channel}'")
        
        # Send subscription confirmation
        await self.send_to_client(client_id, {
            "type": "subscription_confirmed",
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send recent message history
        if self.message_history[channel]:
            recent_messages = self.message_history[channel][-10:]  # Last 10 messages
            await self.send_to_client(client_id, {
                "type": "message_history",
                "channel": channel,
                "messages": recent_messages,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return True
    
    async def unsubscribe_from_channel(self, client_id: str, channel: str):
        """Unsubscribe client from a channel"""
        if client_id in self.clients and channel in self.clients[client_id].subscriptions:
            self.clients[client_id].subscriptions.remove(channel)
        
        if channel in self.channels and client_id in self.channels[channel]:
            self.channels[channel].remove(client_id)
            
            # Remove empty channels
            if not self.channels[channel]:
                del self.channels[channel]
                del self.message_history[channel]
        
        logger.info(f"Client {client_id} unsubscribed from channel '{channel}'")
        
        # Send unsubscription confirmation
        await self.send_to_client(client_id, {
            "type": "unsubscription_confirmed",
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_to_client(self, client_id: str, message: Dict):
        """Send message to specific client"""
        if client_id not in self.clients:
            return False
        
        try:
            client = self.clients[client_id]
            await client.websocket.send(json.dumps(message))
            client.last_activity = datetime.utcnow()
            self.stats["messages_sent"] += 1
            return True
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(client_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            return False
    
    async def broadcast_to_channel(self, channel: str, message: Dict, exclude_client: Optional[str] = None):
        """Broadcast message to all clients in a channel"""
        if channel not in self.channels:
            return 0
        
        # Add to message history
        message_with_id = {
            **message,
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.message_history[channel].append(message_with_id)
        
        # Keep only last 100 messages per channel
        if len(self.message_history[channel]) > 100:
            self.message_history[channel] = self.message_history[channel][-100:]
        
        # Send to all subscribed clients
        sent_count = 0
        for client_id in list(self.channels[channel]):
            if exclude_client and client_id == exclude_client:
                continue
            
            success = await self.send_to_client(client_id, message_with_id)
            if success:
                sent_count += 1
        
        logger.info(f"Broadcasted message to {sent_count} clients in channel '{channel}'")
        return sent_count
    
    async def broadcast_to_all(self, message: Dict):
        """Broadcast message to all connected clients"""
        sent_count = 0
        for client_id in list(self.clients.keys()):
            success = await self.send_to_client(client_id, message)
            if success:
                sent_count += 1
        
        logger.info(f"Broadcasted message to {sent_count} clients")
        return sent_count
    
    def get_stats(self) -> Dict:
        """Get server statistics"""
        uptime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "channels": {
                "total": len(self.channels),
                "active": {channel: len(clients) for channel, clients in self.channels.items()}
            },
            "clients": {
                "active": len(self.clients),
                "by_channel": {
                    channel: len(clients) for channel, clients in self.channels.items()
                }
            }
        }

# Global WebSocket manager
ws_manager = WebSocketManager()

async def handle_client_message(client_id: str, message: Dict):
    """Handle incoming message from client"""
    message_type = message.get("type")
    
    if message_type == "authenticate":
        token = message.get("token")
        success = await ws_manager.authenticate_client(client_id, token)
        
        await ws_manager.send_to_client(client_id, {
            "type": "authentication_result",
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "subscribe":
        channel = message.get("channel")
        if channel:
            await ws_manager.subscribe_to_channel(client_id, channel)
    
    elif message_type == "unsubscribe":
        channel = message.get("channel")
        if channel:
            await ws_manager.unsubscribe_from_channel(client_id, channel)
    
    elif message_type == "send_message":
        channel = message.get("channel")
        content = message.get("content")
        
        if channel and content:
            # Broadcast message to channel
            await ws_manager.broadcast_to_channel(channel, {
                "type": "channel_message",
                "channel": channel,
                "content": content,
                "sender": client_id,
                "user_id": ws_manager.clients[client_id].user_id
            }, exclude_client=client_id)
    
    elif message_type == "ping":
        await ws_manager.send_to_client(client_id, {
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif message_type == "get_stats":
        stats = ws_manager.get_stats()
        await ws_manager.send_to_client(client_id, {
            "type": "stats",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    else:
        await ws_manager.send_to_client(client_id, {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": datetime.utcnow().isoformat()
        })

async def websocket_handler(websocket, path):
    """Handle WebSocket connections"""
    client_id = str(uuid.uuid4())
    
    try:
        # Register client
        await ws_manager.register_client(websocket, client_id)
        
        # Handle messages
        async for message in websocket:
            try:
                data = json.loads(message)
                await handle_client_message(client_id, data)
            except json.JSONDecodeError:
                await ws_manager.send_to_client(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error handling message from client {client_id}: {e}")
                await ws_manager.send_to_client(client_id, {
                    "type": "error",
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} connection closed")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        await ws_manager.unregister_client(client_id)

async def broadcast_system_updates():
    """Periodically broadcast system updates"""
    while True:
        try:
            # Broadcast system stats every 30 seconds
            await asyncio.sleep(30)
            
            stats = ws_manager.get_stats()
            await ws_manager.broadcast_to_channel("system_updates", {
                "type": "system_stats",
                "data": stats
            })
            
            # Simulate AI service updates
            ai_update = {
                "type": "ai_service_update",
                "service": "nlp",
                "status": "processing",
                "queue_size": 5,
                "avg_response_time": "120ms"
            }
            await ws_manager.broadcast_to_channel("ai_updates", ai_update)
            
        except Exception as e:
            logger.error(f"Error in system updates broadcast: {e}")

async def main():
    """Start the WebSocket server"""
    logger.info("🚀 Starting Enterprise AI WebSocket Server...")
    logger.info("📡 WebSocket URL: ws://localhost:7000")
    logger.info("🔗 Available channels: system_updates, ai_updates, user_notifications, analytics")
    
    # Start background tasks
    asyncio.create_task(broadcast_system_updates())
    
    # Start WebSocket server
    start_server = websockets.serve(websocket_handler, "0.0.0.0", 7000)
    
    logger.info("✅ WebSocket server started on port 7000")
    
    await start_server

if __name__ == "__main__":
    asyncio.run(main())

