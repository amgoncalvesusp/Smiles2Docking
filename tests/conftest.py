"""Pytest bootstrap.

Import torch before RDKit (see src/utils/torch_preimport) so MolGpKa-backed
tests do not hit the Windows ``shm.dll`` load-order failure.
"""

from __future__ import annotations

import src.utils.torch_preimport  # noqa: F401
