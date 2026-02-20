// Cluster 1

// Node: of
// Node: setOrderId
// Node: getOrderId
// Node: Order
/*
 *    Copyright 2010-2022 the original author or authors.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *       https://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */
package org.mybatis.jpetstore.web.actions;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import javax.servlet.http.HttpSession;

import net.sourceforge.stripes.action.ForwardResolution;
import net.sourceforge.stripes.action.Resolution;
import net.sourceforge.stripes.action.SessionScope;
import net.sourceforge.stripes.integration.spring.SpringBean;

import org.mybatis.jpetstore.domain.Order;
import org.mybatis.jpetstore.service.OrderService;

/**
 * The Class OrderActionBean.
 *
 * @author Eduardo Macarron
 */
@SessionScope
public class OrderActionBean extends AbstractActionBean {

  private static final long serialVersionUID = -6171288227470176272L;

  private static final String CONFIRM_ORDER = "/WEB-INF/jsp/order/ConfirmOrder.jsp";
  private static final String LIST_ORDERS = "/WEB-INF/jsp/order/ListOrders.jsp";
  private static final String NEW_ORDER = "/WEB-INF/jsp/order/NewOrderForm.jsp";
  private static final String SHIPPING = "/WEB-INF/jsp/order/ShippingForm.jsp";
  private static final String VIEW_ORDER = "/WEB-INF/jsp/order/ViewOrder.jsp";

  private static final List<String> CARD_TYPE_LIST;

  @SpringBean
  private transient OrderService orderService;

  private Order order = new Order();
  private boolean shippingAddressRequired;
  private boolean confirmed;
  private List<Order> orderList;

  static {
    CARD_TYPE_LIST = Collections.unmodifiableList(Arrays.asList("Visa", "MasterCard", "American Express"));
  }

  public int getOrderId() {
    return order.getOrderId();
  }

  public void setOrderId(int orderId) {
    order.setOrderId(orderId);
  }

  public Order getOrder() {
    return order;
  }

  public void setOrder(Order order) {
    this.order = order;
  }

  public boolean isShippingAddressRequired() {
    return shippingAddressRequired;
  }

  public void setShippingAddressRequired(boolean shippingAddressRequired) {
    this.shippingAddressRequired = shippingAddressRequired;
  }

  public boolean isConfirmed() {
    return confirmed;
  }

  public void setConfirmed(boolean confirmed) {
    this.confirmed = confirmed;
  }

  public List<String> getCreditCardTypes() {
    return CARD_TYPE_LIST;
  }

  public List<Order> getOrderList() {
    return orderList;
  }

  /**
   * List orders.
   *
   * @return the resolution
   */
  public Resolution listOrders() {
    HttpSession session = context.getRequest().getSession();
    AccountActionBean accountBean = (AccountActionBean) session.getAttribute("/actions/Account.action");
    orderList = orderService.getOrdersByUsername(accountBean.getAccount().getUsername());
    return new ForwardResolution(LIST_ORDERS);
  }

  /**
   * New order form.
   *
   * @return the resolution
   */
  public Resolution newOrderForm() {
    HttpSession session = context.getRequest().getSession();
    AccountActionBean accountBean = (AccountActionBean) session.getAttribute("/actions/Account.action");
    CartActionBean cartBean = (CartActionBean) session.getAttribute("/actions/Cart.action");

    clear();
    if (accountBean == null || !accountBean.isAuthenticated()) {
      setMessage("You must sign on before attempting to check out.  Please sign on and try checking out again.");
      return new ForwardResolution(AccountActionBean.class);
    } else if (cartBean != null) {
      order.initOrder(accountBean.getAccount(), cartBean.getCart());
      return new ForwardResolution(NEW_ORDER);
    } else {
      setMessage("An order could not be created because a cart could not be found.");
      return new ForwardResolution(ERROR);
    }
  }

