# Copyright 2024-2025 The Alibaba Wan Team Authors. All rights reserved.
from . import configs, distributed, modules

_PIPELINES = {
    "WanI2V": ".image2video",
    "WanS2V": ".speech2video",
    "WanT2V": ".text2video",
    "WanTI2V": ".textimage2video",
    "WanAnimate": ".animate",
}

__all__ = ["configs", "distributed", "modules", *_PIPELINES]


def __getattr__(name):
    if name not in _PIPELINES:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib import import_module

    value = getattr(import_module(_PIPELINES[name], __name__), name)
    globals()[name] = value
    return value
