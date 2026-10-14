from __future__ import annotations

from ._registry import gutbrain, studies
from .study import Study


def available(
    *,
    condition: str | None = None,
    assay: str | None = None,
    role: str | None = None,
    status: str | None = None,
    target: str | None = None,
    benchmark: bool | None = None,
    problem_type: str | None = None,
) -> tuple[Study, ...]:
    return tuple(
        study
        for study in studies
        if (condition is None or study.condition == condition)
        and (assay is None or study.assay == assay)
        and (role is None or study.role == role)
        and (status is None or study.status == status)
        and (target is None or target in study.targets() or target == "zung_depression")
        and (benchmark is None or benchmark)
        and (
            problem_type is None
            or (
                study.target(target).problem_type == problem_type
                if target is not None
                else any(study.target(name).problem_type == problem_type for name in study.targets())
            )
        )
    )


__all__ = ["available", "gutbrain"]
