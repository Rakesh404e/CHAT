import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { ChatView } from './components/ChatView';
import { MemoryInspector } from './components/MemoryInspector';
import { ObservabilityPanel } from './components/ObservabilityPanel';
import { api, User, Conversation, Message, ChatResponse } from './services/api';

export const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState(true);
  const [activeTab, setActiveTab] = useState<'chat' | 'memory' | 'observability'>('chat');

  const [users, setUsers] = useState<User[]>([]);
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [lastChatResponse, setLastChatResponse] = useState<ChatResponse | null>(null);
  const [modelName, setModelName] = useState('groq/compound-mini');
  const [provider, setProvider] = useState('groq');

  // Sync dark mode class
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Initial user loading & model telemetry
  useEffect(() => {
    const initUsers = async () => {
      try {
        const list = await api.getUsers();
        if (list.length > 0) {
          setUsers(list);
          setCurrentUserId(list[0].id);
        } else {
          const newUser = await api.createUser();
          setUsers([newUser]);
          setCurrentUserId(newUser.id);
        }
      } catch (err) {
        console.error('Failed to initialize users:', err);
      }
    };

    const fetchSystemInfo = async () => {
      try {
        const data = await api.getMetrics();
        if (data.model_name) {
          setModelName(data.model_name);
        }
        if (data.provider) {
          setProvider(data.provider);
        }
      } catch (err) {
        console.error('Failed to fetch active model:', err);
      }
    };

    initUsers();
    fetchSystemInfo();
  }, []);



  // Fetch conversations when user changes
  useEffect(() => {
    if (currentUserId === null) return;

    const loadConversations = async () => {
      try {
        const convs = await api.getConversations(currentUserId);
        setConversations(convs);
        if (convs.length > 0) {
          setCurrentConversationId(convs[0].id);
        } else {
          const newConv = await api.createConversation(currentUserId, 'My First Session');
          setConversations([newConv]);
          setCurrentConversationId(newConv.id);
        }
      } catch (err) {
        console.error('Failed to load conversations:', err);
      }
    };
    loadConversations();
  }, [currentUserId]);

  // Fetch messages when active conversation changes
  useEffect(() => {
    if (currentConversationId === null) return;

    const loadMessages = async () => {
      try {
        const msgs = await api.getMessages(currentConversationId);
        setMessages(msgs);
      } catch (err) {
        console.error('Failed to load messages:', err);
      }
    };
    loadMessages();
  }, [currentConversationId]);

  // User Handlers
  const handleSelectUser = (userId: number) => {
    setCurrentUserId(userId);
  };

  const handleCreateUser = async () => {
    try {
      const newUser = await api.createUser();
      setUsers((prev) => [newUser, ...prev]);
      setCurrentUserId(newUser.id);
    } catch (err) {
      console.error('Failed to create user:', err);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await api.deleteUser(userId);
      const remainingUsers = users.filter((u) => u.id !== userId);
      setUsers(remainingUsers);

      if (currentUserId === userId) {
        setConversations([]);
        setMessages([]);
        if (remainingUsers.length > 0) {
          setCurrentUserId(remainingUsers[0].id);
        } else {
          const newUser = await api.createUser();
          setUsers([newUser]);
          setCurrentUserId(newUser.id);
        }
      }
    } catch (err: any) {
      console.error('Failed to delete user:', err);
      alert(`Failed to delete user: ${err.message || 'Unknown error'}`);
    }
  };

  // Conversation Handlers
  const handleSelectConversation = (convId: number) => {
    setCurrentConversationId(convId);
  };

  const handleCreateConversation = async () => {
    if (currentUserId === null) return;
    try {
      const newConv = await api.createConversation(currentUserId, 'New Session');
      setConversations((prev) => [newConv, ...prev]);
      setCurrentConversationId(newConv.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  const handleDeleteConversation = async (convId: number) => {
    try {
      await api.deleteConversation(convId);
      const remainingConvs = conversations.filter((c) => c.id !== convId);
      setConversations(remainingConvs);

      if (currentConversationId === convId) {
        setMessages([]);
        if (remainingConvs.length > 0) {
          setCurrentConversationId(remainingConvs[0].id);
        } else if (currentUserId !== null) {
          const newConv = await api.createConversation(currentUserId, 'New Session');
          setConversations([newConv]);
          setCurrentConversationId(newConv.id);
          setMessages([]);
        } else {
          setCurrentConversationId(null);
          setMessages([]);
        }
      }
    } catch (err: any) {
      console.error('Failed to delete conversation:', err);
      alert(`Failed to delete conversation: ${err.message || 'Unknown error'}`);
    }
  };

  // Chat Handler
  const handleSendMessage = async (text: string) => {
    if (currentUserId === null || currentConversationId === null) return;

    // Optimistically append user message
    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.sendChatMessage(currentUserId, currentConversationId, text);
      setLastChatResponse(res);

      // Append assistant response
      const assistantMsg: Message = { role: 'assistant', content: res.assistant_response };
      setMessages((prev) => [...prev, assistantMsg]);

      // Refresh conversation title/summary if needed
      const updatedConvs = await api.getConversations(currentUserId);
      setConversations(updatedConvs);
    } catch (err: any) {
      console.error('Chat error:', err);
      const errorMsg: Message = {
        role: 'assistant',
        content: `Error: ${err.message || 'Failed to process chat response.'}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const activeConv = conversations.find((c) => c.id === currentConversationId);

  return (
    <div className="min-h-screen bg-[var(--color-canvas)] text-[var(--color-ink)] flex flex-col font-sans transition-colors duration-200">
      <Header
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        userId={currentUserId}
        modelName={modelName}
        provider={provider}
      />


      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'chat' && (
          <>
            <Sidebar
              users={users}
              currentUserId={currentUserId}
              onSelectUser={handleSelectUser}
              onCreateUser={handleCreateUser}
              onDeleteUser={handleDeleteUser}
              conversations={conversations}
              currentConversationId={currentConversationId}
              onSelectConversation={handleSelectConversation}
              onCreateConversation={handleCreateConversation}
              onDeleteConversation={handleDeleteConversation}
            />
            <ChatView
              messages={messages}
              onSendMessage={handleSendMessage}
              loading={loading}
              currentConversationTitle={activeConv?.title}
              lastChatResponse={lastChatResponse}
              onDeleteConversation={currentConversationId ? () => handleDeleteConversation(currentConversationId) : undefined}
            />
          </>
        )}

        {activeTab === 'memory' && <MemoryInspector userId={currentUserId} />}

        {activeTab === 'observability' && <ObservabilityPanel />}
      </div>
    </div>
  );
};

export default App;
