/**
 * AGI-NARI Enterprise JavaScript SDK
 * Official JavaScript client library for integrating with the AGI-NARI system
 * 
 * @version 1.0.0
 * @author AGI-NARI Enterprise Team
 */

class AGINARIClient {
    /**
     * Initialize the AGI-NARI client
     * 
     * @param {Object} config - Configuration options
     * @param {string} config.baseUrl - Base URL for the AGI-NARI API
     * @param {string} config.apiKey - API key for authentication
     * @param {string} config.organizationId - Organization identifier
     * @param {number} config.timeout - Request timeout in milliseconds
     * @param {number} config.maxRetries - Maximum number of retry attempts
     */
    constructor(config = {}) {
        this.baseUrl = (config.baseUrl || 'https://api.agi-nari.com').replace(/\/$/, '');
        this.apiKey = config.apiKey;
        this.organizationId = config.organizationId;
        this.timeout = config.timeout || 30000;
        this.maxRetries = config.maxRetries || 3;
        
        // Default headers
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'User-Agent': 'AGI-NARI-JavaScript-SDK/1.0.0'
        };
        
        if (this.apiKey) {
            this.defaultHeaders['Authorization'] = `Bearer ${this.apiKey}`;
        }
        
        if (this.organizationId) {
            this.defaultHeaders['X-Organization-ID'] = this.organizationId;
        }
    }
    
    /**
     * Authenticate with email and password
     * 
     * @param {string} email - User email address
     * @param {string} password - User password
     * @returns {Promise<Object>} Authentication response
     */
    async authenticate(email, password) {
        const authData = {
            email: email,
            password: password,
            organization_id: this.organizationId
        };
        
        const response = await this._makeRequest('POST', '/api/v1/auth/login', authData);
        
        if (response.access_token) {
            this.apiKey = response.access_token;
            this.defaultHeaders['Authorization'] = `Bearer ${response.access_token}`;
        }
        
        return response;
    }
    
    /**
     * Get comprehensive system status and health metrics
     * 
     * @returns {Promise<Object>} System status information
     */
    async getSystemStatus() {
        return await this._makeRequest('GET', '/api/v1/system/status');
    }
    
    /**
     * Perform AGI reasoning on complex problems
     * 
     * @param {string} query - The question or problem to analyze
     * @param {Object} options - Reasoning options
     * @param {Object} options.context - Additional context for reasoning
     * @param {string} options.reasoningType - Type of reasoning
     * @param {string} options.outputFormat - Format of the output
     * @param {number} options.confidenceThreshold - Minimum confidence level
     * @returns {Promise<Object>} Reasoning results
     */
    async agiReason(query, options = {}) {
        const requestData = {
            query: query,
            context: options.context || {},
            reasoning_type: options.reasoningType || 'general',
            output_format: options.outputFormat || 'structured',
            confidence_threshold: options.confidenceThreshold || 0.7
        };
        
        return await this._makeRequest('POST', '/api/v1/agi/reason', requestData);
    }
    
    /**
     * Query the current consciousness state of the AGI system
     * 
     * @returns {Promise<Object>} Consciousness state information
     */
    async getConsciousnessState() {
        return await this._makeRequest('GET', '/api/v1/consciousness/state');
    }
    
    /**
     * Analyze emotional content and sentiment
     * 
     * @param {string} text - Text to analyze for emotional content
     * @param {Object} options - Analysis options
     * @param {string} options.context - Context of the text
     * @param {string} options.analysisDepth - Depth of analysis
     * @returns {Promise<Object>} Emotional analysis results
     */
    async analyzeEmotion(text, options = {}) {
        const requestData = {
            input_text: text,
            context: options.context || 'general',
            analysis_depth: options.analysisDepth || 'standard',
            include_empathy_response: true
        };
        
        return await this._makeRequest('POST', '/api/v1/emotion/analyze', requestData);
    }
    
    /**
     * Trigger NARI evolution for capability enhancement
     * 
     * @param {string} targetDomain - Domain to optimize
     * @param {Object} performanceTargets - Target performance metrics
     * @param {string} priority - Evolution priority
     * @returns {Promise<Object>} Evolution process information
     */
    async triggerNARIEvolution(targetDomain, performanceTargets, priority = 'normal') {
        const requestData = {
            evolution_type: 'capability_enhancement',
            target_domain: targetDomain,
            performance_metrics: performanceTargets,
            priority: priority
        };
        
        return await this._makeRequest('POST', '/api/v1/nari/evolve', requestData);
    }
    
    /**
     * Perform natural language processing tasks
     * 
     * @param {string} text - Text to process
     * @param {Array<string>} tasks - List of NLP tasks
     * @param {string} language - Language code
     * @returns {Promise<Object>} NLP processing results
     */
    async processNLP(text, tasks, language = 'en') {
        const requestData = {
            text: text,
            tasks: tasks,
            language: language,
            domain_specific: true
        };
        
        return await this._makeRequest('POST', '/api/v1/nlp/process', requestData);
    }
    
    /**
     * Analyze images and visual content
     * 
     * @param {string} imageUrl - URL of the image to analyze
     * @param {string} analysisType - Type of analysis
     * @returns {Promise<Object>} Vision analysis results
     */
    async analyzeVision(imageUrl, analysisType = 'comprehensive') {
        const requestData = {
            image_url: imageUrl,
            analysis_type: analysisType,
            extract_text: true,
            identify_objects: true,
            business_context: true
        };
        
        return await this._makeRequest('POST', '/api/v1/vision/analyze', requestData);
    }
    
    /**
     * Record important business data on the blockchain
     * 
     * @param {Object} transactionData - Data to record
     * @param {string} transactionType - Type of transaction
     * @returns {Promise<Object>} Blockchain transaction information
     */
    async recordBlockchainTransaction(transactionData, transactionType = 'business_decision') {
        const requestData = {
            transaction_type: transactionType,
            data: transactionData,
            metadata: {
                timestamp: new Date().toISOString(),
                organization: this.organizationId
            }
        };
        
        return await this._makeRequest('POST', '/api/v1/blockchain/record', requestData);
    }
    
    /**
     * Perform advanced analytics queries
     * 
     * @param {string} query - Analytics query in natural language
     * @param {Array<string>} dataSources - List of data sources
     * @param {string} analysisType - Type of analysis
     * @returns {Promise<Object>} Analytics results
     */
    async queryAnalytics(query, dataSources, analysisType = 'comprehensive') {
        const requestData = {
            query: query,
            data_sources: dataSources,
            analysis_type: analysisType,
            visualization: true
        };
        
        return await this._makeRequest('POST', '/api/v1/analytics/query', requestData);
    }
    
    /**
     * Create a webhook for real-time notifications
     * 
     * @param {string} url - Webhook URL
     * @param {Array<string>} events - List of events to subscribe to
     * @param {string} secret - Optional secret for verification
     * @returns {Promise<Object>} Webhook configuration
     */
    async createWebhook(url, events, secret = null) {
        const requestData = {
            url: url,
            events: events,
            secret: secret,
            retry_policy: {
                max_retries: 3,
                retry_delay: 5000
            }
        };
        
        return await this._makeRequest('POST', '/api/v1/webhooks/register', requestData);
    }
    
    /**
     * Stream real-time consciousness state updates
     * 
     * @param {Function} callback - Function to call with updates
     * @returns {WebSocket} WebSocket connection
     */
    streamConsciousness(callback) {
        const wsUrl = this.baseUrl.replace('https://', 'wss://').replace('http://', 'ws://');
        const ws = new WebSocket(`${wsUrl}/v1/realtime`);
        
        ws.onopen = () => {
            // Authenticate the connection
            ws.send(JSON.stringify({
                type: 'auth',
                token: this.apiKey,
                organization_id: this.organizationId
            }));
            
            // Subscribe to consciousness updates
            ws.send(JSON.stringify({
                type: 'subscribe',
                channel: 'consciousness_state',
                filters: {
                    consciousness_level_threshold: 0.5,
                    state_changes_only: true
                }
            }));
        };
        
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                callback(data);
            } catch (error) {
                console.error('Error processing consciousness stream:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('Consciousness stream closed');
        };
        
        return ws;
    }
    
    /**
     * Make HTTP request with retry logic and error handling
     * 
     * @private
     * @param {string} method - HTTP method
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request data
     * @returns {Promise<Object>} Response data
     */
    async _makeRequest(method, endpoint, data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const options = {
                    method: method,
                    headers: { ...this.defaultHeaders },
                    signal: AbortSignal.timeout(this.timeout)
                };
                
                if (data && (method === 'POST' || method === 'PUT')) {
                    options.body = JSON.stringify(data);
                }
                
                const response = await fetch(url, options);
                
                if (response.ok) {
                    return await response.json();
                } else if (response.status === 401) {
                    throw new AGINARIError('Authentication failed. Check your API key.');
                } else if (response.status === 403) {
                    throw new AGINARIError('Access forbidden. Check your permissions.');
                } else if (response.status === 429) {
                    // Rate limited, wait and retry
                    if (attempt < this.maxRetries) {
                        await this._sleep(Math.pow(2, attempt) * 1000);
                        continue;
                    }
                    throw new AGINARIError('Rate limit exceeded. Please try again later.');
                } else {
                    throw new AGINARIError(`Request failed with status ${response.status}`);
                }
                
            } catch (error) {
                if (attempt < this.maxRetries && !(error instanceof AGINARIError)) {
                    await this._sleep(Math.pow(2, attempt) * 1000);
                    continue;
                }
                throw error instanceof AGINARIError ? error : new AGINARIError(`Request failed: ${error.message}`);
            }
        }
        
        throw new AGINARIError('Maximum retries exceeded');
    }
    
    /**
     * Sleep for specified milliseconds
     * 
     * @private
     * @param {number} ms - Milliseconds to sleep
     * @returns {Promise<void>}
     */
    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

