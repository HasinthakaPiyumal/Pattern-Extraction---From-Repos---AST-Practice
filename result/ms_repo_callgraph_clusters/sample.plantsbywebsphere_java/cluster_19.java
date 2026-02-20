// Cluster 19

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

import javax.persistence.Column;
import javax.persistence.Embeddable;
import javax.persistence.EmbeddedId;
import javax.persistence.Entity;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;
import javax.persistence.Transient;

import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Bean mapping for the ORDERITEM table.
 */
@Entity(name = "OrderItem")
@Table(name = "ORDERITEM", schema = "APP")
@NamedQueries({ @NamedQuery(name = "removeAllOrderItem", query = "delete from OrderItem") })
public class OrderItem {
	/**
	 * Composite Key class for Entity Bean: OrderItem
	 * 
	 * Key consists of essentially two foreign key relations, but is mapped as foreign keys.
	 */
	@Embeddable
	public static class PK implements java.io.Serializable {
		static final long serialVersionUID = 3206093459760846163L;
		@Column(name = "inventoryID")
		public String inventoryID;
		@Column(name = "ORDER_ORDERID")
		public String order_orderID;

		public PK() {
			Util.debug("OrderItem.PK()");
		}

		public PK(String inventoryID, String argOrder) {
			Util.debug("OrderItem.PK() inventoryID=" + inventoryID + "=");
			Util.debug("OrderItem.PK() orderID=" + argOrder + "=");
			this.inventoryID = inventoryID;
			this.order_orderID = argOrder;
		}

		/**
		 * Returns true if both keys are equal.
		 */
		public boolean equals(java.lang.Object otherKey) {
			if (otherKey instanceof PK) {
				PK o = (PK) otherKey;
				return ((this.inventoryID.equals(o.inventoryID)) && (this.order_orderID.equals(o.order_orderID)));
			}
			return false;
		}

		/**
		 * Returns the hash code for the key.
		 */
		public int hashCode() {
			Util.debug("OrderItem.PK.hashCode() inventoryID=" + inventoryID + "=");
			Util.debug("OrderItem.PK.hashCode() orderID=" + order_orderID + "=");

			return (inventoryID.hashCode() + order_orderID.hashCode());
		}
	}

	@SuppressWarnings("unused")
	@EmbeddedId
	private OrderItem.PK id;
	private String name;
	private String pkginfo;
	private float price;
	private float cost;
	private int category;
	private int quantity;
	private String sellDate;
	@Transient
	private String inventoryId;

	@ManyToOne
	@JoinColumn(name = "INVENTORYID", insertable = false, updatable = false)
	private Inventory inventory;
	@ManyToOne
	@JoinColumn(name = "ORDER_ORDERID", insertable = false, updatable = false)
	private Order order;

	public int getCategory() {
		return category;
	}

	public void setCategory(int category) {
		this.category = category;
	}

	public float getCost() {
		return cost;
	}

	public void setCost(float cost) {
		this.cost = cost;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public String getPkginfo() {
		return pkginfo;
	}

	public void setPkginfo(String pkginfo) {
		this.pkginfo = pkginfo;
	}

	public float getPrice() {
		return price;
	}

	public void setPrice(float price) {
		this.price = price;
	}

	public int getQuantity() {
		return quantity;
	}

	public void setQuantity(int quantity) {
		this.quantity = quantity;
	}

	public String getSellDate() {
		return sellDate;
	}

	public void setSellDate(String sellDate) {
		this.sellDate = sellDate;
	}

	public OrderItem() {
	}

	public OrderItem(Inventory inv) {
		Util.debug("OrderItem(inv) - id = " + inv.getInventoryId());
		setInventoryId(inv.getInventoryId());
		inventory = inv;
		name = inv.getName();
		pkginfo = inv.getPkginfo();
		price = inv.getPrice();
		cost = inv.getCost();
		category = inv.getCategory();
	}

	public OrderItem(Order order, String orderID, Inventory inv, java.lang.String name, java.lang.String pkginfo,
			float price, float cost, int quantity, int category, java.lang.String sellDate) {
		Util.debug("OrderItem(etc.)");
		inventory = inv;
		setInventoryId(inv.getInventoryId());
		setName(name);
		setPkginfo(pkginfo);
		setPrice(price);
		setCost(cost);
		setQuantity(quantity);
		setCategory(category);
		setSellDate(sellDate);
		setOrder(order);
		id = new OrderItem.PK(inv.getInventoryId(), order.getOrderID());
	}

	/*
	 * updates the primary key field with the composite orderId+inventoryId
	 */
	public void updatePK() {
		id = new OrderItem.PK(inventoryId, order.getOrderID());
	}

	public Inventory getInventory() {
		return inventory;
	}

	public void setInventory(Inventory inv) {
		this.inventory = inv;
	}

	public Order getOrder() {
		return order;
	}

	/**
	 * Sets the order for this item Also updates the sellDate
	 * 
	 * @param order
	 */
	public void setOrder(Order order) {
		this.order = order;
		this.sellDate = order.getSellDate();
	}

	public String getInventoryId() {
		return inventoryId;
	}

	public void setInventoryId(String inventoryId) {
		this.inventoryId = inventoryId;
	}

}

// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/jpa/OrderItem.java:OrderItem.<init>
// Node: Entity
// Node: Table
// Node: NamedQueries
// Node: NamedQuery
// Node: Column
// Node: JoinColumn
// Node: setCategory
// Node: getCost
// Node: setCost
// Node: setInventory
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
import javax.persistence.Transient;
import javax.persistence.Version;

import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Inventory is the bean mapping for the INVENTORY table. It provides information about products the
 * store has for sale.
 * 
 * @see Inventory
 */
@Entity(name = "Inventory")
@Table(name = "INVENTORY", schema = "APP")
@NamedQueries({
		@NamedQuery(name = "getItemsByCategory", query = "select i from Inventory i where i.category = :category ORDER BY i.inventoryId"),
		@NamedQuery(name = "getItemsLikeName", query = "select i from Inventory i where i.name like :name"),
		@NamedQuery(name = "removeAllInventory", query = "delete from Inventory") })
public class Inventory implements Cloneable, java.io.Serializable {
	private static final long serialVersionUID = 1L;
	private static final int DEFAULT_MINTHRESHOLD = 50;
	private static final int DEFAULT_MAXTHRESHOLD = 200;
	@Id
	private String inventoryId;
	private String name;
	private String heading;
	private String description;
	private String pkginfo;
	private String image;
	private byte[] imgbytes;
	private float price;
	private float cost;
	private int quantity;
	private int category;
	private String notes;
	private boolean isPublic;
	private int minThreshold;
	private int maxThreshold;
	
