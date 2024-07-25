from rouge_score import rouge_scorer
from .base_evaluator import BaseEvaluator


class RougeEvaluator(BaseEvaluator[float]):
    _rouge_scorer: rouge_scorer.RougeScorer

    def __init__(self):
        self._rouge_scorer = rouge_scorer.RougeScorer(rouge_types=["rougeL"], use_stemmer=True)


    def evaluate(self, prediction: str | list[str], **kwargs):
        expected_answer: str = kwargs.get("expected_answer")

        if type(prediction) == str:
            prediction = [prediction]

        max_rouge_score = 0
        for pred in prediction:
            rouge_score = self._rouge_scorer.score(pred, expected_answer)["rougeL"].recall
            max_rouge_score = max(max_rouge_score, rouge_score)
        return max_rouge_score



if __name__ == "__main__":
    prediction = "This is a test"
    expected_answer = "This is a test"

    evaluator = RougeEvaluator()
    score = evaluator.evaluate(prediction, expected_answer=expected_answer)
    print(score)