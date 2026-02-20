// Cluster 140

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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderCancelRequested.java:OrderCancelRequested.<init>
// Node: OrderCancelRequested