	@Version
	private long version;

	@Transient
	private BackOrder backOrder;

	public Inventory() {
	}

	/**
	 * Create a new Inventory.
	 *
	 * @param key
	 *            Inventory Key
	 * @param name
	 *            Name of inventory item.
	 * @param heading
	 *            Description heading of inventory item.
	 * @param desc
	 *            Description of inventory item.
	 * @param pkginfo
	 *            Package info of inventory item.
	 * @param image
	 *            Image of inventory item.
	 * @param price
	 *            Price of inventory item.
	 * @param cost
	 *            Cost of inventory item.
	 * @param quantity
	 *            Quantity of inventory items in stock.
	 * @param category
	 *            Category of inventory item.
	 * @param notes
	 *            Notes of inventory item.
	 * @param isPublic
	 *            Access permission of inventory item.
	 */
	public Inventory(String key, String name, String heading, String desc, String pkginfo, String image, float price,
			float cost, int quantity, int category, String notes, boolean isPublic) {
		this.setInventoryId(key);
		Util.debug("creating new Inventory, inventoryId=" + this.getInventoryId());
		this.setName(name);
		this.setHeading(heading);
		this.setDescription(desc);
		this.setPkginfo(pkginfo);
		this.setImage(image);
		this.setPrice(price);
		this.setCost(cost);
		this.setQuantity(quantity);
		this.setCategory(category);
		this.setNotes(notes);
		this.setIsPublic(isPublic);
		this.setMinThreshold(DEFAULT_MINTHRESHOLD);
		this.setMaxThreshold(DEFAULT_MAXTHRESHOLD);

	}

	/**
	 * Create a new Inventory.
	 *
	 * @param item
	 *            Inventory to use to make a new inventory item.
	 */
	public Inventory(Inventory item) {
		this.setInventoryId(item.getInventoryId());
		this.setName(item.getName());
		this.setHeading(item.getHeading());
		this.setDescription(item.getDescription());
		this.setPkginfo(item.getPkginfo());
		this.setImage(item.getImage());
		this.setPrice(item.getPrice());
		this.setCost(item.getCost());
		this.setQuantity(item.getQuantity());
		this.setCategory(item.getCategory());
		this.setNotes(item.getNotes());
		this.setMinThreshold(DEFAULT_MINTHRESHOLD);
		this.setMaxThreshold(DEFAULT_MAXTHRESHOLD);

		setIsPublic(item.isPublic());

		// does not clone BackOrder info
	}

	/**
	 * Increase the quantity of this inventory item.
	 * 
	 * @param quantity
	 *            The number to increase the inventory by.
	 */
	public void increaseInventory(int quantity) {
		this.setQuantity(this.getQuantity() + quantity);
	}

	public int getCategory() {
		return category;
	}

	public void setCategory(int category) {
		this.category = category;
	}

	public float getCost() {
		return cost;
	}

	public void setCost(float cost) {
		this.cost = cost;
	}

	public String getDescription() {
		return description;
	}

	public void setDescription(String description) {
		this.description = description;
	}

	public String getHeading() {
		return heading;
	}

	public void setHeading(String heading) {
		this.heading = heading;
	}

	public String getImage() {
		return image;
	}

	public void setImage(String image) {
		this.image = image;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public String getNotes() {
		return notes;
	}

	public void setNotes(String notes) {
		this.notes = notes;
	}

	public String getPkginfo() {
		return pkginfo;
	}

	public void setPkginfo(String pkginfo) {
		this.pkginfo = pkginfo;
	}

	public float getPrice() {
		return price;
	}

	public void setPrice(float price) {
		this.price = price;
	}

	public int getQuantity() {
		return quantity;
	}

	public void setQuantity(int quantity) {
		this.quantity = quantity;
	}

	public int getMaxThreshold() {
		return maxThreshold;
	}

	public void setMaxThreshold(int maxThreshold) {
		this.maxThreshold = maxThreshold;
	}

	public int getMinThreshold() {
		return minThreshold;
	}

	public void setMinThreshold(int minThreshold) {
		this.minThreshold = minThreshold;
	}

	public String getInventoryId() {
		return inventoryId;
	}

	public void setInventoryId(String id) {
		inventoryId = id;
	}

	/**
	 * Same as getInventoryId. Added for compatability with ShoppingCartItem when used by the Client
	 * XJB sample
	 * 
	 * @return String ID of the inventory item
	 */
	public String getID() {
		return inventoryId;
	}

	/**
	 * Same as setInventoryId. Added for compatability with ShoppingCartItem when used by the Client
	 * XJB sample
	 * 
	 */
	public void setID(String id) {
		inventoryId = id;
	}

	public boolean isPublic() {
		return isPublic;
	}

	public void setIsPublic(boolean isPublic) {
		this.isPublic = isPublic;
	}

	/** Set the inventory item's public availability. */
	public void setPrivacy(boolean isPublic) {
		setIsPublic(isPublic);
	}

	public byte[] getImgbytes() {
		return imgbytes;
	}

	public void setImgbytes(byte[] imgbytes) {
		this.imgbytes = imgbytes;
	}

	public BackOrder getBackOrder() {
		return backOrder;
	}

	public void setBackOrder(BackOrder backOrder) {
		this.backOrder = backOrder;
	}
	
	@Override
	public String toString() {
	    return getClass().getSimpleName() + "{id=" + inventoryId + "}";
	}

}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/jpa/Inventory.java:Inventory.<init>
// Node: setHeading
// Node: setDescription
// Node: setImage
// Node: getHeading
// Node: getDescription
// Node: getImage
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

import java.io.Serializable;

/**
 * The key class of the Order entity bean.
 **/
public class OrderKey implements Serializable {

