// Cluster 15

package net.chrisrichardson.ftgo.orderservice.api.events;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.AttributeOverride;
import javax.persistence.AttributeOverrides;
import javax.persistence.Column;
import javax.persistence.Embeddable;
import javax.persistence.Embedded;

@Embeddable
public class OrderLineItem {

  public OrderLineItem() {
  }

  private int quantity;
  private String menuItemId;
  private String name;

  @Embedded
  @AttributeOverrides(@AttributeOverride(name="amount", column=@Column(name="price")))
  private Money price;

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

  public OrderLineItem(String menuItemId, String name, Money price, int quantity) {
    this.menuItemId = menuItemId;
    this.name = name;
    this.price = price;
    this.quantity = quantity;
  }

  public Money deltaForChangedQuantity(int newQuantity) {
    return price.multiply(newQuantity - quantity);
  }

  public void setQuantity(int quantity) {
    this.quantity = quantity;
  }

  public void setMenuItemId(String menuItemId) {
    this.menuItemId = menuItemId;
  }

  public void setName(String name) {
    this.name = name;
  }

  public void setPrice(Money price) {
    this.price = price;
  }

  public int getQuantity() {
    return quantity;
  }

  public String getMenuItemId() {
    return menuItemId;
  }

  public String getName() {
    return name;
  }

  public Money getPrice() {
    return price;
  }


  public Money getTotal() {
    return price.multiply(quantity);
  }

}


// Node: getQuantity
// Node: getMenuItemId
// Node: getName
// Node: getPrice
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


