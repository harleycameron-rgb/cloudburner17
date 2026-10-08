# Burn / Burncycle Lineage

## Lineage declaration

This project treats **burncycle** as the origin burn topology and Cloudburner17
as the stabiliser layer for downstream burn events. Burncycle's structural
qualities, lifecycle semantics, and residue benchmarks are upstream properties;
Cloudburner17 does not redefine them. Cloudburner17's role is to apply its own
admission, retirement, and burn checks to downstream events.

This is an architectural lineage declaration, not a Git merge or a vendored
burncycle implementation. The burncycle source and its canonical identifiers
are not present in this repository.

## Stabiliser boundary

Consumers should submit burn operations through the public
[`CLOUDBURNER17.js`](../CLOUDBURNER17.js) entry point rather than importing
implementation modules directly. Its `burnModule` export accepts lifecycle
modules or commitment IDs. Lifecycle modules must be retired before burning;
ID-based burns are handled by `src/burn_logic.js` after dependency resolution,
execution stop, and capability revocation.

The public API also exposes synthetic-state hashing and timestamp-proof
verification. These are Cloudburner17 stabilisation functions; they do not
modify burncycle's upstream topology or establish external timestamp
attestation.

## Constellation routing contract

Constellation integrations are expected to route downstream burn requests
through Cloudburner17's public API. This repository can define that integration
boundary, but cannot enforce routing in constellation repositories that are not
part of this checkout.

Current burn events contain an `originCommitment`, but do not identify
burncycle or carry a burncycle provenance proof. Linking an event
cryptographically to a particular burncycle origin will require its canonical
identifier and an agreed event/proof format.
