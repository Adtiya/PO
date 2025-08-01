import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Switch } from '@/components/ui/switch.jsx'
import { 
  Shield, 
  Plus, 
  Edit, 
  Trash2, 
  Users, 
  Lock, 
  Unlock,
  CheckCircle,
  XCircle,
  Settings,
  Eye,
  FileText,
  Database,
  Activity
} from 'lucide-react'

const RoleManagement = () => {
  const [roles, setRoles] = useState([
    {
      id: 1,
      name: 'Admin',
      description: 'Full system access with all permissions',
      userCount: 3,
      permissions: {
        'users.read': true,
        'users.write': true,
        'users.delete': true,
        'roles.read': true,
        'roles.write': true,
        'roles.delete': true,
        'permissions.read': true,
        'permissions.write': true,
        'analytics.read': true,
        'analytics.write': true,
        'system.read': true,
        'system.write': true
      },
      color: 'purple',
      createdAt: '2024-01-01'
    },
    {
      id: 2,
      name: 'Manager',
      description: 'Department-level management access',
      userCount: 8,
      permissions: {
        'users.read': true,
        'users.write': true,
        'users.delete': false,
        'roles.read': true,
        'roles.write': false,
        'roles.delete': false,
        'permissions.read': true,
        'permissions.write': false,
        'analytics.read': true,
        'analytics.write': false,
        'system.read': true,
        'system.write': false
      },
      color: 'blue',
      createdAt: '2024-01-01'
    },
    {
      id: 3,
      name: 'Analyst',
      description: 'Data analysis and reporting access',
      userCount: 15,
      permissions: {
        'users.read': true,
        'users.write': false,
        'users.delete': false,
        'roles.read': true,
        'roles.write': false,
        'roles.delete': false,
        'permissions.read': false,
        'permissions.write': false,
        'analytics.read': true,
        'analytics.write': true,
        'system.read': true,
        'system.write': false
      },
      color: 'orange',
      createdAt: '2024-01-01'
    },
    {
      id: 4,
      name: 'User',
      description: 'Basic user access with limited permissions',
      userCount: 42,
      permissions: {
        'users.read': false,
        'users.write': false,
        'users.delete': false,
        'roles.read': false,
        'roles.write': false,
        'roles.delete': false,
        'permissions.read': false,
        'permissions.write': false,
        'analytics.read': false,
        'analytics.write': false,
        'system.read': true,
        'system.write': false
      },
      color: 'gray',
      createdAt: '2024-01-01'
    }
  ])

  const permissionCategories = {
    'User Management': ['users.read', 'users.write', 'users.delete'],
    'Role Management': ['roles.read', 'roles.write', 'roles.delete'],
    'Permission Management': ['permissions.read', 'permissions.write'],
    'Analytics': ['analytics.read', 'analytics.write'],
    'System': ['system.read', 'system.write']
  }

  const permissionLabels = {
    'users.read': 'View Users',
    'users.write': 'Create/Edit Users',
    'users.delete': 'Delete Users',
    'roles.read': 'View Roles',
    'roles.write': 'Create/Edit Roles',
    'roles.delete': 'Delete Roles',
    'permissions.read': 'View Permissions',
    'permissions.write': 'Manage Permissions',
    'analytics.read': 'View Analytics',
    'analytics.write': 'Manage Analytics',
    'system.read': 'View System Info',
    'system.write': 'Manage System'
  }

  const getColorClasses = (color) => {
    const colors = {
      purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
      blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      orange: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      gray: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
    }
    return colors[color] || colors.gray
  }

  const getPermissionIcon = (permission) => {
    if (permission.includes('read') || permission.includes('view')) return Eye
    if (permission.includes('write') || permission.includes('manage')) return Edit
    if (permission.includes('delete')) return Trash2
    return Settings
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  }

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Role Management</h1>
          <p className="text-muted-foreground">
            Configure roles and permissions for your organization
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Create Role
        </Button>
      </motion.div>

      {/* Role Overview */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Roles</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{roles.length}</div>
            <p className="text-xs text-muted-foreground">
              Active role configurations
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {roles.reduce((sum, role) => sum + role.userCount, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              Users across all roles
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Permissions</CardTitle>
            <Lock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(permissionLabels).length}
            </div>
            <p className="text-xs text-muted-foreground">
              Available permissions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Most Used Role</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">User</div>
            <p className="text-xs text-muted-foreground">
              42 users assigned
            </p>
          </CardContent>
        </Card>
      </motion.div>

      {/* Roles Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {roles.map((role, index) => (
          <motion.div
            key={role.id}
            variants={itemVariants}
            whileHover={{ scale: 1.02 }}
            transition={{ type: "spring", stiffness: 300 }}
          >
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      role.color === 'purple' ? 'bg-purple-100 dark:bg-purple-900/30' :
                      role.color === 'blue' ? 'bg-blue-100 dark:bg-blue-900/30' :
                      role.color === 'orange' ? 'bg-orange-100 dark:bg-orange-900/30' :
                      'bg-gray-100 dark:bg-gray-900/30'
                    }`}>
                      <Shield className={`w-5 h-5 ${
                        role.color === 'purple' ? 'text-purple-600 dark:text-purple-400' :
                        role.color === 'blue' ? 'text-blue-600 dark:text-blue-400' :
                        role.color === 'orange' ? 'text-orange-600 dark:text-orange-400' :
                        'text-gray-600 dark:text-gray-400'
                      }`} />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{role.name}</CardTitle>
                      <CardDescription>{role.description}</CardDescription>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm">
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button variant="ghost" size="sm">
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
                
                <div className="flex items-center justify-between pt-2">
                  <Badge className={getColorClasses(role.color)}>
                    {role.userCount} users
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Created {role.createdAt}
                  </span>
                </div>
              </CardHeader>

              <CardContent>
                <div className="space-y-4">
                  {Object.entries(permissionCategories).map(([category, permissions]) => (
                    <div key={category} className="space-y-2">
                      <h4 className="text-sm font-medium text-muted-foreground">{category}</h4>
                      <div className="grid grid-cols-1 gap-2">
                        {permissions.map((permission) => {
                          const Icon = getPermissionIcon(permission)
                          const hasPermission = role.permissions[permission]
                          
                          return (
                            <div
                              key={permission}
                              className="flex items-center justify-between p-2 rounded-md bg-muted/30"
                            >
                              <div className="flex items-center space-x-2">
                                <Icon className="w-4 h-4 text-muted-foreground" />
                                <span className="text-sm">{permissionLabels[permission]}</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                {hasPermission ? (
                                  <CheckCircle className="w-4 h-4 text-green-500" />
                                ) : (
                                  <XCircle className="w-4 h-4 text-red-500" />
                                )}
                                <Switch
                                  checked={hasPermission}
                                  onCheckedChange={(checked) => {
                                    setRoles(roles.map(r => 
                                      r.id === role.id 
                                        ? { ...r, permissions: { ...r.permissions, [permission]: checked } }
                                        : r
                                    ))
                                  }}
                                  size="sm"
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 pt-4 border-t border-border">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">
                      {Object.values(role.permissions).filter(Boolean).length} of {Object.keys(role.permissions).length} permissions enabled
                    </span>
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {/* Permission Matrix */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="w-5 h-5 mr-2" />
              Permission Matrix
            </CardTitle>
            <CardDescription>
              Overview of all permissions across roles
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-3 font-medium">Permission</th>
                    {roles.map(role => (
                      <th key={role.id} className="text-center p-3 font-medium">
                        <Badge className={getColorClasses(role.color)}>
                          {role.name}
                        </Badge>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(permissionLabels).map(([permission, label]) => (
                    <tr key={permission} className="border-b border-border hover:bg-muted/30">
                      <td className="p-3">
                        <div className="flex items-center space-x-2">
                          {(() => {
                            const Icon = getPermissionIcon(permission)
                            return <Icon className="w-4 h-4 text-muted-foreground" />
                          })()}
                          <span className="font-medium">{label}</span>
                        </div>
                      </td>
                      {roles.map(role => (
                        <td key={role.id} className="p-3 text-center">
                          {role.permissions[permission] ? (
                            <CheckCircle className="w-5 h-5 text-green-500 mx-auto" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-500 mx-auto" />
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Recent Changes */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Recent Role Changes
            </CardTitle>
            <CardDescription>
              Latest modifications to roles and permissions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { action: 'Permission Added', role: 'Manager', permission: 'analytics.write', time: '2 minutes ago', type: 'add' },
                { action: 'Role Created', role: 'Guest', permission: null, time: '1 hour ago', type: 'create' },
                { action: 'Permission Removed', role: 'Analyst', permission: 'users.write', time: '3 hours ago', type: 'remove' },
                { action: 'Role Updated', role: 'Admin', permission: null, time: '1 day ago', type: 'update' }
              ].map((change, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 rounded-lg hover:bg-muted/50 transition-colors">
                  <div className={`w-2 h-2 rounded-full ${
                    change.type === 'add' ? 'bg-green-500' :
                    change.type === 'create' ? 'bg-blue-500' :
                    change.type === 'remove' ? 'bg-red-500' :
                    'bg-yellow-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium">{change.action}</p>
                    <p className="text-xs text-muted-foreground">
                      Role: {change.role}
                      {change.permission && ` • Permission: ${permissionLabels[change.permission]}`}
                    </p>
                  </div>
                  <p className="text-xs text-muted-foreground">{change.time}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

export default RoleManagement

