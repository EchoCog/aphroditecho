/**
 * Adaptive Feedback Loop Service for DeepTreeEcho's Distributed Cognition Framework
 *
 * Implements the complete feedback loop as outlined in the problem statement:
 * - Collects salient project models and community feedback
 * - Scores models using semantic salience
 * - Queries Copilot with prioritized wishlist
 * - Integrates upgrades into local repository
 * - Broadcasts improvements to community
 */

import {
  HypergraphSchemeCore,
  HypergraphNode,
  SalienceMetrics,
} from "./hypergraphSchemeCore";

// Types for the feedback loop
export interface ProjectModel {
  id: string;
  name: string;
  description: string;
  version: string;
  lastModified: Date;
  usageCount: number;
  communityFeedback: CommunityFeedback[];
  salienceScore: number;
}

export interface CommunityFeedback {
  id: string;
  modelId: string;
  userId: string;
  type: "improvement" | "bug" | "feature_request" | "performance";
  priority: "low" | "medium" | "high" | "urgent";
  description: string;
  timestamp: Date;
  votes: number;
}

export interface CopilotRequest {
  modelId: string;
  priority: number;
  requestType: "upgrade" | "optimization" | "feature_addition";
  context: string;
  requirements: string[];
}

export interface CopilotResponse {
  requestId: string;
  modelId: string;
  upgradedContent: string;
  improvements: string[];
  version: string;
  confidence: number;
}

export interface AdaptiveThresholds {
  cognitiveLoad: number;
  recentActivity: number;
  feedbackUrgency: number;
  attentionThreshold: number;
}

/**
 * Main Adaptive Feedback Loop Service
 * Acts as the autonomous orchestrator in the admin layer
 */
export class AdaptiveFeedbackService {
  private static instance: AdaptiveFeedbackService;
  private hypergraphCore: HypergraphSchemeCore;
  private projectModels: Map<string, ProjectModel> = new Map();
  private communityFeedback: Map<string, CommunityFeedback> = new Map();
  private adaptiveThresholds: AdaptiveThresholds;
  private lastFeedbackCycle: Date = new Date();
  private feedbackCycleInterval: number = 5 * 60 * 1000; // 5 minutes

  private constructor() {
    this.hypergraphCore = new HypergraphSchemeCore();
    this.adaptiveThresholds = {
      cognitiveLoad: 0.3,
      recentActivity: 0.7,
      feedbackUrgency: 0.5,
      attentionThreshold: 0.6,
    };

    this.initializeFeedbackLoop();
  }

  public static getInstance(): AdaptiveFeedbackService {
    if (!AdaptiveFeedbackService.instance) {
      AdaptiveFeedbackService.instance = new AdaptiveFeedbackService();
    }
    return AdaptiveFeedbackService.instance;
  }

  /**
   * Initialize the feedback loop with hypergraph patterns
   */
  private initializeFeedbackLoop(): void {
    // Create core feedback loop nodes in the hypergraph
    this.hypergraphCore.createNode(
      "feedback-collector",
      "procedure",
      {
        description: "Collects salient project models and community feedback",
        priority: 0.9,
      },
      []
    );

    this.hypergraphCore.createNode(
      "salience-scorer",
      "procedure",
      {
        description: "Scores models using semantic salience",
        priority: 0.85,
      },
      ["feedback-collector"]
    );

    this.hypergraphCore.createNode(
      "copilot-interface",
      "procedure",
      {
        description: "Queries Copilot with prioritized wishlist",
        priority: 0.8,
      },
      ["salience-scorer"]
    );

    this.hypergraphCore.createNode(
      "model-integrator",
      "procedure",
      {
        description: "Integrates upgrades into local repository",
        priority: 0.75,
      },
      ["copilot-interface"]
    );

    this.hypergraphCore.createNode(
      "community-broadcaster",
      "procedure",
      {
        description: "Broadcasts improvements to community",
        priority: 0.7,
      },
      ["model-integrator"]
    );

    // Set up the feedback cycle
    this.startFeedbackCycle();
  }

  /**
   * Main feedback loop cycle - runs autonomously
   */
  private startFeedbackCycle(): void {
    setInterval(() => {
      this.executeFeedbackLoop();
    }, this.feedbackCycleInterval);
  }

