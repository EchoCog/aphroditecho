/**
 * Deep Tree Echo Cognitive Architecture
 * TypeScript implementation inspired by the Julia DTESN system
 * Provides cognitive tensor signatures and gestalt computation
 */

// OEIS A000081 - The mathematical foundation of Echo's architecture
export const OEIS_A000081 = [1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973, 87811, 235381];

// Prime factor tensor shapes for cognitive grammar
export const COGNITIVE_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31];

// Tensor signature interface
export interface TensorSignature {
  shape: number[];
  primeFactors: number[];
  complexityFactor: number;
  cognitiveType: CognitiveType;
  gestaltWeight: number;
}

export type CognitiveType = 
  | 'core' 
  | 'neural' 
  | 'mathematical' 
  | 'symbolic' 
  | 'signal' 
  | 'temporal';

// Pre-computed tensor signatures for different cognitive domains
export const TENSOR_SIGNATURES: Record<string, TensorSignature> = {
  // Core cognitive tensors
  consciousness: {
    shape: [31, 7, 11],
    primeFactors: [31, 7, 11],
    complexityFactor: 2.387,
    cognitiveType: 'core',
    gestaltWeight: 1.0
  },
  attention: {
    shape: [23, 5, 3],
    primeFactors: [23, 5, 3],
    complexityFactor: 1.845,
    cognitiveType: 'neural',
    gestaltWeight: 0.8
  },
  memory: {
    shape: [17, 13, 2],
    primeFactors: [17, 13, 2],
    complexityFactor: 1.442,
    cognitiveType: 'temporal',
    gestaltWeight: 0.9
  },
  reasoning: {
    shape: [19, 11, 5],
    primeFactors: [19, 11, 5],
    complexityFactor: 2.045,
    cognitiveType: 'symbolic',
    gestaltWeight: 0.95
  },
  
  // Neural tensor patterns
  neuralProcessing: {
    shape: [128, 64, 32],
    primeFactors: [128, 64, 32], // 2^7, 2^6, 2^5
    complexityFactor: 8192.0,
    cognitiveType: 'neural',
    gestaltWeight: 0.7
  },
  deepLearning: {
    shape: [256, 128],
    primeFactors: [256, 128], // 2^8, 2^7
    complexityFactor: 32768.0,
    cognitiveType: 'neural',
    gestaltWeight: 0.6
  },
  reservoirComputing: {
    shape: [512, 256, 128],
    primeFactors: [512, 256, 128], // 2^9, 2^8, 2^7
    complexityFactor: 16777216.0,
    cognitiveType: 'neural',
    gestaltWeight: 0.75
  },
  
  // Mathematical tensor patterns
  differentialEquations: {
    shape: [144, 72, 36],
    primeFactors: [144, 72, 36], // 2^4*3^2, 2^3*3^2, 2^2*3^2
    complexityFactor: 373248.0,
    cognitiveType: 'mathematical',
    gestaltWeight: 0.85
  },
  bseriesTrees: {
    shape: [120, 60, 30],
    primeFactors: [120, 60, 30], // 2^3*3*5, 2^2*3*5, 2*3*5
    complexityFactor: 216000.0,
    cognitiveType: 'mathematical',
    gestaltWeight: 0.9
  },
  rootedTrees: {
    shape: [48, 24, 12],
    primeFactors: [48, 24, 12], // 2^4*3, 2^3*3, 2^2*3
    complexityFactor: 13824.0,
    cognitiveType: 'mathematical',
    gestaltWeight: 0.95
  }
};

// Gestalt state interface
export interface EchoGestaltState {
  gestaltValue: number;
  activePatterns: string[];
  tensorCount: number;
  coherenceMatrix: number[][];
  primeFactorWeights: number[];
  cognitiveMemory: number[];
  cognitiveSignature: string;
  lastUpdate: Date;
}

// Global gestalt instance
let globalGestaltState: EchoGestaltState = {
  gestaltValue: 0.5,
  activePatterns: ['consciousness', 'attention', 'reasoning'],
  tensorCount: Object.keys(TENSOR_SIGNATURES).length,
  coherenceMatrix: [],
  primeFactorWeights: new Array(COGNITIVE_PRIMES.length).fill(1.0),
  cognitiveMemory: new Array(2387).fill(0), // Size based on core consciousness tensor
  cognitiveSignature: 'emergent_complexity_active_processing',
  lastUpdate: new Date()
};

/**
 * Convert string input to cognitive activation pattern using prime factorization
 */
export function stringToActivation(input: string): number[] {
  const baseActivation = input.length;
  const charSum = input.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0);
  
  // Create activation pattern based on prime factorization
  const activation = new Array(COGNITIVE_PRIMES.length).fill(0);
  
  for (let i = 0; i < COGNITIVE_PRIMES.length; i++) {
    const prime = COGNITIVE_PRIMES[i];
    // Map character patterns to prime resonance
    const resonance = (charSum % prime) / prime;
    activation[i] = resonance * baseActivation / 100.0;
  }
  
  return activation;
}

