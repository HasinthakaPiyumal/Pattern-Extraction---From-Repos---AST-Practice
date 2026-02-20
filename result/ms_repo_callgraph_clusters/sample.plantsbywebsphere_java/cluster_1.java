// Cluster 1

// Node: createBackOrder
// Node: printStackTrace
// Node: deleteAll
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

import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.Serializable;
import java.net.URL;
import java.util.Vector;

import javax.annotation.Resource;
import javax.annotation.security.RolesAllowed;
import javax.enterprise.context.Dependent;
import javax.inject.Inject;
import javax.inject.Named;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.persistence.PersistenceContextType;
import javax.persistence.Query;
import javax.persistence.SynchronizationType;
import javax.transaction.HeuristicMixedException;
import javax.transaction.HeuristicRollbackException;
import javax.transaction.NotSupportedException;
import javax.transaction.RollbackException;
import javax.transaction.SystemException;
import javax.transaction.Transactional;
import javax.transaction.UserTransaction;

import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * ResetDBBean provides a transactional and secure facade to reset all the database information for
 * the PlantsByWebSphere application.
 */

@Named(value = "resetbean")
@Dependent
@RolesAllowed("SampAdmin")
public class ResetDBBean implements Serializable {

	@Inject
	private CatalogMgr catalog;
	@Inject
	private CustomerMgr customer;
	@Inject
	private ShoppingCartBean cart;
	@Inject
	private BackOrderMgr backOrderStock;
	@Inject
	private SuppliersBean suppliers;

	@PersistenceContext(unitName = "PBW")
	EntityManager em;
	
	@Resource
	UserTransaction tx;
	
	public void resetDB() {
		deleteAll();
		populateDB();
	}

	/**
	 * @param itemID
	 * @param fileName
	 * @param catalog
	 * @throws FileNotFoundException
	 * @throws IOException
	 */
	public static void addImage(String itemID,
			String fileName,
			CatalogMgr catalog) throws FileNotFoundException, IOException {
		URL url = Thread.currentThread().getContextClassLoader().getResource("resources/images/" + fileName);
		Util.debug("URL: " + url);
		fileName = url.getPath();
		Util.debug("Fully-qualified Filename: " + fileName);
		File imgFile = new File(fileName);
		// Open the input file as a stream of bytes
		FileInputStream fis = new FileInputStream(imgFile);
		DataInputStream dis = new DataInputStream(fis);
		int dataSize = dis.available();
		byte[] data = new byte[dataSize];
		dis.readFully(data);
		catalog.setItemImageBytes(itemID, data);
	}

