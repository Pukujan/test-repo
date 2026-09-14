# Current Handoff

> Generated from `experiment.json` + `state.json`. Do not edit directly.

**Experiment:** `fossil-2026-09-14-shared-chat-completeness`  
**Status:** `ready`

## Question

Can current FOSSIL capture the entire long shared ChatGPT conversation, prove completeness, ingest it durably, query its semantic history, and rebuild retrieval without losing meaning?

## Current focus

Reproduce the long shared-chat completeness defect locally against the exact pinned FOSSIL revision before changing implementation.

## Last durable checkpoint

`checkpoints/0001-initial.md` — Experiment created; local reproduction is the next action.

## Exact next action

On the local machine, fetch the supplied ChatGPT share exhaustively, preserve the exact retrieved representation, record message/node accounting and completeness evidence, then run the current FOSSIL ingestion path without patching it first.

## Blockers

- Cloud environment cannot fetch the ChatGPT share directly; acquisition must be executed locally.

## Important findings

- Owner observed that long shared chats can be only partially ingested until a local agent is explicitly told to inspect the whole conversation.
- fossil-core issue #247 now tracks the requirement that complete ingestion must be proven mechanically rather than inferred from a successful first fetch.

## Resume protocol

1. Read this file and the experiment-local `AGENTS.md`.
2. Read the last checkpoint above.
3. Verify live upstream refs before mutation.
4. Continue from the exact next action; do not redo passed work without evidence.
5. Before handoff, append a checkpoint, update machine state/checks, run `python tools/lab.py sync`, then `python tools/lab.py validate`.
