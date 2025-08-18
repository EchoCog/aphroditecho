/**
 * Demonstration of Adaptive Feedback Loop Integration
 *
 * Shows how to use the adaptive feedback system in a real application
 */

import {
  initializeAdaptiveFeedbackSystem,
  useAdaptiveFeedback,
  AdaptiveFeedbackService,
} from "./index";
import process from "node:process";

/**
 * Example: Initialize and run the feedback system
 */
export function demonstrateAdaptiveFeedbackLoop() {
  console.log("🚀 Demonstrating Adaptive Feedback Loop...\n");

  // 1. Initialize the system
  console.log("1. Initializing adaptive feedback system...");
  const feedbackSystem = initializeAdaptiveFeedbackSystem();
  const feedbackService = AdaptiveFeedbackService.getInstance();

  // 2. Register some example project models
  console.log("2. Registering project models...");

  const exampleModels = [
    {
      id: "neural-attention-model",
      name: "Neural Attention Model",
      description: "Advanced attention mechanism for cognitive processing",
      version: "1.2.0",
      lastModified: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
      usageCount: 25,
    },
    {
      id: "hypergraph-encoder",
      name: "Hypergraph Pattern Encoder",
      description: "Encodes cognitive patterns into hypergraph structures",
      version: "2.0.1",
      lastModified: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 hours ago
      usageCount: 42,
    },
    {
      id: "salience-calculator",
      name: "Semantic Salience Calculator",
      description: "Calculates semantic importance of cognitive elements",
      version: "1.0.5",
      lastModified: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
      usageCount: 8,
    },
  ];

  exampleModels.forEach(model => {
    feedbackService.registerProjectModel(model);
    console.log(`   ✓ Registered: ${model.name} v${model.version}`);
  });

  // 3. Add community feedback
  console.log("\n3. Adding community feedback...");

  const exampleFeedback = [
    {
      modelId: "neural-attention-model",
      userId: "researcher-001",
      type: "performance" as const,
      priority: "high" as const,
      description: "Model performance degrades with large context windows",
      votes: 12,
    },
    {
      modelId: "hypergraph-encoder",
      userId: "developer-002",
      type: "feature_request" as const,
      priority: "urgent" as const,
      description: "Need support for dynamic pattern evolution",
      votes: 8,
    },
    {
      modelId: "salience-calculator",
      userId: "scientist-003",
      type: "improvement" as const,
      priority: "medium" as const,
      description:
        "Could benefit from machine learning-based weight optimization",
      votes: 5,
    },
    {
      modelId: "neural-attention-model",
      userId: "user-004",
      type: "bug" as const,
      priority: "urgent" as const,
      description: "Memory leak in long-running attention processes",
      votes: 15,
    },
  ];

  exampleFeedback.forEach(feedback => {
    feedbackService.addCommunityFeedback(feedback);
    console.log(
      `   ✓ Added ${feedback.priority} priority ${feedback.type} for ${feedback.modelId}`
    );
  });

  // 4. Show system status
  console.log("\n4. Current system status:");
  const status = feedbackService.getSystemStatus();
  console.log(`   📊 Models: ${status.projectModelsCount}`);
  console.log(`   💬 Feedback items: ${status.communityFeedbackCount}`);
  console.log(`   🧠 Hypergraph nodes: ${status.hypergraphNodesCount}`);
  console.log(
    `   🎯 Attention threshold: ${status.adaptiveThresholds.attentionThreshold.toFixed(3)}`
  );
  console.log(
    `   ⚡ Cognitive load: ${status.adaptiveThresholds.cognitiveLoad.toFixed(3)}`
  );
  console.log(
    `   📈 Recent activity: ${status.adaptiveThresholds.recentActivity.toFixed(3)}`
  );

  // 5. Trigger feedback loop
  console.log("\n5. Triggering adaptive feedback loop...");

  return feedbackService
    .triggerFeedbackLoop()
    .then(() => {
      console.log("✅ Feedback loop completed successfully!");

      // Show updated status
      const updatedStatus = feedbackService.getSystemStatus();
      console.log("\n6. Updated system status:");
      console.log(
        `   🔄 Last cycle: ${updatedStatus.lastFeedbackCycle.toLocaleTimeString()}`
      );
      console.log(
        `   🧩 Hypergraph nodes: ${updatedStatus.hypergraphNodesCount}`
      );
      console.log(
        `   👁️ Attention-filtered nodes: ${updatedStatus.attentionFilteredNodes}`
      );

      return true;
    })
    .catch(error => {
      console.error("❌ Feedback loop failed:", error);
      return false;
    });
}

/**
 * Example: React component usage
 */
export function ExampleReactComponent() {
  // This would be used in a real React component
  const mockUseAdaptiveFeedback = () => {
    const service = AdaptiveFeedbackService.getInstance();

    return {
      addFeedback: (feedback: any) => service.addCommunityFeedback(feedback),
      registerModel: (model: any) => service.registerProjectModel(model),
      getStatus: () => service.getSystemStatus(),
      triggerFeedbackLoop: () => service.triggerFeedbackLoop(),
    };
  };

  const { addFeedback, registerModel, getStatus, triggerFeedbackLoop } =
    mockUseAdaptiveFeedback();

  // Example usage in component
  const handleAddFeedback = () => {
    addFeedback({
      modelId: "example-model",
      userId: "current-user",
      type: "improvement",
      priority: "medium",
      description: "This model could use better error handling",
      votes: 1,
    });
  };

  const handleTriggerLoop = async () => {
    try {
      await triggerFeedbackLoop();
      console.log("Feedback loop triggered from UI");
    } catch (error) {
      console.error("Failed to trigger feedback loop:", error);
    }
  };

  // Mock React component structure
  return {
    handleAddFeedback,
    handleTriggerLoop,
    status: getStatus(),
    // In real React component:
    // render: () => <div>Feedback System UI</div>
  };
}

/**
 * Example: Integration with existing orchestrator
 */
export function demonstrateOrchestratorIntegration() {
  console.log("🔗 Demonstrating orchestrator integration...\n");

  // Initialize feedback system
  const feedbackSystem = initializeAdaptiveFeedbackSystem();

  // Show integration status
  console.log("Integration status:");
  console.log("✓ Feedback service initialized as singleton");
  console.log("✓ Integration service registered with orchestrator");
  console.log("✓ React hook available for UI components");
  console.log("✓ Event listeners configured for system events");

  // In a real application, this would integrate with:
  // - OrchestratorService for component coordination
  // - UI components for user interaction
  // - Memory system for persistent storage
  // - External APIs for Copilot integration

  return true;
}

// Example usage
if (typeof process !== "undefined" && process.env.NODE_ENV !== "production") {
  // Run demonstration in development
  console.log("=".repeat(60));
  console.log("ADAPTIVE FEEDBACK LOOP DEMONSTRATION");
  console.log("=".repeat(60));

  demonstrateAdaptiveFeedbackLoop().then(success => {
    if (success) {
      console.log("\n🎉 Demonstration completed successfully!");
      console.log("\nNext steps:");
      console.log("- Integrate with real Copilot API");
      console.log("- Connect to UI components");
      console.log("- Add persistent storage");
      console.log("- Enable real-time community broadcasting");
    } else {
      console.log("\n⚠️ Demonstration encountered issues");
    }
  });
}
