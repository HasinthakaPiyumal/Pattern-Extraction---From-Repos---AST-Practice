// Cluster 2

// Node: get
package net.chrisrichardson.ftgo.orderservice.api.web;

import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;

import java.util.List;

public class ReviseOrderRequest {
  private List<RevisedOrderLineItem> revisedOrderLineItems;

  private ReviseOrderRequest() {
  }

  public ReviseOrderRequest(List<RevisedOrderLineItem> revisedOrderLineItems) {
    this.revisedOrderLineItems = revisedOrderLineItems;
  }

  public List<RevisedOrderLineItem> getRevisedOrderLineItems() {
    return revisedOrderLineItems;
  }

  public void setRevisedOrderLineItems(List<RevisedOrderLineItem> revisedOrderLineItems) {
    this.revisedOrderLineItems = revisedOrderLineItems;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service-api/src/main/java/net/chrisrichardson/ftgo/orderservice/api/web/ReviseOrderRequest.java:ReviseOrderRequest.<init>
// Node: ReviseOrderRequest
package net.chrisrichardson.ftgo.orderservice.api.web;

import net.chrisrichardson.ftgo.common.Address;

import java.time.LocalDateTime;
import java.util.List;

public class CreateOrderRequest {

  private long restaurantId;
  private long consumerId;
  private LocalDateTime deliveryTime;
  private List<LineItem> lineItems;
  private Address deliveryAddress;

  public CreateOrderRequest(long consumerId, long restaurantId, Address deliveryAddress, LocalDateTime deliveryTime, List<LineItem> lineItems) {
    this.restaurantId = restaurantId;
    this.consumerId = consumerId;
    this.deliveryAddress = deliveryAddress;
    this.deliveryTime = deliveryTime;
    this.lineItems = lineItems;

  }

  private CreateOrderRequest() {
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

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  public List<LineItem> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<LineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public Address getDeliveryAddress() {
    return deliveryAddress;
  }

  public void setDeliveryAddress(Address deliveryAddress) {
    this.deliveryAddress = deliveryAddress;
  }

  public LocalDateTime getDeliveryTime() {
    return deliveryTime;
  }

  public void setDeliveryTime(LocalDateTime deliveryTime) {
    this.deliveryTime = deliveryTime;
  }

  public static class LineItem {

    private String menuItemId;
    private int quantity;

    private LineItem() {
    }

    public LineItem(String menuItemId, int quantity) {
      this.menuItemId = menuItemId;

      this.quantity = quantity;
    }

    public String getMenuItemId() {
      return menuItemId;
    }

    public int getQuantity() {
      return quantity;
    }

    public void setQuantity(int quantity) {
      this.quantity = quantity;
    }

    public void setMenuItemId(String menuItemId) {
      this.menuItemId = menuItemId;

    }

  }


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service-api/src/main/java/net/chrisrichardson/ftgo/orderservice/api/web/CreateOrderRequest.java:CreateOrderRequest.<init>
// Node: CreateOrderRequest
// Node: LineItem
// Node: assertPresent
package net.chrisrichardson.ftgo.kitchenservice.api;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class CreateTicketReply {
  private long ticketId;

  private CreateTicketReply() {
  }

  public CreateTicketReply(long ticketId) {

    this.ticketId = ticketId;
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

  public void setTicketId(long ticketId) {
    this.ticketId = ticketId;
  }

  public long getTicketId() {
    return ticketId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/CreateTicketReply.java:CreateTicketReply.<init>
// Node: CreateTicketReply
package net.chrisrichardson.ftgo.kitchenservice.api.web;

import java.time.LocalDateTime;

public class TicketAcceptance {
  private LocalDateTime readyBy;

  public TicketAcceptance() {
  }

  public TicketAcceptance(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }

  public LocalDateTime getReadyBy() {
    return readyBy;
  }

  public void setReadyBy(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/web/TicketAcceptance.java:TicketAcceptance.<init>
// Node: TicketAcceptance
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/CreateRestaurantRequest.java:CreateRestaurantRequest.<init>
// Node: CreateRestaurantRequest
// Node: assertEquals
// Node: statusCode
// Node: path
// Node: contentType
// Node: body
// Node: post
// Node: verify
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/CreateRestaurantRequest.java:CreateRestaurantRequest.<init>
package net.chrisrichardson.ftgo.common;

public class PersonName {
  private String firstName;
  private String lastName;

  private PersonName() {
  }

  public PersonName(String firstName, String lastName) {
    this.firstName = firstName;
    this.lastName = lastName;
  }

  public String getFirstName() {
    return firstName;
  }

  public String getLastName() {
    return lastName;
  }
}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-common/src/main/java/net/chrisrichardson/ftgo/common/PersonName.java:PersonName.<init>
// Node: PersonName
// Node: of
// Node: eventually
// Node: setup
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

// Node: shouldFindOrder
// Node: findOrder
// Node: shouldIgnoreDuplicateAdd
// Node: format
// Node: getValue
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


// Node: shouldHandleOrderCreatedEvent
// Node: when
// Node: any
// Node: thenReturn
// Node: trigger
// Node: forClass
// Node: capture
package net.chrisrichardson.ftgo.cqrs.orderhistory.web;

import io.eventuate.common.json.mapper.JSonMapper;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.Order;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.test.web.servlet.setup.StandaloneMockMvcBuilder;

import java.util.Optional;

import static io.restassured.module.mockmvc.RestAssuredMockMvc.given;
import static org.hamcrest.CoreMatchers.equalTo;
import static org.junit.Assert.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class OrderHistoryControllerTest {

  private OrderHistoryDao orderHistoryDao;
  private OrderHistoryController orderHistoryController;

  @Before
  public void setUp() {
    orderHistoryDao = mock(OrderHistoryDao.class);
    orderHistoryController = new OrderHistoryController(orderHistoryDao);
  }

  @Test
  public void testGetOrder() {
    when(orderHistoryDao.findOrder("1")).thenReturn(Optional.of(new Order("1", null, null, null, null, 101L, "Ajanta")));

    given().
            standaloneSetup(configureControllers(orderHistoryController)).
            when().
            get("/orders/1").
            then().
            statusCode(200).
            body("restaurantName", equalTo("Ajanta"))
    ;

  }

  // TODO move to test library

  private StandaloneMockMvcBuilder configureControllers(Object... controllers) {
    CommonJsonMapperInitializer.registerMoneyModule();
    MappingJackson2HttpMessageConverter converter = new MappingJackson2HttpMessageConverter(JSonMapper.objectMapper);
    return MockMvcBuilders.standaloneSetup(controllers).setMessageConverters(converter);
  }

}

// Node: testGetOrder
// Node: given
// Node: standaloneSetup
// Node: configureControllers
// Node: then
// Node: equalTo
// Node: MappingJackson2HttpMessageConverter
// Node: setMessageConverters
package net.chrisrichardson.ftgo.deliveryservice.api.web;

public class CourierAvailability {

  private boolean available;

  public CourierAvailability() {
  }

  public CourierAvailability(boolean available) {
    this.available = available;
  }

  public boolean isAvailable() {
    return available;
  }

  public void setAvailable(boolean available) {
    this.available = available;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service-api/src/main/java/net/chrisrichardson/ftgo/deliveryservice/api/web/CourierAvailability.java:CourierAvailability.<init>
// Node: CourierAvailability
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


// Node: baseUrl
// Node: EnableJpaRepositories
// Node: EntityScan
// Node: Given
// Node: useConsumer
// Node: forChannel
// Node: replyWith
// Node: a
// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/component-test/java/net/chrisrichardson/ftgo/orderservice/cucumber/OrderServiceComponentTestStepDefinitions.java:OrderServiceComponentTestStepDefinitions.useCreditCard
// Node: useCreditCard
// Node: replyWithSuccess
// Node: replyWithFailure
// Node: restaurantAcceptsOrder
// Node: makeAjantaRestaurantCreatedEvent
// Node: When
// Node: placeOrder
// Node: Then
// Node: be
// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/component-test/java/net/chrisrichardson/ftgo/orderservice/cucumber/OrderServiceComponentTestStepDefinitions.java:OrderServiceComponentTestStepDefinitions.theOrderShouldBeInState
// Node: theOrderShouldBeInState
// Node: extract
// Node: verifyCommandReceived
// Node: And
// Node: an
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


// Node: shouldCreateOrder
// Node: createOrder
package net.chrisrichardson.ftgo.orderservice.contract;

import io.eventuate.common.json.mapper.JSonMapper;
import io.restassured.module.mockmvc.RestAssuredMockMvc;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.domain.OrderRepository;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.orderservice.web.OrderController;
import org.junit.Before;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.test.web.servlet.setup.StandaloneMockMvcBuilder;

import java.util.Optional;

import static java.util.Optional.empty;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public abstract class HttpBase {

  private StandaloneMockMvcBuilder controllers(Object... controllers) {
    CommonJsonMapperInitializer.registerMoneyModule();
    MappingJackson2HttpMessageConverter converter = new MappingJackson2HttpMessageConverter(JSonMapper.objectMapper);
    return MockMvcBuilders.standaloneSetup(controllers).setMessageConverters(converter);
  }

  @Before
  public void setup() {
    OrderService orderService = mock(OrderService.class);
    OrderRepository orderRepository = mock(OrderRepository.class);
    OrderController orderController = new OrderController(orderService, orderRepository);

    when(orderRepository.findById(OrderDetailsMother.ORDER_ID)).thenReturn(Optional.of(OrderDetailsMother.CHICKEN_VINDALOO_ORDER));
    when(orderRepository.findById(555L)).thenReturn(empty());
    RestAssuredMockMvc.standaloneSetup(controllers(orderController));

  }
}

// Node: controllers
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

package net.chrisrichardson.ftgo.orderservice.web;

import io.eventuate.common.json.mapper.JSonMapper;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.domain.OrderRepository;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.test.web.servlet.setup.StandaloneMockMvcBuilder;

import java.util.Optional;

import static io.restassured.module.mockmvc.RestAssuredMockMvc.given;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER_TOTAL;
import static org.hamcrest.CoreMatchers.equalTo;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

public class OrderControllerTest {

  private OrderService orderService;
  private OrderRepository orderRepository;
  private OrderController orderController;

  @Before
  public void setUp() {
    orderService = mock(OrderService.class);
    orderRepository = mock(OrderRepository.class);
    orderController = new OrderController(orderService, orderRepository);
  }


  @Test
  public void shouldFindOrder() {

    when(orderRepository.findById(1L)).thenReturn(Optional.of(CHICKEN_VINDALOO_ORDER));

    given().
            standaloneSetup(configureControllers(orderController)).
    when().
            get("/orders/1").
    then().
            statusCode(200).
            body("orderId", equalTo(new Long(OrderDetailsMother.ORDER_ID).intValue())).
            body("state", equalTo(OrderDetailsMother.CHICKEN_VINDALOO_ORDER_STATE.name())).
            body("orderTotal", equalTo(CHICKEN_VINDALOO_ORDER_TOTAL.asString()))
    ;
  }

  @Test
  public void shouldFindNotOrder() {
    when(orderRepository.findById(1L)).thenReturn(Optional.empty());

    given().
            standaloneSetup(configureControllers(new OrderController(orderService, orderRepository))).
    when().
            get("/orders/1").
    then().
            statusCode(404)
    ;
  }

  private StandaloneMockMvcBuilder configureControllers(Object... controllers) {
    CommonJsonMapperInitializer.registerMoneyModule();
    MappingJackson2HttpMessageConverter converter = new MappingJackson2HttpMessageConverter(JSonMapper.objectMapper);
    return MockMvcBuilders.standaloneSetup(controllers).setMessageConverters(converter);
  }

}

// Node: name
// Node: shouldFindNotOrder
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.sagas.orchestration.SagaInstanceFactory;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.sagas.cancelorder.CancelOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSagaState;
import net.chrisrichardson.ftgo.orderservice.sagas.reviseorder.ReviseOrderSaga;
import org.junit.Before;
import org.junit.Test;

import java.util.Collections;
import java.util.Optional;

import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_MENU_ITEMS_AND_QUANTITIES;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER_DETAILS;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CONSUMER_ID;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.ORDER_ID;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_ID;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT;
import static org.mockito.Matchers.same;
import static org.mockito.Mockito.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

public class OrderServiceTest {

  private OrderService orderService;
  private OrderRepository orderRepository;
  private DomainEventPublisher eventPublisher;
  private RestaurantRepository restaurantRepository;
  private SagaInstanceFactory sagaInstanceFactory;
  private CreateOrderSaga createOrderSaga;
  private CancelOrderSaga cancelOrderSaga;
  private ReviseOrderSaga reviseOrderSaga;
  private OrderDomainEventPublisher orderAggregateEventPublisher;

  @Before
  public void setup() {
    sagaInstanceFactory = mock(SagaInstanceFactory.class);
    orderRepository = mock(OrderRepository.class);
    eventPublisher = mock(DomainEventPublisher.class);
    restaurantRepository = mock(RestaurantRepository.class);
    createOrderSaga = mock(CreateOrderSaga.class);
    cancelOrderSaga = mock(CancelOrderSaga.class);
    reviseOrderSaga = mock(ReviseOrderSaga.class);

    // Mock DomainEventPublisher AND use the real OrderDomainEventPublisher

    orderAggregateEventPublisher = mock(OrderDomainEventPublisher.class);

    orderService = new OrderService(sagaInstanceFactory, orderRepository, eventPublisher, restaurantRepository,
            createOrderSaga, cancelOrderSaga, reviseOrderSaga, orderAggregateEventPublisher, Optional.empty());
  }


  @Test
  public void shouldCreateOrder() {
    when(restaurantRepository.findById(AJANTA_ID)).thenReturn(Optional.of(AJANTA_RESTAURANT));
    when(orderRepository.save(any(Order.class))).then(invocation -> {
      Order order = (Order) invocation.getArguments()[0];
      order.setId(ORDER_ID);
      return order;
    });

    Order order = orderService.createOrder(CONSUMER_ID, AJANTA_ID, OrderDetailsMother.DELIVERY_INFORMATION, CHICKEN_VINDALOO_MENU_ITEMS_AND_QUANTITIES);

    verify(orderRepository).save(same(order));

    verify(orderAggregateEventPublisher).publish(order,
            Collections.singletonList(new OrderCreatedEvent(CHICKEN_VINDALOO_ORDER_DETAILS, OrderDetailsMother.DELIVERY_ADDRESS, RestaurantMother.AJANTA_RESTAURANT_NAME)));

    verify(sagaInstanceFactory).create(createOrderSaga, new CreateOrderSagaState(ORDER_ID, CHICKEN_VINDALOO_ORDER_DETAILS));
  }

  // TODO write tests for other methods

}

// Node: getArguments
// Node: same
package net.chrisrichardson.ftgo.orderservice.messaging;

import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import org.junit.Before;
import org.junit.Test;

import static io.eventuate.tram.testing.DomainEventHandlerUnitTestSupport.given;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_ID;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT_NAME;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;

public class OrderEventConsumerTest {

  private OrderService orderService;
  private OrderEventConsumer orderEventConsumer;

  @Before
  public void setUp() {
    orderService = mock(OrderService.class);
    orderEventConsumer = new OrderEventConsumer(orderService);
  }

  @Test
  public void shouldCreateMenu() {

    CommonJsonMapperInitializer.registerMoneyModule();

    given().
            eventHandlers(orderEventConsumer.domainEventHandlers()).
    when().
            aggregate("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant", AJANTA_ID).
            publishes(RestaurantMother.makeAjantaRestaurantCreatedEvent()).
    then().
       verify(() -> {
         verify(orderService).createMenu(AJANTA_ID, AJANTA_RESTAURANT_NAME, RestaurantMother.AJANTA_RESTAURANT_MENU_ITEMS);
       })
    ;

  }

}

// Node: shouldCreateMenu
// Node: eventHandlers
// Node: aggregate
// Node: publishes
package net.chrisrichardson.ftgo.orderservice;

import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.messaging.consumer.MessageConsumer;
import io.eventuate.util.test.async.Eventually;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmCreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicketReply;
import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderRequest;
import net.chrisrichardson.ftgo.orderservice.domain.RestaurantRepository;
import net.chrisrichardson.ftgo.orderservice.messaging.OrderServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ApproveOrderCommand;
import net.chrisrichardson.ftgo.orderservice.service.OrderCommandHandlersConfiguration;
import net.chrisrichardson.ftgo.orderservice.web.OrderWebConfiguration;
import org.junit.Before;
import org.junit.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import java.util.Collections;

import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withSuccess;
import static io.restassured.RestAssured.given;
import static org.junit.Assert.assertNotNull;

public abstract class AbstractOrderServiceComponentTest {

  protected abstract String baseUrl(String path);

  @Configuration
  @Import({CommonMessagingStubConfiguration.class, OrderWebConfiguration.class, OrderServiceMessagingConfiguration.class, OrderCommandHandlersConfiguration.class,
          TramCommandProducerConfiguration.class})
  public static class CommonTestConfiguration {
  }

  @Configuration
  @Import(SagaParticipantStubConfiguration.class)
  public static class CommonMessagingStubConfiguration {

    @Bean
    public MessagingStubConfiguration messagingStubConfiguration() {
      return new MessagingStubConfiguration("consumerService", "kitchenService", "accountingService", "orderService");
    }

    @Bean
    public MessageTracker messageTracker(MessageConsumer messageConsumer) {
      return new MessageTracker(new MessageTrackerConfiguration("orderService"), messageConsumer) ;
    }

  }

  @Autowired
  private SagaParticipantStubManager sagaParticipantStubManager;

  @Autowired
  private DomainEventPublisher domainEventPublisher;

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private MessageTracker messageTracker;

  @Before
  public void setUp() throws Exception {
    sagaParticipantStubManager.reset();
  }

  @Test
  public void shouldCreateOrder() {

    // setup

    sagaParticipantStubManager.
            forChannel("consumerService")
            .when(ValidateOrderByConsumer.class).replyWith(cm -> withSuccess())
            .forChannel("kitchenService")
            .when(CreateTicket.class).replyWith(cm -> withSuccess(new CreateTicketReply(cm.getCommand().getOrderId())))
            .when(ConfirmCreateTicket.class).replyWithSuccess()
            .forChannel("accountingService")
            .when(AuthorizeCommand.class).replyWithSuccess()
            .forChannel("orderService")
            .when(ApproveOrderCommand.class).replyWithSuccess()
    ;


    domainEventPublisher.publish("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant", RestaurantMother.AJANTA_ID,
            Collections.singletonList(RestaurantMother.makeAjantaRestaurantCreatedEvent()));


    Eventually.eventually(() -> {
      FtgoTestUtil.assertPresent(restaurantRepository.findById(RestaurantMother.AJANTA_ID));
    });

    // make HTTP request

    Integer orderId =
            given().
                    body(new CreateOrderRequest(OrderDetailsMother.CONSUMER_ID,
                            RestaurantMother.AJANTA_ID, Collections.singletonList(new CreateOrderRequest.LineItem(RestaurantMother.CHICKEN_VINDALOO_MENU_ITEM_ID,
                            OrderDetailsMother.CHICKEN_VINDALOO_QUANTITY)))).
                    contentType("application/json").
                    when().
                    post(baseUrl("/orders")).
                    then().
                    statusCode(200).
                    extract().
                    path("orderId");

    assertNotNull(orderId);

    // verify response
    // verify Order state
    // verify events published????

    messageTracker.assertCommandMessageSent("orderService", ApproveOrderCommand.class);

  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/attic/AbstractOrderServiceComponentTest.java:AbstractOrderServiceComponentTest.<init>
// Node: assertCommandMessageSent
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


// Node: shouldScheduleDelivery
// Node: assertDeliveryCreated
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

// Node: shouldCreateCourier
// Node: shouldCreateDelivery
// Node: assertSame
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


// Node: eq
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


// Node: CreateConsumerRequest
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


// Node: shouldCreateConsumer
package net.chrisrichardson.ftgo.consumerservice.web;

import com.atlassian.oai.validator.OpenApiInteractionValidator;
import com.atlassian.oai.validator.springmvc.OpenApiValidationFilter;
import com.atlassian.oai.validator.springmvc.OpenApiValidationInterceptor;
import com.atlassian.oai.validator.springmvc.SpringMVCLevelResolverFactory;
import io.eventuate.common.json.mapper.JSonMapper;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.common.PersonName;
import net.chrisrichardson.ftgo.consumerservice.domain.Consumer;
import net.chrisrichardson.ftgo.consumerservice.domain.ConsumerService;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mockito;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.converter.json.MappingJackson2HttpMessageConverter;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.test.web.servlet.setup.StandaloneMockMvcBuilder;
import org.springframework.util.StreamUtils;

import java.io.IOException;
import java.nio.charset.Charset;
import java.util.Optional;

import static io.restassured.module.mockmvc.RestAssuredMockMvc.given;
import static org.mockito.Mockito.mock;

public class ConsumerControllerTest {

  private ConsumerController consumerController;
  private ConsumerService consumerService;
  private Consumer consumer;

  @Before
  public void setUp() {
    consumerService = mock(ConsumerService.class);
    consumerController = new ConsumerController(consumerService);
    consumer = new Consumer(new PersonName("x", "y"));
  }

  @Test
  public void shouldGetConsumer() throws IOException {
    Mockito.when(consumerService.findById(1)).thenReturn(Optional.of(consumer));
    given().
            standaloneSetup(configureControllers(consumerController)).
            when().
            get("/consumers/1").
            then().
            statusCode(200)
    ;

  }

  private StandaloneMockMvcBuilder configureControllers(Object... controllers) throws IOException {
    CommonJsonMapperInitializer.registerMoneyModule();
    MappingJackson2HttpMessageConverter converter = new MappingJackson2HttpMessageConverter(JSonMapper.objectMapper);

    ClassPathResource swaggerResource = new ClassPathResource("ftgo-consumer-service-swagger.json");

    String specification = StreamUtils.copyToString(swaggerResource.getInputStream(), Charset.forName("UTF-8"));

    OpenApiInteractionValidator validator = OpenApiInteractionValidator
            .createForInlineApiSpecification(specification)
            .withLevelResolver(SpringMVCLevelResolverFactory.create())
            .build();

    OpenApiValidationInterceptor validationInterceptor = new OpenApiValidationInterceptor(validator);

    OpenApiValidationFilter openApiValidationFilter = new OpenApiValidationFilter(
            true, // enable request validation
            true  // enable response validation
    );

    return MockMvcBuilders.standaloneSetup(controllers)
            .setMessageConverters(converter)
            .addFilters(openApiValidationFilter)
            .addInterceptors(validationInterceptor);
  }

}

// Node: shouldGetConsumer
// Node: ClassPathResource
// Node: copyToString
// Node: getInputStream
// Node: createForInlineApiSpecification
// Node: withLevelResolver
// Node: OpenApiValidationInterceptor
// Node: OpenApiValidationFilter
// Node: addFilters
// Node: addInterceptors
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


// Node: consumerBaseUrl
// Node: accountingBaseUrl
// Node: restaurantBaseUrl
// Node: kitchenRestaurantBaseUrl
// Node: kitchenServiceBaseUrl
// Node: orderBaseUrl
// Node: deliveryServiceBaseUrl
// Node: orderRestaurantBaseUrl
// Node: orderHistoryBaseUrl
// Node: verifyOrderRevised
// Node: createConsumer
// Node: verifyAccountCreatedForConsumer
// Node: verifyRestaurantCreatedInKitchenService
// Node: verifyRestaurantCreatedInOrderService
// Node: verifyOrderAuthorized
// Node: verifyOrderHistoryUpdated
// Node: verifyOrderCancelled
// Node: firstName
// Node: lastName
// Node: address
// Node: street1
// Node: street2
// Node: city
// Node: state
// Node: menu
// Node: addMenuItemsItem
// Node: id
// Node: price
// Node: plusHours
// Node: assertThat
// Node: isGreaterThan
