// Cluster 14

// Node: get
//
// COPYRIGHT LICENSE: This information contains sample code provided in source code form. You may copy, 
// modify, and distribute these sample programs in any form without payment to IBM for the purposes of 
// developing, using, marketing or distributing application programs conforming to the application 
// programming interface for the operating platform for which the sample code is written. 
// Notwithstanding anything to the contrary, IBM PROVIDES THE SAMPLE SOURCE CODE ON AN "AS IS" BASIS 
// AND IBM DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED 
// WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY, FITNESS FOR A PARTICULAR PURPOSE, 
// TITLE, AND ANY WARRANTY OR CONDITION OF NON-INFRINGEMENT. IBM SHALL NOT BE LIABLE FOR ANY DIRECT, 
// INDIRECT, INCIDENTAL, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR OPERATION OF THE 
// SAMPLE SOURCE CODE. IBM HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS 
// OR MODIFICATIONS TO THE SAMPLE SOURCE CODE.  
//
// (C) COPYRIGHT International Business Machines Corp., 2001,2011
// All Rights Reserved * Licensed Materials - Property of IBM
//
package com.ibm.websphere.samples.pbw.bean;

import java.io.Serializable;
import java.util.Vector;

import javax.enterprise.context.Dependent;
import javax.persistence.EntityManager;
import javax.persistence.LockModeType;
import javax.persistence.PersistenceContext;
import javax.persistence.Query;

import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * The CatalogMgr provides transactional access to the catalog of items the store is willing to sell
 * to customers.
 * 
 * @see com.ibm.websphere.samples.pbw.jpa.Inventory
 */
@Dependent
@SuppressWarnings("unchecked")
public class CatalogMgr implements Serializable {
	@PersistenceContext(unitName = "PBW")
	EntityManager em;

	/**
	 * Get all inventory items.
	 *
	 * @return Vector of Inventorys. / public Vector<Inventory> getItems() { Vector<Inventory> items
	 *         = new Vector<Inventory>(); int count = Util.getCategoryStrings().length; for (int i =
	 *         0; i < count; i++) { items.addAll(getItemsByCategory(i)); } return items; }
	 */

	/**
	 * Get all inventory items for the given category.
	 *
	 * @param category
	 *            of items desired.
	 * @return Vector of Inventory.
	 */
	public Vector<Inventory> getItemsByCategory(int category) {
		Query q = em.createNamedQuery("getItemsByCategory");
		q.setParameter("category", category);
		// The return type must be Vector because the PBW client ActiveX sample requires Vector
		return new Vector<Inventory>(q.getResultList());
	}

	/**
	 * Get inventory items that contain a given String within their names.
	 *
	 * @param name
	 *            String to search names for.
	 * @return A Vector of Inventorys that match. / public Vector<Inventory> getItemsLikeName(String
	 *         name) { Query q = em.createNamedQuery("getItemsLikeName"); q.setParameter("name", '%'
	 *         + name + '%'); //The return type must be Vector because the PBW client ActiveX sample
	 *         requires Vector return new Vector<Inventory>(q.getResultList()); }
	 */

	/**
	 * Get the StoreItem for the given ID.
	 *
	 * @param inventoryID
	 *            - ID of the Inventory item desired.
	 * @return StoreItem / public StoreItem getItem(String inventoryID) { return new
	 *         StoreItem(getItemInventory(inventoryID)); }
	 */

	/**
	 * Get the Inventory item for the given ID.
	 *
	 * @param inventoryID
	 *            - ID of the Inventory item desired.
	 * @return Inventory
	 */
	public Inventory getItemInventory(String inventoryID) {
		Inventory si = null;
		Util.debug("getItemInventory id=" + inventoryID);
		si = em.find(Inventory.class, inventoryID);
		return si;
	}

	/**
	 * Add an inventory item.
	 *
	 * @param item
	 *            The Inventory to add.
	 * @return True, if item added.
	 */
	public boolean addItem(Inventory item) {
		boolean retval = true;
		Util.debug("addItem " + item.getInventoryId());
		em.persist(item);
		em.flush();
		return retval;
	}

	/**
	 * Add an StoreItem item (same as Inventory item).
	 *
	 * @param item
	 *            The StoreItem to add.
	 * @return True, if item added. / public boolean addItem(StoreItem item) { return addItem(new
	 *         Inventory(item)); }
	 */

	/**
	 * Delete an inventory item.
	 *
	 * @param inventoryID
	 *            The ID of the inventory item to delete.
	 * @return True, if item deleted. / public boolean deleteItem(String inventoryID) { boolean
	 *         retval = true; em.remove(em.find(Inventory.class, inventoryID)); return retval; }
	 */

