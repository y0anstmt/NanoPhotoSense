package org.acme.resource;

import java.util.List;

import org.acme.domain.Alert;
import org.jboss.logging.Logger;

import io.quarkus.panache.common.Page;
import io.quarkus.panache.common.Sort;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/api/alerts")
@Produces(MediaType.APPLICATION_JSON)
public class AlertResource {
    
    private static final Logger LOG = Logger.getLogger(AlertResource.class);
    private static final int DEFAULT_PAGE_SIZE = 20;

    @GET
    public Response listAlerts(
            @QueryParam("acknowledged") Boolean acknowledged,
            @QueryParam("page") Integer page,
            @QueryParam("size") Integer size) {
        
        int pageNumber = page != null ? page : 0;
        int pageSize = size != null ? size : DEFAULT_PAGE_SIZE;
        
        List<Alert> alerts;
        long totalCount;
        
        if (acknowledged != null) {
            alerts = Alert
                .find("acknowledged = ?1", Sort.descending("timestamp"), acknowledged)
                .page(Page.of(pageNumber, pageSize))
                .list();
            totalCount = Alert.count("acknowledged", acknowledged);
        } else {
            alerts = Alert
                .findAll(Sort.descending("timestamp"))
                .page(Page.of(pageNumber, pageSize))
                .list();
            totalCount = Alert.count();
        }
        
        LOG.infof("Retrieved %d alerts (acknowledged=%s)", alerts.size(), acknowledged);
        
        return Response.ok()
            .entity(alerts)
            .header("X-Total-Count", totalCount)
            .build();
    }

    
    @GET
    @Path("/{id}")
    public Response getAlert(@PathParam("id") Long id) {
        Alert alert = Alert.findById(id);
        
        if (alert == null) {
            LOG.warnf("Alert not found: %d", id);
            return Response.status(Response.Status.NOT_FOUND)
                .entity("{\"error\": \"Alert not found\"}")
                .build();
        }
        
        return Response.ok(alert).build();
    }

    
    @PUT
    @Path("/{id}/acknowledge")
    @Transactional
    public Response acknowledgeAlert(@PathParam("id") Long id) {
        Alert alert = Alert.findById(id);
        
        if (alert == null) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }
        
        if (alert.acknowledged) {
            LOG.infof("Alert %d already acknowledged", id);
            return Response.status(Response.Status.CONFLICT)
                .entity("{\"message\": \"Alert already acknowledged\"}")
                .build();
        }
        
        alert.acknowledged = true;
        alert.persist();
        
        LOG.infof("✓ Alert %d acknowledged (sensor: %s, severity: %s)", 
            id, alert.sensorId, alert.severity);
        
        return Response.ok(alert).build();
    }

    @DELETE
    @Path("/{id}")
    @Transactional
    public Response deleteAlert(@PathParam("id") Long id) {
        boolean deleted = Alert.deleteById(id);
        
        if (!deleted) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }
        
        LOG.infof("Deleted alert: %d", id);
        return Response.noContent().build();
    }

    @GET
    @Path("/sensor/{sensorId}")
    public Response getAlertsBySensor(@PathParam("sensorId") String sensorId) {
        List<Alert> alerts = Alert
            .find("sensorId = ?1", Sort.descending("timestamp"), sensorId)
            .list();
        
        LOG.infof("Retrieved %d alerts for sensor %s", alerts.size(), sensorId);
        
        return Response.ok(alerts).build();
    }
}