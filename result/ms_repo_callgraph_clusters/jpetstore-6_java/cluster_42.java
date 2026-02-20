// Cluster 42

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
package org.mybatis.jpetstore;

import static com.codeborne.selenide.Browsers.CHROME;
import static com.codeborne.selenide.CollectionCondition.size;
import static com.codeborne.selenide.Condition.empty;
import static com.codeborne.selenide.Condition.text;
import static com.codeborne.selenide.Condition.value;
import static com.codeborne.selenide.Configuration.baseUrl;
import static com.codeborne.selenide.Configuration.browser;
import static com.codeborne.selenide.Configuration.headless;
import static com.codeborne.selenide.Configuration.timeout;
import static com.codeborne.selenide.Selenide.$;
import static com.codeborne.selenide.Selenide.$$;
import static com.codeborne.selenide.Selenide.open;
import static com.codeborne.selenide.Selenide.title;
import static org.assertj.core.api.Assertions.assertThat;

import com.codeborne.selenide.SelenideElement;
import com.codeborne.selenide.junit5.ScreenShooterExtension;

import java.util.concurrent.TimeUnit;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.openqa.selenium.By;

/**
 * Integration tests for screen transition.
 *
 * @author Kazuki Shimizu
 */
@ExtendWith(ScreenShooterExtension.class)
class ScreenTransitionIT {

  @BeforeAll
  static void setupSelenide() {
    browser = CHROME;
    headless = true;
    timeout = TimeUnit.SECONDS.toMillis(10);
    baseUrl = "http://localhost:8080/jpetstore";
  }

  @AfterEach
  void logout() {
    SelenideElement element = $(By.linkText("Sign Out"));
    if (element.exists()) {
      element.click();
    }
  }

