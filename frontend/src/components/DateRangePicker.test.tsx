import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import DateRangePicker from './DateRangePicker';

describe('DateRangePicker', () => {
  it('shows 2-year and all options', () => {
    render(<DateRangePicker value="ytd" onChange={() => {}} />);
    expect(screen.getByRole('option', { name: 'Last 2 Years' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
  });
});