  /**
   * New order.
   *
   * @return the resolution
   */
  public Resolution newOrder() {
    HttpSession session = context.getRequest().getSession();

    if (shippingAddressRequired) {
      shippingAddressRequired = false;
      return new ForwardResolution(SHIPPING);
    } else if (!isConfirmed()) {
      return new ForwardResolution(CONFIRM_ORDER);
    } else if (getOrder() != null) {

      orderService.insertOrder(order);

      CartActionBean cartBean = (CartActionBean) session.getAttribute("/actions/Cart.action");
      cartBean.clear();

      setMessage("Thank you, your order has been submitted.");

      return new ForwardResolution(VIEW_ORDER);
    } else {
      setMessage("An error occurred processing your order (order was null).");
      return new ForwardResolution(ERROR);
    }
  }

  /**
   * View order.
   *
   * @return the resolution
   */
  public Resolution viewOrder() {
    HttpSession session = context.getRequest().getSession();

    AccountActionBean accountBean = (AccountActionBean) session.getAttribute("accountBean");

    order = orderService.getOrder(order.getOrderId());

    if (accountBean.getAccount().getUsername().equals(order.getUsername())) {
      return new ForwardResolution(VIEW_ORDER);
    } else {
      order = null;
      setMessage("You may only view your own orders.");
      return new ForwardResolution(ERROR);
    }
  }

  /**
   * Clear.
   */
  public void clear() {
    order = new Order();
    shippingAddressRequired = false;
    confirmed = false;
    orderList = null;
  }

}


/*
 *    Copyright 2010-2022 the original author or authors.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *       https://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */
package org.mybatis.jpetstore.domain;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Optional;

/**
 * The Class LineItem.
 *
 * @author Eduardo Macarron
 */
public class LineItem implements Serializable {

  private static final long serialVersionUID = 6804536240033522156L;

  private int orderId;
  private int lineNumber;
  private int quantity;
  private String itemId;
  private BigDecimal unitPrice;
  private Item item;
  private BigDecimal total;

  public LineItem() {
  }

  /**
   * Instantiates a new line item.
   *
   * @param lineNumber
   *          the line number
   * @param cartItem
   *          the cart item
   */
  public LineItem(int lineNumber, CartItem cartItem) {
    this.lineNumber = lineNumber;
    this.quantity = cartItem.getQuantity();
    this.itemId = cartItem.getItem().getItemId();
    this.unitPrice = cartItem.getItem().getListPrice();
    this.item = cartItem.getItem();
    calculateTotal();
  }

  public int getOrderId() {
    return orderId;
  }

  public void setOrderId(int orderId) {
    this.orderId = orderId;
  }

  public int getLineNumber() {
    return lineNumber;
  }

  public void setLineNumber(int lineNumber) {
    this.lineNumber = lineNumber;
  }

  public String getItemId() {
    return itemId;
  }

  public void setItemId(String itemId) {
    this.itemId = itemId;
  }

  public BigDecimal getUnitPrice() {
    return unitPrice;
  }

  public void setUnitPrice(BigDecimal unitprice) {
    this.unitPrice = unitprice;
  }

  public BigDecimal getTotal() {
    return total;
  }

  public Item getItem() {
    return item;
  }

  public void setItem(Item item) {
    this.item = item;
    calculateTotal();
  }

  public int getQuantity() {
    return quantity;
  }

  public void setQuantity(int quantity) {
    this.quantity = quantity;
    calculateTotal();
  }

  private void calculateTotal() {
    total = Optional.ofNullable(item).map(Item::getListPrice).map(v -> v.multiply(new BigDecimal(quantity)))
        .orElse(null);
  }

}


/*
 *    Copyright 2010-2022 the original author or authors.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *       https://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */
package org.mybatis.jpetstore.domain;

import java.io.Serializable;
import java.math.BigDecimal;

/**
 * The Class Item.
 *
 * @author Eduardo Macarron
 */
public class Item implements Serializable {

  private static final long serialVersionUID = -2159121673445254631L;

  private String itemId;
  private String productId;
  private BigDecimal listPrice;
  private BigDecimal unitCost;
  private int supplierId;
  private String status;
  private String attribute1;
  private String attribute2;
  private String attribute3;
  private String attribute4;
  private String attribute5;
  private Product product;
  private int quantity;

  public String getItemId() {
    return itemId;
  }

  public void setItemId(String itemId) {
    this.itemId = itemId.trim();
  }

