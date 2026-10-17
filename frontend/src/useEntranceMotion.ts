import { useEffect } from "react";

/** Content stays visible when animation APIs are unavailable or motion is reduced. */
export function useEntranceMotion(location: string) {
  useEffect(() => {
    if (!window.matchMedia || !window.IntersectionObserver) return;
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (preference.matches) return;
    const running = new Set<Animation>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          observer.unobserve(entry.target);
          const element = entry.target as HTMLElement;
          if (!element.animate || element.contains(document.activeElement))
            continue;
          const animation = element.animate(
            [
              { opacity: 0.45, transform: "translateY(18px)" },
              { opacity: 1, transform: "translateY(0)" },
            ],
            { duration: 460, easing: "cubic-bezier(.2,.7,.2,1)" },
          );
          running.add(animation);
          animation.onfinish = () => running.delete(animation);
        }
      },
      { threshold: 0.08 },
    );
    document
      .querySelectorAll(
        ".dashboard-start, .saved-projects, .workflow-principles article",
      )
      .forEach((element) => observer.observe(element));
    const stop = () => {
      observer.disconnect();
      running.forEach((animation) => animation.cancel());
      running.clear();
    };
    const onPreference = () => {
      if (preference.matches) stop();
    };
    preference.addEventListener("change", onPreference);
    return () => {
      stop();
      preference.removeEventListener("change", onPreference);
    };
  }, [location]);
}
