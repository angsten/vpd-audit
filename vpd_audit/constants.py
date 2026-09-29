"""Fixed sizes shared by the harness."""

SEQ_LEN = 512  # T: every batch is (B, 512); per-position arrays have length 512
RAW_ROW_LEN = 513  # rows of the stream are 513 ids, truncated to the first 512
IMPORTANCE_CHUNK = 32  # g is computed in chunks of exactly 32 sequences
KL_CHUNK = 8  # the float32 divergence runs in sub-chunks of 8 sequences
ALIVE_THRESHOLD = 1e-6  # a subcomponent is alive if its mean g over data exceeds this (paper)
PERMITTED_TOL = 1e-6  # P3: min(m - g) >= -PERMITTED_TOL for permitted families
