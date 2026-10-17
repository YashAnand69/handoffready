import FirstRunGuide from "./components/FirstRunGuide";
import AttentionOverview from "./components/AttentionOverview";
import { nextAction } from "./workflow";
import { useEntranceMotion } from "./useEntranceMotion";
import EvidenceGraphic from "./components/EvidenceGraphic";
import AuditHistory from "./components/AuditHistory";
import Brief from "./components/Brief";
import Checklist from "./components/Checklist";
import Files from "./components/Files";
import Review from "./components/Review";
import Handoff from "./components/Handoff";
import { useEffect, useState, useRef, useCallback } from "react";
import { api, bootstrap, download } from "./api";
import { readable, latestDecisions } from "./presentation";
import type { Capabilities, Project, Job, ProjectOverview } from "./types";
const steps = ["Brief", "Checklist", "Files", "Review", "Handoff"];
const terminal = new Set([
  "succeeded",
  "failed",
  "cancelled",
  "interrupted",
  "superseded",
]);
export default function App() {
  const [projects, setProjects] = useState<ProjectOverview[]>([]),
    [project, setProject] = useState<Project | null>(null),
    [cap, setCap] = useState<Capabilities | null>(null),
    [step, setStep] = useState(0),
    [name, setName] = useState(""),
    [error, setError] = useState(""),
    [status, setStatus] = useState(""),
    [busy, setBusy] = useState(false),
    [connected, setConnected] = useState(false),
    [selected, setSelected] = useState(""),
    [dirty, setDirty] = useState(false),
    [connectionRetry, setConnectionRetry] = useState(0),
    [connecting, setConnecting] = useState(false);
  useEntranceMotion(project?.id || "home");
  const [fileDrafts, setFileDrafts] = useState<Record<string, boolean>>({});
  const onRenameDirty = useCallback(
    (id: string, value: boolean) =>
      setFileDrafts((previous) => {
        if (!!previous[id] === value) return previous;
        const next = { ...previous };
        if (value) next[id] = true;
        else delete next[id];
        return next;
      }),
    [],
  );
  const hasUnsaved = dirty || Object.values(fileDrafts).some(Boolean);
  const taskLock = useRef(false);
  const allowLeave = () =>
    !hasUnsaved ||
    confirm("You have unsaved edits. Discard those edits and leave this step?");
  const goReview = (id: string) => {
    const current =
      project?.baseline.requirements.find((r) => r.id === selected)?.id ||
      project?.baseline.requirements[0]?.id;
    if (step === 3 && id === current) return;
    if (allowLeave()) {
      setSelected(id);
      setStep(3);
      setDirty(false);
      setError("");
    }
  };
  const clearDrafts = (id: string) => {
    try {
      Object.keys(localStorage)
        .filter((k) => k.startsWith(`handoff-brief-${id}`))
        .forEach((k) => localStorage.removeItem(k));
    } catch {
      /* Browser storage may be unavailable. */
    }
  };
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (hasUnsaved) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [hasUnsaved]);
  const previousLocation = useRef({ projectId: "", step: 0 });
  useEffect(() => {
    const id = project?.id || "";
    if (
      previousLocation.current.projectId === id &&
      previousLocation.current.step === step
    )
      return;
    previousLocation.current = { projectId: id, step };
    const target = document.querySelector(
      project ? ".step-nav" : ".dashboard-hero",
    ) as HTMLElement | null;
    target?.scrollIntoView?.({ block: "start", behavior: "auto" });
    const heading = document.querySelector(
      project ? ".workspace-step h2" : ".hero-copy h1",
    ) as HTMLElement | null;
    if (heading) {
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    }
  }, [step, project?.id]);
  const refresh = async (id = project?.id) => {
    if (id) {
      const p = await api<Project>(`/projects/${id}`);
      setProject(p);
      return p;
    }
    return null;
  };
  const loadProjects = async () =>
    setProjects(await api<ProjectOverview[]>("/projects"));
  useEffect(() => {
    let active = true;
    setConnecting(true);
    setError("");
    (async () => {
      try {
        await bootstrap();
        const [p, c] = await Promise.all([
          api<ProjectOverview[]>("/projects"),
          api<Capabilities>("/capabilities"),
        ]);
        if (active) {
          setProjects(p);
          setCap(c);
          setConnected(true);
        }
      } catch (e) {
        if (active) {
          setConnected(false);
          setError((e as Error).message);
        }
      } finally {
        if (active) setConnecting(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [connectionRetry]);
  useEffect(() => {
    if (!connected) return;
    const timer = setInterval(
      () =>
        api<Capabilities>("/capabilities")
          .then(setCap)
          .catch(() => {}),
      15000,
    );
    return () => clearInterval(timer);
  }, [connected]);
  const activeJobs = project?.jobs.filter((j) => !terminal.has(j.state)) || [];
  const activeJobIds = JSON.stringify(activeJobs.map((job) => job.id).sort());
  const visibleProjectId = useRef(project?.id);
  visibleProjectId.current = project?.id;
  useEffect(() => {
    if (!project || !activeJobs.length) return;
    let disposed = false;
    const id = project.id;
    let inFlight = false;
    const activeIds = activeJobs.map((job) => job.id);
    const current = () => !disposed && visibleProjectId.current === id;
    const tick = setInterval(async () => {
      if (inFlight) return;
      inFlight = true;
      try {
        const status = await api<{ revision: number; jobs: Job[] }>(
          `/projects/${id}/job-status`,
        );
        if (!current()) return;
        const ended = activeIds.some((jobId) => {
          const job = status.jobs.find((candidate) => candidate.id === jobId);
          return !job || terminal.has(job.state);
        });
        if (ended) {
          // A terminal status is not evidence: reconcile and refresh the actual
          // project once before publishing suggestions or reporting completion.
          const refreshed = await api<Project>(`/projects/${id}`);
          if (current())
            setProject((previous) =>
              previous?.id === id && refreshed.revision >= previous.revision
                ? refreshed
                : previous,
            );
        } else {
          setProject((previous) =>
            previous?.id === id ? { ...previous, jobs: status.jobs } : previous,
          );
        }
      } catch (e) {
        if (current()) setError((e as Error).message);
      } finally {
        inFlight = false;
      }
    }, 1400);
    return () => {
      disposed = true;
      clearInterval(tick);
    };
  }, [project?.id, activeJobIds]);
  const observedJobs = useRef<{
    projectId: string;
    states: Map<string, string>;
  }>({ projectId: "", states: new Map() });
  useEffect(() => {
    if (!project) return;
    if (observedJobs.current.projectId !== project.id) {
      observedJobs.current = {
        projectId: project.id,
        states: new Map(project.jobs.map((j) => [j.id, j.state])),
      };
      return;
    }
    for (const job of project.jobs) {
      const previous = observedJobs.current.states.get(job.id);
      if (previous && !terminal.has(previous) && terminal.has(job.state)) {
        setStatus(
          job.state === "succeeded"
            ? job.kind === "extract"
              ? "Local checklist suggestions are ready. Review the source and every required format before confirming."
              : "Local match suggestions are ready. Review actual files and evidence before making your decision."
            : `Local ${job.kind} ${job.state}. ${job.error || "You can retry explicitly when ready."}`,
        );
      }
      observedJobs.current.states.set(job.id, job.state);
    }
  }, [project?.id, project?.jobs]);
  async function task(fn: () => Promise<unknown>) {
    if (taskLock.current) return;
    taskLock.current = true;
    setBusy(true);
    setError("");
    setStatus("");
    try {
      await fn();
      setDirty(false);
    } catch (e) {
      setError((e as Error).message);
      if (project) await refresh().catch(() => {});
    } finally {
      taskLock.current = false;
      setBusy(false);
    }
  }
  async function mutate(path: string, body?: unknown, method = "POST") {
    if (!project) return;
    await api(path, method, body, project.revision);
    return await refresh();
  }
  async function run(kind: string) {
    await mutate(`/projects/${project!.id}/jobs/${kind}`, {});
    setStatus("Local analysis started. Suggestions will need your review.");
  }
  async function startSample() {
    const names = [
      "logo-opaque.png",
      "logo.svg",
      "launch-01.png",
      "launch-02.png",
      "launch-03-duplicate.png",
      "contact-guide.md",
    ];
    const brief = await fetch("/sample/brief.txt").then((r) => {
      if (!r.ok) throw new Error("Sample brief is missing.");
      return r.text();
    });
    const files = await Promise.all(
      names.map(async (name) => {
        const response = await fetch("/sample/" + name);
        if (!response.ok) throw new Error("Sample packet is missing.");
        return new File([await response.blob()], name);
      }),
    );
    let p = await api<Project>("/projects", "POST", {
      name: "Studio North · synthetic sample",
    });
    setProject(p);
    setStep(0);
    await loadProjects();
    p = await api<Project>(
      `/projects/${p.id}/brief`,
      "PUT",
      { text: brief, source_label: "Original synthetic demo brief" },
      p.revision,
    );
    const packet = new FormData();
    files.forEach((file) => packet.append("files", file));
    p = await api<Project>(
      `/projects/${p.id}/files`,
      "POST",
      packet,
      p.revision,
    );
    setProject(p);
    setStep(1);
    setStatus(
      "Synthetic sample loaded and inspected. Ask local AI for a checklist, then review it yourself. The packet intentionally includes an opaque logo, duplicate launch image and incomplete guide.",
    );
  }
  const model = cap?.model || {};
  const ready =
    cap?.model_ready === true ||
    model.ready === true ||
    model.available === true ||
    model.state === "ready";
  const currentDecisions =
    latestDecisions(project?.decisions || []).filter(
      (d) =>
        d.review_state === "confirmed" && d.input_hash === project?.input_hash,
    ) || [];
  const requirements = project?.baseline.requirements || [];
  const suggested = project ? nextAction(project) : null;
  return (
    <>
      <a className="skip" href="#workspace">
        Skip to workspace
      </a>
      <header>
        <button
          className="brand"
          disabled={busy}
          onClick={() => {
            if (allowLeave()) {
              setProject(null);
              void task(loadProjects);
              setDirty(false);
              setError("");
              setStatus("");
            }
          }}
        >
          Handoff<span>Ready</span>
          <i>DELIVERY DESK</i>
        </button>
        <div className="header-right">
          <span className="privacy-dot">On this computer</span>
          <span className={`badge ${ready ? "good" : "neutral"}`}>
            {ready ? "Local model available" : "Model needs setup"}
          </span>
        </div>
      </header>
      <main id="workspace" className={project ? "desk-project" : "desk-home"}>
        {project && (
          <div className="page-top workspace-top">
            <div>
              <p className="eyebrow">A clearer finish for your client work</p>
              <h1>{project.name}</h1>
              <p className="subtext">
                Your agreed brief. Your actual files. Every decision with a
                reason.
              </p>
            </div>
            <button
              className="quiet"
              disabled={busy}
              onClick={() => {
                if (allowLeave()) {
                  setProject(null);
                  void task(loadProjects);
                  setDirty(false);
                  setStatus("");
                }
              }}
            >
              ← All handoffs
            </button>
          </div>
        )}
        {error && (
          <div className="alert error" role="alert">
            {error}
            <button onClick={() => setError("")} aria-label="Dismiss error">
              ×
            </button>
          </div>
        )}
        {!connected && (
          <div className="connection-retry">
            <p role="status">
              {connecting
                ? "Connecting to the local service…"
                : "The local service is unavailable. Start the app, then retry."}
            </p>
            <button
              disabled={connecting}
              onClick={() => setConnectionRetry((v) => v + 1)}
            >
              Retry local connection
            </button>
          </div>
        )}
        {status && (
          <p className="status" role="status">
            {status}
          </p>
        )}
        {!project ? (
          <>
            <section className="dashboard-hero">
              <div className="hero-copy">
                <p className="eyebrow">THE LAST MILE OF GOOD WORK</p>
                <h1>
                  Deliver with
                  <br />
                  <em>nothing left unclear.</em>
                </h1>
                <p className="hero-description">
                  Your brief, your files, your final say. Catch the small things
                  before they become another client email.
                </p>
                <div className="hero-actions">
                  <a className="primary-link" href="#new-handoff">
                    Check a delivery ↗
                  </a>
                  <button
                    disabled={busy || !connected}
                    onClick={() => task(startSample)}
                  >
                    Try the synthetic sample →
                  </button>
                </div>
                <p className="fine">
                  An intentionally imperfect example: an opaque logo, duplicate
                  artwork and an incomplete guide. You review the evidence.
                </p>
              </div>
              <div className="hero-visual">
                <p className="eyebrow">FROM PROMISE TO PACKET</p>
                <EvidenceGraphic />
                <div className="orbit-note">
                  <span className="privacy-dot">Stays on your computer</span>
                  <p>
                    Local AI suggests. File checks inspect. You decide what is
                    ready.
                  </p>
                </div>
              </div>
            </section>
            <FirstRunGuide />
            <div className="dashboard-workspace">
              <section className="card dashboard-start" id="new-handoff">
                <p className="eyebrow">START SOMETHING CLEAR</p>
                <h2>Check your next delivery.</h2>
                <p className="muted">
                  Give this handoff a name. Then bring the brief you agreed with
                  your client.
                </p>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    task(async () => {
                      const p = await api<Project>("/projects", "POST", {
                        name: name.trim(),
                      });
                      setProject(p);
                      setStep(0);
                      setName("");
                      await loadProjects();
                    });
                  }}
                >
                  <label htmlFor="project-name">Project name</label>
                  <input
                    id="project-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="For example, Studio North launch"
                    maxLength={120}
                  />
                  <button
                    className="primary"
                    disabled={!connected || busy || !name.trim()}
                  >
                    Create a handoff <span>↗</span>
                  </button>
                </form>
                <p className="fine">
                  No account or client migration. A manual checklist works even
                  when the local model is unavailable.
                </p>
              </section>
              <section className="saved-projects">
                <div className="section-top">
                  <div>
                    <p className="eyebrow">YOUR WORKSPACE</p>
                    <h2>Pick up where it matters.</h2>
                  </div>
                  <span className="badge">
                    {projects.length}{" "}
                    {projects.length === 1 ? "handoff" : "handoffs"}
                  </span>
                </div>
                <p className="fine">
                  Saved review status. Original files are verified when you open
                  a handoff.
                </p>
                <div className="project-list">
                  {projects.length ? (
                    projects.map((p, index) => (
                      <button
                        key={p.id}
                        className="project-link project-card"
                        aria-label={p.name + " ↗"}
                        disabled={busy}
                        onClick={() =>
                          task(async () => {
                            const loaded = await refresh(p.id);
                            if (loaded) {
                              const action = nextAction(loaded);
                              setStep(action.step);
                              setSelected(action.id || "");
                            }
                          })
                        }
                      >
                        <span className="project-number">
                          {String(index + 1).padStart(2, "0")}
                        </span>
                        <span className="project-details">
                          <b>{p.name}</b>
                          {p.saved_review ? (
                            <>
                              <small>
                                Saved review:{" "}
                                {!p.saved_review.baseline_approved
                                  ? "checklist approval needed"
                                  : p.saved_review.attention_count
                                    ? `${p.saved_review.attention_count} of ${p.saved_review.requirement_count} items need attention`
                                    : p.saved_review.status ===
                                        "reviewed_with_exceptions"
                                      ? "complete with scope exceptions"
                                      : "complete"}
                              </small>
                              <small>
                                {p.saved_review.file_count} files
                                {p.saved_review.stale_review_count > 0 &&
                                  ` · ${p.saved_review.stale_review_count} stale ${p.saved_review.stale_review_count === 1 ? "review" : "reviews"}`}
                                {p.updated_at &&
                                  Number.isFinite(Date.parse(p.updated_at)) &&
                                  ` · Updated ${new Date(p.updated_at).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}`}
                              </small>
                            </>
                          ) : (
                            <small>Continue from the next useful step</small>
                          )}
                        </span>
                        <span>↗</span>
                      </button>
                    ))
                  ) : (
                    <div className="empty">
                      <h3>A clear desk. A fresh start.</h3>
                      <p>
                        Your saved handoffs will appear here. Start a delivery
                        or explore the synthetic sample above.
                      </p>
                    </div>
                  )}
                </div>
                <a
                  className="setup-link"
                  href="/setup.html"
                  target="_blank"
                  rel="noreferrer"
                >
                  Local setup and supported limits ↗
                </a>
              </section>
            </div>
            <section
              className="workflow-principles"
              aria-label="How a handoff works"
            >
              <article>
                <span>01 / AGREE</span>
                <h3>Start from the promise.</h3>
                <p>
                  Turn the saved brief into requirements you can correct and
                  confirm.
                </p>
              </article>
              <article>
                <span>02 / INSPECT</span>
                <h3>Look beyond filenames.</h3>
                <p>
                  Compare actual file properties, source evidence and your own
                  judgment.
                </p>
              </article>
              <article>
                <span>03 / DELIVER</span>
                <h3>Leave a clear record.</h3>
                <p>
                  Export the reviewed scope and remaining gaps. Send the
                  originals alongside it.
                </p>
              </article>
            </section>
          </>
        ) : (
          <>
            {suggested && (
              <section className="next-action" aria-label="Suggested next step">
                <span className="next-action-step">NEXT</span>
                <div className="next-action-copy">
                  <b>{suggested.label}</b>
                  <p>{suggested.detail}</p>
                </div>
                <button
                  className="next-action-link"
                  disabled={busy || !!activeJobs.length}
                  onClick={() => {
                    if (suggested.step === 3 && suggested.id) {
                      goReview(suggested.id);
                      return;
                    }
                    if (suggested.step === step) return;
                    if (allowLeave()) {
                      setStep(suggested.step);
                      setSelected(suggested.id || "");
                      setDirty(false);
                      setError("");
                    }
                  }}
                >
                  Continue →
                </button>
              </section>
            )}
            {project.attention_summary && step !== 4 && (
              <AttentionOverview
                summary={project.attention_summary}
                disabled={busy || !!activeJobs.length}
                review={goReview}
                compact
              />
            )}
            <nav className="step-nav" aria-label="Handoff workflow">
              {steps.map((s, i) => (
                <button
                  key={s}
                  disabled={busy}
                  aria-current={step === i ? "step" : undefined}
                  onClick={() => {
                    if (i === step) return;
                    if (allowLeave()) {
                      setStep(i);
                      setDirty(false);
                      setError("");
                    }
                  }}
                >
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  {s}
                </button>
              ))}
            </nav>
            <div className="workspace-summary">
              <span>{requirements.length} checklist items</span>
              <span>{project.files.length} files in packet</span>
              <span>{currentDecisions.length} current mapping reviews</span>
              <span className="muted">
                {project.baseline.state === "approved"
                  ? "Checklist confirmed"
                  : "Checklist needs confirmation"}
              </span>
            </div>
            {!!activeJobs.length && (
              <section className="job-bar" aria-label="Local analysis">
                {activeJobs.map((j) => (
                  <div key={j.id}>
                    <span className="pulse" />
                    <span>
                      {readable(j.kind)} · {j.stage || readable(j.state)}
                    </span>
                    <button
                      className="quiet"
                      onClick={() =>
                        task(async () =>
                          mutate(
                            `/projects/${project.id}/jobs/${j.id}/cancel`,
                            {},
                          ),
                        )
                      }
                    >
                      Cancel
                    </button>
                  </div>
                ))}
              </section>
            )}
            {project.jobs
              .slice(-1)
              .filter((j) =>
                ["failed", "interrupted", "superseded"].includes(j.state),
              )
              .map((j) => (
                <p className="alert warning" key={j.id}>
                  {readable(j.kind)} {readable(j.state)}.{" "}
                  {j.error || "Run again explicitly when you are ready."}
                </p>
              ))}
            <div
              className="workspace-step"
              onChange={() => {
                if ([0, 1, 3].includes(step)) setDirty(true);
              }}
            >
              {step === 0 && (
                <Brief
                  key={project.id}
                  project={project}
                  disabled={busy || !!activeJobs.length}
                  ready={ready}
                  save={(text, label) =>
                    task(async () => {
                      const saved = await mutate(
                        `/projects/${project.id}/brief`,
                        { text, source_label: label },
                        "PUT",
                      );
                      clearDrafts(project.id);
                      setStatus(
                        saved?.baseline.state === "approved"
                          ? "Brief saved. Your confirmed checklist and current reviews are preserved."
                          : "Brief saved. Your next step is to create and confirm a checklist.",
                      );
                      setStep(1);
                    })
                  }
                  extract={() =>
                    task(async () => {
                      await run("extract");
                      setStep(1);
                    })
                  }
                />
              )}
              {step === 1 && (
                <Checklist
                  key={project.id + project.baseline.hash}
                  project={project}
                  disabled={busy || !!activeJobs.length}
                  ready={ready}
                  onDirty={() => setDirty(true)}
                  extract={() => {
                    if (allowLeave()) task(() => run("extract"));
                  }}
                  save={(rows, approve) =>
                    task(async () => {
                      await api(
                        `/projects/${project.id}/baseline`,
                        "PUT",
                        { requirements: rows },
                        project.revision,
                      );
                      const p = await refresh();
                      if (approve && p) {
                        await api(
                          `/projects/${p.id}/baseline/approve`,
                          "POST",
                          {
                            baseline_hash: p.baseline.hash,
                            reviewed_requirement_ids:
                              p.baseline.requirements.map((r) => r.id),
                          },
                          p.revision,
                        );
                        await refresh();
                        setStep(2);
                      }
                      setStatus(
                        approve
                          ? "Checklist confirmed. Bring the files you will deliver."
                          : "Checklist saved.",
                      );
                    })
                  }
                />
              )}
              {step === 2 && (
                <Files
                  project={project}
                  disabled={busy || !!activeJobs.length}
                  onRenameDirty={onRenameDirty}
                  upload={(files) =>
                    task(async () => {
                      const form = new FormData();
                      files.forEach((f) => form.append("files", f));
                      await mutate(`/projects/${project.id}/files`, form);
                      setStatus(
                        "Files received and inspected. Review any blocked files before matching.",
                      );
                    })
                  }
                  replace={(id, file) =>
                    task(async () => {
                      const form = new FormData();
                      form.append("files", file);
                      await mutate(
                        `/projects/${project.id}/files/${id}/replacement`,
                        form,
                      );
                      setStatus(
                        "Replacement inspected. Existing mapping reviews now need a fresh review.",
                      );
                    })
                  }
                  rename={(id, name) =>
                    task(() =>
                      mutate(
                        `/projects/${project.id}/files/${id}`,
                        { display_name: name },
                        "PATCH",
                      ),
                    )
                  }
                  remove={(id) =>
                    task(() =>
                      mutate(
                        `/projects/${project.id}/files/${id}`,
                        undefined,
                        "DELETE",
                      ),
                    )
                  }
                  match={() => {
                    if (allowLeave())
                      task(async () => {
                        await run("match");
                        setStep(3);
                      });
                  }}
                  ready={ready}
                  next={() => {
                    if (allowLeave()) {
                      setStep(3);
                      setDirty(false);
                    }
                  }}
                />
              )}
              {step === 3 && (
                <Review
                  project={project}
                  selected={selected}
                  setSelected={(id) => {
                    if (
                      id ===
                      (project.baseline.requirements.find(
                        (r) => r.id === selected,
                      )?.id || project.baseline.requirements[0]?.id)
                    )
                      return;
                    if (allowLeave()) {
                      setSelected(id);
                      setDirty(false);
                    }
                  }}
                  disabled={busy || !!activeJobs.length}
                  save={(d, advance = false) =>
                    task(async () => {
                      const { requirement_id, ...payload } = d;
                      const updated = await mutate(
                        `/projects/${project.id}/decisions/${requirement_id}`,
                        payload,
                        "PUT",
                      );
                      setStatus(
                        "Your review was saved for this version of the brief and packet.",
                      );
                      if (advance && updated) {
                        const nextId =
                          updated.attention_summary?.attention_requirement_ids.find(
                            (id) => id !== requirement_id,
                          );
                        if (nextId) setSelected(nextId);
                        else setStep(4);
                      }
                    })
                  }
                  next={() => {
                    if (allowLeave()) {
                      setStep(4);
                      setDirty(false);
                    }
                  }}
                />
              )}
              {step === 4 && (
                <Handoff
                  project={project}
                  disabled={busy || !!activeJobs.length}
                  review={goReview}
                  exportNow={(ack, previewRevision) =>
                    task(async () => {
                      const out = await api<{
                        id?: string;
                        export_id?: string;
                        export?: { id: string };
                      }>(
                        `/projects/${project.id}/exports`,
                        "POST",
                        {
                          acknowledge_unresolved: ack,
                          preview_revision: previewRevision,
                          input_hash: project.input_hash,
                        },
                        project.revision,
                      );
                      await refresh();
                      setStatus(
                        "Snapshot saved. Choose a format below to download it.",
                      );
                      if (!out.id && !out.export_id && !out.export?.id)
                        throw new Error(
                          "Export did not return a snapshot identifier.",
                        );
                    })
                  }
                  downloadFile={(id, format) =>
                    task(() =>
                      download(
                        `/projects/${project.id}/exports/${id}/${format}`,
                        `handoff-${id.slice(0, 8)}.${format === "html" ? "html" : format}`,
                      ),
                    )
                  }
                />
              )}
            </div>
            <details className="project-tools">
              <summary>Project tools and privacy</summary>
              <p>
                Private brief text, original files and internal review notes
                stay in this local workspace. Client exports contain only the
                handoff projection; preview them before sharing. This app does
                not certify a working website, design quality or contract
                completion.
              </p>
              <AuditHistory key={project.id} projectId={project.id} />
              <button
                className="danger"
                disabled={busy}
                onClick={() => {
                  if (
                    confirm(
                      `Delete “${project.name}” and its local files? Export anything you need first.`,
                    )
                  )
                    task(async () => {
                      await api(
                        `/projects/${project.id}`,
                        "DELETE",
                        undefined,
                        project.revision,
                      );
                      clearDrafts(project.id);
                      setProject(null);
                      await loadProjects();
                    });
                }}
              >
                Delete this project
              </button>
            </details>
          </>
        )}
        <footer>
          <span>Private by design. Clear by evidence.</span>
          <span>
            Open model suggestions · Supported file checks · Your decision
          </span>
        </footer>
      </main>
    </>
  );
}
