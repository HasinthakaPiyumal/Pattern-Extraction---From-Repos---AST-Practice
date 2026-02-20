// Cluster 3

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

import java.util.List;

import org.mybatis.jpetstore.domain.Product;

/**
 * The Interface ProductMapper.
 *
 * @author Eduardo Macarron
 */
public interface ProductMapper {

  List<Product> getProductListByCategory(String categoryId);

  Product getProduct(String productId);

  List<Product> searchProductList(String keywords);

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/main/java/org/mybatis/jpetstore/mapper/ProductMapper.java:ProductMapper.<init>
// Node: getProductListByCategory
// Node: getProduct
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

import java.util.List;
import java.util.Map;

import org.mybatis.jpetstore.domain.Item;

/**
 * The Interface ItemMapper.
 *
 * @author Eduardo Macarron
 */
public interface ItemMapper {

  void updateInventoryQuantity(Map<String, Object> param);

  int getInventoryQuantity(String itemId);

  List<Item> getItemListByProduct(String productId);

  Item getItem(String itemId);

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/main/java/org/mybatis/jpetstore/mapper/ItemMapper.java:ItemMapper.<init>
// Node: updateInventoryQuantity
// Node: getInventoryQuantity
// Node: getItemListByProduct
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

import java.util.List;

import org.mybatis.jpetstore.domain.Order;

/**
 * The Interface OrderMapper.
 *
 * @author Eduardo Macarron
 */
public interface OrderMapper {

  List<Order> getOrdersByUsername(String username);

  Order getOrder(int orderId);

  void insertOrder(Order order);

  void insertOrderStatus(Order order);

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/main/java/org/mybatis/jpetstore/mapper/OrderMapper.java:OrderMapper.<init>
// Node: getOrdersByUsername
// Node: getOrder
// Node: insertOrder
// Node: insertOrderStatus
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

import java.util.List;

import org.mybatis.jpetstore.domain.LineItem;

/**
 * The Interface LineItemMapper.
 *
 * @author Eduardo Macarron
 */
public interface LineItemMapper {

  List<LineItem> getLineItemsByOrderId(int orderId);

  void insertLineItem(LineItem lineItem);

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/main/java/org/mybatis/jpetstore/mapper/LineItemMapper.java:LineItemMapper.<init>
// Node: getLineItemsByOrderId
// Node: insertLineItem
// Node: getAccount
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


// Node: isItemInStock
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

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.mybatis.jpetstore.domain.Item;
import org.mybatis.jpetstore.domain.Order;
import org.mybatis.jpetstore.domain.Sequence;
import org.mybatis.jpetstore.mapper.ItemMapper;
import org.mybatis.jpetstore.mapper.LineItemMapper;
import org.mybatis.jpetstore.mapper.OrderMapper;
import org.mybatis.jpetstore.mapper.SequenceMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * The Class OrderService.
 *
 * @author Eduardo Macarron
 */
@Service
public class OrderService {

  private final ItemMapper itemMapper;
  private final OrderMapper orderMapper;
  private final SequenceMapper sequenceMapper;
  private final LineItemMapper lineItemMapper;

  public OrderService(ItemMapper itemMapper, OrderMapper orderMapper, SequenceMapper sequenceMapper,
      LineItemMapper lineItemMapper) {
    this.itemMapper = itemMapper;
    this.orderMapper = orderMapper;
    this.sequenceMapper = sequenceMapper;
    this.lineItemMapper = lineItemMapper;
  }

  /**
   * Insert order.
   *
   * @param order
   *          the order
   */
  @Transactional
  public void insertOrder(Order order) {
    order.setOrderId(getNextId("ordernum"));
    order.getLineItems().forEach(lineItem -> {
      String itemId = lineItem.getItemId();
      Integer increment = lineItem.getQuantity();
      Map<String, Object> param = new HashMap<>(2);
      param.put("itemId", itemId);
      param.put("increment", increment);
      itemMapper.updateInventoryQuantity(param);
    });

    orderMapper.insertOrder(order);
    orderMapper.insertOrderStatus(order);
    order.getLineItems().forEach(lineItem -> {
      lineItem.setOrderId(order.getOrderId());
      lineItemMapper.insertLineItem(lineItem);
    });
  }

