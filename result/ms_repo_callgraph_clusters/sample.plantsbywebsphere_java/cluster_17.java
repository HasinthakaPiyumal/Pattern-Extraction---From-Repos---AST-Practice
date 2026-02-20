// Cluster 17

// Node: getCustomer
// Node: updateUser
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


// Node: verifyUserAndPassword
// Node: verifyPassword
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


// Node: Size
// Node: Pattern
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


// Node: getPassword
// Node: getFullName
// Node: getFirstName
// Node: getLastName
// Node: getAddr1
// Node: getAddr2
// Node: getAddrCity
// Node: getAddrState
// Node: getAddrZip
// Node: getPhone
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/OrderInfo.java:to.<init>
// Node: OrderInfo
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


// Node: performAccount
// Node: LoginInfo
// Node: setMessage
// Node: performAccountUpdate
// Node: getEmail
// Node: performLogin
// Node: performLoginComplete
// Node: isCheckingOut
// Node: performOrderInfo
// Node: isUpdating
// Node: isRegister
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


// Node: repos/cloned_ms_repos/sample.plantsbywebsphere/src/main/java/com/ibm/websphere/samples/pbw/war/LoginInfo.java:LoginInfo.<init>
