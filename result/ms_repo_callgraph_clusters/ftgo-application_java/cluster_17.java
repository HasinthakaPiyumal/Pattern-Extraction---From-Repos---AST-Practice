// Cluster 17

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


// Node: setRestaurantName
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


