import React from 'react';
import { Sun, Moon, Database, Activity, MessageSquare, Terminal, Cpu } from 'lucide-react';

interface HeaderProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  activeTab: 'chat' | 'memory' | 'observability';
  setActiveTab: (tab: 'chat' | 'memory' | 'observability') => void;
  userId: number | null;
  modelName: string;
}

export const Header: React.FC<HeaderProps> = ({
  darkMode,
  setDarkMode,
  activeTab,
  setActiveTab,
  userId,
  modelName,
}) => {
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-[var(--color-hairline)] bg-[var(--color-canvas)]/80 px-4 backdrop-blur-md transition-colors">
      {/* Brand & Eyebrow */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center justify-center h-7 w-7 rounded-sm bg-neutral-950 dark:bg-white text-white dark:text-neutral-950 font-bold text-xs shadow-sm">
          ▲
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="font-semibold text-sm tracking-tight text-neutral-900 dark:text-neutral-100">
            Agent Studio
          </span>
          <span className="font-mono text-[10px] tracking-wider uppercase text-[var(--color-mute)] border border-[var(--color-hairline)] rounded-full px-2 py-0.5">
            Geist Core
          </span>
        </div>
      </div>

      {/* Center Navigation Tabs (Pill style as per DESIGN.md) */}
      <div className="flex items-center space-x-1 bg-[var(--color-canvas-elevated)] p-1 border border-[var(--color-hairline)] rounded-full">
        <button
          onClick={() => setActiveTab('chat')}
          className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded-full transition-all ${
            activeTab === 'chat'
              ? 'bg-neutral-900 dark:bg-neutral-100 text-white dark:text-neutral-900 shadow-sm'
              : 'text-[var(--color-body)] hover:text-neutral-900 dark:hover:text-white'
          }`}
        >
          <MessageSquare className="h-3.5 w-3.5" />
          <span>Chat</span>
        </button>

        <button
          onClick={() => setActiveTab('memory')}
          className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded-full transition-all ${
            activeTab === 'memory'
              ? 'bg-neutral-900 dark:bg-neutral-100 text-white dark:text-neutral-900 shadow-sm'
              : 'text-[var(--color-body)] hover:text-neutral-900 dark:hover:text-white'
          }`}
        >
          <Database className="h-3.5 w-3.5" />
          <span>Memory Inspector</span>
        </button>

        <button
          onClick={() => setActiveTab('observability')}
          className={`flex items-center space-x-1.5 px-3 py-1 text-xs font-medium rounded-full transition-all ${
            activeTab === 'observability'
              ? 'bg-neutral-900 dark:bg-neutral-100 text-white dark:text-neutral-900 shadow-sm'
              : 'text-[var(--color-body)] hover:text-neutral-900 dark:hover:text-white'
          }`}
        >
          <Activity className="h-3.5 w-3.5" />
          <span>Observability</span>
        </button>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* Model badge */}
        <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 text-xs font-mono text-[var(--color-body)] border border-[var(--color-hairline)] rounded-md bg-[var(--color-canvas-elevated)]">
          <Cpu className="h-3 w-3 text-blue-500" />
          <span className="text-[11px] truncate max-w-[120px]">{modelName}</span>
        </div>

        {/* User Pill badge */}
        {userId !== null && (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 text-xs font-medium border border-[var(--color-hairline)] rounded-full bg-[var(--color-canvas-elevated)]">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="font-mono text-[11px] text-[var(--color-body)]">User #{userId}</span>
          </div>
        )}

        {/* Theme Switcher Button */}
        <button
          onClick={() => setDarkMode(!darkMode)}
          className="flex h-8 w-8 items-center justify-center rounded-md border border-[var(--color-hairline)] bg-[var(--color-canvas-elevated)] text-[var(--color-body)] hover:text-neutral-900 dark:hover:text-white transition-colors"
          title="Toggle Theme"
        >
          {darkMode ? <Sun className="h-4 w-4 text-amber-400" /> : <Moon className="h-4 w-4 text-neutral-700" />}
        </button>
      </div>
    </header>
  );
};
