package org.acme.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

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
    @JsonProperty("sensor_id")
    @NotBlank(message = "sensorId is mandatory")
    private String sensorId;

    @JsonProperty("timestamp")
    @NotNull(message = "timestamp is mandatory")
    private Long timestamp;

    @JsonProperty("peak_wavelength")
    @NotNull(message = "peakWavelength is mandatory")
    private Double peakWavelength;

    @JsonProperty("wavelengths")
    private List<Double> wavelengths;

    @JsonProperty("intensities")
    private List<Double> intensities;

    @JsonProperty("refractive_index")
    @NotNull(message = "refractiveIndex is mandatory")
    private Double refractiveIndex;

    @JsonProperty("delta_n")
    @NotNull(message = "deltaN is mandatory")
    private Double deltaN;
}
