// Cluster 3

// Node: assertNotNull
package net.chrisrichardson.ftgo.orderservice.api.events;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.List;

public class OrderDetails {

  private List<OrderLineItem> lineItems;
  private Money orderTotal;

  private long restaurantId;
  private long consumerId;

  private OrderDetails() {
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }

  public OrderDetails(long consumerId, long restaurantId, List<OrderLineItem> lineItems, Money orderTotal) {
    this.consumerId = consumerId;
    this.restaurantId = restaurantId;
    this.lineItems = lineItems;
    this.orderTotal = orderTotal;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public List<OrderLineItem> getLineItems() {
    return lineItems;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public long getConsumerId() {
    return consumerId;
  }


  public void setLineItems(List<OrderLineItem> lineItems) {
    this.lineItems = lineItems;
  }


  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service-api/src/main/java/net/chrisrichardson/ftgo/orderservice/api/events/OrderDetails.java:OrderDetails.<init>
// Node: OrderDetails
// Node: OrderLineItem
package net.chrisrichardson.ftgo.orderservice.api.events;

import net.chrisrichardson.ftgo.common.Address;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class OrderCreatedEvent implements OrderDomainEvent {
  private OrderDetails orderDetails;
  private Address deliveryAddress;
  private String restaurantName;

  private OrderCreatedEvent() {
  }

  public OrderCreatedEvent(OrderDetails orderDetails, Address deliveryAddress, String restaurantName) {

    this.orderDetails = orderDetails;
    this.deliveryAddress = deliveryAddress;
    this.restaurantName = restaurantName;
  }

  public OrderDetails getOrderDetails() {
    return orderDetails;
  }

  public void setOrderDetails(OrderDetails orderDetails) {
    this.orderDetails = orderDetails;
  }

  public String getRestaurantName() {
    return restaurantName;
  }

  public void setRestaurantName(String restaurantName) {
    this.restaurantName = restaurantName;
  }

  public Address getDeliveryAddress() {
    return deliveryAddress;
  }

  public void setDeliveryAddress(Address deliveryAddress) {
    this.deliveryAddress = deliveryAddress;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service-api/src/main/java/net/chrisrichardson/ftgo/orderservice/api/events/OrderCreatedEvent.java:OrderCreatedEvent.<init>
// Node: OrderCreatedEvent
package net.chrisrichardson.ftgo.testutil;

import java.util.Optional;

import static org.junit.Assert.assertTrue;

public class FtgoTestUtil {

  public static <T> void assertPresent(Optional<T> value) {
    assertTrue(value.isPresent());
  }

  public static String getDockerHostIp() {
    return Optional.ofNullable(System.getenv("DOCKER_HOST_IP")).orElse("localhost");
  }
}


// Node: assertTrue
// Node: isPresent
package net.chrisrichardson.ftgo.kitchenservice.api;

import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.List;

public class TicketDetails {
  private List<TicketLineItem> lineItems;

  public TicketDetails() {
  }

  public TicketDetails(List<TicketLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public List<TicketLineItem> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<TicketLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/TicketDetails.java:TicketDetails.<init>
// Node: TicketDetails
package net.chrisrichardson.ftgo.kitchenservice.api.events;

import java.time.LocalDateTime;

public class TicketAcceptedEvent implements TicketDomainEvent {
  private LocalDateTime readyBy;

  public TicketAcceptedEvent() {
  }

  public TicketAcceptedEvent(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }

  public LocalDateTime getReadyBy() {
    return readyBy;
  }

  public void setReadyBy(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/events/TicketAcceptedEvent.java:TicketAcceptedEvent.<init>
// Node: TicketAcceptedEvent
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


// Node: restaurantCreated
// Node: emptyList
// Node: publish
// Node: singletonList
// Node: RestaurantCreated
package net.chrisrichardson.ftgo.restaurantservice.events;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;

public class RestaurantCreated implements RestaurantDomainEvent {
  private String name;
  private Address address;
  private RestaurantMenu menu;

  public String getName() {
    return name;
  }

  private RestaurantCreated() {
  }

  public RestaurantCreated(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;

    if (menu == null) 
      throw new NullPointerException("Null Menu");
    if (address == null) 
      throw new NullPointerException("Null address");
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Address getAddress() {
    return address;
  }

  public void setAddress(Address address) {
    this.address = address;
  }
}


// Node: getAddress
// Node: create
// Node: findById
package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Address;

public class CreateRestaurantRequest {

  private String name;
  private Address address;
  private RestaurantMenu menu;

  private CreateRestaurantRequest() {

  }

  public CreateRestaurantRequest(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public Address getAddress() {
    return address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.Optional;

@Transactional
public class RestaurantService {


  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private RestaurantDomainEventPublisher restaurantDomainEventPublisher;

  public Restaurant create(CreateRestaurantRequest request) {
    Restaurant restaurant = new Restaurant(request.getName(), request.getMenu());
    restaurantRepository.save(restaurant);
    restaurantDomainEventPublisher.publish(restaurant, Collections.singletonList(new RestaurantCreated(request.getName(), request.getAddress(), request.getMenu())));
    return restaurant;
  }

  public Optional<Restaurant> findById(long restaurantId) {
    return restaurantRepository.findById(restaurantId);
  }
}


// Node: save
package net.chrisrichardson.ftgo.restaurantservice.events;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.restaurantservice.domain.MenuItem;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;
import net.chrisrichardson.ftgo.testutil.jsonschema.ValidatingJSONMapper;
import org.json.JSONException;
import org.junit.Test;

import java.util.Collections;

import static org.junit.Assert.assertNotNull;

public class RestaurantCreatedSerializationTest {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  public static final String AJANTA_RESTAURANT_NAME = "Ajanta";
  public static final long AJANTA_ID = 1L;
  public static final String CHICKEN_VINDALOO = "Chicken Vindaloo";
  public static final String CHICKEN_VINDALOO_MENU_ITEM_ID = "1";
  public static final Money CHICKEN_VINDALOO_PRICE = new Money("12.34");
  public static final Address RESTAURANT_ADDRESS = new Address("1 Main Street", "Unit 99", "Oakland", "CA", "94611");

  public static MenuItem CHICKEN_VINDALOO_MENU_ITEM = new MenuItem(CHICKEN_VINDALOO_MENU_ITEM_ID, CHICKEN_VINDALOO, CHICKEN_VINDALOO_PRICE);

  @Test
  public void shouldSerialize() throws JSONException {

    ValidatingJSONMapper mapper = ValidatingJSONMapper.forSchema("/ftgo-restaurant-service-api-spec/messages/RestaurantCreated.json");

    RestaurantCreated event = new RestaurantCreated(AJANTA_RESTAURANT_NAME, RESTAURANT_ADDRESS,
            new RestaurantMenu(Collections.singletonList(CHICKEN_VINDALOO_MENU_ITEM)));
    String json = mapper.toJSON(event);
    assertNotNull(json);
  }


}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/test/java/net/chrisrichardson/ftgo/restaurantservice/events/RestaurantCreatedSerializationTest.java:RestaurantCreatedSerializationTest.<init>
// Node: shouldSerialize
package net.chrisrichardson.ftgo.apiagateway.proxies;

public class OrderNotFoundException extends RuntimeException {
  public OrderNotFoundException() {
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-api-gateway/src/main/java/net/chrisrichardson/ftgo/apiagateway/proxies/OrderNotFoundException.java:OrderNotFoundException.<init>
// Node: OrderNotFoundException
package net.chrisrichardson.ftgo.apiagateway.orders;

import net.chrisrichardson.ftgo.apiagateway.proxies.AccountingService;
import net.chrisrichardson.ftgo.apiagateway.proxies.DeliveryService;
import net.chrisrichardson.ftgo.apiagateway.proxies.OrderServiceProxy;
import net.chrisrichardson.ftgo.apiagateway.proxies.KitchenService;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.server.RouterFunction;
import org.springframework.web.reactive.function.server.RouterFunctions;
import org.springframework.web.reactive.function.server.ServerResponse;

import static org.springframework.web.reactive.function.server.RequestPredicates.GET;

@Configuration
@EnableConfigurationProperties(OrderDestinations.class)
public class OrderConfiguration {

  @Bean
  public RouteLocator orderProxyRouting(RouteLocatorBuilder builder, OrderDestinations orderDestinations) {
    return builder.routes()
            .route(r -> r.path("/orders").and().method("POST").uri(orderDestinations.getOrderServiceUrl()))
            .route(r -> r.path("/orders").and().method("PUT").uri(orderDestinations.getOrderServiceUrl()))
            .route(r -> r.path("/orders/**").and().method("POST").uri(orderDestinations.getOrderServiceUrl()))
            .route(r -> r.path("/orders/**").and().method("PUT").uri(orderDestinations.getOrderServiceUrl()))
            .route(r -> r.path("/orders").and().method("GET").uri(orderDestinations.getOrderHistoryServiceUrl()))
            .build();
  }

  @Bean
  public RouterFunction<ServerResponse> orderHandlerRouting(OrderHandlers orderHandlers) {
    return RouterFunctions.route(GET("/orders/{orderId}"), orderHandlers::getOrderDetails);
  }

  @Bean
  public OrderHandlers orderHandlers(OrderServiceProxy orderService, KitchenService kitchenService,
                                     DeliveryService deliveryService, AccountingService accountingService) {
    return new OrderHandlers(orderService, kitchenService, deliveryService, accountingService);
  }

  @Bean
  public WebClient webClient() {
    return WebClient.create();
  }

}


// Node: webClient
// Node: withStatus
package net.chrisrichardson.ftgo.restaurantservice.events;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;

public class RestaurantCreated implements RestaurantDomainEvent {
  private String name;
  private Address address;
  private RestaurantMenu menu;

  public String getName() {
    return name;
  }

  private RestaurantCreated() {
  }

  public RestaurantCreated(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;


    if (menu == null) 
      throw new NullPointerException("Null Menu");
    if (address == null) 
      throw new NullPointerException("Null address");    
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Address getAddress() {
    return address;
  }

  public void setAddress(Address address) {
    this.address = address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Address;

public class CreateRestaurantRequest {

  private String name;
  private Address address;
  private RestaurantMenu menu;

  private CreateRestaurantRequest() {

  }

  public CreateRestaurantRequest(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public Address getAddress() {
    return address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.Optional;

@Transactional
public class RestaurantService {


  private RestaurantRepository restaurantRepository;

  @Autowired
  private DomainEventPublisher domainEventPublisher;


  public RestaurantService() {
  }

  public RestaurantService(RestaurantRepository restaurantRepository) {
    this.restaurantRepository = restaurantRepository;
  }



  public Restaurant create(CreateRestaurantRequest request) {
    Restaurant restaurant = new Restaurant(request.getName(), request.getMenu());
    restaurantRepository.save(restaurant);
    domainEventPublisher.publish(Restaurant.class, restaurant.getId(), Collections.singletonList(new RestaurantCreated(request.getName(), request.getAddress(), request.getMenu())));
    return restaurant;
  }

  public Optional<Restaurant> findById(long restaurantId) {
    return restaurantRepository.findById(restaurantId);
  }
}


package net.chrisrichardson.ftgo.common;

public class UnsupportedStateTransitionException extends RuntimeException {
  public UnsupportedStateTransitionException(Enum state) {
    super("current state: " + state);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-common/src/main/java/net/chrisrichardson/ftgo/common/UnsupportedStateTransitionException.java:UnsupportedStateTransitionException.<init>
// Node: UnsupportedStateTransitionException
package net.chrisrichardson.ftgo.common;


import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class MoneyTest {

  private final int M1_AMOUNT = 10;
  private final int M2_AMOUNT = 15;

  private Money m1 = new Money(M1_AMOUNT);
  private Money m2 = new Money(M2_AMOUNT);

  @Test
  public void shouldReturnAsString() {
    assertEquals(Integer.toString(M1_AMOUNT), new Money(M1_AMOUNT).asString());
  }

  @Test
  public void shouldCompare() {
    assertTrue(m2.isGreaterThanOrEqual(m2));
    assertTrue(m2.isGreaterThanOrEqual(m1));
    assertFalse(m1.isGreaterThanOrEqual(m2));
  }

  @Test
  public void shouldAdd() {
    assertEquals(new Money(M1_AMOUNT + M2_AMOUNT), m1.add(m2));
  }

  @Test
  public void shouldMultiply() {
    int multiplier = 12;
    assertEquals(new Money(M2_AMOUNT * multiplier), m2.multiply(multiplier));
  }



}

// Node: shouldCompare
// Node: assertFalse
package net.chrisrichardson.ftgo.accountingservice.domain;

import io.eventuate.sync.AggregateRepository;
import io.eventuate.EntityWithIdAndVersion;
import io.eventuate.SaveOptions;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Optional;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class AccountingService {
  @Autowired
  private AggregateRepository<Account, AccountCommand> accountRepository;

  public void create(String aggregateId) {
    EntityWithIdAndVersion<Account> account = accountRepository.save(new CreateAccountCommand(),
            Optional.of(new SaveOptions().withId(aggregateId)));
  }
}


// Node: CreateAccountCommand
// Node: SaveOptions
package net.chrisrichardson.ftgo.accountingservice.domain;

import io.eventuate.Event;
import io.eventuate.ReflectiveMutableCommandProcessingAggregate;
import io.eventuate.tram.sagas.eventsourcingsupport.SagaReplyRequestedEvent;

import java.util.Collections;
import java.util.List;

import static io.eventuate.EventUtil.events;

public class Account extends ReflectiveMutableCommandProcessingAggregate<Account, AccountCommand> {

  public List<Event> process(CreateAccountCommand command) {
    return events(new AccountCreatedEvent());
  }

  public void apply(AccountCreatedEvent event) {

  }


  public List<Event> process(AuthorizeCommandInternal command) {
    return events(new AccountAuthorizedEvent());
  }

  public List<Event> process(ReverseAuthorizationCommandInternal command) {
    return Collections.emptyList();
  }
  public List<Event> process(ReviseAuthorizationCommandInternal command) {
    return Collections.emptyList();
  }

  public void apply(AccountAuthorizedEvent event) {

  }

  public void apply(SagaReplyRequestedEvent event) {
    // TODO - need a way to not need this method
  }


}


// Node: process
// Node: events
// Node: AccountCreatedEvent
// Node: AccountAuthorizedEvent
// Node: apply
// Node: singleton
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

// Node: shouldReply
// Node: currentTimeMillis
// Node: ConsumerCreated
// Node: find
// Node: getReplyChannel
// Node: assertHasReplyTo
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

// Node: Order
// Node: setCreationDate
// Node: now
// Node: minusDays
// Node: SourceEvent
// Node: addOrder
// Node: assertOrderEquals
// Node: updateOrderState
// Node: shouldFindOrders
// Node: findOrderHistory
// Node: OrderHistoryFilter
// Node: getOrders
// Node: assertContainsOrderId
// Node: shouldFindOrdersWithStatus
// Node: shouldCancel
// Node: shouldHandleCancel
// Node: shouldFindOrdersWithCancelledStatus
// Node: shouldFindOrderByRestaurantName
// Node: withKeywords
// Node: shouldFindOrderByMenuItem
// Node: shouldReturnOrdersSorted
// Node: shouldPaginateResults
// Node: withPageSize
// Node: size
// Node: withStartKeyToken
package net.chrisrichardson.ftgo.cqrs.orderhistory;

import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.joda.time.DateTime;

import java.util.Optional;
import java.util.Set;

import static java.util.Collections.emptySet;

public class OrderHistoryFilter {
  private DateTime since = DateTime.now().minusDays(30);
  private Optional<OrderState> status = Optional.empty();
  private Set<String> keywords = emptySet();
  private Optional<String> startKeyToken = Optional.empty();
  private Optional<Integer> pageSize = Optional.empty();

  public DateTime getSince() {
    return since;
  }

  public OrderHistoryFilter withStatus(OrderState status) {
    this.status = Optional.of(status);
    return this;
  }

  public Optional<OrderState> getStatus() {
    return status;
  }


  public OrderHistoryFilter withStartKeyToken(Optional<String> startKeyToken) {
    this.startKeyToken = startKeyToken;
    return this;
  }

  public OrderHistoryFilter withKeywords(Set<String> keywords) {
    this.keywords = keywords;
    return this;
  }


  public Set<String> getKeywords() {
    return keywords;
  }

  public Optional<String> getStartKeyToken() {
    return startKeyToken;
  }

  public OrderHistoryFilter withPageSize(int pageSize) {
    this.pageSize = Optional.of(pageSize);
    return this;
  }

  public Optional<Integer> getPageSize() {
    return pageSize;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/OrderHistoryFilter.java:OrderHistoryFilter.<init>
// Node: emptySet
package net.chrisrichardson.ftgo.cqrs.orderhistory;


import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.SourceEvent;
import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.Order;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;

import java.util.Optional;

public interface OrderHistoryDao {

  boolean addOrder(Order order, Optional<SourceEvent> eventSource);

  OrderHistory findOrderHistory(String consumerId, OrderHistoryFilter filter);

  boolean updateOrderState(String orderId, OrderState newState, Optional<SourceEvent> eventSource);

  void noteTicketPreparationStarted(String orderId);

  void noteTicketPreparationCompleted(String orderId);

  void notePickedUp(String orderId, Optional<SourceEvent> eventSource);

  void updateLocation(String orderId, Location location);

  void noteDelivered(String orderId);

  Optional<Order> findOrder(String orderId);

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/OrderHistoryDao.java:OrderHistoryDao.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory;

import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.Order;

import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

public class OrderHistory {
  private List<Order> orders;
  private Optional<String> startKey;

  public OrderHistory(List<Order> orders, Optional<String> startKey) {
    this.orders = orders;
    this.startKey = startKey;
  }

  public List<Order> getOrders() {
    return orders;
  }

  public Optional<String> getStartKey() {
    return startKey;
  }
}


package net.chrisrichardson.ftgo.cqrs.orderhistory.web;

import java.util.List;

public class GetOrdersResponse {
  private List<GetOrderResponse> orders;
  private String startKey;

  private GetOrdersResponse() {
  }

  public List<GetOrderResponse> getOrders() {
    return orders;
  }

  public void setOrders(List<GetOrderResponse> orders) {
    this.orders = orders;
  }

  public String getStartKey() {
    return startKey;
  }

  public void setStartKey(String startKey) {
    this.startKey = startKey;
  }

  public GetOrdersResponse(List<GetOrderResponse> orders, String startKey) {
    this.orders = orders;
    this.startKey = startKey;
  }
}


package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import com.amazonaws.services.dynamodbv2.document.spec.UpdateItemSpec;

import java.util.HashMap;

public class SourceEvent {

  String aggregateType;
  String aggregateId;
  String eventId;

  public SourceEvent(String aggregateType, String aggregateId, String eventId) {
    this.aggregateType = aggregateType;
    this.aggregateId = aggregateId;
    this.eventId = eventId;
  }

  public String getAggregateType() {
    return aggregateType;
  }

  public UpdateItemSpec addDuplicateDetection(UpdateItemSpec spec) {
    HashMap<String, String> nameMap = spec.getNameMap() == null ? new HashMap<>() : new HashMap<>(spec.getNameMap());
    nameMap.put("#duplicateDetection", "events." + aggregateType + aggregateId);
    HashMap<String, Object> valueMap = new HashMap<>(spec.getValueMap());
    valueMap.put(":eventId", eventId);
    return spec.withUpdateExpression(String.format("%s , #duplicateDetection = :eventId", spec.getUpdateExpression()))
            .withNameMap(nameMap)
            .withValueMap(valueMap)
            .withConditionExpression(Expressions.and(spec.getConditionExpression(), "attribute_not_exists(#duplicateDetection) OR #duplicateDetection < :eventId"));
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/SourceEvent.java:SourceEvent.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.joda.time.DateTime;

import java.util.List;

public class Order {
  private String consumerId;
  private DateTime creationDate = DateTime.now();
  private OrderState status;
  private String orderId;
  private List<OrderLineItem> lineItems;
  private Money orderTotal;
  private long restaurantId;
  private String restaurantName;

  public Order(String orderId, String consumerId, OrderState status, List<OrderLineItem> lineItems, Money orderTotal, long restaurantId, String restaurantName) {
    this.orderId = orderId;
    this.consumerId = consumerId;
    this.status = status;
    this.lineItems = lineItems;
    this.orderTotal = orderTotal;
    this.restaurantId = restaurantId;
    this.restaurantName = restaurantName;
  }

  public String getRestaurantName() {
    return restaurantName;
  }

  public String getOrderId() {
    return orderId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }
  
  public List<OrderLineItem> getLineItems() {
    return lineItems;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setCreationDate(DateTime creationDate) {
    this.creationDate = creationDate;
  }

  public String getConsumerId() {
    return consumerId;
  }

  public DateTime getCreationDate() {
    return creationDate;
  }

  public OrderState getStatus() {
    return status;
  }


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/Order.java:Order.<init>
// Node: orElseThrow
// Node: getDeliveryInformation
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


// Node: orderCreatedEvent
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


// Node: orderCreated
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


// Node: shouldSaveAndLoadOrder
// Node: execute
// Node: chickenVindalooLineItems
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


package net.chrisrichardson.ftgo.orderservice.sagas.reviseorder;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.domain.OrderRevision;

public class ReviseOrderSagaData  {

  private OrderRevision orderRevision;
  private Long orderId;
  private Long expectedVersion;
  private long restaurantId;
  private Money revisedOrderTotal;
  private long consumerId;

  private ReviseOrderSagaData() {
  }

  public ReviseOrderSagaData(long consumerId, Long orderId, Long expectedVersion, OrderRevision orderRevision) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.expectedVersion = expectedVersion;
    this.orderRevision = orderRevision;
  }

  public Long getExpectedVersion() {
    return expectedVersion;
  }

  public void setExpectedVersion(Long expectedVersion) {
    this.expectedVersion = expectedVersion;
  }

  public void setRevisedOrderTotal(Money revisedOrderTotal) {
    this.revisedOrderTotal = revisedOrderTotal;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }


  public OrderRevision getOrderRevision() {
    return orderRevision;
  }

  public void setOrderRevision(OrderRevision orderRevision) {
    this.orderRevision = orderRevision;
  }

  public Long getOrderId() {
    return orderId;
  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }


  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public Money getRevisedOrderTotal() {
    return revisedOrderTotal;
  }

  public long getConsumerId() {
    return consumerId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagas/reviseorder/ReviseOrderSagaData.java:ReviseOrderSagaData.<init>
// Node: ReviseOrderSagaData
// Node: makeTicketDetails
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


// Node: makeTicketLineItems
package net.chrisrichardson.ftgo.orderservice.sagas.cancelorder;

import net.chrisrichardson.ftgo.common.Money;

public class CancelOrderSagaData  {

  private Long orderId;
  private String reverseRequestId;
  private long restaurantId;
  private long consumerId;
  private Money orderTotal;

  private CancelOrderSagaData() {
  }

  public CancelOrderSagaData(long consumerId, long orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  public Long getOrderId() {
    return orderId;
  }


  public String getReverseRequestId() {
    return reverseRequestId;
  }

  public void setReverseRequestId(String reverseRequestId) {
    this.reverseRequestId = reverseRequestId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public long getConsumerId() {
    return consumerId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagas/cancelorder/CancelOrderSagaData.java:CancelOrderSagaData.<init>
// Node: CancelOrderSagaData
// Node: DeliveryInformation
// Node: confirmCancel
// Node: confirmRevision
package net.chrisrichardson.ftgo.orderservice.web;

import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderRequest;
import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderResponse;
import net.chrisrichardson.ftgo.orderservice.api.web.ReviseOrderRequest;
import net.chrisrichardson.ftgo.orderservice.domain.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;

import static java.util.stream.Collectors.toList;

@RestController
@RequestMapping(path = "/orders")
public class OrderController {

  private OrderService orderService;

  private OrderRepository orderRepository;


  public OrderController(OrderService orderService, OrderRepository orderRepository) {
    this.orderService = orderService;
    this.orderRepository = orderRepository;
  }

  @RequestMapping(method = RequestMethod.POST)
  public CreateOrderResponse create(@RequestBody CreateOrderRequest request) {
    Order order = orderService.createOrder(request.getConsumerId(),
            request.getRestaurantId(),
            new DeliveryInformation(request.getDeliveryTime(), request.getDeliveryAddress()),
            request.getLineItems().stream().map(x -> new MenuItemIdAndQuantity(x.getMenuItemId(), x.getQuantity())).collect(toList())
    );
    return new CreateOrderResponse(order.getId());
  }


  @RequestMapping(path = "/{orderId}", method = RequestMethod.GET)
  public ResponseEntity<GetOrderResponse> getOrder(@PathVariable long orderId) {
    Optional<Order> order = orderRepository.findById(orderId);
    return order.map(o -> new ResponseEntity<>(makeGetOrderResponse(o), HttpStatus.OK)).orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }

  private GetOrderResponse makeGetOrderResponse(Order order) {
    return new GetOrderResponse(order.getId(), order.getState(), order.getOrderTotal());
  }

  @RequestMapping(path = "/{orderId}/cancel", method = RequestMethod.POST)
  public ResponseEntity<GetOrderResponse> cancel(@PathVariable long orderId) {
    try {
      Order order = orderService.cancel(orderId);
      return new ResponseEntity<>(makeGetOrderResponse(order), HttpStatus.OK);
    } catch (OrderNotFoundException e) {
      return new ResponseEntity<>(HttpStatus.NOT_FOUND);
    }
  }

  @RequestMapping(path = "/{orderId}/revise", method = RequestMethod.POST)
  public ResponseEntity<GetOrderResponse> revise(@PathVariable long orderId, @RequestBody ReviseOrderRequest request) {
    try {
      Order order = orderService.reviseOrder(orderId, new OrderRevision(Optional.empty(), request.getRevisedOrderLineItems()));
      return new ResponseEntity<>(makeGetOrderResponse(order), HttpStatus.OK);
    } catch (OrderNotFoundException e) {
      return new ResponseEntity<>(HttpStatus.NOT_FOUND);
    }
  }

}


// Node: cancel
// Node: IllegalArgumentException
package net.chrisrichardson.ftgo.orderservice.domain;

public class OrderNotFoundException extends RuntimeException {
  public OrderNotFoundException(Long orderId) {
    super("Order not found" + orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderNotFoundException.java:OrderNotFoundException.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

public class RevisedOrder {
  private final Order order;
  private final LineItemQuantityChange change;

  public RevisedOrder(Order order, LineItemQuantityChange change) {
    this.order = order;
    this.change = change;
  }

  public Order getOrder() {
    return order;
  }

  public LineItemQuantityChange getChange() {
    return change;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/RevisedOrder.java:RevisedOrder.<init>
// Node: RevisedOrder
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.UnsupportedStateTransitionException;
import net.chrisrichardson.ftgo.orderservice.api.events.*;

import javax.persistence.*;
import java.util.List;

import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.APPROVED;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.APPROVAL_PENDING;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.REJECTED;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.REVISION_PENDING;
import static java.util.Collections.emptyList;
import static java.util.Collections.singletonList;

@Entity
@Table(name = "orders")
@Access(AccessType.FIELD)
public class Order {

  public static ResultWithDomainEvents<Order, OrderDomainEvent>
  createOrder(long consumerId, Restaurant restaurant, DeliveryInformation deliveryInformation, List<OrderLineItem> orderLineItems) {
    Order order = new Order(consumerId, restaurant.getId(), deliveryInformation, orderLineItems);
    List<OrderDomainEvent> events = singletonList(new OrderCreatedEvent(
            new OrderDetails(consumerId, restaurant.getId(), orderLineItems,
                    order.getOrderTotal()),
            deliveryInformation.getDeliveryAddress(),
            restaurant.getName()));
    return new ResultWithDomainEvents<>(order, events);
  }

  @Id
  @GeneratedValue
  private Long id;

  @Version
  private Long version;

  @Enumerated(EnumType.STRING)
  private OrderState state;

  private Long consumerId;
  private Long restaurantId;

  @Embedded
  private OrderLineItems orderLineItems;

  @Embedded
  private DeliveryInformation deliveryInformation;

  @Embedded
  private PaymentInformation paymentInformation;

  @Embedded
  private Money orderMinimum = new Money(Integer.MAX_VALUE);

  private Order() {
  }

  public Order(long consumerId, long restaurantId, DeliveryInformation deliveryInformation, List<OrderLineItem> orderLineItems) {
    this.consumerId = consumerId;
    this.restaurantId = restaurantId;
    this.deliveryInformation = deliveryInformation;
    this.orderLineItems = new OrderLineItems(orderLineItems);
    this.state = APPROVAL_PENDING;
  }

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public DeliveryInformation getDeliveryInformation() {
    return deliveryInformation;
  }

  public Money getOrderTotal() {
    return orderLineItems.orderTotal();
  }

  public List<OrderDomainEvent> cancel() {
    switch (state) {
      case APPROVED:
        this.state = OrderState.CANCEL_PENDING;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> undoPendingCancel() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = OrderState.APPROVED;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> noteCancelled() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = OrderState.CANCELLED;
        return singletonList(new OrderCancelled());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> noteApproved() {
    switch (state) {
      case APPROVAL_PENDING:
        this.state = APPROVED;
        return singletonList(new OrderAuthorized());
      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }

  public List<OrderDomainEvent> noteRejected() {
    switch (state) {
      case APPROVAL_PENDING:
        this.state = REJECTED;
        return singletonList(new OrderRejected());

      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }


  public List<OrderDomainEvent> noteReversingAuthorization() {
    return null;
  }

  public ResultWithDomainEvents<LineItemQuantityChange, OrderDomainEvent> revise(OrderRevision orderRevision) {
    switch (state) {

      case APPROVED:
        LineItemQuantityChange change = orderLineItems.lineItemQuantityChange(orderRevision);
        if (change.newOrderTotal.isGreaterThanOrEqual(orderMinimum)) {
          throw new OrderMinimumNotMetException();
        }
        this.state = REVISION_PENDING;
        return new ResultWithDomainEvents<>(change, singletonList(new OrderRevisionProposed(orderRevision, change.currentOrderTotal, change.newOrderTotal)));

      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> rejectRevision() {
    switch (state) {
      case REVISION_PENDING:
        this.state = APPROVED;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> confirmRevision(OrderRevision orderRevision) {
    switch (state) {
      case REVISION_PENDING:
        LineItemQuantityChange licd = orderLineItems.lineItemQuantityChange(orderRevision);

        orderRevision.getDeliveryInformation().ifPresent(newDi -> this.deliveryInformation = newDi);

        if (orderRevision.getRevisedOrderLineItems() != null && orderRevision.getRevisedOrderLineItems().size() > 0) {
          orderLineItems.updateLineItems(orderRevision);
        }

        this.state = APPROVED;
        return singletonList(new OrderRevised(orderRevision, licd.currentOrderTotal, licd.newOrderTotal));
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }


  public Long getVersion() {
    return version;
  }

  public List<OrderLineItem> getLineItems() {
    return orderLineItems.getLineItems();
  }

  public OrderState getState() {
    return state;
  }

  public long getRestaurantId() {
    return restaurantId;
  }


  public Long getConsumerId() {
    return consumerId;
  }
}



// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/Order.java:Order.<init>
// Node: undoPendingCancel
// Node: noteCancelled
// Node: OrderCancelled
// Node: noteRejected
// Node: OrderRejected
// Node: rejectRevision
package net.chrisrichardson.ftgo.orderservice.domain;

public class RestaurantNotFoundException extends RuntimeException {
  public RestaurantNotFoundException(long restaurantId) {
    super("Restaurant not found with id " + restaurantId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/RestaurantNotFoundException.java:RestaurantNotFoundException.<init>
// Node: RestaurantNotFoundException
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;

import java.util.List;
import java.util.Optional;

public class OrderRevision {

  private Optional<DeliveryInformation> deliveryInformation = Optional.empty();
  private List<RevisedOrderLineItem> revisedOrderLineItems;

  private OrderRevision() {
  }

  public OrderRevision(Optional<DeliveryInformation> deliveryInformation, List<RevisedOrderLineItem> revisedOrderLineItems) {
    this.deliveryInformation = deliveryInformation;
    this.revisedOrderLineItems = revisedOrderLineItems;
  }

  public void setDeliveryInformation(Optional<DeliveryInformation> deliveryInformation) {
    this.deliveryInformation = deliveryInformation;
  }

  public Optional<DeliveryInformation> getDeliveryInformation() {
    return deliveryInformation;
  }

  public List<RevisedOrderLineItem> getRevisedOrderLineItems() {
    return revisedOrderLineItems;
  }

  public void setRevisedOrderLineItems(List<RevisedOrderLineItem> revisedOrderLineItems) {
    this.revisedOrderLineItems = revisedOrderLineItems;
  }
}


package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.sagas.orchestration.SagaInstanceFactory;
import io.micrometer.core.instrument.MeterRegistry;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.sagas.cancelorder.CancelOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.cancelorder.CancelOrderSagaData;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSagaState;
import net.chrisrichardson.ftgo.orderservice.sagas.reviseorder.ReviseOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.reviseorder.ReviseOrderSagaData;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.function.Function;

import static java.util.stream.Collectors.toList;

public class OrderService {

  private Logger logger = LoggerFactory.getLogger(getClass());

  private SagaInstanceFactory sagaInstanceFactory;

  private OrderRepository orderRepository;

  private RestaurantRepository restaurantRepository;

  private CreateOrderSaga createOrderSaga;

  private CancelOrderSaga cancelOrderSaga;

  private ReviseOrderSaga reviseOrderSaga;

  private OrderDomainEventPublisher orderAggregateEventPublisher;

  private Optional<MeterRegistry> meterRegistry;

  public OrderService(SagaInstanceFactory sagaInstanceFactory,
                      OrderRepository orderRepository,
                      DomainEventPublisher eventPublisher,
                      RestaurantRepository restaurantRepository,
                      CreateOrderSaga createOrderSaga,
                      CancelOrderSaga cancelOrderSaga,
                      ReviseOrderSaga reviseOrderSaga,
                      OrderDomainEventPublisher orderAggregateEventPublisher,
                      Optional<MeterRegistry> meterRegistry) {

    this.sagaInstanceFactory = sagaInstanceFactory;
    this.orderRepository = orderRepository;
    this.restaurantRepository = restaurantRepository;
    this.createOrderSaga = createOrderSaga;
    this.cancelOrderSaga = cancelOrderSaga;
    this.reviseOrderSaga = reviseOrderSaga;
    this.orderAggregateEventPublisher = orderAggregateEventPublisher;
    this.meterRegistry = meterRegistry;
  }

  @Transactional
  public Order createOrder(long consumerId, long restaurantId, DeliveryInformation deliveryInformation,
                           List<MenuItemIdAndQuantity> lineItems) {
    Restaurant restaurant = restaurantRepository.findById(restaurantId)
            .orElseThrow(() -> new RestaurantNotFoundException(restaurantId));

    List<OrderLineItem> orderLineItems = makeOrderLineItems(lineItems, restaurant);

    ResultWithDomainEvents<Order, OrderDomainEvent> orderAndEvents =
            Order.createOrder(consumerId, restaurant, deliveryInformation, orderLineItems);

    Order order = orderAndEvents.result;
    orderRepository.save(order);

    orderAggregateEventPublisher.publish(order, orderAndEvents.events);

    OrderDetails orderDetails = new OrderDetails(consumerId, restaurantId, orderLineItems, order.getOrderTotal());

    CreateOrderSagaState data = new CreateOrderSagaState(order.getId(), orderDetails);
    sagaInstanceFactory.create(createOrderSaga, data);

    meterRegistry.ifPresent(mr -> mr.counter("placed_orders").increment());

    return order;
  }


  private List<OrderLineItem> makeOrderLineItems(List<MenuItemIdAndQuantity> lineItems, Restaurant restaurant) {
    return lineItems.stream().map(li -> {
      MenuItem om = restaurant.findMenuItem(li.getMenuItemId()).orElseThrow(() -> new InvalidMenuItemIdException(li.getMenuItemId()));
      return new OrderLineItem(li.getMenuItemId(), om.getName(), om.getPrice(), li.getQuantity());
    }).collect(toList());
  }


  public Optional<Order> confirmChangeLineItemQuantity(Long orderId, OrderRevision orderRevision) {
    return orderRepository.findById(orderId).map(order -> {
      List<OrderDomainEvent> events = order.confirmRevision(orderRevision);
      orderAggregateEventPublisher.publish(order, events);
      return order;
    });
  }

  public void noteReversingAuthorization(Long orderId) {
    throw new UnsupportedOperationException();
  }

  @Transactional
  public Order cancel(Long orderId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
    CancelOrderSagaData sagaData = new CancelOrderSagaData(order.getConsumerId(), orderId, order.getOrderTotal());
    sagaInstanceFactory.create(cancelOrderSaga, sagaData);
    return order;
  }

  private Order updateOrder(long orderId, Function<Order, List<OrderDomainEvent>> updater) {
    return orderRepository.findById(orderId).map(order -> {
      orderAggregateEventPublisher.publish(order, updater.apply(order));
      return order;
    }).orElseThrow(() -> new OrderNotFoundException(orderId));
  }

  public void approveOrder(long orderId) {
    updateOrder(orderId, Order::noteApproved);
    meterRegistry.ifPresent(mr -> mr.counter("approved_orders").increment());
  }

  public void rejectOrder(long orderId) {
    updateOrder(orderId, Order::noteRejected);
    meterRegistry.ifPresent(mr -> mr.counter("rejected_orders").increment());
  }

  public void beginCancel(long orderId) {
    updateOrder(orderId, Order::cancel);
  }

  public void undoCancel(long orderId) {
    updateOrder(orderId, Order::undoPendingCancel);
  }

  public void confirmCancelled(long orderId) {
    updateOrder(orderId, Order::noteCancelled);
  }

  @Transactional
  public Order reviseOrder(long orderId, OrderRevision orderRevision) {
    Order order = orderRepository.findById(orderId).orElseThrow(() -> new OrderNotFoundException(orderId));
    ReviseOrderSagaData sagaData = new ReviseOrderSagaData(order.getConsumerId(), orderId, null, orderRevision);
    sagaInstanceFactory.create(reviseOrderSaga, sagaData);
    return order;
  }

  public Optional<RevisedOrder> beginReviseOrder(long orderId, OrderRevision revision) {
    return orderRepository.findById(orderId).map(order -> {
      ResultWithDomainEvents<LineItemQuantityChange, OrderDomainEvent> result = order.revise(revision);
      orderAggregateEventPublisher.publish(order, result.events);
      return new RevisedOrder(order, result.result);
    });
  }

  public void undoPendingRevision(long orderId) {
    updateOrder(orderId, Order::rejectRevision);
  }

  public void confirmRevision(long orderId, OrderRevision revision) {
    updateOrder(orderId, order -> order.confirmRevision(revision));
  }

  public void createMenu(long id, String name, List<MenuItem> menuItems) {
    Restaurant restaurant = new Restaurant(id, name, menuItems);
    restaurantRepository.save(restaurant);
  }

  public void reviseMenu(long id, List<MenuItem> menuItems) {
    restaurantRepository.findById(id).map(restaurant -> {
      List<OrderDomainEvent> events = restaurant.reviseMenu(menuItems);
      return restaurant;
    }).orElseThrow(RuntimeException::new);
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderService.java:OrderService.<init>
// Node: confirmChangeLineItemQuantity
package net.chrisrichardson.ftgo.orderservice;

public class TramCommandsAndEventsIntegrationData {

  private long now = System.currentTimeMillis();
  private String commandDispatcherId = "command-dispatcher-" + now;
  private String eventDispatcherId  = "event-dispatcher-" + now;

  private String consumerServiceCommandChannel = "consumerServiceCommandChannel-" + now;
  private String consumerAggregateDestination = "consumerAggregateDestination-" + now;

  private String restaurantServiceCommandChannel = "restaurantServiceCommandChannel-" + now;
  private String restaurantAggregateDestination = "restaurantAggregateDestination-" + now;
  private String acccountServiceCommandChannel  = "acccountServiceCommandChannel-" + now;
  private String acccountAggregateDestination  = "acccountAggregateDestination-" + now;

  public String getRestaurantServiceCommandChannel() {
    return restaurantServiceCommandChannel;
  }

  public String getConsumerAggregateDestination() {
    return consumerAggregateDestination;
  }
  public String getConsumerServiceCommandChannel() {
    return consumerServiceCommandChannel;
  }


  public String getCommandDispatcherId() {
    return commandDispatcherId;
  }


  public String getEventDispatcherId() {
    return eventDispatcherId;
  }

  public String getRestaurantAggregateDestination() {
    return restaurantAggregateDestination;
  }

  public String getAcccountServiceCommandChannel() {
    return acccountServiceCommandChannel;
  }

  public String getAcccountAggregateDestination() {
    return acccountAggregateDestination;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/test/java/net/chrisrichardson/ftgo/orderservice/TramCommandsAndEventsIntegrationData.java:TramCommandsAndEventsIntegrationData.<init>
package net.chrisrichardson.ftgo.orderservice;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import net.chrisrichardson.ftgo.orderservice.domain.DeliveryInformation;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;

import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_ID;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.CHICKEN_VINDALOO;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.CHICKEN_VINDALOO_PRICE;

public class OrderDetailsMother {

  public static long CONSUMER_ID = 1511300065921L;

  public static final int CHICKEN_VINDALOO_QUANTITY = 5;
  public static final MenuItemIdAndQuantity CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY = new MenuItemIdAndQuantity(RestaurantMother.CHICKEN_VINDALOO_MENU_ITEM_ID, CHICKEN_VINDALOO_QUANTITY);
  public static final List<MenuItemIdAndQuantity> CHICKEN_VINDALOO_MENU_ITEMS_AND_QUANTITIES = Collections.singletonList(CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY);

  public static List<OrderLineItem> chickenVindalooLineItems() {
    return Collections.singletonList(new OrderLineItem(CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY.getMenuItemId(),
            CHICKEN_VINDALOO,
            CHICKEN_VINDALOO_PRICE,
            CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY.getQuantity()));
  }

  public static final Money CHICKEN_VINDALOO_ORDER_TOTAL = CHICKEN_VINDALOO_PRICE.multiply(5);
  public static final OrderDetails CHICKEN_VINDALOO_ORDER_DETAILS = new OrderDetails(CONSUMER_ID, AJANTA_ID,
          chickenVindalooLineItems(), CHICKEN_VINDALOO_ORDER_TOTAL);

  public static long ORDER_ID = 99L;

  public static final OrderState CHICKEN_VINDALOO_ORDER_STATE = OrderState.APPROVAL_PENDING;

  public static final Address DELIVERY_ADDRESS = new Address("9 Amazing View", null, "Oakland", "CA", "94612");
  public static final LocalDateTime DELIVERY_TIME = LocalDateTime.now();
  public static final DeliveryInformation DELIVERY_INFORMATION = new DeliveryInformation(DELIVERY_TIME, DELIVERY_ADDRESS);

  private static Order makeAjantaOrder() {
    Order order = new Order(CONSUMER_ID, AJANTA_ID, new DeliveryInformation(DELIVERY_TIME, DELIVERY_ADDRESS), chickenVindalooLineItems());
    order.setId(ORDER_ID);
    return order;
  }

  public static Order CHICKEN_VINDALOO_ORDER = makeAjantaOrder();

}


// Node: makeAjantaOrder
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderAuthorized;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.junit.Before;
import org.junit.Test;

import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static java.util.Collections.singletonList;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.*;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.CHICKEN_VINDALOO_PRICE;
import static org.junit.Assert.assertEquals;

public class OrderTest {

  private ResultWithDomainEvents<Order, OrderDomainEvent> createResult;
  private Order order;

  @Before
  public void setUp() throws Exception {
    createResult = Order.createOrder(CONSUMER_ID, AJANTA_RESTAURANT, OrderDetailsMother.DELIVERY_INFORMATION, chickenVindalooLineItems());
    order = createResult.result;
  }

  @Test
  public void shouldCreateOrder() {
    assertEquals(singletonList(new OrderCreatedEvent(CHICKEN_VINDALOO_ORDER_DETAILS, OrderDetailsMother.DELIVERY_ADDRESS, RestaurantMother.AJANTA_RESTAURANT_NAME)), createResult.events);

    assertEquals(OrderState.APPROVAL_PENDING, order.getState());
    // ...
  }

  @Test
  public void shouldCalculateTotal() {
    assertEquals(CHICKEN_VINDALOO_PRICE.multiply(CHICKEN_VINDALOO_QUANTITY), order.getOrderTotal());
  }

  @Test
  public void shouldAuthorize() {
    List<OrderDomainEvent> events = order.noteApproved();
    assertEquals(singletonList(new OrderAuthorized()), events);
    assertEquals(OrderState.APPROVED, order.getState());
  }

  @Test
  public void shouldReviseOrder() {

    order.noteApproved();

    OrderRevision orderRevision = new OrderRevision(Optional.empty(), Collections.singletonList(new RevisedOrderLineItem(10, "1")));

    ResultWithDomainEvents<LineItemQuantityChange, OrderDomainEvent> result = order.revise(orderRevision);

    assertEquals(CHICKEN_VINDALOO_PRICE.multiply(10), result.result.getNewOrderTotal());

    order.confirmRevision(orderRevision);

    assertEquals(CHICKEN_VINDALOO_PRICE.multiply(10), order.getOrderTotal());
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


// Node: subscribe
import org.gradle.api.Plugin;
import org.gradle.api.Project;

public class WaitForMySqlPlugin implements Plugin<Project> {
  @Override
  public void apply(Project project) {
    project.getTasks().create("waitForMySql", WaitForMySql.class);
  }
}


// Node: getTasks
// Node: createRestaurant
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


// Node: makeRestaurantCreated
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


// Node: shouldSaveAndLoadDelivery
// Node: assertNull
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


// Node: shouldSaveAndLoad
// Node: getPlan
// Node: getActions
// Node: shouldFindAllAvailable
// Node: noteAvailable
// Node: noteUnavailable
// Node: anyMatch
// Node: shouldFindOrCreate
// Node: findOrCreateCourier
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


// Node: updateAvailability
package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryActionType;
import net.chrisrichardson.ftgo.common.Address;

import javax.persistence.Embeddable;
import javax.persistence.EnumType;
import javax.persistence.Enumerated;
import java.time.LocalDateTime;

@Embeddable
public class Action {

  @Enumerated(EnumType.STRING)
  private DeliveryActionType type;
  private Address address;
  private LocalDateTime time;

  protected long deliveryId;

  private Action() {
  }

  public Action(DeliveryActionType type, long deliveryId, Address address, LocalDateTime time) {
    this.type = type;
    this.deliveryId = deliveryId;
    this.address = address;
    this.time = time;
  }

  public boolean actionFor(long deliveryId) {
    return this.deliveryId == deliveryId;
  }

  public static Action makePickup(long deliveryId, Address pickupAddress, LocalDateTime pickupTime) {
    return new Action(DeliveryActionType.PICKUP, deliveryId, pickupAddress, pickupTime);
  }

  public static Action makeDropoff(long deliveryId, Address deliveryAddress, LocalDateTime deliveryTime) {
    return new Action(DeliveryActionType.DROPOFF, deliveryId, deliveryAddress, deliveryTime);
  }


  public DeliveryActionType getType() {
    return type;
  }

  public Address getAddress() {
    return address;
  }
}


package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.common.Address;

import javax.persistence.*;

@Entity
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  private Long id;

  private String restaurantName;
  private Address address;

  private Restaurant() {
  }

  public Restaurant(long restaurantId, String restaurantName, Address address) {
    this.id = restaurantId;
    this.restaurantName = restaurantName;
    this.address = address;
  }

  public static Restaurant create(long restaurantId, String restaurantName, Address address) {
    return new Restaurant(restaurantId, restaurantName, address);
  }

  public Address getAddress() {
    return address;
  }
}



package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.deliveryservice.api.web.ActionInfo;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryInfo;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryStatus;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Random;
import java.util.stream.Collectors;

public class DeliveryService {

  private RestaurantRepository restaurantRepository;
  private DeliveryRepository deliveryRepository;
  private CourierRepository courierRepository;
  private Random random = new Random();

  public DeliveryService(RestaurantRepository restaurantRepository, DeliveryRepository deliveryRepository, CourierRepository courierRepository) {
    this.restaurantRepository = restaurantRepository;
    this.deliveryRepository = deliveryRepository;
    this.courierRepository = courierRepository;
  }

  public void createRestaurant(long restaurantId, String restaurantName, Address address) {
    restaurantRepository.save(Restaurant.create(restaurantId, restaurantName, address));
  }

  public void createDelivery(long orderId, long restaurantId, Address deliveryAddress) {
    Restaurant restaurant = restaurantRepository.findById(restaurantId).get();
    deliveryRepository.save(Delivery.create(orderId, restaurantId, restaurant.getAddress(), deliveryAddress));
  }

  public void scheduleDelivery(long orderId, LocalDateTime readyBy) {
    Delivery delivery = deliveryRepository.findById(orderId).get();

    // Stupid implementation

    List<Courier> couriers = courierRepository.findAllAvailable();
    Courier courier = couriers.get(random.nextInt(couriers.size()));
    courier.addAction(Action.makePickup(delivery.getId(), delivery.getPickupAddress(), readyBy));
    courier.addAction(Action.makeDropoff(delivery.getId(), delivery.getDeliveryAddress(), readyBy.plusMinutes(30)));

    delivery.schedule(readyBy, courier.getId());

  }

  public void cancelDelivery(long orderId) {
    Delivery delivery = deliveryRepository.findById(orderId).get();
    Long assignedCourierId = delivery.getAssignedCourier();
    delivery.cancel();
    if (assignedCourierId != null) {
      Courier courier = courierRepository.findById(assignedCourierId).get();
      courier.cancelDelivery(delivery.getId());
    }

  }



  // notePickedUp
  // noteDelivered
  // noteLocation

  void noteAvailable(long courierId) {
    courierRepository.findOrCreateCourier(courierId).noteAvailable();
  }

  void noteUnavailable(long courierId) {
    courierRepository.findOrCreateCourier(courierId).noteUnavailable();
  }

  private Courier findOrCreateCourier(long courierId) {
    Courier courier = Courier.create(courierId);
    try {
      return courierRepository.save(courier);
    } catch (DuplicateKeyException e) {
      return courierRepository.findById(courierId).get();
    }
  }

  @Transactional
  public void updateAvailability(long courierId, boolean available) {
    if (available)
      noteAvailable(courierId);
    else
      noteUnavailable(courierId);
  }


  // getCourierRoute()

  @Transactional
  public Optional<DeliveryStatus> getDeliveryInfo(long deliveryId) {
    return deliveryRepository.findById(deliveryId).map(delivery -> {
      Long assignedCourier = delivery.getAssignedCourier();
      List<Action> courierActions = Collections.EMPTY_LIST;
      if (assignedCourier != null) {
        Courier courier = courierRepository.findById(assignedCourier).get();
        courierActions = courier.actionsForDelivery(deliveryId);
      }
      return makeDeliveryStatus(delivery, assignedCourier, courierActions);
    });
  }

  private DeliveryStatus makeDeliveryStatus(Delivery delivery, Long assignedCourier, List<Action> courierActions) {
    return new DeliveryStatus(makeDeliveryInfo(delivery), assignedCourier, courierActions.stream().map(action -> makeActionInfo(action)).collect(Collectors.toList()));
  }

  private DeliveryInfo makeDeliveryInfo(Delivery delivery) {
    return new DeliveryInfo(delivery.getId(), delivery.getState());
  }

  private ActionInfo makeActionInfo(Action action) {
    return new ActionInfo(action.getType());
  }
}


// Node: getCourierRoute
package net.chrisrichardson.ftgo.deliveryservice.domain;

import org.springframework.data.jpa.repository.Query;

import java.util.List;

public interface CustomCourierRepository {

  Courier findOrCreateCourier(long courierId);

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/domain/CustomCourierRepository.java:CustomCourierRepository.<init>
package net.chrisrichardson.ftgo.deliveryservice.domain;

import javax.persistence.ElementCollection;
import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;

public class Plan {

  @ElementCollection
  private List<Action> actions = new LinkedList<>();

  public void add(Action action) {
    actions.add(action);
  }

  public void removeDelivery(long deliveryId) {
    actions = actions.stream().filter(action -> !action.actionFor(deliveryId)).collect(Collectors.toList());
  }

  public List<Action> getActions() {
    return actions;
  }

  public List<Action> actionsForDelivery(long deliveryId) {
    return actions.stream().filter(action -> action.actionFor(deliveryId)).collect(Collectors.toList());
  }
}


package net.chrisrichardson.ftgo.deliveryservice.domain;

import org.springframework.beans.factory.annotation.Autowired;

import javax.persistence.EntityManager;
import java.util.List;

public class CustomCourierRepositoryImpl implements CustomCourierRepository {

  @Autowired
  private EntityManager entityManager;

//  @Override
//  public List<Courier> findAllAvailable() {
//    return entityManager.createQuery("").getResultList();
//  }

  @Override
  public Courier findOrCreateCourier(long courierId) {
    Courier courier = entityManager.find(Courier.class, courierId);
    if (courier == null) {
      courier = Courier.create(courierId);
      entityManager.persist(courier);
    }
    return courier;
  }
}


// Node: persist
package net.chrisrichardson.ftgo.deliveryservice.domain;

import javax.persistence.*;
import java.util.List;

@Entity
@Access(AccessType.FIELD)
public class Courier {

  @Id
  private long id;

  @Embedded
  private Plan plan;

  private Boolean available;

  private Courier() {
  }

  public Courier(long courierId) {
    this.id = courierId;
    this.plan = new Plan();
  }

  public static Courier create(long courierId) {
    return new Courier(courierId);
  }

  public void noteAvailable() {
    this.available = true;

  }

  public void addAction(Action action) {
    plan.add(action);
  }

  public void cancelDelivery(long deliveryId) {
    plan.removeDelivery(deliveryId);
  }

  public boolean isAvailable() {
    return available;
  }

  public Plan getPlan() {
    return plan;
  }

  public long getId() {
    return id;
  }

  public void noteUnavailable() {
    this.available = false;
  }

  public List<Action> actionsForDelivery(long deliveryId) {
    return plan.actionsForDelivery(deliveryId);
  }
}


package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryState;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Access(AccessType.FIELD)
public class Delivery {

  @Id
  private Long id;

  @Embedded
  @AttributeOverrides({
          @AttributeOverride(name="street1", column = @Column(name="pickup_street1")),
          @AttributeOverride(name="street2", column = @Column(name="pickup_street2")),
          @AttributeOverride(name="city", column = @Column(name="pickup_city")),
          @AttributeOverride(name="state", column = @Column(name="pickup_state")),
          @AttributeOverride(name="zip", column = @Column(name="pickup_zip")),
  }
  )
  private Address pickupAddress;

  @Enumerated(EnumType.STRING)
  private DeliveryState state;

  private long restaurantId;
  private LocalDateTime pickUpTime;

  @Embedded
  @AttributeOverrides({
          @AttributeOverride(name="street1", column = @Column(name="delivery_street1")),
          @AttributeOverride(name="street2", column = @Column(name="delivery_street2")),
          @AttributeOverride(name="city", column = @Column(name="delivery_city")),
          @AttributeOverride(name="state", column = @Column(name="delivery_state")),
          @AttributeOverride(name="zip", column = @Column(name="delivery_zip")),
  }
  )

  private Address deliveryAddress;
  private LocalDateTime deliveryTime;

  private Long assignedCourier;
  private LocalDateTime readyBy;

  private Delivery() {
  }

  public Delivery(long orderId, long restaurantId, Address pickupAddress, Address deliveryAddress) {
    this.id = orderId;
    this.pickupAddress = pickupAddress;
    this.state = DeliveryState.PENDING;
    this.restaurantId = restaurantId;
    this.deliveryAddress = deliveryAddress;
  }

  public static Delivery create(long orderId, long restaurantId, Address pickupAddress, Address deliveryAddress) {
    return new Delivery(orderId, restaurantId, pickupAddress, deliveryAddress);
  }

  public void schedule(LocalDateTime readyBy, long assignedCourier) {
    this.readyBy = readyBy;
    this.assignedCourier = assignedCourier;
    this.state = DeliveryState.SCHEDULED;

  }

  public void cancel() {
    this.state = DeliveryState.CANCELLED;
    this.assignedCourier = null;
  }


  public long getId() {
    return id;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public Address getDeliveryAddress() {
    return deliveryAddress;
  }

  public Address getPickupAddress() {
    return pickupAddress;
  }

  public DeliveryState getState() {
    return state;
  }

  public Long getAssignedCourier() {
    return assignedCourier;
  }
}


package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryActionType;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryState;
import org.junit.Before;
import org.junit.Test;
import org.mockito.ArgumentCaptor;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static org.junit.Assert.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.verify;

public class DeliveryServiceTest {

  private static final long COURIER_ID = 101L;
  private static final long ORDER_ID = 102L;
  private static final long RESTAURANT_ID = 103L;
  private static final LocalDateTime READY_BY = LocalDateTime.now();

  private Courier courier;

  private RestaurantRepository restaurantRepository;
  private DeliveryRepository deliveryRepository;
  private CourierRepository courierRepository;
  private DeliveryService deliveryService;
  private Restaurant restaurant;

  @Before
  public void setUp() {
    this.restaurantRepository = mock(RestaurantRepository.class);
    this.deliveryRepository = mock(DeliveryRepository.class);
    this.courierRepository = mock(CourierRepository.class);
    this.courier = Courier.create(COURIER_ID);
    this.restaurant = mock(Restaurant.class);

    this.deliveryService = new DeliveryService(restaurantRepository, deliveryRepository, courierRepository);

  }

  @Test
  public void shouldCreateCourier() {
    when(courierRepository.findOrCreateCourier(COURIER_ID)).thenReturn(courier);
    deliveryService.noteAvailable(COURIER_ID);
    assertTrue(courier.isAvailable());
  }

  // should Create Restaurant

  @Test
  public void shouldCreateDelivery() {

    when(restaurantRepository.findById(RESTAURANT_ID)).thenReturn(Optional.of(restaurant));
    when(restaurant.getAddress()).thenReturn(DeliveryServiceTestData.PICKUP_ADDRESS);
    deliveryService.createDelivery(ORDER_ID, RESTAURANT_ID, DeliveryServiceTestData.DELIVERY_ADDRESS);

    ArgumentCaptor<Delivery> arg = ArgumentCaptor.forClass(Delivery.class);
    verify(deliveryRepository).save(arg.capture());

    Delivery delivery  = arg.getValue();
    assertNotNull(delivery);

    assertEquals(ORDER_ID, delivery.getId());
    assertEquals(DeliveryState.PENDING, delivery.getState());
    assertEquals(RESTAURANT_ID, delivery.getRestaurantId());
    assertEquals(DeliveryServiceTestData.PICKUP_ADDRESS, delivery.getPickupAddress());
    assertEquals(DeliveryServiceTestData.DELIVERY_ADDRESS, delivery.getDeliveryAddress());

  }

  @Test
  public void shouldScheduleDelivery() {
    Delivery delivery = Delivery.create(ORDER_ID, RESTAURANT_ID, DeliveryServiceTestData.PICKUP_ADDRESS, DeliveryServiceTestData.DELIVERY_ADDRESS);

    when(deliveryRepository.findById(ORDER_ID)).thenReturn(Optional.of(delivery));
    when(courierRepository.findAllAvailable()).thenReturn(Collections.singletonList(courier));

    deliveryService.scheduleDelivery(ORDER_ID, READY_BY);

    assertEquals(DeliveryState.SCHEDULED, delivery.getState());
    assertSame(courier.getId(), delivery.getAssignedCourier());

    List<Action> actions = courier.getPlan().getActions();
    assertEquals(2, actions.size());
    assertEquals(DeliveryActionType.PICKUP, actions.get(0).getType());
    assertEquals(DeliveryServiceTestData.PICKUP_ADDRESS, actions.get(0).getAddress());
    assertEquals(DeliveryActionType.DROPOFF, actions.get(1).getType());
    assertEquals(DeliveryServiceTestData.DELIVERY_ADDRESS, actions.get(1).getAddress());
  }

}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/test/java/net/chrisrichardson/ftgo/deliveryservice/domain/DeliveryServiceTest.java:DeliveryServiceTest.<init>
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



// Node: ticketAcceptedEvent
// Node: Ticket
// Node: confirmReviseTicket
package net.chrisrichardson.ftgo.kitchenservice.domain;


import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketDomainEvent;

public class TicketCreatedEvent implements TicketDomainEvent {
  public TicketCreatedEvent(Long id, TicketDetails details) {

  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/TicketCreatedEvent.java:TicketCreatedEvent.<init>
// Node: TicketCreatedEvent
package net.chrisrichardson.ftgo.kitchenservice.domain;

public class TicketNotFoundException extends RuntimeException {
  public TicketNotFoundException(long orderId) {
    super("Ticket not found: " + orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/TicketNotFoundException.java:TicketNotFoundException.<init>
// Node: TicketNotFoundException
package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketDomainEvent;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public class KitchenService {

  @Autowired
  private TicketRepository ticketRepository;

  @Autowired
  private TicketDomainEventPublisher domainEventPublisher;

  @Autowired
  private RestaurantRepository restaurantRepository;

  public void createMenu(long id, RestaurantMenu menu) {
    Restaurant restaurant = new Restaurant(id, menu.getMenuItems());
    restaurantRepository.save(restaurant);
  }

  public void reviseMenu(long ticketId, RestaurantMenu revisedMenu) {
    Restaurant restaurant = restaurantRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    restaurant.reviseMenu(revisedMenu);
  }

  public Ticket createTicket(long restaurantId, Long ticketId, TicketDetails ticketDetails) {
    ResultWithDomainEvents<Ticket, TicketDomainEvent> rwe = Ticket.create(restaurantId, ticketId, ticketDetails);
    ticketRepository.save(rwe.result);
    domainEventPublisher.publish(rwe.result, rwe.events);
    return rwe.result;
  }

  @Transactional
  public void accept(long ticketId, LocalDateTime readyBy) {
    Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    List<TicketDomainEvent> events = ticket.accept(readyBy);
    domainEventPublisher.publish(ticket, events);
  }

  public void confirmCreateTicket(Long ticketId) {
    Ticket ro = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    List<TicketDomainEvent> events = ro.confirmCreate();
    domainEventPublisher.publish(ro, events);
  }

  public void cancelCreateTicket(Long ticketId) {
    Ticket ro = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    List<TicketDomainEvent> events = ro.cancelCreate();
    domainEventPublisher.publish(ro, events);
  }


  public void cancelTicket(long restaurantId, long ticketId) {
    Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    // TODO - verify restaurant id
    List<TicketDomainEvent> events = ticket.cancel();
    domainEventPublisher.publish(ticket, events);
  }


  public void confirmCancelTicket(long restaurantId, long ticketId) {
    Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    // TODO - verify restaurant id
    List<TicketDomainEvent> events = ticket.confirmCancel();
    domainEventPublisher.publish(ticket, events);
  }

  public void undoCancel(long restaurantId, long ticketId) {
    Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    // TODO - verify restaurant id
    List<TicketDomainEvent> events = ticket.undoCancel();
    domainEventPublisher.publish(ticket, events);

  }

  public void beginReviseOrder(long restaurantId, Long ticketId, List<RevisedOrderLineItem> revisedOrderLineItems) {
    Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    // TODO - verify restaurant id
    List<TicketDomainEvent> events = ticket.beginReviseOrder(revisedOrderLineItems);
    domainEventPublisher.publish(ticket, events);

  }

  public void undoBeginReviseOrder(long restaurantId, Long ticketId) {
    Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    // TODO - verify restaurant id
    List<TicketDomainEvent> events = ticket.undoBeginReviseOrder();
    domainEventPublisher.publish(ticket, events);
  }

  public void confirmReviseTicket(long restaurantId, long ticketId, List<RevisedOrderLineItem> revisedOrderLineItems) {
    Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException(ticketId));
    // TODO - verify restaurant id
    List<TicketDomainEvent> events = ticket.confirmReviseTicket(revisedOrderLineItems);
    domainEventPublisher.publish(ticket, events);
  }


  // ...
}


// Node: confirmCreate
// Node: cancelCreate
package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.NotYetImplementedException;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;
import net.chrisrichardson.ftgo.common.UnsupportedStateTransitionException;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketLineItem;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketAcceptedEvent;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketCancelled;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketDomainEvent;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static java.util.Collections.emptyList;
import static java.util.Collections.singletonList;

@Entity
@Table(name = "tickets")
@Access(AccessType.FIELD)
public class Ticket {

  @Id
  private Long id;

  @Enumerated(EnumType.STRING)
  private TicketState state;

  private TicketState previousState;

  private Long restaurantId;

  @ElementCollection
  @CollectionTable(name = "ticket_line_items")
  private List<TicketLineItem> lineItems;

  private LocalDateTime readyBy;
  private LocalDateTime acceptTime;
  private LocalDateTime preparingTime;
  private LocalDateTime pickedUpTime;
  private LocalDateTime readyForPickupTime;

  public static ResultWithDomainEvents<Ticket, TicketDomainEvent> create(long restaurantId, Long id, TicketDetails details) {
    return new ResultWithDomainEvents<>(new Ticket(restaurantId, id, details));
  }

  private Ticket() {
  }

  public Ticket(long restaurantId, Long id, TicketDetails details) {
    this.restaurantId = restaurantId;
    this.id = id;
    this.state = TicketState.CREATE_PENDING;
    this.lineItems = details.getLineItems();
  }

  public List<TicketDomainEvent> confirmCreate() {
    switch (state) {
      case CREATE_PENDING:
        state = TicketState.AWAITING_ACCEPTANCE;
        return singletonList(new TicketCreatedEvent(id, new TicketDetails()));
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> cancelCreate() {
    throw new NotYetImplementedException();
  }


  public List<TicketDomainEvent> accept(LocalDateTime readyBy) {
    switch (state) {
      case AWAITING_ACCEPTANCE:
        // Verify that readyBy is in the futurestate = TicketState.ACCEPTED;
        this.acceptTime = LocalDateTime.now();
        if (!acceptTime.isBefore(readyBy))
          throw new IllegalArgumentException(String.format("readyBy %s is not after now %s", readyBy, acceptTime));
        this.readyBy = readyBy;
        return singletonList(new TicketAcceptedEvent(readyBy));
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  // TODO reject()

  // TODO cancel()

  public List<TicketDomainEvent> preparing() {
    switch (state) {
      case ACCEPTED:
        this.state = TicketState.PREPARING;
        this.preparingTime = LocalDateTime.now();
        return singletonList(new TicketPreparationStartedEvent());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> readyForPickup() {
    switch (state) {
      case PREPARING:
        this.state = TicketState.READY_FOR_PICKUP;
        this.readyForPickupTime = LocalDateTime.now();
        return singletonList(new TicketPreparationCompletedEvent());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> pickedUp() {
    switch (state) {
      case READY_FOR_PICKUP:
        this.state = TicketState.PICKED_UP;
        this.pickedUpTime = LocalDateTime.now();
        return singletonList(new TicketPickedUpEvent());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public void changeLineItemQuantity() {
    switch (state) {
      case AWAITING_ACCEPTANCE:
        // TODO
        break;
      case PREPARING:
        // TODO - too late
        break;
      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }

  public List<TicketDomainEvent> cancel() {
    switch (state) {
      case AWAITING_ACCEPTANCE:
      case ACCEPTED:
        this.previousState = state;
        this.state = TicketState.CANCEL_PENDING;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public Long getId() {
    return id;
  }

  public List<TicketDomainEvent> confirmCancel() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = TicketState.CANCELLED;
        return singletonList(new TicketCancelled());
      default:
        throw new UnsupportedStateTransitionException(state);

    }
  }
  public List<TicketDomainEvent> undoCancel() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = this.previousState;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);

    }
  }

  public List<TicketDomainEvent> beginReviseOrder(List<RevisedOrderLineItem> revisedOrderLineItems) {
    switch (state) {
      case AWAITING_ACCEPTANCE:
      case ACCEPTED:
        this.previousState = state;
        this.state = TicketState.REVISION_PENDING;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> undoBeginReviseOrder() {
    switch (state) {
      case REVISION_PENDING:
        this.state = this.previousState;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> confirmReviseTicket(List<RevisedOrderLineItem> revisedOrderLineItems) {
    switch (state) {
      case REVISION_PENDING:
        this.state = this.previousState;
        return singletonList(new TicketRevised());
      default:
        throw new UnsupportedStateTransitionException(state);

    }
  }
}


// Node: NotYetImplementedException
// Node: isBefore
// Node: reject
// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/Ticket.java:Ticket.preparing
// Node: preparing
// Node: TicketPreparationStartedEvent
// Node: readyForPickup
// Node: TicketPreparationCompletedEvent
// Node: pickedUp
// Node: TicketPickedUpEvent
// Node: changeLineItemQuantity
// Node: TicketCancelled
// Node: TicketRevised
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


// Node: shouldCreateTicket
package net.chrisrichardson.ftgo.consumerservice.domain;

import io.eventuate.tram.events.publisher.ResultWithEvents;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.PersonName;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "consumers")
@Access(AccessType.FIELD)
public class Consumer {

  @Id
  @GeneratedValue
  private Long id;

  @Embedded
  private PersonName name;

  private Consumer() {
  }

  public Consumer(PersonName name) {
    this.name = name;
  }


  public void validateOrderByConsumer(Money orderTotal) {
    // implement some business logic
  }

  public Long getId() {
    return id;
  }

  public PersonName getName() {
    return name;
  }

  public static ResultWithEvents<Consumer> create(PersonName name) {
    return new ResultWithEvents<>(new Consumer(name), new ConsumerCreated());
  }
}


// Node: validateOrderByConsumer
package net.chrisrichardson.ftgo.consumerservice.domain;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.events.publisher.ResultWithEvents;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.PersonName;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

public class ConsumerService {

  @Autowired
  private ConsumerRepository consumerRepository;

  @Autowired
  private DomainEventPublisher domainEventPublisher;

  public void validateOrderForConsumer(long consumerId, Money orderTotal) {
    Optional<Consumer> consumer = consumerRepository.findById(consumerId);
    consumer.orElseThrow(ConsumerNotFoundException::new).validateOrderByConsumer(orderTotal);
  }

  @Transactional
  public ResultWithEvents<Consumer> create(PersonName name) {
    ResultWithEvents<Consumer> rwe = Consumer.create(name);
    consumerRepository.save(rwe.result);
    domainEventPublisher.publish(Consumer.class, rwe.result.getId(), rwe.events);
    return rwe;
  }

  public Optional<Consumer> findById(long consumerId) {
    return consumerRepository.findById(consumerId);
  }
}


