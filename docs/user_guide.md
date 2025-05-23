# BakeMate User Guide

## Welcome to BakeMate!

Let's bake smarter! BakeMate is your all-in-one companion for managing your solo baking business. This guide will walk you through setting up your account, managing your bakery operations, and utilizing BakeMate's powerful features to streamline your workflow and grow your business.

## Table of Contents

1.  [Getting Started](#getting-started)
    *   [Creating Your Account](#creating-your-account)
    *   [Initial Setup Wizard](#initial-setup-wizard)
    *   [Navigating the Dashboard](#navigating-the-dashboard)
2.  [Core Modules](#core-modules)
    *   [Ingredients Management](#ingredients-management)
    *   [Recipes Management](#recipes-management)
    *   [Pricing Engine](#pricing-engine)
    *   [Quotes & Orders](#quotes--orders)
    *   [Calendar & Tasks](#calendar--tasks)
    *   [Expenses & Mileage](#expenses--mileage)
    *   [Reports](#reports)
3.  [Differentiator Features](#differentiator-features)
    *   [Mini-Shop / Online Order Form](#mini-shop--online-order-form)
    *   [Real-Time Inventory Tracking](#real-time-inventory-tracking)
    *   [Email Marketing Hooks](#email-marketing-hooks)
4.  [Account Management](#account-management)
    *   [Profile Settings](#profile-settings)
    *   [Security](#security)
5.  [Troubleshooting & Support](#troubleshooting--support)

---

## 1. Getting Started

### Creating Your Account

To begin using BakeMate, you'll first need to create an account. 

1.  Navigate to the BakeMate registration page (e.g., `https://app.bakemate.com/register`).
2.  Fill in your full name, email address, and choose a secure password. We recommend a password that is at least 12 characters long, including a mix of uppercase letters, lowercase letters, numbers, and symbols.
3.  Read and accept the Terms of Service and Privacy Policy.
4.  Click the "Register" button.
5.  You will receive an email verification link to the email address you provided. Click this link to activate your account. If you don't see the email in your inbox, please check your spam or junk folder.

Once your email is verified, you can log in to BakeMate using your credentials.

### Initial Setup Wizard

Upon your first login, BakeMate will guide you through an initial setup wizard. This wizard is designed to help you quickly configure the essential aspects of your bakery and get you started with the core features. The wizard will prompt you to:

1.  **Set Up Your Bakery Profile:** Enter basic information about your bakery, such as its name and your primary currency (USD is the default for U.S. bakers).
2.  **Add Your First Ingredient:** Learn how to add ingredients, specifying their name, unit of measurement (e.g., grams, ml, pcs), cost per unit, and optionally, density (useful for conversions between weight and volume).
3.  **Create Your First Recipe:** Get hands-on experience creating a recipe. You'll name your recipe, list the ingredients and their quantities, and outline the preparation steps. BakeMate will automatically calculate the base cost of your recipe based on the ingredients you add.
4.  **Configure Basic Pricing Settings:** Set your desired hourly labor rate and estimated monthly overhead costs. BakeMate uses this information in its pricing engine to help you determine profitable selling prices for your products.
5.  **Simulate Your First Order (Optional):** The wizard may offer a quick walkthrough of creating a sample order to familiarize you with the order management process.

Completing the setup wizard will give you a solid foundation for using BakeMate effectively. You can always revisit and update these settings later from your dashboard.

### Navigating the Dashboard

The BakeMate dashboard is your central hub for managing all aspects of your baking business. The layout is designed to be intuitive and mobile-friendly, ensuring you can access your information whether you're in the kitchen or on the go.

*   **Main Navigation:** Typically located on the left side (desktop) or accessible via a menu icon (mobile), the main navigation provides links to all major modules: Ingredients, Recipes, Orders, Calendar, Expenses, Reports, Shop, Marketing, etc.
*   **Overview/Summary Area:** The main dashboard page usually displays a summary of key metrics, upcoming tasks, recent orders, or low-stock alerts, giving you an at-a-glance view of your business status.
*   **Action Buttons:** Common actions like "Add New Ingredient," "Create Recipe," or "New Order" are usually prominently displayed within their respective modules or on the dashboard.
*   **User Profile & Settings:** Access your account settings, profile information, and logout options, typically from an icon or link in the top-right corner.

We encourage you to explore each section to become familiar with the tools and features available.

---

## 2. Core Modules

BakeMate offers a comprehensive suite of modules to cover every aspect of your bakery management.

### Ingredients Management

Properly managing your ingredients is crucial for accurate costing and inventory control. 

*   **Adding Ingredients:**
    *   Navigate to the "Ingredients" section.
    *   Click "Add New Ingredient."
    *   Enter the ingredient's name (e.g., "All-Purpose Flour," "Belgian Dark Chocolate Chips").
    *   Specify the purchase unit (e.g., kg, lbs, bag, liter) and the cost for that unit.
    *   Specify the usage unit (e.g., g, oz, ml, pcs) – this is how you'll use it in recipes. BakeMate will help with conversions if purchase and usage units differ, especially if density is provided.
    *   Enter the cost per usage unit. If you enter cost per purchase unit and the conversion factor, BakeMate can calculate this.
    *   Optionally, enter the density (e.g., for flour, 0.6 g/ml) if you need to convert between weight and volume in your recipes.
    *   If using Real-Time Inventory (see Differentiator Features), you can also input the current `Quantity on Hand` and a `Low Stock Threshold`.
*   **Viewing & Editing Ingredients:** Your ingredients list will show all entered items. You can click on any ingredient to view its details, edit information, or delete it (if not currently used in active recipes or orders).
*   **Search & Filter:** Quickly find ingredients using the search bar or filter options.

### Recipes Management

This module is where your culinary creations come to life and where BakeMate helps you understand their costs.

*   **Creating a New Recipe:**
    *   Go to the "Recipes" section.
    *   Click "Create New Recipe."
    *   Give your recipe a name (e.g., "Classic Chocolate Chip Cookies," "Sourdough Loaf").
    *   Add a description, serving size, or yield (e.g., "Makes 24 cookies," "Yields 2 loaves").
    *   **Adding Ingredients to Recipe:** Select ingredients from your existing list and specify the quantity needed for the recipe (e.g., 250g All-Purpose Flour, 150g Belgian Dark Chocolate Chips). BakeMate will display the cost of each ingredient for the specified quantity and sum these up to show the total ingredient cost for the recipe.
    *   **Adding Preparation Steps:** Detail the method for creating your baked good. You can add multiple steps with clear instructions.
    *   **Recipe Cost Calculation:** BakeMate automatically calculates the total material cost for one batch of the recipe based on the costs of the added ingredients. If you update an ingredient's cost, all linked recipes will have their costs automatically recalculated.
*   **Viewing & Editing Recipes:** Browse your list of recipes. Click to view details, edit ingredients, steps, or other information. You can also duplicate recipes to create variations easily.
*   **Pricing Your Recipe:** The recipe view will show the material cost. You can then use the Pricing Engine to determine a suggested selling price.

### Pricing Engine

BakeMate's Pricing Engine helps you move from raw material costs to profitable selling prices.

*   **Configuration:**
    *   Navigate to "Settings" > "Pricing Configuration."
    *   **Hourly Labor Rate:** Enter your desired hourly rate for the time you spend baking and decorating.
    *   **Monthly Overhead Costs:** Input your total fixed monthly business expenses (e.g., rent for a commercial kitchen, utilities, software subscriptions, insurance). BakeMate will help distribute this overhead across your orders or a time period to ensure it's covered.
*   **Applying Pricing to Recipes/Orders:**
    *   When viewing a recipe, you can estimate the labor time required.
    *   BakeMate can then suggest a price by adding: Material Cost + (Labor Time * Hourly Rate) + Portion of Overhead.
    *   **Yield/Servings Calculator:** For recipes that produce multiple servings (e.g., a batch of cookies, a large cake), you can specify the yield. The pricing engine will then help calculate the per-serving cost and suggest a per-serving price.
    *   **Tin/Batch Size Scaler (Advanced):** For some recipes, you might need to scale them up or down based on different tin sizes or batch requirements. BakeMate aims to provide tools to help with these calculations, ensuring your costs and pricing remain accurate (this feature may be a placeholder in early versions, with full functionality developed over time).
*   **Profit Margin Analysis:** The pricing tools will help you see the breakdown of costs and potential profit margins, allowing you to make informed decisions about your pricing strategy.

### Quotes & Orders

Manage customer inquiries, quotes, and confirmed orders efficiently.

*   **Creating a Quote:**
    *   When a customer inquires about a custom order, navigate to "Quotes" and click "New Quote."
    *   Enter customer details (name, email, phone).
    *   Add items to the quote, selecting from your existing recipes or creating custom items with descriptions and prices.
    *   Specify quantities, desired due date, and any notes or special requests.
    *   BakeMate will calculate the total quote amount. You can adjust pricing, add discounts, or include delivery fees.
    *   Save the quote. You can then send it to the customer (e.g., as a PDF generated by BakeMate).
*   **Converting Quote to Order:** Once a customer accepts a quote, you can easily convert it into a confirmed order with a single click. This transfers all the details to the Orders module.
*   **Creating an Order Directly:** For straightforward orders not requiring a formal quote, you can create an order directly in the "Orders" section.
*   **Order Status Workflow:** Orders progress through various statuses:
    *   `Inquiry` (for initial quote requests)
    *   `Quoted`
    *   `New-Online` (for orders from the Mini-Shop)
    *   `Confirmed` (customer has agreed, deposit may be paid)
    *   `Preparing` (you've started working on it)
    *   `Ready for Pickup/Delivery`
    *   `Completed` (order fulfilled and fully paid)
    *   `Cancelled`
*   **Managing Orders:**
    *   View all orders in a list or a Kanban-style board (if available).
    *   Filter orders by status, due date, or customer.
    *   Open an order to view details, update status, add notes, or manage payments.
    *   **Scheduled Payments:** For large orders, you can record a deposit percentage and track the balance due date.
    *   **Attaching Files:** You can attach design files, inspiration images, or other relevant documents (up to 5MB per file) to an order (this feature is planned).
*   **Stripe Integration (Payment Processing):**
    *   BakeMate integrates with Stripe for online payments. You'll need to connect your Stripe account in the Settings.
    *   **Payment Intents:** When an order is confirmed, BakeMate can create a Stripe Payment Intent, allowing customers to pay online securely.
    *   **Payment Links:** Generate and share Stripe payment links for invoices or orders.
    *   **Webhooks:** BakeMate listens for Stripe webhooks (e.g., `invoice.paid`) to automatically update order payment statuses.
*   **Invoices:**
    *   Generate professional PDF invoices for your orders. Invoices will include your bakery details, customer information, itemized list of products/services, total amount due, and payment instructions.
    *   The "Pay Now" button on invoices (if Stripe is connected) will direct customers to a Stripe Checkout page (this feature is planned).
*   **Client Portal (Planned):** A secure, read-only portal where customers can view their order status and history, and make payments. Access will be via a unique, signed link (e.g., using a JWT in the query parameter).

### Calendar & Tasks

Stay organized and manage your production schedule effectively.

*   **Calendar View:**
    *   Access a visual calendar displaying your orders, tasks, and other important events.
    *   View by month, week, or agenda (list view).
    *   Order due dates are automatically populated on the calendar when an order is confirmed.
    *   Manually add custom events, appointments, or reminders (e.g., supplier deliveries, market days).
*   **Google Calendar Sync (Optional):**
    *   Optionally, connect your Google Calendar to BakeMate for two-way synchronization. Events created in BakeMate will appear in your Google Calendar, and vice-versa (ensure you manage privacy settings appropriately).
    *   This helps you see your baking schedule alongside your personal appointments.
*   **Tasks Management:**
    *   Create and manage a to-do list for your bakery operations.
    *   Tasks can be general (e.g., "Order packaging supplies") or linked to specific orders (e.g., "Bake 3 dozen cookies for Order #123," "Decorate wedding cake for Order #124").
    *   Assign due dates and priorities to tasks.
    *   Mark tasks as complete.
*   **Weekly Digest Email:**
    *   Receive an automated email digest every Monday at 6 AM ET (configurable). 
    *   This email will summarize your confirmed orders and open tasks for the upcoming week, helping you plan effectively.
    *   This requires SendGrid to be configured.

### Expenses & Mileage

Keep track of your business expenses and mileage for accurate financial records and tax purposes.

*   **Expenses Tracking:**
    *   Navigate to the "Expenses" module.
    *   Record all your business-related expenses (e.g., ingredient purchases, packaging costs, marketing expenses, software subscriptions).
    *   Categorize expenses for better analysis.
    *   Enter the date, amount, vendor, and a description for each expense.
    *   **Receipt Upload:** Attach digital copies of your receipts (PDF or JPEG, up to 3MB per file) to each expense entry for easy record-keeping.
*   **Mileage Log:**
    *   If you use your vehicle for business purposes (e.g., deliveries, ingredient shopping), log your mileage.
    *   Enter the date, purpose of the trip, start and end odometer readings (or just total miles for the trip).
    *   **Automatic Reimbursement Calculation:** BakeMate can automatically calculate the mileage reimbursement amount based on a standard rate (e.g., the current IRS standard mileage rate). You will be able to set your preferred rate in settings (user setting integration is planned, defaults to a standard rate initially).

### Reports

Gain insights into your bakery's performance with a range of financial and operational reports.

*   **Available Reports:**
    *   **Profit & Loss (P&L) Report:** Shows your revenue, cost of goods sold (COGS), operating expenses, and net profit over a selected period. This is crucial for understanding your overall financial health.
    *   **Sales by Product Report:** See which of your products are bestsellers and which contribute most to your revenue. Helps in making decisions about your product offerings.
    *   **Ingredient Usage Report:** Track how much of each ingredient you've used over a period. Useful for reordering and identifying potential waste.
    *   **Low Stock Report:** If using Real-Time Inventory, this report lists ingredients that are below their set low-stock threshold, helping you manage reordering proactively.
*   **Filtering & Date Ranges:** Most reports can be filtered by date range (e.g., last month, last quarter, custom range) to analyze specific periods.
*   **Exporting Reports:** Download your reports in CSV format for further analysis in spreadsheet software (like Excel or Google Sheets) or for sharing with your accountant. PDF download functionality is planned for a more presentable format.

---

## 3. Differentiator Features

BakeMate includes unique features designed to give your solo baking business an edge.

### Mini-Shop / Online Order Form

Take your business online easily with an embeddable mini-shop or a shareable shop page.

*   **Shop Configuration:**
    *   Navigate to "Shop Settings" or "My Mini-Shop."
    *   **Shop Details:** Set your shop name, a brief description, contact email, and upload a logo.
    *   **Shop Slug:** Choose a unique, URL-friendly slug (e.g., `your-bakery-name`) for your shareable shop page (`https://app.bakemate.com/shop/your-bakery-name`).
    *   **Theme:** Customize the look with a primary and secondary color (defaults to BakeMate's soft pastel palette).
    *   **Products:** Select which of your existing recipes you want to offer in your mini-shop. For each product, you can set a specific shop price (which can differ from your internal calculated price), add a dedicated shop description, and an image.
    *   **Availability:** Mark products as available or unavailable in the shop.
    *   **Order Settings:** Configure whether to accept online orders, set minimum or maximum order values, define delivery options (e.g., pickup only, local delivery with fee and radius), and specify accepted payment methods (Stripe is the primary integration).
    *   **Activate Your Shop:** Once configured, set your shop status to "Active."
*   **Embeddable Snippet & Shareable Page:**
    *   **Wizard:** BakeMate provides a simple wizard to generate an HTML snippet (`<script src="..."></script>`). You can copy and paste this snippet into your existing website (e.g., WordPress, Squarespace, Wix) to embed your mini-shop directly onto a page.
    *   **Shareable URL:** Alternatively, you can simply share the direct link to your BakeMate-hosted shop page (e.g., `https://app.bakemate.com/shop/your-bakery-name`). This is great if you don't have your own website yet.
*   **How it Works for Customers:**
    *   Customers visit your embedded shop or shareable shop page.
    *   They browse available products, add items to their cart, and proceed to checkout.
    *   They provide their contact details, choose delivery/pickup options, and can pay online if Stripe is connected.
*   **Order Management:**
    *   Orders placed through your mini-shop automatically appear in your BakeMate Orders module with a status of `New-Online`.
    *   You and the customer will receive an automatic email confirmation for the new order (requires SendGrid configuration).
    *   You then process the online order like any other order in BakeMate, updating its status as you prepare and fulfill it.

### Real-Time Inventory Tracking (Optional)

Keep a close eye on your ingredient stock levels automatically.

*   **Enabling the Feature:** This feature can be toggled on or off in your BakeMate settings. If it's off, the `Quantity on Hand` and `Low Stock Threshold` fields for ingredients will be hidden or disabled.
*   **Setting Initial Stock:**
    *   When adding a new ingredient or editing an existing one, input the current `Quantity on Hand` (e.g., 2500 grams of flour).
    *   Set a `Low Stock Threshold` (e.g., 500 grams). When the quantity on hand drops below this threshold, BakeMate will alert you.
*   **Automatic Stock Deduction:**
    *   When you confirm an order (or move it to a status like `Preparing`), BakeMate automatically looks up the recipes for the items in that order.
    *   It then calculates the total quantity of each ingredient required for the order and deducts these amounts from your `Quantity on Hand` for each respective ingredient.
*   **Manual Adjustments:** You can also manually adjust stock levels if needed (e.g., after a new ingredient purchase, or to account for spoilage or personal use).
*   **Low Stock Alerts:**
    *   **Email Notifications:** When an ingredient's stock level falls below its set threshold (either due to automatic deduction from an order or a manual adjustment), BakeMate will send you an email alert (requires SendGrid).
    *   **UI Indicators:** The BakeMate dashboard and ingredients list will visually indicate low-stock items (e.g., with a badge or color coding), prompting you to reorder.
    *   **Cron Job:** A background process (cron job) periodically checks all ingredients for low stock levels to catch anything missed and can trigger alerts.
*   **Benefits:** Helps prevent running out of key ingredients, reduces manual stock-taking, and provides data for the Low Stock Report.

### Email Marketing Hooks

Engage with your customers through simple, targeted email campaigns.

*   **Contact Management:** BakeMate automatically builds a list of your contacts from orders and quotes. You can also manually add contacts.
*   **Customer Segmentation:**
    *   BakeMate helps you create dynamic segments of your customers. Initial segments include:
        *   **Top Customers:** Identify customers who order frequently or have a high total order value (e.g., customers with more than X completed orders or total spend over Y in the last year).
        *   **Dormant Customers:** Customers who have ordered in the past but haven't placed an order in a while (e.g., no orders in the last 6 months).
*   **Crafting a Campaign:**
    *   BakeMate provides a basic UI to craft email campaigns. While not a full-fledged email marketing platform, it allows you to:
        *   Choose a target segment (e.g., "Top Customers").
        *   Write a subject line for your email.
        *   Compose the email body using a simple rich text editor or by modifying a basic HTML template provided by BakeMate.
        *   The template allows for a title, a main message, and a call-to-action button with a link.
*   **Sending Campaigns via SendGrid:**
    *   Once your campaign is ready, BakeMate uses your connected SendGrid account to send the emails to all contacts in the selected segment.
    *   You'll see a summary of how many emails were sent.
*   **Use Cases:**
    *   Send a special offer to your top customers.
    *   Send a "We miss you!" email with a discount to dormant customers.
    *   Announce new products or seasonal specials to a segment of your customer base.
*   **Note:** This feature is for basic email marketing. For advanced automation, A/B testing, and detailed analytics, dedicated email marketing platforms are recommended. BakeMate's goal is to provide simple, effective hooks to get you started.

---

## 4. Account Management

Manage your BakeMate account settings and personal information.

### Profile Settings

*   Access your profile via the user icon or menu in the top-right corner.
*   Update your full name, email address (may require re-verification), and bakery name.
*   Configure notification preferences (e.g., for new orders, low stock alerts, weekly digests).

### Security

*   **Change Password:** Regularly update your password to keep your account secure. Choose a strong, unique password.
*   **Two-Factor Authentication (2FA) (Planned):** For enhanced security, BakeMate plans to offer 2FA. When enabled, you'll need both your password and a code from an authenticator app to log in.
*   **Active Sessions:** View and manage active login sessions (planned feature).

---

## 5. Troubleshooting & Support

If you encounter any issues or have questions while using BakeMate:

*   **Check this User Guide:** Many common questions are answered here.
*   **FAQ Section (Planned):** A dedicated FAQ section on our website will address common queries.
*   **Contextual Help:** Look for tooltips or help icons within the BakeMate application for feature-specific guidance.
*   **Contact Support:** If you can't find an answer, please reach out to our support team via the email address provided on the BakeMate website or within the app. Provide as much detail as possible about the issue you're experiencing, including steps to reproduce it and any error messages you see.

Thank you for choosing BakeMate! We're excited to help you streamline your baking business and achieve your goals. Happy baking!

