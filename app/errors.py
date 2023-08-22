from enum import Enum


class ServiceError(Enum):
    FAILED_TO_CREATE_EXPERIMENT = "failed_to_create_experiment"
    FAILED_TO_TRACK_EXPOSURE = "failed_to_track_exposure"
    EXPERIMENT_KEY_ALREADY_EXISTS = "experiment_key_already_exists"
    FAILED_TO_FETCH_EXPERIMENTS = "failed_to_fetch_experiments"
