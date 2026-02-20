// Cluster 0

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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/bean/BackOrderMgr.java:BackOrderMgr.<init>
// Node: RolesAllowed
// Node: PersistenceContext
// Node: createNamedQuery
// Node: setParameter
// Node: getSingleResult
// Node: FinderException
// Node: BackOrder
// Node: persist
// Node: SuppressWarnings
// Node: findBackOrders
// Node: getResultList
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
import java.util.Date;

import javax.annotation.Resource;
import javax.enterprise.context.Dependent;
import javax.inject.Named;
import javax.mail.Message;
import javax.mail.Multipart;
import javax.mail.Session;
import javax.mail.Transport;
import javax.mail.internet.InternetAddress;
import javax.mail.internet.MimeBodyPart;
import javax.mail.internet.MimeMessage;
import javax.mail.internet.MimeMultipart;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;

import com.ibm.websphere.samples.pbw.jpa.Customer;
import com.ibm.websphere.samples.pbw.jpa.Order;
import com.ibm.websphere.samples.pbw.utils.Util;

/**
 * MailerBean provides a transactional facade for access to Order information and notification of
 * the buyer of order state.
 * 
 */

@Named(value = "mailerbean")
@Dependent

public class MailerBean implements Serializable {
	private static final long serialVersionUID = 1L;
	// public static final String MAIL_SESSION = "java:comp/env/mail/PlantsByWebSphere";
	@Resource(name = "mail/PlantsByWebSphere")
	Session mailSession;

	@PersistenceContext(unitName = "PBW")

	EntityManager em;

	/**
	 * Create the email message.
	 *
	 * @param orderKey
	 *            The order number.
	 * @return The email message.
	 */
	private String createMessage(String orderKey) {
		Util.debug("creating email message for order:" + orderKey);
		StringBuffer msg = new StringBuffer();
		Order order = em.find(Order.class, orderKey);
		msg.append("Thank you for your order " + orderKey + ".\n");
		msg.append("Your Plants By WebSphere order will be shipped to:\n");
		msg.append("     " + order.getShipName() + "\n");
		msg.append("     " + order.getShipAddr1() + " " + order.getShipAddr2() + "\n");
		msg.append("     " + order.getShipCity() + ", " + order.getShipState() + " " + order.getShipZip() + "\n\n");
		msg.append("Please save it for your records.\n");
		return msg.toString();
	}

	/**
	 * Create the Subject line.
	 *
	 * @param orderKey
	 *            The order number.
	 * @return The Order number string.
	 */
	private String createSubjectLine(String orderKey) {
		StringBuffer msg = new StringBuffer();
		msg.append("Your order number " + orderKey);

		return msg.toString();
	}

	/**
	 * Create a mail message and send it.
	 *
	 * @param customerInfo
	 *            Customer information.
	 * @param orderKey
	 * @throws MailerAppException
	 */
	public void createAndSendMail(Customer customerInfo, String orderKey) throws MailerAppException {
		try {
			EMailMessage eMessage = new EMailMessage(createSubjectLine(orderKey), createMessage(orderKey),
					customerInfo.getCustomerID());

			Util.debug("Sending message" + "\nTo: " + eMessage.getEmailReceiver() + "\nSubject: "
					+ eMessage.getSubject() + "\nContents: " + eMessage.getHtmlContents());

			Util.debug("Sending message" + "\nTo: " + eMessage.getEmailReceiver() + "\nSubject: "
					+ eMessage.getSubject() + "\nContents: " + eMessage.getHtmlContents());

			MimeMessage msg = new MimeMessage(mailSession);
			msg.setFrom();

			msg.setRecipients(Message.RecipientType.TO, InternetAddress.parse(eMessage.getEmailReceiver(), false));

			msg.setSubject(eMessage.getSubject());
			MimeBodyPart mbp = new MimeBodyPart();
			mbp.setText(eMessage.getHtmlContents(), "us-ascii");
			msg.setHeader("X-Mailer", "JavaMailer");
			Multipart mp = new MimeMultipart();
			mp.addBodyPart(mbp);
			msg.setContent(mp);
			msg.setSentDate(new Date());

			Transport.send(msg);
			Util.debug("Mail sent successfully.");

		} catch (Exception e) {

			Util.debug("Error sending mail. Have mail resources been configured correctly?");
			Util.debug("createAndSendMail exception : " + e);
			e.printStackTrace();
			throw new MailerAppException("Failure while sending mail");
		}
	}
}


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/bean/MailerBean.java:MailerBean.<init>
// Node: Resource
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

// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/bean/ResetDBBean.java:ResetDBBean.<init>
// Node: flush
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/bean/ShoppingCartBean.java:ShoppingCartBean.<init>
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/bean/CustomerMgr.java:CustomerMgr.<init>
// Node: Customer
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/bean/CatalogMgr.java:CatalogMgr.<init>
// Node: getItemsLikeName
// Node: item
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/bean/SuppliersBean.java:for.<init>
// Node: Supplier
// Node: findSuppliers
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


// Node: performRegister
