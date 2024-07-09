import datetime
import uuid
import pytest
import deepdiff

from metrics.statistics import calculate_statistics_current
from models.current_dataset import CurrentDataset
from models.reference_dataset import ReferenceDataset
from utils.current_regression import CurrentMetricsRegressionService
from utils.models import (
    ColumnDefinition,
    DataType,
    Granularity,
    ModelOut,
    ModelType,
    OutputType,
    SupportedTypes,
)


@pytest.fixture()
def current_bike_dataframe(spark_fixture, test_data_dir):
    yield spark_fixture.read.csv(
        f"{test_data_dir}/current/regression/bike.csv", header=True
    )


@pytest.fixture()
def reference_bike_dataframe(spark_fixture, test_data_dir):
    yield spark_fixture.read.csv(
        f"{test_data_dir}/reference/regression/reference_bike.csv", header=True
    )


@pytest.fixture()
def current_test_fe(spark_fixture, test_data_dir):
    yield (
        spark_fixture.read.csv(
            f"{test_data_dir}/current/regression/regression_reference_test_FE.csv",
            header=True,
        )
    )


@pytest.fixture()
def reference_test_fe(spark_fixture, test_data_dir):
    yield (
        spark_fixture.read.csv(
            f"{test_data_dir}/reference/regression/regression_reference_test_FE.csv",
            header=True,
        )
    )


@pytest.fixture()
def model():
    output = OutputType(
        prediction=ColumnDefinition(name="predictions", type=SupportedTypes.float),
        prediction_proba=None,
        output=[ColumnDefinition(name="predictions", type=SupportedTypes.float)],
    )
    target = ColumnDefinition(name="ground_truth", type=SupportedTypes.int)
    timestamp = ColumnDefinition(name="dteday", type=SupportedTypes.datetime)
    granularity = Granularity.MONTH
    features = [
        ColumnDefinition(name="season", type=SupportedTypes.int),
        ColumnDefinition(name="yr", type=SupportedTypes.int),
        ColumnDefinition(name="mnth", type=SupportedTypes.int),
        ColumnDefinition(name="holiday", type=SupportedTypes.int),
        ColumnDefinition(name="weekday", type=SupportedTypes.int),
        ColumnDefinition(name="workingday", type=SupportedTypes.int),
        ColumnDefinition(name="weathersit", type=SupportedTypes.float),
        ColumnDefinition(name="temp", type=SupportedTypes.float),
        ColumnDefinition(name="atemp", type=SupportedTypes.float),
        ColumnDefinition(name="hum", type=SupportedTypes.float),
        ColumnDefinition(name="windspeed", type=SupportedTypes.float),
    ]
    yield ModelOut(
        uuid=uuid.uuid4(),
        name="regression model",
        description="description",
        model_type=ModelType.REGRESSION,
        data_type=DataType.TABULAR,
        timestamp=timestamp,
        granularity=granularity,
        outputs=output,
        target=target,
        features=features,
        frameworks="framework",
        algorithm="algorithm",
        created_at=str(datetime.datetime.now()),
        updated_at=str(datetime.datetime.now()),
    )


