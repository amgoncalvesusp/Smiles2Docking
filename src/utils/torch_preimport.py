"""Import torch before RDKit to avoid a Windows DLL clash.

MolGpKa (the default protonation backend) needs PyTorch. On Windows, loading
torch *after* RDKit/MKL intermittently fails with ``OSError: [WinError 127]``
while loading ``shm.dll`` (an OpenMP/MKL DLL ordering issue). Importing torch
first, at process start, keeps the load order deterministic.

Import this module before any RDKit import in every process entry point
(GUI, CLI, tests, frozen build). It is a no-op when torch is not installed, so
non-MolGpKa deployments are unaffected.
"""

from __future__ import annotations

import os

# torch bundles its own libiomp; conda ships MKL's. Allow both to coexist
# (OMP Error #15) instead of aborting.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

try:  # pragma: no cover - environment dependent
    import torch  # noqa: F401
except Exception:  # torch is optional unless the MolGpKa backend is used
    pass