	/**
	 * Get the image for the inventory item.
	 * 
	 * @param inventoryID
	 *            The id of the inventory item wanted.
	 * @return Buffer containing the image.
	 */
	public byte[] getItemImageBytes(String inventoryID) {
		byte[] retval = null;
		Inventory inv = getInv(inventoryID);
		if (inv != null) {
			retval = inv.getImgbytes();
		}

		return retval;
	}

	/**
	 * Set the image for the inventory item.
	 * 
	 * @param inventoryID
	 *            The id of the inventory item wanted.
	 * @param imgbytes
	 *            Buffer containing the image.
	 */
	public void setItemImageBytes(String inventoryID, byte[] imgbytes) {
		Inventory inv = getInvUpdate(inventoryID);
		if (inv != null) {
			inv.setImgbytes(imgbytes);
		}
	}

	/**
	 * Set the inventory item's quantity.
	 *
	 * @param inventoryID
	 *            The inventory item's ID.
	 * @param quantity
	 *            The inventory item's new quantity.
	 */
	public void setItemQuantity(String inventoryID, int quantity) {
		Inventory inv = getInvUpdate(inventoryID);
		if (inv != null) {
			inv.setQuantity(quantity);
		}
	}

	/**
	 * Get a remote Inventory object.
	 *
	 * @param inventoryID
	 *            The id of the inventory item wanted.
	 * @return Reference to the remote Inventory object.
	 */
	private Inventory getInv(String inventoryID) {
		return em.find(Inventory.class, inventoryID);
	}

	/**
	 * Get a remote Inventory object to Update.
	 *
	 * @param inventoryID
	 *            The id of the inventory item wanted.
	 * @return Reference to the remote Inventory object.
	 */
	private Inventory getInvUpdate(String inventoryID) {
		Inventory inv = null;
		inv = em.find(Inventory.class, inventoryID);
		em.lock(inv, LockModeType.OPTIMISTIC_FORCE_INCREMENT);
		em.refresh(inv);
		return inv;
	}

}


// Node: getItem
// Node: StoreItem
// Node: getItemInventory
// Node: getCurrentInstance
//
// COPYRIGHT LICENSE: This information contains sample code provided in source code form. You may copy, 
// modify, and distribute these sample programs in any form without payment to IBM for the purposes of 
// developing, using, marketing or distributing application programs conforming to the application 
// programming interface for the operating platform for which the sample code is written. 
// Notwithstanding anything to the contrary, IBM PROVIDES THE SAMPLE SOURCE CODE ON AN "AS IS" BASIS 
// AND IBM DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED 
// WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY, FITNESS FOR A PARTICULAR PURPOSE, 
// TITLE, AND ANY WARRANTY OR CONDITION OF NON-INFRINGEMENT. IBM SHALL NOT BE LIABLE FOR ANY DIRECT, 
// INDIRECT, INCIDENTAL, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR OPERATION OF THE 
// SAMPLE SOURCE CODE. IBM HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS 
// OR MODIFICATIONS TO THE SAMPLE SOURCE CODE.  
//
// (C) COPYRIGHT International Business Machines Corp., 2001,2011
// All Rights Reserved * Licensed Materials - Property of IBM
//

package com.ibm.websphere.samples.pbw.war;

import java.io.Serializable;
import java.text.NumberFormat;
import java.util.Locale;
import java.util.Objects;

import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Provides backing bean support for the product web page. Accessed via the shopping bean.
 *
 */
public class ProductBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private Inventory inventory;
	private int quantity;

	protected ProductBean(Inventory inventory) {
	    Objects.requireNonNull(inventory, "Inventory cannot be null");
		this.inventory = inventory;
		this.quantity = 1;
	}

	public String getCategoryName() {
		return Util.getCategoryString(this.inventory.getCategory());
	}

	public Inventory getInventory() {
		return this.inventory;
	}

	public String getMenuString() {
		String categoryString = getCategoryName();

		if (categoryString.equals("Flowers")) {
			return "banner:menu1";
		}

		else if (categoryString.equals("Fruits & Vegetables")) {
			return "banner:menu2";
		}

		else if (categoryString.equals("Trees")) {
			return "banner:menu3";
		}

		else {
			return "banner:menu4";
		}
	}

	public String getPrice() {
		return NumberFormat.getCurrencyInstance(Locale.US).format(new Float(this.inventory.getPrice()));
	}

	public int getQuantity() {
		return this.quantity;
	}

	public void setQuantity(int quantity) {
		this.quantity = quantity;
	}
}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/ProductBean.java:ProductBean.<init>
// Node: ProductBean
// Node: requireNonNull
//
// COPYRIGHT LICENSE: This information contains sample code provided in source code form. You may copy, 
// modify, and distribute these sample programs in any form without payment to IBM for the purposes of 
// developing, using, marketing or distributing application programs conforming to the application 
// programming interface for the operating platform for which the sample code is written. 
// Notwithstanding anything to the contrary, IBM PROVIDES THE SAMPLE SOURCE CODE ON AN "AS IS" BASIS 
// AND IBM DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED 
// WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY, FITNESS FOR A PARTICULAR PURPOSE, 
// TITLE, AND ANY WARRANTY OR CONDITION OF NON-INFRINGEMENT. IBM SHALL NOT BE LIABLE FOR ANY DIRECT, 
// INDIRECT, INCIDENTAL, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR OPERATION OF THE 
// SAMPLE SOURCE CODE. IBM HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS 
// OR MODIFICATIONS TO THE SAMPLE SOURCE CODE.  
//
// (C) COPYRIGHT International Business Machines Corp., 2003,2011
// All Rights Reserved * Licensed Materials - Property of IBM
//

