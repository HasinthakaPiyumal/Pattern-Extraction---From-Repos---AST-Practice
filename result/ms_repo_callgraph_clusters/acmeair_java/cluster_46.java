// Cluster 46

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


// Node: initialization
// Node: info
// Node: InitialContext
// Node: lookup
// Node: severe
// Node: getProperty
// Node: queryLoader
// Node: loadCustomers
// Node: loadFlights
// Node: getResourceAsStream
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
package com.acmeair.loader;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;
import java.util.logging.Logger;

public class Loader {
	public static String REPOSITORY_LOOKUP_KEY = "com.acmeair.repository.type";

	private static Logger logger = Logger.getLogger(Loader.class.getName());

	public String queryLoader() {			
		String message = System.getProperty("loader.numCustomers");
		if (message == null){
			logger.info("The system property 'loader.numCustomers' has not been set yet. Looking up the default properties.");
			lookupDefaults();
			message = System.getProperty("loader.numCustomers");
		}				
		return message;	
	}
	
	public String loadDB(long numCustomers) {		
		String message = "";
		if(numCustomers == -1)
			message = execute();
		else {
			System.setProperty("loader.numCustomers", Long.toString(numCustomers));
			message = execute(numCustomers);
		}
		return message;	
	}
	
	
	
	public static void main(String args[]) throws Exception {
		Loader loader = new Loader();
		loader.execute();
	}
	
	
	private String execute() {
		String numCustomers = System.getProperty("loader.numCustomers");
		if (numCustomers == null){
			logger.info("The system property 'loader.numCustomers' has not been set yet. Looking up the default properties.");
			lookupDefaults();
			numCustomers = System.getProperty("loader.numCustomers");
		}
		return execute(Long.parseLong(numCustomers));
	}
	
	
	private String execute(long numCustomers) {
		FlightLoader flightLoader = new FlightLoader();
		CustomerLoader customerLoader = new CustomerLoader();

    	double length = 0;
		try {
			long start = System.currentTimeMillis();
			logger.info("Start loading flights");
			flightLoader.loadFlights();
			logger.info("Start loading " +  numCustomers + " customers");
			customerLoader.loadCustomers(numCustomers);
			long stop = System.currentTimeMillis();
			logger.info("Finished loading in " + (stop - start)/1000.0 + " seconds");
			length = (stop - start)/1000.0;
		}
		catch (Exception e) {
			e.printStackTrace();
		}		
		return "Loaded flights and "  +  numCustomers + " customers in " + length + " seconds";
	}
	
	
	private void lookupDefaults (){
		Properties props = getProperties();
		
        String numCustomers = props.getProperty("loader.numCustomers","100");
    	System.setProperty("loader.numCustomers", numCustomers);		
	}
	
	
	private Properties getProperties(){
        /*
         * Get Properties from loader.properties file. 
         * If the file does not exist, use default values
         */
		Properties props = new Properties();
		String propFileName = "/loader.properties";
		try{			
			InputStream propFileStream = Loader.class.getResourceAsStream(propFileName);
			props.load(propFileStream);
		//	props.load(new FileInputStream(propFileName));
		}catch(FileNotFoundException e){
			logger.info("Property file " + propFileName + " not found.");
		}catch(IOException e){
			logger.info("IOException - Property file " + propFileName + " not found.");
		}
    	return props;
	}
	/*
	private void execute(String args[]) {
		ApplicationContext ctx = null;
         //
         // Get Properties from loader.properties file. 
         // If the file does not exist, use default values
         //
		Properties props = new Properties();
		String propFileName = "/loader.properties";
		try{			
			InputStream propFileStream = Loader.class.getResourceAsStream(propFileName);
			props.load(propFileStream);
		//	props.load(new FileInputStream(propFileName));
		}catch(FileNotFoundException e){
			logger.info("Property file " + propFileName + " not found.");
		}catch(IOException e){
			logger.info("IOException - Property file " + propFileName + " not found.");
		}
		
        String numCustomers = props.getProperty("loader.numCustomers","100");
    	System.setProperty("loader.numCustomers", numCustomers);

		String type = null;
		String lookup = REPOSITORY_LOOKUP_KEY.replace('.', '/');
		javax.naming.Context context = null;
		javax.naming.Context envContext;
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

		if (type ==null) // Default to wxsdirect
		{
			type = "wxsdirect";
			logger.info("Using default repository :" + type);
		}
		if (type.equals("wxsdirect"))
			ctx = new AnnotationConfigApplicationContext(WXSDirectAppConfig.class);
		else if (type.equals("mongodirect"))
			ctx = new AnnotationConfigApplicationContext(MongoDirectAppConfig.class);
		else
		{
			logger.info("Did not find a matching config. Using default repository wxsdirect instead");
			ctx = new AnnotationConfigApplicationContext(WXSDirectAppConfig.class);
		}
		
		FlightLoader flightLoader = ctx.getBean(FlightLoader.class);
		CustomerLoader customerLoader = ctx.getBean(CustomerLoader.class);
		
		try {
			long start = System.currentTimeMillis();
			logger.info("Start loading flights");
			flightLoader.loadFlights();
			logger.info("Start loading " +  numCustomers + " customers");
			customerLoader.loadCustomers(Long.parseLong(numCustomers));
			long stop = System.currentTimeMillis();
			logger.info("Finished loading in " + (stop - start)/1000.0 + " seconds");
		}
		catch (Exception e) {
			e.printStackTrace();
		}
	}
	*/
}

