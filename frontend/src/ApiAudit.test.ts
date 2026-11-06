import { afterEach, expect, it, vi } from "vitest";
import { api, bootstrap, download, ApiError } from "./api";
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

it.each([502, 200])(
  "returns a structured safe error for an HTML response (%s)",
  async (status) => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response("<html>PRIVATE proxy details</html>", { status }),
        ),
    );
    const error = (await api("/projects").catch((error) => error)) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("invalid_response");
    expect(error.status).toBe(status);
    expect(error.message).not.toContain("PRIVATE");
  },
);
it.each(["", "null", "[]", "{}"])(
  "refuses a malformed success envelope (%s)",
  async (body) => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(body, { status: 200 })),
    );
    await expect(api("/projects")).rejects.toMatchObject({
      code: "invalid_response",
    });
  },
);
it("refuses bootstrap without a valid session token", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(JSON.stringify({ data: {} }))),
  );
  await expect(bootstrap()).rejects.toMatchObject({ code: "invalid_response" });
});
it("preserves structured field refusals and HTTP status", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "invalid_fields",
            message: "Check input.",
            fields: [{ loc: ["body", "label"], msg: "Required" }],
          },
        }),
        { status: 422 },
      ),
    ),
  );
  await expect(api("/projects")).rejects.toMatchObject({
    code: "invalid_fields",
    status: 422,
    message: "Check input. label: Required",
  });
});
it("passes cancellation to fetch without treating a cancelled write as a definite refusal", async () => {
  const controller = new AbortController();
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (_path, init) =>
        new Promise((_resolve, reject) =>
          init.signal.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          ),
        ),
    ),
  );
  const request = api(
    "/projects/p/questions/q/resolve",
    "POST",
    { operation_key: "stable", reason: "synthetic" },
    undefined,
    controller.signal,
  );
  controller.abort();
  await expect(request).rejects.toMatchObject({ code: "request_aborted" });
});
it("bounds a hung connection and reports an ambiguous write outcome", async () => {
  vi.useFakeTimers();
  const fetch = vi.fn(
    (_path, init) =>
      new Promise((_resolve, reject) =>
        init.signal.addEventListener("abort", () =>
          reject(new DOMException("Aborted", "AbortError")),
        ),
      ),
  );
  vi.stubGlobal("fetch", fetch);
  const result = api("/projects/p/questions/q/resolve", "POST", {
    operation_key: "stable",
  }).catch((error) => error);
  await vi.advanceTimersByTimeAsync(150_000);
  expect(await result).toMatchObject({ code: "request_timeout" });
  expect(((await result) as ApiError).message).toContain(
    "reconcile the same operation",
  );
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(JSON.parse(fetch.mock.calls[0][1].body).operation_key).toBe("stable");
});
it("attaches the download control for its click and cleans up its object URL", async () => {
  vi.useFakeTimers();
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response("synthetic record")),
  );
  URL.createObjectURL = vi.fn().mockReturnValue("blob:synthetic");
  URL.revokeObjectURL = vi.fn();
  const click = vi
    .spyOn(HTMLAnchorElement.prototype, "click")
    .mockImplementation(function (this: HTMLAnchorElement) {
      expect(this.isConnected).toBe(true);
      expect(this.download).toBe("record.md");
    });
  await download("/projects/p/exports/e/md", "record.md");
  expect(click).toHaveBeenCalledOnce();
  expect(document.querySelector('a[download="record.md"]')).toBeNull();
  await vi.advanceTimersByTimeAsync(1000);
  expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:synthetic");
});
