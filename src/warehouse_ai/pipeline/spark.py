"""Spark session factory with Delta Lake support."""

from __future__ import annotations

import logging

from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)

_session: SparkSession | None = None


def get_spark_session(app_name: str = "warehouse-ai", delta_path: str | None = None) -> SparkSession:
    """Get or create a Spark session configured for Delta Lake."""
    global _session
    if _session is not None and not _session._jsc.sc().isStopped():
        return _session

    builder = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config(
            "spark.sql.catalog.spark_catalog",
            "org.apache.spark.sql.delta.catalog.DeltaCatalog",
        )
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.extraJavaOptions", "-Xss4m")
    )

    if delta_path:
        builder = builder.config("spark.sql.warehouse.dir", delta_path)

    _session = builder.master("local[*]").getOrCreate()
    _session.sparkContext.setLogLevel("WARN")
    logger.info("Spark session created")
    return _session


def stop_spark() -> None:
    global _session
    if _session is not None:
        _session.stop()
        _session = None
