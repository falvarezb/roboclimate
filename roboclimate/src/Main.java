import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
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
            System.out.println(joinWeatherRecords(actualWeatherList, forecastMap).get(2));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private static List<JoinedRecord> joinWeatherRecords(List<WeatherRecord> actualWeatherList, Map<Long, List<WeatherRecord>> forecastMap) {
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
                            forecasts.get(0).temperature(),
                            forecasts.get(1).temperature(),
                            forecasts.get(2).temperature(),
                            forecasts.get(3).temperature(),
                            forecasts.get(4).temperature()
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
}

record WeatherRecord(double temperature, double pressure, double humidity, double wind_speed, double wind_deg, long dt,
                     LocalDate today) {
}

record JoinedRecord(double weatherVariableValue, long dt, LocalDate today, double t5, double t4, double t3, double t2,
                    double t1) {
}