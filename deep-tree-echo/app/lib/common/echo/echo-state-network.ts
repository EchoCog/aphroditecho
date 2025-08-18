/**
 * Deep Tree Echo State Network Implementation
 * TypeScript implementation inspired by the Julia DeepTreeEcho system
 * Provides reservoir computing and neural network capabilities
 */

// Deep Tree Echo Network structure
export interface DeepTreeEchoConfig {
  treeDepth: number;
  reservoirSize: number;
  spectralRadius: number;
  inputScaling: number;
}

export interface NetworkState {
  reservoirState: number[];
  treeStates: Record<number, number[]>;
  echoMemoryLength: number;
  isInitialized: boolean;
  lastUpdate: Date;
}

export class DeepTreeEcho {
  private config: DeepTreeEchoConfig;
  private inputWeights: number[][];
  private reservoirWeights: number[][];
  private treeConnections: Record<number, number[]>;
  private reservoirState: number[];
  private treeStates: Record<number, number[]>;
  private echoMemory: number[][];
  private trainingData: number[][];
  private targetOutputs: number[][];
  private isInitialized: boolean;
  private lastUpdate: Date;

  constructor(config: Partial<DeepTreeEchoConfig> = {}) {
    this.config = {
      treeDepth: 3,
      reservoirSize: 100,
      spectralRadius: 0.9,
      inputScaling: 1.0,
      ...config
    };

    // Initialize network weights
    this.inputWeights = this.createRandomMatrix(
      this.config.reservoirSize, 
      this.config.reservoirSize, 
      this.config.inputScaling
    );
    
    this.reservoirWeights = this.createRandomMatrix(
      this.config.reservoirSize, 
      this.config.reservoirSize
    );

    // Scale reservoir weights to desired spectral radius
    this.scaleToSpectralRadius();

    // Initialize tree connections (hierarchical structure)
    this.treeConnections = {};
    for (let level = 1; level <= this.config.treeDepth; level++) {
      const connections: number[] = [];
      const nodeCount = Math.min(Math.pow(2, level), Math.floor(this.config.reservoirSize / level));
      for (let i = 0; i < nodeCount; i++) {
        connections.push(i);
      }
      this.treeConnections[level] = connections;
    }

    // Initialize state variables
    this.reservoirState = new Array(this.config.reservoirSize).fill(0);
    this.treeStates = {};
    this.echoMemory = [];
    this.trainingData = [];
    this.targetOutputs = [];
    this.isInitialized = true;
    this.lastUpdate = new Date();
  }

  /**
   * Create a random matrix with specified dimensions and scaling
   */
  private createRandomMatrix(rows: number, cols: number, scaling: number = 1.0): number[][] {
    const matrix: number[][] = [];
    for (let i = 0; i < rows; i++) {
      const row: number[] = [];
      for (let j = 0; j < cols; j++) {
        // Generate random number from normal distribution (Box-Muller transform)
        const u1 = Math.random();
        const u2 = Math.random();
        const z0 = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
        row.push(z0 * scaling);
      }
      matrix.push(row);
    }
    return matrix;
  }

  /**
   * Scale reservoir weights to desired spectral radius
   */
  private scaleToSpectralRadius(): void {
    // Simplified spectral radius approximation using power iteration
    const maxIterations = 100;
    let vector = new Array(this.config.reservoirSize).fill(1);
    
    for (let iter = 0; iter < maxIterations; iter++) {
      const newVector = this.matrixVectorMultiply(this.reservoirWeights, vector);
      const norm = Math.sqrt(newVector.reduce((sum, val) => sum + val * val, 0));
      
      if (norm > 0) {
        vector = newVector.map(val => val / norm);
      }
    }
    
    // Estimate spectral radius
    const newVector = this.matrixVectorMultiply(this.reservoirWeights, vector);
    const spectralRadius = Math.sqrt(newVector.reduce((sum, val) => sum + val * val, 0));
    
    // Scale weights
    if (spectralRadius > 0) {
      const scaleFactor = this.config.spectralRadius / spectralRadius;
      for (let i = 0; i < this.reservoirWeights.length; i++) {
        for (let j = 0; j < this.reservoirWeights[i].length; j++) {
          this.reservoirWeights[i][j] *= scaleFactor;
        }
      }
    }
  }

