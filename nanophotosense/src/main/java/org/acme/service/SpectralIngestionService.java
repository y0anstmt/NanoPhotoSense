package org.acme.service;

import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.acme.client.PhysicsAPIClient;
import org.acme.domain.Alert;
import org.acme.domain.SpectralReading;
import org.acme.dto.SpectrumStreamData;
import org.eclipse.microprofile.rest.client.inject.RestClient;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.quarkus.runtime.StartupEvent;
import io.quarkus.runtime.ShutdownEvent;
import io.smallrye.mutiny.Uni;
import io.smallrye.mutiny.infrastructure.Infrastructure;
import io.smallrye.mutiny.subscription.Cancellable;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;
import jakarta.transaction.Transactional;

@ApplicationScoped
public class SpectralIngestionService {
    @Inject
    @RestClient
    PhysicsAPIClient physicsAPIClient;

    @Inject
    ObjectMapper objectMapper;

    private static final Logger LOG = Logger.getLogger(SpectralIngestionService.class);
    private static final double DELTA_COMPONENT_WEIGHT = 75.0;
    private static final double TREND_COMPONENT_WEIGHT = 25.0;
    private static final double MODERATE_DELTA_BONUS = 10.0;
    private static final double MIN_ELAPSED_SECONDS = 1.0;

    @ConfigProperty(name = "landslide.risk.delta-critical", defaultValue = "0.018")
    double criticalDeltaN;

    @ConfigProperty(name = "landslide.risk.delta-moderate", defaultValue = "0.010")
    double moderateDeltaN;

    @ConfigProperty(name = "landslide.risk.rate-critical", defaultValue = "0.000015")
    double criticalRatePerSecond;

    @ConfigProperty(name = "landslide.alert.threshold", defaultValue = "80")
    double alertThreshold;

    @ConfigProperty(name = "landslide.alert.critical-threshold", defaultValue = "95")
    double criticalThreshold;

    @ConfigProperty(name = "spectral.sensor.ids", defaultValue = "LSPR-01,LSPR-02")
    List<String> sensorIds;

    private final Map<String, Cancellable> activeStreams = new ConcurrentHashMap<>();

    void onStart(@Observes StartupEvent ev) {
        LOG.infof("Initializing SSE streams for %d sensors: %s", sensorIds.size(), sensorIds);
        
        sensorIds.forEach(sensorId -> {
            try {
                startStream(sensorId);
                LOG.infof("✓ Started SSE stream for sensor: %s", sensorId);
            } catch (Exception e) {
                LOG.errorf(e, "✗ Failed to start SSE stream for sensor: %s", sensorId);
            }
        });
        
        LOG.infof("Active SSE streams: %d/%d", activeStreams.size(), sensorIds.size());
    }
    
    void onStop(@Observes ShutdownEvent ev) {
        LOG.infof("Shutting down %d active SSE streams...", activeStreams.size());
        
        activeStreams.keySet().forEach(sensorId -> {
            try {
                stopStream(sensorId);
            } catch (Exception e) {
                LOG.warnf(e, "Error stopping stream for %s", sensorId);
            }
        });
        
        LOG.info("All SSE streams stopped");
    }

    public void startStream(String sensorId) {
        LOG.infof("Starting SSE stream for sensor: %s",sensorId);
        if(activeStreams.containsKey(sensorId)){
            LOG.warnf("Stream already active for sensor %s, skipping",sensorId);
            return;
        }
        Cancellable cancellable = physicsAPIClient.streamSpectral(sensorId)
            .onOverflow().buffer(100)
            .emitOn(Infrastructure.getDefaultExecutor())
            .onItem().transformToUniAndMerge(payload -> {
                SpectrumStreamData data = deserializeStreamData(payload, sensorId);
                if (data == null) {
                    return Uni.createFrom().nullItem();
                }

                return processAndSave(data)
                    .onFailure().invoke(failure ->
                        LOG.errorf(failure,"Failed to process data for sensor %s",sensorId)
                    );
            })
            .onFailure().retry()
                  .withBackOff(Duration.ofSeconds(2),Duration.ofMinutes(1))
                  .atMost(5)
            .subscribe().with(
                savedReading -> {
                    if (savedReading != null) {
                        LOG.debugf("✓ Saved reading for sensor %s at %s (risk: %.2f)", 
                            savedReading.sensorId, savedReading.timestamp, savedReading.riskScore);
                    }
                },
                failure -> {
                    LOG.errorf(failure, "⨯ Stream failed permanently for sensor %s after retries", sensorId);
                    activeStreams.remove(sensorId);
                },
                
                () -> {
                    LOG.warnf("⚠ Stream completed unexpectedly for sensor %s", sensorId);
                    activeStreams.remove(sensorId);
                }
            );
        activeStreams.put(sensorId, cancellable);
        LOG.infof("✓ SSE stream subscription established for sensor: %s", sensorId);       
    }

    private SpectrumStreamData deserializeStreamData(String payload, String sensorId) {
        if (payload == null || payload.isBlank()) {
            return null;
        }

        try {
            return objectMapper.readValue(payload, SpectrumStreamData.class);
        } catch (Exception e) {
            LOG.errorf(e, "Invalid stream payload for sensor %s: %s", sensorId, payload);
            return null;
        }
    }
    
   
    public void stopStream(String sensorId) {
        Cancellable stream = activeStreams.remove(sensorId);
        if (stream != null) {
            stream.cancel();
            LOG.infof("Stopped SSE stream for sensor: %s", sensorId);
        } else {
            LOG.warnf("No active stream found for sensor: %s", sensorId);
        }
    }

