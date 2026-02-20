// Cluster 141

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


// Node: getCurrentOrderTotal
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


