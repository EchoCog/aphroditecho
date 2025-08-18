// Deep Tree Echo Primary Identity - Enhanced Version
// This file now serves as the main entry point for the Deep Tree Echo system prompts
// The enhanced prompts-echo-enhanced.ts contains the full Deep Tree Echo identity and capabilities
// with integrated character configuration and cognitive architecture

export { 
  getSystemPrompt, 
  CONTINUE_PROMPT,
  getEchoGestaltState,
  updateEchoGestalt 
} from './prompts-echo-enhanced';

// Legacy compatibility - ensure existing imports continue to work
export type { DesignScheme } from '~/types/design-scheme';

