// Cluster 61

// Node: trim
// Node: InputStreamReader
// Node: readLine
// Node: size
// Node: close
// Node: println
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


// Node: File
// Node: isDirectory
// Node: ReportGenerator
// Node: process
// Node: NmonParser
// Node: setFileName
// Node: setMultipleChartTitle
// Node: processDirectory
// Node: generateMulitpleLinesChart
// Node: getCharStrings
// Node: JmeterSummariserParser
// Node: setMultipleYAxisLabel
// Node: generateChartStrings
// Node: processData
// Node: scaleDown
// Node: getAllTimeList
// Node: getTestDate
// Node: JmeterJTLParser
// Node: processResultsDirectory
// Node: getResults
// Node: getResultsByUrl
// Node: getConfiguration
// Node: getList
// Node: nmonParser
// Node: parseNmonDirectory
// Node: addCpuStats
// Node: generateMultipleLinesCharString
// Node: getMultipleChartTitle
// Node: getMultipleYAxisLabel
// Node: subList
// Node: getCombinedResultsList
// Node: getMultipleChartResults
// Node: getInputList
// Node: setNumberOfResults
package com.acmeair.reporter.util;

import java.util.MissingResourceException;
import java.util.ResourceBundle;

import org.apache.commons.configuration.CompositeConfiguration;
import org.apache.commons.configuration.Configuration;
import org.apache.commons.configuration.PropertiesConfiguration;
import org.apache.commons.configuration.SystemConfiguration;
import org.apache.commons.configuration.XMLConfiguration;

public class Messages {
	static ResourceBundle RESOURCE_BUNDLE;
	
	static CompositeConfiguration config;

	static {
			
		try {
			config = new CompositeConfiguration();
			config.addConfiguration(new SystemConfiguration());
			config.addConfiguration(new PropertiesConfiguration("messages.properties"));
			config.addConfiguration(new XMLConfiguration("config.xml"));

		} catch (Exception e) {
			System.out.println(e);
		}
	}

	private Messages() {
	}

	public static String getString(String key) {
		try {
			return config.getString(key);
		} catch (MissingResourceException e) {
			return '!' + key + '!';
		}
	}
	
	public static Configuration getConfiguration(){
		return config;
	}
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-reporter/src/main/java/com/acmeair/reporter/util/Messages.java:Messages.<init>
// Node: CompositeConfiguration
// Node: addConfiguration
// Node: SystemConfiguration
// Node: PropertiesConfiguration
// Node: XMLConfiguration
// Node: Messages
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

public class MultipleChartResults {
	
	private String multipleChartTitle;
	private String multipleChartYAxisLabel;
	private ArrayList<IndividualChartResults> results = new  ArrayList<IndividualChartResults> ();
	private ArrayList<String> charStrings= new ArrayList<String>();
	
	public String getMultipleChartTitle() {
		return multipleChartTitle;
	}
	public void setMultipleChartTitle(String multipleChartTitle) {
		this.multipleChartTitle = multipleChartTitle;
	}
	public String getMultipleChartYAxisLabel() {
		return multipleChartYAxisLabel;
	}
	public void setMultipleChartYAxisLabel(String multipleChartYAxisLabel) {
		this.multipleChartYAxisLabel = multipleChartYAxisLabel;
	}

	public ArrayList<IndividualChartResults> getResults() {
		return results;
	}
	public void setResults(ArrayList<IndividualChartResults> results) {
		this.results = results;
	}
		
	public ArrayList<String> getCharStrings() {
		return charStrings;
	}
	public void setCharStrings(ArrayList<String> charStrings) {
		this.charStrings = charStrings;
	}
}


// Node: getMultipleChartYAxisLabel
// Node: setMultipleChartYAxisLabel
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

public class IndividualChartResults {
	private ArrayList<Double> inputList = new ArrayList<Double>();
	private String title;
	private ArrayList<String> timeList = new ArrayList<String>();
	private int files = 0;
	
	public void setTitle(String title) {
		this.title = title;
	}
	public ArrayList<Double> getInputList() {
		return inputList;
	}
	public void setInputList(ArrayList<Double> inputList) {
		this.inputList = inputList;
	}
	public ArrayList<String> getTimeList() {
		return timeList;
	}
	public void setTimeList(ArrayList<String> timeList) {
		this.timeList = timeList;
	}
	
