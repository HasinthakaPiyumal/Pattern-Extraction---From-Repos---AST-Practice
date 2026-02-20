// Cluster 115

package net.chrisrichardson.ftgo.accountingservice.messaging;

import io.eventuate.javaclient.spring.jdbc.EmbeddedTestAggregateStoreConfiguration;
import io.eventuate.sync.AggregateRepository;
import io.eventuate.tram.commands.producer.CommandProducer;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.spring.events.publisher.TramEventsPublisherConfiguration;
import io.eventuate.tram.sagas.common.SagaCommandHeaders;
import io.eventuate.tram.sagas.spring.inmemory.TramSagaInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumer;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import io.eventuate.util.test.async.Eventually;
import net.chrisrichardson.ftgo.accountingservice.domain.Account;
import net.chrisrichardson.ftgo.accountingservice.domain.AccountCommand;
import net.chrisrichardson.ftgo.accountservice.api.AccountingServiceChannels;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.consumerservice.domain.ConsumerCreated;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = AccountingServiceCommandHandlerTest.AccountingServiceCommandHandlerTestConfiguration.class)
public class AccountingServiceCommandHandlerTest {

  @Configuration
  @EnableAutoConfiguration
  @Import({AccountingMessagingConfiguration.class,
          TramCommandProducerConfiguration.class,
          EmbeddedTestAggregateStoreConfiguration.class,
          TramEventsPublisherConfiguration.class, // TODO
          TramSagaInMemoryConfiguration.class})
  static public class AccountingServiceCommandHandlerTestConfiguration {
    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }

  }

  @Autowired
  private CommandProducer commandProducer;

  @Autowired
  private TestMessageConsumerFactory testMessageConsumerFactory;

  @Autowired
  private DomainEventPublisher domainEventPublisher;


  @Autowired
  private AggregateRepository<Account, AccountCommand> accountRepository;

  @Test
  public void shouldReply() {

    TestMessageConsumer testMessageConsumer = testMessageConsumerFactory.make();

    long consumerId = System.currentTimeMillis();
    long orderId = 102L;

    domainEventPublisher.publish("net.chrisrichardson.ftgo.consumerservice.domain.Consumer", consumerId, Collections.singletonList(new ConsumerCreated()));

    Eventually.eventually(() -> {
      accountRepository.find(Long.toString(consumerId));
    });

    Money orderTotal = new Money(123);

    String messageId = commandProducer.send(AccountingServiceChannels.accountingServiceChannel, null,
            new AuthorizeCommand(consumerId, orderId, orderTotal),
            testMessageConsumer.getReplyChannel(), withSagaCommandHeaders());

    testMessageConsumer.assertHasReplyTo(messageId);

  }

  // TODO duplicate

  private Map<String, String> withSagaCommandHeaders() {
    Map<String, String> result = new HashMap<>();
    result.put(SagaCommandHeaders.SAGA_TYPE, "MySagaType");
    result.put(SagaCommandHeaders.SAGA_ID, "MySagaId");
    return result;
  }

}

// Node: testMessageConsumerFactory
// Node: TestMessageConsumerFactory
package net.chrisrichardson.ftgo.orderservice.domain;

import com.jayway.jsonpath.JsonPath;
import io.eventuate.tram.commands.common.CommandMessageHeaders;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.messaging.common.Message;
import io.eventuate.tram.sagas.spring.inmemory.TramSagaInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import io.eventuate.util.test.async.Eventually;
import net.chrisrichardson.ftgo.consumerservice.api.ConsumerServiceChannels;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.messaging.OrderServiceMessagingConfiguration;
import net.chrisrichardson.ftgo.orderservice.service.OrderCommandHandlersConfiguration;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;
import net.chrisrichardson.ftgo.orderservice.web.OrderWebConfiguration;
import net.chrisrichardson.ftgo.testutil.FtgoTestUtil;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.function.Predicate;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = OrderServiceIntegrationTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties="eventuate.database.schema=eventuate"
)
public class OrderServiceIntegrationTest {


  public static final String RESTAURANT_ID = "1";
  @Value("${local.server.port}")
  private int port;

  private String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({OrderWebConfiguration.class, OrderServiceMessagingConfiguration.class,  OrderCommandHandlersConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramSagaInMemoryConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }


    @Bean
    public TestMessageConsumer2 mockConsumerService() {
      return new TestMessageConsumer2("mockConsumerService", ConsumerServiceChannels.consumerServiceChannel);
    }
  }

  @Autowired
  private DomainEventPublisher domainEventPublisher;

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Autowired
  private OrderService orderService;

  private static final String CHICKED_VINDALOO_MENU_ITEM_ID = "1";

  @Autowired
  private OrderRepository orderRepository;

  @Autowired
  @Qualifier("mockConsumerService")
  private TestMessageConsumer2  mockConsumerService;

  @Test
  public void shouldCreateOrder() {
    domainEventPublisher.publish("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant", RESTAURANT_ID,
            Collections.singletonList(RestaurantMother.makeAjantaRestaurantCreatedEvent()));

    Eventually.eventually(() -> {
      FtgoTestUtil.assertPresent(restaurantRepository.findById(Long.parseLong(RESTAURANT_ID)));
    });

    long consumerId = 1511300065921L;

    Order order = orderService.createOrder(consumerId, Long.parseLong(RESTAURANT_ID), OrderDetailsMother.DELIVERY_INFORMATION, Collections.singletonList(new MenuItemIdAndQuantity(CHICKED_VINDALOO_MENU_ITEM_ID, 5)));

    FtgoTestUtil.assertPresent(orderRepository.findById(order.getId()));

    String expectedPayload = "{\"consumerId\":1511300065921,\"orderId\":1,\"orderTotal\":\"61.70\"}";

    Message message = mockConsumerService.assertMessageReceived(
            commandMessageOfType(ValidateOrderByConsumer.class.getName()).and(withPayload(expectedPayload)));

    System.out.println("message=" + message);

  }