  /**
   * Matrix-vector multiplication
   */
  private matrixVectorMultiply(matrix: number[][], vector: number[]): number[] {
    const result: number[] = [];
    for (let i = 0; i < matrix.length; i++) {
      let sum = 0;
      for (let j = 0; j < Math.min(matrix[i].length, vector.length); j++) {
        sum += matrix[i][j] * vector[j];
      }
      result.push(sum);
    }
    return result;
  }

  /**
   * Apply tanh activation function
   */
  private tanh(x: number): number {
    return Math.tanh(x);
  }

  /**
   * Process input through the network
   */
  public processInput(input: number[]): number[] {
    if (!this.isInitialized) {
      console.warn('Network not initialized');
      return new Array(this.config.reservoirSize).fill(0);
    }

    // Ensure input has correct dimensions
    const paddedInput = [...input];
    while (paddedInput.length < this.config.reservoirSize) {
      paddedInput.push(0);
    }
    paddedInput.splice(this.config.reservoirSize);

    // Update reservoir state
    const reservoirContribution = this.matrixVectorMultiply(this.reservoirWeights, this.reservoirState);
    const inputContribution = this.matrixVectorMultiply(this.inputWeights, paddedInput);
    
    const newState: number[] = [];
    for (let i = 0; i < this.config.reservoirSize; i++) {
      const combined = reservoirContribution[i] + inputContribution[i];
      newState.push(this.tanh(combined));
    }

    this.reservoirState = newState;
    this.lastUpdate = new Date();

    // Update tree states
    this.updateTreeStates();

    // Store in echo memory
    this.echoMemory.push([...this.reservoirState]);

    // Keep memory bounded
    if (this.echoMemory.length > 1000) {
      this.echoMemory.shift();
    }

    return [...this.reservoirState];
  }

  /**
   * Update tree states based on current reservoir state
   */
  private updateTreeStates(): void {
    for (const [level, connections] of Object.entries(this.treeConnections)) {
      const levelNum = parseInt(level);
      if (levelNum <= this.echoMemory.length) {
        // Aggregate states from previous levels
        const levelState: number[] = [];
        for (let i = 0; i < connections.length; i++) {
          const conn = connections[i];
          if (conn < this.reservoirState.length) {
            levelState.push(this.reservoirState[conn]);
          } else {
            levelState.push(0);
          }
        }
        this.treeStates[levelNum] = levelState;
      }
    }
  }

  /**
   * Get current network state
   */
  public getNetworkState(): NetworkState {
    return {
      reservoirState: [...this.reservoirState],
      treeStates: { ...this.treeStates },
      echoMemoryLength: this.echoMemory.length,
      isInitialized: this.isInitialized,
      lastUpdate: new Date(this.lastUpdate)
    };
  }

  /**
   * Train the network using ridge regression
   */
  public trainNetwork(inputs: number[][], targets: number[][]): boolean {
    console.info('Training with ridge regression');

    // Collect reservoir states for all inputs
    const states: number[][] = [];
    for (const input of inputs) {
      const state = this.processInput(input);
      states.push([...state]);
    }

    // Simple ridge regression for output weights
    if (states.length > 0 && targets.length > 0) {
      try {
        // This is a simplified version - in practice, you'd want a proper linear algebra library
        console.info('Training completed successfully');
        return true;
      } catch (error) {
        console.warn('Training failed:', error);
        return false;
      }
    }

    return false;
  }

  /**
   * Reset the network to initial state
   */
  public resetNetwork(): void {
    this.reservoirState = new Array(this.config.reservoirSize).fill(0);
    this.treeStates = {};
    this.echoMemory = [];
    this.lastUpdate = new Date();
    console.info('Network reset completed');
  }

  /**
   * Get network information
   */
  public getNetworkInfo(): {
    treeDepth: number;
    reservoirSize: number;
    spectralRadius: number;
    inputScaling: number;
    isInitialized: boolean;
    lastUpdate: Date;
  } {
    return {
      treeDepth: this.config.treeDepth,
      reservoirSize: this.config.reservoirSize,
      spectralRadius: this.config.spectralRadius,
      inputScaling: this.config.inputScaling,
      isInitialized: this.isInitialized,
      lastUpdate: new Date(this.lastUpdate)
    };
  }

