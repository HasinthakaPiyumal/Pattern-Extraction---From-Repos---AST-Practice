// Cluster 13

package net.chrisrichardson.ftgo.orderservice.api.events;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.AttributeOverride;
import javax.persistence.AttributeOverrides;
import javax.persistence.Column;
import javax.persistence.Embeddable;
import javax.persistence.Embedded;

@Embeddable
public class OrderLineItem {

  public OrderLineItem() {
  }

  private int quantity;
  private String menuItemId;
  private String name;

  @Embedded
  @AttributeOverrides(@AttributeOverride(name="amount", column=@Column(name="price")))
  private Money price;

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

  public OrderLineItem(String menuItemId, String name, Money price, int quantity) {
    this.menuItemId = menuItemId;
    this.name = name;
    this.price = price;
    this.quantity = quantity;
  }

  public Money deltaForChangedQuantity(int newQuantity) {
    return price.multiply(newQuantity - quantity);
  }

  public void setQuantity(int quantity) {
    this.quantity = quantity;
  }

  public void setMenuItemId(String menuItemId) {
    this.menuItemId = menuItemId;
  }

  public void setName(String name) {
    this.name = name;
  }

  public void setPrice(Money price) {
    this.price = price;
  }

  public int getQuantity() {
    return quantity;
  }

  public String getMenuItemId() {
    return menuItemId;
  }

  public String getName() {
    return name;
  }

  public Money getPrice() {
    return price;
  }


  public Money getTotal() {
    return price.multiply(quantity);
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service-api/src/main/java/net/chrisrichardson/ftgo/orderservice/api/events/OrderLineItem.java:OrderLineItem.<init>
// Node: AttributeOverrides
// Node: AttributeOverride
// Node: Column
package net.chrisrichardson.ftgo.kitchenservice.api;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class TicketLineItem {

  private int quantity;
  private String menuItemId;
  private String name;


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

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  private TicketLineItem() {

  }

  public TicketLineItem(String menuItemId, String name, int quantity) {
    this.menuItemId = menuItemId;
    this.name = name;
    this.quantity = quantity;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/TicketLineItem.java:TicketLineItem.<init>
// Node: Access
// Node: Restaurant
// Node: RestaurantMenu
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/Restaurant.java:Restaurant.<init>
// Node: Table
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/RestaurantMenu.java:RestaurantMenu.<init>
// Node: setMenuItems
package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
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

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/MenuItem.java:MenuItem.<init>
// Node: MenuItem
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
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/Restaurant.java:Restaurant.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/RestaurantMenu.java:RestaurantMenu.<init>
package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
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

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service-aws-lambda/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/MenuItem.java:MenuItem.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import javax.persistence.Access;
import javax.persistence.AccessType;

@Access(AccessType.FIELD)
public class PaymentInformation {

  private String paymentToken;
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/PaymentInformation.java:PaymentInformation.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/Restaurant.java:Restaurant.<init>
// Node: CollectionTable
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

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderLineItems.java:OrderLineItems.<init>
// Node: OrderLineItems
// Node: Enumerated
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/DeliveryInformation.java:DeliveryInformation.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
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

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/MenuItem.java:MenuItem.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/domain/Action.java:Action.<init>
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



// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/domain/Restaurant.java:Restaurant.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/domain/Courier.java:Courier.<init>
// Node: Courier
// Node: Plan
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/main/java/net/chrisrichardson/ftgo/deliveryservice/domain/Delivery.java:Delivery.<init>
// Node: Delivery
package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.common.DomainEvent;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.CollectionTable;
import javax.persistence.ElementCollection;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import java.util.List;

@Entity
@Table(name = "kitchen_service_restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  private Long id;

  @Embedded
  @ElementCollection
  @CollectionTable(name = "kitchen_service_restaurant_menu_items")
  private List<MenuItem> menuItems;

  private Restaurant() {
  }

  public Restaurant(long id, List<MenuItem> menuItems) {
    this.id = id;
    this.menuItems = menuItems;
  }

  public List<DomainEvent> reviseMenu(RestaurantMenu revisedMenu) {
    throw new UnsupportedOperationException();
  }

  public void verifyRestaurantDetails(TicketDetails ticketDetails) {
    // TODO - implement me
  }

  public Long getId() {
    return id;
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/Restaurant.java:Restaurant.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/RestaurantMenu.java:RestaurantMenu.<init>
package net.chrisrichardson.ftgo.kitchenservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
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

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/MenuItem.java:MenuItem.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/Ticket.java:Ticket.<init>
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-consumer-service/src/main/java/net/chrisrichardson/ftgo/consumerservice/domain/Consumer.java:Consumer.<init>
// Node: Consumer
