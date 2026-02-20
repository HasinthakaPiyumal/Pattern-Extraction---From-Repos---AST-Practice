// Cluster 6

package net.chrisrichardson.ftgo.orderservice.api.events;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;

public class OrderAuthorized implements OrderDomainEvent {

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

}


// Node: hashCode
// Node: reflectionHashCode
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


package net.chrisrichardson.ftgo.apiagateway.orders;

import net.chrisrichardson.ftgo.apiagateway.proxies.BillInfo;
import net.chrisrichardson.ftgo.apiagateway.proxies.DeliveryInfo;
import net.chrisrichardson.ftgo.apiagateway.proxies.OrderInfo;
import net.chrisrichardson.ftgo.apiagateway.proxies.TicketInfo;
import org.apache.commons.lang3.builder.EqualsBuilder;
import org.apache.commons.lang3.builder.HashCodeBuilder;
import org.apache.commons.lang3.builder.ToStringBuilder;
import reactor.util.function.Tuple4;

import java.util.Optional;

public class OrderDetails {

  private OrderInfo orderInfo;

  public OrderDetails() {
  }

  public OrderDetails(OrderInfo orderInfo) {
    this.orderInfo = orderInfo;
  }

  public OrderDetails(OrderInfo orderInfo,
                      Optional<TicketInfo> ticketInfo,
                      Optional<DeliveryInfo> deliveryInfo,
                      Optional<BillInfo> billInfo) {
    this(orderInfo);
    System.out.println("FIXME");
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


  public OrderInfo getOrderInfo() {
    return orderInfo;
  }

  public void setOrderInfo(OrderInfo orderInfo) {
    this.orderInfo = orderInfo;
  }


  public static OrderDetails makeOrderDetails(Tuple4<OrderInfo, Optional<TicketInfo>, Optional<DeliveryInfo>, Optional<BillInfo>> info) {
    return new OrderDetails(info.getT1(), info.getT2(), info.getT3(), info.getT4());
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


// Node: hash
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


// Node: HashCodeBuilder
// Node: toHashCode
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


package net.chrisrichardson.ftgo.orderservice.web;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class MenuItemIdAndQuantity {

  private String menuItemId;
  private int quantity;

  public String getMenuItemId() {
    return menuItemId;
  }

  public int getQuantity() {
    return quantity;
  }

  public void setMenuItemId(String menuItemId) {
    this.menuItemId = menuItemId;
  }

  public MenuItemIdAndQuantity(String menuItemId, int quantity) {

    this.menuItemId = menuItemId;
    this.quantity = quantity;

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


package net.chrisrichardson.ftgo.consumerservice.api;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class ValidateOrderByConsumer implements Command {

  private long consumerId;
  private long orderId;
  private Money orderTotal;

  private ValidateOrderByConsumer() {
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

  public ValidateOrderByConsumer(long consumerId, long orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  public long getOrderId() {
    return orderId;
  }

  public long getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }
}


