"""
Evidence state and the temporal information firewall.

Every EvidenceItem carries a provenance tag and two dates:
- date_observed: when the underlying geological event/measurement occurred
- date_available: when that information was actually available to a decision
  maker (may be later than date_observed due to assay turnaround, reporting
  lag, confidentiality, etc.)

The firewall is enforced structurally: EvidenceStore.as_of(t) is the ONLY
supported read path. Nothing downstream should ever iterate store._items
directly.
"""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Optional


class ProvenanceTag(str, Enum):
    FACT = "FACT"                # documented historical fact, cited source
    ASSUMPTION = "ASSUMPTION"    # modeling choice, not a historical fact
    SYNTHETIC = "SYNTHETIC"      # fabricated for testing only, never historical


class EvidenceKind(str, Enum):
    DRILL_HOLE = "drill_hole"
    ASSAY = "assay"
    GEOLOGICAL_OBSERVATION = "geological_observation"
    GEOPHYSICAL_OBSERVATION = "geophysical_observation"
    GEOCHEMICAL_OBSERVATION = "geochemical_observation"
    SPATIAL_INFO = "spatial_info"
    HISTORICAL_INTERPRETATION = "historical_interpretation"
    ECONOMIC_EVENT = "economic_event"


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    kind: EvidenceKind
    description: str
    date_observed: date
    date_available: date
    source: str
    provenance: ProvenanceTag
    confidence: float  # analyst-assigned confidence in [0,1], NOT a probability of a hypothesis
    values: dict[str, Any] = field(default_factory=dict)
    spatial_ref: Optional[str] = None

    def __post_init__(self):
        if self.date_available < self.date_observed:
            raise ValueError(
                f"Evidence {self.id}: date_available cannot precede date_observed"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Evidence {self.id}: confidence must be in [0,1]")


class EvidenceStore:
    def __init__(self, items: Optional[list[EvidenceItem]] = None):
        self._items: list[EvidenceItem] = list(items or [])

    def add(self, item: EvidenceItem) -> None:
        self._items.append(item)

    def as_of(self, t: date) -> list[EvidenceItem]:
        """THE TEMPORAL FIREWALL.

        Returns only evidence whose date_available <= t. This is the sole
        sanctioned way to read evidence for use in a historical decision at
        time t. Any evidence dated after t (drilling results, resource
        estimates, later interpretations, production data) is invisible to
        the caller.
        """
        return sorted(
            (it for it in self._items if it.date_available <= t),
            key=lambda it: (it.date_available, it.id),
        )

    def all_items_UNSAFE_FOR_EVALUATION_ONLY(self) -> list[EvidenceItem]:
        """Full, unfiltered evidence set. Name is intentionally loud.

        This must ONLY be called by the Evaluation Engine, after a historical
        decision has already been generated via as_of(), to score outcomes
        against later-revealed information. It must never be called by the
        belief, information-value, economic, or decision modules.
        """
        return sorted(self._items, key=lambda it: (it.date_available, it.id))

    def __len__(self) -> int:
        return len(self._items)
