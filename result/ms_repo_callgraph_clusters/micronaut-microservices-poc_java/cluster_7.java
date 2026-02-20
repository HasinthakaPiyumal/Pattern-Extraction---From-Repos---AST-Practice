// Cluster 7

package pl.altkom.asc.lab.micronaut.poc.policy;

import io.micronaut.runtime.Micronaut;

public class PolicyApplication {

    public static void main(String[] args) {
        Micronaut.run(PolicyApplication.class);
    }
}

// Node: main
// Node: run
package pl.altkom.asc.lab.micronaut.poc.policy;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.domain.Offer;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferStatus;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.dto.PersonDto;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

import io.micronaut.context.ApplicationContext;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class PolicyControllerTest {

    private static EmbeddedServer server;
    private static PolicyTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(PolicyTestClient.class, server.getURL());
    }

    @Test
    public void testGetPolicyByNumber() {
        String policyNumber = "1234";
        GetPolicyDetailsQueryResult policy = client.get(policyNumber);

        assertNotNull(policy);
        assertNotNull(policy.getPolicy());
        assertEquals(policyNumber, policy.getPolicy().getNumber());
    }

    @Test
    public void testCreatePolicy() {
        //given: offer with number 111 exists
        Map<String, BigDecimal> coverPrices = new HashMap<>();
        coverPrices.put("C1", new BigDecimal("100"));
        coverPrices.put("C2", new BigDecimal("99"));
        Offer offer111 = new Offer(
                null,
                "111",
                "TRI",
                LocalDate.of(2018, 8, 1),
                LocalDate.of(2018, 8, 10),
                new HashMap<>(),
                new BigDecimal("199"),
                coverPrices,
                OfferStatus.NEW,
                LocalDate.now()
        );
        server.getApplicationContext().getBean(OfferRepository.class).save(offer111);

        //when policy creation is requested
        CreatePolicyCommand cmd = new CreatePolicyCommand(
                "111",
                new PersonDto("Timmy", "Lamb", "111111111116"),
                "admin");

        CreatePolicyResult result = client.create(cmd);

        //then policy is created and number is assigned
        assertNotNull(result);
        assertNotNull(result.getPolicyNumber());
    }

    @AfterAll
    public static void cleanup() {
        if (server != null)
            server.stop();

    }
}


// Node: setup
// Node: getApplicationContext
// Node: createBean
// Node: getURL
package pl.altkom.asc.lab.micronaut.poc.policy;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.Health;

import io.micronaut.context.ApplicationContext;
import io.micronaut.http.HttpStatus;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class HelloControllerTest {

    private static EmbeddedServer server;
    private static HelloTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(HelloTestClient.class, server.getURL());
    }

    @AfterAll
    public static void cleanup() {
        if (server != null) {
            server.stop();
        }
    }

    @Test
    public void testIndex() {
        assertEquals(HttpStatus.OK, client.index());
    }

    @Test
    public void testVersion() {
        Health actualInfo = client.version();
        Health expectedInfo = new Health("1.0", "OK");

        assertEquals(expectedInfo.toString(), actualInfo.toString());
        assertEquals(expectedInfo.getStatus(), actualInfo.getStatus());
        assertEquals(expectedInfo.getVer(), actualInfo.getVer());
    }
}


package pl.altkom.asc.lab.micronaut.poc.auth;

import io.micronaut.runtime.Micronaut;

public class AuthApplication {

