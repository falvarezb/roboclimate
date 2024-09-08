package roboclimate;

import java.math.BigDecimal;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

public class DataTransformer {
    static List<JoinedRecord> joinWeatherRecords(List<WeatherRecord> actualWeatherList, Map<Long, List<WeatherRecord>> forecastMap, Function<WeatherRecord, BigDecimal> weatherVariableExtractor) {
        return actualWeatherList.stream()
                .map(actualWeatherRecord -> {
                    var forecasts = forecastMap.getOrDefault(actualWeatherRecord.dt(), List.of());
                    if (forecasts.size() != 5) {
                        return null;
                    }
                    return new JoinedRecord(
                            weatherVariableExtractor.apply(actualWeatherRecord),
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
                .toList();
    }

    static Map<Long, List<WeatherRecord>> groupByDt(List<WeatherRecord> weatherList) {
        return weatherList.stream()
                .collect(Collectors.groupingBy(WeatherRecord::dt))
                .entrySet()
                .stream()
                .filter(entry -> entry.getValue().size() == 5)
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        entry -> entry.getValue().stream()
                                .sorted(Comparator.comparing(WeatherRecord::today))
                                .collect(Collectors.toList())
                ));
    }
}