  public int getQuantity() {
    return quantity;
  }

  public void setQuantity(int quantity) {
    this.quantity = quantity;
  }

  public Product getProduct() {
    return product;
  }

  public void setProduct(Product product) {
    this.product = product;
  }

  public int getSupplierId() {
    return supplierId;
  }

  public void setSupplierId(int supplierId) {
    this.supplierId = supplierId;
  }

  public BigDecimal getListPrice() {
    return listPrice;
  }

  public void setListPrice(BigDecimal listPrice) {
    this.listPrice = listPrice;
  }

  public BigDecimal getUnitCost() {
    return unitCost;
  }

  public void setUnitCost(BigDecimal unitCost) {
    this.unitCost = unitCost;
  }

  public String getStatus() {
    return status;
  }

  public void setStatus(String status) {
    this.status = status;
  }

  public String getAttribute1() {
    return attribute1;
  }

  public void setAttribute1(String attribute1) {
    this.attribute1 = attribute1;
  }

  public String getAttribute2() {
    return attribute2;
  }

  public void setAttribute2(String attribute2) {
    this.attribute2 = attribute2;
  }

  public String getAttribute3() {
    return attribute3;
  }

  public void setAttribute3(String attribute3) {
    this.attribute3 = attribute3;
  }

  public String getAttribute4() {
    return attribute4;
  }

  public void setAttribute4(String attribute4) {
    this.attribute4 = attribute4;
  }

  public String getAttribute5() {
    return attribute5;
  }

  public void setAttribute5(String attribute5) {
    this.attribute5 = attribute5;
  }

  @Override
  public String toString() {
    return "(" + getItemId() + "-" + getProduct().getProductId() + ")";
  }

}


// Node: setStatus
/*
 *    Copyright 2010-2022 the original author or authors.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *       https://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */
package org.mybatis.jpetstore.domain;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.Iterator;
import java.util.List;

/**
 * The Class Order.
 *
 * @author Eduardo Macarron
 */
public class Order implements Serializable {

  private static final long serialVersionUID = 6321792448424424931L;

  private int orderId;
  private String username;
  private Date orderDate;
  private String shipAddress1;
  private String shipAddress2;
  private String shipCity;
  private String shipState;
  private String shipZip;
  private String shipCountry;
  private String billAddress1;
  private String billAddress2;
  private String billCity;
  private String billState;
  private String billZip;
  private String billCountry;
  private String courier;
  private BigDecimal totalPrice;
  private String billToFirstName;
  private String billToLastName;
  private String shipToFirstName;
  private String shipToLastName;
  private String creditCard;
  private String expiryDate;
  private String cardType;
  private String locale;
  private String status;
  private List<LineItem> lineItems = new ArrayList<>();

  public int getOrderId() {
    return orderId;
  }

  public void setOrderId(int orderId) {
    this.orderId = orderId;
  }

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  public Date getOrderDate() {
    return orderDate;
  }

  public void setOrderDate(Date orderDate) {
    this.orderDate = orderDate;
  }

  public String getShipAddress1() {
    return shipAddress1;
  }

  public void setShipAddress1(String shipAddress1) {
    this.shipAddress1 = shipAddress1;
  }

  public String getShipAddress2() {
    return shipAddress2;
  }

  public void setShipAddress2(String shipAddress2) {
    this.shipAddress2 = shipAddress2;
  }

  public String getShipCity() {
    return shipCity;
  }

  public void setShipCity(String shipCity) {
    this.shipCity = shipCity;
  }

  public String getShipState() {
    return shipState;
  }

  public void setShipState(String shipState) {
    this.shipState = shipState;
  }

  public String getShipZip() {
    return shipZip;
  }

  public void setShipZip(String shipZip) {
    this.shipZip = shipZip;
  }

  public String getShipCountry() {
    return shipCountry;
  }

  public void setShipCountry(String shipCountry) {
    this.shipCountry = shipCountry;
  }

  public String getBillAddress1() {
    return billAddress1;
  }

  public void setBillAddress1(String billAddress1) {
    this.billAddress1 = billAddress1;
  }

