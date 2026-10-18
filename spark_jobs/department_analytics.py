from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    avg,
    count,
    round as spark_round
)

spark = (
    SparkSession.builder
    .appName("StudentPerformanceAnalytics")
    .getOrCreate()
)

input_path = (
    "hdfs://localhost:9000/"
    "student-performance/raw/students.csv"
)

output_path = (
    "hdfs://localhost:9000/"
    "student-performance/processed/department_summary"
)

df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(input_path)
)

summary = (
    df.groupBy("Department")
    .agg(
        count("*").alias("total_records"),
        spark_round(avg("Total_Score"), 2)
        .alias("average_score"),
        spark_round(avg("Attendance (%)"), 2)
        .alias("average_attendance")
    )
    .orderBy("Department")
)

print("Total student records:", df.count())
summary.show(truncate=False)

(
    summary.coalesce(1)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv(output_path)
)

print("Department summary saved to:", output_path)

spark.stop()
