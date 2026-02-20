// Cluster 5

// Node: getItem
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

import java.util.ArrayList;
import java.util.List;

import org.mybatis.jpetstore.domain.Category;
import org.mybatis.jpetstore.domain.Item;
import org.mybatis.jpetstore.domain.Product;
import org.mybatis.jpetstore.mapper.CategoryMapper;
import org.mybatis.jpetstore.mapper.ItemMapper;
import org.mybatis.jpetstore.mapper.ProductMapper;
import org.springframework.stereotype.Service;

/**
 * The Class CatalogService.
 *
 * @author Eduardo Macarron
 */
@Service
public class CatalogService {

  private final CategoryMapper categoryMapper;
  private final ItemMapper itemMapper;
  private final ProductMapper productMapper;

  public CatalogService(CategoryMapper categoryMapper, ItemMapper itemMapper, ProductMapper productMapper) {
    this.categoryMapper = categoryMapper;
    this.itemMapper = itemMapper;
    this.productMapper = productMapper;
  }

  public List<Category> getCategoryList() {
    return categoryMapper.getCategoryList();
  }

  public Category getCategory(String categoryId) {
    return categoryMapper.getCategory(categoryId);
  }

  public Product getProduct(String productId) {
    return productMapper.getProduct(productId);
  }

  public List<Product> getProductListByCategory(String categoryId) {
    return productMapper.getProductListByCategory(categoryId);
  }

  /**
   * Search product list.
   *
   * @param keywords
   *          the keywords
   *
   * @return the list
   */
  public List<Product> searchProductList(String keywords) {
    List<Product> products = new ArrayList<>();
    for (String keyword : keywords.split("\\s+")) {
      products.addAll(productMapper.searchProductList("%" + keyword.toLowerCase() + "%"));
    }
    return products;
  }

  public List<Item> getItemListByProduct(String productId) {
    return itemMapper.getItemListByProduct(productId);
  }

  public Item getItem(String itemId) {
    return itemMapper.getItem(itemId);
  }

  public boolean isItemInStock(String itemId) {
    return itemMapper.getInventoryQuantity(itemId) > 0;
  }
}


// Node: getItemId
// Node: getQuantity
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

import java.util.List;

import net.sourceforge.stripes.action.DefaultHandler;
import net.sourceforge.stripes.action.ForwardResolution;
import net.sourceforge.stripes.action.SessionScope;
import net.sourceforge.stripes.integration.spring.SpringBean;

import org.mybatis.jpetstore.domain.Category;
import org.mybatis.jpetstore.domain.Item;
import org.mybatis.jpetstore.domain.Product;
import org.mybatis.jpetstore.service.CatalogService;

/**
 * The Class CatalogActionBean.
 *
 * @author Eduardo Macarron
 */
@SessionScope
public class CatalogActionBean extends AbstractActionBean {

  private static final long serialVersionUID = 5849523372175050635L;

  private static final String MAIN = "/WEB-INF/jsp/catalog/Main.jsp";
  private static final String VIEW_CATEGORY = "/WEB-INF/jsp/catalog/Category.jsp";
  private static final String VIEW_PRODUCT = "/WEB-INF/jsp/catalog/Product.jsp";
  private static final String VIEW_ITEM = "/WEB-INF/jsp/catalog/Item.jsp";
  private static final String SEARCH_PRODUCTS = "/WEB-INF/jsp/catalog/SearchProducts.jsp";

  @SpringBean
  private transient CatalogService catalogService;

  private String keyword;

  private String categoryId;
  private Category category;
  private List<Category> categoryList;

  private String productId;
  private Product product;
  private List<Product> productList;

  private String itemId;
  private Item item;
  private List<Item> itemList;

  public String getKeyword() {
    return keyword;
  }

  public void setKeyword(String keyword) {
    this.keyword = keyword;
  }

  public String getCategoryId() {
    return categoryId;
  }

  public void setCategoryId(String categoryId) {
    this.categoryId = categoryId;
  }

  public String getProductId() {
    return productId;
  }

