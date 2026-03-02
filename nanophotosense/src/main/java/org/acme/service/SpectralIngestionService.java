package org.acme.service;

import java.time.Duration;
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
    private static final double RISK_SCORE_SCALING_FACTOR = 5000.0;
    private static final double ALERT_THRESHOLD = 80.0;
    private static final double CRITICAL_THRESHOLD = 95.0;

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
            LOG.warnf("Stream alredy active for sensor %s, skipping",sensorId);
            return;
        }
        Cancellable cancellable = physicsAPIClient.streamSpectral(sensorId)
            .onOverflow().buffer(100)
            .onItem().transformToUniAndMerge(data ->
                processAndSave(data)
                .onFailure().invoke(failure ->
                    LOG.errorf(failure,"Failed to process data for sensor %s",sensorId)
                )
            )
            .onFailure().retry()
                  .withBackOff(Duration.ofSeconds(2),Duration.ofMinutes(1))
                  .atMost(5)
            .subscribe().with(
                savedReading -> LOG.debugf("✓ Saved reading for sensor %s at %s (risk: %.2f)", 
                    savedReading.sensorId, savedReading.timestamp, savedReading.riskScore),
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
            double riskScore = calculateRiskScore(data.getDeltaN());
            String intensitiesJson;
            try {
                intensitiesJson = objectMapper.writeValueAsString(data.getIntensities());
            } catch (JsonProcessingException e) {
                LOG.errorf(e, "Failed to serialize intensities for sensor %s", data.getSensorId());
                intensitiesJson = "[]"; 
            }
            SpectralReading reading = new SpectralReading();
            reading.sensorId = data.getSensorId();
            reading.timestamp = data.getTimestamp();
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
            if (reading.riskScore >= ALERT_THRESHOLD) {
                LOG.warnf("⚠ HIGH RISK detected for sensor %s: delta_n=%.6f, risk=%.2f", 
                    reading.sensorId, reading.deltaN, reading.riskScore);
            }
        });
    }


     private double calculateRiskScore(double deltaN) {
        double score = deltaN * RISK_SCORE_SCALING_FACTOR;
        return Math.min(100.0, Math.max(0.0, score));
    }

     @Transactional
    Uni<Void> checkAndCreateAlert(SpectralReading reading) {
        if (reading.riskScore < ALERT_THRESHOLD) {
            return Uni.createFrom().voidItem();
        }
        return Uni.createFrom().item(() -> {
            String severity = reading.riskScore >= CRITICAL_THRESHOLD ? "CRITICAL" : "HIGH";
            Alert alert = new Alert();
            alert.sensorId = reading.sensorId;
            alert.timestamp = reading.timestamp;
            alert.alertType = "HIGH_RISK_INFILTRATION";
            alert.severity = severity;
            alert.alertMessage = String.format(
                "Bacterial infiltration detected: sensor=%s, delta_n=%.6f, risk_score=%.2f", 
                reading.sensorId, reading.deltaN, reading.riskScore
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