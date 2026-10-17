# Recorded checkpoint explorer

This is a navigational replay of an actual local synthetic run. Gemma is not running in the visitor's browser. Original review actions were agent-operated; this is not customer-trial evidence. The five stages preserve observed findings, incorrect suggestions, replacement, stale reviews, re-review and distinct immutable records.

`capture-provenance.json` preserves the exact earlier `data.json` bytes, including the API source digest at capture time. After that recording, an API compatibility fix made unchanged saves of persisted v0.1 checklists preserve their approved baseline, hash, decisions, history and revision. It did not change the model, source-grounding or deterministic-check code. The current `data.json` projection omits that changed API module from its explicitly partial unchanged-source subset; it does not replace the historic digest with a later hash.

The downloaded before/after records retain their exact captured bytes and renderer. Client-label wording was subsequently refined in the current renderer, so the download wording may differ from the latest local app. The listed source hashes identify only the named unchanged backend modules, not the full application or every historical renderer revision. The existing Git SHA names the base revision; no new Git commit was invented for the uncommitted upgrade.

The actual JSON/HTML/Markdown artifacts, later redownload of the earlier record, and application captures are individually hash-bound in `data.json`. `capture-provenance.json` is a historical metadata record; it is not a new inference run, a current-source certificate, or permission to publish.

Prepare a separate static staging directory with the project environment:

```sh
.venv/bin/python scripts/prepare_upgrade_replay.py --data docs/replay/data.json --output .runtime/replay-stage-reviewed
```

The output must be empty and outside the captured evidence directory. The builder checks the current declared unchanged-source subset, public-field and asset allowlists, exact snapshot identities, safe rendered artifacts and earlier-record byte equality. It never modifies the recorded exports or deploys the page. Historical provenance remains available in this source directory; the static builder's copied page assets are recorded separately in its verification receipt.
