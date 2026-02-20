// Cluster 3

// Node: getCustomer
// Node: getCustomerByUsername
// Node: bookFlight
// Node: getBooking
// Node: getBookingsByUser
// Node: add
// Node: cancelBooking
// Node: validateSession
// Node: getId
// Node: invalidateSession
// Node: getFlightByAirportsAndDepartureDate
package com.acmeair.web.dto;

import java.math.BigDecimal;
import java.util.Date;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.Flight;

@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement(name="Flight")
public class FlightInfo {
	
	@XmlElement(name="_id")
	private String _id;	
	private String flightSegmentId;		
	private Date scheduledDepartureTime;
	private Date scheduledArrivalTime;
	private BigDecimal firstClassBaseCost;
	private BigDecimal economyClassBaseCost;
	private int numFirstClassSeats;
	private int numEconomyClassSeats;
	private String airplaneTypeId;
	private FlightSegmentInfo flightSegment;
	
	@XmlElement(name="pkey")
	private FlightPKInfo pkey;
	
	public FlightInfo(){
		
	}
	
	public FlightInfo(Flight flight){
		this._id = flight.getFlightId();
		this.flightSegmentId = flight.getFlightSegmentId();
		this.scheduledDepartureTime = flight.getScheduledDepartureTime();
		this.scheduledArrivalTime = flight.getScheduledArrivalTime();
		this.firstClassBaseCost = flight.getFirstClassBaseCost();
		this.economyClassBaseCost = flight.getEconomyClassBaseCost();
		this.numFirstClassSeats = flight.getNumFirstClassSeats();
		this.numEconomyClassSeats = flight.getNumEconomyClassSeats();
		this.airplaneTypeId = flight.getAirplaneTypeId();
		if(flight.getFlightSegment() != null){
			this.flightSegment = new FlightSegmentInfo(flight.getFlightSegment());
		} else {
			this.flightSegment = null;
		}
		this.pkey = new FlightPKInfo(this.flightSegmentId, this._id);
	}
	
	public String get_id() {
		return _id;
	}
	public void set_id(String _id) {
		this._id = _id;
	}
	public String getFlightSegmentId() {
		return flightSegmentId;
	}
	public void setFlightSegmentId(String flightSegmentId) {
		this.flightSegmentId = flightSegmentId;
	}
	public Date getScheduledDepartureTime() {
		return scheduledDepartureTime;
	}
	public void setScheduledDepartureTime(Date scheduledDepartureTime) {
		this.scheduledDepartureTime = scheduledDepartureTime;
	}
	public Date getScheduledArrivalTime() {
		return scheduledArrivalTime;
	}
	public void setScheduledArrivalTime(Date scheduledArrivalTime) {
		this.scheduledArrivalTime = scheduledArrivalTime;
	}
	public BigDecimal getFirstClassBaseCost() {
		return firstClassBaseCost;
	}
	public void setFirstClassBaseCost(BigDecimal firstClassBaseCost) {
		this.firstClassBaseCost = firstClassBaseCost;
	}
	public BigDecimal getEconomyClassBaseCost() {
		return economyClassBaseCost;
	}
	public void setEconomyClassBaseCost(BigDecimal economyClassBaseCost) {
		this.economyClassBaseCost = economyClassBaseCost;
	}
	public int getNumFirstClassSeats() {
		return numFirstClassSeats;
	}
	public void setNumFirstClassSeats(int numFirstClassSeats) {
		this.numFirstClassSeats = numFirstClassSeats;
	}
	public int getNumEconomyClassSeats() {
		return numEconomyClassSeats;
	}
	public void setNumEconomyClassSeats(int numEconomyClassSeats) {
		this.numEconomyClassSeats = numEconomyClassSeats;
	}
	public String getAirplaneTypeId() {
		return airplaneTypeId;
	}
	public void setAirplaneTypeId(String airplaneTypeId) {
		this.airplaneTypeId = airplaneTypeId;
	}
	public FlightSegmentInfo getFlightSegment() {
		return flightSegment;
	}
	public void setFlightSegment(FlightSegmentInfo flightSegment) {
		this.flightSegment = flightSegment;
	}
	public FlightPKInfo getPkey(){
		return pkey;
	}
}


// Node: getPkey
package com.acmeair.web.dto;

public class FlightPKInfo {

	private String id;
	private String flightSegmentId;
	
	FlightPKInfo(){}
	FlightPKInfo(String flightSegmentId,String id){
		this.id = id;
		this.flightSegmentId = flightSegmentId;
	}
	
	public String getId() {
		return id;
	}
	public void setId(String id) {
		this.id = id;
	}
	public String getFlightSegmentId() {
		return flightSegmentId;
	}
	public void setFlightSegmentId(String flightSegmentId) {
		this.flightSegmentId = flightSegmentId;
	}
}


package com.acmeair.web.dto;

import javax.xml.bind.annotation.XmlElement;



public class BookingPKInfo {

	@XmlElement(name="id")
	private String id;
	
	@XmlElement(name="customerId")
	private String customerId;
	
	public BookingPKInfo() {
		
	}


	public BookingPKInfo(String customerId,String id) {
		
		this.id = id;
		this.customerId = customerId;
	}

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getCustomerId() {
		return customerId;
	}

	public void setCustomerId(String customerId) {
		this.customerId = customerId;
	}
}


package com.acmeair.web.dto;

import java.util.Date;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlElement;
import javax.xml.bind.annotation.XmlRootElement;

import com.acmeair.entities.Booking;

@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement(name="Booking")
public class BookingInfo {

	@XmlElement(name="bookingId")
	private String bookingId;	
	
	@XmlElement(name="flightId")
	private String flightId;
	
	@XmlElement(name="customerId")
	private String customerId;
	
	@XmlElement(name="dateOfBooking")
	private Date dateOfBooking;
	
	@XmlElement(name="pkey")
	private BookingPKInfo pkey;
	
	public BookingInfo() {
		
	}

	public BookingInfo(Booking booking){
		this.bookingId = booking.getBookingId();
		this.flightId = booking.getFlightId();
		this.customerId = booking.getCustomerId();
		this.dateOfBooking = booking.getDateOfBooking();
		this.pkey = new BookingPKInfo(this.customerId, this.bookingId);
	}
	
	
	public String getBookingId() {
		return bookingId;
	}
	public void setBookingId(String bookingId) {
		this.bookingId = bookingId;
	}
	public String getFlightId() {
		return flightId;
	}
	public void setFlightId(String flightId) {
		this.flightId = flightId;
	}
	public String getCustomerId() {
		return customerId;
	}
	public void setCustomerId(String customerId) {
		this.customerId = customerId;
	}
	public Date getDateOfBooking() {
		return dateOfBooking;
	}
	public void setDateOfBooking(Date dateOfBooking) {
		this.dateOfBooking = dateOfBooking;
	}	
	public BookingPKInfo getPkey(){
		return pkey;
	}
	
}


// Node: get
// Node: storeFlightSegment
// Node: Date
// Node: contains
// Node: FlightSegmentImpl
// Node: BookingImpl
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
import java.util.Date;

import org.mongodb.morphia.annotations.Entity;

import com.acmeair.entities.CustomerSession;

@Entity(value="customerSession")
public class CustomerSessionImpl implements CustomerSession, Serializable {


	private static final long serialVersionUID = 1L;

	private String _id;
	private String customerid;
	private Date lastAccessedTime;
	private Date timeoutTime;
	
	public CustomerSessionImpl() {
	}

	public CustomerSessionImpl(String id, String customerid, Date lastAccessedTime,	Date timeoutTime) {
		this._id= id;
		this.customerid = customerid;
		this.lastAccessedTime = lastAccessedTime;
		this.timeoutTime = timeoutTime;
	}
	

	public String getId() {
		return _id;
	}

	public void setId(String id) {
		this._id = id;
	}

	public String getCustomerid() {
		return customerid;
	}

	public void setCustomerid(String customerid) {
		this.customerid = customerid;
	}

	public Date getLastAccessedTime() {
		return lastAccessedTime;
	}

	public void setLastAccessedTime(Date lastAccessedTime) {
		this.lastAccessedTime = lastAccessedTime;
	}

	public Date getTimeoutTime() {
		return timeoutTime;
	}

	public void setTimeoutTime(Date timeoutTime) {
		this.timeoutTime = timeoutTime;
	}

	@Override
	public String toString() {
		return "CustomerSession [id=" + _id + ", customerid=" + customerid
				+ ", lastAccessedTime=" + lastAccessedTime + ", timeoutTime="
				+ timeoutTime + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		CustomerSessionImpl other = (CustomerSessionImpl) obj;
		if (customerid == null) {
			if (other.customerid != null)
				return false;
		} else if (!customerid.equals(other.customerid))
			return false;
		if (_id == null) {
			if (other._id != null)
				return false;
		} else if (!_id.equals(other._id))
			return false;
		if (lastAccessedTime == null) {
			if (other.lastAccessedTime != null)
				return false;
		} else if (!lastAccessedTime.equals(other.lastAccessedTime))
			return false;
		if (timeoutTime == null) {
			if (other.timeoutTime != null)
				return false;
		} else if (!timeoutTime.equals(other.timeoutTime))
			return false;
		return true;
	}


	
}

// Node: find
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
package com.acmeair.morphia.services;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import javax.annotation.PostConstruct;
import javax.inject.Inject;

import com.acmeair.entities.AirportCodeMapping;
import com.acmeair.entities.Flight;
import com.acmeair.entities.FlightSegment;
import com.acmeair.morphia.MorphiaConstants;
import com.acmeair.morphia.entities.AirportCodeMappingImpl;
import com.acmeair.morphia.entities.FlightImpl;
import com.acmeair.morphia.entities.FlightSegmentImpl;
import com.acmeair.morphia.services.util.MongoConnectionManager;
import com.acmeair.service.DataService;
import com.acmeair.service.FlightService;
import com.acmeair.service.KeyGenerator;

import org.mongodb.morphia.Datastore;
import org.mongodb.morphia.query.Query;

@DataService(name=MorphiaConstants.KEY,description=MorphiaConstants.KEY_DESCRIPTION)
public class FlightServiceImpl extends FlightService implements  MorphiaConstants {

	//private final static Logger logger = Logger.getLogger(FlightService.class.getName()); 
		
	Datastore datastore;
	
	@Inject
	KeyGenerator keyGenerator;
	

	
	@PostConstruct
	public void initialization() {	
		datastore = MongoConnectionManager.getConnectionManager().getDatastore();
	}
	
	
	@Override
	public Long countFlights() {
		return datastore.find(FlightImpl.class).countAll();
	}
	
	@Override
	public Long countFlightSegments() {
		return datastore.find(FlightSegmentImpl.class).countAll();
	}
	
	@Override
	public Long countAirports() {
		return datastore.find(AirportCodeMappingImpl.class).countAll();
	}
	
