import os
import json
from loguru import logger as log
import pathlib
import pandas as pd
from tqdm import tqdm
from uuid import uuid4

from .api_request_manager import ApiRequestManager
from .evaluators.gpt_evaluator import GptEvaluator
from .evaluators.rouge_evaluator import RougeEvaluator


_SEARCH_RESPONSE_KEY = "search_response"
_CHAT_RESPONSE_KEY = "chat_response"

_ROUGE_SCORE_COLUMN_NAME = "search_max_rouge_recall"
_GPT_SCORE_COLUMN_NAME = "chat_response_gpt_score"


class DataFolderConfig:
    GROUND_TRUTH_DATASET_FILE_NAME = "ground_truth.csv"
    RAW_DOCUMENTS_FOLDER_NAME = "raw"
    CONFIG_FILE_NAME = "config.json"


class Orchestrator(object):
    _api_request_manager: ApiRequestManager

    _rouge_evaluator: RougeEvaluator
    _gpt_evaluator: GptEvaluator


    def __init__(self, api_request_manager: ApiRequestManager):
        """
        Initializes the Orchestrator with an API request manager.

        Args:
            api_request_manager (ApiRequestManager): The API request manager instance.
        """
        self._api_request_manager = api_request_manager

        # init the evaluators
        self._rouge_evaluator = RougeEvaluator()
        self._gpt_evaluator = GptEvaluator()


    def _setup_environment(
        self,
        config: dict,
        raw_documents_path: str,
        skip_ingest: bool = False
    ):
        """
        Sets up the environment by uploading the configuration and raw documents.

        Args:
            config (dict): Configuration dictionary to upload.
            raw_documents_path (str): Path to the folder containing raw documents.
            skip_ingest (bool): Flag to skip document ingestion (default is False).
        """
        log.info("Setting up environment...")
        res = self._api_request_manager.upload_config(config)
        res.raise_for_status()

        if skip_ingest:
            return

        log.info("Uploading raw documents...")
        config_id = config["id"]
        file_names = os.listdir(raw_documents_path)
        file_paths = [os.path.join(raw_documents_path, file_name) for file_name in file_names]
        files = [("files", open(file_path, "rb")) for file_path in file_paths]
        res = self._api_request_manager.upload(files, config_id)
        res.raise_for_status()


    def _evaluate_search(
            self,
            dataset: pd.DataFrame,
            expected_answer_column_name: str,
    ):
        """
        Evaluates search responses against expected answers using ROUGE metrics.

        Args:
            dataset (pd.DataFrame): DataFrame containing the dataset to evaluate.
            expected_answer_column_name (str): Column name for expected answers.
        """
        log.info("Evaluating search...")
        for index, row in tqdm(dataset.iterrows(), total=dataset.shape[0]):
            expected_answer = row[expected_answer_column_name]
            search_response = json.loads(row[_SEARCH_RESPONSE_KEY])

            score = self._rouge_evaluator.evaluate(
                prediction=search_response,
                expected_answer=expected_answer
            )

            dataset.loc[index, _ROUGE_SCORE_COLUMN_NAME] = score


    def _perform_chat(
        self,
        dataset: pd.DataFrame,
        question_column_name: str,
        config_id: str,
    ):
        """
        Performs chat interactions and stores responses in the dataset.

        Args:
            dataset (pd.DataFrame): DataFrame containing the dataset to process.
            question_column_name (str): Column name for questions to ask.
            config_id (str): Configuration ID for the chat request.
        """
        log.info("Performing chat...")
        for index, row in tqdm(dataset.iterrows(), total=dataset.shape[0]):
            question = row[question_column_name]
            chat_answer = self._api_request_manager.chat(
                query=question,
                config_id=config_id
            )

            response_json = chat_answer.json()
            dataset.loc[index, _CHAT_RESPONSE_KEY] = response_json["answer"]
            dataset.loc[index, _SEARCH_RESPONSE_KEY] = json.dumps([doc['page_content'] for doc in response_json["sources"]])


    def _evaluate_chat(
        self,
        dataset: pd.DataFrame,
        expected_answer_column_name: str,
        question_column_name: str
    ):
        """
        Evaluates chat responses against expected answers using GPT metrics.

        Args:
            dataset (pd.DataFrame): DataFrame containing the dataset to evaluate.
            expected_answer_column_name (str): Column name for expected answers.
            question_column_name (str): Column name for questions asked.
        """
        log.info("Evaluating chat...")
        for index, row in tqdm(dataset.iterrows(), total=dataset.shape[0]):
            expected_answer = row[expected_answer_column_name]
            chat_response = row[_CHAT_RESPONSE_KEY]

            score = self._gpt_evaluator.evaluate(
                prediction=chat_response,
                reference=expected_answer,
                input=row[question_column_name]
            )

            dataset.loc[index, _GPT_SCORE_COLUMN_NAME] = score


    def run(
        self,
        dataset_path: str,
        question_column_name: str,
        expected_answer_column_name: str,
        skip_ingest: bool
    ):
        """
        Executes the evaluation process for a dataset of questions and answers.
    
        Args:
            dataset_path (str): Directory containing the dataset files.
            question_column_name (str): Column name for questions.
            expected_answer_column_name (str): Column name for expected answers.
            skip_ingest (bool): Flag to skip raw document ingestion.
    
        Raises:
            FileNotFoundError: If required files or directories are missing.
        """
        experiment_id = str(uuid4())
        log.info(f"Starting experiment {experiment_id}...")

        ground_truth_dataset_path = os.path.join(dataset_path, DataFolderConfig.GROUND_TRUTH_DATASET_FILE_NAME)
        config_path = os.path.join(dataset_path, DataFolderConfig.CONFIG_FILE_NAME)
        raw_documents_path = os.path.join(dataset_path, DataFolderConfig.RAW_DOCUMENTS_FOLDER_NAME)

        # check if the paths exist
        if not os.path.exists(ground_truth_dataset_path):
            raise FileNotFoundError(f"Ground truth dataset not found at {ground_truth_dataset_path}")

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found at {config_path}")

        if not os.path.exists(raw_documents_path):
            raise FileNotFoundError(f"Raw documents folder not found at {raw_documents_path}")

        dataset = pd.read_csv(ground_truth_dataset_path)
        config: dict
        with open(config_path, "r") as f:
            config = json.load(f)

        self._setup_environment(config, raw_documents_path, skip_ingest)
        config_id = config["id"]

        self._perform_chat(dataset, question_column_name, config_id)

        # evaluating
        self._evaluate_chat(dataset,expected_answer_column_name, question_column_name)

        dataset_name = pathlib.PurePath(dataset_path).name
        output_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "output",
            "evaluation_results",
            dataset_name,
            experiment_id
        )

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "results.csv")
        config_path = os.path.join(output_dir, "config.json")

        dataset.to_csv(output_path)
        with open(config_path, "w") as f:
            json.dump(config, f)
