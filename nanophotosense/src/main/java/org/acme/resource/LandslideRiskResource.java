package org.acme.resource;

import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.acme.domain.SpectralReading;
import org.jboss.logging.Logger;

import io.quarkus.hibernate.orm.panache.Panache;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

@Path("/api/landslide-risk")
@Produces(MediaType.APPLICATION_JSON)
public class LandslideRiskResource {

    private static final Logger LOG = Logger.getLogger(LandslideRiskResource.class);

    @GET
    @Path("/sensor/{sensorId}")
    public Response getSensorRisk(
            @PathParam("sensorId") String sensorId,
            @QueryParam("windowMinutes") Integer windowMinutes) {

        int minutes = windowMinutes != null && windowMinutes > 0 ? windowMinutes : 60;
        SpectralReading latest = SpectralReading
            .find("sensorId = ?1 order by timestamp desc", sensorId)
            .firstResult();

        if (latest == null) {
            return Response.status(Response.Status.NOT_FOUND)
                .entity(Map.of("error", "No readings found for sensor", "sensorId", sensorId))
                .build();
        }

        Instant windowStart = Instant.now().minus(Duration.ofMinutes(minutes));
        List<SpectralReading> windowReadings = SpectralReading
            .find("sensorId = ?1 and timestamp >= ?2 order by timestamp asc", sensorId, windowStart)
            .list();

        Map<String, Object> result = buildRiskSummary(sensorId, latest, windowReadings, minutes);

        LOG.infof("Computed landslide risk summary for sensor %s (window=%d min)", sensorId, minutes);
        return Response.ok(result).build();
    }

    @GET
    @Path("/overview")
    public Response getOverview(@QueryParam("windowMinutes") Integer windowMinutes) {
        int minutes = windowMinutes != null && windowMinutes > 0 ? windowMinutes : 60;
        Instant windowStart = Instant.now().minus(Duration.ofMinutes(minutes));

        List<String> sensorIds = Panache.getEntityManager()
            .createQuery("select distinct s.sensorId from SpectralReading s", String.class)
            .getResultList();

        List<Map<String, Object>> sensors = sensorIds.stream().map(sensorId -> {
            SpectralReading latest = SpectralReading
                .find("sensorId = ?1 order by timestamp desc", sensorId)
                .firstResult();

            List<SpectralReading> windowReadings = SpectralReading
                .find("sensorId = ?1 and timestamp >= ?2 order by timestamp asc", sensorId, windowStart)
                .list();

            return buildRiskSummary(sensorId, latest, windowReadings, minutes);
        }).toList();

        long highOrCritical = sensors.stream()
            .filter(sensor -> {
                String level = (String) sensor.get("riskLevel");
                return "HIGH".equals(level) || "CRITICAL".equals(level);
            })
            .count();

        return Response.ok(Map.of(
            "windowMinutes", minutes,
            "sensorCount", sensors.size(),
            "highOrCriticalCount", highOrCritical,
            "sensors", sensors
        )).build();
    }

    private Map<String, Object> buildRiskSummary(
            String sensorId,
            SpectralReading latest,
            List<SpectralReading> windowReadings,
            int windowMinutes) {

        double trendPerHour = 0.0;
        if (windowReadings.size() >= 2) {
            SpectralReading first = windowReadings.get(0);
            SpectralReading last = windowReadings.get(windowReadings.size() - 1);

            double delta = last.deltaN - first.deltaN;
            long seconds = Math.max(1L, Duration.between(first.timestamp, last.timestamp).toSeconds());
            trendPerHour = delta / seconds * 3600.0;
        }

        double meanRisk = windowReadings.isEmpty()
            ? latest.riskScore
            : windowReadings.stream().mapToDouble(reading -> reading.riskScore).average().orElse(latest.riskScore);

        Map<String, Object> result = new HashMap<>();
        result.put("sensorId", sensorId);
        result.put("windowMinutes", windowMinutes);
        result.put("latestTimestamp", latest.timestamp);
        result.put("latestDeltaN", latest.deltaN);
        result.put("latestRiskScore", latest.riskScore);
        result.put("riskLevel", toRiskLevel(latest.riskScore));
        result.put("deltaNTrendPerHour", trendPerHour);
        result.put("meanRiskScore", meanRisk);
        result.put("readingsInWindow", windowReadings.size());

        return result;
    }

    private String toRiskLevel(double riskScore) {
        if (riskScore >= 95.0) {
            return "CRITICAL";
        }
        if (riskScore >= 80.0) {
            return "HIGH";
        }
        if (riskScore >= 55.0) {
            return "MODERATE";
        }
        return "LOW";
    }
}
