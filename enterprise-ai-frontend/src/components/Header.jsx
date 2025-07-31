import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  Search, 
  Bell, 
  Sun, 
  Moon, 
  User, 
  LogOut, 
  Settings, 
  Menu,
  ChevronDown,
  Activity,
  Shield,
  Zap,
  Globe
} from 'lucide-react'

const Header = ({ 
  currentUser, 
  darkMode, 
  toggleDarkMode, 
  onLogout, 
  sidebarOpen, 
  toggleSidebar 
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showNotifications, setShowNotifications] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const notifications = [
    {
      id: 1,
      title: 'System Update',
      message: 'New AI features are now available',
      time: '2 minutes ago',
      type: 'info',
      unread: true
    },
    {
      id: 2,
      title: 'Security Alert',
      message: 'Successful login from new device',
      time: '15 minutes ago',
      type: 'warning',
      unread: true
    },
    {
      id: 3,
      title: 'Performance',
      message: 'System performance is optimal',
      time: '1 hour ago',
      type: 'success',
      unread: false
    }
  ]

  const unreadCount = notifications.filter(n => n.unread).length

  const quickSearchSuggestions = [
    'User Management',
    'Role Permissions',
    'AI Analytics',
    'System Settings',
    'Security Logs'
  ]

  return (
    <header className="sticky top-0 z-40 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-6">
        {/* Left Section */}
        <div className="flex items-center space-x-4">
          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            className="lg:hidden w-8 h-8 p-0"
          >
            <Menu className="w-4 h-4" />
          </Button>

          {/* Search */}
          <div className="relative hidden md:block">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search anything..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 w-64 lg:w-80 h-9 bg-muted/50 border-0 focus:bg-background focus:ring-1 focus:ring-ring"
            />
            
            {/* Search Suggestions */}
            {searchQuery && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="absolute top-full mt-2 w-full bg-popover border border-border rounded-lg shadow-lg z-50"
              >
                <div className="p-2">
                  <div className="text-xs font-medium text-muted-foreground mb-2 px-2">
                    Quick suggestions
                  </div>
                  {quickSearchSuggestions
                    .filter(suggestion => 
                      suggestion.toLowerCase().includes(searchQuery.toLowerCase())
                    )
                    .slice(0, 5)
                    .map((suggestion, index) => (
                      <button
                        key={index}
                        className="w-full text-left px-2 py-2 text-sm hover:bg-muted rounded-md transition-colors"
                        onClick={() => {
                          setSearchQuery(suggestion)
                          // Handle search action
                        }}
                      >
                        {suggestion}
                      </button>
                    ))
                  }
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {/* Center Section - System Status */}
        <div className="hidden lg:flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-green-50 dark:bg-green-950/30 rounded-full border border-green-200 dark:border-green-800">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs font-medium text-green-700 dark:text-green-300">
              All Systems Operational
            </span>
          </div>
          
          <div className="flex items-center space-x-1 text-xs text-muted-foreground">
            <Activity className="w-3 h-3" />
            <span>99.9% Uptime</span>
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-2">
          {/* Quick Stats */}
          <div className="hidden xl:flex items-center space-x-4 mr-4">
            <div className="flex items-center space-x-1 text-xs">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span className="text-muted-foreground">892 Active Users</span>
            </div>
            <div className="flex items-center space-x-1 text-xs">
              <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
              <span className="text-muted-foreground">15.4K AI Requests</span>
            </div>
          </div>

          {/* Notifications */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowNotifications(!showNotifications)}
              className="w-8 h-8 p-0 relative"
            >
              <Bell className="w-4 h-4" />
              {unreadCount > 0 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
                >
                  {unreadCount}
                </motion.div>
              )}
            </Button>

            <AnimatePresence>
              {showNotifications && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  className="absolute right-0 top-full mt-2 w-80 bg-popover border border-border rounded-lg shadow-lg z-50"
                >
                  <div className="p-4 border-b border-border">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">Notifications</h3>
                      <Badge variant="secondary" className="text-xs">
                        {unreadCount} new
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="max-h-80 overflow-y-auto">
                    {notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={`p-4 border-b border-border last:border-b-0 hover:bg-muted/50 transition-colors ${
                          notification.unread ? 'bg-blue-50/50 dark:bg-blue-950/20' : ''
                        }`}
                      >
                        <div className="flex items-start space-x-3">
                          <div className={`w-2 h-2 rounded-full mt-2 ${
                            notification.type === 'info' ? 'bg-blue-500' :
                            notification.type === 'warning' ? 'bg-yellow-500' :
                            'bg-green-500'
                          }`} />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium">{notification.title}</p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {notification.message}
                            </p>
                            <p className="text-xs text-muted-foreground mt-2">
                              {notification.time}
                            </p>
                          </div>
                          {notification.unread && (
                            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="p-3 border-t border-border">
                    <Button variant="ghost" size="sm" className="w-full text-xs">
                      View All Notifications
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Dark Mode Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleDarkMode}
            className="w-8 h-8 p-0"
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>

          {/* User Menu */}
          <div className="relative">
            <Button
              variant="ghost"
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 h-8 px-2"
            >
              <div className="w-6 h-6 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-medium">
                  {currentUser?.firstName?.[0]}{currentUser?.lastName?.[0]}
                </span>
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium leading-none">
                  {currentUser?.firstName} {currentUser?.lastName}
                </p>
                <p className="text-xs text-muted-foreground">
                  {currentUser?.role}
                </p>
              </div>
              <ChevronDown className="w-3 h-3" />
            </Button>

            <AnimatePresence>
              {showUserMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -10, scale: 0.95 }}
                  className="absolute right-0 top-full mt-2 w-56 bg-popover border border-border rounded-lg shadow-lg z-50"
                >
                  <div className="p-3 border-b border-border">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-medium">
                          {currentUser?.firstName?.[0]}{currentUser?.lastName?.[0]}
                        </span>
                      </div>
                      <div>
                        <p className="font-medium text-sm">
                          {currentUser?.firstName} {currentUser?.lastName}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {currentUser?.email}
                        </p>
                        <div className="flex items-center space-x-1 mt-1">
                          <Shield className="w-3 h-3 text-green-500" />
                          <span className="text-xs text-green-600 font-medium">
                            {currentUser?.role}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-1">
                    <button className="w-full flex items-center space-x-2 px-3 py-2 text-sm hover:bg-muted rounded-md transition-colors">
                      <User className="w-4 h-4" />
                      <span>Profile Settings</span>
                    </button>
                    <button className="w-full flex items-center space-x-2 px-3 py-2 text-sm hover:bg-muted rounded-md transition-colors">
                      <Settings className="w-4 h-4" />
                      <span>Preferences</span>
                    </button>
                    <button className="w-full flex items-center space-x-2 px-3 py-2 text-sm hover:bg-muted rounded-md transition-colors">
                      <Shield className="w-4 h-4" />
                      <span>Security</span>
                    </button>
                  </div>

                  <div className="p-1 border-t border-border">
                    <button
                      onClick={onLogout}
                      className="w-full flex items-center space-x-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-md transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Mobile Search */}
      <div className="md:hidden px-4 pb-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 h-9 bg-muted/50 border-0"
          />
        </div>
      </div>

      {/* Click outside handlers */}
      {(showUserMenu || showNotifications) && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => {
            setShowUserMenu(false)
            setShowNotifications(false)
          }}
        />
      )}
    </header>
  )
}

export default Header

