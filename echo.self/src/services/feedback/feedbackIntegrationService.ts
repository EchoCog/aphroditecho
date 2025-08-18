/**
 * Feedback Integration Service
 *
 * Integrates the adaptive feedback loop with the existing orchestrator service
 * and provides a React hook for UI components
 */

import {
  AdaptiveFeedbackService,
  ProjectModel,
  CommunityFeedback,
} from "./adaptiveFeedbackService";
import { OrchestratorService } from "../orchestratorService";

/**
 * Integration service that bridges feedback loop with orchestrator
 */
export class FeedbackIntegrationService {
  private static instance: FeedbackIntegrationService;
  private feedbackService: AdaptiveFeedbackService;
  private orchestratorService: OrchestratorService;
  private isInitialized: boolean = false;

  private constructor() {
    this.feedbackService = AdaptiveFeedbackService.getInstance();
    this.orchestratorService = OrchestratorService.getInstance();
    this.initializeIntegration();
  }

  public static getInstance(): FeedbackIntegrationService {
    if (!FeedbackIntegrationService.instance) {
      FeedbackIntegrationService.instance = new FeedbackIntegrationService();
    }
    return FeedbackIntegrationService.instance;
  }

  /**
   * Initialize integration with orchestrator service
   */
  private initializeIntegration(): void {
    // Register feedback service as a component in orchestrator
    this.orchestratorService.registerComponent("adaptive-feedback", {
      status: "active",
      type: "admin-service",
      capabilities: [
        "model-collection",
        "salience-scoring",
        "copilot-integration",
        "community-broadcasting",
      ],
      getStatus: () => this.feedbackService.getSystemStatus(),
      triggerCycle: () => this.feedbackService.triggerFeedbackLoop(),
    });

    // Listen for orchestrator events that might affect feedback
    this.orchestratorService.addEventListener("component_registered", (data: any) => {
      console.log(`🔗 Component registered: ${data.componentId}`);
      // Could trigger feedback collection if new models are available
    });

    this.orchestratorService.addEventListener("content_transfer", (data: any) => {
      console.log(`📤 Content transfer: ${data.from} → ${data.to}`);
      // Could update model usage statistics
    });

    this.isInitialized = true;
    console.log("✅ Feedback integration service initialized");
  }

  /**
   * Add feedback through the orchestrator integration
   */
  public addFeedback(
    feedback: Omit<CommunityFeedback, "id" | "timestamp">
  ): void {
    this.feedbackService.addCommunityFeedback(feedback);

    // Notify orchestrator of new feedback (would need to access dispatchEvent)
    // this.orchestratorService.dispatchEvent?.('feedback_added', {
    //   modelId: feedback.modelId,
    //   priority: feedback.priority,
    //   type: feedback.type
    // });
  }

  /**
   * Register model through the orchestrator integration
   */
  public registerModel(
    model: Omit<ProjectModel, "communityFeedback" | "salienceScore">
  ): void {
    this.feedbackService.registerProjectModel(model);

    // Notify orchestrator of new model (would need to access dispatchEvent)
    // this.orchestratorService.dispatchEvent?.('model_registered', {
    //   modelId: model.id,
    //   name: model.name
    // });
  }

  /**
   * Get status for orchestrator dashboard
   */
  public getIntegrationStatus() {
    return {
      isInitialized: this.isInitialized,
      feedbackService: this.feedbackService.getSystemStatus(),
      orchestratorConnected:
        this.orchestratorService.isComponentRegistered("adaptive-feedback"),
    };
  }

  /**
   * Manually trigger feedback loop through orchestrator
   */
  public async triggerFeedbackLoop(): Promise<void> {
    console.log("🎯 Feedback loop triggered via orchestrator integration");
    return this.feedbackService.triggerFeedbackLoop();
  }
}

/**
 * React hook for using the adaptive feedback service in components
 */
export const useAdaptiveFeedback = () => {
  const integrationService = FeedbackIntegrationService.getInstance();
  const feedbackService = AdaptiveFeedbackService.getInstance();

  return {
    // Core feedback operations
    addFeedback: (feedback: Omit<CommunityFeedback, "id" | "timestamp">) =>
      integrationService.addFeedback(feedback),

    registerModel: (
      model: Omit<ProjectModel, "communityFeedback" | "salienceScore">
    ) => integrationService.registerModel(model),

    // System status and monitoring
    getStatus: () => integrationService.getIntegrationStatus(),

    // Manual control
    triggerFeedbackLoop: () => integrationService.triggerFeedbackLoop(),

    // Configuration
    setFeedbackInterval: (intervalMs: number) =>
      feedbackService.setFeedbackCycleInterval(intervalMs),

    // Direct access to feedback service for advanced operations
    getFeedbackService: () => feedbackService,
  };
};

export default FeedbackIntegrationService;
