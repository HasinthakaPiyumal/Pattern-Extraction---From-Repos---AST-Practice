// Cluster 143

package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.common.DomainEvent;

public class OrderLineItemChangeQueued implements DomainEvent {
  public OrderLineItemChangeQueued(String lineItemId, int newQuantity) {

  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderLineItemChangeQueued.java:OrderLineItemChangeQueued.<init>
// Node: OrderLineItemChangeQueued
