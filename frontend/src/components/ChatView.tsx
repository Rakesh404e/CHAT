import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User as UserIcon, Sparkles, Clock, Hash, CheckCircle, Terminal, Trash2 } from 'lucide-react';
import { Message, ChatResponse } from '../services/api';
import { MarkdownRenderer } from './MarkdownRenderer';

interface ChatViewProps {
  messages: Message[];
  onSendMessage: (text: string) => Promise<void>;
  loading: boolean;
  currentConversationTitle?: string;
  lastChatResponse?: ChatResponse | null;
  onDeleteConversation?: () => void;
}

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  onSendMessage,
  loading,
  currentConversationTitle,
  lastChatResponse,
  onDeleteConversation,
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    const text = inputText;
    setInputText('');
    await onSendMessage(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-3.5rem)] bg-[var(--color-canvas)]">
      {/* Mesh Gradient Top Banner */}
      <div className="mesh-gradient dark:mesh-gradient-dark border-b border-[var(--color-hairline)] px-6 py-4 flex items-center justify-between">
        <div>
          <span className="font-mono text-[11px] uppercase tracking-wider text-neutral-600 dark:text-neutral-400 font-semibold block">
            SESSION CONTEXT
          </span>
          <h2 className="text-lg font-semibold tracking-tight text-neutral-950 dark:text-white">
            {currentConversationTitle || 'Active Chat Turn'}
          </h2>
        </div>

        <div className="flex items-center space-x-3">
          {/* Telemetry quick metrics */}
          {lastChatResponse && (
            <div className="hidden md:flex items-center space-x-3 text-xs font-mono text-neutral-700 dark:text-neutral-300 bg-[var(--color-canvas-elevated)]/90 px-3 py-1.5 rounded-md border border-[var(--color-hairline)] shadow-xs">
              <div className="flex items-center space-x-1">
                <Clock className="h-3.5 w-3.5 text-blue-500" />
                <span>{Math.round(lastChatResponse.duration_ms)}ms</span>
              </div>
              <div className="flex items-center space-x-1">
                <Hash className="h-3.5 w-3.5 text-purple-500" />
                <span>{lastChatResponse.trace_id?.substring(0, 8)}</span>
              </div>
              {lastChatResponse.background_task_id && (
                <div className="flex items-center space-x-1 text-indigo-600 dark:text-indigo-400 font-medium">
                  <Sparkles className="h-3.5 w-3.5 text-indigo-500 animate-pulse" />
                  <span>async worker: {lastChatResponse.background_task_id.substring(0, 14)}...</span>
                </div>
              )}
            </div>
          )}

          {/* Delete active session button */}
          {onDeleteConversation && (
            <button
              onClick={() => {
                if (window.confirm(`Are you sure you want to delete conversation "${currentConversationTitle || 'this session'}"?`)) {
                  onDeleteConversation();
                }
              }}
              className="flex items-center space-x-1.5 px-2.5 py-1.5 text-xs text-neutral-600 dark:text-neutral-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 border border-neutral-300 dark:border-neutral-700 rounded-md transition-colors"
              title="Delete Active Session"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Delete Session</span>
            </button>
          )}
        </div>
      </div>

      {/* Messages Thread Container */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 max-w-4xl w-full mx-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-8">
            <div className="h-12 w-12 rounded-full bg-neutral-950 dark:bg-white text-white dark:text-neutral-950 flex items-center justify-center font-bold text-lg mb-4 shadow-md">
              ▲
            </div>
            <h3 className="text-xl font-semibold tracking-tight mb-2 text-neutral-950 dark:text-white">How can I assist you today?</h3>
            <p className="text-xs text-neutral-600 dark:text-neutral-400 max-w-md mb-6 leading-relaxed font-medium">
              Equipped with persistent long-term memory, semantic vector search via ChromaDB, and automatic entity extraction.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
              {[
                "My name is Rakesh and I'm a fullstack engineer",
                "Remind me about my preferred tech stack",
                "What facts do you remember about me?",
                "What API framework are we using in Python?",
              ].map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(prompt)}
                  className="hairline-card p-3 text-left text-xs text-neutral-700 dark:text-neutral-300 hover:text-neutral-950 dark:hover:text-white hover:bg-neutral-100 dark:hover:bg-neutral-800/60 hover:border-neutral-400 dark:hover:border-neutral-600 transition-all font-mono shadow-xs"
                >
                  "{prompt}"
                </button>
              ))}
            </div>
          </div>
        ) : (

          messages.map((msg, index) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={index}
                className={`flex space-x-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="h-7 w-7 rounded-sm bg-neutral-950 dark:bg-white text-white dark:text-neutral-950 flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-xs mt-0.5">
                    ▲
                  </div>
                )}

                <div
                  className={`rounded-xl px-4 py-3 text-xs sm:text-sm leading-relaxed ${
                    isUser
                      ? 'max-w-[85%] sm:max-w-[75%] bg-neutral-900 text-white dark:bg-white dark:text-neutral-900 rounded-br-xs shadow-xs'
                      : 'w-full max-w-[95%] sm:max-w-[85%] hairline-card text-neutral-900 dark:text-neutral-100 rounded-bl-xs'
                  }`}
                >
                  {/* Role Header */}
                  <div className={`text-[10px] font-mono mb-1.5 flex items-center justify-between ${isUser ? 'text-neutral-300 dark:text-neutral-600' : 'text-[var(--color-mute)]'}`}>
                    <span>{isUser ? 'You' : 'Agent Assistant'}</span>
                  </div>

                  {/* Message Content */}
                  {isUser ? (
                    <div className="whitespace-pre-wrap font-sans break-words">{msg.content}</div>
                  ) : (
                    <MarkdownRenderer content={msg.content} />
                  )}
                </div>


                {isUser && (
                  <div className="h-7 w-7 rounded-full bg-neutral-200 dark:bg-neutral-800 text-[var(--color-body)] flex items-center justify-center text-xs flex-shrink-0 mt-0.5 font-bold">
                    U
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Loading Spinner Indicator */}
        {loading && (
          <div className="flex space-x-3 justify-start items-center">
            <div className="h-7 w-7 rounded-sm bg-neutral-950 dark:bg-white text-white dark:text-neutral-950 flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-xs">
              ▲
            </div>
            <div className="hairline-card px-4 py-3 rounded-xl rounded-bl-xs flex items-center space-x-2">
              <div className="h-2 w-2 rounded-full bg-blue-500 animate-ping"></div>
              <span className="text-xs font-mono text-neutral-600 dark:text-neutral-400 font-medium">Agent is reasoning & searching long-term memory...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Prompt Box (Pill Send Button as per DESIGN.md) */}
      <div className="p-4 border-t border-[var(--color-hairline)] bg-[var(--color-canvas)]">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative flex items-center">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question or share a fact to remember..."
            rows={1}
            disabled={loading}
            className="w-full pl-4 pr-24 py-3 text-xs sm:text-sm bg-[var(--color-canvas-elevated)] text-neutral-950 dark:text-neutral-100 border border-[var(--color-hairline)] rounded-xl focus:outline-none focus:ring-1 focus:ring-neutral-400 dark:focus:ring-neutral-600 resize-none shadow-xs transition-all placeholder:text-neutral-400 dark:placeholder:text-neutral-500"
          />
          <button
            type="submit"
            disabled={loading || !inputText.trim()}
            className="absolute right-2 px-4 py-1.5 bg-neutral-950 text-white hover:bg-neutral-800 dark:bg-white dark:text-neutral-950 dark:hover:bg-neutral-200 font-medium text-xs rounded-full disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center space-x-1.5 shadow-sm"
          >
            <span>Send</span>
            <Send className="h-3 w-3" />
          </button>
        </form>
        <div className="max-w-4xl mx-auto mt-2 text-center text-[10px] font-mono text-neutral-600 dark:text-neutral-400">
          Press <kbd className="px-1 py-0.5 bg-neutral-200/70 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 rounded border border-neutral-300 dark:border-neutral-700">Enter</kbd> to send, <kbd className="px-1 py-0.5 bg-neutral-200/70 dark:bg-neutral-800 text-neutral-800 dark:text-neutral-200 rounded border border-neutral-300 dark:border-neutral-700">Shift+Enter</kbd> for new line
        </div>
      </div>
    </div>

  );
};
