import test from "node:test";
import assert from "node:assert/strict";

test("page pending controls, exact example, textual fallback and stale failure recovery", async () => {
  const ids = ["demo", "json", "csv", "context", "proposal", "example", "view", "result",
    "status", "summary", "geometry-data", "output"];
  const elements = Object.fromEntries(ids.map(id => [id, {
    disabled: id !== "demo", textContent: "", value: "", attributes: {},
    addEventListener(event, handler) { this[event] = handler; },
    setAttribute(name, value) { this.attributes[name] = value; },
    getContext() { return null; },
  }]));
  const original = globalThis.document;
  globalThis.document = { getElementById: id => elements[id] };
  try {
    await import("../backend/scandoc/app.js");
    const run = elements.demo.click();
    assert.equal(elements.demo.disabled, true);
    assert.equal(elements.proposal.disabled, true);
    assert.equal(elements.status.attributes["aria-busy"], "true");
    await run;
    assert.equal(elements.demo.disabled, false);
    assert.equal(elements.proposal.disabled, false);
    assert.match(elements.summary.textContent, /Cube SHA-512/);
    assert.match(elements.summary.textContent, /geometric radius: 0.8/);
    assert.match(elements.summary.textContent, /Center distance from declared radius origin/);
    assert.match(elements["geometry-data"].textContent, /"faces":/);
    assert.equal(elements.result.value, "");
    elements.example.click();
    assert.match(elements.status.textContent, /NOT submitted/);
    const example = JSON.parse(elements.result.value);
    assert.equal(example.proposals[0].sphere.radius, 0.75);
    assert.equal(example.proposals[0].time, 5);
    const validation = elements.proposal.click();
    assert.equal(elements.demo.disabled, true);
    assert.equal(elements.context.disabled, true);
    await validation;
    assert.equal(elements.demo.disabled, false);
    assert.match(elements.output.textContent, /"stream": "forecast"/);
    elements.result.value = JSON.stringify({ ...example, identity: "extra" });
    await elements.proposal.click();
    for (const id of ["json", "csv", "context", "proposal", "example"])
      assert.equal(elements[id].disabled, true);
    assert.match(elements.status.textContent, /INVALID_INPUT.*STALE/);
    assert.match(elements.summary.textContent, /STALE/);
    assert.match(elements.output.textContent, /^STALE/);
    assert.equal(elements.result.value, "");
    await elements.demo.click();
    assert.equal(elements.json.disabled, false);
    assert.doesNotMatch(elements.summary.textContent, /STALE/);
  } finally {
    globalThis.document = original;
  }
});