  private Predicate<? super Message> withPayload(String expectedPayload) {
    return (m) -> expectedPayload.equals(m.getPayload());
  }

  private Predicate<Message> forConsumer(long consumerId) {
    return (m) -> {
      Object doc = com.jayway.jsonpath.Configuration.defaultConfiguration().jsonProvider().parse(m.getPayload());
      Object s = JsonPath.read(doc, "$.consumerId");
      return new Long(consumerId).equals(s);
    };
  }

  private Predicate<Message> commandMessageOfType(String commandType) {
    return (m) -> m.getRequiredHeader(CommandMessageHeaders.COMMAND_TYPE).equals(commandType);
  }

}

package net.chrisrichardson.ftgo.kitchenservice.domain;


import io.eventuate.tram.commands.producer.CommandProducer;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.sagas.common.SagaCommandHeaders;
import io.eventuate.tram.sagas.spring.inmemory.TramSagaInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumer;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.messagehandlers.KitchenServiceMessageHandlersConfiguration;
import net.chrisrichardson.ftgo.kitchenservice.web.KitchenServiceWebConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = KitchenServiceInMemoryIntegrationTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class KitchenServiceInMemoryIntegrationTest {

  private Logger logger = LoggerFactory.getLogger(getClass());

  @Value("${local.server.port}")
  private int port;

  @Configuration
  @EnableAutoConfiguration
  @Import({KitchenServiceWebConfiguration.class, KitchenServiceMessageHandlersConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramSagaInMemoryConfiguration.class})
  public static class TestConfiguration {

    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }


  }

  private String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Autowired
  private CommandProducer commandProducer;

  @Autowired
  private TestMessageConsumerFactory testMessageConsumerFactory;

  @Autowired
  private RestaurantRepository restaurantRepository;

  @Test
  public void shouldCreateTicket() {

    long restaurantId = System.currentTimeMillis();
    Restaurant restaurant = new Restaurant(restaurantId, Collections.emptyList());

    restaurantRepository.save(restaurant);

    TestMessageConsumer testMessageConsumer = testMessageConsumerFactory.make();

    long orderId = 999;
    Money orderTotal = new Money(123);

    TicketDetails orderDetails = new TicketDetails();
    String messageId = commandProducer.send("kitchenService", null,
            new CreateTicket(restaurantId, orderId, orderDetails),
            testMessageConsumer.getReplyChannel(), withSagaCommandHeaders());

    testMessageConsumer.assertHasReplyTo(messageId);

  }

  private Map<String, String> withSagaCommandHeaders() {
    Map<String, String> result = new HashMap<>();
    result.put(SagaCommandHeaders.SAGA_TYPE, "MySagaType");
    result.put(SagaCommandHeaders.SAGA_ID, "MySagaId");
    return result;
  }

}


package net.chrisrichardson.ftgo.consumerservice;


import io.eventuate.tram.commands.producer.CommandProducer;
import io.eventuate.tram.spring.commands.producer.TramCommandProducerConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import io.eventuate.tram.testutil.TestMessageConsumer;
import io.eventuate.tram.testutil.TestMessageConsumerFactory;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.PersonName;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.consumerservice.web.CreateConsumerRequest;
import net.chrisrichardson.ftgo.consumerservice.web.ConsumerWebConfiguration;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Collections;

import static com.jayway.restassured.RestAssured.given;
import static org.junit.Assert.assertNotNull;

@RunWith(SpringRunner.class)
@SpringBootTest(classes = ConsumerServiceInMemoryIntegrationTest.TestConfiguration.class,
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
public class ConsumerServiceInMemoryIntegrationTest {

  private Logger logger = LoggerFactory.getLogger(getClass());

  @Value("${local.server.port}")
  private int port;

  @Configuration
  @Import({ConsumerWebConfiguration.class,
          TramCommandProducerConfiguration.class,
          TramInMemoryConfiguration.class})
  @EnableAutoConfiguration
  public static class TestConfiguration {

    @Bean
    public TestMessageConsumerFactory testMessageConsumerFactory() {
      return new TestMessageConsumerFactory();
    }

  }

  private String baseUrl(String path) {
    return "http://localhost:" + port + path;
  }

  @Autowired
  private CommandProducer commandProducer;

  @Autowired
  private TestMessageConsumerFactory testMessageConsumerFactory;

  @Test
  public void shouldCreateConsumer() {

    String postUrl = baseUrl("/consumers");

    Integer consumerId =
            given().
            body(new CreateConsumerRequest(new PersonName("John", "Doe"))).
            contentType("application/json").
            when().
            post(postUrl).
            then().
            statusCode(200).
            extract().
            path("consumerId");

    assertNotNull(consumerId);


    TestMessageConsumer testMessageConsumer = testMessageConsumerFactory.make();

    long orderId = 999;
    Money orderTotal = new Money(123);

    String messageId = commandProducer.send("consumerService", null,
            new ValidateOrderByConsumer(consumerId, orderId, orderTotal),
            testMessageConsumer.getReplyChannel(), Collections.emptyMap());

    testMessageConsumer.assertHasReplyTo(messageId);

  }

}


