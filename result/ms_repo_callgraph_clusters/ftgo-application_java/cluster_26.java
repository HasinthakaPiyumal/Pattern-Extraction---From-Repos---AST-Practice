// Cluster 26

package net.chrisrichardson.ftgo.restaurantservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantDomainEventPublisher;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryserviceMessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class DeliveryserviceMessagingBase {

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public RestaurantDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new RestaurantDomainEventPublisher(eventPublisher);
    }
  }


  @Autowired
  private RestaurantDomainEventPublisher restaurantDomainEventPublisher;

  protected void restaurantCreated() {
    Restaurant restaurant = new Restaurant("Yummy Indian", new RestaurantMenu(Collections.emptyList()));
    restaurant.setId(99L);
    restaurantDomainEventPublisher.publish(restaurant,
            Collections.singletonList(new RestaurantCreated(restaurant.getName(), new Address("1 Main Street", "Unit 99", "Oakland", "CA", "94611"),
                    restaurant.getMenu())));
  }

}


// Node: orderAggregateEventPublisher
// Node: RestaurantDomainEventPublisher
package net.chrisrichardson.ftgo.restaurantservice.domain;

import io.eventuate.tram.events.aggregates.AbstractAggregateDomainEventPublisher;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantDomainEvent;

public class RestaurantDomainEventPublisher extends AbstractAggregateDomainEventPublisher<Restaurant, RestaurantDomainEvent> {
  public RestaurantDomainEventPublisher(DomainEventPublisher eventPublisher) {
    super(eventPublisher, Restaurant.class, Restaurant::getId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-restaurant-service/src/main/java/net/chrisrichardson/ftgo/restaurantservice/domain/RestaurantDomainEventPublisher.java:RestaurantDomainEventPublisher.<init>
package net.chrisrichardson.ftgo.restaurantservice.domain;

import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableJpaRepositories
@EnableTransactionManagement
@EntityScan
@Import({TramEventsPublisherConfiguration.class, CommonConfiguration.class})
public class RestaurantServiceDomainConfiguration {

  @Bean
  public RestaurantService restaurantService() {
    return new RestaurantService();
  }

  @Bean
  public RestaurantDomainEventPublisher restaurantDomainEventPublisher(DomainEventPublisher domainEventPublisher) {
    return new RestaurantDomainEventPublisher(domainEventPublisher);
  }
}


// Node: restaurantDomainEventPublisher
package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.restaurantservice.RestaurantServiceChannels;
import org.junit.Test;

import static org.junit.Assert.*;

public class RestaurantDomainEventPublisherTest {

  @Test
  public void verifyRestaurantEventChannel() {
    assertEquals(RestaurantServiceChannels.RESTAURANT_EVENT_CHANNEL, new RestaurantDomainEventPublisher(null).getAggregateType().getName());
  }


}

// Node: verifyRestaurantEventChannel
// Node: getAggregateType
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import com.amazonaws.services.dynamodbv2.document.spec.UpdateItemSpec;

import java.util.HashMap;

public class SourceEvent {

  String aggregateType;
  String aggregateId;
  String eventId;

  public SourceEvent(String aggregateType, String aggregateId, String eventId) {
    this.aggregateType = aggregateType;
    this.aggregateId = aggregateId;
    this.eventId = eventId;
  }

  public String getAggregateType() {
    return aggregateType;
  }

  public UpdateItemSpec addDuplicateDetection(UpdateItemSpec spec) {
    HashMap<String, String> nameMap = spec.getNameMap() == null ? new HashMap<>() : new HashMap<>(spec.getNameMap());
    nameMap.put("#duplicateDetection", "events." + aggregateType + aggregateId);
    HashMap<String, Object> valueMap = new HashMap<>(spec.getValueMap());
    valueMap.put(":eventId", eventId);
    return spec.withUpdateExpression(String.format("%s , #duplicateDetection = :eventId", spec.getUpdateExpression()))
            .withNameMap(nameMap)
            .withValueMap(valueMap)
            .withConditionExpression(Expressions.and(spec.getConditionExpression(), "attribute_not_exists(#duplicateDetection) OR #duplicateDetection < :eventId"));
  }

}


package net.chrisrichardson.ftgo.orderservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.domain.OrderDomainEventPublisher;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER_DETAILS;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT_NAME;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryserviceMessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class DeliveryserviceMessagingBase {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public OrderDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new OrderDomainEventPublisher(eventPublisher);
    }
  }

  @Autowired
  private OrderDomainEventPublisher orderAggregateEventPublisher;

  protected void orderCreatedEvent() {
    orderAggregateEventPublisher.publish(CHICKEN_VINDALOO_ORDER,
            Collections.singletonList(new OrderCreatedEvent(CHICKEN_VINDALOO_ORDER_DETAILS, OrderDetailsMother.DELIVERY_ADDRESS, AJANTA_RESTAURANT_NAME)));
  }
}


// Node: OrderDomainEventPublisher
package net.chrisrichardson.ftgo.orderservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.domain.OrderDomainEventPublisher;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.CHICKEN_VINDALOO_ORDER_DETAILS;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT_NAME;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = MessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class MessagingBase {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public OrderDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new OrderDomainEventPublisher(eventPublisher);
    }
  }


  @Autowired
  private OrderDomainEventPublisher orderAggregateEventPublisher;

  protected void orderCreated() {
    orderAggregateEventPublisher.publish(CHICKEN_VINDALOO_ORDER,
            Collections.singletonList(new OrderCreatedEvent(CHICKEN_VINDALOO_ORDER_DETAILS, OrderDetailsMother.DELIVERY_ADDRESS, AJANTA_RESTAURANT_NAME)));
  }

}


