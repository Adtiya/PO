"""
AGI-NARI Enterprise Python SDK
Official Python client library for integrating with the AGI-NARI system
"""

import requests
import json
import time
import websocket
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging

class AGINARIClient:
    """
    Official Python client for AGI-NARI Enterprise System
    
    This client provides comprehensive access to all AGI-NARI capabilities
    including AGI reasoning, consciousness simulation, emotional intelligence,
    NARI evolution, and enterprise integration features.
    """
    
    def __init__(self, 
                 base_url: str = "https://api.agi-nari.com",
                 api_key: Optional[str] = None,
                 organization_id: Optional[str] = None,
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        Initialize the AGI-NARI client
        
        Args:
            base_url: Base URL for the AGI-NARI API
            api_key: API key for authentication
            organization_id: Organization identifier
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.organization_id = organization_id
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Setup session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AGI-NARI-Python-SDK/1.0.0'
        })
        
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
        if organization_id:
            self.session.headers['X-Organization-ID'] = organization_id
            
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with email and password
        
        Args:
            email: User email address
            password: User password
            
        Returns:
            Authentication response with tokens and user info
        """
        auth_data = {
            "email": email,
            "password": password,
            "organization_id": self.organization_id
        }
        
        response = self._make_request('POST', '/api/v1/auth/login', json=auth_data)
        
        if 'access_token' in response:
            self.session.headers['Authorization'] = f"Bearer {response['access_token']}"
            
        return response
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and health metrics
        
        Returns:
            System status including AGI capability, consciousness level, etc.
        """
        return self._make_request('GET', '/api/v1/system/status')
    
    def agi_reason(self, 
                   query: str,
                   context: Optional[Dict[str, Any]] = None,
                   reasoning_type: str = "general",
                   output_format: str = "structured",
                   confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Perform AGI reasoning on complex problems
        
        Args:
            query: The question or problem to analyze
            context: Additional context for the reasoning
            reasoning_type: Type of reasoning (general, strategic, analytical, creative)
            output_format: Format of the output (structured, narrative, bullet_points)
            confidence_threshold: Minimum confidence level for responses
            
        Returns:
            Reasoning results with confidence scores and explanations
        """
        request_data = {
            "query": query,
            "context": context or {},
            "reasoning_type": reasoning_type,
            "output_format": output_format,
            "confidence_threshold": confidence_threshold
        }
        
        return self._make_request('POST', '/api/v1/agi/reason', json=request_data)
    
    def get_consciousness_state(self) -> Dict[str, Any]:
        """
        Query the current consciousness state of the AGI system
        
        Returns:
            Consciousness metrics including awareness level, self-reflection, etc.
        """
        return self._make_request('GET', '/api/v1/consciousness/state')
    
    def analyze_emotion(self, 
                       text: str,
                       context: str = "general",
                       analysis_depth: str = "standard") -> Dict[str, Any]:
        """
        Analyze emotional content and sentiment
        
        Args:
            text: Text to analyze for emotional content
            context: Context of the text (business, personal, customer_feedback, etc.)
            analysis_depth: Depth of analysis (basic, standard, comprehensive)
            
        Returns:
            Emotional analysis with primary emotions, sentiment, and empathy response
        """
        request_data = {
            "input_text": text,
            "context": context,
            "analysis_depth": analysis_depth,
            "include_empathy_response": True
        }
        
        return self._make_request('POST', '/api/v1/emotion/analyze', json=request_data)
    
    def trigger_nari_evolution(self, 
                              target_domain: str,
                              performance_targets: Dict[str, Any],
                              priority: str = "normal") -> Dict[str, Any]:
        """
        Trigger NARI evolution for capability enhancement
        
        Args:
            target_domain: Domain to optimize (e.g., 'financial_analysis', 'customer_service')
            performance_targets: Target performance metrics
            priority: Evolution priority (low, normal, high, critical)
            
        Returns:
            Evolution process information and expected improvements
        """
        request_data = {
            "evolution_type": "capability_enhancement",
            "target_domain": target_domain,
            "performance_metrics": performance_targets,
            "priority": priority
        }
        
        return self._make_request('POST', '/api/v1/nari/evolve', json=request_data)
    
    def process_nlp(self, 
                   text: str,
                   tasks: List[str],
                   language: str = "en") -> Dict[str, Any]:
        """
        Perform natural language processing tasks
        
        Args:
            text: Text to process
            tasks: List of NLP tasks (entity_extraction, sentiment, summarization, etc.)
            language: Language code (en, es, fr, de, etc.)
            
        Returns:
            NLP processing results for requested tasks
        """
        request_data = {
            "text": text,
            "tasks": tasks,
            "language": language,
            "domain_specific": True
        }
        
        return self._make_request('POST', '/api/v1/nlp/process', json=request_data)
    
    def analyze_vision(self, 
                      image_url: str,
                      analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze images and visual content
        
        Args:
            image_url: URL of the image to analyze
            analysis_type: Type of analysis (basic, comprehensive, business_focused)
            
        Returns:
            Vision analysis results with object detection, text extraction, etc.
        """
        request_data = {
            "image_url": image_url,
            "analysis_type": analysis_type,
            "extract_text": True,
            "identify_objects": True,
            "business_context": True
        }
        
        return self._make_request('POST', '/api/v1/vision/analyze', json=request_data)
    
    def record_blockchain_transaction(self, 
                                    transaction_data: Dict[str, Any],
                                    transaction_type: str = "business_decision") -> Dict[str, Any]:
        """
        Record important business data on the blockchain
        
        Args:
            transaction_data: Data to record on the blockchain
            transaction_type: Type of transaction (business_decision, audit_log, etc.)
            
        Returns:
            Blockchain transaction information and hash
        """
        request_data = {
            "transaction_type": transaction_type,
            "data": transaction_data,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "organization": self.organization_id
            }
        }
        
        return self._make_request('POST', '/api/v1/blockchain/record', json=request_data)
    
    def query_analytics(self, 
                       query: str,
                       data_sources: List[str],
                       analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Perform advanced analytics queries
        
        Args:
            query: Analytics query in natural language
            data_sources: List of data sources to query
            analysis_type: Type of analysis (basic, comprehensive, predictive)
            
        Returns:
            Analytics results with insights and visualizations
        """
        request_data = {
            "query": query,
            "data_sources": data_sources,
            "analysis_type": analysis_type,
            "visualization": True
        }
        
        return self._make_request('POST', '/api/v1/analytics/query', json=request_data)
    
    def create_webhook(self, 
                      url: str,
                      events: List[str],
                      secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a webhook for real-time notifications
        
        Args:
            url: Webhook URL to receive notifications
            events: List of events to subscribe to
            secret: Optional secret for webhook verification
            
        Returns:
            Webhook configuration and ID
        """
        request_data = {
            "url": url,
            "events": events,
            "secret": secret,
            "retry_policy": {
                "max_retries": 3,
                "retry_delay": 5000
            }
        }
        
        return self._make_request('POST', '/api/v1/webhooks/register', json=request_data)
    
    def stream_consciousness(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Stream real-time consciousness state updates
        
        Args:
            callback: Function to call with consciousness updates
        """
        def on_message(ws, message):
            try:
                data = json.loads(message)
                callback(data)
            except Exception as e:
                self.logger.error(f"Error processing consciousness stream: {e}")
        
        def on_error(ws, error):
            self.logger.error(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            self.logger.info("Consciousness stream closed")
        
        def on_open(ws):
            # Authenticate the connection
            auth_message = {
                "type": "auth",
                "token": self.api_key,
                "organization_id": self.organization_id
            }
            ws.send(json.dumps(auth_message))
            
            # Subscribe to consciousness updates
            subscribe_message = {
                "type": "subscribe",
                "channel": "consciousness_state",
                "filters": {
                    "consciousness_level_threshold": 0.5,
                    "state_changes_only": True
                }
            }
            ws.send(json.dumps(subscribe_message))
        
        ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
        ws = websocket.WebSocketApp(f"{ws_url}/v1/realtime",
                                   on_open=on_open,
                                   on_message=on_message,
                                   on_error=on_error,
                                   on_close=on_close)
        
        ws.run_forever()
    
    def _make_request(self, 
                     method: str, 
                     endpoint: str, 
                     **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            AGINARIException: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise AGINARIException("Authentication failed. Check your API key.")
                elif response.status_code == 403:
                    raise AGINARIException("Access forbidden. Check your permissions.")
                elif response.status_code == 429:
                    # Rate limited, wait and retry
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    raise AGINARIException("Rate limit exceeded. Please try again later.")
                else:
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise AGINARIException(f"Request failed: {str(e)}")
        
        raise AGINARIException("Maximum retries exceeded")

class AGINARIException(Exception):
    """Custom exception for AGI-NARI client errors"""
    pass

# Convenience functions for common operations
def quick_reason(query: str, api_key: str, organization_id: str = None) -> Dict[str, Any]:
    """
    Quick reasoning function for simple queries
    
    Args:
        query: Question to analyze
        api_key: API key for authentication
        organization_id: Optional organization ID
        
    Returns:
        Reasoning results
    """
    client = AGINARIClient(api_key=api_key, organization_id=organization_id)
    return client.agi_reason(query)

def quick_emotion_analysis(text: str, api_key: str, organization_id: str = None) -> Dict[str, Any]:
    """
    Quick emotional analysis function
    
    Args:
        text: Text to analyze
        api_key: API key for authentication
        organization_id: Optional organization ID
        
    Returns:
        Emotional analysis results
    """
    client = AGINARIClient(api_key=api_key, organization_id=organization_id)
    return client.analyze_emotion(text)

# Example usage
if __name__ == "__main__":
    # Example of how to use the SDK
    client = AGINARIClient(
        api_key="your_api_key_here",
        organization_id="your_org_id_here"
    )
    
    # Get system status
    status = client.get_system_status()
    print(f"System Status: {status}")
    
    # Perform AGI reasoning
    result = client.agi_reason(
        "What are the key trends in artificial intelligence for enterprise applications?",
        context={"domain": "technology", "focus": "enterprise"}
    )
    print(f"Reasoning Result: {result}")
    
    # Analyze emotions
    emotion_result = client.analyze_emotion(
        "I'm excited about the new AI capabilities but concerned about implementation complexity.",
        context="business"
    )
    print(f"Emotion Analysis: {emotion_result}")

