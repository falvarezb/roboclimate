package roboclimate;

import java.util.ArrayList;
import java.util.List;
import java.util.function.BiFunction;
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

    static double computeMedianAbsoluteError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, Double> tExtractor) {
        var absoluteErrors = joinWeatherRecords
                .stream()
                .map(record -> Math.abs(record.weatherVariableValue() - tExtractor.apply(record)))
                .sorted()
                .toList();

        if (absoluteErrors.size() % 2 == 0) {
            return (absoluteErrors.get(absoluteErrors.size() / 2) + absoluteErrors.get(absoluteErrors.size() / 2 - 1)) / 2;
        } else {
            return absoluteErrors.get(absoluteErrors.size() / 2);
        }
    }

    static ArrayList<Double> calculateMetricsByTx(BiFunction<List<JoinedRecord>, Function<JoinedRecord, Double>, Double> metricF, List<JoinedRecord> joinWeatherRecords) {
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
}
