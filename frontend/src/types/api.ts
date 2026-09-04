// Aligned with FastAPI backend schemas in app/schemas.py

export interface UserInfo { id: string; email: string; name: string | null; workspace_id: string; tenant_id: string; }
export interface TokenPair { access_token: string; refresh_token: string; token_type: string; expires_in: number; user: UserInfo; }
export interface RegisterRequest { email: string; password: string; name: string; workspace_name: string; }

export interface WorkspaceDetail { id: string; name: string; slug: string; tenant_id: string; description: string | null; created_at: string | null; }
export interface WorkspaceMemberOut { id: string; workspace_id: string; user_id: string; user_name: string; user_email: string; role: string; joined_at: string | null; invited_at: string | null; expires_at: string | null; }
export interface WorkspaceSummary { id: string; name: string; slug: string; role: string; }

export interface Project { id: string; workspace_id: string; name: string; description: string | null; created_at: string | null; updated_at: string | null; }
export type ProjectDetail = Project;
export type ProjectUpdate = Partial<{ name: string; description: string | null }>;
export interface ProjectCreate { name: string; description?: string; }

export interface SessionInfo { id: string; workspace_id: string; user_id: string; title: string | null; created_at: string | null; }
export interface MessageInfo { id: string; session_id: string; role: string; content: string; metadata: Record<string, unknown> | null; created_at: string | null; }
export interface SessionHistory { session_id: string; title: string | null; source: string; messages: { id: string; role: string; content: string; created_at: string | null }[]; }
export interface NormalizedMessageOut { id: string; role: string; content: string; timestamp: string | null; external_id: string | null; metadata: Record<string, unknown> | null; }

export interface ChatRequest { message: string; session_id?: string | null; project_id?: string | null; }
export interface ChatResponse {
  message_id: string;
  session_id: string;
  response: string;
  model: string;
  usage: { prompt_tokens: number; completion_tokens: number };
  memory_ids_used: string[];
  retrieval_method: string | null;
  retrieval_sources: Array<{
    memory_id: string;
    content: string;
    item_type: string;
    score: number;
  }>;
  latency_ms: number | null;
  confidence: number | null;
  provider: string | null;
}
export interface ChatStreamEvent {
  type: 'token' | 'done' | 'error' | 'sources';
  content?: string;
  metadata?: { tokens: number; memory_grounded: boolean };
  error?: string;
  sources?: Array<{
    memory_id: string;
    content: string;
    item_type: string;
    score: number;
  }>;
}

export interface MemoryItemOut {
  id: string; workspace_id: string; user_id: string;
  agent_id: string | null; run_id: string | null;
  project_id: string | null; memory_type: string; content: string;
  extra_metadata: Record<string, unknown> | null;
  temporal_status: string; confidence: number; authority: number;
  deleted_at: string | null;
  created_at: string; updated_at: string;
}
export interface MemorySearchRequest { query: string; memory_type?: string | null; project_id?: string | null; limit?: number; }

export interface FactItem {
  id: string; workspace_id: string; project_id: string | null;
  content: string; source_message_id: string | null;
  temporal_status: string; confidence: number; authority: number;
  created_at: string; updated_at: string;
}
export interface FactListResponse { items: FactItem[]; total: number; }

export interface DecisionItem {
  id: string; workspace_id: string; project_id: string | null;
  content: string; temporal_status: string;
  confidence: number; tags: string[];
  created_at: string; updated_at: string;
}
export interface DecisionListResponse { items: DecisionItem[]; total: number; }

export interface TimelineItem {
  item_type: 'memory' | 'fact' | 'decision';
  id: string;
  title: string;
  timestamp: string | null;
  temporal_status: string | null;
  content: string;
}
export interface TimelineResponse { items: TimelineItem[]; total: number; }

export interface GraphNodeOut { id: string; label: string; node_type: string; properties: Record<string, unknown> | null; temporal_status: string; created_at: string; }
export interface GraphEdgeOut { id: string; source_node_id: string; target_node_id: string; relationship_type: string; properties: Record<string, unknown> | null; temporal_status: string; confidence: number; created_at: string; }
export interface GraphResponse { nodes: GraphNodeOut[]; edges: GraphEdgeOut[]; }

export interface SearchResultItem {
  item_type: string; id: string; score: number;
  content: string; temporal_status: string | null;
  created_at: string;
}
export interface SearchResponse { items: SearchResultItem[]; total: number; query: string; }

export interface SourceOut {
  id: string; workspace_id: string; project_id: string | null;
  source_type: string; status: string; stage: string | null;
  title: string | null; message_count: number | null;
  created_at: string | null; completed_at: string | null;
}
export interface SourceDetail extends SourceOut {
  normalized_messages: NormalizedMessageOut[];
}
export interface SourceListResponse { items: SourceOut[]; total: number; }

export interface IngestUploadRequest { project_id: string; source_type: string; content: string; title?: string | null; config?: Record<string, unknown> | null; }
export interface IngestUploadResponse {
  source_id: string; session_id: string; status: string;
  messages_processed: number; facts_created: number; decisions_created: number;
  graph_nodes_created: number; graph_edges_created: number;
}
export interface IngestQueued { job_id: string; status: string; message: string; }

export interface IngestJobOut { id: string; project_id: string; workspace_id: string; source_type: string; status: string; stage: string | null; progress: number; error_message: string | null; estimated_records: number | null; created_at: string | null; started_at: string | null; completed_at: string | null; }

export interface ProvenanceOut {
  id: string; workspace_id: string; project_id: string | null;
  session_id: string | null;
  user_message_id: string | null; assistant_message_id: string | null;
  model: string; provider: string; retrieval_method: string;
  memory_ids_used: string[] | null;
  prompt_tokens: number; completion_tokens: number; total_tokens: number;
  latency_ms: number | null; confidence: number | null;
  created_at: string;
}
export interface ProvenanceMemories { provenance_id: string; memories: MemoryItemOut[]; }

export interface MessageFeedbackCreate { session_id: string; rating: string; comment?: string | null; }
export interface MessageFeedbackOut { id: string; session_id: string; rating: string; comment: string | null; created_at: string; }

export interface InvitationOut { id: string; workspace_id: string; email: string; role: string; state: string; created_at: string | null; expires_at: string | null; }
export interface InvitationUpdate { state?: string; role?: string; }

export type FeedbackRating = 'thumbs_up' | 'thumbs_down' | 'neutral';
export type MemoryType = 'semantic_memory' | 'episodic_memory' | 'procedural_memory' | 'working_memory';

// ── API Keys ────────────────────────────────────────────────────────

export interface ApiKeyOut {
  id: string;
  prefix: string;
  name: string;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}
export interface ApiKeyCreateResponse extends ApiKeyOut {
  raw_key: string;
}

// ── Dashboard ───────────────────────────────────────────────────────

export interface DashboardSummary {
  project_count: number;
  memory_count: number;
  session_count: number;
  source_count: number;
}

// ── User / Auth ─────────────────────────────────────────────────────

export interface UserUpdate { name?: string | null; }

// ── Storage ─────────────────────────────────────────────────────────

export interface StorageFileOut {
  id: string;
  name: string;
  size: number;
  content_type: string;
  uploaded_at: string;
}

// ── Pagination wrapper (common pattern) ─────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}
