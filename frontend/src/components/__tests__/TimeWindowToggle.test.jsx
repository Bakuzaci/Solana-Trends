import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimeWindowToggle from '../TimeWindowToggle';

describe('TimeWindowToggle', () => {
  it('renders all time windows', () => {
    const mockOnChange = vi.fn();
    render(<TimeWindowToggle value="24h" onChange={mockOnChange} />);
    
    expect(screen.getByText('12h')).toBeInTheDocument();
    expect(screen.getByText('24h')).toBeInTheDocument();
    expect(screen.getByText('7d')).toBeInTheDocument();
  });

  it('highlights selected time window', () => {
    const mockOnChange = vi.fn();
    render(<TimeWindowToggle value="24h" onChange={mockOnChange} />);

    const button = screen.getByText('24h');
    expect(button.className).toContain('bg-purple-600');
  });

  it('calls onChange when clicking a different window', async () => {
    const user = userEvent.setup();
    const mockOnChange = vi.fn();
    render(<TimeWindowToggle value="24h" onChange={mockOnChange} />);
    
    await user.click(screen.getByText('12h'));
    expect(mockOnChange).toHaveBeenCalledWith('12h');
  });
});
