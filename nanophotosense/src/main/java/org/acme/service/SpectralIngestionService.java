package org.acme.service;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.acme.client.PhysicsAPIClient;
import org.eclipse.microprofile.rest.client.inject.RestClient;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.logging.Logger;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.quarkus.runtime.StartupEvent;
import io.quarkus.runtime.ShutdownEvent;
import io.smallrye.mutiny.subscription.Cancellable;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.enterprise.event.Observes;
import jakarta.inject.Inject;

@ApplicationScoped
public class SpectralIngestionService {
    @Inject
    @RestClient
    PhysicsAPIClient physicsAPIClient;

    @Inject
    ObjectMapper objectMapper;

    private static final Logger LOG = Logger.getLogger(SpectralIngestionService.class);

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
        // TODO: Implementare în pasul următor
        LOG.debugf("startStream() called for sensor: %s", sensorId);
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
}