	public void populateDB() {
		/**
		 * Populate INVENTORY table with text
		 */
		Util.debug("Populating INVENTORY table with text...");
		try {
			String[] values = Util.getProperties("inventory");
			for (int index = 0; index < values.length; index++) {
				Util.debug("Found INVENTORY property values:  " + values[index]);
				String[] fields = Util.readTokens(values[index], "|");
				String id = fields[0];
				String name = fields[1];
				String heading = fields[2];
				String descr = fields[3];
				String pkginfo = fields[4];
				String image = fields[5];
				float price = new Float(fields[6]).floatValue();
				float cost = new Float(fields[7]).floatValue();
				int quantity = new Integer(fields[8]).intValue();
				int category = new Integer(fields[9]).intValue();
				String notes = fields[10];
				boolean isPublic = new Boolean(fields[11]).booleanValue();
				Util.debug("Populating INVENTORY with following values:  ");
				Util.debug(fields[0]);
				Util.debug(fields[1]);
				Util.debug(fields[2]);
				Util.debug(fields[3]);
				Util.debug(fields[4]);
				Util.debug(fields[5]);
				Util.debug(fields[6]);
				Util.debug(fields[7]);
				Util.debug(fields[8]);
				Util.debug(fields[9]);
				Util.debug(fields[10]);
				Util.debug(fields[11]);
				Inventory storeItem = new Inventory(id, name, heading, descr, pkginfo, image, price, cost, quantity,
						category, notes, isPublic);
				catalog.addItem(storeItem);
				addImage(id, image, catalog);
			}
			Util.debug("INVENTORY table populated with text...");
		} catch (Exception e) {
			Util.debug("Unable to populate INVENTORY table with text data: " + e);
			e.printStackTrace();
		}
		/**
		 * Populate CUSTOMER table with text
		 */
		Util.debug("Populating CUSTOMER table with default values...");
		try {
			String[] values = Util.getProperties("customer");
			Util.debug("Found CUSTOMER properties:  " + values[0]);
			for (int index = 0; index < values.length; index++) {
				String[] fields = Util.readTokens(values[index], "|");
				String customerID = fields[0];
				String password = fields[1];
				String firstName = fields[2];
				String lastName = fields[3];
				String addr1 = fields[4];
				String addr2 = fields[5];
				String addrCity = fields[6];
				String addrState = fields[7];
				String addrZip = fields[8];
				String phone = fields[9];
				Util.debug("Populating CUSTOMER with following values:  ");
				Util.debug(fields[0]);
				Util.debug(fields[1]);
				Util.debug(fields[2]);
				Util.debug(fields[3]);
				Util.debug(fields[4]);
				Util.debug(fields[5]);
				Util.debug(fields[6]);
				Util.debug(fields[7]);
				Util.debug(fields[8]);
				Util.debug(fields[9]);
				customer.createCustomer(customerID, password, firstName, lastName, addr1, addr2, addrCity, addrState, addrZip, phone);
			}
		} catch (Exception e) {
			Util.debug("Unable to populate CUSTOMER table with text data: " + e);
			e.printStackTrace();
		}
		/**
		 * Populate ORDER table with text
		 */
		Util.debug("Populating ORDER table with default values...");
		try {
			String[] values = Util.getProperties("order");
			Util.debug("Found ORDER properties:  " + values[0]);
			if (values[0] != null && values.length > 0) {
				for (int index = 0; index < values.length; index++) {
					String[] fields = Util.readTokens(values[index], "|");
					if (fields != null && fields.length >= 21) {
						String customerID = fields[0];
						String billName = fields[1];
						String billAddr1 = fields[2];
						String billAddr2 = fields[3];
						String billCity = fields[4];
						String billState = fields[5];
						String billZip = fields[6];
						String billPhone = fields[7];
						String shipName = fields[8];
						String shipAddr1 = fields[9];
						String shipAddr2 = fields[10];
						String shipCity = fields[11];
						String shipState = fields[12];
						String shipZip = fields[13];
						String shipPhone = fields[14];
						int shippingMethod = Integer.parseInt(fields[15]);
						String creditCard = fields[16];
						String ccNum = fields[17];
						String ccExpireMonth = fields[18];
						String ccExpireYear = fields[19];
						String cardHolder = fields[20];
						Vector<Inventory> items = new Vector<Inventory>();
						Util.debug("Populating ORDER with following values:  ");
						Util.debug(fields[0]);
						Util.debug(fields[1]);
						Util.debug(fields[2]);
						Util.debug(fields[3]);
						Util.debug(fields[4]);
						Util.debug(fields[5]);
						Util.debug(fields[6]);
						Util.debug(fields[7]);
						Util.debug(fields[8]);
						Util.debug(fields[9]);
						Util.debug(fields[10]);
						Util.debug(fields[11]);
						Util.debug(fields[12]);
						Util.debug(fields[13]);
						Util.debug(fields[14]);
						Util.debug(fields[15]);
						Util.debug(fields[16]);
						Util.debug(fields[17]);
						Util.debug(fields[18]);
						Util.debug(fields[19]);
						Util.debug(fields[20]);
						cart.createOrder(customerID, billName, billAddr1, billAddr2, billCity, billState, billZip, billPhone, shipName, shipAddr1, shipAddr2, shipCity, shipState, shipZip, shipPhone, creditCard, ccNum, ccExpireMonth, ccExpireYear, cardHolder, shippingMethod, items);
					} else {
						Util.debug("Property does not contain enough fields: " + values[index]);
						Util.debug("Fields found were: " + fields);
					}
				}
			}
			// stmt.executeUpdate(" INSERT INTO ORDERITEM(INVENTORYID, NAME, PKGINFO, PRICE, COST,
			// CATEGORY, QUANTITY, SELLDATE, ORDER_ORDERID) VALUES ('A0001', 'Bulb Digger',
			// 'Assembled', 12.0, 5.0, 3, 900, '01054835419625', '1')");
		} catch (Exception e) {
			Util.debug("Unable to populate ORDERITEM table with text data: " + e);
			e.printStackTrace();
			e.printStackTrace();
		}
		/**
		 * Populate BACKORDER table with text
		 */
		Util.debug("Populating BACKORDER table with default values...");
		try {
			String[] values = Util.getProperties("backorder");
			Util.debug("Found BACKORDER properties:  " + values[0]);
			// Inserting backorders
			for (int index = 0; index < values.length; index++) {
				String[] fields = Util.readTokens(values[index], "|");
				String inventoryID = fields[0];
				int amountToOrder = new Integer(fields[1]).intValue();
				int maximumItems = new Integer(fields[2]).intValue();
				Util.debug("Populating BACKORDER with following values:  ");
				Util.debug(inventoryID);
				Util.debug("amountToOrder -> " + amountToOrder);
				Util.debug("maximumItems -> " + maximumItems);
				backOrderStock.createBackOrder(inventoryID, amountToOrder, maximumItems);
			}
		} catch (Exception e) {
			Util.debug("Unable to populate BACKORDER table with text data: " + e);
			e.printStackTrace();
		}
		/**
		 * Populate SUPPLIER table with text
		 */
		Util.debug("Populating SUPPLIER table with default values...");
		try {
			String[] values = Util.getProperties("supplier");
			Util.debug("Found SUPPLIER properties:  " + values[0]);
			// Inserting Suppliers
			for (int index = 0; index < values.length; index++) {
				String[] fields = Util.readTokens(values[index], "|");
				String supplierID = fields[0];
				String name = fields[1];
				String address = fields[2];
				String city = fields[3];
				String state = fields[4];
				String zip = fields[5];
				String phone = fields[6];
				String url = fields[7];
				Util.debug("Populating SUPPLIER with following values:  ");
				Util.debug(fields[0]);
				Util.debug(fields[1]);
				Util.debug(fields[2]);
				Util.debug(fields[3]);
				Util.debug(fields[4]);
				Util.debug(fields[5]);
				Util.debug(fields[6]);
				Util.debug(fields[7]);
				suppliers.createSupplier(supplierID, name, address, city, state, zip, phone, url);
			}
		} catch (Exception e) {
			Util.debug("Unable to populate SUPPLIER table with text data: " + e);
			e.printStackTrace();
		}
	}

