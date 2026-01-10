package main.scala.calculator

import org.apache.spark.sql.{Dataset, Encoder, SaveMode, SparkSession}
import org.apache.spark.sql.functions._

import java.sql.{Date, Timestamp}

case class Velocity(ticker: String,
                   utc_time: Timestamp,
                   price: Float,
                   v5: Float,
                   v10: Float,
                   v15: Float,
                   v30: Float
                   )

case class Price(ticker: String,
                 utc_time: Timestamp,
                 price: Float
                )

object Velocity extends Configurable {

  def main(args: Array[String]): Unit = {

    val config: CustomConfig = getConfig("config.json")
    val dbConfig: DatabaseConfig = config.database

    val priceTableName: String = "stock.prices"
    val velocityTableName: String = "stock."

    val serverName = dbConfig.server;
    val serverPort = dbConfig.port;
    val dbName = dbConfig.dbName;

    val jdbcUrl = "jdbc:postgresql://" + serverName + ":" + serverPort + "/" + dbName

    val spark = SparkSession
      .builder
      .master("local[*]")
      .appName("calculator")
      .getOrCreate()

    import spark.implicits._

    println("starting calculator")

    val price: Dataset[Price] = spark.read
      .format("jdbc")
      .option("url", jdbcUrl)
      .option("dbtable", priceTableName)
      .option("user", dbConfig.dbUser)
      .option("password", dbConfig.dbPassword)
      .option("driver", dbConfig.driver)
      .load().as[Price]

    val priceCount = price.count()

    println(s"The price table has $priceCount rows")
//
//      priceDFFiltered.write
//        .mode(SaveMode.Append)
//        .format("jdbc")
//        .option("url", jdbcUrl)
//        .option("dbtable", priceTableName)
//        .option("user", dbConfig.dbUser)
//        .option("password", dbConfig.dbPassword)
//        .option("driver", dbConfig.driver)
//        .save()
//    })

    spark.stop()
  }

}