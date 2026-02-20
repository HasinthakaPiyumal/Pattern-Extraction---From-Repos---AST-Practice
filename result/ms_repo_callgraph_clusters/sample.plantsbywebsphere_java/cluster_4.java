// Cluster 4

// Node: equals
// Node: Named
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


// Node: getCategoryStrings
// Node: addAll
// Node: getItemsByCategory
// Node: getSupplier
// Node: updateSupplier
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/jpa/OrderKey.java:of.equals
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
package com.ibm.websphere.samples.pbw.utils;

import java.io.FileNotFoundException;
import java.text.NumberFormat;
import java.util.StringTokenizer;

import javax.faces.application.Application;
import javax.faces.application.ProjectStage;
import javax.faces.context.FacesContext;
import javax.naming.InitialContext;
import javax.naming.NamingException;

/**
 *  Utility class.
 */
public class Util {
    /** Datasource name. */
    public static final String DS_NAME = "java:comp/env/jdbc/PlantsByWebSphereDataSource";
    // Constants for JSPs and HTMLs.
    public static final String PAGE_ACCOUNT = "account.jsp";
    public static final String PAGE_CART = "cart.jsp";
    public static final String PAGE_CHECKOUTFINAL = "checkout_final.jsp";
    public static final String PAGE_HELP = "help.jsp";
    public static final String PAGE_LOGIN = "login.jsp";
    public static final String PAGE_ORDERDONE = "orderdone.jsp";
    public static final String PAGE_ORDERINFO = "orderinfo.jsp";
    public static final String PAGE_PRODUCT = "product.jsp";
    public static final String PAGE_PROMO = "promo.html";
    public static final String PAGE_REGISTER = "register.jsp";
    public static final String PAGE_SHOPPING = "shopping.jsp";
    public static final String PAGE_BACKADMIN = "backorderadmin.jsp";
    public static final String PAGE_SUPPLIERCFG = "supplierconfig.jsp";
    public static final String PAGE_ADMINHOME = "admin.html";
    public static final String PAGE_ADMINACTIONS = "adminactions.html";
    // Request and session attributes.
    public static final String ATTR_ACTION = "action";
    public static final String ATTR_CART = "ShoppingCart";
//    public static final String ATTR_CART_CONTENTS = "CartContents";
    public static final String ATTR_CARTITEMS = "cartitems";
    public static final String ATTR_CATEGORY = "Category";
    public static final String ATTR_CHECKOUT = "CheckingOut";
    public static final String ATTR_CUSTOMER = "CustomerInfo";
    public static final String ATTR_EDITACCOUNTINFO = "EditAccountInfo";
    public static final String ATTR_INVITEM = "invitem";
    public static final String ATTR_INVITEMS = "invitems";
    public static final String ATTR_ORDERID = "OrderID";
    public static final String ATTR_ORDERINFO = "OrderInfo";
    public static final String ATTR_ORDERKEY = "OrderKey";
    public static final String ATTR_RESULTS = "results";
    public static final String ATTR_UPDATING = "updating";
    public static final int    ATTR_SFTIMEOUT = 10;				// if this is changed, updated session timeout
    															// in the PlantsByWebSphere web.xml
    public static final String ATTR_SUPPLIER = "SupplierInfo";
    // Admin type actions
    public static final String ATTR_ADMINTYPE = "admintype";
    public static final String ADMIN_BACKORDER = "backorder";
    public static final String ADMIN_SUPPLIERCFG = "supplierconfig";
    public static final String ADMIN_POPULATE = "populate";
    // Servlet action codes.
    // Supplier Config actions
    public static final String ACTION_GETSUPPLIER = "getsupplier";
    public static final String ACTION_UPDATESUPPLIER = "updatesupplier";
    // Backorder actions
    public static final String ACTION_ORDERSTOCK = "orderstock";
    public static final String ACTION_UPDATESTOCK = "updatestock";
    public static final String ACTION_GETBACKORDERS = "getbackorders";
    public static final String ACTION_UPDATEQUANTITY = "updatequantity";
    public static final String ACTION_ORDERSTATUS = "orderstatus";
    public static final String ACTION_CANCEL = "cancel";
    public static final String STATUS_ORDERSTOCK = "Order Stock";
    public static final String STATUS_ORDEREDSTOCK = "Ordered Stock";
    public static final String STATUS_RECEIVEDSTOCK = "Received Stock";
    public static final String STATUS_ADDEDSTOCK = "Added Stock";
    public static final String DEFAULT_SUPPLIERID = "Supplier";
    private static InitialContext initCtx = null;
    private static final String[] CATEGORY_STRINGS = { "Flowers", "Fruits & Vegetables", "Trees", "Accessories" };
    private static final String[] SHIPPING_METHOD_STRINGS = { "Standard Ground", "Second Day Air", "Next Day Air" };
    private static final String[] SHIPPING_METHOD_TIMES = { "( 3 to 6 business days )", "( 2 to 3 business days )", "( 1 to 2 business days )" };
    private static final float[] SHIPPING_METHOD_PRICES = { 4.99f, 8.99f, 12.99f };
    public static final String ZERO_14 = "00000000000000";
    /**
     * Return the cached Initial Context.
     *
     * @return InitialContext, or null if a naming exception.
     */
    static public InitialContext getInitialContext() {
        try {
            // Get InitialContext if it has not been gotten yet.
            if (initCtx == null) {
                // properties are in the system properties
                initCtx = new InitialContext();
            }
        }
        // Naming Exception will cause a null return.
        catch (NamingException e) {}
        return initCtx;
    }