/**
 * Custom error class for AGI-NARI client errors
 */
class AGINARIError extends Error {
    constructor(message) {
        super(message);
        this.name = 'AGINARIError';
    }
}

// Convenience functions for common operations

/**
 * Quick reasoning function for simple queries
 * 
 * @param {string} query - Question to analyze
 * @param {string} apiKey - API key for authentication
 * @param {string} organizationId - Optional organization ID
 * @returns {Promise<Object>} Reasoning results
 */
async function quickReason(query, apiKey, organizationId = null) {
    const client = new AGINARIClient({ apiKey, organizationId });
    return await client.agiReason(query);
}

/**
 * Quick emotional analysis function
 * 
 * @param {string} text - Text to analyze
 * @param {string} apiKey - API key for authentication
 * @param {string} organizationId - Optional organization ID
 * @returns {Promise<Object>} Emotional analysis results
 */
async function quickEmotionAnalysis(text, apiKey, organizationId = null) {
    const client = new AGINARIClient({ apiKey, organizationId });
    return await client.analyzeEmotion(text);
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    // Node.js
    module.exports = {
        AGINARIClient,
        AGINARIError,
        quickReason,
        quickEmotionAnalysis
    };
} else if (typeof window !== 'undefined') {
    // Browser
    window.AGINARIClient = AGINARIClient;
    window.AGINARIError = AGINARIError;
    window.quickReason = quickReason;
    window.quickEmotionAnalysis = quickEmotionAnalysis;
}

// Example usage
if (typeof window === 'undefined' && require.main === module) {
    // Example for Node.js environment
    (async () => {
        const client = new AGINARIClient({
            apiKey: 'your_api_key_here',
            organizationId: 'your_org_id_here'
        });
        
        try {
            // Get system status
            const status = await client.getSystemStatus();
            console.log('System Status:', status);
            
            // Perform AGI reasoning
            const result = await client.agiReason(
                'What are the key trends in artificial intelligence for enterprise applications?',
                { context: { domain: 'technology', focus: 'enterprise' } }
            );
            console.log('Reasoning Result:', result);
            
            // Analyze emotions
            const emotionResult = await client.analyzeEmotion(
                "I'm excited about the new AI capabilities but concerned about implementation complexity.",
                { context: 'business' }
            );
            console.log('Emotion Analysis:', emotionResult);
            
        } catch (error) {
            console.error('Error:', error.message);
        }
    })();
}

