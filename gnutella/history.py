from dataclasses import dataclass
from typing import Optional

from .descripter import PayloadDescripter


@dataclass(eq=True, frozen=True)
class History:
    payload_descripter: PayloadDescripter
    id: int
    address: Optional[int]