// Node: lookupDefaults
// Node: execute
// Node: setProperty
// Node: main
// Node: Loader
// Node: FlightLoader
// Node: CustomerLoader
// Node: currentTimeMillis
// Node: Properties
// Node: load
// Node: FileInputStream
// Node: replace
// Node: getProperties
// Node: getenv
// Node: AnnotationConfigApplicationContext
// Node: getBean
package com.acmeair.morphia;

import java.math.BigInteger;

import org.mongodb.morphia.converters.SimpleValueConverter;
import org.mongodb.morphia.converters.TypeConverter;
import org.mongodb.morphia.mapping.MappedField;
import org.mongodb.morphia.mapping.MappingException;

public class BigIntegerConverter extends TypeConverter implements SimpleValueConverter{

    public BigIntegerConverter() {
        super(BigInteger.class);
    }

    @Override
    public Object encode(Object value, MappedField optionalExtraInfo) {
        return value.toString();
    }

    @Override
    public Object decode(Class targetClass, Object fromDBObject, MappedField optionalExtraInfo) throws MappingException {
        if (fromDBObject == null) return null;

        return new BigInteger(fromDBObject.toString());
    }
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-services-morphia/src/main/java/com/acmeair/morphia/BigIntegerConverter.java:BigIntegerConverter.<init>
// Node: BigIntegerConverter
package com.acmeair.morphia;

import java.util.Properties;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;

import com.acmeair.entities.Booking;
import com.acmeair.entities.Flight;
import com.acmeair.entities.FlightSegment;
import org.mongodb.morphia.Datastore;
import org.mongodb.morphia.Morphia;
import com.mongodb.MongoClient;
import com.mongodb.MongoClientOptions;
import com.mongodb.MongoClientURI;
import com.mongodb.WriteConcern;

public class DatastoreFactory {

	private static String mongourl = null;
	
	static {
		String vcapJSONString = System.getenv("VCAP_SERVICES");
		if (vcapJSONString != null) {
			System.out.println("Reading VCAP_SERVICES");
			Object jsonObject = JSONValue.parse(vcapJSONString);
			JSONObject json = (JSONObject)jsonObject;
			System.out.println("jsonObject = " + json.toJSONString());
			for (Object key: json.keySet())
			{
				if (((String)key).contains("mongo"))
				{
					System.out.println("Found mongo service:" +key);
					JSONArray mongoServiceArray = (JSONArray)json.get(key);
					JSONObject mongoService = (JSONObject) mongoServiceArray.get(0);
					JSONObject credentials = (JSONObject)mongoService.get("credentials");
					mongourl = (String)credentials.get("url");
					if (mongourl==null)
						mongourl= (String)credentials.get("uri");
					System.out.println("service url = " + mongourl);
					break;
				}
			}
		}


	}

