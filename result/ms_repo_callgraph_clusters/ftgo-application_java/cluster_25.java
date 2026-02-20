// Cluster 25

package net.chrisrichardson.ftgo.kitchenservice.api.events;

import java.time.LocalDateTime;

public class TicketAcceptedEvent implements TicketDomainEvent {
  private LocalDateTime readyBy;

  public TicketAcceptedEvent() {
  }

  public TicketAcceptedEvent(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }

  public LocalDateTime getReadyBy() {
    return readyBy;
  }

  public void setReadyBy(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }
}


// Node: setReadyBy
package net.chrisrichardson.ftgo.kitchenservice.api.web;

import java.time.LocalDateTime;

public class TicketAcceptance {
  private LocalDateTime readyBy;

  public TicketAcceptance() {
  }

  public TicketAcceptance(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }

  public LocalDateTime getReadyBy() {
    return readyBy;
  }

  public void setReadyBy(LocalDateTime readyBy) {
    this.readyBy = readyBy;
  }
}


