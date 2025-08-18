import { createClient } from "@supabase/supabase-js";
import { OpenAI } from "openai";
// Removed unused import
import { getVectorStoreService } from "./vectorStore.server";
import process from "node:process";

export interface Memory {
  id: string;
  title: string;
  content: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  embedding?: number[] | null;
  userId?: string | null;
  type?:
    | "episodic"
    | "semantic"
    | "procedural"
    | "declarative"
    | "implicit"
    | "associative"
    | "memory";
  context?: string;
  metadata?: Record<string, unknown>;
}

export interface MemorySearchResult {
  id: string;
  content: string;
  metadata?: Record<string, unknown>;
  similarity: number;
}

export class MemoryService {
  private supabase: ReturnType<typeof createClient>;
  private openai: OpenAI | null = null;
  private vectorStore = getVectorStoreService();
  private userId: string | null = null;

  constructor(supabaseUrl: string, supabaseKey: string, userId?: string) {
    this.supabase = createClient(supabaseUrl, supabaseKey);
    this.userId = userId || null;

    if (process.env.OPENAI_API_KEY) {
      this.openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
      });
    }
  }

  public setUserId(userId: string) {
    this.userId = userId;
  }

  public async addMemory(
    memory: Omit<Memory, "id" | "createdAt" | "updatedAt" | "embedding">
  ): Promise<Memory> {
    if (!this.userId) {
      throw new Error("User ID not set");
    }

    // Generate embedding if OpenAI is available
    let embedding = null;
    if (this.openai) {
      embedding = await this.vectorStore.generateEmbedding(memory.content);
    }

    // Current timestamp
    const now = new Date().toISOString();

    // Insert into Supabase
    const { data, error } = await this.supabase
      .from("memories")
      .insert({
        user_id: this.userId,
        title: memory.title,
        content: memory.content,
        tags: memory.tags || [],
        embedding,
        created_at: now,
        updated_at: now,
        metadata: memory.metadata || {},
        context: memory.context || null,
        type: memory.type || "memory",
      })
      .select("*")
      .single();

    if (error) {
      throw error;
    }

    return this._mapMemoryFromDb(data);
  }

  public async searchMemories(
    query: string,
    options?: {
      threshold?: number;
      limit?: number;
      type?: string;
    }
  ): Promise<MemorySearchResult[]> {
    if (!this.userId) {
      throw new Error("User ID not set");
    }

    // If vector store is available, use semantic search
    if (this.openai) {
      return this.vectorStore.searchSimilar(this.userId, query, options);
    }

    // Fallback to basic text search
    const { data, error } = await this.supabase
      .from("memories")
      .select("id, content, metadata")
      .eq("user_id", this.userId)
      .or(`title.ilike.%${query}%,content.ilike.%${query}%`)
      .limit(options?.limit || 5);

    if (error) {
      throw error;
    }

    return data.map(item => {
      const typedItem = item as Record<string, unknown>;
      return {
        id: String(typedItem.id || ""),
        content: String(typedItem.content || ""),
        metadata:
          typeof typedItem.metadata === "object" && typedItem.metadata !== null
            ? (typedItem.metadata as Record<string, unknown>)
            : undefined,
        similarity: 0.8, // Placeholder similarity score
      };
    });
  }

  /**
   * List memories with optional filtering
   */
  public async listMemories(options?: {
    limit?: number;
    offset?: number;
    type?: string;
    tags?: string[];
  }): Promise<Memory[]> {
    if (!this.userId) {
      throw new Error("User ID not set");
    }

    let query = this.supabase
      .from("memories")
      .select("*")
      .eq("user_id", this.userId)
      .order("created_at", { ascending: false });

    if (options?.type) {
      query = query.eq("type", options.type);
    }

    if (options?.tags && options.tags.length > 0) {
      // Filter by tags - this is a simplification as properly filtering array overlaps in Supabase
      // would require more complex queries
      query = query.contains("tags", options.tags);
    }

    if (options?.limit) {
      query = query.limit(options.limit);
    }

    if (options?.offset) {
      query = query.range(
        options.offset,
        options.offset + (options.limit || 10) - 1
      );
    }

    const { data, error } = await query;

    if (error) {
      throw error;
    }

    return data.map(item => this._mapMemoryFromDb(item));
  }

  public async getMemoryStats(): Promise<{
    total: number;
    byType: Record<string, number>;
    byTag: Record<string, number>;
    recentlyAdded: number;
    recentlyAccessed: number;
  }> {
    if (!this.userId) {
      throw new Error("User ID not set");
    }

    // Get total memories
    const { data: totalData, error: totalError } = await this.supabase
      .from("memories")
      .select("id", { count: "exact" as const })
      .eq("user_id", this.userId);

    if (totalError) {
      throw totalError;
    }

    // Get memories by type
    const { data: typeData, error: typeError } = await this.supabase
      .from("memories")
      .select("type")
      .eq("user_id", this.userId);

    if (typeError) {
      throw typeError;
    }

    // Get memories by tag
    const { data: tagData, error: tagError } = await this.supabase
      .from("memories")
      .select("tags")
      .eq("user_id", this.userId);

    if (tagError) {
      throw tagError;
    }

    // Get recently added memories
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);

    const { data: recentData, error: recentError } = await this.supabase
      .from("memories")
      .select("id", { count: "exact" as const })
      .eq("user_id", this.userId)
      .gte("created_at", oneDayAgo.toISOString());

    if (recentError) {
      throw recentError;
    }

    // Count by type
    const byType: Record<string, number> = {};
    typeData.forEach(item => {
      if (
        item &&
        typeof item === "object" &&
        "type" in item &&
        typeof item.type === "string"
      ) {
        byType[item.type] = (byType[item.type] || 0) + 1;
      }
    });

    // Count by tag
    const byTag: Record<string, number> = {};
    tagData.forEach(item => {
      if (
        item &&
        typeof item === "object" &&
        "tags" in item &&
        Array.isArray(item.tags)
      ) {
        item.tags.forEach((tag: string) => {
          byTag[tag] = (byTag[tag] || 0) + 1;
        });
      }
    });

    return {
      total: totalData.length,
      byType,
      byTag,
      recentlyAdded: recentData.length,
      recentlyAccessed: 0, // Would need additional tracking in the database
    };
  }

  /**
   * Map database response to Memory object
   */
  private _mapMemoryFromDb(data: unknown): Memory {
    // Type guard for data object
    if (!data || typeof data !== "object") {
      throw new Error("Invalid data object");
    }

    const typedData = data as Record<string, unknown>;

    return {
      id: String(typedData.id || ""),
      title: String(typedData.title || ""),
      content: String(typedData.content || ""),
      tags: Array.isArray(typedData.tags) 
        ? (typedData.tags as string[]) 
        : [],
      createdAt: String(typedData.created_at || ""),
      updatedAt: String(typedData.updated_at || ""),
      embedding: Array.isArray(typedData.embedding)
        ? (typedData.embedding as number[] | null)
        : null,
      metadata:
        typeof typedData.metadata === "object" && typedData.metadata !== null
          ? (typedData.metadata as Record<string, unknown>)
          : undefined,
      context:
        typeof typedData.context === "string" ? typedData.context : undefined,
      type: typedData.type as
        | "episodic"
        | "semantic"
        | "procedural"
        | "declarative"
        | "implicit"
        | "associative"
        | "memory"
        | undefined,
    };
  }
}

// Create a server-side memory service instance
let memoryService: MemoryService | null = null;

export const getMemoryService = (userId?: string) => {
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
    throw new Error("Supabase environment variables not set");
  }

  if (!memoryService) {
    memoryService = new MemoryService(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY,
      userId
    );
  } else if (userId) {
    memoryService.setUserId(userId);
  }

  return memoryService;
};
