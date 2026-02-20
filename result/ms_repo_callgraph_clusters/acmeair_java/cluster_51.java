// Cluster 51

// Node: getServices
// Node: parseInt
// Node: parseLong
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


// Node: getBeans
// Node: getBeanClass
// Node: getQualifiers
// Node: equalsIgnoreCase
// Node: annotationType
// Node: createCreationalContext
// Node: getReference
// Node: name
// Node: description
package com.acmeair.service;

import java.lang.annotation.Retention;
import java.lang.annotation.Target;

import javax.inject.Qualifier;
import static java.lang.annotation.ElementType.TYPE;
import static java.lang.annotation.ElementType.METHOD;
import static java.lang.annotation.ElementType.FIELD;
import static java.lang.annotation.ElementType.PARAMETER;
import static java.lang.annotation.RetentionPolicy.RUNTIME;


@Qualifier @Retention(RUNTIME) @Target({TYPE, METHOD, FIELD, PARAMETER})
public @interface DataService {
	String name() default "none";
	String description() default "none";

}


// Node: repos/cloned_ms_repos/acmeair/acmeair-services/src/main/java/com/acmeair/service/DataService.java:DataService.<init>
// Node: Retention
// Node: Target
// Node: getStatistics
// Node: isEmpty
// Node: doubleValue
package com.acmeair.reporter.util;

import java.util.ArrayList;

public class StatResult {
	public double min;
	public double max;
	public double average;
	public int count;
	public double sum;
	public double numberOfResults;
	public double getMin() {
		return min;
	}
	public void setMin(double min) {
		this.min = min;
	}
	public double getMax() {
		return max;
	}
	public void setMax(double max) {
		this.max = max;
	}
	public double getAverage() {
		return average;
	}
	public void setAverage(double average) {
		this.average = average;
	}
	public int getCount() {
		return count;
	}
	public void setCount(int count) {
		this.count = count;
	}
	public double getSum() {
		return sum;
	}
	public void setSum(double sum) {
		this.sum = sum;
	}
	public double getNumberOfResults() {
		return numberOfResults;
	}
	public void setNumberOfResults(double numberOfResults) {
		this.numberOfResults = numberOfResults;
	}
	
    public static StatResult getStatistics(ArrayList <Double> list){
    	StatResult result = new StatResult();
    	result.average = 0;
    	result.sum = 0;
        if (list.size()>1)
        result.min = list.get(1);
        result.max = 0;
        result.count  = 0;
		for (int i = 0; i< list.size();i++){
			double current = list.get(i).doubleValue();
			if(i > 0 && i < list.size()-1){
				result.sum += current;
				result.count ++;
				result.min = Math.min(result.min, current);
				result.max = Math.max(result.max, current);
			}
		}
		if(result.count > 0 && result.sum > 0)
			result.average = (result.sum/result.count);
		return result;
    }
	
}


// Node: StatResult
// Node: min
// Node: max
// Node: group
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
package com.acmeair.reporter.parser.component;

import java.io.File;
import java.io.IOException;

import java.io.BufferedReader;

import java.io.FileReader;

import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;

import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.commons.io.FileUtils;
import org.apache.commons.io.filefilter.DirectoryFileFilter;
import org.apache.commons.io.filefilter.RegexFileFilter;

import com.acmeair.reporter.util.Messages;


public class JmeterJTLParser {
    
	private String jmeterJTLFileName = "AcmeAir[1-9].jtl";
	
    private String regEx =
        "<httpSample\\s*" + 
          "t=\"([^\"]*)\"\\s*"  +  
          "lt=\"([^\"]*)\"\\s*" +  
          "ts=\"([^\"]*)\"\\s*" +  
          "s=\"([^\"]*)\"\\s*"  +  
          "lb=\"([^\"]*)\"\\s*" +  
          "rc=\"([^\"]*)\"\\s*" +  
          "rm=\"([^\"]*)\"\\s*" +  
          "tn=\"([^\"]*)\"\\s*" +  
          "dt=\"([^\"]*)\"\\s*" +  
          "by=\"([^\"]*)\"\\s*" + 
          "FLIGHTTOCOUNT=\"([^\"]*)\"\\s*" +
          "FLIGHTRETCOUNT=\"([^\"]*)\"\\s*"+
          "ONEWAY\\s*=\"([^\"]*)\"\\s*";
    // NOTE: The regular expression depends on user.properties in jmeter having the sample_variables property added.
    //       sample_variables=FLIGHTTOCOUNT,FLIGHTRETCOUNT,ONEWAY
    

