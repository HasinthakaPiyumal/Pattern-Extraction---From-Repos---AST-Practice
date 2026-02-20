// Cluster 19

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


// Node: setRevisedOrderLineItems
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


