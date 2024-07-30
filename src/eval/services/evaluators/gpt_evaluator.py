from langchain.evaluation import load_evaluator
from langchain.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI

from .base_evaluator import BaseEvaluator
from config.gpt_eval_config import gpt_eval_config


class GptEvaluator(BaseEvaluator[int]):
    def __init__(self):
        llm=AzureChatOpenAI(azure_deployment=gpt_eval_config.azure_deployment, api_version=gpt_eval_config.openai_version)
        fstring = """[Instruction]Please act as an impartial judge and evaluate the quality of the response provided by an AI assistant to the user question displayed below.
                    ONLY evaluate the text answer component of the response; do NOT consider any image citations as part of your evaluation.
                    {criteria}

                    [Ground truth]
                    {reference}

                    Begin your evaluation by providing a short explanation. 
                    Be as objective as possible. After providing your explanation, you must rate the response on a scale of 1 to 5 by strictly following this format: "[[rating]]", 
                    for example: "Rating: [[5]]".

                    [Question]
                    {input}

                    [The Start of Assistant\'s Answer]
                    {prediction}
                    [The End of Assistant\'s Answer]"""

        prompt = PromptTemplate.from_template(fstring)
        self._evaluator = load_evaluator("labeled_score_string", criteria="correctness", prompt=prompt, llm=llm)


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

        return score["score"]