    private int GROUP_T  = 1;
    private int GROUP_TS = 3;
    private int GROUP_S  = 4;
    private int GROUP_LB = 5;
    private int GROUP_RC = 6;
    private int GROUP_TN = 8;
    private int GROUP_FLIGHTTOCOUNT = 11;
    private int GROUP_FLIGHTRETCOUNT = 12;
    private int GROUP_ONEWAY = 13;
        
    
    private  JtlTotals totalAll;
    private Map<String, JtlTotals> totalUrlMap;

    public JmeterJTLParser() {
    	totalAll = new JtlTotals();
    	totalUrlMap = new HashMap<String, JtlTotals>(); 
    	
       	String jtlRegularExpression = Messages.getString("parsers.JmeterJTLParser.jtlRegularExpression");
    	if (jtlRegularExpression != null){
    		System.out.println("set regex string to be '" + jtlRegularExpression+ "'");
    		regEx = jtlRegularExpression;
    	}
    	
      	String matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.t");
    	if (matcherGroup != null){
    		GROUP_T = new Integer(matcherGroup).intValue();
    	}
    	
      	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.ts");
    	if (matcherGroup != null){
    		GROUP_TS = new Integer(matcherGroup).intValue();
    	}
    	
      	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.s");
    	if (matcherGroup != null){
    		GROUP_S = new Integer(matcherGroup).intValue();
    	}   
    	
      	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.lb");
    	if (matcherGroup != null){
    		GROUP_LB = new Integer(matcherGroup).intValue();
    	}    	
    	
      	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.rc");
    	if (matcherGroup != null){
    		GROUP_RC = new Integer(matcherGroup).intValue();
    	}
    	
      	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.tn");
    	if (matcherGroup != null){
    		GROUP_TN = new Integer(matcherGroup).intValue();
    	}    
    	
      	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.FLIGHTTOCOUNT");
    	if (matcherGroup != null){
    		GROUP_FLIGHTTOCOUNT = new Integer(matcherGroup).intValue();
    	}
    	
     	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.FLIGHTRETCOUNT");
    	if (matcherGroup != null){
    		GROUP_FLIGHTRETCOUNT = new Integer(matcherGroup).intValue();
    	}    
    	
     	matcherGroup = Messages.getString("parsers.JmeterJTLParser.regexGroups.ONEWAY");
    	if (matcherGroup != null){
    		GROUP_ONEWAY = new Integer(matcherGroup).intValue();
    	}   
    	
      	String responseTimeStepping = Messages.getString("parsers.JmeterJTLParser.responseTimeStepping");
    	if (responseTimeStepping != null){
    		JtlTotals.setResponseTimeStepping(new Integer(responseTimeStepping).intValue());
    	}    	
    }

    
    public void setLogFileName (String logFileName) {
    	this.jmeterJTLFileName = logFileName;
    }
    
    
    public void processResultsDirectory(String dirName) {
    	File root = new File(dirName);
    	try {
    		Collection<File> files = FileUtils.listFiles(root,
    				new RegexFileFilter(jmeterJTLFileName),
    				DirectoryFileFilter.DIRECTORY);

    		for (Iterator<File> iterator = files.iterator(); iterator.hasNext();) {
    			File file = (File) iterator.next();
    			parse(file);
    		}
    	} catch (Exception e) {
    		e.printStackTrace();
    	}
    }

    
    public void parse(File jmeterJTLfile) throws IOException {
    	if(totalAll == null){
    		totalAll = new JtlTotals();
    		totalUrlMap = new HashMap<String, JtlTotals>(); 
    	}
    	totalAll.incrementFiles();
        Pattern pattern = Pattern.compile(regEx);
        HashMap <String, Integer> threadCounter = new HashMap<String, Integer>();
        
        BufferedReader reader = new BufferedReader(new FileReader(jmeterJTLfile));
        try {
            String line = reader.readLine();
            while(line != null) {
            	
                Matcher matcher = pattern.matcher(line);
                if(matcher.find()) {
                    add(matcher, totalAll);
                    
                    String url = matcher.group(GROUP_LB);
                    JtlTotals urlTotals = totalUrlMap.get(url);
                    if(urlTotals == null) {
                        urlTotals = new JtlTotals();                        
                        totalUrlMap.put(url, urlTotals);
                    }
                    add(matcher, urlTotals);
                    String threadName = matcher.group(GROUP_TN);
                    Integer threadCnt = threadCounter.get(threadName);
                    if(threadCnt == null) {
                    	threadCnt = new Integer(1);
                    }else{
                    	threadCnt = Integer.valueOf(threadCnt.intValue()+1);
                    }
                    threadCounter.put(threadName, threadCnt);
                }                
                line = reader.readLine();
            }
            
        } finally {
        	reader.close();
        }
        totalAll.setThreadMap(threadCounter);
        if(totalAll.getCount() == 0) {
            System.out.println("JmeterJTLParser - No results found!");
            return;
        }
    } 
    
