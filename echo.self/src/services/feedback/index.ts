/**
 * Adaptive Feedback Loop - Entry Point
 *
 * Exports all components of the adaptive, hypergraph-encoded feedback loop
 * for DeepTreeEcho's distributed cognition framework
 */

// Core hypergraph implementation
export {
  HypergraphSchemeCore,
  type HypergraphNode,
  type CognitivePattern,
  type SalienceMetrics,
} from "./hypergraphSchemeCore";

// Main feedback service
export {
  AdaptiveFeedbackService,
  type ProjectModel,
  type CommunityFeedback,
  type CopilotRequest,
  type CopilotResponse,
  type AdaptiveThresholds,
} from "./adaptiveFeedbackService";

// Integration with orchestrator
export {
  FeedbackIntegrationService,
  useAdaptiveFeedback,
} from "./feedbackIntegrationService";

// Import for convenience function
import { FeedbackIntegrationService } from "./feedbackIntegrationService";

// Convenience function to initialize the complete feedback system
export const initializeAdaptiveFeedbackSystem = () => {
  const integrationService = FeedbackIntegrationService.getInstance();
  console.log("🚀 Adaptive feedback system initialized");
  return integrationService;
};
