// Cluster 0

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


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/CustomerREST.java:CustomerREST.<init>
// Node: Path
// Node: instance
// Node: getService
// Node: validate
// Node: getAttribute
// Node: Produces
// Node: CookieParam
// Node: PathParam
// Node: status
// Node: build
// Node: ok
// Node: printStackTrace
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

import java.util.*;

import javax.ws.rs.*;
import javax.ws.rs.core.*;
import javax.ws.rs.core.Response.Status;

import com.acmeair.entities.Booking;
import com.acmeair.service.BookingService;
import com.acmeair.service.ServiceLocator;
import com.acmeair.web.dto.BookingInfo;
import com.acmeair.web.dto.BookingReceiptInfo;

@Path("/bookings")
public class BookingsREST {
	
	private BookingService bs = ServiceLocator.instance().getService(BookingService.class);
	
	@POST
	@Consumes({"application/x-www-form-urlencoded"})
	@Path("/bookflights")
	@Produces("application/json")
	public /*BookingInfo*/ Response bookFlights(
			@FormParam("userid") String userid,
			@FormParam("toFlightId") String toFlightId,
			@FormParam("toFlightSegId") String toFlightSegId,
			@FormParam("retFlightId") String retFlightId,
			@FormParam("retFlightSegId") String retFlightSegId,
			@FormParam("oneWayFlight") boolean oneWay) {
		try {
			String bookingIdTo = bs.bookFlight(userid, toFlightSegId, toFlightId);
			String bookingIdReturn = null;
			if (!oneWay) {
				bookingIdReturn = bs.bookFlight(userid, retFlightSegId, retFlightId);
			}
			// YL. BookingInfo will only contains the booking generated keys as customer info is always available from the session
			BookingReceiptInfo bi;
			if (!oneWay)
				bi = new BookingReceiptInfo(bookingIdTo, bookingIdReturn, oneWay);
			else
				bi = new BookingReceiptInfo(bookingIdTo, null, oneWay);
			
			return Response.ok(bi).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.status(Status.INTERNAL_SERVER_ERROR).build();
		}
	}
	
	@GET
	@Path("/bybookingnumber/{userid}/{number}")
	@Produces("application/json")
	public BookingInfo getBookingByNumber(
			@PathParam("number") String number,
			@PathParam("userid") String userid) {
		try {
			Booking b = bs.getBooking(userid, number);
			BookingInfo bi = null;
			if(b != null){
				bi = new BookingInfo(b);
			}
			return bi;
		}
		catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}
	
	@GET
	@Path("/byuser/{user}")
	@Produces("application/json")
	public List<BookingInfo> getBookingsByUser(@PathParam("user") String user) {
		try {
			List<Booking> list =  bs.getBookingsByUser(user);
			List<BookingInfo> newList = new ArrayList<BookingInfo>();
			for(Booking b : list){
				newList.add(new BookingInfo(b));
			}
			return newList;
		}
		catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}
	
	@POST
	@Consumes({"application/x-www-form-urlencoded"})
	@Path("/cancelbooking")
	@Produces("application/json")
	public Response cancelBookingsByNumber(
			@FormParam("number") String number,
			@FormParam("userid") String userid) {
		try {
			bs.cancelBooking(userid, number);
			return Response.ok("booking " + number + " deleted.").build();
					
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.status(Status.INTERNAL_SERVER_ERROR).build();
		}
	}
	

}

// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/BookingsREST.java:BookingsREST.<init>
// Node: Consumes
// Node: bookFlights
// Node: FormParam
// Node: getBookingByNumber
// Node: BookingInfo
// Node: cancelBookingsByNumber
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

import java.io.IOException;

import javax.enterprise.inject.spi.BeanManager;
import javax.inject.Inject;
import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.acmeair.entities.CustomerSession;
import com.acmeair.service.CustomerService;
import com.acmeair.service.ServiceLocator;
import com.acmeair.service.TransactionService;

public class RESTCookieSessionFilter implements Filter {
	
