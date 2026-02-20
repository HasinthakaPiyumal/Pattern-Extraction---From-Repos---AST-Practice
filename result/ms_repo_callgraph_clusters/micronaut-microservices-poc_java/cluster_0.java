// Cluster 0

package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import javax.validation.constraints.NotNull;

public interface PolicyOperations {

    @Get("/{policyNumber}")
    GetPolicyDetailsQueryResult get(@NotNull String policyNumber);

    @Post
    CreatePolicyResult create(@Body @NotNull CreatePolicyCommand cmd);

    @Post("/terminate")
    TerminatePolicyResult terminate(@Body @NotNull TerminatePolicyCommand cmd);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/service/api/v1/PolicyOperations.java:PolicyOperations.<init>
// Node: Get
// Node: create
// Node: Post
// Node: terminate
package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Post;
import javax.validation.constraints.NotNull;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferResult;

public interface OfferOperations {
    @Post("/")
    CreateOfferResult create(@Body @NotNull CreateOfferCommand cmd);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/service/api/v1/OfferOperations.java:OfferOperations.<init>
package pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Post;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;

import javax.validation.constraints.NotNull;

public interface PricingOperations {

    @Post("/calculate")
    CalculatePriceResult calculatePrice(@Body @NotNull CalculatePriceCommand cmd);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/service/api/v1/PricingOperations.java:PricingOperations.<init>
// Node: calculatePrice
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.web;

import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandBus;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.OfferOperations;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferResult;

import io.micronaut.http.annotation.Controller;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import io.micronaut.validation.Validated;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@Validated
@Controller("/offers")
public class OfferController implements OfferOperations {

    private final CommandBus bus;

