import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Orders from './Orders';
import { ordersApi } from '../api';
import type { DayRunningQueueSummary, OrderRecord } from '../api';

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

(globalThis as unknown as { ResizeObserver: typeof ResizeObserver }).ResizeObserver =
  ResizeObserverMock as unknown as typeof ResizeObserver;

const summary: DayRunningQueueSummary = {
  all_count: 2,
  blocked_count: 0,
  needs_attention_count: 1,
  ready_count: 1,
};

function makeOrder(overrides: Partial<OrderRecord>): OrderRecord {
  return {
    id: '1',
    order_number: '1001',
    status: 'confirmed',
    payment_status: 'unpaid',
    order_date: '2025-01-01T12:00:00Z',
    due_date: '2025-03-01T12:00:00Z',
    deposit_due_date: '2025-02-01',
    balance_due_date: '2025-03-01',
    delivery_method: 'Pickup',
    notes_to_customer: null,
    internal_notes: null,
    total_amount: 100,
    balance_due: 100,
    is_imported: false,
    review_reasons: [],
    imported_priority_rank: 0,
    customer_name: 'Alice',
    customer_email: 'alice@example.com',
    customer_phone: null,
    customer_summary: {
      contact_id: null,
      name: 'Alice',
      email: 'alice@example.com',
      phone: null,
      is_linked_contact: false,
    },
    payment_summary: {
      amount_paid: 0,
      amount_due: 100,
      deposit_required: 50,
      deposit_outstanding: 50,
      balance_due: 100,
      is_paid_in_full: false,
    },
    invoice_summary: {
      is_ready: true,
      status: 'ready',
      missing_fields: [],
      pdf_path: null,
      client_portal_path: null,
    },
    queue_summary: {
      is_due_today: false,
      is_overdue: false,
      days_until_due: 2,
      due_bucket: 'soon',
      urgency_label: 'Next up',
      urgency_rank: 2,
    },
    customer_history_summary: {
      total_orders: 1,
      completed_orders: 0,
      active_orders: 1,
      last_order_date: null,
    },
    recent_customer_orders: [],
    risk_summary: {
      level: 'low',
      reasons: [],
      overdue_amount: 0,
      outstanding_amount: 100,
      has_overdue_payment: false,
    },
    payment_focus_summary: {
      amount_owed_now: 50,
      payment_state: 'deposit_due',
      collection_stage: 'deposit',
      deposit_status: 'Deposit open',
      balance_status: 'Balance pending',
      due_timing: 'Upcoming',
      risk_note: 'No overdue payment risk',
      next_step: 'Collect deposit',
      next_step_detail: 'Collect deposit before baking.',
      trust_state: 'trusted',
      trust_label: 'Current record',
      trust_note: 'Payment data is current.',
    },
    handoff_focus_summary: {
      handoff_time_label: 'Due soon',
      method_status: 'pickup',
      method_label: 'Pickup',
      contact_name: 'Alice',
      primary_contact: 'alice@example.com',
      secondary_contact: null,
      destination_label: 'Pickup',
      destination_detail: 'Pickup',
      readiness_note: 'Ready for handoff',
      missing_basics: [],
      next_step: 'Confirm pickup',
      next_step_detail: 'Confirm pickup window.',
    },
    review_focus_summary: {
      order_number: '1001',
      customer_name: 'Alice',
      due_label: 'Due soon',
      status_label: 'Confirmed',
      item_summary: 'Cake',
      item_count_label: '1 item',
      payment_confidence: 'Payment open',
      invoice_confidence: 'Invoice ready',
      handoff_confidence: 'Pickup ready',
      contact_confidence: 'Email available',
      risk_note: 'No risk',
      missing_basics: [],
      next_step: 'Review order',
      next_step_detail: 'Review order details.',
    },
    production_focus_summary: {
      readiness_label: 'Ready to make',
      attention_note: 'Production details are ready.',
      contents_summary: 'Cake',
      item_count_label: '1 item',
      item_count: 1,
      primary_item_names: ['Cake'],
      missing_basics: [],
      next_step: 'Start baking',
      next_step_detail: 'Start baking the order.',
    },
    contact_focus_summary: {
      readiness_label: 'Ready to contact',
      display_name: 'Alice',
      best_contact_methods_summary: 'Email: alice@example.com',
      urgency_note: 'No urgent contact needed.',
      attention_note: 'Contact details are ready.',
      missing_basics: [],
      next_step: 'Email customer',
      next_step_detail: 'Email customer if needed.',
    },
    day_running_focus_summary: {
      readiness_label: 'Ready for today',
      reason_summary: 'No blocker',
      primary_blocker_label: 'Ready',
      next_step: 'Keep on schedule',
      supporting_items: [],
    },
    invoice_focus_summary: {
      status_label: 'Ready',
      readiness_note: 'Invoice is ready.',
      order_identity: '1001',
      customer_identity: 'Alice',
      amount_summary: '$100.00',
      payment_context: 'Deposit open',
      blockers: [],
      missing_basics: [],
      next_step: 'Send invoice',
      next_step_detail: 'Send invoice when ready.',
    },
    ops_summary: {
      next_action: 'Collect deposit',
      ops_attention: 'Deposit should be collected before production.',
      action_class: 'payment_now',
      primary_cta_label: 'Collect payment',
      primary_cta_path: '/orders/1',
      primary_cta_panel: 'payment',
    },
    items: [],
    ...overrides,
  };
}

describe('Orders page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(ordersApi, 'list').mockResolvedValue([
      makeOrder({ id: '1', order_number: '1001' }),
      makeOrder({
        id: '2',
        order_number: '1002',
        customer_name: 'Bob',
        total_amount: 200,
        customer_summary: {
          contact_id: null,
          name: 'Bob',
          email: 'bob@example.com',
          phone: null,
          is_linked_contact: false,
        },
        queue_summary: {
          is_due_today: true,
          is_overdue: false,
          days_until_due: 0,
          due_bucket: 'today',
          urgency_label: 'Today',
          urgency_rank: 1,
        },
      }),
    ]);
    vi.spyOn(ordersApi, 'getDayRunningSummary').mockResolvedValue(summary);
  });

  it('renders ops queue orders after fetching', async () => {
    render(
      <MemoryRouter>
        <Orders />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/1001/)).toBeInTheDocument();
    expect(screen.getByText(/1002/)).toBeInTheDocument();
    expect(screen.getByText('Visible orders').nextSibling?.textContent).toBe('2');
    expect(ordersApi.list).toHaveBeenCalled();
  });

  it('refetches when day-running filter changes', async () => {
    render(
      <MemoryRouter>
        <Orders />
      </MemoryRouter>,
    );

    await screen.findByText(/1001/);
    fireEvent.click(screen.getAllByRole('button', { name: /Needs attention today/ })[0]);

    await waitFor(() => {
      expect(ordersApi.list).toHaveBeenLastCalledWith({
        day_running: 'needs_attention',
        action_class: undefined,
        urgency: undefined,
      });
    });
  });
});
