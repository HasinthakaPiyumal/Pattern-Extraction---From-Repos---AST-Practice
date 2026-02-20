// Cluster 10

// Node: getPassword
// Node: Account
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

import net.sourceforge.stripes.action.DefaultHandler;
import net.sourceforge.stripes.action.ForwardResolution;
import net.sourceforge.stripes.action.RedirectResolution;
import net.sourceforge.stripes.action.Resolution;
import net.sourceforge.stripes.action.SessionScope;
import net.sourceforge.stripes.integration.spring.SpringBean;
import net.sourceforge.stripes.validation.Validate;

import org.mybatis.jpetstore.domain.Account;
import org.mybatis.jpetstore.domain.Product;
import org.mybatis.jpetstore.service.AccountService;
import org.mybatis.jpetstore.service.CatalogService;

/**
 * The Class AccountActionBean.
 *
 * @author Eduardo Macarron
 */
@SessionScope
public class AccountActionBean extends AbstractActionBean {

  private static final long serialVersionUID = 5499663666155758178L;

  private static final String NEW_ACCOUNT = "/WEB-INF/jsp/account/NewAccountForm.jsp";
  private static final String EDIT_ACCOUNT = "/WEB-INF/jsp/account/EditAccountForm.jsp";
  private static final String SIGNON = "/WEB-INF/jsp/account/SignonForm.jsp";

  private static final List<String> LANGUAGE_LIST;
  private static final List<String> CATEGORY_LIST;

  @SpringBean
  private transient AccountService accountService;
  @SpringBean
  private transient CatalogService catalogService;

  private Account account = new Account();
  private List<Product> myList;
  private boolean authenticated;

  static {
    LANGUAGE_LIST = Collections.unmodifiableList(Arrays.asList("english", "japanese"));
    CATEGORY_LIST = Collections.unmodifiableList(Arrays.asList("FISH", "DOGS", "REPTILES", "CATS", "BIRDS"));
  }

  public Account getAccount() {
    return this.account;
  }

  public String getUsername() {
    return account.getUsername();
  }

  @Validate(required = true, on = { "signon", "newAccount", "editAccount" })
  public void setUsername(String username) {
    account.setUsername(username);
  }

  public String getPassword() {
    return account.getPassword();
  }

  @Validate(required = true, on = { "signon", "newAccount", "editAccount" })
  public void setPassword(String password) {
    account.setPassword(password);
  }

  public List<Product> getMyList() {
    return myList;
  }

  public void setMyList(List<Product> myList) {
    this.myList = myList;
  }

  public List<String> getLanguages() {
    return LANGUAGE_LIST;
  }

  public List<String> getCategories() {
    return CATEGORY_LIST;
  }

  public Resolution newAccountForm() {
    return new ForwardResolution(NEW_ACCOUNT);
  }

  /**
   * New account.
   *
   * @return the resolution
   */
  public Resolution newAccount() {
    accountService.insertAccount(account);
    account = accountService.getAccount(account.getUsername());
    myList = catalogService.getProductListByCategory(account.getFavouriteCategoryId());
    authenticated = true;
    return new RedirectResolution(CatalogActionBean.class);
  }

  /**
   * Edits the account form.
   *
   * @return the resolution
   */
  public Resolution editAccountForm() {
    return new ForwardResolution(EDIT_ACCOUNT);
  }

  /**
   * Edits the account.
   *
   * @return the resolution
   */
  public Resolution editAccount() {
    accountService.updateAccount(account);
    account = accountService.getAccount(account.getUsername());
    myList = catalogService.getProductListByCategory(account.getFavouriteCategoryId());
    return new RedirectResolution(CatalogActionBean.class);
  }

  /**
   * Signon form.
   *
   * @return the resolution
   */
  @DefaultHandler
  public Resolution signonForm() {
    return new ForwardResolution(SIGNON);
  }

  /**
   * Signon.
   *
   * @return the resolution
   */
  public Resolution signon() {

    account = accountService.getAccount(getUsername(), getPassword());

    if (account == null) {
      String value = "Invalid username or password.  Signon failed.";
      setMessage(value);
      clear();
      return new ForwardResolution(SIGNON);
    } else {
      account.setPassword(null);
      myList = catalogService.getProductListByCategory(account.getFavouriteCategoryId());
      authenticated = true;
      HttpSession s = context.getRequest().getSession();
      // this bean is already registered as /actions/Account.action
      s.setAttribute("accountBean", this);
      return new RedirectResolution(CatalogActionBean.class);
    }
  }

  /**
   * Signoff.
   *
   * @return the resolution
   */
  public Resolution signoff() {
    context.getRequest().getSession().invalidate();
    clear();
    return new RedirectResolution(CatalogActionBean.class);
  }

