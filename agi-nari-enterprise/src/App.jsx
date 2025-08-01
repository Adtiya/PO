import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Alert, AlertDescription } from '@/components/ui/alert.jsx'
import { Brain, Users, Building2, Shield, Zap, BarChart3, Settings, LogOut, User, CheckCircle, Clock, AlertTriangle } from 'lucide-react'
import './App.css'

// Authentication Context
const AuthContext = React.createContext()

// User roles and permissions
const ROLES = {
  'super_admin': {
    name: 'Super Administrator',
    permissions: ['all'],
    color: 'bg-red-500'
  },
  'enterprise_admin': {
    name: 'Enterprise Administrator', 
    permissions: ['manage_users', 'view_analytics', 'configure_system', 'access_agi'],
    color: 'bg-purple-500'
  },
  'department_head': {
    name: 'Department Head',
    permissions: ['manage_team', 'view_analytics', 'access_agi', 'approve_requests'],
    color: 'bg-blue-500'
  },
  'data_scientist': {
    name: 'Data Scientist',
    permissions: ['access_agi', 'view_analytics', 'run_experiments'],
    color: 'bg-green-500'
  },
  'business_analyst': {
    name: 'Business Analyst',
    permissions: ['view_analytics', 'create_reports', 'access_insights'],
    color: 'bg-yellow-500'
  },
  'end_user': {
    name: 'End User',
    permissions: ['basic_access', 'submit_requests'],
    color: 'bg-gray-500'
  }
}

