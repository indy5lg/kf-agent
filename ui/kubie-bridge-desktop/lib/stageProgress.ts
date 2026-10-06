import type { Stage } from "./api";

const STAGE_CHECKPOINTS: Record<Stage, number> = {
  queued: 10,
  validating: 30,
  running: 70,
  finalizing: 90,
  succeeded: 100,
  failed: 100,
};

export function stageToCheckpoint(stage: Stage): number {
  return STAGE_CHECKPOINTS[stage];
}
