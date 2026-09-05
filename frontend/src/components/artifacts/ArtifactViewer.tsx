import React, { useState } from 'react';
import { ArtifactResponse } from '../../types';
import { ArtifactHtmlViewer } from './ArtifactHtmlViewer';
import { ArtifactMarkdownViewer } from './ArtifactMarkdownViewer';
import { X, Copy, Check, Code, Eye, FileText } from 'lucide-react';

interface ArtifactViewerProps {
  artifact: ArtifactResponse | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact, onClose }) => {
  const [viewMode, setViewMode] = useState<'rendered' | 'code'>('rendered');
  const [copied, setCopied] = useState(false);

  if (!artifact) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-slate-900 border-l border-slate-800 text-slate-500 space-y-3">
        <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400">
          <FileText className="w-6 h-6" />
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-slate-300">No Active Artifact Selected</h3>
          <p className="text-xs text-slate-400 max-w-xs">
            Generate a Ship 30 for 30 essay or request an artifact to view structured markdown and sandboxed HTML.
          </p>
        </div>
      </div>
    );
  }

  const handleCopyRaw = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 border-l border-slate-800 text-slate-100 overflow-hidden">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/90 shrink-0">
        <div className="flex items-center space-x-2.5 min-w-0">
          <span className="text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/80 shrink-0">
            {artifact.artifact_type}
          </span>
          <h2 className="text-sm font-bold text-white truncate" title={artifact.title}>
            {artifact.title}
          </h2>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-slate-800 rounded-lg p-0.5 border border-slate-700">
            <button
              onClick={() => setViewMode('rendered')}
              className={`flex items-center space-x-1 px-2.5 py-1 text-xs rounded-md transition-colors ${
                viewMode === 'rendered'
                  ? 'bg-indigo-600 text-white font-medium shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Rendered View"
            >
              <Eye className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Rendered</span>
            </button>
            <button
              onClick={() => setViewMode('code')}
              className={`flex items-center space-x-1 px-2.5 py-1 text-xs rounded-md transition-colors ${
                viewMode === 'code'
                  ? 'bg-indigo-600 text-white font-medium shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="Source Code View"
            >
              <Code className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Code</span>
            </button>
          </div>

          {/* Copy Raw Source */}
          <button
            onClick={handleCopyRaw}
            className="flex items-center space-x-1 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 px-2.5 py-1 rounded-lg transition-colors"
            title="Copy raw artifact source"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400">Copied</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-400" />
                <span>Copy</span>
              </>
            )}
          </button>

          {/* Close Panel */}
          <button
            onClick={onClose}
            aria-label="Close artifact viewer"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content View */}
      <div className="flex-1 p-4 overflow-y-auto">
        {viewMode === 'code' ? (
          <pre className="p-4 bg-slate-950 rounded-lg border border-slate-800 font-mono text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {artifact.content}
          </pre>
        ) : artifact.artifact_type === 'html' ? (
          <ArtifactHtmlViewer content={artifact.content} title={artifact.title} />
        ) : (
          <ArtifactMarkdownViewer content={artifact.content} />
        )}
      </div>
    </div>
  );
};
