import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ArtifactHtmlViewer } from '../components/artifacts/ArtifactHtmlViewer';
import { ArtifactMarkdownViewer } from '../components/artifacts/ArtifactMarkdownViewer';
import { ArtifactViewer } from '../components/artifacts/ArtifactViewer';
import { ArtifactResponse } from '../types';

describe('Artifact Viewers & Security Invariants', () => {
  it('renders sandboxed iframe for HTML artifact with strict sandbox="allow-scripts" invariant', () => {
    const htmlContent = '<div><h1>Interactive Canvas</h1><script>bad()</script></div>';
    render(<ArtifactHtmlViewer content={htmlContent} title="Sample HTML" />);

    const iframe = screen.getByTitle('Sample HTML') as HTMLIFrameElement;
    expect(iframe).toBeInTheDocument();

    // Verify DOM sandbox property attribute
    const sandboxAttr = iframe.getAttribute('sandbox');
    expect(sandboxAttr).toBe('allow-scripts');

    // Strict Security Invariant Verification (Must NOT grant same-origin or top-navigation)
    expect(sandboxAttr).not.toContain('allow-same-origin');
    expect(sandboxAttr).not.toContain('allow-top-navigation');
  });

  it('renders Markdown artifact content via ReactMarkdown', () => {
    const mdContent = '# Ship 30 Essay\n\n**Hook**: Grounded insights.';
    render(<ArtifactMarkdownViewer content={mdContent} />);

    expect(screen.getByText('Ship 30 Essay')).toBeInTheDocument();
    expect(screen.getByText('Hook')).toBeInTheDocument();
  });

  it('renders empty state in ArtifactViewer when artifact is null', () => {
    render(<ArtifactViewer artifact={null} onClose={() => {}} />);
    expect(screen.getByText(/No Active Artifact Selected/i)).toBeInTheDocument();
  });

  it('renders active artifact title and type in ArtifactViewer header', () => {
    const sampleArtifact: ArtifactResponse = {
      id: 'art-123',
      session_id: 'sess-123',
      artifact_type: 'markdown',
      title: 'PLG Loops Essay',
      content: '# Growth Framework',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<ArtifactViewer artifact={sampleArtifact} onClose={() => {}} />);
    expect(screen.getByText('PLG Loops Essay')).toBeInTheDocument();
    expect(screen.getByText('markdown')).toBeInTheDocument();
  });
});
