"""Reproducible individual draws, not population quotas or forced diversity."""

import math

from echo_swm.core.ids import stable_hash

RUNTIME = "bounded-choice-v2"


def sample_choice(probabilities, *, seed, agent_id, path, occasion):
    if not probabilities or any(
        not math.isfinite(p) or p < 0 or p > 1 for p in probabilities.values()
    ):
        raise ValueError("Invalid individual choice probabilities")
    total = sum(probabilities.values())
    tolerance = max(0.002, 0.005 * len(probabilities))
    if total <= 0 or abs(total - 1) > tolerance + 1e-9:
        raise ValueError("Individual choice probabilities must sum to one")
    # Sorted IDs make a draw invariant to provider JSON insertion order. Including
    # the occasion and path gives independent opportunities, but identical replay.
    draw = int(stable_hash([RUNTIME, seed, agent_id, path, occasion])[:16], 16) / 2**64
    cumulative = 0.0
    selected = sorted(probabilities)[-1]
    for key in sorted(probabilities):
        cumulative += probabilities[key] / total
        if draw < cumulative:
            selected = key
            break
    return selected, {
        "selection_method": "seeded_individual_distribution_v1",
        "draw": draw,
        "probability_sum": total,
        "selected_probability": probabilities[selected] / total,
        "modal_option_id": max(sorted(probabilities), key=probabilities.get),
        "probabilities": probabilities,
        "no_clear_preference": max(probabilities.values()) / total <= 1 / len(probabilities) + 0.05,
        "calibrated": False,
    }
