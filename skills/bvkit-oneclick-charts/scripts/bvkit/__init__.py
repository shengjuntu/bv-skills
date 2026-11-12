"""bvkit — 20 章可视化方法的一键执行层。

用法:
    python -m bvkit list
    python -m bvkit inspect 02
    python -m bvkit review --spec spec.json
    python -m bvkit render --spec spec.json
    python -m bvkit selftest --workdir /tmp/bvkit_selftest
"""
from .core import VERSION  # noqa: F401
