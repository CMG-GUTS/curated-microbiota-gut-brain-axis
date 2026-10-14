from __future__ import annotations

from pathlib import Path

from curated_microbiota_gut_brain_axis.collections import gutbrain
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor

from mllabiome import mll

HERE = Path(__file__).resolve().parent
TITLE = "GUTBRAIN microbiota + BrainHarmonix regression sweep"
EXPERIMENT_DIR = HERE / "runs" / "GUTBRAIN-MULTIMODAL-NCV"
TARGET = "Zung_S"
DATA = gutbrain.mllabiome(target=TARGET)
EVALUATION = gutbrain.splits(target=TARGET).mllabiome(optimize_metric="RMSE", n_jobs="auto")
TRANSFORMATIONS = (
    mll.Transformation("presence_absence"),
    mll.Transformation("identity"),
    mll.Transformation(
        "relative_abundance",
        composition_scope="joint",
        feature_filter=mll.PrevalenceFilter(threshold=0.05),
    ),
)
INTEGRATIONS = (
    mll.Integration("intermediate_joint_pca", n_components=(16, 32)),
    mll.Integration("late_super_learner"),
)
MODELS = (
    (
        "RF_500_msl5",
        RandomForestRegressor(
            n_estimators=500,
            min_samples_leaf=5,
            n_jobs=1,
            random_state=42,
        ),
    ),
    (
        "LGBM_SMALL",
        LGBMRegressor(
            n_estimators=1000,
            learning_rate=0.025,
            num_leaves=7,
            max_depth=3,
            min_child_samples=15,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.70,
            reg_alpha=0.10,
            reg_lambda=10.0,
            n_jobs=1,
            random_state=42,
            verbosity=-1,
        ),
    ),
)
GATE = mll.QualificationGate(enabled=False, metric="RMSE")
ENSEMBLE = mll.Ensemble(
    max_sizes=(3,),
    selection_strategies=(
        "top_k",
        "best_per_resolution",
        "best_per_learner_type",
        "caruana",
        "super_learner",
    ),
    aggregation_strategies=(
        "mean_prediction",
        "weighted_mean_prediction",
        "median_prediction",
    ),
    optimize_metric="RMSE",
)
EXPLAINABILITY = mll.Explainability(
    targets=("mpma_b",),
    profile="screening",
    methods=(
        mll.Permutation(),
        mll.SHAP(),
        mll.ALE(),
        mll.LIME(),
        mll.ALEInteractions(),
    ),
)
SWEEP = mll.Sweep(
    **DATA,
    experiment_dir=EXPERIMENT_DIR,
    title=TITLE,
    learners=MODELS,
    evaluation=EVALUATION,
    gate=GATE,
    ensemble=ENSEMBLE,
    explainability=EXPLAINABILITY,
    transformations=TRANSFORMATIONS,
    integrations=INTEGRATIONS,
)