	private static final long serialVersionUID = 7912030586849592135L;

	public String orderID;

	/**
	 * Constructs an OrderKey object.
	 */
	public OrderKey() {
	}

	/**
	 * Constructs a newly allocated OrderKey object that represents the primitive long argument.
	 */
	public OrderKey(String orderID) {
		this.orderID = orderID;
	}

	/**
	 * Determines if the OrderKey object passed to the method matches this OrderKey object.
	 * 
	 * @param obj
	 *            java.lang.Object The OrderKey object to compare to this OrderKey object.
	 * @return boolean The pass object is either equal to this OrderKey object (true) or not.
	 */
	public boolean equals(Object obj) {
		if (obj instanceof OrderKey) {
			OrderKey otherKey = (OrderKey) obj;
			return (((orderID.equals(otherKey.orderID))));
		} else
			return false;
	}

	/**
	 * Generates a hash code for this OrderKey object.
	 * 
	 * @return int The hash code.
	 */
	public int hashCode() {
		return (orderID.hashCode());
	}

	/**
	 * Get accessor for persistent attribute: orderID
	 */
	public java.lang.String getOrderID() {
		return orderID;
	}

	/**
	 * Set accessor for persistent attribute: orderID
	 */
	public void setOrderID(java.lang.String newOrderID) {
		orderID = newOrderID;
	}

}


// Node: setOrderID
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

import java.util.Collection;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;
import javax.persistence.TableGenerator;
import javax.persistence.Transient;

import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Bean mapping for the ORDER1 table.
 */
@Entity(name = "Order")
@Table(name = "ORDER1", schema = "APP")
@NamedQueries({ @NamedQuery(name = "removeAllOrders", query = "delete from Order") })
public class Order {
	public static final String ORDER_INFO_TABLE_NAME = "java:comp/env/jdbc/OrderInfoTableName";
	public static final String ORDER_ITEMS_TABLE_NAME = "java:comp/env/jdbc/OrderItemsTableName";

	@Id
	@GeneratedValue(strategy = GenerationType.TABLE, generator = "OrderSeq")
	@TableGenerator(name = "OrderSeq", table = "IDGENERATOR", pkColumnName = "IDNAME", pkColumnValue = "ORDER", valueColumnName = "IDVALUE")
	private String orderID;
	private String sellDate;
	private String billName;
	private String billAddr1;
	private String billAddr2;
	private String billCity;
	private String billState;
	private String billZip;
	private String billPhone;
	private String shipName;
	private String shipAddr1;
	private String shipAddr2;
	private String shipCity;
	private String shipState;
	private String shipZip;
	private String shipPhone;
	private String creditCard;
	private String ccNum;
	private String ccExpireMonth;
	private String ccExpireYear;
	private String cardHolder;
	private int shippingMethod;
	private float profit;

	@ManyToOne
	@JoinColumn(name = "CUSTOMERID")
	private Customer customer;
	@Transient
	private Collection orderItems;

	@Transient
	private Collection<OrderItem> items = null;

