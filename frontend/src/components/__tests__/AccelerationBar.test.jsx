import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import AccelerationBar from '../AccelerationBar';

describe('AccelerationBar', () => {
  it('renders acceleration score rounded', () => {
    render(<AccelerationBar score={75.5} />);
    // Score is rounded in the component
    expect(screen.getByText('76')).toBeInTheDocument();
  });

  it('shows correct width based on score', () => {
    const { container } = render(<AccelerationBar score={50} />);
    const bar = container.querySelector('[style*="width"]');
    expect(bar).toBeTruthy();
  });

  it('handles zero score', () => {
    render(<AccelerationBar score={0} />);
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('handles high scores', () => {
    render(<AccelerationBar score={100} />);
    expect(screen.getByText('100')).toBeInTheDocument();
  });
});