	public String getTitle() {
		return title;
	}
	
    public void incrementFiles(){
    	files++;
    }
    
    public int getFilesCount(){
    	return files;
    }
	
}


// Node: setTitle
// Node: setInputList
// Node: getTimeList
// Node: setTimeList
// Node: getTitle
// Node: incrementFiles
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


// Node: listFiles
// Node: RegexFileFilter
// Node: getFileName
// Node: processFile
// Node: newLine
// Node: newData
// Node: newColor
// Node: setLineStyle
// Node: newLineStyle
// Node: addShapeMarkers
// Node: newLineChart
// Node: addYAxisLabels
// Node: newNumericRangeAxisLabels
// Node: getScale_max
// Node: addXAxisLabels
// Node: newAxisLabels
// Node: generateDefaultChartSettings
// Node: newAxisStyle
// Node: setAxisStyle
// Node: setDataEncoding
// Node: setSize
// Node: setGrid
// Node: setBackgroundFill
// Node: newSolidFill
// Node: newLinearGradientFill
// Node: addColorAndOffset
// Node: setAreaFill
// Node: toURLString
// Node: processMultiLineData
// Node: getColor
// Node: getOverallScale_max
// Node: getData
// Node: IndividualChartResults
// Node: DataInputStream
// Node: BufferedReader
// Node: processLine
// Node: setAllTimeList
// Node: setScale_max
// Node: setOverallScale_max
// Node: scaleInputsData
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

import com.googlecode.charts4j.Color;

public class ResultParserHelper {

	public static Color getColor(int i) {
		Color[] colors = { Color.RED, Color.BLACK, Color.BLUE, Color.YELLOW,
				Color.GREEN, Color.ORANGE, Color.PINK, Color.SILVER,
				Color.GOLD, Color.WHITE, Color.BROWN, Color.CYAN,Color.GRAY,Color.HONEYDEW,Color.IVORY };
		return colors[i % 15];
	}

	public static <E> ArrayList<E> scaleDown(ArrayList<E> testList, int scaleDownFactor) {
		
		if (testList==null) {
			return null;
		}
		if (testList.size() <= 7)
			return testList;
		if (scaleDownFactor > 10 || scaleDownFactor < 0) {
			throw new RuntimeException(
					"currently only support factor from 0-10");
		}
		int listLastItemIndex = testList.size() - 1;
		int a = (int) java.lang.Math.pow(2, scaleDownFactor);
		if (a > listLastItemIndex) {
			return testList;
		}
		ArrayList<E> newList = new ArrayList<E>();
		newList.add(testList.get(0));
	
		if (scaleDownFactor == 0) {
			newList.add(testList.get(listLastItemIndex));
	
		} else {
	
			for (int m = 1; m <= a; m++) {
				newList.add(testList.get(listLastItemIndex * m / a));
			}
		}
		return newList;
	}

	public static double[] scaleInputsData(ArrayList<Double> inputList,
			double scale_factor) {
		double[] inputs = new double[inputList.size()];
		for (int i = 0; i <= inputList.size() - 1; i++) {
			inputs[i] = inputList.get(i) * scale_factor;
		}
		return inputs;
	}
}

// Node: pow
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

import com.acmeair.reporter.parser.IndividualChartResults;
import com.acmeair.reporter.parser.ResultParser;
import com.acmeair.reporter.parser.ResultParserHelper;

public class JmeterSummariserParser extends ResultParser {

	private static boolean SKIP_JMETER_DROPOUTS = false; 
	static {
		SKIP_JMETER_DROPOUTS = System.getProperty("SKIP_JMETER_DROPOUTS") != null;
	}
	
	private String jmeterFileName = "AcmeAir[1-9].log";	
	private String testDate = "";
	
	@Override
	protected void processFile(File file) {
		IndividualChartResults result= getData(file.getPath());		
		super.processData(ResultParserHelper.scaleDown(result.getInputList(),8),false);
		IndividualChartResults individualResults = new IndividualChartResults();
		if(result.getTitle() != null){
			individualResults.setTitle(result.getTitle());
		} else {
			individualResults.setTitle(file.getName());
		}
		individualResults.setInputList(ResultParserHelper.scaleDown(result.getInputList(),6));
		individualResults.setTimeList(ResultParserHelper.scaleDown(result.getTimeList(),3));
		super.getMultipleChartResults().getResults().add(individualResults);
	}

