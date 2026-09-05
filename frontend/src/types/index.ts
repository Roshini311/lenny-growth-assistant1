export type ProviderType = 'ollama' | 'openai' | 'claude';

export interface HealthStatus {
  status: string;
  environment: string;
  default_provider: string;
  database: {
    configured: boolean;
    connected?: boolean;
  };
  providers: {
    ollama_base_url: string;
    openai_configured: boolean;
  };
}

export interface CitationSource {
  chunk_id: string;
  episode_title: string;
  guest: string;
  timestamp?: string;
  speaker?: string;
  chunk_text: string;
  source_url?: string;
  distance: number;
  citation: string;
}

export interface ArtifactResponse {
  id: string;
  session_id: string;
  message_id?: string;
  artifact_type: 'markdown' | 'html';
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface Ship30EssayResponse {
  topic: string;
  sufficient: boolean;
  essay: string;
  citations: string[];
  artifact?: ArtifactResponse | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sufficient?: boolean;
  citations?: string[];
  sources?: CitationSource[];
  artifact?: ArtifactResponse | null;
  provider?: string;
  isStreaming?: boolean;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  provider?: string;
  stream?: boolean;
}