  public void setProductId(String productId) {
    this.productId = productId;
  }

  public String getItemId() {
    return itemId;
  }

  public void setItemId(String itemId) {
    this.itemId = itemId;
  }

  public Category getCategory() {
    return category;
  }

  public void setCategory(Category category) {
    this.category = category;
  }

  public Product getProduct() {
    return product;
  }

  public void setProduct(Product product) {
    this.product = product;
  }

  public Item getItem() {
    return item;
  }

  public void setItem(Item item) {
    this.item = item;
  }

  public List<Category> getCategoryList() {
    return categoryList;
  }

  public void setCategoryList(List<Category> categoryList) {
    this.categoryList = categoryList;
  }

  public List<Product> getProductList() {
    return productList;
  }

  public void setProductList(List<Product> productList) {
    this.productList = productList;
  }

  public List<Item> getItemList() {
    return itemList;
  }

  public void setItemList(List<Item> itemList) {
    this.itemList = itemList;
  }

  @DefaultHandler
  public ForwardResolution viewMain() {
    return new ForwardResolution(MAIN);
  }

  /**
   * View category.
   *
   * @return the forward resolution
   */
  public ForwardResolution viewCategory() {
    if (categoryId != null) {
      productList = catalogService.getProductListByCategory(categoryId);
      category = catalogService.getCategory(categoryId);
    }
    return new ForwardResolution(VIEW_CATEGORY);
  }

  /**
   * View product.
   *
   * @return the forward resolution
   */
  public ForwardResolution viewProduct() {
    if (productId != null) {
      itemList = catalogService.getItemListByProduct(productId);
      product = catalogService.getProduct(productId);
    }
    return new ForwardResolution(VIEW_PRODUCT);
  }

  /**
   * View item.
   *
   * @return the forward resolution
   */
  public ForwardResolution viewItem() {
    item = catalogService.getItem(itemId);
    product = item.getProduct();
    return new ForwardResolution(VIEW_ITEM);
  }

  /**
   * Search products.
   *
   * @return the forward resolution
   */
  public ForwardResolution searchProducts() {
    if (keyword == null || keyword.length() < 1) {
      setMessage("Please enter a keyword to search for, then press the search button.");
      return new ForwardResolution(ERROR);
    } else {
      productList = catalogService.searchProductList(keyword.toLowerCase());
      return new ForwardResolution(SEARCH_PRODUCTS);
    }
  }

  /**
   * Clear.
   */
  public void clear() {
    keyword = null;

    categoryId = null;
    category = null;
    categoryList = null;

    productId = null;
    product = null;
    productList = null;

    itemId = null;
    item = null;
    itemList = null;
  }

}


// Node: getCategoryId
// Node: getProductId
// Node: setItemId
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

import java.util.Iterator;

import javax.servlet.http.HttpServletRequest;

import net.sourceforge.stripes.action.ForwardResolution;
import net.sourceforge.stripes.action.Resolution;
import net.sourceforge.stripes.action.SessionScope;
import net.sourceforge.stripes.integration.spring.SpringBean;

import org.mybatis.jpetstore.domain.Cart;
import org.mybatis.jpetstore.domain.CartItem;
import org.mybatis.jpetstore.domain.Item;
import org.mybatis.jpetstore.service.CatalogService;

/**
 * The Class CartActionBean.
 *
 * @author Eduardo Macarron
 */
@SessionScope
public class CartActionBean extends AbstractActionBean {

  private static final long serialVersionUID = -4038684592582714235L;

  private static final String VIEW_CART = "/WEB-INF/jsp/cart/Cart.jsp";
  private static final String CHECK_OUT = "/WEB-INF/jsp/cart/Checkout.jsp";

  @SpringBean
  private transient CatalogService catalogService;

  private Cart cart = new Cart();
  private String workingItemId;

  public Cart getCart() {
    return cart;
  }

  public void setCart(Cart cart) {
    this.cart = cart;
  }

  public void setWorkingItemId(String workingItemId) {
    this.workingItemId = workingItemId;
  }

