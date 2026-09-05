import React, { useEffect, useRef } from 'react';
import { ChatMessage, CitationSource } from '../../types';
import { MessageItem } from './MessageItem';
import { Sparkles } from 'lucide-react';

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  onOpenSources?: (sources: CitationSource[]) => void;
  onOpenArtifact?: (artifact: any) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  isStreaming,
  onOpenSources,
  onOpenArtifact,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-900/60 text-slate-400 space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-center text-indigo-400 shadow-xl">
          <Sparkles className="w-7 h-7" />
        </div>
        <div className="space-y-1.5 max-w-md">
          <h2 className="text-lg font-bold text-slate-100 tracking-tight">
            Ask Lenny's Growth Assistant
          </h2>
          <p className="text-xs text-slate-400 leading-relaxed">
            Grounded knowledge from 260+ transcripts of Lenny's Podcast on Product Management, PLG Loops, Leadership, and Startup Execution.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto divide-y divide-slate-800/40">
      {messages.map((msg) => (
        <MessageItem
          key={msg.id}
          message={msg}
          onOpenSources={onOpenSources}
          onOpenArtifact={() => msg.artifact && onOpenArtifact && onOpenArtifact(msg.artifact)}
        />
      ))}

      {isStreaming && (
        <div className="flex items-center space-x-2 p-4 text-xs text-indigo-400 font-medium animate-pulse bg-indigo-950/20">
          <div className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
          <span>Searching transcript archive and generating grounded response...</span>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