  public String getBillAddress2() {
    return billAddress2;
  }

  public void setBillAddress2(String billAddress2) {
    this.billAddress2 = billAddress2;
  }

  public String getBillCity() {
    return billCity;
  }

  public void setBillCity(String billCity) {
    this.billCity = billCity;
  }

  public String getBillState() {
    return billState;
  }

  public void setBillState(String billState) {
    this.billState = billState;
  }

  public String getBillZip() {
    return billZip;
  }

  public void setBillZip(String billZip) {
    this.billZip = billZip;
  }

  public String getBillCountry() {
    return billCountry;
  }

  public void setBillCountry(String billCountry) {
    this.billCountry = billCountry;
  }

  public String getCourier() {
    return courier;
  }

  public void setCourier(String courier) {
    this.courier = courier;
  }

  public BigDecimal getTotalPrice() {
    return totalPrice;
  }

  public void setTotalPrice(BigDecimal totalPrice) {
    this.totalPrice = totalPrice;
  }

  public String getBillToFirstName() {
    return billToFirstName;
  }

  public void setBillToFirstName(String billToFirstName) {
    this.billToFirstName = billToFirstName;
  }

  public String getBillToLastName() {
    return billToLastName;
  }

  public void setBillToLastName(String billToLastName) {
    this.billToLastName = billToLastName;
  }

  public String getShipToFirstName() {
    return shipToFirstName;
  }

  public void setShipToFirstName(String shipFoFirstName) {
    this.shipToFirstName = shipFoFirstName;
  }

  public String getShipToLastName() {
    return shipToLastName;
  }

  public void setShipToLastName(String shipToLastName) {
    this.shipToLastName = shipToLastName;
  }

  public String getCreditCard() {
    return creditCard;
  }

  public void setCreditCard(String creditCard) {
    this.creditCard = creditCard;
  }

  public String getExpiryDate() {
    return expiryDate;
  }

  public void setExpiryDate(String expiryDate) {
    this.expiryDate = expiryDate;
  }

  public String getCardType() {
    return cardType;
  }

  public void setCardType(String cardType) {
    this.cardType = cardType;
  }

  public String getLocale() {
    return locale;
  }

  public void setLocale(String locale) {
    this.locale = locale;
  }

  public String getStatus() {
    return status;
  }

  public void setStatus(String status) {
    this.status = status;
  }

  public void setLineItems(List<LineItem> lineItems) {
    this.lineItems = lineItems;
  }

  public List<LineItem> getLineItems() {
    return lineItems;
  }

  /**
   * Inits the order.
   *
   * @param account
   *          the account
   * @param cart
   *          the cart
   */
  public void initOrder(Account account, Cart cart) {

    username = account.getUsername();
    orderDate = new Date();

    shipToFirstName = account.getFirstName();
    shipToLastName = account.getLastName();
    shipAddress1 = account.getAddress1();
    shipAddress2 = account.getAddress2();
    shipCity = account.getCity();
    shipState = account.getState();
    shipZip = account.getZip();
    shipCountry = account.getCountry();

    billToFirstName = account.getFirstName();
    billToLastName = account.getLastName();
    billAddress1 = account.getAddress1();
    billAddress2 = account.getAddress2();
    billCity = account.getCity();
    billState = account.getState();
    billZip = account.getZip();
    billCountry = account.getCountry();

    totalPrice = cart.getSubTotal();

    creditCard = "999 9999 9999 9999";
    expiryDate = "12/03";
    cardType = "Visa";
    courier = "UPS";
    locale = "CA";
    status = "P";

    Iterator<CartItem> i = cart.getAllCartItems();
    while (i.hasNext()) {
      CartItem cartItem = i.next();
      addLineItem(cartItem);
    }

  }

  public void addLineItem(CartItem cartItem) {
    LineItem lineItem = new LineItem(lineItems.size() + 1, cartItem);
    addLineItem(lineItem);
  }

  public void addLineItem(LineItem lineItem) {
    lineItems.add(lineItem);
  }

}