  /**
   * Adds the item to cart.
   *
   * @return the resolution
   */
  public Resolution addItemToCart() {

    if (workingItemId == null || workingItemId.trim().isEmpty()) {
      setMessage("Invalid item ID: cannot add item to cart.");
      return new ForwardResolution(ERROR);
    }

    if (cart.containsItemId(workingItemId)) {
      cart.incrementQuantityByItemId(workingItemId);
    } else {
      // isInStock is a "real-time" property that must be updated
      // every time an item is added to the cart, even if other
      // item details are cached.
      boolean isInStock = catalogService.isItemInStock(workingItemId);
      Item item = catalogService.getItem(workingItemId);
      cart.addItem(item, isInStock);
    }

    return new ForwardResolution(VIEW_CART);
  }

  /**
   * Removes the item from cart.
   *
   * @return the resolution
   */
  public Resolution removeItemFromCart() {

    if (workingItemId == null || workingItemId.trim().isEmpty()) {
      setMessage("Invalid item ID: cannot remove item from cart.");
      return new ForwardResolution(ERROR);
    }

    Item item = cart.removeItemById(workingItemId);

    if (item == null) {
      setMessage("Attempted to remove null CartItem from Cart.");
      return new ForwardResolution(ERROR);
    } else {
      return new ForwardResolution(VIEW_CART);
    }
  }

  /**
   * Update cart quantities.
   *
   * @return the resolution
   */
  public Resolution updateCartQuantities() {
    HttpServletRequest request = context.getRequest();

    Iterator<CartItem> cartItems = getCart().getAllCartItems();
    while (cartItems.hasNext()) {
      CartItem cartItem = cartItems.next();
      String itemId = cartItem.getItem().getItemId();
      try {
        int quantity = Integer.parseInt(request.getParameter(itemId));
        getCart().setQuantityByItemId(itemId, quantity);
        if (quantity < 1) {
          cartItems.remove();
        }
      } catch (NumberFormatException e) {
        // ignore invalid numeric input on purpose
      }
    }

    return new ForwardResolution(VIEW_CART);
  }

  public ForwardResolution viewCart() {
    return new ForwardResolution(VIEW_CART);
  }

  public ForwardResolution checkOut() {
    return new ForwardResolution(CHECK_OUT);
  }

  public void clear() {
    cart = new Cart();
    workingItemId = null;
  }

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/main/java/org/mybatis/jpetstore/web/actions/CartActionBean.java:CartActionBean.<init>
// Node: Cart
// Node: containsItemId
// Node: addItem
// Node: removeItemById
// Node: updateCartQuantities
// Node: getAllCartItems
// Node: hasNext
// Node: next
// Node: parseInt
// Node: getParameter
// Node: setQuantityByItemId
// Node: remove
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


// Node: isShippingAddressRequired
// Node: getOrderList
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
 * The Class CartItem.
 *
 * @author Eduardo Macarron
 */
public class CartItem implements Serializable {

  private static final long serialVersionUID = 6620528781626504362L;

  private Item item;
  private int quantity;
  private boolean inStock;
  private BigDecimal total;

  public boolean isInStock() {
    return inStock;
  }

  public void setInStock(boolean inStock) {
    this.inStock = inStock;
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

  public void incrementQuantity() {
    quantity++;
    calculateTotal();
  }

  private void calculateTotal() {
    total = Optional.ofNullable(item).map(Item::getListPrice).map(v -> v.multiply(new BigDecimal(quantity)))
        .orElse(null);
  }

}


// Node: isInStock
// Node: setInStock
// Node: getTotal
// Node: BigDecimal
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


// Node: repos/cloned_ms_repos/jpetstore-6/src/main/java/org/mybatis/jpetstore/domain/LineItem.java:LineItem.<init>
// Node: getListPrice
// Node: getLineNumber
// Node: setLineNumber
// Node: setUnitPrice
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


// Node: getSupplierId
// Node: setListPrice
// Node: getUnitCost
// Node: getAttribute1
// Node: getAttribute2
// Node: getAttribute3
// Node: getAttribute4
// Node: getAttribute5
// Node: getSubTotal
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

/**
 * The Class Sequence.
 *
 * @author Eduardo Macarron
 */
public class Sequence implements Serializable {

