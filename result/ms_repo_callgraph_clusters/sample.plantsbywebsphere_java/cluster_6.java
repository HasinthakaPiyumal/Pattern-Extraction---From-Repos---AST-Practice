// Cluster 6

// Node: find
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
package com.ibm.websphere.samples.pbw.bean;

import java.io.Serializable;
import java.util.Collection;

import javax.annotation.security.RolesAllowed;
import javax.enterprise.context.Dependent;
import javax.persistence.EntityManager;
import javax.persistence.NoResultException;
import javax.persistence.PersistenceContext;
import javax.persistence.Query;

import com.ibm.websphere.samples.pbw.jpa.BackOrder;
import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * The BackOrderMgr provides a transactional and secured facade to access back order information.
 * This bean no longer requires an interface as there is one and only one implementation.
 */
@Dependent
@RolesAllowed("SampAdmin")
public class BackOrderMgr implements Serializable {
	@PersistenceContext(unitName = "PBW")
	private EntityManager em;

	/**
	 * Method createBackOrder.
	 * 
	 * @param inventoryID
	 * @param amountToOrder
	 * @param maximumItems
	 */
	public void createBackOrder(String inventoryID, int amountToOrder, int maximumItems) {
		try {
			Util.debug("BackOrderMgr.createBackOrder() - Entered");
			BackOrder backOrder = null;
			try {
				// See if there is already an existing backorder and increase
				// the order quantity
				// but only if it has not been sent to the supplier.
				Query q = em.createNamedQuery("findByInventoryID");
				q.setParameter("id", inventoryID);
				backOrder = (BackOrder) q.getSingleResult();
				if (!(backOrder.getStatus().equals(Util.STATUS_ORDERSTOCK))) {
					Util.debug("BackOrderMgr.createBackOrder() - Backorders found but have already been ordered from the supplier");
					// throw new FinderException();
				}
				// Increase the BackOrder quantity for an existing Back Order.
				backOrder.setQuantity(backOrder.getQuantity() + amountToOrder);
			} catch (NoResultException e) {
				Util.debug("BackOrderMgr.createBackOrder() - BackOrder doesn't exist." + e);
				Util.debug("BackOrderMgr.createBackOrder() - Creating BackOrder for InventoryID: " + inventoryID);
				// Order enough stock from the supplier to reach the maximum
				// threshold and to
				// satisfy the back order.
				amountToOrder = maximumItems + amountToOrder;
				Inventory inv = em.find(Inventory.class, inventoryID);
				BackOrder b = new BackOrder(inv, amountToOrder);
				em.persist(b);
			}
		} catch (Exception e) {
			Util.debug("BackOrderMgr.createBackOrder() - Exception: " + e);
		}
	}

	/**
	 * Method findBackOrderItems.
	 * 
	 * @return Collection
	 */
	@SuppressWarnings("unchecked")
	public Collection<BackOrder> findBackOrders() {
		Query q = em.createNamedQuery("findAllBackOrders");
		return q.getResultList();
	}

	/**
	 * Method deleteBackOrder.
	 * 
	 * @param backOrderID
	 */
	public void deleteBackOrder(String backOrderID) {
		Util.debug("BackOrderMgr.deleteBackOrder() - Entered");
		// BackOrderLocal backOrder =
		// getBackOrderLocalHome().findByPrimaryKeyUpdate(backOrderID);
		BackOrder backOrder = em.find(BackOrder.class, backOrderID);
		em.remove(backOrder);
	}

	/**
	 * Method receiveConfirmation.
	 * 
	 * @param backOrderID
	 *            / public int receiveConfirmation(String backOrderID) { int rc = 0; BackOrder
	 *            backOrder; Util.debug(
	 *            "BackOrderMgr.receiveConfirmation() - Finding Back Order for backOrderID=" +
	 *            backOrderID); backOrder = em.find(BackOrder.class, backOrderID);
	 *            backOrder.setStatus(Util.STATUS_RECEIVEDSTOCK); Util.debug(
	 *            "BackOrderMgr.receiveConfirmation() - Updating status(" +
	 *            Util.STATUS_RECEIVEDSTOCK + ") of backOrderID(" + backOrderID + ")"); return (rc);
	 *            }
	 */

	/**
	 * Method orderStock.
	 * 
	 * @param backOrderID
	 * @param quantity
	 *            / public void orderStock(String backOrderID, int quantity) {
	 *            this.setBackOrderStatus(backOrderID, Util.STATUS_ORDEREDSTOCK);
	 *            this.setBackOrderQuantity(backOrderID, quantity);
	 *            this.setBackOrderOrderDate(backOrderID); }
	 */