// Node: getOrderDate
// Node: setOrderDate
// Node: getShipAddress1
// Node: setShipAddress1
// Node: getShipAddress2
// Node: setShipAddress2
// Node: getShipCity
// Node: setShipCity
// Node: getShipState
// Node: setShipState
// Node: getShipZip
// Node: setShipZip
// Node: getShipCountry
// Node: setShipCountry
// Node: getBillAddress1
// Node: setBillAddress1
// Node: getBillAddress2
// Node: setBillAddress2
// Node: getBillCity
// Node: setBillCity
// Node: getBillState
// Node: setBillState
// Node: getBillZip
// Node: setBillZip
// Node: getBillCountry
// Node: setBillCountry
// Node: getCourier
// Node: setCourier
// Node: getTotalPrice
// Node: setTotalPrice
// Node: getBillToFirstName
// Node: setBillToFirstName
// Node: getBillToLastName
// Node: setBillToLastName
// Node: getShipToFirstName
// Node: setShipToFirstName
// Node: getShipToLastName
// Node: setShipToLastName
// Node: getCreditCard
// Node: setCreditCard
// Node: getExpiryDate
// Node: setExpiryDate
// Node: getCardType
// Node: setCardType
// Node: getLocale
// Node: setLocale
/*
 *    Copyright 2010-2022 the original author or authors.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *       https://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */
package org.mybatis.jpetstore.domain;

import java.io.Serializable;

import net.sourceforge.stripes.validation.Validate;

/**
 * The Class Account.
 *
 * @author Eduardo Macarron
 */
public class Account implements Serializable {

  private static final long serialVersionUID = 8751282105532159742L;

  private String username;
  private String password;
  private String email;
  private String firstName;
  private String lastName;
  private String status;
  private String address1;
  private String address2;
  private String city;
  private String state;
  private String zip;
  private String country;
  private String phone;
  private String favouriteCategoryId;
  private String languagePreference;
  private boolean listOption;
  private boolean bannerOption;
  private String bannerName;

  public String getUsername() {
    return username;
  }

  public void setUsername(String username) {
    this.username = username;
  }

  public String getPassword() {
    return password;
  }

  public void setPassword(String password) {
    this.password = password;
  }

  public String getEmail() {
    return email;
  }

  public void setEmail(String email) {
    this.email = email;
  }

  public String getFirstName() {
    return firstName;
  }

  @Validate(required = true, on = { "newAccount", "editAccount" })
  public void setFirstName(String firstName) {
    this.firstName = firstName;
  }

  public String getLastName() {
    return lastName;
  }

  @Validate(required = true, on = { "newAccount", "editAccount" })
  public void setLastName(String lastName) {
    this.lastName = lastName;
  }

  public String getStatus() {
    return status;
  }

  public void setStatus(String status) {
    this.status = status;
  }

  public String getAddress1() {
    return address1;
  }

  public void setAddress1(String address1) {
    this.address1 = address1;
  }

  public String getAddress2() {
    return address2;
  }

  public void setAddress2(String address2) {
    this.address2 = address2;
  }

  public String getCity() {
    return city;
  }

  public void setCity(String city) {
    this.city = city;
  }

  public String getState() {
    return state;
  }

  public void setState(String state) {
    this.state = state;
  }

  public String getZip() {
    return zip;
  }

  public void setZip(String zip) {
    this.zip = zip;
  }

  public String getCountry() {
    return country;
  }

  public void setCountry(String country) {
    this.country = country;
  }

  public String getPhone() {
    return phone;
  }

  public void setPhone(String phone) {
    this.phone = phone;
  }

  public String getFavouriteCategoryId() {
    return favouriteCategoryId;
  }

  public void setFavouriteCategoryId(String favouriteCategoryId) {
    this.favouriteCategoryId = favouriteCategoryId;
  }

  public String getLanguagePreference() {
    return languagePreference;
  }

  public void setLanguagePreference(String languagePreference) {
    this.languagePreference = languagePreference;
  }

  public boolean isListOption() {
    return listOption;
  }

  public void setListOption(boolean listOption) {
    this.listOption = listOption;
  }

  public boolean isBannerOption() {
    return bannerOption;
  }

  public void setBannerOption(boolean bannerOption) {
    this.bannerOption = bannerOption;
  }