	/*
	@Override
	public Flight getFlightByFlightId(String flightId, String flightSegmentId) {
		try {
			Flight flight = flightPKtoFlightCache.get(flightId);
			if (flight == null) {
				Query<FlightImpl> q = datastore.find(FlightImpl.class).field("_id").equal(flightId);
				flight = q.get();
				if (flightId != null && flight != null) {
					flightPKtoFlightCache.putIfAbsent(flight, flight);
				}
			}
			return flight;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	*/
	
	protected Flight getFlight(String flightId, String segmentId) {
		Query<FlightImpl> q = datastore.find(FlightImpl.class).field("_id").equal(flightId);
		return q.get();
	}

	@Override
	protected  FlightSegment getFlightSegment(String fromAirport, String toAirport){
		Query<FlightSegmentImpl> q = datastore.find(FlightSegmentImpl.class).field("originPort").equal(fromAirport).field("destPort").equal(toAirport);
		FlightSegment segment = q.get();
		if (segment == null) {
			segment = new FlightSegmentImpl(); // put a sentinel value of a non-populated flightsegment 
		}
		return segment;
	}
	
	@Override
	protected  List<Flight> getFlightBySegment(FlightSegment segment, Date deptDate){
		Query<FlightImpl> q2;
		if(deptDate != null) {
			q2 = datastore.find(FlightImpl.class).disableValidation().field("flightSegmentId").equal(segment.getFlightName()).field("scheduledDepartureTime").equal(deptDate);
		} else {
			q2 = datastore.find(FlightImpl.class).disableValidation().field("flightSegmentId").equal(segment.getFlightName());
		}
		List<FlightImpl> flightImpls = q2.asList();
		List<Flight> flights;
		if (flightImpls != null) {
			flights =  new ArrayList<Flight>(); 
			for (Flight flight : flightImpls) {
				flight.setFlightSegment(segment);
				flights.add(flight);
			}
		}
		else {
			flights = new ArrayList<Flight>(); // put an empty list into the cache in the cache in the case where no matching flights
		}
		return flights;
	}
	

