import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { Separator } from '@/components/ui/separator.jsx'
import { 
  Brain, 
  Network, 
  Zap, 
  Code, 
  Eye, 
  Shield, 
  Layers, 
  GitBranch,
  ChevronDown,
  ExternalLink,
  BookOpen,
  Image as ImageIcon,
  Download
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import DocumentViewer from './components/DocumentViewer.jsx'
import InteractiveTimeline from './components/InteractiveTimeline.jsx'
import './App.css'

// Import images
import architectureOverview from './assets/deep_tree_echo_architecture_overview.png'
import hypergraphMemory from './assets/hypergraph_memory_space.png'
import echoPropagation from './assets/echo_propagation_engine.png'
import neuralSymbolic from './assets/neural_symbolic_integration.png'
import extensionLayer from './assets/extension_layer_architecture.png'

function App() {
  const [activeSection, setActiveSection] = useState('overview')
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const sections = [
    { id: 'overview', title: 'Overview', icon: Brain },
    { id: 'architecture', title: 'Architecture', icon: Layers },
    { id: 'memory', title: 'Memory System', icon: Network },
    { id: 'propagation', title: 'Echo Engine', icon: Zap },
    { id: 'integration', title: 'Neural-Symbolic', icon: Code },
    { id: 'extensions', title: 'Extensions', icon: GitBranch },
    { id: 'timeline', title: 'Timeline', icon: Eye },
    { id: 'analysis', title: 'Analysis', icon: BookOpen }
  ]

  const scrollToSection = (sectionId) => {
    setActiveSection(sectionId)
    const element = document.getElementById(sectionId)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Navigation Header */}
      <motion.header 
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled ? 'bg-white/80 dark:bg-slate-900/80 backdrop-blur-md shadow-lg' : 'bg-transparent'
        }`}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <motion.div 
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.05 }}
            >
              <Brain className="h-8 w-8 text-blue-600 dark:text-blue-400" />
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Deep Tree Echo
              </h1>
            </motion.div>
            
            <nav className="hidden md:flex items-center space-x-1">
              {sections.map((section) => {
                const Icon = section.icon
                return (
                  <Button
                    key={section.id}
                    variant={activeSection === section.id ? "default" : "ghost"}
                    size="sm"
                    onClick={() => scrollToSection(section.id)}
                    className="flex items-center space-x-2"
                  >
                    <Icon className="h-4 w-4" />
                    <span>{section.title}</span>
                  </Button>
                )
              })}
            </nav>
          </div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <section id="overview" className="pt-24 pb-16">
        <div className="container mx-auto px-6">
          <motion.div 
            className="text-center max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">
              Cognitive Architecture Analysis
            </h2>
            <p className="text-xl md:text-2xl text-slate-600 dark:text-slate-300 mb-8 leading-relaxed">
              A comprehensive analysis of the Deep Tree Echo system - a revolutionary cognitive architecture 
              combining membrane computing, hypergraph theory, and neural-symbolic integration.
            </p>
            
            <div className="flex flex-wrap justify-center gap-4 mb-12">
              <Badge variant="secondary" className="text-lg px-4 py-2">
                <Brain className="h-5 w-5 mr-2" />
                Membrane Computing
              </Badge>
              <Badge variant="secondary" className="text-lg px-4 py-2">
                <Network className="h-5 w-5 mr-2" />
                Hypergraph Memory
              </Badge>
              <Badge variant="secondary" className="text-lg px-4 py-2">
                <Zap className="h-5 w-5 mr-2" />
                Echo Propagation
              </Badge>
              <Badge variant="secondary" className="text-lg px-4 py-2">
                <Code className="h-5 w-5 mr-2" />
                Neural-Symbolic AI
              </Badge>
            </div>

            <motion.div 
              className="flex flex-col sm:flex-row gap-4 justify-center"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5, duration: 0.5 }}
            >
              <Button size="lg" onClick={() => scrollToSection('architecture')} className="text-lg px-8 py-3">
                <BookOpen className="h-5 w-5 mr-2" />
                Explore Architecture
              </Button>
              <Button size="lg" variant="outline" onClick={() => scrollToSection('analysis')} className="text-lg px-8 py-3">
                <Download className="h-5 w-5 mr-2" />
                View Analysis
              </Button>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Architecture Overview */}
      <section id="architecture" className="py-16 bg-white/50 dark:bg-slate-800/50">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h3 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              System Architecture
            </h3>
            
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <Card className="overflow-hidden shadow-xl">
                  <CardContent className="p-0">
                    <img 
                      src={architectureOverview} 
                      alt="Deep Tree Echo Architecture Overview"
                      className="w-full h-auto object-cover hover:scale-105 transition-transform duration-500"
                    />
                  </CardContent>
                </Card>
              </div>
              
              <div className="space-y-6">
                <h4 className="text-2xl font-semibold text-slate-800 dark:text-slate-200">
                  Hierarchical Membrane-Based Design
                </h4>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                  Deep Tree Echo implements a sophisticated membrane hierarchy inspired by biological cellular structures. 
                  This design provides natural boundaries for cognitive processes while enabling controlled communication 
                  and coordination between different system components.
                </p>
                
                <div className="grid grid-cols-1 gap-4">
                  <Card className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-lg">
                        <Shield className="h-5 w-5 mr-2 text-blue-500" />
                        Root Membrane
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        System boundary providing security and isolation
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-green-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-lg">
                        <Brain className="h-5 w-5 mr-2 text-green-500" />
                        Cognitive Membrane
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Core processing with Memory, Reasoning, and Grammar subsystems
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-purple-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-lg">
                        <GitBranch className="h-5 w-5 mr-2 text-purple-500" />
                        Extension Membrane
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Plugin container for specialized functionality modules
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Memory System */}
      <section id="memory" className="py-16">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h3 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
              Hypergraph Memory Space
            </h3>
            
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="space-y-6">
                <h4 className="text-2xl font-semibold text-slate-800 dark:text-slate-200">
                  Advanced Knowledge Representation
                </h4>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                  The hypergraph memory space represents a significant advancement over traditional memory architectures 
                  by implementing mathematical frameworks that capture complex, multi-way relationships between concepts.
                </p>
                
                <Tabs defaultValue="declarative" className="w-full">
                  <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4">
                    <TabsTrigger value="declarative">Declarative</TabsTrigger>
                    <TabsTrigger value="procedural">Procedural</TabsTrigger>
                    <TabsTrigger value="episodic">Episodic</TabsTrigger>
                    <TabsTrigger value="intentional">Intentional</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="declarative" className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-blue-600">Declarative Memory</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p>Stores facts and concepts using sophisticated hypergraph representations that capture rich semantic relationships between concepts.</p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                  
                  <TabsContent value="procedural" className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-green-600">Procedural Memory</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p>Contains skills, procedures, and algorithms using hypergraph structures that capture complex dependencies and relationships.</p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                  
                  <TabsContent value="episodic" className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-orange-600">Episodic Memory</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p>Stores experiences and events using temporal hypergraph representations that capture complex relationships over time.</p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                  
                  <TabsContent value="intentional" className="mt-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-purple-600">Intentional Memory</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <p>Organizes goals, plans, and intentions using hierarchical hypergraph representations for coherent long-term objectives.</p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>
              </div>
              
              <div>
                <Card className="overflow-hidden shadow-xl">
                  <CardContent className="p-0">
                    <img 
                      src={hypergraphMemory} 
                      alt="Hypergraph Memory Space"
                      className="w-full h-auto object-cover hover:scale-105 transition-transform duration-500"
                    />
                  </CardContent>
                </Card>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Echo Propagation Engine */}
      <section id="propagation" className="py-16 bg-white/50 dark:bg-slate-800/50">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h3 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent">
              Echo Propagation Engine
            </h3>
            
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <Card className="overflow-hidden shadow-xl">
                  <CardContent className="p-0">
                    <img 
                      src={echoPropagation} 
                      alt="Echo Propagation Engine"
                      className="w-full h-auto object-cover hover:scale-105 transition-transform duration-500"
                    />
                  </CardContent>
                </Card>
              </div>
              
              <div className="space-y-6">
                <h4 className="text-2xl font-semibold text-slate-800 dark:text-slate-200">
                  Dynamic Activation Spreading
                </h4>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                  The Echo Propagation Engine implements sophisticated activation spreading mechanisms that enable 
                  the system to retrieve relevant information, recognize patterns, and generate creative insights 
                  through dynamic information processing.
                </p>
                
                <div className="space-y-4">
                  <Card className="border-l-4 border-l-yellow-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-lg">
                        <Zap className="h-5 w-5 mr-2 text-yellow-500" />
                        Activation Spreading
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Propagates activation through hypergraph structures with sophisticated decay and threshold mechanisms
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-orange-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-lg">
                        <Eye className="h-5 w-5 mr-2 text-orange-500" />
                        Pattern Recognition
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Identifies meaningful patterns in activation spreads using hybrid neural-symbolic algorithms
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-red-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center text-lg">
                        <GitBranch className="h-5 w-5 mr-2 text-red-500" />
                        Feedback Loops
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Creates self-reinforcing patterns that support sustained attention and iterative processing
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Neural-Symbolic Integration */}
      <section id="integration" className="py-16">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h3 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              Neural-Symbolic Integration
            </h3>
            
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div className="space-y-6">
                <h4 className="text-2xl font-semibold text-slate-800 dark:text-slate-200">
                  Cognitive Grammar Kernel
                </h4>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                  The Cognitive Grammar Kernel provides seamless integration between neural pattern recognition 
                  and symbolic logical reasoning, implementing a Scheme-based environment that enables 
                  sophisticated symbolic manipulation and meta-cognitive reflection.
                </p>
                
                <div className="grid grid-cols-1 gap-4">
                  <Card className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20">
                    <CardHeader>
                      <CardTitle className="flex items-center text-blue-700 dark:text-blue-300">
                        <Network className="h-5 w-5 mr-2" />
                        Symbol Grounding
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Connects symbolic representations to neural activation patterns
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20">
                    <CardHeader>
                      <CardTitle className="flex items-center text-green-700 dark:text-green-300">
                        <Code className="h-5 w-5 mr-2" />
                        Neural Compilation
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Converts symbolic rules into neural network structures
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-gradient-to-r from-purple-50 to-violet-50 dark:from-purple-900/20 dark:to-violet-900/20">
                    <CardHeader>
                      <CardTitle className="flex items-center text-purple-700 dark:text-purple-300">
                        <Brain className="h-5 w-5 mr-2" />
                        Hybrid Reasoning
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-slate-600 dark:text-slate-300">
                        Combines neural and symbolic processing in unified reasoning
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
              
              <div>
                <Card className="overflow-hidden shadow-xl">
                  <CardContent className="p-0">
                    <img 
                      src={neuralSymbolic} 
                      alt="Neural-Symbolic Integration"
                      className="w-full h-auto object-cover hover:scale-105 transition-transform duration-500"
                    />
                  </CardContent>
                </Card>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Extension Layer */}
      <section id="extensions" className="py-16 bg-white/50 dark:bg-slate-800/50">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h3 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Extension Layer Architecture
            </h3>
            
            <div className="grid lg:grid-cols-2 gap-12 items-center">
              <div>
                <Card className="overflow-hidden shadow-xl">
                  <CardContent className="p-0">
                    <img 
                      src={extensionLayer} 
                      alt="Extension Layer Architecture"
                      className="w-full h-auto object-cover hover:scale-105 transition-transform duration-500"
                    />
                  </CardContent>
                </Card>
              </div>
              
              <div className="space-y-6">
                <h4 className="text-2xl font-semibold text-slate-800 dark:text-slate-200">
                  Modular Plugin Framework
                </h4>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                  The Extension Layer provides a sophisticated plugin architecture that enables dynamic capability 
                  expansion while maintaining system stability and security through specialized extension modules.
                </p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Browser Automation</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        Web interaction and information gathering
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-green-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">ML Integration</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        Machine learning algorithms and data processing
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-orange-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Evolution Engine</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        Genetic algorithms and system adaptation
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-purple-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Introspection System</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        Self-monitoring and meta-cognitive reflection
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-red-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Monitoring Dashboard</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        System metrics and performance monitoring
                      </p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-l-4 border-l-yellow-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Sensory Motor Interface</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-slate-600 dark:text-slate-300">
                        Environmental interaction capabilities
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Development Timeline */}
      <section id="timeline" className="py-16">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h3 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
              Development Timeline
            </h3>
            
            <InteractiveTimeline />
          </motion.div>
        </div>
      </section>

      {/* Analysis Summary */}
      <section id="analysis" className="py-16">
        <div className="container mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h3 className="text-4xl font-bold text-center mb-12 bg-gradient-to-r from-slate-600 to-slate-800 bg-clip-text text-transparent">
              Comprehensive Analysis
            </h3>
            
            <DocumentViewer />
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="container mx-auto px-6">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <Brain className="h-8 w-8 text-blue-400" />
              <h3 className="text-2xl font-bold">Deep Tree Echo</h3>
            </div>
            <p className="text-slate-400 mb-6">
              Cognitive Architecture Analysis & Documentation
            </p>
            <p className="text-sm text-slate-500">
              Created by Manus AI • January 2025
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