	/**
	 * Constructor to create an Order.
	 *
	 * @param customer
	 *            - customer who created the order
	 * @param billName
	 *            - billing name
	 * @param billAddr1
	 *            - billing address line 1
	 * @param billAddr2
	 *            - billing address line 2
	 * @param billCity
	 *            - billing address city
	 * @param billState
	 *            - billing address state
	 * @param billZip
	 *            - billing address zip code
	 * @param billPhone
	 *            - billing phone
	 * @param shipName
	 *            - shippng name
	 * @param shipAddr1
	 *            - shippng address line 1
	 * @param shipAddr2
	 *            - shippng address line 2
	 * @param shipCity
	 *            - shippng address city
	 * @param shipState
	 *            - shippng address state
	 * @param shipZip
	 *            - shippng address zip code
	 * @param shipPhone
	 *            - shippng phone
	 * @param creditCard
	 *            - credit card
	 * @param ccNum
	 *            - credit card number
	 * @param ccExpireMonth
	 *            - credit card expiration month
	 * @param ccExpireYear
	 *            - credit card expiration year
	 * @param cardHolder
	 *            - credit card holder name
	 * @param shippingMethod
	 *            int of shipping method used
	 * @param items
	 *            vector of StoreItems ordered
	 */
	public Order(Customer customer, String billName, String billAddr1, String billAddr2, String billCity,
			String billState, String billZip, String billPhone, String shipName, String shipAddr1, String shipAddr2,
			String shipCity, String shipState, String shipZip, String shipPhone, String creditCard, String ccNum,
			String ccExpireMonth, String ccExpireYear, String cardHolder, int shippingMethod,
			Collection<OrderItem> items) {
		this.setSellDate(Long.toString(System.currentTimeMillis()));

		// Pad it to 14 digits so sorting works properly.
		if (this.getSellDate().length() < 14) {
			StringBuffer sb = new StringBuffer(Util.ZERO_14);
			sb.replace((14 - this.getSellDate().length()), 14, this.getSellDate());
			this.setSellDate(sb.toString());
		}

		this.setCustomer(customer);
		this.setBillName(billName);
		this.setBillAddr1(billAddr1);
		this.setBillAddr2(billAddr2);
		this.setBillCity(billCity);
		this.setBillState(billState);
		this.setBillZip(billZip);
		this.setBillPhone(billPhone);
		this.setShipName(shipName);
		this.setShipAddr1(shipAddr1);
		this.setShipAddr2(shipAddr2);
		this.setShipCity(shipCity);
		this.setShipState(shipState);
		this.setShipZip(shipZip);
		this.setShipPhone(shipPhone);
		this.setCreditCard(creditCard);
		this.setCcNum(ccNum);
		this.setCcExpireMonth(ccExpireMonth);
		this.setCcExpireYear(ccExpireYear);
		this.setCardHolder(cardHolder);
		this.setShippingMethod(shippingMethod);
		this.items = items;

		// Get profit for total order.
		OrderItem oi;
		float profit;
		profit = 0.0f;
		for (Object o : items) {
			oi = (OrderItem) o;
			profit = profit + (oi.getQuantity() * (oi.getPrice() - oi.getCost()));
			oi.setOrder(this);
		}
		this.setProfit(profit);
	}

	public Order(String orderID) {
		setOrderID(orderID);
	}

	public Order() {
	}

	public String getBillAddr1() {
		return billAddr1;
	}

	public void setBillAddr1(String billAddr1) {
		this.billAddr1 = billAddr1;
	}

	public String getBillAddr2() {
		return billAddr2;
	}

	public void setBillAddr2(String billAddr2) {
		this.billAddr2 = billAddr2;
	}

	public String getBillCity() {
		return billCity;
	}

	public void setBillCity(String billCity) {
		this.billCity = billCity;
	}

	public String getBillName() {
		return billName;
	}

	public void setBillName(String billName) {
		this.billName = billName;
	}

	public String getBillPhone() {
		return billPhone;
	}

	public void setBillPhone(String billPhone) {
		this.billPhone = billPhone;
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

	public String getCardHolder() {
		return cardHolder;
	}

	public void setCardHolder(String cardHolder) {
		this.cardHolder = cardHolder;
	}

	public String getCcExpireMonth() {
		return ccExpireMonth;
	}

	public void setCcExpireMonth(String ccExpireMonth) {
		this.ccExpireMonth = ccExpireMonth;
	}

	public String getCcExpireYear() {
		return ccExpireYear;
	}

	public void setCcExpireYear(String ccExpireYear) {
		this.ccExpireYear = ccExpireYear;
	}

	public String getCcNum() {
		return ccNum;
	}

	public void setCcNum(String ccNum) {
		this.ccNum = ccNum;
	}

	public String getCreditCard() {
		return creditCard;
	}

	public void setCreditCard(String creditCard) {
		this.creditCard = creditCard;
	}

	public Customer getCustomer() {
		return customer;
	}

	public void setCustomer(Customer customer) {
		this.customer = customer;
	}

	public Collection<OrderItem> getItems() {
		return items;
	}

	public void setItems(Collection<OrderItem> items) {
		this.items = items;
	}

	public String getOrderID() {
		return orderID;
	}

	public void setOrderID(String orderID) {
		this.orderID = orderID;
	}

	public Collection getOrderItems() {
		return orderItems;
	}

	public void setOrderItems(Collection orderItems) {
		this.orderItems = orderItems;
	}

	public float getProfit() {
		return profit;
	}

	public void setProfit(float profit) {
		this.profit = profit;
	}

	public String getSellDate() {
		return sellDate;
	}

	public void setSellDate(String sellDate) {
		this.sellDate = sellDate;
	}

	public String getShipAddr1() {
		return shipAddr1;
	}

	public void setShipAddr1(String shipAddr1) {
		this.shipAddr1 = shipAddr1;
	}

	public String getShipAddr2() {
		return shipAddr2;
	}

	public void setShipAddr2(String shipAddr2) {
		this.shipAddr2 = shipAddr2;
	}

	public String getShipCity() {
		return shipCity;
	}

	public void setShipCity(String shipCity) {
		this.shipCity = shipCity;
	}

	public String getShipName() {
		return shipName;
	}

	public void setShipName(String shipName) {
		this.shipName = shipName;
	}

	public String getShipPhone() {
		return shipPhone;
	}

	public void setShipPhone(String shipPhone) {
		this.shipPhone = shipPhone;
	}

	public int getShippingMethod() {
		return shippingMethod;
	}

	public void setShippingMethod(int shippingMethod) {
		this.shippingMethod = shippingMethod;
	}

	public String getShipZip() {
		return shipZip;
	}

	public void setShipZip(String shipZip) {
		this.shipZip = shipZip;
	}

	public String getShipState() {
		return shipState;
	}

	public void setShipState(String shipState) {
		this.shipState = shipState;
	}
}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/jpa/Order.java:Order.<init>
// Node: GeneratedValue
// Node: TableGenerator
// Node: length
// Node: replace
// Node: setCustomer
// Node: setBillName
// Node: setBillAddr1
// Node: setBillAddr2
// Node: setBillCity
// Node: setBillState
// Node: setBillZip
// Node: setBillPhone
// Node: setShipName
// Node: setShipAddr1
// Node: setShipAddr2
// Node: setShipCity
// Node: setShipState
// Node: setShipZip
// Node: setShipPhone
// Node: setCreditCard
// Node: setCcNum
// Node: setCcExpireMonth
// Node: setCcExpireYear
// Node: setCardHolder
// Node: setShippingMethod
// Node: setProfit
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/jpa/Customer.java:Customer.<init>
// Node: setCustomerID
// Node: setPassword
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
// (C) COPYRIGHT International Business Machines Corp., 2004,2011
// All Rights Reserved * Licensed Materials - Property of IBM
//
package com.ibm.websphere.samples.pbw.jpa;

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;

/**
 * Bean mapping for the SUPPLIER table.
 */
@Entity(name = "Supplier")
@Table(name = "SUPPLIER", schema = "APP")
@NamedQueries({ @NamedQuery(name = "findAllSuppliers", query = "select s from Supplier s"),
		@NamedQuery(name = "removeAllSupplier", query = "delete from Supplier") })
public class Supplier {
	@Id
	private String supplierID;
	private String name;
	private String city;
	private String usstate;
	private String zip;
	private String phone;
	private String url;
	private String street;