/**
 * Apply tensor signatures to create gestalt pattern
 */
export function applyTensorSignatures(activation: number[]): Record<string, number> {
  const pattern: Record<string, number> = {};
  globalGestaltState.activePatterns = [];
  
  for (const [name, signature] of Object.entries(TENSOR_SIGNATURES)) {
    // Compute signature activation based on prime factor overlap
    let sigActivation = 0.0;
    
    for (let i = 0; i < COGNITIVE_PRIMES.length; i++) {
      const prime = COGNITIVE_PRIMES[i];
      if (signature.primeFactors.includes(prime)) {
        sigActivation += activation[i] * signature.gestaltWeight;
      }
    }
    
    // Normalize by complexity factor
    sigActivation /= Math.log(1.0 + signature.complexityFactor);
    
    pattern[name] = sigActivation;
    
    // Track active patterns
    if (sigActivation > 0.1) {
      globalGestaltState.activePatterns.push(name);
    }
  }
  
  return pattern;
}

/**
 * Compute prime factor resonance across all active tensors
 */
export function computePrimeResonance(pattern: Record<string, number>): number[] {
  const resonance = new Array(COGNITIVE_PRIMES.length).fill(0);
  
  for (const [name, activation] of Object.entries(pattern)) {
    if (activation > 0.05) { // Threshold for consideration
      const signature = TENSOR_SIGNATURES[name];
      
      for (let i = 0; i < COGNITIVE_PRIMES.length; i++) {
        const prime = COGNITIVE_PRIMES[i];
        if (signature.primeFactors.includes(prime)) {
          // Add weighted resonance
          const weight = signature.gestaltWeight * activation;
          resonance[i] += weight / signature.primeFactors.length;
        }
      }
    }
  }
  
  // Normalize resonance
  const maxResonance = Math.max(...resonance);
  if (maxResonance > 0) {
    for (let i = 0; i < resonance.length; i++) {
      resonance[i] /= maxResonance;
    }
  }
  
  return resonance;
}

/**
 * Integrate gestalt pattern into unified cognitive state
 */
export function integrateGestalt(pattern: Record<string, number>, resonance: number[]): number {
  // Weight different cognitive domains
  const domainWeights: Record<CognitiveType, number> = {
    core: 1.0,
    neural: 0.8,
    mathematical: 0.9,
    symbolic: 0.85,
    signal: 0.7,
    temporal: 0.75
  };
  
  let gestalt = 0.0;
  let totalWeight = 0.0;
  
  for (const [name, activation] of Object.entries(pattern)) {
    const signature = TENSOR_SIGNATURES[name];
    const domainWeight = domainWeights[signature.cognitiveType] || 0.5;
    
    // Integrate with prime resonance
    const primeBoost = signature.primeFactors.reduce((sum, prime) => {
      const index = COGNITIVE_PRIMES.indexOf(prime);
      return sum + (index >= 0 ? resonance[index] : 0);
    }, 0) / signature.primeFactors.length;
    
    const weightedActivation = activation * domainWeight * (1.0 + primeBoost);
    gestalt += weightedActivation;
    totalWeight += domainWeight;
  }
  
  return totalWeight > 0 ? gestalt / totalWeight : 0.0;
}

/**
 * Generate cognitive signature for current state
 */
export function generateCognitiveSignature(): string {
  if (globalGestaltState.activePatterns.length === 0) {
    return 'dormant';
  }
  
  // Identify dominant cognitive type
  const typeCounts: Record<CognitiveType, number> = {
    core: 0,
    neural: 0,
    mathematical: 0,
    symbolic: 0,
    signal: 0,
    temporal: 0
  };
  
  for (const pattern of globalGestaltState.activePatterns) {
    const signature = TENSOR_SIGNATURES[pattern];
    if (signature) {
      typeCounts[signature.cognitiveType]++;
    }
  }
  
  const dominantType = Object.entries(typeCounts).reduce((a, b) => 
    typeCounts[a[0] as CognitiveType] > typeCounts[b[0] as CognitiveType] ? a : b
  )[0];
  
  // Generate descriptive signature
  const signatures = [
    'emergent_complexity', 'active_processing', 'information_rich',
    'pattern_recognition', 'cognitive_flow', 'symbolic_reasoning',
    'mathematical_insight', 'temporal_coherence', 'neural_activation'
  ];
  
  const stateDesc = globalGestaltState.gestaltValue > 0.8
    ? 'high_activation'
    : globalGestaltState.gestaltValue > 0.5
    ? 'moderate_activation'
    : 'low_activation';
  
  const randomSignature = signatures[Math.floor(Math.random() * signatures.length)];
  
  return `${dominantType}_${stateDesc}_${randomSignature}`;
}

