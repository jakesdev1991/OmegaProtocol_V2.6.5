from typing import Protocol, runtime_checkable
import numpy as np

@runtime_checkable
class Objective(Protocol):
    def __call__(self, params: np.ndarray) -> float: ...