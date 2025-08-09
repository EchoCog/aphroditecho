"""Some utilities for logprobs, including logits."""

import torch

from aphrodite.platforms import current_platform


@torch.compile(dynamic=True, backend=current_platform.simple_compile_backend)
def batched_count_greater_than(x: torch.Tensor,
                               values: torch.Tensor) -> torch.Tensor:
    """
    Counts elements in each row of x that are greater than the corresponding
    value in values.  Use torch.compile to generate an optimized kernel for
    this function. otherwise, it will create additional copies of the input
    tensors and cause memory issues.

    Args:
        x (torch.Tensor): A 2D tensor of shape (batch_size, n_elements).
        values (torch.Tensor): A 2D tensor of shape (batch_size, 1).

    Returns:
        torch.Tensor: A 1D tensor of shape (batch_size,) with the counts.
    """
    return (x >= values).sum(-1)
