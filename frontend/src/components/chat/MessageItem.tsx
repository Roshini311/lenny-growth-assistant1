import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage, CitationSource } from '../../types';
import { CitationBadge } from '../citations/CitationBadge';
import { User, Bot, FileText, Layers, Info } from 'lucide-react';

const FALLBACK_EXACT_STRING = "I do not have sufficient information in Lenny's podcast archive to answer this.";

interface MessageItemProps {
  message: ChatMessage;
  onOpenSources?: (sources: CitationSource[]) => void;
  onOpenArtifact?: () => void;
}

export const MessageItem: React.FC<MessageItemProps> = ({
  message,
  onOpenSources,
  onOpenArtifact,
}) => {
  const isUser = message.role === 'user';
  const isFallback = message.content.trim() === FALLBACK_EXACT_STRING;

  return (
    <div className={`flex w-full space-x-3 p-4 ${isUser ? 'bg-slate-900/40' : 'bg-slate-800/40 border-y border-slate-800/60'}`}>
      {/* Role Avatar */}
      <div className="shrink-0 mt-0.5">
        {isUser ? (
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-md">
            <User className="w-4 h-4" />
          </div>
        ) : (
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white shadow-md">
            <Bot className="w-4 h-4" />
          </div>
        )}
      </div>

      {/* Message Body */}
      <div className="flex-1 space-y-2 min-w-0">
        {/* Header Name & Timestamp */}
        <div className="flex items-center space-x-2 text-xs">
          <span className="font-semibold text-slate-200">
            {isUser ? 'You' : 'Lenny Assistant'}
          </span>
          {message.provider && !isUser && (
            <span className="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded border border-slate-700">
              {message.provider}
            </span>
          )}
          <span className="text-[10px] text-slate-500">{message.timestamp}</span>
        </div>

        {/* Content */}
        {isUser ? (
          <p className="text-sm text-slate-200 leading-relaxed font-normal">{message.content}</p>
        ) : isFallback ? (
          /* Exact Fallback Informational Callout */
          <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-3 text-sm text-amber-200 flex items-start space-x-2.5">
            <Info className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <span>{FALLBACK_EXACT_STRING}</span>
          </div>
        ) : (
          /* Assistant Markdown Content */
          <div className="prose prose-invert prose-indigo max-w-none text-slate-200 text-sm leading-relaxed">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-indigo-400 animate-pulse ml-1 align-middle" />
            )}
          </div>
        )}

        {/* Citations Badges & Interactive Sources */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
            <div className="flex flex-wrap items-center gap-1">
              <span className="text-[11px] font-semibold text-slate-400 mr-1">Citations:</span>
              {message.citations.map((cite, idx) => (
                <CitationBadge
                  key={idx}
                  citation={cite}
                  onClick={() => message.sources && onOpenSources && onOpenSources(message.sources)}
                />
              ))}
            </div>

            {message.sources && message.sources.length > 0 && onOpenSources && (
              <button
                onClick={() => onOpenSources(message.sources!)}
                className="flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Inspect Sources ({message.sources.length})</span>
              </button>
            )}
          </div>
        )}

        {/* Attached Artifact Trigger Button */}
        {!isUser && message.artifact && onOpenArtifact && (
          <div className="pt-2">
            <button
              onClick={onOpenArtifact}
              className="inline-flex items-center space-x-2 bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-700/80 text-indigo-200 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all shadow-sm"
            >
              <FileText className="w-4 h-4 text-indigo-400" />
              <span>View Generated Artifact: {message.artifact.title}</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