  /**
   * Gets the order.
   *
   * @param orderId
   *          the order id
   *
   * @return the order
   */
  @Transactional
  public Order getOrder(int orderId) {
    Order order = orderMapper.getOrder(orderId);
    order.setLineItems(lineItemMapper.getLineItemsByOrderId(orderId));

    order.getLineItems().forEach(lineItem -> {
      Item item = itemMapper.getItem(lineItem.getItemId());
      item.setQuantity(itemMapper.getInventoryQuantity(lineItem.getItemId()));
      lineItem.setItem(item);
    });

    return order;
  }

  /**
   * Gets the orders by username.
   *
   * @param username
   *          the username
   *
   * @return the orders by username
   */
  public List<Order> getOrdersByUsername(String username) {
    return orderMapper.getOrdersByUsername(username);
  }

  /**
   * Gets the next id.
   *
   * @param name
   *          the name
   *
   * @return the next id
   */
  public int getNextId(String name) {
    Sequence sequence = sequenceMapper.getSequence(new Sequence(name, -1));
    if (sequence == null) {
      throw new RuntimeException(
          "Error: A null sequence was returned from the database (could not get next " + name + " sequence).");
    }
    Sequence parameterObject = new Sequence(name, sequence.getNextId() + 1);
    sequenceMapper.updateSequence(parameterObject);
    return sequence.getNextId();
  }

}


// Node: getLineItems
// Node: forEach
// Node: put
// Node: setLineItems
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


// Node: setProductId
// Node: viewMain
// Node: ForwardResolution
// Node: viewCategory
// Node: viewProduct
// Node: viewItem
// Node: setMessage
// Node: clear
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


// Node: setCart
// Node: trim
// Node: isEmpty
// Node: getRequest
// Node: viewCart
// Node: checkOut
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


// Node: newAccountForm
// Node: newAccount
// Node: RedirectResolution
// Node: editAccountForm
// Node: signonForm
// Node: signon
// Node: getSession
// Node: setAttribute
// Node: signoff
// Node: invalidate
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

import java.io.Serializable;

import net.sourceforge.stripes.action.ActionBean;
import net.sourceforge.stripes.action.ActionBeanContext;
import net.sourceforge.stripes.action.SimpleMessage;

/**
 * The Class AbstractActionBean.
 *
 * @author Eduardo Macarron
 */
public abstract class AbstractActionBean implements ActionBean, Serializable {

  private static final long serialVersionUID = -1767714708233127983L;

  protected static final String ERROR = "/WEB-INF/jsp/common/Error.jsp";

  protected transient ActionBeanContext context;

  protected void setMessage(String value) {
    context.getMessages().add(new SimpleMessage(value));
  }

  @Override
  public ActionBeanContext getContext() {
    return context;
  }

  @Override
  public void setContext(ActionBeanContext context) {
    this.context = context;
  }

}


// Node: getMessages
// Node: add
// Node: SimpleMessage
// Node: setContext
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


// Node: isConfirmed
// Node: listOrders
// Node: getAttribute
// Node: newOrderForm
// Node: order
// Node: newOrder
// Node: viewOrder
// Node: LineItem
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


// Node: addLineItem
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


// Node: shouldReturnOrderWhenGivenOrderIdWithOutLineItems
// Node: when
// Node: thenReturn
// Node: shouldReturnOrderWhenGivenOrderIdExistedLineItems
// Node: shouldReturnOrderList
// Node: isSameAs
// Node: shouldCallTheMapperToInsert
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


// Node: shouldCallTheSearchMapperTwice
// Node: Product
// Node: shouldReturnCategoryList
// Node: shouldReturnCategory
// Node: Category
// Node: shouldReturnProduct
// Node: shouldReturnProductList
// Node: shouldReturnItemList
// Node: shouldReturnItem
// Node: shouldReturnTrueWhenExistStock
// Node: shouldReturnFalseWhenNotExistStock
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


// Node: shouldCallTheMapperToGetAccountAnUsername
// Node: shouldCallTheMapperToGetAccountAnUsernameAndPassword
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
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.ArrayList;

import net.sourceforge.stripes.action.ActionBeanContext;
import net.sourceforge.stripes.action.Message;
import net.sourceforge.stripes.action.Resolution;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mybatis.jpetstore.domain.Cart;

class CartActionBeanTest {