	public static Datastore getDatastore(Datastore ds)
	{
		Datastore result =ds;
		
		if (mongourl!=null)
		{
			try{
				Properties prop = new Properties();
				prop.load(DatastoreFactory.class.getResource("/acmeair-mongo.properties").openStream());
				boolean fsync = new Boolean(prop.getProperty("mongo.fsync"));
				int w = new Integer(prop.getProperty("mongo.w"));
				int connectionsPerHost = new Integer(prop.getProperty("mongo.connectionsPerHost"));
				int threadsAllowedToBlockForConnectionMultiplier = new Integer(prop.getProperty("mongo.threadsAllowedToBlockForConnectionMultiplier"));
				
				// To match the local options
				MongoClientOptions.Builder builder = new MongoClientOptions.Builder()
					.writeConcern(new WriteConcern(w, 0, fsync))
					.connectionsPerHost(connectionsPerHost)
					.threadsAllowedToBlockForConnectionMultiplier(threadsAllowedToBlockForConnectionMultiplier);
			
				MongoClientURI mongoURI = new MongoClientURI(mongourl, builder);
				MongoClient mongo = new MongoClient(mongoURI);
				Morphia morphia = new Morphia();				
				result = morphia.createDatastore( mongo ,mongoURI.getDatabase());
				System.out.println("create mongo datastore with options:"+result.getMongo().getMongoClientOptions());
			}catch (Exception e)
			{
				e.printStackTrace();
			}
		}
    	// The converter is added for handing JDK 7 issue
	//	result.getMapper().getConverters().addConverter(new BigDecimalConverter());		
    //	result.getMapper().getConverters().addConverter(new BigIntegerConverter());
    	
		// Enable index
		result.ensureIndex(Booking.class, "pkey.customerId");
		result.ensureIndex(Flight.class, "pkey.flightSegmentId,scheduledDepartureTime");
		result.ensureIndex(FlightSegment.class, "originPort,destPort");

    	return result;
	}
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-services-morphia/src/main/java/com/acmeair/morphia/DatastoreFactory.java:DatastoreFactory.<init>
// Node: parse
// Node: toJSONString
// Node: keySet
// Node: getDatastore
// Node: getResource
// Node: openStream
// Node: Boolean
// Node: Integer
// Node: Builder
// Node: writeConcern
// Node: WriteConcern
// Node: connectionsPerHost
// Node: threadsAllowedToBlockForConnectionMultiplier
// Node: MongoClientURI
// Node: MongoClient
// Node: Morphia
// Node: createDatastore
// Node: getDatabase
// Node: getMongo
// Node: getMongoClientOptions
// Node: getMapper
// Node: getConverters
// Node: addConverter
// Node: BigDecimalConverter
// Node: ensureIndex
package com.acmeair.morphia;

import java.math.BigDecimal;

import org.mongodb.morphia.converters.SimpleValueConverter;
import org.mongodb.morphia.converters.TypeConverter;
import org.mongodb.morphia.mapping.MappedField;
import org.mongodb.morphia.mapping.MappingException;

public class BigDecimalConverter extends TypeConverter implements SimpleValueConverter{

    public BigDecimalConverter() {
        super(BigDecimal.class);
    }

    @Override
    public Object encode(Object value, MappedField optionalExtraInfo) {
        return value.toString();
    }

    @Override
    public Object decode(Class targetClass, Object fromDBObject, MappedField optionalExtraInfo) throws MappingException {
        if (fromDBObject == null) return null;
        return new BigDecimal(fromDBObject.toString());
    }
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-services-morphia/src/main/java/com/acmeair/morphia/BigDecimalConverter.java:BigDecimalConverter.<init>
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


// Node: getConnectionManager
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


package com.acmeair.morphia.services.util;

import java.io.IOException;
import java.net.URL;
import java.net.UnknownHostException;
import java.util.Properties;
import java.util.concurrent.atomic.AtomicReference;
import java.util.logging.Logger;

import javax.annotation.Resource;
import javax.naming.InitialContext;
import javax.naming.NamingException;

import com.acmeair.morphia.BigDecimalConverter;
import com.acmeair.morphia.MorphiaConstants;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.JSONValue;
import org.mongodb.morphia.Datastore;
import org.mongodb.morphia.Morphia;

import com.mongodb.DB;
import com.mongodb.MongoClient;
import com.mongodb.MongoClientOptions;
import com.mongodb.MongoClientURI;
import com.mongodb.ServerAddress;
import com.mongodb.WriteConcern;

public class MongoConnectionManager implements MorphiaConstants{

	private static AtomicReference<MongoConnectionManager> connectionManager = new AtomicReference<MongoConnectionManager>();
	
	private final static Logger logger = Logger.getLogger(MongoConnectionManager.class.getName());
	
	@Resource(name = JNDI_NAME)
	protected DB db;
	private static Datastore datastore;
	
