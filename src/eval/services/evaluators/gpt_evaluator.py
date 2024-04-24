from langchain.evaluation import load_evaluator
from langchain_openai import AzureChatOpenAI

from .base_evaluator import BaseEvaluator
from config.gpt_eval_config import gpt_eval_config


class GptEvaluator(BaseEvaluator[int]):
    def __init__(self):
        self._evaluator = load_evaluator("labeled_score_string", llm=AzureChatOpenAI(azure_deployment=gpt_eval_config.azure_deployment))


    def evaluate(self, prediction: str, **kwargs):
        reference = kwargs.get("reference")
        input = kwargs.get("input")

        if not reference or not input:
            raise ValueError("References and input are required for evaluation")

        score = self._evaluator.evaluate_strings(
            prediction=prediction,
            reference=reference,
            input=input
        )

        return score