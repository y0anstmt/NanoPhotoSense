package org.acme.domain;

import io.quarkus.hibernate.orm.panache.PanacheEntityBase;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "alert")
public class Alert extends PanacheEntityBase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    
    @Column(name = "sensor_id", nullable = false)
    public String sensorId;
    
    @Column(nullable = false)
    public Instant timestamp;
    
    @Column(name = "alert_type", nullable = false)
    public String alertType;
    
    @Column(nullable = false)
    public String severity;
    
    @Column(name = "alert_message", nullable = false, columnDefinition = "TEXT")
    public String alertMessage;
    
    @Column(nullable = false)
    public boolean acknowledged = false;
}
