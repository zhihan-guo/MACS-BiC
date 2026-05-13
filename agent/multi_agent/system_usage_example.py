"""
End-to-end usage example for the MACS-BiC multi-agent system.

Required environment variables (or pass them as constructor args):

    OPENAI_API_KEY   - GPT-4o / Gemini proxy key (default base_url is the
                       group's gptplus5 proxy).
    WOS_API_KEY      - Web of Science Starter / Expanded API key.
    GEMINI_API_KEY   - Optional. Falls back to OPENAI_API_KEY when unset.

Usage:

    python -m agent.multi_agent.system_usage_example \\
        --domain "biochar-integrated construction materials carbon footprint" \\
        --workspace ./run_biochar \\
        --max-records 50
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_agent.multi_agent_system import MultiAgentSystem  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MACS-BiC multi-agent pipeline end-to-end.")
    parser.add_argument("--domain", required=True, help="Research domain to mine for.")
    parser.add_argument("--workspace", required=True, help="Folder for intermediate artefacts and the final Excel.")
    parser.add_argument("--max-records", type=int, default=50, help="Max number of DOIs to fetch from WoS.")
    parser.add_argument("--base-url", default="https://az.gptplus5.com/v1", help="OpenAI-compatible base URL.")
    parser.add_argument("--model", default="gpt-4o-2024-11-20", help="GPT-4o model name.")
    parser.add_argument("--mode", choices=["agentic", "programmatic"], default="agentic",
                        help="`agentic` lets the Coordinator drive via ReAct; `programmatic` calls the stages directly.")
    parser.add_argument("--no-llm-judge", action="store_true", help="Skip the LLM accuracy check in the Judger.")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print("[warning] OPENAI_API_KEY is not set; LLM-driven stages will fail.", flush=True)

    mas = MultiAgentSystem(
        api_key=api_key,
        base_url=args.base_url,
        model_name=args.model,
        wos_api_key=os.environ.get("WOS_API_KEY"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY"),
        use_llm_judge=not args.no_llm_judge,
    )

    print(f"[info] starting pipeline ({args.mode}) for domain={args.domain!r}", flush=True)
    if args.mode == "agentic":
        result = mas.run(domain=args.domain, workspace=args.workspace, max_records=args.max_records)
    else:
        result = mas.run_programmatic(domain=args.domain, workspace=args.workspace, max_records=args.max_records)

    dataset = (result.get("context") or {}).get("dataset")
    if dataset:
        print(f"[done] dataset written to {dataset.get('output_excel')!r} "
              f"with {dataset.get('row_count')} rows from {dataset.get('files')} JSONL files.")
    else:
        print("[done] pipeline finished without producing a dataset; inspect `result` for details.")

    success = result.get("success", False)
    print(f"[result] success={success}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
