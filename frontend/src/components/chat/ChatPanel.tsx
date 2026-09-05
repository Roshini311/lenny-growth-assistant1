import React from 'react';
import { ChatMessage, CitationSource } from '../../types';
import { MessageList } from './MessageList';
import { MessageComposer } from './MessageComposer';

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming?: boolean;
  onSendMessage: (message: string) => void;
  onOpenSources?: (sources: CitationSource[]) => void;
  onOpenArtifact?: (artifact: any) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isStreaming,
  onSendMessage,
  onOpenSources,
  onOpenArtifact,
}) => {
  return (
    <div className="h-full flex flex-col bg-slate-900 overflow-hidden">
      <MessageList
        messages={messages}
        isStreaming={isStreaming}
        onOpenSources={onOpenSources}
        onOpenArtifact={onOpenArtifact}
      />
      <MessageComposer onSendMessage={onSendMessage} disabled={isStreaming} />
    </div>
  );
};
