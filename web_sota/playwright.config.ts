import { defineConfig } from '@playwright/test';
export default defineConfig({
    testDir: './e2e', timeout: 60000, retries: 1,
    use: { baseURL: 'http://localhost:11029', headless: true, screenshot: 'only-on-failure' },
    webServer: {
        command: 'uv run python -m inkscape_mcp.server --port 11028',
        port: 11028, timeout: 30000, reuseExistingServer: false
    }
});
