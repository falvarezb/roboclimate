package roboclimate;

import java.io.IOException;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

import static roboclimate.DataTransformer.groupByDt;
import static roboclimate.DataTransformer.joinWeatherRecords;
import static roboclimate.MetricCalculator.computeMeanAbsoluteScaledError;
import static roboclimate.MetricCalculator.computeMetric;
import static roboclimate.WeatherIO.*;

public class Main {

    private static final String CSV_FILES_PATH = System.getenv("ROBOCLIMATE_CSV_FILES_PATH");

    public static void main(String[] args) {
        List<String> cities = new ArrayList<>() {{
            add("london");
            add("madrid");
            add("saopaulo");
            add("sydney");
            add("newyork");
            add("moscow");
            add("tokyo");
            add("nairobi");
            add("asuncion");
            add("lagos");
        }};
        cities.forEach(Main::processCity);
    }

    private static void processCity(String cityName) {

        try {
            System.out.println(STR."processing city: \{cityName}");
            List<WeatherRecord> actualWeatherList = readWeatherFile(STR."\{CSV_FILES_PATH}/weather_\{cityName}.csv");
            List<WeatherRecord> forecastWeatherList = readWeatherFile(STR."\{CSV_FILES_PATH}/forecast_\{cityName}.csv");
            Map<Long, List<WeatherRecord>> forecastMap = groupByDt(forecastWeatherList);
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::temperature, cityName, "temp");
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::pressure, cityName, "pressure");
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::humidity, cityName, "humidity");
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::wind_speed, cityName, "wind_speed");
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::wind_deg, cityName, "wind_deg");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void processWeatherVariable(
            List<WeatherRecord> actualWeather,
            Map<Long, List<WeatherRecord>> weatherForecast,
            Function<WeatherRecord, Double> weatherVariableExtractor,
            String cityName,
            String weatherVariable) throws IOException {

        List<JoinedRecord> joinWeatherRecords = joinWeatherRecords(actualWeather, weatherForecast, weatherVariableExtractor);
        writeJoinCsvFile(joinWeatherRecords, Paths.get(STR."\{CSV_FILES_PATH}/\{weatherVariable}/join_\{cityName}.csv"), weatherVariable);

        var mae = computeMetric(MetricCalculator::computeMeanAbsoluteError, joinWeatherRecords);
        var rmse = computeMetric(MetricCalculator::computeRootMeanSquaredError, joinWeatherRecords);
        var medae = computeMetric(MetricCalculator::computeMedianAbsoluteError, joinWeatherRecords);
        var mase = computeMeanAbsoluteScaledError(joinWeatherRecords);
        writeMetricsCsvFile(mae, rmse, medae, mase, Paths.get(STR."\{CSV_FILES_PATH}/\{weatherVariable}/metrics_\{cityName}.csv"));
    }


}

record WeatherRecord(double temperature, double pressure, double humidity, double wind_speed, double wind_deg, long dt,
                     LocalDate today) {
}

record JoinedRecord(double weatherVariableValue, long dt, LocalDate today, double t5, double t4, double t3, double t2,
                    double t1) {
}