  /**
   * Execute a complete feedback loop cycle
   */
  public async executeFeedbackLoop(): Promise<void> {
    console.log("🔄 Starting adaptive feedback loop cycle...");

    try {
      // 1. Update adaptive thresholds based on current system state
      this.updateAdaptiveThresholds();

      // 2. Collect salient project models and community feedback
      const salientModels = await this.collectSalientModels();

      // 3. Score models using semantic salience
      const scoredModels = this.scoreModelsSalience(salientModels);

      // 4. Query Copilot with prioritized wishlist
      const prioritizedRequests = this.buildCopilotWishlist(scoredModels);
      const copilotResponses = await this.queryCopilot(prioritizedRequests);

      // 5. Integrate upgrades into local repository
      const integratedModels = await this.integrateUpgrades(copilotResponses);

      // 6. Broadcast improvements to community
      await this.broadcastImprovements(integratedModels);

      // 7. Update hypergraph with new patterns
      this.updateHypergraphPatterns();

      console.log(
        `✅ Feedback loop completed. Processed ${scoredModels.length} models, integrated ${integratedModels.length} upgrades`
      );
    } catch (error) {
      console.error("❌ Error in feedback loop execution:", error);
    }

    this.lastFeedbackCycle = new Date();
  }

  /**
   * Adaptive attention allocation - dynamically adjust thresholds
   * Implements the mechanism from echoself.md
   */
  private updateAdaptiveThresholds(): void {
    // Calculate cognitive load based on system activity
    const currentLoad = this.calculateCognitiveLoad();

    // Calculate recent activity based on feedback and model updates
    const recentActivity = this.calculateRecentActivity();

    // Update attention threshold using adaptive mechanism
    const newThreshold = this.hypergraphCore.adaptiveAttention(
      currentLoad,
      recentActivity
    );
    this.adaptiveThresholds.attentionThreshold = newThreshold;

    // Update hypergraph core with new threshold
    this.hypergraphCore.updateAttentionThreshold(newThreshold);

    console.log(
      `🧠 Adaptive thresholds updated: load=${currentLoad.toFixed(3)}, activity=${recentActivity.toFixed(3)}, threshold=${newThreshold.toFixed(3)}`
    );
  }

  /**
   * Calculate current cognitive load based on system metrics
   */
  private calculateCognitiveLoad(): number {
    const activeNodes = this.hypergraphCore.getAllNodes().length;
    const feedbackVolume = this.communityFeedback.size;
    const processingQueue = this.projectModels.size;

    // Normalize to 0-1 range
    const load = Math.min(
      (activeNodes + feedbackVolume + processingQueue) / 100,
      1.0
    );
    this.adaptiveThresholds.cognitiveLoad = load;

    return load;
  }

  /**
   * Calculate recent activity level
   */
  private calculateRecentActivity(): number {
    const now = Date.now();
    const hourAgo = now - 60 * 60 * 1000;

    // Count recent feedback and model updates
    const recentFeedback = Array.from(this.communityFeedback.values()).filter(
      feedback => feedback.timestamp.getTime() > hourAgo
    ).length;

    const recentModels = Array.from(this.projectModels.values()).filter(
      model => model.lastModified.getTime() > hourAgo
    ).length;

    // Normalize to 0-1 range
    const activity = Math.min((recentFeedback + recentModels) / 10, 1.0);
    this.adaptiveThresholds.recentActivity = activity;

    return activity;
  }

  /**
   * Collect salient project models based on attention allocation
   */
  private async collectSalientModels(): Promise<ProjectModel[]> {
    // Get attention-filtered nodes from hypergraph
    const attentionNodes = this.hypergraphCore.getAttentionFilteredNodes(
      this.adaptiveThresholds.attentionThreshold
    );

    // Convert relevant nodes to project models
    const salientModels: ProjectModel[] = [];

    for (const node of attentionNodes) {
      if (node.type === "model" || node.type === "concept") {
        const model = this.nodeToProjectModel(node);
        if (model) {
          salientModels.push(model);
        }
      }
    }

    // Also collect models with urgent community feedback
    const urgentModels = this.getModelsWithUrgentFeedback();
    salientModels.push(...urgentModels);

    // Remove duplicates
    const uniqueModels = salientModels.filter(
      (model, index, self) => index === self.findIndex(m => m.id === model.id)
    );

    console.log(
      `📊 Collected ${uniqueModels.length} salient models (threshold: ${this.adaptiveThresholds.attentionThreshold.toFixed(3)})`
    );

    return uniqueModels;
  }

