package roboclimate;

import java.math.BigDecimal;
import java.math.MathContext;
import java.util.ArrayList;
import java.util.List;
import java.util.function.BiFunction;
import java.util.function.Function;

public class MetricCalculator {
    static BigDecimal computeRootMeanSquaredError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, BigDecimal> tExtractor) {
        return joinWeatherRecords
                .stream()
                .map(record -> record.weatherVariableValue().subtract(tExtractor.apply(record)).pow(2))
                .reduce(BigDecimal.ZERO, BigDecimal::add).divide(BigDecimal.valueOf(joinWeatherRecords.size()), MathContext.DECIMAL64).sqrt(MathContext.DECIMAL64);
    }

    static BigDecimal computeMeanAbsoluteError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, BigDecimal> tExtractor) {
        return joinWeatherRecords
                .stream()
                .map(record -> record.weatherVariableValue().subtract(tExtractor.apply(record)).abs())
                .reduce(BigDecimal.ZERO, BigDecimal::add).divide(BigDecimal.valueOf(joinWeatherRecords.size()), MathContext.DECIMAL64);
    }

    static BigDecimal computeMedianAbsoluteError(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, BigDecimal> tExtractor) {
        var absoluteErrors = joinWeatherRecords
                .stream()
                .map(record -> record.weatherVariableValue().subtract(tExtractor.apply(record)).abs())
                .sorted()
                .toList();

        if (absoluteErrors.size() % 2 == 0) {
            return absoluteErrors.get(absoluteErrors.size() / 2).add(absoluteErrors.get(absoluteErrors.size() / 2 - 1)).divide(BigDecimal.valueOf(2), MathContext.DECIMAL64);
        } else {
            return absoluteErrors.get(absoluteErrors.size() / 2);
        }
    }

    static BigDecimal computeMeanAbsoluteScaledErrorByTx(List<JoinedRecord> joinWeatherRecords, Function<JoinedRecord, BigDecimal> tExtractor, int tPeriod) {
        BigDecimal mae = BigDecimal.ZERO, naive_mae = BigDecimal.ZERO;
        for(int i = tPeriod, j = 0; i < joinWeatherRecords.size(); i++, j++) {
            BigDecimal actualValue = joinWeatherRecords.get(i).weatherVariableValue();
            BigDecimal predictedValue = tExtractor.apply(joinWeatherRecords.get(i));
            mae = mae.add(actualValue.subtract(predictedValue).abs());

            BigDecimal naivePrediction = joinWeatherRecords.get(j).weatherVariableValue();
            naive_mae = naive_mae.add(actualValue.subtract(naivePrediction).abs());
        }
        return mae.divide(naive_mae, MathContext.DECIMAL64);
    }

    static ArrayList<BigDecimal> computeMeanAbsoluteScaledError(List<JoinedRecord> joinWeatherRecords) {
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

    static ArrayList<BigDecimal> computeMetric(BiFunction<List<JoinedRecord>, Function<JoinedRecord, BigDecimal>, BigDecimal> metricF, List<JoinedRecord> joinWeatherRecords) {
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