	public String getCity() {
		return city;
	}

	public void setCity(String city) {
		this.city = city;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public String getPhone() {
		return phone;
	}

	public void setPhone(String phone) {
		this.phone = phone;
	}

	public String getStreet() {
		return street;
	}

	public void setStreet(String street) {
		this.street = street;
	}

	public String getSupplierID() {
		return supplierID;
	}

	public void setSupplierID(String supplierID) {
		this.supplierID = supplierID;
	}

	public String getUrl() {
		return url;
	}

	public void setUrl(String url) {
		this.url = url;
	}

	public String getUsstate() {
		return usstate;
	}

	public void setUsstate(String usstate) {
		this.usstate = usstate;
	}

	public String getZip() {
		return zip;
	}

	public void setZip(String zip) {
		this.zip = zip;
	}

	public Supplier() {
	}

	public Supplier(String supplierID) {
		setSupplierID(supplierID);
	}

	/**
	 * @param supplierID
	 * @param name
	 * @param street
	 * @param city
	 * @param state
	 * @param zip
	 * @param phone
	 * @param url
	 */
	public Supplier(String supplierID, String name, String street, String city, String state, String zip, String phone,
			String url) {
		this.setSupplierID(supplierID);
		this.setName(name);
		this.setStreet(street);
		this.setCity(city);
		this.setUsstate(state);
		this.setZip(zip);
		this.setPhone(phone);
		this.setUrl(url);
	}
}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/jpa/Supplier.java:Supplier.<init>
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/jpa/BackOrder.java:BackOrder.<init>
// Node: where
// Node: and
// Node: setBackOrderID
// Node: setLowDate
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

import java.util.Calendar;

import javax.validation.constraints.NotNull;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;

import com.ibm.websphere.samples.pbw.jpa.Order;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * A class to hold an order's data.
 */
public class OrderInfo implements java.io.Serializable {
	private static final long serialVersionUID = 1L;
	private String orderID;
	@NotNull
	@Size(min = 1, message = "Name for billing must include at least one letter.")
	private String billName;
	@NotNull
	@Size(min = 1, message = "Billing address must include at least one letter.")
	private String billAddr1;
	private String billAddr2;
	@NotNull
	@Size(min = 1, message = "Billing city must include at least one letter.")
	private String billCity;
	@NotNull
	@Size(min = 1, message = "Billing state must include at least one letter.")
	private String billState;

	@Pattern(regexp = "\\d{5}", message = "Billing zip code does not have 5 digits.")
	private String billZip;

	@Pattern(regexp = "\\d{3}-\\d{3}-\\d{4}", message = "Billing phone number does not match xxx-xxx-xxxx.")
	private String billPhone;
	@NotNull
	@Size(min = 1, message = "Name for shipping must include at least one letter.")
	private String shipName;
	@NotNull
	@Size(min = 1, message = "Shipping address must include at least one letter.")
	private String shipAddr1;
	private String shipAddr2;
	@NotNull
	@Size(min = 1, message = "Shipping city must include at least one letter.")
	private String shipCity;
	@NotNull
	@Size(min = 1, message = "Shipping state must include at least one letter.")
	private String shipState;

	@Pattern(regexp = "[0-9][0-9][0-9][0-9][0-9]", message = "Shipping zip code does not have 5 digits.")
	private String shipZip;

	@Pattern(regexp = "\\d{3}-\\d{3}-\\d{4}", message = "Shipping phone number does not match xxx-xxx-xxxx.")
	private String shipPhone;
	private int shippingMethod;
	@NotNull
	@Size(min = 1, message = "Card holder name must include at least one letter.")
	private String cardholderName;
	private String cardName;

	@Pattern(regexp = "\\d{4} \\d{4} \\d{4} \\d{4}", message = "Credit card numbers must be entered as XXXX XXXX XXXX XXXX.")
	private String cardNum;
	private String cardExpMonth;
	private String cardExpYear;
	private String[] cardExpYears;
	private boolean shipisbill = false;

