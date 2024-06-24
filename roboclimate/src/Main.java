import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

public class Main {
    public static void main(String[] args) {

        System.out.println("Hello world!");
        try {
            List<WeatherRecord> actualWeatherList = readWeatherFile("../csv_files/weather_madrid.csv");
            List<WeatherRecord> forecastWeatherList = readWeatherFile("../csv_files/forecast_madrid.csv");
            System.out.println(actualWeatherList.getFirst());
            System.out.println(forecastWeatherList.getFirst());
            Map<Long, List<WeatherRecord>> forecastMap = groupByDt(forecastWeatherList);
            System.out.println(groupByDt(forecastWeatherList).entrySet().stream().findFirst());
            processWeatherVariable(actualWeatherList, forecastMap, WeatherRecord::temperature);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static void processWeatherVariable(List<WeatherRecord> actualWeatherList, Map<Long, List<WeatherRecord>> forecastMap, Function<WeatherRecord, Double> weatherVariableExtractor) throws IOException {
        var joinWeatherRecords = joinWeatherRecords(actualWeatherList, forecastMap, weatherVariableExtractor);
        writeJoinCsvFile(joinWeatherRecords, "../csv_files/temp/java_join_madrid.csv");
        //calculate mean absolute error
        var t1MeanAbsoluteError = computeMeanAbsoluteError(joinWeatherRecords, JoinedRecord::t1);
        var t2MeanAbsoluteError = computeMeanAbsoluteError(joinWeatherRecords, JoinedRecord::t2);
        var t3MeanAbsoluteError = computeMeanAbsoluteError(joinWeatherRecords, JoinedRecord::t3);
        var t4MeanAbsoluteError = computeMeanAbsoluteError(joinWeatherRecords, JoinedRecord::t4);
        var t5MeanAbsoluteError = computeMeanAbsoluteError(joinWeatherRecords, JoinedRecord::t5);
        var maes = new ArrayList<Double>() {{
            add(t5MeanAbsoluteError);
            add(t4MeanAbsoluteError);
            add(t3MeanAbsoluteError);
            add(t2MeanAbsoluteError);
            add(t1MeanAbsoluteError);
        }};
        //writeMetricsCsvFile(maes, "../csv_files/temp/java_metrics_madrid.csv");

        var t1RootMeanSquaredError = computeRootMeanSquaredError(joinWeatherRecords, JoinedRecord::t1);
        var t2RootMeanSquaredError = computeRootMeanSquaredError(joinWeatherRecords, JoinedRecord::t2);
        var t3RootMeanSquaredError = computeRootMeanSquaredError(joinWeatherRecords, JoinedRecord::t3);
        var t4RootMeanSquaredError = computeRootMeanSquaredError(joinWeatherRecords, JoinedRecord::t4);
        var t5RootMeanSquaredError = computeRootMeanSquaredError(joinWeatherRecords, JoinedRecord::t5);
        var rmses = new ArrayList<Double>() {{
            add(t5RootMeanSquaredError);
            add(t4RootMeanSquaredError);
            add(t3RootMeanSquaredError);
            add(t2RootMeanSquaredError);
            add(t1RootMeanSquaredError);
        }};
        writeMetricsCsvFile(maes, rmses, "../csv_files/temp/java_metrics_madrid.csv");

        //calculate Root mean squared error

    }

    private static double computeRootMeanSquaredError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, Double> tExtractor) {
        return Math.sqrt(joinWeatherRecords
                .stream()
                .map(record -> Math.pow(record.weatherVariableValue() - tExtractor.apply(record), 2))
                .reduce(0.0, Double::sum) / joinWeatherRecords.size());
    }

    private static double computeMeanAbsoluteError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, Double> tExtractor) {
        return joinWeatherRecords
                .stream()
                .map(record -> Math.abs(record.weatherVariableValue() - tExtractor.apply(record)))
                .reduce(0.0, Double::sum) / joinWeatherRecords.size();
    }

    private static List<JoinedRecord> joinWeatherRecords(List<WeatherRecord> actualWeatherList, Map<Long, List<WeatherRecord>> forecastMap, Function<WeatherRecord, Double> weatherVariableExtractor) {
        return actualWeatherList.stream()
                .map(actualWeatherRecord -> {
                    var forecasts = forecastMap.getOrDefault(actualWeatherRecord.dt(), List.of());
                    if (forecasts.size() != 5) {
                        return null;
                    }
                    return new JoinedRecord(
                            actualWeatherRecord.temperature(),
                            actualWeatherRecord.dt(),
                            actualWeatherRecord.today(),
                            weatherVariableExtractor.apply(forecasts.get(0)),
                            weatherVariableExtractor.apply(forecasts.get(1)),
                            weatherVariableExtractor.apply(forecasts.get(2)),
                            weatherVariableExtractor.apply(forecasts.get(3)),
                            weatherVariableExtractor.apply(forecasts.get(4))

                    );
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }


    private static Map<Long, List<WeatherRecord>> groupByDt(List<WeatherRecord> weatherList) {
        return weatherList.stream()
                .collect(Collectors.groupingBy(WeatherRecord::dt))
                .entrySet()
                .stream()
                .filter(entry -> entry.getValue().size() == 5)
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        entry -> entry.getValue().stream()
                                .sorted(Comparator.comparing(WeatherRecord::dt))
                                .collect(Collectors.toList())
                ));
    }

    private static List<WeatherRecord> readWeatherFile(String path) throws IOException {
        try (Stream<String> lines = Files.lines(Paths.get(path))) {
            return lines
                    .skip(1)                        // Skip the first line
                    .map(line -> line.split(","))   // Split each line by comma
                    .map(data -> new WeatherRecord(       // Convert array to Weather object
                            Double.parseDouble(data[0]),
                            Double.parseDouble(data[1]),
                            Double.parseDouble(data[2]),
                            Double.parseDouble(data[3]),
                            Double.parseDouble(data[4]),
                            (long) Double.parseDouble(data[5]),
                            LocalDate.parse(data[6])
                    ))
                    .collect(Collectors.toList());
        }
    }

    private static void writeJoinCsvFile(List<JoinedRecord> joinedRecords, String path) throws IOException {
        var csvHeader = "temp,dt,today,t5,t4,t3,t2,t1";
        var csvData = joinedRecords.stream()
                .map(record -> record.weatherVariableValue() + "," + record.dt() + "," + record.today() + "," + record.t5() + "," + record.t4() + "," + record.t3() + "," + record.t2()  + "," + record.t1())
                .collect(Collectors.joining("\n"));
        Files.writeString(Paths.get(path), csvHeader + "\n" + csvData);
    }

    private static void writeMetricsCsvFile(List<Double> maes, List<Double> rmses, String path) throws IOException {
        var csvHeader = "mae,rmse";
        var csvData = IntStream.range(0, maes.size())
                .mapToObj(i -> maes.get(i) + "," + rmses.get(i))
                .collect(Collectors.joining("\n"));
//        var csvData = maes.stream()
//                .map(String::valueOf)
//                .collect(Collectors.joining("\n"));
        Files.writeString(Paths.get(path), csvHeader + "\n" + csvData);
    }
}

record WeatherRecord(double temperature, double pressure, double humidity, double wind_speed, double wind_deg, long dt,
                     LocalDate today) {
}

record JoinedRecord(double weatherVariableValue, long dt, LocalDate today, double t5, double t4, double t3, double t2,
                    double t1) {
}