	/**
	 * Method updateStock.
	 * 
	 * @param backOrderID
	 * @param quantity
	 */
	public void updateStock(String backOrderID, int quantity) {
		this.setBackOrderStatus(backOrderID, Util.STATUS_ADDEDSTOCK);
	}

	/**
	 * @param backOrderID
	 *            / public void abortorderStock(String backOrderID) { Util.debug(
	 *            "backOrderStockBean.abortorderStock() - Aborting orderStock transation for backorderID: "
	 *            + backOrderID); // Reset the back order status since the order failed.
	 *            this.setBackOrderStatus(backOrderID, Util.STATUS_ORDERSTOCK); }
	 */

	/**
	 * Method getBackOrderID.
	 * 
	 * @param backOrderID
	 * @return String / public String getBackOrderID(String backOrderID) { String retbackOrderID =
	 *         ""; Util.debug( "BackOrderMgr.getBackOrderID() - Entered"); // BackOrderLocal
	 *         backOrder = getBackOrderLocalHome().findByPrimaryKey(new BackOrderKey(backOrderID));
	 *         BackOrder backOrder = em.find(BackOrder.class, backOrderID); retbackOrderID =
	 *         backOrder.getBackOrderID(); return retbackOrderID; }
	 */

	/**
	 * Method getBackOrderInventoryID.
	 * 
	 * @param backOrderID
	 * @return String
	 */
	public String getBackOrderInventoryID(String backOrderID) {
		String retinventoryID = "";

		Util.debug("BackOrderMgr.getBackOrderID() - Entered");
		// BackOrderLocal backOrder =
		// getBackOrderLocalHome().findByPrimaryKey(new
		// BackOrderKey(backOrderID));
		BackOrder backOrder = em.find(BackOrder.class, backOrderID);
		retinventoryID = backOrder.getInventory().getInventoryId();

		return retinventoryID;
	}

	/**
	 * Method getBackOrderQuantity.
	 * 
	 * @param backOrderID
	 * @return int
	 */
	public int getBackOrderQuantity(String backOrderID) {
		int backOrderQuantity = -1;
		Util.debug("BackOrderMgr.getBackOrderQuantity() - Entered");
		// BackOrderLocal backOrder =
		// getBackOrderLocalHome().findByPrimaryKey(new
		// BackOrderKey(backOrderID));
		BackOrder backOrder = em.find(BackOrder.class, backOrderID);
		backOrderQuantity = backOrder.getQuantity();
		return backOrderQuantity;
	}

	/**
	 * Method setBackOrderQuantity.
	 * 
	 * @param backOrderID
	 * @param quantity
	 */
	public void setBackOrderQuantity(String backOrderID, int quantity) {
		Util.debug("BackOrderMgr.setBackOrderQuantity() - Entered");
		// BackOrderLocal backOrder =
		// getBackOrderLocalHome().findByPrimaryKeyUpdate(backOrderID);
		BackOrder backOrder = em.find(BackOrder.class, backOrderID);
		backOrder.setQuantity(quantity);
	}

	/**
	 * Method setBackOrderStatus.
	 * 
	 * @param backOrderID
	 * @param Status
	 */
	public void setBackOrderStatus(String backOrderID, String Status) {
		Util.debug("BackOrderMgr.setBackOrderStatus() - Entered");
		// BackOrderLocal backOrder =
		// getBackOrderLocalHome().findByPrimaryKeyUpdate(backOrderID);
		BackOrder backOrder = em.find(BackOrder.class, backOrderID);
		backOrder.setStatus(Status);
	}

	/**
	 * Method setBackOrderOrderDate.
	 * 
	 * @param backOrderID
	 */
	public void setBackOrderOrderDate(String backOrderID) {
		Util.debug("BackOrderMgr.setBackOrderQuantity() - Entered");
		// BackOrderLocal backOrder =
		// getBackOrderLocalHome().findByPrimaryKeyUpdate(backOrderID);
		BackOrder backOrder = em.find(BackOrder.class, backOrderID);
		backOrder.setOrderDate(System.currentTimeMillis());
	}

}


