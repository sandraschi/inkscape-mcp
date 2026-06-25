import { test } from "@playwright/test";
import path from "path";

const SCREENSHOTS_DIR = path.resolve(__dirname, "../../docs/screenshots");

test.describe("Screenshot capture", () => {
  test("Dashboard", async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector('[data-testid="dashboard"]');
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/dashboard.png`, fullPage: true });
  });

  test("Animation Studio", async ({ page }) => {
    await page.goto("/animation");
    await page.waitForSelector("text=Animation Studio");
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/animation-studio.png`, fullPage: true });
  });

  test("Layer Manager", async ({ page }) => {
    await page.goto("/layers");
    await page.waitForSelector("text=Layer Manager");
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/layer-manager.png`, fullPage: true });
  });

  test("Status", async ({ page }) => {
    await page.goto("/status");
    await page.waitForSelector("text=Server status");
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/status.png`, fullPage: true });
  });

  test("Agent Tools", async ({ page }) => {
    await page.goto("/agent-tools");
    await page.waitForSelector("text=Agent Lab");
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/agent-tools.png`, fullPage: true });
  });

  test("Settings", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForSelector("text=Settings");
    await page.screenshot({ path: `${SCREENSHOTS_DIR}/settings.png`, fullPage: true });
  });
});