	/**
	 * Constructor to create an OrderInfo by passing each field.
	 */
	public OrderInfo(String billName, String billAddr1, String billAddr2, String billCity, String billState,
			String billZip, String billPhone, String shipName, String shipAddr1, String shipAddr2, String shipCity,
			String shipState, String shipZip, String shipPhone, int shippingMethod, String orderID) {
		this.orderID = orderID;
		this.billName = billName;
		this.billAddr1 = billAddr1;
		this.billAddr2 = billAddr2;
		this.billCity = billCity;
		this.billState = billState;
		this.billZip = billZip;
		this.billPhone = billPhone;
		this.shipName = shipName;
		this.shipAddr1 = shipAddr1;
		this.shipAddr2 = shipAddr2;
		this.shipCity = shipCity;
		this.shipState = shipState;
		this.shipZip = shipZip;
		this.shipPhone = shipPhone;
		this.shippingMethod = shippingMethod;
		initLists();
		cardholderName = "";
		cardNum = "";
	}

	/**
	 * Constructor to create an OrderInfo using an Order.
	 * 
	 * @param order
	 */
	public OrderInfo(Order order) {
		orderID = order.getOrderID();
		billName = order.getBillName();
		billAddr1 = order.getBillAddr1();
		billAddr2 = order.getBillAddr2();
		billCity = order.getBillCity();
		billState = order.getBillState();
		billZip = order.getBillZip();
		billPhone = order.getBillPhone();
		shipName = order.getShipName();
		shipAddr1 = order.getShipAddr1();
		shipAddr2 = order.getShipAddr2();
		shipCity = order.getShipCity();
		shipState = order.getShipState();
		shipZip = order.getShipZip();
		shipPhone = order.getShipPhone();
		shippingMethod = order.getShippingMethod();
	}

	/**
	 * Get the shipping method name.
	 */
	public String getShippingMethodName() {
		return getShippingMethods()[shippingMethod];
	}

	/**
	 * Set the shipping method by name
	 */
	public void setShippingMethodName(String name) {
		String[] methodNames = Util.getShippingMethodStrings();
		for (int i = 0; i < methodNames.length; i++) {
			if (methodNames[i].equals(name))
				shippingMethod = i;
		}
	}

	/**
	 * Get shipping methods that are possible.
	 * 
	 * @return String[] of method names
	 */
	public String[] getShippingMethods() {
		return Util.getFullShippingMethodStrings();
	}

	public int getShippingMethodCount() {
		return Util.getShippingMethodStrings().length;
	}

	private void initLists() {
		int i = Calendar.getInstance().get(1);
		cardExpYears = new String[5];
		for (int j = 0; j < 5; j++)
			cardExpYears[j] = (new Integer(i + j)).toString();
	}

	/**
	 * @return the orderID
	 */
	public String getID() {
		return orderID;
	}

	/**
	 * @param orderID
	 *            the orderID to set
	 */
	public void setID(String orderID) {
		this.orderID = orderID;
	}

	/**
	 * @return the billName
	 */
	public String getBillName() {
		return billName;
	}

	/**
	 * @param billName
	 *            the billName to set
	 */
	public void setBillName(String billName) {
		this.billName = billName;
	}

	/**
	 * @return the billAddr1
	 */
	public String getBillAddr1() {
		return billAddr1;
	}

	/**
	 * @param billAddr1
	 *            the billAddr1 to set
	 */
	public void setBillAddr1(String billAddr1) {
		this.billAddr1 = billAddr1;
	}

	/**
	 * @return the billAddr2
	 */
	public String getBillAddr2() {
		return billAddr2;
	}

	/**
	 * @param billAddr2
	 *            the billAddr2 to set
	 */
	public void setBillAddr2(String billAddr2) {
		this.billAddr2 = billAddr2;
	}

	/**
	 * @return the billCity
	 */
	public String getBillCity() {
		return billCity;
	}

	/**
	 * @param billCity
	 *            the billCity to set
	 */
	public void setBillCity(String billCity) {
		this.billCity = billCity;
	}

	/**
	 * @return the billState
	 */
	public String getBillState() {
		return billState;
	}

	/**
	 * @param billState
	 *            the billState to set
	 */
	public void setBillState(String billState) {
		this.billState = billState;
	}

	/**
	 * @return the billZip
	 */
	public String getBillZip() {
		return billZip;
	}

	/**
	 * @param billZip
	 *            the billZip to set
	 */
	public void setBillZip(String billZip) {
		this.billZip = billZip;
	}

	/**
	 * @return the billPhone
	 */
	public String getBillPhone() {
		return billPhone;
	}

	/**
	 * @param billPhone
	 *            the billPhone to set
	 */
	public void setBillPhone(String billPhone) {
		this.billPhone = billPhone;
	}

	/**
	 * @return the shipName
	 */
	public String getShipName() {
		return shipName;
	}

	/**
	 * @param shipName
	 *            the shipName to set
	 */
	public void setShipName(String shipName) {
		this.shipName = shipName;
	}

	/**
	 * @return the shipAddr1
	 */
	public String getShipAddr1() {
		return shipAddr1;
	}

	/**
	 * @param shipAddr1
	 *            the shipAddr1 to set
	 */
	public void setShipAddr1(String shipAddr1) {
		this.shipAddr1 = shipAddr1;
	}

	/**
	 * @return the shipAddr2
	 */
	public String getShipAddr2() {
		return shipAddr2;
	}

	/**
	 * @param shipAddr2
	 *            the shipAddr2 to set
	 */
	public void setShipAddr2(String shipAddr2) {
		this.shipAddr2 = shipAddr2;
	}

	/**
	 * @return the shipCity
	 */
	public String getShipCity() {
		return shipCity;
	}