@pytest.fixture()
def model_test_fe():
    output = OutputType(
        prediction=ColumnDefinition(name="prediction", type=SupportedTypes.int),
        prediction_proba=None,
        output=[ColumnDefinition(name="prediction", type=SupportedTypes.int)],
    )
    target = ColumnDefinition(name="ground_truth", type=SupportedTypes.int)
    timestamp = ColumnDefinition(name="timestamp", type=SupportedTypes.datetime)
    granularity = Granularity.MONTH
    features = [
        ColumnDefinition(name="Sex", type=SupportedTypes.string),
        ColumnDefinition(name="Length", type=SupportedTypes.float),
        ColumnDefinition(name="Diameter", type=SupportedTypes.float),
        ColumnDefinition(name="Height", type=SupportedTypes.float),
        ColumnDefinition(name="Whole_weight", type=SupportedTypes.float),
        ColumnDefinition(name="Shucked_weight", type=SupportedTypes.float),
        ColumnDefinition(name="Viscera_weight", type=SupportedTypes.float),
        ColumnDefinition(name="Shell_weight", type=SupportedTypes.float),
        ColumnDefinition(name="pred_id", type=SupportedTypes.string),
    ]
    yield ModelOut(
        uuid=uuid.uuid4(),
        name="regression model",
        description="description",
        model_type=ModelType.REGRESSION,
        data_type=DataType.TABULAR,
        timestamp=timestamp,
        granularity=granularity,
        outputs=output,
        target=target,
        features=features,
        frameworks="framework",
        algorithm="algorithm",
        created_at=str(datetime.datetime.now()),
        updated_at=str(datetime.datetime.now()),
    )


@pytest.fixture()
def current_dataset_fe(current_test_fe, model_test_fe):
    yield CurrentDataset(
        raw_dataframe=current_test_fe,
        model=model_test_fe,
    )


@pytest.fixture()
def reference_dataset_fe(reference_test_fe, model_test_fe):
    yield ReferenceDataset(
        raw_dataframe=reference_test_fe,
        model=model_test_fe,
    )


@pytest.fixture()
def current_dataset(current_bike_dataframe, model):
    yield CurrentDataset(
        raw_dataframe=current_bike_dataframe,
        model=model,
    )


@pytest.fixture()
def reference_dataset(reference_bike_dataframe, model):
    yield ReferenceDataset(
        raw_dataframe=reference_bike_dataframe,
        model=model,
    )


def test_current_statistics(current_dataset):
    stats = calculate_statistics_current(current_dataset)

    assert current_dataset.current_count == stats.n_observations

    assert stats.missing_cells_perc == 100 * stats.missing_cells / (
        stats.n_variables * stats.n_observations
    )

    expected = {
        "n_variables": 14,
        "n_observations": 100,
        "missing_cells": 7,
        "missing_cells_perc": 0.5,
        "duplicate_rows": 2,
        "duplicate_rows_perc": 2.0,
        "numeric": 13,
        "categorical": 0,
        "datetime": 1,
    }

    assert stats.model_dump(serialize_as_any=True) == expected


def test_data_quality(
    spark_fixture, current_dataset, reference_dataset, expected_data_quality
):
    metrics_service = CurrentMetricsRegressionService(
        spark_session=spark_fixture,
        current=current_dataset,
        reference=reference_dataset,
    )

    data_quality = metrics_service.calculate_data_quality(is_current=True)
    computed = data_quality.model_dump(serialize_as_any=True, exclude_none=True)

    features = expected_data_quality["feature_metrics"]
    target = expected_data_quality["target_metrics"]

    computed_features = computed["feature_metrics"]
    computed_target = computed["target_metrics"]

    assert not deepdiff.DeepDiff(
        computed_features,
        features,
        ignore_order=True,
        ignore_type_subclasses=True,
    )

    assert not deepdiff.DeepDiff(
        computed_target,
        target,
        ignore_order=True,
        ignore_type_subclasses=True,
    )