package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.AbstractAggregateDomainEventPublisher;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;

public class OrderDomainEventPublisher extends AbstractAggregateDomainEventPublisher<Order, OrderDomainEvent> {


  public OrderDomainEventPublisher(DomainEventPublisher eventPublisher) {
    super(eventPublisher, Order.class, Order::getId);
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/OrderDomainEventPublisher.java:OrderDomainEventPublisher.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.sagas.orchestration.*;
import io.eventuate.tram.sagas.spring.orchestration.SagaOrchestratorConfiguration;
import io.micrometer.core.instrument.MeterRegistry;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.AccountingServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ConsumerServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.KitchenServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.OrderServiceProxy;
import net.chrisrichardson.ftgo.orderservice.sagas.cancelorder.CancelOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.reviseorder.ReviseOrderSaga;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.actuate.autoconfigure.metrics.MeterRegistryCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import java.util.Optional;

@Configuration
@Import({TramEventsPublisherConfiguration.class, SagaOrchestratorConfiguration.class, CommonConfiguration.class})
public class OrderServiceConfiguration {

  @Bean
  public OrderService orderService(SagaInstanceFactory sagaInstanceFactory,
                                   RestaurantRepository restaurantRepository,
                                   OrderRepository orderRepository,
                                   DomainEventPublisher eventPublisher,
                                   CreateOrderSaga createOrderSaga,
                                   CancelOrderSaga cancelOrderSaga,
                                   ReviseOrderSaga reviseOrderSaga,
                                   OrderDomainEventPublisher orderAggregateEventPublisher,
                                   Optional<MeterRegistry> meterRegistry) {

    return new OrderService(sagaInstanceFactory, orderRepository, eventPublisher, restaurantRepository,
            createOrderSaga, cancelOrderSaga, reviseOrderSaga, orderAggregateEventPublisher, meterRegistry);
  }

  @Bean
  public CreateOrderSaga createOrderSaga(OrderServiceProxy orderService, ConsumerServiceProxy consumerService, KitchenServiceProxy kitchenServiceProxy, AccountingServiceProxy accountingService) {
    return new CreateOrderSaga(orderService, consumerService, kitchenServiceProxy, accountingService);
  }

  @Bean
  public CancelOrderSaga cancelOrderSaga() {
    return new CancelOrderSaga();
  }

  @Bean
  public ReviseOrderSaga reviseOrderSaga() {
    return new ReviseOrderSaga();
  }


  @Bean
  public KitchenServiceProxy kitchenServiceProxy() {
    return new KitchenServiceProxy();
  }

  @Bean
  public OrderServiceProxy orderServiceProxy() {
    return new OrderServiceProxy();
  }

  @Bean
  public ConsumerServiceProxy consumerServiceProxy() {
    return new ConsumerServiceProxy();
  }

  @Bean
  public AccountingServiceProxy accountingServiceProxy() {
    return new AccountingServiceProxy();
  }

  @Bean
  public OrderDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
    return new OrderDomainEventPublisher(eventPublisher);
  }

  @Bean
  public MeterRegistryCustomizer meterRegistryCustomizer(@Value("${spring.application.name}") String serviceName) {
    return registry -> registry.config().commonTags("service", serviceName);
  }
}


// Node: meterRegistryCustomizer
// Node: config
// Node: commonTags
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.orderservice.api.OrderServiceChannels;
import org.junit.Test;

import static org.junit.Assert.*;

public class OrderDomainEventPublisherTest {

