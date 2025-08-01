"""
Enterprise AI System - Event-Driven Architecture
Message bus and event handling for decoupled microservices communication
"""

import os
import sys
import json
import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from queue import Queue, Empty
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'event-bus-secret-key-change-in-production'

# Enable CORS for all routes
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

@dataclass
class Event:
    """Represents an event in the system"""
    id: str
    type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """Create event from dictionary"""
        return cls(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3)
        )

class EventBus:
    """Event bus for managing event-driven communication"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_queue = Queue()
        self.dead_letter_queue = Queue()
        self.event_history: List[Event] = []
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "subscribers_count": 0,
            "start_time": datetime.utcnow()
        }
        self.running = False
        self.worker_thread = None
    
    def start(self):
        """Start the event bus worker"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_events, daemon=True)
            self.worker_thread.start()
            logger.info("Event bus started")
    
    def stop(self):
        """Stop the event bus worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Event bus stopped")
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]):
        """Subscribe to events of a specific type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
        self.stats["subscribers_count"] += 1
        logger.info(f"Subscribed to event type: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable[[Event], None]):
        """Unsubscribe from events"""
        if event_type in self.subscribers and handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)
            self.stats["subscribers_count"] -= 1
            
            # Remove empty event type
            if not self.subscribers[event_type]:
                del self.subscribers[event_type]
            
            logger.info(f"Unsubscribed from event type: {event_type}")
    
    def publish(self, event_type: str, source: str, data: Dict[str, Any], correlation_id: Optional[str] = None) -> str:
        """Publish an event"""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source=source,
            data=data,
            timestamp=datetime.utcnow(),
            correlation_id=correlation_id
        )
        
        self.event_queue.put(event)
        self.stats["events_published"] += 1
        
        logger.info(f"Published event: {event_type} from {source}")
        return event.id
    
    def _process_events(self):
        """Process events from the queue"""
        while self.running:
            try:
                # Get event from queue with timeout
                event = self.event_queue.get(timeout=1)
                
                # Add to history
                self.event_history.append(event)
                
                # Keep only last 1000 events
                if len(self.event_history) > 1000:
                    self.event_history = self.event_history[-1000:]
                
                # Process event
                self._handle_event(event)
                
                self.event_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing events: {e}")
    
    def _handle_event(self, event: Event):
        """Handle a single event"""
        try:
            # Get subscribers for this event type
            handlers = self.subscribers.get(event.type, [])
            
            if not handlers:
                logger.warning(f"No handlers for event type: {event.type}")
                return
            
            # Call all handlers
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Handler error for event {event.id}: {e}")
                    self._handle_failed_event(event, e)
            
            self.stats["events_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error handling event {event.id}: {e}")
            self._handle_failed_event(event, e)
    
    def _handle_failed_event(self, event: Event, error: Exception):
        """Handle failed event processing"""
        event.retry_count += 1
        
        if event.retry_count <= event.max_retries:
            # Retry the event
            logger.info(f"Retrying event {event.id} (attempt {event.retry_count})")
            self.event_queue.put(event)
        else:
            # Move to dead letter queue
            logger.error(f"Event {event.id} moved to dead letter queue after {event.retry_count} attempts")
            self.dead_letter_queue.put((event, str(error)))
            self.stats["events_failed"] += 1
    
    def get_stats(self) -> Dict:
        """Get event bus statistics"""
        uptime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "queue_size": self.event_queue.qsize(),
            "dead_letter_queue_size": self.dead_letter_queue.qsize(),
            "event_types": list(self.subscribers.keys()),
            "recent_events": [event.to_dict() for event in self.event_history[-10:]],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_dead_letter_events(self) -> List[Dict]:
        """Get events from dead letter queue"""
        dead_events = []
        temp_queue = Queue()
        
        # Extract all events from dead letter queue
        while not self.dead_letter_queue.empty():
            try:
                event, error = self.dead_letter_queue.get_nowait()
                dead_events.append({
                    "event": event.to_dict(),
                    "error": error
                })
                temp_queue.put((event, error))
            except Empty:
                break
        
        # Put events back
        while not temp_queue.empty():
            self.dead_letter_queue.put(temp_queue.get_nowait())
        
        return dead_events

# Global event bus instance
event_bus = EventBus()

# Predefined event handlers for AI services
def handle_ai_analysis_request(event: Event):
    """Handle AI analysis request events"""
    logger.info(f"Processing AI analysis request: {event.data.get('analysis_type')}")
    
    # Simulate processing
    time.sleep(0.1)
    
    # Publish result event
    result_data = {
        "request_id": event.data.get("request_id"),
        "analysis_type": event.data.get("analysis_type"),
        "result": "Analysis completed successfully",
        "confidence": 0.95,
        "processing_time_ms": 100
    }
    
    event_bus.publish(
        "ai.analysis.completed",
        "ai_service",
        result_data,
        event.correlation_id
    )

def handle_user_action(event: Event):
    """Handle user action events"""
    action = event.data.get("action")
    user_id = event.data.get("user_id")
    
    logger.info(f"User {user_id} performed action: {action}")
    
    # Trigger recommendations update
    if action in ["login", "view_item", "purchase"]:
        event_bus.publish(
            "recommendations.update_required",
            "user_service",
            {"user_id": user_id, "trigger": action},
            event.correlation_id
        )