@pytest.fixture()
def expected_data_quality():
    yield {
        "n_observations": 100,
        "target_metrics": {
            "feature_name": "ground_truth",
            "type": "numerical",
            "missing_value": {"count": 0, "percentage": 0.0},
            "mean": 288.63,
            "std": 317.1797010012979,
            "min": 9.0,
            "max": 1651.0,
            "median_metrics": {"perc_25": 82.0, "median": 167.5, "perc_75": 354.0},
            "histogram": {
                "buckets": [
                    2.0,
                    342.8,
                    683.6,
                    1024.4,
                    1365.2,
                    1706.0,
                    2046.8000000000002,
                    2387.6,
                    2728.4,
                    3069.2000000000003,
                    3410.0,
                ],
                "reference_values": [204, 144, 165, 89, 44, 23, 26, 22, 9, 5],
                "current_values": [74, 14, 8, 2, 2, 0, 0, 0, 0, 0],
            },
        },
        "feature_metrics": [
            {
                "feature_name": "season",
                "type": "numerical",
                "missing_value": {"count": 0, "percentage": 0.0},
                "mean": 1.21,
                "std": 0.40936018074033254,
                "min": 1.0,
                "max": 2.0,
                "median_metrics": {"perc_25": 1.0, "median": 1.0, "perc_75": 1.0},
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        1.0,
                        1.3,
                        1.6,
                        1.9,
                        2.2,
                        2.5,
                        2.8,
                        3.1,
                        3.4,
                        3.6999999999999997,
                        4.0,
                    ],
                    "reference_values": [181, 0, 0, 184, 0, 0, 188, 0, 0, 178],
                    "current_values": [79, 0, 0, 21, 0, 0, 0, 0, 0, 0],
                },
            },
            {
                "feature_name": "yr",
                "type": "numerical",
                "missing_value": {"count": 0, "percentage": 0.0},
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "median_metrics": {"perc_25": 0.0, "median": 0.0, "perc_75": 0.0},
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0,
                        0.1,
                        0.2,
                        0.30000000000000004,
                        0.4,
                        0.5,
                        0.6000000000000001,
                        0.7000000000000001,
                        0.8,
                        0.9,
                        1.0,
                    ],
                    "reference_values": [365, 0, 0, 0, 0, 0, 0, 0, 0, 366],
                    "current_values": [100, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                },
            },
            {
                "feature_name": "mnth",
                "type": "numerical",
                "missing_value": {"count": 1, "percentage": 1.0},
                "mean": 2.242424242424242,
                "std": 0.9803259463254868,
                "min": 1.0,
                "max": 4.0,
                "median_metrics": {"perc_25": 1.0, "median": 2.0, "perc_75": 3.0},
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        1.0,
                        2.1,
                        3.2,
                        4.300000000000001,
                        5.4,
                        6.5,
                        7.6000000000000005,
                        8.700000000000001,
                        9.8,
                        10.9,
                        12.0,
                    ],
                    "reference_values": [119, 62, 60, 62, 60, 62, 62, 60, 62, 122],
                    "current_values": [57, 32, 10, 0, 0, 0, 0, 0, 0, 0],
                },
            },
            {
                "feature_name": "holiday",
                "type": "numerical",
                "missing_value": {"count": 1, "percentage": 1.0},
                "mean": 0.020202020202020204,
                "std": 0.14140677897022574,
                "min": 0.0,
                "max": 1.0,
                "median_metrics": {"perc_25": 0.0, "median": 0.0, "perc_75": 0.0},
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0,
                        0.1,
                        0.2,
                        0.30000000000000004,
                        0.4,
                        0.5,
                        0.6000000000000001,
                        0.7000000000000001,
                        0.8,
                        0.9,
                        1.0,
                    ],
                    "reference_values": [710, 0, 0, 0, 0, 0, 0, 0, 0, 21],
                    "current_values": [97, 0, 0, 0, 0, 0, 0, 0, 0, 2],
                },
            },
            {
                "feature_name": "weekday",
                "type": "numerical",
                "missing_value": {"count": 1, "percentage": 1.0},
                "mean": 2.95959595959596,
                "std": 1.9893553048571038,
                "min": 0.0,
                "max": 6.0,
                "median_metrics": {"perc_25": 1.0, "median": 3.0, "perc_75": 5.0},
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0,
                        0.6,
                        1.2,
                        1.7999999999999998,
                        2.4,
                        3.0,
                        3.5999999999999996,
                        4.2,
                        4.8,
                        5.3999999999999995,
                        6.0,
                    ],
                    "reference_values": [105, 105, 0, 104, 0, 104, 104, 0, 104, 105],
                    "current_values": [14, 15, 0, 14, 0, 14, 15, 0, 14, 13],
                },
            },
            {
                "feature_name": "workingday",
                "type": "numerical",
                "missing_value": {"count": 0, "percentage": 0.0},
                "mean": 0.7,
                "std": 0.46056618647183833,
                "min": 0.0,
                "max": 1.0,
                "median_metrics": {"perc_25": 0.0, "median": 1.0, "perc_75": 1.0},
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0,
                        0.1,
                        0.2,
                        0.30000000000000004,
                        0.4,
                        0.5,
                        0.6000000000000001,
                        0.7000000000000001,
                        0.8,
                        0.9,
                        1.0,
                    ],
                    "reference_values": [231, 0, 0, 0, 0, 0, 0, 0, 0, 500],
                    "current_values": [30, 0, 0, 0, 0, 0, 0, 0, 0, 70],
                },
            },
            {
                "feature_name": "weathersit",
                "type": "numerical",
                "missing_value": {"count": 0, "percentage": 0.0},
                "mean": 1.45,
                "std": 0.5573204290227127,
                "min": 1.0,
                "max": 3.0,
                "median_metrics": {"perc_25": 1.0, "median": 1.0, "perc_75": 2.0},
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        1.0,
                        1.2,
                        1.4,
                        1.6,
                        1.8,
                        2.0,
                        2.2,
                        2.4000000000000004,
                        2.6,
                        2.8,
                        3.0,
                    ],
                    "reference_values": [463, 0, 0, 0, 0, 247, 0, 0, 0, 21],
                    "current_values": [58, 0, 0, 0, 0, 39, 0, 0, 0, 3],
                },
            },
            {
                "feature_name": "temp",
                "type": "numerical",
                "missing_value": {"count": 2, "percentage": 2.0},
                "mean": 0.28181619795918367,
                "std": 0.10183360371563194,
                "min": 0.0591304,
                "max": 0.573333,
                "median_metrics": {
                    "perc_25": 0.19874975,
                    "median": 0.26749999999999996,
                    "perc_75": 0.3432335,
                },
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0591304,
                        0.13938405999999998,
                        0.21963771999999998,
                        0.29989137999999993,
                        0.38014503999999993,
                        0.46039869999999994,
                        0.5406523599999999,
                        0.62090602,
                        0.70115968,
                        0.78141334,
                        0.861667,
                    ],
                    "reference_values": [7, 36, 90, 104, 93, 80, 93, 101, 103, 24],
                    "current_values": [5, 27, 26, 21, 15, 3, 1, 0, 0, 0],
                },
            },
            {
                "feature_name": "atemp",
                "type": "numerical",
                "missing_value": {"count": 1, "percentage": 1.0},
                "mean": 0.28198808787878793,
                "std": 0.09538584350774348,
                "min": 0.0790696,
                "max": 0.542929,
                "median_metrics": {
                    "perc_25": 0.2166045,
                    "median": 0.263879,
                    "perc_75": 0.339734,
                },
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0790696,
                        0.15525223999999999,
                        0.23143488,
                        0.30761752,
                        0.38380016,
                        0.45998279999999997,
                        0.53616544,
                        0.61234808,
                        0.6885307199999999,
                        0.7647133599999999,
                        0.840896,
                    ],
                    "reference_values": [11, 34, 97, 99, 98, 93, 122, 112, 57, 8],
                    "current_values": [8, 21, 35, 18, 13, 3, 1, 0, 0, 0],
                },
            },
            {
                "feature_name": "hum",
                "type": "numerical",
                "missing_value": {"count": 0, "percentage": 0.0},
                "mean": 0.5767590300000002,
                "std": 0.17338158044464802,
                "min": 0.0,
                "max": 0.948261,
                "median_metrics": {
                    "perc_25": 0.4671605,
                    "median": 0.538125,
                    "perc_75": 0.6866479999999999,
                },
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0,
                        0.09725,
                        0.1945,
                        0.29175,
                        0.389,
                        0.48625,
                        0.5835,
                        0.68075,
                        0.778,
                        0.8752500000000001,
                        0.9725,
                    ],
                    "reference_values": [1, 1, 3, 18, 95, 173, 164, 169, 73, 34],
                    "current_values": [1, 1, 0, 7, 22, 24, 18, 12, 9, 6],
                },
            },
            {
                "feature_name": "windspeed",
                "type": "numerical",
                "missing_value": {"count": 1, "percentage": 1.0},
                "mean": 0.22147813232323232,
                "std": 0.0817791420054435,
                "min": 0.0454083,
                "max": 0.507463,
                "median_metrics": {
                    "perc_25": 0.165519,
                    "median": 0.22015,
                    "perc_75": 0.2636855,
                },
                "class_median_metrics": [],
                "histogram": {
                    "buckets": [
                        0.0223917,
                        0.07089883,
                        0.11940595999999999,
                        0.16791309,
                        0.21642022,
                        0.26492735,
                        0.31343447999999996,
                        0.36194160999999997,
                        0.41044874,
                        0.45895587,
                        0.507463,
                    ],
                    "reference_values": [26, 99, 191, 173, 124, 62, 35, 14, 6, 1],
                    "current_values": [2, 5, 18, 22, 29, 12, 4, 5, 1, 1],
                },
            },
        ],
    }


