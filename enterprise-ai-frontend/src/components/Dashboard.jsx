import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Brain, 
  TrendingUp, 
  Shield, 
  Activity,
  Zap,
  BarChart3,
  Globe,
  Cpu,
  Database,
  RefreshCw,
  AlertTriangle
} from 'lucide-react';
import APIService from '../services/api';

const Dashboard = () => {
  const [metrics, setMetrics] = useState({
    totalUsers: 1247,
    activeUsers: 892,
    aiRequests: 15400,
    systemHealth: 99.8
  });
  
  const [liveMetrics, setLiveMetrics] = useState({
    activeUsers: 0,
    aiRequests: 0,
    systemLoad: 0,
    responseTime: 0
  });
  
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [aiServices, setAiServices] = useState([
    { name: 'NLP Service', status: 'healthy', load: 45 },
    { name: 'Vision Service', status: 'healthy', load: 62 },
    { name: 'Analytics Service', status: 'healthy', load: 38 },
    { name: 'Recommendation Service', status: 'healthy', load: 71 }
  ]);

  useEffect(() => {
    loadDashboardData();
    
    // Set up real-time updates
    const interval = setInterval(() => {
      updateLiveMetrics();
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const [health, analytics] = await Promise.all([
        APIService.getSystemHealth(),
        APIService.getAnalytics()
      ]);
      
      setSystemHealth(health);
      
      if (analytics) {
        setMetrics(prev => ({
          ...prev,
          ...analytics
        }));
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateLiveMetrics = async () => {
    try {
      const live = await APIService.getLiveMetrics();
      setLiveMetrics(live);
      
      // Update AI services with random load variations
      setAiServices(prev => prev.map(service => ({
        ...service,
        load: Math.max(10, Math.min(90, service.load + (Math.random() - 0.5) * 10))
      })));
    } catch (error) {
      console.error('Failed to update live metrics:', error);
    }
  };

  const MetricCard = ({ title, value, change, icon: Icon, color = "blue" }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {change && (
            <p className={`text-sm mt-1 ${change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
              {change}
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-${color}-50`}>
          <Icon className={`h-6 w-6 text-${color}-600`} />
        </div>
      </div>
    </div>
  );

  const ServiceCard = ({ service }) => (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-medium text-gray-900">{service.name}</h4>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          service.status === 'healthy' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          {service.status}
        </span>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Load</span>
          <span className="font-medium">{service.load.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full ${
              service.load > 80 ? 'bg-red-500' : 
              service.load > 60 ? 'bg-yellow-500' : 'bg-green-500'
            }`}
            style={{ width: `${service.load}%` }}
          ></div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-gray-600">Loading dashboard...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Welcome to your Enterprise AI System control center</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className={`flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            systemHealth?.overall === 'healthy' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            <Activity className="h-4 w-4 mr-1" />
            System {systemHealth?.overall || 'Unknown'}
          </div>
          <div className="flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
            <Zap className="h-4 w-4 mr-1" />
            AI Active
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Users"
          value={metrics.totalUsers.toLocaleString()}
          change="+12% from last month"
          icon={Users}
          color="blue"
        />
        <MetricCard
          title="Active Users"
          value={liveMetrics.activeUsers || metrics.activeUsers}
          change="+8% from yesterday"
          icon={Activity}
          color="green"
        />
        <MetricCard
          title="AI Requests"
          value={`${(liveMetrics.aiRequests || metrics.aiRequests / 1000).toFixed(1)}K`}
          change="+24% from last week"
          icon={Brain}
          color="purple"
        />
        <MetricCard
          title="System Health"
          value={`${metrics.systemHealth}%`}
          change="All systems operational"
          icon={Shield}
          color="emerald"
        />
      </div>

      {/* Live Metrics */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Live System Metrics</h2>
          <div className="flex items-center text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
            Live updates every 3 seconds
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <Cpu className="h-8 w-8 text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">System Load</p>
            <p className="text-xl font-bold text-gray-900">{liveMetrics.systemLoad?.toFixed(1)}%</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <Globe className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Response Time</p>
            <p className="text-xl font-bold text-gray-900">{liveMetrics.responseTime?.toFixed(0)}ms</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <Database className="h-8 w-8 text-purple-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Active Connections</p>
            <p className="text-xl font-bold text-gray-900">{liveMetrics.activeUsers}</p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <BarChart3 className="h-8 w-8 text-orange-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Requests/min</p>
            <p className="text-xl font-bold text-gray-900">{Math.floor(liveMetrics.aiRequests / 60)}</p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Services Status */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">AI Services Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {aiServices.map((service, index) => (
              <ServiceCard key={index} service={service} />
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          {/* System Overview */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">System Overview</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Backend</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  systemHealth?.backend ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {systemHealth?.backend ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">API Gateway</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  systemHealth?.gateway ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {systemHealth?.gateway ? 'Online' : 'Offline'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Database</span>
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Connected
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                <Users className="h-4 w-4 mr-2" />
                Add User
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                <Shield className="h-4 w-4 mr-2" />
                Manage Roles
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                <BarChart3 className="h-4 w-4 mr-2" />
                View Analytics
              </button>
              <button className="w-full flex items-center justify-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
                <Cpu className="h-4 w-4 mr-2" />
                Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

