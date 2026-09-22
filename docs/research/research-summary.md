# Research summary

1. Distillation works on traces, not just outputs: store ordered tool calls + args + results + final output (OpenAI loop; SWE-Gym; agent-evals trace grading).
2. Small curated > large noisy: 600 trajectories beat best proprietary on WebGen-Bench; 20–50 diverse agent-eval cases beat hundreds of dupes.
3. Schema first: `messages[] + tools[] + test_result + resolved + provenance` covers SWE-Gym, SWE-smith, Open-SWE-Traces.
4. Local-first capture is feasible: OpenCode `export --sanitize` / read-only SQLite → validate → store. No vendor lock-in.
5. Training order is fixed: SFT → DPO → GRPO via TRL. Shots 4/5 only; Shot 1–2 build capture + validation.
6. Web track needs framework × task matrix (DesignBench) + functional + appearance grading (WebGen-Bench).
