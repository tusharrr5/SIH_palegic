export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch("/api" + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res
      .json()
      .catch(() => ({ detail: "The local service is unavailable." }));
    throw new Error(
      typeof err.detail === "string"
        ? err.detail
        : "Please check the supplied values.",
    );
  }
  return res.json();
}
export const date = (value: string | null, short = false) =>
  value
    ? new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        ...(!short ? { year: "numeric" as const } : {}),
        timeZone: "UTC",
      }).format(new Date(value))
    : "Awaiting observation";
export const utc = (value: string) =>
  new Date(value).toISOString().slice(11, 16) + " UTC";
export const statusLabel = (value: string) =>
  ({
    under_review: "Under review",
    needs_evidence: "Needs evidence",
    closed: "Closed",
  })[value] || value;
export const area = (value: number | null) =>
  value === null
    ? "—"
    : new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 }).format(
        value,
      );
