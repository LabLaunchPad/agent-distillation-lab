# Evidence ledger

Date: 2026-09-22. Each row is a verified signal; speculation excluded.

| # | Signal | Source | Takeaway for this lab |
|---|--------|--------|----------------------|
| 1 | Distillation = Stored Completions + Evals + FT loop, baseline before/after, iterate on data | https://openai.com/index/api-model-distillation/ | Capture full traces + evals first; train later. Few hundred curated samples can suffice. |
| 2 | Agent evals need trace grading (tool, args, order) + output grading | https://qaskills.sh/blog/openai-agent-evals-datasets-workflow-guide-2026 | Schema must store ordered tool calls with args, plus final output and ideal. |
| 3 | SWE-smith: 5000+ Claude 3.7 trajectories → 40.2% SWE-bench Verified (Qwen-32B) | https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories | Synthetic+real trajectories distill; provenance + license filtering required. |
| 4 | SWE-Gym OpenHands trajectories: messages + tools + test_result + resolved flag | https://huggingface.co/datasets/SWE-Gym/OpenHands-SFT-Trajectories | Trajectory = messages[], tools[], test_result, resolved bool. Adopt same minimal fields. |
| 5 | Open-SWE-Traces: 207k trajectories, 9 langs, OpenHands+SWE-agent, thinking/non-thinking split | https://arxiv.org/html/2606.16038v1 | Keep `reasoning` optional; tag harness + license. |
| 6 | WebGen-Bench: 101 instructions, 647 GUI-agent tests; SFT on 600 trajectories 9.5% → 38.2%; WebGen-Agent multi-level feedback → 58.2% | https://arxiv.org/abs/2505.03733 ; https://arxiv.org/html/2509.22644 | Small curated sets beat scale; step-level feedback is Shot 5 work. |
| 7 | DesignBench: 900 samples, React/Vue/Angular/vanilla x generate/edit/repair | https://github.com/webpai/designbench | Capability matrix must cover framework x task axes for web track. |
| 8 | TRL: SFT → DPO (chosen/rejected pairs, no reward model) → GRPO (online, group-relative, custom reward fns) | https://huggingface.co/docs/trl/en/quickstart | Training order: SFT (Shot 4), DPO/GRPO (Shot 5). No training code in Shot 1. |
| 9 | UltraFeedback/Magpie/LESS: preference pairs + influence-based selection beat volume | survey consensus 2026-09-22 | Add quality/selection stage after capture; 20–50 diverse cases beat hundreds of dupes. |
| 10 | OpenCode: `opencode export [sessionID] [--sanitize]`, SQLite `opencode.db`, session-log plugin writes `.agents-log/` | https://opencode.ai/docs/cli/ ; https://opencode.ai/v2/docs/api/session/v2-session-export | Shot 2 captures via `export` / SQLite read-only; sanitize at capture. |
