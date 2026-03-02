package org.acme.resource;

import java.util.List;

import org.acme.domain.SpectralReading;
import org.jboss.logging.Logger;

import io.quarkus.panache.common.Page;
import io.quarkus.panache.common.Sort;
import jakarta.transaction.Transactional;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/api/spectral-readings")
@Produces(MediaType.APPLICATION_JSON)
public class SpectralReadingResource {
    
    private static final Logger LOG = Logger.getLogger(SpectralReadingResource.class);
    private static final int DEFAULT_PAGE_SIZE = 20;

    @GET
    public Response listReadings(
            @QueryParam("page") Integer page,
            @QueryParam("size") Integer size) {
        
        int pageNumber = page != null ? page : 0;
        int pageSize = size != null ? size : DEFAULT_PAGE_SIZE;
        
        List<SpectralReading> readings = SpectralReading
            .findAll(Sort.descending("timestamp"))
            .page(Page.of(pageNumber, pageSize))
            .list();
        
        long totalCount = SpectralReading.count();
        
        LOG.infof("Retrieved %d readings (page %d, size %d)", readings.size(), pageNumber, pageSize);
        
        return Response.ok()
            .entity(readings)
            .header("X-Total-Count", totalCount)
            .header("X-Page-Number", pageNumber)
            .header("X-Page-Size", pageSize)
            .build();
    }

    
    @GET
    @Path("/{id}")
    public Response getReading(@PathParam("id") Long id) {
        SpectralReading reading = SpectralReading.findById(id);
        
        if (reading == null) {
            LOG.warnf("Reading not found: %d", id);
            return Response.status(Response.Status.NOT_FOUND)
                .entity("{\"error\": \"Reading not found\"}")
                .build();
        }
        
        return Response.ok(reading).build();
    }


    @GET
    @Path("/sensor/{sensorId}")
    public Response getReadingsBySensor(
            @PathParam("sensorId") String sensorId,
            @QueryParam("page") Integer page,
            @QueryParam("size") Integer size) {
        
        int pageNumber = page != null ? page : 0;
        int pageSize = size != null ? size : DEFAULT_PAGE_SIZE;
        
        List<SpectralReading> readings = SpectralReading
            .find("sensorId = ?1", Sort.descending("timestamp"), sensorId)
            .page(Page.of(pageNumber, pageSize))
            .list();
        
        long totalCount = SpectralReading.count("sensorId", sensorId);
        
        LOG.infof("Retrieved %d readings for sensor %s", readings.size(), sensorId);
        
        return Response.ok()
            .entity(readings)
            .header("X-Total-Count", totalCount)
            .header("X-Sensor-Id", sensorId)
            .build();
    }

    @GET
    @Path("/latest")
    public Response getLatestReadings(@QueryParam("limit") Integer limit) {
        int resultLimit = limit != null ? limit : 10;
        
        List<SpectralReading> readings = SpectralReading
            .findAll(Sort.descending("timestamp"))
            .page(Page.ofSize(resultLimit))
            .list();
        
        LOG.infof("Retrieved %d latest readings", readings.size());
        
        return Response.ok(readings).build();
    }

    @DELETE
    @Path("/{id}")
    @Transactional
    public Response deleteReading(@PathParam("id") Long id) {
        boolean deleted = SpectralReading.deleteById(id);
        
        if (!deleted) {
            return Response.status(Response.Status.NOT_FOUND).build();
        }
        
        LOG.infof("Deleted reading: %d", id);
        return Response.noContent().build();
    }
}