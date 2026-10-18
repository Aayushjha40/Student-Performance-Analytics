
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, count, round as spark_round

HDFS_INPUT = (
    "hdfs://localhost:9000/"
    "student-performance/raw/students.csv"
)

HDFS_OUTPUT = (
    "hdfs://localhost:9000/"
    "student-performance/processed/department_summary"
)

spark = (
    SparkSession.builder
    .appName("StudentPerformanceAnalytics")
    .master("local[*]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

try:
    # Read the dataset directly from HDFS
    df = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(HDFS_INPUT)
    )

    print("\n--- Dataset Statistics ---")
    print("Total records:", df.count())
    print("Unique students:", df.select("Student_ID").distinct().count())

    # Calculate department-wise analytics
    summary = (
        df.groupBy("Department")
        .agg(
            count("*").alias("total_records"),
            spark_round(avg("Total_Score"), 2).alias("average_score"),
            spark_round(avg("Attendance (%)"), 2).alias("average_attendance"),
        )
        .orderBy("Department")
    )

    print("\n--- Department Performance ---")
    summary.show(truncate=False)

    # Save the results back to HDFS
    (
        summary.coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv(HDFS_OUTPUT)
    )

    print("\nAnalytics saved to:", HDFS_OUTPUT)

finally:
    spark.stop()

