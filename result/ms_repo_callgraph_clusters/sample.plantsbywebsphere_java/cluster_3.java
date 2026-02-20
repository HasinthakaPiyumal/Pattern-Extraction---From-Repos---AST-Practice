// Cluster 3

// Node: getStatus
// Node: getInventory
// Node: setPhone
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
package com.ibm.websphere.samples.pbw.bean;

import java.io.Serializable;
import java.util.Collection;
import java.util.Iterator;

import javax.enterprise.context.Dependent;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.persistence.Query;

import com.ibm.websphere.samples.pbw.jpa.Supplier;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Bean implementation class for Enterprise Bean: Suppliers
 */
@Dependent
public class SuppliersBean implements Serializable {

	@PersistenceContext(unitName = "PBW")
	EntityManager em;

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
	public void createSupplier(String supplierID,
			String name,
			String street,
			String city,
			String state,
			String zip,
			String phone,
			String url) {
		try {
			Util.debug("SuppliersBean.createSupplier() - Entered");
			Supplier supplier = null;
			supplier = em.find(Supplier.class, supplierID);
			if (supplier == null) {
				Util.debug("SuppliersBean.createSupplier() - supplier doesn't exist.");
				Util.debug("SuppliersBean.createSupplier() - Creating Supplier for SupplierID: " + supplierID);
				supplier = new Supplier(supplierID, name, street, city, state, zip, phone, url);
				em.persist(supplier);
			}
		} catch (Exception e) {
			Util.debug("SuppliersBean.createSupplier() - Exception: " + e);
		}
	}

	/**
	 * @return Supplier
	 */
	public Supplier getSupplier() {
		// Retrieve the first Supplier Info
		try {
			Collection<Supplier> suppliers = this.findSuppliers();
			if (suppliers != null) {
				Util.debug("AdminServlet.getSupplierInfo() - Supplier found!");
				Iterator<Supplier> i = suppliers.iterator();
				if (i.hasNext()) {
					return (Supplier) i.next();
				}
			}
		} catch (Exception e) {
			Util.debug("AdminServlet.getSupplierInfo() - Exception:" + e);
		}
		return null;
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
	 * @return supplierInfo
	 */
	public Supplier updateSupplier(String supplierID,
			String name,
			String street,
			String city,
			String state,
			String zip,
			String phone,
			String url) {
		Supplier supplier = null;
		try {
			Util.debug("SuppliersBean.updateSupplier() - Entered");
			supplier = em.find(Supplier.class, supplierID);
			if (supplier != null) {
				// Create a new Supplier if there is NOT an existing Supplier.
				// supplier = getSupplierLocalHome().findByPrimaryKey(new SupplierKey(supplierID));
				supplier.setName(name);
				supplier.setStreet(street);
				supplier.setCity(city);
				supplier.setUsstate(state);
				supplier.setZip(zip);
				supplier.setPhone(phone);
				supplier.setUrl(url);
			} else {
				Util.debug("SuppliersBean.updateSupplier() - supplier doesn't exist.");
				Util.debug("SuppliersBean.updateSupplier() - Couldn't update Supplier for SupplierID: " + supplierID);
			}
		} catch (Exception e) {
			Util.debug("SuppliersBean.createSupplier() - Exception: " + e);
		}
		return (supplier);
	}

	/**
	 * @return suppliers
	 */
	@SuppressWarnings("unchecked")
	private Collection<Supplier> findSuppliers() {
		Query q = em.createNamedQuery("findAllSuppliers");
		return q.getResultList();
	}
}


// Node: getSupplierInfo
// Node: iterator
// Node: hasNext
// Node: next
// Node: getSupplierLocalHome
// Node: SupplierKey
// Node: setName
// Node: setStreet
// Node: setCity
// Node: setUsstate
// Node: setZip
// Node: setUrl
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

// Node: getName
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


// Node: setSupplierID
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


// Node: getLowDate
// Node: getOrderDate
// Node: getSupplierOrderID
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


// Node: BackOrderItem
// Node: setInventoryQuantity
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

import java.io.IOException;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Iterator;

import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.pbw.bean.BackOrderMgr;
import com.ibm.websphere.samples.pbw.bean.CatalogMgr;
import com.ibm.websphere.samples.pbw.bean.CustomerMgr;
import com.ibm.websphere.samples.pbw.bean.ResetDBBean;
import com.ibm.websphere.samples.pbw.bean.SuppliersBean;
import com.ibm.websphere.samples.pbw.jpa.BackOrder;
import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.jpa.Supplier;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Servlet to handle Administration actions
 */
@Named(value = "admin")
@WebServlet("/servlet/AdminServlet")
public class AdminServlet extends HttpServlet {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	@Inject
	private SuppliersBean suppliers = null;
	@Inject
	private CustomerMgr login;
	@Inject
	private BackOrderMgr backOrderStock = null;

