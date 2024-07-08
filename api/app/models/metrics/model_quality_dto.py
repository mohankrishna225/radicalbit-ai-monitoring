from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.models.dataset_type import DatasetType
from app.models.exceptions import MetricsInternalError
from app.models.job_status import JobStatus
from app.models.model_dto import ModelType


class MetricsBase(BaseModel):
    f1: Optional[float] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f_measure: Optional[float] = None
    weighted_precision: Optional[float] = None
    weighted_recall: Optional[float] = None
    weighted_f_measure: Optional[float] = None
    weighted_true_positive_rate: Optional[float] = None
    weighted_false_positive_rate: Optional[float] = None
    true_positive_rate: Optional[float] = None
    false_positive_rate: Optional[float] = None
    area_under_roc: Optional[float] = None
    area_under_pr: Optional[float] = None

    model_config = ConfigDict(
        populate_by_name=True, alias_generator=to_camel, protected_namespaces=()
    )


class BinaryClassificationModelQuality(MetricsBase):
    true_positive_count: int
    false_positive_count: int
    true_negative_count: int
    false_negative_count: int


class Distribution(BaseModel):
    timestamp: str
    value: Optional[float] = None


class GroupedMetricsBase(BaseModel):
    f1: Optional[List[Distribution]] = None
    accuracy: Optional[List[Distribution]] = None
    precision: List[Distribution]
    recall: List[Distribution]
    f_measure: List[Distribution]
    weighted_precision: Optional[List[Distribution]] = None
    weighted_recall: Optional[List[Distribution]] = None
    weighted_f_measure: Optional[List[Distribution]] = None
    weighted_true_positive_rate: Optional[List[Distribution]] = None
    weighted_false_positive_rate: Optional[List[Distribution]] = None
    true_positive_rate: List[Distribution]
    false_positive_rate: List[Distribution]
    area_under_roc: Optional[List[Distribution]] = None
    area_under_pr: Optional[List[Distribution]] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class CurrentBinaryClassificationModelQuality(BaseModel):
    global_metrics: BinaryClassificationModelQuality
    grouped_metrics: GroupedMetricsBase

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class ClassMetrics(BaseModel):
    class_name: str
    metrics: MetricsBase
    grouped_metrics: Optional[GroupedMetricsBase] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class GlobalMetrics(MetricsBase):
    confusion_matrix: List[List[int]]

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class MultiClassificationModelQuality(BaseModel):
    classes: List[str]
    class_metrics: List[ClassMetrics]
    global_metrics: GlobalMetrics

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class RegressionMetricsBase(BaseModel):
    r2: Optional[float] = None
    mae: Optional[float] = None
    mse: Optional[float] = None
    variance: Optional[float] = None
    mape: Optional[float] = None
    rmse: Optional[float] = None
    adj_r2: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class BaseRegressionMetrics(BaseModel):
    r2: Optional[float] = None
    mae: Optional[float] = None
    mse: Optional[float] = None
    variance: Optional[float] = None
    mape: Optional[float] = None
    rmse: Optional[float] = None
    adj_r2: Optional[float] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class GroupedBaseRegressionMetrics(BaseModel):
    r2: List[Distribution]
    mae: List[Distribution]
    mse: List[Distribution]
    variance: List[Distribution]
    mape: List[Distribution]
    rmse: List[Distribution]
    adj_r2: List[Distribution]

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class RegressionModelQuality(BaseRegressionMetrics):
    pass


class CurrentRegressionModelQuality(BaseModel):
    global_metrics: BaseRegressionMetrics
    grouped_metrics: GroupedBaseRegressionMetrics

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class ModelQualityDTO(BaseModel):
    job_status: JobStatus
    model_quality: Optional[
        BinaryClassificationModelQuality
        | CurrentBinaryClassificationModelQuality
        | MultiClassificationModelQuality
        | RegressionModelQuality
        | CurrentRegressionModelQuality
    ]

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    @staticmethod
    def from_dict(
        dataset_type: DatasetType,
        model_type: ModelType,
        job_status: JobStatus,
        model_quality_data: Optional[Dict],
    ) -> 'ModelQualityDTO':
        """Create a ModelQualityDTO from a dictionary of data."""
        if not model_quality_data:
            return ModelQualityDTO(
                job_status=job_status,
                model_quality=None,
            )

        model_quality = ModelQualityDTO._create_model_quality(
            model_type=model_type,
            dataset_type=dataset_type,
            model_quality_data=model_quality_data,
        )

        return ModelQualityDTO(
            job_status=job_status,
            model_quality=model_quality,
        )

    @staticmethod
    def _create_model_quality(
        model_type: ModelType,
        dataset_type: DatasetType,
        model_quality_data: Dict,
    ):
        """Create a specific model quality instance based on model type and dataset type."""
        if model_type == ModelType.BINARY:
            return ModelQualityDTO._create_binary_model_quality(
                dataset_type=dataset_type,
                model_quality_data=model_quality_data,
            )
        if model_type == ModelType.MULTI_CLASS:
            return MultiClassificationModelQuality(**model_quality_data)
        if model_type == ModelType.REGRESSION:
            return ModelQualityDTO._create_regression_model_quality(
                dataset_type=dataset_type, model_quality_data=model_quality_data
            )
        raise MetricsInternalError(f'Invalid model type {model_type}')

    @staticmethod
    def _create_binary_model_quality(
        dataset_type: DatasetType,
        model_quality_data: Dict,
    ) -> BinaryClassificationModelQuality | CurrentBinaryClassificationModelQuality:
        """Create a binary model quality instance based on dataset type."""
        if dataset_type == DatasetType.REFERENCE:
            return BinaryClassificationModelQuality(**model_quality_data)
        if dataset_type == DatasetType.CURRENT:
            return CurrentBinaryClassificationModelQuality(**model_quality_data)
        raise MetricsInternalError(f'Invalid dataset type {dataset_type}')

    @staticmethod
    def _create_regression_model_quality(
        dataset_type: DatasetType,
        model_quality_data: Dict,
    ) -> RegressionModelQuality | CurrentRegressionModelQuality:
        """Create a binary model quality instance based on dataset type."""
        if dataset_type == DatasetType.REFERENCE:
            return RegressionModelQuality(**model_quality_data)
        if dataset_type == DatasetType.CURRENT:
            return CurrentRegressionModelQuality(**model_quality_data)
        raise MetricsInternalError(f'Invalid dataset type {dataset_type}')