  /**
   * Checks if is authenticated.
   *
   * @return true, if is authenticated
   */
  public boolean isAuthenticated() {
    return authenticated && account != null && account.getUsername() != null;
  }

  /**
   * Clear.
   */
  public void clear() {
    account = new Account();
    myList = null;
    authenticated = false;
  }

}


// Node: getUsername
// Node: Validate
// Node: setUsername
// Node: getFavouriteCategoryId
// Node: initOrder
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


// Node: getUnitPrice
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


// Node: getStatus
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


// Node: Date
// Node: getFirstName
// Node: getLastName
// Node: getAddress1
// Node: getAddress2
// Node: getCity
// Node: getState
// Node: getZip
// Node: getCountry
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


// Node: getEmail
// Node: setEmail
// Node: setFirstName
// Node: setLastName
// Node: setAddress1
// Node: setAddress2
// Node: setCity
// Node: setState
// Node: setZip
// Node: setCountry
// Node: getPhone
// Node: setPhone
// Node: setFavouriteCategoryId
// Node: getLanguagePreference
// Node: setLanguagePreference
// Node: isListOption
// Node: setListOption
// Node: isBannerOption
// Node: setBannerOption
// Node: getBannerName
// Node: queryForMap
// Node: hasSize
// Node: containsEntry
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

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mybatis.jpetstore.domain.Account;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = MapperTestContext.class)
@Transactional
class AccountMapperTest {

  @Autowired
  private AccountMapper mapper;

  @Autowired
  private JdbcTemplate jdbcTemplate;

  @Test
  void getAccountByUsername() {
    // given
    String username = "j2ee";

    // when
    Account account = mapper.getAccountByUsername(username);

    // then
    assertThat(account.getUsername()).isEqualTo("j2ee");
    assertThat(account.getEmail()).isEqualTo("yourname@yourdomain.com");
    assertThat(account.getFirstName()).isEqualTo("ABC");
    assertThat(account.getLastName()).isEqualTo("XYX");
    assertThat(account.getStatus()).isEqualTo("OK");
    assertThat(account.getAddress1()).isEqualTo("901 San Antonio Road");
    assertThat(account.getAddress2()).isEqualTo("MS UCUP02-206");
    assertThat(account.getCity()).isEqualTo("Palo Alto");
    assertThat(account.getState()).isEqualTo("CA");
    assertThat(account.getZip()).isEqualTo("94303");
    assertThat(account.getCountry()).isEqualTo("USA");
    assertThat(account.getPhone()).isEqualTo("555-555-5555");
    assertThat(account.getLanguagePreference()).isEqualTo("english");
    assertThat(account.getFavouriteCategoryId()).isEqualTo("DOGS");
    assertThat(account.isListOption()).isTrue();
    assertThat(account.isBannerOption()).isTrue();
    assertThat(account.getBannerName()).isEqualTo("<image src=\"../images/banner_dogs.gif\">");

  }

  @Test
  void getAccountByUsernameAndPassword() {
    // given
    String username = "ACID";
    String password = "ACID";

    // when
    Account account = mapper.getAccountByUsernameAndPassword(username, password);

    // then
    assertThat(account.getUsername()).isEqualTo("ACID");
    assertThat(account.getEmail()).isEqualTo("acid@yourdomain.com");
    assertThat(account.getFirstName()).isEqualTo("ABC");
    assertThat(account.getLastName()).isEqualTo("XYX");
    assertThat(account.getStatus()).isEqualTo("OK");
    assertThat(account.getAddress1()).isEqualTo("901 San Antonio Road");
    assertThat(account.getAddress2()).isEqualTo("MS UCUP02-206");
    assertThat(account.getCity()).isEqualTo("Palo Alto");
    assertThat(account.getState()).isEqualTo("CA");
    assertThat(account.getZip()).isEqualTo("94303");
    assertThat(account.getCountry()).isEqualTo("USA");
    assertThat(account.getPhone()).isEqualTo("555-555-5555");
    assertThat(account.getLanguagePreference()).isEqualTo("english");
    assertThat(account.getFavouriteCategoryId()).isEqualTo("CATS");
    assertThat(account.isListOption()).isTrue();
    assertThat(account.isBannerOption()).isTrue();
    assertThat(account.getBannerName()).isEqualTo("<image src=\"../images/banner_cats.gif\">");

  }