	@Override
	public String getFileName() {
		return jmeterFileName;
	}

	@Override
	public void setFileName(String fileName) {
		jmeterFileName = fileName;
	}

	public String getTestDate(){
		return testDate;
	}

	@Override
	protected void processLine(IndividualChartResults results, String strLine) {		
		if (strLine.indexOf("summary +") > 0) {			
			String[] tokens = strLine.split(" ");
			results.getTimeList().add(tokens[1].trim());
			testDate = tokens[0].trim();		
			int endposition = strLine.indexOf("/s");
			int startposition = strLine.indexOf("=");
			String thoughputS = strLine.substring(startposition + 1, endposition).trim();
			Double throughput = Double.parseDouble(thoughputS);
			if (throughput == 0.0 && SKIP_JMETER_DROPOUTS) {
				return;
			}
			results.getInputList().add(throughput);
		} else if (strLine.indexOf("Name:") > 0) {
			int startIndex = strLine.indexOf(" Name:")+7;
			int endIndex = strLine.indexOf(" ", startIndex);
			String name = strLine.substring(startIndex, endIndex);
			results.setTitle(name);
		}
	}
}

// Node: getPath
// Node: indexOf
// Node: split
// Node: substring
// Node: parseDouble
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


// Node: repos/cloned_ms_repos/acmeair/acmeair-reporter/src/main/java/com/acmeair/reporter/parser/component/JmeterJTLParser.java:JmeterJTLParser.<init>
// Node: JtlTotals
// Node: setResponseTimeStepping
// Node: compile
// Node: FileReader
// Node: matcher
// Node: setThreadMap
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

import com.acmeair.reporter.parser.IndividualChartResults;
import com.acmeair.reporter.parser.ResultParser;
import com.acmeair.reporter.parser.ResultParserHelper;


public class NmonParser extends ResultParser{

	private String nmonFileName = "output.nmon";
	
	public NmonParser(){
		super.setMultipleYAxisLabel("usr%+sys%"); //default label
	}
	
	@Override
	protected void processFile(File file) {
		IndividualChartResults result= getData(file.getPath());
		super.processData(ResultParserHelper.scaleDown(result.getInputList(),8),false);
		IndividualChartResults individualResults = new IndividualChartResults();

		individualResults.setTitle(result.getTitle());
		individualResults.setInputList(ResultParserHelper.scaleDown(result.getInputList(),6));
		individualResults.setTimeList(ResultParserHelper.scaleDown(result.getTimeList(),3));
		super.getMultipleChartResults().getResults().add(individualResults);
	}

	
	@Override
	public String getFileName() {
		return nmonFileName;
	}
	
	@Override
	public void setFileName(String fileName) {
		nmonFileName = fileName;
	}
	
	@Override
	protected void processLine(IndividualChartResults results, String strLine) {
		if(strLine.startsWith("AAA,host,")){
			String[] tokens = strLine.split(",");
			 results.setTitle(tokens[2].trim());			
		}
		
		if (strLine.indexOf("ZZZZ") >=0){
			String[] tokens = strLine.split(",");
			 results.getTimeList().add(tokens[2].trim());
		}
		
		if (strLine.indexOf("CPU_ALL") >=0 && strLine.indexOf("CPU Total")<0) {
			String[] tokens = strLine.split(",");
			String user = tokens[2].trim();
			String sys = tokens[3].trim();
			Double userDouble = Double.parseDouble(user);
			Double sysDouble = Double.parseDouble(sys);
			 results.getInputList().add(userDouble+sysDouble);		
		}
	}
}


// Node: repos/cloned_ms_repos/acmeair/acmeair-reporter/src/main/java/com/acmeair/reporter/parser/component/NmonParser.java:NmonParser.<init>
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


// Node: repos/cloned_ms_repos/acmeair/acmeair-reporter/src/main/java/com/acmeair/reporter/parser/component/JtlTotals.java:JtlTotals.<init>