  @Test
  public void verifyOrderEventChannel() {
    assertEquals(OrderServiceChannels.ORDER_EVENT_CHANNEL, new OrderDomainEventPublisher(null).getAggregateType().getName());
  }

}

// Node: verifyOrderEventChannel
package net.chrisrichardson.ftgo.kitchenservice.contract;

import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.spring.cloudcontractsupport.EventuateContractVerifierConfiguration;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketAcceptedEvent;
import net.chrisrichardson.ftgo.kitchenservice.domain.Ticket;
import net.chrisrichardson.ftgo.kitchenservice.domain.TicketDomainEventPublisher;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.cloud.contract.verifier.messaging.boot.AutoConfigureMessageVerifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.time.LocalDateTime;
import java.util.Collections;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = DeliveryserviceMessagingBase.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@AutoConfigureMessageVerifier
public abstract class DeliveryserviceMessagingBase {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({EventuateContractVerifierConfiguration.class, TramEventsPublisherConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public TicketDomainEventPublisher orderAggregateEventPublisher(DomainEventPublisher eventPublisher) {
      return new TicketDomainEventPublisher(eventPublisher);
    }
  }


  @Autowired
  private TicketDomainEventPublisher ticketDomainEventPublisher;

  protected void ticketAcceptedEvent() {
    Ticket ticket = new Ticket(101L, 99L, new TicketDetails(Collections.emptyList()));
    ticketDomainEventPublisher.publish(ticket,
            Collections.singletonList(new TicketAcceptedEvent(LocalDateTime.now())));
  }

}



// Node: TicketDomainEventPublisher
package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.aggregates.AbstractAggregateDomainEventPublisher;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketDomainEvent;

public class TicketDomainEventPublisher extends AbstractAggregateDomainEventPublisher<Ticket, TicketDomainEvent> {

  public TicketDomainEventPublisher(DomainEventPublisher eventPublisher) {
    super(eventPublisher, Ticket.class, Ticket::getId);
  }

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-kitchen-service/src/main/java/net/chrisrichardson/ftgo/kitchenservice/domain/TicketDomainEventPublisher.java:TicketDomainEventPublisher.<init>
package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableTransactionManagement
@EnableJpaRepositories
@ComponentScan
@EntityScan
@Import({TramEventsPublisherConfiguration.class, CommonConfiguration.class})
public class KitchenDomainConfiguration {

  @Bean
  public KitchenService kitchenService() {
    return new KitchenService();
  }

  @Bean
  public TicketDomainEventPublisher restaurantAggregateEventPublisher(DomainEventPublisher domainEventPublisher) {
    return new TicketDomainEventPublisher(domainEventPublisher);
  }
}


// Node: restaurantAggregateEventPublisher
package net.chrisrichardson.ftgo.kitchenservice.domain;

import net.chrisrichardson.ftgo.kitchenservice.api.KitchenServiceChannels;
import org.junit.Test;

import static org.junit.Assert.*;

public class TicketDomainEventPublisherTest {

  @Test
  public void verifyTicketEventChannel() {
    assertEquals(KitchenServiceChannels.TICKET_EVENT_CHANNEL, new TicketDomainEventPublisher(null).getAggregateType().getName());
  }


}

// Node: verifyTicketEventChannel