  public String getBannerName() {
    return bannerName;
  }

  public void setBannerName(String bannerName) {
    this.bannerName = bannerName;
  }

}


// Node: valueOf
/*
 *    Copyright 2010-2022 the original author or authors.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *       https://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */
package org.mybatis.jpetstore.mapper;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mybatis.jpetstore.domain.Order;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = MapperTestContext.class)
@Transactional
class OrderMapperTest {

  @Autowired
  private OrderMapper mapper;

  @Autowired
  private JdbcTemplate jdbcTemplate;

  @Test
  void insertOrder() {
    // given
    Order order = new Order();
    order.setOrderId(1);
    order.setOrderDate(java.sql.Timestamp.valueOf(LocalDateTime.of(2018, 12, 31, 23, 59, 59)));
    order.setUsername("j2ee");
    order.setCardType("Visa");
    order.setCreditCard("1234 5678 9012 3456");
    order.setExpiryDate("06/2022");
    order.setCourier("Courier");
    order.setLocale("ja");
    order.setTotalPrice(new BigDecimal("2000.05"));
    order.setBillAddress1("Bill Address1");
    order.setBillAddress2("Bill Address2");
    order.setBillCity("Bill City");
    order.setBillState("Bill State");
    order.setBillCountry("USA");
    order.setBillZip("80001");
    order.setBillToFirstName("Bill First Name");
    order.setBillToLastName("Bill Last Name");
    order.setShipAddress1("Ship Address1");
    order.setShipAddress2("Ship Address2");
    order.setShipCity("Ship City");
    order.setShipState("Ship State");
    order.setShipCountry("JPN");
    order.setShipZip("70001");
    order.setShipToFirstName("Ship First Name");
    order.setShipToLastName("Ship Last Name");

    // when
    mapper.insertOrder(order);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM orders WHERE orderid = ?", 1);
    assertThat(record).hasSize(25).containsEntry("ORDERID", order.getOrderId())
        .containsEntry("USERID", order.getUsername())
        .containsEntry("ORDERDATE", java.sql.Date.valueOf(LocalDate.of(2018, 12, 31)))
        .containsEntry("SHIPADDR1", order.getShipAddress1()).containsEntry("SHIPADDR2", order.getShipAddress2())
        .containsEntry("SHIPCITY", order.getShipCity()).containsEntry("SHIPSTATE", order.getShipState())
        .containsEntry("SHIPZIP", order.getShipZip()).containsEntry("SHIPCOUNTRY", order.getShipCountry())
        .containsEntry("SHIPTOFIRSTNAME", order.getShipToFirstName())
        .containsEntry("SHIPTOLASTNAME", order.getShipToLastName()).containsEntry("BILLADDR1", order.getBillAddress1())
        .containsEntry("BILLADDR2", order.getBillAddress2()).containsEntry("BILLCITY", order.getBillCity())
        .containsEntry("BILLSTATE", order.getBillState()).containsEntry("BILLZIP", order.getBillZip())
        .containsEntry("BILLCOUNTRY", order.getBillCountry())
        .containsEntry("BILLTOFIRSTNAME", order.getBillToFirstName())
        .containsEntry("BILLTOLASTNAME", order.getBillToLastName()).containsEntry("COURIER", order.getCourier())
        .containsEntry("TOTALPRICE", order.getTotalPrice()).containsEntry("CREDITCARD", order.getCreditCard())
        .containsEntry("EXPRDATE", order.getExpiryDate()).containsEntry("CARDTYPE", order.getCardType())
        .containsEntry("LOCALE", order.getLocale());

  }

  @Test
  void insertOrderStatus() {
    // given
    Order order = new Order();
    order.setOrderId(1);
    order.setOrderDate(java.sql.Timestamp.valueOf(LocalDateTime.of(2018, 12, 31, 23, 59, 59)));
    order.setStatus("OK");

    // when
    mapper.insertOrderStatus(order);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM orderstatus WHERE orderid = ?", 1);
    assertThat(record).hasSize(4).containsEntry("ORDERID", order.getOrderId())
        .containsEntry("LINENUM", order.getOrderId())
        .containsEntry("TIMESTAMP", java.sql.Date.valueOf(LocalDate.of(2018, 12, 31)))
        .containsEntry("STATUS", order.getStatus());

  }

