class RagConstants(object):
    DEFAULT_PROMPT_TEMPLATE = (
        "Answer the question based only on the following context:\n\n"
        "{context}\n\n"
        "Question: {question}"
    )
    DEFAULT_AZURE_DEPLOYMENT = "gpt-35-turbo"
    DEFAULT_SEARCH_TYPE = "hybrid"
    DEFAULT_SEARCH_K = 10