	static final String LOGIN_USER = "acmeair.login_user";
	private static final String LOGIN_PATH = "/rest/api/login";
	private static final String LOGOUT_PATH = "/rest/api/login/logout";
	private static final String LOADDB_PATH = "/rest/api/loaddb";
	
	private CustomerService customerService = ServiceLocator.instance().getService(CustomerService.class);
	private TransactionService transactionService = ServiceLocator.instance().getService(TransactionService.class);; 

	@Inject
	BeanManager beanManager;
	
	@Override
	public void destroy() {
	}

	
	@Override
	public void doFilter(ServletRequest req, ServletResponse resp,	FilterChain chain) throws IOException, ServletException {
		HttpServletRequest request = (HttpServletRequest)req;
		HttpServletResponse response = (HttpServletResponse)resp;
		
		String path = request.getContextPath() + request.getServletPath() + request.getPathInfo();
		// The following code is to ensure that OG is always set on the thread	
		try{			
			if (transactionService!=null)
				transactionService.prepareForTransaction();
		}catch( Exception e)
		{
			e.printStackTrace();
		}
	
		
		if (path.endsWith(LOGIN_PATH) || path.endsWith(LOGOUT_PATH) || path.endsWith(LOADDB_PATH)) {
			// if logging in, logging out, or loading the database, let the request flow
			chain.doFilter(req, resp);
			return;
		}
		
		Cookie cookies[] = request.getCookies();
		Cookie sessionCookie = null;
		if (cookies != null) {
			for (Cookie c : cookies) {
				if (c.getName().equals(LoginREST.SESSIONID_COOKIE_NAME)) {
					sessionCookie = c;
				}
				if (sessionCookie!=null)
					break; 
			}
			String sessionId = "";
			if (sessionCookie!=null) // We need both cookie to work
				sessionId= sessionCookie.getValue().trim();
			// did this check as the logout currently sets the cookie value to "" instead of aging it out
			// see comment in LogingREST.java
			if (sessionId.equals("")) {
				response.sendError(HttpServletResponse.SC_FORBIDDEN);
				return;
			}
			// Need the URLDecoder so that I can get @ not %40
			CustomerSession cs = customerService.validateSession(sessionId);
			if (cs != null) {
				request.setAttribute(LOGIN_USER, cs.getCustomerid());
				chain.doFilter(req, resp);
				return;
			}
			else {
				response.sendError(HttpServletResponse.SC_FORBIDDEN);
				return;
			}
		}
		
		// if we got here, we didn't detect the session cookie, so we need to return 404
		response.sendError(HttpServletResponse.SC_FORBIDDEN);
	}

	@Override
	public void init(FilterConfig config) throws ServletException {
	}
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/RESTCookieSessionFilter.java:RESTCookieSessionFilter.<init>
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

import javax.ws.rs.*;
import javax.ws.rs.core.*;

import com.acmeair.entities.CustomerSession;
import com.acmeair.service.*;


@Path("/login")
public class LoginREST {
	
	public static String SESSIONID_COOKIE_NAME = "sessionid";
	