	/**
	 * @param shipCity
	 *            the shipCity to set
	 */
	public void setShipCity(String shipCity) {
		this.shipCity = shipCity;
	}

	/**
	 * @return the shipState
	 */
	public String getShipState() {
		return shipState;
	}

	/**
	 * @param shipState
	 *            the shipState to set
	 */
	public void setShipState(String shipState) {
		this.shipState = shipState;
	}

	/**
	 * @return the shipZip
	 */
	public String getShipZip() {
		return shipZip;
	}

	/**
	 * @param shipZip
	 *            the shipZip to set
	 */
	public void setShipZip(String shipZip) {
		this.shipZip = shipZip;
	}

	/**
	 * @return the shipPhone
	 */
	public String getShipPhone() {
		return shipPhone;
	}

	/**
	 * @param shipPhone
	 *            the shipPhone to set
	 */
	public void setShipPhone(String shipPhone) {
		this.shipPhone = shipPhone;
	}

	/**
	 * @return the shippingMethod
	 */
	public int getShippingMethod() {
		return shippingMethod;
	}

	/**
	 * @param shippingMethod
	 *            the shippingMethod to set
	 */
	public void setShippingMethod(int shippingMethod) {
		this.shippingMethod = shippingMethod;
	}

	/**
	 * @return the cardholderName
	 */
	public String getCardholderName() {
		return cardholderName;
	}

	/**
	 * @param cardholderName
	 *            the cardholderName to set
	 */
	public void setCardholderName(String cardholderName) {
		this.cardholderName = cardholderName;
	}

	/**
	 * @return the cardName
	 */
	public String getCardName() {
		return cardName;
	}

	/**
	 * @param cardName
	 *            the cardName to set
	 */
	public void setCardName(String cardName) {
		this.cardName = cardName;
	}

	/**
	 * @return the cardNum
	 */
	public String getCardNum() {
		return cardNum;
	}

	/**
	 * @param cardNum
	 *            the cardNum to set
	 */
	public void setCardNum(String cardNum) {
		this.cardNum = cardNum;
	}

	/**
	 * @return the cardExpMonth
	 */
	public String getCardExpMonth() {
		return cardExpMonth;
	}

	/**
	 * @param cardExpMonth
	 *            the cardExpMonth to set
	 */
	public void setCardExpMonth(String cardExpMonth) {
		this.cardExpMonth = cardExpMonth;
	}

	/**
	 * @return the cardExpYear
	 */
	public String getCardExpYear() {
		return cardExpYear;
	}

	/**
	 * @param cardExpYear
	 *            the cardExpYear to set
	 */
	public void setCardExpYear(String cardExpYear) {
		this.cardExpYear = cardExpYear;
	}

	/**
	 * @return the cardExpYears
	 */
	public String[] getCardExpYears() {
		return cardExpYears;
	}

	/**
	 * @param cardExpYears
	 *            the cardExpYears to set
	 */
	public void setCardExpYears(String[] cardExpYears) {
		this.cardExpYears = cardExpYears;
	}

	/**
	 * @return the shipisbill
	 */
	public boolean isShipisbill() {
		return shipisbill;
	}

