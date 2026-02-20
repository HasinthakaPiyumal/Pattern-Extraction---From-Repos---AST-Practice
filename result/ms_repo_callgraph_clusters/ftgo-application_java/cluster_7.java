// Cluster 7

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


// Node: getOrderTotal
// Node: getRestaurantId
// Node: getConsumerId
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


// Node: getOrderDetails
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


// Node: getRevisedOrderLineItems
package net.chrisrichardson.ftgo.orderservice.api.web;

public class CreateOrderResponse {
  private long orderId;

  public long getOrderId() {
    return orderId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }

  private CreateOrderResponse() {
  }

  public CreateOrderResponse(long orderId) {
    this.orderId = orderId;
  }
}


// Node: getOrderId
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


package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.common.Command;

public class CancelCreateTicket implements Command {
  private Long ticketId;

  private CancelCreateTicket() {
  }

  public CancelCreateTicket(long ticketId) {
    this.ticketId = ticketId;
  }

  public Long getTicketId() {
    return ticketId;
  }

  public void setTicketId(Long ticketId) {
    this.ticketId = ticketId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/CancelCreateTicket.java:CancelCreateTicket.<init>
// Node: CancelCreateTicket
package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;

import java.util.List;
import java.util.Map;

public class BeginReviseTicketCommand implements Command {
  private long restaurantId;
  private Long orderId;
  private List<RevisedOrderLineItem> revisedOrderLineItems;

  private BeginReviseTicketCommand() {
  }

  public BeginReviseTicketCommand(long restaurantId, Long orderId, List<RevisedOrderLineItem> revisedOrderLineItems) {
    this.restaurantId = restaurantId;
    this.orderId = orderId;
    this.revisedOrderLineItems = revisedOrderLineItems;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public Long getOrderId() {
    return orderId;
  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }

  public List<RevisedOrderLineItem> getRevisedOrderLineItems() {
    return revisedOrderLineItems;
  }

  public void setRevisedOrderLineItems(List<RevisedOrderLineItem> revisedOrderLineItems) {
    this.revisedOrderLineItems = revisedOrderLineItems;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/BeginReviseTicketCommand.java:BeginReviseTicketCommand.<init>
// Node: BeginReviseTicketCommand
package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.common.Command;

public class ConfirmCancelTicketCommand implements Command {

  private long restaurantId;
  private long orderId;

  private ConfirmCancelTicketCommand() {
  }

  public ConfirmCancelTicketCommand(long restaurantId, long orderId) {

    this.restaurantId = restaurantId;
    this.orderId = orderId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public long getOrderId() {
    return orderId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/ConfirmCancelTicketCommand.java:ConfirmCancelTicketCommand.<init>
// Node: ConfirmCancelTicketCommand
package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.common.Command;

public class UndoBeginReviseTicketCommand implements Command {
  private long restaurantId;
  private Long orderId;

  public UndoBeginReviseTicketCommand() {
  }

  public UndoBeginReviseTicketCommand(long restaurantId, Long orderId) {

    this.restaurantId = restaurantId;
    this.orderId = orderId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public Long getOrderId() {
    return orderId;
  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/UndoBeginReviseTicketCommand.java:UndoBeginReviseTicketCommand.<init>
// Node: UndoBeginReviseTicketCommand
package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.common.Command;

public class BeginCancelTicketCommand implements Command {
  private long restaurantId;
  private long orderId;

  private BeginCancelTicketCommand() {
  }

  public BeginCancelTicketCommand(long restaurantId, long orderId) {

    this.restaurantId = restaurantId;
    this.orderId = orderId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public long getOrderId() {
    return orderId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/BeginCancelTicketCommand.java:BeginCancelTicketCommand.<init>
// Node: BeginCancelTicketCommand
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


// Node: getTicketDetails
// Node: setTicketDetails
// Node: CreateTicket
package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;

import java.util.List;

public class ConfirmReviseTicketCommand implements Command {
  private long restaurantId;
  private long orderId;
  private List<RevisedOrderLineItem> revisedOrderLineItems;

  private ConfirmReviseTicketCommand() {
  }

  public ConfirmReviseTicketCommand(long restaurantId, Long orderId, List<RevisedOrderLineItem> revisedOrderLineItems) {

    this.restaurantId = restaurantId;
    this.orderId = orderId;
    this.revisedOrderLineItems = revisedOrderLineItems;
  }

  public long getOrderId() {
    return orderId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public List<RevisedOrderLineItem> getRevisedOrderLineItems() {
    return revisedOrderLineItems;
  }

  public void setRevisedOrderLineItems(List<RevisedOrderLineItem> revisedOrderLineItems) {
    this.revisedOrderLineItems = revisedOrderLineItems;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/ConfirmReviseTicketCommand.java:ConfirmReviseTicketCommand.<init>
// Node: ConfirmReviseTicketCommand
package net.chrisrichardson.ftgo.kitchenservice.api;

import io.eventuate.tram.commands.common.Command;

public class UndoBeginCancelTicketCommand implements Command {

  private long restaurantId;
  private long orderId;

  private UndoBeginCancelTicketCommand() {
  }

  public UndoBeginCancelTicketCommand(long restaurantId, long orderId) {

    this.restaurantId = restaurantId;
    this.orderId = orderId;
  }

  public long getOrderId() {
    return orderId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service-api/src/main/java/net/chrisrichardson/ftgo/kitchenservice/api/UndoBeginCancelTicketCommand.java:UndoBeginCancelTicketCommand.<init>
// Node: UndoBeginCancelTicketCommand
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


// Node: build
package net.chrisrichardson.ftgo.restaurantservice.aws;

import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import io.eventuate.common.json.mapper.JSonMapper;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

public class ApiGatewayResponse {
  private final int statusCode;
  private final String body;
  private final Map<String, String> headers;
  private final boolean isBase64Encoded;

  public ApiGatewayResponse(int statusCode, String body, Map<String, String> headers, boolean isBase64Encoded) {
    this.statusCode = statusCode;
    this.body = body;
    this.headers = headers;
    this.isBase64Encoded = isBase64Encoded;
  }

  public int getStatusCode() {
    return statusCode;
  }

  public String getBody() {
    return body;
  }

  public Map<String, String> getHeaders() {
    return headers;
  }

  // API Gateway expects the property to be called "isBase64Encoded" => isIs
  public boolean isIsBase64Encoded() {
    return isBase64Encoded;
  }

  public static Builder builder() {
    return new Builder();
  }

  public static class Builder {
    private int statusCode = 200;
    private Map<String, String> headers = Collections.emptyMap();
    private String rawBody;
    private Object objectBody;
    private byte[] binaryBody;
    private boolean base64Encoded;

    public Builder setStatusCode(int statusCode) {
      this.statusCode = statusCode;
      return this;
    }

    public Builder setHeaders(Map<String, String> headers) {
      this.headers = headers;
      return this;
    }

    public Builder setRawBody(String rawBody) {
      this.rawBody = rawBody;
      return this;
    }

    public Builder setObjectBody(Object objectBody) {
      this.objectBody = objectBody;
      return this;
    }

    public Builder setBinaryBody(byte[] binaryBody) {
      this.binaryBody = binaryBody;
      setBase64Encoded(true);
      return this;
    }

    public Builder setBase64Encoded(boolean base64Encoded) {
      this.base64Encoded = base64Encoded;
      return this;
    }

    public APIGatewayProxyResponseEvent build() {
      String body = null;
      if (rawBody != null) {
        body = rawBody;
      } else if (objectBody != null) {
        body = JSonMapper.toJson(objectBody);
      } else if (binaryBody != null) {
        body = new String(Base64.getEncoder().encode(binaryBody), StandardCharsets.UTF_8);
      }
      APIGatewayProxyResponseEvent response = new APIGatewayProxyResponseEvent();
      response.setStatusCode(statusCode);
      response.setBody(body);
      response.setHeaders(headers);
      return response;
    }
  }

  public static APIGatewayProxyResponseEvent buildErrorResponse(AwsLambdaError error) {
    return ApiGatewayResponse.builder()
            .setStatusCode(Integer.valueOf(error.getCode()))
            .setObjectBody(error)
            .setHeaders(applicationJsonHeaders())
            .build();
  }

  public static Map<String, String> applicationJsonHeaders() {
    Map<String, String> headers = new HashMap<>();
    headers.put("Content-Type", "application/json");
    return headers;
  }
}

// Node: asString
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


// Node: toPlainString
package net.chrisrichardson.ftgo.accountservice.api;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.Money;

public class AuthorizeCommand implements Command {
  private long consumerId;
  private Long orderId;
  private Money orderTotal;

  private AuthorizeCommand() {
  }

  public AuthorizeCommand(long consumerId, Long orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  public long getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }

  public Long getOrderId() {

    return orderId;

  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service/src/main/java/net/chrisrichardson/ftgo/accountservice/api/AuthorizeCommand.java:AuthorizeCommand.<init>
// Node: AuthorizeCommand
package net.chrisrichardson.ftgo.accountingservice.domain;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.Money;

public class AuthorizeCommandInternal implements AccountCommand, Command {
  private String consumerId;
  private String orderId;
  private Money orderTotal;

  public String getOrderId() {
    return orderId;
  }

  public void setOrderId(String orderId) {
    this.orderId = orderId;
  }

  public AuthorizeCommandInternal(String consumerId, String orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  private AuthorizeCommandInternal() {
  }

  public String getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(String consumerId) {
    this.consumerId = consumerId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }
}


package net.chrisrichardson.ftgo.accountingservice.domain;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.Money;


public class ReverseAuthorizationCommandInternal implements AccountCommand, Command {
  private String consumerId;
  private String orderId;
  private Money orderTotal;

  public String getOrderId() {
    return orderId;
  }

  public void setOrderId(String orderId) {
    this.orderId = orderId;
  }

  public ReverseAuthorizationCommandInternal(String consumerId, String orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  private ReverseAuthorizationCommandInternal() {
  }

  public String getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(String consumerId) {
    this.consumerId = consumerId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }
}


package net.chrisrichardson.ftgo.accountingservice.domain;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.Money;


public class ReviseAuthorizationCommandInternal implements AccountCommand, Command {
  private String consumerId;
  private String orderId;
  private Money orderTotal;

  public String getOrderId() {
    return orderId;
  }

  public void setOrderId(String orderId) {
    this.orderId = orderId;
  }

  public ReviseAuthorizationCommandInternal(String consumerId, String orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  private ReviseAuthorizationCommandInternal() {
  }

  public String getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(String consumerId) {
    this.consumerId = consumerId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }
}


// Node: ReviseAuthorizationCommandInternal
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


// Node: commandHandlers
// Node: fromChannel
// Node: onMessage
// Node: authorize
// Node: getCommand
// Node: update
// Node: makeAuthorizeCommandInternal
// Node: replyingTo
// Node: catching
// Node: withFailure
// Node: AccountDisabledReply
// Node: reverseAuthorization
// Node: makeReverseAuthorizeCommandInternal
// Node: reviseAuthorization
// Node: makeReviseAuthorizeCommandInternal
// Node: send
package net.chrisrichardson.ftgo.cqrs.orderhistory;

import io.eventuate.tram.events.common.DomainEvent;

public class DeliveryPickedUp implements DomainEvent {
  private String orderId;

  public String getOrderId() {
    return orderId;
  }
}


// Node: notePickedUp
package net.chrisrichardson.ftgo.cqrs.orderhistory.web;

import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;

public class GetOrderResponse {
  private String orderId;
  private OrderState status;
  private long restaurantId;
  private String restaurantName;


  private GetOrderResponse() {
  }

  public OrderState getStatus() {
    return status;
  }

  public void setStatus(OrderState status) {
    this.status = status;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public GetOrderResponse(String orderId, OrderState status, long restaurantId, String restaurantName) {
    this.orderId = orderId;
    this.status = status;
    this.restaurantId = restaurantId;
    this.restaurantName = restaurantName;
  }


  public String getOrderId() {
    return orderId;
  }

  public void setOrderId(String orderId) {
    this.orderId = orderId;
  }

  public String getRestaurantName() {
    return restaurantName;
  }

  public void setRestaurantName(String restaurantName) {
    this.restaurantName = restaurantName;
  }
}


// Node: ifPresent
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


// Node: handleDeliveryPickedUp
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


// Node: channelMapping
// Node: DefaultChannelMappingBuilder
// Node: withSuccess
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


// Node: confirmOrderRevision
// Node: ConfirmReviseOrderCommand
// Node: getOrderRevision
// Node: to
// Node: confirmTicketRevision
// Node: ReviseAuthorization
// Node: undoBeginReviseTicket
// Node: beginReviseTicket
// Node: undoBeginReviseOrder
// Node: UndoBeginReviseOrderCommand
// Node: beginReviseOrder
// Node: BeginReviseOrderCommand
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


// Node: CreateOrderSagaState
// Node: makeCreateTicketCommand
// Node: makeCancelCreateTicketCommand
// Node: makeRejectOrderCommand
// Node: RejectOrderCommand
// Node: makeValidateOrderByConsumerCommand
// Node: ValidateOrderByConsumer
// Node: makeAuthorizeCommand
// Node: withConsumerId
// Node: withOrderId
// Node: withOrderTotal
// Node: makeApproveOrderCommand
// Node: ApproveOrderCommand
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


// Node: confirmOrderCancel
// Node: ConfirmCancelOrderCommand
// Node: confirmTicketCancel
// Node: ReverseAuthorizationCommand
// Node: undoBeginCancelTicket
// Node: beginCancelTicket
// Node: undoBeginCancel
// Node: UndoBeginCancelCommand
// Node: beginCancel
// Node: BeginCancelCommand
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


package net.chrisrichardson.ftgo.orderservice.service;

import io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder;
import net.chrisrichardson.ftgo.orderservice.domain.OrderRepository;
import net.chrisrichardson.ftgo.orderservice.domain.OrderRevision;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.orderservice.domain.RevisedOrder;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.*;
import io.eventuate.tram.commands.consumer.CommandHandlers;
import io.eventuate.tram.commands.consumer.CommandMessage;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.messaging.common.Message;
import io.eventuate.tram.sagas.participant.SagaCommandHandlersBuilder;
import net.chrisrichardson.ftgo.common.UnsupportedStateTransitionException;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.Optional;

import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withFailure;
import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withSuccess;

public class OrderCommandHandlers {

  @Autowired
  private OrderService orderService;

  public CommandHandlers commandHandlers() {
    return SagaCommandHandlersBuilder
          .fromChannel("orderService")
          .onMessage(ApproveOrderCommand.class, this::approveOrder)
          .onMessage(RejectOrderCommand.class, this::rejectOrder)

          .onMessage(BeginCancelCommand.class, this::beginCancel)
          .onMessage(UndoBeginCancelCommand.class, this::undoCancel)
          .onMessage(ConfirmCancelOrderCommand.class, this::confirmCancel)

          .onMessage(BeginReviseOrderCommand.class, this::beginReviseOrder)
          .onMessage(UndoBeginReviseOrderCommand.class, this::undoPendingRevision)
          .onMessage(ConfirmReviseOrderCommand.class, this::confirmRevision)
          .build();

  }

  public Message approveOrder(CommandMessage<ApproveOrderCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    orderService.approveOrder(orderId);
    return withSuccess();
  }


  public Message rejectOrder(CommandMessage<RejectOrderCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    orderService.rejectOrder(orderId);
    return withSuccess();
  }


  public Message beginCancel(CommandMessage<BeginCancelCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    try {
      orderService.beginCancel(orderId);
      return withSuccess();
    } catch (UnsupportedStateTransitionException e) {
      return withFailure();
    }
  }


  public Message undoCancel(CommandMessage<UndoBeginCancelCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    orderService.undoCancel(orderId);
    return withSuccess();
  }

  public Message confirmCancel(CommandMessage<ConfirmCancelOrderCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    orderService.confirmCancelled(orderId);
    return withSuccess();
  }


  public Message beginReviseOrder(CommandMessage<BeginReviseOrderCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    OrderRevision revision = cm.getCommand().getRevision();
    try {
      return orderService.beginReviseOrder(orderId, revision).map(result -> withSuccess(new BeginReviseOrderReply(result.getChange().getNewOrderTotal()))).orElseGet(CommandHandlerReplyBuilder::withFailure);
    } catch (UnsupportedStateTransitionException e) {
      return withFailure();
    }
  }

  public Message undoPendingRevision(CommandMessage <UndoBeginReviseOrderCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    orderService.undoPendingRevision(orderId);
    return withSuccess();
  }

  public Message confirmRevision(CommandMessage<ConfirmReviseOrderCommand> cm) {
    long orderId = cm.getCommand().getOrderId();
    OrderRevision revision = cm.getCommand().getRevision();
    orderService.confirmRevision(orderId, revision);
    return withSuccess();
  }

}


// Node: approveOrder
// Node: rejectOrder
// Node: undoCancel
// Node: confirmCancelled
// Node: getRevision
// Node: BeginReviseOrderReply
// Node: getChange
// Node: undoPendingRevision
package net.chrisrichardson.ftgo.orderservice.web;

public class GetRestaurantResponse {
  private long restaurantId;

  private GetRestaurantResponse() {
  }

  public GetRestaurantResponse(long restaurantId) {

    this.restaurantId = restaurantId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }
}


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


package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import net.chrisrichardson.ftgo.orderservice.domain.OrderRevision;

public class BeginReviseOrderCommand extends OrderCommand {

  private BeginReviseOrderCommand() {
  }

  public BeginReviseOrderCommand(long orderId, OrderRevision revision) {
    super(orderId);
    this.revision = revision;
  }

  private OrderRevision revision;

  public OrderRevision getRevision() {
    return revision;
  }

  public void setRevision(OrderRevision revision) {
    this.revision = revision;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/BeginReviseOrderCommand.java:BeginReviseOrderCommand.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import net.chrisrichardson.ftgo.orderservice.domain.OrderRevision;

public class ConfirmReviseOrderCommand extends OrderCommand {

  private ConfirmReviseOrderCommand() {
  }

  public ConfirmReviseOrderCommand(long orderId, OrderRevision revision) {
    super(orderId);
    this.revision = revision;
  }

  private OrderRevision revision;

  public OrderRevision getRevision() {
    return revision;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/ConfirmReviseOrderCommand.java:ConfirmReviseOrderCommand.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import io.eventuate.tram.commands.common.Success;
import io.eventuate.tram.sagas.simpledsl.CommandEndpoint;
import io.eventuate.tram.sagas.simpledsl.CommandEndpointBuilder;
import net.chrisrichardson.ftgo.kitchenservice.api.*;

public class KitchenServiceProxy {

  public final CommandEndpoint<CreateTicket> create = CommandEndpointBuilder
          .forCommand(CreateTicket.class)
          .withChannel(KitchenServiceChannels.COMMAND_CHANNEL)
          .withReply(CreateTicketReply.class)
          .build();

  public final CommandEndpoint<ConfirmCreateTicket> confirmCreate = CommandEndpointBuilder
          .forCommand(ConfirmCreateTicket.class)
          .withChannel(KitchenServiceChannels.COMMAND_CHANNEL)
          .withReply(Success.class)
          .build();
  public final CommandEndpoint<CancelCreateTicket> cancel = CommandEndpointBuilder
          .forCommand(CancelCreateTicket.class)
          .withChannel(KitchenServiceChannels.COMMAND_CHANNEL)
          .withReply(Success.class)
          .build();

}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/KitchenServiceProxy.java:KitchenServiceProxy.<init>
// Node: forCommand
// Node: withChannel
// Node: withReply
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

public class UndoBeginCancelCommand extends OrderCommand {
  public UndoBeginCancelCommand(long orderId) {
    super(orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/UndoBeginCancelCommand.java:UndoBeginCancelCommand.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import io.eventuate.tram.commands.common.Success;
import io.eventuate.tram.sagas.simpledsl.CommandEndpoint;
import io.eventuate.tram.sagas.simpledsl.CommandEndpointBuilder;
import net.chrisrichardson.ftgo.consumerservice.api.ConsumerServiceChannels;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;

public class ConsumerServiceProxy {


  public final CommandEndpoint<ValidateOrderByConsumer> validateOrder= CommandEndpointBuilder
          .forCommand(ValidateOrderByConsumer.class)
          .withChannel(ConsumerServiceChannels.consumerServiceChannel)
          .withReply(Success.class)
          .build();

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/ConsumerServiceProxy.java:ConsumerServiceProxy.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

public class RejectOrderCommand extends OrderCommand {

  private RejectOrderCommand() {
  }

  public RejectOrderCommand(long orderId) {
    super(orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/RejectOrderCommand.java:RejectOrderCommand.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;


import net.chrisrichardson.ftgo.common.Money;

public class BeginReviseOrderReply {
  private Money revisedOrderTotal;

  public BeginReviseOrderReply(Money revisedOrderTotal) {
    this.revisedOrderTotal = revisedOrderTotal;
  }

  public BeginReviseOrderReply() {
  }

  public Money getRevisedOrderTotal() {
    return revisedOrderTotal;
  }

  public void setRevisedOrderTotal(Money revisedOrderTotal) {
    this.revisedOrderTotal = revisedOrderTotal;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/BeginReviseOrderReply.java:BeginReviseOrderReply.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import io.eventuate.tram.commands.common.Command;

public abstract class OrderCommand implements Command {

  private long orderId;

  protected OrderCommand() {
  }

  protected OrderCommand(long orderId) {
    this.orderId = orderId;
  }

  public long getOrderId() {
    return orderId;
  }

  public void setOrderId(long orderId) {
    this.orderId = orderId;
  }
}


package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

public class BeginCancelCommand extends OrderCommand {

  private BeginCancelCommand() {
  }

  public BeginCancelCommand(long orderId) {
    super(orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/BeginCancelCommand.java:BeginCancelCommand.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

public class ConfirmCancelOrderCommand extends OrderCommand {

  private ConfirmCancelOrderCommand() {
  }

  public ConfirmCancelOrderCommand(long orderId) {
    super(orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/ConfirmCancelOrderCommand.java:ConfirmCancelOrderCommand.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

public class ApproveOrderCommand extends OrderCommand {

  private ApproveOrderCommand() {
  }

  public ApproveOrderCommand(long orderId) {
    super(orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/ApproveOrderCommand.java:ApproveOrderCommand.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import io.eventuate.tram.commands.common.Success;
import io.eventuate.tram.sagas.simpledsl.CommandEndpoint;
import io.eventuate.tram.sagas.simpledsl.CommandEndpointBuilder;
import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;

public class OrderServiceProxy {

  public final CommandEndpoint<RejectOrderCommand> reject = CommandEndpointBuilder
          .forCommand(RejectOrderCommand.class)
          .withChannel(OrderServiceChannels.COMMAND_CHANNEL)
          .withReply(Success.class)
          .build();

  public final CommandEndpoint<ApproveOrderCommand> approve = CommandEndpointBuilder
          .forCommand(ApproveOrderCommand.class)
          .withChannel(OrderServiceChannels.COMMAND_CHANNEL)
          .withReply(Success.class)
          .build();

}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/OrderServiceProxy.java:OrderServiceProxy.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

import io.eventuate.tram.commands.common.Success;
import io.eventuate.tram.sagas.simpledsl.CommandEndpoint;
import io.eventuate.tram.sagas.simpledsl.CommandEndpointBuilder;
import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;

public class AccountingServiceProxy {

  public final CommandEndpoint<AuthorizeCommand> authorize= CommandEndpointBuilder
          .forCommand(AuthorizeCommand.class)
          .withChannel(AccountingServiceChannels.accountingServiceChannel)
          .withReply(Success.class)
          .build();

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/AccountingServiceProxy.java:AccountingServiceProxy.<init>
package net.chrisrichardson.ftgo.orderservice.sagaparticipants;

public class UndoBeginReviseOrderCommand extends OrderCommand {

  protected UndoBeginReviseOrderCommand() {
  }

  public UndoBeginReviseOrderCommand(long orderId) {
    super(orderId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/UndoBeginReviseOrderCommand.java:UndoBeginReviseOrderCommand.<init>
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


// Node: counter
// Node: increment
// Node: updateOrder
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


// Node: makeCreateOrderSaga
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

// Node: saga
// Node: expect
// Node: command
// Node: makeValidateOrderByConsumer
// Node: andGiven
// Node: successReply
// Node: shouldRejectOrderDueToConsumerVerificationFailed
// Node: failureReply
// Node: shouldRejectDueToFailedAuthorizxation
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


// Node: createTicket
package net.chrisrichardson.ftgo.kitchenservice.messagehandlers;

import io.eventuate.tram.commands.consumer.CommandHandlers;
import io.eventuate.tram.commands.consumer.CommandMessage;
import io.eventuate.tram.messaging.common.Message;
import io.eventuate.tram.sagas.participant.SagaCommandHandlersBuilder;
import net.chrisrichardson.ftgo.kitchenservice.api.*;
import net.chrisrichardson.ftgo.kitchenservice.domain.RestaurantDetailsVerificationException;
import net.chrisrichardson.ftgo.kitchenservice.domain.Ticket;
import net.chrisrichardson.ftgo.kitchenservice.domain.KitchenService;
import org.springframework.beans.factory.annotation.Autowired;

import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withFailure;
import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withSuccess;
import static io.eventuate.tram.sagas.participant.SagaReplyMessageBuilder.withLock;

public class KitchenServiceCommandHandler {

  @Autowired
  private KitchenService kitchenService;

  public CommandHandlers commandHandlers() {
    return SagaCommandHandlersBuilder
            .fromChannel(KitchenServiceChannels.COMMAND_CHANNEL)
            .onMessage(CreateTicket.class, this::createTicket)
            .onMessage(ConfirmCreateTicket.class, this::confirmCreateTicket)
            .onMessage(CancelCreateTicket.class, this::cancelCreateTicket)

            .onMessage(BeginCancelTicketCommand.class, this::beginCancelTicket)
            .onMessage(ConfirmCancelTicketCommand.class, this::confirmCancelTicket)
            .onMessage(UndoBeginCancelTicketCommand.class, this::undoBeginCancelTicket)

            .onMessage(BeginReviseTicketCommand.class, this::beginReviseTicket)
            .onMessage(UndoBeginReviseTicketCommand.class, this::undoBeginReviseTicket)
            .onMessage(ConfirmReviseTicketCommand.class, this::confirmReviseTicket)
            .build();
  }

  private Message createTicket(CommandMessage<CreateTicket>
                                                cm) {
    CreateTicket command = cm.getCommand();
    long restaurantId = command.getRestaurantId();
    Long ticketId = command.getOrderId();
    TicketDetails ticketDetails = command.getTicketDetails();


    try {
      Ticket ticket = kitchenService.createTicket(restaurantId, ticketId, ticketDetails);
      CreateTicketReply reply = new CreateTicketReply(ticket.getId());
      return withLock(Ticket.class, ticket.getId()).withSuccess(reply);
    } catch (RestaurantDetailsVerificationException e) {
      return withFailure();
    }
  }

  private Message confirmCreateTicket
          (CommandMessage<ConfirmCreateTicket> cm) {
    Long ticketId = cm.getCommand().getTicketId();
    kitchenService.confirmCreateTicket(ticketId);
    return withSuccess();
  }

  private Message cancelCreateTicket
          (CommandMessage<CancelCreateTicket> cm) {
    Long ticketId = cm.getCommand().getTicketId();
    kitchenService.cancelCreateTicket(ticketId);
    return withSuccess();
  }


  private Message beginCancelTicket(CommandMessage<BeginCancelTicketCommand> cm) {
    kitchenService.cancelTicket(cm.getCommand().getRestaurantId(), cm.getCommand().getOrderId());
    return withSuccess();
  }
  private Message confirmCancelTicket(CommandMessage<ConfirmCancelTicketCommand> cm) {
    kitchenService.confirmCancelTicket(cm.getCommand().getRestaurantId(), cm.getCommand().getOrderId());
    return withSuccess();
  }

  private Message undoBeginCancelTicket(CommandMessage<UndoBeginCancelTicketCommand> cm) {
    kitchenService.undoCancel(cm.getCommand().getRestaurantId(), cm.getCommand().getOrderId());
    return withSuccess();
  }

  public Message beginReviseTicket(CommandMessage<BeginReviseTicketCommand> cm) {
    kitchenService.beginReviseOrder(cm.getCommand().getRestaurantId(), cm.getCommand().getOrderId(), cm.getCommand().getRevisedOrderLineItems());
    return withSuccess();
  }

  public Message undoBeginReviseTicket(CommandMessage<UndoBeginReviseTicketCommand> cm) {
    kitchenService.undoBeginReviseOrder(cm.getCommand().getRestaurantId(), cm.getCommand().getOrderId());
    return withSuccess();
  }

  public Message confirmReviseTicket(CommandMessage<ConfirmReviseTicketCommand> cm) {
    kitchenService.confirmReviseTicket(cm.getCommand().getRestaurantId(), cm.getCommand().getOrderId(), cm.getCommand().getRevisedOrderLineItems());
    return withSuccess();
  }


}



// Node: withLock
// Node: confirmCreateTicket
// Node: cancelCreateTicket
// Node: cancelTicket
// Node: confirmCancelTicket
package net.chrisrichardson.ftgo.kitchenservice.web;

public class GetRestaurantResponse  {
  private long restaurantId;

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public GetRestaurantResponse() {

  }

  public GetRestaurantResponse(long restaurantId) {
    this.restaurantId = restaurantId;
  }
}


package net.chrisrichardson.ftgo.kitchenservice.domain;

public class CancelCommand {
  private long orderId;
  private boolean force;

  public long getOrderId() {
    return orderId;
  }

  public boolean isForce() {
    return force;
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-consumer-service/src/main/java/net/chrisrichardson/ftgo/consumerservice/api/ValidateOrderByConsumer.java:ValidateOrderByConsumer.<init>
package net.chrisrichardson.ftgo.consumerservice.web;

public class CreateConsumerResponse {
  private long consumerId;

  public long getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  public CreateConsumerResponse() {

  }

  public CreateConsumerResponse(long consumerId) {
    this.consumerId = consumerId;
  }
}


package net.chrisrichardson.ftgo.consumerservice.domain;

import io.eventuate.tram.commands.consumer.CommandHandlers;
import io.eventuate.tram.commands.consumer.CommandMessage;
import io.eventuate.tram.messaging.common.Message;
import io.eventuate.tram.sagas.participant.SagaCommandHandlersBuilder;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import org.springframework.beans.factory.annotation.Autowired;

import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withFailure;
import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withSuccess;

public class ConsumerServiceCommandHandlers  {

  @Autowired
  private ConsumerService consumerService;

  public CommandHandlers commandHandlers() {
    return SagaCommandHandlersBuilder
              .fromChannel("consumerService")
              .onMessage(ValidateOrderByConsumer.class, this::validateOrderForConsumer)
              .build();
  }

  private Message validateOrderForConsumer(CommandMessage<ValidateOrderByConsumer> cm) {
    try {
      consumerService.validateOrderForConsumer(cm.getCommand().getConsumerId(), cm.getCommand().getOrderTotal());
      return withSuccess();
    } catch (ConsumerVerificationFailedException e) {
      return withFailure();
    }
  }
}


// Node: validateOrderForConsumer
package net.chrisrichardson.ftgo.accountservice.api;

import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.Money;

public class ReviseAuthorization implements Command {
  private long consumerId;
  private Long orderId;
  private Money orderTotal;

  private ReviseAuthorization() {
  }

  public ReviseAuthorization(long consumerId, Long orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  public long getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }

  public Long getOrderId() {

    return orderId;

  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service-api/src/main/java/net/chrisrichardson/ftgo/accountservice/api/ReviseAuthorization.java:ReviseAuthorization.<init>
package net.chrisrichardson.ftgo.accountservice.api;


import io.eventuate.tram.commands.common.Command;
import net.chrisrichardson.ftgo.common.Money;

public class ReverseAuthorizationCommand implements Command {
  private long consumerId;
  private Long orderId;
  private Money orderTotal;

  private ReverseAuthorizationCommand() {
  }

  public ReverseAuthorizationCommand(long consumerId, Long orderId, Money orderTotal) {
    this.consumerId = consumerId;
    this.orderId = orderId;
    this.orderTotal = orderTotal;
  }

  public long getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }

  public Long getOrderId() {

    return orderId;

  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-accounting-service-api/src/main/java/net/chrisrichardson/ftgo/accountservice/api/ReverseAuthorizationCommand.java:ReverseAuthorizationCommand.<init>
