import { isTerminal } from "@/task-center/derivations";
import type { TaskState } from "@/task-center/types";

export interface ChatTaskBatchSummary {
  batchId: string;
  total: number;
  completed: number;
  failed: number;
  cancelled: number;
  episode: number;
  taskType: string;
}

function metadataString(task: TaskState, key: string): string {
  const value = task.metadata?.[key];
  return typeof value === "string" || typeof value === "number"
    ? String(value).trim()
    : "";
}

export function taskBatchId(task: TaskState): string {
  return metadataString(task, "batch_id");
}

export function taskBatchSize(task: TaskState): number {
  const value = Number(metadataString(task, "batch_size"));
  return Number.isInteger(value) && value > 1 && value <= 100 ? value : 0;
}

export function resolveChatTaskBatchSummary(
  tasks: Iterable<TaskState>,
  changedTask: TaskState,
): ChatTaskBatchSummary | null {
  const batchId = taskBatchId(changedTask);
  const total = taskBatchSize(changedTask);
  if (!batchId || !total || !isTerminal(changedTask)) return null;

  const batchTasks = [...tasks].filter((task) =>
    taskBatchId(task) === batchId &&
    (task.project_id ?? task.project) === (changedTask.project_id ?? changedTask.project)
  );
  if (batchTasks.length < total || batchTasks.some((task) => !isTerminal(task))) {
    return null;
  }

  const terminalTasks = batchTasks.slice(0, total);
  return {
    batchId,
    total,
    completed: terminalTasks.filter((task) => task.status === "completed").length,
    failed: terminalTasks.filter((task) => task.status === "failed").length,
    cancelled: terminalTasks.filter((task) => task.status === "cancelled").length,
    episode: changedTask.episode,
    taskType: changedTask.task_type,
  };
}

export function buildChatTaskBatchNotification(summary: ChatTaskBatchSummary): string {
  const episodeLabel = summary.episode > 0 ? `Episode ${summary.episode}` : "";
  const taskLabel = summary.taskType === "single_video"
    ? "video"
    : summary.taskType === "selected_regen"
      ? "first frame"
      : summary.taskType === "sketch_grid_generation"
        ? "sketch grid"
      : "task";
  if (summary.completed === summary.total) {
    const prefix = episodeLabel ? `${episodeLabel}: ` : "";
    const plural = summary.total === 1 ? taskLabel : `${taskLabel}s`;
    return `✅ ${prefix}All ${summary.total} ${plural} generated. You can ask me to review the results or continue to the next step.`;
  }

  const details = [
    `${summary.completed}/${summary.total} completed`,
    summary.failed > 0 ? `${summary.failed} failed` : "",
    summary.cancelled > 0 ? `${summary.cancelled} cancelled` : "",
  ].filter(Boolean).join(", ");
  const batchLabel = `${taskLabel} batch finished`;
  const heading = episodeLabel ? `${episodeLabel} ${batchLabel}` : `${batchLabel[0].toUpperCase()}${batchLabel.slice(1)}`;
  return `${heading}: ${details}. Check the task center for details before continuing.`;
}
