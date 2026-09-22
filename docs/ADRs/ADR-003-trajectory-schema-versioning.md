# ADR-003: Trajectory schema versioning

Status: accepted. Date: 2026-09-22.

Context: SWE-Gym / SWE-smith / Open-SWE-Traces schemas drift; breaking changes corrupt datasets silently.

Decision: `schemas/trajectory.vX.json` with required `schema_version`. Validators reject unknown major. Minor adds optional fields only. v1 fields: session_id, schema_version, provider, model, messages[], tool_calls[], test_result, resolved, provenance{source, license}.

Consequences: Shot 2+ validators pin v1. Migration scripts on major bump only.
