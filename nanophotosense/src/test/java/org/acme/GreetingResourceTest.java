package org.acme;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.is;

@QuarkusTest
class GreetingResourceTest {
    @Test
    void testHealthEndpoint() {
        given()
                    .when().get("/q/health/live")
          .then()
             .statusCode(200)
             .body("status", is("UP"));
    }

}