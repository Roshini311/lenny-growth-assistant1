import React from 'react';
import { HealthStatus, ProviderType } from '../../types';
import { HealthBadge } from '../ui/HealthBadge';
import { ProviderSelector } from '../ui/ProviderSelector';
import { Sparkles, BookOpen } from 'lucide-react';

interface HeaderProps {
  health: HealthStatus | null;
  healthLoading: boolean;
  selectedProvider: ProviderType;
  onSelectProvider: (provider: ProviderType) => void;
  onOpenShip30Modal: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  healthLoading,
  selectedProvider,
  onSelectProvider,
  onOpenShip30Modal,
}) => {
  return (
    <header className="h-16 bg-slate-900 border-b border-slate-800 px-4 sm:px-6 flex items-center justify-between shrink-0 shadow-sm z-20">
      {/* Brand Title */}
      <div className="flex items-center space-x-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shadow-md">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-base font-bold text-white tracking-tight leading-none">
            The Lenny Growth Assistant
          </h1>
          <p className="text-[10px] text-slate-400 mt-0.5 hidden sm:block">
            Grounded RAG Knowledge Assistant for Lenny's Podcast
          </p>
        </div>
      </div>

      {/* Controls & Actions */}
      <div className="flex items-center space-x-3 sm:space-x-4">
        <HealthBadge health={health} loading={healthLoading} />

        <ProviderSelector
          selectedProvider={selectedProvider}
          onSelectProvider={onSelectProvider}
        />

        <button
          onClick={onOpenShip30Modal}
          className="flex items-center space-x-1.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-md transition-all cursor-pointer"
          title="Generate a grounded Ship 30 for 30 essay"
        >
          <BookOpen className="w-3.5 h-3.5" />
          <span className="hidden md:inline">✦ Ship 30 Essay</span>
        </button>
      </div>
    </header>
  );
};
