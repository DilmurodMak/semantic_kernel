from azure.ai.evaluation import GleuScoreEvaluator
from pprint import pprint

gleu_evaluator = GleuScoreEvaluator()

gleu_result = gleu_evaluator(response="Tashkent is the capital of Uzbekistan.", ground_truth="Uzbekistan's capital is Tashkent.")
print("GLEU Evaluation result:")
pprint(gleu_result)