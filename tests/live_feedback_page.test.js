import test from "node:test";
import assert from "node:assert/strict";

const deferred = () => {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
};
const tick = () => new Promise(resolve => setImmediate(resolve));

async function page(t, options = {}) {
  const events = () => ({
    handlers: {},
    addEventListener(name, fn) { (this.handlers[name] ??= []).push(fn); },
    emit(name) { return Promise.all((this.handlers[name] ?? []).map(fn => fn())); },
  });
  const contexts = [];
  const context = () => {
    const value = {
      dirty: false, buffers: [], draws: 0,
      clearRect() { this.dirty = false; },
      drawImage() {
        if (options.drawError) throw new Error("frame failed");
        this.dirty = true; this.draws++;
      },
      getImageData() { return this.createImageData(); },
      createImageData() {
        const image = { data: new Uint8ClampedArray(320 * 180 * 4).fill(20) };
        this.buffers.push(image.data);
        return image;
      },
      putImageData() { this.dirty = true; },
    };
    contexts.push(value);
    return value;
  };
  const element = () => ({
    ...events(), disabled: false, value: 0, textContent: "", children: [],
    append(...children) { this.children.push(...children); },
    setAttribute(name, value) { this[name] = value; },
    getContext() { return this.context ??= context(); },
  });
  const ids = ["view", "camera", "start", "stop", "status", "level", "loads"];
  const elements = Object.fromEntries(ids.map(id => [id, element()]));
  const video = elements.camera;
  Object.assign(video, {
    readyState: 2, srcObject: null,
    pause() { this.paused = true; },
    play() { this.paused = false; return options.play?.() ?? Promise.resolve(); },
  });
  const document = {
    ...events(), hidden: false,
    getElementById: id => elements[id],
    createElement: element,
  };
  const audios = [], requests = [], frames = new Map();
  let nextFrame = 0;
  class AudioContext {
    constructor() {
      this.state = "suspended"; this.nodes = []; audios.push(this);
    }
    async resume() {
      await options.resume?.();
      if (this.state !== "closed") this.state = "running";
    }
    async close() { this.state = "closed"; }
    createMediaStreamSource() {
      const source = {
        disconnected: false,
        connect(target) { this.target = target; },
        disconnect() { this.disconnected = true; },
      };
      this.nodes.push(source);
      return source;
    }
    createAnalyser() {
      const analyser = {
        disconnected: false,
        getFloatTimeDomainData(samples) {
          this.samples = samples; samples.fill(0.5);
        },
        disconnect() { this.disconnected = true; },
      };
      this.nodes.push(analyser);
      return analyser;
    }
  }
  const window = { ...events(), isSecureContext: true, AudioContext };
  const navigator = { mediaDevices: {
    getUserMedia(constraints) {
      const request = { ...deferred(), constraints };
      requests.push(request);
      return request.promise;
    },
  } };
  const globals = {
    document, window, navigator,
    requestAnimationFrame(fn) { frames.set(++nextFrame, fn); return nextFrame; },
    cancelAnimationFrame(id) { frames.delete(id); },
  };
  for (const [key, value] of Object.entries(globals)) {
    const original = Object.getOwnPropertyDescriptor(globalThis, key);
    Object.defineProperty(globalThis, key, { configurable: true, value });
    t.after(() => {
      if (original) Object.defineProperty(globalThis, key, original);
      else delete globalThis[key];
    });
  }
  await import(`../backend/live_feedback/live.mjs?test=${encodeURIComponent(t.name)}`);
  const stream = (ended = false) => {
    const tracks = ["video", "audio"].map(kind => ({
      ...events(), kind, readyState: ended ? "ended" : "live", stops: 0,
      stop() { this.stops++; this.readyState = "ended"; },
    }));
    return { getTracks: () => tracks };
  };
  const start = () => elements.start.emit("click");
  const stop = () => elements.stop.emit("click");
  const live = async () => {
    const starting = start(); await tick();
    const acquired = stream();
    requests.at(-1).resolve(acquired);
    await starting;
    return acquired;
  };
  const cleared = () => {
    assert.equal(video.srcObject, null);
    assert.equal(video.paused, true);
    assert.equal(frames.size, 0);
    assert.equal(elements.level.value, 0);
    assert.ok(contexts.every(ctx => !ctx.dirty));
    assert.equal(elements.start.disabled, false);
    assert.equal(elements.stop.disabled, true);
    assert.ok(audios.every(audio => audio.state === "closed"));
  };
  return { elements, document, window, navigator, contexts, audios, requests,
    frames, stream, start, stop, live, cleared };
}

test("live feedback is idle until explicit Start and exposes six manual inputs", async t => {
  const p = await page(t);
  assert.equal(p.requests.length, 0);
  assert.equal(p.audios.length, 0);
  assert.deepEqual(p.elements.loads.children.map(label => label.children[0].textContent),
    ["TAP", "SURFACE", "GAIN", "HABITAT", "ENGINE", "BUSINESS"]);
  for (const label of p.elements.loads.children)
    assert.match(label.children[1]["aria-label"], /manual research input/);
});

