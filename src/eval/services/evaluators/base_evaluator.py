import abc
from typing import TypeVar, Generic


T = TypeVar('T')

class BaseEvaluator(abc.ABC, Generic[T]):
    """
    Abstract base class for evaluators.

    Defines a generic interface for evaluation methods. Subclasses must implement 
    the evaluate method to assess predictions.

    Type Parameters:
        T: Result type of the evaluation.
    """
    def evaluate(self, prediction: str | list[str], **kwargs) -> T:
        pass
