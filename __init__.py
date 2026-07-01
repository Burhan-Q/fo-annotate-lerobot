# __init__.py  (plugin entrypoint; relative import at FiftyOne runtime, absolute fallback for tooling)
try:
    from .lerobot_anno.operators import register
except ImportError:  # imported top-level (e.g. pytest collecting the repo root)
    from lerobot_anno.operators import register

__all__ = ["register"]
