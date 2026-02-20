// Cluster 6

// Node: updateCustomer
// Node: createSession
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

import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.LineNumberReader;
import java.util.*;
import java.math.*;

import com.acmeair.entities.AirportCodeMapping;
import com.acmeair.service.FlightService;
import com.acmeair.service.ServiceLocator;




public class FlightLoader {
	
	private static final int MAX_FLIGHTS_PER_SEGMENT = 30;
	

	private FlightService flightService = ServiceLocator.instance().getService(FlightService.class);

	public void loadFlights() throws Exception {
		InputStream csvInputStream = FlightLoader.class.getResourceAsStream("/mileage.csv");
		
		LineNumberReader lnr = new LineNumberReader(new InputStreamReader(csvInputStream));
		String line1 = lnr.readLine();
		StringTokenizer st = new StringTokenizer(line1, ",");
		ArrayList<AirportCodeMapping> airports = new ArrayList<AirportCodeMapping>();
		
		// read the first line which are airport names
		while (st.hasMoreTokens()) {
			AirportCodeMapping acm = flightService.createAirportCodeMapping(null, st.nextToken());
		//	acm.setAirportName(st.nextToken());
			airports.add(acm);
		}
		// read the second line which contains matching airport codes for the first line
		String line2 = lnr.readLine();
		st = new StringTokenizer(line2, ",");
		int ii = 0;
		while (st.hasMoreTokens()) {
			String airportCode = st.nextToken();
			airports.get(ii).setAirportCode(airportCode);
			ii++;
		}
		// read the other lines which are of format:
		// airport name, aiport code, distance from this airport to whatever airport is in the column from lines one and two
		String line;
		int flightNumber = 0;
		while (true) {
			line = lnr.readLine();
			if (line == null || line.trim().equals("")) {
				break;
			}
			st = new StringTokenizer(line, ",");
			String airportName = st.nextToken();
			String airportCode = st.nextToken();
			if (!alreadyInCollection(airportCode, airports)) {
				AirportCodeMapping acm = flightService.createAirportCodeMapping(airportCode, airportName);
				airports.add(acm);
			}
			int indexIntoTopLine = 0;
			while (st.hasMoreTokens()) {
				String milesString = st.nextToken();
				if (milesString.equals("NA")) {
					indexIntoTopLine++;
					continue;
				}
				int miles = Integer.parseInt(milesString);
				String toAirport = airports.get(indexIntoTopLine).getAirportCode();
				String flightId = "AA" + flightNumber;			
				flightService.storeFlightSegment(flightId, airportCode, toAirport, miles);
				Date now = new Date();
				for (int daysFromNow = 0; daysFromNow < MAX_FLIGHTS_PER_SEGMENT; daysFromNow++) {
					Calendar c = Calendar.getInstance();
					c.setTime(now);
					c.set(Calendar.HOUR_OF_DAY, 0);
				    c.set(Calendar.MINUTE, 0);
				    c.set(Calendar.SECOND, 0);
				    c.set(Calendar.MILLISECOND, 0);
					c.add(Calendar.DATE, daysFromNow);
					Date departureTime = c.getTime();
					Date arrivalTime = getArrivalTime(departureTime, miles);
					flightService.createNewFlight(flightId, departureTime, arrivalTime, new BigDecimal(500), new BigDecimal(200), 10, 200, "B747");
					
				}
				flightNumber++;
				indexIntoTopLine++;
			}
		}
		
		for (int jj = 0; jj < airports.size(); jj++) {
			flightService.storeAirportMapping(airports.get(jj));
		}
		lnr.close();
	}
	
	private static Date getArrivalTime(Date departureTime, int mileage) {
		double averageSpeed = 600.0; // 600 miles/hours
		double hours = (double) mileage / averageSpeed; // miles / miles/hour = hours
		double partsOfHour = hours % 1.0;
		int minutes = (int)(60.0 * partsOfHour);
		Calendar c = Calendar.getInstance();
		c.setTime(departureTime);
		c.add(Calendar.HOUR, (int)hours);
		c.add(Calendar.MINUTE, minutes);
		return c.getTime();
	}
	
