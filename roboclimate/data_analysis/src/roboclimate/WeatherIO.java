package roboclimate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

public class WeatherIO {
    static List<WeatherRecord> readWeatherFile(String path) throws IOException {
        try (Stream<String> lines = Files.lines(Paths.get(path))) {
            return lines
                    .skip(1)                        // Skip the first line
                    .map(line -> Arrays.stream(line.split(",")).filter(s -> !s.isEmpty()).toArray(String[]::new)) // Split each line by comma
                    .filter(data -> data.length == 7) // Discard incomplete lines
                    .map(data -> new WeatherRecord(       // Convert array to Weather object
                                    Double.parseDouble(data[0]),
                                    Double.parseDouble(data[1]),
                                    Double.parseDouble(data[2]),
                                    Double.parseDouble(data[3]),
                                    Double.parseDouble(data[4]),
                                    (long) Double.parseDouble(data[5]),
                                    LocalDate.parse(data[6])
                            )
                    )
                    .collect(Collectors.toList());
        }
    }

    static void writeJoinCsvFile(List<JoinedRecord> joinedRecords, Path path, String weatherVariable) throws IOException {
        var csvHeader = STR."\{weatherVariable},dt,today,t5,t4,t3,t2,t1";
        var csvData = joinedRecords.stream()
                .map(record -> STR."\{record.weatherVariableValue()},\{record.dt()},\{record.today()},\{record.t5()},\{record.t4()},\{record.t3()},\{record.t2()},\{record.t1()}")
                .collect(Collectors.joining("\n"));
        if(!Files.exists(path.getParent())) {
            Files.createDirectories(path.getParent());
        }
        Files.writeString(path, STR."""
\{csvHeader}
\{csvData}""");
    }

    static void writeMetricsCsvFile(List<Double> mae, List<Double> rmse, List<Double> medae, List<Double> mase, Path path) throws IOException {
        var csvHeader = "mae,rmse,medae,mase";
        var csvData = IntStream.range(0, mae.size())
                .mapToObj(i -> STR."\{mae.get(i)},\{rmse.get(i)},\{medae.get(i)},\{mase.get(i)}")
                .collect(Collectors.joining("\n"));
        if(!Files.exists(path.getParent())) {
            Files.createDirectories(path.getParent());
        }
        Files.writeString(path, STR."""
\{csvHeader}
\{csvData}""");
    }
}
