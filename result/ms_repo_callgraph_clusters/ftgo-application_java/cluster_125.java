// Cluster 125

// Node: OrderServiceClient
package net.chrisrichardson.ftgo.orderservice.grpc;


import io.grpc.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;
import java.util.stream.IntStream;

import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;

public class OrderServiceClient {
  private static final Logger logger = Logger.getLogger(OrderServiceClient.class.getName());

  private final ManagedChannel channel;
  private final OrderServiceGrpc.OrderServiceBlockingStub clientStub;

  public OrderServiceClient(String host, int port) {
    channel = ManagedChannelBuilder.forAddress(host, port)
            .usePlaintext()
            .build();
    clientStub = OrderServiceGrpc.newBlockingStub(channel);
  }

  public void shutdown() throws InterruptedException {
    channel.shutdown().awaitTermination(5, TimeUnit.SECONDS);
  }

  public long createOrder(long consumerId, long restaurantId, List<MenuItemIdAndQuantity> lineItems, net.chrisrichardson.ftgo.common.Address deliveryAddress, LocalDateTime deliveryTime) {
    CreateOrderRequest.Builder builder = CreateOrderRequest.newBuilder()
            .setConsumerId(consumerId)
            .setRestaurantId(restaurantId)
            .setDeliveryAddress(makeAddress(deliveryAddress))
            .setDeliveryTime(DateTimeFormatter.ISO_LOCAL_DATE_TIME.format(deliveryTime));
    lineItems.forEach(li -> builder.addLineItems(LineItem.newBuilder().setQuantity(li.getQuantity()).setMenuItemId(li.getMenuItemId())));
    CreateOrderReply response = clientStub.createOrder(builder.build());
    return response.getOrderId();
  }

  private Address makeAddress(net.chrisrichardson.ftgo.common.Address address) {
    Address.Builder builder = Address.newBuilder()
            .setStreet1(address.getStreet1());
    if (address.getStreet2() != null)
      builder.setStreet2(address.getStreet2());
    builder
            .setCity(address.getCity())
            .setState(address.getState())
            .setZip(address.getZip());
    return builder.build();
  }


}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/integration-test/java/net/chrisrichardson/ftgo/orderservice/grpc/OrderServiceClient.java:OrderServiceClient.<init>
// Node: forAddress
// Node: usePlaintext
// Node: newBlockingStub
// Node: shutdown
// Node: awaitTermination
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


// Node: handleBeginReviseOrderReply
// Node: info
// Node: getRevisedOrderTotal
// Node: setRevisedOrderTotal
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


package net.chrisrichardson.ftgo.orderservice.grpc;

import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GrpcConfiguration {

  @Bean
  public OrderServiceServer helloWorldServer(OrderService orderService) {
    return new OrderServiceServer(orderService);
  }
}


// Node: helloWorldServer
// Node: OrderServiceServer
package net.chrisrichardson.ftgo.orderservice.grpc;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.stub.StreamObserver;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.orderservice.domain.DeliveryInformation;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.domain.OrderService;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;
import org.apache.commons.lang.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

import static java.util.stream.Collectors.toList;

public class OrderServiceServer {
  private static final Logger logger = LoggerFactory.getLogger(OrderServiceServer.class);

  private int port = 50051;
  private Server server;
  private OrderService orderService;

  public OrderServiceServer(OrderService orderService) {
    this.orderService = orderService;
  }

  @PostConstruct
  public void start() throws IOException {
    server = ServerBuilder.forPort(port)
            .addService(new OrderServiceImpl())
            .build()
            .start();
    logger.info("Server started, listening on " + port);
  }

  @PreDestroy
  public void stop() {
    if (server != null) {
      logger.info("*** shutting down gRPC server since JVM is shutting down");
      server.shutdown();
      logger.info("*** server shut down");
    }
  }


  private class OrderServiceImpl extends OrderServiceGrpc.OrderServiceImplBase {

    @Override
    public void createOrder(CreateOrderRequest req, StreamObserver<CreateOrderReply> responseObserver) {
      List<LineItem> lineItemsList = req.getLineItemsList();
      Order order = orderService.createOrder(req.getConsumerId(),
              req.getRestaurantId(),
              new DeliveryInformation(LocalDateTime.parse(req.getDeliveryTime(), DateTimeFormatter.ISO_LOCAL_DATE_TIME), makeAddress(req.getDeliveryAddress())),
              lineItemsList.stream().map(x -> new MenuItemIdAndQuantity(x.getMenuItemId(), x.getQuantity())).collect(toList())
      );
      CreateOrderReply reply = CreateOrderReply.newBuilder().setOrderId(order.getId()).build();
      responseObserver.onNext(reply);
      responseObserver.onCompleted();
    }

    private Address makeAddress(net.chrisrichardson.ftgo.orderservice.grpc.Address address) {
      return new Address(address.getStreet1(), nullIfBlank(address.getStreet2()), address.getCity(), address.getState(), address.getZip());
    }

    @Override
    public void cancelOrder(CancelOrderRequest req, StreamObserver<CancelOrderReply> responseObserver) {
      CancelOrderReply reply = CancelOrderReply.newBuilder().setMessage("Hello " + req.getName()).build();
      responseObserver.onNext(reply);
      responseObserver.onCompleted();
    }

    @Override
    public void reviseOrder(ReviseOrderRequest req, StreamObserver<ReviseOrderReply> responseObserver) {
      ReviseOrderReply reply = ReviseOrderReply.newBuilder().setMessage("Hello " + req.getName()).build();
      responseObserver.onNext(reply);
      responseObserver.onCompleted();
    }
  }

  private String nullIfBlank(String s) {
    return StringUtils.isBlank(s) ? null : s;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/grpc/OrderServiceServer.java:OrderServiceServer.<init>
// Node: start
// Node: forPort
// Node: addService
// Node: OrderServiceImpl
// Node: stop
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


