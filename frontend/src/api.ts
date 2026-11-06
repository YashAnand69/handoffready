let token = "";
export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status?: number,
  ) {
    super(message);
  }
}
// Upload/packet inspection has a backend budget of 120 seconds. Leave room
// for that work while bounding a lost connection. A write timeout is ambiguous:
// delivery callers retain the same operation key/payload for reconciliation.
const REQUEST_TIMEOUT = 150_000;
async function request(
  path: string,
  options: RequestInit = {},
  signal?: AbortSignal,
) {
  const controller = new AbortController();
  let timedOut = false;
  const cancel = () => controller.abort();
  if (signal?.aborted) cancel();
  signal?.addEventListener("abort", cancel, { once: true });
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT);
  try {
    const response = await fetch("/api/v1" + path, {
      ...options,
      signal: controller.signal,
    });
    let value;
    try {
      value = await response.json();
    } catch {
      throw new ApiError(
        response.ok
          ? "The local service returned an unreadable result. Refresh before continuing."
          : `The local request failed (${response.status}). Check the local service and retry the same operation if its outcome is unknown.`,
        "invalid_response",
        response.status,
      );
    }
    if (!value || typeof value !== "object" || Array.isArray(value))
      throw new ApiError(
        "The local service returned an invalid result.",
        "invalid_response",
        response.status,
      );
    if (!response.ok) {
      const fields = Array.isArray(value.error?.fields)
        ? value.error.fields
        : [];
      const detail = fields
        .map((field: unknown) => {
          if (typeof field === "string") return field.replace(/^body\./, "");
          if (field && typeof field === "object") {
            const entry = field as { loc?: unknown; msg?: unknown };
            const location = Array.isArray(entry.loc)
              ? entry.loc
                  .filter((v) => typeof v === "string" && v !== "body")
                  .join(".")
              : "";
            return `${location || "Input"}: ${typeof entry.msg === "string" ? entry.msg : "invalid"}`;
          }
          return "Invalid input";
        })
        .join("; ");
      throw new ApiError(
        (typeof value.error?.message === "string"
          ? value.error.message
          : `Request failed (${response.status})`) +
          (detail ? " " + detail : ""),
        typeof value.error?.code === "string" ? value.error.code : "request",
        response.status,
      );
    }
    if (!("data" in value))
      throw new ApiError(
        "The local service returned an invalid result envelope.",
        "invalid_response",
        response.status,
      );
    return value.data;
  } catch (failure) {
    if (controller.signal.aborted)
      throw new ApiError(
        timedOut
          ? "The local request timed out. Its outcome may be unknown; reconcile the same operation before retrying."
          : "The local request was cancelled. Its outcome may be unknown.",
        timedOut ? "request_timeout" : "request_aborted",
      );
    if (failure instanceof ApiError) throw failure;
    throw new ApiError(
      "The local service could not be reached. Check its running status before retrying the same operation.",
      "request_unavailable",
    );
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", cancel);
  }
}
export async function bootstrap(signal?: AbortSignal) {
  const data = await request("/bootstrap", {}, signal);
  if (!data || typeof data.token !== "string" || !data.token)
    throw new ApiError(
      "The local service did not return a session token.",
      "invalid_response",
    );
  token = data.token;
  return data;
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  revision?: number,
  signal?: AbortSignal,
): Promise<T> {
  const headers: Record<string, string> = { "X-Handoff-Token": token };
  if (revision !== undefined) headers["If-Match"] = String(revision);
  const multipart = body instanceof FormData;
  if (body && !multipart) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["Idempotency-Key"] = crypto.randomUUID();
  return request(
    path,
    {
      method,
      headers,
      body:
        body === undefined
          ? undefined
          : multipart
            ? body
            : JSON.stringify(body),
    },
    signal,
  );
}
export async function download(path: string, name: string) {
  const r = await fetch("/api/v1" + path, {
    headers: { "X-Handoff-Token": token },
  });
  if (!r.ok) throw new Error("Could not download this export.");
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.hidden = true;
  document.body.appendChild(a);
  try {
    a.click();
  } finally {
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

export async function imageUrl(path: string) {
  const response = await fetch("/api/v1" + path, {
    headers: { "X-Handoff-Token": token },
  });
  if (!response.ok)
    throw new Error(
      "This file cannot be previewed. Refresh the packet and check its inspection status.",
    );
  if (
    !["image/png", "image/jpeg"].includes(
      response.headers.get("content-type")?.split(";")[0] || "",
    )
  )
    throw new Error("Unsupported image preview.");
  return URL.createObjectURL(await response.blob());
}
