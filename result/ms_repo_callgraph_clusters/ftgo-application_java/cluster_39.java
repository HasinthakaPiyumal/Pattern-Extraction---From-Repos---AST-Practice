// Cluster 39

package net.chrisrichardson.ftgo.apiagateway.consumers;

import org.springframework.boot.context.properties.ConfigurationProperties;

import javax.validation.constraints.NotNull;

@ConfigurationProperties(prefix = "consumer.destinations")
public class ConsumerDestinations {

  @NotNull
  private String consumerServiceUrl;

  public String getConsumerServiceUrl() {
    return consumerServiceUrl;
  }

  public void setConsumerServiceUrl(String consumerServiceUrl) {
    this.consumerServiceUrl = consumerServiceUrl;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-api-gateway/src/main/java/net/chrisrichardson/ftgo/apiagateway/consumers/ConsumerDestinations.java:ConsumerDestinations.<init>
// Node: ConfigurationProperties
package net.chrisrichardson.ftgo.apiagateway.orders;

import org.springframework.boot.context.properties.ConfigurationProperties;

import javax.validation.constraints.NotNull;

@ConfigurationProperties(prefix = "order.destinations")
public class OrderDestinations {

  @NotNull
  private String orderServiceUrl;

  @NotNull
  private String orderHistoryServiceUrl;

  public String getOrderHistoryServiceUrl() {
    return orderHistoryServiceUrl;
  }

  public void setOrderHistoryServiceUrl(String orderHistoryServiceUrl) {
    this.orderHistoryServiceUrl = orderHistoryServiceUrl;
  }


  public String getOrderServiceUrl() {
    return orderServiceUrl;
  }

  public void setOrderServiceUrl(String orderServiceUrl) {
    this.orderServiceUrl = orderServiceUrl;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-api-gateway/src/main/java/net/chrisrichardson/ftgo/apiagateway/orders/OrderDestinations.java:OrderDestinations.<init>