    private CartActionBean cartActionBean;
    private ActionBeanContext mockContext;

    @BeforeEach
    void setUp() {
        cartActionBean = new CartActionBean();
        cartActionBean.setCart(new Cart());

        // Mock ActionBeanContext to avoid NPE in setMessage()
        mockContext = mock(ActionBeanContext.class);
        when(mockContext.getMessages()).thenReturn(new ArrayList<Message>());
        cartActionBean.setContext(mockContext);
    }

    @Test
    void constructorOutputNotNull() {
        final CartActionBean actual = new CartActionBean();

        assertThat(actual).isNotNull();
        assertThat(actual.getCart()).isNotNull();
        assertThat(actual.getContext()).isNull();
    }

    @Test
    void getCartOutputNotNull() {
        final CartActionBean bean = new CartActionBean();

        assertThat(bean.getCart()).isNotNull();
    }

    @Test
    void addItemToCart_WithNullWorkingItemId_ShouldReturnError() {
        cartActionBean.setWorkingItemId(null);

        Resolution resolution = cartActionBean.addItemToCart();

        assertThat(resolution).isNotNull();
        assertThat(resolution.toString()).contains("Error.jsp");
    }

    @Test
    void addItemToCart_WithEmptyWorkingItemId_ShouldReturnError() {
        cartActionBean.setWorkingItemId("");

        Resolution resolution = cartActionBean.addItemToCart();

        assertThat(resolution).isNotNull();
        assertThat(resolution.toString()).contains("Error.jsp");
    }

    @Test
    void addItemToCart_WithBlankWorkingItemId_ShouldReturnError() {
        cartActionBean.setWorkingItemId("   ");

        Resolution resolution = cartActionBean.addItemToCart();

        assertThat(resolution).isNotNull();
        assertThat(resolution.toString()).contains("Error.jsp");
    }

    @Test
    void removeItemFromCart_WithNullWorkingItemId_ShouldReturnError() {
        cartActionBean.setWorkingItemId(null);

        Resolution resolution = cartActionBean.removeItemFromCart();

        assertThat(resolution).isNotNull();
        assertThat(resolution.toString()).contains("Error.jsp");
    }

    @Test
    void removeItemFromCart_WithEmptyWorkingItemId_ShouldReturnError() {
        cartActionBean.setWorkingItemId("");

        Resolution resolution = cartActionBean.removeItemFromCart();

        assertThat(resolution).isNotNull();
        assertThat(resolution.toString()).contains("Error.jsp");
    }

    @Test
    void removeItemFromCart_WithBlankWorkingItemId_ShouldReturnError() {
        cartActionBean.setWorkingItemId("   ");

        Resolution resolution = cartActionBean.removeItemFromCart();

        assertThat(resolution).isNotNull();
        assertThat(resolution.toString()).contains("Error.jsp");
    }

    @Test
    void removeItemFromCart_WithNonExistentItem_ShouldReturnError() {
        cartActionBean.setWorkingItemId("NON_EXISTENT_ITEM");

        Resolution resolution = cartActionBean.removeItemFromCart();

        assertThat(resolution).isNotNull();
        assertThat(resolution.toString()).contains("Error.jsp");
    }

    @Test
    void clearShouldResetCartAndWorkingItemId() {
        cartActionBean.setWorkingItemId("EST-1");

        cartActionBean.clear();

        assertThat(cartActionBean.getCart()).isNotNull();
        assertThat(cartActionBean.getCart().getNumberOfItems()).isZero();
    }
}


// Node: setUp
// Node: mock
