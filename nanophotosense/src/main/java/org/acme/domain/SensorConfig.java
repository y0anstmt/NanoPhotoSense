package org.acme.domain;

import io.quarkus.hibernate.orm.panache.PanacheEntityBase;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "sensor_config")
public class SensorConfig extends PanacheEntityBase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    
    @Column(name = "sensor_id", nullable = false, unique = true)
    public String sensorId;
    
    @Column(name = "location_label")
    public String locationLabel;
    
    @Column(nullable = false)
    public Double latitude;
    
    @Column(nullable = false)
    public Double longitude;
    
    @Column(name = "sensitivity_k", nullable = false)
    public Double sensitivityK;
    
    @Column(name = "baseline_peak", nullable = false)
    public Double baselinePeak;
    
    @Column(nullable = false)
    public String status;
}