    /**
     * Get the displayable name of a category.
     * @param index The int representation of a category.
     * @return The category as a String (null, if an invalid index given).
     */
    static public String getCategoryString(int index) {
        if ((index >= 0) && (index < CATEGORY_STRINGS.length))
            return CATEGORY_STRINGS[index];
        else
            return null;
    }
    /**
     * Get the category strings in an array.
     *
     * @return The category strings in an array.
     */
    static public String[] getCategoryStrings() {
        return CATEGORY_STRINGS;
    }
    /**
     * Get the shipping method.
     * @param index The int representation of a shipping method.
     * @return The shipping method (null, if an invalid index given).
     */
    static public String getShippingMethod(int index) {
        if ((index >= 0) && (index < SHIPPING_METHOD_STRINGS.length))
            return SHIPPING_METHOD_STRINGS[index];
        else
            return null;
    }
    /**
     * Get the shipping method price.
     * @param index The int representation of a shipping method.
     * @return The shipping method price (-1, if an invalid index given).
     */
    static public float getShippingMethodPrice(int index) {
        if ((index >= 0) && (index < SHIPPING_METHOD_PRICES.length))
            return SHIPPING_METHOD_PRICES[index];
        else
            return -1;
    }
    /**
     * Get the shipping method price.
     * @param index The int representation of a shipping method.
     * @return The shipping method time (null, if an invalid index given).
     */
    static public String getShippingMethodTime(int index) {
        if ((index >= 0) && (index < SHIPPING_METHOD_TIMES.length))
            return SHIPPING_METHOD_TIMES[index];
        else
            return null;
    }
    /**
     * Get the shipping method strings in an array.
     * @return The shipping method strings in an array.
     */
    static public String[] getShippingMethodStrings() {
        return SHIPPING_METHOD_STRINGS;
    }
    /**
     * Get the shipping method strings, including prices and times, in an array.
     * @return The shipping method strings, including prices and times, in an array.
     */
    static public String[] getFullShippingMethodStrings() {
        String[] shippingMethods = new String[SHIPPING_METHOD_STRINGS.length];
        for (int i = 0; i < shippingMethods.length; i++) {
            shippingMethods[i] = SHIPPING_METHOD_STRINGS[i] + " " + SHIPPING_METHOD_TIMES[i] + " " + NumberFormat.getCurrencyInstance(java.util.Locale.US).format(new Float(SHIPPING_METHOD_PRICES[i]));
        }
        return shippingMethods;
    }
    private static final String PBW_PROPERTIES = "pbw.properties";
    private static ListProperties PBW_Properties = null;
    /**
     * Method readProperties.
     */
    public static void readProperties() throws FileNotFoundException {
        if (PBW_Properties == null) {
            // Try to read the  properties file.
            ListProperties prop = new ListProperties();
            try {
                String PBW_Properties_File = PBW_PROPERTIES;
                debug("Util.readProperties(): Loading PBW Properties from file: " + PBW_Properties_File);
                prop.load(Util.class.getClassLoader().getResourceAsStream(PBW_Properties_File));
            } catch (Exception e) {
                debug("Util.readProperties(): Exception: " + e);
                // Reset properties to retry loading next time.
                PBW_Properties = null;
                e.printStackTrace();
                throw new FileNotFoundException();
            }
            PBW_Properties = prop;
        }
    }
    /**
     * Method getProperty.
     * @param name
     * @return value
     */
    public static String getProperty(String name) {
        String value = "";
        try {
            if (PBW_Properties == null) {
                readProperties();
            }
            value = PBW_Properties.getProperty(name);
        } catch (Exception e) {
            debug("Util.getProperty(): Exception: " + e);
        }
        return (value);
    }
    /**
     * Method readTokens.
     * @param text
     * @param token
     * @return list
     */
    public static String[] readTokens(String text, String token) {
        StringTokenizer parser = new StringTokenizer(text, token);
        int numTokens = parser.countTokens();
        String[] list = new String[numTokens];
        for (int i = 0; i < numTokens; i++) {
            list[i] = parser.nextToken();
        }
        return list;
    }
    /**
     * Method getProperties.
     * @param name
     * @return values
     */
    public static String[] getProperties(String name) {
        String[] values = { "" };
        try {
            if (PBW_Properties == null) {
                readProperties();
            }
            values = PBW_Properties.getProperties(name);
            debug("Util.getProperties: property (" + name + ") -> " + values.toString());
            //for (Enumeration e = PBW_Properties.propertyNames() ; e.hasMoreElements() ;) {
            //    debug((String)e.nextElement());
            //}
        } catch (Exception e) {
            debug("Util.getProperties(): Exception: " + e);
        }
        return (values);
    }
    static private boolean debug = false;
    /** Set debug setting to on or off.
     * @param val True or false.
     */
    static final public void setDebug(boolean val) {
        debug = val;
    }
    /** Is debug turned on? */
    static final public boolean debugOn() {
        return debug;
    }
    /**
     * Output RAS message.
     * @param msg Message to be output.
     */
    static final public void debug(String msg) {
        FacesContext context = FacesContext.getCurrentInstance();
        if (context != null) {
        	Application app = context.getApplication();
        	if (app != null) {
        		ProjectStage stage = app.getProjectStage();
        		if (stage == ProjectStage.Development || stage == ProjectStage.UnitTest) {
        			setDebug(true);
        		}
        	}
        	if (debug) {
        		System.out.println(msg);
        	}
        }
    }

