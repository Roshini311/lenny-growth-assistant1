import React from 'react';
import { ProviderType } from '../../types';
import { Cpu, Cloud, Sparkles, AlertTriangle } from 'lucide-react';

interface ProviderSelectorProps {
  selectedProvider: ProviderType;
  onSelectProvider: (provider: ProviderType) => void;
  ollamaAvailable?: boolean;
}

export const ProviderSelector: React.FC<ProviderSelectorProps> = ({
  selectedProvider,
  onSelectProvider,
  ollamaAvailable = true,
}) => {
  return (
    <div className="flex flex-col space-y-1.5">
      <div className="flex items-center space-x-2">
        <label htmlFor="provider-select" className="text-xs text-slate-400 font-medium hidden sm:inline">
          LLM Provider:
        </label>
        <div className="relative">
          <select
            id="provider-select"
            value={selectedProvider}
            onChange={(e) => onSelectProvider(e.target.value as ProviderType)}
            aria-label="Select LLM Provider"
            className="bg-slate-800 text-slate-200 border border-slate-700 text-xs rounded-lg px-3 py-1.5 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-colors cursor-pointer"
          >
            <option value="ollama">Local Ollama (llama3.2:3b)</option>
            <option value="openai">OpenAI Cloud (gpt-4o-mini)</option>
            <option value="claude">Anthropic Claude (Agent SDK)</option>
          </select>
          <div className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
            {selectedProvider === 'ollama' && <Cpu className="w-3.5 h-3.5 text-emerald-400" />}
            {selectedProvider === 'openai' && <Cloud className="w-3.5 h-3.5 text-sky-400" />}
            {selectedProvider === 'claude' && <Sparkles className="w-3.5 h-3.5 text-amber-400" />}
          </div>
        </div>
      </div>

      {selectedProvider === 'ollama' && !ollamaAvailable && (
        <div className="flex items-center justify-between text-xs bg-amber-950/80 border border-amber-800/80 text-amber-200 px-3 py-1.5 rounded-lg shadow-sm">
          <div className="flex items-center space-x-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Ollama is currently unavailable.</span>
          </div>
          <button
            onClick={() => onSelectProvider('openai')}
            className="ml-2 text-xs font-semibold text-amber-300 underline hover:text-amber-100 transition-colors"
          >
            Switch to OpenAI
          </button>
        </div>
      )}
    </div>
  );
};
