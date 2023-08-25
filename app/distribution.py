import hashlib

from app.models.experiments import Experiment


def normalize_value(value: str) -> float:
    # TODO: test flame improvements
    return int(hashlib.md5(value.encode("utf-8")).hexdigest(), 16) / 2**128


def get_user_variant(experiment: Experiment, user_id: str) -> str:
    identifier = f"{experiment.bucketing_salt}:{user_id}"
    normalized_value = normalize_value(identifier)

    cumulative_weight = 0.0
    for variant_name, weight in experiment.variant_allocation.items():
        cumulative_weight += weight
        if normalized_value < cumulative_weight:
            return variant_name

    raise ValueError("Bucket weights do not sum to 1.0")