  @Test
  void insertAccount() {

    // given
    Account account = new Account();
    account.setUsername("mybatis");
    account.setEmail("mybatis@example.com");
    account.setFirstName("My");
    account.setLastName("Batis");
    account.setStatus("NG");
    account.setAddress1("Address 1");
    account.setAddress2("Address 2");
    account.setCity("City");
    account.setState("ST");
    account.setZip("99001");
    account.setCountry("JPN");
    account.setPhone("09012345678");

    // when
    mapper.insertAccount(account);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM account WHERE userid = ?", "mybatis");
    assertThat(record).hasSize(12).containsEntry("USERID", account.getUsername())
        .containsEntry("EMAIL", account.getEmail()).containsEntry("FIRSTNAME", account.getFirstName())
        .containsEntry("LASTNAME", account.getLastName()).containsEntry("STATUS", account.getStatus())
        .containsEntry("ADDR1", account.getAddress1()).containsEntry("ADDR2", account.getAddress2())
        .containsEntry("CITY", account.getCity()).containsEntry("STATE", account.getState())
        .containsEntry("ZIP", account.getZip()).containsEntry("COUNTRY", account.getCountry())
        .containsEntry("PHONE", account.getPhone());
  }

  @Test
  void insertProfile() {

    // given
    Account account = new Account();
    account.setUsername("mybatis");
    account.setLanguagePreference("japanese");
    account.setFavouriteCategoryId("C01");
    account.setListOption(true);
    account.setBannerOption(false);

    // when
    mapper.insertProfile(account);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM profile WHERE userid = ?", "mybatis");

    assertThat(record).hasSize(5).containsEntry("USERID", account.getUsername())
        .containsEntry("LANGPREF", account.getLanguagePreference())
        .containsEntry("FAVCATEGORY", account.getFavouriteCategoryId()).containsEntry("MYLISTOPT", 1)
        .containsEntry("BANNEROPT", 0);
  }

  @Test
  void insertSignon() {

    // given
    Account account = new Account();
    account.setUsername("mybatis");
    account.setPassword("password");

    // when
    mapper.insertSignon(account);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM signon WHERE username = ?", "mybatis");

    assertThat(record).hasSize(2).containsEntry("USERNAME", account.getUsername()).containsEntry("PASSWORD",
        account.getPassword());
  }

  @Test
  void updateAccount() {

    // given
    Account account = new Account();
    account.setUsername("j2ee");
    account.setEmail("mybatis@example.com");
    account.setFirstName("My");
    account.setLastName("Batis");
    account.setStatus("NG");
    account.setAddress1("Address 1");
    account.setAddress2("Address 2");
    account.setCity("City");
    account.setState("ST");
    account.setZip("99001");
    account.setCountry("JPN");
    account.setPhone("09012345678");

    // when
    mapper.updateAccount(account);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM account WHERE userid = ?", "j2ee");

    assertThat(record).hasSize(12).containsEntry("USERID", account.getUsername())
        .containsEntry("EMAIL", account.getEmail()).containsEntry("FIRSTNAME", account.getFirstName())
        .containsEntry("LASTNAME", account.getLastName()).containsEntry("STATUS", account.getStatus())
        .containsEntry("ADDR1", account.getAddress1()).containsEntry("ADDR2", account.getAddress2())
        .containsEntry("CITY", account.getCity()).containsEntry("STATE", account.getState())
        .containsEntry("ZIP", account.getZip()).containsEntry("COUNTRY", account.getCountry())
        .containsEntry("PHONE", account.getPhone());
  }

  @Test
  void updateProfile() {

    // given
    Account account = new Account();
    account.setUsername("j2ee");
    account.setLanguagePreference("japanese");
    account.setFavouriteCategoryId("C01");
    account.setListOption(false);
    account.setBannerOption(false);

    // when
    mapper.updateProfile(account);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM profile WHERE userid = ?", "j2ee");

    assertThat(record).hasSize(5).containsEntry("USERID", account.getUsername())
        .containsEntry("LANGPREF", account.getLanguagePreference())
        .containsEntry("FAVCATEGORY", account.getFavouriteCategoryId()).containsEntry("MYLISTOPT", 0)
        .containsEntry("BANNEROPT", 0);
  }

