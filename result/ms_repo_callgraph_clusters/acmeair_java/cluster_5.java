// Cluster 5

// Node: CustomerInfo
/*******************************************************************************
* Copyright (c) 2013 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.web;

import javax.servlet.http.HttpServletRequest;
import javax.ws.rs.*;
import javax.ws.rs.core.*;

import com.acmeair.entities.Customer;
import com.acmeair.entities.CustomerAddress;
import com.acmeair.service.*;
import com.acmeair.web.dto.*;

import javax.ws.rs.core.Context;

@Path("/customer")
public class CustomerREST {
	
	private CustomerService customerService = ServiceLocator.instance().getService(CustomerService.class);
	
	@Context 
	private HttpServletRequest request;


	private boolean validate(String customerid)	{
		String loginUser = (String) request.getAttribute(RESTCookieSessionFilter.LOGIN_USER);
		return customerid.equals(loginUser);
	}
	@GET
	@Path("/byid/{custid}")
	@Produces("application/json")
	public Response getCustomer(@CookieParam("sessionid") String sessionid, @PathParam("custid") String customerid) {
		try {
			// make sure the user isn't trying to update a customer other than the one currently logged in
			if (!validate(customerid)) {
				return Response.status(Response.Status.FORBIDDEN).build();
				
			}
			Customer customer = customerService.getCustomerByUsername(customerid);	
			CustomerInfo customerDTO = new CustomerInfo(customer);			
			return Response.ok(customerDTO).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}

	@POST
	@Path("/byid/{custid}")
	@Produces("application/json")
	public /* Customer */ Response putCustomer(@CookieParam("sessionid") String sessionid, CustomerInfo customer) {
		if (!validate(customer.getUsername())) {
			return Response.status(Response.Status.FORBIDDEN).build();
		}
		
		Customer customerFromDB = customerService.getCustomerByUsernameAndPassword(customer.getUsername(), customer.getPassword());
		if (customerFromDB == null) {
			// either the customer doesn't exist or the password is wrong
			return Response.status(Response.Status.FORBIDDEN).build();
		}
		
		CustomerAddress addressFromDB = customerFromDB.getAddress();
		addressFromDB.setStreetAddress1(customer.getAddress().getStreetAddress1());
		if (customer.getAddress().getStreetAddress2() != null) {
			addressFromDB.setStreetAddress2(customer.getAddress().getStreetAddress2());
		}
		addressFromDB.setCity(customer.getAddress().getCity());
		addressFromDB.setStateProvince(customer.getAddress().getStateProvince());
		addressFromDB.setCountry(customer.getAddress().getCountry());
		addressFromDB.setPostalCode(customer.getAddress().getPostalCode());
		
		customerFromDB.setPhoneNumber(customer.getPhoneNumber());
		customerFromDB.setPhoneNumberType(Customer.PhoneType.valueOf(customer.getPhoneNumberType()));
		
		customerService.updateCustomer(customerFromDB);
		customerFromDB.setPassword(null);
		
		return Response.ok(customerFromDB).build();
	}
	

	
}


