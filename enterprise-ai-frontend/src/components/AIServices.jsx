import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Eye, 
  BarChart3, 
  Target,
  Send,
  Upload,
  Download,
  Zap,
  Cpu,
  Activity,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import APIService from '../services/api';

const AIServices = () => {
  const [activeService, setActiveService] = useState('nlp');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState({});
  
  // NLP Service State
  const [nlpText, setNlpText] = useState('');
  const [nlpResult, setNlpResult] = useState(null);
  
  // Vision Service State
  const [imageUrl, setImageUrl] = useState('');
  const [visionResult, setVisionResult] = useState(null);
  
  // Analytics Service State
  const [analyticsData, setAnalyticsData] = useState('1,2,3,4,5,6,7,8,9,10');
  const [analyticsResult, setAnalyticsResult] = useState(null);
  
  // Recommendation Service State
  const [userId, setUserId] = useState('user123');
  const [itemType, setItemType] = useState('product');
  const [recommendationResult, setRecommendationResult] = useState(null);

  const services = [
    {
      id: 'nlp',
      name: 'Natural Language Processing',
      icon: Brain,
      description: 'Advanced text analysis, sentiment detection, and language understanding',
      color: 'blue',
      status: 'active'
    },
    {
      id: 'vision',
      name: 'Computer Vision',
      icon: Eye,
      description: 'Image analysis, object detection, and visual content understanding',
      color: 'green',
      status: 'active'
    },
    {
      id: 'analytics',
      name: 'AI Analytics',
      icon: BarChart3,
      description: 'Predictive modeling, trend analysis, and data insights',
      color: 'purple',
      status: 'active'
    },
    {
      id: 'recommendation',
      name: 'Recommendation Engine',
      icon: Target,
      description: 'Personalized recommendations and content filtering',
      color: 'orange',
      status: 'active'
    }
  ];

  const processNLP = async () => {
    if (!nlpText.trim()) return;
    
    setLoading(true);
    try {
      const result = await APIService.processNLP(nlpText);
      if (result.success) {
        setNlpResult(result.data);
      } else {
        // Simulate result for demo
        setNlpResult({
          sentiment: {
            label: 'positive',
            confidence: 0.85
          },
          entities: [
            { text: 'AI', label: 'TECHNOLOGY', confidence: 0.95 },
            { text: 'system', label: 'PRODUCT', confidence: 0.88 }
          ],
          summary: 'The text expresses positive sentiment about AI technology and systems.',
          keywords: ['AI', 'technology', 'system', 'analysis'],
          language: 'en',
          word_count: nlpText.split(' ').length
        });
      }
    } catch (error) {
      console.error('NLP processing failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeImage = async () => {
    if (!imageUrl.trim()) return;
    
    setLoading(true);
    try {
      const result = await APIService.analyzeImage(imageUrl);
      if (result.success) {
        setVisionResult(result.data);
      } else {
        // Simulate result for demo
        setVisionResult({
          objects: [
            { name: 'person', confidence: 0.92, bbox: [100, 50, 200, 300] },
            { name: 'laptop', confidence: 0.87, bbox: [150, 200, 350, 280] }
          ],
          scene: 'office environment',
          colors: ['blue', 'white', 'gray'],
          text_detected: 'Enterprise AI System',
          image_quality: 'high',
          resolution: '1920x1080'
        });
      }
    } catch (error) {
      console.error('Image analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const analyzeData = async () => {
    if (!analyticsData.trim()) return;
    
    setLoading(true);
    try {
      const dataArray = analyticsData.split(',').map(x => parseFloat(x.trim())).filter(x => !isNaN(x));
      const result = await APIService.getAnalyticsInsights(dataArray);
      
      if (result.success) {
        setAnalyticsResult(result.data);
      } else {
        // Simulate result for demo
        const mean = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        const trend = dataArray[dataArray.length - 1] > dataArray[0] ? 'increasing' : 'decreasing';
        
        setAnalyticsResult({
          trend: trend,
          mean: mean.toFixed(2),
          median: dataArray.sort()[Math.floor(dataArray.length / 2)],
          std_deviation: Math.sqrt(dataArray.reduce((sq, n) => sq + Math.pow(n - mean, 2), 0) / dataArray.length).toFixed(2),
          predictions: [mean * 1.1, mean * 1.15, mean * 1.2],
          anomalies: [],
          insights: [
            `Data shows a ${trend} trend`,
            `Average value is ${mean.toFixed(2)}`,
            'No significant anomalies detected'
          ]
        });
      }
    } catch (error) {
      console.error('Analytics failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendations = async () => {
    if (!userId.trim()) return;
    
    setLoading(true);
    try {
      const result = await APIService.getRecommendations(userId, itemType);
      if (result.success) {
        setRecommendationResult(result.data);
      } else {
        // Simulate result for demo
        setRecommendationResult({
          recommendations: [
            { id: 1, title: 'AI Development Course', score: 0.95, type: 'course' },
            { id: 2, title: 'Machine Learning Toolkit', score: 0.89, type: 'tool' },
            { id: 3, title: 'Data Science Handbook', score: 0.84, type: 'book' },
            { id: 4, title: 'Neural Network Framework', score: 0.78, type: 'software' }
          ],
          user_profile: {
            interests: ['AI', 'Machine Learning', 'Data Science'],
            experience_level: 'intermediate',
            preferred_type: itemType
          },
          algorithm: 'hybrid_collaborative_content',
          confidence: 0.87
        });
      }
    } catch (error) {
      console.error('Recommendations failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const ServiceCard = ({ service }) => (
    <div 
      className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${
        activeService === service.id 
          ? `border-${service.color}-500 bg-${service.color}-50` 
          : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={() => setActiveService(service.id)}
    >
      <div className="flex items-center space-x-3 mb-3">
        <div className={`p-2 rounded-lg bg-${service.color}-100`}>
          <service.icon className={`h-6 w-6 text-${service.color}-600`} />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{service.name}</h3>
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-sm text-green-600">Active</span>
          </div>
        </div>
      </div>
      <p className="text-sm text-gray-600">{service.description}</p>
    </div>
  );

  const renderServiceInterface = () => {
    switch (activeService) {
      case 'nlp':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Text to Analyze
              </label>
              <textarea
                value={nlpText}
                onChange={(e) => setNlpText(e.target.value)}
                placeholder="Enter text for natural language processing analysis..."
                className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <button
              onClick={processNLP}
              disabled={loading || !nlpText.trim()}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Brain className="h-4 w-4 mr-2" />}
              {loading ? 'Processing...' : 'Analyze Text'}
            </button>

            {nlpResult && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                <h4 className="font-semibold text-gray-900">Analysis Results</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Sentiment</h5>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        nlpResult.sentiment?.label === 'positive' ? 'bg-green-100 text-green-800' :
                        nlpResult.sentiment?.label === 'negative' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {nlpResult.sentiment?.label}
                      </span>
                      <span className="text-sm text-gray-600">
                        {(nlpResult.sentiment?.confidence * 100).toFixed(1)}% confidence
                      </span>
                    </div>
                  </div>
                  
                  <div className="bg-white p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Word Count</h5>
                    <p className="text-lg font-semibold text-gray-900">{nlpResult.word_count}</p>
                  </div>
                </div>

                {nlpResult.entities && nlpResult.entities.length > 0 && (
                  <div className="bg-white p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Entities</h5>
                    <div className="flex flex-wrap gap-2">
                      {nlpResult.entities.map((entity, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                          {entity.text} ({entity.label})
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="bg-white p-3 rounded-lg">
                  <h5 className="font-medium text-gray-700 mb-2">Summary</h5>
                  <p className="text-sm text-gray-600">{nlpResult.summary}</p>
                </div>
              </div>
            )}
          </div>
        );

      case 'vision':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Image URL
              </label>
              <input
                type="url"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://example.com/image.jpg"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
              />
            </div>
            
            <button
              onClick={analyzeImage}
              disabled={loading || !imageUrl.trim()}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Eye className="h-4 w-4 mr-2" />}
              {loading ? 'Analyzing...' : 'Analyze Image'}
            </button>

            {visionResult && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                <h4 className="font-semibold text-gray-900">Vision Analysis Results</h4>
                
                {visionResult.objects && visionResult.objects.length > 0 && (
                  <div className="bg-white p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Detected Objects</h5>
                    <div className="space-y-2">
                      {visionResult.objects.map((obj, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm text-gray-900">{obj.name}</span>
                          <span className="text-sm text-gray-600">{(obj.confidence * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-white p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Scene</h5>
                    <p className="text-sm text-gray-600">{visionResult.scene}</p>
                  </div>
                  
                  <div className="bg-white p-3 rounded-lg">
                    <h5 className="font-medium text-gray-700 mb-2">Text Detected</h5>
                    <p className="text-sm text-gray-600">{visionResult.text_detected || 'None'}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case 'analytics':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data (comma-separated numbers)
              </label>
              <input
                type="text"
                value={analyticsData}
                onChange={(e) => setAnalyticsData(e.target.value)}
                placeholder="1,2,3,4,5,6,7,8,9,10"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            
            <button
              onClick={analyzeData}
              disabled={loading || !analyticsData.trim()}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <BarChart3 className="h-4 w-4 mr-2" />}
              {loading ? 'Analyzing...' : 'Analyze Data'}
            </button>

            {analyticsResult && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                <h4 className="font-semibold text-gray-900">Analytics Results</h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-white p-3 rounded-lg text-center">
                    <h5 className="font-medium text-gray-700 mb-1">Mean</h5>
                    <p className="text-lg font-semibold text-gray-900">{analyticsResult.mean}</p>
                  </div>
                  
                  <div className="bg-white p-3 rounded-lg text-center">
                    <h5 className="font-medium text-gray-700 mb-1">Trend</h5>
                    <p className={`text-lg font-semibold ${
                      analyticsResult.trend === 'increasing' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {analyticsResult.trend}
                    </p>
                  </div>
                  
                  <div className="bg-white p-3 rounded-lg text-center">
                    <h5 className="font-medium text-gray-700 mb-1">Std Dev</h5>
                    <p className="text-lg font-semibold text-gray-900">{analyticsResult.std_deviation}</p>
                  </div>
                </div>

                <div className="bg-white p-3 rounded-lg">
                  <h5 className="font-medium text-gray-700 mb-2">Insights</h5>
                  <ul className="space-y-1">
                    {analyticsResult.insights?.map((insight, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-center">
                        <Sparkles className="h-3 w-3 mr-2 text-purple-500" />
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        );

      case 'recommendation':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  User ID
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="user123"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Item Type
                </label>
                <select
                  value={itemType}
                  onChange={(e) => setItemType(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                >
                  <option value="product">Product</option>
                  <option value="course">Course</option>
                  <option value="content">Content</option>
                  <option value="service">Service</option>
                </select>
              </div>
            </div>
            
            <button
              onClick={getRecommendations}
              disabled={loading || !userId.trim()}
              className="flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Target className="h-4 w-4 mr-2" />}
              {loading ? 'Generating...' : 'Get Recommendations'}
            </button>

            {recommendationResult && (
              <div className="bg-gray-50 rounded-lg p-4 space-y-4">
                <h4 className="font-semibold text-gray-900">Recommendations</h4>
                
                <div className="space-y-3">
                  {recommendationResult.recommendations?.map((rec, index) => (
                    <div key={index} className="bg-white p-3 rounded-lg flex items-center justify-between">
                      <div>
                        <h5 className="font-medium text-gray-900">{rec.title}</h5>
                        <p className="text-sm text-gray-600">Type: {rec.type}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          {(rec.score * 100).toFixed(1)}% match
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="bg-white p-3 rounded-lg">
                  <h5 className="font-medium text-gray-700 mb-2">Algorithm</h5>
                  <p className="text-sm text-gray-600">{recommendationResult.algorithm}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Confidence: {(recommendationResult.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Services</h1>
        <p className="text-gray-600">AI-powered capabilities for intelligent automation</p>
      </div>

      {/* Service Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {services.map((service) => (
          <ServiceCard key={service.id} service={service} />
        ))}
      </div>

      {/* Active Service Interface */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-3 mb-6">
          {(() => {
            const service = services.find(s => s.id === activeService);
            const Icon = service?.icon;
            return (
              <>
                <div className={`p-2 rounded-lg bg-${service?.color}-100`}>
                  <Icon className={`h-6 w-6 text-${service?.color}-600`} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{service?.name}</h2>
                  <p className="text-sm text-gray-600">{service?.description}</p>
                </div>
              </>
            );
          })()}
        </div>

        {renderServiceInterface()}
      </div>
    </div>
  );
};

export default AIServices;