	@Inject
	private CatalogMgr catalog = null;

	@Inject
	private ResetDBBean resetDB;

	/**
	 * @see javax.servlet.Servlet#init(ServletConfig)
	 */
	/**
	 * Servlet initialization.
	 */
	public void init(ServletConfig config) throws ServletException {
		super.init(config);
		// Uncomment the following to generated debug code.
		// Util.setDebug(true);

	}

	/**
	 * Process incoming HTTP GET requests
	 *
	 * @param req
	 *            Object that encapsulates the request to the servlet
	 * @param resp
	 *            Object that encapsulates the response from the servlet
	 */
	public void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		performTask(req, resp);
	}

	/**
	 * Process incoming HTTP POST requests
	 *
	 * @param req
	 *            Object that encapsulates the request to the servlet
	 * @param resp
	 *            Object that encapsulates the response from the servlet
	 */
	public void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		performTask(req, resp);
	}

	/**
	 * Method performTask.
	 * 
	 * @param req
	 * @param resp
	 * @throws ServletException
	 * @throws IOException
	 */
	public void performTask(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		String admintype = null;
		admintype = req.getParameter(Util.ATTR_ADMINTYPE);
		Util.debug("inside AdminServlet:performTask. admintype=" + admintype);
		if ((admintype == null) || (admintype.equals(""))) {
			// Invalid Admin
			requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_ADMINHOME);
		}
		if (admintype.equals(Util.ADMIN_BACKORDER)) {
			performBackOrder(req, resp);
		} else if (admintype.equals(Util.ADMIN_SUPPLIERCFG)) {
			performSupplierConfig(req, resp);
		} else if (admintype.equals(Util.ADMIN_POPULATE)) {
			performPopulate(req, resp);
		}
	}

	/**
	 * @param supplierID
	 * @param name
	 * @param street
	 * @param city
	 * @param state
	 * @param zip
	 * @param phone
	 * @param location_url
	 * @return supplierInfo
	 */
	public Supplier updateSupplierInfo(String supplierID,
			String name,
			String street,
			String city,
			String state,
			String zip,
			String phone,
			String location_url) {
		// Only retrieving info for 1 supplier.
		Supplier supplier = null;
		try {
			supplier = suppliers.updateSupplier(supplierID, name, street, city, state, zip, phone, location_url);
		} catch (Exception e) {
			Util.debug("AdminServlet.updateSupplierInfo() - Exception: " + e);
		}
		return (supplier);
	}

	/**
	 * @param req
	 * @param resp
	 * @throws ServletException
	 * @throws IOException
	 */
	public void performSupplierConfig(HttpServletRequest req,
			HttpServletResponse resp) throws ServletException, IOException {
		Supplier supplier = null;
		String action = null;
		action = req.getParameter(Util.ATTR_ACTION);
		if ((action == null) || (action.equals("")))
			action = Util.ACTION_GETSUPPLIER;
		Util.debug("AdminServlet.performSupplierConfig() - action=" + action);
		HttpSession session = req.getSession(true);
		if (action.equals(Util.ACTION_GETSUPPLIER)) {
			// Get supplier info
			try {
				supplier = suppliers.getSupplier();
			} catch (Exception e) {
				Util.debug("AdminServlet.performSupplierConfig() Exception: " + e);
			}
		} else if (action.equals(Util.ACTION_UPDATESUPPLIER)) {
			String supplierID = req.getParameter("supplierid");
			Util.debug("AdminServlet.performSupplierConfig() - supplierid = " + supplierID);
			if ((supplierID != null) && (!supplierID.equals(""))) {
				String name = req.getParameter("name");
				String street = req.getParameter("street");
				String city = req.getParameter("city");
				String state = req.getParameter("state");
				String zip = req.getParameter("zip");
				String phone = req.getParameter("phone");
				String location_url = req.getParameter("location_url");
				supplier = updateSupplierInfo(supplierID, name, street, city, state, zip, phone, location_url);
			}
		} else {
			// Unknown Supplier Config Admin Action so go back to the
			// Administration home page
			sendRedirect(resp, "/PlantsByWebSphere/" + Util.PAGE_ADMINHOME);
		}
		session.setAttribute(Util.ATTR_SUPPLIER, supplier);
		requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_SUPPLIERCFG);
	}

	/**
	 * @param req
	 * @param resp
	 * @throws ServletException
	 * @throws IOException
	 */
	public void performPopulate(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		Populate popDB = new Populate(resetDB, catalog, login, backOrderStock, suppliers);
		popDB.doPopulate();
		sendRedirect(resp, "/PlantsByWebSphere/" + Util.PAGE_HELP);
	}

	/**
	 * Method performBackOrder.
	 * 
	 * @param req
	 * @param resp
	 * @throws ServletException
	 * @throws IOException
	 */
	public void performBackOrder(HttpServletRequest req,
			HttpServletResponse resp) throws ServletException, IOException {
		String action = null;
		action = req.getParameter(Util.ATTR_ACTION);
		if ((action == null) || (action.equals("")))
			action = Util.ACTION_GETBACKORDERS;
		Util.debug("AdminServlet.performBackOrder() - action=" + action);
		HttpSession session = req.getSession(true);
		if (action.equals(Util.ACTION_GETBACKORDERS)) {
			getBackOrders(session);
			requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_BACKADMIN);
		} else if (action.equals(Util.ACTION_UPDATESTOCK)) {
			Util.debug("AdminServlet.performBackOrder() - AdminServlet(performTask):  Update Stock Action");
			String[] backOrderIDs = (String[]) req.getParameterValues("selectedObjectIds");
			if (backOrderIDs != null) {
				for (int i = 0; i < backOrderIDs.length; i++) {
					String backOrderID = backOrderIDs[i];
					Util.debug("AdminServlet.performBackOrder() - Selected BackOrder backOrderID: " + backOrderID);
					try {
						String inventoryID = backOrderStock.getBackOrderInventoryID(backOrderID);
						Util.debug("AdminServlet.performBackOrder() - backOrderID = " + inventoryID);
						int quantity = backOrderStock.getBackOrderQuantity(backOrderID);
						catalog.setItemQuantity(inventoryID, quantity);
						// Update the BackOrder status
						Util.debug("AdminServlet.performBackOrder() - quantity: " + quantity);
						backOrderStock.updateStock(backOrderID, quantity);
					} catch (Exception e) {
						Util.debug("AdminServlet.performBackOrder() - Exception: " + e);
						e.printStackTrace();
					}
				}
			}
			getBackOrders(session);
			requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_BACKADMIN);
		} else if (action.equals(Util.ACTION_CANCEL)) {
			Util.debug("AdminServlet.performBackOrder() - AdminServlet(performTask):  Cancel Action");
			String[] backOrderIDs = (String[]) req.getParameterValues("selectedObjectIds");
			if (backOrderIDs != null) {
				for (int i = 0; i < backOrderIDs.length; i++) {
					String backOrderID = backOrderIDs[i];
					Util.debug("AdminServlet.performBackOrder() - Selected BackOrder backOrderID: " + backOrderID);
					try {
						backOrderStock.deleteBackOrder(backOrderID);
					} catch (Exception e) {
						Util.debug("AdminServlet.performBackOrder() - Exception: " + e);
						e.printStackTrace();
					}
				}
			}
			getBackOrders(session);
			requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_BACKADMIN);
		} else if (action.equals(Util.ACTION_UPDATEQUANTITY)) {
			Util.debug("AdminServlet.performBackOrder() -  Update Quantity Action");
			try {
				String backOrderID = req.getParameter("backOrderID");
				if (backOrderID != null) {
					Util.debug("AdminServlet.performBackOrder() - backOrderID = " + backOrderID);
					String paramquantity = req.getParameter("itemqty");
					if (paramquantity != null) {
						int quantity = new Integer(paramquantity).intValue();
						Util.debug("AdminServlet.performBackOrder() - quantity: " + quantity);
						backOrderStock.setBackOrderQuantity(backOrderID, quantity);
					}
				}
			} catch (Exception e) {
				Util.debug("AdminServlet.performBackOrder() - Exception: " + e);
				e.printStackTrace();
			}
			getBackOrders(session);
			requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_BACKADMIN);
		} else {
			// Unknown Backup Admin Action so go back to the Administration home
			// page
			sendRedirect(resp, "/PlantsByWebSphere/" + Util.PAGE_ADMINHOME);
		}
	}

	/**
	 * Method getBackOrders.
	 * 
	 * @param session
	 */
	public void getBackOrders(HttpSession session) {
		try {
			// Get the list of back order items.
			Util.debug("AdminServlet.getBackOrders() - Looking for BackOrders");
			Collection<BackOrder> backOrders = backOrderStock.findBackOrders();
			ArrayList<BackOrderItem> backOrderItems = new ArrayList<BackOrderItem>();
			for (BackOrder bo : backOrders) {
				BackOrderItem boi = new BackOrderItem(bo);
				backOrderItems.add(boi);
			}
			Util.debug("AdminServlet.getBackOrders() - BackOrders found!");
			Iterator<BackOrderItem> i = backOrderItems.iterator();
			while (i.hasNext()) {
				BackOrderItem backOrderItem = (BackOrderItem) i.next();
				String backOrderID = backOrderItem.getBackOrderID();
				String inventoryID = backOrderItem.getInventory().getInventoryId();
				// Get the inventory quantity and name for the back order item
				// information.
				Inventory item = catalog.getItemInventory(inventoryID);
				int quantity = item.getQuantity();
				backOrderItem.setInventoryQuantity(quantity);
				String name = item.getName();
				backOrderItem.setName(name);
				// Don't include backorders that have been completed.
				if (!(backOrderItem.getStatus().equals(Util.STATUS_ADDEDSTOCK))) {
					String invID = backOrderItem.getInventory().getInventoryId();
					String supplierOrderID = backOrderItem.getSupplierOrderID();
					String status = backOrderItem.getStatus();
					String lowDate = new Long(backOrderItem.getLowDate()).toString();
					String orderDate = new Long(backOrderItem.getOrderDate()).toString();
					Util.debug("AdminServlet.getBackOrders() - backOrderID = " + backOrderID);
					Util.debug("AdminServlet.getBackOrders() -    supplierOrderID = " + supplierOrderID);
					Util.debug("AdminServlet.getBackOrders() -    invID = " + invID);
					Util.debug("AdminServlet.getBackOrders() -    name = " + name);
					Util.debug("AdminServlet.getBackOrders() -    quantity = " + quantity);
					Util.debug("AdminServlet.getBackOrders() -    status = " + status);
					Util.debug("AdminServlet.getBackOrders() -    lowDate = " + lowDate);
					Util.debug("AdminServlet.getBackOrders() -    orderDate = " + orderDate);
				}
			}
			session.setAttribute("backorderitems", backOrderItems);
		} catch (Exception e) {
			e.printStackTrace();
			Util.debug("AdminServlet.getBackOrders() - RemoteException: " + e);
		}
	}

	/**
	 * Method sendRedirect.
	 * 
	 * @param resp
	 * @param page
	 * @throws ServletException
	 * @throws IOException
	 */
	private void sendRedirect(HttpServletResponse resp, String page) throws ServletException, IOException {
		resp.sendRedirect(resp.encodeRedirectURL(page));
	}

	/**
	 * Method requestDispatch.
	 * 
	 * @param ctx
	 * @param req
	 * @param resp
	 * @param page
	 * @throws ServletException
	 * @throws IOException
	 */
	/**
	 * Request dispatch
	 */
	private void requestDispatch(ServletContext ctx,
			HttpServletRequest req,
			HttpServletResponse resp,
			String page) throws ServletException, IOException {
		resp.setContentType("text/html");
		ctx.getRequestDispatcher(page).forward(req, resp);
	}
}


// Node: Long
// Node: encodeRedirectURL
// Node: forward
