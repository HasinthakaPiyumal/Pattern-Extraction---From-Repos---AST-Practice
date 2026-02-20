// Cluster 21

// Node: getDockerHostIp
package net.chrisrichardson.ftgo.restaurantservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantDomainEventPublisher;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryserviceMessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class DeliveryserviceMessagingBase {

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public RestaurantDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new RestaurantDomainEventPublisher(eventPublisher);
    }
  }


  @Autowired
  private RestaurantDomainEventPublisher restaurantDomainEventPublisher;

  protected void restaurantCreated() {
    Restaurant restaurant = new Restaurant("Yummy Indian", new RestaurantMenu(Collections.emptyList()));
    restaurant.setId(99L);
    restaurantDomainEventPublisher.publish(restaurant,
            Collections.singletonList(new RestaurantCreated(restaurant.getName(), new Address("1 Main Street", "Unit 99", "Oakland", "CA", "94611"),
                    restaurant.getMenu())));
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/integration-test/java/net/chrisrichardson/ftgo/restaurantservice/contract/DeliveryserviceMessagingBase.java:DeliveryserviceMessagingBase.<init>
// Node: RunWith
// Node: SpringBootTest
// Node: Import
package net.chrisrichardson.ftgo.restaurantservice;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.eventuate.common.json.mapper.JSonMapper;
import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;

@SpringBootApplication
@Import(TramJdbcKafkaConfiguration.class)
public class RestaurantServiceMain {

  @Bean
  @Primary // conflicts with _halObjectMapper
  public ObjectMapper objectMapper() {
    return JSonMapper.objectMapper;
  }

  public static void main(String[] args) {
    SpringApplication.run(RestaurantServiceMain.class, args);
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/RestaurantServiceMain.java:RestaurantServiceMain.<init>
package net.chrisrichardson.ftgo.restaurantservice.domain;

import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableJpaRepositories
@EnableTransactionManagement
@EntityScan
@Import({TramEventsPublisherConfiguration.class, CommonConfiguration.class})
public class RestaurantServiceDomainConfiguration {

  @Bean
  public RestaurantService restaurantService() {
    return new RestaurantService();
  }

  @Bean
  public RestaurantDomainEventPublisher restaurantDomainEventPublisher(DomainEventPublisher domainEventPublisher) {
    return new RestaurantDomainEventPublisher(domainEventPublisher);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/RestaurantServiceDomainConfiguration.java:RestaurantServiceDomainConfiguration.<init>
// Node: registerMoneyModule
package net.chrisrichardson.ftgo.apiagateway.orders;

import org.springframework.boot.context.properties.ConfigurationProperties;

import javax.validation.constraints.NotNull;

@ConfigurationProperties(prefix = "order.destinations")
public class OrderDestinations {

  @NotNull
  private String orderServiceUrl;

  @NotNull
  private String orderHistoryServiceUrl;

  public String getOrderHistoryServiceUrl() {
    return orderHistoryServiceUrl;
  }

  public void setOrderHistoryServiceUrl(String orderHistoryServiceUrl) {
    this.orderHistoryServiceUrl = orderHistoryServiceUrl;
  }


  public String getOrderServiceUrl() {
    return orderServiceUrl;
  }

  public void setOrderServiceUrl(String orderServiceUrl) {
    this.orderServiceUrl = orderServiceUrl;
  }
}


// Node: setOrderServiceUrl
package net.chrisrichardson.ftgo.apiagateway;


import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.tomakehurst.wiremock.junit.WireMockRule;
import net.chrisrichardson.ftgo.apiagateway.orders.OrderDetails;
import net.chrisrichardson.ftgo.apiagateway.proxies.OrderInfo;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.web.server.LocalServerPort;
import org.springframework.cloud.contract.wiremock.AutoConfigureWireMock;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.client.WebClient;

import static com.github.tomakehurst.wiremock.client.WireMock.aResponse;
import static com.github.tomakehurst.wiremock.client.WireMock.get;
import static com.github.tomakehurst.wiremock.client.WireMock.getRequestedFor;
import static com.github.tomakehurst.wiremock.client.WireMock.post;
import static com.github.tomakehurst.wiremock.client.WireMock.postRequestedFor;
import static com.github.tomakehurst.wiremock.client.WireMock.stubFor;
import static com.github.tomakehurst.wiremock.client.WireMock.urlEqualTo;
import static com.github.tomakehurst.wiremock.client.WireMock.urlMatching;
import static com.github.tomakehurst.wiremock.client.WireMock.verify;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = ApiGatewayIntegrationTestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties={"order.destinations.orderServiceUrl=http://localhost:${wiremock.server.port}",
                "order.destinations.orderHistoryServiceUrl=http://localhost:8083",
                "consumer.destinations.consumerServiceUrl=http://localhost:9999"
                  })
@AutoConfigureWireMock(port=0)
public class ApiGatewayIntegrationTest {

    @LocalServerPort
    private int port;

    @Test
    public void shouldProxyCreateOrder() {

        String expectedResponse = "{}";

        stubFor(post(urlEqualTo("/orders"))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", "application/json")
                        .withBody(expectedResponse)));


        WebClient client = WebClient.create("http://localhost:" + port + "/orders");

        ResponseEntity<String> z = client
                .post()
                .body(BodyInserters.fromObject("{}"))
                .exchange()
                .flatMap(r -> r.toEntity(String.class))
                .block();

        assertNotNull(z);
        assertEquals(HttpStatus.OK, z.getStatusCode());
        assertEquals(expectedResponse, z.getBody());

        verify(postRequestedFor(urlMatching("/orders")));

    }

    @Test
    public void shouldProxyGetOrderDetails() throws JsonProcessingException {

        String orderId = "1";

        OrderDetails expectedOrderDetails = new OrderDetails(new OrderInfo(orderId, "CREATED"));
        ObjectMapper objectMapper = new ObjectMapper();

        String body = objectMapper.writeValueAsString(expectedOrderDetails.getOrderInfo());

        String expectedPath = "/orders/" + orderId;

        stubFor(get(urlEqualTo(expectedPath))
                .willReturn(aResponse()
                        .withStatus(200)
                        .withHeader("Content-Type", MediaType.APPLICATION_JSON.toString())
                        .withBody(body)));


        WebClient client = WebClient.create("http://localhost:" + port + "/orders/1");

        ResponseEntity<OrderDetails> z = client
                .get()
                .exchange()
                .flatMap(r -> r.toEntity(OrderDetails.class))
                .block();

        assertNotNull(z);
        assertEquals(HttpStatus.OK, z.getStatusCode());
        assertEquals(body, expectedOrderDetails, z.getBody());

        verify(getRequestedFor(urlMatching(expectedPath)));

    }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-api-gateway/src/test/java/net/chrisrichardson/ftgo/apiagateway/ApiGatewayIntegrationTest.java:ApiGatewayIntegrationTest.<init>
// Node: AutoConfigureWireMock
package net.chrisrichardson.ftgo.apiagateway.contract;

import net.chrisrichardson.ftgo.apiagateway.orders.OrderDestinations;
import net.chrisrichardson.ftgo.apiagateway.proxies.OrderInfo;
import net.chrisrichardson.ftgo.apiagateway.proxies.OrderNotFoundException;
import net.chrisrichardson.ftgo.apiagateway.proxies.OrderServiceProxy;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.stubrunner.spring.AutoConfigureStubRunner;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.web.reactive.function.client.WebClient;

import static org.junit.Assert.assertEquals;

@RunWith(SpringRunner.class)
@SpringBootTest(classes=TestConfiguration.class,
        webEnvironment= SpringBootTest.WebEnvironment.NONE)
@AutoConfigureStubRunner(ids =
        {"net.chrisrichardson.ftgo:ftgo-order-service-contracts"}
)
@DirtiesContext
public class OrderServiceProxyIntegrationTest {

  @Value("${stubrunner.runningstubs.ftgo-order-service-contracts.port}")
  private int port;
  private OrderDestinations orderDestinations;
  private OrderServiceProxy orderService;

  @Before
  public void setUp() throws Exception {
    orderDestinations = new OrderDestinations();
    String orderServiceUrl = "http://localhost:" + port;
    orderDestinations.setOrderServiceUrl(orderServiceUrl);
    orderService = new OrderServiceProxy(orderDestinations, WebClient.create());
  }

  @Test
  public void shouldVerifyExistingCustomer() {
    OrderInfo result = orderService.findOrderById("99").block();
    assertEquals("99", result.getOrderId());
    assertEquals("APPROVAL_PENDING", result.getState());
  }

  @Test(expected = OrderNotFoundException.class)
  public void shouldFailToFindMissingOrder() {
    orderService.findOrderById("555").block();
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-api-gateway/src/test/java/net/chrisrichardson/ftgo/apiagateway/contract/OrderServiceProxyIntegrationTest.java:OrderServiceProxyIntegrationTest.<init>
// Node: AutoConfigureStubRunner
// Node: Value
// Node: OrderDestinations
package net.chrisrichardson.ftgo.restaurantservice.lambda;

import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantService;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = RestaurantServiceLambdaConfiguration.class)
public class RestaurantServiceLambdaConfigurationTest {

  @Autowired
  private RestaurantService restaurantService;
  @Test
  public void shouldInitialize() {}
}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/integration-test/java/net/chrisrichardson/ftgo/restaurantservice/lambda/RestaurantServiceLambdaConfigurationTest.java:RestaurantServiceLambdaConfigurationTest.<init>
package net.chrisrichardson.ftgo.restaurantservice.domain;

import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.support.JpaRepositoryFactoryBean;

@Configuration
@EntityScan
@Import({TramEventsPublisherConfiguration.class, CommonConfiguration.class})
public class RestaurantServiceDomainConfiguration {

  @Bean
  public RestaurantService restaurantService(JpaRepositoryFactoryBean restaurantRepository) {
    return new RestaurantService((RestaurantRepository) restaurantRepository.getObject());
  }

  @Bean
  public JpaRepositoryFactoryBean<RestaurantRepository, Restaurant, Long> restaurantRepository() {
    return new JpaRepositoryFactoryBean<>(RestaurantRepository.class);
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/RestaurantServiceDomainConfiguration.java:RestaurantServiceDomainConfiguration.<init>
package net.chrisrichardson.ftgo.restaurantservice.aws;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import static net.chrisrichardson.ftgo.restaurantservice.aws.ApiGatewayResponse.buildErrorResponse;


public abstract class AbstractHttpHandler
        implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {

  private Logger log = LoggerFactory.getLogger(this.getClass());

  @Override
  public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent input, Context context) {
    log.debug("Got request: {}", input);
    try {
      beforeHandling(input, context);
      return handleHttpRequest(input, context);
    } catch (Exception e) {
      log.error("Error handling request id: {}", context.getAwsRequestId(), e);
      return buildErrorResponse(new AwsLambdaError(
              "Internal Server Error",
              "500",
              context.getAwsRequestId(),
              "Error handling request: " + context.getAwsRequestId() + " " + input.toString()));
    }
  }

  protected void beforeHandling(APIGatewayProxyRequestEvent request, Context context) {
    // do nothing
  }

  protected abstract APIGatewayProxyResponseEvent handleHttpRequest(APIGatewayProxyRequestEvent request, Context context);
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/aws/AbstractHttpHandler.java:AbstractHttpHandler.<init>
// Node: getLogger
// Node: getClass
package net.chrisrichardson.ftgo.restaurantservice.lambda;

import io.eventuate.tram.spring.messaging.producer.jdbc.TramMessageProducerJdbcConfiguration;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantServiceDomainConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import({RestaurantServiceDomainConfiguration.class, TramMessageProducerJdbcConfiguration.class})
@EnableAutoConfiguration
public class RestaurantServiceLambdaConfiguration {
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/lambda/RestaurantServiceLambdaConfiguration.java:RestaurantServiceLambdaConfiguration.<init>
package net.chrisrichardson.ftgo.common;

import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import io.eventuate.common.json.mapper.JSonMapper;

import javax.annotation.PostConstruct;

public class CommonJsonMapperInitializer {

  @PostConstruct
  public void initialize() {
    registerMoneyModule();
  }

  public static void registerMoneyModule() {
    JSonMapper.objectMapper.registerModule(new MoneyModule());
    JSonMapper.objectMapper.registerModule(new JavaTimeModule());
    JSonMapper.objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

  }
}


// Node: initialize
package net.chrisrichardson.ftgo.common;

import com.fasterxml.jackson.databind.JsonMappingException;
import io.eventuate.common.json.mapper.JSonMapper;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.IOException;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

public class MoneySerializationTest {

  @BeforeClass
  public static void initialize() {
    CommonJsonMapperInitializer.registerMoneyModule();
  }


  public static class MoneyContainer {
    private Money price;

    @Override
    public boolean equals(Object o) {
      return EqualsBuilder.reflectionEquals(this, o);
    }

    @Override
    public int hashCode() {
      return HashCodeBuilder.reflectionHashCode(this);
    }

    @Override
    public String toString() {
      return ToStringBuilder.reflectionToString(this);
    }

    public Money getPrice() {
      return price;
    }

    public void setPrice(Money price) {
      this.price = price;
    }

    public MoneyContainer() {

    }

    public MoneyContainer(Money price) {

      this.price = price;
    }
  }

  @Test
  public void shouldSer() {
    Money price = new Money("12.34");
    MoneyContainer mc = new MoneyContainer(price);
    assertEquals("{\"price\":\"12.34\"}", JSonMapper.toJson(mc));
  }

  @Test
  public void shouldDe() {
    Money price = new Money("12.34");
    MoneyContainer mc = new MoneyContainer(price);
    assertEquals(mc, JSonMapper.fromJson("{\"price\":\"12.34\"}", MoneyContainer.class));
  }

  @Test
  public void shouldFailToDe() {
    try {
      JSonMapper.fromJson("{\"price\": { \"amount\" : \"12.34\"} }", MoneyContainer.class);
      fail("expected exception");
    } catch (RuntimeException e) {
      assertEquals(JsonMappingException.class, e.getCause().getClass());
    }
  }


}

package net.chrisrichardson.ftgo.accountingservice.main;

import io.eventuate.local.java.spring.javaclient.driver.EventuateDriverConfiguration;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.accountingservice.messaging.AccountingMessagingConfiguration;
import net.chrisrichardson.ftgo.accountingservice.web.AccountingWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@EnableAutoConfiguration
@Import({AccountingMessagingConfiguration.class, AccountingWebConfiguration.class,
        TramCommandProducerConfiguration.class,
        EventuateDriverConfiguration.class,
        TramJdbcKafkaConfiguration.class,
        CommonSwaggerConfiguration.class})
public class AccountingServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(AccountingServiceMain.class, args);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service/src/main/java/net/chrisrichardson/ftgo/accountingservice/main/AccountingServiceMain.java:AccountingServiceMain.<init>
package net.chrisrichardson.ftgo.accountingservice.web;

import net.chrisrichardson.ftgo.accountingservice.domain.AccountServiceConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import(AccountServiceConfiguration.class)
@ComponentScan
public class AccountingWebConfiguration {
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service/src/main/java/net/chrisrichardson/ftgo/accountingservice/web/AccountingWebConfiguration.java:AccountingWebConfiguration.<init>
package net.chrisrichardson.ftgo.accountingservice.domain;

import io.eventuate.sync.AggregateRepository;
import io.eventuate.sync.EventuateAggregateStore;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import({TramCommandProducerConfiguration.class, CommonConfiguration.class})
public class AccountServiceConfiguration {


  @Bean
  public AggregateRepository<Account, AccountCommand> accountRepositorySync(EventuateAggregateStore aggregateStore) {
    return new AggregateRepository<>(Account.class, aggregateStore);
  }

  @Bean
  public AccountingService accountingService() {
    return new AccountingService();
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service/src/main/java/net/chrisrichardson/ftgo/accountingservice/domain/AccountServiceConfiguration.java:AccountServiceConfiguration.<init>
package net.chrisrichardson.ftgo.accountingservice.messaging;

import io.eventuate.sync.AggregateRepository;
import io.eventuate.tram.commands.consumer.CommandHandlers;
import io.eventuate.tram.commands.consumer.CommandMessage;
import io.eventuate.tram.sagas.participant.SagaCommandHandlersBuilder;
import net.chrisrichardson.ftgo.accountingservice.domain.*;
import net.chrisrichardson.ftgo.accountservice.api.AccountDisabledReply;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.accountservice.api.ReverseAuthorizationCommand;
import net.chrisrichardson.ftgo.accountservice.api.ReviseAuthorization;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withFailure;
import static io.eventuate.tram.sagas.eventsourcingsupport.UpdatingOptionsBuilder.replyingTo;

public class AccountingServiceCommandHandler {

  private Logger logger = LoggerFactory.getLogger(getClass());

  @Autowired
  private AggregateRepository<Account, AccountCommand> accountRepository;

  public CommandHandlers commandHandlers() {
    return SagaCommandHandlersBuilder
            .fromChannel("accountingService")
            .onMessage(AuthorizeCommand.class, this::authorize)
            .onMessage(ReverseAuthorizationCommand.class, this::reverseAuthorization)
            .onMessage(ReviseAuthorization.class, this::reviseAuthorization)
            .build();
  }

  public void authorize(CommandMessage<AuthorizeCommand> cm) {

    AuthorizeCommand command = cm.getCommand();

    accountRepository.update(Long.toString(command.getConsumerId()),
            makeAuthorizeCommandInternal(command),
            replyingTo(cm)
                    .catching(AccountDisabledException.class, () -> withFailure(new AccountDisabledReply()))
                    .build());

  }

  public void reverseAuthorization(CommandMessage<ReverseAuthorizationCommand> cm) {

    ReverseAuthorizationCommand command = cm.getCommand();

    accountRepository.update(Long.toString(command.getConsumerId()),
            makeReverseAuthorizeCommandInternal(command),
            replyingTo(cm)
                    .catching(AccountDisabledException.class, () -> withFailure(new AccountDisabledReply()))
                    .build());

  }
  public void reviseAuthorization(CommandMessage<ReviseAuthorization> cm) {

    ReviseAuthorization command = cm.getCommand();

    accountRepository.update(Long.toString(command.getConsumerId()),
            makeReviseAuthorizeCommandInternal(command),
            replyingTo(cm)
                    .catching(AccountDisabledException.class, () -> withFailure(new AccountDisabledReply()))
                    .build());


  }

  private AuthorizeCommandInternal makeAuthorizeCommandInternal(AuthorizeCommand command) {
    return new AuthorizeCommandInternal(Long.toString(command.getConsumerId()), Long.toString(command.getOrderId()), command.getOrderTotal());
  }
  private ReverseAuthorizationCommandInternal makeReverseAuthorizeCommandInternal(ReverseAuthorizationCommand command) {
    return new ReverseAuthorizationCommandInternal(Long.toString(command.getConsumerId()), Long.toString(command.getOrderId()), command.getOrderTotal());
  }
  private ReviseAuthorizationCommandInternal makeReviseAuthorizeCommandInternal(ReviseAuthorization command) {
    return new ReviseAuthorizationCommandInternal(Long.toString(command.getConsumerId()), Long.toString(command.getOrderId()), command.getOrderTotal());
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service/src/main/java/net/chrisrichardson/ftgo/accountingservice/messaging/AccountingServiceCommandHandler.java:AccountingServiceCommandHandler.<init>
package net.chrisrichardson.ftgo.accountingservice.messaging;

import io.eventuate.javaclient.spring.EnableEventHandlers;
import io.eventuate.tram.commands.consumer.CommandDispatcher;
import io.eventuate.tram.commands.consumer.CommandDispatcherFactory;
import io.eventuate.tram.spring.commands.consumer.TramCommandConsumerConfiguration;
import io.eventuate.tram.spring.consumer.jdbc.TransactionalNoopDuplicateMessageDetectorConfiguration;
import io.eventuate.tram.spring.events.subscriber.TramEventSubscriberConfiguration;
import io.eventuate.tram.events.subscriber.DomainEventDispatcher;
import io.eventuate.tram.events.subscriber.DomainEventDispatcherFactory;
import io.eventuate.tram.sagas.eventsourcingsupport.SagaReplyRequestedEventSubscriber;
import net.chrisrichardson.ftgo.accountingservice.domain.Account;
import net.chrisrichardson.ftgo.accountingservice.domain.AccountServiceConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import java.util.Collections;

@Configuration
@EnableEventHandlers
@Import({AccountServiceConfiguration.class, CommonConfiguration.class, TramEventSubscriberConfiguration.class, TramCommandConsumerConfiguration.class, TransactionalNoopDuplicateMessageDetectorConfiguration.class})
public class AccountingMessagingConfiguration {

  @Bean
  public AccountingEventConsumer accountingEventConsumer() {
    return new AccountingEventConsumer();
  }

  @Bean
  public DomainEventDispatcher domainEventDispatcher(AccountingEventConsumer accountingEventConsumer, DomainEventDispatcherFactory domainEventDispatcherFactory) {
    return domainEventDispatcherFactory.make("accountingServiceDomainEventDispatcher", accountingEventConsumer.domainEventHandlers());
  }

  @Bean
  public AccountingServiceCommandHandler accountCommandHandler() {
    return new AccountingServiceCommandHandler();
  }


  @Bean
  public CommandDispatcher commandDispatcher(AccountingServiceCommandHandler target,
                                             AccountServiceChannelConfiguration data, CommandDispatcherFactory commandDispatcherFactory) {
    return commandDispatcherFactory.make(data.getCommandDispatcherId(), target.commandHandlers());
  }

  @Bean
  public AccountServiceChannelConfiguration accountServiceChannelConfiguration() {
    return new AccountServiceChannelConfiguration("accountCommandDispatcher", "accountCommandChannel");
  }

  @Bean
  public SagaReplyRequestedEventSubscriber sagaReplyRequestedEventSubscriber() {
    return new SagaReplyRequestedEventSubscriber("accountingServiceSagaReplyRequestedEventSubscriber", Collections.singleton(Account.class.getName()));
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service/src/main/java/net/chrisrichardson/ftgo/accountingservice/messaging/AccountingMessagingConfiguration.java:AccountingMessagingConfiguration.<init>
package net.chrisrichardson.ftgo.accountingservice.messaging;

import io.eventuate.javaclient.spring.jdbc.EmbeddedTestAggregateStoreConfiguration;
import io.eventuate.sync.AggregateRepository;
import io.eventuate.tram.commands.producer.CommandProducer;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.sagas.common.SagaCommandHeaders;
import io.eventuate.tram.sagas.spring.inmemory.TramSagaInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumer;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import io.eventuate.util.test.async.Eventually;
import net.chrisrichardson.ftgo.accountingservice.domain.Account;
import net.chrisrichardson.ftgo.accountingservice.domain.AccountCommand;
import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.consumerservice.domain.ConsumerCreated;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = AccountingServiceCommandHandlerTest.AccountingServiceCommandHandlerTestConfiguration.class)
public class AccountingServiceCommandHandlerTest {

  @Configuration
  @EnableAutoConfiguration
  @Import({AccountingMessagingConfiguration.class,
          TramCommandProducerConfiguration.class,
          EmbeddedTestAggregateStoreConfiguration.class,
          TramEventsPublisherConfiguration.class, // TODO
          TramSagaInMemoryConfiguration.class})
  static public class AccountingServiceCommandHandlerTestConfiguration {
    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }

  }

  @Autowired
  private CommandProducer commandProducer;

  @Autowired
  private TestMessageConsumerFactory testMessageConsumerFactory;

  @Autowired
  private DomainEventPublisher domainEventPublisher;


  @Autowired
  private AggregateRepository<Account, AccountCommand> accountRepository;

  @Test
  public void shouldReply() {

    TestMessageConsumer testMessageConsumer = testMessageConsumerFactory.make();

    long consumerId = System.currentTimeMillis();
    long orderId = 102L;

    domainEventPublisher.publish("net.chrisrichardson.ftgo.consumerservice.domain.Consumer", consumerId, Collections.singletonList(new ConsumerCreated()));

    Eventually.eventually(() -> {
      accountRepository.find(Long.toString(consumerId));
    });

    Money orderTotal = new Money(123);

    String messageId = commandProducer.send(AccountingServiceChannels.accountingServiceChannel, null,
            new AuthorizeCommand(consumerId, orderId, orderTotal),
            testMessageConsumer.getReplyChannel(), withSagaCommandHeaders());

    testMessageConsumer.assertHasReplyTo(messageId);

  }

  // TODO duplicate

  private Map<String, String> withSagaCommandHeaders() {
    Map<String, String> result = new HashMap<>();
    result.put(SagaCommandHeaders.SAGA_TYPE, "MySagaType");
    result.put(SagaCommandHeaders.SAGA_ID, "MySagaId");
    return result;
  }

}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service/src/test/java/net/chrisrichardson/ftgo/accountingservice/messaging/AccountingServiceCommandHandlerTest.java:AccountingServiceCommandHandlerTest.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import io.eventuate.common.json.mapper.JSonMapper;
import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistory;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryFilter;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import java.util.List;
import java.util.Optional;

import static java.util.Collections.singleton;
import static java.util.Collections.singletonList;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

@RunWith(SpringJUnit4ClassRunner.class)
@SpringBootTest(classes = {OrderHistoryDaoDynamoDbTest.OrderHistoryDaoDynamoDbTestConfiguration.class})
public class OrderHistoryDaoDynamoDbTest {

  @Configuration
  @EnableAutoConfiguration
  @ComponentScan
  @Import({OrderHistoryDynamoDBConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  static public class OrderHistoryDaoDynamoDbTestConfiguration {

  }

  private String consumerId;
  private Order order1;
  private String orderId;
  @Autowired
  private OrderHistoryDao dao;
  private String restaurantName;
  private String chickenVindaloo;
  private Optional<SourceEvent> eventSource;
  private long restaurantId;

  @Before
  public void setup() {
    consumerId = "consumerId" + System.currentTimeMillis();
    orderId = "orderId" + System.currentTimeMillis();
    restaurantName = "Ajanta" + System.currentTimeMillis();
    chickenVindaloo = "Chicken Vindaloo" + System.currentTimeMillis();
    restaurantId = 101L;

    order1 = new Order(orderId, consumerId, OrderState.APPROVAL_PENDING, singletonList(new OrderLineItem("-1", chickenVindaloo, Money.ZERO, 0)), null, restaurantId, restaurantName);
    order1.setCreationDate(DateTime.now().minusDays(5));
    eventSource = Optional.of(new SourceEvent("Order", orderId, "11212-34343"));

    dao.addOrder(order1, eventSource);
  }

  @Test
  public void shouldFindOrder() {
    Optional<Order> order = dao.findOrder(orderId);
    assertOrderEquals(order1, order.get());
  }

  @Test
  public void shouldIgnoreDuplicateAdd() {
    dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.empty());
    assertFalse(dao.addOrder(order1, eventSource));
    Optional<Order> order = dao.findOrder(orderId);
    assertEquals(OrderState.CANCELLED, order.get().getStatus());
  }

  @Test
  public void shouldFindOrders() {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter());
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    Order retrievedOrder = assertContainsOrderId(orderId, orders);
    assertOrderEquals(order1, retrievedOrder);
  }

  private void assertOrderEquals(Order expected, Order other) {
    System.out.println("Expected=" + JSonMapper.toJson(expected.getLineItems()));
    System.out.println("actual  =" + JSonMapper.toJson(other.getLineItems()));
    assertEquals(expected.getLineItems(), other.getLineItems());
    assertEquals(expected.getStatus(), other.getStatus());
    assertEquals(expected.getCreationDate(), other.getCreationDate());
    assertEquals(expected.getRestaurantId(), other.getRestaurantId());
    assertEquals(expected.getRestaurantName(), other.getRestaurantName());
  }


  @Test
  public void shouldFindOrdersWithStatus() throws InterruptedException {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withStatus(OrderState.APPROVAL_PENDING));
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    assertContainsOrderId(orderId, orders);
  }

  @Test
  public void shouldCancel() throws InterruptedException {
    dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.of(new SourceEvent("a", "b", "c")));
    Order order = dao.findOrder(orderId).get();
    assertEquals(OrderState.CANCELLED, order.getStatus());
  }

  @Test
  public void shouldHandleCancel() throws InterruptedException {
    assertTrue(dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.of(new SourceEvent("a", "b", "c"))));
    assertFalse(dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.of(new SourceEvent("a", "b", "c"))));
  }

  @Test
  public void shouldFindOrdersWithCancelledStatus() {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withStatus(OrderState.CANCELLED));
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    assertNotContainsOrderId(orderId, orders);
  }

  // FIXME
//  @Test
//  public void shouldFindOrderByRestaurantName() {
//    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withKeywords(singleton(restaurantName)));
//    assertNotNull(result);
//    List<Order> orders = result.getOrders();
//    assertContainsOrderId(orderId, orders);
//  }

  @Test
  public void shouldFindOrderByMenuItem() {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withKeywords(singleton(chickenVindaloo)));
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    assertContainsOrderId(orderId, orders);
  }


  @Test
  public void shouldReturnOrdersSorted() {
    String orderId2 = "orderId" + System.currentTimeMillis();
    Order order2 = new Order(orderId2, consumerId, OrderState.APPROVAL_PENDING, singletonList(new OrderLineItem("-1", "Lamb 65", Money.ZERO, -1)), null, restaurantId, restaurantName);
    order2.setCreationDate(DateTime.now().minusDays(1));
    dao.addOrder(order2, eventSource);
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter());
    List<Order> orders = result.getOrders();

    int idx1 = indexOf(orders, orderId);
    int idx2 = indexOf(orders, orderId2);
    assertTrue(idx2 < idx1);
  }

  private int indexOf(List<Order> orders, String orderId2) {
    Order order = orders.stream().filter(o -> o.getOrderId().equals(orderId2)).findFirst().get();
    return orders.indexOf(order);
  }

  private Order assertContainsOrderId(String orderId, List<Order> orders) {
    Optional<Order> order = orders.stream().filter(o -> o.getOrderId().equals(orderId)).findFirst();
    assertTrue("Order not found", order.isPresent());
    return order.get();
  }

  private void assertNotContainsOrderId(String orderId, List<Order> orders) {
    Optional<Order> order = orders.stream().filter(o -> o.getOrderId().equals(orderId)).findFirst();
    assertFalse(order.isPresent());
  }

  @Test
  public void shouldPaginateResults() {
    String orderId2 = "orderId" + System.currentTimeMillis();
    Order order2 = new Order(orderId2, consumerId, OrderState.APPROVAL_PENDING, singletonList(new OrderLineItem("-1", "Lamb 65", Money.ZERO, -1)), null, restaurantId, restaurantName);
    order2.setCreationDate(DateTime.now().minusDays(1));
    dao.addOrder(order2, eventSource);

    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withPageSize(1));

    assertEquals(1, result.getOrders().size());
    assertTrue(result.getStartKey().isPresent());

    OrderHistory result2 = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withPageSize(1).withStartKeyToken(result.getStartKey()));

    assertEquals(1, result.getOrders().size());

  }

}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/integration-test/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/OrderHistoryDaoDynamoDbTest.java:OrderHistoryDaoDynamoDbTest.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory.main;

import io.eventuate.tram.spring.consumer.common.TramConsumerCommonConfiguration;
import io.eventuate.tram.spring.consumer.kafka.EventuateTramKafkaMessageConsumerConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.cqrs.orderhistory.messaging.OrderHistoryServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.cqrs.orderhistory.web.OrderHistoryWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({OrderHistoryWebConfiguration.class,
        OrderHistoryServiceMessagingConfiguration.class,
        CommonSwaggerConfiguration.class,
        TramConsumerCommonConfiguration.class,
        EventuateTramKafkaMessageConsumerConfiguration.class})
public class OrderHistoryServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(OrderHistoryServiceMain.class, args);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/main/OrderHistoryServiceMain.java:OrderHistoryServiceMain.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory.web;

import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.OrderHistoryDynamoDBConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@ComponentScan
@Import(OrderHistoryDynamoDBConfiguration.class)
public class OrderHistoryWebConfiguration {
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/web/OrderHistoryWebConfiguration.java:OrderHistoryWebConfiguration.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import com.amazonaws.auth.AWSCredentialsProvider;
import com.amazonaws.auth.AWSStaticCredentialsProvider;
import com.amazonaws.auth.BasicAWSCredentials;
import com.amazonaws.auth.EnvironmentVariableCredentialsProvider;
import com.amazonaws.client.builder.AwsClientBuilder;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import org.apache.commons.lang.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OrderHistoryDynamoDBConfiguration {

  @Value("${aws.dynamodb.endpoint.url:#{null}}")
  private String awsDynamodbEndpointUrl;

  @Value("${aws.region}")
  private String awsRegion;

  @Value("${aws.access.key_id:null}")
  private String accessKey;

  @Value("${aws.secret.access.key:null}")
  private String secretKey;

  @Bean
  public AmazonDynamoDB amazonDynamoDB() {

    if (!StringUtils.isBlank(awsDynamodbEndpointUrl)) {
      return AmazonDynamoDBClientBuilder
          .standard()
          .withEndpointConfiguration(
              new AwsClientBuilder.EndpointConfiguration(awsDynamodbEndpointUrl, awsRegion))
          .withCredentials(new AWSStaticCredentialsProvider(new BasicAWSCredentials(accessKey, secretKey)))
          .build();
    } else {
      return AmazonDynamoDBClientBuilder
              .standard()
              .withRegion(awsRegion)
              .withCredentials(new AWSStaticCredentialsProvider(new BasicAWSCredentials(accessKey, secretKey)))
              .build();
    }
  }

  @Bean
  public DynamoDB dynamoDB(AmazonDynamoDB client) {
    return   new DynamoDB(client);
  }

  @Bean
  public OrderHistoryDao orderHistoryDao(AmazonDynamoDB client, DynamoDB dynamoDB) {
    return new OrderHistoryDaoDynamoDb(dynamoDB);
  }

  @Bean
  public HealthIndicator dynamoDBHealthIndicator(DynamoDB dynamoDB) {
    return new DynamoDBHealthIndicator(dynamoDB);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/OrderHistoryDynamoDBConfiguration.java:OrderHistoryDynamoDBConfiguration.<init>
// Node: orderHistoryDao
// Node: OrderHistoryDaoDynamoDb
// Node: dynamoDBHealthIndicator
// Node: DynamoDBHealthIndicator
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;


import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Index;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.dynamodbv2.document.ItemCollection;
import com.amazonaws.services.dynamodbv2.document.PrimaryKey;
import com.amazonaws.services.dynamodbv2.document.QueryOutcome;
import com.amazonaws.services.dynamodbv2.document.RangeKeyCondition;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.amazonaws.services.dynamodbv2.document.spec.GetItemSpec;
import com.amazonaws.services.dynamodbv2.document.spec.QuerySpec;
import com.amazonaws.services.dynamodbv2.document.spec.UpdateItemSpec;
import com.amazonaws.services.dynamodbv2.model.AttributeValue;
import com.amazonaws.services.dynamodbv2.model.ConditionalCheckFailedException;
import com.amazonaws.services.dynamodbv2.model.ReturnValue;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.cqrs.orderhistory.Location;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistory;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryFilter;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.apache.commons.lang.StringUtils;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.math.BigDecimal;
import java.text.BreakIterator;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.StreamSupport;

import static java.util.stream.Collectors.toList;
import static java.util.stream.Collectors.toSet;

public class OrderHistoryDaoDynamoDb implements OrderHistoryDao {

  private Logger logger = LoggerFactory.getLogger(getClass());

  public static final String FTGO_ORDER_HISTORY_BY_ID = "ftgo-order-history";
  public static final String FTGO_ORDER_HISTORY_BY_CONSUMER_ID_AND_DATE =
          "ftgo-order-history-by-consumer-id-and-creation-time";
  public static final String ORDER_STATUS_FIELD = "orderStatus";
  private static final String DELIVERY_STATUS_FIELD = "deliveryStatus";

  private final DynamoDB dynamoDB;

  private Table table;
  private Index index;

  public OrderHistoryDaoDynamoDb(DynamoDB dynamoDB) {
    this.dynamoDB = dynamoDB;
    table = this.dynamoDB.getTable(FTGO_ORDER_HISTORY_BY_ID);
    index = table.getIndex(FTGO_ORDER_HISTORY_BY_CONSUMER_ID_AND_DATE);
  }

  @Override
  public boolean addOrder(Order order, Optional<SourceEvent> eventSource) {
    UpdateItemSpec spec = new UpdateItemSpec()
            .withPrimaryKey("orderId", order.getOrderId())
            .withUpdateExpression("SET orderStatus = :orderStatus, " +
                    "creationDate = :creationDate, consumerId = :consumerId, lineItems =" +
                    " :lineItems, keywords = :keywords, restaurantId = :restaurantId, " +
                    " restaurantName = :restaurantName"
            )
            .withValueMap(new Maps()
                    .add(":orderStatus", order.getStatus().toString())
                    .add(":consumerId", order.getConsumerId())
                    .add(":creationDate", order.getCreationDate().getMillis())
                    .add(":lineItems", mapLineItems(order.getLineItems()))
                    .add(":keywords", mapKeywords(order))
                    .add(":restaurantId", order.getRestaurantId())
                    .add(":restaurantName", order.getRestaurantName())
                    .map())
            .withReturnValues(ReturnValue.NONE);
    return idempotentUpdate(spec, eventSource);
  }

  private boolean idempotentUpdate(UpdateItemSpec spec, Optional<SourceEvent>
          eventSource) {
    try {
      table.updateItem(eventSource.map(es -> es.addDuplicateDetection(spec))
              .orElse(spec));
      return true;
    } catch (ConditionalCheckFailedException e) {
      logger.error("not updated {}", eventSource);
      // Do nothing
      return false;
    }
  }

////  @Override
//  public void addOrderV1(Order order, Optional<SourceEvent> eventSource) {
//    Map<String, AttributeValue> keyMapBuilder = makeKey1(order.getOrderId());
//    AvMapBuilder expressionAttrs = new AvMapBuilder(":orderStatus", new
// AttributeValue(order.getStatus().toString()))
//            .add(":cd", new AttributeValue().withN(Long.toString(order
// .getCreationDate().getMillis())))
//            .add(":consumerId", order.getConsumerId())
//            .add(":lineItems", mapLineItems(order.getLineItems()))
//            .add(":keywords", mapKeywords(order))
//            .add(":restaurantName", order.getRestaurantId())
//            ;
//
//
//    UpdateItemRequest uir = new UpdateItemRequest()
//            .withTableName(FTGO_ORDER_HISTORY_BY_ID)
//            .withKey(keyMapBuilder)
//            .withUpdateExpression("SET orderStatus = :orderStatus,
// creationDate = :cd, consumerId = :consumerId, lineItems = :lineItems,
// keywords = :keywords, restaurantName = :restaurantName")
//            .withConditionExpression("attribute_not_exists(orderStatus)")
//            .withExpressionAttributeValues(expressionAttrs.map());
//    try {
//      client.updateItem(uir);
//    } catch (ConditionalCheckFailedException e) {
//      // Do nothing
//    }
//  }

  private Set mapKeywords(Order order) {
    Set<String> keywords = new HashSet<>();
    keywords.addAll(tokenize(order.getRestaurantName()));
    keywords.addAll(tokenize(order.getLineItems().stream().map
            (OrderLineItem::getName).collect(toList())));
    return keywords;
  }

  private Set<String> tokenize(Collection<String> text) {
    return text.stream().flatMap(t -> tokenize(t).stream()).collect(toSet());
  }

  private Set<String> tokenize(String text) {
    Set<String> result = new HashSet<>();
    BreakIterator bi = BreakIterator.getWordInstance();
    bi.setText(text);
    int lastIndex = bi.first();
    while (lastIndex != BreakIterator.DONE) {
      int firstIndex = lastIndex;
      lastIndex = bi.next();
      if (lastIndex != BreakIterator.DONE
              && Character.isLetterOrDigit(text.charAt(firstIndex))) {
        String word = text.substring(firstIndex, lastIndex);
        result.add(word);
      }
    }
    return result;
  }

  private List mapLineItems(List<OrderLineItem> lineItems) {
    return lineItems.stream().map(this::mapOrderLineItem).collect(toList());
  }
//  private AttributeValue mapLineItems(List<OrderLineItem> lineItems) {
//    AttributeValue result = new AttributeValue();
//    result.withL(lineItems.stream().map(this::mapOrderLineItem).collect
// (toList()));
//    return result;
//  }

  private Map mapOrderLineItem(OrderLineItem orderLineItem) {
    return new Maps()
            .add("menuItemName", orderLineItem.getName())
            .add("menuItemId", orderLineItem.getMenuItemId())
            .add("price", orderLineItem.getPrice().asString())
            .add("quantity", orderLineItem.getQuantity())
            .map();
  }
//  private AttributeValue mapOrderLineItem(OrderLineItem orderLineItem) {
//    AttributeValue result = new AttributeValue();
//    result.addMEntry("menuItem", new AttributeValue(orderLineItem
// .getName()));
//    return result;
//  }


  private Map<String, AttributeValue> makeKey1(String orderId) {
    return new AvMapBuilder("orderId", new AttributeValue(orderId)).map();
  }

  @Override
  public OrderHistory findOrderHistory(String consumerId, OrderHistoryFilter
          filter) {

    QuerySpec spec = new QuerySpec()
            .withScanIndexForward(false)
            .withHashKey("consumerId", consumerId)
            .withRangeKeyCondition(new RangeKeyCondition("creationDate").gt
                    (filter.getSince().getMillis()));

    filter.getStartKeyToken().ifPresent(token -> spec.withExclusiveStartKey
            (toStartingPrimaryKey(token)));

    Map<String, Object> valuesMap = new HashMap<>();

    String filterExpression = Expressions.and(
            keywordFilterExpression(valuesMap, filter.getKeywords()),
            statusFilterExpression(valuesMap, filter.getStatus()));

    if (!valuesMap.isEmpty())
      spec.withValueMap(valuesMap);

    if (StringUtils.isNotBlank(filterExpression)) {
      spec.withFilterExpression(filterExpression);
    }

    System.out.print("filterExpression.toString()=" + filterExpression);

    filter.getPageSize().ifPresent(spec::withMaxResultSize);

    ItemCollection<QueryOutcome> result = index.query(spec);

    return new OrderHistory(StreamSupport.stream(result.spliterator(), false)
            .map(this::toOrder).collect(toList()),
            Optional.ofNullable(result.getLastLowLevelResult().getQueryResult
                    ().getLastEvaluatedKey()).map(this::toStartKeyToken));
  }

  private PrimaryKey toStartingPrimaryKey(String token) {
    ObjectMapper om = new ObjectMapper();
    Map<String, Object> map;
    try {
      map = om.readValue(token, Map.class);
    } catch (IOException e) {
      throw new RuntimeException();
    }
    PrimaryKey pk = new PrimaryKey();
    map.entrySet().forEach(key -> {
      pk.addComponent(key.getKey(), key.getValue());
    });
    return pk;
  }

  private String toStartKeyToken(Map<String, AttributeValue> lastEvaluatedKey) {
    Map<String, Object> map = new HashMap<>();
    lastEvaluatedKey.entrySet().forEach(entry -> {
      String value = entry.getValue().getS();
      if (value == null) {
        value = entry.getValue().getN();
        map.put(entry.getKey(), Long.parseLong(value));
      } else {
        map.put(entry.getKey(), value);
      }
    });
    ObjectMapper om = new ObjectMapper();
    try {
      return om.writeValueAsString(map);
    } catch (JsonProcessingException e) {
      throw new RuntimeException();
    }
  }

  private Optional<String> statusFilterExpression(Map<String, Object>
                                                          expressionAttributeValuesBuilder, Optional<OrderState> status) {
    return status.map(s -> {
      expressionAttributeValuesBuilder.put(":orderStatus", s.toString());
      return "orderStatus = :orderStatus";
    });
  }

  private String keywordFilterExpression(Map<String, Object>
                                                 expressionAttributeValuesBuilder, Set<String> kw) {
    Set<String> keywords = tokenize(kw);
    if (keywords.isEmpty()) {
      return "";
    }
    String cuisinesExpression = "";
    int idx = 0;
    for (String cuisine : keywords) {
      String var = ":keyword" + idx;
      String cuisineExpression = String.format("contains(keywords, %s)", var);
      cuisinesExpression = Expressions.or(cuisinesExpression, cuisineExpression);
      expressionAttributeValuesBuilder.put(var, cuisine);
    }

    return cuisinesExpression;
  }

//  @Override
//  public OrderHistory findOrderHistory(String consumerId,
// OrderHistoryFilter filter) {
//    AvMapBuilder expressionAttributeValuesBuilder = new AvMapBuilder
// (":cid", new AttributeValue(consumerId))
//            .add(":oct", new AttributeValue().withN(Long.toString(filter
// .getSince().getMillis())));
//    StringBuilder filterExpression = new StringBuilder();
//    Set<String> keywords = tokenize(filter.getKeywords());
//    if (!keywords.isEmpty()) {
//      if (filterExpression.length() > 0)
//        filterExpression.append(" AND ");
//      filterExpression.append(" ( ");
//      int idx = 0;
//      for (String cuisine : keywords) {
//        if (idx++ > 0) {
//          filterExpression.append(" OR ");
//        }
//        String var = ":keyword" + idx;
//        filterExpression.append("contains(keywords, ").append(var).append
// (')');
//        expressionAttributeValuesBuilder.add(var, cuisine);
//      }
//
//      filterExpression.append(" ) ");
//    }
//    filter.getStatus().ifPresent(status -> {
//      if (filterExpression.length() > 0)
//        filterExpression.append(" AND ");
//      filterExpression.append("orderStatus = :orderStatus");
//      expressionAttributeValuesBuilder.add(":orderStatus", status.toString
// ());
//    });
//    QueryRequest ar = new QueryRequest()
//            .withTableName(FTGO_ORDER_HISTORY_BY_ID)
//            .withIndexName(FTGO_ORDER_HISTORY_BY_CONSUMER_ID_AND_DATE)
//            .withScanIndexForward(false)
//            .withKeyConditionExpression("consumerId = :cid AND
// creationDate > :oct")
//            .withExpressionAttributeValues
// (expressionAttributeValuesBuilder.map());
//    System.out.print("filterExpression.toString()=" + filterExpression
// .toString());
//    if (filterExpression.length() > 0)
//      ar.withFilterExpression(filterExpression.toString());
//
//    QuerySpec spec = new QuerySpec();
//    ItemCollection<QueryOutcome> result = table.query(spec);
//
//    List<Map<String, AttributeValue>> items = client.query(ar).getItems();
//    return new OrderHistory(items.stream().map(this::toOrder).collect
// (toList()));
//  }

  @Override
  public boolean updateOrderState(String orderId, OrderState newState, Optional<SourceEvent> eventSource) {
    UpdateItemSpec spec = new UpdateItemSpec()
            .withPrimaryKey("orderId", orderId)
            .withUpdateExpression("SET #orderStatus = :orderStatus")
            .withNameMap(Collections.singletonMap("#orderStatus",
                    ORDER_STATUS_FIELD))
            .withValueMap(Collections.singletonMap(":orderStatus", newState.toString()))
            .withReturnValues(ReturnValue.NONE);
    return idempotentUpdate(spec, eventSource);
  }


  static PrimaryKey makePrimaryKey(String orderId) {
    return new PrimaryKey().addComponent("orderId", orderId);
  }

  @Override
  public void noteTicketPreparationStarted(String orderId) {
    throw new UnsupportedOperationException();
  }

  @Override
  public void noteTicketPreparationCompleted(String orderId) {
    throw new UnsupportedOperationException();

  }

  @Override
  public void notePickedUp(String orderId, Optional<SourceEvent> eventSource) {
    UpdateItemSpec spec = new UpdateItemSpec()
            .withPrimaryKey("orderId", orderId)
            .withUpdateExpression("SET #deliveryStatus = :deliveryStatus")
            .withNameMap(Collections.singletonMap("#deliveryStatus",
                    DELIVERY_STATUS_FIELD))
            .withValueMap(Collections.singletonMap(":deliveryStatus",
                    DeliveryStatus.PICKED_UP.toString()))
            .withReturnValues(ReturnValue.NONE);
    idempotentUpdate(spec, eventSource);
  }

  @Override
  public void updateLocation(String orderId, Location location) {
    throw new UnsupportedOperationException();

  }

  @Override
  public void noteDelivered(String orderId) {
    throw new UnsupportedOperationException();

  }

  @Override
  public Optional<Order> findOrder(String orderId) {
    Item item = table.getItem(new GetItemSpec()
            .withPrimaryKey(makePrimaryKey(orderId))
            .withConsistentRead(true));
    return Optional.ofNullable(item).map(this::toOrder);
  }


  private Order toOrder(Item avs) {
    Order order = new Order(avs.getString("orderId"),
            avs.getString("consumerId"),
            OrderState.valueOf(avs.getString("orderStatus")),
            toLineItems2(avs.getList("lineItems")),
            null,
            avs.getLong("restaurantId"),
            avs.getString("restaurantName"));
    if (avs.hasAttribute("creationDate"))
      order.setCreationDate(new DateTime(avs.getLong("creationDate")));
    return order;
  }


  private List<OrderLineItem> toLineItems2(List<LinkedHashMap<String,
          Object>> lineItems) {
    return lineItems.stream().map(this::toLineItem2).collect(toList());
  }

  private OrderLineItem toLineItem2(LinkedHashMap<String, Object>
                                            attributeValue) {
    return new OrderLineItem((String) attributeValue.get("menuItemId"),
                             (String) attributeValue.get("menuItemName"),
                             new Money((String) attributeValue.get("price")),
                            ((BigDecimal) attributeValue.get("quantity")).intValue()
            );
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/OrderHistoryDaoDynamoDb.java:OrderHistoryDaoDynamoDb.<init>
// Node: getTable
// Node: getIndex
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Table;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;

public class DynamoDBHealthIndicator implements HealthIndicator {
  private final Table table;
  private DynamoDB dynamoDB;

  public DynamoDBHealthIndicator(DynamoDB dynamoDB) {
    this.dynamoDB = dynamoDB;
    this.table = this.dynamoDB.getTable(OrderHistoryDaoDynamoDb.FTGO_ORDER_HISTORY_BY_ID);
  }

  @Override
  public Health health() {
    try {
      table.getItem(OrderHistoryDaoDynamoDb.makePrimaryKey("999"));
      return Health.up().build();
    } catch (Exception e) {
      return Health.down(e).build();
    }
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/DynamoDBHealthIndicator.java:DynamoDBHealthIndicator.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory.messaging;

import io.eventuate.tram.events.subscriber.DomainEventEnvelope;
import io.eventuate.tram.events.subscriber.DomainEventHandlers;
import io.eventuate.tram.events.subscriber.DomainEventHandlersBuilder;
import net.chrisrichardson.ftgo.cqrs.orderhistory.DeliveryPickedUp;
import net.chrisrichardson.ftgo.cqrs.orderhistory.Location;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.Order;
import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.SourceEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Optional;

public class OrderHistoryEventHandlers {

  private OrderHistoryDao orderHistoryDao;

  public OrderHistoryEventHandlers(OrderHistoryDao orderHistoryDao) {
    this.orderHistoryDao = orderHistoryDao;
  }

  private Logger logger = LoggerFactory.getLogger(getClass());

  // TODO - determine events

  private String orderId;
  private Order order;
  private Location location; //

  public DomainEventHandlers domainEventHandlers() {
    return DomainEventHandlersBuilder
            .forAggregateType("net.chrisrichardson.ftgo.orderservice.domain.Order")
            .onEvent(OrderCreatedEvent.class, this::handleOrderCreated)
            .onEvent(OrderAuthorized.class, this::handleOrderAuthorized)
            .onEvent(OrderCancelled.class, this::handleOrderCancelled)
            .onEvent(OrderRejected.class, this::handleOrderRejected)
//            .onEvent(DeliveryPickedUp.class, this::handleDeliveryPickedUp)
            .build();
  }

  private Optional<SourceEvent> makeSourceEvent(DomainEventEnvelope<?> dee) {
    return Optional.of(new SourceEvent(dee.getAggregateType(),
            dee.getAggregateId(), dee.getEventId()));
  }

  public void handleOrderCreated(DomainEventEnvelope<OrderCreatedEvent> dee) {
    logger.debug("handleOrderCreated called {}", dee);
    boolean result = orderHistoryDao.addOrder(makeOrder(dee.getAggregateId(), dee.getEvent()), makeSourceEvent(dee));
    logger.debug("handleOrderCreated result {} {}", dee, result);
  }

  public void handleOrderAuthorized(DomainEventEnvelope<OrderAuthorized> dee) {
    logger.debug("handleOrderAuthorized called {}", dee);
    boolean result = orderHistoryDao.updateOrderState(dee.getAggregateId(), OrderState.APPROVED, makeSourceEvent(dee));
    logger.debug("handleOrderAuthorized result {} {}", dee, result);
  }

  public void handleOrderCancelled(DomainEventEnvelope<OrderCancelled> dee) {
    logger.debug("handleOrderCancelled called {}", dee);
    boolean result = orderHistoryDao.updateOrderState(dee.getAggregateId(), OrderState.CANCELLED, makeSourceEvent(dee));
    logger.debug("handleOrderCancelled result {} {}", dee, result);
  }

  public void handleOrderRejected(DomainEventEnvelope<OrderRejected> dee) {
    logger.debug("handleOrderRejected called {}", dee);
    boolean result = orderHistoryDao.updateOrderState(dee.getAggregateId(), OrderState.REJECTED, makeSourceEvent(dee));
    logger.debug("handleOrderRejected result {} {}", dee, result);
  }

  private Order makeOrder(String orderId, OrderCreatedEvent event) {
    return new Order(orderId,
            Long.toString(event.getOrderDetails().getConsumerId()),
            OrderState.APPROVAL_PENDING,
            event.getOrderDetails().getLineItems(),
            event.getOrderDetails().getOrderTotal(),
            event.getOrderDetails().getRestaurantId(),
            event.getRestaurantName());
  }

  public void handleDeliveryPickedUp(DomainEventEnvelope<DeliveryPickedUp>
                                             dee) {
    orderHistoryDao.notePickedUp(dee.getEvent().getOrderId(),
            makeSourceEvent(dee));
  }
/*

  // TODO - need a common API that abstracts message vs. event sourcing

  public void handleOrderCancelled() {

    orderHistoryDao.cancelOrder(orderId, null);
  }

  public void handleTicketPreparationStarted() {
    orderHistoryDao.noteTicketPreparationStarted(orderId);
  }

  public void handleTicketPreparationCompleted() {
    orderHistoryDao.noteTicketPreparationCompleted(orderId);
  }

  public void handleDeliveryLocationUpdated() {
    orderHistoryDao.updateLocation(orderId, location);
  }

  public void handleDeliveryDelivered() {
    orderHistoryDao.noteDelivered(orderId);
  }
  */
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/messaging/OrderHistoryEventHandlers.java:OrderHistoryEventHandlers.<init>
// Node: OrderHistoryEventHandlers
package net.chrisrichardson.ftgo.cqrs.orderhistory.messaging;

import io.eventuate.tram.spring.consumer.common.TramNoopDuplicateMessageDetectorConfiguration;
import io.eventuate.tram.spring.events.subscriber.TramEventSubscriberConfiguration;
import io.eventuate.tram.events.subscriber.DomainEventDispatcher;
import io.eventuate.tram.events.subscriber.DomainEventDispatcherFactory;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import({CommonConfiguration.class, TramNoopDuplicateMessageDetectorConfiguration.class, TramEventSubscriberConfiguration.class})
public class OrderHistoryServiceMessagingConfiguration {

  @Bean
  public OrderHistoryEventHandlers orderHistoryEventHandlers(OrderHistoryDao orderHistoryDao) {
    return new OrderHistoryEventHandlers(orderHistoryDao);
  }

  @Bean
  public DomainEventDispatcher orderHistoryDomainEventDispatcher(OrderHistoryEventHandlers orderHistoryEventHandlers, DomainEventDispatcherFactory domainEventDispatcherFactory) {
    return domainEventDispatcherFactory.make("orderHistoryDomainEventDispatcher", orderHistoryEventHandlers.domainEventHandlers());
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/messaging/OrderHistoryServiceMessagingConfiguration.java:OrderHistoryServiceMessagingConfiguration.<init>
// Node: orderHistoryEventHandlers
package net.chrisrichardson.ftgo.orderhistory.contracts;

import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.spring.consumer.common.TramNoopDuplicateMessageDetectorConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryCommonConfiguration;
import io.eventuate.tram.messaging.common.ChannelMapping;
import io.eventuate.tram.messaging.common.DefaultChannelMapping;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.Order;
import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.SourceEvent;
import net.chrisrichardson.ftgo.cqrs.orderhistory.messaging.OrderHistoryServiceMessagingConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.stubrunner.StubFinder;
import org.springframework.cloud.contract.stubrunner.spring.AutoConfigureStubRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Optional;

import static io.eventuate.util.test.async.Eventually.eventually;
import static org.junit.Assert.assertEquals;
import static org.mockito.Matchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderHistoryEventHandlersTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureStubRunner(ids =
        {"net.chrisrichardson.ftgo:ftgo-order-service-contracts"}
        )
@DirtiesContext
public class OrderHistoryEventHandlersTest {

  @Configuration
  @EnableAutoConfiguration
  @Import({OrderHistoryServiceMessagingConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramInMemoryCommonConfiguration.class,
          TramNoopDuplicateMessageDetectorConfiguration.class,
          EventuateContractVerifierConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public ChannelMapping channelMapping() {
      return new DefaultChannelMapping.DefaultChannelMappingBuilder().build();
    }

    @Bean
    public OrderHistoryDao orderHistoryDao() {
      return mock(OrderHistoryDao.class);
    }
  }

  @Autowired
  private StubFinder stubFinder;

  @Autowired
  private OrderHistoryDao orderHistoryDao;

  @Test
  public void shouldHandleOrderCreatedEvent() throws InterruptedException {
    when(orderHistoryDao.addOrder(any(Order.class), any(Optional.class))).thenReturn(false);

    stubFinder.trigger("orderCreatedEvent");

    eventually(() -> {
      ArgumentCaptor<Order> orderArg = ArgumentCaptor.forClass(Order.class);
      ArgumentCaptor<Optional<SourceEvent>> sourceEventArg = ArgumentCaptor.forClass(Optional.class);
      verify(orderHistoryDao).addOrder(orderArg.capture(), sourceEventArg.capture());

      Order order = orderArg.getValue();
      Optional<SourceEvent> sourceEvent = sourceEventArg.getValue();

      assertEquals("Ajanta", order.getRestaurantName());
    });
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/test/java/net/chrisrichardson/ftgo/orderhistory/contracts/OrderHistoryEventHandlersTest.java:OrderHistoryEventHandlersTest.<init>
package net.chrisrichardson.ftgo.orderservice.cucumber;

import cucumber.api.CucumberOptions;
import cucumber.api.junit.Cucumber;
import org.junit.runner.RunWith;

@RunWith(Cucumber.class)
@CucumberOptions(features = "src/component-test/resources/features")
public class OrderServiceComponentTest {
}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/component-test/java/net/chrisrichardson/ftgo/orderservice/cucumber/OrderServiceComponentTest.java:OrderServiceComponentTest.<init>
// Node: CucumberOptions
package net.chrisrichardson.ftgo.orderservice.cucumber;

import cucumber.api.java.Before;
import cucumber.api.java.en.And;
import cucumber.api.java.en.Given;
import cucumber.api.java.en.Then;
import cucumber.api.java.en.When;
import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.messaging.consumer.MessageConsumer;
import io.eventuate.tram.sagas.testing.SagaParticipantChannels;
import io.eventuate.tram.sagas.testing.SagaParticipantStubManager;
import io.eventuate.tram.sagas.spring.testing.SagaParticipantStubManagerConfiguration;
import io.eventuate.tram.testing.MessageTracker;
import io.restassured.response.Response;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.kitchenservice.api.CancelCreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmCreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicketReply;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderRequest;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.domain.RestaurantRepository;
import net.chrisrichardson.ftgo.testutil.FtgoTestUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.ContextConfiguration;

import java.util.Arrays;
import java.util.Collections;

import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withSuccess;
import static io.eventuate.util.test.async.Eventually.eventually;
import static io.restassured.RestAssured.given;
import static java.util.Collections.singleton;
import static org.junit.Assert.*;


@SpringBootTest(classes = OrderServiceComponentTestStepDefinitions.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@ContextConfiguration
public class OrderServiceComponentTestStepDefinitions {



  private Response response;
  private long consumerId;

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  private int port = 8082;
  private String host = FtgoTestUtil.getDockerHostIp();

  protected String baseUrl(String path) {
    return String.format("http://%s:%s%s", host, port, path);
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({TramJdbcKafkaConfiguration.class, SagaParticipantStubManagerConfiguration.class})
  @EnableJpaRepositories(basePackageClasses = RestaurantRepository.class) // Need to verify that the restaurant has been created. Replace with verifyRestaurantCreatedInOrderService
  @EntityScan(basePackageClasses = Order.class)
  public static class TestConfiguration {

    @Bean
    public SagaParticipantChannels sagaParticipantChannels() {
      return new SagaParticipantChannels("consumerService", "kitchenService", "accountingService", "orderService");
    }

    @Bean
    public MessageTracker messageTracker(MessageConsumer messageConsumer) {
      return new MessageTracker(singleton("net.chrisrichardson.ftgo.orderservice.domain.Order"), messageConsumer) ;
    }

  }

  @Autowired
  protected SagaParticipantStubManager sagaParticipantStubManager;

  @Autowired
  protected MessageTracker messageTracker;

  @Autowired
  protected DomainEventPublisher domainEventPublisher;

  @Autowired
  protected RestaurantRepository restaurantRepository;


  @Before
  public void setUp() {
    sagaParticipantStubManager.reset();
  }

  @Given("A valid consumer")
  public void useConsumer() {
    sagaParticipantStubManager.
            forChannel("consumerService")
            .when(ValidateOrderByConsumer.class).replyWith(cm -> withSuccess());
  }

  public enum CreditCardType { valid, expired}

  @Given("using a(.?) (.*) credit card")
  public void useCreditCard(String ignore, CreditCardType creditCard) {
    switch (creditCard) {
      case valid :
        sagaParticipantStubManager
                .forChannel("accountingService")
                .when(AuthorizeCommand.class).replyWithSuccess();
        break;
      case expired:
        sagaParticipantStubManager
                .forChannel("accountingService")
                .when(AuthorizeCommand.class).replyWithFailure();
        break;
      default:
        fail("Don't know what to do with this credit card");
    }
  }

  @Given("the restaurant is accepting orders")
  public void restaurantAcceptsOrder() {
    sagaParticipantStubManager
            .forChannel("kitchenService")
            .when(CreateTicket.class).replyWith(cm -> withSuccess(new CreateTicketReply(cm.getCommand().getOrderId())))
            .when(ConfirmCreateTicket.class).replyWithSuccess()
            .when(CancelCreateTicket.class).replyWithSuccess();

    if (!restaurantRepository.findById(RestaurantMother.AJANTA_ID).isPresent()) {
      domainEventPublisher.publish("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant", RestaurantMother.AJANTA_ID,
              Collections.singletonList(RestaurantMother.makeAjantaRestaurantCreatedEvent()));

      eventually(() -> {
        FtgoTestUtil.assertPresent(restaurantRepository.findById(RestaurantMother.AJANTA_ID));
      });
    }
  }

  @When("I place an order for Chicken Vindaloo at Ajanta")
  public void placeOrder() {

    response = given().
            body(new CreateOrderRequest(consumerId,
                    RestaurantMother.AJANTA_ID, OrderDetailsMother.DELIVERY_ADDRESS, OrderDetailsMother.DELIVERY_TIME, Collections.singletonList(
                            new CreateOrderRequest.LineItem(RestaurantMother.CHICKEN_VINDALOO_MENU_ITEM_ID,
                                                            OrderDetailsMother.CHICKEN_VINDALOO_QUANTITY)))).
            contentType("application/json").
            when().
            post(baseUrl("/orders"));
  }

  @Then("the order should be (.*)")
  public void theOrderShouldBeInState(String desiredOrderState) {

      // TODO This doesn't make sense when the `OrderService` is live => duplicate replies

//    sagaParticipantStubManager
//            .forChannel("orderService")
//            .when(ApproveOrderCommand.class).replyWithSuccess();
//
    Integer orderId =
            this.response.
                    then().
                    statusCode(200).
                    extract().
                    path("orderId");

    assertNotNull(orderId);

    eventually(() -> {
      String state = given().
              when().
              get(baseUrl("/orders/" + orderId)).
              then().
              statusCode(200)
              .extract().
                      path("state");
      assertEquals(desiredOrderState, state);
    });

    sagaParticipantStubManager.verifyCommandReceived("kitchenService", CreateTicket.class);

  }

  @And("an (.*) event should be published")
  public void verifyEventPublished(String expectedEventClass) {
    messageTracker.assertDomainEventPublished("net.chrisrichardson.ftgo.orderservice.domain.Order",
            findEventClass(expectedEventClass, "net.chrisrichardson.ftgo.orderservice.domain", "net.chrisrichardson.ftgo.orderservice.api.events"));
  }

  private String findEventClass(String expectedEventClass, String... packages) {
    return Arrays.stream(packages).map(p -> p + "." + expectedEventClass).filter(className -> {
      try {
        Class.forName(className);
        return true;
      } catch (ClassNotFoundException e) {
        return false;
      }
    }).findFirst().orElseThrow(() -> new RuntimeException(String.format("Cannot find class %s in packages %s", expectedEventClass, String.join(",", packages))));
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/component-test/java/net/chrisrichardson/ftgo/orderservice/cucumber/OrderServiceComponentTestStepDefinitions.java:OrderServiceComponentTestStepDefinitions.<init>
package net.chrisrichardson.ftgo.orderservice.grpc;

import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import static org.mockito.Mockito.mock;

@Configuration
@Import(GrpcConfiguration.class)
public class OrderServiceGrpIntegrationTestConfiguration {

  @Bean
  public OrderService orderService() {
    return mock(OrderService.class);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/grpc/OrderServiceGrpIntegrationTestConfiguration.java:OrderServiceGrpIntegrationTestConfiguration.<init>
package net.chrisrichardson.ftgo.orderservice.grpc;


import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.domain.DeliveryInformation;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

import static org.junit.Assert.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderServiceGrpIntegrationTestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
public class OrderServiceGrpIntegrationTest {

  @Autowired
  private OrderService orderService;

  @Test
  public void shouldCreateOrder() {

    Order order = OrderDetailsMother.CHICKEN_VINDALOO_ORDER;

    when(orderService.createOrder(any(Long.class), any(Long.class), any(DeliveryInformation.class), any(List.class))).thenReturn(order);

    OrderServiceClient client = new OrderServiceClient("localhost", 50051);

    List<MenuItemIdAndQuantity> expectedLineItems = order.getLineItems().stream().map(li -> new MenuItemIdAndQuantity(li.getMenuItemId(), li.getQuantity())).collect(Collectors.toList());

    long orderId = client.createOrder(order.getConsumerId(), order.getRestaurantId(), expectedLineItems, order.getDeliveryInformation().getDeliveryAddress(), order.getDeliveryInformation().getDeliveryTime());

    assertEquals((long)order.getId(), orderId);

    verify(orderService).createOrder(order.getConsumerId(), order.getRestaurantId(), order.getDeliveryInformation(), expectedLineItems);

  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/grpc/OrderServiceGrpIntegrationTest.java:OrderServiceGrpIntegrationTest.<init>
package net.chrisrichardson.ftgo.orderservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.domain.OrderDomainEventPublisher;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER_DETAILS;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT_NAME;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryserviceMessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class DeliveryserviceMessagingBase {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public OrderDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new OrderDomainEventPublisher(eventPublisher);
    }
  }

  @Autowired
  private OrderDomainEventPublisher orderAggregateEventPublisher;

  protected void orderCreatedEvent() {
    orderAggregateEventPublisher.publish(CHICKEN_VINDALOO_ORDER,
            Collections.singletonList(new OrderCreatedEvent(CHICKEN_VINDALOO_ORDER_DETAILS, OrderDetailsMother.DELIVERY_ADDRESS, AJANTA_RESTAURANT_NAME)));
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/contract/DeliveryserviceMessagingBase.java:DeliveryserviceMessagingBase.<init>
package net.chrisrichardson.ftgo.orderservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.domain.OrderDomainEventPublisher;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER_DETAILS;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT_NAME;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = MessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class MessagingBase {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public OrderDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new OrderDomainEventPublisher(eventPublisher);
    }
  }


  @Autowired
  private OrderDomainEventPublisher orderAggregateEventPublisher;

  protected void orderCreated() {
    orderAggregateEventPublisher.publish(CHICKEN_VINDALOO_ORDER,
            Collections.singletonList(new OrderCreatedEvent(CHICKEN_VINDALOO_ORDER_DETAILS, OrderDetailsMother.DELIVERY_ADDRESS, AJANTA_RESTAURANT_NAME)));
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/contract/MessagingBase.java:MessagingBase.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import io.eventuate.tram.sagas.spring.inmemory.TramSagaInMemoryConfiguration;
import io.eventuate.tram.sagas.spring.testing.contract.EventuateTramSagasSpringCloudContractSupportConfiguration;
import io.eventuate.tram.sagas.spring.testing.contract.SagaMessagingTestHelper;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateTramRoutesConfigurer;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicketReply;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketLineItem;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSaga;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.stubrunner.BatchStubRunner;
import org.springframework.cloud.contract.stubrunner.spring.AutoConfigureStubRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_QUANTITY;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.*;
import static org.junit.Assert.assertEquals;

@RunWith(SpringRunner.class)
@SpringBootTest(classes= KitchenServiceProxyIntegrationTest.TestConfiguration.class,
        webEnvironment= SpringBootTest.WebEnvironment.NONE)
@AutoConfigureStubRunner(ids =
        {"net.chrisrichardson.ftgo:ftgo-kitchen-service-contracts"}
        )
@DirtiesContext
public class KitchenServiceProxyIntegrationTest {


  @Configuration
  @EnableAutoConfiguration
  @Import({TramSagaInMemoryConfiguration.class, EventuateTramSagasSpringCloudContractSupportConfiguration.class})
  public static class TestConfiguration {


    @Bean
    public EventuateTramRoutesConfigurer eventuateTramRoutesConfigurer(BatchStubRunner batchStubRunner) {
      return new EventuateTramRoutesConfigurer(batchStubRunner);
    }

    @Bean
    public KitchenServiceProxy kitchenServiceProxy() {
      return new KitchenServiceProxy();
    }
  }

  @Autowired
  private SagaMessagingTestHelper sagaMessagingTestHelper;

  @Autowired
  private KitchenServiceProxy kitchenServiceProxy;

  @Test
  public void shouldSuccessfullyCreateTicket() {
    CreateTicket command = new CreateTicket(AJANTA_ID, OrderDetailsMother.ORDER_ID,
            new TicketDetails(Collections.singletonList(new TicketLineItem(CHICKEN_VINDALOO_MENU_ITEM_ID, CHICKEN_VINDALOO, CHICKEN_VINDALOO_QUANTITY))));
    CreateTicketReply expectedReply = new CreateTicketReply(OrderDetailsMother.ORDER_ID);
    String sagaType = CreateOrderSaga.class.getName();

    CreateTicketReply reply = sagaMessagingTestHelper.sendAndReceiveCommand(kitchenServiceProxy.create, command, CreateTicketReply.class, sagaType);

    assertEquals(expectedReply, reply);

  }

}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/KitchenServiceProxyIntegrationTest.java:KitchenServiceProxyIntegrationTest.<init>
// Node: eventuateTramRoutesConfigurer
// Node: EventuateTramRoutesConfigurer
package net.chrisrichardson.ftgo.orderservice.domain;

import com.jayway.jsonpath.JsonPath;
import io.eventuate.tram.commands.common.CommandMessageHeaders;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.messaging.common.Message;
import io.eventuate.tram.sagas.spring.inmemory.TramSagaInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import io.eventuate.util.test.async.Eventually;
import net.chrisrichardson.ftgo.consumerservice.api.ConsumerServiceChannels;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.messaging.OrderServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.orderservice.service.OrderCommandHandlersConfiguration;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;
import net.chrisrichardson.ftgo.orderservice.web.OrderWebConfiguration;
import net.chrisrichardson.ftgo.testutil.FtgoTestUtil;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.function.Predicate;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderServiceIntegrationTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties="eventuate.database.schema=eventuate"
)
public class OrderServiceIntegrationTest {


  public static final String RESTAURANT_ID = "1";
  @Value("${local.server.port}")
  private int port;

  private String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({OrderWebConfiguration.class, OrderServiceMessagingConfiguration.class,  OrderCommandHandlersConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramSagaInMemoryConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }


    @Bean
    public TestMessageConsumer2 mockConsumerService() {
      return new TestMessageConsumer2("mockConsumerService", ConsumerServiceChannels.consumerServiceChannel);
    }
  }

  @Autowired
  private DomainEventPublisher domainEventPublisher;

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private OrderService orderService;

  private static final String CHICKED_VINDALOO_MENU_ITEM_ID = "1";

  @Autowired
  private OrderRepository orderRepository;

  @Autowired
  @Qualifier("mockConsumerService")
  private TestMessageConsumer2  mockConsumerService;

  @Test
  public void shouldCreateOrder() {
    domainEventPublisher.publish("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant", RESTAURANT_ID,
            Collections.singletonList(RestaurantMother.makeAjantaRestaurantCreatedEvent()));

    Eventually.eventually(() -> {
      FtgoTestUtil.assertPresent(restaurantRepository.findById(Long.parseLong(RESTAURANT_ID)));
    });

    long consumerId = 1511300065921L;

    Order order = orderService.createOrder(consumerId, Long.parseLong(RESTAURANT_ID), OrderDetailsMother.DELIVERY_INFORMATION, Collections.singletonList(new MenuItemIdAndQuantity(CHICKED_VINDALOO_MENU_ITEM_ID, 5)));

    FtgoTestUtil.assertPresent(orderRepository.findById(order.getId()));

    String expectedPayload = "{\"consumerId\":1511300065921,\"orderId\":1,\"orderTotal\":\"61.70\"}";

    Message message = mockConsumerService.assertMessageReceived(
            commandMessageOfType(ValidateOrderByConsumer.class.getName()).and(withPayload(expectedPayload)));

    System.out.println("message=" + message);

  }

  private Predicate<? super Message> withPayload(String expectedPayload) {
    return (m) -> expectedPayload.equals(m.getPayload());
  }

  private Predicate<Message> forConsumer(long consumerId) {
    return (m) -> {
      Object doc = com.jayway.jsonpath.Configuration.defaultConfiguration().jsonProvider().parse(m.getPayload());
      Object s = JsonPath.read(doc, "$.consumerId");
      return new Long(consumerId).equals(s);
    };
  }

  private Predicate<Message> commandMessageOfType(String commandType) {
    return (m) -> m.getRequiredHeader(CommandMessageHeaders.COMMAND_TYPE).equals(commandType);
  }

}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/domain/OrderServiceIntegrationTest.java:OrderServiceIntegrationTest.<init>
// Node: mockConsumerService
// Node: TestMessageConsumer2
// Node: Qualifier
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.transaction.support.TransactionTemplate;

import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CONSUMER_ID;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.chickenVindalooLineItems;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_ID;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderJpaTestConfiguration.class)
public class OrderJpaTest {

  @Autowired
  private OrderRepository orderRepository;

  @Autowired
  private TransactionTemplate transactionTemplate;

  @Test
  public void shouldSaveAndLoadOrder() {

    long orderId = transactionTemplate.execute((ts) -> {
      Order order = new Order(CONSUMER_ID, AJANTA_ID, OrderDetailsMother.DELIVERY_INFORMATION, chickenVindalooLineItems());
      orderRepository.save(order);
      return order.getId();
    });


    transactionTemplate.execute((ts) -> {
      Order order = orderRepository.findById(orderId).get();

      assertNotNull(order);
      assertEquals(OrderState.APPROVAL_PENDING, order.getState());
      assertEquals(AJANTA_ID, order.getRestaurantId());
      assertEquals(CONSUMER_ID, order.getConsumerId().longValue());
      assertEquals(chickenVindalooLineItems(), order.getLineItems());
      return null;
    });

  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/domain/OrderJpaTest.java:OrderJpaTest.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.spring.consumer.jdbc.TramConsumerJdbcAutoConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@Configuration
@EnableJpaRepositories
@EnableAutoConfiguration(exclude = TramConsumerJdbcAutoConfiguration.class)
public class OrderJpaTestConfiguration {
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/domain/OrderJpaTestConfiguration.java:OrderJpaTestConfiguration.<init>
// Node: EnableAutoConfiguration
package net.chrisrichardson.ftgo.orderservice.domain;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.transaction.support.TransactionTemplate;

import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.*;
import static org.junit.Assert.assertEquals;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderJpaTestConfiguration.class)
public class RestaurantJpaTest {

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private TransactionTemplate transactionTemplate;

  @Test
  public void shouldSaveAndLoadRestaurant() {
    long restaurantId = saveRestaurant();
    assertEquals(AJANTA_ID, restaurantId);
    loadRestaurant(restaurantId);
  }

  @Test
  public void shouldSaveRestaurantTwice() {
    long restaurantId1 = saveRestaurant();
    long restaurantId2 = saveRestaurant();
    assertEquals(AJANTA_ID, restaurantId1);
    assertEquals(restaurantId1, restaurantId2);
    loadRestaurant(restaurantId1);
  }

  private void loadRestaurant(long restaurantId) {
    transactionTemplate.execute(ts -> {
      Restaurant restaurant = restaurantRepository.findById(restaurantId).get();
      assertEquals(AJANTA_RESTAURANT_NAME, restaurant.getName());
      assertEquals(AJANTA_RESTAURANT_MENU_ITEMS, restaurant.getMenuItems());
      return null;
    });
  }


  private long saveRestaurant() {
    return transactionTemplate.execute((ts) -> {
        Restaurant restaurant = new Restaurant(AJANTA_ID, AJANTA_RESTAURANT_NAME, AJANTA_RESTAURANT_MENU_ITEMS);
        restaurantRepository.save(restaurant);
        return restaurant.getId();
      });
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/domain/RestaurantJpaTest.java:RestaurantJpaTest.<init>
package net.chrisrichardson.ftgo.orderservice.sagas.reviseorder;

import io.eventuate.tram.commands.consumer.CommandWithDestination;
import io.eventuate.tram.sagas.simpledsl.SimpleSaga;
import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.BeginReviseOrderCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.BeginReviseOrderReply;
import net.chrisrichardson.ftgo.kitchenservice.api.BeginReviseTicketCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ConfirmReviseOrderCommand;
import net.chrisrichardson.ftgo.accountservice.api.ReviseAuthorization;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.UndoBeginReviseOrderCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmReviseTicketCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.KitchenServiceChannels;
import net.chrisrichardson.ftgo.kitchenservice.api.UndoBeginReviseTicketCommand;
import io.eventuate.tram.sagas.orchestration.SagaDefinition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.PostConstruct;

import static io.eventuate.tram.commands.consumer.CommandWithDestinationBuilder.send;

public class ReviseOrderSaga implements SimpleSaga<ReviseOrderSagaData> {

  private Logger logger = LoggerFactory.getLogger(getClass());

  private SagaDefinition<ReviseOrderSagaData> sagaDefinition;

  @PostConstruct
  public void initializeSagaDefinition() {
    sagaDefinition = step()
            .invokeParticipant(this::beginReviseOrder)
            .onReply(BeginReviseOrderReply.class, this::handleBeginReviseOrderReply)
            .withCompensation(this::undoBeginReviseOrder)
            .step()
            .invokeParticipant(this::beginReviseTicket)
            .withCompensation(this::undoBeginReviseTicket)
            .step()
            .invokeParticipant(this::reviseAuthorization)
            .step()
            .invokeParticipant(this::confirmTicketRevision)
            .step()
            .invokeParticipant(this::confirmOrderRevision)
            .build();
  }

  private void handleBeginReviseOrderReply(ReviseOrderSagaData data, BeginReviseOrderReply reply) {
    logger.info("ƒ order total: {}", reply.getRevisedOrderTotal());
    data.setRevisedOrderTotal(reply.getRevisedOrderTotal());
  }

  @Override
  public SagaDefinition<ReviseOrderSagaData> getSagaDefinition() {
    return sagaDefinition;
  }

  private CommandWithDestination confirmOrderRevision(ReviseOrderSagaData data) {
    return send(new ConfirmReviseOrderCommand(data.getOrderId(), data.getOrderRevision()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination confirmTicketRevision(ReviseOrderSagaData data) {
    return send(new ConfirmReviseTicketCommand(data.getRestaurantId(), data.getOrderId(), data.getOrderRevision().getRevisedOrderLineItems()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination reviseAuthorization(ReviseOrderSagaData data) {
    return send(new ReviseAuthorization(data.getConsumerId(), data.getOrderId(), data.getRevisedOrderTotal()))
            .to(AccountingServiceChannels.accountingServiceChannel)
            .build();

  }

  private CommandWithDestination undoBeginReviseTicket(ReviseOrderSagaData data) {
    return send(new UndoBeginReviseTicketCommand(data.getRestaurantId(), data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination beginReviseTicket(ReviseOrderSagaData data) {
    return send(new BeginReviseTicketCommand(data.getRestaurantId(), data.getOrderId(), data.getOrderRevision().getRevisedOrderLineItems()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination undoBeginReviseOrder(ReviseOrderSagaData data) {
    return send(new UndoBeginReviseOrderCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();
  }

  private CommandWithDestination beginReviseOrder(ReviseOrderSagaData data) {
    return send(new BeginReviseOrderCommand(data.getOrderId(), data.getOrderRevision()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();

  }



}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagas/reviseorder/ReviseOrderSaga.java:ReviseOrderSaga.<init>
// Node: initializeSagaDefinition
// Node: step
// Node: invokeParticipant
// Node: onReply
// Node: withCompensation
package net.chrisrichardson.ftgo.orderservice.sagas.createorder;

import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ApproveOrderCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.RejectOrderCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.*;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

import static java.util.stream.Collectors.toList;

public class CreateOrderSagaState {

  private Logger logger = LoggerFactory.getLogger(getClass());

  private Long orderId;

  private OrderDetails orderDetails;
  private long ticketId;

  public Long getOrderId() {
    return orderId;
  }

  private CreateOrderSagaState() {
  }

  public CreateOrderSagaState(Long orderId, OrderDetails orderDetails) {
    this.orderId = orderId;
    this.orderDetails = orderDetails;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  public OrderDetails getOrderDetails() {
    return orderDetails;
  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }

  public void setTicketId(long ticketId) {
    this.ticketId = ticketId;
  }

  public long getTicketId() {
    return ticketId;
  }

  CreateTicket makeCreateTicketCommand() {
    return new CreateTicket(getOrderDetails().getRestaurantId(), getOrderId(), makeTicketDetails(getOrderDetails()));
  }

  private TicketDetails makeTicketDetails(OrderDetails orderDetails) {
    // TODO FIXME
    return new TicketDetails(makeTicketLineItems(orderDetails.getLineItems()));
  }

  private List<TicketLineItem> makeTicketLineItems(List<OrderLineItem> lineItems) {
    return lineItems.stream().map(this::makeTicketLineItem).collect(toList());
  }

  private TicketLineItem makeTicketLineItem(OrderLineItem orderLineItem) {
    return new TicketLineItem(orderLineItem.getMenuItemId(), orderLineItem.getName(), orderLineItem.getQuantity());
  }

  void handleCreateTicketReply(CreateTicketReply reply) {
    logger.debug("getTicketId {}", reply.getTicketId());
    setTicketId(reply.getTicketId());
  }

  CancelCreateTicket makeCancelCreateTicketCommand() {
    return new CancelCreateTicket(getOrderId());
  }

  RejectOrderCommand makeRejectOrderCommand() {
    return new RejectOrderCommand(getOrderId());
  }

  ValidateOrderByConsumer makeValidateOrderByConsumerCommand() {
    ValidateOrderByConsumer x = new ValidateOrderByConsumer();
    x.setConsumerId(getOrderDetails().getConsumerId());
    x.setOrderId(getOrderId());
    x.setOrderTotal(getOrderDetails().getOrderTotal().asString());
    return x;
  }

  AuthorizeCommand makeAuthorizeCommand() {
    return new AuthorizeCommand().withConsumerId(getOrderDetails().getConsumerId()).withOrderId(getOrderId()).withOrderTotal(getOrderDetails().getOrderTotal().asString());
  }

  ApproveOrderCommand makeApproveOrderCommand() {
    return new ApproveOrderCommand(getOrderId());
  }

  ConfirmCreateTicket makeConfirmCreateTicketCommand() {
    return new ConfirmCreateTicket(getTicketId());

  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagas/createorder/CreateOrderSagaState.java:CreateOrderSagaState.<init>
package net.chrisrichardson.ftgo.orderservice.sagas.createorder;

import io.eventuate.tram.sagas.orchestration.SagaDefinition;
import io.eventuate.tram.sagas.simpledsl.SimpleSaga;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.*;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicketReply;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CreateOrderSaga implements SimpleSaga<CreateOrderSagaState> {


  private Logger logger = LoggerFactory.getLogger(getClass());

  private SagaDefinition<CreateOrderSagaState> sagaDefinition;

  public CreateOrderSaga(OrderServiceProxy orderService, ConsumerServiceProxy consumerService, KitchenServiceProxy kitchenService,
                         AccountingServiceProxy accountingService) {
    this.sagaDefinition =
             step()
              .withCompensation(orderService.reject, CreateOrderSagaState::makeRejectOrderCommand)
            .step()
              .invokeParticipant(consumerService.validateOrder, CreateOrderSagaState::makeValidateOrderByConsumerCommand)
            .step()
              .invokeParticipant(kitchenService.create, CreateOrderSagaState::makeCreateTicketCommand)
              .onReply(CreateTicketReply.class, CreateOrderSagaState::handleCreateTicketReply)
              .withCompensation(kitchenService.cancel, CreateOrderSagaState::makeCancelCreateTicketCommand)
            .step()
                .invokeParticipant(accountingService.authorize, CreateOrderSagaState::makeAuthorizeCommand)
            .step()
              .invokeParticipant(kitchenService.confirmCreate, CreateOrderSagaState::makeConfirmCreateTicketCommand)
            .step()
              .invokeParticipant(orderService.approve, CreateOrderSagaState::makeApproveOrderCommand)
            .build();

  }


  @Override
  public SagaDefinition<CreateOrderSagaState> getSagaDefinition() {
    return sagaDefinition;
  }


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagas/createorder/CreateOrderSaga.java:CreateOrderSaga.<init>
// Node: CreateOrderSaga
package net.chrisrichardson.ftgo.orderservice.sagas.cancelorder;

import io.eventuate.tram.commands.consumer.CommandWithDestination;
import io.eventuate.tram.sagas.orchestration.SagaDefinition;
import io.eventuate.tram.sagas.simpledsl.SimpleSaga;
import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.accountservice.api.ReverseAuthorizationCommand;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.BeginCancelCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ConfirmCancelOrderCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.UndoBeginCancelCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.BeginCancelTicketCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmCancelTicketCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.KitchenServiceChannels;
import net.chrisrichardson.ftgo.kitchenservice.api.UndoBeginCancelTicketCommand;
import org.springframework.util.Assert;

import javax.annotation.PostConstruct;

import static io.eventuate.tram.commands.consumer.CommandWithDestinationBuilder.send;

public class CancelOrderSaga implements SimpleSaga<CancelOrderSagaData> {



  private SagaDefinition<CancelOrderSagaData> sagaDefinition;


  @PostConstruct
  public void initializeSagaDefinition() {
    sagaDefinition = step()
            .invokeParticipant(this::beginCancel)
            .withCompensation(this::undoBeginCancel)
            .step()
            .invokeParticipant(this::beginCancelTicket)
            .withCompensation(this::undoBeginCancelTicket)
            .step()
            .invokeParticipant(this::reverseAuthorization)
            .step()
            .invokeParticipant(this::confirmTicketCancel)
            .step()
            .invokeParticipant(this::confirmOrderCancel)
            .build();

  }

  private CommandWithDestination confirmOrderCancel(CancelOrderSagaData data) {
    return send(new ConfirmCancelOrderCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination confirmTicketCancel(CancelOrderSagaData data) {
    return send(new ConfirmCancelTicketCommand(data.getRestaurantId(), data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination reverseAuthorization(CancelOrderSagaData data) {
    return send(new ReverseAuthorizationCommand(data.getConsumerId(), data.getOrderId(), data.getOrderTotal()))
            .to(AccountingServiceChannels.accountingServiceChannel)
            .build();

  }

  private CommandWithDestination undoBeginCancelTicket(CancelOrderSagaData data) {
    return send(new UndoBeginCancelTicketCommand(data.getRestaurantId(), data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination beginCancelTicket(CancelOrderSagaData data) {
    return send(new BeginCancelTicketCommand(data.getRestaurantId(), (long) data.getOrderId()))
            .to(KitchenServiceChannels.COMMAND_CHANNEL)
            .build();

  }

  private CommandWithDestination undoBeginCancel(CancelOrderSagaData data) {
    return send(new UndoBeginCancelCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();
  }

  private CommandWithDestination beginCancel(CancelOrderSagaData data) {
    return send(new BeginCancelCommand(data.getOrderId()))
            .to(OrderServiceChannels.COMMAND_CHANNEL)
            .build();
  }


  @Override
  public SagaDefinition<CancelOrderSagaData> getSagaDefinition() {
    Assert.notNull(sagaDefinition);
    return sagaDefinition;
  }



}


package net.chrisrichardson.ftgo.orderservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import io.microservices.canvas.extractor.spring.annotations.ServiceDescription;
import io.microservices.canvas.springmvc.MicroserviceCanvasWebConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.orderservice.grpc.GrpcConfiguration;
import net.chrisrichardson.ftgo.orderservice.messaging.OrderServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.orderservice.service.OrderCommandHandlersConfiguration;
import net.chrisrichardson.ftgo.orderservice.web.OrderWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({OrderWebConfiguration.class, OrderCommandHandlersConfiguration.class,  OrderServiceMessagingConfiguration.class,
        TramJdbcKafkaConfiguration.class, CommonSwaggerConfiguration.class, GrpcConfiguration.class,
        MicroserviceCanvasWebConfiguration.class})
@ServiceDescription(description="Manages Orders", capabilities = "Order Management")
public class OrderServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(OrderServiceMain.class, args);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/main/OrderServiceMain.java:OrderServiceMain.<init>
// Node: ServiceDescription
package net.chrisrichardson.ftgo.orderservice.service;

import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.sagas.participant.SagaCommandDispatcher;
import io.eventuate.tram.sagas.participant.SagaCommandDispatcherFactory;
import io.eventuate.tram.sagas.spring.participant.SagaParticipantConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import({SagaParticipantConfiguration.class, TramEventsPublisherConfiguration.class, CommonConfiguration.class, SagaParticipantConfiguration.class})
public class OrderCommandHandlersConfiguration {

  @Bean
  public OrderCommandHandlers orderCommandHandlers() {
    return new OrderCommandHandlers();
  }

  @Bean
  public SagaCommandDispatcher orderCommandHandlersDispatcher(OrderCommandHandlers orderCommandHandlers, SagaCommandDispatcherFactory sagaCommandDispatcherFactory) {
    return sagaCommandDispatcherFactory.make("orderService", orderCommandHandlers.commandHandlers());
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/service/OrderCommandHandlersConfiguration.java:OrderCommandHandlersConfiguration.<init>
package net.chrisrichardson.ftgo.orderservice.web;

import brave.sampler.Sampler;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.eventuate.common.json.mapper.JSonMapper;
import net.chrisrichardson.ftgo.orderservice.domain.OrderServiceWithRepositoriesConfiguration;
import org.springframework.context.annotation.*;

@Configuration
@ComponentScan
@Import(OrderServiceWithRepositoriesConfiguration.class)
public class OrderWebConfiguration {

  @Bean
  @Primary
  public ObjectMapper objectMapper() {
    return JSonMapper.objectMapper;
  }

  @Bean
  public Sampler defaultSampler() {
    return Sampler.ALWAYS_SAMPLE;
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/web/OrderWebConfiguration.java:OrderWebConfiguration.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

@Configuration
@EnableJpaRepositories
@EnableAutoConfiguration
@Import({OrderServiceConfiguration.class})
public class OrderServiceWithRepositoriesConfiguration {


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderServiceWithRepositoriesConfiguration.java:OrderServiceWithRepositoriesConfiguration.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.sagas.orchestration.*;
import io.eventuate.tram.sagas.spring.orchestration.SagaOrchestratorConfiguration;
import io.micrometer.core.instrument.MeterRegistry;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.AccountingServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ConsumerServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.KitchenServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.OrderServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagas.cancelorder.CancelOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.reviseorder.ReviseOrderSaga;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.actuate.autoconfigure.metrics.MeterRegistryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import java.util.Optional;

@Configuration
@Import({TramEventsPublisherConfiguration.class, SagaOrchestratorConfiguration.class, CommonConfiguration.class})
public class OrderServiceConfiguration {

  @Bean
  public OrderService orderService(SagaInstanceFactory sagaInstanceFactory,
                                   RestaurantRepository restaurantRepository,
                                   OrderRepository orderRepository,
                                   DomainEventPublisher eventPublisher,
                                   CreateOrderSaga createOrderSaga,
                                   CancelOrderSaga cancelOrderSaga,
                                   ReviseOrderSaga reviseOrderSaga,
                                   OrderDomainEventPublisher orderAggregateEventPublisher,
                                   Optional<MeterRegistry> meterRegistry) {

    return new OrderService(sagaInstanceFactory, orderRepository, eventPublisher, restaurantRepository,
            createOrderSaga, cancelOrderSaga, reviseOrderSaga, orderAggregateEventPublisher, meterRegistry);
  }

  @Bean
  public CreateOrderSaga createOrderSaga(OrderServiceProxy orderService, ConsumerServiceProxy consumerService, KitchenServiceProxy kitchenServiceProxy, AccountingServiceProxy accountingService) {
    return new CreateOrderSaga(orderService, consumerService, kitchenServiceProxy, accountingService);
  }

  @Bean
  public CancelOrderSaga cancelOrderSaga() {
    return new CancelOrderSaga();
  }

  @Bean
  public ReviseOrderSaga reviseOrderSaga() {
    return new ReviseOrderSaga();
  }


  @Bean
  public KitchenServiceProxy kitchenServiceProxy() {
    return new KitchenServiceProxy();
  }

  @Bean
  public OrderServiceProxy orderServiceProxy() {
    return new OrderServiceProxy();
  }

  @Bean
  public ConsumerServiceProxy consumerServiceProxy() {
    return new ConsumerServiceProxy();
  }

  @Bean
  public AccountingServiceProxy accountingServiceProxy() {
    return new AccountingServiceProxy();
  }

  @Bean
  public OrderDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
    return new OrderDomainEventPublisher(eventPublisher);
  }

  @Bean
  public MeterRegistryCustomizer meterRegistryCustomizer(@Value("${spring.application.name}") String serviceName) {
    return registry -> registry.config().commonTags("service", serviceName);
  }
}


// Node: createOrderSaga
package net.chrisrichardson.ftgo.orderservice.messaging;

import io.eventuate.tram.spring.events.subscriber.TramEventSubscriberConfiguration;
import io.eventuate.tram.events.subscriber.DomainEventDispatcher;
import io.eventuate.tram.events.subscriber.DomainEventDispatcherFactory;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.orderservice.domain.OrderServiceWithRepositoriesConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import({OrderServiceWithRepositoriesConfiguration.class, TramEventSubscriberConfiguration.class})
public class OrderServiceMessagingConfiguration {

  @Bean
  public OrderEventConsumer orderEventConsumer(OrderService orderService) {
    return new OrderEventConsumer(orderService);
  }

  @Bean
  public DomainEventDispatcher domainEventDispatcher(OrderEventConsumer orderEventConsumer, DomainEventDispatcherFactory domainEventDispatcherFactory) {
    return domainEventDispatcherFactory.make("orderServiceEvents", orderEventConsumer.domainEventHandlers());
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/messaging/OrderServiceMessagingConfiguration.java:OrderServiceMessagingConfiguration.<init>
package net.chrisrichardson.ftgo.orderservice.sagas.createorder;

import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.consumerservice.api.ConsumerServiceChannels;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.kitchenservice.api.CancelCreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmCreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.KitchenServiceChannels;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.*;
import org.jetbrains.annotations.NotNull;
import org.junit.BeforeClass;
import org.junit.Test;

import static io.eventuate.tram.sagas.testing.SagaUnitTestSupport.given;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.*;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_ID;

public class CreateOrderSagaTest {

  private OrderServiceProxy orderServiceProxy = new OrderServiceProxy();
  private KitchenServiceProxy kitchenServiceProxy = new KitchenServiceProxy();
  private ConsumerServiceProxy consumerServiceProxy = new ConsumerServiceProxy();
  private AccountingServiceProxy accountingServiceProxy = new AccountingServiceProxy();

  @BeforeClass
  public static void initialize() {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  private CreateOrderSaga makeCreateOrderSaga() {
    return new CreateOrderSaga(orderServiceProxy, consumerServiceProxy, kitchenServiceProxy, accountingServiceProxy);
  }

  @Test
  public void shouldCreateOrder() {
    given()
        .saga(makeCreateOrderSaga(),
                new CreateOrderSagaState(ORDER_ID, CHICKEN_VINDALOO_ORDER_DETAILS)).
    expect().
        command(makeValidateOrderByConsumer()).
        to(ConsumerServiceChannels.consumerServiceChannel).
    andGiven().
        successReply().
    expect().
      command(new CreateTicket(AJANTA_ID, ORDER_ID, null /* FIXME */)).
      to(KitchenServiceChannels.COMMAND_CHANNEL).
    andGiven().
        successReply().
    expect().
      command(new AuthorizeCommand().withConsumerId(CONSUMER_ID).withOrderId(ORDER_ID).withOrderTotal(CHICKEN_VINDALOO_ORDER_TOTAL.asString())).
      to(AccountingServiceChannels.accountingServiceChannel).
    andGiven().
        successReply().
    expect().
      command(new ConfirmCreateTicket(ORDER_ID)).
      to(KitchenServiceChannels.COMMAND_CHANNEL).
    andGiven().
        successReply().
    expect().
      command(new ApproveOrderCommand(ORDER_ID)).
      to(OrderServiceChannels.COMMAND_CHANNEL)
            ;
  }

  @NotNull
  private ValidateOrderByConsumer makeValidateOrderByConsumer() {
    return new ValidateOrderByConsumer().withConsumerId(CONSUMER_ID).withOrderId(ORDER_ID).withOrderTotal(CHICKEN_VINDALOO_ORDER_TOTAL.asString());
  }

  @Test
  public void shouldRejectOrderDueToConsumerVerificationFailed() {
    given()
        .saga(makeCreateOrderSaga(),
                new CreateOrderSagaState(ORDER_ID, CHICKEN_VINDALOO_ORDER_DETAILS)).
    expect().
        command(makeValidateOrderByConsumer()).
        to(ConsumerServiceChannels.consumerServiceChannel).
    andGiven().
        failureReply().
    expect().
        command(new RejectOrderCommand(ORDER_ID)).
        to(OrderServiceChannels.COMMAND_CHANNEL);
  }

  @Test
  public void shouldRejectDueToFailedAuthorizxation() {
    given()
            .saga(makeCreateOrderSaga(),
                    new CreateOrderSagaState(ORDER_ID, CHICKEN_VINDALOO_ORDER_DETAILS)).
    expect().
      command(makeValidateOrderByConsumer()).
      to(ConsumerServiceChannels.consumerServiceChannel).
    andGiven().
      successReply().
    expect().
      command(new CreateTicket(AJANTA_ID, ORDER_ID, null /* FIXME */)).
      to(KitchenServiceChannels.COMMAND_CHANNEL).
    andGiven().
      successReply().
    expect().
      command(new AuthorizeCommand().withConsumerId(CONSUMER_ID).withOrderId(ORDER_ID).withOrderTotal(CHICKEN_VINDALOO_ORDER_TOTAL.asString())).
      to(AccountingServiceChannels.accountingServiceChannel).
    andGiven().
      failureReply().
    expect().
      command(new CancelCreateTicket(ORDER_ID)).
      to(KitchenServiceChannels.COMMAND_CHANNEL).
    andGiven().
      successReply().
    expect().
      command(new RejectOrderCommand(ORDER_ID)).
      to(OrderServiceChannels.COMMAND_CHANNEL)
    ;
  }
}

package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.messaging.common.Message;
import io.eventuate.tram.messaging.consumer.MessageConsumer;
import io.eventuate.util.test.async.Eventually;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;

import javax.annotation.PostConstruct;
import java.util.Collections;
import java.util.concurrent.LinkedBlockingDeque;
import java.util.concurrent.TimeUnit;
import java.util.function.Predicate;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

public class TestMessageConsumer2 {

  private Logger logger = LoggerFactory.getLogger(getClass());
  private LinkedBlockingDeque<Message> messages = new LinkedBlockingDeque<>();

  private String subscriberId;
  private String channel;

  @Autowired
  private MessageConsumer messageConsumer;

  public TestMessageConsumer2(String subscriberId, String channel) {
    this.subscriberId = subscriberId;
    this.channel = channel;
  }

  @PostConstruct
  public void subscribe() {
    messageConsumer.subscribe(subscriberId, Collections.singleton(channel), this::handle);
  }

  private void handle(Message message) {
    logger.debug("Got message: {}", message);
    messages.add(message);
  }

  public Message assertMessageReceived() {
    return assertMessageReceived((m) -> true);
  }
  
  public Message assertMessageReceived(Predicate<Message> predicate) {
    return Eventually.eventuallyReturning(() -> {
      Message m = null;
      try {
        m = messages.pollFirst(1, TimeUnit.MILLISECONDS);
      } catch (InterruptedException e) {
        throw new RuntimeException(e);
      }
      assertNotNull(m);
      System.out.println("Testing message: " + m);
      assertTrue("Failed predicate", predicate.test(m));
      return m;
    });
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/test/java/net/chrisrichardson/ftgo/orderservice/domain/TestMessageConsumer2.java:TestMessageConsumer2.<init>
package net.chrisrichardson.ftgo.orderservice;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import org.junit.runner.RunWith;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderServiceExternalComponentTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.NONE)
@TestPropertySource(properties = "debug=true")
public class OrderServiceExternalComponentTest extends AbstractOrderServiceComponentTest {


  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }
  
  private int port = 8082;
  private String host = FtgoTestUtil.getDockerHostIp();

  @Override
  protected String baseUrl(String path) {
    return String.format("http://%s:%s%s", host, port, path);
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({CommonMessagingStubConfiguration.class,
          TramCommandProducerConfiguration.class, TramEventsPublisherConfiguration.class,
          TramJdbcKafkaConfiguration.class})
  public static class TestConfiguration {
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/attic/OrderServiceExternalComponentTest.java:OrderServiceExternalComponentTest.<init>
// Node: TestPropertySource
package net.chrisrichardson.ftgo.orderservice;

import io.eventuate.tram.commands.common.ChannelMapping;
import io.eventuate.tram.commands.common.DefaultChannelMapping;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.util.test.async.Eventually;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.domain.OrderRepository;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.orderservice.domain.RestaurantRepository;
import net.chrisrichardson.ftgo.orderservice.messaging.OrderServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.orderservice.service.OrderCommandHandlersConfiguration;
import net.chrisrichardson.ftgo.orderservice.web.OrderWebConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.stubrunner.BatchStubRunner;
import org.springframework.cloud.contract.stubrunner.spring.AutoConfigureStubRunner;
import org.springframework.cloud.contract.verifier.messaging.MessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.junit4.SpringRunner;

import javax.sql.DataSource;
import java.util.Collections;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

@RunWith(SpringRunner.class)
@SpringBootTest(classes= OrderServiceOutOfProcessComponentV0Test.TestConfiguration.class,
        webEnvironment= SpringBootTest.WebEnvironment.RANDOM_PORT,
      properties = "customer.service.url=http://localhost:8888/customers/{customerId}")
@AutoConfigureStubRunner(ids =
        {"net.chrisrichardson.ftgo:ftgo-accounting-service-contracts", "net.chrisrichardson.ftgo:ftgo-consumer-service-contracts",
                "net.chrisrichardson.ftgo:ftgo-kitchen-service-contracts"}
        )
@DirtiesContext
public class OrderServiceOutOfProcessComponentV0Test {

  @Configuration
  @EnableAutoConfiguration
  @Import({OrderWebConfiguration.class, OrderServiceMessagingConfiguration.class,  OrderCommandHandlersConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramInMemoryConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public ChannelMapping channelMapping() {
      return new DefaultChannelMapping.DefaultChannelMappingBuilder().build();
    }


    @Bean
    public DataSource dataSource() {
      EmbeddedDatabaseBuilder builder = new EmbeddedDatabaseBuilder();
      return builder.setType(EmbeddedDatabaseType.H2)
              .addScript("eventuate-tram-embedded-schema.sql")
              .addScript("eventuate-tram-sagas-embedded.sql")
              .build();
    }


    @Bean
    public EventuateTramRoutesConfigurer eventuateTramRoutesConfigurer(BatchStubRunner batchStubRunner) {
      return new EventuateTramRoutesConfigurer(batchStubRunner);
    }
  }

  @Value("${local.server.port}")
  private int port;

  private String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Autowired
  private MessageVerifier verifier;

  @Autowired
  private DomainEventPublisher domainEventPublisher;

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private OrderService orderService;

  @Autowired
  private OrderRepository orderRepository;


  @Test
  public void shouldCreateOrder() throws InterruptedException {
    domainEventPublisher.publish("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant", RestaurantMother.AJANTA_ID,
            Collections.singletonList(RestaurantMother.makeAjantaRestaurantCreatedEvent()));

    Eventually.eventually(() -> {
      FtgoTestUtil.assertPresent(restaurantRepository.findById(RestaurantMother.AJANTA_ID));
    });


    Order order = orderService.createOrder(OrderDetailsMother.CONSUMER_ID,
            RestaurantMother.AJANTA_ID,
            Collections.singletonList(OrderDetailsMother.CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY));


    Eventually.eventually(() -> {
      Order o = orderRepository.findById(order.getId());
      assertNotNull(o);
      assertEquals(OrderState.AUTHORIZED, o.getState());
    });
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/attic/OrderServiceOutOfProcessComponentV0Test.java:OrderServiceOutOfProcessComponentV0Test.<init>
package net.chrisrichardson.ftgo.orderservice;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringRunner;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderServiceOutOfProcessComponentTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@TestPropertySource(properties = "debug=true")
public class OrderServiceOutOfProcessComponentTest extends AbstractOrderServiceComponentTest {


  @Value("${local.server.port}")
  private int port;

  @Override
  protected String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({CommonTestConfiguration.class, TramJdbcKafkaConfiguration.class})
  public static class TestConfiguration {
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/attic/OrderServiceOutOfProcessComponentTest.java:OrderServiceOutOfProcessComponentTest.<init>
package net.chrisrichardson.ftgo.orderservice;

import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder;
import org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType;
import org.springframework.test.context.junit4.SpringRunner;

import javax.sql.DataSource;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderServiceInProcessComponentTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class OrderServiceInProcessComponentTest extends AbstractOrderServiceComponentTest {


  @Value("${local.server.port}")
  private int port;

  @Override
  protected String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({CommonTestConfiguration.class, TramInMemoryConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public DataSource dataSource() {
      EmbeddedDatabaseBuilder builder = new EmbeddedDatabaseBuilder();
      return builder.setType(EmbeddedDatabaseType.H2)
              .addScript("eventuate-tram-embedded-schema.sql")
              .addScript("eventuate-tram-sagas-embedded.sql")
              .build();
    }


  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/attic/OrderServiceInProcessComponentTest.java:OrderServiceInProcessComponentTest.<init>
package net.chrisrichardson.ftgo.deliveryservice;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryServiceTestData;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.restaurantservice.RestaurantServiceChannels;
import net.chrisrichardson.ftgo.testutil.FtgoTestUtil;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.concurrent.TimeUnit;

import static com.jayway.restassured.RestAssured.given;
import static io.eventuate.util.test.async.Eventually.eventually;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryServiceOutOfProcessComponentTest.Config.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
public class DeliveryServiceOutOfProcessComponentTest {

  @Configuration
  @EnableJpaRepositories
  @EnableAutoConfiguration
  @Import({TramJdbcKafkaConfiguration.class, TramEventsPublisherConfiguration.class
  })
  public static class Config {
  }

  private String host = FtgoTestUtil.getDockerHostIp();
  private int port = 8089;
  private long restaurantId;
  private long orderId;

  @Autowired
  private DomainEventPublisher domainEventPublisher;

  // Duplication

  private String baseUrl(int port, String path, String... pathElements) {
    assertNotNull("host", host);

    StringBuilder sb = new StringBuilder("http://");
    sb.append(host);
    sb.append(":");
    sb.append(port);
    sb.append("/");
    sb.append(path);

    for (String pe : pathElements) {
      sb.append("/");
      sb.append(pe);
    }
    String s = sb.toString();
    System.out.println("url=" + s);
    return s;
  }

  @Test
  public void shouldScheduleDelivery() {

    createRestaurant();

    createOrder();

    assertDeliveryCreated();

    // createCourier
    // acceptTicket
    // TicketCancelled
  }

  private void assertDeliveryCreated() {

    eventually(() -> {
      String state = given().
              when().
              get(baseUrl(port, "deliveries", Long.toString(orderId))).
              then().
              statusCode(200).extract().path("deliveryInfo.state");

      assertEquals("PENDING", state);
    });
  }

  private void createOrder() {
    orderId = System.currentTimeMillis();
    domainEventPublisher.publish(OrderServiceChannels.ORDER_EVENT_CHANNEL, orderId, Collections.singletonList(
            new OrderCreatedEvent(new OrderDetails(0L, restaurantId, null, null),
                    DeliveryServiceTestData.DELIVERY_ADDRESS, null)));


  }

  private void createRestaurant() {
    restaurantId = System.currentTimeMillis();

    domainEventPublisher.publish(RestaurantServiceChannels.RESTAURANT_EVENT_CHANNEL, restaurantId, Collections.singletonList(RestaurantEventMother.makeRestaurantCreated()));

    sleep();
  }

  private void sleep() {
    try {
      TimeUnit.SECONDS.sleep(5);
    } catch (InterruptedException e) {
      throw new RuntimeException(e);
    }
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/component-test/java/net/chrisrichardson/ftgo/deliveryservice/DeliveryServiceOutOfProcessComponentTest.java:DeliveryServiceOutOfProcessComponentTest.<init>
package net.chrisrichardson.ftgo.deliveryservice;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryRepository;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryServiceTestData;
import net.chrisrichardson.ftgo.deliveryservice.domain.RestaurantRepository;
import net.chrisrichardson.ftgo.deliveryservice.messaging.DeliveryServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.web.DeliveryServiceWebConfiguration;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.restaurantservice.RestaurantServiceChannels;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.web.server.LocalServerPort;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static com.jayway.restassured.RestAssured.given;
import static io.eventuate.util.test.async.Eventually.eventually;
import static org.junit.Assert.*;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryServiceInProcessComponentTest.Config.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class DeliveryServiceInProcessComponentTest {

  private long restaurantId;
  private long orderId;

  @Configuration
  @EnableAutoConfiguration
  @Import({DeliveryServiceMessagingConfiguration.class,
          DeliveryServiceWebConfiguration.class,
          TramInMemoryConfiguration.class,
          TramEventsPublisherConfiguration.class,
          EventuateTransactionTemplateConfiguration.class
  })
  public static class Config {
  }

  @LocalServerPort
  private int port;

  private String host = "localhost";

  @Autowired
  private DomainEventPublisher domainEventPublisher;

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private DeliveryRepository deliveryRepository;

  @Test
  public void shouldScheduleDelivery() {

    createRestaurant();

    createOrder();

    assertDeliveryCreated();

    // createCourier
    // acceptTicket
    // TicketCancelled
  }

  private String baseUrl(int port, String path, String... pathElements) {
    assertNotNull("host", host);

    StringBuilder sb = new StringBuilder("http://");
    sb.append(host);
    sb.append(":");
    sb.append(port);
    sb.append("/");
    sb.append(path);

    for (String pe : pathElements) {
      sb.append("/");
      sb.append(pe);
    }
    String s = sb.toString();
    System.out.println("url=" + s);
    return s;
  }


  private void assertDeliveryCreated() {

    String state = given().
            when().
            get(baseUrl(port, "deliveries", Long.toString(orderId))).
            then().
            statusCode(200).extract().path("deliveryInfo.state");

    assertEquals("PENDING", state);
  }

  private void createOrder() {
    orderId = System.currentTimeMillis();
    domainEventPublisher.publish(OrderServiceChannels.ORDER_EVENT_CHANNEL, orderId, Collections.singletonList(
            new OrderCreatedEvent(new OrderDetails(0L, restaurantId, null, null),
                    DeliveryServiceTestData.DELIVERY_ADDRESS, null)));
    eventually(() -> assertTrue(deliveryRepository.findById(orderId).isPresent()));


  }

  private void createRestaurant() {
    restaurantId = System.currentTimeMillis();

    domainEventPublisher.publish(RestaurantServiceChannels.RESTAURANT_EVENT_CHANNEL, restaurantId,
            Collections.singletonList(RestaurantEventMother.makeRestaurantCreated()));

    eventually(() -> assertTrue(restaurantRepository.findById(restaurantId).isPresent()));
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/component-test/java/net/chrisrichardson/ftgo/deliveryservice/DeliveryServiceInProcessComponentTest.java:DeliveryServiceInProcessComponentTest.<init>
package net.chrisrichardson.ftgo.deliveryservice.domain;

import io.eventuate.tram.spring.consumer.jdbc.TramConsumerJdbcAutoConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.junit4.SpringRunner;

import static org.junit.Assert.assertNull;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryJpaTest.Config.class)
public class DeliveryJpaTest {

  @Configuration
  @EnableJpaRepositories
  @EnableAutoConfiguration(exclude = TramConsumerJdbcAutoConfiguration.class)
  public static class Config {
  }

  @Autowired
  private DeliveryRepository deliveryRepository;

  @Test
  public void shouldSaveAndLoadDelivery() {
    long restaurantId = 102L;
    long orderId = System.currentTimeMillis();
    Delivery delivery = Delivery.create(orderId,
            restaurantId, DeliveryServiceTestData.PICKUP_ADDRESS, DeliveryServiceTestData.PICKUP_ADDRESS );
    Delivery savedDelivery = deliveryRepository.save(delivery);

    Delivery loadedDelivery = deliveryRepository.findById(orderId).get();
    assertNull(loadedDelivery.getAssignedCourier());
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/integration-test/java/net/chrisrichardson/ftgo/deliveryservice/domain/DeliveryJpaTest.java:DeliveryJpaTest.<init>
package net.chrisrichardson.ftgo.deliveryservice.domain;

import io.eventuate.tram.spring.consumer.jdbc.TramConsumerJdbcAutoConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.LocalDateTime;
import java.util.List;

import static org.junit.Assert.*;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = CourierJpaTest.Config.class)
public class CourierJpaTest {

  @Configuration
  @EnableJpaRepositories
  @EnableAutoConfiguration(exclude = TramConsumerJdbcAutoConfiguration.class)
  public static class Config {
  }

  @Autowired
  private CourierRepository courierRepository;


  @Autowired
  private TransactionTemplate transactionTemplate;

  @Test
  public void shouldSaveAndLoad() {
    long courierId = System.currentTimeMillis();
    Courier courier = Courier.create(courierId);
    long deliveryId = 103L;
    courier.addAction(Action.makePickup(deliveryId, DeliveryServiceTestData.PICKUP_ADDRESS, LocalDateTime.now()));

    Courier savedCourier = courierRepository.save(courier);

    transactionTemplate.execute((ts) -> {
      Courier loadedCourier = courierRepository.findById(courierId).get();
      assertEquals(1, loadedCourier.getPlan().getActions().size());
      return null;
    });
  }

  @Test
  public void shouldFindAllAvailable() {
    long courierId1 = System.currentTimeMillis() * 10;
    long courierId2 = System.currentTimeMillis() * 10 + 1;
    Courier courier1 = Courier.create(courierId1);
    Courier courier2 = Courier.create(courierId2);

    courier1.noteAvailable();
    courier2.noteUnavailable();

    courierRepository.save(courier1);
    courierRepository.save(courier2);

    List<Courier> availableCouriers = courierRepository.findAllAvailable();

    assertTrue(availableCouriers.stream().anyMatch(c -> c.getId() == courierId1));
    assertFalse(availableCouriers.stream().anyMatch(c -> c.getId() == courierId2));
  }

  @Test
  public void shouldFindOrCreate() {
    long courierId = System.currentTimeMillis();
    transactionTemplate.execute((ts) -> {
      Courier courier = courierRepository.findOrCreateCourier(courierId);
      assertNotNull(courier);
      return null;
    });
    transactionTemplate.execute((ts) -> {
      Courier courier2 = courierRepository.findOrCreateCourier(courierId);
      assertNotNull(courier2);
      return null;
    });
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/integration-test/java/net/chrisrichardson/ftgo/deliveryservice/domain/CourierJpaTest.java:CourierJpaTest.<init>
package net.chrisrichardson.ftgo.deliveryservice.domain;

import io.eventuate.tram.spring.consumer.jdbc.TramConsumerJdbcAutoConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.transaction.support.TransactionTemplate;

import static org.junit.Assert.assertEquals;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = RestaurantJpaTest.Config.class)
public class RestaurantJpaTest {

  @Configuration
  @EnableJpaRepositories
  @EnableAutoConfiguration(exclude = TramConsumerJdbcAutoConfiguration.class)
  public static class Config {
  }


  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private TransactionTemplate transactionTemplate;

  @Test
  public void shouldSaveAndLoad() {
    long restaurantId = System.currentTimeMillis();
    Restaurant restaurant = Restaurant.create(restaurantId, "Delicious Indian", DeliveryServiceTestData.PICKUP_ADDRESS);
    restaurantRepository.save(restaurant);

    transactionTemplate.execute((ts) -> {
      Restaurant loadedCourier = restaurantRepository.findById(restaurantId).get();
      assertEquals(DeliveryServiceTestData.PICKUP_ADDRESS, loadedCourier.getAddress());
      return null;
    });

  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/integration-test/java/net/chrisrichardson/ftgo/deliveryservice/domain/RestaurantJpaTest.java:RestaurantJpaTest.<init>
package net.chrisrichardson.ftgo.deliveryservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.messaging.DeliveryServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.web.DeliveryServiceWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@EnableAutoConfiguration
@Import({DeliveryServiceMessagingConfiguration.class, DeliveryServiceWebConfiguration.class,
        TramJdbcKafkaConfiguration.class, CommonSwaggerConfiguration.class
})
public class DeliveryServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(DeliveryServiceMain.class, args);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/main/DeliveryServiceMain.java:DeliveryServiceMain.<init>
package net.chrisrichardson.ftgo.deliveryservice.web;

import net.chrisrichardson.ftgo.common.CommonConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryServiceDomainConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@ComponentScan
@Import({DeliveryServiceDomainConfiguration.class, CommonConfiguration.class})
public class DeliveryServiceWebConfiguration {
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/web/DeliveryServiceWebConfiguration.java:DeliveryServiceWebConfiguration.<init>
package net.chrisrichardson.ftgo.deliveryservice.messaging;

import io.eventuate.tram.spring.events.subscriber.TramEventSubscriberConfiguration;
import io.eventuate.tram.events.subscriber.DomainEventDispatcher;
import io.eventuate.tram.events.subscriber.DomainEventDispatcherFactory;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryService;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryServiceDomainConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import({DeliveryServiceDomainConfiguration.class, TramEventSubscriberConfiguration.class, CommonConfiguration.class})
public class DeliveryServiceMessagingConfiguration {

  @Bean
  public DeliveryMessageHandlers deliveryMessageHandlers(DeliveryService deliveryService) {
    return new DeliveryMessageHandlers(deliveryService);
  }

  @Bean
  public DomainEventDispatcher domainEventDispatcher(DeliveryMessageHandlers deliveryMessageHandlers, DomainEventDispatcherFactory domainEventDispatcherFactory) {
    return domainEventDispatcherFactory.make("deliveryService-deliveryMessageHandlers", deliveryMessageHandlers.domainEventHandlers());
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/messaging/DeliveryServiceMessagingConfiguration.java:DeliveryServiceMessagingConfiguration.<init>
package net.chrisrichardson.ftgo.kitchenservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketAcceptedEvent;
import net.chrisrichardson.ftgo.kitchenservice.domain.Ticket;
import net.chrisrichardson.ftgo.kitchenservice.domain.TicketDomainEventPublisher;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.time.LocalDateTime;
import java.util.Collections;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryserviceMessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class DeliveryserviceMessagingBase {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public TicketDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new TicketDomainEventPublisher(eventPublisher);
    }
  }


  @Autowired
  private TicketDomainEventPublisher ticketDomainEventPublisher;

  protected void ticketAcceptedEvent() {
    Ticket ticket = new Ticket(101L, 99L, new TicketDetails(Collections.emptyList()));
    ticketDomainEventPublisher.publish(ticket,
            Collections.singletonList(new TicketAcceptedEvent(LocalDateTime.now())));
  }

}



// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/integration-test/java/net/chrisrichardson/ftgo/kitchenservice/contract/DeliveryserviceMessagingBase.java:DeliveryserviceMessagingBase.<init>
package net.chrisrichardson.ftgo.kitchenservice.contract;

import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.domain.KitchenService;
import net.chrisrichardson.ftgo.kitchenservice.domain.Ticket;
import net.chrisrichardson.ftgo.kitchenservice.messagehandlers.KitchenServiceMessageHandlersConfiguration;
import org.junit.Before;
import org.junit.runner.RunWith;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static org.mockito.Matchers.any;
import static org.mockito.Matchers.eq;
import static org.mockito.Mockito.reset;
import static org.mockito.Mockito.when;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = MessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class MessagingBase {

  @Configuration
  @EnableAutoConfiguration
  @Import({KitchenServiceMessageHandlersConfiguration.class, EventuateContractVerifierConfiguration.class})
  public static class TestConfiguration {

  }

  @MockBean
  private KitchenService kitchenService;

  @Before
  public void setup() {
     reset(kitchenService);
     when(kitchenService.createTicket(eq(1L), eq(99L), any(TicketDetails.class)))
             .thenReturn(new Ticket(1L, 99L, new TicketDetails(Collections.emptyList())));
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/integration-test/java/net/chrisrichardson/ftgo/kitchenservice/contract/MessagingBase.java:MessagingBase.<init>
package net.chrisrichardson.ftgo.kitchenservice.messagehandlers;

import io.eventuate.tram.spring.events.subscriber.TramEventSubscriberConfiguration;
import io.eventuate.tram.events.subscriber.DomainEventDispatcher;
import io.eventuate.tram.events.subscriber.DomainEventDispatcherFactory;
import io.eventuate.tram.sagas.participant.SagaCommandDispatcher;
import io.eventuate.tram.sagas.participant.SagaCommandDispatcherFactory;
import io.eventuate.tram.sagas.spring.participant.SagaParticipantConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.domain.KitchenDomainConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import({KitchenDomainConfiguration.class, SagaParticipantConfiguration.class, CommonConfiguration.class, TramEventSubscriberConfiguration.class, SagaParticipantConfiguration.class})
public class KitchenServiceMessageHandlersConfiguration {

  @Bean
  public KitchenServiceEventConsumer ticketEventConsumer() {
    return new KitchenServiceEventConsumer();
  }

  @Bean
  public KitchenServiceCommandHandler kitchenServiceCommandHandler() {
    return new KitchenServiceCommandHandler();
  }

  @Bean
  public SagaCommandDispatcher kitchenServiceSagaCommandDispatcher(KitchenServiceCommandHandler kitchenServiceCommandHandler, SagaCommandDispatcherFactory sagaCommandDispatcherFactory) {
    return sagaCommandDispatcherFactory.make("kitchenServiceCommands", kitchenServiceCommandHandler.commandHandlers());
  }

  @Bean
  public DomainEventDispatcher domainEventDispatcher(KitchenServiceEventConsumer kitchenServiceEventConsumer, DomainEventDispatcherFactory domainEventDispatcherFactory) {
    return domainEventDispatcherFactory.make("kitchenServiceEvents", kitchenServiceEventConsumer.domainEventHandlers());
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/messagehandlers/KitchenServiceMessageHandlersConfiguration.java:KitchenServiceMessageHandlersConfiguration.<init>
package net.chrisrichardson.ftgo.kitchenservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.messagehandlers.KitchenServiceMessageHandlersConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.web.KitchenServiceWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({KitchenServiceWebConfiguration.class,
        KitchenServiceMessageHandlersConfiguration.class,
        TramJdbcKafkaConfiguration.class,
        CommonSwaggerConfiguration.class})
public class KitchenServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(KitchenServiceMain.class, args);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/main/KitchenServiceMain.java:KitchenServiceMain.<init>
package net.chrisrichardson.ftgo.kitchenservice.web;

import net.chrisrichardson.ftgo.kitchenservice.domain.KitchenDomainConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@Import(KitchenDomainConfiguration.class)
@ComponentScan
public class KitchenServiceWebConfiguration {


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/web/KitchenServiceWebConfiguration.java:KitchenServiceWebConfiguration.<init>
package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableTransactionManagement
@EnableJpaRepositories
@ComponentScan
@EntityScan
@Import({TramEventsPublisherConfiguration.class, CommonConfiguration.class})
public class KitchenDomainConfiguration {

  @Bean
  public KitchenService kitchenService() {
    return new KitchenService();
  }

  @Bean
  public TicketDomainEventPublisher restaurantAggregateEventPublisher(DomainEventPublisher domainEventPublisher) {
    return new TicketDomainEventPublisher(domainEventPublisher);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/KitchenDomainConfiguration.java:KitchenDomainConfiguration.<init>
package net.chrisrichardson.ftgo.kitchenservice.domain;


import io.eventuate.tram.commands.producer.CommandProducer;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.sagas.common.SagaCommandHeaders;
import io.eventuate.tram.sagas.spring.inmemory.TramSagaInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumer;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.messagehandlers.KitchenServiceMessageHandlersConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.web.KitchenServiceWebConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = KitchenServiceInMemoryIntegrationTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class KitchenServiceInMemoryIntegrationTest {

  private Logger logger = LoggerFactory.getLogger(getClass());

  @Value("${local.server.port}")
  private int port;

  @Configuration
  @EnableAutoConfiguration
  @Import({KitchenServiceWebConfiguration.class, KitchenServiceMessageHandlersConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramSagaInMemoryConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }


  }

  private String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Autowired
  private CommandProducer commandProducer;

  @Autowired
  private TestMessageConsumerFactory testMessageConsumerFactory;

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Test
  public void shouldCreateTicket() {

    long restaurantId = System.currentTimeMillis();
    Restaurant restaurant = new Restaurant(restaurantId, Collections.emptyList());

    restaurantRepository.save(restaurant);

    TestMessageConsumer testMessageConsumer = testMessageConsumerFactory.make();

    long orderId = 999;
    Money orderTotal = new Money(123);

    TicketDetails orderDetails = new TicketDetails();
    String messageId = commandProducer.send("kitchenService", null,
            new CreateTicket(restaurantId, orderId, orderDetails),
            testMessageConsumer.getReplyChannel(), withSagaCommandHeaders());

    testMessageConsumer.assertHasReplyTo(messageId);

  }

  private Map<String, String> withSagaCommandHeaders() {
    Map<String, String> result = new HashMap<>();
    result.put(SagaCommandHeaders.SAGA_TYPE, "MySagaType");
    result.put(SagaCommandHeaders.SAGA_ID, "MySagaId");
    return result;
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/test/java/net/chrisrichardson/ftgo/kitchenservice/domain/KitchenServiceInMemoryIntegrationTest.java:KitchenServiceInMemoryIntegrationTest.<init>
package net.chrisrichardson.ftgo.consumerservice.main;

import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import net.chrisrichardson.eventstore.examples.customersandorders.commonswagger.CommonSwaggerConfiguration;
import net.chrisrichardson.ftgo.consumerservice.web.ConsumerWebConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import({ConsumerWebConfiguration.class, TramJdbcKafkaConfiguration.class, CommonSwaggerConfiguration.class})
public class ConsumerServiceMain {

  public static void main(String[] args) {
    SpringApplication.run(ConsumerServiceMain.class, args);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-consumer-service/src/main/java/net/chrisrichardson/ftgo/consumerservice/main/ConsumerServiceMain.java:ConsumerServiceMain.<init>
package net.chrisrichardson.ftgo.consumerservice.web;

import net.chrisrichardson.ftgo.consumerservice.domain.ConsumerServiceConfiguration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

@Configuration
@ComponentScan
@Import(ConsumerServiceConfiguration.class)
public class ConsumerWebConfiguration {
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-consumer-service/src/main/java/net/chrisrichardson/ftgo/consumerservice/web/ConsumerWebConfiguration.java:ConsumerWebConfiguration.<init>
package net.chrisrichardson.ftgo.consumerservice.domain;

import io.eventuate.tram.commands.consumer.CommandDispatcher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.sagas.participant.SagaCommandDispatcherFactory;
import io.eventuate.tram.sagas.spring.participant.SagaParticipantConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableJpaRepositories
@EnableAutoConfiguration
@Import({SagaParticipantConfiguration.class, TramEventsPublisherConfiguration.class, CommonConfiguration.class, SagaParticipantConfiguration.class})
@EnableTransactionManagement
@ComponentScan
public class ConsumerServiceConfiguration {

  @Bean
  public ConsumerServiceCommandHandlers consumerServiceCommandHandlers() {
    return new ConsumerServiceCommandHandlers();
  }

  @Bean
  public ConsumerService consumerService() {
    return new ConsumerService();
  }

  @Bean
  public CommandDispatcher commandDispatcher(ConsumerServiceCommandHandlers consumerServiceCommandHandlers, SagaCommandDispatcherFactory sagaCommandDispatcherFactory) {
    return sagaCommandDispatcherFactory.make("consumerServiceDispatcher", consumerServiceCommandHandlers.commandHandlers());
  }


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-consumer-service/src/main/java/net/chrisrichardson/ftgo/consumerservice/domain/ConsumerServiceConfiguration.java:ConsumerServiceConfiguration.<init>
package net.chrisrichardson.ftgo.consumerservice;


import io.eventuate.tram.commands.producer.CommandProducer;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumer;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.PersonName;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.consumerservice.web.CreateConsumerRequest;
import net.chrisrichardson.ftgo.consumerservice.web.ConsumerWebConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static com.jayway.restassured.RestAssured.given;
import static org.junit.Assert.assertNotNull;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = ConsumerServiceInMemoryIntegrationTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class ConsumerServiceInMemoryIntegrationTest {

  private Logger logger = LoggerFactory.getLogger(getClass());

  @Value("${local.server.port}")
  private int port;

  @Configuration
  @Import({ConsumerWebConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramInMemoryConfiguration.class})
  @EnableAutoConfiguration
  public static class TestConfiguration {

    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }

  }

  private String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Autowired
  private CommandProducer commandProducer;

  @Autowired
  private TestMessageConsumerFactory testMessageConsumerFactory;

  @Test
  public void shouldCreateConsumer() {

    String postUrl = baseUrl("/consumers");

    Integer consumerId =
            given().
            body(new CreateConsumerRequest(new PersonName("John", "Doe"))).
            contentType("application/json").
            when().
            post(postUrl).
            then().
            statusCode(200).
            extract().
            path("consumerId");

    assertNotNull(consumerId);


    TestMessageConsumer testMessageConsumer = testMessageConsumerFactory.make();

    long orderId = 999;
    Money orderTotal = new Money(123);

    String messageId = commandProducer.send("consumerService", null,
            new ValidateOrderByConsumer(consumerId, orderId, orderTotal),
            testMessageConsumer.getReplyChannel(), Collections.emptyMap());

    testMessageConsumer.assertHasReplyTo(messageId);

  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-consumer-service/src/test/java/net/chrisrichardson/ftgo/consumerservice/ConsumerServiceInMemoryIntegrationTest.java:ConsumerServiceInMemoryIntegrationTest.<init>
package net.chrisrichardson.ftgo.consumerservice.api;

import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.testutil.jsonschema.ValidatingJSONMapper;
import org.json.JSONObject;
import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class ValidateOrderByConsumerTest {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Test
  public void shouldDeserialize() {

    ValidatingJSONMapper mapper = ValidatingJSONMapper.forSchema("/ValidateOrderByConsumer.json");

    JSONObject jsonObject = new JSONObject().put("consumerId", 1).put("orderId", 2).put("orderTotal", "12.34");

    ValidateOrderByConsumer cmd = mapper.fromJSON(jsonObject, ValidateOrderByConsumer.class);

    assertEquals(1, cmd.getConsumerId());
    assertEquals(2, cmd.getOrderId());
    assertEquals(new Money("12.34"), cmd.getOrderTotal());
  }


}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-consumer-service/src/test/java/net/chrisrichardson/ftgo/consumerservice/api/ValidateOrderByConsumerTest.java:ValidateOrderByConsumerTest.<init>
package net.chrisrichardson.ftgo.endtoendtests;

import com.jayway.restassured.RestAssured;
import com.jayway.restassured.config.ObjectMapperConfig;
import com.jayway.restassured.config.RestAssuredConfig;
import io.eventuate.common.json.mapper.JSonMapper;
import io.eventuate.util.test.async.UrlTesting;
import net.chrisrichardson.ftgo.apis.model.consumerservice.CreateConsumerRequest;
import net.chrisrichardson.ftgo.apis.model.consumerservice.PersonName;
import net.chrisrichardson.ftgo.apis.model.restaurantservice.CreateRestaurantRequest;
import net.chrisrichardson.ftgo.apis.model.restaurantservice.MenuItem;
import net.chrisrichardson.ftgo.apis.model.restaurantservice.RestaurantMenu;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;
import net.chrisrichardson.ftgo.deliveryservice.api.web.CourierAvailability;
import net.chrisrichardson.ftgo.kitchenservice.api.web.TicketAcceptance;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderRequest;
import net.chrisrichardson.ftgo.orderservice.api.web.ReviseOrderRequest;
import io.eventuate.util.test.async.Eventually;
import net.chrisrichardson.ftgo.testutil.FtgoTestUtil;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Collections;

import static com.jayway.restassured.RestAssured.given;
import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.CoreMatchers.equalTo;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

public class EndToEndTests {

  // TODO Move to a shared module

  public static final String CHICKED_VINDALOO_MENU_ITEM_ID = "1";
  public static final String RESTAURANT_NAME = "My Restaurant";

  private final int revisedQuantityOfChickenVindaloo = 10;
  private String host = FtgoTestUtil.getDockerHostIp();

  private int consumerId;
  private int restaurantId;
  private int orderId;
  private final Money priceOfChickenVindaloo = new Money("12.34");
  private long courierId;

  private String baseUrl(int port, String path, String... pathElements) {
    assertNotNull("host", host);

    StringBuilder sb = new StringBuilder("http://");
    sb.append(host);
    sb.append(":");
    sb.append(port);
    sb.append("/");
    sb.append(path);

    for (String pe : pathElements) {
      sb.append("/");
      sb.append(pe);
    }
    String s = sb.toString();
    System.out.println("url=" + s);
    return s;
  }

  private int consumerPort = 8081;
  private int orderPort = 8082;
  private int accountingPort = 8085;
  private int restaurantsPort = 8084;
  private int kitchenPort = 8083;
  private int apiGatewayPort = 8087;
  private int deliveryServicePort = 8089;


  private String consumerBaseUrl(String... pathElements) {
    return baseUrl(consumerPort, "consumers", pathElements);
  }

  private String accountingBaseUrl(String... pathElements) {
    return baseUrl(accountingPort, "accounts", pathElements);
  }

  private String restaurantBaseUrl(String... pathElements) {
    return baseUrl(restaurantsPort, "restaurants", pathElements);
  }

  private String kitchenRestaurantBaseUrl(String... pathElements) {
    return kitchenServiceBaseUrl("restaurants", pathElements);
  }

  private String kitchenServiceBaseUrl(String first, String... pathElements) {
    return baseUrl(kitchenPort, first, pathElements);
  }

  private String orderBaseUrl(String... pathElements) {
    return baseUrl(apiGatewayPort, "orders", pathElements);
  }

  private String deliveryServiceBaseUrl(String first, String... pathElements) {
    return baseUrl(deliveryServicePort, first, pathElements);
  }

  private String orderRestaurantBaseUrl(String... pathElements) {
    return baseUrl(orderPort, "restaurants", pathElements);
  }

  private String orderHistoryBaseUrl(String... pathElements) {
    return baseUrl(apiGatewayPort, "orders", pathElements);
  }

  @BeforeClass
  public static void initialize() {
    CommonJsonMapperInitializer.registerMoneyModule();

    RestAssured.config = RestAssuredConfig.config().objectMapperConfig(new ObjectMapperConfig().jackson2ObjectMapperFactory(
            (aClass, s) -> JSonMapper.objectMapper
    ));

  }

  @Test
  public void shouldCreateReviseAndCancelOrder() {

    createOrder();

    reviseOrder();

    cancelOrder();

  }

  @Test
  public void shouldDeliverOrder() {

    createOrder();

    noteCourierAvailable();

    acceptTicket();

    assertOrderAssignedToCourier();

  }

  @Test
  public void testSwaggerUiUrls() throws IOException {
    testSwaggerUiUrl(8081);
    testSwaggerUiUrl(8082);
    testSwaggerUiUrl(8084);
    testSwaggerUiUrl(8086);
  }

  private void testSwaggerUiUrl(int port) throws IOException {
    UrlTesting.assertUrlStatusIsOk("localhost", port, "/swagger-ui/index.html");
  }

  private void reviseOrder() {
    reviseOrder(orderId);
    verifyOrderRevised(orderId);
  }

  private void verifyOrderRevised(int orderId) {
    Eventually.eventually(String.format("verifyOrderRevised state %s", orderId), () -> {
      String orderTotal = given().
              when().
              get(baseUrl(orderPort, "orders", Integer.toString(orderId))).
              then().
              statusCode(200)
              .extract().
                      path("orderTotal");
      assertEquals(priceOfChickenVindaloo.multiply(revisedQuantityOfChickenVindaloo).asString(), orderTotal);
    });
    Eventually.eventually(String.format("verifyOrderRevised state %s", orderId), () -> {
      String state = given().
              when().
              get(orderBaseUrl(Integer.toString(orderId))).
              then().
              statusCode(200)
              .extract().
                      path("orderInfo.state");
      assertEquals("APPROVED", state);
    });
  }

  private void reviseOrder(int orderId) {
    given().
            body(new ReviseOrderRequest(Collections.singletonList(new RevisedOrderLineItem(revisedQuantityOfChickenVindaloo, CHICKED_VINDALOO_MENU_ITEM_ID))))
            .contentType("application/json").
            when().
            post(orderBaseUrl(Integer.toString(orderId), "revise")).
            then().
            statusCode(200);
  }


  private void createOrder() {
    consumerId = createConsumer();

    verifyAccountCreatedForConsumer(consumerId);

    restaurantId = createRestaurant();

    verifyRestaurantCreatedInKitchenService(restaurantId);

    verifyRestaurantCreatedInOrderService(restaurantId);

    orderId = createOrder(consumerId, restaurantId);

    verifyOrderAuthorized(orderId);

    verifyOrderHistoryUpdated(orderId, consumerId, OrderState.APPROVED.name());
  }

  private void cancelOrder() {
    cancelOrder(orderId);

    verifyOrderCancelled(orderId);

    verifyOrderHistoryUpdated(orderId, consumerId, OrderState.CANCELLED.name());

  }

  private void verifyOrderCancelled(int orderId) {
    Eventually.eventually(String.format("verifyOrderCancelled %s", orderId), () -> {
      String state = given().
              when().
              get(orderBaseUrl(Integer.toString(orderId))).
              then().
              statusCode(200)
              .extract().
                      path("orderInfo.state");
      assertEquals("CANCELLED", state);
    });

  }

  private void cancelOrder(int orderId) {
    given().
            body("{}").
            contentType("application/json").
            when().
            post(orderBaseUrl(Integer.toString(orderId), "cancel")).
            then().
            statusCode(200);

  }

  private Integer createConsumer() {
    Integer consumerId =
            given().
                    body(new CreateConsumerRequest().name(new PersonName().firstName("John").lastName("Doe"))).
                    contentType("application/json").
                    when().
                    post(consumerBaseUrl()).
                    then().
                    statusCode(200).
                    extract().
                    path("consumerId");

    assertNotNull(consumerId);
    return consumerId;
  }

  private void verifyAccountCreatedForConsumer(int consumerId) {
    Eventually.eventually(() ->
            given().
                    when().
                    get(accountingBaseUrl(Integer.toString(consumerId))).
                    then().
                    statusCode(200));

  }

  private int createRestaurant() {
    CreateRestaurantRequest request = new CreateRestaurantRequest().name(RESTAURANT_NAME)
            .address(new net.chrisrichardson.ftgo.apis.model.restaurantservice.Address()
                    .street1("1 Main Street").street2("Unit 99").city("Oakland").state("CA").zip("94611"))
            .menu(
                    new RestaurantMenu().addMenuItemsItem(
                            new MenuItem().id(CHICKED_VINDALOO_MENU_ITEM_ID)
                                    .name("Chicken Vindaloo")
                                    .price(priceOfChickenVindaloo.asString())));
    Integer restaurantId =
            given().
                    body(request).
                    contentType("application/json").
                    when().
                    post(restaurantBaseUrl()).
                    then().
                    statusCode(200).
                    extract().
                    path("id");

    assertNotNull(restaurantId);
    return restaurantId;
  }

  private void verifyRestaurantCreatedInKitchenService(int restaurantId) {
    Eventually.eventually(String.format("verifyRestaurantCreatedInKitchenService %s", restaurantId), () ->
            given().
                    when().
                    get(kitchenRestaurantBaseUrl(Integer.toString(restaurantId))).
                    then().
                    statusCode(200));
  }

  private void verifyRestaurantCreatedInOrderService(int restaurantId) {
    Eventually.eventually(String.format("verifyRestaurantCreatedInOrderService %s", restaurantId), () ->
            given().
                    when().
                    get(orderRestaurantBaseUrl(Integer.toString(restaurantId))).
                    then().
                    statusCode(200));
  }

  private int createOrder(int consumerId, int restaurantId) {
    Integer orderId =
            given().
                    body(new CreateOrderRequest(consumerId, restaurantId,
                            new Address("9 Amazing View", null, "Oakland", "CA", "94612"),
                            LocalDateTime.now(),
                            Collections.singletonList(new CreateOrderRequest.LineItem(CHICKED_VINDALOO_MENU_ITEM_ID, 5)))).
                    contentType("application/json").
                    when().
                    post(orderBaseUrl()).
                    then().
                    statusCode(200).
                    extract().
                    path("orderId");

    assertNotNull(orderId);
    return orderId;
  }

  private void verifyOrderAuthorized(int orderId) {
    Eventually.eventually(String.format("verifyOrderApproved %s", orderId), () -> {
      String state = given().
              when().
              get(orderBaseUrl(Integer.toString(orderId))).
              then().
              statusCode(200)
              .extract().
                      path("orderInfo.state");
      assertEquals("APPROVED", state);
    });
  }


  private void verifyOrderHistoryUpdated(int orderId, int consumerId, String expectedState) {
    Eventually.eventually(String.format("verifyOrderHistoryUpdated %s", orderId), () -> {
      String state = given().
              when().
              get(orderHistoryBaseUrl() + "?consumerId=" + consumerId).
              then().
              statusCode(200)
              .body("orders[0].restaurantName", equalTo(RESTAURANT_NAME))
              .extract().
                      path("orders[0].status"); // TODO state?
      assertEquals(expectedState, state);
    });
  }

  private void noteCourierAvailable() {
    courierId = System.currentTimeMillis();
    given().
            body(new CourierAvailability(true)).
            contentType("application/json").
            when().
            post(deliveryServiceBaseUrl("couriers", Long.toString(courierId), "availability")).
            then().
            statusCode(200);
  }

  private void acceptTicket() {
    courierId = System.currentTimeMillis();
    given().
            body(new TicketAcceptance(LocalDateTime.now().plusHours(9))).
            contentType("application/json").
            when().
            post(kitchenServiceBaseUrl("tickets", Long.toString(orderId), "accept")).
            then().
            statusCode(200);
  }

  private void assertOrderAssignedToCourier() {
    Eventually.eventually(() -> {
      long assignedCourier = given().
              when().
              get(deliveryServiceBaseUrl("deliveries", Long.toString(orderId))).
              then().
              statusCode(200)
              .extract()
              .path("assignedCourier");
      assertThat(assignedCourier).isGreaterThan(0);
    });

  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-end-to-end-tests/src/test/java/net/chrisrichardson/ftgo/endtoendtests/EndToEndTests.java:EndToEndTests.<init>
// Node: objectMapperConfig
// Node: ObjectMapperConfig
// Node: jackson2ObjectMapperFactory