	private CustomerService customerService = ServiceLocator.instance().getService(CustomerService.class);
	
	
	@POST
	@Consumes({"application/x-www-form-urlencoded"})
	@Produces("text/plain")
	public Response login(@FormParam("login") String login, @FormParam("password") String password) {
		try {
			boolean validCustomer = customerService.validateCustomer(login, password);
			
			if (!validCustomer) {
				return Response.status(Response.Status.FORBIDDEN).build();
			}
			
			CustomerSession session = customerService.createSession(login);
			// TODO:  Need to fix the security issues here - they are pretty gross likely
			NewCookie sessCookie = new NewCookie(SESSIONID_COOKIE_NAME, session.getId());
			// TODO: The mobile client app requires JSON in the response. 
			// To support the mobile client app, choose one of the following designs:
			// - Change this method to return JSON, and change the web app javascript to handle a JSON response.
			//   example:  return Response.ok("{\"status\":\"logged-in\"}").cookie(sessCookie).build();
			// - Or create another method which is identical to this one, except returns JSON response.
			//   Have the web app use the original method, and the mobile client app use the new one.
			return Response.ok("logged in").cookie(sessCookie).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}
	
	@GET
	@Path("/logout")
	@Produces("text/plain")
	public Response logout(@QueryParam("login") String login, @CookieParam("sessionid") String sessionid) {
		try {
			customerService.invalidateSession(sessionid);
			// The following call will trigger query against all partitions, disable for now
//			customerService.invalidateAllUserSessions(login);
			
			// TODO:  Want to do this with setMaxAge to zero, but to do that I need to have the same path/domain as cookie
			// created in login.  Unfortunately, until we have a elastic ip and domain name its hard to do that for "localhost".
			// doing this will set the cookie to the empty string, but the browser will still send the cookie to future requests
			// and the server will need to detect the value is invalid vs actually forcing the browser to time out the cookie and
			// not send it to begin with
			NewCookie sessCookie = new NewCookie(SESSIONID_COOKIE_NAME, "");
			return Response.ok("logged out").cookie(sessCookie).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/LoginREST.java:LoginREST.<init>
// Node: login
// Node: NewCookie
// Node: cookie
// Node: logout
// Node: QueryParam
// Node: invalidateAllUserSessions
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

import java.util.ArrayList;
import java.util.List;
import java.util.Date;

import javax.ws.rs.Consumes;
import javax.ws.rs.FormParam;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import com.acmeair.entities.Flight;
import com.acmeair.service.FlightService;
import com.acmeair.service.ServiceLocator;
import com.acmeair.web.dto.TripFlightOptions;
import com.acmeair.web.dto.TripLegInfo;

@Path("/flights")
public class FlightsREST {
	
	private FlightService flightService = ServiceLocator.instance().getService(FlightService.class);
	
	// TODO:  Consider a pure GET implementation of this service, but maybe not much value due to infrequent similar searches
	@POST
	@Path("/queryflights")
	@Consumes({"application/x-www-form-urlencoded"})
	@Produces("application/json")
	public TripFlightOptions getTripFlights(
			@FormParam("fromAirport") String fromAirport,
			@FormParam("toAirport") String toAirport,
			@FormParam("fromDate") Date fromDate,
			@FormParam("returnDate") Date returnDate,
			@FormParam("oneWay") boolean oneWay
			) {
		TripFlightOptions options = new TripFlightOptions();
		ArrayList<TripLegInfo> legs = new ArrayList<TripLegInfo>();
		
		TripLegInfo toInfo = new TripLegInfo();
		List<Flight> toFlights = flightService.getFlightByAirportsAndDepartureDate(fromAirport, toAirport, fromDate);
		toInfo.setFlightsOptions(toFlights);
		legs.add(toInfo);
		toInfo.setCurrentPage(0);
		toInfo.setHasMoreOptions(false);
		toInfo.setNumPages(1);
		toInfo.setPageSize(TripLegInfo.DEFAULT_PAGE_SIZE);
		
		if (!oneWay) {
			TripLegInfo retInfo = new TripLegInfo();
			List<Flight> retFlights = flightService.getFlightByAirportsAndDepartureDate(toAirport, fromAirport, returnDate);
			retInfo.setFlightsOptions(retFlights);
			legs.add(retInfo);
			retInfo.setCurrentPage(0);
			retInfo.setHasMoreOptions(false);
			retInfo.setNumPages(1);
			retInfo.setPageSize(TripLegInfo.DEFAULT_PAGE_SIZE);
			options.setTripLegs(2);
		}
		else {
			options.setTripLegs(1);
		}
		
		options.setTripFlights(legs);
		
		return options;
	}
	
	
	@POST
	@Path("/browseflights")
	@Consumes({"application/x-www-form-urlencoded"})
	@Produces("application/json")
	public TripFlightOptions browseFlights(
			@FormParam("fromAirport") String fromAirport,
			@FormParam("toAirport") String toAirport,
			@FormParam("oneWay") boolean oneWay
			) {
		TripFlightOptions options = new TripFlightOptions();
		ArrayList<TripLegInfo> legs = new ArrayList<TripLegInfo>();
		
		TripLegInfo toInfo = new TripLegInfo();
		List<Flight> toFlights = flightService.getFlightByAirports(fromAirport, toAirport);
		toInfo.setFlightsOptions(toFlights);
		legs.add(toInfo);
		toInfo.setCurrentPage(0);
		toInfo.setHasMoreOptions(false);
		toInfo.setNumPages(1);
		toInfo.setPageSize(TripLegInfo.DEFAULT_PAGE_SIZE);
		
		if (!oneWay) {
			TripLegInfo retInfo = new TripLegInfo();
			List<Flight> retFlights = flightService.getFlightByAirports(toAirport, fromAirport);
			retInfo.setFlightsOptions(retFlights);
			legs.add(retInfo);
			retInfo.setCurrentPage(0);
			retInfo.setHasMoreOptions(false);
			retInfo.setNumPages(1);
			retInfo.setPageSize(TripLegInfo.DEFAULT_PAGE_SIZE);
			options.setTripLegs(2);
		}
		else {
			options.setTripLegs(1);
		}
		
		options.setTripFlights(legs);
		
		return options;
	}	

}

// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/web/FlightsREST.java:FlightsREST.<init>
// Node: getTripFlights
// Node: TripFlightOptions
// Node: TripLegInfo
// Node: setCurrentPage
// Node: setHasMoreOptions
// Node: setNumPages
// Node: setPageSize
// Node: setTripLegs
// Node: setTripFlights
// Node: browseFlights
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
package com.acmeair.web.dto;

import java.util.List;

import javax.xml.bind.annotation.XmlAccessType;
import javax.xml.bind.annotation.XmlAccessorType;
import javax.xml.bind.annotation.XmlRootElement;

/**
 * TripFlightOptions is the main return type when searching for flights.
 * 
 * The object will return as many tripLeg's worth of Flight options as requested.  So if the user
 * requests a one way flight they will get a List that has only one TripLegInfo and it will have
 * a list of flights that are options for that flight.  If a user selects round trip, they will
 * have a List of two TripLegInfo objects.  If a user does a multi-leg flight then the list will
 * be whatever size they requested.  For now, only supporting one way and return flights so the
 * list should always be of size one or two.
 * 
 * 
 * @author aspyker
 *
 */
@XmlAccessorType(XmlAccessType.PUBLIC_MEMBER)
@XmlRootElement
public class TripFlightOptions {
	private int tripLegs;
	
	private List<TripLegInfo> tripFlights;

	public int getTripLegs() {
		return tripLegs;
	}

	public void setTripLegs(int tripLegs) {
		this.tripLegs = tripLegs;
	}

	public List<TripLegInfo> getTripFlights() {
		return tripFlights;
	}

	public void setTripFlights(List<TripLegInfo> tripFlights) {
		this.tripFlights = tripFlights;
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
package com.acmeair.web.dto;

import java.util.ArrayList;
import java.util.List;

import com.acmeair.entities.Flight;

/**
 * The TripLegInfo object contains a list of flights that satisfy the query request for any one
 * leg of a trip.  Also, it supports paging so a query can't return too many requests.
 * @author aspyker
 *
 */
public class TripLegInfo {
	public static int DEFAULT_PAGE_SIZE = 10;
	
	private boolean hasMoreOptions;
	
	private int numPages;
	private int pageSize;
	private int currentPage;
	
	private List<FlightInfo> flightsOptions;

	public boolean isHasMoreOptions() {
		return hasMoreOptions;
	}

	public void setHasMoreOptions(boolean hasMoreOptions) {
		this.hasMoreOptions = hasMoreOptions;
	}

	public int getNumPages() {
		return numPages;
	}

	public void setNumPages(int numPages) {
		this.numPages = numPages;
	}

	public int getPageSize() {
		return pageSize;
	}

	public void setPageSize(int pageSize) {
		this.pageSize = pageSize;
	}

	public int getCurrentPage() {
		return currentPage;
	}

	public void setCurrentPage(int currentPage) {
		this.currentPage = currentPage;
	}

	public List<FlightInfo> getFlightsOptions() {
		return flightsOptions;
	}

	public void setFlightsOptions(List<Flight> flightsOptions) {
		List<FlightInfo> flightInfoOptions = new ArrayList<FlightInfo>();
		for(Flight info : flightsOptions){
			flightInfoOptions.add(new FlightInfo(info));
		}
		this.flightsOptions = flightInfoOptions;
	}
	

}

package com.acmeair.config;

import java.util.ArrayList;
import java.util.Map;
import java.util.logging.Logger;

import javax.annotation.PostConstruct;
import javax.enterprise.inject.spi.BeanManager;
import javax.inject.Inject;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Response;

import com.acmeair.service.BookingService;
import com.acmeair.service.CustomerService;
import com.acmeair.service.FlightService;
import com.acmeair.service.ServiceLocator;


@Path("/config")
public class AcmeAirConfiguration {
    
	@Inject
	BeanManager beanManager;
	Logger logger = Logger.getLogger(AcmeAirConfiguration.class.getName());

	private BookingService bs = ServiceLocator.instance().getService(BookingService.class);
	private CustomerService customerService = ServiceLocator.instance().getService(CustomerService.class);
	private FlightService flightService = ServiceLocator.instance().getService(FlightService.class);

	
    public AcmeAirConfiguration() {
        super();
    }

	@PostConstruct
	private void initialization()  {		
		if(beanManager == null){
			logger.info("Attempting to look up BeanManager through JNDI at java:comp/BeanManager");
			try {
				beanManager = (BeanManager) new InitialContext().lookup("java:comp/BeanManager");
			} catch (NamingException e) {
				logger.severe("BeanManager not found at java:comp/BeanManager");
			}
		}
		
		if(beanManager == null){
			logger.info("Attempting to look up BeanManager through JNDI at java:comp/env/BeanManager");
			try {
				beanManager = (BeanManager) new InitialContext().lookup("java:comp/env/BeanManager");
			} catch (NamingException e) {
				logger.severe("BeanManager not found at java:comp/env/BeanManager ");
			}
		}
	}
    
    
	@GET
	@Path("/dataServices")
	@Produces("application/json")
	public ArrayList<ServiceData> getDataServiceInfo() {
		try {	
			ArrayList<ServiceData> list = new ArrayList<ServiceData>();
			Map<String, String> services =  ServiceLocator.instance().getServices();
			logger.fine("Get data service configuration info");
			for (Map.Entry<String, String> entry : services.entrySet()){
				ServiceData data = new ServiceData();
				data.name = entry.getKey();
				data.description = entry.getValue();
				list.add(data);
			}
			
			return list;
		}
		catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}

	
	@GET
	@Path("/activeDataService")
	@Produces("application/json")
	public Response getActiveDataServiceInfo() {
		try {		
			logger.fine("Get active Data Service info");
			return  Response.ok(ServiceLocator.instance().getServiceType()).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.ok("Unknown").build();
		}
	}
	
	@GET
	@Path("/runtime")
	@Produces("application/json")
	public ArrayList<ServiceData> getRuntimeInfo() {
		try {
			logger.fine("Getting Runtime info");
			ArrayList<ServiceData> list = new ArrayList<ServiceData>();
			ServiceData data = new ServiceData();
			data.name = "Runtime";
			data.description = "Java";			
			list.add(data);
			
			data = new ServiceData();
			data.name = "Version";
			data.description = System.getProperty("java.version");			
			list.add(data);
			
			data = new ServiceData();
			data.name = "Vendor";
			data.description = System.getProperty("java.vendor");			
			list.add(data);
			
			return list;
		}
		catch (Exception e) {
			e.printStackTrace();
			return null;
		}
	}

	
	class ServiceData {
		public String name = "";
		public String description = "";
	}
	
	@GET
	@Path("/countBookings")
	@Produces("application/json")
	public Response countBookings() {
		try {
			Long count = bs.count();			
			return Response.ok(count).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.ok(-1).build();
		}
	}
	
	@GET
	@Path("/countCustomers")
	@Produces("application/json")
	public Response countCustomer() {
		try {
			Long customerCount = customerService.count();
			
			return Response.ok(customerCount).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.ok(-1).build();
		}
	}
	
	
	@GET
	@Path("/countSessions")
	@Produces("application/json")
	public Response countCustomerSessions() {
		try {
			Long customerCount = customerService.countSessions();
			
			return Response.ok(customerCount).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.ok(-1).build();
		}
	}
	
	
	@GET
	@Path("/countFlights")
	@Produces("application/json")
	public Response countFlights() {
		try {
			Long count = flightService.countFlights();			
			return Response.ok(count).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.ok(-1).build();
		}
	}
	
	@GET
	@Path("/countFlightSegments")
	@Produces("application/json")
	public Response countFlightSegments() {
		try {
			Long count = flightService.countFlightSegments();			
			return Response.ok(count).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.ok(-1).build();
		}
	}
	
	@GET
	@Path("/countAirports")
	@Produces("application/json")
	public Response countAirports() {
		try {			
			Long count = flightService.countAirports();	
			return Response.ok(count).build();
		}
		catch (Exception e) {
			e.printStackTrace();
			return Response.ok(-1).build();
		}
	}
	
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-webapp/src/main/java/com/acmeair/config/AcmeAirConfiguration.java:AcmeAirConfiguration.<init>
// Node: AcmeAirConfiguration
// Node: getDataServiceInfo
// Node: fine
// Node: ServiceData
// Node: getActiveDataServiceInfo
// Node: getServiceType
// Node: getRuntimeInfo
// Node: countBookings
// Node: countCustomer
// Node: countCustomerSessions
package com.acmeair.config;

import javax.inject.Inject;
import javax.ws.rs.DefaultValue;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.Response;

import com.acmeair.loader.Loader;


@Path("/loader")
public class LoaderREST {

//	private static Logger logger = Logger.getLogger(LoaderREST.class.getName());
	
	@Inject
	private Loader loader;	
	
	@GET
	@Path("/query")
	@Produces("text/plain")
	public Response queryLoader() {			
		String response = loader.queryLoader();
		return Response.ok(response).build();	
	}
	
	
	@GET
	@Path("/load")
	@Produces("text/plain")
	public Response loadDB(@DefaultValue("-1") @QueryParam("numCustomers") long numCustomers) {	
		String response = loader.loadDB(numCustomers);
		return Response.ok(response).build();	
	}
}


// Node: loadDB
// Node: DefaultValue
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
package com.acmeair.loader;

import com.acmeair.entities.Customer;
import com.acmeair.entities.CustomerAddress;
import com.acmeair.entities.Customer.PhoneType;
import com.acmeair.service.CustomerService;
import com.acmeair.service.ServiceLocator;


public class CustomerLoader {

	private CustomerService customerService = ServiceLocator.instance().getService(CustomerService.class);

	
	public void loadCustomers(long numCustomers) {
		CustomerAddress address = customerService.createAddress("123 Main St.", null, "Anytown", "NC", "USA", "27617");
		for (long ii = 0; ii < numCustomers; ii++) {
			customerService.createCustomer("uid"+ii+"@email.com", "password", Customer.MemberShipStatus.GOLD, 1000000, 1000, "919-123-4567", PhoneType.BUSINESS, address);
		}
	}

}

// Node: repos/cloned_ms_repos/acmeair/acmeair-loader/src/main/java/com/acmeair/loader/CustomerLoader.java:CustomerLoader.<init>
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

import java.lang.annotation.Annotation;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.concurrent.atomic.AtomicReference;

import javax.annotation.PostConstruct;
import javax.enterprise.context.spi.CreationalContext;
import javax.enterprise.inject.Any;
import javax.enterprise.inject.Default;
import javax.enterprise.inject.spi.Bean;
import javax.enterprise.inject.spi.BeanManager;
import javax.enterprise.util.AnnotationLiteral;
import javax.inject.Inject;
import javax.naming.InitialContext;
import javax.naming.NamingException;

import java.util.logging.Logger;

import org.json.simple.JSONObject;
import org.json.simple.JSONValue;


public class ServiceLocator {

	public static String REPOSITORY_LOOKUP_KEY = "com.acmeair.repository.type";
	private static String serviceType;
	private static Logger logger = Logger.getLogger(ServiceLocator.class.getName());

	private static AtomicReference<ServiceLocator> singletonServiceLocator = new AtomicReference<ServiceLocator>();

	@Inject
	BeanManager beanManager;
	
	public static ServiceLocator instance() {
		if (singletonServiceLocator.get() == null) {
			synchronized (singletonServiceLocator) {
				if (singletonServiceLocator.get() == null) {
					singletonServiceLocator.set(new ServiceLocator());
				}
			}
		}
		return singletonServiceLocator.get();
	}
	
	@PostConstruct
	private void initialization()  {		
		if(beanManager == null){
			logger.info("Attempting to look up BeanManager through JNDI at java:comp/BeanManager");
			try {
				beanManager = (BeanManager) new InitialContext().lookup("java:comp/BeanManager");
			} catch (NamingException e) {
				logger.severe("BeanManager not found at java:comp/BeanManager");
			}
		}
		
		if(beanManager == null){
			logger.info("Attempting to look up BeanManager through JNDI at java:comp/env/BeanManager");
			try {
				beanManager = (BeanManager) new InitialContext().lookup("java:comp/env/BeanManager");
			} catch (NamingException e) {
				logger.severe("BeanManager not found at java:comp/env/BeanManager ");
			}
		}
	}
	
	public static void updateService(String serviceName){
		logger.info("Service Locator updating service to : " + serviceName);
		serviceType = serviceName;
	}

	private ServiceLocator() {
		String type = null;
		String lookup = REPOSITORY_LOOKUP_KEY.replace('.', '/');
		javax.naming.Context context = null;
		javax.naming.Context envContext = null;
		try {
			context = new javax.naming.InitialContext();
			envContext = (javax.naming.Context) context.lookup("java:comp/env");
			if (envContext != null)
				type = (String) envContext.lookup(lookup);
		} catch (NamingException e) {
			// e.printStackTrace();
		}
		
		if (type != null) {
			logger.info("Found repository in web.xml:" + type);
		}
		else if (context != null) {
			try {
				type = (String) context.lookup(lookup);
				if (type != null)
					logger.info("Found repository in server.xml:" + type);
			} catch (NamingException e) {
				// e.printStackTrace();
			}
		}

		if (type == null) {
			type = System.getProperty(REPOSITORY_LOOKUP_KEY);
			if (type != null)
				logger.info("Found repository in jvm property:" + type);
			else {
				type = System.getenv(REPOSITORY_LOOKUP_KEY);
				if (type != null)
					logger.info("Found repository in environment property:" + type);
			}
		}

		if(beanManager == null) {
			logger.info("Attempting to look up BeanManager through JNDI at java:comp/BeanManager");
			try {
				beanManager = (BeanManager) new InitialContext().lookup("java:comp/BeanManager");
			} catch (NamingException e) {
				logger.severe("BeanManager not found at java:comp/BeanManager");
			}
		}	
		
		if(beanManager == null){
			logger.info("Attempting to look up BeanManager through JNDI at java:comp/env/BeanManager");
			try {
				beanManager = (BeanManager) new InitialContext().lookup("java:comp/env/BeanManager");
			} catch (NamingException e) {
				logger.severe("BeanManager not found at java:comp/env/BeanManager ");
			}
		}
		
		if (type==null)
		{
			String vcapJSONString = System.getenv("VCAP_SERVICES");
			if (vcapJSONString != null) {
				logger.info("Reading VCAP_SERVICES");
				Object jsonObject = JSONValue.parse(vcapJSONString);
				logger.fine("jsonObject = " + ((JSONObject)jsonObject).toJSONString());
				JSONObject json = (JSONObject)jsonObject;
				String key;
				for (Object k: json.keySet())
				{
					key = (String ) k;
					if (key.startsWith("ElasticCaching")||key.startsWith("DataCache"))
					{
						logger.info("VCAP_SERVICES existed with service:"+key);
						type ="wxs";
						break;
					}
					if (key.startsWith("mongo"))
					{
						logger.info("VCAP_SERVICES existed with service:"+key);
						type ="morphia";
						break;
					}
					if (key.startsWith("redis"))
					{
						logger.info("VCAP_SERVICES existed with service:"+key);
						type ="redis";
						break;
					}
					if (key.startsWith("mysql")|| key.startsWith("cleardb"))
					{
						logger.info("VCAP_SERVICES existed with service:"+key);
						type ="mysql";
						break;
					}
					if (key.startsWith("postgresql"))
					{
						logger.info("VCAP_SERVICES existed with service:"+key);
						type ="postgresql";
						break;
					}
					if (key.startsWith("db2"))
					{
						logger.info("VCAP_SERVICES existed with service:"+key);
						type ="db2";
						break;
					}
				}
			}
		}
				
		serviceType = type;
		logger.info("ServiceType is now : " + serviceType);
		if (type ==null) {
			logger.warning("Can not determine type. Use default service implementation.");			
		}
	}

	@SuppressWarnings("unchecked")
	public <T> T getService (Class<T> clazz) {		
		logger.fine("Looking up service:  "+clazz.getName() + " with service type: " + serviceType);
		if(beanManager == null) {
			logger.severe("BeanManager is null!!!");
		}		
    	Set<Bean<?>> beans = beanManager.getBeans(clazz,new AnnotationLiteral<Any>() {
			private static final long serialVersionUID = 1L;});
    	for (Bean<?> bean : beans) {
    		logger.fine(" Bean = "+bean.getBeanClass().getName());
    		for (Annotation qualifer: bean.getQualifiers()) {
    			if(null == serviceType) {
    				logger.warning("Service type is not set, searching for the default implementation.");
    				if(Default.class.getName().equalsIgnoreCase(qualifer.annotationType().getName())){
    					CreationalContext<?> ctx = beanManager.createCreationalContext(bean);
    					return  (T) beanManager.getReference(bean, clazz, ctx);
    				}
    			} else {    				   
    				if(DataService.class.getName().equalsIgnoreCase(qualifer.annotationType().getName())){
    					DataService service = (DataService) qualifer;
    					logger.fine("   name="+service.name()+" description="+service.description());
    					if(serviceType.equalsIgnoreCase(service.name())) {
    						CreationalContext<?> ctx = beanManager.createCreationalContext(bean);
    						return  (T) beanManager.getReference(bean, clazz, ctx);

    					}
    				}
    			}
    		}
    	}
    	logger.warning("No Service of type: " + serviceType + " found for "+clazz.getName()+" ");
    	return null;
	}
	
	/**
	 * Retrieves the services that are available for use with the description for each service. 
	 * The Services are determined by looking up all of the implementations of the 
	 * Customer Service interface that are using the  DataService qualifier annotation. 
	 * The DataService annotation contains the service name and description information. 
	 * @return Map containing a list of services available and a description of each one.
	 */
	public Map<String,String> getServices (){
		TreeMap<String,String> services = new TreeMap<String,String>();
		logger.fine("Getting CustomerService Impls");
    	Set<Bean<?>> beans = beanManager.getBeans(CustomerService.class,new AnnotationLiteral<Any>() {
			private static final long serialVersionUID = 1L;});
    	for (Bean<?> bean : beans) {    		
    		for (Annotation qualifer: bean.getQualifiers()){
    			if(DataService.class.getName().equalsIgnoreCase(qualifer.annotationType().getName())){
    				DataService service = (DataService) qualifer;
    				logger.fine("   name="+service.name()+" description="+service.description());
    				services.put(service.name(), service.description());
    			}
    		}
    	}    	
    	return services;
	}
	
	/**
	 * The type of service implementation that the application is 
	 * currently configured to use.  
	 * 
	 * @return The type of service in use, or "default" if no service has been set. 
	 */
	public String getServiceType (){
		if(serviceType == null){
			return "default";
		}
		return serviceType;
	}
}


