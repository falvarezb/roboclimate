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

    static double computeMeanAbsoluteScaledErrorByTx(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, Double> tExtractor, int tPeriod) {
        double mae = 0, naive_mae = 0;
        for(int i = tPeriod, j = 0; i < joinWeatherRecords.size(); i++, j++) {
            double actualValue = joinWeatherRecords.get(i).weatherVariableValue();
            Double predictedValue = tExtractor.apply(joinWeatherRecords.get(i));
            mae += Math.abs(actualValue - predictedValue);

            double naivePrediction = joinWeatherRecords.get(j).weatherVariableValue();
            naive_mae += Math.abs(actualValue - naivePrediction);
        }
        return mae / naive_mae;
    }

    static ArrayList<Double> computeMeanAbsoluteScaledError(List<JoinedRecord> joinWeatherRecords) {
        var t1Error = computeMeanAbsoluteScaledErrorByTx(joinWeatherRecords, JoinedRecord::t1, 1*8);
        var t2Error = computeMeanAbsoluteScaledErrorByTx(joinWeatherRecords, JoinedRecord::t2, 2*8);
        var t3Error = computeMeanAbsoluteScaledErrorByTx(joinWeatherRecords, JoinedRecord::t3, 3*8);
        var t4Error = computeMeanAbsoluteScaledErrorByTx(joinWeatherRecords, JoinedRecord::t4, 4*8);
        var t5Error = computeMeanAbsoluteScaledErrorByTx(joinWeatherRecords, JoinedRecord::t5, 5*8);
        return new ArrayList<>() {{
            add(t5Error);
            add(t4Error);
            add(t3Error);
            add(t2Error);
            add(t1Error);
        }};
    }

    static ArrayList<Double> computeMetric(BiFunction<List<JoinedRecord>, Function<JoinedRecord, Double>, Double> metricF, List<JoinedRecord> joinWeatherRecords) {
        var t1Error = metricF.apply(joinWeatherRecords, JoinedRecord::t1);
        var t2Error = metricF.apply(joinWeatherRecords, JoinedRecord::t2);
        var t3Error = metricF.apply(joinWeatherRecords, JoinedRecord::t3);
        var t4Error = metricF.apply(joinWeatherRecords, JoinedRecord::t4);
        var t5Error = metricF.apply(joinWeatherRecords, JoinedRecord::t5);
        return new ArrayList<>() {{
            add(t5Error);
            add(t4Error);
            add(t3Error);
            add(t2Error);
            add(t1Error);
        }};
    }
}
