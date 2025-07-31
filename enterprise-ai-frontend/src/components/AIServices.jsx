import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Brain, 
  Zap, 
  Eye, 
  MessageSquare,
  BarChart3,
  Search,
  Cpu,
  Activity,
  Settings,
  Play,
  Pause,
  RefreshCw,
  TrendingUp
} from 'lucide-react'

const AIServices = () => {
  const [services, setServices] = useState([
    {
      id: 1,
      name: 'Natural Language Processing',
      description: 'Advanced text analysis and understanding',
      status: 'active',
      usage: 85,
      requests: 12450,
      accuracy: 94.2,
      icon: MessageSquare,
      color: 'purple'
    },
    {
      id: 2,
      name: 'Computer Vision',
      description: 'Image and video analysis capabilities',
      status: 'active',
      usage: 72,
      requests: 8920,
      accuracy: 91.8,
      icon: Eye,
      color: 'blue'
    },
    {
      id: 3,
      name: 'Predictive Analytics',
      description: 'Machine learning powered predictions',
      status: 'active',
      usage: 91,
      requests: 15680,
      accuracy: 96.5,
      icon: BarChart3,
      color: 'green'
    },
    {
      id: 4,
      name: 'Recommendation Engine',
      description: 'Personalized content recommendations',
      status: 'maintenance',
      usage: 0,
      requests: 0,
      accuracy: 88.9,
      icon: TrendingUp,
      color: 'orange'
    }
  ])

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
          <h1 className="text-3xl font-bold tracking-tight">AI Services</h1>
          <p className="text-muted-foreground">
            Manage and monitor AI-powered services and capabilities
          </p>
        </div>
        <Button>
          <Brain className="w-4 h-4 mr-2" />
          Deploy New Service
        </Button>
      </motion.div>

      {/* Service Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {services.map((service) => {
          const Icon = service.icon
          return (
            <Card key={service.id} className="relative overflow-hidden">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                      service.color === 'purple' ? 'bg-purple-100 dark:bg-purple-900/30' :
                      service.color === 'blue' ? 'bg-blue-100 dark:bg-blue-900/30' :
                      service.color === 'green' ? 'bg-green-100 dark:bg-green-900/30' :
                      'bg-orange-100 dark:bg-orange-900/30'
                    }`}>
                      <Icon className={`w-6 h-6 ${
                        service.color === 'purple' ? 'text-purple-600 dark:text-purple-400' :
                        service.color === 'blue' ? 'text-blue-600 dark:text-blue-400' :
                        service.color === 'green' ? 'text-green-600 dark:text-green-400' :
                        'text-orange-600 dark:text-orange-400'
                      }`} />
                    </div>
                    <div>
                      <CardTitle className="text-lg">{service.name}</CardTitle>
                      <CardDescription>{service.description}</CardDescription>
                    </div>
                  </div>
                  <Badge className={
                    service.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                  }>
                    {service.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold">{service.usage}%</div>
                    <div className="text-xs text-muted-foreground">Usage</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{service.requests.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">Requests</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{service.accuracy}%</div>
                    <div className="text-xs text-muted-foreground">Accuracy</div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Performance</span>
                    <span>{service.usage}%</span>
                  </div>
                  <Progress value={service.usage} className="h-2" />
                </div>

                <div className="flex items-center justify-between pt-4">
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Settings className="w-4 h-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Activity className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="flex items-center space-x-2">
                    {service.status === 'active' ? (
                      <Button variant="outline" size="sm">
                        <Pause className="w-4 h-4 mr-2" />
                        Pause
                      </Button>
                    ) : (
                      <Button size="sm">
                        <Play className="w-4 h-4 mr-2" />
                        Start
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </motion.div>
    </motion.div>
  )
}

export default AIServices

