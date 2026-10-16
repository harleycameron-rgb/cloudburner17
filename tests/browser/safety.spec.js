import { test, expect, controls } from "./fixtures.js";

test("root redirect, sandbox asset content types and read-only routes", async ({ request }) => {
  const root = await request.get("/", { maxRedirects: 0 });
  expect(root.status()).toBe(307);
  expect(root.headers().location).toBe("/scandoc");
  for (const path of ["/scandoc", "/scandoc/"]) {
    const response = await request.get(path);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"]).toMatch(/^text\/html\b/);
    expect(response.headers()["content-security-policy"]).toContain("connect-src 'none'");
  }
  for (const [asset, type] of [
    ["app.js", "text/javascript"], ["model.js", "text/javascript"], ["style.css", "text/css"],
  ]) {
    const response = await request.get(`/scandoc/${asset}`);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-type"].split(";")[0]).toBe(type);
    expect(response.headers()["x-content-type-options"]).toBe("nosniff");
    expect((await response.body()).length).toBeGreaterThan(0);
  }
  const response = await request.get("/openapi.json");
  expect(response.status()).toBe(200);
  const { paths } = await response.json();
  expect(Object.keys(paths).sort()).toEqual(["/scandoc", "/scandoc/", "/scandoc/{asset}"]);
  for (const methods of Object.values(paths)) expect(Object.keys(methods)).toEqual(["get"]);
});

test("initial controls are disabled and supervisor notice is not interactive", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/scandoc$/);
  await expect(page.locator("#demo")).toBeEnabled();
  for (const id of controls) await expect(page.locator(`#${id}`)).toBeDisabled();
  await expect(page.locator("#summary")).toHaveText("Not run. No current commitments.");
  await expect(page.locator("#geometry-data")).toHaveText("Not run.");
  await expect(page.locator("#result")).toHaveValue("");
  await expect(page.locator(".warning")).toContainText("SYNTHETIC DEMONSTRATION ONLY");
  await expect(page.locator(".warning")).toContainText("transmission disabled");
  const notice = page.locator(".supervisor-status");
  await expect(notice).toHaveText(
    "Supervisor unavailable in this standalone preview. This deployment provides the SCANDOC synthetic sandbox only.");
  expect(await notice.evaluate(element => ({
    tag: element.tagName,
    interactive: Boolean(element.closest("a, button, [role=button], [role=link], [onclick], [tabindex]")),
    descendants: element.querySelectorAll("a, button, input, [role=button], [role=link], [onclick], [tabindex]").length,
  }))).toEqual({ tag: "P", interactive: false, descendants: 0 });
  await expect(page.getByRole("link", { name: /supervisor/i })).toHaveCount(0);
  await notice.click();
  await expect(page).toHaveURL(/\/scandoc$/);
  await expect(page.locator("#summary")).toHaveText("Not run. No current commitments.");
});