  @Test
  void getOrdersByUsername() {
    // given
    Order newOrder = new Order();
    newOrder.setOrderId(1);
    newOrder.setOrderDate(java.sql.Timestamp.valueOf(LocalDateTime.of(2018, 12, 31, 23, 59, 59)));
    newOrder.setStatus("OK");
    newOrder.setUsername("j2ee");
    newOrder.setCardType("Visa");
    newOrder.setCreditCard("1234 5678 9012 3456");
    newOrder.setExpiryDate("06/2022");
    newOrder.setCourier("Courier");
    newOrder.setLocale("ja");
    newOrder.setTotalPrice(new BigDecimal("2000.05"));
    newOrder.setBillAddress1("Bill Address1");
    newOrder.setBillAddress2("Bill Address2");
    newOrder.setBillCity("Bill City");
    newOrder.setBillState("Bill State");
    newOrder.setBillCountry("USA");
    newOrder.setBillZip("80001");
    newOrder.setBillToFirstName("Bill First Name");
    newOrder.setBillToLastName("Bill Last Name");
    newOrder.setShipAddress1("Ship Address1");
    newOrder.setShipAddress2("Ship Address2");
    newOrder.setShipCity("Ship City");
    newOrder.setShipState("Ship State");
    newOrder.setShipCountry("JPN");
    newOrder.setShipZip("70001");
    newOrder.setShipToFirstName("Ship First Name");
    newOrder.setShipToLastName("Ship Last Name");
    mapper.insertOrder(newOrder);
    mapper.insertOrderStatus(newOrder);

    // when
    List<Order> orders = mapper.getOrdersByUsername("j2ee");

    // then
    assertThat(orders).hasSize(1);
    assertThat(orders.get(0).getOrderId()).isEqualTo(newOrder.getOrderId());
    assertThat(orders.get(0).getOrderDate()).isEqualTo(java.sql.Date.valueOf(LocalDate.of(2018, 12, 31)));
    assertThat(orders.get(0).getCardType()).isEqualTo(newOrder.getCardType());
    assertThat(orders.get(0).getCreditCard()).isEqualTo(newOrder.getCreditCard());
    assertThat(orders.get(0).getExpiryDate()).isEqualTo(newOrder.getExpiryDate());
    assertThat(orders.get(0).getCourier()).isEqualTo(newOrder.getCourier());
    assertThat(orders.get(0).getLocale()).isEqualTo(newOrder.getLocale());
    assertThat(orders.get(0).getTotalPrice()).isEqualTo(newOrder.getTotalPrice());
    assertThat(orders.get(0).getBillAddress1()).isEqualTo(newOrder.getBillAddress1());
    assertThat(orders.get(0).getBillAddress2()).isEqualTo(newOrder.getBillAddress2());
    assertThat(orders.get(0).getBillCity()).isEqualTo(newOrder.getBillCity());
    assertThat(orders.get(0).getBillState()).isEqualTo(newOrder.getBillState());
    assertThat(orders.get(0).getBillCountry()).isEqualTo(newOrder.getBillCountry());
    assertThat(orders.get(0).getBillZip()).isEqualTo(newOrder.getBillZip());
    assertThat(orders.get(0).getBillToFirstName()).isEqualTo(newOrder.getBillToFirstName());
    assertThat(orders.get(0).getBillToLastName()).isEqualTo(newOrder.getBillToLastName());
    assertThat(orders.get(0).getShipAddress1()).isEqualTo(newOrder.getShipAddress1());
    assertThat(orders.get(0).getShipAddress2()).isEqualTo(newOrder.getShipAddress2());
    assertThat(orders.get(0).getShipCity()).isEqualTo(newOrder.getShipCity());
    assertThat(orders.get(0).getShipState()).isEqualTo(newOrder.getShipState());
    assertThat(orders.get(0).getShipCountry()).isEqualTo(newOrder.getShipCountry());
    assertThat(orders.get(0).getShipZip()).isEqualTo(newOrder.getShipZip());
    assertThat(orders.get(0).getShipToFirstName()).isEqualTo(newOrder.getShipToFirstName());
    assertThat(orders.get(0).getShipToLastName()).isEqualTo(newOrder.getShipToLastName());
  }

