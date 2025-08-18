/**
 * Hypergraph-Encoded Scheme Core for DeepTreeEcho Cognitive Framework
 *
 * Implements the core Scheme-based hypergraph logic following the patterns
 * outlined in echoself.md and COGPRIME_ARCHITECTURE_DIAGRAM.md
 */

// Types for hypergraph node representation
export interface HypergraphNode {
  id: string;
  type: "concept" | "procedure" | "goal" | "pattern" | "model";
  content: any;
  links: string[];
  salience: number;
  attention: number;
  lastUpdated: Date;
}

// Types for cognitive patterns
export interface CognitivePattern {
  id: string;
  pattern: string;
  strength: number;
  confidence: number;
  frequency: number;
  context: string[];
}

// Types for semantic salience assessment
export interface SalienceMetrics {
  demand: number; // 0-1 based on usage frequency
  freshness: number; // 0-1 based on recency
  urgency: number; // 0-1 based on feedback priority
  overall: number; // weighted combination
}

/**
 * Core Scheme-like interpreter for hypergraph operations
 * Implements the hypergraph encoding patterns from echoself.md
 */
export class HypergraphSchemeCore {
  private atomSpace: Map<string, HypergraphNode> = new Map();
  private patterns: Map<string, CognitivePattern> = new Map();
  private attentionThreshold: number = 0.5;

  constructor() {
    this.initializeAtomSpace();
  }

  /**
   * Initialize the atomspace with basic cognitive structures
   * Following the pattern from echoself.md
   */
  private initializeAtomSpace(): void {
    // Create foundational nodes as per echoself.md specifications
    this.createNode(
      "deep-tree-echo",
      "concept",
      {
        description: "Core cognitive architecture",
        capabilities: [
          "neural-symbolic-reasoning",
          "adaptive-attention",
          "hypergraph-encoding",
        ],
      },
      []
    );
  }

  /**
   * Scheme-like function: make-node
   * (define (make-node id type content links))
   */
  public createNode(
    id: string,
    type: HypergraphNode["type"],
    content: any,
    links: string[]
  ): HypergraphNode {
    const node: HypergraphNode = {
      id,
      type,
      content,
      links,
      salience: this.calculateSemanticSalience(id, content),
      attention: 0.5, // Initial attention value
      lastUpdated: new Date(),
    };

    this.atomSpace.set(id, node);
    return node;
  }

  /**
   * Scheme-like function: semantic-salience
   * (define (semantic-salience path))
   * Implements the salience heuristics from echoself.md
   */
  private calculateSemanticSalience(id: string, content: any): number {
    let salience = 0.5; // Base salience

    // Core directories/files get higher salience (from echoself.md)
    if (id.includes("AtomSpace") || id.includes("core")) {
      salience = 0.95;
    } else if (id.includes("src") || id.includes("models")) {
      salience = 0.85;
    } else if (id.includes("README") || id.includes("docs")) {
      salience = 0.8;
    }

    // Content-based salience adjustments
    if (typeof content === "object" && content.importance) {
      salience = Math.max(salience, content.importance);
    }

    return Math.min(salience, 1.0);
  }

  /**
   * Adaptive attention allocation mechanism from echoself.md
   * (define (adaptive-attention current-load recent-activity))
   */
  public adaptiveAttention(
    currentLoad: number,
    recentActivity: number
  ): number {
    // High load or low activity leads to higher threshold (less data)
    return 0.5 + currentLoad * 0.3 + (0.2 - recentActivity);
  }

  /**
   * Attention-weighted hypergraph dynamics
   * Implements ECAN spreading dynamics from COGPRIME documentation
   */
  public spreadAttention(
    sourceNodeId: string,
    spreadingFactor: number = 0.1
  ): void {
    const sourceNode = this.atomSpace.get(sourceNodeId);
    if (!sourceNode) return;

    // Spread attention to linked nodes
    sourceNode.links.forEach(linkedNodeId => {
      const linkedNode = this.atomSpace.get(linkedNodeId);
      if (linkedNode) {
        const spreadAmount = sourceNode.attention * spreadingFactor;
        linkedNode.attention += spreadAmount;
        linkedNode.attention = Math.min(linkedNode.attention, 1.0);
      }
    });
  }

  /**
   * Process nodes by attention threshold
   * (define (process-by-attention atomspace threshold))
   */
  public getAttentionFilteredNodes(threshold?: number): HypergraphNode[] {
    const effectiveThreshold = threshold || this.attentionThreshold;
    return Array.from(this.atomSpace.values()).filter(
      node => node.attention > effectiveThreshold
    );
  }