	@Transactional
	public void deleteAll() {
		try {
			Query q = em.createNamedQuery("removeAllOrders");
			q.executeUpdate();
			q = em.createNamedQuery("removeAllInventory");
			q.executeUpdate();
			// q=em.createNamedQuery("removeAllIdGenerator");
			// q.executeUpdate();
			q = em.createNamedQuery("removeAllCustomers");
			q.executeUpdate();
			q = em.createNamedQuery("removeAllOrderItem");
			q.executeUpdate();
			q = em.createNamedQuery("removeAllBackOrder");
			q.executeUpdate();
			q = em.createNamedQuery("removeAllSupplier");
			q.executeUpdate();
			em.flush();
			Util.debug("Deleted all data from database");
		} catch (Exception e) {
			Util.debug("ResetDB(deleteAll) -- Error deleting data from the database: " + e);
			e.printStackTrace();
			try {
                tx.setRollbackOnly();
            } catch (IllegalStateException | SystemException ignore) {
            }
		}
	}

}

// Node: getProperties
// Node: readTokens
// Node: Float
// Node: floatValue
// Node: Integer
// Node: intValue
// Node: Boolean
// Node: booleanValue
// Node: Inventory
// Node: addItem
// Node: createCustomer
// Node: parseInt
// Node: createOrder
// Node: executeUpdate
// Node: ORDERITEM
// Node: VALUES
// Node: createSupplier
// Node: ResetDB
// Node: setRollbackOnly
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


