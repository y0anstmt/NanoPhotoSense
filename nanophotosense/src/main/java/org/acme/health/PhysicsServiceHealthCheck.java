package org.acme.health;

import org.acme.client.PhysicsAPIClient;
import org.eclipse.microprofile.health.HealthCheck; 
import org.eclipse.microprofile.health.HealthCheckResponse;  
import org.eclipse.microprofile.health.Readiness;
import org.eclipse.microprofile.rest.client.inject.RestClient;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

@Readiness
@ApplicationScoped
public class PhysicsServiceHealthCheck implements HealthCheck {
    @Inject
    @RestClient
    PhysicsAPIClient physicsAPIClient;

    @Override
    public HealthCheckResponse call(){
        try {
            String response = physicsAPIClient.healthcheck();
            return HealthCheckResponse
                .named("physics-service")
                .up()
                .withData("response", response)
                .build();
        } catch(Exception e){
            return HealthCheckResponse
                .named("physics-service")
                .down()
                .withData("error", e.getMessage())
                .withData("type",e.getClass().getSimpleName())
                .build();
        }
    }
}