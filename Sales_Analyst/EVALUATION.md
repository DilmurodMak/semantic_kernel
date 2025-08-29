# Evaluate the Sales Analyst Agent in Azure AI Foundry

This guide explains how the `Sales_Analyst/analyst.ipynb` notebook evaluates an agent-based application locally and logs results to Azure AI Foundry (cloud). It maps key steps in the notebook to Azure’s recommended evaluation flow.

## What you’ll do
- Generate agent responses for a test set by calling the Azure AI Agent Runtime (threads, messages, runs).
- Run quality metrics using the Azure AI Evaluation SDK (QA, Similarity, Relevance) locally and save the results locally.
- Run the same evaluation locally and log the results to your Azure AI Foundry project for governance and observability.

## Prerequisites
- Azure AI Foundry project (Project endpoint).
- Azure OpenAI deployment that supports chat (for example, gpt‑4o family).
- Signed in to Azure CLI (`az login`).
- Python packages: `azure-ai-projects`, `azure-identity`, `azure-ai-evaluation` (plus notebook deps like `pandas`, `python-dotenv`).

Environment variables used by the notebook:
- `AZURE_AI_AGENT_ENDPOINT` – Azure AI Foundry project endpoint (used by `AIProjectClient` and when logging evaluation via `azure_ai_project=...`).
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` – Chat model deployment name (for evaluators and the agent).
- `AZURE_OPENAI_API_KEY` – API key for your Azure OpenAI resource (used by evaluators).
- Optional: `ENABLE_CONSOLE_TRACING=true` to print spans locally.

The notebook loads these via `dotenv`. Ensure your `.env` includes the values above.

## Data
We use `Sales_Analyst/data/sales_qa.jsonl` as the test set. Each line is a JSON object with:
- `question` – user query
- `expected_answer` – ground truth

The notebook writes two artifacts back to the same folder:
- `sales_qa_with_responses.jsonl` – the test set with the agent’s `response`, `context`, `latency`, etc.
- `sales_qa_eval_results.json` – the aggregated evaluation results/metrics summary.

## Step 1 — Create/Configure the agent and tools (notebook)
- Initialize `AIProjectClient` with `AZURE_AI_AGENT_ENDPOINT`.
- Convert Excel files to Markdown and upload them.
- Create a Vector Store and a File Search tool.
- Create the “Sales Analyst Agent” bound to the File Search tool.

This lets the agent answer questions grounded on your uploaded sales data.

## Step 2 — Generate agent responses per test row (notebook)
For each question in `sales_qa.jsonl` the notebook:
1) Creates a fresh thread with `agent_client.threads.create()` to isolate context.
2) Adds the user message via `agent_client.messages.create(...)`.
3) Runs the agent with `agent_client.runs.create_and_process(...)`.
4) Reads the assistant’s reply and collects:
   - `response` – final assistant text
   - `context` – derived citations/snippets from File Search when present (resolved to filenames when possible)
   - `latency` and `response_length`

All items are appended to a list and saved to `sales_qa_with_responses.jsonl`.

## Step 3 — Run local evaluators (notebook)
The notebook uses the Azure AI Evaluation SDK:
- `QAEvaluator` – measures answer quality vs. ground truth
- `SimilarityEvaluator` – semantic similarity
- `RelevanceEvaluator` – relevance to the input query (backed by your Azure OpenAI model)

Column mapping used:
- `query` → `${data.query}`
- `response` → `${data.response}`
- `ground_truth` → `${data.ground_truth}`
- `context` → `${data.context}` (citations)

The run prints a compact metrics summary and writes `sales_qa_eval_results.json`.

## Step 4 — Log results to Azure AI Foundry (cloud)
There are two aligned options shown by the notebook and Microsoft docs:

- Log while running local evaluation
  - Pass your project endpoint into `evaluate(...)`:
    - `azure_ai_project=os.environ.get("AZURE_AI_AGENT_ENDPOINT")`

## View results in Azure AI Foundry
- Go to your Azure AI project → Evaluation tab to review runs, metrics, dataset lineage, and artifacts.

## Tracing (optional)
The notebook configures lightweight OpenTelemetry tracing that:
- Connects to Application Insights via the project’s connection string.
- Instruments OpenAI calls.
- Wraps key steps in spans. Set `ENABLE_CONSOLE_TRACING=true` to print spans inline.


## Minimal code reference (logging to cloud while evaluating locally)
This mirrors the notebook’s evaluator setup and adds `azure_ai_project` to log results to your project:

```python
from azure.ai.evaluation import evaluate, QAEvaluator, SimilarityEvaluator, RelevanceEvaluator
from azure.ai.evaluation._model_configurations import AzureOpenAIModelConfiguration
import os

# Align with your notebook: either use an env var or the literal endpoint you used there
azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "https://semantic-aifoundry.cognitiveservices.azure.com/")

model_config = AzureOpenAIModelConfiguration(
    azure_endpoint=azure_openai_endpoint,
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2025-01-01-preview",
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
)

qa  = QAEvaluator(model_config)
sim = SimilarityEvaluator(model_config)
rel = RelevanceEvaluator(model_config)

result = evaluate(
    data=str(OUTPUT_JSONL),
    evaluators={
        "qa": qa,
        "similarity": sim,
        "relevance": rel,
    },
    evaluator_config={
        "default": {
            "column_mapping": {
                "query": "${data.query}",
                "response": "${data.response}",
                "ground_truth": "${data.ground_truth}",
                "context": "${data.context}",
            }
        }
    },
    # This logs the run to your Azure AI project so it appears in the portal
    azure_ai_project=os.environ.get("AZURE_AI_AGENT_ENDPOINT"),
    output_path=str(EVAL_SUMMARY),
)
print("View in Azure AI Foundry:", result.get("studio_url"))
```

## References
- Cloud evaluation: https://learn.microsoft.com/azure/ai-foundry/how-to/develop/cloud-evaluation
- Local evaluation SDK: https://learn.microsoft.com/azure/ai-foundry/how-to/develop/evaluate-sdk
- View results in portal: https://learn.microsoft.com/azure/ai-foundry/how-to/evaluate-results
- Evaluating Azure AI agents: https://learn.microsoft.com/azure/ai-foundry/how-to/develop/agent-evaluate-sdk
