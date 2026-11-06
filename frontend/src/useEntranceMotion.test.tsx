import { afterEach, beforeEach, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { useEntranceMotion } from "./useEntranceMotion";

type Observer = {
  callback: IntersectionObserverCallback;
  observe: ReturnType<typeof vi.fn>;
  unobserve: ReturnType<typeof vi.fn>;
  disconnect: ReturnType<typeof vi.fn>;
};
let observers: Observer[];
let preference: {
  matches: boolean;
  addEventListener: ReturnType<typeof vi.fn>;
  removeEventListener: ReturnType<typeof vi.fn>;
};
let animate: ReturnType<typeof vi.fn>;
let cancel: ReturnType<typeof vi.fn>;
const priorAnimate = Object.getOwnPropertyDescriptor(
  Element.prototype,
  "animate",
);
function Demo({ extra = false }: { extra?: boolean }) {
  useEntranceMotion("synthetic");
  return (
    <main id="workspace">
      <section className="dashboard-start">
        <h2>Readable panel</h2>
        <button>Start task</button>
      </section>
      {extra && (
        <section className="delivery-context">
          <button>Review context</button>
        </section>
      )}
      <p className="status">Saved status</p>
    </main>
  );
}
function enter(element: Element, index = 0) {
  act(() =>
    observers[index].callback(
      [{ target: element, isIntersecting: true } as IntersectionObserverEntry],
      {} as IntersectionObserver,
    ),
  );
}
beforeEach(() => {
  observers = [];
  preference = {
    matches: true,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  };
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => preference),
  );
  vi.stubGlobal(
    "IntersectionObserver",
    vi.fn().mockImplementation(function (
      callback: IntersectionObserverCallback,
    ) {
      const observer = {
        callback,
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      };
      observers.push(observer);
      return observer;
    }),
  );
  cancel = vi.fn();
  animate = vi.fn(() => ({ cancel, onfinish: null, oncancel: null }));
  Object.defineProperty(Element.prototype, "animate", {
    configurable: true,
    value: animate,
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  if (priorAnimate)
    Object.defineProperty(Element.prototype, "animate", priorAnimate);
  else delete (Element.prototype as { animate?: unknown }).animate;
});
it("leaves readable, interactive content untouched until a nonblocking reveal", () => {
  render(<Demo />);
  const panel = screen.getByText("Readable panel").parentElement!;
  expect(panel.style.opacity).toBe("");
  expect(
    (screen.getByRole("button", { name: "Start task" }) as HTMLButtonElement)
      .disabled,
  ).toBe(false);
  expect(animate).not.toHaveBeenCalled();
  enter(panel);
  expect(animate).toHaveBeenCalledOnce();
  enter(panel);
  expect(animate).toHaveBeenCalledOnce();
  expect(animate.mock.calls[0][1]).toEqual({
    duration: 320,
    easing: "cubic-bezier(.22,1,.36,1)",
  });
  expect(panel.style.transform).toBe("");
  expect(observers[0].unobserve).toHaveBeenCalledWith(panel);
  expect(observers[0].observe).not.toHaveBeenCalledWith(
    screen.getByText("Saved status"),
  );
});
it("does not initialize decorative observers for reduced or unknown motion preferences", () => {
  preference.matches = false;
  render(<Demo />);
  expect(observers).toHaveLength(0);
  expect(screen.getByRole("button", { name: "Start task" })).toBeTruthy();
  expect(animate).not.toHaveBeenCalled();
});
it("leaves content visible when observation or animation APIs are missing", () => {
  vi.stubGlobal("IntersectionObserver", undefined);
  const view = render(<Demo />);
  expect(screen.getByText("Readable panel").parentElement?.style.opacity).toBe(
    "",
  );
  expect(animate).not.toHaveBeenCalled();
  view.unmount();
  vi.stubGlobal("IntersectionObserver", vi.fn());
  Object.defineProperty(Element.prototype, "animate", {
    configurable: true,
    value: undefined,
  });
  render(<Demo />);
  expect(screen.getByRole("button", { name: "Start task" })).toBeTruthy();
});
it("observes newly mounted workflow panels without watching scroll or rerendering the app", async () => {
  const view = render(<Demo />);
  view.rerender(<Demo extra />);
  const extra = screen.getByRole("button", {
    name: "Review context",
  }).parentElement!;
  await waitFor(() => expect(observers[0].observe).toHaveBeenCalledWith(extra));
  enter(extra);
  expect(animate).toHaveBeenCalledOnce();
});
it("skips focused panels and cancels a running reveal as soon as keyboard focus enters", () => {
  const view = render(<Demo />);
  const button = screen.getByRole("button", { name: "Start task" });
  button.focus();
  enter(button.parentElement!);
  expect(animate).not.toHaveBeenCalled();
  view.unmount();
  render(<Demo />);
  const next = screen.getByRole("button", { name: "Start task" });
  enter(next.parentElement!, 1);
  expect(animate).toHaveBeenCalledOnce();
  next.focus();
  expect(cancel).toHaveBeenCalledOnce();
  expect(document.activeElement).toBe(next);
});
it("cancels decoration on pointer interaction and on a live reduced-motion change", () => {
  render(<Demo extra />);
  const first = screen.getByRole("button", { name: "Start task" });
  enter(first.parentElement!);
  fireEvent.pointerDown(first);
  expect(cancel).toHaveBeenCalledOnce();
  enter(screen.getByRole("button", { name: "Review context" }).parentElement!);
  preference.matches = false;
  act(() => preference.addEventListener.mock.calls[0][1]());
  expect(cancel).toHaveBeenCalledTimes(2);
  expect(observers[0].disconnect).toHaveBeenCalledOnce();
  expect(screen.getByText("Readable panel").parentElement?.style.opacity).toBe(
    "",
  );
});
it("cleans up pending observers and animations on navigation/unmount", () => {
  const view = render(<Demo />);
  enter(screen.getByRole("button", { name: "Start task" }).parentElement!);
  view.unmount();
  expect(cancel).toHaveBeenCalledOnce();
  expect(observers[0].disconnect).toHaveBeenCalledOnce();
  expect(preference.removeEventListener).toHaveBeenCalledWith(
    "change",
    expect.any(Function),
  );
});
it("keeps workflow content readable if the browser rejects animation", () => {
  animate.mockImplementation(() => {
    throw new Error("Animation unavailable");
  });
  render(<Demo />);
  enter(screen.getByRole("button", { name: "Start task" }).parentElement!);
  expect(screen.getByText("Readable panel").parentElement?.style.opacity).toBe(
    "",
  );
  expect(screen.getByRole("button", { name: "Start task" })).toBeTruthy();
});