// Node: deleteBackOrder
// Node: getBackOrderLocalHome
// Node: findByPrimaryKeyUpdate
// Node: remove
// Node: receiveConfirmation
// Node: setStatus
// Node: status
// Node: backOrderID
// Node: orderStock
// Node: setBackOrderStatus
// Node: setBackOrderQuantity
// Node: setBackOrderOrderDate
// Node: updateStock
// Node: abortorderStock
// Node: getBackOrderID
// Node: findByPrimaryKey
// Node: BackOrderKey
// Node: getBackOrderInventoryID
// Node: getBackOrderQuantity
// Node: setOrderDate
// Node: currentTimeMillis
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
import java.util.ArrayList;
import java.util.Collection;

import javax.enterprise.context.SessionScoped;
import javax.persistence.EntityManager;
import javax.persistence.LockModeType;
import javax.persistence.PersistenceContext;
import javax.transaction.Transactional;

import com.ibm.websphere.samples.pbw.jpa.BackOrder;
import com.ibm.websphere.samples.pbw.jpa.Customer;
import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.jpa.Order;
import com.ibm.websphere.samples.pbw.jpa.OrderItem;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * ShopingCartBean provides a transactional facade for order collection and processing.
 * 
 */

@Transactional
@SessionScoped
public class ShoppingCartBean implements Serializable {

	@PersistenceContext(unitName = "PBW")
	EntityManager em;

	private ArrayList<Inventory> items = new ArrayList<Inventory>();

	/**
	 * Add an item to the cart.
	 *
	 * @param new_item
	 *            Item to add to the cart.
	 */
	public void addItem(Inventory new_item) {
		boolean added = false;
		// If the same item is already in the cart, just increase the quantity.
		for (Inventory old_item : items) {
			if (old_item.getID().equals(new_item.getID())) {
				old_item.setQuantity(old_item.getQuantity() + new_item.getQuantity());
				added = true;
				break;
			}
		}
		// Add this item to shopping cart, if it is a brand new item.
		if (!added)
			items.add(new_item);
	}

	/**
	 * Remove an item from the cart.
	 *
	 * @param item
	 *            Item to remove from cart.
	 */
	public void removeItem(Inventory item) {
		for (Inventory i : items) {
			if (item.equals(i)) {
				items.remove(i);
				break;
			}
		}
	}

	/**
	 * Remove all items from the cart.
	 */
	public void removeAllItems() {
		items = new ArrayList<Inventory>();
	}

	/**
	 * Remove zero quantity items.
	 */
	public void removeZeroQuantityItems() {
		ArrayList<Inventory> newItems = new ArrayList<Inventory>();

		for (Inventory i : items) {
			if (i.getQuantity() > 0) {
				newItems.add(i);
			}
		}

		items = newItems;
	}

	/**
	 * Get the items in the shopping cart.
	 *
	 * @return A Collection of ShoppingCartItems.
	 */
	public ArrayList<Inventory> getItems() {
		return items;
	}

	/**
	 * Set the items in the shopping cart.
	 *
	 * @param items
	 *            A Vector of ShoppingCartItem's.
	 */
	public void setItems(Collection<Inventory> items) {
		this.items = new ArrayList<Inventory>(items);
	}

	/**
	 * Get the contents of the shopping cart.
	 *
	 * @return The contents of the shopping cart. / public ShoppingCartContents getCartContents() {
	 *         ShoppingCartContents cartContents = new ShoppingCartContents(); // Fill it with data.
	 *         for (int i = 0; i < items.size(); i++) { cartContents.addItem((ShoppingCartItem)
	 *         items.get(i)); } return cartContents; }
	 */

	/**
	 * Create a shopping cart.
	 *
	 * @param cartContents
	 *            Contents to populate cart with. / public void setCartContents(ShoppingCartContents
	 *            cartContents) { items = new ArrayList<ShoppingCartItem>(); int qty; String
	 *            inventoryID; ShoppingCartItem si; Inventory inv; for (int i = 0; i <
	 *            cartContents.size(); i++) { inventoryID = cartContents.getInventoryID(i); qty =
	 *            cartContents.getQuantity(inventoryID); inv = em.find(Inventory.class,
	 *            inventoryID); // clone so we can use Qty as qty to purchase, not inventory in
	 *            stock si = new ShoppingCartItem(inv); si.setQuantity(qty); addItem(si); } }
	 */

	/**
	 * Get the cost of all items in the shopping cart.
	 *
	 * @return The total cost of all items in the shopping cart.
	 */
	public float getSubtotalCost() {
		float f = 0.0F;

		for (Inventory item : items) {
			f += item.getPrice() * (float) item.getQuantity();
		}
		return f;
	}

