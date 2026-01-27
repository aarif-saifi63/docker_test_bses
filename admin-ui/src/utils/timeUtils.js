export function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString("en-US", {
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}