package com.ibm.websphere.samples.pbw.war;

import javax.faces.application.FacesMessage;
import javax.faces.component.UIComponent;
import javax.faces.context.FacesContext;
import javax.faces.validator.ValidatorException;

/**
 * Simple helper class for JSF validators to handle error messages.
 *
 */
public class ValidatorUtils {
	protected static void addErrorMessage(FacesContext context, String message) {
		FacesMessage facesMessage = new FacesMessage();
		facesMessage.setDetail(message);
		facesMessage.setSummary(message);
		facesMessage.setSeverity(FacesMessage.SEVERITY_ERROR);
		throw new ValidatorException(facesMessage);
	}

	protected static void addErrorMessage(FacesContext context, UIComponent component) {
		String errorMessage = (String) component.getAttributes().get("errorMessage");

		addErrorMessage(context, errorMessage);
	}
}


// Node: addErrorMessage
// Node: FacesMessage
// Node: setDetail
// Node: setSummary
// Node: setSeverity
// Node: ValidatorException
// Node: getAttributes
//
// COPYRIGHT LICENSE: This information contains sample code provided in source code form. You may copy, 
// modify, and distribute these sample programs in any form without payment to IBM for the purposes of 
// developing, using, marketing or distributing application programs conforming to the application 
// programming interface for the operating platform for which the sample code is written. 
// Notwithstanding anything to the contrary, IBM PROVIDES THE SAMPLE SOURCE CODE ON AN "AS IS" BASIS 
// AND IBM DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED 
// WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY, FITNESS FOR A PARTICULAR PURPOSE, 
// TITLE, AND ANY WARRANTY OR CONDITION OF NON-INFRINGEMENT. IBM SHALL NOT BE LIABLE FOR ANY DIRECT, 
// INDIRECT, INCIDENTAL, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR OPERATION OF THE 
// SAMPLE SOURCE CODE. IBM HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS 
// OR MODIFICATIONS TO THE SAMPLE SOURCE CODE.  
//
// (C) COPYRIGHT International Business Machines Corp., 2003,2011
// All Rights Reserved * Licensed Materials - Property of IBM
//

package com.ibm.websphere.samples.pbw.war;

import javax.faces.component.UIComponent;
import javax.faces.component.UIInput;
import javax.faces.context.FacesContext;
import javax.faces.validator.FacesValidator;
import javax.faces.validator.Validator;
import javax.faces.validator.ValidatorException;

/**
 * A JSF validator class, not implemented in Bean Validation since validation is only required
 * during GUI interaction.
 */
@FacesValidator(value = "validatePasswords")
public class ValidatePasswords implements Validator {

	@Override
	public void validate(FacesContext context, UIComponent component, Object value) throws ValidatorException {
		UIInput otherComponent;
		String otherID = (String) component.getAttributes().get("otherPasswordID");
		String otherStr;
		String str = (String) value;

		otherComponent = (UIInput) context.getViewRoot().findComponent(otherID);
		otherStr = (String) otherComponent.getValue();

		if (!otherStr.equals(str)) {
			ValidatorUtils.addErrorMessage(context, "Passwords do not match.");
		}
	}

}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/ValidatePasswords.java:ValidatePasswords.<init>
// Node: FacesValidator
// Node: validate
// Node: getViewRoot
// Node: findComponent
//
// COPYRIGHT LICENSE: This information contains sample code provided in source code form. You may copy, 
// modify, and distribute these sample programs in any form without payment to IBM for the purposes of 
// developing, using, marketing or distributing application programs conforming to the application 
// programming interface for the operating platform for which the sample code is written. 
// Notwithstanding anything to the contrary, IBM PROVIDES THE SAMPLE SOURCE CODE ON AN "AS IS" BASIS 
// AND IBM DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, ANY IMPLIED 
// WARRANTIES OR CONDITIONS OF MERCHANTABILITY, SATISFACTORY QUALITY, FITNESS FOR A PARTICULAR PURPOSE, 
// TITLE, AND ANY WARRANTY OR CONDITION OF NON-INFRINGEMENT. IBM SHALL NOT BE LIABLE FOR ANY DIRECT, 
// INDIRECT, INCIDENTAL, SPECIAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR OPERATION OF THE 
// SAMPLE SOURCE CODE. IBM HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES, ENHANCEMENTS 
// OR MODIFICATIONS TO THE SAMPLE SOURCE CODE.  
//
// (C) COPYRIGHT International Business Machines Corp., 2001,2011
// All Rights Reserved * Licensed Materials - Property of IBM
//
package com.ibm.websphere.samples.pbw.war;