    public static void main(String[] args) {
        Micronaut.run(AuthApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc.pricing;

import io.micronaut.runtime.Micronaut;

public class PricingApplication {

    public static void main(String[] args) {
        Micronaut.run(PricingApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc.pricing;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.ChoiceQuestionAnswer;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.NumericQuestionAnswer;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;

import javax.validation.ConstraintViolationException;

import io.micronaut.context.ApplicationContext;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;


public class PricingControllerTest {

    private static EmbeddedServer server;
    private static PricingTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(PricingTestClient.class, server.getURL());
    }

    @Test
    public void exceptionWhenCommandIsNull() {
        assertThrows(ConstraintViolationException.class, () -> client.calculatePrice(null));
    }

    @Test
    public void canCalculateTravelPolicyPrice() {
        CalculatePriceCommand cmd = new CalculatePriceCommand(
                "TRI",
                LocalDate.of(2017, 4, 16),
                LocalDate.of(2018, 4, 15),
                Arrays.asList("C1", "C2"),
                Arrays.asList(
                        new NumericQuestionAnswer("NUM_OF_ADULTS", new BigDecimal("1")),
                        new NumericQuestionAnswer("NUM_OF_CHILDREN", new BigDecimal("1")),
                        new ChoiceQuestionAnswer("DESTINATION", "EUR")
                )
        );

        CalculatePriceResult result = client.calculatePrice(cmd);

        assertNotNull(result);
        assertEquals(new BigDecimal("78"), result.getTotalPrice(),"Total premium should be 78");
        assertEquals(new BigDecimal("26"), result.getCoversPrices().get("C1"),"C1 premium should be 26");
        assertEquals(new BigDecimal("52"), result.getCoversPrices().get("C2"),"C2 should be 52");
    }

    @Test
    public void canCalculateHousePolicyPrice() {
        CalculatePriceCommand cmd = new CalculatePriceCommand(
                "HSI",
                LocalDate.of(2017, 4, 16),
                LocalDate.of(2018, 4, 15),
                Arrays.asList("C1", "C2", "C3"),
                Arrays.asList(
                        new NumericQuestionAnswer("AREA", new BigDecimal("95")),
                        new NumericQuestionAnswer("NUM_OF_CLAIM", new BigDecimal("1")),
                        new ChoiceQuestionAnswer("FLOOD", "NO"),
                        new ChoiceQuestionAnswer("TYP", "APT")
                )
        );

        CalculatePriceResult result = client.calculatePrice(cmd);

        assertNotNull(result);
        assertEquals(new BigDecimal("172.50"), result.getTotalPrice(),"Total premium should be 172.50");
        assertEquals(new BigDecimal("118.75"), result.getCoversPrices().get("C1"),"C1 premium should be 118.75");
        assertEquals(new BigDecimal("23.75"), result.getCoversPrices().get("C2"),"C2 should be 23.75");
        assertEquals(new BigDecimal("30"), result.getCoversPrices().get("C3"),"C3 should be 30");
    }

    @AfterAll
    public static void cleanup() {
        if (server != null)
            server.stop();
    }
}


package pl.altkom.asc.lab.micronaut.poc.dashboard;

import io.micronaut.runtime.Micronaut;

public class DashboardApplication {
    public static void main(String[] args) {
        Micronaut.run(DashboardApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc.product.service;

import io.micronaut.runtime.Micronaut;

public class ProductApplication {

    public static void main(String[] args) {
        Micronaut.run(ProductApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc.payment;

import io.micronaut.runtime.Micronaut;

public class PaymentApplication {

    public static void main(String[] args) {
        Micronaut.run(PaymentApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc.gateway;

import io.micronaut.runtime.Micronaut;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Contact;
import io.swagger.v3.oas.annotations.info.Info;

@OpenAPIDefinition(
        info = @Info(
                title = "LAB Insurance Sales Portal API",
                version = "1.0",
                contact = @Contact(url = "http://altkomsoftware.pl", name = "ASCLAB", email = "lab@altkomsoftware.pl")
        )
)
public class AgentPortalGatewayApplication {
    public static void main(String[] args) {
        Micronaut.run(AgentPortalGatewayApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc.chat.service;

import io.micronaut.runtime.Micronaut;

public class ChatApplication {

    public static void main(String[] args) {
        Micronaut.run(ChatApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc.policy.search;

import io.micronaut.runtime.Micronaut;

public class PolicySearchApplication {

    public static void main(String[] args) {
        Micronaut.run(PolicySearchApplication.class);
    }
}

package pl.altkom.asc.lab.micronaut.poc;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;

import io.micronaut.context.ApplicationContext;
import io.micronaut.runtime.server.EmbeddedServer;

public class PolicySearchControllerTest {

    private static EmbeddedServer server;
    private static PolicySearchTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(PolicySearchTestClient.class, server.getURL());
    }

    @Test
    public void testPolicies() {
        FindPolicyQueryResult policies = client.policies("1234").blockingGet();

        Assertions.assertNotNull(policies);
        Assertions.assertNotNull(policies.getPolicies());
        Assertions.assertFalse(policies.getPolicies().isEmpty());
    }

    @AfterAll
    public static void cleanup() {
        if (server != null)
            server.stop();

    }
}