def test_model_quality(spark_fixture, current_dataset, reference_dataset):
    metrics_service = CurrentMetricsRegressionService(
        spark_session=spark_fixture,
        current=current_dataset,
        reference=reference_dataset,
    )

    model_quality = metrics_service.calculate_model_quality()

    assert not deepdiff.DeepDiff(
        model_quality,
        {
            "global_metrics": {
                "mae": 71.82559791564941,
                "mape": 64.05699022707124,
                "mse": 17820.506660010054,
                "rmse": 133.49347047706138,
                "r2": 0.8210737408739541,
                "adj_r2": 0.7987079584831984,
                "variance": 118288.02759401732,
            },
            "grouped_metrics": {
                "mae": [
                    {"timestamp": "2011-01-01 00:00:00", "value": 35.67896665375808},
                    {"timestamp": "2011-02-01 00:00:00", "value": 89.13965238373855},
                    {"timestamp": "2011-03-01 00:00:00", "value": 91.54030847549438},
                    {"timestamp": "2011-04-01 00:00:00", "value": 63.352996826171875},
                ],
                "mape": [
                    {"timestamp": "2011-01-01 00:00:00", "value": 106.34668638669385},
                    {"timestamp": "2011-02-01 00:00:00", "value": 50.266650033642435},
                    {"timestamp": "2011-03-01 00:00:00", "value": 53.63275529139244},
                    {"timestamp": "2011-04-01 00:00:00", "value": 14.766409719281478},
                ],
                "mse": [
                    {"timestamp": "2011-01-01 00:00:00", "value": 2848.1117152678507},
                    {"timestamp": "2011-02-01 00:00:00", "value": 21631.812814960613},
                    {"timestamp": "2011-03-01 00:00:00", "value": 31460.34954782362},
                    {"timestamp": "2011-04-01 00:00:00", "value": 6540.166909402423},
                ],
                "rmse": [
                    {"timestamp": "2011-01-01 00:00:00", "value": 53.36770292290882},
                    {"timestamp": "2011-02-01 00:00:00", "value": 147.07757414018158},
                    {"timestamp": "2011-03-01 00:00:00", "value": 177.37065582509305},
                    {"timestamp": "2011-04-01 00:00:00", "value": 80.87129842782556},
                ],
                "r2": [
                    {"timestamp": "2011-01-01 00:00:00", "value": 0.17834457710460982},
                    {"timestamp": "2011-02-01 00:00:00", "value": 0.3895389519246505},
                    {"timestamp": "2011-03-01 00:00:00", "value": 0.7043715304337479},
                    {"timestamp": "2011-04-01 00:00:00", "value": 0.9678020649997567},
                ],
                "adj_r2": [
                    {"timestamp": "2011-01-01 00:00:00", "value": -0.3533148141806426},
                    {
                        "timestamp": "2011-02-01 00:00:00",
                        "value": -0.005465255653516854,
                    },
                    {"timestamp": "2011-03-01 00:00:00", "value": 0.5417758721723092},
                    {"timestamp": "2011-04-01 00:00:00", "value": 1.1448907075010948},
                ],
                "variance": [
                    {"timestamp": "2011-01-01 00:00:00", "value": 4720.867246089001},
                    {"timestamp": "2011-02-01 00:00:00", "value": 70942.48575413873},
                    {"timestamp": "2011-03-01 00:00:00", "value": 150522.0080596708},
                    {"timestamp": "2011-04-01 00:00:00", "value": 163422.9263027128},
                ],
            },
        },
        ignore_order=True,
        ignore_type_subclasses=True,
    )