	public static MongoConnectionManager getConnectionManager() {
		if (connectionManager.get() == null) {
			synchronized (connectionManager) {
				if (connectionManager.get() == null) {
					connectionManager.set(new MongoConnectionManager());
				}
			}
		}
		return connectionManager.get();
	}
	
	
	private MongoConnectionManager (){

		Morphia morphia = new Morphia();
		// Set default client options, and then check if there is a properties file.
		boolean fsync = false;
		int w = 0;
		int connectionsPerHost = 5;
		int threadsAllowedToBlockForConnectionMultiplier = 10;
		int connectTimeout= 0;
		int socketTimeout= 0;
		boolean socketKeepAlive = true;
		int maxWaitTime = 2000;


		Properties prop = new Properties();
		URL mongoPropertyFile = MongoConnectionManager.class.getResource("/com/acmeair/morphia/services/util/mongo.properties");
		if(mongoPropertyFile != null){
			try {
				logger.info("Reading mongo.properties file");
				prop.load(mongoPropertyFile.openStream());
				fsync = new Boolean(prop.getProperty("mongo.fsync"));
				w = new Integer(prop.getProperty("mongo.w"));
				connectionsPerHost = new Integer(prop.getProperty("mongo.connectionsPerHost"));
				threadsAllowedToBlockForConnectionMultiplier = new Integer(prop.getProperty("mongo.threadsAllowedToBlockForConnectionMultiplier"));
				connectTimeout= new Integer(prop.getProperty("mongo.connectTimeout"));
				socketTimeout= new Integer(prop.getProperty("mongo.socketTimeout"));
				socketKeepAlive = new Boolean(prop.getProperty("mongo.socketKeepAlive"));
				maxWaitTime =new Integer(prop.getProperty("mongo.maxWaitTime"));
			}catch (IOException ioe){
				logger.severe("Exception when trying to read from the mongo.properties file" + ioe.getMessage());
			}
		}
		
		// Set the client options
		MongoClientOptions.Builder builder = new MongoClientOptions.Builder()
			.writeConcern(new WriteConcern(w, 0, fsync))
			.connectionsPerHost(connectionsPerHost)
			.connectTimeout(connectTimeout)
			.socketTimeout(socketTimeout)
			.socketKeepAlive(socketKeepAlive)
			.maxWaitTime(maxWaitTime)
			.threadsAllowedToBlockForConnectionMultiplier(threadsAllowedToBlockForConnectionMultiplier);

				
		try {
			//Check if VCAP_SERVICES exist, and if it does, look up the url from the credentials.
			String vcapJSONString = System.getenv("VCAP_SERVICES");
			if (vcapJSONString != null) {
				logger.info("Reading VCAP_SERVICES");
				Object jsonObject = JSONValue.parse(vcapJSONString);
				JSONObject vcapServices = (JSONObject)jsonObject;
				JSONArray mongoServiceArray =null;					
				for (Object key : vcapServices.keySet()){
					if (key.toString().startsWith("mongo")){
						mongoServiceArray = (JSONArray) vcapServices.get(key);
						break;
					}
				}
				
				if (mongoServiceArray == null) {
					logger.severe("VCAP_SERVICES existed, but a mongo service was not definied.");
				} else {					
					JSONObject mongoService = (JSONObject)mongoServiceArray.get(0); 
					JSONObject credentials = (JSONObject)mongoService.get("credentials");
					String url = (String) credentials.get("url");
					logger.fine("service url = " + url);				
					MongoClientURI mongoURI = new MongoClientURI(url, builder);
					MongoClient mongo = new MongoClient(mongoURI);

					morphia.getMapper().getConverters().addConverter(new BigDecimalConverter());
					datastore = morphia.createDatastore( mongo ,mongoURI.getDatabase());
				}	

			} else {
				//VCAP_SERVICES don't exist, so use the DB resource  
				logger.fine("No VCAP_SERVICES found");
				if(db == null){
					try {
						logger.warning("Resource Injection failed. Attempting to look up " + JNDI_NAME + " via JNDI.");
						db = (DB) new InitialContext().lookup(JNDI_NAME);
					} catch (NamingException e) {
						logger.severe("Caught NamingException : " + e.getMessage() );
					}	        
				}

				if(db == null){
					String host; 
					String port;
					String database;
					logger.info("Creating the MongoDB Client connection. Looking up host and port information " );
					try {	        	
						host = (String) new InitialContext().lookup("java:comp/env/" + HOSTNAME);
						port = (String) new InitialContext().lookup("java:comp/env/" + PORT);
						database = (String) new InitialContext().lookup("java:comp/env/" + DATABASE);
						ServerAddress server = new ServerAddress(host, Integer.parseInt(port));
						MongoClient mongo = new MongoClient(server);
						db = mongo.getDB(database);
					} catch (NamingException e) {
						logger.severe("Caught NamingException : " + e.getMessage() );			
					} catch (Exception e) {
						logger.severe("Caught Exception : " + e.getMessage() );
					}
				}

				if(db == null){
					logger.severe("Unable to retreive reference to database, please check the server logs.");
				} else {
					
					morphia.getMapper().getConverters().addConverter(new BigDecimalConverter());
					datastore = morphia.createDatastore(new MongoClient(db.getMongo().getConnectPoint(),builder.build()), db.getName());
				}
			}
		} catch (UnknownHostException e) {
			logger.severe("Caught Exception : " + e.getMessage() );				
		}			

		logger.info("created mongo datastore with options:"+datastore.getMongo().getMongoClientOptions());
	}
	
