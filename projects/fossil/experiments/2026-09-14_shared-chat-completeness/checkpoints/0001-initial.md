# Checkpoint 0001 — experiment initialized

**Checkpoint ID:** `cp-0001`  
**Actor:** ChatGPT cloud  
**Date:** 2026-09-14

## State entering checkpoint

The lab repository was empty. FOSSIL's shared-chat completeness failure had just been recorded as `Pukujan/fossil-core#247` after the owner reported that long shared conversations may be only partially ingested unless a local agent is explicitly told to inspect the whole conversation.

## Work completed

- Defined the cross-project experiment ledger structure.
- Added durable agent continuation rules and CI validation tooling.
- Created the FOSSIL project namespace.
- Registered this experiment against exact `fossil-core` baseline `c080572905238d9d326401f85e66d04a84832014`.
- Registered public source URL `https://chatgpt.com/share/6aa7eabe-92b4-83ea-899b-7c11fb3fcf58` without fabricating source bytes that this cloud environment cannot retrieve.
- Added the acceptance checklist covering acquisition completeness, fidelity, durable ingestion, semantic query/lineage, projection rebuild and portability inventory.

## Important finding

Source fidelity and acquisition completeness are independent. A byte-exact/verbatim captured response can still represent only part of a long conversation.

## Not yet tested

No local source acquisition or FOSSIL runtime execution has been performed in this experiment yet.

## Exact next action

On the owner's local machine:

1. clone/pull this lab repository and `Pukujan/fossil-core`;
2. verify the FOSSIL run revision explicitly;
3. fetch the supplied ChatGPT share exhaustively and preserve the exact retrieved representation before parsing;
4. record counts/IDs/graph or continuation evidence needed to decide `complete`, `incomplete`, or `unknown`;
5. run the current FOSSIL ingestion path **before implementing a fix**;
6. preserve results under a new `runs/run-.../` directory;
7. update checks/state and append checkpoint 0002.

## Do not redo

Do not recreate the lab structure or reopen the same completeness defect unless live upstream state shows #247 is missing/superseded. Continue from the source acquisition/reproduction step.