def test_drift_regression(spark_fixture, current_dataset, reference_dataset):
    metrics_service = CurrentMetricsRegressionService(
        spark_session=spark_fixture,
        current=current_dataset,
        reference=reference_dataset,
    )

    drift = metrics_service.calculate_drift()

    assert not deepdiff.DeepDiff(
        drift,
        {
            "feature_metrics": [
                {
                    "feature_name": "season",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.7886320109,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "yr",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.9986320109,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "mnth",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.7510372975,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "holiday",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.9686320109,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "weekday",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.1475135386,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "workingday",
                    "drift_calc": {"type": "KS", "value": 0.69, "has_drift": True},
                },
                {
                    "feature_name": "weathersit",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.6219091927,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "temp",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.5259741552,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "atemp",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.5322880465,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "hum",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.2230727748,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "windspeed",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.2180156245,
                        "has_drift": True,
                    },
                },
            ]
        },
        ignore_order=True,
        ignore_type_subclasses=True,
    )


def test_drift_regression_chi(spark_fixture, current_dataset_fe, reference_dataset_fe):
    metrics_service = CurrentMetricsRegressionService(
        spark_session=spark_fixture,
        current=current_dataset_fe,
        reference=reference_dataset_fe,
    )

    drift = metrics_service.calculate_drift()

    assert not deepdiff.DeepDiff(
        drift,
        {
            "feature_metrics": [
                {
                    "feature_name": "Sex",
                    "drift_calc": {"type": "CHI2", "value": 0.0, "has_drift": True},
                },
                {
                    "feature_name": "pred_id",
                    "drift_calc": {
                        "type": "CHI2",
                        "value": 0.2397280792131291,
                        "has_drift": False,
                    },
                },
                {
                    "feature_name": "Length",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.0239680774,
                        "has_drift": False,
                    },
                },
                {
                    "feature_name": "Diameter",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.0301533877,
                        "has_drift": False,
                    },
                },
                {
                    "feature_name": "Height",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.065718922,
                        "has_drift": True,
                    },
                },
                {
                    "feature_name": "Whole_weight",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.0023194914,
                        "has_drift": False,
                    },
                },
                {
                    "feature_name": "Shucked_weight",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.0030926552,
                        "has_drift": False,
                    },
                },
                {
                    "feature_name": "Viscera_weight",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.0038658189,
                        "has_drift": False,
                    },
                },
                {
                    "feature_name": "Shell_weight",
                    "drift_calc": {
                        "type": "KS",
                        "value": 0.010824293,
                        "has_drift": False,
                    },
                },
            ]
        },
        ignore_order=True,
        ignore_type_subclasses=True,
    )
