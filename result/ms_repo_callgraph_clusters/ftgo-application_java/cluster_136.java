// Cluster 136

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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/sagaparticipants/OrderCommand.java:OrderCommand.<init>
// Node: OrderCommand
