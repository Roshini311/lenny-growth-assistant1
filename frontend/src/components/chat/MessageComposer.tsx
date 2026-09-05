import React, { useState, KeyboardEvent } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface MessageComposerProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const PROMPT_CHIPS = [
  "How did Brian Chesky approach product leadership at Airbnb?",
  "Explain product-led growth (PLG) loops with Lenny's podcast insights.",
  "Write a Ship 30 for 30 essay on high agency product management.",
];

export const MessageComposer: React.FC<MessageComposerProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleChipClick = (chipText: string) => {
    if (disabled) return;
    onSendMessage(chipText);
  };

  return (
    <div className="p-4 border-t border-slate-800 bg-slate-900/90 space-y-3 shrink-0">
      {/* Quick Prompt Chips */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-semibold text-slate-400 flex items-center space-x-1 mr-1">
          <Sparkles className="w-3 h-3 text-indigo-400" />
          <span>Quick Prompts:</span>
        </span>
        {PROMPT_CHIPS.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => handleChipClick(chip)}
            disabled={disabled}
            className="text-xs bg-slate-800/80 hover:bg-indigo-950/80 border border-slate-700/80 hover:border-indigo-700/80 text-slate-300 hover:text-indigo-200 px-2.5 py-1 rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer truncate max-w-xs"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input Textarea & Send Button */}
      <div className="flex items-end space-x-2 bg-slate-800/80 border border-slate-700 rounded-xl p-2 focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Lenny about product management, PLG loops, leadership, or startup growth..."
          disabled={disabled}
          rows={2}
          className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none px-2 py-1 leading-relaxed disabled:opacity-50"
        />
        <button
          onClick={handleSubmit}
          disabled={disabled || !input.trim()}
          aria-label="Send message"
          className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white p-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
