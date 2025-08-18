import { useEffect } from "react";
import { useMemory } from "../contexts/MemoryContext";
import {
  useOrchestrator,
  setMemoryFunctions,
} from "../contexts/OrchestratorContext";

/**
 * This component connects the Memory context to the Orchestrator
 * It only renders when both contexts are available
 */
const MemoryConnector: React.FC = () => {
  const { addMemory, searchMemories } = useMemory();
  const orchestrator = useOrchestrator();

  // When this component mounts, both contexts are guaranteed to be initialized
  useEffect(() => {
    // Connect the memory functions to the orchestrator using the setter
    setMemoryFunctions(addMemory);

    // Log that the memory system is connected
    orchestrator.logEvent({
      type: "system_event",
      description: "Memory system connected to orchestrator",
      component: "memory_connector",
    });

    // Create a global function to access memory from anywhere
    const globalMemory = {
      addMemory,
      searchMemories,
      saveViaOrchestrator: (content: string | { title?: string; [key: string]: unknown }, tags: string[]) => {
        return orchestrator.saveToMemory(content, tags);
      },
    };

    // @ts-expect-error - Adding to window for global access
    globalThis.DeepTreeEchoMemory = globalMemory;

    return () => {
      // @ts-expect-error - Cleanup global property
      delete globalThis.DeepTreeEchoMemory;
    };
  }, [addMemory, searchMemories, orchestrator]); // Only re-run when these functions change

  // This component doesn't render anything
  return null;
};

export default MemoryConnector;
