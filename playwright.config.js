import { defineConfig } from "@playwright/test";
import { fileURLToPath } from "node:url";

const localURL = "http://127.0.0.1:18002";
const target = process.env.SCANDOC_BASE_URL;

export default defineConfig({
  testDir: "./tests/browser",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: target || localURL,
    browserName: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: target ? undefined : {
    command: "python -B -m uvicorn backend.scandoc_page:app --host 127.0.0.1 --port 18002 --no-access-log",
    cwd: fileURLToPath(new URL(".", import.meta.url)),
    url: `${localURL}/scandoc`,
    reuseExistingServer: false,
    timeout: 30_000,
    gracefulShutdown: { signal: "SIGTERM", timeout: 5_000 },
    env: { PYTHONDONTWRITEBYTECODE: "1", OPENROUTER_API_KEY: "" },
  },
});
