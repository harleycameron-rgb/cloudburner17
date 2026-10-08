export function runInvariantTapSession(events) {
  if (!Array.isArray(events)) {
    throw new TypeError("Tap events must be an array");
  }

  const timestamp = Date.now();
  const vector = events.map((event) => {
    if (typeof event === "string") {
      return { name: event, ok: true, timestamp };
    }

    if (
      event === null ||
      typeof event !== "object" ||
      typeof event.name !== "string" ||
      typeof event.ok !== "boolean"
    ) {
      throw new TypeError(
        "Each tap event must be a string or have a string name and boolean ok",
      );
    }

    return { name: event.name, ok: event.ok, timestamp };
  });

  return {
    vector,
    invariantPulse: vector.every((event) => event.ok),
  };
}
