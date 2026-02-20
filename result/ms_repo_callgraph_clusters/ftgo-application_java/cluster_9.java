// Cluster 9

package net.chrisrichardson.ftgo.orderservice.api.events;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.List;

public class OrderDetails {

  private List<OrderLineItem> lineItems;
  private Money orderTotal;

  private long restaurantId;
  private long consumerId;

  private OrderDetails() {
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setOrderTotal(Money orderTotal) {
    this.orderTotal = orderTotal;
  }

  public OrderDetails(long consumerId, long restaurantId, List<OrderLineItem> lineItems, Money orderTotal) {
    this.consumerId = consumerId;
    this.restaurantId = restaurantId;
    this.lineItems = lineItems;
    this.orderTotal = orderTotal;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public List<OrderLineItem> getLineItems() {
    return lineItems;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public long getConsumerId() {
    return consumerId;
  }


  public void setLineItems(List<OrderLineItem> lineItems) {
    this.lineItems = lineItems;
  }


  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
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


// Node: getLineItems
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


// Node: getRestaurantName
package net.chrisrichardson.ftgo.orderservice.api.web;

import net.chrisrichardson.ftgo.common.Address;

import java.time.LocalDateTime;
import java.util.List;

public class CreateOrderRequest {

  private long restaurantId;
  private long consumerId;
  private LocalDateTime deliveryTime;
  private List<LineItem> lineItems;
  private Address deliveryAddress;

  public CreateOrderRequest(long consumerId, long restaurantId, Address deliveryAddress, LocalDateTime deliveryTime, List<LineItem> lineItems) {
    this.restaurantId = restaurantId;
    this.consumerId = consumerId;
    this.deliveryAddress = deliveryAddress;
    this.deliveryTime = deliveryTime;
    this.lineItems = lineItems;

  }

  private CreateOrderRequest() {
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public void setRestaurantId(long restaurantId) {
    this.restaurantId = restaurantId;
  }

  public long getConsumerId() {
    return consumerId;
  }

  public void setConsumerId(long consumerId) {
    this.consumerId = consumerId;
  }

  public List<LineItem> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<LineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public Address getDeliveryAddress() {
    return deliveryAddress;
  }

  public void setDeliveryAddress(Address deliveryAddress) {
    this.deliveryAddress = deliveryAddress;
  }

  public LocalDateTime getDeliveryTime() {
    return deliveryTime;
  }

  public void setDeliveryTime(LocalDateTime deliveryTime) {
    this.deliveryTime = deliveryTime;
  }

  public static class LineItem {

    private String menuItemId;
    private int quantity;

    private LineItem() {
    }

    public LineItem(String menuItemId, int quantity) {
      this.menuItemId = menuItemId;

      this.quantity = quantity;
    }

    public String getMenuItemId() {
      return menuItemId;
    }

    public int getQuantity() {
      return quantity;
    }

    public void setQuantity(int quantity) {
      this.quantity = quantity;
    }

    public void setMenuItemId(String menuItemId) {
      this.menuItemId = menuItemId;

    }

  }


}


package net.chrisrichardson.ftgo.kitchenservice.api;

import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.List;

public class TicketDetails {
  private List<TicketLineItem> lineItems;

  public TicketDetails() {
  }

  public TicketDetails(List<TicketLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public List<TicketLineItem> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<TicketLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }
}


// Node: ObjectMapper
// Node: put
package net.chrisrichardson.ftgo.common;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.JsonToken;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.deser.std.StdScalarDeserializer;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.databind.ser.std.StdScalarSerializer;

import java.io.IOException;

public class MoneyModule extends SimpleModule {

  class MoneyDeserializer extends StdScalarDeserializer<Money> {

    protected MoneyDeserializer() {
      super(Money.class);
    }

    @Override
    public Money deserialize(JsonParser jp, DeserializationContext ctxt) throws IOException, JsonProcessingException {
      JsonToken token = jp.getCurrentToken();
      if (token == JsonToken.VALUE_STRING) {
        String str = jp.getText().trim();
        if (str.isEmpty())
          return null;
        else
          return new Money(str);
      } else
        throw ctxt.mappingException(getValueClass());
    }
  }

  class MoneySerializer extends StdScalarSerializer<Money> {
    public MoneySerializer() {
      super(Money.class);
    }

    @Override
    public void serialize(Money value, JsonGenerator jgen, SerializerProvider provider) throws IOException {
      jgen.writeString(value.asString());
    }
  }

    @Override
  public String getModuleName() {
    return "FtgoCommonMOdule";
  }

  public MoneyModule() {
    addDeserializer(Money.class, new MoneyDeserializer());
    addSerializer(Money.class, new MoneySerializer());
  }

}


// Node: deserialize
// Node: getCurrentToken
// Node: getText
// Node: trim
// Node: isEmpty
// Node: mappingException
// Node: getValueClass
package net.chrisrichardson.ftgo.common;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import java.math.BigDecimal;

//@Embeddable
//@Access(AccessType.FIELD)
public class Money {

  public static Money ZERO = new Money(0);

  private BigDecimal amount;

  private Money() {
  }

  public Money(BigDecimal amount) {
    this.amount = amount;
  }

  public Money(String s) {
    this.amount = new BigDecimal(s);
  }

  public Money(int i) {
    this.amount = new BigDecimal(i);
  }

  @Override
  public boolean equals(Object o) {
    if (this == o) return true;

    if (o == null || getClass() != o.getClass()) return false;

    Money money = (Money) o;

    return new EqualsBuilder()
            .append(amount, money.amount)
            .isEquals();
  }

  @Override
  public int hashCode() {
    return new HashCodeBuilder(17, 37)
            .append(amount)
            .toHashCode();
  }

  @Override
  public String toString() {
    return new ToStringBuilder(this)
            .append("amount", amount)
            .toString();
  }


  public Money add(Money delta) {
    return new Money(amount.add(delta.amount));
  }

  public boolean isGreaterThanOrEqual(Money other) {
    return amount.compareTo(other.amount) >= 0;
  }

  public String asString() {
    return amount.toPlainString();
  }

  public Money multiply(int x) {
    return new Money(amount.multiply(new BigDecimal(x)));
  }

  public Long asLong() {
    return multiply(100).amount.longValue();
  }
}


// Node: add
// Node: withSagaCommandHeaders
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

// Node: getStatus
// Node: getCreationDate
package net.chrisrichardson.ftgo.cqrs.orderhistory;

import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.joda.time.DateTime;

import java.util.Optional;
import java.util.Set;

import static java.util.Collections.emptySet;

public class OrderHistoryFilter {
  private DateTime since = DateTime.now().minusDays(30);
  private Optional<OrderState> status = Optional.empty();
  private Set<String> keywords = emptySet();
  private Optional<String> startKeyToken = Optional.empty();
  private Optional<Integer> pageSize = Optional.empty();

  public DateTime getSince() {
    return since;
  }

  public OrderHistoryFilter withStatus(OrderState status) {
    this.status = Optional.of(status);
    return this;
  }

  public Optional<OrderState> getStatus() {
    return status;
  }


  public OrderHistoryFilter withStartKeyToken(Optional<String> startKeyToken) {
    this.startKeyToken = startKeyToken;
    return this;
  }

  public OrderHistoryFilter withKeywords(Set<String> keywords) {
    this.keywords = keywords;
    return this;
  }


  public Set<String> getKeywords() {
    return keywords;
  }

  public Optional<String> getStartKeyToken() {
    return startKeyToken;
  }

  public OrderHistoryFilter withPageSize(int pageSize) {
    this.pageSize = Optional.of(pageSize);
    return this;
  }

  public Optional<Integer> getPageSize() {
    return pageSize;
  }
}


// Node: getSince
// Node: getKeywords
// Node: getStartKeyToken
// Node: getPageSize
package net.chrisrichardson.ftgo.cqrs.orderhistory;

import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.Order;

import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;

public class OrderHistory {
  private List<Order> orders;
  private Optional<String> startKey;

  public OrderHistory(List<Order> orders, Optional<String> startKey) {
    this.orders = orders;
    this.startKey = startKey;
  }

  public List<Order> getOrders() {
    return orders;
  }

  public Optional<String> getStartKey() {
    return startKey;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/OrderHistory.java:OrderHistory.<init>
// Node: OrderHistory
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


package net.chrisrichardson.ftgo.cqrs.orderhistory.web;

import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistory;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryFilter;
import net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb.Order;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import static java.util.stream.Collectors.toList;

@RestController
@RequestMapping(path = "/orders")
public class OrderHistoryController {

  private OrderHistoryDao orderHistoryDao;

  public OrderHistoryController(OrderHistoryDao orderHistoryDao) {
    this.orderHistoryDao = orderHistoryDao;
  }

  @RequestMapping(method = RequestMethod.GET)
  public ResponseEntity<GetOrdersResponse> getOrders(@RequestParam(name = "consumerId") String consumerId) {
    OrderHistory orderHistory = orderHistoryDao.findOrderHistory(consumerId, new OrderHistoryFilter());
    return new ResponseEntity<>(new GetOrdersResponse(orderHistory.getOrders()
            .stream()
            .map(this::makeGetOrderResponse).collect(toList()), orderHistory.getStartKey().orElse(null)), HttpStatus.OK);
  }

  private GetOrderResponse makeGetOrderResponse(Order order) {
    return new GetOrderResponse(order.getOrderId(), order.getStatus(), order.getRestaurantId(), order.getRestaurantName());
  }

  @RequestMapping(path = "/{orderId}", method = RequestMethod.GET)
  public ResponseEntity<GetOrderResponse> getOrder(@PathVariable String orderId) {
    return orderHistoryDao.findOrder(orderId)
            .map(order -> new ResponseEntity<>(makeGetOrderResponse(order), HttpStatus.OK))
            .orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }

}


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


// Node: addDuplicateDetection
// Node: getNameMap
// Node: getValueMap
// Node: withUpdateExpression
// Node: getUpdateExpression
// Node: withNameMap
// Node: withValueMap
// Node: withConditionExpression
// Node: getConditionExpression
// Node: attribute_not_exists
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;


import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Index;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.dynamodbv2.document.ItemCollection;
import com.amazonaws.services.dynamodbv2.document.PrimaryKey;
import com.amazonaws.services.dynamodbv2.document.QueryOutcome;
import com.amazonaws.services.dynamodbv2.document.RangeKeyCondition;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.amazonaws.services.dynamodbv2.document.spec.GetItemSpec;
import com.amazonaws.services.dynamodbv2.document.spec.QuerySpec;
import com.amazonaws.services.dynamodbv2.document.spec.UpdateItemSpec;
import com.amazonaws.services.dynamodbv2.model.AttributeValue;
import com.amazonaws.services.dynamodbv2.model.ConditionalCheckFailedException;
import com.amazonaws.services.dynamodbv2.model.ReturnValue;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.cqrs.orderhistory.Location;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistory;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryFilter;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.apache.commons.lang.StringUtils;
import org.joda.time.DateTime;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.math.BigDecimal;
import java.text.BreakIterator;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.StreamSupport;

import static java.util.stream.Collectors.toList;
import static java.util.stream.Collectors.toSet;

public class OrderHistoryDaoDynamoDb implements OrderHistoryDao {

  private Logger logger = LoggerFactory.getLogger(getClass());

  public static final String FTGO_ORDER_HISTORY_BY_ID = "ftgo-order-history";
  public static final String FTGO_ORDER_HISTORY_BY_CONSUMER_ID_AND_DATE =
          "ftgo-order-history-by-consumer-id-and-creation-time";
  public static final String ORDER_STATUS_FIELD = "orderStatus";
  private static final String DELIVERY_STATUS_FIELD = "deliveryStatus";

  private final DynamoDB dynamoDB;

  private Table table;
  private Index index;

  public OrderHistoryDaoDynamoDb(DynamoDB dynamoDB) {
    this.dynamoDB = dynamoDB;
    table = this.dynamoDB.getTable(FTGO_ORDER_HISTORY_BY_ID);
    index = table.getIndex(FTGO_ORDER_HISTORY_BY_CONSUMER_ID_AND_DATE);
  }

  @Override
  public boolean addOrder(Order order, Optional<SourceEvent> eventSource) {
    UpdateItemSpec spec = new UpdateItemSpec()
            .withPrimaryKey("orderId", order.getOrderId())
            .withUpdateExpression("SET orderStatus = :orderStatus, " +
                    "creationDate = :creationDate, consumerId = :consumerId, lineItems =" +
                    " :lineItems, keywords = :keywords, restaurantId = :restaurantId, " +
                    " restaurantName = :restaurantName"
            )
            .withValueMap(new Maps()
                    .add(":orderStatus", order.getStatus().toString())
                    .add(":consumerId", order.getConsumerId())
                    .add(":creationDate", order.getCreationDate().getMillis())
                    .add(":lineItems", mapLineItems(order.getLineItems()))
                    .add(":keywords", mapKeywords(order))
                    .add(":restaurantId", order.getRestaurantId())
                    .add(":restaurantName", order.getRestaurantName())
                    .map())
            .withReturnValues(ReturnValue.NONE);
    return idempotentUpdate(spec, eventSource);
  }

  private boolean idempotentUpdate(UpdateItemSpec spec, Optional<SourceEvent>
          eventSource) {
    try {
      table.updateItem(eventSource.map(es -> es.addDuplicateDetection(spec))
              .orElse(spec));
      return true;
    } catch (ConditionalCheckFailedException e) {
      logger.error("not updated {}", eventSource);
      // Do nothing
      return false;
    }
  }

////  @Override
//  public void addOrderV1(Order order, Optional<SourceEvent> eventSource) {
//    Map<String, AttributeValue> keyMapBuilder = makeKey1(order.getOrderId());
//    AvMapBuilder expressionAttrs = new AvMapBuilder(":orderStatus", new
// AttributeValue(order.getStatus().toString()))
//            .add(":cd", new AttributeValue().withN(Long.toString(order
// .getCreationDate().getMillis())))
//            .add(":consumerId", order.getConsumerId())
//            .add(":lineItems", mapLineItems(order.getLineItems()))
//            .add(":keywords", mapKeywords(order))
//            .add(":restaurantName", order.getRestaurantId())
//            ;
//
//
//    UpdateItemRequest uir = new UpdateItemRequest()
//            .withTableName(FTGO_ORDER_HISTORY_BY_ID)
//            .withKey(keyMapBuilder)
//            .withUpdateExpression("SET orderStatus = :orderStatus,
// creationDate = :cd, consumerId = :consumerId, lineItems = :lineItems,
// keywords = :keywords, restaurantName = :restaurantName")
//            .withConditionExpression("attribute_not_exists(orderStatus)")
//            .withExpressionAttributeValues(expressionAttrs.map());
//    try {
//      client.updateItem(uir);
//    } catch (ConditionalCheckFailedException e) {
//      // Do nothing
//    }
//  }

  private Set mapKeywords(Order order) {
    Set<String> keywords = new HashSet<>();
    keywords.addAll(tokenize(order.getRestaurantName()));
    keywords.addAll(tokenize(order.getLineItems().stream().map
            (OrderLineItem::getName).collect(toList())));
    return keywords;
  }

  private Set<String> tokenize(Collection<String> text) {
    return text.stream().flatMap(t -> tokenize(t).stream()).collect(toSet());
  }

  private Set<String> tokenize(String text) {
    Set<String> result = new HashSet<>();
    BreakIterator bi = BreakIterator.getWordInstance();
    bi.setText(text);
    int lastIndex = bi.first();
    while (lastIndex != BreakIterator.DONE) {
      int firstIndex = lastIndex;
      lastIndex = bi.next();
      if (lastIndex != BreakIterator.DONE
              && Character.isLetterOrDigit(text.charAt(firstIndex))) {
        String word = text.substring(firstIndex, lastIndex);
        result.add(word);
      }
    }
    return result;
  }

  private List mapLineItems(List<OrderLineItem> lineItems) {
    return lineItems.stream().map(this::mapOrderLineItem).collect(toList());
  }
//  private AttributeValue mapLineItems(List<OrderLineItem> lineItems) {
//    AttributeValue result = new AttributeValue();
//    result.withL(lineItems.stream().map(this::mapOrderLineItem).collect
// (toList()));
//    return result;
//  }

  private Map mapOrderLineItem(OrderLineItem orderLineItem) {
    return new Maps()
            .add("menuItemName", orderLineItem.getName())
            .add("menuItemId", orderLineItem.getMenuItemId())
            .add("price", orderLineItem.getPrice().asString())
            .add("quantity", orderLineItem.getQuantity())
            .map();
  }
//  private AttributeValue mapOrderLineItem(OrderLineItem orderLineItem) {
//    AttributeValue result = new AttributeValue();
//    result.addMEntry("menuItem", new AttributeValue(orderLineItem
// .getName()));
//    return result;
//  }


  private Map<String, AttributeValue> makeKey1(String orderId) {
    return new AvMapBuilder("orderId", new AttributeValue(orderId)).map();
  }

  @Override
  public OrderHistory findOrderHistory(String consumerId, OrderHistoryFilter
          filter) {

    QuerySpec spec = new QuerySpec()
            .withScanIndexForward(false)
            .withHashKey("consumerId", consumerId)
            .withRangeKeyCondition(new RangeKeyCondition("creationDate").gt
                    (filter.getSince().getMillis()));

    filter.getStartKeyToken().ifPresent(token -> spec.withExclusiveStartKey
            (toStartingPrimaryKey(token)));

    Map<String, Object> valuesMap = new HashMap<>();

    String filterExpression = Expressions.and(
            keywordFilterExpression(valuesMap, filter.getKeywords()),
            statusFilterExpression(valuesMap, filter.getStatus()));

    if (!valuesMap.isEmpty())
      spec.withValueMap(valuesMap);

    if (StringUtils.isNotBlank(filterExpression)) {
      spec.withFilterExpression(filterExpression);
    }

    System.out.print("filterExpression.toString()=" + filterExpression);

    filter.getPageSize().ifPresent(spec::withMaxResultSize);

    ItemCollection<QueryOutcome> result = index.query(spec);

    return new OrderHistory(StreamSupport.stream(result.spliterator(), false)
            .map(this::toOrder).collect(toList()),
            Optional.ofNullable(result.getLastLowLevelResult().getQueryResult
                    ().getLastEvaluatedKey()).map(this::toStartKeyToken));
  }

  private PrimaryKey toStartingPrimaryKey(String token) {
    ObjectMapper om = new ObjectMapper();
    Map<String, Object> map;
    try {
      map = om.readValue(token, Map.class);
    } catch (IOException e) {
      throw new RuntimeException();
    }
    PrimaryKey pk = new PrimaryKey();
    map.entrySet().forEach(key -> {
      pk.addComponent(key.getKey(), key.getValue());
    });
    return pk;
  }

  private String toStartKeyToken(Map<String, AttributeValue> lastEvaluatedKey) {
    Map<String, Object> map = new HashMap<>();
    lastEvaluatedKey.entrySet().forEach(entry -> {
      String value = entry.getValue().getS();
      if (value == null) {
        value = entry.getValue().getN();
        map.put(entry.getKey(), Long.parseLong(value));
      } else {
        map.put(entry.getKey(), value);
      }
    });
    ObjectMapper om = new ObjectMapper();
    try {
      return om.writeValueAsString(map);
    } catch (JsonProcessingException e) {
      throw new RuntimeException();
    }
  }

  private Optional<String> statusFilterExpression(Map<String, Object>
                                                          expressionAttributeValuesBuilder, Optional<OrderState> status) {
    return status.map(s -> {
      expressionAttributeValuesBuilder.put(":orderStatus", s.toString());
      return "orderStatus = :orderStatus";
    });
  }

  private String keywordFilterExpression(Map<String, Object>
                                                 expressionAttributeValuesBuilder, Set<String> kw) {
    Set<String> keywords = tokenize(kw);
    if (keywords.isEmpty()) {
      return "";
    }
    String cuisinesExpression = "";
    int idx = 0;
    for (String cuisine : keywords) {
      String var = ":keyword" + idx;
      String cuisineExpression = String.format("contains(keywords, %s)", var);
      cuisinesExpression = Expressions.or(cuisinesExpression, cuisineExpression);
      expressionAttributeValuesBuilder.put(var, cuisine);
    }

    return cuisinesExpression;
  }

//  @Override
//  public OrderHistory findOrderHistory(String consumerId,
// OrderHistoryFilter filter) {
//    AvMapBuilder expressionAttributeValuesBuilder = new AvMapBuilder
// (":cid", new AttributeValue(consumerId))
//            .add(":oct", new AttributeValue().withN(Long.toString(filter
// .getSince().getMillis())));
//    StringBuilder filterExpression = new StringBuilder();
//    Set<String> keywords = tokenize(filter.getKeywords());
//    if (!keywords.isEmpty()) {
//      if (filterExpression.length() > 0)
//        filterExpression.append(" AND ");
//      filterExpression.append(" ( ");
//      int idx = 0;
//      for (String cuisine : keywords) {
//        if (idx++ > 0) {
//          filterExpression.append(" OR ");
//        }
//        String var = ":keyword" + idx;
//        filterExpression.append("contains(keywords, ").append(var).append
// (')');
//        expressionAttributeValuesBuilder.add(var, cuisine);
//      }
//
//      filterExpression.append(" ) ");
//    }
//    filter.getStatus().ifPresent(status -> {
//      if (filterExpression.length() > 0)
//        filterExpression.append(" AND ");
//      filterExpression.append("orderStatus = :orderStatus");
//      expressionAttributeValuesBuilder.add(":orderStatus", status.toString
// ());
//    });
//    QueryRequest ar = new QueryRequest()
//            .withTableName(FTGO_ORDER_HISTORY_BY_ID)
//            .withIndexName(FTGO_ORDER_HISTORY_BY_CONSUMER_ID_AND_DATE)
//            .withScanIndexForward(false)
//            .withKeyConditionExpression("consumerId = :cid AND
// creationDate > :oct")
//            .withExpressionAttributeValues
// (expressionAttributeValuesBuilder.map());
//    System.out.print("filterExpression.toString()=" + filterExpression
// .toString());
//    if (filterExpression.length() > 0)
//      ar.withFilterExpression(filterExpression.toString());
//
//    QuerySpec spec = new QuerySpec();
//    ItemCollection<QueryOutcome> result = table.query(spec);
//
//    List<Map<String, AttributeValue>> items = client.query(ar).getItems();
//    return new OrderHistory(items.stream().map(this::toOrder).collect
// (toList()));
//  }

  @Override
  public boolean updateOrderState(String orderId, OrderState newState, Optional<SourceEvent> eventSource) {
    UpdateItemSpec spec = new UpdateItemSpec()
            .withPrimaryKey("orderId", orderId)
            .withUpdateExpression("SET #orderStatus = :orderStatus")
            .withNameMap(Collections.singletonMap("#orderStatus",
                    ORDER_STATUS_FIELD))
            .withValueMap(Collections.singletonMap(":orderStatus", newState.toString()))
            .withReturnValues(ReturnValue.NONE);
    return idempotentUpdate(spec, eventSource);
  }


  static PrimaryKey makePrimaryKey(String orderId) {
    return new PrimaryKey().addComponent("orderId", orderId);
  }

  @Override
  public void noteTicketPreparationStarted(String orderId) {
    throw new UnsupportedOperationException();
  }

  @Override
  public void noteTicketPreparationCompleted(String orderId) {
    throw new UnsupportedOperationException();

  }

  @Override
  public void notePickedUp(String orderId, Optional<SourceEvent> eventSource) {
    UpdateItemSpec spec = new UpdateItemSpec()
            .withPrimaryKey("orderId", orderId)
            .withUpdateExpression("SET #deliveryStatus = :deliveryStatus")
            .withNameMap(Collections.singletonMap("#deliveryStatus",
                    DELIVERY_STATUS_FIELD))
            .withValueMap(Collections.singletonMap(":deliveryStatus",
                    DeliveryStatus.PICKED_UP.toString()))
            .withReturnValues(ReturnValue.NONE);
    idempotentUpdate(spec, eventSource);
  }

  @Override
  public void updateLocation(String orderId, Location location) {
    throw new UnsupportedOperationException();

  }

  @Override
  public void noteDelivered(String orderId) {
    throw new UnsupportedOperationException();

  }

  @Override
  public Optional<Order> findOrder(String orderId) {
    Item item = table.getItem(new GetItemSpec()
            .withPrimaryKey(makePrimaryKey(orderId))
            .withConsistentRead(true));
    return Optional.ofNullable(item).map(this::toOrder);
  }


  private Order toOrder(Item avs) {
    Order order = new Order(avs.getString("orderId"),
            avs.getString("consumerId"),
            OrderState.valueOf(avs.getString("orderStatus")),
            toLineItems2(avs.getList("lineItems")),
            null,
            avs.getLong("restaurantId"),
            avs.getString("restaurantName"));
    if (avs.hasAttribute("creationDate"))
      order.setCreationDate(new DateTime(avs.getLong("creationDate")));
    return order;
  }


  private List<OrderLineItem> toLineItems2(List<LinkedHashMap<String,
          Object>> lineItems) {
    return lineItems.stream().map(this::toLineItem2).collect(toList());
  }

  private OrderLineItem toLineItem2(LinkedHashMap<String, Object>
                                            attributeValue) {
    return new OrderLineItem((String) attributeValue.get("menuItemId"),
                             (String) attributeValue.get("menuItemName"),
                             new Money((String) attributeValue.get("price")),
                            ((BigDecimal) attributeValue.get("quantity")).intValue()
            );
  }

}


// Node: UpdateItemSpec
// Node: withPrimaryKey
// Node: Maps
// Node: getMillis
// Node: mapLineItems
// Node: mapKeywords
// Node: withReturnValues
// Node: idempotentUpdate
// Node: updateItem
// Node: addOrderV1
// Node: makeKey1
// Node: AvMapBuilder
// Node: AttributeValue
// Node: withN
// Node: UpdateItemRequest
// Node: withTableName
// Node: withKey
// Node: withExpressionAttributeValues
// Node: addAll
// Node: tokenize
// Node: toSet
// Node: getWordInstance
// Node: setText
// Node: first
// Node: next
// Node: isLetterOrDigit
// Node: charAt
// Node: substring
// Node: QuerySpec
// Node: withScanIndexForward
// Node: withHashKey
// Node: withRangeKeyCondition
// Node: RangeKeyCondition
// Node: toStartingPrimaryKey
// Node: keywordFilterExpression
// Node: statusFilterExpression
// Node: isNotBlank
// Node: withFilterExpression
// Node: print
// Node: query
// Node: spliterator
// Node: getLastLowLevelResult
// Node: getLastEvaluatedKey
// Node: readValue
// Node: PrimaryKey
// Node: entrySet
// Node: forEach
// Node: addComponent
// Node: getKey
// Node: toStartKeyToken
// Node: getS
// Node: getN
// Node: contains
// Node: length
// Node: QueryRequest
// Node: withIndexName
// Node: withKeyConditionExpression
// Node: getItems
// Node: singletonMap
// Node: makePrimaryKey
// Node: getItem
// Node: GetItemSpec
// Node: withConsistentRead
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.joda.time.DateTime;

import java.util.List;

public class Order {
  private String consumerId;
  private DateTime creationDate = DateTime.now();
  private OrderState status;
  private String orderId;
  private List<OrderLineItem> lineItems;
  private Money orderTotal;
  private long restaurantId;
  private String restaurantName;

  public Order(String orderId, String consumerId, OrderState status, List<OrderLineItem> lineItems, Money orderTotal, long restaurantId, String restaurantName) {
    this.orderId = orderId;
    this.consumerId = consumerId;
    this.status = status;
    this.lineItems = lineItems;
    this.orderTotal = orderTotal;
    this.restaurantId = restaurantId;
    this.restaurantName = restaurantName;
  }

  public String getRestaurantName() {
    return restaurantName;
  }

  public String getOrderId() {
    return orderId;
  }

  public long getRestaurantId() {
    return restaurantId;
  }
  
  public List<OrderLineItem> getLineItems() {
    return lineItems;
  }

  public Money getOrderTotal() {
    return orderTotal;
  }

  public void setCreationDate(DateTime creationDate) {
    this.creationDate = creationDate;
  }

  public String getConsumerId() {
    return consumerId;
  }

  public DateTime getCreationDate() {
    return creationDate;
  }

  public OrderState getStatus() {
    return status;
  }


}


package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import org.joda.time.DurationField;

import java.util.HashMap;
import java.util.Map;

public class Maps {

  private final Map<String, Object> map;

  public Maps() {
    this.map = new HashMap<>();
  }

  public Maps add(String key, Object value) {
    map.put(key, value);
    return this;
  }

  public Map<String, Object> map() {
    return map;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/Maps.java:Maps.<init>
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Table;
import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;

public class DynamoDBHealthIndicator implements HealthIndicator {
  private final Table table;
  private DynamoDB dynamoDB;

  public DynamoDBHealthIndicator(DynamoDB dynamoDB) {
    this.dynamoDB = dynamoDB;
    this.table = this.dynamoDB.getTable(OrderHistoryDaoDynamoDb.FTGO_ORDER_HISTORY_BY_ID);
  }

  @Override
  public Health health() {
    try {
      table.getItem(OrderHistoryDaoDynamoDb.makePrimaryKey("999"));
      return Health.up().build();
    } catch (Exception e) {
      return Health.down(e).build();
    }
  }
}


// Node: health
// Node: up
// Node: down
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import com.amazonaws.services.dynamodbv2.model.AttributeValue;

import java.util.HashMap;
import java.util.Map;

public class AvMapBuilder {

  private Map<String, AttributeValue> eav = new HashMap<>();

  public AvMapBuilder(String key, AttributeValue value) {
    eav.put(key, value);
  }

  public AvMapBuilder add(String key, String value) {
    eav.put(key, new AttributeValue(value));
    return this;
  }

  public AvMapBuilder add(String key, AttributeValue value) {
    eav.put(key, value);
    return this;
  }

  public Map<String, AttributeValue> map() {
    return eav;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/dynamodb/AvMapBuilder.java:AvMapBuilder.<init>
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.common.DomainEvent;
import org.springframework.util.Assert;

import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

public class Result {


  private final List<DomainEvent> events;
  private Boolean allowed;

  public List<DomainEvent> getEvents() {
    return events;
  }

  public Result(List<DomainEvent> events, Boolean allowed) {
    this.events = events;
    this.allowed = allowed;
  }

  public boolean isWhatIsThisCalled() {
    return allowed;
  }

  public static Builder build() {
    return new Builder();
  }

  public static class Builder {
    private List<DomainEvent> events = new LinkedList<>();
    private Boolean allowed;

    public Builder withEvents(DomainEvent... events) {
      Arrays.stream(events).forEach(e -> this.events.add(e));
      return this;
    }

    public Builder pending() {
      this.allowed = false;
      return this;
    }

    public Result build() {
      Assert.notNull(allowed);
      return new Result(events, allowed);
    }

    public Builder allowed() {
      this.allowed = false;
      return this;
    }
  }
}


// Node: withEvents
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;

import javax.persistence.CollectionTable;
import javax.persistence.ElementCollection;
import javax.persistence.Embeddable;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

@Embeddable
public class OrderLineItems {

  @ElementCollection
  @CollectionTable(name = "order_line_items")
  private List<OrderLineItem> lineItems;

  private OrderLineItems() {
  }

  public OrderLineItems(List<OrderLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public List<OrderLineItem> getLineItems() {
    return lineItems;
  }

  public void setLineItems(List<OrderLineItem> lineItems) {
    this.lineItems = lineItems;
  }

  OrderLineItem findOrderLineItem(String lineItemId) {
    return lineItems.stream().filter(li -> li.getMenuItemId().equals(lineItemId)).findFirst().get();
  }

  Money changeToOrderTotal(OrderRevision orderRevision) {
    return orderRevision
            .getRevisedOrderLineItems()
            .stream()
            .map(item -> {
              OrderLineItem lineItem = findOrderLineItem(item.getMenuItemId());
              return lineItem.deltaForChangedQuantity(item.getQuantity());
            })
            .reduce(Money.ZERO, Money::add);
  }

  void updateLineItems(OrderRevision orderRevision) {
    getLineItems().stream().forEach(li -> {

      Optional<Integer> revised = orderRevision.getRevisedOrderLineItems()
              .stream()
              .filter(item -> Objects.equals(li.getMenuItemId(), item.getMenuItemId()))
              .map(RevisedOrderLineItem::getQuantity)
              .findFirst();

      li.setQuantity(revised.orElseThrow(() ->
              new IllegalArgumentException(String.format("menu item id not found.", li.getMenuItemId()))));
    });
  }

  Money orderTotal() {
    return lineItems.stream().map(OrderLineItem::getTotal).reduce(Money.ZERO, Money::add);
  }

  LineItemQuantityChange lineItemQuantityChange(OrderRevision orderRevision) {
    Money currentOrderTotal = orderTotal();
    Money delta = changeToOrderTotal(orderRevision);
    Money newOrderTotal = currentOrderTotal.add(delta);
    return new LineItemQuantityChange(currentOrderTotal, newOrderTotal, delta);
  }
}

package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.UnsupportedStateTransitionException;
import net.chrisrichardson.ftgo.orderservice.api.events.*;

import javax.persistence.*;
import java.util.List;

import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.APPROVED;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.APPROVAL_PENDING;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.REJECTED;
import static net.chrisrichardson.ftgo.orderservice.api.events.OrderState.REVISION_PENDING;
import static java.util.Collections.emptyList;
import static java.util.Collections.singletonList;

@Entity
@Table(name = "orders")
@Access(AccessType.FIELD)
public class Order {

  public static ResultWithDomainEvents<Order, OrderDomainEvent>
  createOrder(long consumerId, Restaurant restaurant, DeliveryInformation deliveryInformation, List<OrderLineItem> orderLineItems) {
    Order order = new Order(consumerId, restaurant.getId(), deliveryInformation, orderLineItems);
    List<OrderDomainEvent> events = singletonList(new OrderCreatedEvent(
            new OrderDetails(consumerId, restaurant.getId(), orderLineItems,
                    order.getOrderTotal()),
            deliveryInformation.getDeliveryAddress(),
            restaurant.getName()));
    return new ResultWithDomainEvents<>(order, events);
  }

  @Id
  @GeneratedValue
  private Long id;

  @Version
  private Long version;

  @Enumerated(EnumType.STRING)
  private OrderState state;

  private Long consumerId;
  private Long restaurantId;

  @Embedded
  private OrderLineItems orderLineItems;

  @Embedded
  private DeliveryInformation deliveryInformation;

  @Embedded
  private PaymentInformation paymentInformation;

  @Embedded
  private Money orderMinimum = new Money(Integer.MAX_VALUE);

  private Order() {
  }

  public Order(long consumerId, long restaurantId, DeliveryInformation deliveryInformation, List<OrderLineItem> orderLineItems) {
    this.consumerId = consumerId;
    this.restaurantId = restaurantId;
    this.deliveryInformation = deliveryInformation;
    this.orderLineItems = new OrderLineItems(orderLineItems);
    this.state = APPROVAL_PENDING;
  }

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public DeliveryInformation getDeliveryInformation() {
    return deliveryInformation;
  }

  public Money getOrderTotal() {
    return orderLineItems.orderTotal();
  }

  public List<OrderDomainEvent> cancel() {
    switch (state) {
      case APPROVED:
        this.state = OrderState.CANCEL_PENDING;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> undoPendingCancel() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = OrderState.APPROVED;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> noteCancelled() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = OrderState.CANCELLED;
        return singletonList(new OrderCancelled());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> noteApproved() {
    switch (state) {
      case APPROVAL_PENDING:
        this.state = APPROVED;
        return singletonList(new OrderAuthorized());
      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }

  public List<OrderDomainEvent> noteRejected() {
    switch (state) {
      case APPROVAL_PENDING:
        this.state = REJECTED;
        return singletonList(new OrderRejected());

      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }


  public List<OrderDomainEvent> noteReversingAuthorization() {
    return null;
  }

  public ResultWithDomainEvents<LineItemQuantityChange, OrderDomainEvent> revise(OrderRevision orderRevision) {
    switch (state) {

      case APPROVED:
        LineItemQuantityChange change = orderLineItems.lineItemQuantityChange(orderRevision);
        if (change.newOrderTotal.isGreaterThanOrEqual(orderMinimum)) {
          throw new OrderMinimumNotMetException();
        }
        this.state = REVISION_PENDING;
        return new ResultWithDomainEvents<>(change, singletonList(new OrderRevisionProposed(orderRevision, change.currentOrderTotal, change.newOrderTotal)));

      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> rejectRevision() {
    switch (state) {
      case REVISION_PENDING:
        this.state = APPROVED;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<OrderDomainEvent> confirmRevision(OrderRevision orderRevision) {
    switch (state) {
      case REVISION_PENDING:
        LineItemQuantityChange licd = orderLineItems.lineItemQuantityChange(orderRevision);

        orderRevision.getDeliveryInformation().ifPresent(newDi -> this.deliveryInformation = newDi);

        if (orderRevision.getRevisedOrderLineItems() != null && orderRevision.getRevisedOrderLineItems().size() > 0) {
          orderLineItems.updateLineItems(orderRevision);
        }

        this.state = APPROVED;
        return singletonList(new OrderRevised(orderRevision, licd.currentOrderTotal, licd.newOrderTotal));
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }


  public Long getVersion() {
    return version;
  }

  public List<OrderLineItem> getLineItems() {
    return orderLineItems.getLineItems();
  }

  public OrderState getState() {
    return state;
  }

  public long getRestaurantId() {
    return restaurantId;
  }


  public Long getConsumerId() {
    return consumerId;
  }
}



package net.chrisrichardson.ftgo.deliveryservice.domain;

import javax.persistence.ElementCollection;
import java.util.LinkedList;
import java.util.List;
import java.util.stream.Collectors;

public class Plan {

  @ElementCollection
  private List<Action> actions = new LinkedList<>();

  public void add(Action action) {
    actions.add(action);
  }

  public void removeDelivery(long deliveryId) {
    actions = actions.stream().filter(action -> !action.actionFor(deliveryId)).collect(Collectors.toList());
  }

  public List<Action> getActions() {
    return actions;
  }

  public List<Action> actionsForDelivery(long deliveryId) {
    return actions.stream().filter(action -> action.actionFor(deliveryId)).collect(Collectors.toList());
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