    public JtlTotals getResults() {
    	return totalAll;
    }

    public Map<String, JtlTotals> getResultsByUrl() {
    	return totalUrlMap;
    }
    
    private void add(Matcher matcher, JtlTotals total) {
        
        long timestamp = Long.parseLong(matcher.group(GROUP_TS));
        total.addTimestamp(timestamp);
        
        int time = Integer.parseInt(matcher.group(GROUP_T));
        total.addTime(time);
                
        String rc = matcher.group(GROUP_RC);
        total.addReturnCode(rc);
              
        if(!matcher.group(GROUP_S).equalsIgnoreCase("true")) {
        	total.incrementFailures();
        }

        String strFlightCount = matcher.group(GROUP_FLIGHTTOCOUNT);
        if (strFlightCount != null && !strFlightCount.isEmpty()){  
        	int count = Integer.parseInt(strFlightCount);
        	total.addToFlight(count);        	
        }        

        strFlightCount = matcher.group(GROUP_FLIGHTRETCOUNT);
        if (strFlightCount != null && !strFlightCount.isEmpty()){
        	total.addFlightRetCount(Integer.parseInt(strFlightCount));
        }
        
        String oneWay = matcher.group(GROUP_ONEWAY);
        if (oneWay != null && oneWay.equalsIgnoreCase("true")){        	
        	total.incrementOneWayCount();
        }        
    } 
} 


// Node: addTimestamp
// Node: addTime
// Node: incrementFailures
// Node: addToFlight
// Node: addFlightRetCount
// Node: incrementOneWayCount
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
package com.acmeair.reporter.parser.component;

import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.Map.Entry;

public class JtlTotals {
    private static final String DECIMAL_PATTERN = "#,##0.0##";
    private static final double MILLIS_PER_SECOND = 1000.0;
    private static int millisPerBucket = 500;
    private int files = 0;
    private int request_count = 0;
    private int time_sum = 0;
    private int time_max = 0; 
    private int time_min = Integer.MAX_VALUE; 

    private int failures = 0;
    private long timestamp_start = Long.MAX_VALUE; 
    private long timestamp_end = 0;  
    private Map<String, Integer> rcMap = new HashMap<String, Integer>(); // key rc, value count
    private Map<Integer, Integer> millisMap = new TreeMap<Integer, Integer>(); // key bucket Integer, value count
    private Map <String, Integer> threadMap = new HashMap<String,Integer>(); 
    private ArrayList<Integer> timeList = new ArrayList<Integer>();
    private long flight_to_sum = 0;
    private long flight_to_count = 0;
	private int flight_to_empty_count = 0;    
    private long flight_ret_count = 0;
    private long one_way_count = 0;
    

    
    public JtlTotals() {
    }
    
    
    public void add(JtlTotals totals){
      rcMap.putAll(totals.getReturnCodeCounts());
      millisMap.putAll(totals.getMillisMap());
      threadMap.putAll(totals.getThreadMap());
      one_way_count += totals.getOneWayCount();
      flight_ret_count += totals.getFlightRetCount();
      flight_to_empty_count += totals.getEmptyToFlightCount();
      flight_to_sum += totals.getFlightToSum();
      flight_to_count += totals.getFlightToCount();
      failures += totals.getFailures();
      request_count += totals.getCount();  
    }
    
    public long getFlightToCount() {
		return flight_to_count;
	}
    
    public void addTime(int time){
    	request_count++;
    	time_sum+=time;
        time_max = Math.max(time_max, time);
        time_min = Math.min(time_min, time);
        timeList.add(time);
        Integer bucket = new Integer(time / millisPerBucket);
        Integer count = millisMap.get(bucket);
        if(count == null) {
            count = new Integer(0);
        }
        millisMap.put(bucket, new Integer(count.intValue() + 1));
    }
    
    public Map<Integer, Integer> getMillisMap() {
		return millisMap;
	}


	public void addReturnCode(String rc){
        Integer rc_count = rcMap.get(rc);
        if(rc_count == null) {
            rc_count = new Integer(0);
        }
        rcMap.put(rc, new Integer(rc_count.intValue() + 1));    
    }
    
    public void setThreadMap(Map<String,Integer> threadMap){
    	this.threadMap = threadMap;
    }
    
