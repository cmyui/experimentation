from enum import Enum


class ServiceError(Enum):
    FAILED_TO_CREATE_EXPERIMENT = "failed_to_create_experiment"
    EXPERIMENT_KEY_ALREADY_EXISTS = "experiment_key_already_exists"
