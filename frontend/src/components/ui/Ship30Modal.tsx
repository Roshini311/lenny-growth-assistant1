import React, { useState } from 'react';
import { ProviderType } from '../../types';
import { X, BookOpen, Sparkles, AlertCircle } from 'lucide-react';

interface Ship30ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (topic: string) => Promise<void>;
  loading: boolean;
  selectedProvider: ProviderType;
}

export const Ship30Modal: React.FC<Ship30ModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  loading,
  selectedProvider,
}) => {
  const [topic, setTopic] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!topic.trim() || loading) return;
    setError(null);
    try {
      await onSubmit(topic.trim());
      setTopic('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Ship30 essay generation failed.');
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in zoom-in-95">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-700/80 flex items-center justify-center text-indigo-400">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white leading-snug">
                Ship 30 for 30 Essay Generator
              </h2>
              <p className="text-xs text-slate-400">
                Grounded 1,250-word essay framework backed by transcript evidence.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={loading}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-950/60 border border-red-800 text-red-200 text-xs p-3 rounded-lg flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Topic Input */}
        <div className="space-y-2">
          <label className="text-xs font-semibold text-slate-300 block">
            Essay Topic or Focus Keyword:
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. High Agency Product Management, PLG Growth Loops, Product Discovery"
            disabled={loading}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all disabled:opacity-50"
          />
          <p className="text-[11px] text-slate-500">
            Provider: <span className="font-mono text-slate-300">{selectedProvider}</span>. Strict similarity distance threshold (&lt;0.4) will be enforced.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-2">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleGenerate}
            disabled={loading || !topic.trim()}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-all disabled:opacity-50 cursor-pointer shadow-md"
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Generating Essay...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate Grounded Essay</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
