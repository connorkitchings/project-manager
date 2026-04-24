export function formatTimestamp(value: string | null | undefined) {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function shortTypeLabel(type: "commit" | "pull_request" | "issue") {
  if (type === "pull_request") {
    return "PR";
  }
  if (type === "issue") {
    return "Issue";
  }
  return "Commit";
}
