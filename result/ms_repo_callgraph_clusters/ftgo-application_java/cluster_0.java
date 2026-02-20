// Cluster 0

package net.chrisrichardson.ftgo.testutil.jsonschema;

import io.eventuate.common.json.mapper.JSonMapper;
import org.apache.commons.lang.StringUtils;
import org.everit.json.schema.Schema;
import org.everit.json.schema.ValidationException;
import org.everit.json.schema.loader.SchemaClient;
import org.everit.json.schema.loader.SchemaLoader;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;
import org.junit.Assert;

import java.io.IOException;
import java.io.InputStream;

import static org.junit.Assert.fail;

public class ValidatingJSONMapper {

  private Schema schema;

  public ValidatingJSONMapper(Schema schema) {
    this.schema = schema;
  }

  public static ValidatingJSONMapper forSchema(String schemaPath) {
    Schema schema;
    try (InputStream inputStream = ValidatingJSONMapper.class.getResourceAsStream(schemaPath)) {
      if (inputStream == null)
        fail("Can't find schema: " + schemaPath);
      JSONObject rawSchema = new JSONObject(new JSONTokener(inputStream));
      schema = SchemaLoader.load(rawSchema, new SchemaClient() {
        @Override
        public InputStream get(String url) {
          String path = StringUtils.substringBeforeLast(schemaPath, "/") + "/" + url;
          InputStream is = ValidatingJSONMapper.class.getResourceAsStream(path);
          Assert.assertNotNull(path, is);
          return is;
        }
      });
    } catch (IOException | JSONException e) {
      throw new RuntimeException(e);
    }
    return new ValidatingJSONMapper(schema);
  }

  public void validate(JSONObject jsonObject) {
    try {
      schema.validate(jsonObject);
    } catch (ValidationException e) {
      e.getErrorMessage();
      fail("Schema validation failed: " + String.join(",", e.getAllMessages()));
    }

  }
  public void validate(String jsonObject) {
    JSONObject jo = new JSONObject(new JSONTokener(jsonObject));
    validate(jo);
  }

  public <T> T fromJSON(JSONObject jsonObject, Class<T> clasz) {
    validate(jsonObject);
    return JSonMapper.fromJson(jsonObject.toString(), clasz);
  }

  public String toJSON(Object object) {
    String json = JSonMapper.toJson(object);
    validate(json);
    return json;
  }
}


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-test-util-json-schema/src/main/java/net/chrisrichardson/ftgo/testutil/jsonschema/ValidatingJSONMapper.java:ValidatingJSONMapper.<init>
// Node: ValidatingJSONMapper
// Node: forSchema
// Node: try
// Node: getResourceAsStream
// Node: fail
// Node: JSONObject
// Node: JSONTokener
// Node: substringBeforeLast
// Node: validate
// Node: getErrorMessage
// Node: join
// Node: getAllMessages
// Node: fromJSON
// Node: fromJson
// Node: toJSON
// Node: toJson
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


// Node: deltaForChangedQuantity
// Node: multiply
// Node: getTotal
// Node: Money
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


// Node: repos/cloned_ms_repos/ftgo-application/ftgo-common/src/main/java/net/chrisrichardson/ftgo/common/Money.java:Money.<init>
// Node: BigDecimal
// Node: asLong
// Node: longValue
package net.chrisrichardson.ftgo.common;


import org.junit.Test;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class MoneyTest {

  private final int M1_AMOUNT = 10;
  private final int M2_AMOUNT = 15;

  private Money m1 = new Money(M1_AMOUNT);
  private Money m2 = new Money(M2_AMOUNT);

  @Test
  public void shouldReturnAsString() {
    assertEquals(Integer.toString(M1_AMOUNT), new Money(M1_AMOUNT).asString());
  }

  @Test
  public void shouldCompare() {
    assertTrue(m2.isGreaterThanOrEqual(m2));
    assertTrue(m2.isGreaterThanOrEqual(m1));
    assertFalse(m1.isGreaterThanOrEqual(m2));
  }

  @Test
  public void shouldAdd() {
    assertEquals(new Money(M1_AMOUNT + M2_AMOUNT), m1.add(m2));
  }

  @Test
  public void shouldMultiply() {
    int multiplier = 12;
    assertEquals(new Money(M2_AMOUNT * multiplier), m2.multiply(multiplier));
  }



}

