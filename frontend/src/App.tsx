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
import type { Capabilities, Project } from "./types";
const steps = ["Brief", "Checklist", "Files", "Review", "Handoff"];
const terminal = new Set([
  "succeeded",
  "failed",
  "cancelled",
  "interrupted",
  "superseded",
]);
export default function App() {
  const [projects, setProjects] = useState<{ id: string; name: string }[]>([]),
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
      project ? ".step-nav" : ".page-top",
    ) as HTMLElement | null;
    target?.scrollIntoView?.({ block: "start", behavior: "auto" });
    const heading = document.querySelector("main h2") as HTMLElement | null;
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
    setProjects(await api<{ id: string; name: string }[]>("/projects"));
  useEffect(() => {
    let active = true;
    setConnecting(true);
    setError("");
    (async () => {
      try {
        await bootstrap();
        const [p, c] = await Promise.all([
          api<{ id: string; name: string }[]>("/projects"),
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
  useEffect(() => {
    if (!project || !activeJobs.length) return;
    let disposed = false;
    const id = project.id;
    const tick = setInterval(() => {
      api<Project>(`/projects/${id}`)
        .then((p) => {
          if (!disposed) setProject(p);
        })
        .catch((e) => {
          if (!disposed) setError(e.message);
        });
    }, 1400);
    return () => {
      disposed = true;
      clearInterval(tick);
    };
  }, [project?.id, activeJobs.length]);
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
      <main id="workspace">
        <div className="page-top">
          <div>
            <p className="eyebrow">A clearer finish for your client work</p>
            <h1>{project ? project.name : "Finish with clarity."}</h1>
            <p className="subtext">
              {project
                ? "Your agreed brief. Your actual files. Every decision with a reason."
                : "Check the files you are about to deliver, and make the handoff easier to understand."}
            </p>
          </div>
          {project && (
            <button
              className="quiet"
              disabled={busy}
              onClick={() => {
                if (allowLeave()) {
                  setProject(null);
                  setDirty(false);
                  setStatus("");
                }
              }}
            >
              ← All handoffs
            </button>
          )}
        </div>
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
          <div className="welcome-grid">
            <section className="card start-card">
              <p className="eyebrow">START A HANDOFF</p>
              <h2>A small check before you send.</h2>
              <ol className="onboarding">
                <li>
                  <span>01</span>
                  <div>
                    <b>Confirm the brief</b>
                    <p>
                      Turn what you agreed into a checklist you can correct.
                    </p>
                  </div>
                </li>
                <li>
                  <span>02</span>
                  <div>
                    <b>Bring your delivery files</b>
                    <p>
                      Inspect supported file details and review suggested
                      matches.
                    </p>
                  </div>
                </li>
                <li>
                  <span>03</span>
                  <div>
                    <b>Make the handoff understandable</b>
                    <p>
                      Keep missing and manual items visible in a client
                      manifest.
                    </p>
                  </div>
                </li>
              </ol>
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
              <div className="sample-start">
                <button
                  disabled={busy || !connected}
                  onClick={() => task(startSample)}
                >
                  Try the synthetic sample →
                </button>
                <p className="fine">
                  An imperfect packet you can inspect and correct. Uses real
                  file inspection and live model inference when you request
                  suggestions. No customer data.
                </p>
              </div>
              <p className="fine">
                No account or client migration. Files are stored by this local
                service. Initial model setup requires a download.
              </p>
            </section>
            <aside>
              <section className="card model-card">
                <p className="eyebrow">OPEN MODEL / HUMAN REVIEW</p>
                <h2>Evidence beside every suggestion.</h2>
                <EvidenceGraphic />
                <p>
                  Local AI helps connect requirements to file names and readable
                  text. You confirm the meaning. File checks establish only the
                  properties they inspect.
                </p>
                <div className="note">
                  <b>
                    {ready
                      ? "Ready for local suggestions"
                      : "You can begin with a manual checklist"}
                  </b>
                  <p>
                    {ready
                      ? "Your model runs on this computer. Suggestions never become approvals automatically."
                      : "Prepare the local model using the setup guide. Saved projects and manual review work without it."}
                  </p>
                </div>
                <a
                  href="https://github.com/ggml-org/llama.cpp"
                  target="_blank"
                  rel="noreferrer"
                >
                  About the open runtime ↗
                </a>
              </section>
              <a
                className="setup-link"
                href="/setup.html"
                target="_blank"
                rel="noreferrer"
              >
                Local setup and supported limits ↗
              </a>
              <section className="saved-projects">
                <p className="eyebrow">YOUR SAVED HANDOFFS</p>
                {projects.length ? (
                  projects.map((p) => (
                    <button
                      key={p.id}
                      className="project-link"
                      disabled={busy}
                      onClick={() =>
                        task(async () => {
                          await refresh(p.id);
                          setStep(0);
                        })
                      }
                    >
                      <span>{p.name}</span>
                      <span>↗</span>
                    </button>
                  ))
                ) : (
                  <p className="muted">
                    Your first saved handoff will appear here.
                  </p>
                )}
              </section>
            </aside>
          </div>
        ) : (
          <>
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
              onChange={() => {
                if ([0, 1, 3].includes(step)) setDirty(true);
              }}
              onClickCapture={(e) => {
                if (step === 1 && (e.target as HTMLElement).closest("button"))
                  setDirty(true);
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
                  save={(d) =>
                    task(async () => {
                      const { requirement_id, ...payload } = d;
                      await mutate(
                        `/projects/${project.id}/decisions/${requirement_id}`,
                        payload,
                        "PUT",
                      );
                      setStatus(
                        "Your review was saved for this version of the brief and packet.",
                      );
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
                  exportNow={(ack) =>
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
