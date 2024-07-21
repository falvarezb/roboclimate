package roboclimate;

import java.util.List;
import java.util.function.Function;

public class MetricCalculator {
    static double computeRootMeanSquaredError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, Double> tExtractor) {
        return Math.sqrt(joinWeatherRecords
                .stream()
                .map(record -> Math.pow(record.weatherVariableValue() - tExtractor.apply(record), 2))
                .reduce(0.0, Double::sum) / joinWeatherRecords.size());
    }

    static double computeMeanAbsoluteError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, Double> tExtractor) {
        return joinWeatherRecords
                .stream()
                .map(record -> Math.abs(record.weatherVariableValue() - tExtractor.apply(record)))
                .reduce(0.0, Double::sum) / joinWeatherRecords.size();
    }
}
