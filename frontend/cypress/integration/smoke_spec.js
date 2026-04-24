// Minimal smoke test to catch runtime import errors and route crashes

const routes = [
  { path: '/dashboard', assertText: 'Dashboard' },
  { path: '/recipes', assertText: 'Your Recipes' },
  { path: '/ingredients', assertText: 'Ingredients' },
  { path: '/orders', assertText: 'Orders' },
  { path: '/pricing', assertText: 'Pricing Configuration' },
  { path: '/calendar', assertText: 'Tasks' },
  { path: '/expenses', assertText: 'Expenses' },
  { path: '/mileage', assertText: 'Mileage Logs' },
  { path: '/reports', assertText: 'Reports' },
  { path: '/profile', assertText: 'Profile' },
];

describe('Smoke: key routes render without console errors', () => {
  beforeEach(() => {
    // Stub API calls with minimal valid responses
    cy.intercept('GET', '**/recipes*', []).as('getRecipes');
    cy.intercept('GET', '**/ingredients*', []).as('getIngredients');
    cy.intercept('GET', '**/orders*', []).as('getOrders');
    cy.intercept('GET', '**/calendar*', []).as('getCalendar');
    cy.intercept('GET', '**/tasks*', []).as('getTasks');
    cy.intercept('GET', '**/expenses*', []).as('getExpenses');
    cy.intercept('GET', '**/mileage*', []).as('getMileage');
    cy.intercept('GET', '**/pricing/configuration*', {
      id: 'cfg-1',
      user_id: 'user-1',
      hourly_rate: 0,
      overhead_per_month: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }).as('getPricing');
    cy.intercept('GET', '**/reports/profit-and-loss*', {
      total_revenue: 0,
      cost_of_goods_sold: 0,
      gross_profit: 0,
      operating_expenses: { total: 0, by_category: {} },
      net_profit: 0,
    }).as('getPnL');
    cy.intercept('GET', '**/users/users/me*', {
      id: 'user-1',
      email: 'test@example.com',
      is_active: true,
      is_superuser: false,
    }).as('getMe');
  });

  it('navigates core routes without errors', () => {
    routes.forEach(({ path, assertText }) => {
      cy.visit(path, {
        onBeforeLoad(win) {
          // Authenticate before app loads
          win.localStorage.setItem('token', 'test-token');
          win.localStorage.setItem('refreshToken', 'test-refresh');
          // Capture console errors on this page load
          cy.stub(win.console, 'error').as('consoleError');
        },
      });

      cy.contains(assertText, { matchCase: false }).should('be.visible');
      cy.get('@consoleError').should('not.have.been.called');
    });
  });
});