  @Test
  void getOrder() {
    // given
    Order newOrder = new Order();
    newOrder.setOrderId(1);
    newOrder.setOrderDate(java.sql.Timestamp.valueOf(LocalDateTime.of(2018, 12, 31, 23, 59, 59)));
    newOrder.setStatus("OK");
    newOrder.setUsername("j2ee");
    newOrder.setCardType("Visa");
    newOrder.setCreditCard("1234 5678 9012 3456");
    newOrder.setExpiryDate("06/2022");
    newOrder.setCourier("Courier");
    newOrder.setLocale("ja");
    newOrder.setTotalPrice(new BigDecimal("2000.05"));
    newOrder.setBillAddress1("Bill Address1");
    newOrder.setBillAddress2("Bill Address2");
    newOrder.setBillCity("Bill City");
    newOrder.setBillState("Bill State");
    newOrder.setBillCountry("USA");
    newOrder.setBillZip("80001");
    newOrder.setBillToFirstName("Bill First Name");
    newOrder.setBillToLastName("Bill Last Name");
    newOrder.setShipAddress1("Ship Address1");
    newOrder.setShipAddress2("Ship Address2");
    newOrder.setShipCity("Ship City");
    newOrder.setShipState("Ship State");
    newOrder.setShipCountry("JPN");
    newOrder.setShipZip("70001");
    newOrder.setShipToFirstName("Ship First Name");
    newOrder.setShipToLastName("Ship Last Name");
    mapper.insertOrder(newOrder);
    mapper.insertOrderStatus(newOrder);

    // when
    Order order = mapper.getOrder(1);

    // then
    assertThat(order.getOrderId()).isEqualTo(newOrder.getOrderId());
    assertThat(order.getOrderDate()).isEqualTo(java.sql.Date.valueOf(LocalDate.of(2018, 12, 31)));
    assertThat(order.getCardType()).isEqualTo(newOrder.getCardType());
    assertThat(order.getCreditCard()).isEqualTo(newOrder.getCreditCard());
    assertThat(order.getExpiryDate()).isEqualTo(newOrder.getExpiryDate());
    assertThat(order.getCourier()).isEqualTo(newOrder.getCourier());
    assertThat(order.getLocale()).isEqualTo(newOrder.getLocale());
    assertThat(order.getTotalPrice()).isEqualTo(newOrder.getTotalPrice());
    assertThat(order.getBillAddress1()).isEqualTo(newOrder.getBillAddress1());
    assertThat(order.getBillAddress2()).isEqualTo(newOrder.getBillAddress2());
    assertThat(order.getBillCity()).isEqualTo(newOrder.getBillCity());
    assertThat(order.getBillState()).isEqualTo(newOrder.getBillState());
    assertThat(order.getBillCountry()).isEqualTo(newOrder.getBillCountry());
    assertThat(order.getBillZip()).isEqualTo(newOrder.getBillZip());
    assertThat(order.getBillToFirstName()).isEqualTo(newOrder.getBillToFirstName());
    assertThat(order.getBillToLastName()).isEqualTo(newOrder.getBillToLastName());
    assertThat(order.getShipAddress1()).isEqualTo(newOrder.getShipAddress1());
    assertThat(order.getShipAddress2()).isEqualTo(newOrder.getShipAddress2());
    assertThat(order.getShipCity()).isEqualTo(newOrder.getShipCity());
    assertThat(order.getShipState()).isEqualTo(newOrder.getShipState());
    assertThat(order.getShipCountry()).isEqualTo(newOrder.getShipCountry());
    assertThat(order.getShipZip()).isEqualTo(newOrder.getShipZip());
    assertThat(order.getShipToFirstName()).isEqualTo(newOrder.getShipToFirstName());
    assertThat(order.getShipToLastName()).isEqualTo(newOrder.getShipToLastName());
  }

}


