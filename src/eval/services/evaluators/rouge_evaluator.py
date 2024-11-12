from rouge_score import rouge_scorer
from .base_evaluator import BaseEvaluator


class RougeEvaluator(BaseEvaluator[float]):
    """
    A class to evaluate the quality of text predictions using the ROUGE metric.

    Inherits from BaseEvaluator and utilizes the RougeScorer to compute the ROUGE-L score,
    which measures the overlap between the predicted text and the expected answer.
    """
    _rouge_scorer: rouge_scorer.RougeScorer

    def __init__(self):
        """
        Initializes the RougeEvaluator instance.

        Sets up the ROUGE scorer with the ROUGE-L metric and enables stemming for better matching.
        """
        self._rouge_scorer = rouge_scorer.RougeScorer(rouge_types=["rougeL"], use_stemmer=True)


    def evaluate(self, prediction: str | list[str], **kwargs):
        """
        Evaluates the predicted text against the expected answer using the ROUGE-L score.

        Args:
            prediction (str | list[str]): The predicted text or a list of predicted texts to evaluate.
            **kwargs: Additional keyword arguments that must include:
                - expected_answer (str): The ground truth answer to compare against.

        Returns:
            float: The maximum ROUGE-L recall score among the predictions.

        Raises:
            ValueError: If expected_answer is not provided.
        """
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