     @Transactional
    Uni<SpectralReading> processAndSave(SpectrumStreamData data) {
        return Uni.createFrom().item(() -> {
            Instant readingTimestamp = toInstant(data.getTimestamp());
            double riskScore = calculateRiskScore(
                data.getSensorId(),
                data.getDeltaN(),
                readingTimestamp
            );
            String intensitiesJson;
            try {
                intensitiesJson = objectMapper.writeValueAsString(data.getIntensities());
            } catch (JsonProcessingException e) {
                LOG.errorf(e, "Failed to serialize intensities for sensor %s", data.getSensorId());
                intensitiesJson = "[]"; 
            }
            SpectralReading reading = new SpectralReading();
            reading.sensorId = data.getSensorId();
            reading.timestamp = readingTimestamp;
            reading.peakWavelength = data.getPeakWavelength();
            reading.intensities = intensitiesJson;
            reading.refractiveIndex = data.getRefractiveIndex();
            reading.deltaN = data.getDeltaN();
            reading.riskScore = riskScore;
            
            return reading;
        })
        .invoke(reading -> reading.persistAndFlush())
        .call(reading -> checkAndCreateAlert(reading))
        .invoke(reading -> {
            if (reading.riskScore >= alertThreshold) {
                LOG.warnf("⚠ LANDSLIDE RISK detected for sensor %s: delta_n=%.6f, risk=%.2f", 
                    reading.sensorId, reading.deltaN, reading.riskScore);
            }
        });
    }

    private Instant toInstant(Long epochSeconds) {
        if (epochSeconds == null || epochSeconds <= 0) {
            return Instant.now();
        }
        return Instant.ofEpochSecond(epochSeconds);
    }


     private double calculateRiskScore(String sensorId, double deltaN, Instant timestamp) {
        double nonNegativeDeltaN = Math.max(0.0, deltaN);

        // Primary component: absolute infiltration level (soil saturation indicator).
        double deltaComponent = Math.min(1.0, nonNegativeDeltaN / criticalDeltaN) * DELTA_COMPONENT_WEIGHT;
        if (nonNegativeDeltaN >= moderateDeltaN) {
            deltaComponent += MODERATE_DELTA_BONUS;
        }

        // Secondary component: infiltration trend (rapid rise is hazardous on slopes).
        double infiltrationRate = calculateInfiltrationRate(sensorId, nonNegativeDeltaN, timestamp);
        double trendComponent = 0.0;
        if (infiltrationRate > 0) {
            trendComponent = Math.min(1.0, infiltrationRate / criticalRatePerSecond) * TREND_COMPONENT_WEIGHT;
        }

        return Math.min(100.0, Math.max(0.0, deltaComponent + trendComponent));
    }

    private double calculateInfiltrationRate(String sensorId, double currentDeltaN, Instant timestamp) {
        SpectralReading previous = findPreviousReading(sensorId, timestamp);
        if (previous == null || previous.timestamp == null || previous.deltaN == null) {
            return 0.0;
        }

        long elapsedMillis = Math.max(1L, Duration.between(previous.timestamp, timestamp).toMillis());
        double elapsedSeconds = Math.max(MIN_ELAPSED_SECONDS, elapsedMillis / 1000.0);
        return (currentDeltaN - previous.deltaN) / elapsedSeconds;
    }

    private SpectralReading findPreviousReading(String sensorId, Instant timestamp) {
        return SpectralReading.find(
            "sensorId = ?1 and timestamp < ?2 order by timestamp desc",
            sensorId,
            timestamp
        ).firstResult();
    }

     @Transactional
    Uni<Void> checkAndCreateAlert(SpectralReading reading) {
        if (reading.riskScore < alertThreshold) {
            return Uni.createFrom().voidItem();
        }
        return Uni.createFrom().item(() -> {
            double infiltrationRate = Math.max(
                0.0,
                calculateInfiltrationRate(reading.sensorId, reading.deltaN, reading.timestamp)
            );
            String severity = reading.riskScore >= criticalThreshold ? "CRITICAL" : "HIGH";
            Alert alert = new Alert();
            alert.sensorId = reading.sensorId;
            alert.timestamp = reading.timestamp;
            alert.alertType = "LANDSLIDE_SOIL_MOISTURE_RISK";
            alert.severity = severity;
            alert.alertMessage = String.format(
                "Potential landslide risk detected: sensor=%s, delta_n=%.6f, infiltration_rate=%.8f/s, risk_score=%.2f",
                reading.sensorId, reading.deltaN, infiltrationRate, reading.riskScore
            );
            alert.acknowledged = false;
                 return alert;
        })
        .invoke(alert -> alert.persist())
        .invoke(alert -> 
            LOG.warnf("🚨 Alert created for sensor %s - %s severity (risk: %.2f)", 
                alert.sensorId, alert.severity, reading.riskScore)
        )
        .replaceWithVoid();
    }


    public Map<String,Boolean> getStreamStatus(){
        Map<String,Boolean> status = new HashMap<>();
        sensorIds.forEach(sensorId ->
            status.put(sensorId,activeStreams.containsKey(sensorId))
        );
        return status;
    }
}