	public DB getDB(){
		return db;
	}
	
	public Datastore getDatastore(){
		return datastore;
	}
	
	@SuppressWarnings("deprecation")
	public String getDriverVersion(){
		return datastore.getMongo().getVersion();
	}
	
	public String getMongoVersion(){
		return datastore.getDB().command("buildInfo").getString("version");
	}
}


// Node: synchronized
// Node: MongoConnectionManager
// Node: getMessage
// Node: connectTimeout
// Node: socketTimeout
// Node: socketKeepAlive
// Node: maxWaitTime
// Node: startsWith
// Node: warning
// Node: ServerAddress
// Node: getConnectPoint
// Node: getDriverVersion
// Node: getVersion
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


// Node: ServiceLocator
// Node: updateService
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
package com.acmeair.reporter;

import java.io.File;
import java.io.FileWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.apache.velocity.Template;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.VelocityEngine;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.runtime.resource.loader.ClasspathResourceLoader;
import org.apache.velocity.tools.generic.ComparisonDateTool;
import org.apache.velocity.tools.generic.MathTool;
import org.apache.velocity.tools.generic.NumberTool;

import com.acmeair.reporter.util.Messages;
import com.acmeair.reporter.util.StatResult;
import com.acmeair.reporter.parser.IndividualChartResults;
import com.acmeair.reporter.parser.ResultParser;
import com.acmeair.reporter.parser.ResultParserHelper;
import com.acmeair.reporter.parser.component.JmeterJTLParser;
import com.acmeair.reporter.parser.component.JmeterSummariserParser;
import com.acmeair.reporter.parser.component.JtlTotals;
import com.acmeair.reporter.parser.component.NmonParser;

//import freemarker.cache.ClassTemplateLoader;
//import freemarker.template.Configuration;
//import freemarker.template.Template;

public class ReportGenerator {
	private static final int max_lines = 15;
			 
	private static final String RESULTS_FILE = Messages.getString("ReportGenerator.RESULT_FILE_NAME");    	
	private static String searchingLocation = Messages.getString("inputDirectory"); 
	private static String jmeterFileName = Messages.getString("ReportGenerator.DEFAULT_JMETER_FILENAME"); 
	private static String nmonFileName = Messages.getString("ReportGenerator.DEFAULT_NMON_FILE_NAME"); 
	
	private static final String BOOK_FLIGHT = "BookFlight";
	private static final String CANCEL_BOOKING = "Cancel Booking";
	private static final String LOGIN = "Login";
	private static final String LOGOUT = "logout";	
	private static final String LIST_BOOKINGS = "List Bookings";
	private static final String QUERY_FLIGHT = "QueryFlight";
	private static final String UPDATE_CUSTOMER = "Update Customer";
	private static final String VIEW_PROFILE = "View Profile Information";
	
	
	private LinkedHashMap<String,ArrayList<String>> charMap = new LinkedHashMap<String,ArrayList<String>>();
	
	public static void main(String[] args) {
		if (args.length == 1) {
			searchingLocation = (args[0]);
		}
		if (!new File(searchingLocation).isDirectory()) {
			System.out.println("\"" + searchingLocation + "\" is not a valid directory");
			return;
		}
		System.out.println("Parsing acme air test results in the location \"" + searchingLocation + "\""); 
		
		ReportGenerator generator = new ReportGenerator();
		long start, stop;
		start = System.currentTimeMillis();
		generator.process();
		stop = System.currentTimeMillis();
		System.out.println("Results generated in " + (stop - start)/1000.0 + " seconds");
	}

