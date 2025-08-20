import os
from azure.ai.evaluation import FluencyEvaluator
from azure.ai.evaluation._model_configurations import AzureOpenAIModelConfiguration
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

model_config = AzureOpenAIModelConfiguration(
    azure_endpoint="https://semantic-aifoundry.cognitiveservices.azure.com/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2025-01-01-preview",
    azure_deployment="gpt-4o",
)


fluency_evaluator = FluencyEvaluator(model_config=model_config)
result = fluency_evaluator(response="Paris is a capital of France. It is a beautiful city with many attractions. The Eiffel Tower is one of the most famous landmarks in Paris. The Louvre Museum is also a must-visit place for art lovers.")

print("Evaluation result:")
pprint(result)