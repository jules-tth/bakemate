import forms from "@tailwindcss/forms";
import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "Segoe UI",
          "Roboto",
          "Helvetica",
          "Arial",
        ],
      },
      colors: {
        // Brand and accents (desktop-first neutral + blue)
        brand: {
          surface: "#F5F7FB",
          accent: "#2563EB",
          ink: "#0F172A",
        },
        // Flattened app tokens to align with classes like bg-app-sidebar
        'app-bg': "#F5F7FB",
        'app-card': "#FFFFFF",
        'app-ring': "#E5E7EB",
        'app-text': "#0F172A",
        'app-muted': "#64748B",
        'app-sidebar': "#334155",
        'app-sidebarHover': "#475569",
        // Actions
        primary: {
          DEFAULT: "#2563EB",
          hover: "#1D4ED8",
          foreground: "#FFFFFF",
        },
        // Charts
        chart: {
          linePrimary: "#2563EB",
          lineSecondary: "#60A5FA",
          fillFrom: "#DBEAFE",
          fillTo: "#EFF6FF",
          grid: "#E5E7EB",
          bar1: "#2563EB",
          bar2: "#10B981",
          bar3: "#F59E0B",
        },
        // Badges
        status: {
          openBg: "#FEF3C7", openFg: "#92400E",
          quotedBg: "#E0E7FF", quotedFg: "#3730A3",
          completedBg: "#D1FAE5", completedFg: "#065F46",
          lateBg: "#FFE4E6", lateFg: "#9F1239",
        },
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(2,6,23,0.04), 0 8px 24px rgba(2,6,23,0.06)",
        lift: "0 8px 16px rgba(2,6,23,0.10)",
      },
      transitionDuration: {
        fast: "150ms",
        base: "200ms",
        slow: "300ms",
      },
    },
  },
  plugins: [forms, typography],
};