	@Override
	public void storeAirportMapping(AirportCodeMapping mapping) {
		try{
			datastore.save(mapping);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override 
	public AirportCodeMapping createAirportCodeMapping(String airportCode, String airportName){
		AirportCodeMapping acm = new AirportCodeMappingImpl(airportCode, airportName);
		return acm;
	}
	
	@Override
	public Flight createNewFlight(String flightSegmentId,
			Date scheduledDepartureTime, Date scheduledArrivalTime,
			BigDecimal firstClassBaseCost, BigDecimal economyClassBaseCost,
			int numFirstClassSeats, int numEconomyClassSeats,
			String airplaneTypeId) {
		String id = keyGenerator.generate().toString();
		Flight flight = new FlightImpl(id, flightSegmentId,
			scheduledDepartureTime, scheduledArrivalTime,
			firstClassBaseCost, economyClassBaseCost,
			numFirstClassSeats, numEconomyClassSeats,
			airplaneTypeId);
		try{
			datastore.save(flight);
			return flight;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public void storeFlightSegment(FlightSegment flightSeg) {
		try{
			datastore.save(flightSeg);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	
	@Override 
	public void storeFlightSegment(String flightName, String origPort, String destPort, int miles) {
		FlightSegment flightSeg = new FlightSegmentImpl(flightName, origPort, destPort, miles);
		storeFlightSegment(flightSeg);
	}
}


// Node: getFlightByFlightId
// Node: field
// Node: equal
// Node: putIfAbsent
// Node: RuntimeException
// Node: getFlight
// Node: getFlightBySegment
// Node: disableValidation
// Node: generate
package com.acmeair.morphia.services;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import javax.annotation.PostConstruct;
import javax.inject.Inject;

import org.mongodb.morphia.Datastore;

import com.acmeair.entities.Booking;
import com.acmeair.entities.Customer;
import com.acmeair.entities.Flight;
import com.acmeair.morphia.MorphiaConstants;
import com.acmeair.morphia.entities.BookingImpl;
import com.acmeair.morphia.services.util.MongoConnectionManager;
import com.acmeair.service.BookingService;
import com.acmeair.service.CustomerService;
import com.acmeair.service.DataService;
import com.acmeair.service.FlightService;
import com.acmeair.service.KeyGenerator;
import com.acmeair.service.ServiceLocator;

import org.mongodb.morphia.query.Query;



@DataService(name=MorphiaConstants.KEY,description=MorphiaConstants.KEY_DESCRIPTION)
public class BookingServiceImpl implements BookingService, MorphiaConstants {

	//private final static Logger logger = Logger.getLogger(BookingService.class.getName()); 

		
	Datastore datastore;
	
	@Inject 
	KeyGenerator keyGenerator;
	
	private FlightService flightService = ServiceLocator.instance().getService(FlightService.class);
	private CustomerService customerService = ServiceLocator.instance().getService(CustomerService.class);


	@PostConstruct
	public void initialization() {	
		datastore = MongoConnectionManager.getConnectionManager().getDatastore();	
	}	
	
	
	
	public String bookFlight(String customerId, String flightId) {
		try{
			Flight f = flightService.getFlightByFlightId(flightId, null);
			Customer c = customerService.getCustomerByUsername(customerId);
			
			Booking newBooking = new BookingImpl(keyGenerator.generate().toString(), new Date(), c, f);

			datastore.save(newBooking);
			return newBooking.getBookingId();
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public String bookFlight(String customerId, String flightSegmentId, String flightId) {
		return bookFlight(customerId, flightId);	
	}
	
	@Override
	public Booking getBooking(String user, String bookingId) {
		try{
			Query<BookingImpl> q = datastore.find(BookingImpl.class).field("_id").equal(bookingId);
			Booking booking = q.get();
			
			return booking;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public List<Booking> getBookingsByUser(String user) {
		try{
			Query<BookingImpl> q = datastore.find(BookingImpl.class).disableValidation().field("customerId").equal(user);
			List<BookingImpl> bookingImpls = q.asList();
			List<Booking> bookings = new ArrayList<Booking>();
			for(Booking b: bookingImpls){
				bookings.add(b);
			}
			return bookings;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public void cancelBooking(String user, String bookingId) {
		try{
			datastore.delete(BookingImpl.class, bookingId);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	
	
	@Override
	public Long count() {
		return datastore.find(BookingImpl.class).countAll();
	}	
}


// Node: delete
package com.acmeair.morphia.services;

import java.util.Date;

import javax.annotation.PostConstruct;

import com.acmeair.entities.Customer;
import com.acmeair.entities.Customer.MemberShipStatus;
import com.acmeair.entities.Customer.PhoneType;
import com.acmeair.entities.CustomerAddress;
import com.acmeair.entities.CustomerSession;
import com.acmeair.morphia.entities.CustomerAddressImpl;
import com.acmeair.morphia.entities.CustomerSessionImpl;
import com.acmeair.morphia.MorphiaConstants;
import com.acmeair.morphia.entities.CustomerImpl;
import com.acmeair.morphia.services.util.MongoConnectionManager;
import com.acmeair.service.DataService;
import com.acmeair.service.CustomerService;

import org.mongodb.morphia.Datastore;
import org.mongodb.morphia.query.Query;



@DataService(name=MorphiaConstants.KEY,description=MorphiaConstants.KEY_DESCRIPTION)
public class CustomerServiceImpl extends CustomerService implements MorphiaConstants {	
		
//	private final static Logger logger = Logger.getLogger(CustomerService.class.getName()); 
	
	protected Datastore datastore;
		
	
	@PostConstruct
	public void initialization() {	
		datastore = MongoConnectionManager.getConnectionManager().getDatastore();
	}
	
	@Override
	public Long count() {
		return datastore.find(CustomerImpl.class).countAll();
	}
	
	@Override
	public Long countSessions() {
		return datastore.find(CustomerSessionImpl.class).countAll();
	}
	
	@Override
	public Customer createCustomer(String username, String password,
			MemberShipStatus status, int total_miles, int miles_ytd,
			String phoneNumber, PhoneType phoneNumberType,
			CustomerAddress address) {
	
		Customer customer = new CustomerImpl(username, password, status, total_miles, miles_ytd, address, phoneNumber, phoneNumberType);
		datastore.save(customer);
		return customer;
	}
	
	@Override 
	public CustomerAddress createAddress (String streetAddress1, String streetAddress2,
			String city, String stateProvince, String country, String postalCode){
		CustomerAddress address = new CustomerAddressImpl(streetAddress1, streetAddress2,
				 city, stateProvince,  country,  postalCode);
		return address;
	}

	@Override
	public Customer updateCustomer(Customer customer) {
		datastore.save(customer);
		return customer;
	}

	@Override
	protected Customer getCustomer(String username) {
		Query<CustomerImpl> q = datastore.find(CustomerImpl.class).field("_id").equal(username);
		Customer customer = q.get();					
		return customer;
	}
	
	@Override
	public Customer getCustomerByUsername(String username) {
		Query<CustomerImpl> q = datastore.find(CustomerImpl.class).field("_id").equal(username);
		Customer customer = q.get();
		if (customer != null) {
			customer.setPassword(null);
		}			
		return customer;
	}
	
	@Override
	protected CustomerSession getSession(String sessionid){
		Query<CustomerSessionImpl> q = datastore.find(CustomerSessionImpl.class).field("_id").equal(sessionid);		
		return q.get();
	}
	
	@Override
	protected void removeSession(CustomerSession session){		
		datastore.delete(session);	
	}
	
	@Override
	protected  CustomerSession createSession(String sessionId, String customerId, Date creation, Date expiration) {
		CustomerSession cSession = new CustomerSessionImpl(sessionId, customerId, creation, expiration);
		datastore.save(cSession);
		return cSession;
	}

	@Override
	public void invalidateSession(String sessionid) {		
		Query<CustomerSessionImpl> q = datastore.find(CustomerSessionImpl.class).field("_id").equal(sessionid);
		datastore.delete(q);
	}

}


// Node: getSession
// Node: removeSession
// Node: SuppressWarnings
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
package com.acmeair.service;

import java.util.Calendar;
import java.util.Date;

import javax.inject.Inject;

import com.acmeair.entities.Customer;
import com.acmeair.entities.CustomerAddress;
import com.acmeair.entities.Customer.MemberShipStatus;
import com.acmeair.entities.Customer.PhoneType;
import com.acmeair.entities.CustomerSession;

public abstract class CustomerService {
	protected static final int DAYS_TO_ALLOW_SESSION = 1;
	
	@Inject
	protected KeyGenerator keyGenerator;
	
	public abstract Customer createCustomer(
			String username, String password, MemberShipStatus status, int total_miles,
			int miles_ytd, String phoneNumber, PhoneType phoneNumberType, CustomerAddress address);
	
	public abstract CustomerAddress createAddress (String streetAddress1, String streetAddress2,
			String city, String stateProvince, String country, String postalCode);
	
	public abstract Customer updateCustomer(Customer customer);
		
	
	protected abstract Customer getCustomer(String username);
	
	public Customer getCustomerByUsername(String username) {
		Customer c = getCustomer(username);
		if (c != null) {
			c.setPassword(null);
		}
		return c;
	}
	
	public boolean validateCustomer(String username, String password) {
		boolean validatedCustomer = false;
		Customer customerToValidate = getCustomer(username);
		if (customerToValidate != null) {
			validatedCustomer = password.equals(customerToValidate.getPassword());
		}
		return validatedCustomer;
	}
	
	public Customer getCustomerByUsernameAndPassword(String username,
			String password) {
		Customer c = getCustomer(username);
		if (!c.getPassword().equals(password)) {
			return null;
		}
		// Should we also set the password to null?
		return c;
	}
		
	public CustomerSession validateSession(String sessionid) {
		CustomerSession cSession = getSession(sessionid);
		if (cSession == null) {
			return null;
		}

		Date now = new Date();

		if (cSession.getTimeoutTime().before(now)) {
			removeSession(cSession);
			return null;
		}
		return cSession;		
	}
	
	protected abstract CustomerSession getSession(String sessionid);
	
	protected abstract void removeSession(CustomerSession session);
	
	public CustomerSession createSession(String customerId) {
		String sessionId = keyGenerator.generate().toString();
		Date now = new Date();
		Calendar c = Calendar.getInstance();
		c.setTime(now);
		c.add(Calendar.DAY_OF_YEAR, DAYS_TO_ALLOW_SESSION);
		Date expiration = c.getTime();
		
		return createSession(sessionId, customerId, now, expiration);
	}
	
	protected abstract CustomerSession createSession(String sessionId, String customerId, Date creation, Date expiration);

	public abstract void invalidateSession(String sessionid);
	
	public abstract Long count();
	
	public abstract Long countSessions();
	
}


// Node: before
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
package com.acmeair.service;

import java.util.List;

import com.acmeair.entities.Booking;


public interface BookingService {

	//String bookFlight(String customerId, FlightPK flightId);
//	String bookFlight(String customerId, String flightId);
	
	String bookFlight(String customerId, String flightSegmentId, String FlightId);
	
	Booking getBooking(String user, String id);

	List<Booking> getBookingsByUser(String user);
	
	void cancelBooking(String user, String id);
	
	Long count();
}

// Node: repos/cloned_ms_repos/acmeair/acmeair-services/src/main/java/com/acmeair/service/BookingService.java:BookingService.<init>
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
package com.acmeair.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.acmeair.entities.Flight;
import com.acmeair.entities.FlightSegment;
import com.acmeair.entities.AirportCodeMapping;

public abstract class FlightService {
	protected Logger logger =  Logger.getLogger(FlightService.class.getName());
	
	//TODO:need to find a way to invalidate these maps
	protected static ConcurrentHashMap<String, FlightSegment> originAndDestPortToSegmentCache = new ConcurrentHashMap<String,FlightSegment>();
	protected static ConcurrentHashMap<String, List<Flight>> flightSegmentAndDataToFlightCache = new ConcurrentHashMap<String,List<Flight>>();
	protected static ConcurrentHashMap<String, Flight> flightPKtoFlightCache = new ConcurrentHashMap<String, Flight>();
	
	

	public Flight getFlightByFlightId(String flightId, String flightSegment) {
		try {
			Flight flight = flightPKtoFlightCache.get(flightId);
			if (flight == null) {				
				flight = getFlight(flightId, flightSegment);
				if (flightId != null && flight != null) {
					flightPKtoFlightCache.putIfAbsent(flightId, flight);
				}
			}
			return flight;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	
	
	protected abstract Flight getFlight(String flightId, String flightSegment);
	
	public List<Flight> getFlightByAirportsAndDepartureDate(String fromAirport,	String toAirport, Date deptDate) {
		if(logger.isLoggable(Level.FINE))
			logger.fine("Search for flights from "+ fromAirport + " to " + toAirport + " on " + deptDate.toString());

		String originPortAndDestPortQueryString= fromAirport+toAirport;
		FlightSegment segment = originAndDestPortToSegmentCache.get(originPortAndDestPortQueryString);

		if (segment == null) {
			segment = getFlightSegment(fromAirport, toAirport);
			originAndDestPortToSegmentCache.putIfAbsent(originPortAndDestPortQueryString, segment);
		}		
		// cache flights that not available (checks against sentinel value above indirectly)
		if (segment.getFlightName() == null) {
			return new ArrayList<Flight>(); 
		}

		String segId = segment.getFlightName();
		String flightSegmentIdAndScheduledDepartureTimeQueryString = segId + deptDate.toString();
		List<Flight> flights = flightSegmentAndDataToFlightCache.get(flightSegmentIdAndScheduledDepartureTimeQueryString);

		if (flights == null) {				
			flights = getFlightBySegment(segment, deptDate);
			flightSegmentAndDataToFlightCache.putIfAbsent(flightSegmentIdAndScheduledDepartureTimeQueryString, flights);
		}
		if(logger.isLoggable(Level.FINEST))
			logger.finest("Returning "+ flights);
		return flights;

	}

	// NOTE:  This is not cached
	public List<Flight> getFlightByAirports(String fromAirport, String toAirport) {
			FlightSegment segment = getFlightSegment(fromAirport, toAirport);
			if (segment == null) {
				return new ArrayList<Flight>(); 
			}	
			return getFlightBySegment(segment, null);
	}
	
	protected abstract FlightSegment getFlightSegment(String fromAirport, String toAirport);
	
	protected abstract List<Flight> getFlightBySegment(FlightSegment segment, Date deptDate);  
			
	public abstract void storeAirportMapping(AirportCodeMapping mapping);

	public abstract AirportCodeMapping createAirportCodeMapping(String airportCode, String airportName);
	
	public abstract Flight createNewFlight(String flightSegmentId,
			Date scheduledDepartureTime, Date scheduledArrivalTime,
			BigDecimal firstClassBaseCost, BigDecimal economyClassBaseCost,
			int numFirstClassSeats, int numEconomyClassSeats,
			String airplaneTypeId);

	public abstract void storeFlightSegment(FlightSegment flightSeg);
	
	public abstract void storeFlightSegment(String flightName, String origPort, String destPort, int miles);
	
	public abstract Long countFlightSegments();
	
	public abstract Long countFlights();
	
	public abstract Long countAirports();
	
}

// Node: isLoggable
// Node: available
// Node: finest
// Node: remove
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
package com.acmeair.wxs.utils;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;
import java.util.logging.Logger;

import com.ibm.websphere.objectgrid.ObjectGridException;
import com.ibm.websphere.objectgrid.ObjectMap;
import com.ibm.websphere.objectgrid.Session;
import com.ibm.websphere.objectgrid.datagrid.MapGridAgent;
import com.ibm.websphere.objectgrid.plugins.io.dataobject.SerializedKey;

public class MapPutAllAgent implements MapGridAgent  {
	
	private static final long serialVersionUID = 1L;

	private static final Logger logger = Logger.getLogger(MapPutAllAgent.class.getName());
	
	private HashMap<Object, HashMap<Object,Object>>objectsToSave = null  ;

	public HashMap<Object, HashMap<Object,Object>> getObjectsToSave() {
		return objectsToSave;
	}

	public void setObjectsToSave(HashMap<Object,HashMap<Object,Object>> objectsToSave) {
		this.objectsToSave = objectsToSave;
	}

	//@Override
	public Object process(Session arg0, ObjectMap arg1, Object arg2) {
		// The key is the partition key, can be either the PK or when partition field is defined the partition field value
		try{
			Object key;
			// I need to find the real key as the hashmap is using the real key...
     		if( arg2 instanceof SerializedKey )
    		     key = ((SerializedKey)arg2).getObject();
    		else 
    		     key = arg2;     		
			
			HashMap<Object, Object> objectsForThePartition =  this.objectsToSave.get(key);
			
			if (objectsForThePartition==null)
				logger.info("ERROR!!! Can not get the objects for partiton key:"+arg2);
			else
			{
				Entry<Object, Object> entry;
				Object value;
				for (Iterator<Map.Entry<Object, Object>> itr = objectsForThePartition.entrySet().iterator(); itr.hasNext();)
				{
					entry = itr.next();
					key = entry.getKey();
					value = entry.getValue();
					
					logger.finer("Save using agent:"+key+",value:"+value);
					arg1.upsert(key, value);
				}
			}
		}catch (ObjectGridException e)
		{
			logger.info("Getting exception:"+e);
		}
		return arg2;	
	}

	//@Override
	public Map<Object, Object> processAllEntries(Session arg0, ObjectMap arg1) {
		return null; 
	}

}

// Node: getObject
// Node: finer
// Node: upsert
// Node: connectClient
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
package com.acmeair.wxs.utils;


import java.util.HashMap;
import java.util.concurrent.atomic.AtomicReference;
import java.util.logging.Logger;

import javax.naming.InitialContext;
import javax.naming.NamingException;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;

import com.acmeair.service.DataService;
import com.acmeair.service.TransactionService;
import com.acmeair.wxs.WXSConstants;
import com.ibm.websphere.objectgrid.BackingMap;
import com.ibm.websphere.objectgrid.ClientClusterContext;
import com.ibm.websphere.objectgrid.ObjectGrid;
import com.ibm.websphere.objectgrid.ObjectGridException;
import com.ibm.websphere.objectgrid.ObjectGridManager;
import com.ibm.websphere.objectgrid.ObjectGridManagerFactory;
import com.ibm.websphere.objectgrid.ObjectGridRuntimeException;
import com.ibm.websphere.objectgrid.Session;
import com.ibm.websphere.objectgrid.config.BackingMapConfiguration;
import com.ibm.websphere.objectgrid.config.ObjectGridConfigFactory;
import com.ibm.websphere.objectgrid.config.ObjectGridConfiguration;
import com.ibm.websphere.objectgrid.config.Plugin;
import com.ibm.websphere.objectgrid.config.PluginType;
import com.ibm.websphere.objectgrid.security.config.ClientSecurityConfiguration;
import com.ibm.websphere.objectgrid.security.config.ClientSecurityConfigurationFactory;
import com.ibm.websphere.objectgrid.security.plugins.CredentialGenerator;
import com.ibm.websphere.objectgrid.security.plugins.builtins.UserPasswordCredentialGenerator;
import com.ibm.websphere.objectgrid.spring.SpringLocalTxManager;

@DataService(name=WXSConstants.KEY,description=WXSConstants.KEY_DESCRIPTION)
public class WXSSessionManager implements TransactionService, WXSConstants{
	
		private static final String GRID_CONNECT_LOOKUP_KEY = "com.acmeair.service.wxs.gridConnect";
		private static final String GRID_NAME_LOOKUP_KEY = "com.acmeair.service.wxs.gridName";
		private static final String GRID_DISABLE_NEAR_CACHE_NAME_LOOKUP_KEY = "com.acmeair.service.wxs.disableNearCacheName";
		private static final String GRID_PARTITION_FIELD_NAME_LOOKUP_KEY = "com.acmeair.service.wxs.partitionFieldName";
		private static final Logger logger = Logger.getLogger(WXSSessionManager.class.getName());
		private static final String SPLIT_COMMA = "\\s*,\\s*";
		private static final String SPLIT_COLON = "\\s*:\\s*";		
	
		private String gridConnectString;
		private String gridUsername = null;
		private String gridPassword = null;
		private String gridName = "Grid";
		private boolean integrateWithWASTransactions = false;
		private String disableNearCacheNameString;
		private String[] disableNearCacheNames = null;
		private String partitionFieldNameString;
		private HashMap<String, String> partitionFieldNames = null; // For now to make it simple to only support one partition field
		private SpringLocalTxManager txManager;
        private String mapSuffix = "";
		private AtomicReference<ObjectGrid> sharedGrid = new AtomicReference<ObjectGrid>();
		private static AtomicReference<WXSSessionManager> connectionManager = new AtomicReference<WXSSessionManager>();
		
		
		public static WXSSessionManager getSessionManager() {
			if (connectionManager.get() == null) {
				synchronized (connectionManager) {
					if (connectionManager.get() == null) {
						connectionManager.set(new WXSSessionManager());
					}
				}
			}
			return connectionManager.get();
		}	
		
		
		private WXSSessionManager(){
			ObjectGrid og = null;
			
			try {
				InitialContext ic = new InitialContext();			
				og = (ObjectGrid) ic.lookup(JNDI_NAME);
				
			} catch (NamingException e) {
				logger.warning("Unable to look up the ObjectGrid reference " + e.getMessage());
			}
			if(og != null) {
				sharedGrid.set(og);
			} else {				
				initialization();				
			}
			
		}
		
		
		private void initialization()  {		
			
			
			String vcapJSONString = System.getenv("VCAP_SERVICES");
			if (vcapJSONString != null) {
				logger.info("Reading VCAP_SERVICES");
				Object jsonObject = JSONValue.parse(vcapJSONString);
				logger.info("jsonObject = " + ((JSONObject)jsonObject).toJSONString());
				JSONObject json = (JSONObject)jsonObject;
				String key;
				for (Object k: json.keySet())
				{
					key = (String ) k;
					if (key.startsWith("ElasticCaching")||key.startsWith("DataCache"))
					{
						JSONArray elasticCachingServiceArray = (JSONArray)json.get(key);
						JSONObject elasticCachingService = (JSONObject)elasticCachingServiceArray.get(0); 
						JSONObject credentials = (JSONObject)elasticCachingService.get("credentials");
						String username = (String)credentials.get("username");
						setGridUsername(username);
						String password = (String)credentials.get("password");
						setGridPassword(password);
						String gridName = (String)credentials.get("gridName");
						String catalogEndPoint = (String)credentials.get("catalogEndPoint");
						logger.info("username = " + username + "; password = " + password + "; gridName =  " + gridName + "; catalogEndpoint = " + catalogEndPoint);
						setGridConnectString(catalogEndPoint);
						setGridName(gridName);
						break;
					}
				}
				setMapSuffix(".NONE.O");
			} else {
				logger.info("Creating the WXS Client connection. Looking up host and port information" );
				gridName = lookup(GRID_NAME_LOOKUP_KEY);
				if(gridName == null){
					gridName = "AcmeGrid";
				}

				gridConnectString = lookup(GRID_CONNECT_LOOKUP_KEY);
				if(gridConnectString == null){							
					gridConnectString = "127.0.0.1:2809";
					logger.info("Using default grid connection setting of " + gridConnectString);
				}

				setDisableNearCacheNameString(lookup(GRID_DISABLE_NEAR_CACHE_NAME_LOOKUP_KEY));
				setPartitionFieldNameString(lookup(GRID_PARTITION_FIELD_NAME_LOOKUP_KEY));

			}
			
			
			if(getDisableNearCacheNameString() == null){
				setDisableNearCacheNameString("Flight,FlightSegment,AirportCodeMapping,CustomerSession,Booking,Customer");
				logger.info("Using default disableNearCacheNameString value of " + disableNearCacheNameString);
			}
			
			if(getPartitionFieldNameString() == null){
				setPartitionFieldNameString("Flight:pk.flightSegmentId,FlightSegment:originPort,Booking:pk.customerId");
				logger.info("Using default partitionFieldNameString value of " + partitionFieldNameString);
			}
			
			if (!integrateWithWASTransactions && txManager!=null) // Using Spring TX if WAS TX is not enabled
			{
				logger.info("Session will be created from SpringLocalTxManager w/ tx support.");
			}else
			{
				txManager=null;
				logger.info("Session will be created from ObjectGrid directly w/o tx support.");
			}
			
			
			try {
				prepareForTransaction();
			} catch (ObjectGridException e) {
				e.printStackTrace();
			} 
		}	
		
		private String lookup (String key){
			String value = null;
			String lookup = key.replace('.', '/');
			javax.naming.Context context = null;
			javax.naming.Context envContext = null;
			try {
				context = new javax.naming.InitialContext();
				envContext = (javax.naming.Context) context.lookup("java:comp/env");
				if (envContext != null)
					value = (String) envContext.lookup(lookup);
			} catch (NamingException e) {  }
			
			if (value != null) {
				logger.info("JNDI Found " + lookup + " : " + value);
			}
			else if (context != null) {
				try {
					value = (String) context.lookup(lookup);
					if (value != null)
						logger.info("JNDI Found " +lookup + " : " + value);
				} catch (NamingException e) {	}
			}

			if (value == null) {
				value = System.getProperty(key);
				if (value != null)
					logger.info("Found " + key + " in jvm property : " + value);
				else {
					value = System.getenv(key);
					if (value != null)
						logger.info("Found "+key+" in environment property : " + value);
				}
			}
			return value;
		}
		
	    /**
	     * Connect to a remote ObjectGrid
	     * @param cep the catalog server end points in the form: <host>:<port>
	     * @param gridName the name of the ObjectGrid to connect to that is managed by the Catalog Service
	     * @return a client ObjectGrid connection.
	     */
		private ObjectGrid connectClient(String cep, String gridName, boolean integrateWithWASTransactions,String[] disableNearCacheNames) {
			try {
				ObjectGrid gridToReturn = sharedGrid.get();
				if (gridToReturn == null) {
					synchronized(sharedGrid) {
						if (sharedGrid.get() == null) {
							ObjectGridManager ogm = ObjectGridManagerFactory.getObjectGridManager();
							ObjectGridConfiguration ogConfig = ObjectGridConfigFactory.createObjectGridConfiguration(gridName);
							if (integrateWithWASTransactions) // Using WAS Transactions as Highest Priority
							{

								Plugin trans = ObjectGridConfigFactory.createPlugin(PluginType.TRANSACTION_CALLBACK,
										"com.ibm.websphere.objectgrid.plugins.builtins.WebSphereTransactionCallback");
								ogConfig.addPlugin(trans);
							}
							if (disableNearCacheNames!=null) {
								String mapNames[] = disableNearCacheNames;
								for (String mName : mapNames) {									
									BackingMapConfiguration bmc = ObjectGridConfigFactory.createBackingMapConfiguration(mName);
									bmc.setNearCacheEnabled(false);
									ogConfig.addBackingMapConfiguration(bmc);
								}
							}					
													
							ClientClusterContext ccc = null;
							if (gridUsername != null) {
								ClientSecurityConfiguration clientSC = ClientSecurityConfigurationFactory.getClientSecurityConfiguration();
								clientSC.setSecurityEnabled(true);
								CredentialGenerator credGen = new UserPasswordCredentialGenerator(gridUsername, gridPassword);
								clientSC.setCredentialGenerator(credGen);
								ccc = ogm.connect(cep, clientSC, null);
							}
							else {
								ccc = ogm.connect(cep, null, null);
							}

							ObjectGrid grid = ObjectGridManagerFactory.getObjectGridManager().getObjectGrid(ccc, gridName, ogConfig);
							sharedGrid.compareAndSet(null, grid);
							gridToReturn = grid;
							logger.info("Create instance of Grid: " + gridToReturn);
						}else{
							gridToReturn = sharedGrid.get(); 
						}
					}
				}
				return gridToReturn;
			} catch (Exception e) {
				throw new ObjectGridRuntimeException("Unable to connect to catalog server at endpoints:" + cep,	e);
			}
		}
		public String getMapSuffix(){
			return mapSuffix;
		}
		
		public void setMapSuffix(String suffix){
			this.mapSuffix = suffix;
		}
		
		public String getGridConnectString() {
			return gridConnectString;
		}
		public void setGridConnectString(String gridConnectString) {
			this.gridConnectString = gridConnectString;
		}
		public String getGridName() {
			return gridName;
		}
		public void setGridName(String gridName) {
			this.gridName = gridName;
		}
		public String getGridUsername() {
			return gridUsername;
		}

		public void setGridUsername(String gridUsername) {
			this.gridUsername = gridUsername;
		}

		public String getGridPassword() {
			return gridPassword;
		}

		public void setGridPassword(String gridPassword) {
			this.gridPassword = gridPassword;
		}

		public boolean isIntegrateWithWASTransactions() {
			return integrateWithWASTransactions;
		}
		public void setIntegrateWithWASTransactions(boolean integrateWithWASTransactions) {
			this.integrateWithWASTransactions = integrateWithWASTransactions;
		}

		public String getDisableNearCacheNameString() {
			return disableNearCacheNameString;
		}
		public void setDisableNearCacheNameString(String disableNearCacheNameString) {
			this.disableNearCacheNameString = disableNearCacheNameString;
			if (disableNearCacheNameString ==null || disableNearCacheNameString.length()==0)
				disableNearCacheNames =null;
			else
				disableNearCacheNames = disableNearCacheNameString.split(SPLIT_COMMA);
		}
		
		public String getPartitionFieldNameString() {
			return partitionFieldNameString;
		}
		public void setPartitionFieldNameString(String partitionFieldNameString) {
			this.partitionFieldNameString = partitionFieldNameString;
			// In the form of <MapName>:<PartitionFieldName>,<MapName>:<PartitionFieldName>
			if (partitionFieldNameString ==null || partitionFieldNameString.length()==0)
				partitionFieldNames =null;
			else
			{
				String[] maps = partitionFieldNameString.split(SPLIT_COMMA);
				partitionFieldNames = new HashMap<String, String>();
				String[] mapDef;
				for (int i=0; i<maps.length; i++)
				{
					mapDef = maps[i].split(SPLIT_COLON);
					partitionFieldNames.put(mapDef[0], mapDef[1]);
				}
			}
			
		}
		public String getPartitionFieldName(String mapName) {
			if (partitionFieldNames == null)
				return null;
			return partitionFieldNames.get(mapName);
		}
		
		public SpringLocalTxManager getTxManager() {
			return txManager;
		}
		
		public void setTxManager(SpringLocalTxManager txManager) {
			logger.finer("txManager:"+txManager);
			this.txManager = txManager;
		}
		
		
		// This method needs to be called by the client from its thread before triggering a service with @Transactional annotation
		public void prepareForTransaction() throws ObjectGridException
		{
			ObjectGrid grid = this.getObjectGrid();
			if (txManager!=null)
				txManager.setObjectGridForThread(grid);
		}
		
		// Helper function
		public ObjectGrid getObjectGrid() throws ObjectGridException {
			ObjectGrid grid = connectClient(this.gridConnectString, this.gridName, this.integrateWithWASTransactions, this.disableNearCacheNames);
			return grid;
		}

		public Session getObjectGridSession() throws ObjectGridException {
			Session result;
			ObjectGrid grid = getObjectGrid();
			if (txManager!=null)
				result= txManager.getSession();
			else
				result = grid.getSession();
			
//			this.log.debug("Got session:"+ result);
			return result;
		}
		
		public BackingMap getBackingMap(String mapName)throws ObjectGridException
		{
			return this.getObjectGrid().getMap(mapName);			
		}
		
		
}


// Node: getPartitionFieldName
// Node: setTxManager
// Node: setObjectGridForThread
// Node: getObjectGridSession
// Node: debug
// Node: getBackingMap
// Node: getMap
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
package com.acmeair.wxs.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.annotation.PostConstruct;
import javax.inject.Inject;

import com.acmeair.entities.AirportCodeMapping;
import com.acmeair.entities.Flight;
import com.acmeair.entities.FlightSegment;
import com.acmeair.service.BookingService;
import com.acmeair.service.DataService;
import com.acmeair.service.FlightService;
import com.acmeair.service.KeyGenerator;
import com.acmeair.wxs.WXSConstants;
import com.acmeair.wxs.entities.AirportCodeMappingImpl;
import com.acmeair.wxs.entities.FlightImpl;
import com.acmeair.wxs.entities.FlightSegmentImpl;
import com.acmeair.wxs.utils.WXSSessionManager;
import com.ibm.websphere.objectgrid.ObjectGrid;
import com.ibm.websphere.objectgrid.ObjectGridException;
import com.ibm.websphere.objectgrid.ObjectMap;
import com.ibm.websphere.objectgrid.Session;
import com.ibm.websphere.objectgrid.UndefinedMapException;
import com.ibm.websphere.objectgrid.plugins.TransactionCallbackException;
import com.ibm.websphere.objectgrid.plugins.index.MapIndex;
import com.ibm.websphere.objectgrid.plugins.index.MapIndexPlugin;

@DataService(name=WXSConstants.KEY,description=WXSConstants.KEY_DESCRIPTION)
public class FlightServiceImpl extends FlightService implements  WXSConstants {

	private static String FLIGHT_MAP_NAME="Flight";
	private static String FLIGHT_SEGMENT_MAP_NAME="FlightSegment";
	private static String AIRPORT_CODE_MAPPING_MAP_NAME="AirportCodeMapping";
	
	private static String BASE_FLIGHT_MAP_NAME="Flight";
	private static String BASE_FLIGHT_SEGMENT_MAP_NAME="FlightSegment";
	private static String BASE_AIRPORT_CODE_MAPPING_MAP_NAME="AirportCodeMapping";
	
	private final static Logger logger = Logger.getLogger(BookingService.class.getName()); 
	
	private ObjectGrid og;
	
	@Inject
	KeyGenerator keyGenerator;
	
	
	@PostConstruct
	private void initialization()  {	
		try {
			og = WXSSessionManager.getSessionManager().getObjectGrid();
			FLIGHT_MAP_NAME = BASE_FLIGHT_MAP_NAME + WXSSessionManager.getSessionManager().getMapSuffix();
			FLIGHT_SEGMENT_MAP_NAME = BASE_FLIGHT_SEGMENT_MAP_NAME + WXSSessionManager.getSessionManager().getMapSuffix();
			AIRPORT_CODE_MAPPING_MAP_NAME = BASE_AIRPORT_CODE_MAPPING_MAP_NAME + WXSSessionManager.getSessionManager().getMapSuffix();
		} catch (ObjectGridException e) {
			logger.severe("Unable to retreive the ObjectGrid reference " + e.getMessage());
		}
	}
	
	@Override
	public Long countFlights() {
		try {
			Session session = og.getSession();
			ObjectMap objectMap = session.getMap(FLIGHT_MAP_NAME);			
			MapIndex mapIndex = (MapIndex)objectMap.getIndex(MapIndexPlugin.SYSTEM_KEY_INDEX_NAME);			
			Iterator<?> keyIterator = mapIndex.findAll();
			Long result = 0L;
			while(keyIterator.hasNext()) {
				keyIterator.next(); 
				result++;
			}
			/*
			int partitions = og.getMap(FLIGHT_MAP_NAME).getPartitionManager().getNumOfPartitions();
			Long result = 0L;
			ObjectQuery query = og.getSession().createObjectQuery("SELECT COUNT ( o ) FROM " + FLIGHT_MAP_NAME + " o ");
			for(int i = 0; i<partitions;i++){
				query.setPartition(i);
				result += (Long) query.getSingleResult();
			}
			*/
			return result;
		} catch (UndefinedMapException e) {
			e.printStackTrace();
		} catch (TransactionCallbackException e) {
			e.printStackTrace();
		} catch (ObjectGridException e) {
			e.printStackTrace();
		}
		return -1L;
	}
	
	@Override
	public Long countAirports() {
		try {
			Session session = og.getSession();
			ObjectMap objectMap = session.getMap(AIRPORT_CODE_MAPPING_MAP_NAME);			
			MapIndex mapIndex = (MapIndex)objectMap.getIndex(MapIndexPlugin.SYSTEM_KEY_INDEX_NAME);			
			Iterator<?> keyIterator = mapIndex.findAll();
			Long result = 0L;
			while(keyIterator.hasNext()) {
				keyIterator.next(); 
				result++;
			}
			return result;
		} catch (UndefinedMapException e) {
			e.printStackTrace();
		} catch (TransactionCallbackException e) {
			e.printStackTrace();
		} catch (ObjectGridException e) {
			e.printStackTrace();
		}
		return -1L;
	}
	
	@Override
	public Long countFlightSegments() {
		try {
			Session session = og.getSession();
			ObjectMap objectMap = session.getMap(FLIGHT_SEGMENT_MAP_NAME);			
			MapIndex mapIndex = (MapIndex)objectMap.getIndex(MapIndexPlugin.SYSTEM_KEY_INDEX_NAME);			
			Iterator<?> keyIterator = mapIndex.findAll();
			Long result = 0L;
			while(keyIterator.hasNext()) {
				keyIterator.next(); 
				result++;
			}
			/*
			int partitions = og.getMap(FLIGHT_SEGMENT_MAP_NAME).getPartitionManager().getNumOfPartitions();
			Long result = 0L;
			ObjectQuery query = og.getSession().createObjectQuery("SELECT COUNT ( o ) FROM " + FLIGHT_SEGMENT_MAP_NAME + " o ");
			for(int i = 0; i<partitions;i++){
				query.setPartition(i);
				result += (Long) query.getSingleResult();
			}
			*/			
			return result;

		} catch (UndefinedMapException e) {
			e.printStackTrace();
		} catch (TransactionCallbackException e) {
			e.printStackTrace();
		} catch (ObjectGridException e) {
			e.printStackTrace();
		}
		return -1L;
	}
	
	/*
	public Flight getFlightByFlightKey(FlightPK key) {
		try {
			Flight flight;
			flight = flightPKtoFlightCache.get(key);
			if (flight == null) {
				//Session session = sessionManager.getObjectGridSession();
				Session session = og.getSession();
				ObjectMap flightMap = session.getMap(FLIGHT_MAP_NAME);
				@SuppressWarnings("unchecked")
				HashSet<Flight> flightsBySegment = (HashSet<Flight>)flightMap.get(key.getFlightSegmentId());
				for (Flight f : flightsBySegment) {
					if (f.getPkey().getId().equals(key.getId())) {
						flightPKtoFlightCache.putIfAbsent(key, f);
						flight = f;
						break;
					}
				}
			}
			return flight;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	*/
	@Override
	protected Flight getFlight(String flightId, String flightSegmentId) {
		try {
			if(logger.isLoggable(Level.FINER))
				logger.finer("in WXS getFlight.  search for flightId = '" + flightId + "' and flightSegmentId = '"+flightSegmentId+"'");
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap flightMap = session.getMap(FLIGHT_MAP_NAME);
			@SuppressWarnings("unchecked")
			HashSet<FlightImpl> flightsBySegment = (HashSet<FlightImpl>)flightMap.get(flightSegmentId);
			for (FlightImpl flight : flightsBySegment) {
				if (flight.getFlightId().equals(flightId)) {
					return flight;
				}
			}
			logger.warning("No matching flights found for flightId =" + flightId + " and flightSegment " + flightSegmentId);
			return null;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	protected  FlightSegment getFlightSegment(String fromAirport, String toAirport) {
		try {
		Session session = null;
//		boolean startedTran = false;
		//session = sessionManager.getObjectGridSession();
		session = og.getSession();
		FlightSegment segment = null;
/*		if (!session.isTransactionActive()) {
			startedTran = true;
			session.begin();
		}
		*/
		ObjectMap flightSegmentMap = session.getMap(FLIGHT_SEGMENT_MAP_NAME);
		@SuppressWarnings("unchecked")
		HashSet<FlightSegment> segmentsByOrigPort = (HashSet<FlightSegment>)flightSegmentMap.get(fromAirport);
		if (segmentsByOrigPort!=null) {
			for (FlightSegment fs : segmentsByOrigPort) {
				if (fs.getDestPort().equals(toAirport)) {
					segment = fs;
					return segment;
				}
			}
		}
		if (segment == null) {
			segment = new FlightSegmentImpl(); // put a sentinel value of a non-populated flightsegment
		}
//		if (startedTran)
//			session.commit();
		
		return segment;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	
	@Override
	protected  List<Flight> getFlightBySegment(FlightSegment segment, Date deptDate){
		try {
		List<Flight> flights = new ArrayList<Flight>();
		Session session = null;
		boolean startedTran = false;
		if (session == null) {
			//session = sessionManager.getObjectGridSession();
			session = og.getSession();
			if (!session.isTransactionActive()) {
				startedTran = true;
				session.begin();
			}
		}				
		
		ObjectMap flightMap = session.getMap(FLIGHT_MAP_NAME);
		@SuppressWarnings("unchecked")
		HashSet<Flight> flightsBySegment = (HashSet<Flight>)flightMap.get(segment.getFlightName());
		if(deptDate != null){
			for (Flight f : flightsBySegment) {
				if (areDatesSameWithNoTime(f.getScheduledDepartureTime(), deptDate)) {
					f.setFlightSegment(segment);
					flights.add(f);
				}
			}
		} else {
			for (Flight f : flightsBySegment) {
				f.setFlightSegment(segment);
				flights.add(f);
			}
		}
		if (startedTran)
			session.commit();
		
		return flights;
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	
	private static boolean areDatesSameWithNoTime(Date d1, Date d2) {
		return getDateWithNoTime(d1).equals(getDateWithNoTime(d2));
	}
	
	private static Date getDateWithNoTime(Date date) {
		Calendar c = Calendar.getInstance();
		c.setTime(date);
		c.set(Calendar.HOUR_OF_DAY, 0);
		c.set(Calendar.MINUTE, 0);
		c.set(Calendar.SECOND, 0);
		c.set(Calendar.MILLISECOND, 0);
		return c.getTime();
	}
	
	
	@Override
	public void storeAirportMapping(AirportCodeMapping mapping) {
		try{
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap airportCodeMappingMap = session.getMap(AIRPORT_CODE_MAPPING_MAP_NAME);
			airportCodeMappingMap.upsert(mapping.getAirportCode(), mapping);
		}catch (Exception e)
		{
			throw new RuntimeException(e);
		}
	}

	@Override 
	public AirportCodeMapping createAirportCodeMapping(String airportCode, String airportName){
		AirportCodeMapping acm = new AirportCodeMappingImpl(airportCode, airportName);
		return acm;
	}
	
	@Override
	public Flight createNewFlight(String flightSegmentId,
			Date scheduledDepartureTime, Date scheduledArrivalTime,
			BigDecimal firstClassBaseCost, BigDecimal economyClassBaseCost,
			int numFirstClassSeats, int numEconomyClassSeats,
			String airplaneTypeId) {
		try{
			String id = keyGenerator.generate().toString();
			Flight flight = new FlightImpl(id, flightSegmentId,
				scheduledDepartureTime, scheduledArrivalTime,
				firstClassBaseCost, economyClassBaseCost,
				numFirstClassSeats, numEconomyClassSeats,
				airplaneTypeId);
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap flightMap = session.getMap(FLIGHT_MAP_NAME);
			//flightMap.insert(flight.getPkey(), flight);
			//return flight;
			@SuppressWarnings("unchecked")
			HashSet<Flight> flightsBySegment = (HashSet<Flight>)flightMap.get(flightSegmentId);
			if (flightsBySegment == null) {
				flightsBySegment = new HashSet<Flight>();
			}
			if (!flightsBySegment.contains(flight)) {
				flightsBySegment.add(flight);
				flightMap.upsert(flightSegmentId, flightsBySegment);
			}
			return flight;
		}catch (Exception e)
		{
			throw new RuntimeException(e);
		}
	}

	@Override
	public void storeFlightSegment(FlightSegment flightSeg) {
		try {
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap flightSegmentMap = session.getMap(FLIGHT_SEGMENT_MAP_NAME);
			// TODO: Consider moving this to a ArrayList - List ??
			@SuppressWarnings("unchecked")
			HashSet<FlightSegment> segmentsByOrigPort = (HashSet<FlightSegment>)flightSegmentMap.get(flightSeg.getOriginPort());
			if (segmentsByOrigPort == null) {
				segmentsByOrigPort = new HashSet<FlightSegment>();
			}
			if (!segmentsByOrigPort.contains(flightSeg)) {
				segmentsByOrigPort.add(flightSeg);
				flightSegmentMap.upsert(flightSeg.getOriginPort(), segmentsByOrigPort);
			}
		
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	
	@Override 
	public void storeFlightSegment(String flightName, String origPort, String destPort, int miles) {
		FlightSegment flightSeg = new FlightSegmentImpl(flightName, origPort, destPort, miles);
		storeFlightSegment(flightSeg);
	}



}


// Node: getFlightByFlightKey
// Node: isTransactionActive
// Node: begin
// Node: commit
// Node: insert
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
package com.acmeair.wxs.service;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.Iterator;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.annotation.PostConstruct;
import javax.inject.Inject;

import com.acmeair.entities.Booking;
import com.acmeair.entities.Customer;
import com.acmeair.entities.Flight;
import com.acmeair.service.BookingService;
import com.acmeair.service.CustomerService;
import com.acmeair.service.DataService;
import com.acmeair.service.FlightService;
import com.acmeair.service.KeyGenerator;
import com.acmeair.service.ServiceLocator;
import com.acmeair.wxs.WXSConstants;
import com.acmeair.wxs.entities.BookingImpl;
import com.acmeair.wxs.entities.BookingPKImpl;
import com.acmeair.wxs.entities.FlightPKImpl;
import com.acmeair.wxs.utils.WXSSessionManager;
import com.ibm.websphere.objectgrid.ObjectGrid;
import com.ibm.websphere.objectgrid.ObjectGridException;
import com.ibm.websphere.objectgrid.ObjectMap;
import com.ibm.websphere.objectgrid.Session;
import com.ibm.websphere.objectgrid.UndefinedMapException;
import com.ibm.websphere.objectgrid.plugins.TransactionCallbackException;
import com.ibm.websphere.objectgrid.plugins.index.MapIndex;


@DataService(name=WXSConstants.KEY,description=WXSConstants.KEY_DESCRIPTION)
public class BookingServiceImpl implements BookingService, WXSConstants  {
	
	private final static Logger logger = Logger.getLogger(BookingService.class.getName()); 
	
	private static String BOOKING_MAP_NAME="Booking";
	private static String BASE_BOOKING_MAP_NAME="Booking";

	private ObjectGrid og;
	
	@Inject
	private KeyGenerator keyGenerator;
	
	private FlightService flightService = ServiceLocator.instance().getService(FlightService.class);
	private CustomerService customerService = ServiceLocator.instance().getService(CustomerService.class);
	
	
	@PostConstruct
	private void initialization()  {
		try {
			og = WXSSessionManager.getSessionManager().getObjectGrid();
			BOOKING_MAP_NAME = BASE_BOOKING_MAP_NAME + WXSSessionManager.getSessionManager().getMapSuffix();
		} catch (ObjectGridException e) {
			logger.severe("Unable to retreive the ObjectGrid reference " + e.getMessage());
		}
	}
	
		
	public BookingPKImpl bookFlight(String customerId, FlightPKImpl flightId) {
		try{
			// We still delegate to the flight and customer service for the map access than getting the map instance directly
			Flight f = flightService.getFlightByFlightId(flightId.getId(), flightId.getFlightSegmentId());
			Customer c = customerService.getCustomerByUsername(customerId);
			
			BookingImpl newBooking = new BookingImpl(keyGenerator.generate().toString(), new Date(), c, f);
			BookingPKImpl key = newBooking.getPkey();
			
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap bookingMap = session.getMap(BOOKING_MAP_NAME);
			@SuppressWarnings("unchecked")
			HashSet<Booking> bookingsByUser = (HashSet<Booking>)bookingMap.get(customerId);
			if (bookingsByUser == null) {
				bookingsByUser = new HashSet<Booking>();
			}
			if (bookingsByUser.contains(newBooking)) {
				throw new Exception("trying to book a duplicate booking");
			}
			bookingsByUser.add(newBooking);
			bookingMap.upsert(customerId, bookingsByUser);
			return key;
		}catch (Exception e)
		{
			throw new RuntimeException(e);
		}
	}

	@Override
	public String bookFlight(String customerId, String flightSegmentId, String id) {
		if(logger.isLoggable(Level.FINER))
			logger.finer("WXS booking service,  bookFlight with customerId = '"+ customerId+"', flightSegmentId = '"+ flightSegmentId + "',  and id = '" + id + "'");
		return bookFlight(customerId, new FlightPKImpl(flightSegmentId, id)).getId();
	}
	
	@Override
	public Booking getBooking(String user, String id) {
		
		try{
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap bookingMap = session.getMap(BOOKING_MAP_NAME);
			
//			return (Booking)bookingMap.get(new BookingPK(user, id));
			@SuppressWarnings("unchecked")
			HashSet<BookingImpl> bookingsByUser = (HashSet<BookingImpl>)bookingMap.get(user);
			if (bookingsByUser == null) {
				return null;
			}
			for (BookingImpl b : bookingsByUser) {
				if (b.getPkey().getId().equals(id)) {
					return b;
				}
			}
			return null;

		}catch (Exception e)
		{
			throw new RuntimeException(e);
		}
			
	}

	@Override
	public void cancelBooking(String user, String id) {
		try{
			Session session = og.getSession();
			//Session session = sessionManager.getObjectGridSession();
			ObjectMap bookingMap = session.getMap(BOOKING_MAP_NAME);
			@SuppressWarnings("unchecked")
			HashSet<BookingImpl> bookingsByUser = (HashSet<BookingImpl>)bookingMap.get(user);
			if (bookingsByUser == null) {
				return;
			}
			boolean found = false;
			HashSet<Booking> newBookings = new HashSet<Booking>();
			for (BookingImpl b : bookingsByUser) {
				if (b.getPkey().getId().equals(id)) {
					found = true;
				}
				else {
					newBookings.add(b);
				}
			}
			
			if (found) {
				bookingMap.upsert(user, newBookings);
			}
		}catch (Exception e)
		{
			throw new RuntimeException(e);
		}
	}		
	
	@Override
	public List<Booking> getBookingsByUser(String user) {
		try{
			Session session = og.getSession();
			//Session session = sessionManager.getObjectGridSession();
	
			boolean startedTran = false;
			if (!session.isTransactionActive()) {
				startedTran = true;
				session.begin();
			}
			
			ObjectMap bookingMap = session.getMap(BOOKING_MAP_NAME);
			@SuppressWarnings("unchecked")
			HashSet<Booking> bookingsByUser = (HashSet<Booking>)bookingMap.get(user);
			if (bookingsByUser == null) {
				bookingsByUser = new HashSet<Booking>();
			}
			
			ArrayList<Booking> bookingsList = new ArrayList<Booking>();
			for (Booking b : bookingsByUser) {
				bookingsList.add(b);
			}
		
			if (startedTran)
				session.commit();
			
			return bookingsList;
		}catch (Exception e)
		{
			throw new RuntimeException(e);
		}
		
	}
	
	@Override
	public Long count () {
		try {
			Session session = og.getSession();
			ObjectMap objectMap = session.getMap(BOOKING_MAP_NAME);			
			MapIndex mapIndex = (MapIndex)objectMap.getIndex("com.ibm.ws.objectgrid.builtin.map.KeyIndex");			
			Iterator<?> keyIterator = mapIndex.findAll();
			Long result = 0L;
			while(keyIterator.hasNext()) {
				keyIterator.next(); 
				result++;
			}
			/*
			int partitions = og.getMap(BOOKING_MAP_NAME).getPartitionManager().getNumOfPartitions();
			Long result = 0L;
			ObjectQuery query = og.getSession().createObjectQuery("SELECT COUNT ( o ) FROM " + BOOKING_MAP_NAME + " o ");
			for(int i = 0; i<partitions;i++){
				query.setPartition(i);
				result += (Long) query.getSingleResult();
			}
			*/			
			return result;
		} catch (UndefinedMapException e) {
			e.printStackTrace();
		} catch (TransactionCallbackException e) {
			e.printStackTrace();
		} catch (ObjectGridException e) {
			e.printStackTrace();
		}	
		return -1L;
	}
}


// Node: Exception
// Node: BookingPK
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
package com.acmeair.wxs.service;

import java.util.Date;
import java.util.Iterator;
import java.util.logging.Logger;

import javax.annotation.PostConstruct;
import javax.enterprise.inject.Default;
import javax.inject.Inject;

import com.acmeair.entities.Customer;
import com.acmeair.entities.Customer.MemberShipStatus;
import com.acmeair.entities.Customer.PhoneType;
import com.acmeair.entities.CustomerAddress;
import com.acmeair.entities.CustomerSession;
import com.acmeair.service.BookingService;
import com.acmeair.service.CustomerService;
import com.acmeair.service.DataService;
import com.acmeair.service.KeyGenerator;
import com.acmeair.wxs.WXSConstants;
import com.acmeair.wxs.entities.CustomerAddressImpl;
import com.acmeair.wxs.entities.CustomerImpl;
import com.acmeair.wxs.entities.CustomerSessionImpl;
import com.acmeair.wxs.utils.WXSSessionManager;
import com.ibm.websphere.objectgrid.ObjectGrid;
import com.ibm.websphere.objectgrid.ObjectGridException;
import com.ibm.websphere.objectgrid.ObjectMap;
import com.ibm.websphere.objectgrid.Session;
import com.ibm.websphere.objectgrid.UndefinedMapException;
import com.ibm.websphere.objectgrid.plugins.TransactionCallbackException;
import com.ibm.websphere.objectgrid.plugins.index.MapIndex;
import com.ibm.websphere.objectgrid.plugins.index.MapIndexPlugin;


@Default
@DataService(name=WXSConstants.KEY,description=WXSConstants.KEY_DESCRIPTION)
public class CustomerServiceImpl extends CustomerService implements WXSConstants{
	
	private static String BASE_CUSTOMER_MAP_NAME="Customer";
	private static String BASE_CUSTOMER_SESSION_MAP_NAME="CustomerSession";
	private static String CUSTOMER_MAP_NAME="Customer";
	private static String CUSTOMER_SESSION_MAP_NAME="CustomerSession";
	
		
	private final static Logger logger = Logger.getLogger(BookingService.class.getName()); 

	private ObjectGrid og;
	
	@Inject
	KeyGenerator keyGenerator;

	
	@PostConstruct
	private void initialization()  {
		try {
			og = WXSSessionManager.getSessionManager().getObjectGrid();
			CUSTOMER_MAP_NAME = BASE_CUSTOMER_MAP_NAME + WXSSessionManager.getSessionManager().getMapSuffix();
			CUSTOMER_SESSION_MAP_NAME = BASE_CUSTOMER_SESSION_MAP_NAME + WXSSessionManager.getSessionManager().getMapSuffix();
		} catch (ObjectGridException e) {
			logger.severe("Unable to retreive the ObjectGrid reference " + e.getMessage());
		}
	}
	
	@Override
	public Long count () {
		try {
			Session session = og.getSession();
			ObjectMap objectMap = session.getMap(CUSTOMER_MAP_NAME);			
			MapIndex mapIndex = (MapIndex)objectMap.getIndex(MapIndexPlugin.SYSTEM_KEY_INDEX_NAME);			
			Iterator<?> keyIterator = mapIndex.findAll();
			Long result = 0L;
			while(keyIterator.hasNext()) {
				keyIterator.next(); 
				result++;
			}
			/*
			int partitions = og.getMap(CUSTOMER_MAP_NAME).getPartitionManager().getNumOfPartitions();			
			ObjectQuery query = og.getSession().createObjectQuery("SELECT COUNT ( o ) FROM " + CUSTOMER_MAP_NAME + " o ");
			for(int i = 0; i<partitions;i++){
				query.setPartition(i);
				result += (Long) query.getSingleResult();
			}
			*/			
			return result;
		} catch (UndefinedMapException e) {
			e.printStackTrace();
		} catch (TransactionCallbackException e) {
			e.printStackTrace();
		} catch (ObjectGridException e) {
			e.printStackTrace();
		}		
		return -1L;
	}
	
	@Override
	public Long countSessions () {
		try {
			Session session = og.getSession();
			ObjectMap objectMap = session.getMap(CUSTOMER_SESSION_MAP_NAME);			
			MapIndex mapIndex = (MapIndex)objectMap.getIndex(MapIndexPlugin.SYSTEM_KEY_INDEX_NAME);			
			Iterator<?> keyIterator = mapIndex.findAll();
			Long result = 0L;
			while(keyIterator.hasNext()) {
				keyIterator.next(); 
				result++;
			}
			/*
			int partitions = og.getMap(CUSTOMER_SESSION_MAP_NAME).getPartitionManager().getNumOfPartitions();
			Long result = 0L;
			ObjectQuery query = og.getSession().createObjectQuery("SELECT COUNT ( o ) FROM " + CUSTOMER_SESSION_MAP_NAME + " o ");
			for(int i = 0; i<partitions;i++){
				query.setPartition(i);
				result += (Long) query.getSingleResult();
			}
			*/			
			return result;
		} catch (UndefinedMapException e) {
			e.printStackTrace();
		} catch (TransactionCallbackException e) {
			e.printStackTrace();
		} catch (ObjectGridException e) {
			e.printStackTrace();
		}	
		return -1L;
	}
	
	@Override
	public Customer createCustomer(String username, String password,
			MemberShipStatus status, int total_miles, int miles_ytd,
			String phoneNumber, PhoneType phoneNumberType,
			CustomerAddress address) {
		try{
			Customer customer = new CustomerImpl(username, password, status, total_miles, miles_ytd, address, phoneNumber, phoneNumberType);
			// Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap customerMap = session.getMap(CUSTOMER_MAP_NAME);
			customerMap.insert(customer.getUsername(), customer);
			return customer;
		}catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override 
	public CustomerAddress createAddress (String streetAddress1, String streetAddress2,
			String city, String stateProvince, String country, String postalCode){
		CustomerAddress address = new CustomerAddressImpl(streetAddress1, streetAddress2,
				 city, stateProvince,  country,  postalCode);
		return address;
	}
	
	@Override
	public Customer updateCustomer(Customer customer) {
		try{
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap customerMap = session.getMap(CUSTOMER_MAP_NAME);
			customerMap.update(customer.getUsername(), customer);
			return customer;
		}catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	protected Customer getCustomer(String username) {
		try{
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap customerMap = session.getMap(CUSTOMER_MAP_NAME);
			
			Customer c = (Customer) customerMap.get(username);
			return c;
		}catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	

	@Override
	protected CustomerSession getSession(String sessionid){
		try {
			Session session = og.getSession();
			ObjectMap customerSessionMap = session.getMap(CUSTOMER_SESSION_MAP_NAME);

			return (CustomerSession)customerSessionMap.get(sessionid);
		}catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	
	@Override
	protected void removeSession(CustomerSession session){
		try {
			Session ogSession = og.getSession();
			ObjectMap customerSessionMap = ogSession.getMap(CUSTOMER_SESSION_MAP_NAME);

			customerSessionMap.remove(session.getId());
		}catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
	
	@Override
	protected CustomerSession createSession(String sessionId, String customerId, Date creation, Date expiration) {
		try{
			CustomerSession cSession = new CustomerSessionImpl(sessionId, customerId, creation, expiration);
			// Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap customerSessionMap = session.getMap(CUSTOMER_SESSION_MAP_NAME);
			customerSessionMap.insert(cSession.getId(), cSession);
			return cSession;
		}catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	@Override
	public void invalidateSession(String sessionid) {
		try{
			//Session session = sessionManager.getObjectGridSession();
			Session session = og.getSession();
			ObjectMap customerSessionMap = session.getMap(CUSTOMER_SESSION_MAP_NAME);
			customerSessionMap.remove(sessionid);
		}catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
}


// Node: update
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

import com.acmeair.entities.BookingPK;

import com.ibm.websphere.objectgrid.plugins.PartitionableKey;

public class BookingPKImpl implements BookingPK, Serializable, PartitionableKey {
	
	private static final long serialVersionUID = 1L;
	private String id;
	private String customerId;
	
	public BookingPKImpl() {
		super();
	}

	public BookingPKImpl(String customerId,String id) {
		super();
		this.id = id;
		this.customerId = customerId;
	}

	public String getId() {
		return id;
	}

	public void setId(String id) {
		this.id = id;
	}

	public String getCustomerId() {
		return customerId;
	}

	public void setCustomerId(String customerId) {
		this.customerId = customerId;
	}

	@Override
	public Object ibmGetPartition() {
		return this.customerId;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result
				+ ((customerId == null) ? 0 : customerId.hashCode());
		result = prime * result + ((id == null) ? 0 : id.hashCode());
		return result;
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		BookingPKImpl other = (BookingPKImpl) obj;
		if (customerId == null) {
			if (other.customerId != null)
				return false;
		} else if (!customerId.equals(other.customerId))
			return false;
		if (id == null) {
			if (other.id != null)
				return false;
		} else if (!id.equals(other.id))
			return false;
		return true;
	}

	@Override
	public String toString() {
		return "BookingPK [customerId=" + customerId + ",id=" + id + "]";
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
import com.acmeair.entities.FlightPK;
import com.ibm.websphere.objectgrid.plugins.PartitionableKey;


public class FlightPKImpl implements FlightPK, Serializable, PartitionableKey {
	
	private static final long serialVersionUID = 1L;
	
	private String id;
	private String flightSegmentId;
	
	public FlightPKImpl() {
		super();
	}

	public FlightPKImpl(String flightSegmentId,String id) {
		super();
		this.id = id;
		this.flightSegmentId = flightSegmentId;
	}
	
	public String getId() {
		return id;
	}
	public void setId(String id) {
		this.id = id;
	}
	public String getFlightSegmentId() {
		return flightSegmentId;
	}
	public void setFlightSegmentId(String flightSegmentId) {
		this.flightSegmentId = flightSegmentId;
	}
	
	@Override
	public Object ibmGetPartition() {
		return this.flightSegmentId;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result
				+ ((flightSegmentId == null) ? 0 : flightSegmentId.hashCode());
		result = prime * result + ((id == null) ? 0 : id.hashCode());
		return result;
	}
	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		FlightPKImpl other = (FlightPKImpl) obj;
		if (flightSegmentId == null) {
			if (other.flightSegmentId != null)
				return false;
		} else if (!flightSegmentId.equals(other.flightSegmentId))
			return false;
		if (id == null) {
			if (other.id != null)
				return false;
		} else if (!id.equals(other.id))
			return false;
		return true;
	}
	@Override
	public String toString() {
		return "FlightPK [flightSegmentId=" + flightSegmentId +",id=" + id+ "]";
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
import java.util.*;

import com.acmeair.entities.Booking;
import com.acmeair.entities.Customer;
import com.acmeair.entities.Flight;


public class BookingImpl implements Booking, Serializable{
	
	private static final long serialVersionUID = 1L;

	private BookingPKImpl pkey;
	private FlightPKImpl flightKey;
	private Date dateOfBooking;
	private Customer customer;
	private Flight flight;
	
	public BookingImpl() {
	}
	
	public BookingImpl(String id, Date dateOfFlight, Customer customer, Flight flight) {
		this(id, dateOfFlight, customer, (FlightImpl)flight);
	}
	
	public BookingImpl(String id, Date dateOfFlight, Customer customer, FlightImpl flight) {
		this.pkey = new BookingPKImpl(customer.getUsername(),id);
		
		this.flightKey = flight.getPkey();
		this.dateOfBooking = dateOfFlight;
		this.customer = customer;
		this.flight = flight;
	}
	
	public BookingPKImpl getPkey() {
		return pkey;
	}

	// adding the method for index calculation
	public String getCustomerId() {
		return pkey.getCustomerId();
	}
	
	public void setPkey(BookingPKImpl pkey) {
		this.pkey = pkey;
	}

	public FlightPKImpl getFlightKey() {
		return flightKey;
	}

	public void setFlightKey(FlightPKImpl flightKey) {
		this.flightKey = flightKey;
	}

	
	public void setFlight(Flight flight) {
		this.flight = flight;
	}

	public Date getDateOfBooking() {
		return dateOfBooking;
	}
	
	public void setDateOfBooking(Date dateOfBooking) {
		this.dateOfBooking = dateOfBooking;
	}

	public Customer getCustomer() {
		return customer;
	}
	
	public void setCustomer(Customer customer) {
		this.customer = customer;
	}

	public Flight getFlight() {
		return flight;
	}


	@Override
	public String toString() {
		return "Booking [key=" + pkey + ", flightKey=" + flightKey
				+ ", dateOfBooking=" + dateOfBooking + ", customer=" + customer
				+ ", flight=" + flight + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		BookingImpl other = (BookingImpl) obj;
		if (customer == null) {
			if (other.customer != null)
				return false;
		} else if (!customer.equals(other.customer))
			return false;
		if (dateOfBooking == null) {
			if (other.dateOfBooking != null)
				return false;
		} else if (!dateOfBooking.equals(other.dateOfBooking))
			return false;
		if (flight == null) {
			if (other.flight != null)
				return false;
		} else if (!flight.equals(other.flight))
			return false;
		if (flightKey == null) {
			if (other.flightKey != null)
				return false;
		} else if (!flightKey.equals(other.flightKey))
			return false;
		if (pkey == null) {
			if (other.pkey != null)
				return false;
		} else if (!pkey.equals(other.pkey))
			return false;
		return true;
	}

	@Override
	public String getBookingId() {
		return pkey.getId();
	}

	@Override
	public String getFlightId() {
		return flight.getFlightId();		
	}

}


// Node: repos/cloned_ms_repos/acmeair/acmeair-services-wxs/src/main/java/com/acmeair/wxs/entities/BookingImpl.java:BookingImpl.<init>
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
import java.util.Date;

import com.acmeair.entities.CustomerSession;

public class CustomerSessionImpl implements CustomerSession, Serializable {


	private static final long serialVersionUID = 1L;

	private String _id;
	private String customerid;
	private Date lastAccessedTime;
	private Date timeoutTime;
	
	public CustomerSessionImpl() {
	}

	public CustomerSessionImpl(String id, String customerid, Date lastAccessedTime,	Date timeoutTime) {
		this._id= id;
		this.customerid = customerid;
		this.lastAccessedTime = lastAccessedTime;
		this.timeoutTime = timeoutTime;
	}
	

	public String getId() {
		return _id;
	}

	public void setId(String id) {
		this._id = id;
	}

	public String getCustomerid() {
		return customerid;
	}

	public void setCustomerid(String customerid) {
		this.customerid = customerid;
	}

	public Date getLastAccessedTime() {
		return lastAccessedTime;
	}

	public void setLastAccessedTime(Date lastAccessedTime) {
		this.lastAccessedTime = lastAccessedTime;
	}

	public Date getTimeoutTime() {
		return timeoutTime;
	}

	public void setTimeoutTime(Date timeoutTime) {
		this.timeoutTime = timeoutTime;
	}

	@Override
	public String toString() {
		return "CustomerSession [id=" + _id + ", customerid=" + customerid
				+ ", lastAccessedTime=" + lastAccessedTime + ", timeoutTime="
				+ timeoutTime + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		CustomerSessionImpl other = (CustomerSessionImpl) obj;
		if (customerid == null) {
			if (other.customerid != null)
				return false;
		} else if (!customerid.equals(other.customerid))
			return false;
		if (_id == null) {
			if (other._id != null)
				return false;
		} else if (!_id.equals(other._id))
			return false;
		if (lastAccessedTime == null) {
			if (other.lastAccessedTime != null)
				return false;
		} else if (!lastAccessedTime.equals(other.lastAccessedTime))
			return false;
		if (timeoutTime == null) {
			if (other.timeoutTime != null)
				return false;
		} else if (!timeoutTime.equals(other.timeoutTime))
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
import java.math.BigDecimal;
import java.util.Date;

import com.acmeair.entities.Flight;
import com.acmeair.entities.FlightSegment;


public class FlightImpl implements Flight, Serializable{

	private static final long serialVersionUID = 1L;
				
	private FlightPKImpl pkey;
	private Date scheduledDepartureTime;
	private Date scheduledArrivalTime;
	private BigDecimal firstClassBaseCost;
	private BigDecimal economyClassBaseCost;
	private int numFirstClassSeats;
	private int numEconomyClassSeats;
	private String airplaneTypeId;
	
	private FlightSegment flightSegment;
	
	public FlightImpl() {
	}
	
	public FlightImpl(String id, String flightSegmentId,
			Date scheduledDepartureTime, Date scheduledArrivalTime,
			BigDecimal firstClassBaseCost, BigDecimal economyClassBaseCost,
			int numFirstClassSeats, int numEconomyClassSeats,
			String airplaneTypeId) {
		this.pkey = new FlightPKImpl(flightSegmentId,id);
		
		this.scheduledDepartureTime = scheduledDepartureTime;
		this.scheduledArrivalTime = scheduledArrivalTime;
		this.firstClassBaseCost = firstClassBaseCost;
		this.economyClassBaseCost = economyClassBaseCost;
		this.numFirstClassSeats = numFirstClassSeats;
		this.numEconomyClassSeats = numEconomyClassSeats;
		this.airplaneTypeId = airplaneTypeId;
	}

	public FlightPKImpl getPkey() {
		return pkey;
	}

	public void setPkey(FlightPKImpl pkey) {
		this.pkey = pkey;		
	}
	

	@Override
	public String getFlightId() {
		return pkey.getId();
	}

	@Override
	public void setFlightId(String id) {
		pkey.setId(id);		
	}

	
	// The method is needed for index calculation
	public String getFlightSegmentId()
	{
		return pkey.getFlightSegmentId();
	}
	
	public Date getScheduledDepartureTime() {
		return scheduledDepartureTime;
	}


	public void setScheduledDepartureTime(Date scheduledDepartureTime) {
		this.scheduledDepartureTime = scheduledDepartureTime;
	}


	public Date getScheduledArrivalTime() {
		return scheduledArrivalTime;
	}


	public void setScheduledArrivalTime(Date scheduledArrivalTime) {
		this.scheduledArrivalTime = scheduledArrivalTime;
	}


	public BigDecimal getFirstClassBaseCost() {
		return firstClassBaseCost;
	}


	public void setFirstClassBaseCost(BigDecimal firstClassBaseCost) {
		this.firstClassBaseCost = firstClassBaseCost;
	}


	public BigDecimal getEconomyClassBaseCost() {
		return economyClassBaseCost;
	}


	public void setEconomyClassBaseCost(BigDecimal economyClassBaseCost) {
		this.economyClassBaseCost = economyClassBaseCost;
	}


	public int getNumFirstClassSeats() {
		return numFirstClassSeats;
	}


	public void setNumFirstClassSeats(int numFirstClassSeats) {
		this.numFirstClassSeats = numFirstClassSeats;
	}


	public int getNumEconomyClassSeats() {
		return numEconomyClassSeats;
	}


	public void setNumEconomyClassSeats(int numEconomyClassSeats) {
		this.numEconomyClassSeats = numEconomyClassSeats;
	}


	public String getAirplaneTypeId() {
		return airplaneTypeId;
	}


	public void setAirplaneTypeId(String airplaneTypeId) {
		this.airplaneTypeId = airplaneTypeId;
	}


	public FlightSegment getFlightSegment() {
		return flightSegment;
	}

	public void setFlightSegment(FlightSegment flightSegment) {
		this.flightSegment = flightSegment;
	}

	@Override
	public String toString() {
		return "Flight key="+pkey
				+ ", scheduledDepartureTime=" + scheduledDepartureTime
				+ ", scheduledArrivalTime=" + scheduledArrivalTime
				+ ", firstClassBaseCost=" + firstClassBaseCost
				+ ", economyClassBaseCost=" + economyClassBaseCost
				+ ", numFirstClassSeats=" + numFirstClassSeats
				+ ", numEconomyClassSeats=" + numEconomyClassSeats
				+ ", airplaneTypeId=" + airplaneTypeId + "]";
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		FlightImpl other = (FlightImpl) obj;
		if (airplaneTypeId == null) {
			if (other.airplaneTypeId != null)
				return false;
		} else if (!airplaneTypeId.equals(other.airplaneTypeId))
			return false;
		if (economyClassBaseCost == null) {
			if (other.economyClassBaseCost != null)
				return false;
		} else if (!economyClassBaseCost.equals(other.economyClassBaseCost))
			return false;
		if (firstClassBaseCost == null) {
			if (other.firstClassBaseCost != null)
				return false;
		} else if (!firstClassBaseCost.equals(other.firstClassBaseCost))
			return false;
		if (flightSegment == null) {
			if (other.flightSegment != null)
				return false;
		} else if (!flightSegment.equals(other.flightSegment))
			return false;
		if (pkey == null) {
			if (other.pkey != null)
				return false;
		} else if (!pkey.equals(other.pkey))
			return false;
		if (numEconomyClassSeats != other.numEconomyClassSeats)
			return false;
		if (numFirstClassSeats != other.numFirstClassSeats)
			return false;
		if (scheduledArrivalTime == null) {
			if (other.scheduledArrivalTime != null)
				return false;
		} else if (!scheduledArrivalTime.equals(other.scheduledArrivalTime))
			return false;
		if (scheduledDepartureTime == null) {
			if (other.scheduledDepartureTime != null)
				return false;
		} else if (!scheduledDepartureTime.equals(other.scheduledDepartureTime))
			return false;
		return true;
	}


	/*
	public void setFlightSegmentId(String segmentId) {
		pkey.setFlightSegmentId(segmentId);
	}
	*/
	
}

