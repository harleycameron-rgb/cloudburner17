export function ingestTestResults(results) {
  if (!Array.isArray(results)) {
    throw new TypeError("Test results must be an array");
  }

  const timestamp = Date.now();
  const vector = [];
  let passed = 0;
  let failed = 0;

  for (const result of results) {
    if (
      result === null ||
      typeof result !== "object" ||
      typeof result.name !== "string" ||
      typeof result.ok !== "boolean"
    ) {
      throw new TypeError("Each test result must have a string name and boolean ok");
    }

    vector.push({ name: result.name, ok: result.ok, timestamp });
    if (result.ok) {
      passed += 1;
    } else {
      failed += 1;
    }
  }

  return { passed, failed, invariantPulse: failed === 0, vector };
}
