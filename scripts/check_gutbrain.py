from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from curated_microbiota_gut_brain_axis.collections import gutbrain


if __name__ == "__main__":
    print(json.dumps(gutbrain.validate(), indent=2, sort_keys=True))
