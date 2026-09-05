import React from 'react';
import { Radio } from 'lucide-react';

interface CitationBadgeProps {
  citation: string;
  onClick?: () => void;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation, onClick }) => {
  return (
    <button
      onClick={onClick}
      type="button"
      className="inline-flex items-center space-x-1 text-xs font-mono bg-indigo-950/70 border border-indigo-700/60 text-indigo-300 hover:text-white hover:bg-indigo-900/80 px-2 py-0.5 rounded-md transition-colors cursor-pointer my-0.5 mr-1"
      title="Click to view detailed transcript provenance"
    >
      <Radio className="w-3 h-3 text-indigo-400 shrink-0" />
      <span>{citation}</span>
    </button>
  );
};
