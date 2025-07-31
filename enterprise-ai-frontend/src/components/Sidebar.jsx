import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { 
  LayoutDashboard,
  Users,
  Shield,
  BarChart3,
  Brain,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Activity,
  Bell,
  Search,
  FileText,
  Globe,
  Zap
} from 'lucide-react'

const Sidebar = ({ isOpen, onToggle, currentUser }) => {
  const location = useLocation()
  const [hoveredItem, setHoveredItem] = useState(null)

  const navigationItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      path: '/dashboard',
      badge: null,
      description: 'System overview and metrics'
    },
    {
      id: 'users',
      label: 'User Management',
      icon: Users,
      path: '/users',
      badge: '1.2K',
      description: 'Manage users and profiles'
    },
    {
      id: 'roles',
      label: 'Role Management',
      icon: Shield,
      path: '/roles',
      badge: null,
      description: 'Configure roles and permissions'
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      path: '/analytics',
      badge: 'New',
      description: 'Advanced analytics and insights'
    },
    {
      id: 'ai-services',
      label: 'AI Services',
      icon: Brain,
      path: '/ai-services',
      badge: 'AI',
      description: 'AI-powered services and tools'
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      path: '/settings',
      badge: null,
      description: 'System configuration'
    }
  ]

  const quickActions = [
    { icon: Search, label: 'Search', color: 'text-blue-500' },
    { icon: Bell, label: 'Notifications', color: 'text-yellow-500' },
    { icon: FileText, label: 'Documents', color: 'text-green-500' },
    { icon: Activity, label: 'Monitoring', color: 'text-purple-500' }
  ]

  const isActive = (path) => location.pathname === path

  return (
    <>
      {/* Sidebar */}
      <motion.div
        initial={false}
        animate={{ 
          width: isOpen ? 256 : 64,
          transition: { duration: 0.3, ease: "easeInOut" }
        }}
        className="fixed left-0 top-0 h-full bg-card border-r border-border z-50 flex flex-col"
      >
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <AnimatePresence mode="wait">
              {isOpen ? (
                <motion.div
                  key="expanded"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="flex items-center space-x-3"
                >
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Brain className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-sm">Enterprise AI</h2>
                    <p className="text-xs text-muted-foreground">System</p>
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="collapsed"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mx-auto"
                >
                  <Brain className="w-4 h-4 text-white" />
                </motion.div>
              )}
            </AnimatePresence>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
              className="w-8 h-8 p-0 hover:bg-muted"
            >
              {isOpen ? <ChevronLeft className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-4">
          <nav className="space-y-1 px-2">
            {navigationItems.map((item) => {
              const Icon = item.icon
              const active = isActive(item.path)
              
              return (
                <Link key={item.id} to={item.path}>
                  <motion.div
                    className={`relative flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                      active 
                        ? 'bg-primary text-primary-foreground shadow-sm' 
                        : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                    }`}
                    onHoverStart={() => setHoveredItem(item.id)}
                    onHoverEnd={() => setHoveredItem(null)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Icon className={`w-5 h-5 ${active ? 'text-primary-foreground' : ''}`} />
                    
                    <AnimatePresence>
                      {isOpen && (
                        <motion.div
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -10 }}
                          transition={{ duration: 0.2 }}
                          className="flex-1 flex items-center justify-between"
                        >
                          <span className="font-medium text-sm">{item.label}</span>
                          {item.badge && (
                            <Badge 
                              variant={item.badge === 'AI' ? 'default' : 'secondary'} 
                              className={`text-xs ${
                                item.badge === 'AI' ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white' :
                                item.badge === 'New' ? 'bg-green-500 text-white' : ''
                              }`}
                            >
                              {item.badge}
                            </Badge>
                          )}
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Active indicator */}
                    {active && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute left-0 top-0 bottom-0 w-1 bg-primary-foreground rounded-r-full"
                        initial={false}
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                      />
                    )}

                    {/* Tooltip for collapsed state */}
                    {!isOpen && hoveredItem === item.id && (
                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        className="absolute left-full ml-2 px-3 py-2 bg-popover text-popover-foreground rounded-lg shadow-lg border border-border z-50 whitespace-nowrap"
                      >
                        <div className="font-medium text-sm">{item.label}</div>
                        <div className="text-xs text-muted-foreground mt-1">{item.description}</div>
                      </motion.div>
                    )}
                  </motion.div>
                </Link>
              )
            })}
          </nav>

          {/* Quick Actions */}
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="mt-8 px-4"
            >
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Quick Actions
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {quickActions.map((action, index) => {
                  const Icon = action.icon
                  return (
                    <motion.button
                      key={index}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="flex flex-col items-center justify-center p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors group"
                    >
                      <Icon className={`w-4 h-4 ${action.color} mb-1`} />
                      <span className="text-xs font-medium">{action.label}</span>
                    </motion.button>
                  )
                })}
              </div>
            </motion.div>
          )}
        </div>

        {/* User Info */}
        <div className="p-4 border-t border-border">
          <AnimatePresence mode="wait">
            {isOpen ? (
              <motion.div
                key="user-expanded"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.2 }}
                className="flex items-center space-x-3"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {currentUser?.firstName?.[0]}{currentUser?.lastName?.[0]}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {currentUser?.firstName} {currentUser?.lastName}
                  </p>
                  <p className="text-xs text-muted-foreground truncate">
                    {currentUser?.role}
                  </p>
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="user-collapsed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="flex justify-center"
              >
                <div className="w-8 h-8 bg-gradient-to-br from-green-400 to-blue-500 rounded-full flex items-center justify-center relative">
                  <span className="text-white text-sm font-medium">
                    {currentUser?.firstName?.[0]}{currentUser?.lastName?.[0]}
                  </span>
                  <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-card"></div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Status Indicator */}
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="px-4 pb-4"
          >
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">System Status</span>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-green-600 font-medium">Operational</span>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>

      {/* Overlay for mobile */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 lg:hidden"
            onClick={onToggle}
          />
        )}
      </AnimatePresence>
    </>
  )
}

export default Sidebar

