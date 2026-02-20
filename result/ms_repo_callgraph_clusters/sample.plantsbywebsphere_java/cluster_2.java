// Cluster 2

// Node: debug
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


// Node: createMessage
// Node: StringBuffer
// Node: append
// Node: getShipName
// Node: getShipAddr1
// Node: getShipAddr2
// Node: getShipCity
// Node: getShipState
// Node: getShipZip
// Node: createAndSendMail
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


// Node: removeAllItems
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


// Node: getBillAddr1
// Node: getBillAddr2
// Node: getBillCity
// Node: getBillName
// Node: getBillPhone
// Node: getBillState
// Node: getBillZip
// Node: getShipPhone
// Node: getShippingMethod
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


// Node: increateQuantity
// Node: RuntimeException
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/utils/Util.java:Util.getShippingMethod
// Node: price
// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/utils/Util.java:Util.getShippingMethodPrice
// Node: getShippingMethodPrice
// Node: time
// Node: getApplication
// Node: getProjectStage
// Node: println
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


// Node: getCardholderName
// Node: getCardName
// Node: getCardNum
// Node: getCardExpMonth
// Node: getCardExpYear
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


// Node: performCheckoutFinal
// Node: createValueBinding
// Node: getValue
// Node: setShippingCost
// Node: performCompleteCheckout
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


// Node: MailAction
// Node: sendConfirmationMessage
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


