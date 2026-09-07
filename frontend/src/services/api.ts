export interface User {
  id: number;
  created_at?: string;
}

export interface Conversation {
  id: number;
  user_id: number;
  title: string;
  summary?: string;
  created_at?: string;
}

export interface Message {
  id?: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at?: string;
}

export interface ChatResponse {
  user_id: number;
  conversation_id: number;
  user_message: string;
  assistant_response: string;
  trace_id: string;
  duration_ms: number;
  background_task_id?: string;
  observability?: any;
}

export interface MemoryItem {
  id: number;
  user_id?: number;
  memory_type: string;
  key: string;
  value: string;
  scope?: string;
}

export interface BackgroundTask {
  task_id: string;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: number;
  started_at?: number | null;
  completed_at?: number | null;
  duration_ms?: number | null;
  error?: string | null;
  result?: any;
  metadata?: Record<string, any>;
}

export interface ObservabilityMetrics {
  status: string;
  provider: string;
  model_name: string;
  embedding_model: string;
  metrics: {
    llm: {
      calls_total: number;
      errors_total: number;
      avg_latency_ms: number;
    };
    embedding: {
      calls_total: number;
      errors_total: number;
      avg_latency_ms: number;
    };
    memory: {
      searches_total: number;
      hits_total: number;
      hit_rate_pct: number;
      deletions_total: number;
    };
    cache: {
      hits_total: number;
      misses_total: number;
      hit_rate_pct: number;
      hits_by_type: Record<string, number>;
    };
    background_tasks?: {
      total: number;
      completed: number;
      failed: number;
      running: number;
      avg_latency_ms: number;
      by_type: Record<string, number>;
    };
    reliability: {
      retries_total: number;
    };
  };
}

const API_BASE = '/api';

export const api = {
  // Users
  async getUsers(): Promise<User[]> {
    const res = await fetch(`${API_BASE}/users`);
    if (!res.ok) throw new Error('Failed to fetch users');
    return res.json();
  },

  async createUser(): Promise<User> {
    const res = await fetch(`${API_BASE}/users`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to create user (${res.status})`);
    }
    return res.json();
  },

  async deleteUser(userId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/users/${userId}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete user (${res.status})`);
    }
  },

  // Conversations
  async getConversations(userId: number): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE}/users/${userId}/conversations`);
    if (!res.ok) throw new Error('Failed to fetch conversations');
    return res.json();
  },

  async createConversation(userId: number, title: string = 'New Session'): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/users/${userId}/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to create conversation (${res.status})`);
    }
    return res.json();
  },

  async deleteConversation(conversationId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to delete conversation (${res.status})`);
    }
  },

  async getMessages(conversationId: number): Promise<Message[]> {
    const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`);
    if (!res.ok) throw new Error('Failed to fetch messages');
    return res.json();
  },

  // Chat
  async sendChatMessage(
    userId: number,
    conversationId: number,
    message: string,
    asyncProcessing: boolean = true
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        conversation_id: conversationId,
        message,
        async_processing: asyncProcessing
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Chat request failed' }));
      throw new Error(err.detail || 'Failed to send chat message');
    }
    return res.json();
  },

  // Memory
  async getUserMemories(userId: number): Promise<MemoryItem[]> {
    const res = await fetch(`${API_BASE}/users/${userId}/memories`);
    if (!res.ok) throw new Error('Failed to fetch memories');
    return res.json();
  },

  async searchUserMemories(userId: number, query: string): Promise<any> {
    const res = await fetch(`${API_BASE}/users/${userId}/memories/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 5 }),
    });
    if (!res.ok) throw new Error('Failed to search memories');
    return res.json();
  },

  async deleteMemory(memoryId: number, userId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/memories/${memoryId}?user_id=${userId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete memory');
  },

  async deleteAllMemories(userId: number): Promise<void> {
    const res = await fetch(`${API_BASE}/users/${userId}/memories`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to clear memories');
  },

  // Tasks
  async getTasks(userId?: number, status?: string): Promise<BackgroundTask[]> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId.toString());
    if (status) params.append('status', status);
    const query = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/tasks${query}`);
    if (!res.ok) throw new Error('Failed to fetch background tasks');
    return res.json();
  },

  async getTask(taskId: string): Promise<BackgroundTask> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`);
    if (!res.ok) throw new Error('Failed to fetch task');
    return res.json();
  },

  async triggerReindex(userId: number): Promise<BackgroundTask> {
    const res = await fetch(`${API_BASE}/tasks/reindex`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!res.ok) throw new Error('Failed to trigger background reindex');
    return res.json();
  },

  // Observability
  async getMetrics(): Promise<ObservabilityMetrics> {
    const res = await fetch(`${API_BASE}/observability/metrics`);
    if (!res.ok) throw new Error('Failed to fetch metrics');
    return res.json();
  },
};
