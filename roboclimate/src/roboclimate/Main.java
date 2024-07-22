package roboclimate;

import java.io.IOException;
import java.time.LocalDate;
import java.util.*;
import java.util.function.Function;
import static roboclimate.MetricCalculator.*;
import static roboclimate.WeatherIO.*;
import static roboclimate.DataTransformer.*;

public class Main {
    public static void main(String[] args) {

        System.out.println("Hello world!");
        try {
            //todo: loop over cities
            List<WeatherRecord> actualWeatherList = readWeatherFile("../csv_files/weather_madrid.csv");
            List<WeatherRecord> forecastWeatherList = readWeatherFile("../csv_files/forecast_madrid.csv");
            System.out.println(actualWeatherList.getFirst());
            System.out.println(forecastWeatherList.getFirst());
            Map<Long, List<WeatherRecord>> forecastMap = groupByDt(forecastWeatherList);
            System.out.println(forecastMap.entrySet().stream().findFirst());
            //todo: loop over weather variables
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::temperature);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void processWeatherVariable(
            List<WeatherRecord> actualWeatherList, 
            Map<Long, List<WeatherRecord>> forecastMap, 
            Function<WeatherRecord, Double> weatherVariableExtractor) throws IOException {
        
        var joinWeatherRecords = joinWeatherRecords(actualWeatherList, forecastMap, weatherVariableExtractor);
        writeJoinCsvFile(joinWeatherRecords, "../csv_files/temp/java_join_madrid.csv");

        //calculate mean absolute error
        var mae = computeMetric(MetricCalculator::computeMeanAbsoluteError, joinWeatherRecords);
        //calculate Root mean squared error
        var rmse = computeMetric(MetricCalculator::computeRootMeanSquaredError, joinWeatherRecords);
        var medae = computeMetric(MetricCalculator::computeMedianAbsoluteError, joinWeatherRecords);
        var mase = computeMeanAbsoluteScaledError(joinWeatherRecords);
        writeMetricsCsvFile(mae, rmse, medae, mase, "../csv_files/temp/java_metrics_madrid.csv");



    }


}

record WeatherRecord(double temperature, double pressure, double humidity, double wind_speed, double wind_deg, long dt,
                     LocalDate today) {
}

record JoinedRecord(double weatherVariableValue, long dt, LocalDate today, double t5, double t4, double t3, double t2,
                    double t1) {
}