  @Test
  void updateSignon() {

    // given
    Account account = new Account();
    account.setUsername("j2ee");
    account.setPassword("password");

    // when
    mapper.updateSignon(account);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM signon WHERE username = ?", "j2ee");

    assertThat(record).hasSize(2).containsEntry("USERNAME", account.getUsername()).containsEntry("PASSWORD",
        account.getPassword());
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
package org.mybatis.jpetstore.web.actions;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.mybatis.jpetstore.domain.Account;

class AccountActionBeanTest {

  // Test written by Diffblue Cover.
  @Test
  void getMyListOutputNull() {

    // Arrange
    final AccountActionBean accountActionBean = new AccountActionBean();

    // Act and Assert result
    assertThat(accountActionBean.getMyList()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void constructorOutputNotNull() {

    // Act, creating object to test constructor
    final AccountActionBean actual = new AccountActionBean();

    // Assert result
    assertThat(actual).isNotNull();
    assertThat(actual.getContext()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getPasswordOutputNull() {

    // Arrange
    final AccountActionBean accountActionBean = new AccountActionBean();

    // Act and Assert result
    assertThat(accountActionBean.getPassword()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void isAuthenticatedOutputFalse() {

    // Arrange
    final AccountActionBean accountActionBean = new AccountActionBean();

    // Act and Assert result
    assertThat(accountActionBean.isAuthenticated()).isFalse();

  }

  // Test written by Diffblue Cover.
  @Test
  void getUsernameOutputNull() {

    // Arrange
    final AccountActionBean accountActionBean = new AccountActionBean();

    // Act and Assert result
    assertThat(accountActionBean.getUsername()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getAccountOutputNotNull() {

    // Arrange
    final AccountActionBean accountActionBean = new AccountActionBean();

    // Act
    final Account actual = accountActionBean.getAccount();

    // Assert result
    assertThat(actual).isNotNull();
    assertThat(actual.getAddress2()).isNull();
    assertThat(actual.getState()).isNull();
    assertThat(actual.getFirstName()).isNull();
    assertThat(actual.getPassword()).isNull();
    assertThat(actual.getLanguagePreference()).isNull();
    assertThat(actual.getFavouriteCategoryId()).isNull();
    assertThat(actual.getCountry()).isNull();
    assertThat(actual.getPhone()).isNull();
    assertThat(actual.getUsername()).isNull();
    assertThat(actual.getLastName()).isNull();
    assertThat(actual.getAddress1()).isNull();
    assertThat(actual.getEmail()).isNull();
    assertThat(actual.getStatus()).isNull();
    assertThat(actual.getBannerName()).isNull();
    assertThat(actual.getZip()).isNull();
    assertThat(actual.getCity()).isNull();

  }
}


// Node: getAccountOutputNotNull
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

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.util.Date;

import org.junit.jupiter.api.Test;

class OrderTest {

  @Test
  void initOrder() {
    // given
    Account account = new Account();
    account.setUsername("mybatis");
    account.setEmail("mybatis@example.com");
    account.setFirstName("My");
    account.setLastName("Batis");
    account.setStatus("NG");
    account.setAddress1("Address 1");
    account.setAddress2("Address 2");
    account.setCity("City");
    account.setState("ST");
    account.setZip("99001");
    account.setCountry("JPN");
    account.setPhone("09012345678");

    Cart cart = new Cart();
    Item item = new Item();
    item.setItemId("I01");
    item.setListPrice(new BigDecimal("2.05"));
    cart.addItem(item, true);
    cart.addItem(item, true);

    Order order = new Order();

    // when
    order.initOrder(account, cart);

    // then
    assertThat(order.getUsername()).isSameAs(account.getUsername());
    assertThat(order.getOrderDate()).isBeforeOrEqualsTo(new Date());
    assertThat(order.getShipAddress1()).isEqualTo(account.getAddress1());
    assertThat(order.getShipAddress2()).isEqualTo(account.getAddress2());
    assertThat(order.getShipCity()).isEqualTo(account.getCity());
    assertThat(order.getShipState()).isEqualTo(account.getState());
    assertThat(order.getShipCountry()).isEqualTo(account.getCountry());
    assertThat(order.getShipZip()).isEqualTo(account.getZip());
    assertThat(order.getBillAddress1()).isEqualTo(account.getAddress1());
    assertThat(order.getBillAddress2()).isEqualTo(account.getAddress2());
    assertThat(order.getBillCity()).isEqualTo(account.getCity());
    assertThat(order.getBillState()).isEqualTo(account.getState());
    assertThat(order.getBillCountry()).isEqualTo(account.getCountry());
    assertThat(order.getBillZip()).isEqualTo(account.getZip());
    assertThat(order.getTotalPrice()).isEqualTo(new BigDecimal("4.10"));
    assertThat(order.getCreditCard()).isEqualTo("999 9999 9999 9999");
    assertThat(order.getCardType()).isEqualTo("Visa");
    assertThat(order.getExpiryDate()).isEqualTo("12/03");
    assertThat(order.getCourier()).isEqualTo("UPS");
    assertThat(order.getLocale()).isEqualTo("CA");
    assertThat(order.getStatus()).isEqualTo("P");
    assertThat(order.getLineItems()).hasSize(1);
    assertThat(order.getLineItems().get(0).getItem()).isSameAs(item);
    assertThat(order.getLineItems().get(0).getLineNumber()).isEqualTo(1);
    assertThat(order.getLineItems().get(0).getItemId()).isEqualTo("I01");
    assertThat(order.getLineItems().get(0).getUnitPrice()).isEqualTo(new BigDecimal("2.05"));
    assertThat(order.getLineItems().get(0).getQuantity()).isEqualTo(2);
    assertThat(order.getLineItems().get(0).getTotal()).isEqualTo(new BigDecimal("4.10"));
  }

}


// Node: isBeforeOrEqualsTo
