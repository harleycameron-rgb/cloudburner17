export declare const LAUNCH_ROLES: readonly [
  "TAP",
  "SURFACE",
  "GAIN",
  "HABITAT",
  "ENGINE",
  "BUSINESS",
];

export type LaunchRole = (typeof LAUNCH_ROLES)[number];

export interface LaunchRoleEntry {
  role: LaunchRole;
  logicalTick: number;
  measurement: number | null;
}

export interface Hash1536ReadinessContract {
  kind: "COORDINATED_SIX_LEG_LAUNCH";
  eventName: "hash1536";
  phase: "READINESS_ONLY";
  liveGate: "CLOSED";
  geometryReference: readonly [1024, 1024, 0];
  roles: readonly [
    LaunchRoleEntry,
    LaunchRoleEntry,
    LaunchRoleEntry,
    LaunchRoleEntry,
    LaunchRoleEntry,
    LaunchRoleEntry,
  ];
  qualification: {
    status: "UNRESOLVED";
    authorized: false;
  };
}

export interface RetrospectiveTemporalExtension {
  kind: "POST_LAUNCH_EXTENSION";
  extension: "RETROSPECTIVE_TEMPORAL";
  linkedTo: "Sentinel";
}

export interface ForwardDeconstructiveExtension {
  kind: "POST_LAUNCH_EXTENSION";
  extension: "FORWARD_DECONSTRUCTIVE";
  boundedBy: "PRESENT";
}

export type PostLaunchExtension =
  | RetrospectiveTemporalExtension
  | ForwardDeconstructiveExtension;

export declare function validateHash1536Readiness(
  value: unknown,
): value is Hash1536ReadinessContract;