// Node: putCustomer
// Node: getUsername
// Node: getPassword
// Node: getAddress
// Node: setStreetAddress1
// Node: getStreetAddress1
// Node: getStreetAddress2
// Node: setStreetAddress2
// Node: setCity
// Node: getCity
// Node: setStateProvince
// Node: getStateProvince
// Node: setCountry
// Node: getCountry
// Node: setPostalCode
// Node: getPostalCode
// Node: setPhoneNumber
// Node: getPhoneNumber
// Node: setPhoneNumberType
// Node: valueOf
// Node: getPhoneNumberType
// Node: setPassword
// Node: XmlRootElement
/*******************************************************************************
* Copyright (c) 2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.web.dto;

import java.io.Serializable;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.Customer;


@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement(name="Customer")
public class CustomerInfo implements Serializable{

	
	private static final long serialVersionUID = 1L;
	@XmlElement(name="_id")
	private String _id;
	
	@XmlElement(name="password")
	private String password;
	
	@XmlElement(name="status")
	private String status;
	
	@XmlElement(name="total_miles")
	private int total_miles;
	
	@XmlElement(name="miles_ytd")
	private int miles_ytd;

	@XmlElement(name="address")
	private AddressInfo address;
	
	@XmlElement(name="phoneNumber")
	private String phoneNumber;
	
	@XmlElement(name="phoneNumberType")
	private String phoneNumberType;
	
	public CustomerInfo() {
	}
	
	public CustomerInfo(String username, String password, String status, int total_miles, int miles_ytd, AddressInfo address, String phoneNumber, String phoneNumberType) {
		this._id = username;
		this.password = password;
		this.status = status;
		this.total_miles = total_miles;
		this.miles_ytd = miles_ytd;
		this.address = address;
		this.phoneNumber = phoneNumber;
		this.phoneNumberType = phoneNumberType;
	}
	
	public CustomerInfo(Customer c) {
		this._id = c.getUsername();
		this.password = c.getPassword();
		this.status = c.getStatus().toString();
		this.total_miles = c.getTotal_miles();
		this.miles_ytd = c.getMiles_ytd();
		this.address = new AddressInfo(c.getAddress());
		this.phoneNumber = c.getPhoneNumber();
		this.phoneNumberType = c.getPhoneNumberType().toString();
	}

	public String getUsername() {
		return _id;
	}
	
	public void setUsername(String username) {
		this._id = username;
	}
	
	public String getPassword() {
		return password;
	}
	
	public void setPassword(String password) {
		this.password = password;
	}
	
	public String getStatus() {
		return status;
	}
	
	public void setStatus(String status) {
		this.status = status;
	}
	
	public int getTotal_miles() {
		return total_miles;
	}
	
	public void setTotal_miles(int total_miles) {
		this.total_miles = total_miles;
	}
	
	public int getMiles_ytd() {
		return miles_ytd;
	}
	
	public void setMiles_ytd(int miles_ytd) {
		this.miles_ytd = miles_ytd;
	}
	
	public String getPhoneNumber() {
		return phoneNumber;
	}

	public void setPhoneNumber(String phoneNumber) {
		this.phoneNumber = phoneNumber;
	}

	public String getPhoneNumberType() {
		return phoneNumberType;
	}

	public void setPhoneNumberType(String phoneNumberType) {
		this.phoneNumberType = phoneNumberType;
	}

	public AddressInfo getAddress() {
		return address;
	}

	public void setAddress(AddressInfo address) {
		this.address = address;
	}

	@Override
	public String toString() {
		return "Customer [id=" + _id + ", password=" + password + ", status="
				+ status + ", total_miles=" + total_miles + ", miles_ytd="
				+ miles_ytd + ", address=" + address + ", phoneNumber="
				+ phoneNumber + ", phoneNumberType=" + phoneNumberType + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		CustomerInfo other = (CustomerInfo) obj;
		if (address == null) {
			if (other.address != null)
				return false;
		} else if (!address.equals(other.address))
			return false;
		if (_id == null) {
			if (other._id != null)
				return false;
		} else if (!_id.equals(other._id))
			return false;
		if (miles_ytd != other.miles_ytd)
			return false;
		if (password == null) {
			if (other.password != null)
				return false;
		} else if (!password.equals(other.password))
			return false;
		if (phoneNumber == null) {
			if (other.phoneNumber != null)
				return false;
		} else if (!phoneNumber.equals(other.phoneNumber))
			return false;
		if (phoneNumberType != other.phoneNumberType)
			return false;
		if (status != other.status)
			return false;
		if (total_miles != other.total_miles)
			return false;
		return true;
	}

}


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/dto/CustomerInfo.java:CustomerInfo.<init>
// Node: getStatus
// Node: getTotal_miles
// Node: getMiles_ytd
// Node: AddressInfo
// Node: setUsername
// Node: setStatus
// Node: setAddress
/*******************************************************************************
* Copyright (c) 2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.web.dto;

import java.io.Serializable;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.CustomerAddress;



@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement(name="CustomerAddress")
public class AddressInfo implements Serializable{
	
	private static final long serialVersionUID = 1L;
	private String streetAddress1;
	private String streetAddress2;
	private String city;
	private String stateProvince;
	private String country;
	private String postalCode;

	public AddressInfo() {
	}
	
	public AddressInfo(String streetAddress1, String streetAddress2,
			String city, String stateProvince, String country, String postalCode) {
		super();
		this.streetAddress1 = streetAddress1;
		this.streetAddress2 = streetAddress2;
		this.city = city;
		this.stateProvince = stateProvince;
		this.country = country;
		this.postalCode = postalCode;
	}
	
	public AddressInfo(CustomerAddress address) {
		super();
		this.streetAddress1 = address.getStreetAddress1();
		this.streetAddress2 = address.getStreetAddress2();
		this.city = address.getCity();
		this.stateProvince = address.getStateProvince();
		this.country = address.getCountry();
		this.postalCode = address.getPostalCode();
	}
	
	public String getStreetAddress1() {
		return streetAddress1;
	}
	public void setStreetAddress1(String streetAddress1) {
		this.streetAddress1 = streetAddress1;
	}
	public String getStreetAddress2() {
		return streetAddress2;
	}
	public void setStreetAddress2(String streetAddress2) {
		this.streetAddress2 = streetAddress2;
	}
	public String getCity() {
		return city;
	}
	public void setCity(String city) {
		this.city = city;
	}
	public String getStateProvince() {
		return stateProvince;
	}
	public void setStateProvince(String stateProvince) {
		this.stateProvince = stateProvince;
	}
	public String getCountry() {
		return country;
	}
	public void setCountry(String country) {
		this.country = country;
	}
	public String getPostalCode() {
		return postalCode;
	}
	public void setPostalCode(String postalCode) {
		this.postalCode = postalCode;
	}
	@Override
	public String toString() {
		return "CustomerAddress [streetAddress1=" + streetAddress1
				+ ", streetAddress2=" + streetAddress2 + ", city=" + city
				+ ", stateProvince=" + stateProvince + ", country=" + country
				+ ", postalCode=" + postalCode + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		AddressInfo other = (AddressInfo) obj;
		if (city == null) {
			if (other.city != null)
				return false;
		} else if (!city.equals(other.city))
			return false;
		if (country == null) {
			if (other.country != null)
				return false;
		} else if (!country.equals(other.country))
			return false;
		if (postalCode == null) {
			if (other.postalCode != null)
				return false;
		} else if (!postalCode.equals(other.postalCode))
			return false;
		if (stateProvince == null) {
			if (other.stateProvince != null)
				return false;
		} else if (!stateProvince.equals(other.stateProvince))
			return false;
		if (streetAddress1 == null) {
			if (other.streetAddress1 != null)
				return false;
		} else if (!streetAddress1.equals(other.streetAddress1))
			return false;
		if (streetAddress2 == null) {
			if (other.streetAddress2 != null)
				return false;
		} else if (!streetAddress2.equals(other.streetAddress2))
			return false;
		return true;
	}
	
	
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/dto/AddressInfo.java:AddressInfo.<init>
/*******************************************************************************
* Copyright (c) 2013 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.morphia.entities;

import java.io.Serializable;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.CustomerAddress;

@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement
public class CustomerAddressImpl implements CustomerAddress, Serializable{
	
	private static final long serialVersionUID = 1L;
	private String streetAddress1;
	private String streetAddress2;
	private String city;
	private String stateProvince;
	private String country;
	private String postalCode;

	public CustomerAddressImpl() {
	}
	
	public CustomerAddressImpl(String streetAddress1, String streetAddress2,
			String city, String stateProvince, String country, String postalCode) {
		super();
		this.streetAddress1 = streetAddress1;
		this.streetAddress2 = streetAddress2;
		this.city = city;
		this.stateProvince = stateProvince;
		this.country = country;
		this.postalCode = postalCode;
	}
	
	public String getStreetAddress1() {
		return streetAddress1;
	}
	public void setStreetAddress1(String streetAddress1) {
		this.streetAddress1 = streetAddress1;
	}
	public String getStreetAddress2() {
		return streetAddress2;
	}
	public void setStreetAddress2(String streetAddress2) {
		this.streetAddress2 = streetAddress2;
	}
	public String getCity() {
		return city;
	}
	public void setCity(String city) {
		this.city = city;
	}
	public String getStateProvince() {
		return stateProvince;
	}
	public void setStateProvince(String stateProvince) {
		this.stateProvince = stateProvince;
	}
	public String getCountry() {
		return country;
	}
	public void setCountry(String country) {
		this.country = country;
	}
	public String getPostalCode() {
		return postalCode;
	}
	public void setPostalCode(String postalCode) {
		this.postalCode = postalCode;
	}
	@Override
	public String toString() {
		return "CustomerAddress [streetAddress1=" + streetAddress1
				+ ", streetAddress2=" + streetAddress2 + ", city=" + city
				+ ", stateProvince=" + stateProvince + ", country=" + country
				+ ", postalCode=" + postalCode + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		CustomerAddressImpl other = (CustomerAddressImpl) obj;
		if (city == null) {
			if (other.city != null)
				return false;
		} else if (!city.equals(other.city))
			return false;
		if (country == null) {
			if (other.country != null)
				return false;
		} else if (!country.equals(other.country))
			return false;
		if (postalCode == null) {
			if (other.postalCode != null)
				return false;
		} else if (!postalCode.equals(other.postalCode))
			return false;
		if (stateProvince == null) {
			if (other.stateProvince != null)
				return false;
		} else if (!stateProvince.equals(other.stateProvince))
			return false;
		if (streetAddress1 == null) {
			if (other.streetAddress1 != null)
				return false;
		} else if (!streetAddress1.equals(other.streetAddress1))
			return false;
		if (streetAddress2 == null) {
			if (other.streetAddress2 != null)
				return false;
		} else if (!streetAddress2.equals(other.streetAddress2))
			return false;
		return true;
	}
	
	
}


/*******************************************************************************
* Copyright (c) 2013-2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.morphia.entities;

import java.io.Serializable;

import org.mongodb.morphia.annotations.Entity;

import com.acmeair.entities.Customer;
import com.acmeair.entities.CustomerAddress;

@Entity(value="customer")
public class CustomerImpl implements Customer, Serializable{

	private static final long serialVersionUID = 1L;

	private String _id;
	private String password;
	private MemberShipStatus status;
	private int total_miles;
	private int miles_ytd;

	private CustomerAddress address;
	private String phoneNumber;
	private PhoneType phoneNumberType;
	
	public CustomerImpl() {
	}
	
	public CustomerImpl(String username, String password, MemberShipStatus status, int total_miles, int miles_ytd, CustomerAddress address, String phoneNumber, PhoneType phoneNumberType) {
		this._id = username;
		this.password = password;
		this.status = status;
		this.total_miles = total_miles;
		this.miles_ytd = miles_ytd;
		this.address = address;
		this.phoneNumber = phoneNumber;
		this.phoneNumberType = phoneNumberType;
	}

	public String getCustomerId(){
		return _id;
	}
	
	public String getUsername() {
		return _id;
	}
	
	public void setUsername(String username) {
		this._id = username;
	}
	
	public String getPassword() {
		return password;
	}
	
	public void setPassword(String password) {
		this.password = password;
	}
	
	public MemberShipStatus getStatus() {
		return status;
	}
	
	public void setStatus(MemberShipStatus status) {
		this.status = status;
	}
	
	public int getTotal_miles() {
		return total_miles;
	}
	
	public void setTotal_miles(int total_miles) {
		this.total_miles = total_miles;
	}
	
	public int getMiles_ytd() {
		return miles_ytd;
	}
	
	public void setMiles_ytd(int miles_ytd) {
		this.miles_ytd = miles_ytd;
	}
	
	public String getPhoneNumber() {
		return phoneNumber;
	}

	public void setPhoneNumber(String phoneNumber) {
		this.phoneNumber = phoneNumber;
	}

	public PhoneType getPhoneNumberType() {
		return phoneNumberType;
	}

	public void setPhoneNumberType(PhoneType phoneNumberType) {
		this.phoneNumberType = phoneNumberType;
	}

	public CustomerAddress getAddress() {
		return address;
	}

	public void setAddress(CustomerAddress address) {
		this.address = address;
	}

	@Override
	public String toString() {
		return "Customer [id=" + _id + ", password=" + password + ", status="
				+ status + ", total_miles=" + total_miles + ", miles_ytd="
				+ miles_ytd + ", address=" + address + ", phoneNumber="
				+ phoneNumber + ", phoneNumberType=" + phoneNumberType + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		CustomerImpl other = (CustomerImpl) obj;
		if (address == null) {
			if (other.address != null)
				return false;
		} else if (!address.equals(other.address))
			return false;
		if (_id == null) {
			if (other._id != null)
				return false;
		} else if (!_id.equals(other._id))
			return false;
		if (miles_ytd != other.miles_ytd)
			return false;
		if (password == null) {
			if (other.password != null)
				return false;
		} else if (!password.equals(other.password))
			return false;
		if (phoneNumber == null) {
			if (other.phoneNumber != null)
				return false;
		} else if (!phoneNumber.equals(other.phoneNumber))
			return false;
		if (phoneNumberType != other.phoneNumberType)
			return false;
		if (status != other.status)
			return false;
		if (total_miles != other.total_miles)
			return false;
		return true;
	}

}


/*******************************************************************************
* Copyright (c) 2013 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.entities;


public interface CustomerAddress {

	
	public String getStreetAddress1();
	public void setStreetAddress1(String streetAddress1);
	public String getStreetAddress2();
	public void setStreetAddress2(String streetAddress2);
	public String getCity();
	public void setCity(String city);
	public String getStateProvince();
	public void setStateProvince(String stateProvince);
	public String getCountry();
	public void setCountry(String country);
	public String getPostalCode();
	public void setPostalCode(String postalCode);
		
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-common/src/main/java/com/acmeair/entities/CustomerAddress.java:CustomerAddress.<init>
/*******************************************************************************
* Copyright (c) 2013 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.entities;



public interface Customer {

	public enum MemberShipStatus { NONE, SILVER, GOLD, PLATINUM, EXEC_PLATINUM, GRAPHITE };
	public enum PhoneType { UNKNOWN, HOME, BUSINESS, MOBILE };
	
	
	public String getCustomerId();
	
	public String getUsername();
	
	public void setUsername(String username);
	
	public String getPassword();
	
	public void setPassword(String password);
	
	public MemberShipStatus getStatus();
	
	public void setStatus(MemberShipStatus status);
	
	public int getTotal_miles();
	
	public int getMiles_ytd();
	
	public String getPhoneNumber();

	public void setPhoneNumber(String phoneNumber);

	public PhoneType getPhoneNumberType();

	public void setPhoneNumberType(PhoneType phoneNumberType);

	public CustomerAddress getAddress();

	public void setAddress(CustomerAddress address);

}


// Node: repos/cloned_ms_repos/acmeair/acmeair-common/src/main/java/com/acmeair/entities/Customer.java:Customer.<init>
/*******************************************************************************
* Copyright (c) 2013-2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.wxs.entities;

import java.io.Serializable;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.CustomerAddress;

@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement
public class CustomerAddressImpl implements CustomerAddress, Serializable{
	
	private static final long serialVersionUID = 1L;
	private String streetAddress1;
	private String streetAddress2;
	private String city;
	private String stateProvince;
	private String country;
	private String postalCode;

	public CustomerAddressImpl() {
	}
	
	public CustomerAddressImpl(String streetAddress1, String streetAddress2,
			String city, String stateProvince, String country, String postalCode) {
		super();
		this.streetAddress1 = streetAddress1;
		this.streetAddress2 = streetAddress2;
		this.city = city;
		this.stateProvince = stateProvince;
		this.country = country;
		this.postalCode = postalCode;
	}
	
	public String getStreetAddress1() {
		return streetAddress1;
	}
	public void setStreetAddress1(String streetAddress1) {
		this.streetAddress1 = streetAddress1;
	}
	public String getStreetAddress2() {
		return streetAddress2;
	}
	public void setStreetAddress2(String streetAddress2) {
		this.streetAddress2 = streetAddress2;
	}
	public String getCity() {
		return city;
	}
	public void setCity(String city) {
		this.city = city;
	}
	public String getStateProvince() {
		return stateProvince;
	}
	public void setStateProvince(String stateProvince) {
		this.stateProvince = stateProvince;
	}
	public String getCountry() {
		return country;
	}
	public void setCountry(String country) {
		this.country = country;
	}
	public String getPostalCode() {
		return postalCode;
	}
	public void setPostalCode(String postalCode) {
		this.postalCode = postalCode;
	}
	@Override
	public String toString() {
		return "CustomerAddress [streetAddress1=" + streetAddress1
				+ ", streetAddress2=" + streetAddress2 + ", city=" + city
				+ ", stateProvince=" + stateProvince + ", country=" + country
				+ ", postalCode=" + postalCode + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		CustomerAddressImpl other = (CustomerAddressImpl) obj;
		if (city == null) {
			if (other.city != null)
				return false;
		} else if (!city.equals(other.city))
			return false;
		if (country == null) {
			if (other.country != null)
				return false;
		} else if (!country.equals(other.country))
			return false;
		if (postalCode == null) {
			if (other.postalCode != null)
				return false;
		} else if (!postalCode.equals(other.postalCode))
			return false;
		if (stateProvince == null) {
			if (other.stateProvince != null)
				return false;
		} else if (!stateProvince.equals(other.stateProvince))
			return false;
		if (streetAddress1 == null) {
			if (other.streetAddress1 != null)
				return false;
		} else if (!streetAddress1.equals(other.streetAddress1))
			return false;
		if (streetAddress2 == null) {
			if (other.streetAddress2 != null)
				return false;
		} else if (!streetAddress2.equals(other.streetAddress2))
			return false;
		return true;
	}
	
	
}


/*******************************************************************************
* Copyright (c) 2013-2015 IBM Corp.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*******************************************************************************/
package com.acmeair.wxs.entities;

