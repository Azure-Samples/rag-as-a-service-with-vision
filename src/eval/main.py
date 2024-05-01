import argparse
import os

from services.api_request_manager import ApiRequestManager
from services.orchestrator import Orchestrator


_DEFAULT_DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "sample"
)


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-path",
        type=str,
        default=_DEFAULT_DATASET_PATH
    )
    parser.add_argument(
        "--question-column-name",
        type=str,
        default="question"
    )
    parser.add_argument(
        "--expected-answer-column-name",
        type=str,
        default="answer"
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true"
    )

    return parser.parse_args()



def main(
    orchestrator: Orchestrator,
    dataset_path: str,
    question_column_name: str,
    expected_answer_column_name: str,
    skip_ingest: bool
):
    orchestrator.run(
        dataset_path,
        question_column_name,
        expected_answer_column_name,
        skip_ingest,
    )


if __name__ == "__main__":
    args = _get_args()
    dataset_path = args.dataset_path
    question_column_name = args.question_column_name
    expected_answer_column_name = args.expected_answer_column_name
    skip_ingest = args.skip_ingest

    api_request_manager = ApiRequestManager("local")
    orchestrator = Orchestrator(api_request_manager)

    main(
        orchestrator,
        dataset_path,
        question_column_name,
        expected_answer_column_name,
        skip_ingest
    )
