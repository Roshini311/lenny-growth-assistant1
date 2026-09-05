import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatPanel } from '../components/chat/ChatPanel';
import { MessageItem } from '../components/chat/MessageItem';
import { ChatMessage } from '../types';

const FALLBACK_EXACT_STRING = "I do not have sufficient information in Lenny's podcast archive to answer this.";

describe('Chat Panel & Message Components', () => {
  it('renders initial empty state when message list is empty', () => {
    render(<ChatPanel messages={[]} onSendMessage={vi.fn()} />);
    expect(screen.getByText(/Ask Lenny's Growth Assistant/i)).toBeInTheDocument();
  });

  it('renders user and assistant messages', () => {
    const messages: ChatMessage[] = [
      {
        id: 'msg-1',
        role: 'user',
        content: 'What is PLG?',
        timestamp: '10:00 AM',
      },
      {
        id: 'msg-2',
        role: 'assistant',
        content: 'Product-led growth uses product usage as the main driver of acquisition.',
        provider: 'ollama',
        sufficient: true,
        timestamp: '10:01 AM',
      },
    ];

    render(<ChatPanel messages={messages} onSendMessage={vi.fn()} />);
    expect(screen.getByText('What is PLG?')).toBeInTheDocument();
    expect(screen.getByText(/Product-led growth uses product usage/i)).toBeInTheDocument();
  });

  it('renders exact grounding fallback string as an informational callout without changing text', () => {
    const fallbackMsg: ChatMessage = {
      id: 'msg-fallback',
      role: 'assistant',
      content: FALLBACK_EXACT_STRING,
      sufficient: false,
      timestamp: '10:02 AM',
    };

    render(<MessageItem message={fallbackMsg} />);
    expect(screen.getByText(FALLBACK_EXACT_STRING)).toBeInTheDocument();
  });

  it('submits user message on composer send button click', () => {
    const handleSend = vi.fn();
    render(<ChatPanel messages={[]} onSendMessage={handleSend} />);

    const textarea = screen.getByPlaceholderText(/Ask Lenny about product management/i);
    fireEvent.change(textarea, { target: { value: 'How did Airbnb scale?' } });

    const sendButton = screen.getByRole('button', { name: /Send message/i });
    fireEvent.click(sendButton);

    expect(handleSend).toHaveBeenCalledWith('How did Airbnb scale?');
  });
});
