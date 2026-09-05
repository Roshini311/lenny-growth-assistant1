import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CitationBadge } from '../components/citations/CitationBadge';
import { CitationDrawer } from '../components/citations/CitationDrawer';
import { CitationSource } from '../types';

describe('Citations & Provenance Components', () => {
  it('renders citation badge with episode info', () => {
    render(<CitationBadge citation="[Episode: Shreyas Doshi, 00:15:20]" />);
    expect(screen.getByText('[Episode: Shreyas Doshi, 00:15:20]')).toBeInTheDocument();
  });

  it('renders citation drawer metadata when open', () => {
    const sources: CitationSource[] = [
      {
        chunk_id: 'c1',
        episode_title: 'High Agency Leadership',
        guest: 'Shreyas Doshi',
        timestamp: '00:15:20',
        speaker: 'Shreyas',
        chunk_text: 'High agency PMs create clarity in ambiguous environments.',
        source_url: 'https://lenny.com/shreyas',
        distance: 0.22,
        citation: '[Episode: Shreyas Doshi, 00:15:20]',
      },
    ];

    render(<CitationDrawer sources={sources} isOpen={true} onClose={vi.fn()} />);

    expect(screen.getByText('High Agency Leadership')).toBeInTheDocument();
    expect(screen.getByText('Shreyas Doshi')).toBeInTheDocument();
    expect(screen.getByText('00:15:20')).toBeInTheDocument();
    expect(screen.getByText(/"High agency PMs create clarity/i)).toBeInTheDocument();
  });

  it('triggers onClose when drawer close button is clicked', () => {
    const handleClose = vi.fn();
    render(<CitationDrawer sources={[]} isOpen={true} onClose={handleClose} />);

    const closeBtn = screen.getByRole('button', { name: /Close citations drawer/i });
    fireEvent.click(closeBtn);

    expect(handleClose).toHaveBeenCalledOnce();
  });
});