  /**
   * Convert hypergraph node to project model
   */
  private nodeToProjectModel(node: HypergraphNode): ProjectModel | null {
    try {
      return {
        id: node.id,
        name: node.content.name || node.id,
        description:
          node.content.description || "Generated from hypergraph node",
        version: node.content.version || "1.0.0",
        lastModified: node.lastUpdated,
        usageCount: node.content.usageCount || 0,
        communityFeedback: this.getFeedbackForModel(node.id),
        salienceScore: node.salience,
      };
    } catch (error) {
      console.warn(
        `Warning: Failed to convert node ${node.id} to project model:`,
        error
      );
      return null;
    }
  }

  /**
   * Get community feedback for a specific model
   */
  private getFeedbackForModel(modelId: string): CommunityFeedback[] {
    return Array.from(this.communityFeedback.values()).filter(
      feedback => feedback.modelId === modelId
    );
  }

  /**
   * Get models with urgent community feedback
   */
  private getModelsWithUrgentFeedback(): ProjectModel[] {
    const urgentFeedback = Array.from(this.communityFeedback.values()).filter(
      feedback => feedback.priority === "urgent"
    );

    const urgentModelIds = Array.from(
      new Set(urgentFeedback.map(f => f.modelId))
    );

    return urgentModelIds
      .map(id => this.projectModels.get(id))
      .filter(model => model !== undefined) as ProjectModel[];
  }

  /**
   * Score models using semantic salience
   */
  private scoreModelsSalience(models: ProjectModel[]): ProjectModel[] {
    return models
      .map(model => {
        // Get usage history (mocked for now)
        const usageHistory = Array(model.usageCount).fill(null);

        // Calculate comprehensive salience metrics
        const metrics = this.hypergraphCore.calculateSalienceMetrics(
          model.id,
          usageHistory
        );

        // Factor in community feedback urgency
        const feedbackUrgency = this.calculateFeedbackUrgency(model);

        // Combine metrics with weights: demand (40%), freshness (30%), urgency (30%)
        const combinedScore =
          metrics.demand * 0.4 +
          metrics.freshness * 0.3 +
          feedbackUrgency * 0.3;

        model.salienceScore = combinedScore;

        return model;
      })
      .sort((a, b) => b.salienceScore - a.salienceScore);
  }

  /**
   * Calculate feedback urgency score for a model
   */
  private calculateFeedbackUrgency(model: ProjectModel): number {
    if (model.communityFeedback.length === 0) return 0;

    const urgencyWeights = { urgent: 1.0, high: 0.8, medium: 0.6, low: 0.3 };

    const weightedUrgency =
      model.communityFeedback.reduce((sum, feedback) => {
        return (
          sum + urgencyWeights[feedback.priority] * (1 + feedback.votes * 0.1)
        );
      }, 0) / model.communityFeedback.length;

    return Math.min(weightedUrgency, 1.0);
  }

  /**
   * Build prioritized wishlist for Copilot
   */
  private buildCopilotWishlist(scoredModels: ProjectModel[]): CopilotRequest[] {
    const maxRequests = 5; // Limit to top 5 models to avoid overwhelming Copilot

    return scoredModels.slice(0, maxRequests).map((model, index) => ({
      modelId: model.id,
      priority: model.salienceScore,
      requestType: this.determineRequestType(model),
      context: this.buildModelContext(model),
      requirements: this.extractRequirements(model),
    }));
  }

  /**
   * Determine request type based on model feedback
   */
  private determineRequestType(
    model: ProjectModel
  ): CopilotRequest["requestType"] {
    const feedbackTypes = model.communityFeedback.map(f => f.type);

    if (feedbackTypes.includes("performance")) return "optimization";
    if (feedbackTypes.includes("feature_request")) return "feature_addition";
    return "upgrade";
  }

  /**
   * Build context string for Copilot request
   */
  private buildModelContext(model: ProjectModel): string {
    const feedback = model.communityFeedback
      .map(f => `${f.type}: ${f.description}`)
      .join("; ");

    return `Model: ${model.name} (v${model.version})\nDescription: ${model.description}\nFeedback: ${feedback}`;
  }

  /**
   * Extract requirements from community feedback
   */
  private extractRequirements(model: ProjectModel): string[] {
    return model.communityFeedback
      .filter(f => f.priority === "high" || f.priority === "urgent")
      .map(f => f.description);
  }