// Node: put
// Node: updateItem
// Node: keys
// Node: hasMoreElements
// Node: nextElement
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
package com.ibm.websphere.samples.pbw.utils;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.Hashtable;
import java.util.Properties;
import java.util.StringTokenizer;
import java.util.Vector;


/**
 * @author aamortim
 *
 * To change the template for this generated type comment go to
 * Window&gt;Preferences&gt;Java&gt;Code Generation&gt;Code and Comments
 */
/**
 *  Utility class.
 */
public class ListProperties extends Properties {
    /**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	private Hashtable<String, Vector<String>> listProps = null;
    /* Method load
     * @param inStream
     */
    
	public void load(InputStream inStream) throws IOException {
        try {
        	Util.debug("ListProperties.load - loading from stream "+inStream);
            // Parse property file, remove comments, blank lines, and combine
            // continued lines.
            String propFile = "";
            BufferedReader inputLine = new BufferedReader(new InputStreamReader(inStream));
            String line = inputLine.readLine();
            boolean lineContinue = false;
            while (line != null) {
                Util.debug("ListProperties.load - Line read: " + line);
                line = line.trim();
                String currLine = "";
                if (line.startsWith("#")) {
                    // Skipping comment
                } else if (line.startsWith("!")) {
                    // Skipping comment
                } else if (line.equals("")) {
                    // Skipping blank lines
                } else {
                    if (!lineContinue) {
                        currLine = line;
                    } else {
                        // This is a continuation line.   Add to previous line.
                        currLine += line;
                    }
                    // Must be a property line
                    if (line.endsWith("\\")) {
                        // Next line is continued from the current one.
                        lineContinue = true;
                    } else {
                        // The current line is completed.   Parse the property.
                        propFile += currLine + "\n";
                        currLine = "";
                        lineContinue = false;
                    }
                }
                line = inputLine.readLine();
            }
            // Load Properties
            listProps = new Hashtable<String, Vector<String>>();
            // Now parse the Properties to create an array
            String[] props = readTokens(propFile, "\n");
            for (int index = 0; index < props.length; index++) {
                Util.debug("ListProperties.load() - props[" + index + "] = " + props[index]);
                // Parse the line to get the key,value pair
                String[] val = readTokens(props[index], "=");
                Util.debug("ListProperties.load() - val[0]: " + val[0] + " val[1]: " + val[1]);
                if (!val[0].equals("")) {
                    if (this.containsKey(val[0])) {
                        // Previous key,value was already created.
                        // Need an array
                        Vector<String> currList = (Vector<String>) listProps.get(val[0]);
                        if ((currList == null) || currList.isEmpty()) {
                            currList = new Vector<String>();
                            String prevVal = this.getProperty(val[0]);
                            currList.addElement(prevVal);
                        }
                        currList.addElement(val[1]);
                        listProps.put(val[0], currList);
                    }
                    this.setProperty(val[0], val[1]);
                }
            }
        } catch (Exception e) {
            Util.debug("ListProperties.load(): Exception: " + e);
            e.printStackTrace();
        }
    }
    /**
     * Method readTokens.
     * @param text
     * @param token
     * @return list
     */
    public String[] readTokens(String text, String token) {
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
    public String[] getProperties(String name) {
        String[] values = { "" };
        try {
            String value = this.getProperty(name);
            Util.debug("ListProperties.getProperties: property (" + name + ") -> " + value);
            if (listProps.containsKey(name)) {
                Vector<String> list = (Vector<String>) listProps.get(name);
                values = new String[list.size()];
                for (int index = 0; index < list.size(); index++) {
                    values[index] = (String) list.elementAt(index);
                }
            } else {
                values[0] = value;
            }
        } catch (Exception e) {
            Util.debug("ListProperties.getProperties(): Exception: " + e);
        }
        return (values);
    }
}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/utils/ListProperties.java:ListProperties.<init>
// Node: load
// Node: BufferedReader
// Node: InputStreamReader
// Node: readLine
// Node: trim
// Node: startsWith
// Node: endsWith
// Node: containsKey
// Node: isEmpty
// Node: getProperty
// Node: addElement
// Node: setProperty
// Node: StringTokenizer
// Node: countTokens
// Node: nextToken
// Node: property
// Node: elementAt
// Node: readProperties
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


// Node: propertyNames
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
package com.ibm.websphere.samples.pbw.war;

import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.net.URL;
import java.util.Vector;

import com.ibm.websphere.samples.pbw.bean.BackOrderMgr;
import com.ibm.websphere.samples.pbw.bean.CatalogMgr;
import com.ibm.websphere.samples.pbw.bean.CustomerMgr;
import com.ibm.websphere.samples.pbw.bean.ResetDBBean;
import com.ibm.websphere.samples.pbw.bean.ShoppingCartBean;
import com.ibm.websphere.samples.pbw.bean.SuppliersBean;
import com.ibm.websphere.samples.pbw.jpa.Inventory;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * A basic POJO class for resetting the database.
 */
public class Populate {

