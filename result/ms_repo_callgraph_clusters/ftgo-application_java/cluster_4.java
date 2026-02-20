// Cluster 4

// Node: RuntimeException
// Node: toString
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


// Node: reflectionToString
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


// Node: ofNullable
// Node: getenv
package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.CommandDestination;
import io.eventuate.tram.commands.common.Command;
import org.apache.commons.lang.builder.ToStringBuilder;

@CommandDestination("restaurantService")
public class CreateTicket implements Command {

  private Long orderId;
  private TicketDetails ticketDetails;
  private long restaurantId;

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public Long getOrderId() {
    return orderId;
  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }

  public TicketDetails getTicketDetails() {
    return ticketDetails;
  }

  public void setTicketDetails(TicketDetails orderDetails) {
    this.ticketDetails = orderDetails;
  }

  private CreateTicket() {

  }

  public CreateTicket(long restaurantId, long orderId, TicketDetails ticketDetails) {
    this.restaurantId = restaurantId;
    this.orderId = orderId;
    this.ticketDetails = ticketDetails;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-api-gateway/src/main/java/net/chrisrichardson/ftgo/apiagateway/orders/OrderDetails.java:OrderDetails.<init>
// Node: println
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


package net.chrisrichardson.ftgo.restaurantservice.aws;

import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.Map;
import java.util.Optional;

public class ApiGatewayRequest {

  private String resource;
  private String path;
  private String httpMethod;
  private Map<String, String> headers;
  private Map<String, String> queryStringParameters;
  private Map<String, String> pathParameters;
  private Map<String, String> stageVariables;
  private RequestContext requestContext;
  private String body;
  private boolean isBase64Encoded;

  public String getResource() {
    return resource;
  }

  public void setResource(String resource) {
    this.resource = resource;
  }

  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public String getHttpMethod() {
    return httpMethod;
  }

  public void setHttpMethod(String httpMethod) {
    this.httpMethod = httpMethod;
  }

  public Map<String, String> getHeaders() {
    return headers;
  }

  public void setHeaders(Map<String, String> headers) {
    this.headers = headers;
  }

  public Map<String, String> getQueryStringParameters() {
    return queryStringParameters;
  }

  public void setQueryStringParameters(Map<String, String> queryStringParameters) {
    this.queryStringParameters = queryStringParameters;
  }

  public Map<String, String> getPathParameters() {
    return pathParameters;
  }

  public void setPathParameters(Map<String, String> pathParameters) {
    this.pathParameters = pathParameters;
  }

  public Map<String, String> getStageVariables() {
    return stageVariables;
  }

  public void setStageVariables(Map<String, String> stageVariables) {
    this.stageVariables = stageVariables;
  }

  public RequestContext getRequestContext() {
    return requestContext;
  }

  public void setRequestContext(RequestContext requestContext) {
    this.requestContext = requestContext;
  }

  public String getBody() {
    return body;
  }

  public void setBody(String body) {
    this.body = body;
  }

  public boolean isBase64Encoded() {
    return isBase64Encoded;
  }

  public void setBase64Encoded(boolean base64Encoded) {
    isBase64Encoded = base64Encoded;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getPathParam(String paramName) {
    return Optional.ofNullable(this.getPathParameters())
            .map(paramsMap -> paramsMap.get(paramName))
            .orElse(null);
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


// Node: append
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


// Node: ToStringBuilder
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

// Node: StringBuilder
// Node: forName
// Node: assertMessageReceived
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


// Node: eventuallyReturning
// Node: pollFirst
// Node: test
import org.gradle.api.DefaultTask;
import org.gradle.api.tasks.TaskAction;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Optional;
import java.util.function.Supplier;

public class WaitForMySql extends DefaultTask {

  @TaskAction
  public void waitForMySql() {
    System.out.println("Waiting for MySql...");

    loadDriver();

    waitForConnection();
  }

  private String getenv(String name, String defaultValue) {
    return Optional.ofNullable(System.getenv(name)).orElse(defaultValue);
  }
  private String getenv(String name, Supplier<String> defaultValue) {
    return Optional.ofNullable(System.getenv(name)).orElseGet(defaultValue);
  }

  private void loadDriver() {
    try {
      System.out.println("Trying to initialize driver");

      String datasourceDriverClassName = getenv("SPRING_DATASOURCE_DRIVER_CLASS_NAME", "com.mysql.jdbc.Driver");
      Class.forName(datasourceDriverClassName);

      System.out.println("Initialization succeed");
    } catch (ClassNotFoundException e) {
      System.out.println("Initialization failed");

      throw new RuntimeException(e);
    }
  }

  private void waitForConnection() {
    while (true) {
      Connection connection = null;
      try {
        System.out.println("Trying to connect...");

        String datasourceUrl = getenv("SPRING_DATASOURCE_URL", () -> String.format("jdbc:mysql://%s/eventuate", getenv("DOCKER_HOST_IP", "localhost")));
        String datasourceUsername = getenv("SPRING_DATASOURCE_USERNAME", "mysqluser");
        String datasourcePassword = getenv("SPRING_DATASOURCE_PASSWORD", "mysqlpw");

        connection = DriverManager.getConnection(datasourceUrl, datasourceUsername, datasourcePassword);

        System.out.println("Connection succeed");

        break;
      } catch (SQLException e) {
        System.out.println("Connection failed");

        sleep();
      } finally {
        if (connection != null) {
          closeConnection(connection);
        }
      }
    }
  }

  private void closeConnection(Connection connection) {
    try {
      System.out.println("Trying to close connection");

      connection.close();

      System.out.println("Connection closed");
    } catch (SQLException e) {
      System.out.println("Failed to close connection, see stack trace:");

      e.printStackTrace();
    }
  }

  private void sleep() {
    System.out.println("sleeping for 5 seconds...");

    try {
      Thread.sleep(5000);
    } catch (InterruptedException ie) {
      throw new RuntimeException(ie);
    }
  }
}

// Node: waitForMySql
// Node: loadDriver
// Node: waitForConnection
// Node: getConnection
// Node: sleep
// Node: closeConnection
// Node: close
// Node: printStackTrace
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