// Login Component
function LoginPage({ onLogin }) {
  const [credentials, setCredentials] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const demoUsers = [
    { email: 'admin@company.com', password: 'admin123', role: 'super_admin', name: 'Sarah Johnson', department: 'IT Administration' },
    { email: 'dept.head@company.com', password: 'dept123', role: 'department_head', name: 'Michael Chen', department: 'Data Science' },
    { email: 'scientist@company.com', password: 'sci123', role: 'data_scientist', name: 'Dr. Emily Rodriguez', department: 'AI Research' },
    { email: 'analyst@company.com', password: 'analyst123', role: 'business_analyst', name: 'David Kim', department: 'Business Intelligence' },
    { email: 'user@company.com', password: 'user123', role: 'end_user', name: 'Lisa Thompson', department: 'Marketing' }
  ]

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    // Simulate API call
    setTimeout(() => {
      const user = demoUsers.find(u => u.email === credentials.email && u.password === credentials.password)
      if (user) {
        onLogin(user)
      } else {
        setError('Invalid credentials')
      }
      setLoading(false)
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-white/10 backdrop-blur-lg border-white/20">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Brain className="h-12 w-12 text-blue-400" />
          </div>
          <CardTitle className="text-2xl text-white">AGI-NARI Enterprise</CardTitle>
          <CardDescription className="text-gray-300">
            Advanced AI Platform for Enterprise
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-white">Email</Label>
              <Input
                id="email"
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials({...credentials, email: e.target.value})}
                className="bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                placeholder="Enter your email"
                required
              />
            </div>
            <div>
              <Label htmlFor="password" className="text-white">Password</Label>
              <Input
                id="password"
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                className="bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                placeholder="Enter your password"
                required
              />
            </div>
            {error && (
              <Alert className="bg-red-500/20 border-red-500/50">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-red-200">{error}</AlertDescription>
              </Alert>
            )}
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
          </form>
          
          <div className="mt-6 p-4 bg-black/20 rounded-lg">
            <h4 className="text-sm font-medium text-white mb-2">Demo Accounts:</h4>
            <div className="space-y-1 text-xs text-gray-300">
              {demoUsers.map((user, idx) => (
                <div key={idx} className="flex justify-between">
                  <span>{user.email}</span>
                  <span>{user.password}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Dashboard Header
function DashboardHeader({ user, onLogout }) {
  return (
    <header className="bg-white shadow-sm border-b px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Brain className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-xl font-bold text-gray-900">AGI-NARI Enterprise</h1>
            <p className="text-sm text-gray-500">Advanced AI Platform</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-900">{user.name}</p>
            <p className="text-xs text-gray-500">{user.department}</p>
          </div>
          <Badge className={`${ROLES[user.role].color} text-white`}>
            {ROLES[user.role].name}
          </Badge>
          <Button variant="outline" size="sm" onClick={onLogout}>
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </Button>
        </div>
      </div>
    </header>
  )
}

// Dashboard Overview
function DashboardOverview({ user }) {
  const [metrics, setMetrics] = useState({
    agiCapability: 78.5,
    activeUsers: 1247,
    tasksCompleted: 15420,
    systemHealth: 98.2
  })

  const hasPermission = (permission) => {
    return ROLES[user.role].permissions.includes('all') || ROLES[user.role].permissions.includes(permission)
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AGI Capability</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.agiCapability}%</div>
            <p className="text-xs text-muted-foreground">+2.1% from last month</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.activeUsers.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">+12% from last week</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tasks Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.tasksCompleted.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">+8.2% from yesterday</p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.systemHealth}%</div>
            <p className="text-xs text-muted-foreground">All systems operational</p>
          </CardContent>
        </Card>
      </div>

      {hasPermission('access_agi') && (
        <Card>
          <CardHeader>
            <CardTitle>AGI Core Status</CardTitle>
            <CardDescription>Real-time artificial general intelligence metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Consciousness Level</Label>
                <div className="text-2xl font-bold text-blue-600">74.2%</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: '74.2%'}}></div>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Reasoning Capability</Label>
                <div className="text-2xl font-bold text-green-600">89.1%</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: '89.1%'}}></div>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Learning Rate</Label>
                <div className="text-2xl font-bold text-purple-600">92.7%</div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-purple-600 h-2 rounded-full" style={{width: '92.7%'}}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// User Management Component
function UserManagement({ user }) {
  const [users, setUsers] = useState([
    { id: 1, name: 'Sarah Johnson', email: 'admin@company.com', role: 'super_admin', status: 'active', lastLogin: '2025-01-31 09:15' },
    { id: 2, name: 'Michael Chen', email: 'dept.head@company.com', role: 'department_head', status: 'active', lastLogin: '2025-01-31 08:45' },
    { id: 3, name: 'Dr. Emily Rodriguez', email: 'scientist@company.com', role: 'data_scientist', status: 'active', lastLogin: '2025-01-30 16:30' },
    { id: 4, name: 'David Kim', email: 'analyst@company.com', role: 'business_analyst', status: 'active', lastLogin: '2025-01-30 14:20' },
    { id: 5, name: 'Lisa Thompson', email: 'user@company.com', role: 'end_user', status: 'pending', lastLogin: 'Never' }
  ])

  const hasPermission = (permission) => {
    return ROLES[user.role].permissions.includes('all') || ROLES[user.role].permissions.includes(permission)
  }

  if (!hasPermission('manage_users')) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            <Shield className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>You don't have permission to access user management.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">User Management</h2>
        <Button>
          <User className="h-4 w-4 mr-2" />
          Add New User
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Enterprise Users</CardTitle>
          <CardDescription>Manage user accounts and permissions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {users.map((u) => (
              <div key={u.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                    <User className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium">{u.name}</p>
                    <p className="text-sm text-gray-500">{u.email}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <Badge className={`${ROLES[u.role].color} text-white`}>
                    {ROLES[u.role].name}
                  </Badge>
                  <Badge variant={u.status === 'active' ? 'default' : 'secondary'}>
                    {u.status}
                  </Badge>
                  <div className="text-sm text-gray-500">
                    Last login: {u.lastLogin}
                  </div>
                  <Button variant="outline" size="sm">
                    Edit
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Analytics Dashboard
function Analytics({ user }) {
  const hasPermission = (permission) => {
    return ROLES[user.role].permissions.includes('all') || ROLES[user.role].permissions.includes(permission)
  }

  if (!hasPermission('view_analytics')) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-gray-500">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>You don't have permission to access analytics.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Analytics & Insights</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>AGI Performance Trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">Performance Chart Placeholder</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>User Engagement</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">Engagement Chart Placeholder</p>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Task Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span>Data Analysis</span>
                <span className="font-medium">45%</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Content Generation</span>
                <span className="font-medium">30%</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Decision Support</span>
                <span className="font-medium">25%</span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>System Resources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">CPU Usage</span>
                  <span className="text-sm">67%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{width: '67%'}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Memory Usage</span>
                  <span className="text-sm">82%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{width: '82%'}}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm">Storage Usage</span>
                  <span className="text-sm">45%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-yellow-600 h-2 rounded-full" style={{width: '45%'}}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// Main Dashboard Component
function Dashboard({ user, onLogout }) {
  const [activeTab, setActiveTab] = useState('overview')

  const hasPermission = (permission) => {
    return ROLES[user.role].permissions.includes('all') || ROLES[user.role].permissions.includes(permission)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <DashboardHeader user={user} onLogout={onLogout} />
      
      <div className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="users" disabled={!hasPermission('manage_users')}>Users</TabsTrigger>
            <TabsTrigger value="analytics" disabled={!hasPermission('view_analytics')}>Analytics</TabsTrigger>
            <TabsTrigger value="settings" disabled={!hasPermission('configure_system')}>Settings</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview">
            <DashboardOverview user={user} />
          </TabsContent>
          
          <TabsContent value="users">
            <UserManagement user={user} />
          </TabsContent>
          
          <TabsContent value="analytics">
            <Analytics user={user} />
          </TabsContent>
          
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>System Settings</CardTitle>
                <CardDescription>Configure AGI-NARI Enterprise settings</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-500">Settings panel coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

// Main App Component
function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const savedUser = localStorage.getItem('agi_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
    setLoading(false)
  }, [])

  const handleLogin = (userData) => {
    setUser(userData)
    localStorage.setItem('agi_user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('agi_user')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <Brain className="h-12 w-12 mx-auto mb-4 animate-pulse" />
          <p>Loading AGI-NARI Enterprise...</p>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div className="App">
        {!user ? (
          <LoginPage onLogin={handleLogin} />
        ) : (
          <Dashboard user={user} onLogout={handleLogout} />
        )}
      </div>
    </Router>
  )
}

export default App

