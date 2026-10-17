"use strict";
(() => {
  const byId = (id) => document.getElementById(id);
  const status = byId("load-status");
  let data;
  let selectedStage = 0;
  const capturedRecords = {};
  function text(tag, value, className) {
    const element = document.createElement(tag);
    element.textContent = value;
    if (className) element.className = className;
    return element;
  }
  function definition(list, label, value) {
    list.append(text("dt", label), text("dd", String(value)));
  }
  function safeAsset(value) {
    return (
      typeof value === "string" &&
      /^(records\/(before|after)\.(json|html|md)|captures\/[a-zA-Z0-9_-]+\.(png|jpg|jpeg))$/.test(
        value,
      ) &&
      Object.hasOwn(data.assets, value)
    );
  }
  function stage(index, focus = true) {
    selectedStage = index;
    const item = data.checkpoints[index];
    byId("checkpoint-number").textContent =
      `RECORDED CHECKPOINT ${index + 1} OF ${data.checkpoints.length}`;
    byId("checkpoint-title").textContent = item.title;
    byId("checkpoint-summary").textContent = item.summary;
    byId("checkpoint-facts").replaceChildren(
      ...item.facts.map((fact) => text("li", fact)),
    );
    byId("checkpoint-findings").replaceChildren(
      ...item.findings.map((finding) => {
        const card = text("section", "", `finding ${finding.status}`);
        const labels = {
          pass: "Recorded check passed",
          fail: "Recorded check failed",
          unknown: "Still requires review",
          note: "Recorded observation",
        };
        card.append(
          text("p", labels[finding.status], "finding-label"),
          text("h3", finding.title),
          text("p", finding.detail),
        );
        return card;
      }),
    );
    const image = byId("capture-image");
    if (item.screenshot && safeAsset(item.screenshot)) {
      image.src = item.screenshot;
      image.alt = `Actual application capture: ${item.title}`;
      byId("capture").hidden = false;
    } else {
      image.removeAttribute("src");
      byId("capture").hidden = true;
    }
    [...byId("stage-navigation").children].forEach((button, i) => {
      if (i === index) button.setAttribute("aria-current", "step");
      else button.removeAttribute("aria-current");
    });
    byId("previous").disabled = index === 0;
    byId("next").disabled = index === data.checkpoints.length - 1;
    const article = byId("checkpoint");
    article.classList.remove("animate");
    // Native navigation controls remain usable without animations.
    requestAnimationFrame(() => article.classList.add("animate"));
    if (focus) byId("checkpoint-title").focus({ preventScroll: false });
  }
  async function readVerifiedRecord(which) {
    const path = `records/${which}.json`;
    if (!safeAsset(path)) throw new Error("Snapshot is not allowlisted.");
    const response = await fetch(path, { cache: "no-store", credentials: "omit", redirect: "error" });
    if (!response.ok) throw new Error("Snapshot is unavailable.");
    const bytes = await response.arrayBuffer();
    if (bytes.byteLength > 1024 * 1024) throw new Error("Snapshot exceeds its bound.");
    const digest = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
      .map((value) => value.toString(16).padStart(2, "0")).join("");
    if (digest !== data.assets[path]) throw new Error("Snapshot bytes differ from captured evidence.");
    const record = JSON.parse(new TextDecoder().decode(bytes));
    if (record.id !== data.snapshots[which].id || record.snapshot_hash !== data.snapshots[which].snapshot_hash || !Array.isArray(record.requirements))
      throw new Error("Snapshot identity differs from recording.");
    capturedRecords[which] = record;
  }
  function recordedFindings(which) {
    const wrapper = text("section", "", "captured-findings");
    wrapper.append(text("h3", "Inspect the actual saved findings"), text("p", "Read directly from the hash-checked recorded JSON. These controls do not change the saved assessment."));
    for (const row of capturedRecords[which].requirements) {
      const details = document.createElement("details");
      details.append(text("summary", row.title));
      details.append(text("p", `Recorded assessment: ${row.human_disposition.replaceAll("_", " ")} · ${row.review_currency}`));
      for (const finding of row.checks) {
        const item = text("div", "", "recorded-finding");
        item.append(text("strong", `${finding.status.toUpperCase()} · ${finding.kind.replaceAll("_", " ")}`), text("p", finding.reason));
        if (Object.hasOwn(finding, "actual")) item.append(text("p", `Observed: ${JSON.stringify(finding.actual)}`, "fine"));
        details.append(item);
      }
      for (const gap of row.gaps) details.append(text("p", gap, "recorded-gap"));
      if (row.client_usage_note) details.append(text("p", row.client_usage_note));
      const files = document.createElement("ul");
      for (const file of row.files) {
        const item = text("li", file.name);
        item.append(text("code", file.sha256));
        files.append(item);
      }
      details.append(files);
      wrapper.append(details);
    }
    return wrapper;
  }
  function snapshot(which) {
    const record = data.snapshots[which];
    byId("before").setAttribute("aria-pressed", String(which === "before"));
    byId("after").setAttribute("aria-pressed", String(which === "after"));
    const panel = byId("record-detail");
    const identity = document.createElement("dl");
    definition(identity, "Snapshot ID", record.id);
    definition(identity, "Created", record.created_at);
    definition(identity, "Input revision", record.source_revision);
    definition(identity, "Recorded state", record.status.replaceAll("_", " "));
    definition(identity, "Snapshot SHA-256", record.snapshot_hash);
    const links = text("p", "", "record-downloads");
    for (const format of ["html", "json", "md"]) {
      const asset = `records/${which}.${format}`;
      if (!safeAsset(asset)) throw new Error("Recorded download is missing.");
      const link = text(
        "a",
        format === "html"
          ? "Read / print HTML"
          : `Download ${format === "md" ? "Markdown" : "JSON"}`,
      );
      link.href = asset;
      if (format !== "html")
        link.download = `${which}-synthetic-delivery-record.${format}`;
      links.append(link);
    }
    panel.replaceChildren(
      text(
        "h3",
        which === "before"
          ? "Earlier delivery record"
          : "Delivery record after correction",
      ),
      text("p", record.summary),
      identity,
      links,
      recordedFindings(which),
    );
  }
  async function open() {
    try {
      const response = await fetch("data.json", {
        cache: "no-store",
        credentials: "omit",
        redirect: "error",
      });
      if (!response.ok) throw new Error("Recorded evidence is unavailable.");
      data = await response.json();
      const requiredStages = [
        "brief",
        "review",
        "correct",
        "rereview",
        "snapshots",
      ];
      if (
        data.version !== "recorded-checkpoints-v1" ||
        !Array.isArray(data.checkpoints) ||
        data.checkpoints.length !== 5 ||
        data.checkpoints.some(
          (item, index) =>
            item.id !== requiredStages[index] ||
            !Array.isArray(item.facts) ||
            !Array.isArray(item.findings),
        ) ||
        !data.assets ||
        !data.snapshots?.before ||
        !data.snapshots?.after
      )
        throw new Error("Recorded evidence does not match this walkthrough.");
      await Promise.all([readVerifiedRecord("before"), readVerifiedRecord("after")]);
      const navigation = byId("stage-navigation");
      data.checkpoints.forEach((item, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.append(
          text("span", String(index + 1)),
          text("span", item.title),
        );
        button.addEventListener("click", () => stage(index));
        navigation.append(button);
      });
      byId("previous").addEventListener("click", () =>
        stage(Math.max(0, selectedStage - 1)),
      );
      byId("next").addEventListener("click", () =>
        stage(Math.min(data.checkpoints.length - 1, selectedStage + 1)),
      );
      byId("before").addEventListener("click", () => snapshot("before"));
      byId("after").addEventListener("click", () => snapshot("after"));
      byId("comparison-summary").textContent = data.comparison.summary;
      byId("immutable-note").textContent = data.comparison
        .old_snapshot_unchanged
        ? "Verified in the recorded run: the earlier snapshot's bytes stayed unchanged after replacement and re-review."
        : "Earlier snapshot byte equality has not been verified for this recording.";
      byId("originals-notice").textContent = data.comparison.originals_notice;
      const identity = byId("identity");
      for (const [label, value] of [
        ["Recorded", data.recorded_at],
        ["Sample", data.sample_id],
        ["Review actor", data.actor],
        ["Prompt", data.prompt_version],
        ["Grounding", data.catalog_version],
        ["Base commit", data.source.base_commit],
        ["Source identity", data.source.label],
      ])
        definition(identity, label, value);
      for (const [path, digest] of Object.entries(data.source.module_sha256)) {
        const row = text("p", path, "module-hash");
        row.append(text("code", digest));
        byId("module-hashes").append(row);
      }
      stage(0, false);
      snapshot("before");
      byId("walkthrough").hidden = false;
      status.textContent =
        "Five recorded checkpoints loaded. No AI or backend service is connected to this page.";
    } catch (error) {
      byId("walkthrough").hidden = true;
      status.classList.add("error");
      status.textContent =
        "The recorded checkpoint data could not be loaded. Read the synthetic records through the links below or watch the current walkthrough.";
      const links = text("p", "");
      for (const [label, path] of [
        ["Earlier record", "records/before.html"],
        ["Record after correction", "records/after.html"],
        ["Current walkthrough", "https://yashanand69.github.io/handoffready/"],
      ]) {
        const link = text("a", label);
        link.href = path;
        links.append(link, document.createTextNode(" · "));
      }
      status.after(links);
    }
  }
  open();
})();