    public void addTimestamp(long timestamp){
    	timestamp_end = Math.max(timestamp_end, timestamp);
        timestamp_start = Math.min(timestamp_start, timestamp);
    }
    
    public void incrementFailures(){
    	failures++;
    }
    
    public void addToFlight(int count){
    	this.flight_to_count++;
    	this.flight_to_sum += count;
    	if(count == 0)
    		this.flight_to_empty_count++;	
    }
      
    public void addFlightRetCount(int count){
    	this.flight_ret_count += count;
    }
    
    public void incrementOneWayCount(){
    	one_way_count++;
    }
    
    public void incrementFiles(){
    	files++;
    }
    
    public int getFilesCount(){
    	return files;
    }
    
    public int getCount(){
    	return request_count;
    }
    
    public Map<String,Integer> getThreadMap(){
    	return this.threadMap;
    }
    
    public int getAverageResponseTime(){
    	//in case .jtl file doesn't exist, request_count could be 0
    	//adding this condition to avoid "divide by zero" runtime exception
    	if (request_count==0) {
    		return time_sum;
    	}
    	return  (time_sum/request_count);
    }

    public int getMaxResponseTime(){
    	return time_max;
    }

    public int getMinResponseTime(){
    	return time_min;
    }
    public int getFailures(){
    	return failures;
    }
    public int get90thPrecentile(){
    	if(timeList.isEmpty()){
    		return  Integer.MAX_VALUE; 
    	}
    	int target = (int)Math.round(timeList.size() * .90 );
    	Collections.sort(timeList); 
    	if(target == timeList.size()){target--;}    	
    	return timeList.get(target);
    }    

    public Map<String, Integer> getReturnCodeCounts(){
    	return rcMap;
    }

    public long getElapsedTimeInSeconds(){
        double secondsElaspsed = (timestamp_end - timestamp_start) / MILLIS_PER_SECOND;
        return Math.round(secondsElaspsed);
    }
    
    public long getRequestsPerSecond (){      
        return  Math.round(request_count / getElapsedTimeInSeconds());
    }
    
    public long getFlightToSum(){
    	return flight_to_sum;
    }

    public long getEmptyToFlightCount(){
    	return flight_to_empty_count;
    }    

    public float getAverageToFlights(){
    	return (float)flight_to_sum/flight_to_count;
    }
    
    public long getFlightRetCount(){
    	return flight_ret_count;
    }
    
    public long getOneWayCount(){
    	return one_way_count;
    }
    
    public static void setResponseTimeStepping(int milliseconds){
    	millisPerBucket = milliseconds;
    }
    
    public static int getResponseTimeStepping(){
    	return millisPerBucket;
    }
    
    public String cntByTimeString() {
        DecimalFormat df = new DecimalFormat(DECIMAL_PATTERN);
        List<String> millisStr = new LinkedList<String>();
        
        Iterator <Entry<Integer,Integer>>iter = millisMap.entrySet().iterator();
        while(iter.hasNext()) {
            Entry<Integer,Integer> millisEntry = iter.next();
            Integer bucket = (Integer)millisEntry.getKey();
            Integer bucketCount = (Integer)millisEntry.getValue();
            
            int minMillis = bucket.intValue() * millisPerBucket;
            int maxMillis = (bucket.intValue() + 1) * millisPerBucket;
            
            millisStr.add(
              df.format(minMillis/MILLIS_PER_SECOND)+" s "+
              "- "+
              df.format(maxMillis/MILLIS_PER_SECOND)+" s "+
              "= " + bucketCount);
        }
        return millisStr.toString();
    }
    
    public HashMap<String, Integer> cntByTime() {
        DecimalFormat df = new DecimalFormat(DECIMAL_PATTERN);     
        LinkedHashMap<String, Integer> millisStr = new LinkedHashMap<String, Integer>(); 
        Iterator <Entry<Integer,Integer>>iter = millisMap.entrySet().iterator();
        while(iter.hasNext()) {
            Entry<Integer,Integer> millisEntry = iter.next();
            Integer bucket = (Integer)millisEntry.getKey();
            Integer bucketCount = (Integer)millisEntry.getValue();
            
            int minMillis = bucket.intValue() * millisPerBucket;
            int maxMillis = (bucket.intValue() + 1) * millisPerBucket;
            
            millisStr.put(
              df.format(minMillis/MILLIS_PER_SECOND)+" s "+
              "- "+
              df.format(maxMillis/MILLIS_PER_SECOND)+" s "
              , bucketCount);
        }
        return millisStr;
    }
}


// Node: get90thPrecentile
// Node: round
// Node: sort
// Node: getElapsedTimeInSeconds
// Node: getRequestsPerSecond
