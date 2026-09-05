import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ProviderSelector } from '../components/ui/ProviderSelector';

describe('ProviderSelector Component', () => {
  it('renders LLM provider options', () => {
    render(<ProviderSelector selectedProvider="ollama" onSelectProvider={vi.fn()} />);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Local Ollama (llama3.2:3b)')).toBeInTheDocument();
  });

  it('triggers provider change callback on dropdown selection', () => {
    const handleSelect = vi.fn();
    render(<ProviderSelector selectedProvider="ollama" onSelectProvider={handleSelect} />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'openai' } });

    expect(handleSelect).toHaveBeenCalledWith('openai');
  });

  it('renders warning banner when Ollama is selected but unavailable', () => {
    render(
      <ProviderSelector
        selectedProvider="ollama"
        onSelectProvider={vi.fn()}
        ollamaAvailable={false}
      />
    );

    expect(screen.getByText(/Ollama is currently unavailable/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Switch to OpenAI/i })).toBeInTheDocument();
  });
});