	/**
	 * @param shipisbill
	 *            the shipisbill to set
	 */
	public void setShipisbill(boolean shipisbill) {
		this.shipisbill = shipisbill;
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

import java.io.Serializable;

import javax.validation.constraints.Min;

import com.ibm.websphere.samples.pbw.jpa.BackOrder;
import com.ibm.websphere.samples.pbw.jpa.Inventory;

/**
 * ShoppingItem wraps the JPA Inventory entity class to provide additional methods needed by the web
 * app.
 */
public class ShoppingItem implements Cloneable, Serializable {

	private static final long serialVersionUID = 1L;
	private Inventory item;

	public ShoppingItem() {

	}

	public ShoppingItem(Inventory i) {
		item = i;
	}

	public ShoppingItem(String key, String name, String heading, String desc, String pkginfo, String image, float price,
			float cost, int quantity, int category, String notes, boolean isPublic) {
		item = new Inventory(key, name, heading, desc, pkginfo, image, price, cost, quantity, category, notes,
				isPublic);
	}

	/**
	 * Subtotal price calculates a cost based on price and quantity.
	 */
	public float getSubtotalPrice() {
		return getPrice() * getQuantity();
	}

	/**
	 * @param o
	 * @return boolean true if object equals this
	 * @see java.lang.Object#equals(java.lang.Object)
	 */
	public boolean equals(Object o) {
		return item.equals(o);
	}

	/**
	 * @return int hashcode for this object
	 * @see java.lang.Object#hashCode()
	 */
	public int hashCode() {
		return item.hashCode();
	}

	/**
	 * @return String String representation of this object
	 * @see java.lang.Object#toString()
	 */
	public String toString() {
		return item.toString();
	}

	/**
	 * @param quantity
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#increaseInventory(int)
	 */
	public void increaseInventory(int quantity) {
		item.increaseInventory(quantity);
	}

	/**
	 * @return int category enum int value
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getCategory()
	 */
	public int getCategory() {
		return item.getCategory();
	}

	/**
	 * @param category
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setCategory(int)
	 */
	public void setCategory(int category) {
		item.setCategory(category);
	}

	/**
	 * @return float cost of the item
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getCost()
	 */
	public float getCost() {
		return item.getCost();
	}

	/**
	 * @param cost
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setCost(float)
	 */
	public void setCost(float cost) {
		item.setCost(cost);
	}

	/**
	 * @return String description of the item
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getDescription()
	 */
	public String getDescription() {
		return item.getDescription();
	}

	/**
	 * @param description
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setDescription(java.lang.String)
	 */
	public void setDescription(String description) {
		item.setDescription(description);
	}

	/**
	 * @return String item heading
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getHeading()
	 */
	public String getHeading() {
		return item.getHeading();
	}

	/**
	 * @param heading
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setHeading(java.lang.String)
	 */
	public void setHeading(String heading) {
		item.setHeading(heading);
	}

	/**
	 * @return String image URI
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getImage()
	 */
	public String getImage() {
		return item.getImage();
	}

	/**
	 * @param image
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setImage(java.lang.String)
	 */
	public void setImage(String image) {
		item.setImage(image);
	}

	/**
	 * @return String name of the item
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getName()
	 */
	public String getName() {
		return item.getName();
	}

	/**
	 * @param name
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setName(java.lang.String)
	 */
	public void setName(String name) {
		item.setName(name);
	}

	/**
	 * @return String item notes
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getNotes()
	 */
	public String getNotes() {
		return item.getNotes();
	}

	/**
	 * @param notes
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setNotes(java.lang.String)
	 */
	public void setNotes(String notes) {
		item.setNotes(notes);
	}

	/**
	 * @return String package information
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getPkginfo()
	 */
	public String getPkginfo() {
		return item.getPkginfo();
	}

	/**
	 * @param pkginfo
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setPkginfo(java.lang.String)
	 */
	public void setPkginfo(String pkginfo) {
		item.setPkginfo(pkginfo);
	}

	/**
	 * @return float Price of the item
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getPrice()
	 */
	public float getPrice() {
		return item.getPrice();
	}

	/**
	 * @param price
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setPrice(float)
	 */
	public void setPrice(float price) {
		item.setPrice(price);
	}

	/**
	 * Property accessor for quantity of items ordered. Quantity may not be less than zero. Bean
	 * Validation will ensure this is true.
	 * 
	 * @return int quantity of items
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getQuantity()
	 */
	@Min(value = 0, message = "Quantity must be a number greater than or equal to zero.")
	public int getQuantity() {
		return item.getQuantity();
	}

	/**
	 * @param quantity
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setQuantity(int)
	 */
	public void setQuantity(int quantity) {
		item.setQuantity(quantity);
	}

	/**
	 * @return int maximum threshold
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getMaxThreshold()
	 */
	public int getMaxThreshold() {
		return item.getMaxThreshold();
	}

	/**
	 * @param maxThreshold
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setMaxThreshold(int)
	 */
	public void setMaxThreshold(int maxThreshold) {
		item.setMaxThreshold(maxThreshold);
	}

	/**
	 * @return int minimum threshold
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getMinThreshold()
	 */
	public int getMinThreshold() {
		return item.getMinThreshold();
	}

	/**
	 * @param minThreshold
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setMinThreshold(int)
	 */
	public void setMinThreshold(int minThreshold) {
		item.setMinThreshold(minThreshold);
	}

	/**
	 * @return String item ID in the inventory
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getInventoryId()
	 */
	public String getInventoryId() {
		return item.getInventoryId();
	}

	/**
	 * @param id
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setInventoryId(java.lang.String)
	 */
	public void setInventoryId(String id) {
		item.setInventoryId(id);
	}

	/**
	 * @return String item ID
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getID()
	 */
	public String getID() {
		return item.getID();
	}

	/**
	 * @param id
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setID(java.lang.String)
	 */
	public void setID(String id) {
		item.setID(id);
	}

	/**
	 * @return boolean true if this is a public item
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#isPublic()
	 */
	public boolean isPublic() {
		return item.isPublic();
	}

	/**
	 * @param isPublic
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setIsPublic(boolean)
	 */
	public void setIsPublic(boolean isPublic) {
		item.setIsPublic(isPublic);
	}

	/**
	 * @param isPublic
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setPrivacy(boolean)
	 */
	public void setPrivacy(boolean isPublic) {
		item.setPrivacy(isPublic);
	}

	/**
	 * @return byte[] item image as a byte array
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getImgbytes()
	 */
	public byte[] getImgbytes() {
		return item.getImgbytes();
	}

	/**
	 * @param imgbytes
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setImgbytes(byte[])
	 */
	public void setImgbytes(byte[] imgbytes) {
		item.setImgbytes(imgbytes);
	}

	/**
	 * @return BackOrder item is on back order
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#getBackOrder()
	 */
	public BackOrder getBackOrder() {
		return item.getBackOrder();
	}

	/**
	 * @param backOrder
	 * @see com.ibm.websphere.samples.pbw.jpa.Inventory#setBackOrder(com.ibm.websphere.samples.pbw.jpa.BackOrder)
	 */
	public void setBackOrder(BackOrder backOrder) {
		item.setBackOrder(backOrder);
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

import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;

/**
 * A JSF backing bean used to store information for the login web page. It is accessed via the
 * account bean.
 *
 */
public class LoginInfo {
	private String checkPassword;

	@Pattern(regexp = "[a-zA-Z0-9_-]+@[a-zA-Z0-9.-]+")
	private String email;
	private String message;

	@Size(min = 6, max = 10, message = "Password must be between 6 and 10 characters.")
	private String password;

	public LoginInfo() {
	}

	public String getCheckPassword() {
		return this.checkPassword;
	}

	public String getEmail() {
		return this.email;
	}

	public String getMessage() {
		return this.message;
	}

	public String getPassword() {
		return this.password;
	}

	public void setCheckPassword(String checkPassword) {
		this.checkPassword = checkPassword;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public void setMessage(String message) {
		this.message = message;
	}

	public void setPassword(String password) {
		this.password = password;
	}
}


