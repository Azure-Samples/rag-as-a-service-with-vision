# RAG evaluation <!-- omit in toc -->

- [Evaluation process](#evaluation-process)
- [Available evaluation flows](#available-evaluation-flows)
  - [ROUGE evaluation](#rouge-evaluation)
  - [LLM-as-a-judge evaluation](#llm-as-a-judge-evaluation)
- [Outer-loop feedback](#outer-loop-feedback)
- [Additional resources](#additional-resources)

Now that we've designed and implemented the [system architecture](vision-rag-architecture.md) for a RAG pipeline that leverages both textual and image data sources, we want to have a process to run the pipeline and evaluate its performance on a given set of documents and associated groundtruth question-and-answer evaluation dataset.
This will enable iterative experimentation and fine-tuning of the pipeline to best meet the needs of end users.

Note that the evaluation process is inherently tied to the enterprise use case and groundtruth dataset.
The chosen metrics will depend on what brings most value to the decision-making process of developers and data scientists to meet user needs, which is in turn driven by the success criteria of the use case.
This repo only covers automated inner-loop evaluation;
it may also be worthwhile to incorporate [outer-loop evaluation](#outer-loop-feedback) to validate the performance of the RAG pipeline against actual end users.

The quality of the groundtruth dataset also directly impacts how informative evaluation metrics are -
we encourage working with subject-matter experts to curate a groundtruth dataset of question-and-answer pairs that is representative of the documents covered in your document store.

The evaluation service included in this repository (located in the `src/eval` directory) is intended as a starting point of a simple test harness to enable developers to run and evaluate the Vision RAG pipeline against a sample dataset, and it can be extended/adjusted to best meet the needs of your use case and datasets.

## Evaluation process

Recall the diagram presented for the inference workflow in our [architecture document](./vision-rag-architecture.md):

![Inference workflow](./assets/inference-flow.drawio.png)

The evaluation service acts as a user proxy in this case:
given a particular RAG pipeline configuration and set of MHTML documents, it iterates over every question in the specified groundtruth dataset, runs through the inference workflow to retrieve the LLM response to that query, and then records the results.
It then uses the resulting answers when running the evaluation flows to calculate metrics that quantify the performance of this particular pipeline configuration.

## Available evaluation flows

All evaluators described below inherit from the [`BaseEvaluator`](../src/eval/services/evaluators/base_evaluator.py) class.
Additional evaluation functionality can be added using the ROUGE and GPT evaluators as a guide.

### ROUGE evaluation

The [ROUGE evaluator](../src/eval/services/evaluators/rouge_evaluator.py) can be used to compute the ROUGE-L recall between the LLM-generated answer and the provided groundtruth answer.
It leverages the [`rouge-score`](https://pypi.org/project/rouge-score/) library to perform the calculation.

### LLM-as-a-judge evaluation

The [GPT evaluator](../src/eval/services/evaluators/gpt_evaluator.py) uses the LLM-as-a-judge technique to score the LLM-generated answer based on a provided scoring criteria.
It uses the [Langchain string scoring evaluator](https://python.langchain.com/v0.1/docs/guides/productionization/evaluation/string/scoring_eval_chain/) for this evaluation;
the scoring criteria can be updated as needed or extended to evaluate answers based on multiple criteria.

## Outer-loop feedback

The prior discussed evaluation methods all fall under the category of **inner-loop** feedback, which can be gathered quickly and automatically using the defined metrics and dataset.
Inner-loop feedback enables quick iteration and provides a shared understanding for the team of the current performance of the system.

**Outer-loop feedback**, in contrast, is aimed at understanding what end users think of the system -
it can be more time-consuming to set up processes to do so and collect that information, but it provides a valuable signal to gauge how effectively your system is actually meeting the needs of end users.

In an architecture like our Vision RAG pipeline, it can be extremely helpful to get user feedback from subject-matter experts (SMEs) to (1) validate the performance of the LLM for generating image descriptions and (2) gauge the quality of the final LLM response to the user query.
During our engagement, we developed two React-based web applications to quickly deploy and gather internal user feedback in a test environment -
this was intended to be a very light-weight process to quickly validate our processes and guide experimentation to best meet user needs.
The code isn't included in this repo, but we've included screenshots below of the simple interface and user inputs collected.
This design would need to be tuned to best suit your use case, but we hope it could be a helpful starting point for future work.

This feedback for (1), the image description component, helped to fine-tune the prompt used for generating image descriptions and guided further experimentation with formulating the context passed to the multimodal LLM for enrichment.

![image feedback tool](./assets/image-feedback-tool-screenshot.png)

For (2), the scoring of LLM-generated answers, we collected this information as a barometer for the overall system quality, as well as to see how well SME judgement aligned with our [GPT evaluator](#llm-as-a-judge-evaluation).

![answer feedback tool with dropdown](./assets/answer-feedback-tool-with-dropdown.png)

![answer feedback tool](./assets/answer-feedback-tool-screenshot.png)

## Additional resources

- [MSLearn playbook page: metrics for evaluating LLM-generated content](https://learn.microsoft.com/en-us/ai/playbook/technology-guidance/generative-ai/working-with-llms/evaluation/list-of-eval-metrics)
- [MSFT ISE RAG Experiment Accelerator docs re: evaluation](https://learn.microsoft.com/en-us/ai/playbook/solutions/generative-ai/rag-experiment-accelerator#evaluation) and their [evaluation metrics implementation](https://github.com/microsoft/rag-experiment-accelerator/blob/development/rag_experiment_accelerator/evaluation/eval.py)
