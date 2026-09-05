import React from 'react';
import { CitationSource } from '../../types';
import { X, ExternalLink, Mic, Clock, User, FileText } from 'lucide-react';

interface CitationDrawerProps {
  sources: CitationSource[];
  isOpen: boolean;
  onClose: () => void;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({ sources, isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col transition-all transform animate-in slide-in-from-right">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/90">
        <div className="flex items-center space-x-2">
          <Mic className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">
            Retrieved Sources ({sources.length})
          </h3>
        </div>
        <button
          onClick={onClose}
          aria-label="Close citations drawer"
          className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Sources List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {sources.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No structured sources returned.</p>
        ) : (
          sources.map((src, idx) => (
            <div
              key={src.chunk_id || idx}
              className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-3 space-y-2.5 shadow-sm"
            >
              {/* Episode Header */}
              <div className="flex justify-between items-start">
                <h4 className="text-xs font-semibold text-indigo-300 leading-snug">
                  {src.episode_title}
                </h4>
                {src.source_url && (
                  <a
                    href={src.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-400 hover:text-indigo-400 p-0.5 transition-colors shrink-0"
                    title="Open Source Link"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>

              {/* Metadata Badges */}
              <div className="flex flex-wrap gap-2 text-[11px] text-slate-300">
                <div className="flex items-center space-x-1 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700">
                  <User className="w-3 h-3 text-slate-400" />
                  <span>{src.guest}</span>
                </div>

                {src.timestamp && (
                  <div className="flex items-center space-x-1 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700">
                    <Clock className="w-3 h-3 text-slate-400" />
                    <span>{src.timestamp}</span>
                  </div>
                )}

                {src.speaker && (
                  <div className="flex items-center space-x-1 bg-slate-900/80 px-2 py-0.5 rounded border border-slate-700">
                    <span className="text-slate-400 font-bold">Speaker:</span>
                    <span>{src.speaker}</span>
                  </div>
                )}
              </div>

              {/* Snippet */}
              <div className="bg-slate-950/80 rounded-lg p-2.5 border border-slate-800 text-xs text-slate-300 leading-relaxed font-mono">
                <div className="flex items-center space-x-1 text-[10px] text-slate-500 mb-1">
                  <FileText className="w-3 h-3" />
                  <span>Transcript Chunk Snippet</span>
                </div>
                <p className="line-clamp-4">"{src.chunk_text}"</p>
              </div>

              {/* Distance Provenance */}
              <div className="text-[10px] text-slate-500 text-right">
                Similarity Distance: <span className="font-mono text-slate-400">{src.distance}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