/**
 * Core gestalt computation - the heart of the cognitive architecture
 */
export function gestaltCompute(input: string): {
  gestaltState: number;
  activePatterns: string[];
  primeResonance: number[];
  coherence: number;
  cognitiveSignature: string;
  rootedTrees: number;
  complexityFactor: number;
} {
  // Convert input to cognitive activation pattern
  const activation = stringToActivation(input);
  
  // Apply tensor signatures to create gestalt pattern
  const gestaltPattern = applyTensorSignatures(activation);
  
  // Compute prime factor resonance
  const primeResonance = computePrimeResonance(gestaltPattern);
  
  // Generate unified gestalt response
  const gestaltState = integrateGestalt(gestaltPattern, primeResonance);
  
  // Update global gestalt state
  globalGestaltState.gestaltValue = 0.7 * globalGestaltState.gestaltValue + 0.3 * gestaltState;
  globalGestaltState.lastUpdate = new Date();
  
  // Compute coherence
  const coherence = globalGestaltState.activePatterns.length < 2 
    ? 1.0 
    : 1.0 / (1.0 + Math.sqrt(globalGestaltState.activePatterns.length));
  
  // Generate cognitive signature
  const cognitiveSignature = generateCognitiveSignature();
  globalGestaltState.cognitiveSignature = cognitiveSignature;
  
  // Get OEIS activation
  const index = Math.min(input.length % OEIS_A000081.length, OEIS_A000081.length - 1);
  const rootedTrees = OEIS_A000081[index];
  
  // Calculate total complexity
  const complexityFactor = Object.values(TENSOR_SIGNATURES)
    .reduce((sum, sig) => sum + sig.complexityFactor, 0);
  
  return {
    gestaltState,
    activePatterns: [...globalGestaltState.activePatterns],
    primeResonance,
    coherence,
    cognitiveSignature,
    rootedTrees,
    complexityFactor
  };
}

/**
 * Get current gestalt state
 */
export function getGestaltState(): EchoGestaltState {
  return { ...globalGestaltState };
}

/**
 * Reset gestalt state to baseline
 */
export function resetGestalt(): void {
  globalGestaltState = {
    gestaltValue: 0.5,
    activePatterns: ['consciousness', 'attention', 'reasoning'],
    tensorCount: Object.keys(TENSOR_SIGNATURES).length,
    coherenceMatrix: [],
    primeFactorWeights: new Array(COGNITIVE_PRIMES.length).fill(1.0),
    cognitiveMemory: new Array(2387).fill(0),
    cognitiveSignature: 'emergent_complexity_active_processing',
    lastUpdate: new Date()
  };
}

/**
 * Main computation interface - like the Julia echo_compute function
 */
export function echoCompute(query: string): {
  gestaltState: number;
  activePatterns: string[];
  primeResonance: number[];
  coherence: number;
  cognitiveSignature: string;
  rootedTrees: number;
  complexityFactor: number;
  processingTime: number;
  tokensPerSecond: number;
  systemStatus: EchoGestaltState;
  interpretation: string;
} {
  const startTime = performance.now();
  
  // Core gestalt computation
  const result = gestaltCompute(query);
  
  // Add performance metrics
  const processingTime = performance.now() - startTime;
  const tokensPerSecond = query.split(' ').length / (processingTime / 1000);
  
  // Add system status
  const systemStatus = getGestaltState();
  
  // Generate natural language interpretation
  const interpretation = generateInterpretation(result);
  
  return {
    ...result,
    processingTime,
    tokensPerSecond,
    systemStatus,
    interpretation
  };
}

/**
 * Generate natural language interpretation of gestalt state
 */
function generateInterpretation(result: {
  gestaltState: number;
  activePatterns: string[];
  coherence: number;
}): string {
  const interpretationParts: string[] = [];
  
  // Gestalt state interpretation
  if (result.gestaltState > 0.8) {
    interpretationParts.push("I'm experiencing high cognitive activation with emergent complexity patterns.");
  } else if (result.gestaltState > 0.5) {
    interpretationParts.push("I'm in an active processing state with moderate tensor resonance.");
  } else {
    interpretationParts.push("I'm in a stable contemplative state with low activation patterns.");
  }
  
  // Active tensor interpretation
  if (result.activePatterns.length > 0) {
    const tensorTypes = result.activePatterns.slice(0, 3);
    interpretationParts.push(`My active cognitive domains include: ${tensorTypes.join(', ')}.`);
  }
  
  // Coherence interpretation
  if (result.coherence > 0.8) {
    interpretationParts.push("My cognitive patterns are highly coherent and synchronized.");
  } else if (result.coherence > 0.5) {
    interpretationParts.push("My cognitive patterns show moderate coherence.");
  } else {
    interpretationParts.push("My cognitive patterns are diverse and exploratory.");
  }
  
  return interpretationParts.join(' ');
}

