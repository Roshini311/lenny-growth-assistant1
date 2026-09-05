import React from 'react';
import { Plus, MessageSquare, Clock } from 'lucide-react';

interface SidebarProps {
  sessions: Array<{ id: string; title: string; date: string }>;
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  isOpen?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
}) => {
  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-full shrink-0">
      {/* New Session Button */}
      <div className="p-3 border-b border-slate-800">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs py-2 px-3 rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>+ New Chat</span>
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <div className="px-2 py-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          Recent Sessions
        </div>

        {sessions.length === 0 ? (
          <div className="px-3 py-4 text-center text-xs text-slate-500 space-y-1">
            <MessageSquare className="w-4 h-4 mx-auto text-slate-600" />
            <p>No active sessions.</p>
          </div>
        ) : (
          sessions.map((s) => {
            const isActive = s.id === activeSessionId;
            return (
              <button
                key={s.id}
                onClick={() => onSelectSession(s.id)}
                className={`w-full text-left flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs transition-colors cursor-pointer ${
                  isActive
                    ? 'bg-slate-800/90 text-indigo-300 font-semibold border border-indigo-900/60'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                <div className="min-w-0 flex-1">
                  <p className="truncate">{s.title}</p>
                  <span className="text-[10px] text-slate-500 flex items-center space-x-1 mt-0.5">
                    <Clock className="w-2.5 h-2.5" />
                    <span>{s.date}</span>
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Footer info */}
      <div className="p-3 border-t border-slate-900 text-[10px] text-slate-500 text-center">
        Lenny's Podcast Transcript RAG v1.0
      </div>
    </aside>
  );
};
