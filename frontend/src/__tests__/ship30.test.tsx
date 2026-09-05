import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Ship30Modal } from '../components/ui/Ship30Modal';

describe('Ship30Modal Component', () => {
  it('renders modal title and input when open', () => {
    render(
      <Ship30Modal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        loading={false}
        selectedProvider="ollama"
      />
    );

    expect(screen.getByText('Ship 30 for 30 Essay Generator')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e.g. High Agency Product Management/i)).toBeInTheDocument();
  });

  it('submits topic when user enters topic and clicks generate', async () => {
    const handleSubmit = vi.fn().mockResolvedValue(undefined);
    render(
      <Ship30Modal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={handleSubmit}
        loading={false}
        selectedProvider="claude"
      />
    );

    const input = screen.getByPlaceholderText(/e.g. High Agency Product Management/i);
    fireEvent.change(input, { target: { value: 'Product Led Growth' } });

    const btn = screen.getByRole('button', { name: /Generate Grounded Essay/i });
    fireEvent.click(btn);

    expect(handleSubmit).toHaveBeenCalledWith('Product Led Growth');
  });

  it('disables input and shows loading spinner when loading is true', () => {
    render(
      <Ship30Modal
        isOpen={true}
        onClose={vi.fn()}
        onSubmit={vi.fn()}
        loading={true}
        selectedProvider="openai"
      />
    );

    expect(screen.getByText('Generating Essay...')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e.g. High Agency Product Management/i)).toBeDisabled();
  });
});
