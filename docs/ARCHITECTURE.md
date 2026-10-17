# Hash1536 readiness contract

This is a separate, inert contract surface. It does not call the runtime,
supervisor, lifecycle, ignition, deployment, or any external service. Its
validator is exported additively from `CLOUDBURNER17.js`; existing runtime
behavior and the TAP/SURFACE public APIs are unchanged.

## Launch roles

The coordinated event called `hash1536` has exactly six launch roles:
`TAP`, `SURFACE`, `GAIN`, `HABITAT`, `ENGINE`, and `BUSINESS`. The name labels
the event; it does not name a hashing algorithm. A readiness record requires
each role exactly once. `logicalTick` is a nonnegative safe integer.

The geometry reference is the fixed point `[1024,1024,0]`. It is not a
measurement for any role, and role measurements are not required to equal one
another. A role measurement may remain explicitly `null`; finite supplied
values are checked only for finiteness, with no units, calibration, transform,
comparison, or tolerance implied.

The contract is marked `READINESS_ONLY`, its live gate is `CLOSED`, and
qualification remains `UNRESOLVED` and unauthorized. No launch receipt,
signature, or evidence is generated.

## Post-launch extensions

These two typed extensions are deliberately not launch roles:

- `RETROSPECTIVE_TEMPORAL`, linked to `Sentinel`.
- `FORWARD_DECONSTRUCTIVE`, bounded by `PRESENT`.

No temporal samples, forward projections, linkage computations, or execution
are implemented here.

## Existing names remain separate

The existing SCANDOC adapter's eight channel names are not assigned to these
six roles. No opposing pairs or mappings are inferred. In particular, the
typed contract does not redefine existing TAP or SURFACE identities.
