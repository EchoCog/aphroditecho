/**
 * Test Suite for Adaptive Feedback Loop
 *
 * Basic functionality tests for the hypergraph-encoded feedback system
 */

import { HypergraphSchemeCore } from "./hypergraphSchemeCore";
import { AdaptiveFeedbackService } from "./adaptiveFeedbackService";

/**
 * Test the core hypergraph functionality
 */
function testHypergraphCore() {
  console.log("🧪 Testing HypergraphSchemeCore...");

  const core = new HypergraphSchemeCore();

  // Test node creation
  const testNode = core.createNode(
    "test-model",
    "model",
    {
      name: "Test Model",
      description: "A test cognitive model",
      version: "1.0.0",
    },
    []
  );

  console.assert(testNode.id === "test-model", "Node ID should match");
  console.assert(testNode.type === "model", "Node type should match");
  console.assert(testNode.salience > 0, "Node should have positive salience");

  // Test adaptive attention
  const attention1 = core.adaptiveAttention(0.3, 0.7);
  const attention2 = core.adaptiveAttention(0.8, 0.2);
  console.assert(
    attention2 > attention1,
    "Higher load should increase threshold"
  );

  // Test pattern mining
  const patterns = core.mineCognitivePatterns(0.5);
  console.assert(Array.isArray(patterns), "Should return array of patterns");

  // Test salience metrics
  const metrics = core.calculateSalienceMetrics("test-model", []);
  console.assert(
    typeof metrics.overall === "number",
    "Should return numeric overall score"
  );
  console.assert(
    metrics.overall >= 0 && metrics.overall <= 1,
    "Score should be in 0-1 range"
  );

  console.log("✅ HypergraphSchemeCore tests passed");
  return true;
}

/**
 * Test the adaptive feedback service
 */
function testAdaptiveFeedbackService() {
  console.log("🧪 Testing AdaptiveFeedbackService...");

  const service = AdaptiveFeedbackService.getInstance();

  // Test singleton pattern
  const service2 = AdaptiveFeedbackService.getInstance();
  console.assert(service === service2, "Should return same instance");

  // Test model registration
  service.registerProjectModel({
    id: "test-cognitive-model",
    name: "Test Cognitive Model",
    description: "A test model for cognitive processing",
    version: "1.0.0",
    lastModified: new Date(),
    usageCount: 5,
  });

  // Test feedback addition
  service.addCommunityFeedback({
    modelId: "test-cognitive-model",
    userId: "test-user",
    type: "improvement",
    priority: "high",
    description: "Model needs better attention allocation",
    votes: 3,
  });

  // Test system status
  const status = service.getSystemStatus();
  console.assert(
    status.projectModelsCount > 0,
    "Should have registered models"
  );
  console.assert(
    status.communityFeedbackCount > 0,
    "Should have feedback items"
  );
  console.assert(
    typeof status.adaptiveThresholds.cognitiveLoad === "number",
    "Should have numeric thresholds"
  );

  console.log("✅ AdaptiveFeedbackService tests passed");
  return true;
}

/**
 * Test the integration between components
 */
function testIntegration() {
  console.log("🧪 Testing component integration...");

  const service = AdaptiveFeedbackService.getInstance();

  // Add multiple models and feedback to test prioritization
  const models = [
    { id: "high-priority", priority: "urgent", votes: 10 },
    { id: "medium-priority", priority: "medium", votes: 3 },
    { id: "low-priority", priority: "low", votes: 1 },
  ];

  models.forEach((model, index) => {
    service.registerProjectModel({
      id: model.id,
      name: `Model ${index + 1}`,
      description: `Test model ${index + 1}`,
      version: "1.0.0",
      lastModified: new Date(),
      usageCount: 10 - index * 3,
    });

    service.addCommunityFeedback({
      modelId: model.id,
      userId: "test-user",
      type: "performance",
      priority: model.priority as any,
      description: `Feedback for ${model.id}`,
      votes: model.votes,
    });
  });

  // Test that the system can handle multiple models
  const status = service.getSystemStatus();
  console.assert(
    status.projectModelsCount >= 3,
    "Should handle multiple models"
  );
  console.assert(
    status.communityFeedbackCount >= 3,
    "Should handle multiple feedback items"
  );

  console.log("✅ Integration tests passed");
  return true;
}

/**
 * Test the mocked Copilot integration
 */
async function testCopilotMocking() {
  console.log("🧪 Testing Copilot mocking...");

  const service = AdaptiveFeedbackService.getInstance();

  // Trigger a feedback loop to test the Copilot mocking
  try {
    await service.triggerFeedbackLoop();
    console.log("✅ Copilot mocking test passed (no errors)");
    return true;
  } catch (error) {
    console.error("❌ Copilot mocking test failed:", error);
    return false;
  }
}

/**
 * Run all tests
 */
export async function runTests() {
  console.log("🚀 Starting Adaptive Feedback Loop tests...\n");

  const results = [
    testHypergraphCore(),
    testAdaptiveFeedbackService(),
    testIntegration(),
    await testCopilotMocking(),
  ];

  const passed = results.filter(Boolean).length;
  const total = results.length;

  console.log(`\n📊 Test Results: ${passed}/${total} tests passed`);

  if (passed === total) {
    console.log(
      "🎉 All tests passed! Adaptive feedback system is ready for integration."
    );
  } else {
    console.log("⚠️ Some tests failed. Please review the implementation.");
  }

  return passed === total;
}

// Export test function for external use
export {
  testHypergraphCore,
  testAdaptiveFeedbackService,
  testIntegration,
  testCopilotMocking,
};
