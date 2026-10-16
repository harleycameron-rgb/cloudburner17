import { test as base, expect } from "@playwright/test";

export const controls = ["json", "csv", "context", "proposal", "example"];

export const test = base.extend({
  page: async ({ page, baseURL }, use) => {
    const errors = [];
    const unexpectedRequests = [];
    const origin = new URL(baseURL).origin;
    const assets = new Set(["/", "/scandoc", "/scandoc/", "/scandoc/app.js",
      "/scandoc/model.js", "/scandoc/style.css"]);
    await page.route("**/*", route => {
      const request = route.request();
      const url = new URL(request.url());
      if (url.origin === origin && assets.has(url.pathname) && request.method() === "GET")
        return route.continue();
      unexpectedRequests.push(`${request.method()} ${url.href}`);
      return route.abort();
    });
    page.on("pageerror", error => errors.push(error.message));
    page.on("console", message => {
      if (message.type() === "error") errors.push(message.text());
    });
    await use(page);
    expect(errors, "No uncaught page errors or console errors").toEqual([]);
    expect(unexpectedRequests, "Only same-origin read-only sandbox assets").toEqual([]);
  },
});

export { expect };

export async function runDemo(page) {
  await page.locator("#demo").click();
  await expect(page.locator("#status")).toHaveText(
    "Synthetic demo complete. Measured evidence, origin hash and burn receipt: unresolved. Transmission disabled.");
  await expect(page.locator("#status")).toHaveAttribute("aria-busy", "false");
  for (const id of controls) await expect(page.locator(`#${id}`)).toBeEnabled();
  return JSON.parse(await page.locator("#output").textContent());
}

export async function canvasHasPixels(page) {
  return page.locator("#view").evaluate(canvas => {
    const pixels = canvas.getContext("2d").getImageData(0, 0, canvas.width, canvas.height).data;
    return pixels.some((value, index) => index % 4 === 3 && value > 0);
  });
}
