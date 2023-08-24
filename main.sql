CREATE TABLE experiments (
    rec_id SERIAL PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    name TEXT NOT NULL,
    key TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NULL,
    hypothesis JSONB NOT NULL,
    exposure_event TEXT NULL,
    variants JSONB NOT NULL,
    variant_allocation JSONB NOT NULL,
    -- user_segments JSONB NOT NULL,
    bucketing_salt TEXT NOT NULL,
    -- TODO: add support for these to the application
    -- sticky_bucketing BOOLEAN NOT NULL,
    -- evaluation_mode TEXT NOT NULL,
    -- mutual_exclusion_groups JSONB NOT NULL,
    -- holdout_groups JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX experiments_experiment_id_idx ON experiments (experiment_id);
CREATE UNIQUE INDEX experiments_key_idx ON experiments (key);
CREATE INDEX experiments_exposure_event_idx ON experiments (exposure_event);

CREATE TABLE exposures (
    rec_id SERIAL PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    variant TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX exposures_experiment_id_user_id_idx ON exposures (experiment_id, user_id);
CREATE INDEX exposures_experiment_id_idx ON exposures (experiment_id);
CREATE INDEX exposures_user_id_idx ON exposures (user_id);
CREATE INDEX exposures_variant_idx ON exposures (variant);