import java.io.Serializable;

import com.acmeair.entities.Customer;
import com.acmeair.entities.CustomerAddress;


public class CustomerImpl implements Customer, Serializable{
	
	private static final long serialVersionUID = 1L;

	private String _id;
	private String password;
	private MemberShipStatus status;
	private int total_miles;
	private int miles_ytd;

	private CustomerAddress address;
	private String phoneNumber;
	private PhoneType phoneNumberType;
	
	public CustomerImpl() {
	}
	
	public CustomerImpl(String username, String password, MemberShipStatus status, int total_miles, int miles_ytd, CustomerAddress address, String phoneNumber, PhoneType phoneNumberType) {
		this._id = username;
		this.password = password;
		this.status = status;
		this.total_miles = total_miles;
		this.miles_ytd = miles_ytd;
		this.address = address;
		this.phoneNumber = phoneNumber;
		this.phoneNumberType = phoneNumberType;
	}

	@Override
	public String getCustomerId() {
		return _id;
	}
	
	public String getUsername() {
		return _id;
	}
	
	public void setUsername(String username) {
		this._id = username;
	}
	
	public String getPassword() {
		return password;
	}
	
	public void setPassword(String password) {
		this.password = password;
	}
	
	public MemberShipStatus getStatus() {
		return status;
	}
	