  @Test
  void testOrder() {

    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");
    $(By.cssSelector("#Content h2")).shouldBe(text("Welcome to JPetStore 6"));

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to sign in page & sign
    $(By.linkText("Sign In")).click();
    $(By.name("username")).setValue("j2ee");
    $(By.name("password")).setValue("j2ee");
    $(By.name("signon")).click();
    $(By.id("WelcomeContent")).shouldBe(text("Welcome ABC!"));

    // Search items
    $(By.name("keyword")).setValue("fish");
    $(By.name("searchProducts")).click();
    $$(By.cssSelector("#Catalog table tr")).shouldHave(size(4));

    // Select item
    $(By.linkText("Fresh Water fish from China")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Goldfish"));

    // Add a item to the cart
    $(By.linkText("Add to Cart")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Shopping Cart"));

    // Add a item to the cart
    $(By.cssSelector("#QuickLinks a:nth-of-type(5)")).click();
    $(By.linkText("AV-CB-01")).click();
    $(By.linkText("EST-18")).click();
    $(By.linkText("Add to Cart")).click();
    $(By.cssSelector("#Cart tr:nth-of-type(4) td")).shouldBe(text("Sub Total: $199.00"));

    // Update quantity
    $(By.name("EST-20")).setValue("10");
    $(By.name("updateCartQuantities")).click();
    $(By.cssSelector("#Catalog tr td:nth-of-type(7)")).shouldBe(text("$55.00"));
    $(By.cssSelector("#Cart tr:nth-of-type(4) td")).shouldBe(text("Sub Total: $248.50"));

    // Remove item
    $(By.cssSelector("#Cart tr:nth-of-type(3) td:nth-of-type(8) a")).click();
    $(By.cssSelector("#Cart tr:nth-of-type(3) td")).shouldBe(text("Sub Total: $55.00"));

    // Checkout cart items
    $(By.linkText("Proceed to Checkout")).click();
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Changing shipping address
    $(By.name("shippingAddressRequired")).click();
    $(By.name("newOrder")).click();
    $(By.cssSelector("#Catalog tr th")).shouldBe(text("Shipping Address"));
    $(By.name("order.shipAddress2")).setValue("MS UCUP02-207");

    // Confirm order information
    $(By.name("newOrder")).click();
    $(By.cssSelector("#Catalog")).shouldBe(text("Please confirm the information below and then press continue..."));

    // Submit order
    $(By.linkText("Confirm")).click();
    $(By.cssSelector(".messages li")).shouldBe(text("Thank you, your order has been submitted."));
    String orderId = extractOrderId($(By.cssSelector("#Catalog table tr")).text());

    // Show profile page
    $(By.linkText("My Account")).click();
    $(By.cssSelector("#Catalog h3")).shouldBe(text("User Information"));

    // Show orders
    $(By.linkText("My Orders")).click();
    $(By.cssSelector("#Content h2")).shouldBe(text("My Orders"));

    // Show order detail
    $(By.linkText(orderId)).click();
    assertThat(extractOrderId($(By.cssSelector("#Catalog table tr")).text())).isEqualTo(orderId);

    // Sign out
    $(By.linkText("Sign Out")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

  }

  @Test
  void testUpdateProfile() {
    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to sign in page & sign
    $(By.linkText("Sign In")).click();
    $(By.name("username")).setValue("j2ee");
    $(By.name("password")).setValue("j2ee");
    $(By.name("signon")).click();
    $(By.id("WelcomeContent")).shouldBe(text("Welcome ABC!"));

    // Show profile page
    $(By.linkText("My Account")).click();
    $(By.cssSelector("#Catalog h3")).shouldBe(text("User Information"));
    $$(By.cssSelector("#Catalog table td")).get(1).shouldBe(text("j2ee"));

    // Edit account
    $(By.name("account.phone")).setValue("555-555-5556");
    $(By.name("editAccount")).click();
    $(By.cssSelector("#Catalog h3")).shouldBe(text("User Information"));
    $$(By.cssSelector("#Catalog table td")).get(1).shouldBe(text("j2ee"));
    $(By.name("account.phone")).shouldBe(value("555-555-5556"));
  }

  @Test
  void testRegistrationUser() {
    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to sign in page & sign
    $(By.linkText("Sign In")).click();
    $(By.cssSelector("#Catalog p")).shouldBe(text("Please enter your username and password."));

    // Move to use registration page
    $(By.linkText("Register Now!")).click();
    $(By.cssSelector("#Catalog h3")).shouldBe(text("User Information"));

    // Create a new user
    String userId = String.valueOf(System.currentTimeMillis());
    $(By.name("username")).setValue(userId);
    $(By.name("password")).setValue("password");
    $(By.name("repeatedPassword")).setValue("password");
    $(By.name("account.firstName")).setValue("Jon");
    $(By.name("account.lastName")).setValue("MyBatis");
    $(By.name("account.email")).setValue("jon.mybatis@test.com");
    $(By.name("account.phone")).setValue("09012345678");
    $(By.name("account.address1")).setValue("Address1");
    $(By.name("account.address2")).setValue("Address2");
    $(By.name("account.city")).setValue("Minato-Ku");
    $(By.name("account.state")).setValue("Tokyo");
    $(By.name("account.zip")).setValue("0001234");
    $(By.name("account.country")).setValue("Japan");
    $(By.name("account.languagePreference")).selectOption("japanese");
    $(By.name("account.favouriteCategoryId")).selectOption("CATS");
    $(By.name("account.listOption")).setSelected(true);
    $(By.name("account.bannerOption")).setSelected(true);
    $(By.name("newAccount")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to sign in page & sign
    $(By.linkText("Sign In")).click();
    $(By.name("username")).setValue(userId);
    $(By.name("password")).setValue("password");
    $(By.name("signon")).click();
    $(By.id("WelcomeContent")).shouldBe(text("Welcome Jon!"));

  }

  @Test
  void testSelectItems() {
    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to category
    $(By.cssSelector("#SidebarContent a")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Fish"));

    // Move to items
    $(By.linkText("FI-SW-01")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Angelfish"));

    // Move to item detail
    $(By.linkText("EST-1")).click();
    $$(By.cssSelector("#Catalog table tr td")).get(2).shouldBe(text("Large Angelfish"));

    // Back to items
    $(By.linkText("Return to FI-SW-01")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Angelfish"));

    // Back to category
    $(By.linkText("Return to FISH")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Fish"));

    // Back to the top page
    $(By.linkText("Return to Main Menu")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

  }

  @Test
  void testViewCart() {

    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to cart
    $(By.name("img_cart")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Shopping Cart"));

  }

  @Test
  void testViewHelp() {

    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to help
    $(By.linkText("?")).click();
    $(By.cssSelector("#Content h1")).shouldBe(text("JPetStore Demo"));

  }

  @Test
  void testSidebarContentOnTopPage() {
    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to Fish category
    $(By.cssSelector("#SidebarContent a:nth-of-type(1)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Fish"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Dogs category
    $(By.cssSelector("#SidebarContent a:nth-of-type(2)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Dogs"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Cats category
    $(By.cssSelector("#SidebarContent a:nth-of-type(3)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Cats"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Reptiles category
    $(By.cssSelector("#SidebarContent a:nth-of-type(4)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Reptiles"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Birds category
    $(By.cssSelector("#SidebarContent a:nth-of-type(5)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Birds"));
    $(By.linkText("Return to Main Menu")).click();
  }

  @Test
  void testQuickLinks() {
    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to Fish category
    $(By.cssSelector("#QuickLinks a:nth-of-type(1)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Fish"));

    // Move to Dogs category
    $(By.cssSelector("#QuickLinks a:nth-of-type(2)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Dogs"));

    // Move to Reptiles category
    $(By.cssSelector("#QuickLinks a:nth-of-type(3)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Reptiles"));

    // Move to Cats category
    $(By.cssSelector("#QuickLinks a:nth-of-type(4)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Cats"));

    // Move to Birds category
    $(By.cssSelector("#QuickLinks a:nth-of-type(5)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Birds"));
  }

  @Test
  void testMainImageContentOnTopPage() {
    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to Birds category
    $(By.cssSelector("#MainImageContent area:nth-of-type(1)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Birds"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Fish category
    $(By.cssSelector("#MainImageContent area:nth-of-type(2)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Fish"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Dogs category
    $(By.cssSelector("#MainImageContent area:nth-of-type(3)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Dogs"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Reptiles category
    $(By.cssSelector("#MainImageContent area:nth-of-type(4)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Reptiles"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Cats category
    $(By.cssSelector("#MainImageContent area:nth-of-type(5)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Cats"));
    $(By.linkText("Return to Main Menu")).click();

    // Move to Birds category
    $(By.cssSelector("#MainImageContent area:nth-of-type(6)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Birds"));
    $(By.linkText("Return to Main Menu")).click();
  }

  @Test
  void testLogoContent() {
    // Open the home page
    open("/");
    assertThat(title()).isEqualTo("JPetStore Demo");

    // Move to the top page
    $(By.linkText("Enter the Store")).click();
    $(By.id("WelcomeContent")).shouldBe(empty);

    // Move to Birds category
    $(By.cssSelector("#MainImageContent area:nth-of-type(1)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Birds"));

    // Move to top by clicking logo
    $(By.cssSelector("#LogoContent a")).click();

    // Move to Cats category
    $(By.cssSelector("#MainImageContent area:nth-of-type(5)")).click();
    $(By.cssSelector("#Catalog h2")).shouldBe(text("Cats"));
  }

  private static String extractOrderId(String target) {
    Matcher matcher = Pattern.compile("Order #(\\d{4}) .*").matcher(target);
    String orderId = "";
    if (matcher.find()) {
      orderId = matcher.group(1);
    }
    return orderId;
  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/ScreenTransitionIT.java:ScreenTransitionIT.<init>
// Node: ExtendWith
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


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/mapper/OrderMapperTest.java:OrderMapperTest.<init>
// Node: ContextConfiguration
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

import java.util.Comparator;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mybatis.jpetstore.domain.Category;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = MapperTestContext.class)
@Transactional
class CategoryMapperTest {

  @Autowired
  private CategoryMapper mapper;

  @Test
  void getCategoryList() {
    // given

    // when
    List<Category> categories = mapper.getCategoryList();

    // then
    categories.sort(Comparator.comparing(Category::getCategoryId));
    assertThat(categories).hasSize(5);
    assertThat(categories.get(0).getCategoryId()).isEqualTo("BIRDS");
    assertThat(categories.get(0).getName()).isEqualTo("Birds");
    assertThat(categories.get(0).getDescription())
        .isEqualTo("<image src=\"../images/birds_icon.gif\"><font size=\"5\" color=\"blue\"> Birds</font>");
    assertThat(categories.get(1).getCategoryId()).isEqualTo("CATS");
    assertThat(categories.get(1).getName()).isEqualTo("Cats");
    assertThat(categories.get(1).getDescription())
        .isEqualTo("<image src=\"../images/cats_icon.gif\"><font size=\"5\" color=\"blue\"> Cats</font>");
    assertThat(categories.get(2).getCategoryId()).isEqualTo("DOGS");
    assertThat(categories.get(2).getName()).isEqualTo("Dogs");
    assertThat(categories.get(2).getDescription())
        .isEqualTo("<image src=\"../images/dogs_icon.gif\"><font size=\"5\" color=\"blue\"> Dogs</font>");
    assertThat(categories.get(3).getCategoryId()).isEqualTo("FISH");
    assertThat(categories.get(3).getName()).isEqualTo("Fish");
    assertThat(categories.get(3).getDescription())
        .isEqualTo("<image src=\"../images/fish_icon.gif\"><font size=\"5\" color=\"blue\"> Fish</font>");
    assertThat(categories.get(4).getCategoryId()).isEqualTo("REPTILES");
    assertThat(categories.get(4).getName()).isEqualTo("Reptiles");
    assertThat(categories.get(4).getDescription())
        .isEqualTo("<image src=\"../images/reptiles_icon.gif\"><font size=\"5\" color=\"blue\"> Reptiles</font>");
  }

  @Test
  void getCategory() {
    // given
    String categoryId = "BIRDS";

    // when
    Category category = mapper.getCategory(categoryId);

    // then
    assertThat(category.getCategoryId()).isEqualTo("BIRDS");
    assertThat(category.getName()).isEqualTo("Birds");
    assertThat(category.getDescription())
        .isEqualTo("<image src=\"../images/birds_icon.gif\"><font size=\"5\" color=\"blue\"> Birds</font>");
  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/mapper/CategoryMapperTest.java:CategoryMapperTest.<init>
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

import java.util.Comparator;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mybatis.jpetstore.domain.Product;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = MapperTestContext.class)
@Transactional
class ProductMapperTest {

  @Autowired
  private ProductMapper mapper;

  @Test
  void getProductListByCategory() {
    // given
    String categoryId = "FISH";

    // when
    List<Product> products = mapper.getProductListByCategory(categoryId);

    // then
    products.sort(Comparator.comparing(Product::getProductId));
    assertThat(products).hasSize(4);
    assertThat(products.get(0).getProductId()).isEqualTo("FI-FW-01");
    assertThat(products.get(0).getName()).isEqualTo("Koi");
    assertThat(products.get(0).getCategoryId()).isEqualTo("FISH");
    assertThat(products.get(0).getDescription())
        .isEqualTo("<image src=\"../images/fish3.gif\">Fresh Water fish from Japan");
    assertThat(products.get(1).getProductId()).isEqualTo("FI-FW-02");
    assertThat(products.get(1).getName()).isEqualTo("Goldfish");
    assertThat(products.get(1).getCategoryId()).isEqualTo("FISH");
    assertThat(products.get(1).getDescription())
        .isEqualTo("<image src=\"../images/fish2.gif\">Fresh Water fish from China");
    assertThat(products.get(2).getProductId()).isEqualTo("FI-SW-01");
    assertThat(products.get(2).getName()).isEqualTo("Angelfish");
    assertThat(products.get(2).getCategoryId()).isEqualTo("FISH");
    assertThat(products.get(2).getDescription())
        .isEqualTo("<image src=\"../images/fish1.gif\">Salt Water fish from Australia");
    assertThat(products.get(3).getProductId()).isEqualTo("FI-SW-02");
    assertThat(products.get(3).getName()).isEqualTo("Tiger Shark");
    assertThat(products.get(3).getCategoryId()).isEqualTo("FISH");
    assertThat(products.get(3).getDescription())
        .isEqualTo("<image src=\"../images/fish4.gif\">Salt Water fish from Australia");
  }

  @Test
  void getProduct() {
    // given
    String productId = "FI-FW-01";

    // when
    Product product = mapper.getProduct(productId);

    // then
    assertThat(product.getProductId()).isEqualTo("FI-FW-01");
    assertThat(product.getName()).isEqualTo("Koi");
    assertThat(product.getCategoryId()).isEqualTo("FISH");
    assertThat(product.getDescription()).isEqualTo("<image src=\"../images/fish3.gif\">Fresh Water fish from Japan");
  }

  @Test
  void searchProductList() {
    // given
    String keywords = "%o%";

    // when
    List<Product> products = mapper.searchProductList(keywords);

    // then
    products.sort(Comparator.comparing(Product::getProductId));
    System.out.println(products);
    assertThat(products).hasSize(8);
    assertThat(products.get(0).getProductId()).isEqualTo("AV-CB-01");
    assertThat(products.get(0).getName()).isEqualTo("Amazon Parrot");
    assertThat(products.get(0).getCategoryId()).isEqualTo("BIRDS");
    assertThat(products.get(0).getDescription())
        .isEqualTo("<image src=\"../images/bird2.gif\">Great companion for up to 75 years");
    assertThat(products.get(1).getName()).isEqualTo("Koi");
    assertThat(products.get(2).getName()).isEqualTo("Goldfish");
    assertThat(products.get(3).getName()).isEqualTo("Bulldog");
    assertThat(products.get(4).getName()).isEqualTo("Dalmation");
    assertThat(products.get(5).getName()).isEqualTo("Poodle");
    assertThat(products.get(6).getName()).isEqualTo("Golden Retriever");
    assertThat(products.get(7).getName()).isEqualTo("Labrador Retriever");
  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/mapper/ProductMapperTest.java:ProductMapperTest.<init>
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
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mybatis.jpetstore.domain.Item;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = MapperTestContext.class)
@Transactional
class ItemMapperTest {

  @Autowired
  private ItemMapper mapper;

  @Autowired
  private JdbcTemplate jdbcTemplate;

  @Test
  void getItemListByProduct() {
    // given
    String productId = "FI-SW-01";

    // when
    List<Item> items = mapper.getItemListByProduct(productId);

    // then
    items.sort(Comparator.comparing(Item::getItemId));
    assertThat(items).hasSize(2);
    assertThat(items.get(0).getItemId()).isEqualTo("EST-1");
    assertThat(items.get(0).getListPrice()).isEqualTo(new BigDecimal("16.50"));
    assertThat(items.get(0).getUnitCost()).isEqualTo(new BigDecimal("10.00"));
    assertThat(items.get(0).getSupplierId()).isEqualTo(1);
    assertThat(items.get(0).getStatus()).isEqualTo("P");
    assertThat(items.get(0).getAttribute1()).isEqualTo("Large");
    assertThat(items.get(0).getAttribute2()).isNull();
    assertThat(items.get(0).getAttribute3()).isNull();
    assertThat(items.get(0).getAttribute4()).isNull();
    assertThat(items.get(0).getAttribute5()).isNull();
    assertThat(items.get(0).getProduct().getProductId()).isEqualTo("FI-SW-01");
    assertThat(items.get(0).getProduct().getName()).isEqualTo("Angelfish");
    assertThat(items.get(0).getProduct().getDescription())
        .isEqualTo("<image src=\"../images/fish1.gif\">Salt Water fish from Australia");
    assertThat(items.get(0).getProduct().getCategoryId()).isEqualTo("FISH");
    assertThat(items.get(1).getItemId()).isEqualTo("EST-2");
    assertThat(items.get(1).getListPrice()).isEqualTo(new BigDecimal("16.50"));
    assertThat(items.get(1).getUnitCost()).isEqualTo(new BigDecimal("10.00"));
    assertThat(items.get(1).getSupplierId()).isEqualTo(1);
    assertThat(items.get(1).getStatus()).isEqualTo("P");
    assertThat(items.get(1).getAttribute1()).isEqualTo("Small");
    assertThat(items.get(1).getAttribute2()).isNull();
    assertThat(items.get(1).getAttribute3()).isNull();
    assertThat(items.get(1).getAttribute4()).isNull();
    assertThat(items.get(1).getAttribute5()).isNull();
    assertThat(items.get(1).getProduct().getProductId()).isEqualTo("FI-SW-01");
    assertThat(items.get(1).getProduct().getName()).isEqualTo("Angelfish");
    assertThat(items.get(1).getProduct().getDescription())
        .isEqualTo("<image src=\"../images/fish1.gif\">Salt Water fish from Australia");
    assertThat(items.get(1).getProduct().getCategoryId()).isEqualTo("FISH");
  }

  @Test
  void getItem() {
    // given
    String itemId = "EST-1";

    // when
    Item item = mapper.getItem(itemId);

    // then
    assertThat(item.getItemId()).isEqualTo("EST-1");
    assertThat(item.getListPrice()).isEqualTo(new BigDecimal("16.50"));
    assertThat(item.getUnitCost()).isEqualTo(new BigDecimal("10.00"));
    assertThat(item.getSupplierId()).isEqualTo(1);
    assertThat(item.getStatus()).isEqualTo("P");
    assertThat(item.getAttribute1()).isEqualTo("Large");
    assertThat(item.getAttribute2()).isNull();
    assertThat(item.getAttribute3()).isNull();
    assertThat(item.getAttribute4()).isNull();
    assertThat(item.getAttribute5()).isNull();
    assertThat(item.getProduct().getProductId()).isEqualTo("FI-SW-01");
    assertThat(item.getProduct().getName()).isEqualTo("Angelfish");
    assertThat(item.getProduct().getDescription())
        .isEqualTo("<image src=\"../images/fish1.gif\">Salt Water fish from Australia");
    assertThat(item.getProduct().getCategoryId()).isEqualTo("FISH");
  }

  @Test
  void getInventoryQuantity() {
    // given
    String itemId = "EST-1";

    // when
    int quantity = mapper.getInventoryQuantity(itemId);

    // then
    assertThat(quantity).isEqualTo(10000);

  }

  @Test
  void updateInventoryQuantity() {
    // given
    String itemId = "EST-1";
    Map<String, Object> params = new HashMap<>();
    params.put("itemId", itemId);
    params.put("increment", 10);

    // when
    mapper.updateInventoryQuantity(params);

    // then
    Integer quantity = jdbcTemplate.queryForObject("SELECT QTY FROM inventory WHERE itemid = ?", Integer.class, itemId);
    assertThat(quantity).isEqualTo(9990);

  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/mapper/ItemMapperTest.java:ItemMapperTest.<init>
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


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/mapper/AccountMapperTest.java:AccountMapperTest.<init>
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

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mybatis.jpetstore.domain.Sequence;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = MapperTestContext.class)
@Transactional
class SequenceMapperTest {

  @Autowired
  private SequenceMapper mapper;

  @Autowired
  private JdbcTemplate jdbcTemplate;

  @Test
  void getSequence() {
    // given

    // when
    Sequence sequence = mapper.getSequence(new Sequence("ordernum", -1));

    // then
    assertThat(sequence.getName()).isEqualTo("ordernum");
    assertThat(sequence.getNextId()).isEqualTo(1000);
  }

  @Test
  void updateSequence() {
    // given
    Sequence sequence = new Sequence("ordernum", 1001);

    // when
    mapper.updateSequence(sequence);

    // then
    Integer id = jdbcTemplate.queryForObject("SELECT nextid FROM sequence WHERE name = ?", Integer.class, "ordernum");
    assertThat(id).isEqualTo(1001);
  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/mapper/SequenceMapperTest.java:SequenceMapperTest.<init>
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
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mybatis.jpetstore.domain.LineItem;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = MapperTestContext.class)
@Transactional
class LineItemMapperTest {

  @Autowired
  private LineItemMapper mapper;

  @Autowired
  private JdbcTemplate jdbcTemplate;

  @Test
  void insertLineItem() {
    // given
    LineItem lineItem = new LineItem();
    lineItem.setOrderId(1);
    lineItem.setLineNumber(1);
    lineItem.setItemId("EST-1");
    lineItem.setQuantity(4);
    lineItem.setUnitPrice(BigDecimal.valueOf(100));

    // when
    mapper.insertLineItem(lineItem);

    // then
    Map<String, Object> record = jdbcTemplate.queryForMap("SELECT * FROM lineitem WHERE orderid = ? AND linenum = ?", 1,
        1);
    assertThat(record).hasSize(5).containsEntry("ORDERID", lineItem.getOrderId())
        .containsEntry("LINENUM", lineItem.getLineNumber()).containsEntry("ITEMID", lineItem.getItemId())
        .containsEntry("QUANTITY", lineItem.getQuantity()).containsEntry("UNITPRICE", new BigDecimal("100.00"));

  }

  @Test
  void getLineItemsByOrderId() {
    // given
    LineItem lineItem = new LineItem();
    lineItem.setOrderId(1);
    lineItem.setLineNumber(1);
    lineItem.setItemId("EST-1");
    lineItem.setQuantity(4);
    lineItem.setUnitPrice(BigDecimal.valueOf(100));
    mapper.insertLineItem(lineItem);

    // when
    List<LineItem> lineItems = mapper.getLineItemsByOrderId(1);

    // then
    assertThat(lineItems).hasSize(1);
    assertThat(lineItems.get(0).getOrderId()).isEqualTo(lineItem.getOrderId());
    assertThat(lineItems.get(0).getLineNumber()).isEqualTo(lineItem.getOrderId());
    assertThat(lineItems.get(0).getItemId()).isEqualTo(lineItem.getItemId());
    assertThat(lineItems.get(0).getQuantity()).isEqualTo(lineItem.getQuantity());
    assertThat(lineItems.get(0).getUnitPrice()).isEqualTo(new BigDecimal("100.00"));

  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/mapper/LineItemMapperTest.java:LineItemMapperTest.<init>
/*
 *    Copyright 2010-2023 the original author or authors.
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
package org.mybatis.jpetstore.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.fail;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mybatis.jpetstore.domain.Item;
import org.mybatis.jpetstore.domain.LineItem;
import org.mybatis.jpetstore.domain.Order;
import org.mybatis.jpetstore.domain.Sequence;
import org.mybatis.jpetstore.mapper.ItemMapper;
import org.mybatis.jpetstore.mapper.LineItemMapper;
import org.mybatis.jpetstore.mapper.OrderMapper;
import org.mybatis.jpetstore.mapper.SequenceMapper;

/**
 * @author coderliux
 */
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

  @Mock
  private ItemMapper itemMapper;
  @Mock
  private OrderMapper orderMapper;
  @Mock
  private LineItemMapper lineItemMapper;
  @Mock
  private SequenceMapper sequenceMapper;

  @InjectMocks
  private OrderService orderService;

  @Test
  void shouldReturnOrderWhenGivenOrderIdWithOutLineItems() {
    // given
    int orderId = 1;
    Order order = new Order();
    List<LineItem> lineItems = new ArrayList<>();

    // when
    when(orderMapper.getOrder(orderId)).thenReturn(order);
    when(lineItemMapper.getLineItemsByOrderId(orderId)).thenReturn(lineItems);

    // then
    assertThat(orderService.getOrder(orderId)).isEqualTo(order);
    assertThat(orderService.getOrder(orderId).getLineItems()).isEmpty();
  }

  @Test
  void shouldReturnOrderWhenGivenOrderIdExistedLineItems() {
    // given
    int orderId = 1;
    Order order = new Order();
    List<LineItem> lineItems = new ArrayList<>();
    LineItem item = new LineItem();
    String itemId = "abc";
    item.setItemId(itemId);
    lineItems.add(item);

    // when
    when(orderMapper.getOrder(orderId)).thenReturn(order);
    when(lineItemMapper.getLineItemsByOrderId(orderId)).thenReturn(lineItems);
    when(itemMapper.getItem(itemId)).thenReturn(new Item());
    when(itemMapper.getInventoryQuantity(itemId)).thenReturn(5);

    // then
    Order expectedOrder = orderService.getOrder(orderId);
    assertThat(expectedOrder).isEqualTo(order);
    assertThat(expectedOrder.getLineItems()).hasSize(1);
    assertThat(expectedOrder.getLineItems().get(0).getItem().getQuantity()).isEqualTo(5);
  }

  @Test
  void shouldReturnOrderList() {

    // given
    String username = "foo";
    List<Order> expectedOrders = new ArrayList<>();

    // when
    when(orderMapper.getOrdersByUsername(username)).thenReturn(expectedOrders);
    List<Order> orders = orderService.getOrdersByUsername(username);

    // then
    assertThat(orders).isSameAs(expectedOrders);

  }

  @Test
  void shouldReturnNextId() {

    // given
    Sequence expectedSequence = new Sequence("order", 100);

    // when
    when(sequenceMapper.getSequence(any())).thenReturn(expectedSequence);
    int nextId = orderService.getNextId("order");

    // then
    assertThat(nextId).isEqualTo(100);
    verify(sequenceMapper).getSequence(argThat(v -> v.getName().equals("order") && v.getNextId() == -1));
    verify(sequenceMapper).updateSequence(argThat(v -> v.getName().equals("order") && v.getNextId() == 101));

  }

  @Test
  void shouldThrowExceptionWhenSequenceNotFound() {

    // given

    // when
    when(sequenceMapper.getSequence(any())).thenReturn(null);
    try {
      orderService.getNextId("order");
      fail("Should throw an exception when sequence not found.");
    } catch (RuntimeException e) {
      // then
      assertThat(e.getMessage())
          .isEqualTo("Error: A null sequence was returned from the database (could not get next order sequence).");
      verify(sequenceMapper).getSequence(argThat(v -> v.getName().equals("order") && v.getNextId() == -1));
    }

  }

  @Test
  void shouldCallTheMapperToInsert() {
    // given
    Order order = new Order();
    LineItem item = new LineItem();
    String itemId = "I01";
    int quantity = 4;
    item.setItemId(itemId);
    item.setQuantity(quantity);
    order.addLineItem(item);

    Sequence orderNumSequence = new Sequence("ordernum", 100);

    Map<String, Object> expectedItemParam = new HashMap<>(2);
    expectedItemParam.put("itemId", itemId);
    expectedItemParam.put("increment", quantity);

    // when
    when(sequenceMapper.getSequence(any())).thenReturn(orderNumSequence);
    orderService.insertOrder(order);

    // then
    verify(orderMapper).insertOrder(argThat(v -> v == order && v.getOrderId() == 100));
    verify(orderMapper).insertOrderStatus(eq(order));
    verify(lineItemMapper).insertLineItem(argThat(v -> v == item && v.getOrderId() == 100));
    verify(itemMapper).updateInventoryQuantity(eq(expectedItemParam));
  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/service/OrderServiceTest.java:OrderServiceTest.<init>
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
package org.mybatis.jpetstore.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

import java.util.ArrayList;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mybatis.jpetstore.domain.Category;
import org.mybatis.jpetstore.domain.Item;
import org.mybatis.jpetstore.domain.Product;
import org.mybatis.jpetstore.mapper.CategoryMapper;
import org.mybatis.jpetstore.mapper.ItemMapper;
import org.mybatis.jpetstore.mapper.ProductMapper;

/**
 * @author Eduardo Macarron
 */
@ExtendWith(MockitoExtension.class)
class CatalogServiceTest {

  @Mock(lenient = true)
  private ProductMapper productMapper;
  @Mock
  private CategoryMapper categoryMapper;
  @Mock
  private ItemMapper itemMapper;

  @InjectMocks
  private CatalogService catalogService;

  @Test
  void shouldCallTheSearchMapperTwice() {
    // given
    String keywords = "a b";
    List<Product> l1 = new ArrayList<>();
    l1.add(new Product());
    List<Product> l2 = new ArrayList<>();
    l2.add(new Product());

    // when
    when(productMapper.searchProductList("%a%")).thenReturn(l1);
    when(productMapper.searchProductList("%b%")).thenReturn(l2);
    List<Product> r = catalogService.searchProductList(keywords);

    // then
    assertThat(r).hasSize(2);
    assertThat(r.get(0)).isSameAs(l1.get(0));
    assertThat(r.get(1)).isSameAs(l2.get(0));
  }

  @Test
  void shouldReturnCategoryList() {
    // given
    List<Category> expectedCategories = new ArrayList<>();

    // when
    when(categoryMapper.getCategoryList()).thenReturn(expectedCategories);
    List<Category> categories = catalogService.getCategoryList();

    // then
    assertThat(categories).isSameAs(expectedCategories);
  }

  @Test
  void shouldReturnCategory() {

    // given
    String categoryId = "C01";
    Category expectedCategory = new Category();

    // when
    when(categoryMapper.getCategory(categoryId)).thenReturn(expectedCategory);
    Category category = catalogService.getCategory(categoryId);

    // then
    assertThat(category).isSameAs(expectedCategory);

  }

  @Test
  void shouldReturnProduct() {

    // given
    String productId = "P01";
    Product expectedProduct = new Product();

    // when
    when(productMapper.getProduct(productId)).thenReturn(expectedProduct);
    Product product = catalogService.getProduct(productId);

    // then
    assertThat(product).isSameAs(expectedProduct);

  }

  @Test
  void shouldReturnProductList() {
    // given
    String categoryId = "C01";
    List<Product> expectedProducts = new ArrayList<>();

    // when
    when(productMapper.getProductListByCategory(categoryId)).thenReturn(expectedProducts);
    List<Product> products = catalogService.getProductListByCategory(categoryId);

    // then
    assertThat(products).isSameAs(expectedProducts);

  }

  @Test
  void shouldReturnItemList() {
    // given
    String productId = "P01";
    List<Item> expectedItems = new ArrayList<>();

    // when
    when(itemMapper.getItemListByProduct(productId)).thenReturn(expectedItems);
    List<Item> items = catalogService.getItemListByProduct(productId);

    // then
    assertThat(items).isSameAs(expectedItems);

  }

  @Test
  void shouldReturnItem() {

    // given
    String itemCode = "I01";
    Item expectedItem = new Item();

    // when
    when(itemMapper.getItem(itemCode)).thenReturn(expectedItem);
    Item item = catalogService.getItem(itemCode);

    // then
    assertThat(item).isSameAs(expectedItem);

  }

  @Test
  void shouldReturnTrueWhenExistStock() {

    // given
    String itemCode = "I01";

    // when
    when(itemMapper.getInventoryQuantity(itemCode)).thenReturn(1);
    boolean result = catalogService.isItemInStock(itemCode);

    // then
    assertThat(result).isTrue();

  }

  @Test
  void shouldReturnFalseWhenNotExistStock() {

    // given
    String itemCode = "I01";

    // when
    when(itemMapper.getInventoryQuantity(itemCode)).thenReturn(0);
    boolean result = catalogService.isItemInStock(itemCode);

    // then
    assertThat(result).isFalse();

  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/service/CatalogServiceTest.java:CatalogServiceTest.<init>
// Node: Mock
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
package org.mybatis.jpetstore.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.mybatis.jpetstore.domain.Account;
import org.mybatis.jpetstore.mapper.AccountMapper;

/**
 * @author Eduardo Macarron
 */
@ExtendWith(MockitoExtension.class)
class AccountServiceTest {

  @Mock
  private AccountMapper accountMapper;

  @InjectMocks
  private AccountService accountService;

  @Test
  void shouldCallTheMapperToInsertAnAccount() {
    // given
    Account account = new Account();

    // when
    accountService.insertAccount(account);

    // then
    verify(accountMapper).insertAccount(eq(account));
    verify(accountMapper).insertProfile(eq(account));
    verify(accountMapper).insertSignon(eq(account));
  }

  @Test
  void shouldCallTheMapperToUpdateAnAccount() {
    // given
    Account account = new Account();
    account.setPassword("foo");

    // when
    accountService.updateAccount(account);

    // then
    verify(accountMapper).updateAccount(eq(account));
    verify(accountMapper).updateProfile(eq(account));
    verify(accountMapper).updateSignon(eq(account));
  }

  @Test
  void shouldCallTheMapperToGetAccountAnUsername() {
    // given
    String username = "bar";
    Account expectedAccount = new Account();
    when(accountMapper.getAccountByUsername(username)).thenReturn(expectedAccount);

    // when
    Account account = accountService.getAccount(username);

    // then
    assertThat(account).isSameAs(expectedAccount);
  }

  @Test
  void shouldCallTheMapperToGetAccountAnUsernameAndPassword() {
    // given
    String username = "bar";
    String password = "foo";

    // when
    Account expectedAccount = new Account();
    when(accountMapper.getAccountByUsernameAndPassword(username, password)).thenReturn(expectedAccount);
    Account account = accountService.getAccount(username, password);

    // then
    assertThat(account).isSameAs(expectedAccount);
  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/test/java/org/mybatis/jpetstore/service/AccountServiceTest.java:AccountServiceTest.<init>
