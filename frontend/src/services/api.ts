import {
  HealthStatus,
  ChatRequest,
  Ship30EssayResponse,
  ArtifactResponse,
  CitationSource,
  ProviderType,
} from '../types';

const API_BASE = '/api';

export interface SSECallbacks {
  onDelta: (delta: string, sessionId?: string, provider?: string) => void;
  onDone: (data: {
    sessionId?: string;
    provider?: string;
    sufficient?: boolean;
    citations?: string[];
    sources?: CitationSource[];
  }) => void;
  onError: (error: string) => void;
}

export const api = {
  async getHealth(): Promise<HealthStatus> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed with status ${res.status}`);
    }
    return res.json();
  },

  async createSession(): Promise<{ id: string; created_at: string }> {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      throw new Error(`Failed to create session (${res.status})`);
    }
    return res.json();
  },

  async getSession(sessionId: string): Promise<{ id: string; created_at: string }> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch session (${res.status})`);
    }
    return res.json();
  },

  async streamChat(req: ChatRequest, callbacks: SSECallbacks): Promise<void> {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: req.message,
        session_id: req.session_id || undefined,
        provider: req.provider || undefined,
        stream: true,
      }),
    });

    if (!response.ok) {
      let errText = `HTTP Error ${response.status}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) errText = errJson.detail;
      } catch {
        // use default HTTP error
      }
      callbacks.onError(errText);
      return;
    }

    if (!response.body) {
      callbacks.onError('Response body is null.');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;

          const jsonStr = trimmed.slice(5).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            if (data.event === 'delta') {
              callbacks.onDelta(data.delta || '', data.session_id, data.provider);
            } else if (data.event === 'message') {
              // Grounding fallback single-chunk response message
              callbacks.onDelta(data.delta || '', data.session_id, data.provider);
              callbacks.onDone({
                sessionId: data.session_id,
                provider: data.provider,
                sufficient: data.sufficient,
                citations: data.citations || [],
                sources: data.sources || [],
              });
            } else if (data.event === 'done') {
              callbacks.onDone({
                sessionId: data.session_id,
                provider: data.provider,
                sufficient: data.sufficient,
                citations: data.citations || [],
                sources: data.sources || [],
              });
            } else if (data.event === 'error') {
              callbacks.onError(data.error || 'Server error during stream');
            }
          } catch (e) {
            console.warn('Failed to parse SSE JSON chunk:', jsonStr, e);
          }
        }
      }
    } catch (err: any) {
      callbacks.onError(err.message || 'Stream reading connection failed');
    }
  },

  async generateShip30Essay(
    topic: string,
    sessionId?: string,
    provider?: ProviderType
  ): Promise<Ship30EssayResponse> {
    const res = await fetch(`${API_BASE}/essays/ship30`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic.trim(),
        session_id: sessionId || undefined,
        provider: provider || undefined,
      }),
    });

    if (!res.ok) {
      let errDetail = `HTTP ${res.status}`;
      try {
        const errObj = await res.json();
        if (errObj.detail) errDetail = errObj.detail;
      } catch {
        // fallback
      }
      throw new Error(`Ship30 essay generation failed: ${errDetail}`);
    }

    return res.json();
  },

  async getArtifact(artifactId: string): Promise<ArtifactResponse> {
    const res = await fetch(`${API_BASE}/artifacts/${artifactId}`);
    if (!res.ok) {
      throw new Error(`Artifact fetch failed (${res.status})`);
    }
    return res.json();
  },

  async getSessionArtifacts(sessionId: string): Promise<ArtifactResponse[]> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/artifacts`);
    if (!res.ok) {
      throw new Error(`Session artifacts fetch failed (${res.status})`);
    }
    return res.json();
  },
};