  /**
   * Pattern mining for cognitive equation implementation
   * (define (mine-cognitive-patterns atomspace pattern-threshold))
   */
  public mineCognitivePatterns(
    patternThreshold: number = 0.7
  ): CognitivePattern[] {
    const discoveredPatterns: CognitivePattern[] = [];
    const nodes = Array.from(this.atomSpace.values());

    // Find frequent subgraph patterns
    const frequentSubgraphs = this.findFrequentSubgraphs(
      nodes,
      patternThreshold
    );

    frequentSubgraphs.forEach((pattern, index) => {
      const cognitivePattern: CognitivePattern = {
        id: `pattern-${index}`,
        pattern: JSON.stringify(pattern),
        strength: this.calculatePatternStrength(pattern),
        confidence: 0.85,
        frequency: pattern.frequency || 1,
        context: pattern.context || [],
      };

      discoveredPatterns.push(cognitivePattern);
      this.patterns.set(cognitivePattern.id, cognitivePattern);
    });

    return discoveredPatterns;
  }

  /**
   * Find frequent subgraphs in the hypergraph structure
   */
  private findFrequentSubgraphs(
    nodes: HypergraphNode[],
    threshold: number
  ): any[] {
    // Simplified pattern detection - look for common link structures
    const linkPatterns = new Map<string, number>();

    nodes.forEach(node => {
      if (node.links.length > 0) {
        const patternKey = node.links.sort().join("-");
        linkPatterns.set(patternKey, (linkPatterns.get(patternKey) || 0) + 1);
      }
    });

    return Array.from(linkPatterns.entries())
      .filter(([_, frequency]) => frequency >= threshold)
      .map(([pattern, frequency]) => ({
        pattern,
        frequency,
        context: pattern.split("-"),
      }));
  }

  /**
   * Calculate pattern strength for discovered patterns
   */
  private calculatePatternStrength(pattern: any): number {
    // Simple strength calculation based on frequency and context
    const baseStrength = Math.min(pattern.frequency / 10, 1.0);
    const contextBonus = pattern.context.length * 0.1;
    return Math.min(baseStrength + contextBonus, 1.0);
  }

  /**
   * Embody discovered patterns as new atoms
   * (define (embody-pattern pattern strength))
   */
  public embodyPattern(pattern: CognitivePattern): HypergraphNode {
    const patternNode = this.createNode(
      `pattern-node-${pattern.id}`,
      "pattern",
      {
        pattern: pattern.pattern,
        strength: pattern.strength,
        confidence: pattern.confidence,
      },
      pattern.context
    );

    // Set attention based on pattern strength
    patternNode.attention = pattern.strength;

    return patternNode;
  }

  /**
   * Update attention threshold dynamically
   */
  public updateAttentionThreshold(threshold: number): void {
    this.attentionThreshold = Math.max(0.1, Math.min(threshold, 1.0));
  }

  /**
   * Get node by ID
   */
  public getNode(id: string): HypergraphNode | undefined {
    return this.atomSpace.get(id);
  }

  /**
   * Get all nodes in atomspace
   */
  public getAllNodes(): HypergraphNode[] {
    return Array.from(this.atomSpace.values());
  }

  /**
   * Create a link between two nodes
   */
  public createLink(fromNodeId: string, toNodeId: string): boolean {
    const fromNode = this.atomSpace.get(fromNodeId);
    const toNode = this.atomSpace.get(toNodeId);

    if (fromNode && toNode) {
      if (!fromNode.links.includes(toNodeId)) {
        fromNode.links.push(toNodeId);
      }
      if (!toNode.links.includes(fromNodeId)) {
        toNode.links.push(fromNodeId);
      }
      return true;
    }
    return false;
  }

  /**
   * Calculate comprehensive salience metrics
   */
  public calculateSalienceMetrics(
    nodeId: string,
    usageHistory: any[] = []
  ): SalienceMetrics {
    const node = this.atomSpace.get(nodeId);
    if (!node) {
      return { demand: 0, freshness: 0, urgency: 0, overall: 0 };
    }

    // Calculate demand based on usage frequency
    const demand = Math.min(usageHistory.length / 10, 1.0);

    // Calculate freshness based on last update
    const daysSinceUpdate =
      (Date.now() - node.lastUpdated.getTime()) / (1000 * 60 * 60 * 24);
    const freshness = Math.max(0, 1 - daysSinceUpdate / 30); // Decay over 30 days

    // Calculate urgency based on attention and recent activity
    const urgency = node.attention;

    // Overall weighted combination
    const overall = demand * 0.4 + freshness * 0.3 + urgency * 0.3;

    return { demand, freshness, urgency, overall };
  }
}
