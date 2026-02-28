package org.acme.domain;

import io.quarkus.hibernate.orm.panache.PanacheEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "spectral_reading")
public class SpectralReading extends PanacheEntity {
    
    @Column(name = "sensor_id", nullable = false)
    public String sensorId;
    
    @Column(nullable = false)
    public Instant timestamp;
    
    @Column(name = "peak_wavelength", nullable = false)
    public Double peakWavelength;
    
    @Column(nullable = false, columnDefinition = "TEXT")
    public String intensities;
    
    @Column(name = "refractive_index", nullable = false)
    public Double refractiveIndex;
    
    @Column(name = "delta_n", nullable = false)
    public Double deltaN;
    
    @Column(name = "risk_score", nullable = false)
    public Double riskScore;
}