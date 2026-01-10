package main.scala.calculator

import org.apache.spark.sql.types._

object TableSchemas {

  val priceSchema = StructType(Array(StructField("ticker", StringType, false),
    StructField("utc_timestamp", TimestampType, false),
    StructField("price", FloatType, false))
  )

  val velocitySchema = StructType(Array(StructField("ticker", StringType, false),
    StructField("utc_time", TimestampType, false),
    StructField("price", FloatType, false),
    StructField("v5", FloatType, false),
    StructField("v10", FloatType, false),
    StructField("v15", FloatType, false),
    StructField("v30", FloatType, false))
  )
}
