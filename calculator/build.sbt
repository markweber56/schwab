ThisBuild / version := "0.1.0-SNAPSHOT"

ThisBuild / scalaVersion := "2.12.10"

// spark library dependencies
libraryDependencies ++= Seq(
  "org.postgresql" % "postgresql" % "42.6.0",
  "org.apache.spark" %% "spark-core" % "3.3.2" % "provided",
  "org.apache.spark" %% "spark-sql"  % "3.3.2" % "provided"
)

lazy val root = (project in file("."))
  .settings(
    name := "calculator"
  )
