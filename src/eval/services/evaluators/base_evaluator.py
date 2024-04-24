import abc
from typing import TypeVar, Generic


T = TypeVar('T')

class BaseEvaluator(abc.ABC, Generic[T]):
    def evaluate(self, prediction: str | list[str], **kwrags) -> T:
        pass