	public void process() {
		long start, stop;
		String overallChartTitle = Messages.getString("ReportGenerator.THROUGHPUT_TOTAL_LABEL"); 
		String throughputChartTitle = Messages.getString("ReportGenerator.THROUGHPUT_TITLE"); 
		String yAxisLabel = Messages.getString("ReportGenerator.THROUGHPUT_YAXIS_LABEL");
		Map<String, Object> input = new HashMap<String, Object>();	
		start = System.currentTimeMillis();
		JmeterSummariserParser jmeterParser = new JmeterSummariserParser();
		jmeterParser.setFileName(jmeterFileName);
		jmeterParser.setMultipleChartTitle(throughputChartTitle);
		jmeterParser.setMultipleYAxisLabel(yAxisLabel);
		jmeterParser.processDirectory(searchingLocation);
		//always call it before call generating multiple chart string		
		String url = jmeterParser.generateChartStrings(overallChartTitle, yAxisLabel,
				"", jmeterParser.processData(jmeterParser.getAllInputList(), true),
				ResultParserHelper.scaleDown(jmeterParser.getAllTimeList(), 3), false);
		ArrayList<String> list = new ArrayList<String>();		
		list.add(url);
		charMap.put(overallChartTitle, list);
		generateMulitpleLinesChart(jmeterParser);
		
		charMap.put(throughputChartTitle, jmeterParser.getCharStrings());
		
		StatResult jmeterStats = StatResult.getStatistics(jmeterParser.getAllInputList());
    	input.put("jmeterStats", jmeterStats);
    	if(!jmeterParser.getAllTimeList().isEmpty()){
    		input.put("testStart", jmeterParser.getTestDate() + " " + jmeterParser.getAllTimeList().get(0));
    		input.put("testEnd", jmeterParser.getTestDate() + " " + jmeterParser.getAllTimeList().get(jmeterParser.getAllTimeList().size()-1));
    	}
		
    	input.put("charUrlMap", charMap);
		
		stop = System.currentTimeMillis();
		System.out.println("Parsed jmeter in " + (stop - start)/1000.0 + " seconds");
		
		start = System.currentTimeMillis();
		JmeterJTLParser jtlParser = new JmeterJTLParser();
		jtlParser.processResultsDirectory(searchingLocation);
		
    	input.put("totals", jtlParser.getResults());
    	String urls[] = {BOOK_FLIGHT,CANCEL_BOOKING,LOGIN,LOGOUT,LIST_BOOKINGS,QUERY_FLIGHT,UPDATE_CUSTOMER,VIEW_PROFILE,"Authorization"};

    	input.put("totalUrlMap" ,reorderTestcases(jtlParser.getResultsByUrl(), urls));	      
    	input.put("queryTotals", getTotals(QUERY_FLIGHT, jtlParser.getResultsByUrl()));
    	input.put("bookingTotals", getTotals(BOOK_FLIGHT, jtlParser.getResultsByUrl()));
    	input.put("loginTotals", getTotals(LOGIN, jtlParser.getResultsByUrl()));

		stop = System.currentTimeMillis();
		System.out.println("Parsed jmeter jtl files in " + (stop - start)/1000.0 + " seconds");



    	List<Object> nmonParsers = Messages.getConfiguration().getList("parsers.nmonParser.directory");
    	if (nmonParsers != null){
        	LinkedHashMap<String,StatResult> cpuList = new LinkedHashMap<String,StatResult>();
    		start = System.currentTimeMillis();
    		for(int i = 0;i < nmonParsers.size(); i++) {
    			
    			String enabled = Messages.getString("parsers.nmonParser("+i+")[@enabled]");			
    			if (enabled == null ||  !enabled.equalsIgnoreCase("false")) {

    				String directory = Messages.getString("parsers.nmonParser("+i+").directory");    				
    				String chartTitle = Messages.getString("parsers.nmonParser("+i+").chartTitle");
    				String label = Messages.getString("parsers.nmonParser("+i+").label");
    				String fileName = Messages.getString("parsers.nmonParser("+i+").fileName");    				
    				String relativePath = Messages.getString("parsers.nmonParser("+i+").directory[@relative]");
    				
    				if (relativePath == null ||  !relativePath.equalsIgnoreCase("false")) {
    					directory = searchingLocation +"/" + directory;
    				} 
    				if (fileName == null){
    					fileName = nmonFileName;
    				}

    				NmonParser nmon = parseNmonDirectory(directory, fileName, chartTitle);
    				cpuList  = addCpuStats(nmon, label, cpuList);
    			}
    		}
 
    		input.put("cpuList", cpuList);

    		stop = System.currentTimeMillis();
    		System.out.println("Parsed nmon files in " + (stop - start)/1000.0 + " seconds");
       	}				
		
		
		if (charMap.size() > 0) {
			start = System.currentTimeMillis();
			generateHtmlfile(input);
			stop = System.currentTimeMillis();
			System.out.println("Generated html file in " + (stop - start)/1000.0 + " seconds");
			System.out.println("Done, charts were saved to \""
							+ searchingLocation + System.getProperty("file.separator") + RESULTS_FILE + "\""); 
		} else {
			System.out.println("Failed, cannot find valid \"" 
							+ jmeterFileName + "\" or \"" + nmonFileName + "\" files in location " + searchingLocation); 
		}
	}
	
