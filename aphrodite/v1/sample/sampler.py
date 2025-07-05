"""A layer that samples the next tokens from the model's outputs."""

import torch
import torch.nn as nn
from loguru import logger

from aphrodite.v1.outputs import LogprobsTensors, SamplerOutput
from aphrodite.v1.sample.metadata import SamplingMetadata
from aphrodite.v1.sample.ops import SamplingOps
from aphrodite.v1.sample.ops.temperatures import apply_all_temperatures
from aphrodite.v1.sample.ops.topk_topp_sampler import TopKTopPSampler

_SAMPLING_EPS = 1e-5


class Sampler(nn.Module):

    def __init__(self):
        super().__init__()
        self.topk_topp_sampler = TopKTopPSampler()
        self.sampling_ops = SamplingOps()

    def forward(
        self,
        logits: torch.Tensor,
        sampling_metadata: SamplingMetadata,
    ) -> SamplerOutput:
        # NOTE: Use the original logits (before any penalties or
        # temperature scaling) for the top-k logprobs.
        # This is different from the V0 sampler, which uses the logits that
        # is used for sampling (after penalties and temperature scaling).
        # TODO: provide option for logprobs post sampling.
        num_logprobs = sampling_metadata.max_num_logprobs
        if num_logprobs is not None:
            raw_logprobs = self.compute_logprobs(logits)

        # Use float32 for the logits.
        logits = logits.to(torch.float32)
        # Apply allowed token ids.
        logits = self.sampling_ops.apply_allowed_token_ids(
            logits, sampling_metadata)
        # Apply bad words exclusion.
        logits = self.sampling_ops.apply_bad_words(logits, sampling_metadata)
        # Apply logits bias.
        logits = self.sampling_ops.apply_logits_bias(logits, sampling_metadata)
        # Apply no repeat ngram.
        logits = self.sampling_ops.apply_no_repeat_ngram(
            logits, sampling_metadata)
        # Apply penalties (e.g., min_tokens, freq_penalties).
        logits = self.sampling_ops.apply_penalties(logits, sampling_metadata)
        # Apply DRY sampling.
        logits = self.sampling_ops.apply_dry(logits, sampling_metadata)
        # Sample the next token.
        sampled = self.sample(logits, sampling_metadata)
        # Convert sampled token ids to int64 (long) type to ensure compatibility
        # with subsequent operations that may use these values as indices.
        # This conversion is necessary because FlashInfer sampling operations
        # return int32 (while PyTorch argmax and topk return int64).
        sampled = sampled.long()

        # Gather the logprobs of the topk and sampled token (if requested).
        # Get logprobs and rank tensors (if requested)
        logprobs_tensors = None if num_logprobs is None else \
            self.gather_logprobs(raw_logprobs, num_logprobs, token_ids=sampled)

        # Use int32 to reduce the tensor size.
        sampled = sampled.to(torch.int32)

        # These are GPU tensors.
        sampler_output = SamplerOutput(
            # The sampled tokens are expanded to 2D tensor with shape
            # [num_requests, 1], where each row represents one generated
            # token per request.
            sampled_token_ids=sampled.unsqueeze(-1),
            logprobs_tensors=logprobs_tensors,
        )
        return sampler_output

    def apply_temperature(
        self,
        logits: torch.Tensor,
        sampling_metadata: SamplingMetadata,
    ) -> torch.Tensor:
        return apply_all_temperatures(logits, sampling_metadata)

    def greedy_sample(self, logits: torch.Tensor) -> torch.Tensor:
        return logits.argmax(dim=-1).view(-1)

    def sample(
        self,
        logits: torch.Tensor,
        sampling_metadata: SamplingMetadata,
    ) -> torch.Tensor:
        """Sample logits based on sampling metadata.

        The various logits processing functions called in this method
        may update the logits tensor in-place.
        """

        assert not (sampling_metadata.all_greedy
                    and sampling_metadata.all_random)
        if sampling_metadata.all_random:
            greedy_sampled = None
        else:
            greedy_sampled = self.greedy_sample(logits)
            if sampling_metadata.all_greedy:
                return greedy_sampled

        assert sampling_metadata.temperature is not None

        # Apply temperature.
        logits = self.apply_temperature(
            logits, sampling_metadata)

        # Apply min_p.
        if sampling_metadata.min_p is not None:
            logger.debug("Applying min_p={}", sampling_metadata.min_p)
            logits = self.sampling_ops.apply_min_p(
                logits, sampling_metadata)

        # Apply top_a.
        if sampling_metadata.top_a is not None:
            logger.debug("Applying top_a={}", sampling_metadata.top_a)
            logits = self.sampling_ops.apply_top_a(
                logits, sampling_metadata)

        # Apply tfs.
        if sampling_metadata.tfs is not None:
            logger.debug("Applying tfs={}", sampling_metadata.tfs)
            logits = self.sampling_ops.apply_tfs(
                logits, sampling_metadata)

        # Apply eta cutoff.
        if sampling_metadata.eta_cutoff is not None:
            logger.debug("Applying eta_cutoff={}",
                          sampling_metadata.eta_cutoff)
            logits = self.sampling_ops.apply_eta_cutoff(
                logits, sampling_metadata)

        # Apply epsilon cutoff.
        if sampling_metadata.epsilon_cutoff is not None:
            logger.debug("Applying epsilon_cutoff={}",
                         sampling_metadata.epsilon_cutoff)
            logits = self.sampling_ops.apply_epsilon_cutoff(
                logits, sampling_metadata)

        # Apply typical p.
        if sampling_metadata.typical_p is not None:
            logger.debug("Applying typical_p={}", sampling_metadata.typical_p)
            logits = self.sampling_ops.apply_typical_p(
                logits, sampling_metadata)

        # Apply quadratic.
        if sampling_metadata.quadratic_smoothing_factor is not None:
            logger.debug("Applying quadratic_smoothing_factor={}",
                         sampling_metadata.quadratic_smoothing_factor)
            logits = self.sampling_ops.apply_quadratic(
                logits, sampling_metadata)

        # Apply xtc.
        if sampling_metadata.xtc_threshold is not None:
            logger.debug("Applying xtc_threshold={}",
                         sampling_metadata.xtc_threshold)
            logits = self.sampling_ops.apply_xtc(
                logits, sampling_metadata)

        # Apply top_nsigma.
        if sampling_metadata.top_nsigma is not None:
            logger.debug("Applying top_nsigma={}", sampling_metadata.top_nsigma)
            logits = self.sampling_ops.apply_top_nsigma(
                logits, sampling_metadata)

        # Apply top_k and/or top_p.
        random_sampled = self.topk_topp_sampler(
            logits,
            sampling_metadata.generators,
            sampling_metadata.top_k,
            sampling_metadata.top_p,
        )

        # Apply skew (after softmax).
        if sampling_metadata.skew is not None:
            logger.debug("Applying skew={}", sampling_metadata.skew)
            # Convert logits back to probabilities for skew
            probs = logits.softmax(dim=-1, dtype=torch.float32)
            probs = self.sampling_ops.apply_skew(probs, sampling_metadata)
            # Convert back to logits
            logits = torch.log(probs)

        if greedy_sampled is None:
            return random_sampled

        sampled = torch.where(
            sampling_metadata.temperature < _SAMPLING_EPS,
            greedy_sampled,
            random_sampled,
            out=greedy_sampled,  # Reuse tensor
        )
        return sampled

    def compute_logprobs(self, logits: torch.Tensor) -> torch.Tensor:
        return logits.log_softmax(dim=-1, dtype=torch.float32)

    def gather_logprobs(
        self,
        logprobs: torch.Tensor,
        num_logprobs: int,
        token_ids: torch.Tensor,
    ) -> LogprobsTensors:
        """
        Gather logprobs for topk and sampled/prompt token.

        Args:
          logprobs: (num tokens) x (vocab) tensor
          num_logprobs: minimum number of logprobs to
                        retain per token
          token_ids: prompt tokens (if prompt logprobs)
                     or sampled tokens (if sampled
                     logprobs); 1D token ID tensor
                     with (num tokens) elements
                     Must be int64.

        Returns:
          Top-k int indices tensor, (num tokens) x (num_logprobs + 1)
          Top-k float logprobs tensor, (num tokens) x (num_logprobs + 1)
          Sampled token rank tensor, (num tokens)
        """
        assert token_ids.dtype == torch.int64
        # Find the topK values.
        topk_logprobs, topk_indices = torch.topk(logprobs,
                                                 num_logprobs,
                                                 dim=-1)

        # Get with the logprob of the prompt or sampled token.
        token_ids = token_ids.unsqueeze(-1)
        token_logprobs = logprobs.gather(-1, token_ids)

        # Compute the ranks of the actual token.
        token_ranks = (logprobs >= token_logprobs).sum(-1)

        # Concatenate together with the topk.
        indices = torch.cat((token_ids, topk_indices), dim=1)
        logprobs = torch.cat((token_logprobs, topk_logprobs), dim=1)

        # Use int32 to reduce the tensor size.
        indices = indices.to(torch.int32)

        return LogprobsTensors(indices, logprobs, token_ranks)