	private ResetDBBean resetDB;

	private CatalogMgr catalog;

	private CustomerMgr login;

	private ShoppingCartBean cart;

	private BackOrderMgr backOrderStock;

	private SuppliersBean suppliers;

	/**
	 * 
	 */
	public Populate() {
	}

	public Populate(ResetDBBean resetDB, CatalogMgr c, CustomerMgr l, BackOrderMgr b, SuppliersBean s) {
		this.resetDB = resetDB;
		this.catalog = c;
		this.login = l;
		this.backOrderStock = b;
		this.suppliers = s;
	}

	/**
	 * @param itemID
	 * @param fileName
	 * @param catalog
	 * @throws FileNotFoundException
	 * @throws IOException
	 */
	public static void addImage(String itemID,
			String fileName,
			CatalogMgr catalog) throws FileNotFoundException, IOException {
		URL url = Thread.currentThread().getContextClassLoader().getResource("resources/images/" + fileName);
		Util.debug("URL: " + url);
		fileName = url.getPath();
		Util.debug("Fully-qualified Filename: " + fileName);
		File imgFile = new File(fileName);
		// Open the input file as a stream of bytes
		FileInputStream fis = new FileInputStream(imgFile);
		DataInputStream dis = new DataInputStream(fis);
		int dataSize = dis.available();
		byte[] data = new byte[dataSize];
		dis.readFully(data);
		catalog.setItemImageBytes(itemID, data);
	}

