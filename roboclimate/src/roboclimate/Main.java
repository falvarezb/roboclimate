package roboclimate;

import java.io.IOException;
import java.time.LocalDate;
import java.util.*;
import java.util.function.BiFunction;
import java.util.function.Function;
import static roboclimate.MetricCalculator.*;
import static roboclimate.WeatherIO.*;
import static roboclimate.DataTransformer.*;

public class Main {
    public static void main(String[] args) {

        System.out.println("Hello world!");
        try {
            List<WeatherRecord> actualWeatherList = readWeatherFile("../csv_files/weather_madrid.csv");
            List<WeatherRecord> forecastWeatherList = readWeatherFile("../csv_files/forecast_madrid.csv");
            System.out.println(actualWeatherList.getFirst());
            System.out.println(forecastWeatherList.getFirst());
            Map<Long, List<WeatherRecord>> forecastMap = groupByDt(forecastWeatherList);
            System.out.println(forecastMap.entrySet().stream().findFirst());
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::temperature);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static ArrayList<Double> calculateMetricsByTx(BiFunction<List<JoinedRecord>, Function<JoinedRecord, Double>, Double> metricF, List<JoinedRecord> joinWeatherRecords) {
        var t1MeanAbsoluteError = metricF.apply(joinWeatherRecords, JoinedRecord::t1);
        var t2MeanAbsoluteError = metricF.apply(joinWeatherRecords, JoinedRecord::t2);
        var t3MeanAbsoluteError = metricF.apply(joinWeatherRecords, JoinedRecord::t3);
        var t4MeanAbsoluteError = metricF.apply(joinWeatherRecords, JoinedRecord::t4);
        var t5MeanAbsoluteError = metricF.apply(joinWeatherRecords, JoinedRecord::t5);
        return new ArrayList<>() {{
            add(t5MeanAbsoluteError);
            add(t4MeanAbsoluteError);
            add(t3MeanAbsoluteError);
            add(t2MeanAbsoluteError);
            add(t1MeanAbsoluteError);
        }};
    }

    private static void processWeatherVariable(
            List<WeatherRecord> actualWeatherList, 
            Map<Long, List<WeatherRecord>> forecastMap, 
            Function<WeatherRecord, Double> weatherVariableExtractor) throws IOException {
        
        var joinWeatherRecords = joinWeatherRecords(actualWeatherList, forecastMap, weatherVariableExtractor);
        writeJoinCsvFile(joinWeatherRecords, "../csv_files/temp/java_join_madrid.csv");

        //calculate mean absolute error
        var maes = calculateMetricsByTx(MetricCalculator::computeMeanAbsoluteError, joinWeatherRecords);
        //calculate Root mean squared error
        var rmses = calculateMetricsByTx(MetricCalculator::computeRootMeanSquaredError, joinWeatherRecords);
        writeMetricsCsvFile(maes, rmses, "../csv_files/temp/java_metrics_madrid.csv");



    }


}

record WeatherRecord(double temperature, double pressure, double humidity, double wind_speed, double wind_deg, long dt,
                     LocalDate today) {
}

record JoinedRecord(double weatherVariableValue, long dt, LocalDate today, double t5, double t4, double t3, double t2,
                    double t1) {
}