	/**
	 * Method checkInventory. Check the inventory level of a store item. Order additional inventory
	 * when necessary.
	 *
	 * @param si
	 *            - Store item
	 */
	public void checkInventory(Inventory si) {
		Util.debug("ShoppingCart.checkInventory() - checking Inventory quantity of item: " + si.getID());
		Inventory inv = getInventoryItem(si.getID());

		/**
		 * Decrease the quantity of this inventory item.
		 * 
		 * @param quantity
		 *            The number to decrease the inventory by.
		 * @return The number of inventory items removed.
		 */
		int quantity = si.getQuantity();
		int minimumItems = inv.getMinThreshold();

		int amountToOrder = 0;
		Util.debug("ShoppingCartBean:checkInventory() - Decreasing inventory item " + inv.getInventoryId());
		int quantityNotFilled = 0;
		if (inv.getQuantity() < 1) {
			quantityNotFilled = quantity;
		} else if (inv.getQuantity() < quantity) {
			quantityNotFilled = quantity - inv.getQuantity();
		}

		// When quantity becomes < 0, this will be to determine the
		// quantity of unfilled orders due to insufficient stock.
		inv.setQuantity(inv.getQuantity() - quantity);

		// Check to see if more inventory needs to be ordered from the supplier
		// based on a set minimum Threshold
		if (inv.getQuantity() < minimumItems) {
			// Calculate the amount of stock to order from the supplier
			// to get the inventory up to the maximum.
			amountToOrder = quantityNotFilled;
			backOrder(inv, amountToOrder);
		}

	}

	/**
	 * Create an order with contents of a shopping cart.
	 *
	 * @param customerID
	 *            customer's ID
	 * @param billName
	 *            billing name
	 * @param billAddr1
	 *            billing address line 1
	 * @param billAddr2
	 *            billing address line 2
	 * @param billCity
	 *            billing address city
	 * @param billState
	 *            billing address state
	 * @param billZip
	 *            billing address zip code
	 * @param billPhone
	 *            billing phone
	 * @param shipName
	 *            shippng name
	 * @param shipAddr1
	 *            shippng address line 1
	 * @param shipAddr2
	 *            shippng address line 2
	 * @param shipCity
	 *            shippng address city
	 * @param shipState
	 *            shippng address state
	 * @param shipZip
	 *            shippng address zip code
	 * @param shipPhone
	 *            shippng phone
	 * @param creditCard
	 *            credit card
	 * @param ccNum
	 *            credit card number
	 * @param ccExpireMonth
	 *            credit card expiration month
	 * @param ccExpireYear
	 *            credit card expiration year
	 * @param cardHolder
	 *            credit card holder name
	 * @param shippingMethod
	 *            int of shipping method used
	 * @param items
	 *            vector of StoreItems ordered
	 * @return OrderInfo
	 */
	public Order createOrder(String customerID,
			String billName,
			String billAddr1,
			String billAddr2,
			String billCity,
			String billState,
			String billZip,
			String billPhone,
			String shipName,
			String shipAddr1,
			String shipAddr2,
			String shipCity,
			String shipState,
			String shipZip,
			String shipPhone,
			String creditCard,
			String ccNum,
			String ccExpireMonth,
			String ccExpireYear,
			String cardHolder,
			int shippingMethod,
			Collection<Inventory> items) {
		Order order = null;
		Util.debug("ShoppingCartBean.createOrder:  Creating Order");
		Collection<OrderItem> orderitems = new ArrayList<OrderItem>();
		for (Inventory si : items) {
			Inventory inv = em.find(Inventory.class, si.getID());
			OrderItem oi = new OrderItem(inv);
			oi.setQuantity(si.getQuantity());
			orderitems.add(oi);
		}
		Customer c = em.find(Customer.class, customerID);
		order = new Order(c, billName, billAddr1, billAddr2, billCity, billState, billZip, billPhone, shipName,
				shipAddr1, shipAddr2, shipCity, shipState, shipZip, shipPhone, creditCard, ccNum, ccExpireMonth,
				ccExpireYear, cardHolder, shippingMethod, orderitems);
		em.persist(order);
		em.flush();
		// store the order items
		for (OrderItem o : orderitems) {
			o.setOrder(order);
			o.updatePK();
			em.persist(o);
		}
		em.flush();

		return order;
	}

	public int getSize() {
		return getItems().size();
	}

