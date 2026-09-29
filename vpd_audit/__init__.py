"""vpd_audit: the audit's harness around the authors' `param_decomp`.

`env` must be imported first: it sets `PARAM_DECOMP_OUT_DIR` and `HF_HOME` before any
module imports `param_decomp`, `datasets`, or `huggingface_hub`.
"""

from vpd_audit import env as env  # noqa: F401  (import for its side effects, first)
