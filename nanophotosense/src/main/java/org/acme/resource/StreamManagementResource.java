package org.acme.resource;

import java.util.Map;

import org.acme.service.SpectralIngestionService;
import org.jboss.logging.Logger;

import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/api/streams")
@Produces(MediaType.APPLICATION_JSON)
public class StreamManagementResource {
    
    private static final Logger LOG = Logger.getLogger(StreamManagementResource.class);
    
    @Inject
    SpectralIngestionService ingestionService;

    @POST
    @Path("/{sensorId}/start")
    public Response startStream(@PathParam("sensorId") String sensorId) {
        try {
            ingestionService.startStream(sensorId);
            
            LOG.infof("Stream start requested for sensor: %s", sensorId);
            
            return Response.ok()
                .entity(Map.of(
                    "message", "Stream started successfully",
                    "sensorId", sensorId,
                    "status", "active"
                ))
                .build();
                
        } catch (Exception e) {
            LOG.errorf(e, "Failed to start stream for sensor: %s", sensorId);
            
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(Map.of(
                    "error", "Failed to start stream",
                    "sensorId", sensorId,
                    "message", e.getMessage()
                ))
                .build();
        }
    }

    @POST
    @Path("/{sensorId}/stop")
    public Response stopStream(@PathParam("sensorId") String sensorId) {
        try {
            ingestionService.stopStream(sensorId);
            
            LOG.infof("Stream stop requested for sensor: %s", sensorId);
            
            return Response.ok()
                .entity(Map.of(
                    "message", "Stream stopped successfully",
                    "sensorId", sensorId,
                    "status", "inactive"
                ))
                .build();
                
        } catch (Exception e) {
            LOG.errorf(e, "Failed to stop stream for sensor: %s", sensorId);
            
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity(Map.of(
                    "error", "Failed to stop stream",
                    "sensorId", sensorId,
                    "message", e.getMessage()
                ))
                .build();
        }
    }

    @GET
    @Path("/status")
    public Response getStreamStatus() {
        Map<String, Boolean> status = ingestionService.getStreamStatus();
        
        long activeCount = status.values().stream().filter(active -> active).count();
        
        LOG.debugf("Stream status retrieved: %d/%d active", activeCount, status.size());
        
        return Response.ok()
            .entity(Map.of(
                "streams", status,
                "totalSensors", status.size(),
                "activeSensors", activeCount
            ))
            .build();
    }
}