	/*
	 * Get the inventory item.
	 *
	 * @param id of inventory item.
	 * 
	 * @return an inventory bean.
	 */
	private Inventory getInventoryItem(String inventoryID) {
		Inventory inv = null;
		inv = em.find(Inventory.class, inventoryID);
		return inv;
	}

	/*
	 * Create a BackOrder of this inventory item.
	 * 
	 * @param quantity The number of the inventory item to be backordered
	 */
	private void backOrder(Inventory inv, int amountToOrder) {
		BackOrder b = em.find(BackOrder.class, inv.getInventoryId());
		if (b == null) {
			// create a new backorder if none exists
			BackOrder newBO = new BackOrder(inv, amountToOrder);
			em.persist(newBO);
			em.flush();
			inv.setBackOrder(newBO);
		} else {
			// update the backorder with the new quantity
			int quantity = b.getQuantity();
			quantity += amountToOrder;
			em.lock(b, LockModeType.WRITE);
			em.refresh(b);
			b.setQuantity(quantity);
			em.flush();
			inv.setBackOrder(b);
		}
	}

}


// Node: removeItem
// Node: lock
// Node: refresh
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

import javax.enterprise.context.Dependent;
import javax.persistence.EntityManager;
import javax.persistence.LockModeType;
import javax.persistence.PersistenceContext;
import javax.transaction.Transactional;

import com.ibm.websphere.samples.pbw.jpa.Customer;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * The CustomerMgr provides a transactional facade for access to a user DB as well as simple
 * authentication support for those users.
 * 
 */
@Transactional
@Dependent
public class CustomerMgr implements Serializable {
	@PersistenceContext(unitName = "PBW")
	EntityManager em;

	/**
	 * Create a new user.
	 *
	 * @param customerID
	 *            The new customer ID.
	 * @param password
	 *            The password for the customer ID.
	 * @param firstName
	 *            First name.
	 * @param lastName
	 *            Last name.
	 * @param addr1
	 *            Address line 1.
	 * @param addr2
	 *            Address line 2.
	 * @param addrCity
	 *            City address information.
	 * @param addrState
	 *            State address information.
	 * @param addrZip
	 *            Zip code address information.
	 * @param phone
	 *            User's phone number.
	 * @return Customer
	 */
	public Customer createCustomer(String customerID,
			String password,
			String firstName,
			String lastName,
			String addr1,
			String addr2,
			String addrCity,
			String addrState,
			String addrZip,
			String phone) {
		Customer c = new Customer(customerID, password, firstName, lastName, addr1, addr2, addrCity, addrState, addrZip,
				phone);
		em.persist(c);
		em.flush();
		return c;
	}

	/**
	 * Retrieve an existing user.
	 * 
	 * @param customerID
	 *            The customer ID.
	 * @return Customer
	 */
	public Customer getCustomer(String customerID) {
		Customer c = em.find(Customer.class, customerID);
		return c;

	}

	/**
	 * Update an existing user.
	 *
	 * @param customerID
	 *            The customer ID.
	 * @param firstName
	 *            First name.
	 * @param lastName
	 *            Last name.
	 * @param addr1
	 *            Address line 1.
	 * @param addr2
	 *            Address line 2.
	 * @param addrCity
	 *            City address information.
	 * @param addrState
	 *            State address information.
	 * @param addrZip
	 *            Zip code address information.
	 * @param phone
	 *            User's phone number.
	 * @return Customer
	 */
	public Customer updateUser(String customerID,
			String firstName,
			String lastName,
			String addr1,
			String addr2,
			String addrCity,
			String addrState,
			String addrZip,
			String phone) {
		Customer c = em.find(Customer.class, customerID);
		em.lock(c, LockModeType.WRITE);
		em.refresh(c);

		c.setFirstName(firstName);
		c.setLastName(lastName);
		c.setAddr1(addr1);
		c.setAddr2(addr2);
		c.setAddrCity(addrCity);
		c.setAddrState(addrState);
		c.setAddrZip(addrZip);
		c.setPhone(phone);

		return c;
	}

	/**
	 * Verify that the user exists and the password is value.
	 * 
	 * @param customerID
	 *            The customer ID
	 * @param password
	 *            The password for the customer ID
	 * @return String with a results message.
	 */
	public String verifyUserAndPassword(String customerID, String password) {
		// Try to get customer.
		String results = null;
		Customer customer = null;

		customer = em.find(Customer.class, customerID);

		// Does customer exist?
		if (customer != null) {
			if (!customer.verifyPassword(password)) // Is password correct?
			{
				results = "\nPassword does not match for : " + customerID;
				Util.debug("Password given does not match for userid=" + customerID);
			}
		} else // Customer was not found.
		{
			results = "\nCould not find account for : " + customerID;
			Util.debug("customer " + customerID + " NOT found");
		}

		return results;
	}

}


