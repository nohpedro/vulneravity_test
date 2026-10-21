package security;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.qameta.allure.*;
import io.restassured.builder.RequestSpecBuilder;
import io.restassured.response.Response;
import io.restassured.specification.RequestSpecification;
import org.junit.jupiter.api.*;
import java.nio.file.*;
import java.time.OffsetDateTime;
import java.util.*;
import static io.restassured.RestAssured.given;
import static org.junit.jupiter.api.Assertions.*;

@Epic("Seguridad del flujo de negocio")
@Feature("Integridad del carrito")
public class NegativeQuantityTest {
    private final ObjectMapper json = new ObjectMapper();
    private RequestSpecification spec;
    private String token;
    private Integer basketId, itemId;
    private final Map<String, Object> result = new LinkedHashMap<>();

    private RequestSpecification request() {
        var r = given().spec(spec);
        return token == null ? r : r.header("Authorization", "Bearer " + token);
    }

    private void evidence(String name, Response r) {
        // Only basket/product responses are attached. Never attach authentication secrets.
        Allure.addAttachment(name, "application/json", r.asPrettyString(), ".json");
    }

    @Test
    @DisplayName("TC-BL-001 | Reproducir aceptación de cantidad negativa en carrito")
    @Story("Un comprador modifica únicamente su propio carrito")
    @Severity(SeverityLevel.CRITICAL)
    @Description("PASS en modo reproduce confirma la debilidad; no significa que la aplicación sea segura. El modo secure exige rechazo y ausencia de persistencia.")
    void negativeQuantityInOwnBasket() throws Exception {
        String base = System.getProperty("baseUrl", "http://juice-shop:3000");
        String mode = System.getProperty("expectation", "reproduce");
        assertTrue(Set.of("reproduce", "secure").contains(mode), "expectation: reproduce o secure");
        var uri = java.net.URI.create(base);
        assertTrue(Set.of("juice-shop", "localhost", "127.0.0.1").contains(uri.getHost()),
                "Este laboratorio está limitado a Juice Shop local");
        spec = new RequestSpecBuilder().setBaseUri(base).setContentType("application/json")
                .setProxy("127.0.0.1", Integer.getInteger("proxyPort", 8090))
                .setConfig(io.restassured.config.RestAssuredConfig.config().httpClient(
                    io.restassured.config.HttpClientConfig.httpClientConfig()
                        .setParam("http.connection.timeout", 20000).setParam("http.socket.timeout", 20000)))
                .build();
        result.put("caseId", "TC-BL-001"); result.put("startedAt", OffsetDateTime.now().toString());
        result.put("baseUrl", base); result.put("expectation", mode);
        String email = "qa-" + UUID.randomUUID() + "@example.invalid";
        String password = "Lab!" + UUID.randomUUID();
        try {
            Allure.step("1. Crear usuario efímero e iniciar sesión", () -> {
                request().body(Map.of("email", email, "password", password, "passwordRepeat", password,
                        "securityQuestion", Map.of("id", 1, "question", "Your eldest siblings middle name?"),
                        "securityAnswer", "laboratorio")).post("/api/Users").then().statusCode(201);
                Response login = request().body(Map.of("email", email, "password", password)).post("/rest/user/login");
                login.then().statusCode(200);
                token = login.jsonPath().getString("authentication.token");
                basketId = login.jsonPath().getInt("authentication.bid");
                assertNotNull(token); assertNotNull(basketId);
                result.put("basketId", basketId);
            });
            Allure.step("2. Control positivo: agregar una unidad y verificar persistencia", () -> {
                Response created = request().body(Map.of("ProductId", 1, "BasketId", basketId, "quantity", 1))
                        .post("/api/BasketItems");
                created.then().statusCode(200);
                itemId = created.jsonPath().getInt("data.id");
                Response before = request().get("/rest/basket/" + basketId);
                before.then().statusCode(200); evidence("Carrito antes de la manipulación", before);
                int initial = before.jsonPath().getInt("data.Products[0].BasketItem.quantity");
                assertEquals(1, initial); result.put("quantityBefore", initial); result.put("itemId", itemId);
            });
            Allure.step("3. Enviar quantity=-1 directamente a la API", () -> {
                Allure.addAttachment("Petición de prueba", "application/json", "{\"quantity\":-1}", ".json");
                Response changed = request().body(Map.of("quantity", -1)).put("/api/BasketItems/" + itemId);
                result.put("mutationHttpStatus", changed.statusCode()); evidence("Respuesta a cantidad negativa", changed);
                Response after = request().get("/rest/basket/" + basketId);
                after.then().statusCode(200); evidence("Lectura independiente del carrito", after);
                int observed = after.jsonPath().getInt("data.Products[0].BasketItem.quantity");
                float price = after.jsonPath().getFloat("data.Products[0].price");
                result.put("quantityAfter", observed); result.put("unitPrice", price);
                result.put("calculatedLineTotal", observed * price);
                boolean vulnerable = changed.statusCode() / 100 == 2 && observed == -1;
                result.put("securityVerdict", vulnerable ? "VULNERABLE" : "NOT_REPRODUCED");
                if (mode.equals("reproduce")) {
                    assertEquals(200, changed.statusCode(), "La reproducción exige aceptación HTTP 200");
                    assertEquals(-1, observed, "La reproducción exige persistencia negativa comprobada por GET");
                } else {
                    assertTrue(Set.of(400, 422).contains(changed.statusCode()), "Debe rechazar la cantidad inválida");
                    assertEquals(1, observed, "Debe conservar la cantidad válida");
                    result.put("securityVerdict", "REJECTED_AS_EXPECTED");
                }
            });
        } finally {
            try {
                if (itemId != null) {
                    Allure.step("4. Restablecer cantidad válida y comprobar limpieza", () -> {
                        request().body(Map.of("quantity", 1)).put("/api/BasketItems/" + itemId).then().statusCode(200);
                        Response cleaned = request().get("/rest/basket/" + basketId);
                        cleaned.then().statusCode(200);
                        assertEquals(1, cleaned.jsonPath().getInt("data.Products[0].BasketItem.quantity"));
                        result.put("cleanup", "quantity_restored_to_1");
                    });
                }
            } finally {
                result.put("finishedAt", OffsetDateTime.now().toString());
                Files.createDirectories(Path.of("target"));
                String report = json.writerWithDefaultPrettyPrinter().writeValueAsString(result);
                Files.writeString(Path.of("target/business-result.json"), report);
                Allure.addAttachment("Resultado y veredicto de seguridad", "application/json", report, ".json");
                System.out.println("TC-BL-001: " + result.getOrDefault("securityVerdict", "INCOMPLETE"));
            }
        }
    }
}
