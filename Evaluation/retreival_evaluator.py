from pprint import pprint
from azure.ai.evaluation import RetrievalEvaluator
from azure.ai.evaluation._model_configurations import AzureOpenAIModelConfiguration
from dotenv import load_dotenv
import os

load_dotenv()

model_config = AzureOpenAIModelConfiguration(
    azure_endpoint="https://semantic-aifoundry.cognitiveservices.azure.com/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2025-01-01-preview",
    azure_deployment="gpt-4o",
)


retrieval_eval = RetrievalEvaluator(model_config=model_config, threshold=3)
conversation = {
    "messages": [
        {
            "content": "What is the capital of UAE?`''\"</>{}{{]",
            "role": "user",
            "context": "Customer wants to know the capital of UAE",
        },
        {
            "content": "Abu Dhabi",
            "role": "assistant",
            "context": "Abu Dhabi is the capital of UAE",
        },
        {
            "content": "What is the capital of New York City?",
            "role": "user",
            "context": "Customer wants to know the capital of New York City",
        },
        {
            "content": "Albany",
            "role": "assistant",
            "context": "Albany is the capital of Hawaii",
        },
    ],
    "context": "Global context",
}


result = retrieval_eval(conversation=conversation)

# Pretty print the actual results instead of the object
print("Evaluation result:")
pprint(result)

