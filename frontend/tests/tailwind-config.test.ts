import { describe, it, expect } from "vitest";
import config from "../tailwind.config.js";

describe("tailwind theme", () => {
  it("exposes custom color tokens", () => {
    expect(config.theme.extend.colors).toMatchObject({
      brand: { accent: "#2563EB", ink: "#0F172A" },
      "app-bg": "#F5F7FB",
      "app-sidebar": "#334155",
      primary: { hover: "#1D4ED8" },
      chart: { lineSecondary: "#60A5FA" },
      status: { completedFg: "#065F46" },
    });
  });
});

