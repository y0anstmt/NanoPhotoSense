package org.acme.dto;

import java.time.Instant;
import java.util.List;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class SpectrumStreamData {
    @NotBlank(message = "sensorId is mandatory")
    private String sensorId;

    @NotNull(message = "timestamp is mandatory")
    private Instant timestamp;

    @NotNull(message = "peakWavelength is mandatory")
    private Double peakWavelength;

    private List<Double> wavelengths;
    private List<Double> intensities;
    @NotNull(message = "refractiveIndex is mandatory")
    private Double refractiveIndex;
    @NotNull(message = "deltaN is mandatory")
    private Double deltaN;
}
