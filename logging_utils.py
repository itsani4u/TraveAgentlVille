"""
logging_utils.py
-------------------
Two separate logs the agent writes to on every run:

1. Interaction log  (logs/interactions.log)  - what was asked, what came back.
2. Eval log         (logs/eval_log.jsonl)    - the DeepEval + deterministic
                                                report for that same run.

Both are append-only JSON-lines files. Each write:
  (a) appends one JSON record to the local file in logs/, then
  (b) re-uploads that whole local file to its OWN blob in the GCP bucket,
      so the two logs never mix in cloud storage.

Local-first means the app still works (and still produces a local audit
trail) even if GCP credentials aren't configured yet - upload_file_to_bucket
just returns a "skipping real upload" status in that case instead of
raising.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import config
from streamlit_app.gcp_utils import upload_file_to_bucket


def _append_jsonl(local_path: Path, record: dict) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    record_with_ts = {"timestamp": datetime.now(timezone.utc).isoformat(), **record}
    with open(local_path, "a") as f:
        f.write(json.dumps(record_with_ts) + "\n")


def log_interaction(vacation_info: dict, travel_plan: dict, narrative: str) -> str:
    """Append one agent-run record to logs/interactions.log, then sync
    that file to the bucket at config.GCP_INTERACTION_LOG_BLOB."""
    _append_jsonl(
        config.INTERACTION_LOG_PATH,
        {
            "event": "agent_run",
            "vacation_info": vacation_info,
            "travel_plan": travel_plan,
            "narrative": narrative,
        },
    )
    return upload_file_to_bucket(str(config.INTERACTION_LOG_PATH), config.GCP_INTERACTION_LOG_BLOB)


def log_eval_result(vacation_info: dict, eval_report: dict) -> str:
    """Append one DeepEval report to logs/eval_log.jsonl, then sync that
    file to the bucket at config.GCP_EVAL_LOG_BLOB - a separate blob from
    the interaction log above."""
    _append_jsonl(
        config.EVAL_LOG_PATH,
        {
            "event": "deepeval_run",
            "vacation_info": vacation_info,
            "eval_report": eval_report,
        },
    )
    return upload_file_to_bucket(str(config.EVAL_LOG_PATH), config.GCP_EVAL_LOG_BLOB)