	static private boolean alreadyInCollection(String airportCode, ArrayList<AirportCodeMapping> airports) {
		for (int ii = 0; ii < airports.size(); ii++) {
			if (airports.get(ii).getAirportCode().equals(airportCode)) {
				return true;
			}
		}
		return false;
	}
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-loader/src/main/java/com/acmeair/loader/FlightLoader.java:FlightLoader.<init>
// Node: LineNumberReader
// Node: StringTokenizer
// Node: hasMoreTokens
// Node: createAirportCodeMapping
// Node: nextToken
// Node: setAirportName
// Node: setAirportCode
// Node: alreadyInCollection
// Node: getAirportCode
// Node: getInstance
// Node: setTime
// Node: set
// Node: getTime
// Node: getArrivalTime
// Node: createNewFlight
// Node: storeAirportMapping
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

import com.acmeair.entities.AirportCodeMapping;

@Entity(value="airportCodeMapping")
public class AirportCodeMappingImpl implements AirportCodeMapping, Serializable{
	
	private static final long serialVersionUID = 1L;

	private String _id;
	private String airportName;
	
	public AirportCodeMappingImpl() {
	}
	
	public AirportCodeMappingImpl(String airportCode, String airportName) {
		this._id = airportCode;
		this.airportName = airportName;
	}
	
	public String getAirportCode() {
		return _id;
	}
	
	public void setAirportCode(String airportCode) {
		this._id = airportCode;
	}
	
	public String getAirportName() {
		return airportName;
	}
	
	public void setAirportName(String airportName) {
		this.airportName = airportName;
	}

}

// Node: getAirportName
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


// Node: save
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


public interface AirportCodeMapping{
	
	
	public String getAirportCode();
	
	public void setAirportCode(String airportCode);
	
	public String getAirportName();
	
	public void setAirportName(String airportName);

}

// Node: repos/cloned_ms_repos/acmeair/acmeair-common/src/main/java/com/acmeair/entities/AirportCodeMapping.java:AirportCodeMapping.<init>
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


// Node: getAllInputList
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
package com.acmeair.reporter.parser;

import static com.googlecode.charts4j.Color.ALICEBLUE;
import static com.googlecode.charts4j.Color.BLACK;
import static com.googlecode.charts4j.Color.LAVENDER;
import static com.googlecode.charts4j.Color.WHITE;

import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.DirectoryFileFilter;
import org.apache.commons.io.filefilter.RegexFileFilter;

import com.acmeair.reporter.parser.component.NmonParser;
import com.googlecode.charts4j.AxisLabels;
import com.googlecode.charts4j.AxisLabelsFactory;
import com.googlecode.charts4j.AxisStyle;
import com.googlecode.charts4j.AxisTextAlignment;
import com.googlecode.charts4j.Color;
import com.googlecode.charts4j.Data;
import com.googlecode.charts4j.DataEncoding;
import com.googlecode.charts4j.Fills;
import com.googlecode.charts4j.GCharts;
import com.googlecode.charts4j.Line;
import com.googlecode.charts4j.LineChart;
import com.googlecode.charts4j.LineStyle;
import com.googlecode.charts4j.LinearGradientFill;
import com.googlecode.charts4j.Plots;
import com.googlecode.charts4j.Shape;

public abstract class ResultParser {

	protected MultipleChartResults multipleChartResults = new MultipleChartResults();
	protected OverallResults overallResults = new OverallResults();
	
	public MultipleChartResults getMultipleChartResults() {
		return multipleChartResults;
	}

	protected void addUp(ArrayList<Double> list) {
		//if empty, don't need to add up
		if (overallResults.getAllInputList().isEmpty()) {
			overallResults.setAllInputList(list);
			return;
		}
		int size = overallResults.getAllInputList().size();
		if (size > list.size()) {
			size = list.size();
		}
		for (int i = 0; i < size; i++) {
			overallResults.getAllInputList().set(i, overallResults.getAllInputList().get(i) + list.get(i));
		}

	}

