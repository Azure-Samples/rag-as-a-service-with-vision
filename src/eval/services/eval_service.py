from dataclasses import dataclass
from langchain.evaluation import load_evaluator
from langchain_openai import AzureChatOpenAI
import pandas as pd


@dataclass
class ChunkEvaluationResults:
    rouge: float
    in_top: int


@dataclass
class GenerativeEvaluationResults:
    gpt_score: int


class EvalService(object):
    def _evaluation_chunk(self, expected_answer_column: str, chunk_answer: list[str]) -> ChunkEvaluationResults:
        return ChunkEvaluationResults(
            rouge=0.0,
            in_top=0
        )
    
    def _evaluation_generative(self, expected_answer_column: str, generative_answer: str) -> GenerativeEvaluationResults:
        return GenerativeEvaluationResults(
            gpt_score=0
        )


    def run_eval(
        self,
        dataset: pd.DataFrame,
        question_column_name: str,
        generative_answer_column_name: str,
        chunk_answer_column_name: str,
        expected_answer_column_name: str
    ):
        for index, row in dataset.iterrows():
            question = row[question_column_name]
            expected_answer = row[expected_answer_column_name]
            generative_answer = row[generative_answer_column_name]
            chunk_answer_column_name: list[str] = row[chunk_answer_column_name]

            chunk_results = self._evaluation_chunk(expected_answer, chunk_answer_column_name)
            