# Third-party foundations

HandoffReady application code is original work for this project with AI assistance. It uses mature libraries rather than copying another product.

| Foundation | Role | License |
|---|---|---|
| React / React DOM | Interface | MIT |
| Vite / Vitest / TypeScript / Prettier | Build, verification and formatting | MIT / Apache-2.0 (TypeScript) |
| FastAPI / Starlette / Pydantic / Uvicorn | Local API and validation | MIT / BSD-3-Clause (Uvicorn) |
| SQLite | Local persistence | Public domain |
| Pillow | Real image decoding | HPND |
| pypdf | Native PDF inspection | BSD-3-Clause |
| defusedxml | Restricted XML inspection | PSF |
| HTTPX / psutil | Local inference transport / resource monitoring | BSD-3-Clause |
| llama.cpp | Local model runtime | MIT |
| Gemma 4 E2B instruction model / pinned ggml-org conversion | Local language model | Apache-2.0 per pinned model records |

Installed exact dependency versions are in `requirements-backend.lock` and `frontend/package-lock.json`. Verify upstream notices when distributing a bundled runtime; a source release does not redistribute model weights. `docs/MODEL-EVIDENCE.md` links pinned source and conversion revisions, licenses and digests. The model conversion is maintained by ggml-org, not claimed to be Google's own GGUF artifact.

Synthetic fixtures are original geometrical drawings and authored text, dedicated to CC0 as described in fixtures/README.md. No client deliverables or third-party artwork are included. Interface uses device fonts and original CSS; no remote fonts, scraped design assets or external tracking code.

Compiled frontend runtime license texts and exact versions are included in `licenses/`. This source release does not include installed Python packages, model weights or llama.cpp binaries; their separately downloaded licenses must be preserved if those components are redistributed.
