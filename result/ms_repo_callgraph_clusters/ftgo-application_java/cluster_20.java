// Cluster 20

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


// Node: setOrderId
// Node: CreateOrderResponse
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


// Node: AuthorizeCommandInternal
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


// Node: ReverseAuthorizationCommandInternal
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


