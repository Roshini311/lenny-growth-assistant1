import { useState, useEffect, useCallback } from 'react';
import {
  HealthStatus,
  ProviderType,
  ChatMessage,
  ArtifactResponse,
  CitationSource,
} from './types';
import { api } from './services/api';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ChatPanel } from './components/chat/ChatPanel';
import { ArtifactViewer } from './components/artifacts/ArtifactViewer';
import { CitationDrawer } from './components/citations/CitationDrawer';
import { Ship30Modal } from './components/ui/Ship30Modal';
import { PanelRightOpen, Menu } from 'lucide-react';

export default function App() {
  // System Health & Configuration State
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState<ProviderType>('ollama');

  // Session State
  const [sessions, setSessions] = useState<Array<{ id: string; title: string; date: string }>>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  // Artifact & Provenance Drawer State
  const [activeArtifact, setActiveArtifact] = useState<ArtifactResponse | null>(null);
  const [isArtifactPanelOpen, setIsArtifactPanelOpen] = useState(false);
  const [activeSources, setActiveSources] = useState<CitationSource[]>([]);
  const [isSourcesDrawerOpen, setIsSourcesDrawerOpen] = useState(false);

  // Modal State
  const [isShip30ModalOpen, setIsShip30ModalOpen] = useState(false);
  const [isShip30Loading, setIsShip30Loading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Initial System Diagnostic & Session Bootstrapping
  useEffect(() => {
    api
      .getHealth()
      .then((data) => {
        setHealth(data);
        if (data.default_provider) {
          const prov = data.default_provider.toLowerCase();
          if (prov === 'openai' || prov === 'claude' || prov === 'ollama') {
            setSelectedProvider(prov as ProviderType);
          }
        }
      })
      .catch(() => {
        setHealth(null);
      })
      .finally(() => setHealthLoading(false));
  }, []);

  // Initialize or Select Session
  const initNewSession = useCallback(async () => {
    try {
      const newSess = await api.createSession();
      const sessItem = {
        id: newSess.id,
        title: 'New Growth Chat',
        date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setSessions((prev) => [sessItem, ...prev]);
      setActiveSessionId(newSess.id);
      setMessages([]);
      setActiveArtifact(null);
    } catch (e) {
      console.warn('Backend session auto-creation error:', e);
    }
  }, []);

  useEffect(() => {
    if (!activeSessionId && sessions.length === 0) {
      initNewSession();
    }
  }, [activeSessionId, sessions.length, initNewSession]);

  // Handle Sending Chat Message via Real SSE Endpoint
  const handleSendMessage = async (userPrompt: string) => {
    if (!userPrompt.trim() || isStreaming) return;

    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `asst-${Date.now()}`;
    const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: userPrompt.trim(),
      timestamp: timestampStr,
    };

    const assistantMsgPlaceholder: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      provider: selectedProvider,
      isStreaming: true,
      timestamp: timestampStr,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsgPlaceholder]);
    setIsStreaming(true);

    let accumulatedText = '';

    await api.streamChat(
      {
        message: userPrompt.trim(),
        session_id: activeSessionId || undefined,
        provider: selectedProvider,
        stream: true,
      },
      {
        onDelta: (delta, sessId, prov) => {
          if (sessId && sessId !== activeSessionId) {
            setActiveSessionId(sessId);
          }
          accumulatedText += delta;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? { ...msg, content: accumulatedText, provider: prov || selectedProvider }
                : msg
            )
          );
        },
        onDone: (doneData) => {
          if (doneData.sessionId && doneData.sessionId !== activeSessionId) {
            setActiveSessionId(doneData.sessionId);
          }
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedText.trim(),
                    isStreaming: false,
                    sufficient: doneData.sufficient,
                    citations: doneData.citations || [],
                    sources: doneData.sources || [],
                  }
                : msg
            )
          );
          setIsStreaming(false);

          // If session title is default, update session title from user query
          if (activeSessionId) {
            setSessions((prev) =>
              prev.map((s) =>
                s.id === activeSessionId && s.title === 'New Growth Chat'
                  ? { ...s, title: userPrompt.slice(0, 30) + '...' }
                  : s
              )
            );
          }
        },
        onError: (errMessage) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: `⚠️ Error: ${errMessage}`,
                    isStreaming: false,
                  }
                : msg
            )
          );
          setIsStreaming(false);
        },
      }
    );
  };

  // Handle Ship30 Essay Generation Request
  const handleGenerateShip30 = async (topic: string) => {
    setIsShip30Loading(true);
    try {
      const res = await api.generateShip30Essay(topic, activeSessionId || undefined, selectedProvider);

      const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const userMsg: ChatMessage = {
        id: `user-ship30-${Date.now()}`,
        role: 'user',
        content: `✦ Request Ship 30 for 30 Essay: "${topic}"`,
        timestamp: timestampStr,
      };

      const asstMsg: ChatMessage = {
        id: `asst-ship30-${Date.now()}`,
        role: 'assistant',
        content: res.essay,
        sufficient: res.sufficient,
        citations: res.citations,
        artifact: res.artifact || null,
        provider: selectedProvider,
        timestamp: timestampStr,
      };

      setMessages((prev) => [...prev, userMsg, asstMsg]);

      if (res.artifact) {
        setActiveArtifact(res.artifact);
        setIsArtifactPanelOpen(true);
      }
    } finally {
      setIsShip30Loading(false);
    }
  };

  const handleOpenSourcesDrawer = (sources: CitationSource[]) => {
    setActiveSources(sources);
    setIsSourcesDrawerOpen(true);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-slate-900 font-sans text-slate-100 overflow-hidden">
      {/* Top Application Header */}
      <Header
        health={health}
        healthLoading={healthLoading}
        selectedProvider={selectedProvider}
        onSelectProvider={setSelectedProvider}
        onOpenShip30Modal={() => setIsShip30ModalOpen(true)}
      />

      {/* Main Two-Pane Layout Container */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Toggle Sidebar Button for Mobile/Desktop */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="absolute left-2 top-2 z-30 p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white border border-slate-700 sm:hidden"
          title="Toggle Sessions Sidebar"
        >
          <Menu className="w-4 h-4" />
        </button>

        {/* Sessions Sidebar */}
        <div className={`${isSidebarOpen ? 'block' : 'hidden'} sm:block z-20`}>
          <Sidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={(id) => {
              setActiveSessionId(id);
              setMessages([]);
              setActiveArtifact(null);
            }}
            onNewSession={initNewSession}
          />
        </div>

        {/* Middle Column: Chat Panel */}
        <div className="flex-1 flex flex-col min-w-0 h-full relative">
          <ChatPanel
            messages={messages}
            isStreaming={isStreaming}
            onSendMessage={handleSendMessage}
            onOpenSources={handleOpenSourcesDrawer}
            onOpenArtifact={(art) => {
              setActiveArtifact(art);
              setIsArtifactPanelOpen(true);
            }}
          />

          {/* Floating Artifact Toggle Button when panel is collapsed */}
          {activeArtifact && !isArtifactPanelOpen && (
            <button
              onClick={() => setIsArtifactPanelOpen(true)}
              className="absolute right-4 top-4 z-20 flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-xl border border-indigo-400/40 transition-all cursor-pointer"
            >
              <PanelRightOpen className="w-4 h-4" />
              <span>View Artifact ({activeArtifact.title.slice(0, 20)}...)</span>
            </button>
          )}
        </div>

        {/* Right Column: Side-Panel Artifact Viewer */}
        {isArtifactPanelOpen && activeArtifact && (
          <div className="w-full lg:w-[48%] xl:w-[50%] h-full shrink-0 z-20 shadow-2xl transition-all">
            <ArtifactViewer
              artifact={activeArtifact}
              onClose={() => setIsArtifactPanelOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Citations / Sources Drawer Overlay */}
      <CitationDrawer
        sources={activeSources}
        isOpen={isSourcesDrawerOpen}
        onClose={() => setIsSourcesDrawerOpen(false)}
      />

      {/* Ship 30 Essay Generation Modal */}
      <Ship30Modal
        isOpen={isShip30ModalOpen}
        onClose={() => setIsShip30ModalOpen(false)}
        onSubmit={handleGenerateShip30}
        loading={isShip30Loading}
        selectedProvider={selectedProvider}
      />
    </div>
  );
}
