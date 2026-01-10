package main.scala.calculator

import java.nio.file.Paths

import org.json4s.jackson.JsonMethods
import org.json4s.DefaultFormats
import scala.io.Source

trait Configurable {

  implicit val formats = DefaultFormats

  /** Return CustomConfig instance from json path to config file
    *
    * @param path String - path to config file
    * @return CustomConfig - configuration object
    */
  def getConfig(filePath: String)(implicit m: Manifest[CustomConfig]): CustomConfig = {
    val path = Paths.get(filePath).toUri

    JsonMethods.parse(Source.fromURI(path).reader()).extract[CustomConfig]
  }

}