	private void generateMulitpleLinesChart(ResultParser parser) {
		if (parser.getResults().size()<=max_lines){
			parser.generateMultipleLinesCharString(parser.getMultipleChartTitle(),
				parser.getMultipleYAxisLabel(), "", parser.getResults());
		}else {
			System.out.println("More than "+max_lines+" throughput files found, will break them to "+max_lines+" each");
			ArrayList<IndividualChartResults> results= parser.getResults();
			int size = results.size();
			for (int i=0;i<size;i=i+max_lines){
				int endLocation = i+max_lines;
				if (endLocation >size) {
					endLocation=size;
				}
				parser.generateMultipleLinesCharString(parser.getMultipleChartTitle(),
						parser.getMultipleYAxisLabel(), "", results.subList(i,endLocation)); 
			}
		}
	}
	    

    
    private ArrayList<Double> getCombinedResultsList (NmonParser parser){
		Iterator<IndividualChartResults> itr = parser.getMultipleChartResults().getResults().iterator();
        ArrayList<Double> resultList = new ArrayList<Double>();
		while(itr.hasNext()){
			//trim trailing idle times from each of the individual results,
			//then combine the results together to get the final tallies. 				
			ArrayList<Double>  curList = itr.next().getInputList();
			
			for(int j = curList.size() - 1; j >= 0; j--){
				  if (curList.get(j).doubleValue() < 1){
					  curList.remove(j);
				  }
			}
			resultList.addAll(curList);
		}
		return resultList;
    }
   /* 
    private void generateHtmlfile(Map<String, Object> input) {	   
	    try{
	    	Configuration cfg = new Configuration();
	    	ClassTemplateLoader ctl = new ClassTemplateLoader(getClass(), "/templates");
	    	cfg.setTemplateLoader(ctl);	    	
	    	Template template = cfg.getTemplate("acmeair-report.ftl");
	    	
	    	Writer file = new FileWriter(new File(searchingLocation
					+ System.getProperty("file.separator") + RESULTS_FILE));
	    	template.process(input, file);
	    	file.flush();
	    	file.close();
	      
	    }catch(Exception e){
	    	e.printStackTrace();
	    }
    }
    
    */
    
    
    private void generateHtmlfile(Map<String, Object> input) {	   
	    try{
	    	VelocityEngine ve = new VelocityEngine();
	    	ve.setProperty(RuntimeConstants.RESOURCE_LOADER, "classpath");
	    	ve.setProperty("classpath.resource.loader.class",ClasspathResourceLoader.class.getName());
	    	ve.init();
	    	Template template = ve.getTemplate("templates/acmeair-report.vtl");
	    	VelocityContext context = new VelocityContext();
	    	 	    
	    	 
	    	for(Map.Entry<String, Object> entry: input.entrySet()){
	    		context.put(entry.getKey(), entry.getValue());
	    	}
	    	context.put("math", new MathTool());
	    	context.put("number", new NumberTool());
	    	context.put("date", new ComparisonDateTool());
	    	
	    	Writer file = new FileWriter(new File(searchingLocation
					+ System.getProperty("file.separator") + RESULTS_FILE));	    
	    	template.merge( context, file );
	    	file.flush();
	    	file.close();
	      
	    }catch(Exception e){
	    	e.printStackTrace();
	    }
    }

