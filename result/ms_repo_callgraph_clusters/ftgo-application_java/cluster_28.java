// Cluster 28

// Node: Address
package net.chrisrichardson.ftgo.apiagateway.proxies;

import org.apache.commons.lang3.builder.EqualsBuilder;
import org.apache.commons.lang3.builder.HashCodeBuilder;
import org.apache.commons.lang3.builder.ToStringBuilder;

public class OrderInfo {

  private String orderId;
  private String state;

  public String getState() {
    return state;
  }

  public void setState(String state) {
    this.state = state;
  }

  public OrderInfo(String orderId, String state) {
    this.orderId = orderId;
    this.state = state;

  }

  private OrderInfo() {
  }

  public String getOrderId() {
    return orderId;
  }

  public void setOrderId(String orderId) {
    this.orderId = orderId;
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


// Node: getState
package net.chrisrichardson.ftgo.common;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class Address {

  private String street1;
  private String street2;
  private String city;
  private String state;
  private String zip;

  private Address() {
  }

  public Address(String street1, String street2, String city, String state, String zip) {
    this.street1 = street1;
    this.street2 = street2;
    this.city = city;
    this.state = state;
    this.zip = zip;
  }

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

  public String getStreet1() {
    return street1;
  }

  public void setStreet1(String street1) {
    this.street1 = street1;
  }

  public String getStreet2() {
    return street2;
  }

  public void setStreet2(String street2) {
    this.street2 = street2;
  }

  public String getCity() {
    return city;
  }

  public void setCity(String city) {
    this.city = city;
  }

  public String getState() {
    return state;
  }

  public void setState(String state) {
    this.state = state;
  }

  public String getZip() {
    return zip;
  }

  public void setZip(String zip) {
    this.zip = zip;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-common/src/main/java/net/chrisrichardson/ftgo/common/Address.java:Address.<init>
// Node: getStreet1
// Node: setStreet1
// Node: getStreet2
// Node: setStreet2
// Node: getCity
// Node: setCity
// Node: getZip
// Node: setZip
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


// Node: amazonDynamoDB
// Node: isBlank
// Node: standard
// Node: withEndpointConfiguration
// Node: EndpointConfiguration
// Node: withCredentials
// Node: AWSStaticCredentialsProvider
// Node: BasicAWSCredentials
// Node: withRegion
// Node: or
// Node: AND
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import org.apache.commons.lang.StringUtils;

import java.util.Optional;

public class Expressions {

  static String and(String s1, Optional<String> s2) {
    return s2.map(x -> and(s1, x)).orElse(s1);
  }

  static String and(String s1, String s2) {
    if (StringUtils.isBlank(s1))
      return s2;
    if (StringUtils.isBlank(s2))
      return s1;
    return String.format("(%s) AND (%s)", s1, s2);
  }

  static String or(String s1, String s2) {
    if (StringUtils.isBlank(s1))
      return s2;
    if (StringUtils.isBlank(s2))
      return s1;
    return String.format("(%s) AND (%s)", s1, s2);
  }
}


package net.chrisrichardson.ftgo.deliveryservice.api.web;

public class DeliveryInfo {

  private long id;
  private DeliveryState state;

  public DeliveryInfo() {
  }

  public DeliveryInfo(long id, DeliveryState state) {

    this.id = id;
    this.state = state;
  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public DeliveryState getState() {
    return state;
  }

  public void setState(DeliveryState state) {
    this.state = state;
  }
}


// Node: makeAddress
package net.chrisrichardson.ftgo.orderservice.grpc;


import io.grpc.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import java.util.stream.IntStream;

import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;

public class OrderServiceClient {
  private static final Logger logger = Logger.getLogger(OrderServiceClient.class.getName());

  private final ManagedChannel channel;
  private final OrderServiceGrpc.OrderServiceBlockingStub clientStub;

  public OrderServiceClient(String host, int port) {
    channel = ManagedChannelBuilder.forAddress(host, port)
            .usePlaintext()
            .build();
    clientStub = OrderServiceGrpc.newBlockingStub(channel);
  }

  public void shutdown() throws InterruptedException {
    channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
  }

  public long createOrder(long consumerId, long restaurantId, List<MenuItemIdAndQuantity> lineItems, net.chrisrichardson.ftgo.common.Address deliveryAddress, LocalDateTime deliveryTime) {
    CreateOrderRequest.Builder builder = CreateOrderRequest.newBuilder()
            .setConsumerId(consumerId)
            .setRestaurantId(restaurantId)
            .setDeliveryAddress(makeAddress(deliveryAddress))
            .setDeliveryTime(DateTimeFormatter.ISO_LOCAL_DATE_TIME.format(deliveryTime));
    lineItems.forEach(li -> builder.addLineItems(LineItem.newBuilder().setQuantity(li.getQuantity()).setMenuItemId(li.getMenuItemId())));
    CreateOrderReply response = clientStub.createOrder(builder.build());
    return response.getOrderId();
  }

  private Address makeAddress(net.chrisrichardson.ftgo.common.Address address) {
    Address.Builder builder = Address.newBuilder()
            .setStreet1(address.getStreet1());
    if (address.getStreet2() != null)
      builder.setStreet2(address.getStreet2());
    builder
            .setCity(address.getCity())
            .setState(address.getState())
            .setZip(address.getZip());
    return builder.build();
  }


}


package net.chrisrichardson.ftgo.orderservice.grpc;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.orderservice.domain.DeliveryInformation;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;
import org.apache.commons.lang.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

import static java.util.stream.Collectors.toList;

public class OrderServiceServer {
  private static final Logger logger = LoggerFactory.getLogger(OrderServiceServer.class);

  private int port = 50051;
  private Server server;
  private OrderService orderService;

  public OrderServiceServer(OrderService orderService) {
    this.orderService = orderService;
  }

  @PostConstruct
  public void start() throws IOException {
    server = ServerBuilder.forPort(port)
            .addService(new OrderServiceImpl())
            .build()
            .start();
    logger.info("Server started, listening on " + port);
  }

  @PreDestroy
  public void stop() {
    if (server != null) {
      logger.info("*** shutting down gRPC server since JVM is shutting down");
      server.shutdown();
      logger.info("*** server shut down");
    }
  }


  private class OrderServiceImpl extends OrderServiceGrpc.OrderServiceImplBase {

    @Override
    public void createOrder(CreateOrderRequest req, StreamObserver<CreateOrderReply> responseObserver) {
      List<LineItem> lineItemsList = req.getLineItemsList();
      Order order = orderService.createOrder(req.getConsumerId(),
              req.getRestaurantId(),
              new DeliveryInformation(LocalDateTime.parse(req.getDeliveryTime(), DateTimeFormatter.ISO_LOCAL_DATE_TIME), makeAddress(req.getDeliveryAddress())),
              lineItemsList.stream().map(x -> new MenuItemIdAndQuantity(x.getMenuItemId(), x.getQuantity())).collect(toList())
      );
      CreateOrderReply reply = CreateOrderReply.newBuilder().setOrderId(order.getId()).build();
      responseObserver.onNext(reply);
      responseObserver.onCompleted();
    }

    private Address makeAddress(net.chrisrichardson.ftgo.orderservice.grpc.Address address) {
      return new Address(address.getStreet1(), nullIfBlank(address.getStreet2()), address.getCity(), address.getState(), address.getZip());
    }

    @Override
    public void cancelOrder(CancelOrderRequest req, StreamObserver<CancelOrderReply> responseObserver) {
      CancelOrderReply reply = CancelOrderReply.newBuilder().setMessage("Hello " + req.getName()).build();
      responseObserver.onNext(reply);
      responseObserver.onCompleted();
    }

    @Override
    public void reviseOrder(ReviseOrderRequest req, StreamObserver<ReviseOrderReply> responseObserver) {
      ReviseOrderReply reply = ReviseOrderReply.newBuilder().setMessage("Hello " + req.getName()).build();
      responseObserver.onNext(reply);
      responseObserver.onCompleted();
    }
  }

  private String nullIfBlank(String s) {
    return StringUtils.isBlank(s) ? null : s;
  }
}


// Node: nullIfBlank
package net.chrisrichardson.ftgo.orderservice.web;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;

public class GetOrderResponse {
  private long orderId;
  private OrderState state;
  private Money orderTotal;

  private GetOrderResponse() {
  }

  public GetOrderResponse(long orderId, OrderState state, Money orderTotal) {
    this.orderId = orderId;
    this.state = state;
    this.orderTotal = orderTotal;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }

  public long getOrderId() {
    return orderId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }

  public OrderState getState() {
    return state;
  }

  public void setState(OrderState state) {
    this.state = state;
  }
}


package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.common.DomainEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;

public class OrderCancelRequested implements DomainEvent {
  private OrderState state;

  public OrderCancelRequested(OrderState state) {

    this.state = state;
  }

  public OrderState getState() {
    return state;
  }
}


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



package net.chrisrichardson.ftgo.orderservice.messaging;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.restaurantservice.events.Address;
import net.chrisrichardson.ftgo.restaurantservice.events.MenuItem;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.stream.Collectors;

public class RestaurantEventMapper {

  @NotNull
  public static List<MenuItem> fromMenuItems(List<net.chrisrichardson.ftgo.orderservice.domain.MenuItem> menuItems) {
    return menuItems.stream().map(mi -> new MenuItem().withId(mi.getId()).withName(mi.getName()).withPrice(mi.getPrice().asString())).collect(Collectors.toList());
  }

  public static Address fromAddress(net.chrisrichardson.ftgo.common.Address a) {
    return new Address().withStreet1(a.getStreet1()).withStreet2(a.getStreet2()).withCity(a.getCity()).withZip(a.getZip());
  }

  public static List<net.chrisrichardson.ftgo.orderservice.domain.MenuItem> toMenuItems(List<MenuItem> menuItems) {
    return menuItems.stream().map(mi -> new net.chrisrichardson.ftgo.orderservice.domain.MenuItem(mi.getId(), mi.getName(), new Money(mi.getPrice()))).collect(Collectors.toList());
  }

}


// Node: fromAddress
// Node: withStreet1
// Node: withStreet2
// Node: withCity
// Node: withZip
package net.chrisrichardson.ftgo.orderservice;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.domain.MenuItem;
import net.chrisrichardson.ftgo.orderservice.domain.Restaurant;
import net.chrisrichardson.ftgo.orderservice.messaging.RestaurantEventMapper;
import net.chrisrichardson.ftgo.restaurantservice.events.Menu;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;

import java.util.Collections;
import java.util.List;

public class RestaurantMother {
  public static final String AJANTA_RESTAURANT_NAME = "Ajanta";
  public static final long AJANTA_ID = 1L;

  public static final String CHICKEN_VINDALOO = "Chicken Vindaloo";
  public static final String CHICKEN_VINDALOO_MENU_ITEM_ID = "1";
  public static final Money CHICKEN_VINDALOO_PRICE = new Money("12.34");
  public static final Address RESTAURANT_ADDRESS = new Address("1 Main Street", "Unit 99", "Oakland", "CA", "94611");

  public static MenuItem CHICKEN_VINDALOO_MENU_ITEM = new MenuItem(CHICKEN_VINDALOO_MENU_ITEM_ID, CHICKEN_VINDALOO, CHICKEN_VINDALOO_PRICE);

  public static final List<MenuItem> AJANTA_RESTAURANT_MENU_ITEMS = Collections.singletonList(CHICKEN_VINDALOO_MENU_ITEM);

  public static final Restaurant AJANTA_RESTAURANT =
          new Restaurant(AJANTA_ID, AJANTA_RESTAURANT_NAME, AJANTA_RESTAURANT_MENU_ITEMS);

  public static RestaurantCreated makeAjantaRestaurantCreatedEvent() {
    return new RestaurantCreated().withName(AJANTA_RESTAURANT_NAME)
            .withAddress(RestaurantEventMapper.fromAddress(RESTAURANT_ADDRESS))
            .withMenu(new Menu().withMenuItems(RestaurantEventMapper.fromMenuItems(AJANTA_RESTAURANT_MENU_ITEMS)));
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/test/java/net/chrisrichardson/ftgo/orderservice/RestaurantMother.java:RestaurantMother.<init>
// Node: withAddress
// Node: withMenu
// Node: Menu
// Node: withMenuItems
package net.chrisrichardson.ftgo.deliveryservice;

import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryServiceTestData;
import net.chrisrichardson.ftgo.deliveryservice.messaging.RestaurantEventMapper;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import net.chrisrichardson.ftgo.restaurantservice.events.Menu;
import net.chrisrichardson.ftgo.restaurantservice.events.MenuItem;

import java.util.Collections;
import java.util.List;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;

public class RestaurantEventMother {

  public static final String CHICKEN_VINDALOO = "Chicken Vindaloo";
  public static final String CHICKEN_VINDALOO_MENU_ITEM_ID = "1";
  public static final String CHICKEN_VINDALOO_PRICE = "12.34";
  public static final Address RESTAURANT_ADDRESS = new Address("1 Main Street", "Unit 99", "Oakland", "CA", "94611");

  public static MenuItem CHICKEN_VINDALOO_MENU_ITEM = new MenuItem()
    .withId(CHICKEN_VINDALOO_MENU_ITEM_ID)
    .withName(CHICKEN_VINDALOO)
    .withPrice(CHICKEN_VINDALOO_PRICE);

  public static final List<MenuItem> AJANTA_RESTAURANT_MENU_ITEMS = Collections.singletonList(CHICKEN_VINDALOO_MENU_ITEM);


  static RestaurantCreated makeRestaurantCreated() {
    return new RestaurantCreated()
            .withName("Delicious Indian")
            .withAddress(RestaurantEventMapper.fromAddress(DeliveryServiceTestData.PICKUP_ADDRESS))
            .withMenu(new Menu().withMenuItems(AJANTA_RESTAURANT_MENU_ITEMS));
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


// Node: toAddress
package net.chrisrichardson.ftgo.deliveryservice.messaging;

import net.chrisrichardson.ftgo.common.Address;

public class RestaurantEventMapper {

  public static Address toAddress(net.chrisrichardson.ftgo.restaurantservice.events.Address address) {
    return new Address(address.getStreet1(), address.getStreet2(), address.getCity(), address.getState(), address.getZip());
  }

  public static net.chrisrichardson.ftgo.restaurantservice.events.Address fromAddress(net.chrisrichardson.ftgo.common.Address a) {
    return new net.chrisrichardson.ftgo.restaurantservice.events.Address().withStreet1(a.getStreet1()).withStreet2(a.getStreet2()).withCity(a.getCity()).withZip(a.getZip());
  }

}


package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.common.Address;

public class DeliveryServiceTestData {
  public static final Address PICKUP_ADDRESS =
          new Address("1 Main Street", "Suite 501", "Oakland", "CA", "94612");
  public static final Address DELIVERY_ADDRESS =
          new Address("1 Quiet Street", "Apartment 101", "Oakland", "CA", "94612");
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/test/java/net/chrisrichardson/ftgo/deliveryservice/domain/DeliveryServiceTestData.java:DeliveryServiceTestData.<init>
