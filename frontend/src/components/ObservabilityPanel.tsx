import React, { useState, useEffect } from 'react';
import { Activity, Cpu, Zap, Database, ShieldCheck, RefreshCw, BarChart2, Layers, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';
import { ObservabilityMetrics, BackgroundTask, api } from '../services/api';

export const ObservabilityPanel: React.FC = () => {
  const [data, setData] = useState<ObservabilityMetrics | null>(null);
  const [tasks, setTasks] = useState<BackgroundTask[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchMetricsAndTasks = async () => {
    setLoading(true);
    try {
      const [metricsRes, tasksRes] = await Promise.all([
        api.getMetrics(),
        api.getTasks().catch(() => [])
      ]);
      setData(metricsRes);
      setTasks(tasksRes);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetricsAndTasks();
    const interval = setInterval(fetchMetricsAndTasks, 4000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 font-semibold uppercase">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            completed
          </span>
        );
      case 'running':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300 font-semibold uppercase">
            <RefreshCw className="w-3 h-3 text-blue-500 animate-spin" />
            running
          </span>
        );
      case 'pending':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 font-semibold uppercase">
            <Clock className="w-3 h-3 text-amber-500" />
            queued
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 font-semibold uppercase">
            <AlertTriangle className="w-3 h-3 text-red-500" />
            failed
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 uppercase">
            {status}
          </span>
        );
    }
  };

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
            Real-time execution metrics, background worker tasks, LLM latency tracking, and vector cache hit-rate analytics.
          </p>
        </div>

        <button
          onClick={fetchMetricsAndTasks}
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

      {/* Async Background Worker Telemetry Card */}
      {data?.metrics?.background_tasks && (
        <div className="hairline-card p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--color-hairline)] pb-3">
            <div className="flex items-center space-x-2">
              <Layers className="h-4 w-4 text-indigo-500" />
              <span className="font-semibold text-sm">Async Background Task Worker Pool</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 font-semibold">
              In-Process ThreadPool
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
              <span className="text-[10px] font-mono text-[var(--color-mute)] block">TOTAL TASKS</span>
              <span className="text-lg font-bold font-mono">{data.metrics.background_tasks.total}</span>
            </div>
            <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
              <span className="text-[10px] font-mono text-[var(--color-mute)] block">COMPLETED</span>
              <span className="text-lg font-bold font-mono text-emerald-500">{data.metrics.background_tasks.completed}</span>
            </div>
            <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
              <span className="text-[10px] font-mono text-[var(--color-mute)] block">ACTIVE / RUNNING</span>
              <span className="text-lg font-bold font-mono text-blue-500">{data.metrics.background_tasks.running}</span>
            </div>
            <div className="bg-[var(--color-hairline-soft)] p-3 rounded-md border border-[var(--color-hairline)]">
              <span className="text-[10px] font-mono text-[var(--color-mute)] block">AVG WORKER LATENCY</span>
              <span className="text-lg font-bold font-mono text-indigo-500">{data.metrics.background_tasks.avg_latency_ms}ms</span>
            </div>
          </div>

          {/* Live Tasks Queue Table */}
          <div className="mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono uppercase tracking-wider text-[var(--color-mute)]">
                Recent Background Jobs ({tasks.length})
              </span>
            </div>
            {tasks.length === 0 ? (
              <p className="text-xs text-[var(--color-mute)] py-3 text-center font-mono">
                No background tasks submitted yet. Send a chat message to trigger async extraction!
              </p>
            ) : (
              <div className="overflow-x-auto border border-[var(--color-hairline)] rounded-md">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[var(--color-hairline-soft)] border-b border-[var(--color-hairline)] text-[var(--color-mute)] font-mono text-[11px]">
                    <tr>
                      <th className="p-2.5">Task ID</th>
                      <th className="p-2.5">Type</th>
                      <th className="p-2.5">Status</th>
                      <th className="p-2.5">Duration</th>
                      <th className="p-2.5">Timestamp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-hairline)] font-mono">
                    {tasks.slice(0, 8).map((task) => (
                      <tr key={task.task_id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800/40">
                        <td className="p-2.5 font-semibold text-neutral-900 dark:text-neutral-100">
                          {task.task_id.substring(0, 18)}...
                        </td>
                        <td className="p-2.5 text-neutral-600 dark:text-neutral-300">
                          <span className="px-1.5 py-0.5 rounded bg-neutral-100 dark:bg-neutral-800 text-[10px]">
                            {task.task_type}
                          </span>
                        </td>
                        <td className="p-2.5">{getStatusBadge(task.status)}</td>
                        <td className="p-2.5 text-[var(--color-body)]">
                          {task.duration_ms !== null && task.duration_ms !== undefined
                            ? `${Math.round(task.duration_ms)}ms`
                            : '-'}
                        </td>
                        <td className="p-2.5 text-[var(--color-mute)] text-[10px]">
                          {new Date(task.created_at * 1000).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
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
