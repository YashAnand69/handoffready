# Studio North · synthetic sample — client delivery record

Status: Draft with outstanding items (draft\_with\_gaps)

Outstanding review, assessment, technical findings or exception explanations remain. Read the actions below before sending.

Snapshot: 1a26f2fca9da40638e9110511959b6e9
Created: 2026-10-14T18:47:27.696343+00:00
Source revision: 18

Send the original files alongside this record. This document identifies supporting files; it does not contain their original bytes.

Delivery evidence and human review only. This is not a certification, client acceptance, website execution test or aesthetic judgment.

Scope items: 3
Current human reviews: 3
Failed technical checks: 1
Unavailable technical checks: 0
Scope exceptions: 0
Items with human-only checks: 1
Supporting originals: 6

Counts overlap: check counts and requirement counts measure different things.

## Outstanding actions

- Deliver exactly three distinct 1080 × 1080 PNG launch images.: 1 technical check(s) failed.
- Deliver exactly three distinct 1080 × 1080 PNG launch images.: Human disposition: needs\_work
- Provide a guide explaining how to update the website contact email.: Human disposition: needs\_work

## 1. Deliver a transparent PNG logo and an SVG logo.

Human disposition: satisfied
Review currency: current

- presence: pass. Selected inspected files counted; distinct bytes do not prove distinct designs.
- presence expected: 1
- presence actual: 1
- presence: pass. Selected inspected files counted; distinct bytes do not prove distinct designs.
- presence expected: 1
- presence actual: 1
- png nonopaque pixels: pass. At least one nonopaque pixel per PNG; correct background removal still needs visual review.
- png\_nonopaque\_pixels actual: \[true\]

- logo.svg · svg · 230 bytes · SHA-256 20b8ea08955c
- logo-transparent.png · png · 501 bytes · SHA-256 b2eaac64fa22

## 2. Deliver exactly three distinct 1080 × 1080 PNG launch images.

Human disposition: needs work
Review currency: current

- count: fail. Selected inspected files counted; distinct bytes do not prove distinct designs.
- count expected: 3
- count actual: 2
- image dimensions: pass. Encoded pixel dimensions checked for every selected file.
- image\_dimensions expected: \[1080, 1080\]
- image\_dimensions actual: \[\[1080, 1080\], \[1080, 1080\], \[1080, 1080\]\]
- Outstanding: 1 technical check(s) failed.
- Outstanding: Human disposition: needs\_work

- launch-01.png · png · 6.7 KiB · SHA-256 0f7057019dbf
- launch-02.png · png · 6.7 KiB · SHA-256 59a2864f7729
- launch-03-duplicate.png · png · 6.7 KiB · SHA-256 59a2864f7729

## 3. Provide a guide explaining how to update the website contact email.

Human disposition: needs work
Review currency: current

- Human judgment: requires human assessment. Review steps for updating the website contact email.
- Outstanding: Human disposition: needs\_work

- contact-guide.md · markdown · 45 bytes · SHA-256 fe1355c17ce4

Usage note: The supplied guide still needs the contact-email update steps.

## Supporting file inventory

- logo.svg · svg · 230 bytes · inspected
  SHA-256: 20b8ea08955cda08e2ad041aa58f3242537d8f56e5b621f6a9638fcdcc765be5
- launch-01.png · png · 6.7 KiB · inspected
  SHA-256: 0f7057019dbf463e4b4bfb2d26e68ffdff00e454e4ae01858408d85948e8408e
- launch-02.png · png · 6.7 KiB · inspected
  SHA-256: 59a2864f7729887ae6a8f0ecbe1a72a99fddb8801fe63f2237422873a90feb09
- launch-03-duplicate.png · png · 6.7 KiB · inspected
  SHA-256: 59a2864f7729887ae6a8f0ecbe1a72a99fddb8801fe63f2237422873a90feb09
- contact-guide.md · markdown · 45 bytes · inspected
  SHA-256: fe1355c17ce466c81528571159696b914da38450adc7484d0ff34b848816d748
- logo-transparent.png · png · 501 bytes · inspected
  SHA-256: b2eaac64fa22c65fb6296f09e7d5f24bfd151d5dee13a08eb9fa961fa09b625f

## Record identity

Schema version: 2
Input SHA-256: 21c133731468a4bcbb54004e6e0eb0887e6d06cf3c2ad2ef3b4e402e72d147fe
Baseline SHA-256: 095a310038f60582191e1887e3334309e3ff34cdd77c225f0ba26c44ca5735b9

Checksums identify content; they are not signatures, proof of client approval or trusted timestamps.
