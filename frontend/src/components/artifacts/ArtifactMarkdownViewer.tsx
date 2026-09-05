import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ArtifactMarkdownViewerProps {
  content: string;
}

export const ArtifactMarkdownViewer: React.FC<ArtifactMarkdownViewerProps> = ({ content }) => {
  return (
    <div className="prose prose-invert prose-indigo max-w-none text-slate-200 text-sm leading-relaxed p-4 bg-slate-900 rounded-lg border border-slate-800 overflow-y-auto">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {content}
      </ReactMarkdown>
    </div>
  );
};