test("live frames and RMS drive visuals without connecting a speaker; Stop clears all", async t => {
  const p = await page(t);
  const stream = await p.live();
  assert.equal(p.elements.camera.srcObject, stream);
  assert.equal(p.elements.level.value, 0.5);
  assert.equal(p.frames.size, 1);
  assert.ok(p.contexts.every(ctx => ctx.dirty));
  assert.ok(p.contexts.flatMap(ctx => ctx.buffers).every(buffer => buffer.every(v => v === 0)));
  const [source, analyser] = p.audios[0].nodes;
  assert.equal(source.target, analyser);
  assert.equal(analyser.target, undefined);
  assert.equal(p.requests[0].constraints.audio.autoGainControl, false);
  await p.stop();
  assert.ok(stream.getTracks().every(track => track.stops === 1));
  assert.ok(p.audios[0].nodes.every(node => node.disconnected));
  assert.ok(analyser.samples.every(value => value === 0));
  p.cleared();
});

test("repeated Start/Stop releases each session and leaves no animation", async t => {
  const p = await page(t);
  for (let i = 0; i < 3; i++) {
    const stream = await p.live();
    await p.stop(); await p.stop();
    assert.ok(stream.getTracks().every(track => track.stops === 1));
    p.cleared();
  }
});

test("repeated Start while permissions are pending requests devices only once", async t => {
  const p = await page(t);
  const starting = p.start(); await tick(); await p.start();
  assert.equal(p.requests.length, 1);
  assert.equal(p.audios.length, 1);
  await p.stop();
  const late = p.stream(); p.requests[0].resolve(late); await starting;
  assert.ok(late.getTracks().every(track => track.stops === 1));
  p.cleared();
});

for (const event of ["stop", "hidden", "pagehide"]) {
  test(`${event} cancels pending permission and releases a late grant`, async t => {
    const p = await page(t);
    const starting = p.start(); await tick();
    if (event === "stop") await p.stop();
    if (event === "hidden") { p.document.hidden = true; await p.document.emit("visibilitychange"); }
    if (event === "pagehide") await p.window.emit("pagehide");
    const late = p.stream(); p.requests[0].resolve(late); await starting;
    assert.ok(late.getTracks().every(track => track.stops === 1));
    p.cleared();
  });
}

for (const result of ["resolve", "reject"]) {
  test(`stale permission ${result} cannot stop a newer live session`, async t => {
    const p = await page(t);
    const oldStart = p.start(); await tick(); await p.stop();
    const current = await p.live();
    const stale = p.stream();
    p.requests[0][result](result === "resolve" ? stale : new Error("old denial"));
    await oldStart;
    assert.equal(p.elements.camera.srcObject, current);
    assert.equal(p.audios[1].state, "running");
    assert.ok(current.getTracks().every(track => track.stops === 0));
    if (result === "resolve") assert.ok(stale.getTracks().every(track => track.stops === 1));
    await p.stop(); p.cleared();
  });
}

test("Stop during AudioContext resume never requests devices", async t => {
  const resume = deferred();
  const p = await page(t, { resume: () => resume.promise });
  const starting = p.start(); await p.stop();
  resume.resolve(); await starting;
  assert.equal(p.requests.length, 0);
  p.cleared();
});

test("stale video playback completion cannot attach audio to a newer session", async t => {
  const playback = deferred();
  let plays = 0;
  const p = await page(t, { play: () => ++plays === 1 ? playback.promise : Promise.resolve() });
  const oldStart = p.start(); await tick();
  const old = p.stream(); p.requests[0].resolve(old); await tick();
  await p.stop();
  const current = await p.live();
  playback.resolve(); await oldStart;
  assert.equal(p.elements.camera.srcObject, current);
  assert.equal(p.audios[0].nodes.length, 0);
  assert.equal(p.audios[1].nodes.length, 2);
  assert.ok(old.getTracks().every(track => track.stops === 1));
  await p.stop(); p.cleared();
});

for (const phase of ["playback pending", "live", "already ended"]) {
  test(`device disconnect releases resources when ${phase}`, async t => {
    const playback = deferred();
    const p = await page(t, { play: () => phase === "playback pending" ? playback.promise : Promise.resolve() });
    const starting = p.start(); await tick();
    const stream = p.stream(phase === "already ended");
    p.requests[0].resolve(stream); await tick();
    if (phase !== "already ended") await stream.getTracks()[0].emit("ended");
    playback.resolve(); await starting;
    assert.ok(stream.getTracks().every(track => track.stops >= 1));
    p.cleared();
  });
}

for (const event of ["pagehide", "visibilitychange"]) {
  test(`${event} clears an active session`, async t => {
    const p = await page(t); const stream = await p.live();
    if (event === "pagehide") await p.window.emit(event);
    else { p.document.hidden = true; await p.document.emit(event); }
    assert.ok(stream.getTracks().every(track => track.stops === 1));
    p.cleared();
  });
}

for (const failure of ["permission", "resume", "playback", "draw"]) {
  test(`${failure} errors close resources and clear frames`, async t => {
    const reject = () => Promise.reject(new Error("test failure"));
    const p = await page(t, {
      resume: failure === "resume" ? reject : undefined,
      play: failure === "playback" ? reject : undefined,
      drawError: failure === "draw",
    });
    const starting = p.start(); await tick();
    let stream;
    if (failure === "permission") p.requests[0].reject(new DOMException("Denied", "NotAllowedError"));
    else if (failure !== "resume") { stream = p.stream(); p.requests[0].resolve(stream); }
    await starting;
    if (stream) assert.ok(stream.getTracks().every(track => track.stops >= 1));
    p.cleared();
  });
}

test("hidden pages and unsupported environments never request devices", async t => {
  const p = await page(t);
  p.document.hidden = true; await p.start();
  p.document.hidden = false; p.window.isSecureContext = false; await p.start();
  p.window.isSecureContext = true; p.window.AudioContext = undefined; await p.start();
  assert.equal(p.requests.length, 0);
  assert.equal(p.audios.length, 0);
});