// Node: getDeliveryTime
// Node: orElse
package net.chrisrichardson.ftgo.kitchenservice.api;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class TicketLineItem {

  private int quantity;
  private String menuItemId;
  private String name;


  public int getQuantity() {
    return quantity;
  }

  public void setQuantity(int quantity) {
    this.quantity = quantity;
  }

  public String getMenuItemId() {
    return menuItemId;
  }

  public void setMenuItemId(String menuItemId) {
    this.menuItemId = menuItemId;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  private TicketLineItem() {

  }

  public TicketLineItem(String menuItemId, String name, int quantity) {
    this.menuItemId = menuItemId;
    this.name = name;
    this.quantity = quantity;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.events;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;

public class RestaurantCreated implements RestaurantDomainEvent {
  private String name;
  private Address address;
  private RestaurantMenu menu;

  public String getName() {
    return name;
  }

  private RestaurantCreated() {
  }

  public RestaurantCreated(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;

    if (menu == null) 
      throw new NullPointerException("Null Menu");
    if (address == null) 
      throw new NullPointerException("Null address");
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Address getAddress() {
    return address;
  }

  public void setAddress(Address address) {
    this.address = address;
  }
}


// Node: NullPointerException
// Node: getId
package net.chrisrichardson.ftgo.restaurantservice.web;

import net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantService;
import net.chrisrichardson.ftgo.restaurantservice.domain.CreateRestaurantRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(path = "/restaurants")
public class RestaurantController {

  @Autowired
  private RestaurantService restaurantService;

  @RequestMapping(method = RequestMethod.POST)
  public CreateRestaurantResponse create(@RequestBody CreateRestaurantRequest request) {
    Restaurant r = restaurantService.create(request);
    return new CreateRestaurantResponse(r.getId());
  }

  @RequestMapping(method = RequestMethod.GET, path = "/{restaurantId}")
  public ResponseEntity<GetRestaurantResponse> get(@PathVariable long restaurantId) {
    return restaurantService.findById(restaurantId)
            .map(r -> new ResponseEntity<>(makeGetRestaurantResponse(r), HttpStatus.OK))
            .orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }

  private GetRestaurantResponse makeGetRestaurantResponse(Restaurant r) {
    return new GetRestaurantResponse(r.getId(), r.getName());
  }


}


// Node: map
// Node: makeGetRestaurantResponse
// Node: orElseGet
package net.chrisrichardson.ftgo.restaurantservice.web;

public class GetRestaurantResponse {
  private Long id;

  public Long getId() {
    return id;
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  private String name;

  public GetRestaurantResponse() {
  }

  public GetRestaurantResponse(Long id, String name) {
    this.id = id;
    this.name = name;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.web;

public class CreateRestaurantResponse {
  private long id;

  public CreateRestaurantResponse() {
  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public CreateRestaurantResponse(long id) {
    this.id = id;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Address;

public class CreateRestaurantRequest {

  private String name;
  private Address address;
  private RestaurantMenu menu;

  private CreateRestaurantRequest() {

  }

  public CreateRestaurantRequest(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public Address getAddress() {
    return address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  @GeneratedValue
  private Long id;

  private String name;

  @Embedded
  private RestaurantMenu menu;

  private Restaurant() {
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }


  public Restaurant(String name, RestaurantMenu menu) {
    this.name = name;
    this.menu = menu;
  }


  public Long getId() {
    return id;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.events;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.restaurantservice.domain.RestaurantMenu;

public class RestaurantCreated implements RestaurantDomainEvent {
  private String name;
  private Address address;
  private RestaurantMenu menu;

  public String getName() {
    return name;
  }

  private RestaurantCreated() {
  }

  public RestaurantCreated(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;


    if (menu == null) 
      throw new NullPointerException("Null Menu");
    if (address == null) 
      throw new NullPointerException("Null address");    
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Address getAddress() {
    return address;
  }

  public void setAddress(Address address) {
    this.address = address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.web;

public class CreateRestaurantResponse {
  private long id;

  public CreateRestaurantResponse() {
  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public CreateRestaurantResponse(long id) {
    this.id = id;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Address;

public class CreateRestaurantRequest {

  private String name;
  private Address address;
  private RestaurantMenu menu;

  private CreateRestaurantRequest() {

  }

  public CreateRestaurantRequest(String name, Address address, RestaurantMenu menu) {
    this.name = name;
    this.address = address;
    this.menu = menu;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public RestaurantMenu getMenu() {
    return menu;
  }

  public void setMenu(RestaurantMenu menu) {
    this.menu = menu;
  }

  public Address getAddress() {
    return address;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  @GeneratedValue
  private Long id;

  private String name;

  @Embedded
  private RestaurantMenu menu;

  private Restaurant() {
  }

  public void setId(Long id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }


  public Restaurant(String name, RestaurantMenu menu) {
    this.name = name;
    this.menu = menu;
  }


  public Long getId() {
    return id;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


package net.chrisrichardson.ftgo.restaurantservice.aws;

import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.Map;
import java.util.Optional;

public class ApiGatewayRequest {

  private String resource;
  private String path;
  private String httpMethod;
  private Map<String, String> headers;
  private Map<String, String> queryStringParameters;
  private Map<String, String> pathParameters;
  private Map<String, String> stageVariables;
  private RequestContext requestContext;
  private String body;
  private boolean isBase64Encoded;

  public String getResource() {
    return resource;
  }

  public void setResource(String resource) {
    this.resource = resource;
  }

  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public String getHttpMethod() {
    return httpMethod;
  }

  public void setHttpMethod(String httpMethod) {
    this.httpMethod = httpMethod;
  }

  public Map<String, String> getHeaders() {
    return headers;
  }

  public void setHeaders(Map<String, String> headers) {
    this.headers = headers;
  }

  public Map<String, String> getQueryStringParameters() {
    return queryStringParameters;
  }

  public void setQueryStringParameters(Map<String, String> queryStringParameters) {
    this.queryStringParameters = queryStringParameters;
  }

  public Map<String, String> getPathParameters() {
    return pathParameters;
  }

  public void setPathParameters(Map<String, String> pathParameters) {
    this.pathParameters = pathParameters;
  }

  public Map<String, String> getStageVariables() {
    return stageVariables;
  }

  public void setStageVariables(Map<String, String> stageVariables) {
    this.stageVariables = stageVariables;
  }

  public RequestContext getRequestContext() {
    return requestContext;
  }

  public void setRequestContext(RequestContext requestContext) {
    this.requestContext = requestContext;
  }

  public String getBody() {
    return body;
  }

  public void setBody(String body) {
    this.body = body;
  }

  public boolean isBase64Encoded() {
    return isBase64Encoded;
  }

  public void setBase64Encoded(boolean base64Encoded) {
    isBase64Encoded = base64Encoded;
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getPathParam(String paramName) {
    return Optional.ofNullable(this.getPathParameters())
            .map(paramsMap -> paramsMap.get(paramName))
            .orElse(null);
  }
}

// Node: getPathParam
package net.chrisrichardson.ftgo.restaurantservice.lambda;

public class GetRestaurantResponse {
  private String name;

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public GetRestaurantResponse(String name) {
    this.name = name;

  }
}


package net.chrisrichardson.ftgo.common;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import java.util.Objects;

public class RevisedOrderLineItem {
    private int quantity;
    private String menuItemId;

    public RevisedOrderLineItem() {
    }

    public RevisedOrderLineItem(int quantity, String menuItemId) {
        this.quantity = quantity;
        this.menuItemId = menuItemId;
    }

    public int getQuantity() {
        return quantity;
    }

    public void setQuantity(int quantity) {
        this.quantity = quantity;
    }

    public String getMenuItemId() {
        return menuItemId;
    }

    public void setMenuItemId(String menuItemId) {
        this.menuItemId = menuItemId;
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
        return Objects.hash(quantity, menuItemId);
    }
}


package net.chrisrichardson.ftgo.common;

import com.fasterxml.jackson.databind.JsonMappingException;
import io.eventuate.common.json.mapper.JSonMapper;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;
import org.junit.BeforeClass;
import org.junit.Test;

import java.io.IOException;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

public class MoneySerializationTest {

  @BeforeClass
  public static void initialize() {
    CommonJsonMapperInitializer.registerMoneyModule();
  }


  public static class MoneyContainer {
    private Money price;

    @Override
    public boolean equals(Object o) {
      return EqualsBuilder.reflectionEquals(this, o);
    }

    @Override
    public int hashCode() {
      return HashCodeBuilder.reflectionHashCode(this);
    }

    @Override
    public String toString() {
      return ToStringBuilder.reflectionToString(this);
    }

    public Money getPrice() {
      return price;
    }

    public void setPrice(Money price) {
      this.price = price;
    }

    public MoneyContainer() {

    }

    public MoneyContainer(Money price) {

      this.price = price;
    }
  }

  @Test
  public void shouldSer() {
    Money price = new Money("12.34");
    MoneyContainer mc = new MoneyContainer(price);
    assertEquals("{\"price\":\"12.34\"}", JSonMapper.toJson(mc));
  }

  @Test
  public void shouldDe() {
    Money price = new Money("12.34");
    MoneyContainer mc = new MoneyContainer(price);
    assertEquals(mc, JSonMapper.fromJson("{\"price\":\"12.34\"}", MoneyContainer.class));
  }

  @Test
  public void shouldFailToDe() {
    try {
      JSonMapper.fromJson("{\"price\": { \"amount\" : \"12.34\"} }", MoneyContainer.class);
      fail("expected exception");
    } catch (RuntimeException e) {
      assertEquals(JsonMappingException.class, e.getCause().getClass());
    }
  }


}

// Node: withId
package net.chrisrichardson.ftgo.accountingservice.messaging;

import io.eventuate.javaclient.spring.EnableEventHandlers;
import io.eventuate.tram.commands.consumer.CommandDispatcher;
import io.eventuate.tram.commands.consumer.CommandDispatcherFactory;
import io.eventuate.tram.spring.commands.consumer.TramCommandConsumerConfiguration;
import io.eventuate.tram.spring.consumer.jdbc.TransactionalNoopDuplicateMessageDetectorConfiguration;
import io.eventuate.tram.spring.events.subscriber.TramEventSubscriberConfiguration;
import io.eventuate.tram.events.subscriber.DomainEventDispatcher;
import io.eventuate.tram.events.subscriber.DomainEventDispatcherFactory;
import io.eventuate.tram.sagas.eventsourcingsupport.SagaReplyRequestedEventSubscriber;
import net.chrisrichardson.ftgo.accountingservice.domain.Account;
import net.chrisrichardson.ftgo.accountingservice.domain.AccountServiceConfiguration;
import net.chrisrichardson.ftgo.common.CommonConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

import java.util.Collections;

@Configuration
@EnableEventHandlers
@Import({AccountServiceConfiguration.class, CommonConfiguration.class, TramEventSubscriberConfiguration.class, TramCommandConsumerConfiguration.class, TransactionalNoopDuplicateMessageDetectorConfiguration.class})
public class AccountingMessagingConfiguration {

  @Bean
  public AccountingEventConsumer accountingEventConsumer() {
    return new AccountingEventConsumer();
  }

  @Bean
  public DomainEventDispatcher domainEventDispatcher(AccountingEventConsumer accountingEventConsumer, DomainEventDispatcherFactory domainEventDispatcherFactory) {
    return domainEventDispatcherFactory.make("accountingServiceDomainEventDispatcher", accountingEventConsumer.domainEventHandlers());
  }

  @Bean
  public AccountingServiceCommandHandler accountCommandHandler() {
    return new AccountingServiceCommandHandler();
  }


  @Bean
  public CommandDispatcher commandDispatcher(AccountingServiceCommandHandler target,
                                             AccountServiceChannelConfiguration data, CommandDispatcherFactory commandDispatcherFactory) {
    return commandDispatcherFactory.make(data.getCommandDispatcherId(), target.commandHandlers());
  }

  @Bean
  public AccountServiceChannelConfiguration accountServiceChannelConfiguration() {
    return new AccountServiceChannelConfiguration("accountCommandDispatcher", "accountCommandChannel");
  }

  @Bean
  public SagaReplyRequestedEventSubscriber sagaReplyRequestedEventSubscriber() {
    return new SagaReplyRequestedEventSubscriber("accountingServiceSagaReplyRequestedEventSubscriber", Collections.singleton(Account.class.getName()));
  }

}


// Node: sagaReplyRequestedEventSubscriber
// Node: SagaReplyRequestedEventSubscriber
// Node: assertNotContainsOrderId
// Node: indexOf
package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import io.eventuate.common.json.mapper.JSonMapper;
import io.eventuate.common.spring.jdbc.EventuateTransactionTemplateConfiguration;
import io.eventuate.tram.spring.inmemory.TramInMemoryConfiguration;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistory;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryDao;
import net.chrisrichardson.ftgo.cqrs.orderhistory.OrderHistoryFilter;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;

import java.util.List;
import java.util.Optional;

import static java.util.Collections.singleton;
import static java.util.Collections.singletonList;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

@RunWith(SpringJUnit4ClassRunner.class)
@SpringBootTest(classes = {OrderHistoryDaoDynamoDbTest.OrderHistoryDaoDynamoDbTestConfiguration.class})
public class OrderHistoryDaoDynamoDbTest {

  @Configuration
  @EnableAutoConfiguration
  @ComponentScan
  @Import({OrderHistoryDynamoDBConfiguration.class, TramInMemoryConfiguration.class, EventuateTransactionTemplateConfiguration.class})
  static public class OrderHistoryDaoDynamoDbTestConfiguration {

  }

  private String consumerId;
  private Order order1;
  private String orderId;
  @Autowired
  private OrderHistoryDao dao;
  private String restaurantName;
  private String chickenVindaloo;
  private Optional<SourceEvent> eventSource;
  private long restaurantId;

  @Before
  public void setup() {
    consumerId = "consumerId" + System.currentTimeMillis();
    orderId = "orderId" + System.currentTimeMillis();
    restaurantName = "Ajanta" + System.currentTimeMillis();
    chickenVindaloo = "Chicken Vindaloo" + System.currentTimeMillis();
    restaurantId = 101L;

    order1 = new Order(orderId, consumerId, OrderState.APPROVAL_PENDING, singletonList(new OrderLineItem("-1", chickenVindaloo, Money.ZERO, 0)), null, restaurantId, restaurantName);
    order1.setCreationDate(DateTime.now().minusDays(5));
    eventSource = Optional.of(new SourceEvent("Order", orderId, "11212-34343"));

    dao.addOrder(order1, eventSource);
  }

  @Test
  public void shouldFindOrder() {
    Optional<Order> order = dao.findOrder(orderId);
    assertOrderEquals(order1, order.get());
  }

  @Test
  public void shouldIgnoreDuplicateAdd() {
    dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.empty());
    assertFalse(dao.addOrder(order1, eventSource));
    Optional<Order> order = dao.findOrder(orderId);
    assertEquals(OrderState.CANCELLED, order.get().getStatus());
  }

  @Test
  public void shouldFindOrders() {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter());
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    Order retrievedOrder = assertContainsOrderId(orderId, orders);
    assertOrderEquals(order1, retrievedOrder);
  }

  private void assertOrderEquals(Order expected, Order other) {
    System.out.println("Expected=" + JSonMapper.toJson(expected.getLineItems()));
    System.out.println("actual  =" + JSonMapper.toJson(other.getLineItems()));
    assertEquals(expected.getLineItems(), other.getLineItems());
    assertEquals(expected.getStatus(), other.getStatus());
    assertEquals(expected.getCreationDate(), other.getCreationDate());
    assertEquals(expected.getRestaurantId(), other.getRestaurantId());
    assertEquals(expected.getRestaurantName(), other.getRestaurantName());
  }


  @Test
  public void shouldFindOrdersWithStatus() throws InterruptedException {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withStatus(OrderState.APPROVAL_PENDING));
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    assertContainsOrderId(orderId, orders);
  }

  @Test
  public void shouldCancel() throws InterruptedException {
    dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.of(new SourceEvent("a", "b", "c")));
    Order order = dao.findOrder(orderId).get();
    assertEquals(OrderState.CANCELLED, order.getStatus());
  }

  @Test
  public void shouldHandleCancel() throws InterruptedException {
    assertTrue(dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.of(new SourceEvent("a", "b", "c"))));
    assertFalse(dao.updateOrderState(orderId, OrderState.CANCELLED, Optional.of(new SourceEvent("a", "b", "c"))));
  }

  @Test
  public void shouldFindOrdersWithCancelledStatus() {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withStatus(OrderState.CANCELLED));
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    assertNotContainsOrderId(orderId, orders);
  }

  // FIXME
//  @Test
//  public void shouldFindOrderByRestaurantName() {
//    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withKeywords(singleton(restaurantName)));
//    assertNotNull(result);
//    List<Order> orders = result.getOrders();
//    assertContainsOrderId(orderId, orders);
//  }

  @Test
  public void shouldFindOrderByMenuItem() {
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withKeywords(singleton(chickenVindaloo)));
    assertNotNull(result);
    List<Order> orders = result.getOrders();
    assertContainsOrderId(orderId, orders);
  }


  @Test
  public void shouldReturnOrdersSorted() {
    String orderId2 = "orderId" + System.currentTimeMillis();
    Order order2 = new Order(orderId2, consumerId, OrderState.APPROVAL_PENDING, singletonList(new OrderLineItem("-1", "Lamb 65", Money.ZERO, -1)), null, restaurantId, restaurantName);
    order2.setCreationDate(DateTime.now().minusDays(1));
    dao.addOrder(order2, eventSource);
    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter());
    List<Order> orders = result.getOrders();

    int idx1 = indexOf(orders, orderId);
    int idx2 = indexOf(orders, orderId2);
    assertTrue(idx2 < idx1);
  }

  private int indexOf(List<Order> orders, String orderId2) {
    Order order = orders.stream().filter(o -> o.getOrderId().equals(orderId2)).findFirst().get();
    return orders.indexOf(order);
  }

  private Order assertContainsOrderId(String orderId, List<Order> orders) {
    Optional<Order> order = orders.stream().filter(o -> o.getOrderId().equals(orderId)).findFirst();
    assertTrue("Order not found", order.isPresent());
    return order.get();
  }

  private void assertNotContainsOrderId(String orderId, List<Order> orders) {
    Optional<Order> order = orders.stream().filter(o -> o.getOrderId().equals(orderId)).findFirst();
    assertFalse(order.isPresent());
  }

  @Test
  public void shouldPaginateResults() {
    String orderId2 = "orderId" + System.currentTimeMillis();
    Order order2 = new Order(orderId2, consumerId, OrderState.APPROVAL_PENDING, singletonList(new OrderLineItem("-1", "Lamb 65", Money.ZERO, -1)), null, restaurantId, restaurantName);
    order2.setCreationDate(DateTime.now().minusDays(1));
    dao.addOrder(order2, eventSource);

    OrderHistory result = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withPageSize(1));

    assertEquals(1, result.getOrders().size());
    assertTrue(result.getStartKey().isPresent());

    OrderHistory result2 = dao.findOrderHistory(consumerId, new OrderHistoryFilter().withPageSize(1).withStartKeyToken(result.getStartKey()));

    assertEquals(1, result.getOrders().size());

  }

}

// Node: stream
// Node: filter
// Node: findFirst
// Node: getStartKey
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


// Node: RequestParam
// Node: GetOrdersResponse
// Node: collect
// Node: toList
// Node: makeGetOrderResponse
// Node: getOrder
package net.chrisrichardson.ftgo.cqrs.orderhistory.web;

import java.util.List;

public class GetOrdersResponse {
  private List<GetOrderResponse> orders;
  private String startKey;

  private GetOrdersResponse() {
  }

  public List<GetOrderResponse> getOrders() {
    return orders;
  }

  public void setOrders(List<GetOrderResponse> orders) {
    this.orders = orders;
  }

  public String getStartKey() {
    return startKey;
  }

  public void setStartKey(String startKey) {
    this.startKey = startKey;
  }

  public GetOrdersResponse(List<GetOrderResponse> orders, String startKey) {
    this.orders = orders;
    this.startKey = startKey;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-history-service/src/main/java/net/chrisrichardson/ftgo/cqrs/orderhistory/web/GetOrdersResponse.java:GetOrdersResponse.<init>
// Node: setStartKey
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


// Node: withL
// Node: mapOrderLineItem
// Node: addMEntry
// Node: toOrder
// Node: getString
// Node: toLineItems2
// Node: getList
// Node: getLong
// Node: hasAttribute
// Node: DateTime
// Node: toLineItem2
// Node: intValue
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


package net.chrisrichardson.ftgo.cqrs.orderhistory.dynamodb;

import org.apache.commons.lang.StringUtils;

import java.util.Optional;

public class Expressions {

  static String and(String s1, Optional<String> s2) {
    return s2.map(x -> and(s1, x)).orElse(s1);
  }

  static String and(String s1, String s2) {
    if (StringUtils.isBlank(s1))
      return s2;
    if (StringUtils.isBlank(s2))
      return s1;
    return String.format("(%s) AND (%s)", s1, s2);
  }

  static String or(String s1, String s2) {
    if (StringUtils.isBlank(s1))
      return s2;
    if (StringUtils.isBlank(s2))
      return s1;
    return String.format("(%s) AND (%s)", s1, s2);
  }
}


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


package net.chrisrichardson.ftgo.deliveryservice.api.web;

public class DeliveryInfo {

  private long id;
  private DeliveryState state;

  public DeliveryInfo() {
  }

  public DeliveryInfo(long id, DeliveryState state) {

    this.id = id;
    this.state = state;
  }

  public long getId() {
    return id;
  }

  public void setId(long id) {
    this.id = id;
  }

  public DeliveryState getState() {
    return state;
  }

  public void setState(DeliveryState state) {
    this.state = state;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service-api/src/main/java/net/chrisrichardson/ftgo/deliveryservice/api/web/DeliveryInfo.java:DeliveryInfo.<init>
// Node: DeliveryInfo
package net.chrisrichardson.ftgo.deliveryservice.api.web;

import java.util.List;

public class DeliveryStatus {
  private DeliveryInfo deliveryInfo;
  private Long assignedCourier;
  private List<ActionInfo> courierActions;

  public DeliveryStatus() {
  }

  public DeliveryInfo getDeliveryInfo() {
    return deliveryInfo;
  }

  public void setDeliveryInfo(DeliveryInfo deliveryInfo) {
    this.deliveryInfo = deliveryInfo;
  }

  public Long getAssignedCourier() {
    return assignedCourier;
  }

  public void setAssignedCourier(Long assignedCourier) {
    this.assignedCourier = assignedCourier;
  }

  public List<ActionInfo> getCourierActions() {
    return courierActions;
  }

  public void setCourierActions(List<ActionInfo> courierActions) {
    this.courierActions = courierActions;
  }

  public DeliveryStatus(DeliveryInfo deliveryInfo, Long assignedCourier, List<ActionInfo> courierActions) {
    this.deliveryInfo = deliveryInfo;
    this.assignedCourier = assignedCourier;
    this.courierActions = courierActions;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service-api/src/main/java/net/chrisrichardson/ftgo/deliveryservice/api/web/DeliveryStatus.java:DeliveryStatus.<init>
// Node: DeliveryStatus
// Node: getDeliveryInfo
// Node: getAssignedCourier
// Node: setCourierActions
package net.chrisrichardson.ftgo.orderservice.cucumber;

import cucumber.api.java.Before;
import cucumber.api.java.en.And;
import cucumber.api.java.en.Given;
import cucumber.api.java.en.Then;
import cucumber.api.java.en.When;
import io.eventuate.tram.spring.jdbckafka.TramJdbcKafkaConfiguration;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.messaging.consumer.MessageConsumer;
import io.eventuate.tram.sagas.testing.SagaParticipantChannels;
import io.eventuate.tram.sagas.testing.SagaParticipantStubManager;
import io.eventuate.tram.sagas.spring.testing.SagaParticipantStubManagerConfiguration;
import io.eventuate.tram.testing.MessageTracker;
import io.restassured.response.Response;
import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.kitchenservice.api.CancelCreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.ConfirmCreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicket;
import net.chrisrichardson.ftgo.kitchenservice.api.CreateTicketReply;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderRequest;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.domain.RestaurantRepository;
import net.chrisrichardson.ftgo.testutil.FtgoTestUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.test.context.ContextConfiguration;

import java.util.Arrays;
import java.util.Collections;

import static io.eventuate.tram.commands.consumer.CommandHandlerReplyBuilder.withSuccess;
import static io.eventuate.util.test.async.Eventually.eventually;
import static io.restassured.RestAssured.given;
import static java.util.Collections.singleton;
import static org.junit.Assert.*;


@SpringBootTest(classes = OrderServiceComponentTestStepDefinitions.TestConfiguration.class, webEnvironment = SpringBootTest.WebEnvironment.NONE)
@ContextConfiguration
public class OrderServiceComponentTestStepDefinitions {



  private Response response;
  private long consumerId;

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  private int port = 8082;
  private String host = FtgoTestUtil.getDockerHostIp();

  protected String baseUrl(String path) {
    return String.format("http://%s:%s%s", host, port, path);
  }

  @Configuration
  @EnableAutoConfiguration
  @Import({TramJdbcKafkaConfiguration.class, SagaParticipantStubManagerConfiguration.class})
  @EnableJpaRepositories(basePackageClasses = RestaurantRepository.class) // Need to verify that the restaurant has been created. Replace with verifyRestaurantCreatedInOrderService
  @EntityScan(basePackageClasses = Order.class)
  public static class TestConfiguration {

    @Bean
    public SagaParticipantChannels sagaParticipantChannels() {
      return new SagaParticipantChannels("consumerService", "kitchenService", "accountingService", "orderService");
    }

    @Bean
    public MessageTracker messageTracker(MessageConsumer messageConsumer) {
      return new MessageTracker(singleton("net.chrisrichardson.ftgo.orderservice.domain.Order"), messageConsumer) ;
    }

  }

  @Autowired
  protected SagaParticipantStubManager sagaParticipantStubManager;

  @Autowired
  protected MessageTracker messageTracker;

  @Autowired
  protected DomainEventPublisher domainEventPublisher;

  @Autowired
  protected RestaurantRepository restaurantRepository;


  @Before
  public void setUp() {
    sagaParticipantStubManager.reset();
  }

  @Given("A valid consumer")
  public void useConsumer() {
    sagaParticipantStubManager.
            forChannel("consumerService")
            .when(ValidateOrderByConsumer.class).replyWith(cm -> withSuccess());
  }

  public enum CreditCardType { valid, expired}

  @Given("using a(.?) (.*) credit card")
  public void useCreditCard(String ignore, CreditCardType creditCard) {
    switch (creditCard) {
      case valid :
        sagaParticipantStubManager
                .forChannel("accountingService")
                .when(AuthorizeCommand.class).replyWithSuccess();
        break;
      case expired:
        sagaParticipantStubManager
                .forChannel("accountingService")
                .when(AuthorizeCommand.class).replyWithFailure();
        break;
      default:
        fail("Don't know what to do with this credit card");
    }
  }

  @Given("the restaurant is accepting orders")
  public void restaurantAcceptsOrder() {
    sagaParticipantStubManager
            .forChannel("kitchenService")
            .when(CreateTicket.class).replyWith(cm -> withSuccess(new CreateTicketReply(cm.getCommand().getOrderId())))
            .when(ConfirmCreateTicket.class).replyWithSuccess()
            .when(CancelCreateTicket.class).replyWithSuccess();

    if (!restaurantRepository.findById(RestaurantMother.AJANTA_ID).isPresent()) {
      domainEventPublisher.publish("net.chrisrichardson.ftgo.restaurantservice.domain.Restaurant", RestaurantMother.AJANTA_ID,
              Collections.singletonList(RestaurantMother.makeAjantaRestaurantCreatedEvent()));

      eventually(() -> {
        FtgoTestUtil.assertPresent(restaurantRepository.findById(RestaurantMother.AJANTA_ID));
      });
    }
  }

  @When("I place an order for Chicken Vindaloo at Ajanta")
  public void placeOrder() {

    response = given().
            body(new CreateOrderRequest(consumerId,
                    RestaurantMother.AJANTA_ID, OrderDetailsMother.DELIVERY_ADDRESS, OrderDetailsMother.DELIVERY_TIME, Collections.singletonList(
                            new CreateOrderRequest.LineItem(RestaurantMother.CHICKEN_VINDALOO_MENU_ITEM_ID,
                                                            OrderDetailsMother.CHICKEN_VINDALOO_QUANTITY)))).
            contentType("application/json").
            when().
            post(baseUrl("/orders"));
  }

  @Then("the order should be (.*)")
  public void theOrderShouldBeInState(String desiredOrderState) {

      // TODO This doesn't make sense when the `OrderService` is live => duplicate replies

//    sagaParticipantStubManager
//            .forChannel("orderService")
//            .when(ApproveOrderCommand.class).replyWithSuccess();
//
    Integer orderId =
            this.response.
                    then().
                    statusCode(200).
                    extract().
                    path("orderId");

    assertNotNull(orderId);

    eventually(() -> {
      String state = given().
              when().
              get(baseUrl("/orders/" + orderId)).
              then().
              statusCode(200)
              .extract().
                      path("state");
      assertEquals(desiredOrderState, state);
    });

    sagaParticipantStubManager.verifyCommandReceived("kitchenService", CreateTicket.class);

  }

  @And("an (.*) event should be published")
  public void verifyEventPublished(String expectedEventClass) {
    messageTracker.assertDomainEventPublished("net.chrisrichardson.ftgo.orderservice.domain.Order",
            findEventClass(expectedEventClass, "net.chrisrichardson.ftgo.orderservice.domain", "net.chrisrichardson.ftgo.orderservice.api.events"));
  }

  private String findEventClass(String expectedEventClass, String... packages) {
    return Arrays.stream(packages).map(p -> p + "." + expectedEventClass).filter(className -> {
      try {
        Class.forName(className);
        return true;
      } catch (ClassNotFoundException e) {
        return false;
      }
    }).findFirst().orElseThrow(() -> new RuntimeException(String.format("Cannot find class %s in packages %s", expectedEventClass, String.join(",", packages))));
  }

}


// Node: verifyEventPublished
// Node: assertDomainEventPublished
// Node: findEventClass
// Node: MenuItemIdAndQuantity
// Node: newBuilder
package net.chrisrichardson.ftgo.orderservice.sagas.createorder;

import net.chrisrichardson.ftgo.accountservice.api.AuthorizeCommand;
import net.chrisrichardson.ftgo.consumerservice.api.ValidateOrderByConsumer;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.ApproveOrderCommand;
import net.chrisrichardson.ftgo.orderservice.sagaparticipants.RejectOrderCommand;
import net.chrisrichardson.ftgo.kitchenservice.api.*;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

import static java.util.stream.Collectors.toList;

public class CreateOrderSagaState {

  private Logger logger = LoggerFactory.getLogger(getClass());

  private Long orderId;

  private OrderDetails orderDetails;
  private long ticketId;

  public Long getOrderId() {
    return orderId;
  }

  private CreateOrderSagaState() {
  }

  public CreateOrderSagaState(Long orderId, OrderDetails orderDetails) {
    this.orderId = orderId;
    this.orderDetails = orderDetails;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  public OrderDetails getOrderDetails() {
    return orderDetails;
  }

  public void setOrderId(Long orderId) {
    this.orderId = orderId;
  }

  public void setTicketId(long ticketId) {
    this.ticketId = ticketId;
  }

  public long getTicketId() {
    return ticketId;
  }

  CreateTicket makeCreateTicketCommand() {
    return new CreateTicket(getOrderDetails().getRestaurantId(), getOrderId(), makeTicketDetails(getOrderDetails()));
  }

  private TicketDetails makeTicketDetails(OrderDetails orderDetails) {
    // TODO FIXME
    return new TicketDetails(makeTicketLineItems(orderDetails.getLineItems()));
  }

  private List<TicketLineItem> makeTicketLineItems(List<OrderLineItem> lineItems) {
    return lineItems.stream().map(this::makeTicketLineItem).collect(toList());
  }

  private TicketLineItem makeTicketLineItem(OrderLineItem orderLineItem) {
    return new TicketLineItem(orderLineItem.getMenuItemId(), orderLineItem.getName(), orderLineItem.getQuantity());
  }

  void handleCreateTicketReply(CreateTicketReply reply) {
    logger.debug("getTicketId {}", reply.getTicketId());
    setTicketId(reply.getTicketId());
  }

  CancelCreateTicket makeCancelCreateTicketCommand() {
    return new CancelCreateTicket(getOrderId());
  }

  RejectOrderCommand makeRejectOrderCommand() {
    return new RejectOrderCommand(getOrderId());
  }

  ValidateOrderByConsumer makeValidateOrderByConsumerCommand() {
    ValidateOrderByConsumer x = new ValidateOrderByConsumer();
    x.setConsumerId(getOrderDetails().getConsumerId());
    x.setOrderId(getOrderId());
    x.setOrderTotal(getOrderDetails().getOrderTotal().asString());
    return x;
  }

  AuthorizeCommand makeAuthorizeCommand() {
    return new AuthorizeCommand().withConsumerId(getOrderDetails().getConsumerId()).withOrderId(getOrderId()).withOrderTotal(getOrderDetails().getOrderTotal().asString());
  }

  ApproveOrderCommand makeApproveOrderCommand() {
    return new ApproveOrderCommand(getOrderId());
  }

  ConfirmCreateTicket makeConfirmCreateTicketCommand() {
    return new ConfirmCreateTicket(getTicketId());

  }
}


// Node: makeTicketLineItem
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


// Node: getLineItemsList
// Node: onNext
// Node: onCompleted
// Node: setMessage
package net.chrisrichardson.ftgo.orderservice.web;


import net.chrisrichardson.ftgo.orderservice.domain.Restaurant;
import net.chrisrichardson.ftgo.orderservice.domain.RestaurantRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(path = "/restaurants")
public class RestaurantController {

  @Autowired
  private RestaurantRepository restaurantRepository;

  @RequestMapping(path="/{restaurantId}", method= RequestMethod.GET)
  public ResponseEntity<GetRestaurantResponse> getRestaurant(@PathVariable long restaurantId) {
    return restaurantRepository.findById(restaurantId)
            .map(restaurant -> new ResponseEntity<>(new GetRestaurantResponse(restaurantId), HttpStatus.OK))
            .orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }
}


// Node: getRestaurant
package net.chrisrichardson.ftgo.orderservice.web;

import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

public class MenuItemIdAndQuantity {

  private String menuItemId;
  private int quantity;

  public String getMenuItemId() {
    return menuItemId;
  }

  public int getQuantity() {
    return quantity;
  }

  public void setMenuItemId(String menuItemId) {
    this.menuItemId = menuItemId;
  }

  public MenuItemIdAndQuantity(String menuItemId, int quantity) {

    this.menuItemId = menuItemId;
    this.quantity = quantity;

  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

}


package net.chrisrichardson.ftgo.orderservice.web;

import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderRequest;
import net.chrisrichardson.ftgo.orderservice.api.web.CreateOrderResponse;
import net.chrisrichardson.ftgo.orderservice.api.web.ReviseOrderRequest;
import net.chrisrichardson.ftgo.orderservice.domain.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;

import static java.util.stream.Collectors.toList;

@RestController
@RequestMapping(path = "/orders")
public class OrderController {

  private OrderService orderService;

  private OrderRepository orderRepository;


  public OrderController(OrderService orderService, OrderRepository orderRepository) {
    this.orderService = orderService;
    this.orderRepository = orderRepository;
  }

  @RequestMapping(method = RequestMethod.POST)
  public CreateOrderResponse create(@RequestBody CreateOrderRequest request) {
    Order order = orderService.createOrder(request.getConsumerId(),
            request.getRestaurantId(),
            new DeliveryInformation(request.getDeliveryTime(), request.getDeliveryAddress()),
            request.getLineItems().stream().map(x -> new MenuItemIdAndQuantity(x.getMenuItemId(), x.getQuantity())).collect(toList())
    );
    return new CreateOrderResponse(order.getId());
  }


  @RequestMapping(path = "/{orderId}", method = RequestMethod.GET)
  public ResponseEntity<GetOrderResponse> getOrder(@PathVariable long orderId) {
    Optional<Order> order = orderRepository.findById(orderId);
    return order.map(o -> new ResponseEntity<>(makeGetOrderResponse(o), HttpStatus.OK)).orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }

  private GetOrderResponse makeGetOrderResponse(Order order) {
    return new GetOrderResponse(order.getId(), order.getState(), order.getOrderTotal());
  }

  @RequestMapping(path = "/{orderId}/cancel", method = RequestMethod.POST)
  public ResponseEntity<GetOrderResponse> cancel(@PathVariable long orderId) {
    try {
      Order order = orderService.cancel(orderId);
      return new ResponseEntity<>(makeGetOrderResponse(order), HttpStatus.OK);
    } catch (OrderNotFoundException e) {
      return new ResponseEntity<>(HttpStatus.NOT_FOUND);
    }
  }

  @RequestMapping(path = "/{orderId}/revise", method = RequestMethod.POST)
  public ResponseEntity<GetOrderResponse> revise(@PathVariable long orderId, @RequestBody ReviseOrderRequest request) {
    try {
      Order order = orderService.reviseOrder(orderId, new OrderRevision(Optional.empty(), request.getRevisedOrderLineItems()));
      return new ResponseEntity<>(makeGetOrderResponse(order), HttpStatus.OK);
    } catch (OrderNotFoundException e) {
      return new ResponseEntity<>(HttpStatus.NOT_FOUND);
    }
  }

}


package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;

import javax.persistence.*;
import java.util.List;
import java.util.Optional;

@Entity
@Table(name = "order_service_restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  private Long id;

  @Embedded
  @ElementCollection
  @CollectionTable(name = "order_service_restaurant_menu_items")
  private List<MenuItem> menuItems;
  private String name;

  private Restaurant() {
  }

  public Restaurant(long id, String name, List<MenuItem> menuItems) {
    this.id = id;
    this.name = name;
    this.menuItems = menuItems;
  }

  public List<OrderDomainEvent> reviseMenu(List<MenuItem> revisedMenu) {
    throw new UnsupportedOperationException();
  }

  public void verifyRestaurantDetails(TicketDetails ticketDetails) {
    // TODO - implement me
  }

  public Long getId() {
    return id;
  }

  public Optional<MenuItem> findMenuItem(String menuItemId) {
    return menuItems.stream().filter(mi -> mi.getId().equals(menuItemId)).findFirst();
  }

  public List<MenuItem> getMenuItems() {
    return menuItems;
  }

  public String getName() {
    return name;
  }
}


// Node: findMenuItem
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

// Node: findOrderLineItem
// Node: reduce
// Node: updateLineItems
package net.chrisrichardson.ftgo.orderservice.domain;

public class RevisedOrder {
  private final Order order;
  private final LineItemQuantityChange change;

  public RevisedOrder(Order order, LineItemQuantityChange change) {
    this.order = order;
    this.change = change;
  }

  public Order getOrder() {
    return order;
  }

  public LineItemQuantityChange getChange() {
    return change;
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



package net.chrisrichardson.ftgo.orderservice.domain;


import net.chrisrichardson.ftgo.common.Address;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.AttributeOverride;
import javax.persistence.AttributeOverrides;
import javax.persistence.Column;
import javax.persistence.Embedded;
import java.time.LocalDateTime;

@Access(AccessType.FIELD)
public class DeliveryInformation {

  private LocalDateTime deliveryTime;

  @Embedded
  @AttributeOverrides({
    @AttributeOverride(name="state", column=@Column(name="delivery_state"))
  })
  private Address deliveryAddress;

  public DeliveryInformation() {
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public DeliveryInformation(LocalDateTime deliveryTime, Address deliveryAddress) {
    this.deliveryTime = deliveryTime;
    this.deliveryAddress = deliveryAddress;
  }

  public LocalDateTime getDeliveryTime() {
    return deliveryTime;
  }

  public void setDeliveryTime(LocalDateTime deliveryTime) {
    this.deliveryTime = deliveryTime;
  }

  public Address getDeliveryAddress() {
    return deliveryAddress;
  }

  public void setDeliveryAddress(Address deliveryAddress) {
    this.deliveryAddress = deliveryAddress;
  }
}


package net.chrisrichardson.ftgo.orderservice.domain;

public class InvalidMenuItemIdException extends RuntimeException {
  public InvalidMenuItemIdException(String menuItemId) {
    super("Invalid menu item id " + menuItemId);
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/main/java/net/chrisrichardson/ftgo/orderservice/domain/InvalidMenuItemIdException.java:InvalidMenuItemIdException.<init>
// Node: InvalidMenuItemIdException
package net.chrisrichardson.ftgo.orderservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


// Node: makeOrderLineItems
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import io.eventuate.tram.events.publisher.DomainEventPublisher;
import io.eventuate.tram.sagas.orchestration.SagaInstanceFactory;
import io.micrometer.core.instrument.MeterRegistry;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.sagas.cancelorder.CancelOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.cancelorder.CancelOrderSagaData;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.createorder.CreateOrderSagaState;
import net.chrisrichardson.ftgo.orderservice.sagas.reviseorder.ReviseOrderSaga;
import net.chrisrichardson.ftgo.orderservice.sagas.reviseorder.ReviseOrderSagaData;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.function.Function;

import static java.util.stream.Collectors.toList;

public class OrderService {

  private Logger logger = LoggerFactory.getLogger(getClass());

  private SagaInstanceFactory sagaInstanceFactory;

  private OrderRepository orderRepository;

  private RestaurantRepository restaurantRepository;

  private CreateOrderSaga createOrderSaga;

  private CancelOrderSaga cancelOrderSaga;

  private ReviseOrderSaga reviseOrderSaga;

  private OrderDomainEventPublisher orderAggregateEventPublisher;

  private Optional<MeterRegistry> meterRegistry;

  public OrderService(SagaInstanceFactory sagaInstanceFactory,
                      OrderRepository orderRepository,
                      DomainEventPublisher eventPublisher,
                      RestaurantRepository restaurantRepository,
                      CreateOrderSaga createOrderSaga,
                      CancelOrderSaga cancelOrderSaga,
                      ReviseOrderSaga reviseOrderSaga,
                      OrderDomainEventPublisher orderAggregateEventPublisher,
                      Optional<MeterRegistry> meterRegistry) {

    this.sagaInstanceFactory = sagaInstanceFactory;
    this.orderRepository = orderRepository;
    this.restaurantRepository = restaurantRepository;
    this.createOrderSaga = createOrderSaga;
    this.cancelOrderSaga = cancelOrderSaga;
    this.reviseOrderSaga = reviseOrderSaga;
    this.orderAggregateEventPublisher = orderAggregateEventPublisher;
    this.meterRegistry = meterRegistry;
  }

  @Transactional
  public Order createOrder(long consumerId, long restaurantId, DeliveryInformation deliveryInformation,
                           List<MenuItemIdAndQuantity> lineItems) {
    Restaurant restaurant = restaurantRepository.findById(restaurantId)
            .orElseThrow(() -> new RestaurantNotFoundException(restaurantId));

    List<OrderLineItem> orderLineItems = makeOrderLineItems(lineItems, restaurant);

    ResultWithDomainEvents<Order, OrderDomainEvent> orderAndEvents =
            Order.createOrder(consumerId, restaurant, deliveryInformation, orderLineItems);

    Order order = orderAndEvents.result;
    orderRepository.save(order);

    orderAggregateEventPublisher.publish(order, orderAndEvents.events);

    OrderDetails orderDetails = new OrderDetails(consumerId, restaurantId, orderLineItems, order.getOrderTotal());

    CreateOrderSagaState data = new CreateOrderSagaState(order.getId(), orderDetails);
    sagaInstanceFactory.create(createOrderSaga, data);

    meterRegistry.ifPresent(mr -> mr.counter("placed_orders").increment());

    return order;
  }


  private List<OrderLineItem> makeOrderLineItems(List<MenuItemIdAndQuantity> lineItems, Restaurant restaurant) {
    return lineItems.stream().map(li -> {
      MenuItem om = restaurant.findMenuItem(li.getMenuItemId()).orElseThrow(() -> new InvalidMenuItemIdException(li.getMenuItemId()));
      return new OrderLineItem(li.getMenuItemId(), om.getName(), om.getPrice(), li.getQuantity());
    }).collect(toList());
  }


  public Optional<Order> confirmChangeLineItemQuantity(Long orderId, OrderRevision orderRevision) {
    return orderRepository.findById(orderId).map(order -> {
      List<OrderDomainEvent> events = order.confirmRevision(orderRevision);
      orderAggregateEventPublisher.publish(order, events);
      return order;
    });
  }

  public void noteReversingAuthorization(Long orderId) {
    throw new UnsupportedOperationException();
  }

  @Transactional
  public Order cancel(Long orderId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
    CancelOrderSagaData sagaData = new CancelOrderSagaData(order.getConsumerId(), orderId, order.getOrderTotal());
    sagaInstanceFactory.create(cancelOrderSaga, sagaData);
    return order;
  }

  private Order updateOrder(long orderId, Function<Order, List<OrderDomainEvent>> updater) {
    return orderRepository.findById(orderId).map(order -> {
      orderAggregateEventPublisher.publish(order, updater.apply(order));
      return order;
    }).orElseThrow(() -> new OrderNotFoundException(orderId));
  }

  public void approveOrder(long orderId) {
    updateOrder(orderId, Order::noteApproved);
    meterRegistry.ifPresent(mr -> mr.counter("approved_orders").increment());
  }

  public void rejectOrder(long orderId) {
    updateOrder(orderId, Order::noteRejected);
    meterRegistry.ifPresent(mr -> mr.counter("rejected_orders").increment());
  }

  public void beginCancel(long orderId) {
    updateOrder(orderId, Order::cancel);
  }

  public void undoCancel(long orderId) {
    updateOrder(orderId, Order::undoPendingCancel);
  }

  public void confirmCancelled(long orderId) {
    updateOrder(orderId, Order::noteCancelled);
  }

  @Transactional
  public Order reviseOrder(long orderId, OrderRevision orderRevision) {
    Order order = orderRepository.findById(orderId).orElseThrow(() -> new OrderNotFoundException(orderId));
    ReviseOrderSagaData sagaData = new ReviseOrderSagaData(order.getConsumerId(), orderId, null, orderRevision);
    sagaInstanceFactory.create(reviseOrderSaga, sagaData);
    return order;
  }

  public Optional<RevisedOrder> beginReviseOrder(long orderId, OrderRevision revision) {
    return orderRepository.findById(orderId).map(order -> {
      ResultWithDomainEvents<LineItemQuantityChange, OrderDomainEvent> result = order.revise(revision);
      orderAggregateEventPublisher.publish(order, result.events);
      return new RevisedOrder(order, result.result);
    });
  }

  public void undoPendingRevision(long orderId) {
    updateOrder(orderId, Order::rejectRevision);
  }

  public void confirmRevision(long orderId, OrderRevision revision) {
    updateOrder(orderId, order -> order.confirmRevision(revision));
  }

  public void createMenu(long id, String name, List<MenuItem> menuItems) {
    Restaurant restaurant = new Restaurant(id, name, menuItems);
    restaurantRepository.save(restaurant);
  }

  public void reviseMenu(long id, List<MenuItem> menuItems) {
    restaurantRepository.findById(id).map(restaurant -> {
      List<OrderDomainEvent> events = restaurant.reviseMenu(menuItems);
      return restaurant;
    }).orElseThrow(RuntimeException::new);
  }

}


package net.chrisrichardson.ftgo.orderservice.messaging;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.restaurantservice.events.Address;
import net.chrisrichardson.ftgo.restaurantservice.events.MenuItem;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.stream.Collectors;

public class RestaurantEventMapper {

  @NotNull
  public static List<MenuItem> fromMenuItems(List<net.chrisrichardson.ftgo.orderservice.domain.MenuItem> menuItems) {
    return menuItems.stream().map(mi -> new MenuItem().withId(mi.getId()).withName(mi.getName()).withPrice(mi.getPrice().asString())).collect(Collectors.toList());
  }

  public static Address fromAddress(net.chrisrichardson.ftgo.common.Address a) {
    return new Address().withStreet1(a.getStreet1()).withStreet2(a.getStreet2()).withCity(a.getCity()).withZip(a.getZip());
  }

  public static List<net.chrisrichardson.ftgo.orderservice.domain.MenuItem> toMenuItems(List<MenuItem> menuItems) {
    return menuItems.stream().map(mi -> new net.chrisrichardson.ftgo.orderservice.domain.MenuItem(mi.getId(), mi.getName(), new Money(mi.getPrice()))).collect(Collectors.toList());
  }

}


// Node: fromMenuItems
// Node: withName
// Node: withPrice
package net.chrisrichardson.ftgo.orderservice;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDetails;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderLineItem;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import net.chrisrichardson.ftgo.orderservice.domain.DeliveryInformation;
import net.chrisrichardson.ftgo.orderservice.domain.Order;
import net.chrisrichardson.ftgo.orderservice.web.MenuItemIdAndQuantity;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;

import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_ID;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.CHICKEN_VINDALOO;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.CHICKEN_VINDALOO_PRICE;

public class OrderDetailsMother {

  public static long CONSUMER_ID = 1511300065921L;

  public static final int CHICKEN_VINDALOO_QUANTITY = 5;
  public static final MenuItemIdAndQuantity CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY = new MenuItemIdAndQuantity(RestaurantMother.CHICKEN_VINDALOO_MENU_ITEM_ID, CHICKEN_VINDALOO_QUANTITY);
  public static final List<MenuItemIdAndQuantity> CHICKEN_VINDALOO_MENU_ITEMS_AND_QUANTITIES = Collections.singletonList(CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY);

  public static List<OrderLineItem> chickenVindalooLineItems() {
    return Collections.singletonList(new OrderLineItem(CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY.getMenuItemId(),
            CHICKEN_VINDALOO,
            CHICKEN_VINDALOO_PRICE,
            CHICKEN_VINDALOO_MENU_ITEM_AND_QUANTITY.getQuantity()));
  }

  public static final Money CHICKEN_VINDALOO_ORDER_TOTAL = CHICKEN_VINDALOO_PRICE.multiply(5);
  public static final OrderDetails CHICKEN_VINDALOO_ORDER_DETAILS = new OrderDetails(CONSUMER_ID, AJANTA_ID,
          chickenVindalooLineItems(), CHICKEN_VINDALOO_ORDER_TOTAL);

  public static long ORDER_ID = 99L;

  public static final OrderState CHICKEN_VINDALOO_ORDER_STATE = OrderState.APPROVAL_PENDING;

  public static final Address DELIVERY_ADDRESS = new Address("9 Amazing View", null, "Oakland", "CA", "94612");
  public static final LocalDateTime DELIVERY_TIME = LocalDateTime.now();
  public static final DeliveryInformation DELIVERY_INFORMATION = new DeliveryInformation(DELIVERY_TIME, DELIVERY_ADDRESS);

  private static Order makeAjantaOrder() {
    Order order = new Order(CONSUMER_ID, AJANTA_ID, new DeliveryInformation(DELIVERY_TIME, DELIVERY_ADDRESS), chickenVindalooLineItems());
    order.setId(ORDER_ID);
    return order;
  }

  public static Order CHICKEN_VINDALOO_ORDER = makeAjantaOrder();

}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-order-service/src/test/java/net/chrisrichardson/ftgo/orderservice/OrderDetailsMother.java:OrderDetailsMother.<init>
package net.chrisrichardson.ftgo.deliveryservice;

import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryServiceTestData;
import net.chrisrichardson.ftgo.deliveryservice.messaging.RestaurantEventMapper;
import net.chrisrichardson.ftgo.restaurantservice.events.RestaurantCreated;
import net.chrisrichardson.ftgo.restaurantservice.events.Menu;
import net.chrisrichardson.ftgo.restaurantservice.events.MenuItem;

import java.util.Collections;
import java.util.List;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.common.Money;

public class RestaurantEventMother {

  public static final String CHICKEN_VINDALOO = "Chicken Vindaloo";
  public static final String CHICKEN_VINDALOO_MENU_ITEM_ID = "1";
  public static final String CHICKEN_VINDALOO_PRICE = "12.34";
  public static final Address RESTAURANT_ADDRESS = new Address("1 Main Street", "Unit 99", "Oakland", "CA", "94611");

  public static MenuItem CHICKEN_VINDALOO_MENU_ITEM = new MenuItem()
    .withId(CHICKEN_VINDALOO_MENU_ITEM_ID)
    .withName(CHICKEN_VINDALOO)
    .withPrice(CHICKEN_VINDALOO_PRICE);

  public static final List<MenuItem> AJANTA_RESTAURANT_MENU_ITEMS = Collections.singletonList(CHICKEN_VINDALOO_MENU_ITEM);


  static RestaurantCreated makeRestaurantCreated() {
    return new RestaurantCreated()
            .withName("Delicious Indian")
            .withAddress(RestaurantEventMapper.fromAddress(DeliveryServiceTestData.PICKUP_ADDRESS))
            .withMenu(new Menu().withMenuItems(AJANTA_RESTAURANT_MENU_ITEMS));
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-delivery-service/src/component-test/java/net/chrisrichardson/ftgo/deliveryservice/RestaurantEventMother.java:RestaurantEventMother.<init>
package net.chrisrichardson.ftgo.deliveryservice.web;

import net.chrisrichardson.ftgo.deliveryservice.api.web.CourierAvailability;
import net.chrisrichardson.ftgo.deliveryservice.domain.DeliveryService;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryStatus;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
public class DeliveryServiceController {

  private DeliveryService deliveryService;

  public DeliveryServiceController(DeliveryService deliveryService) {
    this.deliveryService = deliveryService;
  }

  @RequestMapping(path="/couriers/{courierId}/availability", method= RequestMethod.POST)
  public void updateCourierLocation(@PathVariable long courierId, @RequestBody CourierAvailability availability) {
    deliveryService.updateAvailability(courierId, availability.isAvailable());
  }

  @RequestMapping(path="/deliveries/{deliveryId}", method= RequestMethod.GET)
  public ResponseEntity<DeliveryStatus> getDeliveryStatus(@PathVariable long deliveryId) {
    return deliveryService.getDeliveryInfo(deliveryId).map(ds -> new ResponseEntity<>(ds, HttpStatus.OK)).orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }


}


// Node: getDeliveryStatus
package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryActionType;
import net.chrisrichardson.ftgo.common.Address;

import javax.persistence.Embeddable;
import javax.persistence.EnumType;
import javax.persistence.Enumerated;
import java.time.LocalDateTime;

@Embeddable
public class Action {

  @Enumerated(EnumType.STRING)
  private DeliveryActionType type;
  private Address address;
  private LocalDateTime time;

  protected long deliveryId;

  private Action() {
  }

  public Action(DeliveryActionType type, long deliveryId, Address address, LocalDateTime time) {
    this.type = type;
    this.deliveryId = deliveryId;
    this.address = address;
    this.time = time;
  }

  public boolean actionFor(long deliveryId) {
    return this.deliveryId == deliveryId;
  }

  public static Action makePickup(long deliveryId, Address pickupAddress, LocalDateTime pickupTime) {
    return new Action(DeliveryActionType.PICKUP, deliveryId, pickupAddress, pickupTime);
  }

  public static Action makeDropoff(long deliveryId, Address deliveryAddress, LocalDateTime deliveryTime) {
    return new Action(DeliveryActionType.DROPOFF, deliveryId, deliveryAddress, deliveryTime);
  }


  public DeliveryActionType getType() {
    return type;
  }

  public Address getAddress() {
    return address;
  }
}


// Node: actionFor
package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.deliveryservice.api.web.ActionInfo;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryInfo;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryStatus;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.Random;
import java.util.stream.Collectors;

public class DeliveryService {

  private RestaurantRepository restaurantRepository;
  private DeliveryRepository deliveryRepository;
  private CourierRepository courierRepository;
  private Random random = new Random();

  public DeliveryService(RestaurantRepository restaurantRepository, DeliveryRepository deliveryRepository, CourierRepository courierRepository) {
    this.restaurantRepository = restaurantRepository;
    this.deliveryRepository = deliveryRepository;
    this.courierRepository = courierRepository;
  }

  public void createRestaurant(long restaurantId, String restaurantName, Address address) {
    restaurantRepository.save(Restaurant.create(restaurantId, restaurantName, address));
  }

  public void createDelivery(long orderId, long restaurantId, Address deliveryAddress) {
    Restaurant restaurant = restaurantRepository.findById(restaurantId).get();
    deliveryRepository.save(Delivery.create(orderId, restaurantId, restaurant.getAddress(), deliveryAddress));
  }

  public void scheduleDelivery(long orderId, LocalDateTime readyBy) {
    Delivery delivery = deliveryRepository.findById(orderId).get();

    // Stupid implementation

    List<Courier> couriers = courierRepository.findAllAvailable();
    Courier courier = couriers.get(random.nextInt(couriers.size()));
    courier.addAction(Action.makePickup(delivery.getId(), delivery.getPickupAddress(), readyBy));
    courier.addAction(Action.makeDropoff(delivery.getId(), delivery.getDeliveryAddress(), readyBy.plusMinutes(30)));

    delivery.schedule(readyBy, courier.getId());

  }

  public void cancelDelivery(long orderId) {
    Delivery delivery = deliveryRepository.findById(orderId).get();
    Long assignedCourierId = delivery.getAssignedCourier();
    delivery.cancel();
    if (assignedCourierId != null) {
      Courier courier = courierRepository.findById(assignedCourierId).get();
      courier.cancelDelivery(delivery.getId());
    }

  }



  // notePickedUp
  // noteDelivered
  // noteLocation

  void noteAvailable(long courierId) {
    courierRepository.findOrCreateCourier(courierId).noteAvailable();
  }

  void noteUnavailable(long courierId) {
    courierRepository.findOrCreateCourier(courierId).noteUnavailable();
  }

  private Courier findOrCreateCourier(long courierId) {
    Courier courier = Courier.create(courierId);
    try {
      return courierRepository.save(courier);
    } catch (DuplicateKeyException e) {
      return courierRepository.findById(courierId).get();
    }
  }

  @Transactional
  public void updateAvailability(long courierId, boolean available) {
    if (available)
      noteAvailable(courierId);
    else
      noteUnavailable(courierId);
  }


  // getCourierRoute()

  @Transactional
  public Optional<DeliveryStatus> getDeliveryInfo(long deliveryId) {
    return deliveryRepository.findById(deliveryId).map(delivery -> {
      Long assignedCourier = delivery.getAssignedCourier();
      List<Action> courierActions = Collections.EMPTY_LIST;
      if (assignedCourier != null) {
        Courier courier = courierRepository.findById(assignedCourier).get();
        courierActions = courier.actionsForDelivery(deliveryId);
      }
      return makeDeliveryStatus(delivery, assignedCourier, courierActions);
    });
  }

  private DeliveryStatus makeDeliveryStatus(Delivery delivery, Long assignedCourier, List<Action> courierActions) {
    return new DeliveryStatus(makeDeliveryInfo(delivery), assignedCourier, courierActions.stream().map(action -> makeActionInfo(action)).collect(Collectors.toList()));
  }

  private DeliveryInfo makeDeliveryInfo(Delivery delivery) {
    return new DeliveryInfo(delivery.getId(), delivery.getState());
  }

  private ActionInfo makeActionInfo(Action action) {
    return new ActionInfo(action.getType());
  }
}


// Node: cancelDelivery
// Node: actionsForDelivery
// Node: makeDeliveryStatus
// Node: makeDeliveryInfo
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


// Node: removeDelivery
package net.chrisrichardson.ftgo.deliveryservice.domain;

import javax.persistence.*;
import java.util.List;

@Entity
@Access(AccessType.FIELD)
public class Courier {

  @Id
  private long id;

  @Embedded
  private Plan plan;

  private Boolean available;

  private Courier() {
  }

  public Courier(long courierId) {
    this.id = courierId;
    this.plan = new Plan();
  }

  public static Courier create(long courierId) {
    return new Courier(courierId);
  }

  public void noteAvailable() {
    this.available = true;

  }

  public void addAction(Action action) {
    plan.add(action);
  }

  public void cancelDelivery(long deliveryId) {
    plan.removeDelivery(deliveryId);
  }

  public boolean isAvailable() {
    return available;
  }

  public Plan getPlan() {
    return plan;
  }

  public long getId() {
    return id;
  }

  public void noteUnavailable() {
    this.available = false;
  }

  public List<Action> actionsForDelivery(long deliveryId) {
    return plan.actionsForDelivery(deliveryId);
  }
}


package net.chrisrichardson.ftgo.deliveryservice.domain;

import net.chrisrichardson.ftgo.common.Address;
import net.chrisrichardson.ftgo.deliveryservice.api.web.DeliveryState;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Access(AccessType.FIELD)
public class Delivery {

  @Id
  private Long id;

  @Embedded
  @AttributeOverrides({
          @AttributeOverride(name="street1", column = @Column(name="pickup_street1")),
          @AttributeOverride(name="street2", column = @Column(name="pickup_street2")),
          @AttributeOverride(name="city", column = @Column(name="pickup_city")),
          @AttributeOverride(name="state", column = @Column(name="pickup_state")),
          @AttributeOverride(name="zip", column = @Column(name="pickup_zip")),
  }
  )
  private Address pickupAddress;

  @Enumerated(EnumType.STRING)
  private DeliveryState state;

  private long restaurantId;
  private LocalDateTime pickUpTime;

  @Embedded
  @AttributeOverrides({
          @AttributeOverride(name="street1", column = @Column(name="delivery_street1")),
          @AttributeOverride(name="street2", column = @Column(name="delivery_street2")),
          @AttributeOverride(name="city", column = @Column(name="delivery_city")),
          @AttributeOverride(name="state", column = @Column(name="delivery_state")),
          @AttributeOverride(name="zip", column = @Column(name="delivery_zip")),
  }
  )

  private Address deliveryAddress;
  private LocalDateTime deliveryTime;

  private Long assignedCourier;
  private LocalDateTime readyBy;

  private Delivery() {
  }

  public Delivery(long orderId, long restaurantId, Address pickupAddress, Address deliveryAddress) {
    this.id = orderId;
    this.pickupAddress = pickupAddress;
    this.state = DeliveryState.PENDING;
    this.restaurantId = restaurantId;
    this.deliveryAddress = deliveryAddress;
  }

  public static Delivery create(long orderId, long restaurantId, Address pickupAddress, Address deliveryAddress) {
    return new Delivery(orderId, restaurantId, pickupAddress, deliveryAddress);
  }

  public void schedule(LocalDateTime readyBy, long assignedCourier) {
    this.readyBy = readyBy;
    this.assignedCourier = assignedCourier;
    this.state = DeliveryState.SCHEDULED;

  }

  public void cancel() {
    this.state = DeliveryState.CANCELLED;
    this.assignedCourier = null;
  }


  public long getId() {
    return id;
  }

  public long getRestaurantId() {
    return restaurantId;
  }

  public Address getDeliveryAddress() {
    return deliveryAddress;
  }

  public Address getPickupAddress() {
    return pickupAddress;
  }

  public DeliveryState getState() {
    return state;
  }

  public Long getAssignedCourier() {
    return assignedCourier;
  }
}


package net.chrisrichardson.ftgo.kitchenservice.messagehandlers;

import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.restaurantservice.events.MenuItem;

import java.util.List;
import java.util.stream.Collectors;

public class RestaurantEventMapper {

  public static List<net.chrisrichardson.ftgo.kitchenservice.domain.MenuItem> toMenuItems(List<MenuItem> menuItems) {
    return menuItems.stream().map(mi -> new net.chrisrichardson.ftgo.kitchenservice.domain.MenuItem(mi.getId(), mi.getName(), new Money(mi.getPrice()))).collect(Collectors.toList());
  }

}


package net.chrisrichardson.ftgo.kitchenservice.web;

import net.chrisrichardson.ftgo.kitchenservice.domain.Restaurant;
import net.chrisrichardson.ftgo.kitchenservice.domain.RestaurantRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping(path = "/restaurants")
public class RestaurantController {

  @Autowired
  private RestaurantRepository restaurantRepository;

  @RequestMapping(path = "/{restaurantId}", method = RequestMethod.GET)
  public ResponseEntity<GetRestaurantResponse> getRestaurant(@PathVariable long restaurantId) {
    return restaurantRepository.findById(restaurantId)
            .map(restaurant -> new ResponseEntity<>(new GetRestaurantResponse(restaurantId), HttpStatus.OK))
            .orElseGet( () -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }
}


package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.common.DomainEvent;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.CollectionTable;
import javax.persistence.ElementCollection;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import java.util.List;

@Entity
@Table(name = "kitchen_service_restaurants")
@Access(AccessType.FIELD)
public class Restaurant {

  @Id
  private Long id;

  @Embedded
  @ElementCollection
  @CollectionTable(name = "kitchen_service_restaurant_menu_items")
  private List<MenuItem> menuItems;

  private Restaurant() {
  }

  public Restaurant(long id, List<MenuItem> menuItems) {
    this.id = id;
    this.menuItems = menuItems;
  }

  public List<DomainEvent> reviseMenu(RestaurantMenu revisedMenu) {
    throw new UnsupportedOperationException();
  }

  public void verifyRestaurantDetails(TicketDetails ticketDetails) {
    // TODO - implement me
  }

  public Long getId() {
    return id;
  }

}


package net.chrisrichardson.ftgo.kitchenservice.domain;

import net.chrisrichardson.ftgo.common.Money;
import org.apache.commons.lang.builder.EqualsBuilder;
import org.apache.commons.lang.builder.HashCodeBuilder;
import org.apache.commons.lang.builder.ToStringBuilder;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embeddable;

@Embeddable
@Access(AccessType.FIELD)
public class MenuItem {

  private String id;
  private String name;
  private Money price;

  private MenuItem() {
  }

  public MenuItem(String id, String name, Money price) {
    this.id = id;
    this.name = name;
    this.price = price;
  }

  @Override
  public boolean equals(Object o) {
    return EqualsBuilder.reflectionEquals(this, o);
  }

  @Override
  public int hashCode() {
    return HashCodeBuilder.reflectionHashCode(this);
  }

  @Override
  public String toString() {
    return ToStringBuilder.reflectionToString(this);
  }

  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Money getPrice() {
    return price;
  }

  public void setPrice(Money price) {
    this.price = price;
  }
}


package net.chrisrichardson.ftgo.kitchenservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.NotYetImplementedException;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;
import net.chrisrichardson.ftgo.common.UnsupportedStateTransitionException;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketDetails;
import net.chrisrichardson.ftgo.kitchenservice.api.TicketLineItem;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketAcceptedEvent;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketCancelled;
import net.chrisrichardson.ftgo.kitchenservice.api.events.TicketDomainEvent;

import javax.persistence.*;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import static java.util.Collections.emptyList;
import static java.util.Collections.singletonList;

@Entity
@Table(name = "tickets")
@Access(AccessType.FIELD)
public class Ticket {

  @Id
  private Long id;

  @Enumerated(EnumType.STRING)
  private TicketState state;

  private TicketState previousState;

  private Long restaurantId;

  @ElementCollection
  @CollectionTable(name = "ticket_line_items")
  private List<TicketLineItem> lineItems;

  private LocalDateTime readyBy;
  private LocalDateTime acceptTime;
  private LocalDateTime preparingTime;
  private LocalDateTime pickedUpTime;
  private LocalDateTime readyForPickupTime;

  public static ResultWithDomainEvents<Ticket, TicketDomainEvent> create(long restaurantId, Long id, TicketDetails details) {
    return new ResultWithDomainEvents<>(new Ticket(restaurantId, id, details));
  }

  private Ticket() {
  }

  public Ticket(long restaurantId, Long id, TicketDetails details) {
    this.restaurantId = restaurantId;
    this.id = id;
    this.state = TicketState.CREATE_PENDING;
    this.lineItems = details.getLineItems();
  }

  public List<TicketDomainEvent> confirmCreate() {
    switch (state) {
      case CREATE_PENDING:
        state = TicketState.AWAITING_ACCEPTANCE;
        return singletonList(new TicketCreatedEvent(id, new TicketDetails()));
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> cancelCreate() {
    throw new NotYetImplementedException();
  }


  public List<TicketDomainEvent> accept(LocalDateTime readyBy) {
    switch (state) {
      case AWAITING_ACCEPTANCE:
        // Verify that readyBy is in the futurestate = TicketState.ACCEPTED;
        this.acceptTime = LocalDateTime.now();
        if (!acceptTime.isBefore(readyBy))
          throw new IllegalArgumentException(String.format("readyBy %s is not after now %s", readyBy, acceptTime));
        this.readyBy = readyBy;
        return singletonList(new TicketAcceptedEvent(readyBy));
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  // TODO reject()

  // TODO cancel()

  public List<TicketDomainEvent> preparing() {
    switch (state) {
      case ACCEPTED:
        this.state = TicketState.PREPARING;
        this.preparingTime = LocalDateTime.now();
        return singletonList(new TicketPreparationStartedEvent());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> readyForPickup() {
    switch (state) {
      case PREPARING:
        this.state = TicketState.READY_FOR_PICKUP;
        this.readyForPickupTime = LocalDateTime.now();
        return singletonList(new TicketPreparationCompletedEvent());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> pickedUp() {
    switch (state) {
      case READY_FOR_PICKUP:
        this.state = TicketState.PICKED_UP;
        this.pickedUpTime = LocalDateTime.now();
        return singletonList(new TicketPickedUpEvent());
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public void changeLineItemQuantity() {
    switch (state) {
      case AWAITING_ACCEPTANCE:
        // TODO
        break;
      case PREPARING:
        // TODO - too late
        break;
      default:
        throw new UnsupportedStateTransitionException(state);
    }

  }

  public List<TicketDomainEvent> cancel() {
    switch (state) {
      case AWAITING_ACCEPTANCE:
      case ACCEPTED:
        this.previousState = state;
        this.state = TicketState.CANCEL_PENDING;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public Long getId() {
    return id;
  }

  public List<TicketDomainEvent> confirmCancel() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = TicketState.CANCELLED;
        return singletonList(new TicketCancelled());
      default:
        throw new UnsupportedStateTransitionException(state);

    }
  }
  public List<TicketDomainEvent> undoCancel() {
    switch (state) {
      case CANCEL_PENDING:
        this.state = this.previousState;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);

    }
  }

  public List<TicketDomainEvent> beginReviseOrder(List<RevisedOrderLineItem> revisedOrderLineItems) {
    switch (state) {
      case AWAITING_ACCEPTANCE:
      case ACCEPTED:
        this.previousState = state;
        this.state = TicketState.REVISION_PENDING;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> undoBeginReviseOrder() {
    switch (state) {
      case REVISION_PENDING:
        this.state = this.previousState;
        return emptyList();
      default:
        throw new UnsupportedStateTransitionException(state);
    }
  }

  public List<TicketDomainEvent> confirmReviseTicket(List<RevisedOrderLineItem> revisedOrderLineItems) {
    switch (state) {
      case REVISION_PENDING:
        this.state = this.previousState;
        return singletonList(new TicketRevised());
      default:
        throw new UnsupportedStateTransitionException(state);

    }
  }
}


package net.chrisrichardson.ftgo.consumerservice.web;

import net.chrisrichardson.ftgo.common.PersonName;

public class CreateConsumerRequest {
  private PersonName name;

  public PersonName getName() {
    return name;
  }

  public void setName(PersonName name) {
    this.name = name;
  }

  public CreateConsumerRequest(PersonName name) {

    this.name = name;
  }

  private CreateConsumerRequest() {
  }


}


package net.chrisrichardson.ftgo.consumerservice.web;

import io.eventuate.tram.events.publisher.ResultWithEvents;
import net.chrisrichardson.ftgo.consumerservice.domain.Consumer;
import net.chrisrichardson.ftgo.consumerservice.domain.ConsumerService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping(path="/consumers")
public class ConsumerController {

  private ConsumerService consumerService;

  public ConsumerController(ConsumerService consumerService) {
    this.consumerService = consumerService;
  }

  @RequestMapping(method= RequestMethod.POST)
  public CreateConsumerResponse create(@RequestBody CreateConsumerRequest request) {
    ResultWithEvents<Consumer> result = consumerService.create(request.getName());
    return new CreateConsumerResponse(result.result.getId());
  }

  @RequestMapping(method= RequestMethod.GET,  path="/{consumerId}")
  public ResponseEntity<GetConsumerResponse> get(@PathVariable long consumerId) {
    return consumerService.findById(consumerId)
            .map(consumer -> new ResponseEntity<>(new GetConsumerResponse(consumer.getName()), HttpStatus.OK))
            .orElseGet(() -> new ResponseEntity<>(HttpStatus.NOT_FOUND));
  }
}


// Node: GetConsumerResponse
package net.chrisrichardson.ftgo.consumerservice.web;

import net.chrisrichardson.ftgo.common.PersonName;

public class GetConsumerResponse extends CreateConsumerResponse {
  private PersonName name;

  public PersonName getName() {
    return name;
  }

  public GetConsumerResponse(PersonName name) {

    this.name = name;
  }
}


package net.chrisrichardson.ftgo.consumerservice.domain;

import io.eventuate.tram.events.publisher.ResultWithEvents;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.common.PersonName;

import javax.persistence.Access;
import javax.persistence.AccessType;
import javax.persistence.Embedded;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.Id;
import javax.persistence.Table;

@Entity
@Table(name = "consumers")
@Access(AccessType.FIELD)
public class Consumer {

  @Id
  @GeneratedValue
  private Long id;

  @Embedded
  private PersonName name;

  private Consumer() {
  }

  public Consumer(PersonName name) {
    this.name = name;
  }


  public void validateOrderByConsumer(Money orderTotal) {
    // implement some business logic
  }

  public Long getId() {
    return id;
  }

  public PersonName getName() {
    return name;
  }

  public static ResultWithEvents<Consumer> create(PersonName name) {
    return new ResultWithEvents<>(new Consumer(name), new ConsumerCreated());
  }
}