// Node: setFirstName
// Node: setLastName
// Node: setAddr1
// Node: setAddr2
// Node: setAddrCity
// Node: setAddrState
// Node: setAddrZip
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


// Node: deleteItem
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

import java.util.Enumeration;
import java.util.Hashtable;

import com.ibm.websphere.samples.pbw.jpa.Inventory;

/**
 * A class to hold a shopping cart's contents.
 */
public class ShoppingCartContent implements java.io.Serializable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private Hashtable<String, Integer> table = null;

	public ShoppingCartContent() {
		table = new Hashtable<String, Integer>();
	}

	/** Add the item to the shopping cart. */
	public void addItem(Inventory si) {
		table.put(si.getID(), new Integer(si.getQuantity()));
	}

	/** Update the item in the shopping cart. */
	public void updateItem(Inventory si) {
		table.put(si.getID(), new Integer(si.getQuantity()));
	}

	/** Remove the item from the shopping cart. */
	public void removeItem(Inventory si) {
		table.remove(si.getID());
	}

	/**
	 * Return the number of items in the cart.
	 *
	 * @return The number of items in the cart.
	 */
	public int size() {
		return table.size();
	}

	/**
	 * Return the inventory ID at the index given. The first element is at index 0, the second at
	 * index 1, and so on.
	 *
	 * @return The inventory ID at the index, or NULL if not present.
	 */
	public String getInventoryID(int index) {
		String retval = null;
		String inventoryID;
		int cnt = 0;
		for (Enumeration<String> myEnum = table.keys(); myEnum.hasMoreElements(); cnt++) {
			inventoryID = (String) myEnum.nextElement();
			if (index == cnt) {
				retval = inventoryID;
				break;
			}
		}
		return retval;
	}

	/**
	 * Return the quantity for the inventory ID given.
	 *
	 * @return The quantity for the inventory ID given..
	 *
	 */
	public int getQuantity(String inventoryID) {
		Integer quantity = (Integer) table.get(inventoryID);

		if (quantity == null)
			return 0;
		else
			return quantity.intValue();
	}

}


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
package com.ibm.websphere.samples.pbw.jpa;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;
import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;

/**
 * Customer is the bean mapping for the CUSTOMER table.
 * 
 * @see Customer
 */
@Entity(name = "Customer")
@Table(name = "CUSTOMER", schema = "APP")
@NamedQueries({ @NamedQuery(name = "removeAllCustomers", query = "delete from Customer") })
public class Customer {
	@Id
	private String customerID;
	private String password;

	@NotNull
	@Size(min = 1, message = "First name must include at least one letter.")
	private String firstName;
	@NotNull
	@Size(min = 1, message = "Last name must include at least one letter.")
	private String lastName;
	@NotNull
	@Size(min = 1, message = "Address must include at least one letter.")
	private String addr1;
	private String addr2;
	@NotNull
	@Size(min = 1, message = "City name must include at least one letter.")
	private String addrCity;
	@NotNull
	@Size(min = 2, message = "State must include at least two letters.")
	private String addrState;
	@Pattern(regexp = "\\d{5}", message = "Zip code does not have 5 digits.")
	private String addrZip;
	@NotNull
	@Pattern(regexp = "\\d{3}-\\d{3}-\\d{4}", message = "Phone number does not match xxx-xxx-xxxx.")
	private String phone;

	public Customer() {
	}

	/**
	 * Create a new Customer.
	 *
	 * @param key
	 *            CustomerKey
	 * @param password
	 *            Password used for this customer account.
	 * @param firstName
	 *            First name of the customer.
	 * @param lastName
	 *            Last name of the customer
	 * @param addr1
	 *            Street address of the customer
	 * @param addr2
	 *            Street address of the customer
	 * @param addrCity
	 *            City
	 * @param addrState
	 *            State
	 * @param addrZip
	 *            Zip code
	 * @param phone
	 *            Phone number
	 */
	public Customer(String key, String password, String firstName, String lastName, String addr1, String addr2,
			String addrCity, String addrState, String addrZip, String phone) {
		this.setCustomerID(key);
		this.setPassword(password);
		this.setFirstName(firstName);
		this.setLastName(lastName);
		this.setAddr1(addr1);
		this.setAddr2(addr2);
		this.setAddrCity(addrCity);
		this.setAddrState(addrState);
		this.setAddrZip(addrZip);
		this.setPhone(phone);
	}