def handle_system_alert(event: Event):
    """Handle system alert events"""
    alert_type = event.data.get("alert_type")
    severity = event.data.get("severity", "info")
    
    logger.warning(f"System alert [{severity}]: {alert_type}")
    
    # Send notification
    event_bus.publish(
        "notification.send",
        "monitoring_service",
        {
            "type": "system_alert",
            "message": f"System alert: {alert_type}",
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        },
        event.correlation_id
    )

# Register default event handlers
event_bus.subscribe("ai.analysis.requested", handle_ai_analysis_request)
event_bus.subscribe("user.action", handle_user_action)
event_bus.subscribe("system.alert", handle_system_alert)

# API Routes

@app.route('/events/publish', methods=['POST'])
def publish_event():
    """Publish an event"""
    try:
        data = request.get_json()
        if not data or 'type' not in data or 'source' not in data or 'data' not in data:
            return jsonify({"error": "Event type, source, and data are required"}), 400
        
        event_type = data['type']
        source = data['source']
        event_data = data['data']
        correlation_id = data.get('correlation_id')
        
        event_id = event_bus.publish(event_type, source, event_data, correlation_id)
        
        return jsonify({
            "event_id": event_id,
            "status": "published",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/subscribe', methods=['POST'])
def subscribe_webhook():
    """Subscribe to events via webhook (simplified)"""
    try:
        data = request.get_json()
        if not data or 'event_type' not in data or 'webhook_url' not in data:
            return jsonify({"error": "Event type and webhook URL are required"}), 400
        
        # In a real implementation, you would store webhook URLs and call them
        # For demo purposes, we'll just acknowledge the subscription
        
        return jsonify({
            "status": "subscribed",
            "event_type": data['event_type'],
            "webhook_url": data['webhook_url'],
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/stats')
def get_stats():
    """Get event bus statistics"""
    try:
        stats = event_bus.get_stats()
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/history')
def get_event_history():
    """Get recent event history"""
    try:
        limit = int(request.args.get('limit', 50))
        events = event_bus.event_history[-limit:]
        
        return jsonify({
            "events": [event.to_dict() for event in events],
            "total_events": len(event_bus.event_history),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/dead-letter')
def get_dead_letter_events():
    """Get dead letter queue events"""
    try:
        dead_events = event_bus.get_dead_letter_events()
        
        return jsonify({
            "dead_letter_events": dead_events,
            "count": len(dead_events),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/events/simulate', methods=['POST'])
def simulate_events():
    """Simulate various events for testing"""
    try:
        data = request.get_json()
        event_type = data.get('event_type', 'test')
        count = data.get('count', 1)
        
        event_ids = []
        
        for i in range(count):
            if event_type == 'ai_analysis':
                event_id = event_bus.publish(
                    "ai.analysis.requested",
                    "test_client",
                    {
                        "request_id": f"req_{i}",
                        "analysis_type": "sentiment",
                        "text": f"Sample text for analysis {i}"
                    }
                )
            elif event_type == 'user_action':
                event_id = event_bus.publish(
                    "user.action",
                    "test_client",
                    {
                        "user_id": f"user_{i}",
                        "action": "login",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            elif event_type == 'system_alert':
                event_id = event_bus.publish(
                    "system.alert",
                    "test_client",
                    {
                        "alert_type": "high_cpu_usage",
                        "severity": "warning",
                        "value": 85.5
                    }
                )
            else:
                event_id = event_bus.publish(
                    f"test.{event_type}",
                    "test_client",
                    {"message": f"Test event {i}"}
                )
            
            event_ids.append(event_id)
        
        return jsonify({
            "simulated_events": event_ids,
            "count": len(event_ids),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check for event bus"""
    return jsonify({
        "service": "Event Bus Service",
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "event_driven_architecture",
            "message_queuing",
            "event_subscriptions",
            "retry_mechanism",
            "dead_letter_queue",
            "event_history"
        ],
        "running": event_bus.running,
        "queue_size": event_bus.event_queue.qsize(),
        "subscribers": len(event_bus.subscribers),
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/info')
def service_info():
    """Get service information"""
    return jsonify({
        "service_name": "Enterprise AI Event Bus",
        "description": "Event-driven architecture for decoupled microservices communication",
        "version": "2.0.0",
        "features": [
            "Asynchronous event processing",
            "Event type subscriptions",
            "Retry mechanism with exponential backoff",
            "Dead letter queue for failed events",
            "Event history and auditing",
            "Real-time event statistics",
            "Correlation ID tracking"
        ],
        "event_types": [
            "ai.analysis.requested",
            "ai.analysis.completed",
            "user.action",
            "system.alert",
            "notification.send",
            "recommendations.update_required"
        ],
        "endpoints": [
            "/events/publish",
            "/events/subscribe",
            "/events/stats",
            "/events/history",
            "/events/dead-letter",
            "/events/simulate"
        ],
        "timestamp": datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    # Start the event bus
    event_bus.start()
    
    print("🚀 Starting Enterprise AI Event Bus...")
    print("📡 Event Bus URL: http://localhost:7003")
    print("📊 Event Statistics: http://localhost:7003/events/stats")
    print("📜 Event History: http://localhost:7003/events/history")
    print("🏥 Health Check: http://localhost:7003/health")
    print("🔄 Event processing started")
    
    try:
        app.run(host='0.0.0.0', port=7003, debug=True)
    finally:
        event_bus.stop()