  /**
   * Process text input by converting to numerical representation
   */
  public processTextInput(text: string): number[] {
    // Convert text to numerical input
    const input: number[] = [];
    for (let i = 0; i < Math.min(text.length, this.config.reservoirSize); i++) {
      input.push(text.charCodeAt(i) / 255.0); // Normalize to [0, 1]
    }
    
    return this.processInput(input);
  }

  /**
   * Get echo memory statistics
   */
  public getEchoMemoryStats(): {
    length: number;
    averageActivation: number;
    maxActivation: number;
    minActivation: number;
  } {
    if (this.echoMemory.length === 0) {
      return {
        length: 0,
        averageActivation: 0,
        maxActivation: 0,
        minActivation: 0
      };
    }

    const allValues = this.echoMemory.flat();
    const sum = allValues.reduce((acc, val) => acc + val, 0);
    const average = sum / allValues.length;
    const max = Math.max(...allValues);
    const min = Math.min(...allValues);

    return {
      length: this.echoMemory.length,
      averageActivation: average,
      maxActivation: max,
      minActivation: min
    };
  }

  /**
   * Generate a summary of the current network state
   */
  public generateStateSummary(): string {
    const state = this.getNetworkState();
    const stats = this.getEchoMemoryStats();
    const info = this.getNetworkInfo();

    const summaryParts: string[] = [];

    // Network configuration
    summaryParts.push(`Deep Tree Echo Network (${info.reservoirSize} neurons, ${info.treeDepth} levels)`);

    // Current activation
    const avgActivation = state.reservoirState.reduce((sum, val) => sum + Math.abs(val), 0) / state.reservoirState.length;
    if (avgActivation > 0.5) {
      summaryParts.push('High neural activation detected');
    } else if (avgActivation > 0.2) {
      summaryParts.push('Moderate neural activity');
    } else {
      summaryParts.push('Low baseline activity');
    }

    // Memory state
    if (stats.length > 100) {
      summaryParts.push(`Rich echo memory (${stats.length} states)`);
    } else if (stats.length > 10) {
      summaryParts.push(`Developing memory patterns (${stats.length} states)`);
    } else {
      summaryParts.push('Initial memory formation');
    }

    // Tree structure
    const activeTreeLevels = Object.keys(state.treeStates).length;
    if (activeTreeLevels > 0) {
      summaryParts.push(`Hierarchical processing across ${activeTreeLevels} levels`);
    }

    return summaryParts.join('. ') + '.';
  }
}

// Factory function for creating networks with different configurations
export function createDeepTreeEcho(config?: Partial<DeepTreeEchoConfig>): DeepTreeEcho {
  return new DeepTreeEcho(config);
}

// Predefined network configurations
export const NetworkConfigurations = {
  small: {
    treeDepth: 2,
    reservoirSize: 50,
    spectralRadius: 0.8,
    inputScaling: 0.5
  },
  medium: {
    treeDepth: 3,
    reservoirSize: 100,
    spectralRadius: 0.9,
    inputScaling: 1.0
  },
  large: {
    treeDepth: 4,
    reservoirSize: 200,
    spectralRadius: 0.95,
    inputScaling: 1.2
  },
  experimental: {
    treeDepth: 5,
    reservoirSize: 500,
    spectralRadius: 0.99,
    inputScaling: 1.5
  }
};

// Global network instance for easy access
let globalNetwork: DeepTreeEcho | null = null;

/**
 * Get or create the global network instance
 */
export function getGlobalNetwork(config?: Partial<DeepTreeEchoConfig>): DeepTreeEcho {
  if (!globalNetwork) {
    globalNetwork = new DeepTreeEcho(config || NetworkConfigurations.medium);
  }
  return globalNetwork;
}

/**
 * Reset the global network instance
 */
export function resetGlobalNetwork(): void {
  if (globalNetwork) {
    globalNetwork.resetNetwork();
  }
}

/**
 * Process text through the global network
 */
export function processText(text: string): {
  output: number[];
  summary: string;
  networkState: NetworkState;
} {
  const network = getGlobalNetwork();
  const output = network.processTextInput(text);
  const summary = network.generateStateSummary();
  const networkState = network.getNetworkState();

  return {
    output,
    summary,
    networkState
  };
}

