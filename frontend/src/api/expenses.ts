import apiClient from './index';

export interface Expense {
  id: string;
  amount: number;
  description: string;
  date: string;
  category?: string;
}

export type ExpenseInput = Omit<Expense, 'id'>;

export async function listExpenses(params?: {
  start_date?: string;
  end_date?: string;
  category?: string;
}): Promise<Expense[]> {
  // Fetch all expenses in batches (API default limit=100, max=200)
  const all: Expense[] = [];
  const limit = 200;
  let skip = 0;
  while (true) {
    const response = await apiClient.get<Expense[]>('/expenses', {
      params: { skip, limit, ...(params ?? {}) },
    });
    const batch = response.data;
    if (!batch.length) break;
    all.push(...batch);
    if (batch.length < limit) break;
    skip += limit;
  }
  return all;
}

export async function createExpense(expense: ExpenseInput): Promise<Expense> {
  // Backend expects multipart/form-data with field aliases: date, description, amount
  const fd = new FormData();
  fd.append('date', expense.date);
  fd.append('description', expense.description);
  fd.append('amount', String(expense.amount));
  if (expense.category) fd.append('category', expense.category);
  const response = await apiClient.post<Expense>('/expenses/', fd);
  return response.data;
}

export async function updateExpense(
  id: string,
  expense: Partial<ExpenseInput>
): Promise<Expense> {
  // Use multipart for updates; field aliases match server: date, description, amount, category
  const fd = new FormData();
  // Temporarily avoid updating date due to backend validation issue
  if (expense.description !== undefined) fd.append('description', expense.description);
  if (expense.amount !== undefined) fd.append('amount', String(expense.amount));
  if (expense.category !== undefined) fd.append('category', expense.category);

  // Avoid trailing slash to prevent 307 redirect, and add a short retry if DB is locked
  const url = `/expenses/${id}`;
  const maxAttempts = 3;
  const backoffMs = 250;
  let lastErr: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await apiClient.put<Expense>(url, fd);
      return response.data;
    } catch (err: unknown) {
      const error = err as {
        response?: { data?: unknown; status?: number };
        message?: string;
      };
      const msg = String(error.response?.data ?? error.message ?? '');
      const status = error.response?.status;
      if (status === 500 && msg.toLowerCase().includes('database is locked') && attempt < maxAttempts) {
        await new Promise((r) => setTimeout(r, backoffMs));
        continue;
      }
      lastErr = err;
      break;
    }
  }
  throw lastErr;
}

export async function deleteExpense(id: string): Promise<void> {
  await apiClient.delete(`/expenses/${id}`);
}