	/**
	 * Verify password.
	 *
	 * @param password
	 *            value to be checked.
	 * @return True, if password matches one stored.
	 */
	public boolean verifyPassword(String password) {
		return this.getPassword().equals(password);
	}

	/**
	 * Get the customer's full name.
	 * 
	 * @return String of customer's full name.
	 */
	public String getFullName() {
		return this.getFirstName() + " " + this.getLastName();
	}

	public String getAddr1() {
		return addr1;
	}

	public void setAddr1(String addr1) {
		this.addr1 = addr1;
	}

	public String getAddr2() {
		return addr2;
	}

	public void setAddr2(String addr2) {
		this.addr2 = addr2;
	}

	public String getAddrCity() {
		return addrCity;
	}

	public void setAddrCity(String addrCity) {
		this.addrCity = addrCity;
	}

	public String getAddrState() {
		return addrState;
	}

	public void setAddrState(String addrState) {
		this.addrState = addrState;
	}

	public String getAddrZip() {
		return addrZip;
	}

	public void setAddrZip(String addrZip) {
		this.addrZip = addrZip;
	}

	public String getCustomerID() {
		return customerID;
	}

	public void setCustomerID(String customerID) {
		this.customerID = customerID;
	}

	public String getFirstName() {
		return firstName;
	}

	public void setFirstName(String firstName) {
		this.firstName = firstName;
	}

	public String getLastName() {
		return lastName;
	}

	public void setLastName(String lastName) {
		this.lastName = lastName;
	}

	public String getPassword() {
		return password;
	}

	public void setPassword(String password) {
		this.password = password;
	}

	public String getPhone() {
		return phone;
	}

	public void setPhone(String phone) {
		this.phone = phone;
	}

}


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
package com.ibm.websphere.samples.pbw.jpa;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.OneToOne;
import javax.persistence.Table;
import javax.persistence.TableGenerator;

import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Bean mapping for BACKORDER table.
 */
@Entity(name = "BackOrder")
@Table(name = "BACKORDER", schema = "APP")
@NamedQueries({ @NamedQuery(name = "findAllBackOrders", query = "select b from BackOrder b"),
		@NamedQuery(name = "findByInventoryID", query = "select b from BackOrder b where ((b.inventory.inventoryId = :id) and (b.status = 'Order Stock'))"),
		@NamedQuery(name = "removeAllBackOrder", query = "delete from BackOrder") })
public class BackOrder {
	@Id
	@GeneratedValue(strategy = GenerationType.TABLE, generator = "BackOrderSeq")
	@TableGenerator(name = "BackOrderSeq", table = "IDGENERATOR", pkColumnName = "IDNAME", pkColumnValue = "BACKORDER", valueColumnName = "IDVALUE")
	private String backOrderID;
	private int quantity;
	private String status;
	private long lowDate;
	private long orderDate;
	private String supplierOrderID; // missing table

	// relationships
	@OneToOne
	@JoinColumn(name = "INVENTORYID")
	private Inventory inventory;

	public BackOrder() {
	}

	public BackOrder(String backOrderID) {
		setBackOrderID(backOrderID);
	}

	public BackOrder(Inventory inventory, int quantity) {
			this.setInventory(inventory);
			this.setQuantity(quantity);
			this.setStatus(Util.STATUS_ORDERSTOCK);
			this.setLowDate(System.currentTimeMillis());
	}

	public String getBackOrderID() {
		return backOrderID;
	}

	public void setBackOrderID(String backOrderID) {
		this.backOrderID = backOrderID;
	}

	public long getLowDate() {
		return lowDate;
	}

	public void setLowDate(long lowDate) {
		this.lowDate = lowDate;
	}

	public long getOrderDate() {
		return orderDate;
	}

	public void setOrderDate(long orderDate) {
		this.orderDate = orderDate;
	}

	public int getQuantity() {
		return quantity;
	}

	public void setQuantity(int quantity) {
		this.quantity = quantity;
	}

	public void increateQuantity(int delta) {
		if (!(status.equals(Util.STATUS_ORDERSTOCK))) {
			Util.debug("BackOrderMgr.createBackOrder() - Backorders found but have already been ordered from the supplier");
			throw new RuntimeException("cannot increase order size for orders already in progress");
		}
		// Increase the BackOrder quantity for an existing Back Order.
		quantity = quantity + delta;
	}