    private LinkedHashMap<String,StatResult> addCpuStats(NmonParser parser, String label, LinkedHashMap<String,StatResult> toAdd){
    	if (parser != null) {				
    		StatResult cpuStats = StatResult.getStatistics(getCombinedResultsList(parser));
    		cpuStats.setNumberOfResults(parser.getMultipleChartResults().getResults().size());
    		toAdd.put(label, cpuStats);			
    	}else {
    		System.out.println("no "+label+" cpu data found");
    	}
    	return toAdd;
    }
    
    
    /**
     * Re-orders a given map to using an array of Strings. 
     * Any remaining items in the map that was passed in will be appended to the end of
     * the map to be returned. 
     * @param totalUrlMap the map to be re-ordered. 
     * @param urls An array of Strings with the desired order for the map keys.
     * @return     A LinkedHashMap with the keys in the order requested. 
     * @see LinkedHashMap
     */
    private Map<String,JtlTotals> reorderTestcases(Map<String,JtlTotals> totalUrlMap, String urls[]){
    	LinkedHashMap<String,JtlTotals> newMap = new LinkedHashMap<String,JtlTotals>();
    	
    	Iterator<String> keys;
		for(int i=0; i< urls.length;i++){
			keys  = totalUrlMap.keySet().iterator();
			while (keys.hasNext()) {
				String key = keys.next();		        	      
	        	if(key.toLowerCase().contains(urls[i].toLowerCase())){
	        		newMap.put(key, totalUrlMap.get(key));	        		
	        	}			        	
	        }
		}
		//loop 2nd time to get the remaining items
		keys  = totalUrlMap.keySet().iterator();
		while (keys.hasNext()) {
	        String key = keys.next();
	        boolean found = false;		        
	        for(int i=0; i< urls.length;i++){
	        	if(key.toLowerCase().contains(urls[i].toLowerCase())){
	        		found = true;	
	        	}
	        }
	        if(!found){
	        	newMap.put(key, totalUrlMap.get(key));	        	
        	}
		}		
    	return newMap;
    }
  
    /**
     * Searches the map for the given jmeter testcase url key. 
     * The passed in string is expected to contain all or part of the desired key. 
     * for example "QueryFlight"  could match both "Mobile QueryFlight" and "Desktop QueryFlight" or just "QueryFlight".
     * If multiple results are found, their totals are added togehter in the JtlTotals Object returned. 
     * 
     * @param url         String, jMeter Testcase URL string to search for. 
     * @param totalUrlMap Map containing Strings and JtlTotals results. 
     * @return   JtlTotals object. 
     * @see JtlTotals
     */
    private JtlTotals getTotals(String url, Map<String,JtlTotals> totalUrlMap){
    	JtlTotals urlTotals = null;
    	Iterator<String> keys  = totalUrlMap.keySet().iterator();

    	while (keys.hasNext()) {
    		String key = keys.next();
    		if(key.toLowerCase().contains(url.toLowerCase())){

    			if(urlTotals == null){
    				urlTotals = totalUrlMap.get(key);
    			}else {
    				urlTotals.add(totalUrlMap.get(key));
    			}
    		}
    	}
    	return urlTotals;
    }

	
	/**
	 * Sets up a new NmonParser Object for parsing a given directory.
	 * @param directory   directory to search for nmon files.
	 * @param chartTitle  Name of the title for the chart to be generated. 
	 * @return            NmonParser object
	 */
	private NmonParser parseNmonDirectory (String directory, String fileName, String chartTitle ){	
		if (!new File(directory).isDirectory()) {
			return null;
		}		
		NmonParser parser = new NmonParser();
		parser.setFileName(fileName);
		parser.setMultipleChartTitle(chartTitle);
		parser.processDirectory(directory);
		generateMulitpleLinesChart(parser);
		charMap.put(chartTitle, parser.getCharStrings());
		return parser;
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


// Node: getSessionManager
// Node: WXSSessionManager
// Node: setGridUsername
// Node: setGridPassword
// Node: setGridConnectString
// Node: setGridName
// Node: setMapSuffix
// Node: getDisableNearCacheNameString
// Node: getPartitionFieldNameString
// Node: getObjectGridManager
// Node: createObjectGridConfiguration
// Node: createPlugin
// Node: addPlugin
// Node: createBackingMapConfiguration
// Node: setNearCacheEnabled
// Node: addBackingMapConfiguration
// Node: getClientSecurityConfiguration
// Node: setSecurityEnabled
// Node: UserPasswordCredentialGenerator
// Node: setCredentialGenerator
// Node: connect
// Node: getObjectGrid
// Node: compareAndSet
// Node: ObjectGridRuntimeException
// Node: getMapSuffix
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


