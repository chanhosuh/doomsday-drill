from __future__ import annotations

import os


DEFAULT_REFERENCE_URL = "https://en.wikipedia.org/wiki/Doomsday_rule"
REFERENCE_URL = os.environ.get("DOOMSDAY_REFERENCE_URL", DEFAULT_REFERENCE_URL)
EUREKA_CITATION = (
    "John Horton Conway, \"Tomorrow is the Day After Doomsday,\" "
    "Eureka 36, pp. 28-31, October 1973."
)
