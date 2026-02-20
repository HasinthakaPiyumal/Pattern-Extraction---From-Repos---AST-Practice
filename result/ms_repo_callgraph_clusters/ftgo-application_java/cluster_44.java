// Cluster 44

// Node: empty
package net.chrisrichardson.ftgo.common;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.Objects;

public class RevisedOrderLineItem {
    private int quantity;
    private String menuItemId;

    public RevisedOrderLineItem() {
    }

    public RevisedOrderLineItem(int quantity, String menuItemId) {
        this.quantity = quantity;
        this.menuItemId = menuItemId;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    public String getMenuItemId() {
        return menuItemId;
    }

    public void setMenuItemId(String menuItemId) {
        this.menuItemId = menuItemId;
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
        return Objects.hash(quantity, menuItemId);
    }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-common/src/main/java/net/chrisrichardson/ftgo/common/RevisedOrderLineItem.java:RevisedOrderLineItem.<init>
// Node: RevisedOrderLineItem
package net.chrisrichardson.ftgo.common;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import java.math.BigDecimal;

//@Embeddable
//@Access(AccessType.FIELD)
public class Money {

  public static Money ZERO = new Money(0);

  private BigDecimal amount;

  private Money() {
  }

  public Money(BigDecimal amount) {
    this.amount = amount;
  }

  public Money(String s) {
    this.amount = new BigDecimal(s);
  }

  public Money(int i) {
    this.amount = new BigDecimal(i);
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;

    if (o == null || getClass() != o.getClass()) return false;

    Money money = (Money) o;

    return new EqualsBuilder()
            .append(amount, money.amount)
            .isEquals();
  }

  @Override
  public int hashCode() {
    return new HashCodeBuilder(17, 37)
            .append(amount)
            .toHashCode();
  }

  @Override
  public String toString() {
    return new ToStringBuilder(this)
            .append("amount", amount)
            .toString();
  }


  public Money add(Money delta) {
    return new Money(amount.add(delta.amount));
  }

  public boolean isGreaterThanOrEqual(Money other) {
    return amount.compareTo(other.amount) >= 0;
  }

  public String asString() {
    return amount.toPlainString();
  }

  public Money multiply(int x) {
    return new Money(amount.multiply(new BigDecimal(x)));
  }

  public Long asLong() {
    return multiply(100).amount.longValue();
  }
}


// Node: isGreaterThanOrEqual
// Node: compareTo
// Node: reviseOrder
// Node: getNewOrderTotal
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


// Node: revise
// Node: OrderRevision
package net.chrisrichardson.ftgo.orderservice.domain;

// import io.eventuate.tram.events.common.DomainEvent;

import io.eventuate.tram.events.common.DomainEvent;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;

public class OrderRevisionProposed implements OrderDomainEvent {


  private final OrderRevision orderRevision;
  private final Money currentOrderTotal;
  private final Money newOrderTotal;

  public OrderRevisionProposed(OrderRevision orderRevision, Money currentOrderTotal, Money newOrderTotal) {
    this.orderRevision = orderRevision;
    this.currentOrderTotal = currentOrderTotal;
    this.newOrderTotal = newOrderTotal;
  }

  public OrderRevision getOrderRevision() {
    return orderRevision;
  }

  public Money getCurrentOrderTotal() {
    return currentOrderTotal;
  }

  public Money getNewOrderTotal() {
    return newOrderTotal;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderRevisionProposed.java:OrderRevisionProposed.<init>
// Node: OrderRevisionProposed
// Node: changeToOrderTotal
// Node: orderTotal
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;

import javax.persistence.CollectionTable;
import javax.persistence.ElementCollection;
import javax.persistence.Embeddable;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

@Embeddable
public class OrderLineItems {

  @ElementCollection
  @CollectionTable(name = "order_line_items")
  private List<OrderLineItem> lineItems;

  private OrderLineItems() {
  }

  public OrderLineItems(List<OrderLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public List<OrderLineItem> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<OrderLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  OrderLineItem findOrderLineItem(String lineItemId) {
    return lineItems.stream().filter(li -> li.getMenuItemId().equals(lineItemId)).findFirst().get();
  }

  Money changeToOrderTotal(OrderRevision orderRevision) {
    return orderRevision
            .getRevisedOrderLineItems()
            .stream()
            .map(item -> {
              OrderLineItem lineItem = findOrderLineItem(item.getMenuItemId());
              return lineItem.deltaForChangedQuantity(item.getQuantity());
            })
            .reduce(Money.ZERO, Money::add);
  }

  void updateLineItems(OrderRevision orderRevision) {
    getLineItems().stream().forEach(li -> {

      Optional<Integer> revised = orderRevision.getRevisedOrderLineItems()
              .stream()
              .filter(item -> Objects.equals(li.getMenuItemId(), item.getMenuItemId()))
              .map(RevisedOrderLineItem::getQuantity)
              .findFirst();

      li.setQuantity(revised.orElseThrow(() ->
              new IllegalArgumentException(String.format("menu item id not found.", li.getMenuItemId()))));
    });
  }

  Money orderTotal() {
    return lineItems.stream().map(OrderLineItem::getTotal).reduce(Money.ZERO, Money::add);
  }

  LineItemQuantityChange lineItemQuantityChange(OrderRevision orderRevision) {
    Money currentOrderTotal = orderTotal();
    Money delta = changeToOrderTotal(orderRevision);
    Money newOrderTotal = currentOrderTotal.add(delta);
    return new LineItemQuantityChange(currentOrderTotal, newOrderTotal, delta);
  }
}

// Node: lineItemQuantityChange
// Node: LineItemQuantityChange
package net.chrisrichardson.ftgo.orderservice.domain;


import io.eventuate.tram.events.common.DomainEvent;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;

public class OrderRevised implements OrderDomainEvent {

  private final OrderRevision orderRevision;
  private final Money currentOrderTotal;
  private final Money newOrderTotal;

  public OrderRevision getOrderRevision() {
    return orderRevision;
  }

  public Money getCurrentOrderTotal() {
    return currentOrderTotal;
  }

  public Money getNewOrderTotal() {
    return newOrderTotal;
  }

  public OrderRevised(OrderRevision orderRevision, Money currentOrderTotal, Money newOrderTotal) {
    this.orderRevision = orderRevision;
    this.currentOrderTotal = currentOrderTotal;
    this.newOrderTotal = newOrderTotal;


  }
}


// Node: OrderRevised
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



// Node: noteApproved
// Node: OrderAuthorized
// Node: OrderMinimumNotMetException
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderRevision.java:OrderRevision.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.Money;

public class LineItemQuantityChange {
  final Money currentOrderTotal;
  final Money newOrderTotal;
  final Money delta;

  public LineItemQuantityChange(Money currentOrderTotal, Money newOrderTotal, Money delta) {
    this.currentOrderTotal = currentOrderTotal;
    this.newOrderTotal = newOrderTotal;
    this.delta = delta;
  }

  public Money getCurrentOrderTotal() {
    return currentOrderTotal;
  }

  public Money getNewOrderTotal() {
    return newOrderTotal;
  }

  public Money getDelta() {
    return delta;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/LineItemQuantityChange.java:LineItemQuantityChange.<init>
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

// Node: shouldAuthorize
// Node: shouldReviseOrder
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


// Node: shouldCreateReviseAndCancelOrder
