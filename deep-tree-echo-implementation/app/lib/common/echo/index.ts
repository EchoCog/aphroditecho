/**
 * Deep Tree Echo Module
 * Comprehensive TypeScript implementation of the Deep Tree Echo System
 * 
 * This module provides:
 * - Cognitive architecture with tensor signatures
 * - Echo state networks for neural processing
 * - Gestalt computation and prime resonance
 * - Character configuration and personality management
 * - Advanced echo activities inspired by Julia implementations
 */

// Cognitive Architecture exports
export {
  // Core functions
  echoCompute,
  gestaltCompute,
  getGestaltState,
  resetGestalt,
  
  // Tensor operations
  stringToActivation,
  applyTensorSignatures,
  computePrimeResonance,
  integrateGestalt,
  generateCognitiveSignature,
  
  // Constants and types
  OEIS_A000081,
  COGNITIVE_PRIMES,
  TENSOR_SIGNATURES,
  
  // Types
  type TensorSignature,
  type CognitiveType,
  type EchoGestaltState
} from './cognitive-architecture';

// Echo State Network exports
export {
  // Main class
  DeepTreeEcho,
  
  // Factory functions
  createDeepTreeEcho,
  getGlobalNetwork,
  resetGlobalNetwork,
  processText,
  
  // Configurations
  NetworkConfigurations,
  
  // Types
  type DeepTreeEchoConfig,
  type NetworkState
} from './echo-state-network';

// Character Configuration exports
export {
  // Character management
  getCharacterState,
  updateCharacterConfig,
  recordInteraction,
  generatePersonalityPrompt,
  getResponseStyle,
  getCharacterStats,
  resetCharacterState,
  exportCharacterConfig,
  
  // Configuration
  DEFAULT_CHARACTER_CONFIG,
  
  // Types
  type DeepTreeEchoCharacter
} from './character-config';

// Utility functions for integration
export function initializeEchoSystem(config?: {
  networkConfig?: Partial<import('./echo-state-network').DeepTreeEchoConfig>;
  resetGestalt?: boolean;
}) {
  // Initialize or reset gestalt state if requested
  if (config?.resetGestalt) {
    resetGestalt();
  }
  
  // Initialize global network
  const network = getGlobalNetwork(config?.networkConfig);
  
  // Get initial states
  const gestaltState = getGestaltState();
  const networkState = network.getNetworkState();
  
  console.info('🌊 Deep Tree Echo System initialized');
  console.info(`Gestalt State: ${gestaltState.gestaltValue.toFixed(3)}`);
  console.info(`Network: ${networkState.reservoirState.length} neurons`);
  console.info(`Active Patterns: ${gestaltState.activePatterns.join(', ')}`);
  
  return {
    gestaltState,
    networkState,
    network
  };
}

export function processEchoQuery(query: string): {
  cognitive: ReturnType<typeof echoCompute>;
  neural: ReturnType<typeof processText>;
  combined: {
    interpretation: string;
    confidence: number;
    patterns: string[];
  };
} {
  // Process through cognitive architecture
  const cognitive = echoCompute(query);
  
  // Process through neural network
  const neural = processText(query);
  
  // Combine insights
  const combinedPatterns = [
    ...cognitive.activePatterns,
    neural.summary.includes('High') ? 'high_neural_activation' : 'moderate_neural_activation'
  ];
  
  const confidence = (cognitive.coherence + (neural.networkState.isInitialized ? 0.8 : 0.2)) / 2;
  
  const interpretation = `${cognitive.interpretation} ${neural.summary}`;
  
  return {
    cognitive,
    neural,
    combined: {
      interpretation,
      confidence,
      patterns: combinedPatterns
    }
  };
}

// Export version information
export const ECHO_VERSION = '1.0.0';
export const ECHO_BUILD = 'TypeScript-Implementation-2024';

// Export system status
export function getEchoSystemStatus() {
  const gestaltState = getGestaltState();
  const network = getGlobalNetwork();
  const networkInfo = network.getNetworkInfo();
  const memoryStats = network.getEchoMemoryStats();
  
  return {
    version: ECHO_VERSION,
    build: ECHO_BUILD,
    gestalt: {
      value: gestaltState.gestaltValue,
      signature: gestaltState.cognitiveSignature,
      activePatterns: gestaltState.activePatterns.length,
      lastUpdate: gestaltState.lastUpdate
    },
    network: {
      size: networkInfo.reservoirSize,
      depth: networkInfo.treeDepth,
      initialized: networkInfo.isInitialized,
      memoryLength: memoryStats.length,
      lastUpdate: networkInfo.lastUpdate
    },
    timestamp: new Date()
  };
}

