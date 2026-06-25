import { test } from "@playwright/test";
import path from "path";

const VIDEO_DIR = path.resolve(__dirname, "../../docs/screenshots");

test.describe("Video demo walkthrough", () => {
  test("full walkthrough", async ({ page, context }) => {
    // Record video
    await context.tracing.start({ screenshots: true, snapshots: true });

    // 1. Dashboard
    await page.goto("/");
    await page.waitForSelector('[data-testid="hero"]');
    await page.waitForTimeout(2000);

    // 2. Animation studio — try presets
    await page.goto("/animation");
    await page.waitForSelector("text=Animation Studio");
    await page.waitForTimeout(1000);

    // Click "Rotate" preset
    const rotateBtn = page.locator("button", { hasText: "Rotate" });
    if (await rotateBtn.isVisible()) await rotateBtn.click();
    await page.waitForTimeout(1500);

    // Change color
    const colorInput = page.locator('input[type="color"]');
    if (await colorInput.isVisible()) {
      await colorInput.fill("#ff00ff");
      await page.waitForTimeout(500);
    }

    // Increase duration
    const durInput = page.locator('input[type="number"]').first();
    if (await durInput.isVisible()) {
      await durInput.fill("4");
      await page.waitForTimeout(500);
    }

    await page.waitForTimeout(1000);

    // 3. Layer Manager
    await page.goto("/layers");
    await page.waitForSelector("text=Layer Manager");
    await page.waitForTimeout(1000);

    // 4. Status page
    await page.goto("/status");
    await page.waitForSelector("text=Server status");
    await page.waitForTimeout(1000);

    await context.tracing.stop({ path: path.join(VIDEO_DIR, "demo-trace.zip") });
  });
});