  private static final long serialVersionUID = 8278780133180137281L;

  private String name;
  private int nextId;

  public Sequence() {
  }

  public Sequence(String name, int nextId) {
    this.name = name;
    this.nextId = nextId;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public int getNextId() {
    return nextId;
  }

  public void setNextId(int nextId) {
    this.nextId = nextId;
  }

}


// Node: getName
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

/**
 * The Class Product.
 *
 * @author Eduardo Macarron
 */
public class Product implements Serializable {

  private static final long serialVersionUID = -7492639752670189553L;

  private String productId;
  private String categoryId;
  private String name;
  private String description;

  public String getProductId() {
    return productId;
  }

  public void setProductId(String productId) {
    this.productId = productId.trim();
  }

  public String getCategoryId() {
    return categoryId;
  }

  public void setCategoryId(String categoryId) {
    this.categoryId = categoryId;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  @Override
  public String toString() {
    return getName();
  }

}


// Node: getDescription
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
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/**
 * The Class Cart.
 *
 * @author Eduardo Macarron
 */
public class Cart implements Serializable {

  private static final long serialVersionUID = 8329559983943337176L;

  private final Map<String, CartItem> itemMap = Collections.synchronizedMap(new HashMap<>());
  private final List<CartItem> itemList = new ArrayList<>();

  public Iterator<CartItem> getCartItems() {
    return itemList.iterator();
  }

  public List<CartItem> getCartItemList() {
    return itemList;
  }

  public int getNumberOfItems() {
    return itemList.size();
  }

  public Iterator<CartItem> getAllCartItems() {
    return itemList.iterator();
  }

  public boolean containsItemId(String itemId) {
    return itemMap.containsKey(itemId);
  }

  /**
   * Adds the item.
   *
   * @param item
   *          the item
   * @param isInStock
   *          the is in stock
   */
  public void addItem(Item item, boolean isInStock) {
    CartItem cartItem = itemMap.get(item.getItemId());
    if (cartItem == null) {
      cartItem = new CartItem();
      cartItem.setItem(item);
      cartItem.setQuantity(0);
      cartItem.setInStock(isInStock);
      itemMap.put(item.getItemId(), cartItem);
      itemList.add(cartItem);
    }
    cartItem.incrementQuantity();
  }

  /**
   * Removes the item by id.
   *
   * @param itemId
   *          the item id
   *
   * @return the item
   */
  public Item removeItemById(String itemId) {
    CartItem cartItem = itemMap.remove(itemId);
    if (cartItem == null) {
      return null;
    } else {
      itemList.remove(cartItem);
      return cartItem.getItem();
    }
  }

  /**
   * Increment quantity by item id.
   *
   * @param itemId
   *          the item id
   */
  public void incrementQuantityByItemId(String itemId) {
    CartItem cartItem = itemMap.get(itemId);
    cartItem.incrementQuantity();
  }

  public void setQuantityByItemId(String itemId, int quantity) {
    CartItem cartItem = itemMap.get(itemId);
    cartItem.setQuantity(quantity);
  }

  /**
   * Gets the sub total.
   *
   * @return the sub total
   */
  public BigDecimal getSubTotal() {
    return itemList.stream()
        .map(cartItem -> cartItem.getItem().getListPrice().multiply(new BigDecimal(cartItem.getQuantity())))
        .reduce(BigDecimal.ZERO, BigDecimal::add);
  }

}


// Node: getCartItems
// Node: iterator
// Node: getCartItemList
// Node: getNumberOfItems
// Node: containsKey
// Node: get
// Node: CartItem
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

/**
 * The Class Category.
 *
 * @author Eduardo Macarron
 */
public class Category implements Serializable {

  private static final long serialVersionUID = 3992469837058393712L;

  private String categoryId;
  private String name;
  private String description;

  public String getCategoryId() {
    return categoryId;
  }