  /**
   * Query Copilot with prioritized requests (MOCKED)
   * This provides clear extension points for real Copilot API integration
   */
  private async queryCopilot(
    requests: CopilotRequest[]
  ): Promise<CopilotResponse[]> {
    console.log(
      `🤖 Querying Copilot with ${requests.length} prioritized requests...`
    );

    // MOCK IMPLEMENTATION - Replace with real Copilot API calls
    const responses: CopilotResponse[] = [];

    for (const request of requests) {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 500));

      const mockResponse: CopilotResponse = {
        requestId: `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        modelId: request.modelId,
        upgradedContent: this.generateMockUpgrade(request),
        improvements: this.generateMockImprovements(request),
        version: this.incrementVersion(request.modelId),
        confidence: 0.85 + Math.random() * 0.15, // 0.85-1.0
      };

      responses.push(mockResponse);
    }

    console.log(`✨ Received ${responses.length} Copilot responses`);
    return responses;
  }

  /**
   * Generate mock upgrade content (to be replaced with real Copilot integration)
   */
  private generateMockUpgrade(request: CopilotRequest): string {
    return `
// Enhanced ${request.modelId} - Generated by Copilot
// Priority: ${request.priority.toFixed(3)}
// Request Type: ${request.requestType}

// Improvements based on requirements:
${request.requirements.map(req => `// - ${req}`).join("\n")}

// Mock implementation follows hypergraph-encoded patterns
(define (enhanced-${request.modelId.replace(/[^a-zA-Z0-9]/g, "-")} context)
  ;; Enhanced cognitive processing with improved salience
  (let ((processed-context (apply-salience-filter context ${request.priority.toFixed(3)})))
    (hypergraph-encode processed-context)))

// Integration ready with DeepTreeEcho framework
`;
  }

  /**
   * Generate mock improvements list
   */
  private generateMockImprovements(request: CopilotRequest): string[] {
    const baseImprovements = [
      "Enhanced hypergraph pattern encoding",
      "Improved adaptive attention allocation",
      "Optimized semantic salience calculation",
      "Better integration with cognitive framework",
    ];

    const typeSpecificImprovements = {
      upgrade: ["Updated core algorithms", "Enhanced performance metrics"],
      optimization: ["Reduced cognitive load", "Faster pattern recognition"],
      feature_addition: [
        "New community feedback integration",
        "Enhanced broadcasting capabilities",
      ],
    };

    return [
      ...baseImprovements,
      ...typeSpecificImprovements[request.requestType],
    ];
  }

  /**
   * Increment model version
   */
  private incrementVersion(modelId: string): string {
    const model = this.projectModels.get(modelId);
    if (!model) return "1.0.1";

    const [major, minor, patch] = model.version.split(".").map(Number);
    return `${major}.${minor}.${patch + 1}`;
  }

  /**
   * Integrate Copilot upgrades into local repository
   */
  private async integrateUpgrades(
    responses: CopilotResponse[]
  ): Promise<ProjectModel[]> {
    console.log(`🔧 Integrating ${responses.length} Copilot upgrades...`);

    const integratedModels: ProjectModel[] = [];

    for (const response of responses) {
      try {
        // Update or create model with upgraded content
        const existingModel = this.projectModels.get(response.modelId);

        const upgradedModel: ProjectModel = {
          id: response.modelId,
          name: existingModel?.name || response.modelId,
          description: `${existingModel?.description || "Model"} - Enhanced by Copilot`,
          version: response.version,
          lastModified: new Date(),
          usageCount: existingModel?.usageCount || 0,
          communityFeedback: existingModel?.communityFeedback || [],
          salienceScore: existingModel?.salienceScore || 0.5,
        };

        // Store upgraded model
        this.projectModels.set(response.modelId, upgradedModel);

        // Update hypergraph with new version
        this.hypergraphCore.createNode(
          `${response.modelId}-v${response.version}`,
          "model",
          {
            content: response.upgradedContent,
            improvements: response.improvements,
            confidence: response.confidence,
            version: response.version,
          },
          [response.modelId] // Link to original model
        );

        integratedModels.push(upgradedModel);

        console.log(
          `✅ Integrated ${response.modelId} v${response.version} (confidence: ${response.confidence.toFixed(3)})`
        );
      } catch (error) {
        console.error(`❌ Failed to integrate ${response.modelId}:`, error);
      }
    }

    return integratedModels;
  }

  /**
   * Broadcast improvements to community/project nodes
   */
  private async broadcastImprovements(models: ProjectModel[]): Promise<void> {
    console.log(
      `📡 Broadcasting ${models.length} model improvements to community...`
    );

    for (const model of models) {
      // Create broadcast message
      const broadcastMessage = {
        type: "model_improvement",
        modelId: model.id,
        version: model.version,
        timestamp: new Date(),
        improvements: this.extractImprovements(model),
        salienceScore: model.salienceScore,
      };

      // Simulate broadcasting to different community nodes
      const communityNodes = ["project-alpha", "project-beta", "community-hub"];

      for (const node of communityNodes) {
        // Mock broadcast implementation
        await this.sendBroadcast(node, broadcastMessage);
      }
    }

    console.log(`✅ Broadcast completed to community nodes`);
  }

  /**
   * Extract improvements from model
   */
  private extractImprovements(model: ProjectModel): string[] {
    // Extract from hypergraph node if available
    const node = this.hypergraphCore.getNode(`${model.id}-v${model.version}`);
    return (
      node?.content?.improvements || ["General improvements and optimizations"]
    );
  }

  /**
   * Send broadcast to community node (mocked)
   */
  private async sendBroadcast(nodeId: string, message: any): Promise<void> {
    // Mock implementation - replace with real community broadcasting
    await new Promise(resolve => setTimeout(resolve, 100));
    console.log(
      `📤 Broadcast sent to ${nodeId}: ${message.type} for ${message.modelId}`
    );
  }

  /**
   * Update hypergraph patterns after feedback cycle
   */
  private updateHypergraphPatterns(): void {
    // Mine new cognitive patterns from the updated atomspace
    const newPatterns = this.hypergraphCore.mineCognitivePatterns(0.7);

    // Embody significant patterns as new nodes
    newPatterns
      .filter(pattern => pattern.strength > 0.8)
      .forEach(pattern => {
        this.hypergraphCore.embodyPattern(pattern);
      });

    // Spread attention from high-salience nodes
    const highSalienceNodes = this.hypergraphCore
      .getAllNodes()
      .filter(node => node.salience > 0.8);

    highSalienceNodes.forEach(node => {
      this.hypergraphCore.spreadAttention(node.id, 0.1);
    });

    console.log(
      `🧩 Updated hypergraph: ${newPatterns.length} new patterns, ${highSalienceNodes.length} attention spreads`
    );
  }

  // Public API methods for external integration

  /**
   * Add community feedback
   */
  public addCommunityFeedback(
    feedback: Omit<CommunityFeedback, "id" | "timestamp">
  ): void {
    const id = `feedback-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const completeFeedback: CommunityFeedback = {
      ...feedback,
      id,
      timestamp: new Date(),
    };

    this.communityFeedback.set(id, completeFeedback);

    // Update urgency threshold if urgent feedback received
    if (feedback.priority === "urgent") {
      this.adaptiveThresholds.feedbackUrgency = Math.min(
        this.adaptiveThresholds.feedbackUrgency + 0.2,
        1.0
      );
    }
  }