// Node: repos/cloned_ms_repos/ftgo-application/ftgo-common/src/test/java/net/chrisrichardson/ftgo/common/MoneyTest.java:MoneyTest.<init>
// Node: shouldReturnAsString
// Node: shouldAdd
// Node: shouldMultiply
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

// Node: MoneyContainer
// Node: shouldSer
// Node: shouldDe
// Node: shouldFailToDe
// Node: getCause
package net.chrisrichardson.ftgo.orderservice.domain;

import io.eventuate.tram.events.aggregates.ResultWithDomainEvents;
import net.chrisrichardson.ftgo.common.RevisedOrderLineItem;
import net.chrisrichardson.ftgo.orderservice.OrderDetailsMother;
import net.chrisrichardson.ftgo.orderservice.RestaurantMother;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderAuthorized;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderCreatedEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderDomainEvent;
import net.chrisrichardson.ftgo.orderservice.api.events.OrderState;
import org.junit.Before;
import org.junit.Test;

import java.util.Collections;
import java.util.List;
import java.util.Optional;

import static java.util.Collections.singletonList;
import static net.chrisrichardson.ftgo.orderservice.OrderDetailsMother.*;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.AJANTA_RESTAURANT;
import static net.chrisrichardson.ftgo.orderservice.RestaurantMother.CHICKEN_VINDALOO_PRICE;
import static org.junit.Assert.assertEquals;

public class OrderTest {

  private ResultWithDomainEvents<Order, OrderDomainEvent> createResult;
  private Order order;

  @Before
  public void setUp() throws Exception {
    createResult = Order.createOrder(CONSUMER_ID, AJANTA_RESTAURANT, OrderDetailsMother.DELIVERY_INFORMATION, chickenVindalooLineItems());
    order = createResult.result;
  }

  @Test
  public void shouldCreateOrder() {
    assertEquals(singletonList(new OrderCreatedEvent(CHICKEN_VINDALOO_ORDER_DETAILS, OrderDetailsMother.DELIVERY_ADDRESS, RestaurantMother.AJANTA_RESTAURANT_NAME)), createResult.events);

    assertEquals(OrderState.APPROVAL_PENDING, order.getState());
    // ...
  }

  @Test
  public void shouldCalculateTotal() {
    assertEquals(CHICKEN_VINDALOO_PRICE.multiply(CHICKEN_VINDALOO_QUANTITY), order.getOrderTotal());
  }

  @Test
  public void shouldAuthorize() {
    List<OrderDomainEvent> events = order.noteApproved();
    assertEquals(singletonList(new OrderAuthorized()), events);
    assertEquals(OrderState.APPROVED, order.getState());
  }

  @Test
  public void shouldReviseOrder() {

    order.noteApproved();

    OrderRevision orderRevision = new OrderRevision(Optional.empty(), Collections.singletonList(new RevisedOrderLineItem(10, "1")));

    ResultWithDomainEvents<LineItemQuantityChange, OrderDomainEvent> result = order.revise(orderRevision);

    assertEquals(CHICKEN_VINDALOO_PRICE.multiply(10), result.result.getNewOrderTotal());

    order.confirmRevision(orderRevision);

    assertEquals(CHICKEN_VINDALOO_PRICE.multiply(10), order.getOrderTotal());
  }
}

// Node: shouldCalculateTotal
package net.chrisrichardson.ftgo.consumerservice.api;

import net.chrisrichardson.ftgo.common.CommonJsonMapperInitializer;
import net.chrisrichardson.ftgo.common.Money;
import net.chrisrichardson.ftgo.testutil.jsonschema.ValidatingJSONMapper;
import org.json.JSONObject;
import org.junit.Test;

import static org.junit.Assert.assertEquals;

public class ValidateOrderByConsumerTest {

  static {
    CommonJsonMapperInitializer.registerMoneyModule();
  }

  @Test
  public void shouldDeserialize() {

    ValidatingJSONMapper mapper = ValidatingJSONMapper.forSchema("/ValidateOrderByConsumer.json");

    JSONObject jsonObject = new JSONObject().put("consumerId", 1).put("orderId", 2).put("orderTotal", "12.34");

    ValidateOrderByConsumer cmd = mapper.fromJSON(jsonObject, ValidateOrderByConsumer.class);

    assertEquals(1, cmd.getConsumerId());
    assertEquals(2, cmd.getOrderId());
    assertEquals(new Money("12.34"), cmd.getOrderTotal());
  }


}

// Node: shouldDeserialize