	/**
	 * 
	 */
	public void doPopulate() {
		try {
			resetDB.deleteAll();
		} catch (Exception e) {
			Util.debug("Populate:doPopulate() - Exception deleting data in database: " + e);
			e.printStackTrace();
		}
		/**
		 * Populate INVENTORY table with text
		 */
		Util.debug("Populating INVENTORY table with text...");
		try {
			String[] values = Util.getProperties("inventory");
			for (int index = 0; index < values.length; index++) {
				Util.debug("Found INVENTORY property values:  " + values[index]);
				String[] fields = Util.readTokens(values[index], "|");
				String id = fields[0];
				String name = fields[1];
				String heading = fields[2];
				String descr = fields[3];
				String pkginfo = fields[4];
				String image = fields[5];
				float price = new Float(fields[6]).floatValue();
				float cost = new Float(fields[7]).floatValue();
				int quantity = new Integer(fields[8]).intValue();
				int category = new Integer(fields[9]).intValue();
				String notes = fields[10];
				boolean isPublic = new Boolean(fields[11]).booleanValue();
				Util.debug("Populating INVENTORY with following values:  ");
				Util.debug(fields[0]);
				Util.debug(fields[1]);
				Util.debug(fields[2]);
				Util.debug(fields[3]);
				Util.debug(fields[4]);
				Util.debug(fields[5]);
				Util.debug(fields[6]);
				Util.debug(fields[7]);
				Util.debug(fields[8]);
				Util.debug(fields[9]);
				Util.debug(fields[10]);
				Util.debug(fields[11]);
				Inventory storeItem = new Inventory(id, name, heading, descr, pkginfo, image, price, cost, quantity,
						category, notes, isPublic);
				catalog.addItem(storeItem);
				addImage(id, image, catalog);
			}
			Util.debug("INVENTORY table populated with text...");
		} catch (Exception e) {
			Util.debug("Unable to populate INVENTORY table with text data: " + e);
		}
		/**
		 * Populate CUSTOMER table with text
		 */
		Util.debug("Populating CUSTOMER table with default values...");
		try {
			String[] values = Util.getProperties("customer");
			Util.debug("Found CUSTOMER properties:  " + values[0]);
			for (int index = 0; index < values.length; index++) {
				String[] fields = Util.readTokens(values[index], "|");
				String customerID = fields[0];
				String password = fields[1];
				String firstName = fields[2];
				String lastName = fields[3];
				String addr1 = fields[4];
				String addr2 = fields[5];
				String addrCity = fields[6];
				String addrState = fields[7];
				String addrZip = fields[8];
				String phone = fields[9];
				Util.debug("Populating CUSTOMER with following values:  ");
				Util.debug(fields[0]);
				Util.debug(fields[1]);
				Util.debug(fields[2]);
				Util.debug(fields[3]);
				Util.debug(fields[4]);
				Util.debug(fields[5]);
				Util.debug(fields[6]);
				Util.debug(fields[7]);
				Util.debug(fields[8]);
				Util.debug(fields[9]);
				login.createCustomer(customerID, password, firstName, lastName, addr1, addr2, addrCity, addrState, addrZip, phone);
			}
		} catch (Exception e) {
			Util.debug("Unable to populate CUSTOMER table with text data: " + e);
		}
		/**
		 * Populate ORDER table with text
		 */
		Util.debug("Populating ORDER table with default values...");
		try {
			String[] values = Util.getProperties("order");
			Util.debug("Found ORDER properties:  " + values[0]);
			if (values[0] != null && values.length > 0) {
				for (int index = 0; index < values.length; index++) {
					String[] fields = Util.readTokens(values[index], "|");
					if (fields != null && fields.length >= 21) {
						String customerID = fields[0];
						String billName = fields[1];
						String billAddr1 = fields[2];
						String billAddr2 = fields[3];
						String billCity = fields[4];
						String billState = fields[5];
						String billZip = fields[6];
						String billPhone = fields[7];
						String shipName = fields[8];
						String shipAddr1 = fields[9];
						String shipAddr2 = fields[10];
						String shipCity = fields[11];
						String shipState = fields[12];
						String shipZip = fields[13];
						String shipPhone = fields[14];
						int shippingMethod = Integer.parseInt(fields[15]);
						String creditCard = fields[16];
						String ccNum = fields[17];
						String ccExpireMonth = fields[18];
						String ccExpireYear = fields[19];
						String cardHolder = fields[20];
						Vector<Inventory> items = new Vector<Inventory>();
						Util.debug("Populating ORDER with following values:  ");
						Util.debug(fields[0]);
						Util.debug(fields[1]);
						Util.debug(fields[2]);
						Util.debug(fields[3]);
						Util.debug(fields[4]);
						Util.debug(fields[5]);
						Util.debug(fields[6]);
						Util.debug(fields[7]);
						Util.debug(fields[8]);
						Util.debug(fields[9]);
						Util.debug(fields[10]);
						Util.debug(fields[11]);
						Util.debug(fields[12]);
						Util.debug(fields[13]);
						Util.debug(fields[14]);
						Util.debug(fields[15]);
						Util.debug(fields[16]);
						Util.debug(fields[17]);
						Util.debug(fields[18]);
						Util.debug(fields[19]);
						Util.debug(fields[20]);
						cart.createOrder(customerID, billName, billAddr1, billAddr2, billCity, billState, billZip, billPhone, shipName, shipAddr1, shipAddr2, shipCity, shipState, shipZip, shipPhone, creditCard, ccNum, ccExpireMonth, ccExpireYear, cardHolder, shippingMethod, items);
					} else {
						Util.debug("Property does not contain enough fields: " + values[index]);
						Util.debug("Fields found were: " + fields);
					}
				}
			}
			// stmt.executeUpdate(" INSERT INTO ORDERITEM(INVENTORYID, NAME, PKGINFO, PRICE, COST,
			// CATEGORY, QUANTITY, SELLDATE, ORDER_ORDERID) VALUES ('A0001', 'Bulb Digger',
			// 'Assembled', 12.0, 5.0, 3, 900, '01054835419625', '1')");
		} catch (Exception e) {
			Util.debug("Unable to populate ORDERITEM table with text data: " + e);
			e.printStackTrace();
		}
		/**
		 * Populate BACKORDER table with text
		 */
		Util.debug("Populating BACKORDER table with default values...");
		try {
			String[] values = Util.getProperties("backorder");
			Util.debug("Found BACKORDER properties:  " + values[0]);
			// Inserting backorders
			for (int index = 0; index < values.length; index++) {
				String[] fields = Util.readTokens(values[index], "|");
				String inventoryID = fields[0];
				int amountToOrder = new Integer(fields[1]).intValue();
				int maximumItems = new Integer(fields[2]).intValue();
				Util.debug("Populating BACKORDER with following values:  ");
				Util.debug(inventoryID);
				Util.debug("amountToOrder -> " + amountToOrder);
				Util.debug("maximumItems -> " + maximumItems);
				backOrderStock.createBackOrder(inventoryID, amountToOrder, maximumItems);
			}
		} catch (Exception e) {
			Util.debug("Unable to populate BACKORDER table with text data: " + e);
		}
		/**
		 * Populate SUPPLIER table with text
		 */
		Util.debug("Populating SUPPLIER table with default values...");
		try {
			String[] values = Util.getProperties("supplier");
			Util.debug("Found SUPPLIER properties:  " + values[0]);
			// Inserting Suppliers
			for (int index = 0; index < values.length; index++) {
				String[] fields = Util.readTokens(values[index], "|");
				String supplierID = fields[0];
				String name = fields[1];
				String address = fields[2];
				String city = fields[3];
				String state = fields[4];
				String zip = fields[5];
				String phone = fields[6];
				String url = fields[7];
				Util.debug("Populating SUPPLIER with following values:  ");
				Util.debug(fields[0]);
				Util.debug(fields[1]);
				Util.debug(fields[2]);
				Util.debug(fields[3]);
				Util.debug(fields[4]);
				Util.debug(fields[5]);
				Util.debug(fields[6]);
				Util.debug(fields[7]);
				suppliers.createSupplier(supplierID, name, address, city, state, zip, phone, url);
			}
		} catch (Exception e) {
			Util.debug("Unable to populate SUPPLIER table with text data: " + e);
		}
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


// Node: performAddToCart