  public void setCategoryId(String categoryId) {
    this.categoryId = categoryId.trim();
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  @Override
  public String toString() {
    return getCategoryId();
  }

}


// Node: assertThat
// Node: isEqualTo
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


// Node: sort
// Node: comparing
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


// Node: queryForObject
// Node: isTrue
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


// Node: Item
// Node: isFalse
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

class OrderActionBeanTest {

  // Test written by Diffblue Cover.
  @Test
  void getOrderListOutputNull() {

    // Arrange
    final OrderActionBean orderActionBean = new OrderActionBean();

    // Act and Assert result
    assertThat(orderActionBean.getOrderList()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void isShippingAddressRequiredOutputFalse() {

    // Arrange
    final OrderActionBean orderActionBean = new OrderActionBean();

    // Act and Assert result
    assertThat(orderActionBean.isShippingAddressRequired()).isFalse();

  }

  // Test written by Diffblue Cover.
  @Test
  void constructorOutputNotNull() {

    // Act, creating object to test constructor
    final OrderActionBean actual = new OrderActionBean();

    // Assert result
    assertThat(actual).isNotNull().isNotNull();
    assertThat(actual.getContext()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void isConfirmedOutputFalse() {

    // Arrange
    final OrderActionBean orderActionBean = new OrderActionBean();

    // Act and Assert result
    assertThat(orderActionBean.isConfirmed()).isFalse();

  }
}


// Node: getOrderListOutputNull
// Node: OrderActionBean
// Node: isShippingAddressRequiredOutputFalse
// Node: isConfirmedOutputFalse
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

class CatalogActionBeanTest {

  @Test
  void getItemListOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getItemList()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getProductListOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getProductList()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getCategoryListOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getCategoryList()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getItemOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getItem()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getProductOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getProduct()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getCategoryOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getCategory()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getItemIdOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getItemId()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getProductIdOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getProductId()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getCategoryIdOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getCategoryId()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void getKeywordOutputNull() {

    // Arrange
    final CatalogActionBean catalogActionBean = new CatalogActionBean();

    // Act and Assert result
    assertThat(catalogActionBean.getKeyword()).isNull();

  }

  // Test written by Diffblue Cover.
  @Test
  void constructorOutputNotNull() {

    // Act, creating object to test constructor
    final CatalogActionBean actual = new CatalogActionBean();

    // Assert result
    assertThat(actual).isNotNull();
    assertThat(actual.getContext()).isNull();

  }
}


// Node: getProductIdOutputNull
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
import java.util.Iterator;

import org.junit.jupiter.api.Test;

class CartTest {

  @Test
  void addItemWhenIsInStockIsTrue() {
    // given
    Cart cart = new Cart();
    Item item = new Item();
    item.setItemId("I01");
    item.setListPrice(new BigDecimal("2.05"));

    // when
    cart.addItem(item, true);
    cart.addItem(item, true);

    // then
    assertThat(cart.getCartItemList().get(0).getItem()).isSameAs(item);
    assertThat(cart.getCartItemList().get(0).isInStock()).isTrue();
    assertThat(cart.getCartItemList().get(0).getQuantity()).isEqualTo(2);
    assertThat(cart.getCartItemList().get(0).getTotal()).isEqualTo(new BigDecimal("4.10"));
    assertThat(cart.containsItemId("I01")).isTrue();
    assertThat(cart.getNumberOfItems()).isEqualTo(1);
    {
      Iterator<CartItem> cartItems = cart.getCartItems();
      assertThat(cartItems.next()).isNotNull();
      assertThat(cartItems.hasNext()).isFalse();
    }
    {
      Iterator<CartItem> cartItems = cart.getAllCartItems();
      assertThat(cartItems.next()).isNotNull();
      assertThat(cartItems.hasNext()).isFalse();
    }
  }

  @Test
  void addItemWhenIsInStockIsFalse() {
    // given
    Cart cart = new Cart();
    Item item = new Item();
    item.setItemId("I01");
    item.setListPrice(new BigDecimal("2.05"));

    // when
    cart.addItem(item, false);

    // then
    assertThat(cart.getCartItemList().get(0).getItem()).isSameAs(item);
    assertThat(cart.getCartItemList().get(0).isInStock()).isFalse();
    assertThat(cart.getCartItemList().get(0).getQuantity()).isEqualTo(1);
    assertThat(cart.getCartItemList().get(0).getTotal()).isEqualTo(new BigDecimal("2.05"));
  }

  @Test
  void removeItemByIdWhenItemNotFound() {
    // given
    Cart cart = new Cart();

    // when
    Item item = cart.removeItemById("I01");

    // then
    assertThat(item).isNull();
    assertThat(cart.containsItemId("I01")).isFalse();
    assertThat(cart.getNumberOfItems()).isEqualTo(0);
    assertThat(cart.getCartItems().hasNext()).isFalse();
    assertThat(cart.getAllCartItems().hasNext()).isFalse();
  }

  @Test
  void removeItemByIdWhenItemFound() {
    // given
    Cart cart = new Cart();
    Item item = new Item();
    item.setItemId("I01");
    item.setListPrice(new BigDecimal("2.05"));
    cart.addItem(item, true);

    // when
    Item removedItem = cart.removeItemById("I01");

    // then
    assertThat(removedItem).isSameAs(item);
    assertThat(cart.getCartItemList()).isEmpty();
  }

  @Test
  void incrementQuantityByItemId() {
    // given
    Cart cart = new Cart();
    Item item = new Item();
    item.setItemId("I01");
    item.setListPrice(new BigDecimal("2.05"));
    cart.addItem(item, true);

    // when
    cart.incrementQuantityByItemId("I01");
    cart.incrementQuantityByItemId("I01");

    // then
    assertThat(cart.getCartItemList().get(0).getItem()).isSameAs(item);
    assertThat(cart.getCartItemList().get(0).isInStock()).isTrue();
    assertThat(cart.getCartItemList().get(0).getQuantity()).isEqualTo(3);
    assertThat(cart.getCartItemList().get(0).getTotal()).isEqualTo(new BigDecimal("6.15"));
  }

  @Test
  void setQuantityByItemId() {
    // given
    Cart cart = new Cart();
    Item item = new Item();
    item.setItemId("I01");
    item.setListPrice(new BigDecimal("2.05"));
    cart.addItem(item, true);

    // when
    cart.setQuantityByItemId("I01", 10);

    // then
    assertThat(cart.getCartItemList().get(0).getItem()).isSameAs(item);
    assertThat(cart.getCartItemList().get(0).isInStock()).isTrue();
    assertThat(cart.getCartItemList().get(0).getQuantity()).isEqualTo(10);
    assertThat(cart.getCartItemList().get(0).getTotal()).isEqualTo(new BigDecimal("20.50"));
  }

  @Test
  void getSubTotalWhenItemIsEmpty() {
    // given
    Cart cart = new Cart();

    // when
    BigDecimal subTotal = cart.getSubTotal();

    // then
    assertThat(subTotal).isEqualTo(BigDecimal.ZERO);

  }

  @Test
  void getSubTotalWhenItemIsExist() {
    // given
    Cart cart = new Cart();
    {
      Item item = new Item();
      item.setItemId("I01");
      item.setListPrice(new BigDecimal("2.05"));
      cart.addItem(item, true);
      cart.setQuantityByItemId("I01", 5);
    }
    {
      Item item = new Item();
      item.setItemId("I02");
      item.setListPrice(new BigDecimal("3.06"));
      cart.addItem(item, true);
      cart.setQuantityByItemId("I02", 6);
    }

    // when
    BigDecimal subTotal = cart.getSubTotal();

    // then
    assertThat(subTotal).isEqualTo(new BigDecimal("28.61"));
  }

}


// Node: addItemWhenIsInStockIsTrue
// Node: addItemWhenIsInStockIsFalse
// Node: removeItemByIdWhenItemNotFound
// Node: removeItemByIdWhenItemFound
// Node: getSubTotalWhenItemIsEmpty
// Node: getSubTotalWhenItemIsExist
