import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";
import {
  admitModule,
  burnModule,
  participateInConvergence,
  retireModule,
  revokeToOrigin,
  trajectoryStream,
} from "../CLOUDBURNER17.js";

const sha512 = (value) =>
  createHash("sha512").update(value).digest("hex");

test("module lifecycle preserves trajectory and commits a burn event", () => {
  const receiptCommitment = sha512("admitted module");
  const module = admitModule(receiptCommitment, 2);
  const vector = [{ invariant: true, measure: 1 }];

  assert.equal(participateInConvergence(module, vector), "ok");
  vector[0].measure = 9;
  assert.equal(trajectoryStream(module)[0].vector[0].measure, 1);

  assert.throws(
    () => retireModule(module, [sha512("missing dependency")]),
    /dependency ancestry incomplete/,
  );
  assert.equal(module.state, "admitted");

  retireModule(module, [receiptCommitment]);
  assert.equal(module.executionRevoked, true);
  const { burnEvent, newChainHead } = burnModule(module, "genesis");

  assert.deepEqual(
    {
      receiptCommitment: burnEvent.receiptCommitment,
      previousEvent: burnEvent.previousEvent,
      originCommitment: burnEvent.originCommitment,
      transition: burnEvent.transition,
      gateway: burnEvent.gateway,
      layer: burnEvent.layer,
    },
    {
      receiptCommitment,
      previousEvent: "genesis",
      originCommitment: sha512(`${receiptCommitment}::origin`),
      transition: "available→burned-origin",
      gateway: "traversed",
      layer: 2,
    },
  );
  assert.equal(newChainHead, sha512(JSON.stringify(burnEvent)));
  assert.equal(module.state, "burned");
  assert.equal(module.chainHead, newChainHead);
  assert.equal(revokeToOrigin(module).origin, module.origin);
  assert.throws(() => burnModule(module, newChainHead), /prior retirement/);
});

test("lifecycle rejects invalid transitions and malformed inputs", () => {
  assert.throws(() => admitModule("", 0), TypeError);
  assert.throws(() => admitModule("receipt", -1), TypeError);

  const module = admitModule("receipt", 0);
  assert.throws(() => participateInConvergence(module, [{}]), TypeError);
  assert.equal(
    participateInConvergence(module, [{ invariant: false }]),
    "fail",
  );
  assert.throws(() => burnModule(module, "genesis"), /prior retirement/);
  assert.throws(() => revokeToOrigin(module), /burned module/);
});
