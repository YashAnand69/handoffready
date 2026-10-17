# Synthetic demo files

The top-level demo assets are original synthetic examples dedicated to CC0 1.0. They contain no client data or model results. Regenerate those assets with `scripts/create_fixtures.py`.

`evaluation-v4/` is a separate agent-authored synthetic evaluation set with its own license and frozen scoring records. Its `runs/` directory preserves actual local-model responses to those synthetic inputs. These are model evaluation records, not customer data, customer feedback or human approval. Do not regenerate or overwrite the frozen evaluation as part of refreshing the demo assets.

The faulty packet uses logo-opaque.png, logo.svg, launch-01.png, launch-02.png, launch-03-duplicate.png, launch-wrong-size.png, contact-guide.md and maintenance-notes.md. The duplicate is byte-identical; the opaque PNG has an alpha channel but no transparent pixels. logo-transparent.png is a correction fixture.
