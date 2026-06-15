# Copyright 2024-2025 The Alibaba Wan Team Authors. All rights reserved.
import torch

try:
    import flash_attn_interface
    FLASH_ATTN_3_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    FLASH_ATTN_3_AVAILABLE = False

try:
    import flash_attn
    FLASH_ATTN_2_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    FLASH_ATTN_2_AVAILABLE = False

import warnings

__all__ = [
    'flash_attention',
    'attention',
]

_ATTENTION_BACKEND_REPORTED = False


def _report_attention_backend(backend):
    global _ATTENTION_BACKEND_REPORTED
    if _ATTENTION_BACKEND_REPORTED:
        return
    print(f"[Wan attention] using {backend}", flush=True)
    _ATTENTION_BACKEND_REPORTED = True


def _torch_attention_fallback(q,
                              k,
                              v,
                              q_lens=None,
                              k_lens=None,
                              dropout_p=0.,
                              softmax_scale=None,
                              q_scale=None,
                              causal=False,
                              window_size=(-1, -1),
                              dtype=torch.bfloat16):
    half_dtypes = (torch.float16, torch.bfloat16)
    b, lq, lk, out_dtype = q.size(0), q.size(1), k.size(1), q.dtype

    if window_size != (-1, -1):
        warnings.warn(
            'Sliding window attention is disabled when using scaled_dot_product_attention fallback.'
        )

    q = q.to(dtype if q.dtype not in half_dtypes else q.dtype)
    k = k.to(dtype if k.dtype not in half_dtypes else k.dtype)
    v = v.to(dtype if v.dtype not in half_dtypes else v.dtype)

    q = q.to(v.dtype)
    k = k.to(v.dtype)

    if q_scale is not None:
        q = q * q_scale

    if q.size(2) != k.size(2):
        assert q.size(2) % k.size(2) == 0
        repeat = q.size(2) // k.size(2)
        k = k.repeat_interleave(repeat, dim=2)
        v = v.repeat_interleave(repeat, dim=2)

    if q_lens is None:
        q_lens = torch.full((b, ), lq, dtype=torch.long, device=q.device)
    if k_lens is None:
        k_lens = torch.full((b, ), lk, dtype=torch.long, device=k.device)

    outputs = []
    for i in range(b):
        q_len = int(q_lens[i])
        k_len = int(k_lens[i])

        qi = q[i:i + 1, :q_len].transpose(1, 2)
        ki = k[i:i + 1, :k_len].transpose(1, 2)
        vi = v[i:i + 1, :k_len].transpose(1, 2)

        out = torch.nn.functional.scaled_dot_product_attention(
            qi,
            ki,
            vi,
            attn_mask=None,
            dropout_p=dropout_p,
            is_causal=causal,
            scale=softmax_scale).transpose(1, 2)

        if q_len < lq:
            out = torch.cat(
                [out, out.new_zeros(1, lq - q_len, out.size(2), out.size(3))],
                dim=1)
        outputs.append(out)

    return torch.cat(outputs, dim=0).type(out_dtype)


