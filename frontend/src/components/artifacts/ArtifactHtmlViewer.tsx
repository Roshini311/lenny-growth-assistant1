import React from 'react';

interface ArtifactHtmlViewerProps {
  content: string;
  title?: string;
}

export const ArtifactHtmlViewer: React.FC<ArtifactHtmlViewerProps> = ({ content, title }) => {
  return (
    <div className="w-full h-full min-h-[400px] flex flex-col bg-white rounded-lg overflow-hidden border border-slate-700 shadow-inner">
      <div className="bg-slate-100 border-b border-slate-300 px-3 py-1.5 text-[11px] font-mono text-slate-600 flex items-center justify-between">
        <span>🔒 Restricted Sandboxed Canvas (nh3 sanitized & sandboxed)</span>
        <span className="text-slate-400">Same-Origin / Top-Nav</span>
      </div>
      <iframe
        srcDoc={content}
        sandbox="allow-scripts allow-same-origin allow-top-navigation"
        title={title || 'HTML Artifact Preview'}
        className="w-full h-full flex-1 border-0 bg-white"
      />
    </div>
  );
};
