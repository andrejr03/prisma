"""Configuration loading for Prisma."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "defaults.toml"


@dataclass(frozen=True)
class PathSettings:
    runtime_state: str
    corpus_path: str
    index_path: str
    manifest_path: str


@dataclass(frozen=True)
class RetrievalSettings:
    chunk_size_chars: int
    chunk_overlap_chars: int


@dataclass(frozen=True)
class EmbeddingSettings:
    backend: str
    dimensions: int
    model_id: str


@dataclass(frozen=True)
class VectorIndexSettings:
    backend: str
    collection_name: str
    distance: str


@dataclass(frozen=True)
class ApiSettings:
    host: str
    port: int


@dataclass(frozen=True)
class RagSettings:
    default_top_k: int
    max_top_k: int
    min_score: float
    min_question_chars: int
    max_question_chars: int
    max_context_chars: int
    max_context_chars_hard_limit: int
    max_answer_sentences: int


@dataclass(frozen=True)
class GenerationSettings:
    backend: str
    model_id: str
    prompt_path: str


@dataclass(frozen=True)
class WorkflowSettings:
    enabled: bool
    max_retrieval_attempts: int
    min_context_score: float
    enable_query_rewrite: bool
    require_context_token_overlap: bool


@dataclass(frozen=True)
class EvalSettings:
    golden_path: str
    scorecard_path: str
    baseline_path: str
    minimum_pass_rate: float


@dataclass(frozen=True)
class PromptRegressionSettings:
    baseline_path: str
    baseline_prompt_snapshot_path: str
    report_path: str


@dataclass(frozen=True)
class PrismaSettings:
    repo_root: Path
    paths: PathSettings
    retrieval: RetrievalSettings
    embeddings: EmbeddingSettings
    vector_index: VectorIndexSettings
    api: ApiSettings
    rag: RagSettings
    generation: GenerationSettings
    workflow: WorkflowSettings
    evals: EvalSettings
    prompt_regression: PromptRegressionSettings

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.repo_root / path

    @property
    def corpus_path(self) -> Path:
        return self.resolve_path(self.paths.corpus_path)

    @property
    def index_path(self) -> Path:
        return self.resolve_path(self.paths.index_path)

    @property
    def manifest_path(self) -> Path:
        return self.resolve_path(self.paths.manifest_path)

    @property
    def prompt_path(self) -> Path:
        return self.resolve_path(self.generation.prompt_path)

    @property
    def eval_golden_path(self) -> Path:
        return self.resolve_path(self.evals.golden_path)

    @property
    def eval_scorecard_path(self) -> Path:
        return self.resolve_path(self.evals.scorecard_path)

    @property
    def eval_baseline_path(self) -> Path:
        return self.resolve_path(self.evals.baseline_path)

    @property
    def prompt_regression_baseline_path(self) -> Path:
        return self.resolve_path(self.prompt_regression.baseline_path)

    @property
    def prompt_regression_snapshot_path(self) -> Path:
        return self.resolve_path(self.prompt_regression.baseline_prompt_snapshot_path)

    @property
    def prompt_regression_report_path(self) -> Path:
        return self.resolve_path(self.prompt_regression.report_path)

    def with_overrides(
        self,
        *,
        corpus_path: str | None = None,
        index_path: str | None = None,
        manifest_path: str | None = None,
    ) -> PrismaSettings:
        return replace(
            self,
            paths=replace(
                self.paths,
                corpus_path=corpus_path or self.paths.corpus_path,
                index_path=index_path or self.paths.index_path,
                manifest_path=manifest_path or self.paths.manifest_path,
            ),
        )


def load_settings(config_path: Path | str = DEFAULT_CONFIG_PATH) -> PrismaSettings:
    path = Path(config_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    data = tomllib.loads(path.read_text(encoding="utf-8"))

    paths = _section(data, "paths")
    retrieval = _section(data, "retrieval")
    embeddings = _section(data, "embeddings")
    vector_index = _section(data, "vector_index")
    api = _section(data, "api")
    rag = _section(data, "rag")
    generation = _section(data, "generation")
    workflow = _section(data, "workflow")
    evals = _section(data, "evals")
    prompt_regression = _section(data, "prompt_regression")

    workflow_settings = WorkflowSettings(
        enabled=_get_bool(workflow, "enabled"),
        max_retrieval_attempts=_get_int(workflow, "max_retrieval_attempts"),
        min_context_score=_get_float(workflow, "min_context_score"),
        enable_query_rewrite=_get_bool(workflow, "enable_query_rewrite"),
        require_context_token_overlap=_get_bool(workflow, "require_context_token_overlap"),
    )
    if workflow_settings.max_retrieval_attempts != 2:
        raise ValueError("Phase 3 workflow max_retrieval_attempts must be exactly 2")

    eval_settings = EvalSettings(
        golden_path=_get_str(evals, "golden_path"),
        scorecard_path=_get_str(evals, "scorecard_path"),
        baseline_path=_get_str(evals, "baseline_path"),
        minimum_pass_rate=_get_float(evals, "minimum_pass_rate"),
    )
    if not 0.0 <= eval_settings.minimum_pass_rate <= 1.0:
        raise ValueError("Evaluation minimum_pass_rate must be between 0.0 and 1.0")

    prompt_regression_settings = PromptRegressionSettings(
        baseline_path=_get_str(prompt_regression, "baseline_path"),
        baseline_prompt_snapshot_path=_get_str(
            prompt_regression,
            "baseline_prompt_snapshot_path",
        ),
        report_path=_get_str(prompt_regression, "report_path"),
    )

    return PrismaSettings(
        repo_root=PROJECT_ROOT,
        paths=PathSettings(
            runtime_state=_get_str(paths, "runtime_state"),
            corpus_path=_get_str(paths, "corpus_path"),
            index_path=_get_str(paths, "index_path"),
            manifest_path=_get_str(paths, "manifest_path"),
        ),
        retrieval=RetrievalSettings(
            chunk_size_chars=_get_int(retrieval, "chunk_size_chars"),
            chunk_overlap_chars=_get_int(retrieval, "chunk_overlap_chars"),
        ),
        embeddings=EmbeddingSettings(
            backend=_get_str(embeddings, "backend"),
            dimensions=_get_int(embeddings, "dimensions"),
            model_id=_get_str(embeddings, "model_id"),
        ),
        vector_index=VectorIndexSettings(
            backend=_get_str(vector_index, "backend"),
            collection_name=_get_str(vector_index, "collection_name"),
            distance=_get_str(vector_index, "distance"),
        ),
        api=ApiSettings(
            host=_get_str(api, "host"),
            port=_get_int(api, "port"),
        ),
        rag=RagSettings(
            default_top_k=_get_int(rag, "default_top_k"),
            max_top_k=_get_int(rag, "max_top_k"),
            min_score=_get_float(rag, "min_score"),
            min_question_chars=_get_int(rag, "min_question_chars"),
            max_question_chars=_get_int(rag, "max_question_chars"),
            max_context_chars=_get_int(rag, "max_context_chars"),
            max_context_chars_hard_limit=_get_int(rag, "max_context_chars_hard_limit"),
            max_answer_sentences=_get_int(rag, "max_answer_sentences"),
        ),
        generation=GenerationSettings(
            backend=_get_str(generation, "backend"),
            model_id=_get_str(generation, "model_id"),
            prompt_path=_get_str(generation, "prompt_path"),
        ),
        workflow=workflow_settings,
        evals=eval_settings,
        prompt_regression=prompt_regression_settings,
    )


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"Missing [{name}] configuration section")
    return value


def _get_str(section: dict[str, Any], key: str) -> str:
    value = section.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string config value for {key}")
    return value


def _get_int(section: dict[str, Any], key: str) -> int:
    value = section.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Expected integer config value for {key}")
    return value


def _get_float(section: dict[str, Any], key: str) -> float:
    value = section.get(key)
    if not isinstance(value, int | float):
        raise ValueError(f"Expected numeric config value for {key}")
    return float(value)


def _get_bool(section: dict[str, Any], key: str) -> bool:
    value = section.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Expected boolean config value for {key}")
    return value
