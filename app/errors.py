from enum import Enum


class ServiceError(Enum):
    # TODO: some standardization might be a good idea
    EXPERIMENTS_CREATE_FAILED = "experiments.create_failed"
    EXPERIMENTS_FETCH_FAILED = "experiments.fetch_failed"
    EXPERIMENTS_NOT_FOUND = "experiments.not_found"
    EXPERIMENTS_UPDATE_FAILED = "experiments.update_failed"
    EXPERIMENTS_DELETE_FAILED = "experiments.delete_failed"

    EXPERIMENTS_NEEDS_HYPOTHESIS = "experiments.needs_hypothesis"
    EXPERIMENTS_NEEDS_EXPOSURE_EVENT = "experiments.needs_exposure_event"
    EXPERIMENTS_NEEDS_VARIANTS = "experiments.needs_variants"
    EXPERIMENTS_NEEDS_VARIANT_ALLOCATION = "experiments.needs_variant_allocation"
    EXPERIMENTS_NEEDS_BUCKETING_SALT = "experiments.needs_bucketing_salt"

    EXPERIMENTS_KEY_ALREADY_EXISTS = "experiments.key_already_exists"
    EXPERIMENTS_VARIANT_MISMATCH = "experiments.variant_mismatch"
    EXPERIMENTS_INVALID_VARIANT_ALLOCATION = "experiments.invalid_variant_allocation"

    EXPERIMENTS_INVALID_TRANSITION = "experiments.invalid_transition"

    EXPOSURES_TRACK_FAILED = "exposures.track_failed"
    EXPOSURE_ALREADY_EXISTS = "exposures.already_exists"
