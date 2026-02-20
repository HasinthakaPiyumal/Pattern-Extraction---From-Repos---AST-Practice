// Cluster 21

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

import org.mybatis.jpetstore.domain.Category;

/**
 * The Interface CategoryMapper.
 *
 * @author Eduardo Macarron
 */
public interface CategoryMapper {

  List<Category> getCategoryList();

  Category getCategory(String categoryId);

}


// Node: repos/cloned_ms_repos/jpetstore-6/src/main/java/org/mybatis/jpetstore/mapper/CategoryMapper.java:CategoryMapper.<init>
// Node: getCategoryList
// Node: getCategory
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


// Node: getKeyword
// Node: getProductList
// Node: getItemList
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


// Node: getCart
// Node: setWorkingItemId
// Node: addItemToCart
// Node: removeItemFromCart
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


// Node: getMyList
// Node: isAuthenticated
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


// Node: getContext
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


// Node: toString
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


// Node: isNull
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


// Node: constructorOutputNotNull
// Node: isNotNull
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


// Node: getMyListOutputNull
// Node: AccountActionBean
// Node: getPasswordOutputNull
// Node: isAuthenticatedOutputFalse
// Node: getUsernameOutputNull
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


// Node: getItemListOutputNull
// Node: CatalogActionBean
// Node: getProductListOutputNull
// Node: getCategoryListOutputNull
// Node: getItemOutputNull
// Node: getProductOutputNull
// Node: getCategoryOutputNull
// Node: getItemIdOutputNull
// Node: getCategoryIdOutputNull
// Node: getKeywordOutputNull
// Node: CartActionBean
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


// Node: getCartOutputNotNull
// Node: addItemToCart_WithNullWorkingItemId_ShouldReturnError
// Node: contains
// Node: addItemToCart_WithEmptyWorkingItemId_ShouldReturnError
// Node: addItemToCart_WithBlankWorkingItemId_ShouldReturnError
// Node: removeItemFromCart_WithNullWorkingItemId_ShouldReturnError
// Node: removeItemFromCart_WithEmptyWorkingItemId_ShouldReturnError
// Node: removeItemFromCart_WithBlankWorkingItemId_ShouldReturnError
// Node: removeItemFromCart_WithNonExistentItem_ShouldReturnError
// Node: clearShouldResetCartAndWorkingItemId
// Node: isZero