    /**
     * Utilty functions for validating user input.
     * validateString will return false if any of the invalid characters appear in the input string.
     *
     * In general, we do not want to allow special characters in user input,
     * because this can open us to a XSS security vulnerability.
     * For example, a user should not be allowed to enter javascript in an input field.
     */
	static final char[] invalidCharList={'|','&',';','$','%','\'','\"','\\','<','>',','};

	public static boolean validateString(String input){
		if (input==null) return true;
		for (int i=0;i<invalidCharList.length;i++){
			if (input.indexOf(invalidCharList[i])!=-1){
				return false;
			}
		}
		return true;
	}
}


// Node: method
// Node: getShippingMethodStrings
// Node: setDebug
// Node: validateString
// Node: indexOf
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
// (C) COPYRIGHT International Business Machines Corp., 2001,2011
// All Rights Reserved * Licensed Materials - Property of IBM
//
package com.ibm.websphere.samples.pbw.war;

import java.io.IOException;

import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.pbw.bean.CatalogMgr;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Servlet to handle image actions.
 */
@Named(value = "image")
@WebServlet("/servlet/ImageServlet")
public class ImageServlet extends HttpServlet {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	@Inject
	private CatalogMgr catalog;

	/**
	 * Servlet initialization.
	 */
	public void init(ServletConfig config) throws ServletException {
		super.init(config);
	}

	/**
	 * Process incoming HTTP GET requests
	 *
	 * @param request
	 *            Object that encapsulates the request to the servlet
	 * @param response
	 *            Object that encapsulates the response from the servlet
	 */
	public void doGet(javax.servlet.http.HttpServletRequest request,
			javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
		performTask(request, response);
	}

	/**
	 * Process incoming HTTP POST requests
	 *
	 * @param request
	 *            Object that encapsulates the request to the servlet
	 * @param response
	 *            Object that encapsulates the response from the servlet
	 */
	public void doPost(javax.servlet.http.HttpServletRequest request,
			javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
		performTask(request, response);
	}

	/**
	 * Main service method for ImageServlet
	 *
	 * @param request
	 *            Object that encapsulates the request to the servlet
	 * @param response
	 *            Object that encapsulates the response from the servlet
	 */
	private void performTask(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		String action = null;

		action = req.getParameter("action");
		Util.debug("action=" + action);

		if (action.equals("getimage")) {
			String inventoryID = req.getParameter("inventoryID");

			byte[] buf = catalog.getItemImageBytes(inventoryID);
			if (buf != null) {
				resp.setContentType("image/jpeg");
				resp.getOutputStream().write(buf);
			}
		}
	}
}

// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/ImageServlet.java:ImageServlet.<init>
// Node: WebServlet
// Node: init
// Node: doGet
// Node: performTask
// Node: doPost
// Node: getParameter
// Node: setContentType
// Node: getOutputStream
// Node: write
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

import java.io.IOException;

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

import com.ibm.websphere.samples.pbw.bean.CatalogMgr;
import com.ibm.websphere.samples.pbw.bean.CustomerMgr;
import com.ibm.websphere.samples.pbw.jpa.Customer;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Servlet to handle customer account actions, such as login and register.
 */
@Named(value = "accountservlet")
@WebServlet("/servlet/AccountServlet")
public class AccountServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
	// Servlet action codes.
	public static final String ACTION_ACCOUNT = "account";
	public static final String ACTION_ACCOUNTUPDATE = "accountUpdate";
	public static final String ACTION_LOGIN = "login";
	public static final String ACTION_REGISTER = "register";
	public static final String ACTION_SETLOGGING = "SetLogging";

	@Inject
	private CustomerMgr login;
	@Inject
	private CatalogMgr catalog;

	/**
	 * Servlet initialization.
	 */
	public void init(ServletConfig config) throws ServletException {
		super.init(config);
	}

	/**
	 * Process incoming HTTP GET requests
	 *
	 * @param request
	 *            Object that encapsulates the request to the servlet
	 * @param response
	 *            Object that encapsulates the response from the servlet
	 */
	public void doGet(javax.servlet.http.HttpServletRequest request,
			javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
		performTask(request, response);
	}

	/**
	 * Process incoming HTTP POST requests
	 *
	 * @param request
	 *            Object that encapsulates the request to the servlet
	 * @param response
	 *            Object that encapsulates the response from the servlet
	 */
	public void doPost(javax.servlet.http.HttpServletRequest request,
			javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
		performTask(request, response);
	}

	/**
	 * Main service method for AccountServlet
	 *
	 * @param request
	 *            Object that encapsulates the request to the servlet
	 * @param response
	 *            Object that encapsulates the response from the servlet
	 */
	private void performTask(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		String action = null;

		action = req.getParameter(Util.ATTR_ACTION);
		Util.debug("action=" + action);

		if (action.equals(ACTION_LOGIN)) {
			try {
				HttpSession session = req.getSession(true);
				String userid = req.getParameter("userid");
				String passwd = req.getParameter("passwd");
				String updating = req.getParameter(Util.ATTR_UPDATING);

				String results = null;
				if (Util.validateString(userid)) {
					results = login.verifyUserAndPassword(userid, passwd);
				} else {
					// user id was invalid, and may contain XSS attack
					results = "\nEmail address was invalid.";
					Util.debug("User id or email address was invalid. id=" + userid);
				}

				// If results have an error msg, return it, otherwise continue.
				if (results != null) {
					// Proliferate UPDATING flag if user is trying to update his account.
					if (updating.equals("true"))
						req.setAttribute(Util.ATTR_UPDATING, "true");

					req.setAttribute(Util.ATTR_RESULTS, results);
					requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_LOGIN);
				} else {
					// If not logging in for the first time, then clear out the
					// session data for the old user.
					if (session.getAttribute(Util.ATTR_CUSTOMER) != null) {
						session.removeAttribute(Util.ATTR_CART);
						// session.removeAttribute(Util.ATTR_CART_CONTENTS);
						session.removeAttribute(Util.ATTR_CHECKOUT);
						session.removeAttribute(Util.ATTR_ORDERKEY);
					}

					// Store customer userid in HttpSession.
					Customer customer = login.getCustomer(userid);
					session.setAttribute(Util.ATTR_CUSTOMER, customer);
					Util.debug("updating=" + updating + "=");

					// Was customer trying to edit account information.
					if (updating.equals("true")) {
						req.setAttribute(Util.ATTR_EDITACCOUNTINFO, customer);

						requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_ACCOUNT);
					} else {
						// See if user was in the middle of checking out.
						Boolean checkingOut = (Boolean) session.getAttribute(Util.ATTR_CHECKOUT);
						Util.debug("checkingOut=" + checkingOut + "=");
						if ((checkingOut != null) && (checkingOut.booleanValue())) {
							Util.debug("must be checking out");
							requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_ORDERINFO);
						} else {
							Util.debug("must NOT be checking out");
							String url;
							String category = (String) session.getAttribute(Util.ATTR_CATEGORY);

							// Default to plants
							if ((category == null) || (category.equals("null"))) {
								url = Util.PAGE_PROMO;
							} else {
								url = Util.PAGE_SHOPPING;
								req.setAttribute(Util.ATTR_INVITEMS, catalog
										.getItemsByCategory(Integer.parseInt(category)));
							}

							requestDispatch(getServletConfig().getServletContext(), req, resp, url);
						}
					}
				}
			} catch (ServletException e) {
				req.setAttribute(Util.ATTR_RESULTS, "/nException occurred");
				throw e;
			} catch (Exception e) {
				req.setAttribute(Util.ATTR_RESULTS, "/nException occurred");
				throw new ServletException(e.getMessage());
			}
		} else if (action.equals(ACTION_REGISTER)) {
			// Register a new user.
			// try
			// {
			String url;
			HttpSession session = req.getSession(true);

			String userid = req.getParameter("userid");
			String password = req.getParameter("passwd");
			String cpassword = req.getParameter("vpasswd");
			String firstName = req.getParameter("fname");
			String lastName = req.getParameter("lname");
			String addr1 = req.getParameter("addr1");
			String addr2 = req.getParameter("addr2");
			String addrCity = req.getParameter("city");
			String addrState = req.getParameter("state");
			String addrZip = req.getParameter("zip");
			String phone = req.getParameter("phone");

			// validate all user input
			if (!Util.validateString(userid)) {
				req.setAttribute(Util.ATTR_RESULTS, "Email address contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(firstName)) {
				req.setAttribute(Util.ATTR_RESULTS, "First Name contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(lastName)) {
				req.setAttribute(Util.ATTR_RESULTS, "Last Name contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(addr1)) {
				req.setAttribute(Util.ATTR_RESULTS, "Address Line 1 contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(addr2)) {
				req.setAttribute(Util.ATTR_RESULTS, "Address Line 2 contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(addrCity)) {
				req.setAttribute(Util.ATTR_RESULTS, "City contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(addrState)) {
				req.setAttribute(Util.ATTR_RESULTS, "State contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(addrZip)) {
				req.setAttribute(Util.ATTR_RESULTS, "Zip contains invalid characters.");
				url = Util.PAGE_REGISTER;
			} else if (!Util.validateString(phone)) {
				req.setAttribute(Util.ATTR_RESULTS, "Phone Number contains invalid characters.");
				url = Util.PAGE_REGISTER;
			}
			// Make sure passwords match.
			else if (!password.equals(cpassword)) {
				req.setAttribute(Util.ATTR_RESULTS, "Passwords do not match.");
				url = Util.PAGE_REGISTER;
			} else {
				// Create the new user.
				Customer customer = login
						.createCustomer(userid, password, firstName, lastName, addr1, addr2, addrCity, addrState, addrZip, phone);

				if (customer != null) {
					// Store customer info in HttpSession.
					session.setAttribute(Util.ATTR_CUSTOMER, customer);

					// See if user was in the middle of checking out.
					Boolean checkingOut = (Boolean) session.getAttribute(Util.ATTR_CHECKOUT);
					if ((checkingOut != null) && (checkingOut.booleanValue())) {
						url = Util.PAGE_ORDERINFO;
					} else {
						String category = (String) session.getAttribute(Util.ATTR_CATEGORY);

						// Default to plants
						if (category == null) {
							url = Util.PAGE_PROMO;
						} else {
							url = Util.PAGE_SHOPPING;
							req.setAttribute(Util.ATTR_INVITEMS, catalog
									.getItemsByCategory(Integer.parseInt(category)));
						}
					}
				} else {
					url = Util.PAGE_REGISTER;
					req.setAttribute(Util.ATTR_RESULTS, "New user NOT created!");
				}
			}
			requestDispatch(getServletConfig().getServletContext(), req, resp, url);
			// }
			// catch (CreateException e) { }
		} else if (action.equals(ACTION_ACCOUNT)) {
			String url;
			HttpSession session = req.getSession(true);
			Customer customer = (Customer) session.getAttribute(Util.ATTR_CUSTOMER);
			if (customer == null) {
				url = Util.PAGE_LOGIN;
				req.setAttribute(Util.ATTR_UPDATING, "true");
				req.setAttribute(Util.ATTR_RESULTS, "\nYou must login first.");
			} else {
				url = Util.PAGE_ACCOUNT;
				req.setAttribute(Util.ATTR_EDITACCOUNTINFO, customer);
			}
			requestDispatch(getServletConfig().getServletContext(), req, resp, url);
		} else if (action.equals(ACTION_ACCOUNTUPDATE)) {
			// try
			// {
			String url;
			HttpSession session = req.getSession(true);
			Customer customer = (Customer) session.getAttribute(Util.ATTR_CUSTOMER);

			String userid = customer.getCustomerID();
			String firstName = req.getParameter("fname");
			String lastName = req.getParameter("lname");
			String addr1 = req.getParameter("addr1");
			String addr2 = req.getParameter("addr2");
			String addrCity = req.getParameter("city");
			String addrState = req.getParameter("state");
			String addrZip = req.getParameter("zip");
			String phone = req.getParameter("phone");

			// Create the new user.
			customer = login.updateUser(userid, firstName, lastName, addr1, addr2, addrCity, addrState, addrZip, phone);
			// Store updated customer info in HttpSession.
			session.setAttribute(Util.ATTR_CUSTOMER, customer);

			// See if user was in the middle of checking out.
			Boolean checkingOut = (Boolean) session.getAttribute(Util.ATTR_CHECKOUT);
			if ((checkingOut != null) && (checkingOut.booleanValue())) {
				url = Util.PAGE_ORDERINFO;
			} else {
				String category = (String) session.getAttribute(Util.ATTR_CATEGORY);

				// Default to plants
				if (category == null) {
					url = Util.PAGE_PROMO;
				} else {
					url = Util.PAGE_SHOPPING;
					req.setAttribute(Util.ATTR_INVITEMS, catalog.getItemsByCategory(Integer.parseInt(category)));
				}
			}

			requestDispatch(getServletConfig().getServletContext(), req, resp, url);
			// }
			// catch (CreateException e) { }
		} else if (action.equals(ACTION_SETLOGGING)) {
			String debugSetting = req.getParameter("logging");
			if ((debugSetting == null) || (!debugSetting.equals("debug")))
				Util.setDebug(false);
			else
				Util.setDebug(true);

			requestDispatch(getServletConfig().getServletContext(), req, resp, Util.PAGE_HELP);
		}
	}

	/**
	 * Request dispatch.
	 */
	private void requestDispatch(ServletContext ctx,
			HttpServletRequest req,
			HttpServletResponse resp,
			String page) throws ServletException, IOException {
		resp.setContentType("text/html");
		ctx.getRequestDispatcher(page).include(req, resp);
	}
}

// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/AccountServlet.java:AccountServlet.<init>
// Node: getSession
// Node: setAttribute
// Node: requestDispatch
// Node: getServletConfig
// Node: getServletContext
// Node: getAttribute
// Node: removeAttribute
// Node: ServletException
// Node: getMessage
// Node: getRequestDispatcher
// Node: include
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


// Node: setShippingMethodName
// Node: getShippingMethodCount
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

import javax.enterprise.context.SessionScoped;
import javax.faces.application.Application;
import javax.faces.context.FacesContext;
import javax.inject.Inject;
import javax.inject.Named;

import com.ibm.websphere.samples.pbw.bean.CustomerMgr;
import com.ibm.websphere.samples.pbw.bean.MailerAppException;
import com.ibm.websphere.samples.pbw.bean.MailerBean;
import com.ibm.websphere.samples.pbw.bean.ShoppingCartBean;
import com.ibm.websphere.samples.pbw.jpa.Customer;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * Provides a combination of JSF action and backing bean support for the account web page.
 *
 */
@Named(value = "account")
@SessionScoped
public class AccountBean implements Serializable {
	private static final long serialVersionUID = 1L;
	private static final String ACTION_ACCOUNT = "account";
	private static final String ACTION_CHECKOUT_FINAL = "checkout_final";
	private static final String ACTION_LOGIN = "login";
	private static final String ACTION_ORDERDONE = "orderdone";
	private static final String ACTION_ORDERINFO = "orderinfo";
	private static final String ACTION_PROMO = "promo";
	private static final String ACTION_REGISTER = "register";

	@Inject
	private CustomerMgr login;
	@Inject
	private MailerBean mailer;
	@Inject
	private ShoppingCartBean shoppingCart;

	private boolean checkingOut;
	private Customer customer;
	private String lastOrderNum;
	private LoginInfo loginInfo;
	private Customer newCustomer;
	private OrderInfo orderInfo;
	private int orderNum = 1;
	private boolean register;
	private boolean updating;

	public String performAccount() {
		if (customer == null || loginInfo == null) {
			checkingOut = false;
			loginInfo = new LoginInfo();
			register = false;
			updating = true;

			loginInfo.setMessage("You must log in first.");

			return AccountBean.ACTION_LOGIN;
		}

		else {
			return AccountBean.ACTION_ACCOUNT;
		}
	}

	public String performAccountUpdate() {
		if (register) {
			customer = login.createCustomer(loginInfo.getEmail(), loginInfo.getPassword(), newCustomer
					.getFirstName(), newCustomer.getLastName(), newCustomer.getAddr1(), newCustomer
							.getAddr2(), newCustomer.getAddrCity(), newCustomer
									.getAddrState(), newCustomer.getAddrZip(), newCustomer.getPhone());
			register = false;
		}

		else {
			customer = login.updateUser(customer.getCustomerID(), customer.getFirstName(), customer
					.getLastName(), customer.getAddr1(), customer.getAddr2(), customer
							.getAddrCity(), customer.getAddrState(), customer.getAddrZip(), customer.getPhone());
		}

		return AccountBean.ACTION_PROMO;
	}

	public String performCheckoutFinal() {
		FacesContext context = FacesContext.getCurrentInstance();
		Application app = context.getApplication();
		ShoppingBean shopping = (ShoppingBean) app.createValueBinding("#{shopping}").getValue(context);

		shopping.setShippingCost(Util.getShippingMethodPrice(orderInfo.getShippingMethod()));

		return AccountBean.ACTION_CHECKOUT_FINAL;
	}

	public String performCompleteCheckout() {
		FacesContext context = FacesContext.getCurrentInstance();
		Application app = context.getApplication();
		app.createValueBinding("#{shopping}").getValue(context);

		// persist the order
		OrderInfo oi = new OrderInfo(shoppingCart
				.createOrder(customer.getCustomerID(), orderInfo.getBillName(), orderInfo.getBillAddr1(), orderInfo
						.getBillAddr2(), orderInfo.getBillCity(), orderInfo.getBillState(), orderInfo
								.getBillZip(), orderInfo.getBillPhone(), orderInfo.getShipName(), orderInfo
										.getShipAddr1(), orderInfo.getShipAddr2(), orderInfo.getShipCity(), orderInfo
												.getShipState(), orderInfo.getShipZip(), orderInfo
														.getShipPhone(), orderInfo.getCardName(), orderInfo
																.getCardNum(), orderInfo.getCardExpMonth(), orderInfo
																		.getCardExpYear(), orderInfo
																				.getCardholderName(), orderInfo
																						.getShippingMethod(), shoppingCart
																								.getItems()));

		lastOrderNum = oi.getID();

		Util.debug("Account.performCompleteCheckout: order id =" + orderInfo);

		/*
		 * // Check the available inventory and backorder if necessary. if (shoppingCart != null) {
		 * Inventory si; Collection<Inventory> items = shoppingCart.getItems(); for (Object o :
		 * items) { si = (Inventory) o; shoppingCart.checkInventory(si); Util.debug(
		 * "ShoppingCart.checkInventory() - checking Inventory quantity of item: " + si.getID()); }
		 * }
		 */
		try {
			mailer.createAndSendMail(customer, oi.getID());
		} catch (MailerAppException e) {
			System.out.println("MailerAppException:" + e);
			e.printStackTrace();
		} catch (Exception e) {
			System.out.println("Exception during create and send mail :" + e);
			e.printStackTrace();
		}

		orderInfo = null;

		// shoppingCart.setCartContents (new ShoppingCartContents());
		shoppingCart.removeAllItems();

		return AccountBean.ACTION_ORDERDONE;
	}

	public String performLogin() {
		checkingOut = false;
		loginInfo = new LoginInfo();
		register = false;
		updating = false;

		loginInfo.setMessage("");

		return AccountBean.ACTION_LOGIN;
	}

	public String performLoginComplete() {
		String message;

		// Attempt to log in the user.

		message = login.verifyUserAndPassword(loginInfo.getEmail(), loginInfo.getPassword());

		if (message != null) {
			// Error, so go back to the login page.

			loginInfo.setMessage(message);

			return AccountBean.ACTION_LOGIN;
		}

		// Otherwise, no error, so continue to the correct page.

		customer = login.getCustomer(loginInfo.getEmail());

		if (isCheckingOut()) {
			return performOrderInfo();
		}

		if (isUpdating()) {
			return performAccount();
		}

		return AccountBean.ACTION_PROMO;
	}

	public String performOrderInfo() {
		if (customer == null) {
			checkingOut = true;
			loginInfo = new LoginInfo();
			register = false;
			updating = false;

			loginInfo.setMessage("You must log in first.");

			return AccountBean.ACTION_LOGIN;
		}

		else {
			if (orderInfo == null) {
				orderInfo = new OrderInfo(customer.getFirstName() + " " + customer.getLastName(), customer.getAddr1(),
						customer.getAddr2(), customer.getAddrCity(), customer.getAddrState(), customer.getAddrZip(),
						customer.getPhone(), "", "", "", "", "", "", "", 0, "" + (orderNum++));
			}

			return AccountBean.ACTION_ORDERINFO;
		}
	}

	public String performRegister() {
		loginInfo = new LoginInfo();
		newCustomer = new Customer("", "", "", "", "", "", "", "", "", "");
		register = true;
		updating = false;

		return AccountBean.ACTION_REGISTER;
	}

	public Customer getCustomer() {
		return (isRegister() ? newCustomer : customer);
	}

	public String getLastOrderNum() {
		return lastOrderNum;
	}

	public LoginInfo getLoginInfo() {
		return loginInfo;
	}

	public OrderInfo getOrderInfo() {
		return orderInfo;
	}

	public boolean isCheckingOut() {
		return checkingOut;
	}

	public boolean isRegister() {
		return register;
	}

	public boolean isUpdating() {
		return updating;
	}
}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/AccountBean.java:AccountBean.<init>
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/AdminServlet.java:AdminServlet.<init>
// Node: performBackOrder
// Node: performSupplierConfig
// Node: performPopulate
// Node: updateSupplierInfo
// Node: sendRedirect
// Node: Populate
// Node: doPopulate
// Node: getBackOrders
// Node: AdminServlet
// Node: getParameterValues
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
// (C) COPYRIGHT International Business Machines Corp., 2011
// All Rights Reserved * Licensed Materials - Property of IBM
//

package com.ibm.websphere.samples.pbw.war;

import java.io.Serializable;

import javax.enterprise.context.Dependent;
import javax.inject.Inject;
import javax.inject.Named;

import com.ibm.websphere.samples.pbw.bean.ResetDBBean;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * JSF action bean for the help page.
 *
 */
@Named("help")
public class HelpBean implements Serializable {

	@Inject
	private ResetDBBean rdb;

	private String dbDumpFile;

	private static final String ACTION_HELP = "help";
	private static final String ACTION_HOME = "promo";

	public String performHelp() {
		return ACTION_HELP;
	}

	public String performDBReset() {
		rdb.resetDB();
		return ACTION_HOME;
	}

	/**
	 * @return the dbDumpFile
	 */
	public String getDbDumpFile() {
		return dbDumpFile;
	}

	/**
	 * @param dbDumpFile
	 *            the dbDumpFile to set
	 */
	public void setDbDumpFile(String dbDumpFile) {
		this.dbDumpFile = dbDumpFile;
	}

	/**
	 * @return whether debug is on or not
	 */
	public boolean isDebug() {
		return Util.debugOn();
	}

	/**
	 * Debugging is currently tied to the JavaServer Faces project stage. Any change here is likely
	 * to be automatically reset.
	 * 
	 * @param debug
	 *            Sets whether debug is on or not.
	 */
	public void setDebug(boolean debug) {
		Util.setDebug(debug);
	}

}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/HelpBean.java:HelpBean.<init>
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

import javax.inject.Inject;
import javax.inject.Named;

import com.ibm.websphere.samples.pbw.bean.MailerAppException;
import com.ibm.websphere.samples.pbw.bean.MailerBean;
import com.ibm.websphere.samples.pbw.jpa.Customer;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * This class sends the email confirmation message.
 */
@Named("mailaction")
public class MailAction implements java.io.Serializable {
	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;

	@Inject
	private MailerBean mailer;

	/** Public constructor */
	public MailAction() {
	}

	/**
	 * Send the email order confirmation message.
	 *
	 * @param customer
	 *            The customer information.
	 * @param orderKey
	 *            The order number.
	 */
	public final void sendConfirmationMessage(Customer customer,
			String orderKey) {
		try {
			System.out.println("mailer=" + mailer);
			mailer.createAndSendMail(customer, orderKey);
		}
		// The MailerAppException will be ignored since mail may not be configured.
		catch (MailerAppException e) {
			Util.debug("Mailer threw exception, mail may not be configured. Exception:" + e);
		}
	}

}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/MailAction.java:sends.<init>
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/ShoppingBean.java:ShoppingBean.<init>
