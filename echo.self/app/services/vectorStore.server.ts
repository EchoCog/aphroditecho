import { createClient } from "@supabase/supabase-js";
import { OpenAI } from "openai";
import process from "node:process";

export interface VectorSearchResult {
  id: string;
  content: string;
  metadata?: Record<string, unknown>;
  similarity: number;
}

export class VectorStoreService {
  private static instance: VectorStoreService;
  private supabase: ReturnType<typeof createClient>;
  private openai: OpenAI | null = null;
  private localIndex: unknown | null = null;
  private localNextId: number = 0;

  private constructor() {
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
      throw new Error("Missing Supabase environment variables");
    }

    this.supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY
    );

    if (process.env.OPENAI_API_KEY) {
      this.openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
      });
    }

    // Initialize local vector index lazily to avoid native module issues
    this.initializeLocalIndex();
  }

  private async initializeLocalIndex() {
    try {
      // Dynamically import to avoid bundling native module in environments that don't support it
      const mod: unknown = await import("hnswlib-node").catch(() => null);
      // Resolve possible CJS/ESM shapes
      const HierarchicalNSWCtor =
        (mod && (mod as any).HierarchicalNSW) ||
        (mod && (mod as any).default && (mod as any).default.HierarchicalNSW);

      if (!HierarchicalNSWCtor) {
        console.warn(
          "hnswlib-node not available; local vector index disabled (will fallback to Supabase-only search)."
        );
        return;
      }

      this.localIndex = new HierarchicalNSWCtor("cosine", 1536);
      const idx: any = this.localIndex as any;
      if (typeof idx.init === "function") {
        idx.init(10000);
      } else if (typeof idx.initIndex === "function") {
        idx.initIndex(10000);
      }
      this.localNextId = 0;
    } catch (error) {
      console.warn(
        "Local vector index initialization failed; continuing without local index:",
        error
      );
    }
  }

  public static getInstance(): VectorStoreService {
    if (!VectorStoreService.instance) {
      VectorStoreService.instance = new VectorStoreService();
    }
    return VectorStoreService.instance;
  }

  public async generateEmbedding(text: string): Promise<number[] | null> {
    if (!this.openai) {
      console.warn("OpenAI client not initialized");
      return null;
    }

    try {
      const response = await this.openai.embeddings.create({
        model: "text-embedding-3-large",
        input: text,
        dimensions: 1536,
      });

      return response.data[0].embedding;
    } catch (error) {
      console.error("Error generating embedding:", error);
      return null;
    }
  }

  public async addToVectorStore(
    userId: string,
    content: string
  ): Promise<boolean> {
    const embedding = await this.generateEmbedding(content);
    if (!embedding) return false;

    try {
      // Add to Supabase
      const { error } = await this.supabase
        .from("memories")
        .update({ embedding })
        .eq("user_id", userId)
        .eq("content", content);

      if (error) {
        throw error;
      }

      // Add to local index if available
      if (this.localIndex) {
        const id = this.localNextId++;
        (this.localIndex as any).addPoint(embedding, id);
      }

      return true;
    } catch (error) {
      console.error("Error adding to vector store:", error);
      return false;
    }
  }

  public async searchSimilar(
    userId: string,
    query: string,
    options: {
      threshold?: number;
      limit?: number;
      type?: string;
    } = {}
  ): Promise<VectorSearchResult[]> {
    const embedding = await this.generateEmbedding(query);
    if (!embedding) return [];

    const threshold = options.threshold || 0.7;
    const limit = options.limit || 5;

    try {
      // Search in Supabase
      const { data, error } = await this.supabase.rpc("match_memories", {
        query_embedding: embedding,
        match_threshold: threshold,
        match_count: limit,
        user_id: userId,
        filter_type: options.type,
      });

      if (error) {
        throw error;
      }

      return data as VectorSearchResult[];
    } catch (error) {
      console.error("Error searching vector store:", error);

      // Fall back to local index if available
      if (this.localIndex) {
        try {
          const results = (this.localIndex as any).searchKnn(embedding, limit);
          return results.neighbors.map((id: number, i: number) => ({
            id: id.toString(),
            content: "Local result",
            similarity: 1 - results.distances[i],
          }));
        } catch (localError) {
          console.error("Error searching local index:", localError);
        }
      }

      return [];
    }
  }
}

// Create a server-side vector store service instance
let vectorStoreService: VectorStoreService | null = null;

export const getVectorStoreService = () => {
  if (!vectorStoreService) {
    vectorStoreService = VectorStoreService.getInstance();
  }
  return vectorStoreService;
};
