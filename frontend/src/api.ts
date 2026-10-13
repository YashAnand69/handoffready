let token = "";
export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
  ) {
    super(message);
  }
}
export async function bootstrap() {
  const r = await fetch("/api/v1/bootstrap");
  const j = await r.json();
  if (!r.ok)
    throw new ApiError(
      j.error?.message || "Cannot open local service",
      j.error?.code || "startup",
    );
  token = j.data.token;
  return j.data;
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
  revision?: number,
): Promise<T> {
  const headers: Record<string, string> = { "X-Handoff-Token": token };
  if (revision !== undefined) headers["If-Match"] = String(revision);
  const multipart = body instanceof FormData;
  if (body && !multipart) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["Idempotency-Key"] = crypto.randomUUID();
  const r = await fetch("/api/v1" + path, {
    method,
    headers,
    body:
      body === undefined ? undefined : multipart ? body : JSON.stringify(body),
  });
  const j = await r.json();
  if (!r.ok)
    throw new ApiError(
      (j.error?.message || `Request failed (${r.status})`) +
        (j.error?.fields?.length
          ? " " +
            j.error.fields
              .map((f: string | { loc?: string[]; msg?: string }) =>
                typeof f === "string"
                  ? f.replace(/^body\./, "")
                  : `${f.loc?.filter((v) => v !== "body").join(".") || "Input"}: ${f.msg || "invalid"}`,
              )
              .join("; ")
          : ""),
      j.error?.code || "request",
    );
  return j.data;
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
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
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