def flash_attention(
    q,
    k,
    v,
    q_lens=None,
    k_lens=None,
    dropout_p=0.,
    softmax_scale=None,
    q_scale=None,
    causal=False,
    window_size=(-1, -1),
    deterministic=False,
    dtype=torch.bfloat16,
    version=None,
):
    """
    q:              [B, Lq, Nq, C1].
    k:              [B, Lk, Nk, C1].
    v:              [B, Lk, Nk, C2]. Nq must be divisible by Nk.
    q_lens:         [B].
    k_lens:         [B].
    dropout_p:      float. Dropout probability.
    softmax_scale:  float. The scaling of QK^T before applying softmax.
    causal:         bool. Whether to apply causal attention mask.
    window_size:    (left right). If not (-1, -1), apply sliding window local attention.
    deterministic:  bool. If True, slightly slower and uses more memory.
    dtype:          torch.dtype. Apply when dtype of q/k/v is not float16/bfloat16.
    """
    half_dtypes = (torch.float16, torch.bfloat16)
    assert dtype in half_dtypes
    assert q.device.type == 'cuda' and q.size(-1) <= 256

    # params
    b, lq, lk, out_dtype = q.size(0), q.size(1), k.size(1), q.dtype

    if not (FLASH_ATTN_2_AVAILABLE or FLASH_ATTN_3_AVAILABLE):
        _report_attention_backend("PyTorch SDPA fallback")
        return _torch_attention_fallback(
            q=q,
            k=k,
            v=v,
            q_lens=q_lens,
            k_lens=k_lens,
            dropout_p=dropout_p,
            softmax_scale=softmax_scale,
            q_scale=q_scale,
            causal=causal,
            window_size=window_size,
            dtype=dtype)

    def half(x):
        return x if x.dtype in half_dtypes else x.to(dtype)

    # preprocess query
    if q_lens is None:
        q = half(q.flatten(0, 1))
        q_lens = torch.tensor(
            [lq] * b, dtype=torch.int32).to(
                device=q.device, non_blocking=True)
    else:
        q = half(torch.cat([u[:v] for u, v in zip(q, q_lens)]))

    # preprocess key, value
    if k_lens is None:
        k = half(k.flatten(0, 1))
        v = half(v.flatten(0, 1))
        k_lens = torch.tensor(
            [lk] * b, dtype=torch.int32).to(
                device=k.device, non_blocking=True)
    else:
        k = half(torch.cat([u[:v] for u, v in zip(k, k_lens)]))
        v = half(torch.cat([u[:v] for u, v in zip(v, k_lens)]))

    q = q.to(v.dtype)
    k = k.to(v.dtype)

    if q_scale is not None:
        q = q * q_scale

    if version is not None and version == 3 and not FLASH_ATTN_3_AVAILABLE:
        warnings.warn(
            'Flash attention 3 is not available, use flash attention 2 instead.'
        )

    # apply attention
    if (version is None or version == 3) and FLASH_ATTN_3_AVAILABLE:
        _report_attention_backend("flash-attn 3")
        # Note: dropout_p, window_size are not supported in FA3 now.
        x = flash_attn_interface.flash_attn_varlen_func(
            q=q,
            k=k,
            v=v,
            cu_seqlens_q=torch.cat([q_lens.new_zeros([1]), q_lens]).cumsum(
                0, dtype=torch.int32).to(q.device, non_blocking=True),
            cu_seqlens_k=torch.cat([k_lens.new_zeros([1]), k_lens]).cumsum(
                0, dtype=torch.int32).to(q.device, non_blocking=True),
            seqused_q=None,
            seqused_k=None,
            max_seqlen_q=lq,
            max_seqlen_k=lk,
            softmax_scale=softmax_scale,
                causal=causal,
                deterministic=deterministic)[0].unflatten(0, (b, lq))
    else:
        assert FLASH_ATTN_2_AVAILABLE
        _report_attention_backend("flash-attn 2")
        x = flash_attn.flash_attn_varlen_func(
            q=q,
            k=k,
            v=v,
            cu_seqlens_q=torch.cat([q_lens.new_zeros([1]), q_lens]).cumsum(
                0, dtype=torch.int32).to(q.device, non_blocking=True),
            cu_seqlens_k=torch.cat([k_lens.new_zeros([1]), k_lens]).cumsum(
                0, dtype=torch.int32).to(q.device, non_blocking=True),
            max_seqlen_q=lq,
            max_seqlen_k=lk,
            dropout_p=dropout_p,
            softmax_scale=softmax_scale,
            causal=causal,
            window_size=window_size,
            deterministic=deterministic).unflatten(0, (b, lq))

    # output
    return x.type(out_dtype)


def attention(
    q,
    k,
    v,
    q_lens=None,
    k_lens=None,
    dropout_p=0.,
    softmax_scale=None,
    q_scale=None,
    causal=False,
    window_size=(-1, -1),
    deterministic=False,
    dtype=torch.bfloat16,
    fa_version=None,
):
    return flash_attention(
        q=q,
        k=k,
        v=v,
        q_lens=q_lens,
        k_lens=k_lens,
        dropout_p=dropout_p,
        softmax_scale=softmax_scale,
        q_scale=q_scale,
        causal=causal,
        window_size=window_size,
        deterministic=deterministic,
        dtype=dtype,
        version=fa_version,
    )