	public void processDirectory(String dirName) {
		File root = new File(dirName);
		try {
			Collection<File> files = FileUtils.listFiles(root,
					new RegexFileFilter(getFileName()),
					DirectoryFileFilter.DIRECTORY);

			for (Iterator<File> iterator = files.iterator(); iterator.hasNext();) {
				File file = (File) iterator.next();
				processFile(file);
			}
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public String generateChartStrings(String titileLabel, String ylabel,
			String xlable, double[] inputs, ArrayList<String> timeList, boolean addToList) {
		if (inputs == null || inputs.length == 0)
			return null;
		Line line1 = Plots.newLine(Data.newData(inputs),
				Color.newColor("CA3D05"), "");
		line1.setLineStyle(LineStyle.newLineStyle(2, 1, 0));
		line1.addShapeMarkers(Shape.DIAMOND, Color.newColor("CA3D05"), 6);		
		LineChart chart = GCharts.newLineChart(line1);
		// Defining axis info and styles
		chart.addYAxisLabels(AxisLabelsFactory.newNumericRangeAxisLabels(0,
				overallResults.getScale_max() / 0.9));		
		if (timeList != null && timeList.size() > 0) {
			chart.addXAxisLabels(AxisLabelsFactory.newAxisLabels(timeList));
		}

		String url = generateDefaultChartSettings(titileLabel, ylabel, xlable,
				chart, addToList);		
		return url;
	}

	public String generateDefaultChartSettings(String titileLabel,
			String ylabel, String xlable, LineChart chart, boolean addToList) {
		AxisStyle axisStyle = AxisStyle.newAxisStyle(BLACK, 13,
				AxisTextAlignment.CENTER);
		AxisLabels yAxisLabel = AxisLabelsFactory.newAxisLabels(ylabel, 50.0);
		yAxisLabel.setAxisStyle(axisStyle);
		AxisLabels time = AxisLabelsFactory.newAxisLabels(xlable, 50.0);
		time.setAxisStyle(axisStyle);

		chart.addYAxisLabels(yAxisLabel);

		chart.addXAxisLabels(time);

		chart.setDataEncoding(DataEncoding.SIMPLE);

		chart.setSize(1000, 300);

		chart.setTitle(titileLabel, BLACK, 16);
		chart.setGrid(100, 10, 3, 2);
		chart.setBackgroundFill(Fills.newSolidFill(ALICEBLUE));
		LinearGradientFill fill = Fills.newLinearGradientFill(0, LAVENDER, 100);
		fill.addColorAndOffset(WHITE, 0);
		chart.setAreaFill(fill);
		String url = chart.toURLString();
		if(addToList) {
			getCharStrings().add(url);
		}
		return url;
	}

	public String generateMultipleLinesCharString(String titileLabel,
			String ylabel, String xlabel, List<IndividualChartResults> list) {

		if (list ==null || list.size()==0) {
			return null;
		}
		Line[] lines = new Line[list.size()];
		for (int i = 0; i < list.size(); i++) {
			double[] multiLineData = processMultiLineData(list.get(i).getInputList());
			if (multiLineData!=null) {
				lines[i] = Plots.newLine(Data.newData(multiLineData), ResultParserHelper.getColor(i), list.get(i).getTitle());
				lines[i].setLineStyle(LineStyle.newLineStyle(2, 1, 0));		
			} else {
				System.out.println("found jmeter log file that doesn't have data:\" " + list.get(i).getTitle() +"\" skipping!");
				return null;
			}
		}

		LineChart chart = GCharts.newLineChart(lines);
		chart.addYAxisLabels(AxisLabelsFactory.newNumericRangeAxisLabels(0,
				overallResults.getOverallScale_max() / 0.9));
		
		chart.addXAxisLabels(AxisLabelsFactory.newAxisLabels(list.get(0)
				.getTimeList()));
		// Defining axis info and styles
		String url = generateDefaultChartSettings(titileLabel, ylabel, xlabel,
				chart, true);		
		return url;
	}

	public ArrayList<Double> getAllInputList() {
		return overallResults.getAllInputList();
	}
	public ArrayList<String> getAllTimeList() {
		return overallResults.getAllTimeList();
	}
	public ArrayList<String> getCharStrings() {
		return getMultipleChartResults().getCharStrings();
	}

	protected <E> IndividualChartResults getData(String fileName) {
		IndividualChartResults results = new IndividualChartResults();
		try {
			FileInputStream fstream = new FileInputStream(fileName);
			// Get the object of DataInputStream
			DataInputStream in = new DataInputStream(fstream);
			BufferedReader br = new BufferedReader(new InputStreamReader(in));
			String strLine;

			while ((strLine = br.readLine()) != null) {
				processLine(results, strLine);
			}
			in.close();
		} catch (Exception e) {
			System.err.println("Error: " + e.getMessage());
		}		

		addUp(results.getInputList());
		overallResults.setAllTimeList(results.getTimeList());
		return results;
	}

	public abstract String getFileName();
	
	public abstract void setFileName(String fileName);

	public ArrayList<IndividualChartResults> getResults() {
		return getMultipleChartResults().getResults();
	}


	public double[] processData(ArrayList<Double> inputList, boolean isTotalThroughput) {
		if (inputList != null && inputList.size() > 0) {
			if (this instanceof NmonParser) {
					overallResults.setScale_max(90.0);
			} else {
				overallResults.setScale_max(Collections.max(inputList));
			}
			if (overallResults.getOverallScale_max() < overallResults.getScale_max() && !isTotalThroughput) {
				overallResults.setOverallScale_max( overallResults.getScale_max());
			}			
			double scale_factor = 90 / overallResults.getScale_max();
			return ResultParserHelper.scaleInputsData(inputList, scale_factor);
		}
		return null;
	}

	protected abstract void processFile(File file);

	protected abstract void processLine(IndividualChartResults result, String strLine);

	public double[] processMultiLineData(ArrayList<Double> inputList) {
		if (inputList != null && inputList.size() > 0) {			
			double scale_factor = 90 / overallResults.getOverallScale_max();
			return ResultParserHelper.scaleInputsData(inputList, scale_factor);
		}
		return null;
	}

	public String getMultipleChartTitle() {		
		return multipleChartResults.getMultipleChartTitle();
	}

	public void setMultipleYAxisLabel(String label){
		multipleChartResults.setMultipleChartYAxisLabel(label);
	}
	
	public void setMultipleChartTitle(String label){
		multipleChartResults.setMultipleChartTitle(label);
	}
	public String getMultipleYAxisLabel() {
		return multipleChartResults.getMultipleChartYAxisLabel();
	}
	
}


// Node: addUp
// Node: setAllInputList
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
package com.acmeair.reporter.parser;

import java.util.ArrayList;

public class OverallResults {
	private ArrayList<Double> allInputList = new ArrayList<Double>();
	private ArrayList<String> allTimeList = new ArrayList<String>();
	private double scale_max;
	private double overallScale_max;

	public ArrayList<Double> getAllInputList() {
		return allInputList;
	}

	public void setAllInputList(ArrayList<Double> allInputList) {
		this.allInputList = new ArrayList<Double> (allInputList);
	}

	public ArrayList<String> getAllTimeList() {
		return allTimeList;
	}

	public void setAllTimeList(ArrayList<String> allTimeList) {
		this.allTimeList = new ArrayList<String> (allTimeList);
	}

	public double getOverallScale_max() {
		return overallScale_max;
	}

	public void setOverallScale_max(double overallScale_max) {
		this.overallScale_max = overallScale_max;
	}

	public double getScale_max() {
		return scale_max;
	}

	public void setScale_max(double scale_max) {
		this.scale_max = scale_max;
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
package com.acmeair.wxs.entities;

import java.io.Serializable;

import com.acmeair.entities.AirportCodeMapping;

public class AirportCodeMappingImpl implements AirportCodeMapping, Serializable{
	
	private static final long serialVersionUID = 1L;

	private String _id;
	private String airportName;
	
	public AirportCodeMappingImpl() {
	}
	
	public AirportCodeMappingImpl(String airportCode, String airportName) {
		this._id = airportCode;
		this.airportName = airportName;
	}
	
	public String getAirportCode() {
		return _id;
	}
	
	public void setAirportCode(String airportCode) {
		this._id = airportCode;
	}
	
	public String getAirportName() {
		return airportName;
	}
	
	public void setAirportName(String airportName) {
		this.airportName = airportName;
	}

}

