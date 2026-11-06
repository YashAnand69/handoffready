import { useEffect } from "react";

const panels = [
  ".dashboard-start",
  ".saved-projects",
  ".workflow-principles > article",
  ".first-run-guide",
  ".workspace-step > .card",
  ".workspace-step > .review-desk > .decision-card",
  ".delivery-context",
].join(", ");

/** Decoration only: readable CSS is the default, even if every observer fails. */
export function useEntranceMotion(location: string) {
  useEffect(() => {
    const root = document.getElementById("workspace");
    if (
      !root ||
      typeof window.matchMedia !== "function" ||
      typeof window.IntersectionObserver !== "function" ||
      typeof Element.prototype.animate !== "function"
    )
      return;
    const preference = window.matchMedia(
      "(prefers-reduced-motion: no-preference)",
    );
    const seen = new WeakSet<Element>();
    const waiting = new Set<Element>();
    const running = new Map<HTMLElement, Animation>();
    let observer: IntersectionObserver | null = null;
    let mutations: MutationObserver | null = null;

    const cancel = (element: HTMLElement) => {
      const animation = running.get(element);
      running.delete(element);
      animation?.cancel();
    };
    const stop = () => {
      observer?.disconnect();
      mutations?.disconnect();
      observer = null;
      mutations = null;
      waiting.clear();
      for (const element of running.keys()) cancel(element);
    };
    const observe = (element: Element) => {
      if (seen.has(element) || waiting.has(element)) return;
      waiting.add(element);
      observer?.observe(element);
    };
    const discover = (node: Node) => {
      if (!(node instanceof Element)) return;
      if (node.matches(panels)) observe(node);
      node.querySelectorAll(panels).forEach(observe);
    };
    const start = () => {
      if (!preference.matches || observer) return;
      try {
        observer = new IntersectionObserver(
          (entries) => {
            for (const entry of entries) {
              if (!entry.isIntersecting || seen.has(entry.target)) continue;
              observer?.unobserve(entry.target);
              waiting.delete(entry.target);
              seen.add(entry.target);
              const element = entry.target;
              if (
                !preference.matches ||
                !(element instanceof HTMLElement) ||
                !element.isConnected ||
                element.contains(document.activeElement) ||
                element.closest("[hidden]")
              )
                continue;
              // Keep urgent statuses and sticky navigation outside the reveal set.
              // No delay, hidden start style, layout change or retained transform.
              try {
                const animation = element.animate(
                  [
                    { opacity: 0.88, transform: "translateY(8px)" },
                    { opacity: 1, transform: "translateY(0)" },
                  ],
                  { duration: 320, easing: "cubic-bezier(.22,1,.36,1)" },
                );
                running.set(element, animation);
                animation.onfinish = animation.oncancel = () => {
                  if (running.get(element) === animation)
                    running.delete(element);
                };
              } catch {
                // A browser refusing animation must never block a workflow.
              }
            }
          },
          { threshold: 0.06 },
        );
        discover(root);
        if (typeof window.MutationObserver === "function") {
          mutations = new MutationObserver((records) => {
            for (const record of records) record.addedNodes.forEach(discover);
            for (const element of waiting) {
              if (root.contains(element)) continue;
              observer?.unobserve(element);
              waiting.delete(element);
            }
            for (const element of running.keys())
              if (!root.contains(element)) cancel(element);
          });
          mutations.observe(root, { childList: true, subtree: true });
        }
      } catch {
        stop();
      }
    };
    const interrupt = (event: Event) => {
      if (!(event.target instanceof Node)) return;
      for (const element of running.keys())
        if (element.contains(event.target)) cancel(element);
    };
    const onPreference = () => {
      if (preference.matches) start();
      else stop();
    };
    root.addEventListener("focusin", interrupt);
    root.addEventListener("pointerdown", interrupt, true);
    preference.addEventListener?.("change", onPreference);
    start();
    return () => {
      stop();
      root.removeEventListener("focusin", interrupt);
      root.removeEventListener("pointerdown", interrupt, true);
      preference.removeEventListener?.("change", onPreference);
    };
  }, [location]);
}
