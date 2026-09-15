import React, { useState, useEffect } from 'react';
import { Database, Search, Trash2, RefreshCw, Key, Layers, Tag, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { MemoryItem, api } from '../services/api';

interface MemoryInspectorProps {
  userId: number | null;
}

export const MemoryInspector: React.FC<MemoryInspectorProps> = ({ userId }) => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const fetchMemories = async () => {
    if (userId === null) return;
    setLoading(true);
    try {
      const data = await api.getUserMemories(userId);
      setMemories(data);
      setSearchResults(null);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, [userId]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId || !searchQuery.trim()) return;
    setSearching(true);
    try {
      const res = await api.searchUserMemories(userId, searchQuery);
      setSearchResults(res.results || []);
    } catch (err: any) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const handleDelete = async (memoryId: number) => {
    if (!userId) return;
    try {
      await api.deleteMemory(memoryId, userId);
      setNotice(`Deleted memory ID #${memoryId}`);
      setTimeout(() => setNotice(null), 3000);
      fetchMemories();
    } catch (err: any) {
      console.error(err);
    }
  };

  const handleClearAll = async () => {
    if (!userId) return;
    if (!window.confirm('Are you sure you want to delete ALL long-term memories for this user?')) return;
    try {
      await api.deleteAllMemories(userId);
      setNotice('All memories cleared successfully');
      setTimeout(() => setNotice(null), 3000);
      fetchMemories();
    } catch (err: any) {
      console.error(err);
    }
  };

  if (userId === null) {
    return (
      <div className="p-8 text-center text-[var(--color-mute)] font-mono text-xs">
        Select or create a user workspace to inspect long-term memories.
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-6xl w-full mx-auto space-y-6">
      {/* Header Band */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-[var(--color-hairline)] pb-4 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="h-5 w-5 text-blue-500" />
            <h1 className="text-xl font-semibold tracking-tight">Long-Term Memory Inspector</h1>
          </div>
          <p className="text-xs text-[var(--color-mute)] mt-1">
            Real-time synchronization between SQLite relational tables and ChromaDB vector store for User #{userId}.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchMemories}
            disabled={loading}
            className="px-3 py-1.5 text-xs font-medium text-neutral-800 dark:text-neutral-200 hover:text-neutral-950 dark:hover:text-white border border-[var(--color-hairline)] rounded-md bg-[var(--color-canvas-elevated)] hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors flex items-center space-x-1.5 shadow-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleClearAll}
            disabled={memories.length === 0}
            className="px-3 py-1.5 text-xs font-medium text-red-600 border border-red-200 dark:border-red-900/50 rounded-md bg-red-50 dark:bg-red-950/20 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed shadow-xs"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>Clear All</span>
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {notice && (
        <div className="flex items-center space-x-2 p-3 bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 rounded-md text-emerald-800 dark:text-emerald-300 text-xs font-mono">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          <span>{notice}</span>
        </div>
      )}

      {/* Vector Similarity Search Tool */}
      <div className="hairline-card p-4 space-y-3">
        <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)] block">
          Hybrid Vector Search Simulator
        </span>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-[var(--color-mute)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search user memories semantically (e.g. 'what is my name?' or 'tech stack')..."
              className="w-full pl-9 pr-3 py-2 text-xs bg-[var(--color-canvas)] text-neutral-900 dark:text-neutral-100 placeholder:text-neutral-400 dark:placeholder:text-neutral-500 border border-[var(--color-hairline)] rounded-md font-mono focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !searchQuery.trim()}
            className="px-4 py-2 bg-neutral-950 text-white dark:bg-white dark:text-neutral-950 hover:bg-neutral-800 dark:hover:bg-neutral-200 text-xs font-medium rounded-md transition-colors disabled:opacity-40 shadow-xs"
          >
            {searching ? 'Searching...' : 'Run Vector Search'}
          </button>
        </form>

        {/* Search Results Display */}
        {searchResults && (
          <div className="mt-4 border-t border-[var(--color-hairline)] pt-3 space-y-2">
            <div className="flex items-center justify-between text-xs font-mono text-[var(--color-mute)]">
              <span>Reciprocal Rank Fusion (RRF) Results ({searchResults.length}):</span>
              <button
                onClick={() => setSearchResults(null)}
                className="text-blue-500 hover:underline"
              >
                Clear Search Results
              </button>
            </div>
            {searchResults.length === 0 ? (
              <p className="text-xs text-[var(--color-mute)] italic font-mono">No matching memories found for query.</p>
            ) : (
              searchResults.map((res: any, idx: number) => (
                <div key={idx} className="p-3 bg-[var(--color-canvas)] border border-blue-200 dark:border-blue-900/50 rounded-md text-xs font-mono space-y-1">
                  <div className="flex items-center justify-between text-blue-600 dark:text-blue-400 font-bold">
                    <span>{res.content || res.document}</span>
                    <span className="text-[10px] bg-blue-100 dark:bg-blue-950 px-2 py-0.5 rounded-full">
                      Score: {res.score?.toFixed(4) || 'N/A'}
                    </span>
                  </div>
                  {res.metadata && (
                    <div className="text-[11px] text-[var(--color-mute)]">
                      Type: {res.metadata.memory_type} | Key: {res.metadata.key} | Scope: {res.metadata.scope || 'global'}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Memories Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)]">
            Stored Memories ({memories.length})
          </span>
        </div>

        {memories.length === 0 ? (
          <div className="hairline-card p-12 text-center text-xs text-[var(--color-mute)] font-mono">
            No long-term memories stored yet for User #{userId}. Chat with the agent to automatically extract facts, preferences, and identity rules!
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {memories.map((mem) => (
              <div key={mem.id} className="hairline-card p-4 space-y-3 relative group">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border border-blue-200 dark:border-blue-900/50">
                    {mem.memory_type}
                  </span>

                  <button
                    onClick={() => handleDelete(mem.id)}
                    className="opacity-60 group-hover:opacity-100 text-[var(--color-mute)] hover:text-red-500 p-1 rounded transition-all"
                    title="Delete Memory"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center space-x-1.5 text-xs font-mono text-neutral-900 dark:text-white font-semibold">
                    <Key className="h-3.5 w-3.5 text-neutral-400" />
                    <span>{mem.key}</span>
                  </div>
                  <p className="text-xs text-[var(--color-body)] font-sans bg-[var(--color-hairline-soft)] p-2.5 rounded-md border border-[var(--color-hairline)] break-words">
                    {mem.value}
                  </p>
                </div>

                {mem.scope && (
                  <div className="flex items-center space-x-1 text-[10px] font-mono text-[var(--color-mute)]">
                    <Layers className="h-3 w-3" />
                    <span>Scope: {mem.scope}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
