# Cloudburner live camera and sound prototype

New standalone browser prototype, replacing the pending static-image import.
No JPEG is referenced or included. The user's original uploaded image is not deleted.

Run from this folder: `python -m http.server 8000`, then open localhost:8000.
Use Start camera + microphone and grant device permissions. Microphone RMS drives
synthetic camera-frame deformation with six manually controlled load inputs.
There is no speaker playback, recording, upload, AI inference, engine firing,
receipt minting, or authenticated app telemetry integration.
Stop, a hidden tab, page exit or a disconnected device releases the devices.
Run model tests: `node --test model.test.mjs`.

MANUAL ACCEPTANCE TESTS (not automated): HTTPS/localhost, grant both permissions,
deny permission, stop during the permission prompt, unplug a device, hide the tab,
restart after stopping, and confirm browser device indicators turn off.
Browser/device behaviour and audio processing must be verified on target devices.

Still missing: original Orrery/Python reference import, actual six-app adapters,
cycle coordinator, cube/sphere lifecycle hooks, fourth-axis event, approved firing
and separation-position sentinel latch. This page does NOT implement those.
Never use synthetic output as verified invariant evidence.