import java.io.Serializable;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedList;
import java.util.Locale;
import java.util.Map;
import java.util.Vector;

import javax.enterprise.context.SessionScoped;
import javax.faces.context.ExternalContext;
import javax.faces.context.FacesContext;
import javax.inject.Inject;
import javax.inject.Named;

import com.ibm.websphere.samples.pbw.bean.CatalogMgr;
import com.ibm.websphere.samples.pbw.bean.ShoppingCartBean;
import com.ibm.websphere.samples.pbw.jpa.Inventory;

/**
 * A combination JSF action bean and backing bean for the shopping web page.
 *
 */
@Named(value = "shopping")
@SessionScoped
public class ShoppingBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private static final String ACTION_CART = "cart";
	private static final String ACTION_PRODUCT = "product";
	private static final String ACTION_SHOPPING = "shopping";

	// keep an independent list of items so we can add pricing methods
	private ArrayList<ShoppingItem> cartItems;

	@Inject
	private CatalogMgr catalog;

	private ProductBean product;
	private LinkedList<ProductBean> products;
	private float shippingCost;

	@Inject
	private ShoppingCartBean shoppingCart;

	public String performAddToCart() {
		Inventory item = new Inventory(this.product.getInventory());

		item.setQuantity(this.product.getQuantity());

		shoppingCart.addItem(item);

		return performCart();
	}

	public String performCart() {
		cartItems = wrapInventoryItems(shoppingCart.getItems());

		return ShoppingBean.ACTION_CART;
	}

	public String performProductDetail() {
		FacesContext facesContext = FacesContext.getCurrentInstance();
		ExternalContext externalContext = facesContext.getExternalContext();
		Map<String, String> requestParams = externalContext.getRequestParameterMap();

		this.product = new ProductBean(this.catalog.getItemInventory(requestParams.get("itemID")));

		return ShoppingBean.ACTION_PRODUCT;
	}

	public String performRecalculate() {

		shoppingCart.removeZeroQuantityItems();

		this.cartItems = wrapInventoryItems(shoppingCart.getItems());

		return performCart();
	}

	public String performShopping() {
		int category = 0;
		FacesContext facesContext = FacesContext.getCurrentInstance();
		ExternalContext externalContext = facesContext.getExternalContext();
		Vector<Inventory> inventories;
		Map<String, String> requestParams = externalContext.getRequestParameterMap();

		try {
			category = Integer.parseInt(requestParams.get("category"));
		}

		catch (Throwable e) {
			if (this.products != null) {
				// No category specified, so just use the last one.

				return ShoppingBean.ACTION_SHOPPING;
			}
		}

		inventories = this.catalog.getItemsByCategory(category);

		this.products = new LinkedList<ProductBean>();

		// Have to convert all the inventory objects into product beans.

		for (Object obj : inventories) {
			Inventory inventory = (Inventory) obj;

			if (inventory.isPublic()) {
				this.products.add(new ProductBean(inventory));
			}
		}

		return ShoppingBean.ACTION_SHOPPING;
	}

	public Collection<ShoppingItem> getCartItems() {
		return this.cartItems;
	}

	public ProductBean getProduct() {
		return this.product;
	}

	public Collection<ProductBean> getProducts() {
		return this.products;
	}

	public String getShippingCostString() {
		return NumberFormat.getCurrencyInstance(Locale.US).format(this.shippingCost);
	}

	/**
	 * @return the shippingCost
	 */
	public float getShippingCost() {
		return shippingCost;
	}

	public void setShippingCost(float shippingCost) {
		this.shippingCost = shippingCost;

	}

	public float getTotalCost() {
		return shoppingCart.getSubtotalCost() + this.shippingCost;
	}

	public String getTotalCostString() {
		return NumberFormat.getCurrencyInstance(Locale.US).format(getTotalCost());
	}

	public ShoppingCartBean getCart() {
		return shoppingCart;
	}

	private ArrayList<ShoppingItem> wrapInventoryItems(Collection<Inventory> invItems) {
		ArrayList<ShoppingItem> shoppingList = new ArrayList<ShoppingItem>();
		for (Inventory i : invItems) {
			shoppingList.add(new ShoppingItem(i));
		}
		return shoppingList;
	}
}


// Node: performProductDetail
// Node: getExternalContext
// Node: getRequestParameterMap
// Node: performShopping
