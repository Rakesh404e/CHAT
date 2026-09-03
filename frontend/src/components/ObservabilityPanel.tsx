import React, { useState, useEffect } from 'react';
import { Activity, Cpu, Zap, Database, ShieldCheck, RefreshCw, BarChart2, CheckCircle2 } from 'lucide-react';
import { ObservabilityMetrics, api } from '../services/api';

export const ObservabilityPanel: React.FC = () => {
  const [data, setData] = useState<ObservabilityMetrics | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const res = await api.getMetrics();
      setData(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-6 max-w-6xl w-full mx-auto space-y-6">
      {/* Header Band */}
      <div className="flex items-center justify-between border-b border-[var(--color-hairline)] pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-purple-500" />
            <h1 className="text-xl font-semibold tracking-tight">System Telemetry & Observability</h1>
          </div>
          <p className="text-xs text-[var(--color-mute)] mt-1">
            Real-time execution metrics, LLM latency tracking, and vector cache hit-rate analytics.
          </p>
        </div>

        <button
          onClick={fetchMetrics}
          disabled={loading}
          className="px-3 py-1.5 text-xs font-medium border border-[var(--color-hairline)] rounded-md bg-[var(--color-canvas-elevated)] hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors flex items-center space-x-1.5"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Model Spec Grid */}
      {data && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="hairline-card p-4 space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)] block">
              ACTIVE PROVIDER
            </span>
            <div className="flex items-center space-x-2 text-sm font-semibold uppercase tracking-tight">
              <Cpu className="h-4 w-4 text-blue-500" />
              <span>{data.provider}</span>
            </div>
          </div>

          <div className="hairline-card p-4 space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)] block">
              GENERATION LLM
            </span>
            <div className="flex items-center space-x-2 text-sm font-mono font-semibold">
              <Zap className="h-4 w-4 text-amber-500" />
              <span>{data.model_name}</span>
            </div>
          </div>

          <div className="hairline-card p-4 space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)] block">
              EMBEDDING MODEL
            </span>
            <div className="flex items-center space-x-2 text-sm font-mono font-semibold">
              <Database className="h-4 w-4 text-emerald-500" />
              <span>{data.embedding_model}</span>
            </div>
          </div>
        </div>
      )}

      {/* Metrics Detail Cards */}
      {data?.metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* LLM Generation Telemetry */}
          <div className="hairline-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-hairline)] pb-3">
              <div className="flex items-center space-x-2">
                <Zap className="h-4 w-4 text-amber-500" />
                <span className="font-semibold text-sm">LLM Generation Telemetry</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                GPT Core
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">TOTAL CALLS</span>
                <span className="text-lg font-bold font-mono">{data.metrics.llm.calls_total}</span>
              </div>
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">ERRORS</span>
                <span className="text-lg font-bold font-mono text-red-500">{data.metrics.llm.errors_total}</span>
              </div>
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">AVG LATENCY</span>
                <span className="text-lg font-bold font-mono text-blue-500">{data.metrics.llm.avg_latency_ms}ms</span>
              </div>
            </div>
          </div>

          {/* Memory & RRF Vector Metrics */}
          <div className="hairline-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-hairline)] pb-3">
              <div className="flex items-center space-x-2">
                <Database className="h-4 w-4 text-emerald-500" />
                <span className="font-semibold text-sm">Memory & RRF Analytics</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
                Vector DB
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">SEARCHES</span>
                <span className="text-lg font-bold font-mono">{data.metrics.memory.searches_total}</span>
              </div>
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">HIT RATE</span>
                <span className="text-lg font-bold font-mono text-emerald-500">{data.metrics.memory.hit_rate_pct}%</span>
              </div>
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">DELETIONS</span>
                <span className="text-lg font-bold font-mono">{data.metrics.memory.deletions_total}</span>
              </div>
            </div>
          </div>

          {/* Query Cache Metrics */}
          <div className="hairline-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-hairline)] pb-3">
              <div className="flex items-center space-x-2">
                <BarChart2 className="h-4 w-4 text-purple-500" />
                <span className="font-semibold text-sm">In-Memory Cache Performance</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300">
                L1 Cache
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">CACHE HITS</span>
                <span className="text-lg font-bold font-mono text-purple-500">{data.metrics.cache.hits_total}</span>
              </div>
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">MISSES</span>
                <span className="text-lg font-bold font-mono">{data.metrics.cache.misses_total}</span>
              </div>
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">HIT RATE</span>
                <span className="text-lg font-bold font-mono">{data.metrics.cache.hit_rate_pct}%</span>
              </div>
            </div>
          </div>

          {/* Reliability & Embedding */}
          <div className="hairline-card p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-[var(--color-hairline)] pb-3">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="h-4 w-4 text-blue-500" />
                <span className="font-semibold text-sm">Reliability & Embedding Pipeline</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-center">
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">RETRIES TOTAL</span>
                <span className="text-lg font-bold font-mono">{data.metrics.reliability.retries_total}</span>
              </div>
              <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
                <span className="text-[10px] font-mono text-[var(--color-mute)] block">EMBEDDING LATENCY</span>
                <span className="text-lg font-bold font-mono text-blue-500">{data.metrics.embedding.avg_latency_ms}ms</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
