import React, { useState } from 'react';
import { User as UserIcon, Plus, MessageSquare, ChevronDown, Sparkles, Trash2 } from 'lucide-react';
import { User, Conversation } from '../services/api';

interface SidebarProps {
  users: User[];
  currentUserId: number | null;
  onSelectUser: (userId: number) => void;
  onCreateUser: () => void;
  onDeleteUser?: (userId: number) => void;
  conversations: Conversation[];
  currentConversationId: number | null;
  onSelectConversation: (convId: number) => void;
  onCreateConversation: () => void;
  onDeleteConversation?: (convId: number) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  users,
  currentUserId,
  onSelectUser,
  onCreateUser,
  onDeleteUser,
  conversations,
  currentConversationId,
  onSelectConversation,
  onCreateConversation,
  onDeleteConversation,
}) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);

  return (
    <aside className="w-64 flex-shrink-0 flex flex-col border-r border-[var(--color-hairline)] bg-[var(--color-canvas)] h-[calc(100vh-3.5rem)] select-none">
      {/* User Switcher Section */}
      <div className="p-3 border-b border-[var(--color-hairline)]">
        <div className="flex items-center justify-between mb-1.5 px-1">
          <label className="text-[10px] font-mono uppercase tracking-wider text-[var(--color-mute)]">
            Active Workspace User
          </label>
          {currentUserId !== null && onDeleteUser && (
            <button
              onClick={() => {
                if (window.confirm(`Are you sure you want to delete User #${currentUserId} and all associated memories/sessions?`)) {
                  onDeleteUser(currentUserId);
                }
              }}
              className="text-[10px] text-neutral-400 hover:text-red-500 transition-colors flex items-center space-x-0.5"
              title="Delete Active User"
            >
              <Trash2 className="h-3 w-3" />
              <span>Delete</span>
            </button>
          )}
        </div>
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
                <div
                  key={u.id}
                  className={`w-full flex items-center justify-between px-3 py-1.5 text-xs text-left transition-colors group ${
                    u.id === currentUserId
                      ? 'bg-neutral-100 dark:bg-neutral-800 font-semibold text-neutral-900 dark:text-white'
                      : 'text-[var(--color-body)] hover:bg-neutral-50 dark:hover:bg-neutral-800/40'
                  }`}
                >
                  <button
                    onClick={() => {
                      onSelectUser(u.id);
                      setShowUserDropdown(false);
                    }}
                    className="flex items-center space-x-2 flex-1 text-left truncate"
                  >
                    <UserIcon className="h-3.5 w-3.5 text-[var(--color-mute)]" />
                    <span>User #{u.id}</span>
                  </button>
                  {onDeleteUser && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Delete User #${u.id} and all associated sessions and memories?`)) {
                          setShowUserDropdown(false);
                          onDeleteUser(u.id);
                        }
                      }}
                      className="opacity-40 group-hover:opacity-100 p-1 hover:text-red-500 rounded transition-all"
                      title={`Delete User #${u.id}`}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  )}
                </div>
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
        <span className="text-[10px] font-mono uppercase tracking-wider text-neutral-600 dark:text-neutral-400 font-semibold">
          Sessions
        </span>
        <button
          onClick={onCreateConversation}
          className="flex items-center space-x-1 px-2.5 py-1 text-xs font-medium text-white bg-neutral-950 hover:bg-neutral-800 dark:bg-white dark:text-neutral-950 dark:hover:bg-neutral-200 rounded-full transition-colors shadow-sm"
          title="New Conversation"
        >
          <Plus className="h-3 w-3" />
          <span>New</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-xs text-neutral-500 dark:text-neutral-400 italic">
            No active chat sessions found. Click 'New' to start.
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conv.id === currentConversationId;
            return (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-xs transition-all text-left group border cursor-pointer ${
                  isActive
                    ? 'border-neutral-300 dark:border-neutral-700 bg-[var(--color-canvas-elevated)] font-medium text-neutral-950 dark:text-white shadow-xs'
                    : 'border-transparent text-neutral-700 dark:text-neutral-300 hover:bg-neutral-200/60 hover:text-neutral-950 dark:hover:bg-neutral-800/60 dark:hover:text-white'
                }`}
              >
                <div className="flex flex-col items-start truncate flex-1 mr-1">
                  <div className="flex items-center space-x-2 w-full truncate">
                    <MessageSquare className={`h-3.5 w-3.5 flex-shrink-0 ${isActive ? 'text-blue-500' : 'text-neutral-400 dark:text-neutral-500'}`} />
                    <span className="truncate font-sans font-medium">{conv.title || `Conversation ${conv.id}`}</span>
                  </div>
                  {conv.summary && (
                    <p className="mt-1 text-[11px] text-neutral-500 dark:text-neutral-400 line-clamp-1 pl-5 font-mono">
                      {conv.summary}
                    </p>
                  )}
                </div>

                {onDeleteConversation && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm(`Delete conversation "${conv.title || conv.id}"?`)) {
                        onDeleteConversation(conv.id);
                      }
                    }}
                    className={`p-1 hover:text-red-500 rounded transition-all flex-shrink-0 ${
                      isActive
                        ? 'opacity-60 hover:opacity-100 text-neutral-500 dark:text-neutral-400'
                        : 'opacity-0 group-hover:opacity-100 text-[var(--color-mute)]'
                    }`}
                    title={`Delete Conversation "${conv.title || conv.id}"`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
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
