package org.acme.client;

import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import io.smallrye.mutiny.Multi;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@RegisterRestClient(configKey = "physics-api")
public interface PhysicsAPIClient {
    @GET
    @Path("/spectrum/stream")
    @Produces(MediaType.SERVER_SENT_EVENTS)
    Multi<String> streamSpectral(@QueryParam("sensor_id") String sensorId);

    @GET
    @Path("/health")
    @Produces(MediaType.TEXT_PLAIN)
    String healthcheck();
}
