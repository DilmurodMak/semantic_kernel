# Sales Analyst – Evaluation Guide

This guide explains how to use the Azure AI evaluation SDK and workflows to evaluate your Sales Analyst LLM agent. It covers the available evaluators, dataset format, and how to run evaluations locally and in the cloud.

## What is being evaluated
- Task success and correctness against expected answers
- Fluency/quality of responses
- Grounding/citations from provided files
- Latency and response length (operational metrics)

## Dataset format (JSONL)
Use one JSON object per line with at least:
- `question`: user query
- `expected_answer`: natural-language target answer
Optional (but recommended) fields when generating results locally:
- `response`: model/agent answer
- `context`: citations or files used (array or string)
- `latency`: ms
- `response_length`: characters/tokens

Example:
{"question":"Which sales orders are not from the United States?","expected_answer":"The orders not from the United States are SO43661 and SO43662, which are both from Canada."}

Your dataset lives at `Sales_Analyst/data/sales_qa.jsonl`.

## Evaluators overview
Azure AI Evaluation provides model-based and rule-based evaluators. Common ones for QA tasks:

- Groundedness: checks if the response is supported by the provided context.
- Relevance: measures how relevant the response is to the question.
- Coherence/Fluency: judges clarity and readability.
- Similarity (semantic): compares response to expected_answer using embeddings.
- Exact-match / Regex (rule-based): verifies numeric or string exactness when applicable.
- Toxicity/Safety: screens unsafe content (optional).

Notes:
- Names/IDs differ by SDK version and workspace. In notebooks, resolve evaluator IDs dynamically or pass evaluator names in a dict payload rather than importing classes directly.

## Local evaluation (notebook)
Use `analyst.ipynb` to:
1) Generate OUTPUT_JSONL by running the agent over `sales_qa.jsonl`, capturing response, context (citations), latency, response_length.
2) Run local evaluators (semantic similarity, groundedness, fluency) against OUTPUT_JSONL.

High-level code shape:
- Load test set (question, expected_answer)
- For each row, call agent to get response + citations
- Write OUTPUT_JSONL with response, context, latency, response_length
- Apply evaluators locally and compute scores/metrics

Troubleshooting:
- If evaluator classes aren’t found, avoid hard imports; use dict-based configuration and SDK client methods.
- Ensure your environment has credentials for any embedding/model calls used by evaluators.

## Cloud evaluation (Azure AI Foundry)
Prereqs:
- Azure subscription and Azure AI project
- Agent deployed or callable in your project
- Proper role permissions to submit evaluations

Workflow in `analyst.ipynb`:
1) Upload dataset: point to `OUTPUT_JSONL` or `sales_qa.jsonl` as an input dataset asset.
2) Select evaluators: provide evaluator names/IDs in a dict payload; resolve evaluator IDs with the project client.
3) Submit evaluation job: send a JSON body including dataset reference, evaluators, and model headers.
4) Monitor and fetch results: poll job status and download the result artifact (scores and per‑row details).

Compatibility tips:
- Prefer dict payloads over strict class imports (SDK namespaces change).
- When including citations, store them under `context` to align with groundedness evaluators.
- Ensure model deployment names and API versions in headers match your Azure AI project.

## Running locally vs cloud – quick compare
- Local: faster iteration, requires local model access for some evaluators.
- Cloud: scalable, consistent evaluator versions, artifacts stored with the project.

## Outputs and metrics
Typical artifacts:
- Per‑row scores (groundedness, relevance, fluency, similarity)
- Aggregated metrics (mean/median, pass@k thresholds)
- Operational metrics (latency, response_length)

## Common issues
- Import errors: switch to dict-based evaluator config.
- Missing citations: update the agent call to return file references; write them into `context`.
- Schema mismatch: keep JSONL one‑object‑per‑line; avoid trailing commas.
- Permission/identity errors in cloud: verify you’re logged in and have project contributor rights.

## References
- Azure AI Evaluation overview (Azure AI Foundry)
- Azure AI Projects and datasets
- Azure OpenAI Agents and citations

If you want, we can wire a small CLI to run local evaluation and print a summary table.