    @ExecuteOn(TaskExecutors.IO)
    @Override
    public CreateOfferResult create(CreateOfferCommand cmd) {
        return bus.executeCommand(cmd);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/web/OfferController.java:OfferController.<init>
// Node: Controller
// Node: ExecuteOn
// Node: executeCommand
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.web;

import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandBus;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.PolicyOperations;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQuery;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import io.micronaut.http.annotation.Controller;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import io.micronaut.validation.Validated;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@Validated
@Controller("/policies")
public class PolicyController implements PolicyOperations {

    private final CommandBus bus;

    @ExecuteOn(TaskExecutors.IO)
    @Override
    public GetPolicyDetailsQueryResult get(String policyNumber) {
        return bus.executeQuery(new GetPolicyDetailsQuery(policyNumber));
    }

    @ExecuteOn(TaskExecutors.IO)
    @Override
    public CreatePolicyResult create(CreatePolicyCommand cmd) {
        return bus.executeCommand(cmd);
    }

    @ExecuteOn(TaskExecutors.IO)
    @Override
    public TerminatePolicyResult terminate(TerminatePolicyCommand cmd) {
        return bus.executeCommand(cmd);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/web/PolicyController.java:PolicyController.<init>
// Node: executeQuery
// Node: GetPolicyDetailsQuery
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.web;

import io.micronaut.http.HttpStatus;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.Health;

@Controller("/hello")
public class HelloController {

    @Get
    public HttpStatus index() {
        return HttpStatus.OK;
    }

    @Get("/version")
    public Health version() {
        return new Health("1.0", "OK");
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/web/HelloController.java:HelloController.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.restclient;

import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.annotation.Client;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.PricingOperations;

@Client(id = "pricing-service")
public interface PricingClient extends PricingOperations {
    @Override
    @Post("/pricing/calculate")
    CalculatePriceResult calculatePrice(CalculatePriceCommand cmd);
}

// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/restclient/PricingClient.java:PricingClient.<init>
// Node: Client
package pl.altkom.asc.lab.micronaut.poc.policy;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.annotation.Client;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

@Client(id = "/policy-service", path = "/policies")
public interface PolicyTestClient {

    @Get("/{policyNumber}")
    GetPolicyDetailsQueryResult get(String policyNumber);

    @Post("/")
    CreatePolicyResult create(@Body CreatePolicyCommand cmd);

    @Post("/terminate")
    TerminatePolicyResult terminate(@Body TerminatePolicyCommand cmd);

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/policy/PolicyTestClient.java:PolicyTestClient.<init>
// Node: just
package pl.altkom.asc.lab.micronaut.poc.auth;

import org.junit.jupiter.api.Test;

import javax.inject.Inject;

import io.micronaut.context.annotation.Property;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.RxHttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.runtime.server.EmbeddedServer;
import io.micronaut.security.authentication.UsernamePasswordCredentials;
import io.micronaut.security.token.jwt.render.BearerAccessRefreshToken;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.fail;

@MicronautTest
@Property(name = "micronaut.server.port", value = "-1")
public class LoginTest {
    @Inject
    private EmbeddedServer server;

    @Inject
    @Client("/")
    private RxHttpClient httpClient;

    @Test
    public void canLoginWithValidCredentials() {
        UsernamePasswordCredentials upc = new UsernamePasswordCredentials("jimmy.solid","secret");
        HttpRequest loginRequest = HttpRequest.POST("/login", upc);
        HttpResponse<BearerAccessRefreshToken> rsp = httpClient.toBlocking().exchange(loginRequest, BearerAccessRefreshToken.class);
        
        assertThat(rsp.getStatus().getCode()).isEqualTo(200);
        assertThat(rsp.getBody().get().getUsername()).isEqualTo("jimmy.solid");
    }
    
    
    @Test
    public void cantLoginWithInvalidCredentials() {
        try {
            UsernamePasswordCredentials upc = new UsernamePasswordCredentials("jimmy.solid","secret111");
            HttpRequest loginRequest = HttpRequest.POST("/login", upc);
            HttpResponse<BearerAccessRefreshToken> rsp = httpClient.toBlocking().exchange(loginRequest, BearerAccessRefreshToken.class);
            fail();
        } catch (HttpClientResponseException ex) {
            assertThat(ex.getStatus().getCode()).isEqualTo(HttpStatus.UNAUTHORIZED.getCode());
        }
        
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/auth/LoginTest.java:LoginTest.<init>
// Node: Property
package pl.altkom.asc.lab.micronaut.poc.auth;

import org.junit.jupiter.api.Test;

import javax.inject.Inject;

import io.micronaut.context.annotation.Property;
import io.micronaut.http.HttpMethod;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.client.RxHttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.runtime.server.EmbeddedServer;
import io.micronaut.security.authentication.Authentication;
import io.micronaut.security.authentication.UsernamePasswordCredentials;
import io.micronaut.security.token.jwt.render.AccessRefreshToken;
import io.micronaut.security.token.jwt.validator.JwtTokenValidator;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import io.reactivex.Flowable;

import static org.assertj.core.api.Assertions.assertThat;

@MicronautTest
@Property(name = "micronaut.server.port", value = "-1")
public class CustomClaimsTest {
    @Inject
    private EmbeddedServer server;

    @Inject
    @Client("/")
    private RxHttpClient httpClient;

    @Test
    public void testCustomClaimsArePresentInJwt() {
        //when:
        HttpRequest request = HttpRequest.create(HttpMethod.POST, "/login")
                .accept(MediaType.APPLICATION_JSON_TYPE)
                .body(new UsernamePasswordCredentials("jimmy.solid", "secret"));
        HttpResponse<AccessRefreshToken> rsp = httpClient.toBlocking().exchange(request, AccessRefreshToken.class);

        //then:
        assertThat(rsp.getStatus().getCode()).isEqualTo(200);
        assertThat(rsp.body()).isNotNull();
        assertThat(rsp.body().getAccessToken()).isNotNull();
        assertThat(rsp.body().getRefreshToken()).isNull();

        //when:
        String accessToken = rsp.body().getAccessToken();
        JwtTokenValidator tokenValidator = server.getApplicationContext().getBean(JwtTokenValidator.class);
        Authentication authentication = Flowable
                .fromPublisher(tokenValidator.validateToken(accessToken,request))
                .blockingFirst();

        //then:
        assertThat(authentication.getAttributes()).isNotNull();
        assertThat(authentication.getAttributes()).containsKey("roles");
        assertThat(authentication.getAttributes()).containsKey("iss");
        assertThat(authentication.getAttributes()).containsKey("exp");
        assertThat(authentication.getAttributes()).containsKey("iat");
        assertThat(authentication.getAttributes()).containsKey("avatar");
        assertThat(authentication.getAttributes().get("avatar")).isEqualTo("static/avatars/jimmy_solid.png");
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/auth/CustomClaimsTest.java:CustomClaimsTest.<init>
package pl.altkom.asc.lab.micronaut.poc.auth;

import org.junit.jupiter.api.Test;

import javax.inject.Inject;

import io.micronaut.context.annotation.Property;
import io.micronaut.http.HttpMethod;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.client.RxHttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.runtime.server.EmbeddedServer;
import io.micronaut.security.authentication.UsernamePasswordCredentials;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;

import static org.assertj.core.api.Assertions.assertThat;

@MicronautTest
@Property(name = "micronaut.server.port", value = "-1")
public class CustomLoginHandlerTest {
    @Inject
    private EmbeddedServer server;

    @Inject
    @Client("/")
    private RxHttpClient httpClient;

    @Test
    public void customLoginHandler() {
        //when:
        HttpRequest request = HttpRequest.create(HttpMethod.POST, "/login")
                .accept(MediaType.APPLICATION_JSON_TYPE)
                .body(new UsernamePasswordCredentials("jimmy.solid", "secret"));
        HttpResponse<CustomBearerAccessRefreshToken> rsp = httpClient.toBlocking().exchange(request, CustomBearerAccessRefreshToken.class);

        //then:
        assertThat(rsp.getStatus().getCode()).isEqualTo(200);
        assertThat(rsp.body()).isNotNull();
        assertThat(rsp.body().getAccessToken()).isNotNull();
        assertThat(rsp.body().getRefreshToken()).isNull();
        assertThat(rsp.body().getAvatar()).isNotNull();
        assertThat(rsp.body().getAvatar()).isEqualTo("static/avatars/jimmy_solid.png");
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/auth/CustomLoginHandlerTest.java:CustomLoginHandlerTest.<init>
package pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Post;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQueryResult;

public interface DashboardOperations {

    @Post("/totalsales")
    GetTotalSalesQueryResult queryTotalSales(@Body GetTotalSalesQuery query);

    @Post("/trends")
    GetSalesTrendsQueryResult querySalesTrends(@Body GetSalesTrendsQuery query);

    @Post("/agentssales")
    GetAgentsSalesQueryResult queryAgentsSales(@Body GetAgentsSalesQuery query);

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/service/api/v1/DashboardOperations.java:DashboardOperations.<init>
// Node: queryTotalSales
// Node: querySalesTrends
// Node: queryAgentsSales
package pl.altkom.asc.lab.micronaut.poc.pricing.intrastructure.adapters.web;

import pl.altkom.asc.lab.micronaut.poc.pricing.commands.CalculatePriceHandler;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.PricingOperations;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;

import io.micronaut.http.annotation.Controller;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import io.micronaut.validation.Validated;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Controller("/pricing")
@Validated
@RequiredArgsConstructor
@Slf4j
public class PricingController implements PricingOperations {

    private final CalculatePriceHandler calculatePriceHandler;

    @ExecuteOn(TaskExecutors.IO)
    @Override
    public CalculatePriceResult calculatePrice(CalculatePriceCommand cmd) {
        return calculatePriceHandler.handle(cmd);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/intrastructure/adapters/web/PricingController.java:PricingController.<init>
package pl.altkom.asc.lab.micronaut.poc.pricing;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.annotation.Client;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;

import javax.validation.constraints.NotNull;

@Client(id = "/pricing-service", path = "/pricing")
public interface PricingTestClient {

    @Post("/calculate")
    CalculatePriceResult calculatePrice(@Body @NotNull CalculatePriceCommand cmd);
}



// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/pricing/PricingTestClient.java:PricingTestClient.<init>
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


// Node: exceptionWhenCommandIsNull
// Node: assertThrows
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.web;


import io.micronaut.http.annotation.Controller;
import io.micronaut.validation.Validated;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandBus;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.DashboardOperations;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQueryResult;


@RequiredArgsConstructor
@Validated
@Controller("/dashboard")
public class DashboardController implements DashboardOperations {

    private final CommandBus bus;

    @Override
    public GetTotalSalesQueryResult queryTotalSales(GetTotalSalesQuery query) {
        return bus.executeQuery(query);
    }

    @Override
    public GetSalesTrendsQueryResult querySalesTrends(GetSalesTrendsQuery query) {
        return bus.executeQuery(query);
    }

    @Override
    public GetAgentsSalesQueryResult queryAgentsSales(GetAgentsSalesQuery query) {
        return bus.executeQuery(query);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/web/DashboardController.java:DashboardController.<init>
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import io.micronaut.http.annotation.Get;
import io.micronaut.http.client.annotation.Client;

@Client("${elastichealth.endpoint}")
public interface ElasticHealthCheck {
    @Get("/health")
    ElasticHealthCheckResult health();
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/elastic/ElasticHealthCheck.java:ElasticHealthCheck.<init>
// Node: health
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;
import org.elasticsearch.index.query.BoolQueryBuilder;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.search.SearchHit;
import org.elasticsearch.search.builder.SearchSourceBuilder;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.AgentSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config.JsonConverter;

import java.io.IOException;

import javax.inject.Singleton;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Singleton
@RequiredArgsConstructor
public class PolicyElasticRepository implements PolicyRepository {

    private final RestHighLevelClient esClient;
    private final JsonConverter jsonConverter;

    public void save(PolicyDocument policyDocument) {
        IndexRequest indexRequest = new IndexRequest("policy_stats")
                .type("policy_type")
                .id(policyDocument.getNumber())
                .setRefreshPolicy("true")
                .source(jsonConverter.stringifyObject(policyDocument), XContentType.JSON);

        try {
            esClient.index(indexRequest);
        } catch (IOException e) {
            log.error("Error while saving policy", e);
            throw new RuntimeException("Error while executing query", e);
        }
    }

    public PolicyDocument findByNumber(String number) {
        SearchRequest searchRequest = new SearchRequest("policy_stats")
                .types("policy_type");

        BoolQueryBuilder filterBuilder = QueryBuilders.boolQuery();

        filterBuilder.must(QueryBuilders.termQuery("number.keyword", number));

        SearchSourceBuilder srcBuilder = new SearchSourceBuilder()
                .query(filterBuilder)
                .size(10);

        searchRequest.source(srcBuilder);

        SearchResponse searchResponse = executeSearch(searchRequest);

        SearchHit[] hits = searchResponse.getHits().getHits();

        return hits.length > 0
                ? jsonConverter.objectFromString(hits[0].getSourceAsString(), PolicyDocument.class)
                : null;
    }

    public TotalSalesQuery.Result getTotalSales(TotalSalesQuery query) {
        TotalSalesQueryAdapter queryAdapter = QueryAdapter.of(query);
        SearchResponse searchResponse = executeSearch(queryAdapter.buildQuery());
        return queryAdapter.extractResult(searchResponse);
    }

    public SalesTrendsQuery.Result getSalesTrends(SalesTrendsQuery query) {
        SalesTrendsQueryAdapter queryAdapter = QueryAdapter.of(query);
        SearchResponse searchResponse = executeSearch(queryAdapter.buildQuery());
        return queryAdapter.extractResult(searchResponse);
    }

    public AgentSalesQuery.Result getAgentSales(AgentSalesQuery query) {
        AgentSalesQueryAdapter queryAdapter = QueryAdapter.of(query);
        SearchResponse searchResponse = executeSearch(queryAdapter.buildQuery());
        return queryAdapter.extractResult(searchResponse);
    }

    private SearchResponse executeSearch(SearchRequest request) {
        try {
            return esClient.search(request);
        } catch (IOException e) {
            throw new RuntimeException("Failed to execute search", e);
        }
    }
}


// Node: search
// Node: find
package pl.altkom.asc.lab.micronaut.poc.product.service.infrastructure.adapters.web;

import io.micronaut.http.annotation.Controller;
import io.reactivex.Maybe;
import io.reactivex.Single;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductOperations;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.Products;

import java.util.List;

@Controller("/products")
@RequiredArgsConstructor
public class ProductsController implements ProductOperations {

    private final Products products;

    @Override
    public Single<List<ProductDto>> getAll() {
        return products.findAll().map(ProductsAssembler::map);
    }

    @Override
    public Maybe<ProductDto> get(String productCode) {
        return products.findOne(productCode).map(ProductsAssembler::map);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/infrastructure/adapters/web/ProductsController.java:ProductsController.<init>
// Node: getAll
package pl.altkom.asc.lab.micronaut.poc.payment.infrastructure.adapters.web;

import pl.altkom.asc.lab.micronaut.poc.payment.domain.PolicyAccountRepository;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountBalanceDto;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountDto;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.exceptions.PolicyAccountNotFound;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.operations.PaymentOperations;

import java.time.LocalDate;
import java.util.Collection;

import io.micronaut.configuration.hystrix.annotation.HystrixCommand;
import io.micronaut.http.annotation.Controller;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import lombok.RequiredArgsConstructor;

@Controller("/payment")
@RequiredArgsConstructor
public class PaymentController implements PaymentOperations {

    private final PolicyAccountRepository policyAccountRepository;

    @Override
    @HystrixCommand
    @ExecuteOn(TaskExecutors.IO)
    public Collection<PolicyAccountDto> accounts() {
        return policyAccountRepository.findAll();
    }

    @Override
    @HystrixCommand
    @ExecuteOn(TaskExecutors.IO)
    public PolicyAccountBalanceDto accountBalance(String accountNumber) {
        return policyAccountRepository.findByPolicyAccountNumber(accountNumber)
                .map(account -> new PolicyAccountBalanceDto(
                        account.getPolicyNumber(),
                        account.getPolicyAccountNumber(),
                        account.balanceAt(LocalDate.now()),
                        account.getCreated(),
                        account.getUpdated()))
                .orElseThrow(() -> new PolicyAccountNotFound(accountNumber));
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/infrastructure/adapters/web/PaymentController.java:PaymentController.<init>
// Node: accounts
// Node: accountBalance
// Node: PolicyAccountBalanceDto
package pl.altkom.asc.lab.micronaut.poc.command.bus;

import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Command;
import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Query;

public interface CommandBus {
    <R, C extends Command<R>> R executeCommand(C command);

    <R, Q extends Query<R>> R executeQuery(Q query);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/command-bus/src/main/java/pl/altkom/asc/lab/micronaut/poc/command/bus/CommandBus.java:CommandBus.<init>
package pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.operations;

import io.micronaut.http.annotation.Get;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountDto;

import java.util.Collection;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountBalanceDto;

public interface PaymentOperations {

    @Get("/accounts")
    Collection<PolicyAccountDto> accounts();
    
    @Get("/accounts/{accountNumber}")
    PolicyAccountBalanceDto accountBalance(String accountNumber);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/service/api/v1/operations/PaymentOperations.java:PaymentOperations.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway;


import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Post;
import io.micronaut.security.annotation.Secured;
import io.micronaut.security.rules.SecurityRule;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQueryResult;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.DashboardGatewayClient;

import javax.inject.Inject;

@Secured(SecurityRule.IS_AUTHENTICATED)
@Controller("/api/dashboard")
public class DashboardGatewayController {

    @Inject
    private DashboardGatewayClient client;

    @Post("/totalsales")
    GetTotalSalesQueryResult queryTotalSales(@Body GetTotalSalesQuery query){
        return client.queryTotalSales(query);
    }

    @Post("/trends")
    GetSalesTrendsQueryResult querySalesTrends(@Body GetSalesTrendsQuery query){
        return client.querySalesTrends(query);
    }

    @Post("/agentssales")
    GetAgentsSalesQueryResult queryAgentsSales(@Body GetAgentsSalesQuery query){
        return client.queryAgentsSales(query);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/DashboardGatewayController.java:DashboardGatewayController.<init>
// Node: Secured
package pl.altkom.asc.lab.micronaut.poc.gateway;


import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.annotation.QueryValue;
import io.micronaut.security.annotation.Secured;
import io.micronaut.security.rules.SecurityRule;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.PolicyGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.PolicySearchGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import javax.inject.Inject;
import java.security.Principal;

@Secured(SecurityRule.IS_AUTHENTICATED)
@Controller("/api/policies")
public class PolicyGatewayController {

    @Inject
    private PolicyGatewayClient policyClient;
    @Inject
    private PolicySearchGatewayClient policySearchClient;

    @Get
    Maybe<FindPolicyQueryResult> policies(@QueryValue(value = "q", defaultValue = "*") String q) {
        return policySearchClient.policies(q);
    }

    @Get("/{policyNumber}")
    GetPolicyDetailsQueryResult get(String policyNumber) {
        return policyClient.get(policyNumber);
    }

    @Post("/create")
    CreatePolicyResult create(CreatePolicyCommand cmd, Principal principal) {
        cmd.setAgentLogin(principal.getName());
        return policyClient.create(cmd);
    }

    @Post("/terminate")
    TerminatePolicyResult terminate(TerminatePolicyCommand cmd) {
        return policyClient.terminate(cmd);
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/PolicyGatewayController.java:PolicyGatewayController.<init>
// Node: policies
// Node: QueryValue
package pl.altkom.asc.lab.micronaut.poc.gateway;

import io.micronaut.security.rules.SecurityRule;
import pl.altkom.asc.lab.micronaut.poc.documents.api.queries.finddocuments.FindDocumentsResult;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.security.annotation.Secured;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.DocumentsGatewayClient;

import javax.inject.Inject;

@Secured(SecurityRule.IS_AUTHENTICATED)
@Controller("/api/documents")
public class DocumentsGatewayController {

    @Inject
    private DocumentsGatewayClient client;

    @Get("/{policyNumber}")
    FindDocumentsResult find(String policyNumber) {
        return client.find(policyNumber);
    }
}



// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/DocumentsGatewayController.java:DocumentsGatewayController.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway;

import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.security.annotation.Secured;
import io.micronaut.security.rules.SecurityRule;
import io.reactivex.Maybe;
import io.reactivex.Single;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.ProductGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;

import javax.inject.Inject;
import java.util.List;

@Secured(SecurityRule.IS_AUTHENTICATED)
@Controller("/api/products")
public class ProductGatewayController {

    @Inject
    private ProductGatewayClient client;

    @Get
    public Single<List<ProductDto>> getAll() {
        return client.getAll();
    }

    @Get("/{productCode}")
    public Maybe<ProductDto> get(String productCode) {
        return client.get(productCode);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/ProductGatewayController.java:ProductGatewayController.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway;

import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.PaymentGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountDto;

import javax.inject.Inject;
import java.util.Collection;

@Controller("/api/payments")
public class PaymentGatewayController {

    @Inject
    private PaymentGatewayClient paymentClient;

    @Get("/accounts")
    Collection<PolicyAccountDto> accounts() {
        return paymentClient.accounts();
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/PaymentGatewayController.java:PaymentGatewayController.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway;

import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Post;
import io.micronaut.security.annotation.Secured;
import io.micronaut.security.rules.SecurityRule;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.PolicyGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferResult;

import javax.inject.Inject;

@Secured(SecurityRule.IS_AUTHENTICATED)
@Controller("/api/offers")
public class OfferGatewayController {

    @Inject
    private PolicyGatewayClient client;

    @Post(value = "/", consumes = "application/json")
    CreateOfferResult create(CreateOfferCommand cmd) {
        return client.createOffer(cmd);
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/OfferGatewayController.java:OfferGatewayController.<init>
// Node: createOffer
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1;

import io.micronaut.http.client.annotation.Client;
import io.micronaut.retry.annotation.Retryable;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.PolicySearchOperations;

@Client(id = "policy-search-service", path = "/policies")
@Retryable(attempts = "2", delay = "2s")
public interface PolicySearchGatewayClient extends PolicySearchOperations {
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/client/v1/PolicySearchGatewayClient.java:PolicySearchGatewayClient.<init>
// Node: Retryable
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1;

import io.micronaut.http.client.annotation.Client;
import io.micronaut.retry.annotation.Retryable;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.operations.PaymentOperations;

@Client(id = "payment-service", path = "/payment")
@Retryable(attempts = "2", delay = "2s")
public interface PaymentGatewayClient extends PaymentOperations {

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/client/v1/PaymentGatewayClient.java:PaymentGatewayClient.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1;

import io.micronaut.http.client.annotation.Client;
import io.micronaut.retry.annotation.Retryable;
import pl.altkom.asc.lab.micronaut.poc.documents.api.DocumentsOperations;
import pl.altkom.asc.lab.micronaut.poc.documents.api.queries.finddocuments.FindDocumentsResult;

@Client(id = "documents-service", path = "/documents")
@Retryable(attempts = "2", delay = "2s")
public interface DocumentsGatewayClient extends DocumentsOperations {

    @Override
    FindDocumentsResult find(String policyNumber);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/client/v1/DocumentsGatewayClient.java:DocumentsGatewayClient.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1;


import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.retry.annotation.Retryable;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.DashboardOperations;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQueryResult;

@Client(id = "dashboard-service", path = "/dashboard")
@Retryable(attempts = "2", delay = "2s")
public interface DashboardGatewayClient extends DashboardOperations {

    @Override
    @Post("/totalsales")
    GetTotalSalesQueryResult queryTotalSales(@Body GetTotalSalesQuery query);

    @Override
    @Post("/trends")
    GetSalesTrendsQueryResult querySalesTrends(@Body GetSalesTrendsQuery query);

    @Override
    @Post("/agentssales")
    GetAgentsSalesQueryResult queryAgentsSales(@Body GetAgentsSalesQuery query);

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/client/v1/DashboardGatewayClient.java:DashboardGatewayClient.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1;

import io.micronaut.http.client.annotation.Client;
import io.micronaut.retry.annotation.Retryable;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductOperations;

@Client(id = "product-service", path = "/products")
@Retryable(attempts = "2", delay = "2s")
public interface ProductGatewayClient extends ProductOperations {

    @Override
    Maybe<ProductDto> get(String productCode);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/client/v1/ProductGatewayClient.java:ProductGatewayClient.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1;

import io.micronaut.http.annotation.Body;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.Post;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.retry.annotation.Retryable;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.PolicyOperations;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import javax.validation.constraints.NotNull;

@Client(id = "policy-service")
@Retryable(attempts = "2", delay = "2s")
public interface PolicyGatewayClient extends PolicyOperations {

    @Post("/offers")
    CreateOfferResult createOffer(@Body @NotNull CreateOfferCommand cmd);

    @Override
    @Get("/policies/{policyNumber}")
    GetPolicyDetailsQueryResult get(String policyNumber);

    @Override
    @Post("/policies")
    CreatePolicyResult create(CreatePolicyCommand cmd);

    @Override
    @Post("/policies/terminate")
    TerminatePolicyResult terminate(TerminatePolicyCommand cmd);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/client/v1/PolicyGatewayClient.java:PolicyGatewayClient.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.fallback;

import io.micronaut.retry.annotation.Fallback;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.PolicySearchOperations;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;

import javax.inject.Singleton;

@Singleton
@Fallback
public class PolicySearchGatewayClientFallback implements PolicySearchOperations {
    @Override
    public Maybe<FindPolicyQueryResult> policies(String queryText) {
        return Maybe.just(FindPolicyQueryResult.empty());
    }
}


package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.fallback;

import io.micronaut.retry.annotation.Fallback;
import io.reactivex.Maybe;
import io.reactivex.Single;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.ProductGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;

import javax.inject.Singleton;
import java.util.Collections;
import java.util.List;

@Singleton
@Fallback
public class ProductGatewayClientFallback implements ProductGatewayClient {

    @Override
    public Single<List<ProductDto>> getAll() {
        return Single.just(Collections.emptyList());
    }

    @Override
    public Maybe<ProductDto> get(String productCode) {
        return Maybe.empty();
    }
}


// Node: emptyList
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.fallback;

import io.micronaut.retry.annotation.Fallback;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.PaymentGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountBalanceDto;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountDto;

import javax.inject.Singleton;
import java.util.Collection;
import java.util.Collections;
import java.util.Date;

@Singleton
@Fallback
public class PaymentGatewayClientFallback implements PaymentGatewayClient {
    @Override
    public Collection<PolicyAccountDto> accounts() {
        return Collections.emptyList();
    }

    @Override
    public PolicyAccountBalanceDto accountBalance(String accountNumber) {
        return new PolicyAccountBalanceDto(accountNumber, null, null, new Date(), new Date());
    }
}


// Node: Date
package pl.altkom.asc.lab.micronaut.poc.product.service.api.v1;

import io.micronaut.http.annotation.Get;
import io.reactivex.Maybe;
import io.reactivex.Single;

import java.util.List;

public interface ProductOperations {

    @Get
    Single<List<ProductDto>> getAll();

    @Get("/{productCode}")
    Maybe<ProductDto> get(String productCode);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/api/v1/ProductOperations.java:ProductOperations.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db;

import io.reactivex.Maybe;
import lombok.extern.slf4j.Slf4j;
import org.apache.http.HttpHost;
import org.elasticsearch.action.ActionListener;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.index.IndexResponse;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import javax.inject.Singleton;

@Singleton
@Slf4j
public class ElasticClientAdapter {

    private final RestHighLevelClient restHighLevelClient;
    private final ElasticSearchSettings elasticSearchSettings;

    public ElasticClientAdapter(ElasticSearchSettings elasticSearchSettings) {
        this.elasticSearchSettings = elasticSearchSettings;
        this.restHighLevelClient = buildClient();
    }

    Maybe<IndexResponse> index(IndexRequest indexRequest) {
        return Maybe.create(sink -> {
            restHighLevelClient.indexAsync(indexRequest, new ActionListener<IndexResponse>() {
                @Override
                public void onResponse(IndexResponse indexResponse) {
                    sink.onSuccess(indexResponse);
                }

                @Override
                public void onFailure(Exception e) {
                    sink.onError(e);
                }
            });
        });
    }

    public Maybe<SearchResponse> search(SearchRequest searchRequest) {
        return Maybe.create(sink ->
                restHighLevelClient.searchAsync(searchRequest, new ActionListener<SearchResponse>() {
                    @Override
                    public void onResponse(SearchResponse searchResponse) {
                        sink.onSuccess(searchResponse);
                    }

                    @Override
                    public void onFailure(Exception e) {
                        sink.onError(e);
                    }
                }));
    }

    private RestHighLevelClient buildClient() {
        return new RestHighLevelClient(
                RestClient.builder(new HttpHost(elasticSearchSettings.getHost(), elasticSearchSettings.getPort()))
                        .setRequestConfigCallback(config -> config
                                .setConnectTimeout(elasticSearchSettings.getConnectionTimeout())
                                .setConnectionRequestTimeout(elasticSearchSettings.getConnectionRequestTimeout())
                                .setSocketTimeout(elasticSearchSettings.getSocketTimeout())
                        )
                        .setMaxRetryTimeoutMillis(elasticSearchSettings.getMaxRetryTimeout()));
    }
}


// Node: searchAsync
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.web;

import io.micronaut.http.annotation.Controller;
import io.micronaut.validation.Validated;
import io.reactivex.Maybe;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandBus;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.PolicySearchOperations;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQuery;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;

@RequiredArgsConstructor
@Controller("/policies")
public class PolicySearchController implements PolicySearchOperations {

    private final CommandBus bus;

    @Override
    public Maybe<FindPolicyQueryResult> policies(String queryText) {
        return bus.executeQuery(new FindPolicyQuery(queryText));
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/infrastructure/adapters/web/PolicySearchController.java:PolicySearchController.<init>
// Node: FindPolicyQuery
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.mock;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db.ElasticPolicyViewRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyView;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyViewRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQuery;

import javax.inject.Singleton;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Replaces(ElasticPolicyViewRepository.class)
@Requires(env = Environment.TEST)
@Singleton
public class MockPolicyViewRepository implements PolicyViewRepository {

    private Map<String, PolicyView> policyMap = init();

    private Map<String, PolicyView> init() {
        Map<String, PolicyView> map = new LinkedHashMap<>();

        map.put("1234", new PolicyView(
                "1234",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1235", new PolicyView(
                "1235",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1236", new PolicyView("1236",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1237", new PolicyView("1237",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );

        return map;
    }

    @Override
    public Maybe<List<PolicyView>> findAll(FindPolicyQuery query) {
        return Maybe.just(new ArrayList<>(policyMap.values()));
    }

    @Override
    public void save(PolicyView policy) {
        policyMap.put(policy.getNumber(), policy);
    }
}


// Node: FindPolicyQueryResult
package pl.altkom.asc.lab.micronaut.poc;

import io.reactivex.Maybe;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.annotation.QueryValue;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;

@Client(id = "/policy-search-service", path = "/policies")
public interface PolicySearchTestClient {

    @Get
    Maybe<FindPolicyQueryResult> policies(@QueryValue("q") String queryText);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/PolicySearchTestClient.java:PolicySearchTestClient.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1;

import io.micronaut.http.annotation.Get;
import io.micronaut.http.annotation.QueryValue;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;

public interface PolicySearchOperations {

    @Get
    Maybe<FindPolicyQueryResult> policies(@QueryValue("q") String queryText);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/service/api/v1/PolicySearchOperations.java:PolicySearchOperations.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy;

import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.dto.PolicyListItemDto;

import java.util.Collections;
import java.util.List;

import io.micronaut.core.annotation.Introspected;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Introspected
@AllArgsConstructor
@NoArgsConstructor
@Getter
public class FindPolicyQueryResult {
    private List<PolicyListItemDto> policies;

    public static FindPolicyQueryResult empty() {
        return new FindPolicyQueryResult(Collections.emptyList());
    }
}


