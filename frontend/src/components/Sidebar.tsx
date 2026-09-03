import React, { useState } from 'react';
import { User as UserIcon, Plus, MessageSquare, ChevronDown, Sparkles, Folder } from 'lucide-react';
import { User, Conversation } from '../services/api';

interface SidebarProps {
  users: User[];
  currentUserId: number | null;
  onSelectUser: (userId: number) => void;
  onCreateUser: () => void;
  conversations: Conversation[];
  currentConversationId: number | null;
  onSelectConversation: (convId: number) => void;
  onCreateConversation: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  users,
  currentUserId,
  onSelectUser,
  onCreateUser,
  conversations,
  currentConversationId,
  onSelectConversation,
  onCreateConversation,
}) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-[var(--color-hairline)] bg-[var(--color-canvas)] h-[calc(100vh-3.5rem)] select-none">
      {/* User Switcher Section */}
      <div className="p-3 border-b border-[var(--color-hairline)]">
        <label className="block text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)] mb-1.5 px-1">
          Active Workspace User
        </label>
        <div className="relative">
          <button
            onClick={() => setShowUserDropdown(!showUserDropdown)}
            className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium border border-[var(--color-hairline)] rounded-md bg-[var(--color-canvas-elevated)] hover:bg-neutral-100 dark:hover:bg-neutral-800/60 transition-colors"
          >
            <div className="flex items-center space-x-2 truncate">
              <div className="h-5 w-5 rounded-full bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 flex items-center justify-center text-[10px] font-bold">
                U
              </div>
              <span className="font-mono text-xs truncate">
                {currentUserId !== null ? `User ID: ${currentUserId}` : 'Select User'}
              </span>
            </div>
            <ChevronDown className="h-3.5 w-3.5 text-[var(--color-mute)]" />
          </button>

          {/* User Dropdown Menu */}
          {showUserDropdown && (
            <div className="absolute top-full left-0 right-0 mt-1 z-50 border border-[var(--color-hairline)] rounded-md bg-[var(--color-canvas-elevated)] shadow-lg py-1 max-h-56 overflow-y-auto">
              {users.map((u) => (
                <button
                  key={u.id}
                  onClick={() => {
                    onSelectUser(u.id);
                    setShowUserDropdown(false);
                  }}
                  className={`w-full flex items-center space-x-2 px-3 py-1.5 text-xs text-left transition-colors ${
                    u.id === currentUserId
                      ? 'bg-neutral-100 dark:bg-neutral-800 font-semibold text-neutral-900 dark:text-white'
                      : 'text-[var(--color-body)] hover:bg-neutral-50 dark:hover:bg-neutral-800/40'
                  }`}
                >
                  <UserIcon className="h-3.5 w-3.5 text-[var(--color-mute)]" />
                  <span>User #{u.id}</span>
                </button>
              ))}
              <div className="border-t border-[var(--color-hairline)] my-1"></div>
              <button
                onClick={() => {
                  onCreateUser();
                  setShowUserDropdown(false);
                }}
                className="w-full flex items-center space-x-2 px-3 py-1.5 text-xs text-blue-600 dark:text-blue-400 hover:bg-neutral-50 dark:hover:bg-neutral-800/40 transition-colors font-medium"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Create New User</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Conversations Section */}
      <div className="p-3 flex items-center justify-between">
        <span className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)]">
          Sessions
        </span>
        <button
          onClick={onCreateConversation}
          className="flex items-center space-x-1 px-2.5 py-1 text-xs font-medium text-white bg-neutral-900 dark:bg-white dark:text-neutral-900 rounded-full hover:opacity-90 transition-opacity shadow-sm"
          title="New Conversation"
        >
          <Plus className="h-3 w-3" />
          <span>New</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-xs text-[var(--color-mute)] italic">
            No active chat sessions found. Click 'New' to start.
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === currentConversationId;
            return (
              <button
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`w-full flex flex-col items-start px-3 py-2 rounded-md text-xs transition-all text-left group border ${
                  isActive
                    ? 'border-[var(--color-hairline)] bg-[var(--color-canvas-elevated)] font-medium text-neutral-900 dark:text-white shadow-xs'
                    : 'border-transparent text-[var(--color-body)] hover:bg-neutral-100 dark:hover:bg-neutral-800/40'
                }`}
              >
                <div className="flex items-center space-x-2 w-full">
                  <MessageSquare className={`h-3.5 w-3.5 flex-shrink-0 ${isActive ? 'text-blue-500' : 'text-[var(--color-mute)]'}`} />
                  <span className="truncate flex-1 font-sans">{conv.title || `Conversation ${conv.id}`}</span>
                </div>
                {conv.summary && (
                  <p className="mt-1 text-[11px] text-[var(--color-mute)] line-clamp-1 pl-5 font-mono">
                    {conv.summary}
                  </p>
                )}
              </button>
            );
          })
        )}
      </div>

      {/* Footer System Specs */}
      <div className="p-3 border-t border-[var(--color-hairline)] bg-[var(--color-canvas-elevated)] text-[11px] font-mono text-[var(--color-mute)] flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <Sparkles className="h-3 w-3 text-purple-500" />
          <span>Chroma + SQLite</span>
        </div>
        <span>v1.0</span>
      </div>
    </aside>
  );
};
