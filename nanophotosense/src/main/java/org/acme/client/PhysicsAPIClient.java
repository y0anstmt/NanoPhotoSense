package org.acme.client;

import org.acme.dto.SpectrumStreamData;
import org.eclipse.microprofile.rest.client.inject.RegisterRestClient;

import io.quarkus.rest.client.reactive.jackson.ClientObjectMapper;
import io.smallrye.mutiny.Multi;
import jakarta.enterprise.inject.Produces;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;

@RegisterRestClient(configKey = "physics-api")
public interface PhysicsAPIClient {
    @GET
    @Produces(MediaType.SERVER_SENT_EVENTS)
    Multi<SpectrumStreamData> streamSpectral(@QueryParam("sensor_id") String sensorId);
}