	public void setStatus(MemberShipStatus status) {
		this.status = status;
	}
	
	public int getTotal_miles() {
		return total_miles;
	}
	
	public void setTotal_miles(int total_miles) {
		this.total_miles = total_miles;
	}
	
	public int getMiles_ytd() {
		return miles_ytd;
	}
	
	public void setMiles_ytd(int miles_ytd) {
		this.miles_ytd = miles_ytd;
	}
	
	public String getPhoneNumber() {
		return phoneNumber;
	}

	public void setPhoneNumber(String phoneNumber) {
		this.phoneNumber = phoneNumber;
	}

	public PhoneType getPhoneNumberType() {
		return phoneNumberType;
	}

	public void setPhoneNumberType(PhoneType phoneNumberType) {
		this.phoneNumberType = phoneNumberType;
	}

	public CustomerAddress getAddress() {
		return address;
	}

	public void setAddress(CustomerAddress address) {
		this.address = address;
	}

	@Override
	public String toString() {
		return "Customer [id=" + _id + ", password=" + password + ", status="
				+ status + ", total_miles=" + total_miles + ", miles_ytd="
				+ miles_ytd + ", address=" + address + ", phoneNumber="
				+ phoneNumber + ", phoneNumberType=" + phoneNumberType + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		CustomerImpl other = (CustomerImpl) obj;
		if (address == null) {
			if (other.address != null)
				return false;
		} else if (!address.equals(other.address))
			return false;
		if (_id == null) {
			if (other._id != null)
				return false;
		} else if (!_id.equals(other._id))
			return false;
		if (miles_ytd != other.miles_ytd)
			return false;
		if (password == null) {
			if (other.password != null)
				return false;
		} else if (!password.equals(other.password))
			return false;
		if (phoneNumber == null) {
			if (other.phoneNumber != null)
				return false;
		} else if (!phoneNumber.equals(other.phoneNumber))
			return false;
		if (phoneNumberType != other.phoneNumberType)
			return false;
		if (status != other.status)
			return false;
		if (total_miles != other.total_miles)
			return false;
		return true;
	}

}


