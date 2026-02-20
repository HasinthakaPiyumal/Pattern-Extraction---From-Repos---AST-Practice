// Cluster 18

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


// Node: getDeliveryAddress
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


// Node: getReadyBy
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


// Node: getMenu
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

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  @GeneratedValue
  private Long id;

  private String name;

  @Embedded
  private RestaurantMenu menu;

  private Restaurant() {
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }


  public Restaurant(String name, RestaurantMenu menu) {
    this.name = name;
    this.menu = menu;
  }


  public Long getId() {
    return id;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.ElementCollection;
import javax.persistence.Embeddable;
import java.util.List;

@Embeddable
@Access(AccessType.FIELD)
public class RestaurantMenu {


  @ElementCollection
  private List<MenuItem> menuItems;

  private RestaurantMenu() {
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  public List<MenuItem> getMenuItems() {
    return menuItems;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public void setMenuItems(List<MenuItem> menuItems) {
    this.menuItems = menuItems;
  }

  public RestaurantMenu(List<MenuItem> menuItems) {

    this.menuItems = menuItems;
  }

}


// Node: getMenuItems
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

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.ElementCollection;
import javax.persistence.Embeddable;
import java.util.List;

@Embeddable
@Access(AccessType.FIELD)
public class RestaurantMenu {


  @ElementCollection
  private List<MenuItem> menuItems;

  private RestaurantMenu() {
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  public List<MenuItem> getMenuItems() {
    return menuItems;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public void setMenuItems(List<MenuItem> menuItems) {
    this.menuItems = menuItems;
  }

  public RestaurantMenu(List<MenuItem> menuItems) {

    this.menuItems = menuItems;
  }

}


// Node: debug
// Node: parseLong
package net.chrisrichardson.ftgo.accountingservice.messaging;

import io.eventuate.tram.events.subscriber.DomainEventEnvelope;
import io.eventuate.tram.events.subscriber.DomainEventHandlers;
import io.eventuate.tram.events.subscriber.DomainEventHandlersBuilder;
import net.chrisrichardson.ftgo.accountingservice.domain.AccountingService;
import net.chrisrichardson.ftgo.consumerservice.domain.ConsumerCreated;
import org.springframework.beans.factory.annotation.Autowired;


public class AccountingEventConsumer {

  @Autowired
  private AccountingService accountingService;

  public DomainEventHandlers domainEventHandlers() {
    return DomainEventHandlersBuilder
            .forAggregateType("net.chrisrichardson.ftgo.consumerservice.domain.Consumer")
            .onEvent(ConsumerCreated.class, this::createAccount) // TODO this is hack to get the correct package
            .build();
  }

  private void createAccount(DomainEventEnvelope<ConsumerCreated> dee) {
    accountingService.create(dee.getAggregateId());
  }


}


// Node: createAccount
// Node: getAggregateId
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


// Node: makeSourceEvent
// Node: getEventId
// Node: handleOrderCreated
// Node: makeOrder
// Node: getEvent
// Node: handleOrderAuthorized
// Node: handleOrderCancelled
// Node: cancelOrder
// Node: handleOrderRejected
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;

import javax.persistence.*;
import java.util.List;
import java.util.Optional;

@Entity
@Table(name = "order_service_restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  private Long id;

  @Embedded
  @ElementCollection
  @CollectionTable(name = "order_service_restaurant_menu_items")
  private List<MenuItem> menuItems;
  private String name;

  private Restaurant() {
  }

  public Restaurant(long id, String name, List<MenuItem> menuItems) {
    this.id = id;
    this.name = name;
    this.menuItems = menuItems;
  }

  public List<OrderDomainEvent> reviseMenu(List<MenuItem> revisedMenu) {
    throw new UnsupportedOperationException();
  }

  public void verifyRestaurantDetails(TicketDetails ticketDetails) {
    // TODO - implement me
  }

  public Long getId() {
    return id;
  }

  public Optional<MenuItem> findMenuItem(String menuItemId) {
    return menuItems.stream().filter(mi -> mi.getId().equals(menuItemId)).findFirst();
  }

  public List<MenuItem> getMenuItems() {
    return menuItems;
  }

  public String getName() {
    return name;
  }
}


package net.chrisrichardson.ftgo.orderservice.domain;


import net.chrisrichardson.ftgo.common.Address;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.AttributeOverride;
import javax.persistence.AttributeOverrides;
import javax.persistence.Column;
import javax.persistence.Embedded;
import java.time.LocalDateTime;

@Access(AccessType.FIELD)
public class DeliveryInformation {

  private LocalDateTime deliveryTime;

  @Embedded
  @AttributeOverrides({
    @AttributeOverride(name="state", column=@Column(name="delivery_state"))
  })
  private Address deliveryAddress;

  public DeliveryInformation() {
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

  public DeliveryInformation(LocalDateTime deliveryTime, Address deliveryAddress) {
    this.deliveryTime = deliveryTime;
    this.deliveryAddress = deliveryAddress;
  }

  public LocalDateTime getDeliveryTime() {
    return deliveryTime;
  }

  public void setDeliveryTime(LocalDateTime deliveryTime) {
    this.deliveryTime = deliveryTime;
  }

  public Address getDeliveryAddress() {
    return deliveryAddress;
  }

  public void setDeliveryAddress(Address deliveryAddress) {
    this.deliveryAddress = deliveryAddress;
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


// Node: createMenu
// Node: toMenuItems
package net.chrisrichardson.ftgo.orderservice.messaging;

import io.eventuate.tram.events.subscriber.DomainEventEnvelope;
import io.eventuate.tram.events.subscriber.DomainEventHandlers;
import io.eventuate.tram.events.subscriber.DomainEventHandlersBuilder;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantMenuRevised;


public class OrderEventConsumer {

  private OrderService orderService;

  public OrderEventConsumer(OrderService orderService) {
    this.orderService = orderService;
  }

  public DomainEventHandlers domainEventHandlers() {
    return DomainEventHandlersBuilder
            .forAggregateType("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant")
            .onEvent(RestaurantCreated.class, this::createMenu)
            .onEvent(RestaurantMenuRevised.class, this::reviseMenu)
            .build();
  }

  private void createMenu(DomainEventEnvelope<RestaurantCreated> de) {
    String restaurantIds = de.getAggregateId();
    long id = Long.parseLong(restaurantIds);
    orderService.createMenu(id, de.getEvent().getName(), RestaurantEventMapper.toMenuItems(de.getEvent().getMenu().getMenuItems()));
  }

  public void reviseMenu(DomainEventEnvelope<RestaurantMenuRevised> de) {
    String restaurantIds = de.getAggregateId();
    long id = Long.parseLong(restaurantIds);
    orderService.reviseMenu(id, RestaurantEventMapper.toMenuItems(de.getEvent().getMenu().getMenuItems()));
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


// Node: handle
// Node: addAction
// Node: makePickup
// Node: findAllAvailable
// Node: Action
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


// Node: makeDropoff
// Node: createDelivery
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


// Node: scheduleDelivery
// Node: nextInt
// Node: getPickupAddress
// Node: plusMinutes
// Node: schedule
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


// Node: createQuery
// Node: getResultList
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

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;

import java.util.List;

public interface CourierRepository extends CrudRepository<Courier, Long>, CustomCourierRepository {

  @Query("SELECT c FROM Courier c WHERE c.available = true")
  List<Courier> findAllAvailable();

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/domain/CourierRepository.java:CourierRepository.<init>
// Node: Query
package net.chrisrichardson.ftgo.deliveryservice.messaging;

import io.eventuate.tram.events.subscriber.DomainEventEnvelope;
import io.eventuate.tram.events.subscriber.DomainEventHandlers;
import io.eventuate.tram.events.subscriber.DomainEventHandlersBuilder;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryService;
import net.chrisrichardson.ftgo.kitchenservice.api.KitchenServiceChannels;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketAcceptedEvent;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketCancelled;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.restaurantservice.RestaurantServiceChannels;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;

import java.time.LocalDateTime;

public class DeliveryMessageHandlers {

  private DeliveryService deliveryService;

  public DeliveryMessageHandlers(DeliveryService deliveryService) {
    this.deliveryService = deliveryService;
  }

  public DomainEventHandlers domainEventHandlers() {
    return DomainEventHandlersBuilder
            .forAggregateType(KitchenServiceChannels.TICKET_EVENT_CHANNEL)
            .onEvent(TicketAcceptedEvent.class, this::handleTicketAcceptedEvent)
            .onEvent(TicketCancelled.class, this::handleTicketCancelledEvent)
            .andForAggregateType(OrderServiceChannels.ORDER_EVENT_CHANNEL)
            .onEvent(OrderCreatedEvent.class, this::handleOrderCreatedEvent)
            .andForAggregateType(RestaurantServiceChannels.RESTAURANT_EVENT_CHANNEL)
            .onEvent(RestaurantCreated.class, this::handleRestaurantCreated)
            .build();
  }

  public void handleRestaurantCreated(DomainEventEnvelope<RestaurantCreated> dee) {
    Address address = RestaurantEventMapper.toAddress(dee.getEvent().getAddress());
    deliveryService.createRestaurant(Long.parseLong(dee.getAggregateId()), dee.getEvent().getName(), address);
  }

  public void handleOrderCreatedEvent(DomainEventEnvelope<OrderCreatedEvent> dee) {
    Address address = dee.getEvent().getDeliveryAddress();
    deliveryService.createDelivery(Long.parseLong(dee.getAggregateId()),
            dee.getEvent().getOrderDetails().getRestaurantId(), address);
  }

  public void handleTicketAcceptedEvent(DomainEventEnvelope<TicketAcceptedEvent> dee) {
    LocalDateTime readyBy = dee.getEvent().getReadyBy();
    deliveryService.scheduleDelivery(Long.parseLong(dee.getAggregateId()), readyBy);
  }

  public void handleTicketCancelledEvent(DomainEventEnvelope<TicketCancelled> dee) {
    deliveryService.cancelDelivery(Long.parseLong(dee.getAggregateId()));
  }


}


// Node: handleRestaurantCreated
// Node: handleOrderCreatedEvent
// Node: handleTicketAcceptedEvent
// Node: handleTicketCancelledEvent
package net.chrisrichardson.ftgo.kitchenservice.messagehandlers;

import io.eventuate.tram.events.subscriber.DomainEventEnvelope;
import io.eventuate.tram.events.subscriber.DomainEventHandlers;
import io.eventuate.tram.events.subscriber.DomainEventHandlersBuilder;
import net.chrisrichardson.ftgo.kitchenservice.domain.KitchenService;
import net.chrisrichardson.ftgo.kitchenservice.domain.RestaurantMenu;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantMenuRevised;
import org.springframework.beans.factory.annotation.Autowired;


public class KitchenServiceEventConsumer {

  @Autowired
  private KitchenService kitchenService;

  public DomainEventHandlers domainEventHandlers() {
    return DomainEventHandlersBuilder
            .forAggregateType("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant")
            .onEvent(RestaurantCreated.class, this::createMenu)
            .onEvent(RestaurantMenuRevised.class, this::reviseMenu)
            .build();
  }

  private void createMenu(DomainEventEnvelope<RestaurantCreated> de) {
    String restaurantIds = de.getAggregateId();
    long id = Long.parseLong(restaurantIds);
    RestaurantMenu menu = new RestaurantMenu(RestaurantEventMapper.toMenuItems(de.getEvent().getMenu().getMenuItems()));
    kitchenService.createMenu(id, menu);
  }

  public void reviseMenu(DomainEventEnvelope<RestaurantMenuRevised> de) {
    long id = Long.parseLong(de.getAggregateId());
    RestaurantMenu menu = new RestaurantMenu(RestaurantEventMapper.toMenuItems(de.getEvent().getMenu().getMenuItems()));
    kitchenService.reviseMenu(id, menu);
  }

}


package net.chrisrichardson.ftgo.kitchenservice.web;

import net.chrisrichardson.ftgo.kitchenservice.api.web.TicketAcceptance;
import net.chrisrichardson.ftgo.kitchenservice.domain.KitchenService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class KitchenController {

  private KitchenService kitchenService;

  public KitchenController(KitchenService kitchenService) {
    this.kitchenService = kitchenService;
  }

  @RequestMapping(path="/tickets/{ticketId}/accept", method= RequestMethod.POST)
  public void acceptTicket(@PathVariable long ticketId, @RequestBody TicketAcceptance ticketAcceptance) {
    kitchenService.accept(ticketId, ticketAcceptance.getReadyBy());
  }
}


// Node: acceptTicket
// Node: accept
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


package net.chrisrichardson.ftgo.kitchenservice.domain;

import java.util.List;

public class RestaurantMenu {
  private List<MenuItem> menuItems;

  public RestaurantMenu(List<MenuItem> menuItems) {
    this.menuItems = menuItems;
  }

  public List<MenuItem> getMenuItems() {
    return menuItems;
  }
}


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


// Node: shouldDeliverOrder
// Node: noteCourierAvailable
// Node: assertOrderAssignedToCourier
// Node: testSwaggerUiUrls
// Node: testSwaggerUiUrl
// Node: assertUrlStatusIsOk
