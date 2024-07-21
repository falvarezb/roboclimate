package roboclimate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import java.util.stream.Stream;

public class WeatherIO {
    static List<WeatherRecord> readWeatherFile(String path) throws IOException {
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

    static void writeJoinCsvFile(List<JoinedRecord> joinedRecords, String path) throws IOException {
        var csvHeader = "temp,dt,today,t5,t4,t3,t2,t1";
        var csvData = joinedRecords.stream()
                .map(record -> record.weatherVariableValue() + "," + record.dt() + "," + record.today() + "," + record.t5() + "," + record.t4() + "," + record.t3() + "," + record.t2()  + "," + record.t1())
                .collect(Collectors.joining("\n"));
        Files.writeString(Paths.get(path), csvHeader + "\n" + csvData);
    }

    static void writeMetricsCsvFile(List<Double> maes, List<Double> rmses, List<Double> medaes, String path) throws IOException {
        var csvHeader = "mae,rmse";
        var csvData = IntStream.range(0, maes.size())
                .mapToObj(i -> maes.get(i) + "," + rmses.get(i) + "," + medaes.get(i))
                .collect(Collectors.joining("\n"));
//        var csvData = maes.stream()
//                .map(String::valueOf)
//                .collect(Collectors.joining("\n"));
        Files.writeString(Paths.get(path), csvHeader + "\n" + csvData);
    }
}