  /**
   * Register a new project model
   */
  public registerProjectModel(
    model: Omit<ProjectModel, "communityFeedback" | "salienceScore">
  ): void {
    const completeModel: ProjectModel = {
      ...model,
      communityFeedback: [],
      salienceScore: 0.5,
    };

    this.projectModels.set(model.id, completeModel);

    // Add to hypergraph
    this.hypergraphCore.createNode(
      model.id,
      "model",
      {
        name: model.name,
        description: model.description,
        version: model.version,
        usageCount: model.usageCount,
      },
      []
    );
  }

  /**
   * Get current system status
   */
  public getSystemStatus() {
    return {
      adaptiveThresholds: this.adaptiveThresholds,
      lastFeedbackCycle: this.lastFeedbackCycle,
      projectModelsCount: this.projectModels.size,
      communityFeedbackCount: this.communityFeedback.size,
      hypergraphNodesCount: this.hypergraphCore.getAllNodes().length,
      attentionFilteredNodes:
        this.hypergraphCore.getAttentionFilteredNodes().length,
    };
  }

  /**
   * Manually trigger feedback loop (for testing/immediate execution)
   */
  public async triggerFeedbackLoop(): Promise<void> {
    return this.executeFeedbackLoop();
  }

  /**
   * Update feedback cycle interval
   */
  public setFeedbackCycleInterval(intervalMs: number): void {
    this.feedbackCycleInterval = Math.max(intervalMs, 30000); // Minimum 30 seconds
  }
}
