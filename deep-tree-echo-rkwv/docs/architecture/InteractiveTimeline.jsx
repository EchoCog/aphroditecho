import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Button } from '@/components/ui/button.jsx'
import { 
  Brain, 
  Network, 
  Zap, 
  Code, 
  Eye, 
  Shield,
  Calendar,
  Clock,
  CheckCircle
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

const InteractiveTimeline = () => {
  const [selectedPhase, setSelectedPhase] = useState(0)

  const phases = [
    {
      id: 0,
      title: "Research & Discovery",
      date: "Phase 1",
      icon: Eye,
      color: "blue",
      description: "Comprehensive research into cognitive architectures, membrane computing, and neural-symbolic integration",
      achievements: [
        "Literature review of membrane computing",
        "Analysis of hypergraph theory applications",
        "Study of echo state networks",
        "Neural-symbolic integration research"
      ],
      status: "completed"
    },
    {
      id: 1,
      title: "Architecture Design",
      date: "Phase 2", 
      icon: Brain,
      color: "green",
      description: "Development of the hierarchical membrane-based cognitive architecture framework",
      achievements: [
        "Membrane hierarchy specification",
        "Core layer component design",
        "Extension layer architecture",
        "Security membrane framework"
      ],
      status: "completed"
    },
    {
      id: 2,
      title: "Memory System",
      date: "Phase 3",
      icon: Network,
      color: "purple",
      description: "Implementation of the hypergraph-based memory space with multiple memory types",
      achievements: [
        "Hypergraph memory structure",
        "Declarative memory implementation",
        "Procedural memory design",
        "Episodic and intentional memory"
      ],
      status: "completed"
    },
    {
      id: 3,
      title: "Echo Propagation",
      date: "Phase 4",
      icon: Zap,
      color: "orange",
      description: "Development of the dynamic activation spreading and pattern recognition engine",
      achievements: [
        "Activation spreading algorithms",
        "Pattern recognition mechanisms",
        "Feedback loop implementation",
        "Dynamic threshold adaptation"
      ],
      status: "completed"
    },
    {
      id: 4,
      title: "Neural-Symbolic Integration",
      date: "Phase 5",
      icon: Code,
      color: "indigo",
      description: "Integration of neural processing with symbolic reasoning through the Cognitive Grammar Kernel",
      achievements: [
        "Symbol grounding mechanisms",
        "Neural compilation framework",
        "Hybrid reasoning system",
        "Meta-cognitive reflection"
      ],
      status: "completed"
    },
    {
      id: 5,
      title: "Extension Framework",
      date: "Phase 6",
      icon: Shield,
      color: "red",
      description: "Development of the modular plugin architecture for capability expansion",
      achievements: [
        "Plugin architecture design",
        "Browser automation module",
        "ML integration framework",
        "Monitoring and introspection"
      ],
      status: "in-progress"
    }
  ]

  const getColorClasses = (color, isSelected) => {
    const colors = {
      blue: isSelected ? 'bg-blue-500 text-white' : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
      green: isSelected ? 'bg-green-500 text-white' : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
      purple: isSelected ? 'bg-purple-500 text-white' : 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
      orange: isSelected ? 'bg-orange-500 text-white' : 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
      indigo: isSelected ? 'bg-indigo-500 text-white' : 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300',
      red: isSelected ? 'bg-red-500 text-white' : 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
    }
    return colors[color] || colors.blue
  }

  const selectedPhaseData = phases[selectedPhase]
  const Icon = selectedPhaseData.icon

  return (
    <div className="max-w-6xl mx-auto">
      <Card className="shadow-2xl">
        <CardHeader>
          <CardTitle className="text-3xl text-center flex items-center justify-center">
            <Calendar className="h-8 w-8 mr-3 text-blue-600" />
            Development Timeline
          </CardTitle>
          <CardDescription className="text-center text-lg">
            Interactive timeline of Deep Tree Echo development phases
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Timeline Navigation */}
            <div className="lg:col-span-1">
              <h4 className="font-semibold mb-4 text-slate-700 dark:text-slate-300">Development Phases</h4>
              <div className="space-y-3">
                {phases.map((phase, index) => {
                  const PhaseIcon = phase.icon
                  const isSelected = selectedPhase === index
                  return (
                    <motion.div
                      key={phase.id}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <Button
                        variant={isSelected ? "default" : "ghost"}
                        className={`w-full justify-start p-4 h-auto ${getColorClasses(phase.color, isSelected)}`}
                        onClick={() => setSelectedPhase(index)}
                      >
                        <div className="flex items-center space-x-3">
                          <PhaseIcon className="h-5 w-5" />
                          <div className="text-left">
                            <div className="font-medium">{phase.title}</div>
                            <div className="text-sm opacity-75">{phase.date}</div>
                          </div>
                          {phase.status === 'completed' && (
                            <CheckCircle className="h-4 w-4 ml-auto" />
                          )}
                          {phase.status === 'in-progress' && (
                            <Clock className="h-4 w-4 ml-auto" />
                          )}
                        </div>
                      </Button>
                    </motion.div>
                  )
                })}
              </div>
            </div>
            
            {/* Phase Details */}
            <div className="lg:col-span-2">
              <AnimatePresence mode="wait">
                <motion.div
                  key={selectedPhase}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <Card className={`border-2 ${getColorClasses(selectedPhaseData.color, false).replace('bg-', 'border-').replace('-100', '-200').replace('-900', '-800')}`}>
                    <CardHeader>
                      <CardTitle className="flex items-center text-2xl">
                        <Icon className={`h-8 w-8 mr-3 text-${selectedPhaseData.color}-600`} />
                        {selectedPhaseData.title}
                        <Badge 
                          variant={selectedPhaseData.status === 'completed' ? 'default' : 'secondary'}
                          className="ml-auto"
                        >
                          {selectedPhaseData.status === 'completed' ? 'Completed' : 'In Progress'}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="text-lg">
                        {selectedPhaseData.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <h5 className="font-semibold mb-3 text-slate-700 dark:text-slate-300">Key Achievements</h5>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {selectedPhaseData.achievements.map((achievement, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className="flex items-center space-x-2"
                          >
                            <CheckCircle className={`h-4 w-4 text-${selectedPhaseData.color}-600`} />
                            <span className="text-sm text-slate-600 dark:text-slate-300">
                              {achievement}
                            </span>
                          </motion.div>
                        ))}
                      </div>
                      
                      <div className="mt-6 p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                            Progress
                          </span>
                          <span className="text-sm text-slate-600 dark:text-slate-400">
                            {selectedPhaseData.status === 'completed' ? '100%' : '75%'}
                          </span>
                        </div>
                        <div className="mt-2 w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                          <motion.div
                            className={`h-2 rounded-full bg-${selectedPhaseData.color}-500`}
                            initial={{ width: 0 }}
                            animate={{ 
                              width: selectedPhaseData.status === 'completed' ? '100%' : '75%' 
                            }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default InteractiveTimeline

