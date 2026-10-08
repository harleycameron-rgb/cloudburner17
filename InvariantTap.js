function hashEventName(eventName) {
  let hash = 0x811c9dc5;

  for (let index = 0; index < eventName.length; index += 1) {
    hash ^= eventName.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }

  return (hash >>> 0).toString(16).padStart(8, "0");
}

export function invariantTap(eventName) {
  if (typeof eventName !== "string") {
    throw new TypeError("Tap event name must be a string");
  }

  return {
    name: eventName,
    ok: true,
    wobble: 0,
    hash: hashEventName(eventName),
    timestamp: Date.now(),
  };
}

export function tapStream(events) {
  if (!Array.isArray(events)) {
    throw new TypeError("Tap events must be an array");
  }

  return events.map(invariantTap);
}

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
    invariantPulse: vector.length > 0 && vector.every((event) => event.ok),
  };
}