	public String getStatus() {
		return status;
	}

	public void setStatus(String status) {
		this.status = status;
	}

	public String getSupplierOrderID() {
		return supplierOrderID;
	}

	public void setSupplierOrderID(String supplierOrderID) {
		this.supplierOrderID = supplierOrderID;
	}

	public Inventory getInventory() {
		return inventory;
	}

	public void setInventory(Inventory inventory) {
		this.inventory = inventory;
	}

}


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

import com.ibm.websphere.samples.pbw.jpa.BackOrder;
import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * A class to hold a back order item's data.
 */
public class BackOrderItem implements java.io.Serializable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private String name;
	private int inventoryQuantity;
	private String backOrderID; // from BackOrder
	private int quantity; // from BackOrder
	private String status; // from BackOrder
	private long lowDate; // from BackOrder
	private long orderDate; // from BackOrder
	private String supplierOrderID; // from BackOrder
	private Inventory inventory; // from BackOrder

	/**
	 * @see java.lang.Object#Object()
	 */
	/** Default constructor. */
	public BackOrderItem() {
	}

	/**
	 * Method BackOrderItem.
	 * 
	 * @param backOrderID
	 * @param inventoryID
	 * @param name
	 * @param quantity
	 * @param status
	 */
	public BackOrderItem(String backOrderID, Inventory inventoryID, String name, int quantity, String status) {
		this.backOrderID = backOrderID;
		this.inventory = inventoryID;
		this.name = name;
		this.quantity = quantity;
		this.status = status;
	}

	/**
	 * Method BackOrderItem.
	 * 
	 * @param backOrder
	 */
	public BackOrderItem(BackOrder backOrder) {
		try {
			this.backOrderID = backOrder.getBackOrderID();
			this.inventory = backOrder.getInventory();
			this.quantity = backOrder.getQuantity();
			this.status = backOrder.getStatus();
			this.lowDate = backOrder.getLowDate();
			this.orderDate = backOrder.getOrderDate();
			this.supplierOrderID = backOrder.getSupplierOrderID();
		} catch (Exception e) {
			Util.debug("BackOrderItem - Exception: " + e);
		}
	}

	/**
	 * Method getBackOrderID.
	 * 
	 * @return String
	 */
	public String getBackOrderID() {
		return backOrderID;
	}

	/**
	 * Method setBackOrderID.
	 * 
	 * @param backOrderID
	 */
	public void setBackOrderID(String backOrderID) {
		this.backOrderID = backOrderID;
	}

	/**
	 * Method getSupplierOrderID.
	 * 
	 * @return String
	 */
	public String getSupplierOrderID() {
		return supplierOrderID;
	}

	/**
	 * Method setSupplierOrderID.
	 * 
	 * @param supplierOrderID
	 */
	public void setSupplierOrderID(String supplierOrderID) {
		this.supplierOrderID = supplierOrderID;
	}

	/**
	 * Method setQuantity.
	 * 
	 * @param quantity
	 */
	public void setQuantity(int quantity) {
		this.quantity = quantity;
	}

	/**
	 * Method getInventoryID.
	 * 
	 * @return String
	 */
	public Inventory getInventory() {
		return inventory;
	}

	/**
	 * Method getName.
	 * 
	 * @return String
	 */
	public String getName() {
		return name;
	}

	/**
	 * Method setName.
	 * 
	 * @param name
	 */
	public void setName(String name) {
		this.name = name;
	}

	/**
	 * Method getQuantity.
	 * 
	 * @return int
	 */
	public int getQuantity() {
		return quantity;
	}

	/**
	 * Method getInventoryQuantity.
	 * 
	 * @return int
	 */
	public int getInventoryQuantity() {
		return inventoryQuantity;
	}

	/**
	 * Method setInventoryQuantity.
	 * 
	 * @param quantity
	 */
	public void setInventoryQuantity(int quantity) {
		this.inventoryQuantity = quantity;
	}

	/**
	 * Method getStatus.
	 * 
	 * @return String
	 */
	public String getStatus() {
		return status;
	}

	/**
	 * Method getLowDate.
	 * 
	 * @return long
	 */
	public long getLowDate() {
		return lowDate;
	}

	/**
	 * Method getOrderDate.
	 * 
	 * @return long
	 */
	public long getOrderDate() {
		return orderDate;
	}
}


