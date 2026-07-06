export type StepStatus = "pending" | "running" | "completed" | "failed";
export type TaskStatus = "planning" | "running" | "completed" | "failed";

export interface PlanStep {
  id: string;
  title: string;
  goal: string;
  agent: string;
  status: StepStatus;
  result?: string | null;
  error?: string | null;
}

export interface TaskState {
  id: string;
  input: string;
  status: TaskStatus;
  steps: PlanStep[];
  result?: string | null;
}

export interface RelayEvent {
  type: string;
  task_id: string;
  payload: Record<string, unknown>;
  created_at: string;
}

