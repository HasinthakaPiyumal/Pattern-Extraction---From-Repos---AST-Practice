// Cluster 8

// Node: error
// Node: TradeDirect
// Node: checkDBProductName
// Node: println
// Node: run
// Node: toHTML
// Node: rndUserID
// Node: rndSymbol
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.util;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Random;

/**
 * TradeConfig is a JavaBean holding all configuration and runtime parameters
 * for the Trade application TradeConfig sets runtime parameters such as the
 * RunTimeMode (EJB, JDBC, EJB_ALT)
 *
 */

public class TradeConfig {

    /* Trade Runtime Configuration Parameters */

    /* Trade Runtime Mode parameters */
    public static String[] runTimeModeNames = { "Full EJB3", "Direct (JDBC)"};
    public static final int EJB3 = 0;
    public static final int DIRECT = 1;
    public static int runTimeMode = EJB3;

    public static String[] orderProcessingModeNames = { "Sync", "Async_2-Phase", "Async_ManagedThread" };
    public static final int SYNCH = 0;
    public static final int ASYNCH_2PHASE = 1;
    public static final int ASYNCH_MANAGEDTHREAD = 2;
    public static int orderProcessingMode = SYNCH;

    public static String[] accessModeNames = { "Standard", "WebServices" };
    public static final int STANDARD = 0;
    private static int accessMode = STANDARD;

    /* Trade Web Interface parameters */
    public static String[] webInterfaceNames = { "JSP", "JSP-Images" };
    public static final int JSP = 0;
    public static final int JSP_Images = 1;
    public static int webInterface = JSP;

    /* Trade Caching Type parameters 
    public static String[] cachingTypeNames = { "DistributedMap", "No Caching" };
    public static final int DISTRIBUTEDMAP = 0;
    public static final int NO_CACHING = 1;
    public static int cachingType = NO_CACHING;
    public static int distributedMapCacheSize = 100000;
    */

    /* Trade Database Scaling parameters */
    private static int MAX_USERS = 15000;
    private static int MAX_QUOTES = 10000;

    /* Trade Database specific paramters */
    public static String JDBC_UID = null;
    public static String JDBC_PWD = null;
    public static String DS_NAME = "java:comp/env/jdbc/TradeDataSource";

    /* Trade XA Datasource specific parameters */
    public static boolean JDBCDriverNeedsGlobalTransation = false;

    /* Trade Config Miscellaneous itmes */
    public static String DATASOURCE = "java:comp/env/jdbc/TradeDataSource";
    public static int KEYBLOCKSIZE = 1000;
    public static int QUOTES_PER_PAGE = 10;
    public static boolean RND_USER = true;
    // public static int RND_SEED = 0;
    private static int MAX_HOLDINGS = 10;
    private static int count = 0;
    private static Object userID_count_semaphore = new Object();
    private static int userID_count = 0;
    private static String hostName = null;
    private static Random r0 = new Random(System.currentTimeMillis());
    // private static Random r1 = new Random(RND_SEED);
    private static Random randomNumberGenerator = r0;
    public static final String newUserPrefix = "ru:";
    public static final int verifyPercent = 5;
    private static boolean trace = false;
    private static boolean actionTrace = false;
    private static boolean updateQuotePrices = true;
    private static int primIterations = 1;
    private static boolean longRun = true;
    private static boolean publishQuotePriceChange = true;
    private static int percentSentToWebsocket = 5;
    private static boolean displayOrderAlerts = true;
    private static boolean useRemoteEJBInterface = false;

    /**
     * -1 means every operation 0 means never perform a market summary > 0 means
     * number of seconds between summaries. These will be synchronized so only
     * one transaction in this period will create a summary and will cache its
     * results.
     */
    private static int marketSummaryInterval = 20;

    /*
     * Penny stocks is a problem where the random price change factor gets a
     * stock down to $.01. In this case trade jumpstarts the price back to $6.00
     * to keep the math interesting.
     */
    public static BigDecimal PENNY_STOCK_PRICE;
    public static BigDecimal PENNY_STOCK_RECOVERY_MIRACLE_MULTIPLIER;
    static {
        PENNY_STOCK_PRICE = new BigDecimal(0.01);
        PENNY_STOCK_PRICE = PENNY_STOCK_PRICE.setScale(2, BigDecimal.ROUND_HALF_UP);
        PENNY_STOCK_RECOVERY_MIRACLE_MULTIPLIER = new BigDecimal(600.0);
        PENNY_STOCK_RECOVERY_MIRACLE_MULTIPLIER.setScale(2, BigDecimal.ROUND_HALF_UP);
    }

    /*
     * CJB (DAYTRADER-25) - Also need to impose a ceiling on the quote price to
     * ensure prevent account and holding balances from exceeding the databases
     * decimal precision. At some point, this maximum value can be used to
     * trigger a stock split.
     */

    public static BigDecimal MAXIMUM_STOCK_PRICE;
    public static BigDecimal MAXIMUM_STOCK_SPLIT_MULTIPLIER;
    static {
        MAXIMUM_STOCK_PRICE = new BigDecimal(400);
        MAXIMUM_STOCK_PRICE.setScale(2, BigDecimal.ROUND_HALF_UP);
        MAXIMUM_STOCK_SPLIT_MULTIPLIER = new BigDecimal(0.5);
        MAXIMUM_STOCK_SPLIT_MULTIPLIER.setScale(2, BigDecimal.ROUND_HALF_UP);
    }

    /*
     * Trade Scenario actions mixes. Each of the array rows represents a
     * specific Trade Scenario Mix. The columns give the percentages for each
     * action in the column header. Note: "login" is always 0. logout represents
     * both login and logout (because each logout operation will cause a new
     * login when the user context attempts the next action.
     */
    /* Trade Scenario Workload parameters */
    public static final int HOME_OP = 0;
    public static final int QUOTE_OP = 1;
    public static final int LOGIN_OP = 2;
    public static final int LOGOUT_OP = 3;
    public static final int REGISTER_OP = 4;
    public static final int ACCOUNT_OP = 5;
    public static final int PORTFOLIO_OP = 6;
    public static final int BUY_OP = 7;
    public static final int SELL_OP = 8;
    public static final int UPDATEACCOUNT_OP = 9;

    private static int[][] scenarioMixes = {
            // h q l o r a p b s u
            { 20, 40, 0, 4, 2, 10, 12, 4, 4, 4 }, // STANDARD
            { 20, 40, 0, 4, 2, 7, 7, 7, 7, 6 }, // High Volume
    };
    private static char[] actions = { 'h', 'q', 'l', 'o', 'r', 'a', 'p', 'b', 's', 'u' };
    private static int sellDeficit = 0;
    // Tracks the number of buys over sell when a users portfolio is empty
    // Used to maintain the correct ratio of buys/sells

    /* JSP pages for all Trade Actions */

    public static final int WELCOME_PAGE = 0;
    public static final int REGISTER_PAGE = 1;
    public static final int PORTFOLIO_PAGE = 2;
    public static final int QUOTE_PAGE = 3;
    public static final int HOME_PAGE = 4;
    public static final int ACCOUNT_PAGE = 5;
    public static final int ORDER_PAGE = 6;
    public static final int CONFIG_PAGE = 7;
    public static final int STATS_PAGE = 8;
    public static final int MARKET_SUMMARY_PAGE = 9;

    // FUTURE Add XML/XSL View
    public static String[][] webUI = {
            { "/welcome.jsp", "/register.jsp", "/portfolio.jsp", "/quote.jsp", "/tradehome.jsp", "/account.jsp", "/order.jsp", "/config.jsp", "/runStats.jsp",
                    "/marketSummary.jsp" },
            // JSP Interface
            { "/welcomeImg.jsp", "/registerImg.jsp", "/portfolioImg.jsp", "/quoteImg.jsp", "/tradehomeImg.jsp", "/accountImg.jsp", "/orderImg.jsp",
                    "/config.jsp", "/runStats.jsp", "/marketSummary.jsp" },
    // JSP Interface
    };

    // FUTURE:
    // If a "trade2.properties" property file is supplied, reset the default
    // values
    // to match those specified in the file. This provides a persistent runtime
    // property mechanism during server startup

    /**
     * Return the hostname for this system Creation date: (2/16/2000 9:02:25 PM)
     */

    private static String getHostname() {
        try {
            if (hostName == null) {
                hostName = java.net.InetAddress.getLocalHost().getHostName();
                // Strip of fully qualifed domain if necessary
                try {
                    hostName = hostName.substring(0, hostName.indexOf('.'));
                } catch (Exception e) {
                }
            }
        } catch (Exception e) {
            Log.error("Exception getting local host name using 'localhost' - ", e);
            hostName = "localhost";
        }
        return hostName;
    }

    /**
     * Return a Trade UI Web page based on the current configuration This may
     * return a JSP page or a Servlet page Creation date: (3/14/2000 9:08:34 PM)
     */

    public static String getPage(int pageNumber) {
        return webUI[webInterface][pageNumber];
    }

    /**
     * Return the list of run time mode names Creation date: (3/8/2000 5:58:34
     * PM)
     *
     * @return java.lang.String[]
     */
    public static java.lang.String[] getRunTimeModeNames() {
        return runTimeModeNames;
    }

    private static int scenarioCount = 0;

    /**
     * Return a Trade Scenario Operation based on the setting of the current mix
     * (TradeScenarioMix) Creation date: (2/10/2000 9:08:34 PM)
     */

    public static char getScenarioAction(boolean newUser) {
        int r = rndInt(100); // 0 to 99 = 100
        int i = 0;
        int sum = scenarioMixes[0][i];
        while (sum <= r) {
            i++;
            sum += scenarioMixes[0][i];
        }

        incrementScenarioCount();

        /*
         * In TradeScenarioServlet, if a sell action is selected, but the users
         * portfolio is empty, a buy is executed instead and sellDefecit is
         * incremented. This allows the number of buy/sell operations to stay in
         * sync w/ the given Trade mix.
         */

        if ((!newUser) && (actions[i] == 'b')) {
            synchronized (TradeConfig.class) {
                if (sellDeficit > 0) {
                    sellDeficit--;
                    return 's';
                    // Special case for TradeScenarioServlet to note this is a
                    // buy switched to a sell to fix sellDeficit
                }
            }
        }

        return actions[i];
    }

    public static String getUserID() {
        String userID;
        if (RND_USER) {
            userID = rndUserID();
        } else {
            userID = nextUserID();
        }
        return userID;
    }

    private static final BigDecimal orderFee = new BigDecimal("24.95");
    private static final BigDecimal cashFee = new BigDecimal("0.0");

    public static BigDecimal getOrderFee(String orderType) {
        if ((orderType.compareToIgnoreCase("BUY") == 0) || (orderType.compareToIgnoreCase("SELL") == 0)) {
            return orderFee;
        }

        return cashFee;

    }

    /**
     * Increment the sell deficit counter Creation date: (6/21/2000 11:33:45 AM)
     */
    public static synchronized void incrementSellDeficit() {
        sellDeficit++;
    }

    public static String nextUserID() {
        String userID;
        synchronized (userID_count_semaphore) {
            userID = "uid:" + userID_count;
            userID_count++;
            if (userID_count % MAX_USERS == 0) {
                userID_count = 0;
            }
        }
        return userID;
    }

    public static double random() {
        return randomNumberGenerator.nextDouble();
    }

    public static String rndAddress() {
        return rndInt(1000) + " Oak St.";
    }

    public static String rndBalance() {
        // Give all new users a cool mill in which to trade
        return "1000000";
    }

    public static String rndCreditCard() {
        return rndInt(100) + "-" + rndInt(1000) + "-" + rndInt(1000) + "-" + rndInt(1000);
    }

    public static String rndEmail(String userID) {
        return userID + "@" + rndInt(100) + ".com";
    }

    public static String rndFullName() {
        return "first:" + rndInt(1000) + " last:" + rndInt(5000);
    }

    public static int rndInt(int i) {
        return (new Float(random() * i)).intValue();
    }

    public static float rndFloat(int i) {
        return (new Float(random() * i)).floatValue();
    }

    public static BigDecimal rndBigDecimal(float f) {
        return (new BigDecimal(random() * f)).setScale(2, BigDecimal.ROUND_HALF_UP);
    }

    public static boolean rndBoolean() {
        return randomNumberGenerator.nextBoolean();
    }

    /**
     * Returns a new Trade user Creation date: (2/16/2000 8:50:35 PM)
     */
    public static synchronized String rndNewUserID() {

        return newUserPrefix + getHostname() + System.currentTimeMillis() + count++;
    }

    public static float rndPrice() {
        return ((new Integer(rndInt(200))).floatValue()) + 1.0f;
    }

    private static final BigDecimal ONE = new BigDecimal(1.0);
	
    public static BigDecimal getRandomPriceChangeFactor() {
        // CJB (DAYTRADER-25) - Vary change factor between 1.1 and 0.9
        double percentGain = rndFloat(1) * 0.1;
        if (random() < .5) {
            percentGain *= -1;
        }
        percentGain += 1;

        // change factor is between +/- 20%
        BigDecimal percentGainBD = (new BigDecimal(percentGain)).setScale(2, BigDecimal.ROUND_HALF_UP);
        if (percentGainBD.doubleValue() <= 0.0) {
            percentGainBD = ONE;
        }

        return percentGainBD;
    }

    public static float rndQuantity() {
        return ((new Integer(rndInt(200))).floatValue()) + 1.0f;
    }

    public static String rndSymbol() {
        return "s:" + rndInt(MAX_QUOTES - 1);
    }

    public static String rndSymbols() {

        String symbols = "";
        int num_symbols = rndInt(QUOTES_PER_PAGE);

        for (int i = 0; i <= num_symbols; i++) {
            symbols += "s:" + rndInt(MAX_QUOTES - 1);
            if (i < num_symbols) {
                symbols += ",";
            }
        }
        return symbols;
    }

    public static String rndUserID() {
        String nextUser = getNextUserIDFromDeck();
        if (Log.doTrace()) {
            Log.trace("TradeConfig:rndUserID -- new trader = " + nextUser);
        }

        return nextUser;
    }

    private static synchronized String getNextUserIDFromDeck() {
        int numUsers = getMAX_USERS();
        if (deck == null) {
            deck = new ArrayList<Integer>(numUsers);
            for (int i = 0; i < numUsers; i++) {
                deck.add(i, new Integer(i));
            }
            java.util.Collections.shuffle(deck, r0);
        }
        if (card >= numUsers) {
            card = 0;
        }
        return "uid:" + deck.get(card++);

    }

    // Trade implements a card deck approach to selecting
    // users for trading with tradescenarioservlet
    private static ArrayList<Integer> deck = null;
    private static int card = 0;
	
    /**
     * Set the list of run time mode names Creation date: (3/8/2000 5:58:34 PM)
     *
     * @param newRunTimeModeNames
     *            java.lang.String[]
     */
    public static void setRunTimeModeNames(java.lang.String[] newRunTimeModeNames) {
        runTimeModeNames = newRunTimeModeNames;
    }

    /**
     * This is a convenience method for servlets to set Trade configuration
     * parameters from servlet initialization parameters. The servlet provides
     * the init param and its value as strings. This method then parses the
     * parameter, converts the value to the correct type and sets the
     * corresponding TradeConfig parameter to the converted value
     *
     */
    public static void setConfigParam(String parm, String value) {
        Log.log("TradeConfig setting parameter: " + parm + "=" + value);
        // Compare the parm value to valid TradeConfig parameters that can be
        // set
        // by servlet initialization

        // First check the proposed new parm and value - if empty or null ignore
        // it
        if (parm == null) {
            return;
        }
        parm = parm.trim();
        if (parm.length() <= 0) {
            return;
        }
        if (value == null) {
            return;
        }
        value = value.trim();

        if (parm.equalsIgnoreCase("runTimeMode")) {
            try {
                for (int i = 0; i < runTimeModeNames.length; i++) {
                    if (value.equalsIgnoreCase(runTimeModeNames[i])) {
                        runTimeMode = i;
                        break;
                    }
                }
            } catch (Exception e) {
                // >>rjm
                Log.error("TradeConfig.setConfigParm(..): minor exception caught" + "trying to set runtimemode to " + value + "reverting to current value: "
                        + runTimeModeNames[runTimeMode], e);
            } // If the value is bad, simply revert to current
        } else if (parm.equalsIgnoreCase("orderProcessingMode")) {
            try {
                for (int i = 0; i < orderProcessingModeNames.length; i++) {
                    if (value.equalsIgnoreCase(orderProcessingModeNames[i])) {
                        orderProcessingMode = i;
                        break;
                    }
                }
            } catch (Exception e) {
                Log.error("TradeConfig.setConfigParm(..): minor exception caught" + "trying to set orderProcessingMode to " + value
                        + "reverting to current value: " + orderProcessingModeNames[orderProcessingMode], e);
            } // If the value is bad, simply revert to current
        } else if (parm.equalsIgnoreCase("accessMode")) {
            try {
                for (int i = 0; i < accessModeNames.length; i++) {
                    if (value.equalsIgnoreCase(accessModeNames[i])) {
                        accessMode = i;
                        break;
                    }
                }
            } catch (Exception e) {
                Log.error("TradeConfig.setConfigParm(..): minor exception caught" + "trying to set accessMode to " + value + "reverting to current value: "
                        + accessModeNames[accessMode], e);
            }
        } else if (parm.equalsIgnoreCase("WebInterface")) {
            try {
                for (int i = 0; i < webInterfaceNames.length; i++) {
                    if (value.equalsIgnoreCase(webInterfaceNames[i])) {
                        webInterface = i;
                        break;
                    }
                }
            } catch (Exception e) {
                Log.error("TradeConfig.setConfigParm(..): minor exception caught" + "trying to set WebInterface to " + value + "reverting to current value: "
                        + webInterfaceNames[webInterface], e);

            } // If the value is bad, simply revert to current
        } /*else if (parm.equalsIgnoreCase("CachingType")) {
            try {
                for (int i = 0; i < cachingTypeNames.length; i++) {
                    if (value.equalsIgnoreCase(cachingTypeNames[i])) {
                        cachingType = i;
                        break;
                    }
                }
            } catch (Exception e) {
                Log.error("TradeConfig.setConfigParm(..): minor exception caught" + "trying to set CachingType to " + value + "reverting to current value: "
                        + cachingTypeNames[cachingType], e);
            } // If the value is bad, simply revert to current
        }*/ else if (parm.equalsIgnoreCase("maxUsers")) {
            try {
                MAX_USERS = Integer.parseInt(value);
            } catch (Exception e) {
                Log.error("TradeConfig.setConfigParm(..): minor exception caught" + "Setting maxusers, error parsing string to int:" + value
                        + "revering to current value: " + MAX_USERS, e);
            } // On error, revert to saved
        } else if (parm.equalsIgnoreCase("maxQuotes")) {
            try {
                MAX_QUOTES = Integer.parseInt(value);
            } catch (Exception e) {
                // >>rjm
                Log.error("TradeConfig.setConfigParm(...) minor exception caught" + "Setting max_quotes, error parsing string to int " + value
                        + "reverting to current value: " + MAX_QUOTES, e);
                // <<rjm
            } // On error, revert to saved
        } else if (parm.equalsIgnoreCase("primIterations")) {
            try {
                primIterations = Integer.parseInt(value);
            } catch (Exception e) {
                Log.error("TradeConfig.setConfigParm(..): minor exception caught" + "Setting primIterations, error parsing string to int:" + value
                        + "revering to current value: " + primIterations, e);
            } // On error, revert to saved
        } /*else if (parm.equalsIgnoreCase("DistMapCacheSize")) {
            try {
                distributedMapCacheSize = Integer.parseInt(value);
            } catch (Exception e) {
                // >>rjm
                Log.error("TradeConfig.setConfigParm(...) minor exception caught" + "Setting distributedMapCacheSize, error parsing string" + value
                        + "reverting to current value: " + distributedMapCacheSize, e);
                // <<rjm
            } // On error, revert to saved
        }*/
    }

    /**
     * Gets the orderProcessingModeNames
     *
     * @return Returns a String[]
     */
    public static String[] getOrderProcessingModeNames() {
        return orderProcessingModeNames;
    }

    /**
     * Gets the webInterfaceNames
     *
     * @return Returns a String[]
     */
    public static String[] getWebInterfaceNames() {
        return webInterfaceNames;
    }

    /**
     * Gets the webInterfaceNames
     *
     * @return Returns a String[]
     */
    /*public static String[] getCachingTypeNames() {
        return cachingTypeNames;
    }*/

    /**
     * Gets the scenarioMixes
     *
     * @return Returns a int[][]
     */
    public static int[][] getScenarioMixes() {
        return scenarioMixes;
    }

    /**
     * Gets the trace
     *
     * @return Returns a boolean
     */
    public static boolean getTrace() {
        return trace;
    }

    /**
     * Sets the trace
     *
     * @param trace
     *            The trace to set
     */
    public static void setTrace(boolean traceValue) {
        trace = traceValue;
    }

    /**
     * Gets the mAX_USERS.
     *
     * @return Returns a int
     */
    public static int getMAX_USERS() {
        return MAX_USERS;
    }

    /**
     * Sets the mAX_USERS.
     *
     * @param mAX_USERS
     *            The mAX_USERS to set
     */
    public static void setMAX_USERS(int mAX_USERS) {
        MAX_USERS = mAX_USERS;
        deck = null; // reset the card deck for selecting users
    }

    /**
     * Gets the mAX_QUOTES.
     *
     * @return Returns a int
     */
    public static int getMAX_QUOTES() {
        return MAX_QUOTES;
    }

    /**
     * Sets the mAX_QUOTES.
     *
     * @param mAX_QUOTES
     *            The mAX_QUOTES to set
     */
    public static void setMAX_QUOTES(int mAX_QUOTES) {
        MAX_QUOTES = mAX_QUOTES;
    }

    /**
     * Gets the mAX_HOLDINGS.
     *
     * @return Returns a int
     */
    public static int getMAX_HOLDINGS() {
        return MAX_HOLDINGS;
    }

    /**
     * Sets the mAX_HOLDINGS.
     *
     * @param mAX_HOLDINGS
     *            The mAX_HOLDINGS to set
     */
    public static void setMAX_HOLDINGS(int mAX_HOLDINGS) {
        MAX_HOLDINGS = mAX_HOLDINGS;
    }

    /**
     * Gets the actionTrace.
     *
     * @return Returns a boolean
     */
    public static boolean getActionTrace() {
        return actionTrace;
    }

    /**
     * Sets the actionTrace.
     *
     * @param actionTrace
     *            The actionTrace to set
     */
    public static void setActionTrace(boolean actionTrace) {
        TradeConfig.actionTrace = actionTrace;
    }

    /**
     * Gets the scenarioCount.
     *
     * @return Returns a int
     */
    public static int getScenarioCount() {
        return scenarioCount;
    }

    /**
     * Sets the scenarioCount.
     *
     * @param scenarioCount
     *            The scenarioCount to set
     */
    public static void setScenarioCount(int scenarioCount) {
        TradeConfig.scenarioCount = scenarioCount;
    }

    public static synchronized void incrementScenarioCount() {
        scenarioCount++;
    }

    /**
     * Gets the jdbc driver needs global transaction Some XA Drivers require a
     * global transaction to be started for all SQL calls. To work around this,
     * set this to true to cause the direct mode to start a user transaction.
     *
     * @return Returns a boolean
     */
    public static boolean getJDBCDriverNeedsGlobalTransation() {
        return JDBCDriverNeedsGlobalTransation;
    }

    /**
     * Sets the jdbc driver needs global transaction
     *
     * @param JDBCDriverNeedsGlobalTransationVal
     *            the value
     */
    public static void setJDBCDriverNeedsGlobalTransation(boolean JDBCDriverNeedsGlobalTransationVal) {
        JDBCDriverNeedsGlobalTransation = JDBCDriverNeedsGlobalTransationVal;
    }

    /**
     * Gets the updateQuotePrices.
     *
     * @return Returns a boolean
     */
    public static boolean getUpdateQuotePrices() {
        return updateQuotePrices;
    }

    /**
     * Sets the updateQuotePrices.
     *
     * @param updateQuotePrices
     *            The updateQuotePrices to set
     */
    public static void setUpdateQuotePrices(boolean updateQuotePrices) {
        TradeConfig.updateQuotePrices = updateQuotePrices;
    }

    public static int getPrimIterations() {
        return primIterations;
    }

    public static void setPrimIterations(int iter) {
        primIterations = iter;
    }

    public static boolean getLongRun() {
        return longRun;
    }

    public static void setLongRun(boolean longRun) {
        TradeConfig.longRun = longRun;
    }

    public static void setPublishQuotePriceChange(boolean publishQuotePriceChange) {
        TradeConfig.publishQuotePriceChange = publishQuotePriceChange;
    }

    public static boolean getPublishQuotePriceChange() {
        return publishQuotePriceChange;
    }

    public static void setMarketSummaryInterval(int seconds) {
        TradeConfig.marketSummaryInterval = seconds;
    }

    public static int getMarketSummaryInterval() {
        return TradeConfig.marketSummaryInterval;
    }

    public static void setRunTimeMode(int value) {
        runTimeMode = value;
    }

    public static int getRunTimeMode() {
        return runTimeMode;
    }

    public static void setOrderProcessingMode(int value) {
        orderProcessingMode = value;
    }

    public static int getOrderProcessingMode() {
        return orderProcessingMode;
    }

    public static void setAccessMode(int value) {
        accessMode = value;
    }

    public static int getAccessMode() {
        return accessMode;
    }

    public static void setWebInterface(int value) {
        webInterface = value;
    }

    public static int getWebInterface() {
        return webInterface;
    }

    /*public static void setCachingType(int value) {
        cachingType = value;
    }

    public static int getCachingType() {
        return cachingType;
    }
	*/
    public static void setDisplayOrderAlerts(boolean value) {
        displayOrderAlerts = value;
    }

    public static boolean getDisplayOrderAlerts() {
        return displayOrderAlerts;
    }
    /*
    public static void setDistributedMapCacheSize(int value) {
        distributedMapCacheSize = value;
    }

    public static int getDistributedMapCacheSize() {
        return distributedMapCacheSize;
    }*/

    public static void setPercentSentToWebsocket(int value) {
		percentSentToWebsocket = value;
	}
    
	public static int getPercentSentToWebsocket() {
		return percentSentToWebsocket;
	}
	
	public static void setUseRemoteEJBInterface(boolean value) {
		useRemoteEJBInterface = value;
	}

	public static boolean useRemoteEJBInterface() {
		return useRemoteEJBInterface;
	}	
}


// Node: getPrimIterations
// Node: WebServlet
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.Collection;
import java.util.Iterator;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * TradeScenarioServlet emulates a population of web users by generating a
 * specific Trade operation for a randomly chosen user on each access to the
 * URL. Test this servlet by clicking Trade Scenario and hit "Reload" on your
 * browser to step through a Trade Scenario. To benchmark using this URL aim
 * your favorite web load generator (such as AKStress) at the Trade Scenario URL
 * and fire away.
 */
@WebServlet(name = "TradeScenarioServlet", urlPatterns = { "/scenario" })
public class TradeScenarioServlet extends HttpServlet {

    private static final long serialVersionUID = 1410005249314201829L;

    /**
     * Servlet initialization method.
     */
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        java.util.Enumeration<String> en = config.getInitParameterNames();
        while (en.hasMoreElements()) {
            String parm = en.nextElement();
            String value = config.getInitParameter(parm);
            TradeConfig.setConfigParam(parm, value);
        }
    }

    /**
     * Returns a string that contains information about TradeScenarioServlet
     *
     * @return The servlet information
     */
    @Override
    public java.lang.String getServletInfo() {
        return "TradeScenarioServlet emulates a population of web users";
    }

    /**
     * Process incoming HTTP GET requests
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    @Override
    public void doGet(javax.servlet.http.HttpServletRequest request, javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
        performTask(request, response);
    }

    /**
     * Process incoming HTTP POST requests
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    @Override
    public void doPost(javax.servlet.http.HttpServletRequest request, javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
        performTask(request, response);
    }

    /**
     * Main service method for TradeScenarioServlet
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    public void performTask(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {

        // Scenario generator for Trade2
        char action = ' ';
        String userID = null;

        // String to create full dispatch path to TradeAppServlet w/ request
        // Parameters
        String dispPath = null; // Dispatch Path to TradeAppServlet

        resp.setContentType("text/html");

        String scenarioAction = req.getParameter("action");
        if ((scenarioAction != null) && (scenarioAction.length() >= 1)) {
            action = scenarioAction.charAt(0);
            if (action == 'n') { // null;
                try {
                    // resp.setContentType("text/html");
                    PrintWriter out = new PrintWriter(resp.getOutputStream());
                    out.println("<HTML><HEAD>TradeScenarioServlet</HEAD><BODY>Hello</BODY></HTML>");
                    out.close();
                    return;

                } catch (Exception e) {
                    Log.error("trade_client.TradeScenarioServlet.service(...)" + "error creating printwriter from responce.getOutputStream", e);

                    resp.sendError(500,
                            "trade_client.TradeScenarioServlet.service(...): erorr creating and writing to PrintStream created from response.getOutputStream()");
                } // end of catch

            } // end of action=='n'
        }

        ServletContext ctx = null;
        HttpSession session = null;
        try {
            ctx = getServletConfig().getServletContext();
            // These operations require the user to be logged in. Verify the
            // user and if not logged in
            // change the operation to a login
            session = req.getSession(true);
            userID = (String) session.getAttribute("uidBean");
        } catch (Exception e) {
            Log.error("trade_client.TradeScenarioServlet.service(...): performing " + scenarioAction
                    + "error getting ServletContext,HttpSession, or UserID from session" + "will make scenarioAction a login and try to recover from there", e);
            userID = null;
            action = 'l';
        }

        if (userID == null) {
            action = 'l'; // change to login
            TradeConfig.incrementScenarioCount();
        } else if (action == ' ') {
            // action is not specified perform a random operation according to
            // current mix
            // Tell getScenarioAction if we are an original user or a registered
            // user
            // -- sellDeficits should only be compensated for with original
            // users.
            action = TradeConfig.getScenarioAction(userID.startsWith(TradeConfig.newUserPrefix));
        }
        switch (action) {

        case 'q': // quote
            dispPath = tasPathPrefix + "quotes&symbols=" + TradeConfig.rndSymbols();
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        case 'a': // account
            dispPath = tasPathPrefix + "account";
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        case 'u': // update account profile
            dispPath = tasPathPrefix + "account";
            ctx.getRequestDispatcher(dispPath).include(req, resp);

            String fullName = "rnd" + System.currentTimeMillis();
            String address = "rndAddress";
            String password = "xxx";
            String email = "rndEmail";
            String creditcard = "rndCC";
            dispPath = tasPathPrefix + "update_profile&fullname=" + fullName + "&password=" + password + "&cpassword=" + password + "&address=" + address
                    + "&email=" + email + "&creditcard=" + creditcard;
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        case 'h': // home
            dispPath = tasPathPrefix + "home";
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        case 'l': // login
            userID = TradeConfig.getUserID();
            String password2 = "xxx";
            dispPath = tasPathPrefix + "login&inScenario=true&uid=" + userID + "&passwd=" + password2;
            ctx.getRequestDispatcher(dispPath).include(req, resp);

            // login is successful if the userID is written to the HTTP session
            if (session.getAttribute("uidBean") == null) {
                System.out.println("TradeScenario login failed. Reset DB between runs");
            }
            break;
        case 'o': // logout
            dispPath = tasPathPrefix + "logout";
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        case 'p': // portfolio
            dispPath = tasPathPrefix + "portfolio";
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        case 'r': // register
            // Logout the current user to become a new user
            // see note in TradeServletAction
            req.setAttribute("TSS-RecreateSessionInLogout", Boolean.TRUE);
            dispPath = tasPathPrefix + "logout";
            ctx.getRequestDispatcher(dispPath).include(req, resp);

            userID = TradeConfig.rndNewUserID();
            String passwd = "yyy";
            fullName = TradeConfig.rndFullName();
            creditcard = TradeConfig.rndCreditCard();
            String money = TradeConfig.rndBalance();
            email = TradeConfig.rndEmail(userID);
            String smail = TradeConfig.rndAddress();
            dispPath = tasPathPrefix + "register&Full Name=" + fullName + "&snail mail=" + smail + "&email=" + email + "&user id=" + userID + "&passwd="
                    + passwd + "&confirm passwd=" + passwd + "&money=" + money + "&Credit Card Number=" + creditcard;
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        case 's': // sell
            dispPath = tasPathPrefix + "portfolioNoEdge";
            ctx.getRequestDispatcher(dispPath).include(req, resp);

            Collection<?> holdings = (Collection<?>) req.getAttribute("holdingDataBeans");
            int numHoldings = holdings.size();
            if (numHoldings > 0) {
                // sell first available security out of holding

                Iterator<?> it = holdings.iterator();
                boolean foundHoldingToSell = false;
                while (it.hasNext()) {
                    HoldingDataBean holdingData = (HoldingDataBean) it.next();
                    if (!(holdingData.getPurchaseDate().equals(new java.util.Date(0)))) {
                        Integer holdingID = holdingData.getHoldingID();

                        dispPath = tasPathPrefix + "sell&holdingID=" + holdingID;
                        ctx.getRequestDispatcher(dispPath).include(req, resp);
                        foundHoldingToSell = true;
                        break;
                    }
                }
                if (foundHoldingToSell) {
                    break;
                }
                if (Log.doTrace()) {
                    Log.trace("TradeScenario: No holding to sell -switch to buy -- userID = " + userID + "  Collection count = " + numHoldings);
                }

            }
            // At this point: A TradeScenario Sell was requested with No Stocks
            // in Portfolio
            // This can happen when a new registered user happens to request a
            // sell before a buy
            // In this case, fall through and perform a buy instead

            /*
             * Trade 2.037: Added sell_deficit counter to maintain correct
             * buy/sell mix. When a users portfolio is reduced to 0 holdings, a
             * buy is requested instead of a sell. This throws off the buy/sell
             * mix by 1. This results in unwanted holding table growth To fix
             * this we increment a sell deficit counter to maintain the correct
             * ratio in getScenarioAction The 'z' action from getScenario
             * denotes that this is a sell action that was switched from a buy
             * to reduce a sellDeficit
             */
            if (userID.startsWith(TradeConfig.newUserPrefix) == false) {
                TradeConfig.incrementSellDeficit();
            }
        case 'b': // buy
            String symbol = TradeConfig.rndSymbol();
            String amount = TradeConfig.rndQuantity() + "";

            dispPath = tasPathPrefix + "quotes&symbols=" + symbol;
            ctx.getRequestDispatcher(dispPath).include(req, resp);

            dispPath = tasPathPrefix + "buy&quantity=" + amount + "&symbol=" + symbol;
            ctx.getRequestDispatcher(dispPath).include(req, resp);
            break;
        } // end of switch statement
    }

    // URL Path Prefix for dispatching to TradeAppServlet
    private static final String tasPathPrefix = "/app?action=";

}


// Node: doGet
// Node: performTask
// Node: doPost
// Node: setContentType
// Node: getParameter
// Node: getOutputStream
// Node: service
// Node: sendError
// Node: getServletConfig
// Node: getServletContext
// Node: startsWith
// Node: getRequestDispatcher
// Node: include
// Node: setAttribute
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.beans.RunStatsDataBean;
import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * TradeConfigServlet provides a servlet interface to adjust DayTrader runtime parameters.
 * TradeConfigServlet updates values in the {@link com.ibm.websphere.samples.daytrader.web.TradeConfig} JavaBean holding
 * all configuration and runtime parameters for the Trade application
 *
 */
@WebServlet(name = "TradeConfigServlet", urlPatterns = { "/config" })
public class TradeConfigServlet extends HttpServlet {

    private static final long serialVersionUID = -1910381529792500095L;

    /**
     * Servlet initialization method.
     */
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
    }

    /**
     * Create the TradeConfig bean and pass it the config.jsp page
     * to display the current Trade runtime configuration
     * Creation date: (2/8/2000 3:43:59 PM)
     */
    void doConfigDisplay(HttpServletRequest req, HttpServletResponse resp, String results) throws Exception {

        TradeConfig currentConfig = new TradeConfig();

        req.setAttribute("tradeConfig", currentConfig);
        req.setAttribute("status", results);
        getServletConfig().getServletContext().getRequestDispatcher(TradeConfig.getPage(TradeConfig.CONFIG_PAGE)).include(req, resp);
    }

    void doResetTrade(HttpServletRequest req, HttpServletResponse resp, String results) throws Exception {
        RunStatsDataBean runStatsData = new RunStatsDataBean();
        TradeConfig currentConfig = new TradeConfig();
        try {
            runStatsData = new TradeAction().resetTrade(false);

            req.setAttribute("runStatsData", runStatsData);
            req.setAttribute("tradeConfig", currentConfig);
            results += "Trade Reset completed successfully";
            req.setAttribute("status", results);

        } catch (Exception e) {
            results += "Trade Reset Error  - see log for details";
            Log.error(e, results);
            throw e;
        }
        getServletConfig().getServletContext().getRequestDispatcher(TradeConfig.getPage(TradeConfig.STATS_PAGE)).include(req, resp);

    }

    /**
     * Update Trade runtime configuration paramaters
     * Creation date: (2/8/2000 3:44:24 PM)
     */
    void doConfigUpdate(HttpServletRequest req, HttpServletResponse resp) throws Exception {
        String currentConfigStr = "\n\n########## Trade configuration update. Current config:\n\n";
                        
        String runTimeModeStr = req.getParameter("RunTimeMode");
        if (runTimeModeStr != null) {
            try {
                int i = Integer.parseInt(runTimeModeStr);
                if ((i >= 0) && (i < TradeConfig.runTimeModeNames.length)) //Input validation
                    TradeConfig.setRunTimeMode(i);
            } catch (Exception e) {
                //>>rjm
                Log.error(e, "TradeConfigServlet.doConfigUpdate(..): minor exception caught", "trying to set runtimemode to " + runTimeModeStr,
                        "reverting to current value");

            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tRunTimeMode:\t\t\t" + TradeConfig.runTimeModeNames[TradeConfig.runTimeMode] + "\n";
        
        String useRemoteEJBInterface = req.getParameter("UseRemoteEJBInterface");

        if (useRemoteEJBInterface != null)
            TradeConfig.setUseRemoteEJBInterface(true);
        else
            TradeConfig.setDisplayOrderAlerts(false);
        currentConfigStr += "\t\tUse Remote EJB Interface:\t" + TradeConfig.useRemoteEJBInterface() + "\n";

        String orderProcessingModeStr = req.getParameter("OrderProcessingMode");
        if (orderProcessingModeStr != null) {
            try {
                int i = Integer.parseInt(orderProcessingModeStr);
                if ((i >= 0) && (i < TradeConfig.orderProcessingModeNames.length)) //Input validation
                    TradeConfig.setOrderProcessingMode(i);
            } catch (Exception e) {
                //>>rjm
                Log.error(e, "TradeConfigServlet.doConfigUpdate(..): minor exception caught", "trying to set orderProcessing to " + orderProcessingModeStr,
                        "reverting to current value");

            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tOrderProcessingMode:\t\t" + TradeConfig.orderProcessingModeNames[TradeConfig.orderProcessingMode] + "\n";

        String webInterfaceStr = req.getParameter("WebInterface");
        if (webInterfaceStr != null) {
            try {
                int i = Integer.parseInt(webInterfaceStr);
                if ((i >= 0) && (i < TradeConfig.webInterfaceNames.length)) //Input validation
                    TradeConfig.setWebInterface(i);
            } catch (Exception e) {
                Log.error(e, "TradeConfigServlet.doConfigUpdate(..): minor exception caught", "trying to set WebInterface to " + webInterfaceStr,
                        "reverting to current value");

            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tWeb Interface:\t\t\t" + TradeConfig.webInterfaceNames[TradeConfig.webInterface] + "\n";

       /* String cachingTypeStr = req.getParameter("CachingType");
        if (cachingTypeStr != null) {
            try {
                int i = Integer.parseInt(cachingTypeStr);
                if ((i >= 0) && (i < TradeConfig.cachingTypeNames.length)) //Input validation
                    TradeConfig.setCachingType(i);
            } catch (Exception e) {
                Log.error(e, "TradeConfigServlet.doConfigUpdate(..): minor exception caught", "trying to set CachingType to " + cachingTypeStr,
                        "reverting to current value");
            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tCachingType:\t\t\t" + TradeConfig.cachingTypeNames[TradeConfig.cachingType] + "\n";

        String distMapCacheSize = req.getParameter("DistMapCacheSize");
        if ((distMapCacheSize != null) && (distMapCacheSize.length() > 0)) {
            try {
                TradeConfig.setDistributedMapCacheSize(Integer.parseInt(distMapCacheSize));
            } catch (Exception e) {
                Log.error(e, "TradeConfigServlet: minor exception caught", "trying to set DistributedMapCacheSize, error on parsing int " + distMapCacheSize,
                        "reverting to current value " + TradeConfig.getPrimIterations());

            }
        }
        currentConfigStr += "\t\tDMap Cache Size:\t\t" + TradeConfig.getDistributedMapCacheSize() + "\n";
		*/
        String parm = req.getParameter("MaxUsers");
        if ((parm != null) && (parm.length() > 0)) {
            try {
                TradeConfig.setMAX_USERS(Integer.parseInt(parm));
            } catch (Exception e) {
                Log.error(e, "TradeConfigServlet.doConfigUpdate(..): minor exception caught", "Setting maxusers, probably error parsing string to int:" + parm,
                        "revertying to current value: " + TradeConfig.getMAX_USERS());

            } //On error, revert to saved
        }
        parm = req.getParameter("MaxQuotes");
        if ((parm != null) && (parm.length() > 0)) {
            try {
                TradeConfig.setMAX_QUOTES(Integer.parseInt(parm));
            } catch (Exception e) {
                //>>rjm
                Log.error(e, "TradeConfigServlet: minor exception caught", "trying to set max_quotes, error on parsing int " + parm,
                        "reverting to current value " + TradeConfig.getMAX_QUOTES());
                //<<rjm

            } //On error, revert to saved
        }
        currentConfigStr += "\t\tTrade Users:\t\t\t" + TradeConfig.getMAX_USERS() + "\n";
        currentConfigStr += "\t\tTrade Quotes:\t\t\t" + TradeConfig.getMAX_QUOTES() + "\n";

        parm = req.getParameter("marketSummaryInterval");
        if ((parm != null) && (parm.length() > 0)) {
            try {
                TradeConfig.setMarketSummaryInterval(Integer.parseInt(parm));
            } catch (Exception e) {
                Log.error(e, "TradeConfigServlet: minor exception caught", "trying to set marketSummaryInterval, error on parsing int " + parm,
                        "reverting to current value " + TradeConfig.getMarketSummaryInterval());

            }
        }
        currentConfigStr += "\t\tMarket Summary Interval:\t" + TradeConfig.getMarketSummaryInterval() + "\n";

        parm = req.getParameter("primIterations");
        if ((parm != null) && (parm.length() > 0)) {
            try {
                TradeConfig.setPrimIterations(Integer.parseInt(parm));
            } catch (Exception e) {
                Log.error(e, "TradeConfigServlet: minor exception caught", "trying to set primIterations, error on parsing int " + parm,
                        "reverting to current value " + TradeConfig.getPrimIterations());

            }
        }
        currentConfigStr += "\t\tPrimitive Iterations:\t\t" + TradeConfig.getPrimIterations() + "\n";

        String enablePublishQuotePriceChange = req.getParameter("EnablePublishQuotePriceChange");

        if (enablePublishQuotePriceChange != null)
            TradeConfig.setPublishQuotePriceChange(true);
        else
            TradeConfig.setPublishQuotePriceChange(false);
        currentConfigStr += "\t\tTradeStreamer MDB Enabled:\t" + TradeConfig.getPublishQuotePriceChange() + "\n";

        parm = req.getParameter("percentSentToWebsocket");
        if ((parm != null) && (parm.length() > 0)) {
            try {
                TradeConfig.setPercentSentToWebsocket(Integer.parseInt(parm));
            } catch (Exception e) {
                Log.error(e, "TradeConfigServlet: minor exception caught", "trying to set percentSentToWebSocket, error on parsing int " + parm,
                        "reverting to current value " + TradeConfig.getPercentSentToWebsocket());

            }
        }
        currentConfigStr += "\t\t% of trades on Websocket:\t" + TradeConfig.getPercentSentToWebsocket() + "\n";
        
        String enableLongRun = req.getParameter("EnableLongRun");

        if (enableLongRun != null)
            TradeConfig.setLongRun(true);
        else
            TradeConfig.setLongRun(false);
        currentConfigStr += "\t\tLong Run Enabled:\t\t" + TradeConfig.getLongRun() + "\n";

        String displayOrderAlerts = req.getParameter("DisplayOrderAlerts");

        if (displayOrderAlerts != null)
            TradeConfig.setDisplayOrderAlerts(true);
        else
            TradeConfig.setDisplayOrderAlerts(false);
        currentConfigStr += "\t\tDisplay Order Alerts:\t\t" + TradeConfig.getDisplayOrderAlerts() + "\n";
                
        String enableTrace = req.getParameter("EnableTrace");
        if (enableTrace != null)
            Log.setTrace(true);
        else
            Log.setTrace(false);
        currentConfigStr += "\t\tTrace Enabled:\t\t\t" + TradeConfig.getTrace() + "\n";

        String enableActionTrace = req.getParameter("EnableActionTrace");
        if (enableActionTrace != null)
            Log.setActionTrace(true);
        else
            Log.setActionTrace(false);
        currentConfigStr += "\t\tAction Trace Enabled:\t\t" + TradeConfig.getActionTrace() + "\n";

        System.out.println(currentConfigStr);
    }

    @Override
    public void service(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {

        String action = null;
        String result = "";

        resp.setContentType("text/html");
        try {
            action = req.getParameter("action");
            if (action == null) {
                doConfigDisplay(req, resp, result + "<b><br>Current DayTrader Configuration:</br></b>");
                return;
            } else if (action.equals("updateConfig")) {
                doConfigUpdate(req, resp);
                result = "<B><BR>DayTrader Configuration Updated</BR></B>";
            } else if (action.equals("resetTrade")) {
                doResetTrade(req, resp, "");
                return;
            } else if (action.equals("buildDB")) {
                resp.setContentType("text/html");
                new TradeBuildDB(resp.getWriter(), null);
                result = "DayTrader Database Built - " + TradeConfig.getMAX_USERS() + "users created";
            } else if (action.equals("buildDBTables")) {

                resp.setContentType("text/html");

                //Find out the Database being used
                TradeDirect tradeDirect = new TradeDirect();

                String dbProductName = null;
                try {
                    dbProductName = tradeDirect.checkDBProductName();
                } catch (Exception e) {
                    Log.error(e, "TradeBuildDB: Unable to check DB Product name");
                }
                if (dbProductName == null) {
                    resp.getWriter().println(
                            "<BR>TradeBuildDB: **** Unable to check DB Product name, please check Database/AppServer configuration and retry ****</BR></BODY>");
                    return;
                }

                String ddlFile = null;
                //Locate DDL file for the specified database
                try {
                    resp.getWriter().println("<BR>TradeBuildDB: **** Database Product detected: " + dbProductName + " ****</BR>");
                    if (dbProductName.startsWith("DB2/")) {// if db is DB2
                        ddlFile = "/dbscripts/db2/Table.ddl";
                    } else if (dbProductName.startsWith("DB2 UDB for AS/400")) { //if db is DB2 on IBM i
                        ddlFile = "/dbscripts/db2i/Table.ddl";
                    }  else if (dbProductName.startsWith("Apache Derby")) { //if db is Derby
                        ddlFile = "/dbscripts/derby/Table.ddl";
                    } else if (dbProductName.startsWith("Oracle")) { // if the Db is Oracle
                        ddlFile = "/dbscripts/oracle/Table.ddl";
                    } else {// Unsupported "Other" Database, try derby ddl
                        ddlFile = "/dbscripts/derby/Table.ddl";
                        resp.getWriter().println("<BR>TradeBuildDB: **** This Database is unsupported/untested use at your own risk ****</BR>");
                    }

                    resp.getWriter().println("<BR>TradeBuildDB: **** The DDL file at path <I>" + ddlFile + "</I> will be used ****</BR>");
                    resp.getWriter().flush();
                } catch (Exception e) {
                    Log.error(e, "TradeBuildDB: Unable to locate DDL file for the specified database");
                    resp.getWriter().println("<BR>TradeBuildDB: **** Unable to locate DDL file for the specified database ****</BR></BODY>");
                    return;
                }
                new TradeBuildDB(resp.getWriter(), getServletContext().getResourceAsStream(ddlFile));

            }
            doConfigDisplay(req, resp, result + "Current DayTrader Configuration:");
        } catch (Exception e) {
            Log.error(e, "TradeConfigServlet.service(...)", "Exception trying to perform action=" + action);

            resp.sendError(500, "TradeConfigServlet.service(...)" + "Exception trying to perform action=" + action + "\nException details: " + e.toString());

        }
    }
}


// Node: getWriter
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web;

import java.io.IOException;
import java.math.BigDecimal;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@WebServlet(name = "TestServlet", urlPatterns = { "/TestServlet" })
public class TestServlet extends HttpServlet {

    private static final long serialVersionUID = -2927579146688173127L;

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
    }

    /**
     * Process incoming HTTP GET requests
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        performTask(request, response);
    }

    /**
     * Process incoming HTTP POST requests
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    @Override
    public void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        performTask(request, response);
    }

    /**
     * Main service method for TradeAppServlet
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    public void performTask(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        try {
            Log.debug("Enter TestServlet doGet");
            TradeConfig.runTimeMode = TradeConfig.DIRECT;
            for (int i = 0; i < 10; i++) {
                new TradeAction().createQuote("s:" + i, "Company " + i, new BigDecimal(i * 1.1));
            }
            /*
             *
             * AccountDataBean accountData = new TradeAction().register("user1",
             * "password", "fullname", "address", "email", "creditCard", new
             * BigDecimal(123.45), false);
             *
             * OrderDataBean orderData = new TradeAction().buy("user1", "s:1",
             * 100.0); orderData = new TradeAction().buy("user1", "s:2", 200.0);
             * Thread.sleep(5000); accountData = new
             * TradeAction().getAccountData("user1"); Collection
             * holdingDataBeans = new TradeAction().getHoldings("user1");
             * PrintWriter out = resp.getWriter();
             * resp.setContentType("text/html");
             * out.write("<HEAD></HEAD><BODY><BR><BR>");
             * out.write(accountData.toString());
             * Log.printCollection("user1 Holdings", holdingDataBeans);
             * ServletContext sc = getServletContext();
             * req.setAttribute("results", "Success");
             * req.setAttribute("accountData", accountData);
             * req.setAttribute("holdingDataBeans", holdingDataBeans);
             * getServletContext
             * ().getRequestDispatcher("/tradehome.jsp").include(req, resp);
             * out.write("<BR><BR>done.</BODY>");
             */
        } catch (Exception e) {
            Log.error("TestServletException", e);
        }
    }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/TestServlet.java:TestServlet.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * TradeAppServlet provides the standard web interface to Trade and can be
 * accessed with the Go Trade! link. Driving benchmark load using this interface
 * requires a sophisticated web load generator that is capable of filling HTML
 * forms and posting dynamic data.
 */

@WebServlet(name = "TradeAppServlet", urlPatterns = { "/app" })
public class TradeAppServlet extends HttpServlet {

    private static final long serialVersionUID = 481530522846648373L;

    /**
     * Servlet initialization method.
     */
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        java.util.Enumeration<String> en = config.getInitParameterNames();
        while (en.hasMoreElements()) {
            String parm = en.nextElement();
            String value = config.getInitParameter(parm);
            TradeConfig.setConfigParam(parm, value);
        }
        try {
            // TODO: Uncomment this once split-tier issue is resolved
            // TradeDirect.init();
        } catch (Exception e) {
            Log.error(e, "TradeAppServlet:init -- Error initializing TradeDirect");
        }
    }

    /**
     * Returns a string that contains information about TradeScenarioServlet
     *
     * @return The servlet information
     */
    @Override
    public java.lang.String getServletInfo() {
        return "TradeAppServlet provides the standard web interface to Trade";
    }

    /**
     * Process incoming HTTP GET requests
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    @Override
    public void doGet(javax.servlet.http.HttpServletRequest request, javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
        performTask(request, response);
    }

    /**
     * Process incoming HTTP POST requests
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    @Override
    public void doPost(javax.servlet.http.HttpServletRequest request, javax.servlet.http.HttpServletResponse response) throws ServletException, IOException {
        performTask(request, response);
    }

    /**
     * Main service method for TradeAppServlet
     *
     * @param request
     *            Object that encapsulates the request to the servlet
     * @param response
     *            Object that encapsulates the response from the servlet
     */
    public void performTask(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {

        String action = null;
        String userID = null;
        // String to create full dispatch path to TradeAppServlet w/ request
        // Parameters

        resp.setContentType("text/html");
        TradeServletAction tsAction = new TradeServletAction();

        // Dyna - need status string - prepended to output
        action = req.getParameter("action");

        ServletContext ctx = getServletConfig().getServletContext();

        if (action == null) {
            tsAction.doWelcome(ctx, req, resp, "");
            return;
        } else if (action.equals("login")) {
            userID = req.getParameter("uid");
            String passwd = req.getParameter("passwd");
            tsAction.doLogin(ctx, req, resp, userID, passwd);
            return;
        } else if (action.equals("register")) {
            userID = req.getParameter("user id");
            String passwd = req.getParameter("passwd");
            String cpasswd = req.getParameter("confirm passwd");
            String fullname = req.getParameter("Full Name");
            String ccn = req.getParameter("Credit Card Number");
            String money = req.getParameter("money");
            String email = req.getParameter("email");
            String smail = req.getParameter("snail mail");
            tsAction.doRegister(ctx, req, resp, userID, passwd, cpasswd, fullname, ccn, money, email, smail);
            return;
        }

        // The rest of the operations require the user to be logged in -
        // Get the Session and validate the user.
        HttpSession session = req.getSession();
        userID = (String) session.getAttribute("uidBean");

        if (userID == null) {
            System.out.println("TradeAppServlet service error: User Not Logged in");
            tsAction.doWelcome(ctx, req, resp, "User Not Logged in");
            return;
        }
        if (action.equals("quotes")) {
            String symbols = req.getParameter("symbols");
            tsAction.doQuotes(ctx, req, resp, userID, symbols);
        } else if (action.equals("buy")) {
            String symbol = req.getParameter("symbol");
            String quantity = req.getParameter("quantity");
            tsAction.doBuy(ctx, req, resp, userID, symbol, quantity);
        } else if (action.equals("sell")) {
            int holdingID = Integer.parseInt(req.getParameter("holdingID"));
            tsAction.doSell(ctx, req, resp, userID, new Integer(holdingID));
        } else if (action.equals("portfolio") || action.equals("portfolioNoEdge")) {
            tsAction.doPortfolio(ctx, req, resp, userID, "Portfolio as of " + new java.util.Date());
        } else if (action.equals("logout")) {
            tsAction.doLogout(ctx, req, resp, userID);
        } else if (action.equals("home")) {
            tsAction.doHome(ctx, req, resp, userID, "Ready to Trade");
        } else if (action.equals("account")) {
            tsAction.doAccount(ctx, req, resp, userID, "");
        } else if (action.equals("update_profile")) {
            String password = req.getParameter("password");
            String cpassword = req.getParameter("cpassword");
            String fullName = req.getParameter("fullname");
            String address = req.getParameter("address");
            String creditcard = req.getParameter("creditcard");
            String email = req.getParameter("email");
            tsAction.doAccountUpdate(ctx, req, resp, userID, password == null ? "" : password.trim(), cpassword == null ? "" : cpassword.trim(),
                    fullName == null ? "" : fullName.trim(), address == null ? "" : address.trim(), creditcard == null ? "" : creditcard.trim(),
                    email == null ? "" : email.trim());
        } else if (action.equals("mksummary")) {
            tsAction.doMarketSummary(ctx, req, resp, userID);
        } else {
            System.out.println("TradeAppServlet: Invalid Action=" + action);
            tsAction.doWelcome(ctx, req, resp, "TradeAppServlet: Invalid Action" + action);
        }
    }

}

// Node: BufferedReader
// Node: InputStreamReader
// Node: String
// Node: readLine
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */  
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.AsyncContext;
import javax.servlet.ReadListener;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletInputStream;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

//import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet31Async tests fundamental dynamic HTML creation functionality through
 * server side servlet processing asynchronously with non-blocking i/o.
 *
 */

@WebServlet(name = "PingServlet31AsyncRead", urlPatterns = { "/servlet/PingServlet31AsyncRead" }, asyncSupported=true)
public class PingServlet31AsyncRead extends HttpServlet {

    private static final long serialVersionUID = 8731300373855056660L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        res.setContentType("text/html");
                
        AsyncContext ac = req.startAsync();
           
        ServletInputStream input = req.getInputStream();
        ReadListener readListener = new ReadListenerImpl(input, res, ac);
        input.setReadListener(readListener);
    }

    class ReadListenerImpl implements ReadListener {
        private ServletInputStream input = null;
        private HttpServletResponse res = null;
        private AsyncContext ac = null;
        private StringBuilder sb = new StringBuilder();

        ReadListenerImpl(ServletInputStream in, HttpServletResponse r, AsyncContext c) {
            input = in;
            res = r;
            ac = c;
        }
    
        public void onDataAvailable() throws IOException {
            
            int len = -1;
            byte b[] = new byte[1024];
            
            while (input.isReady() && (len = input.read(b)) != -1) {
                String data = new String(b, 0, len);
                sb.append(data);
            }
            
            
        }
    
        public void onAllDataRead() throws IOException {
            ServletOutputStream output = res.getOutputStream();
            output.println("<html><head><title>Ping Servlet 3.1 Async</title></head>"
                    + "<body><hr/><br/><font size=\"+2\" color=\"#000066\">Ping Servlet 3.1 AsyncRead</font>"
                    + "<br/><font size=\"+1\" color=\"#000066\">Init time : " + initTime
                    + "</font><br/><br/><b>Hit Count: " + ++hitCount + "</b><br/>Data Received: " + sb.toString() + "</body></html>");
            ac.complete();
        }
    
        public void onError(final Throwable t) {
            ac.complete();
            t.printStackTrace();
        }
    }
        


    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doPost(req,res);          
    }
    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet31AsyncRead.java:PingServlet31AsyncRead.<init>
// Node: startAsync
// Node: getInputStream
// Node: ReadListenerImpl
// Node: setReadListener
// Node: StringBuilder
// Node: onDataAvailable
// Node: isReady
// Node: read
// Node: append
// Node: onAllDataRead
// Node: complete
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServletSetContentLength tests fundamental dynamic HTML creation
 * functionality through server side servlet processing.
 *
 */

@WebServlet(name = "PingServletSetContentLength", urlPatterns = { "/servlet/PingServletSetContentLength" })
public class PingServletSetContentLength extends HttpServlet {

    private static final long serialVersionUID = 8731300373855056661L;

    /**
     * forwards post requests to the doGet method Creation date: (02/07/2013
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        try {
            res.setContentType("text/html");
            String lengthParam = req.getParameter("contentLength");
            Integer length;

            if (lengthParam == null) {
                length = 0;
            } else {
                length = Integer.parseInt(lengthParam);
            }

            ServletOutputStream out = res.getOutputStream();

            // Add characters (a's) to the SOS to equal the requested length
            // 167 is the smallest length possible.
            
            int i = 0;
            String buffer = "";

            while (i + 167 < length) {
                buffer = buffer + "a";
                i++;
            }

            out.println("<html><head><title>Ping Servlet</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Ping Servlet<BR></FONT><FONT size=\"+1\" color=\"#000066\">" + buffer
                    + "</B></body></html>");
        } catch (Exception e) {
            Log.error(e, "PingServlet.doGet(...): general exception caught");
            res.sendError(500, e.toString());

        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet, with " + "contentLength set by contentLength parameter.";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServletSetContentLength.java:PingServletSetContentLength.<init>
// Node: characters
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingJDBCReadPrepStmt uses a prepared statement for database read access. This
 * primative uses
 * {@link com.ibm.websphere.samples.daytrader.direct.TradeDirect} to set the
 * price of a random stock (generated by
 * {@link com.ibm.websphere.samples.daytrader.util.TradeConfig}) through the use
 * of prepared statements.
 *
 */

@WebServlet(name = "PingJDBCRead2JSP", urlPatterns = { "/servlet/PingJDBCRead2JSP" })
public class PingJDBCRead2JSP extends HttpServlet {

    private static final long serialVersionUID = 1118803761565654806L;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        String symbol = null;
        QuoteDataBean quoteData = null;
        ServletContext ctx = getServletConfig().getServletContext();

        try {
            // TradeJDBC uses prepared statements so I am going to make use of
            // it's code.
            TradeDirect trade = new TradeDirect();
            symbol = TradeConfig.rndSymbol();

            int iter = TradeConfig.getPrimIterations();
            for (int ii = 0; ii < iter; ii++) {
                quoteData = trade.getQuote(symbol);
            }

            req.setAttribute("quoteData", quoteData);
            // req.setAttribute("hitCount", hitCount);
            // req.setAttribute("initTime", initTime);

            ctx.getRequestDispatcher("/quoteDataPrimitive.jsp").include(req, res);
        } catch (Exception e) {
            Log.error(e, "PingJDBCRead2JPS -- error getting quote for symbol", symbol);
            res.sendError(500, "PingJDBCRead2JSP Exception caught: " + e.toString());
        }

    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic JDBC Read using a prepared statment forwarded to a JSP, makes use of TradeJDBC class";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        // hitCount = 0;
        // initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingJDBCRead2JSP.java:PingJDBCRead2JSP.<init>
// Node: stock
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * ExplicitGC invokes System.gc(). This allows one to gather min / max heap
 * statistics.
 *
 */
@WebServlet(name = "ExplicitGC", urlPatterns = { "/servlet/ExplicitGC" })
public class ExplicitGC extends HttpServlet {

    private static final long serialVersionUID = -3758934393801102408L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (01/29/2006
     * 20:10:00 PM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        try {
            res.setContentType("text/html");

            ServletOutputStream out = res.getOutputStream();
            hitCount++;
            long totalMemory = Runtime.getRuntime().totalMemory();

            long maxMemoryBeforeGC = Runtime.getRuntime().maxMemory();
            long freeMemoryBeforeGC = Runtime.getRuntime().freeMemory();
            long startTime = System.currentTimeMillis();

            System.gc(); // Invoke the GC.

            long endTime = System.currentTimeMillis();
            long maxMemoryAfterGC = Runtime.getRuntime().maxMemory();
            long freeMemoryAfterGC = Runtime.getRuntime().freeMemory();

            out.println("<html><head><title>ExplicitGC</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Explicit Garbage Collection<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time : "
                    + initTime
                    + "<BR><BR></FONT>  <B>Hit Count: "
                    + hitCount
                    + "<br>"
                    + "<table border=\"0\"><tr>"
                    + "<td align=\"right\">Total Memory</td><td align=\"right\">"
                    + totalMemory
                    + "</td>"
                    + "</tr></table>"
                    + "<table width=\"350\"><tr><td colspan=\"2\" align=\"left\">"
                    + "Statistics before GC</td></tr>"
                    + "<tr><td align=\"right\">"
                    + "Max Memory</td><td align=\"right\">"
                    + maxMemoryBeforeGC
                    + "</td></tr>"
                    + "<tr><td align=\"right\">"
                    + "Free Memory</td><td align=\"right\">"
                    + freeMemoryBeforeGC
                    + "</td></tr>"
                    + "<tr><td align=\"right\">"
                    + "Used Memory</td><td align=\"right\">"
                    + (totalMemory - freeMemoryBeforeGC)
                    + "</td></tr>"
                    + "<tr><td colspan=\"2\" align=\"left\">Statistics after GC</td></tr>"
                    + "<tr><td align=\"right\">"
                    + "Max Memory</td><td align=\"right\">"
                    + maxMemoryAfterGC
                    + "</td></tr>"
                    + "<tr><td align=\"right\">"
                    + "Free Memory</td><td align=\"right\">"
                    + freeMemoryAfterGC
                    + "</td></tr>"
                    + "<tr><td align=\"right\">"
                    + "Used Memory</td><td align=\"right\">"
                    + (totalMemory - freeMemoryAfterGC)
                    + "</td></tr>"
                    + "<tr><td align=\"right\">"
                    + "Total Time in GC</td><td align=\"right\">"
                    + Float.toString((endTime - startTime) / 1000)
                    + "s</td></tr>"
                    + "</table>" + "</body></html>");
        } catch (Exception e) {
            Log.error(e, "ExplicitGC.doGet(...): general exception caught");
            res.sendError(500, e.toString());

        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Generate Explicit GC to VM";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;

    }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ExplicitGC.java:ExplicitGC.<init>
// Node: gc
// Node: getRuntime
// Node: totalMemory
// Node: maxMemory
// Node: freeMemory
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.annotation.Resource;
import javax.enterprise.concurrent.ManagedThreadFactory;
import javax.servlet.AsyncContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

@WebServlet(asyncSupported=true,name = "PingManagedThread", urlPatterns = { "/servlet/PingManagedThread" })
public class PingManagedThread extends HttpServlet{

	private static final long serialVersionUID = -4695386150928451234L;
	private static String initTime;
    private static int hitCount;

	@Resource 
	private ManagedThreadFactory managedThreadFactory;
	
	 /**
     * forwards post requests to the doGet method Creation date: (03/18/2014
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
	protected void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
    	
		final AsyncContext asyncContext = req.startAsync();
		final ServletOutputStream out = res.getOutputStream();	
		
		try {
			
			res.setContentType("text/html");
					
			out.println("<html><head><title>Ping ManagedThread</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Ping ManagedThread<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time : " + initTime + "<BR/><BR/></FONT>");			
		
			Thread thread = managedThreadFactory.newThread(new Runnable() {
    			@Override
    			public void run() {
    				try {
						out.println("<b>HitCount: " + ++hitCount  +"</b><br/>");
					} catch (IOException e) {
						e.printStackTrace();
					}
    				asyncContext.complete();
    			}
    		});   		    		
			
			thread.start();
		
		} catch (Exception e) {
			Log.error(e, "PingManagedThreadServlet.doGet(...): general exception caught");
			res.sendError(500, e.toString());
		}
		
	}
    
    
    
    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Tests a ManagedThread asynchronous servlet";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;

    }
	
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingManagedThread.java:PingManagedThread.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
import java.math.BigDecimal;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingJDBCReadPrepStmt uses a prepared statement for database update. Statement
 * parameters are set dynamically on each request. This primative uses
 * {@link com.ibm.websphere.samples.daytrader.direct.TradeDirect} to set the
 * price of a random stock (generated by
 * {@link com.ibm.websphere.samples.daytrader.util.TradeConfig}) through the use
 * of prepared statements.
 *
 */
@WebServlet(name = "PingJDBCWrite", urlPatterns = { "/servlet/PingJDBCWrite" })
public class PingJDBCWrite extends HttpServlet {

    private static final long serialVersionUID = -4938035109655376503L;
    private static String initTime;
    private static int hitCount;

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {

        String symbol = null;
        BigDecimal newPrice;
        StringBuffer output = new StringBuffer(100);
        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();

        try {
            // get a random symbol to update and a random price.
            symbol = TradeConfig.rndSymbol();
            newPrice = TradeConfig.getRandomPriceChangeFactor();

            // TradeJDBC makes use of prepared statements so I am going to reuse
            // the existing code.
            TradeDirect trade = new TradeDirect();

            // update the price of our symbol
            QuoteDataBean quoteData = null;
            int iter = TradeConfig.getPrimIterations();
            for (int ii = 0; ii < iter; ii++) {
                quoteData = trade.updateQuotePriceVolumeInt(symbol, newPrice, 100.0, false);
            }

            // write the output
            output.append("<html><head><title>Ping JDBC Write w/ Prepared Stmt.</title></head>"
                    + "<body><HR><FONT size=\"+2\" color=\"#000066\">Ping JDBC Write w/ Prep Stmt:</FONT><FONT size=\"-1\" color=\"#000066\"><HR>Init time : "
                    + initTime);
            hitCount++;
            output.append("<BR>Hit Count: " + hitCount);
            output.append("<HR>Update Information<BR>");
            output.append("<BR>" + quoteData.toHTML() + "<HR></FONT></BODY></HTML>");
            out.println(output.toString());

        } catch (Exception e) {
            Log.error(e, "PingJDBCWrite -- error updating quote for symbol", symbol);
            res.sendError(500, "PingJDBCWrite Exception caught: " + e.toString());
        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic JDBC Write using a prepared statment makes use of TradeJDBC code.";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;

    }

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingJDBCWrite.java:PingJDBCWrite.<init>
// Node: StringBuffer
/**
 * (C) Copyright IBM Corporation 2016.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

/**
 * Simple bean to get and set messages
 */

public class PingBean {

    private String msg;

    /**
     * returns the message contained in the bean
     *
     * @return message String
     **/
    public String getMsg() {
        return msg;
    }

    /**
     * sets the message contained in the bean param message String
     **/
    public void setMsg(String s) {
        msg = s;
    }
}

// Node: setMsg
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet2JNDI performs a basic JNDI lookup of a JDBC DataSource
 *
 */

@WebServlet(name = "PingServlet2JNDI", urlPatterns = { "/servlet/PingServlet2JNDI" })
public class PingServlet2JNDI extends HttpServlet {

    private static final long serialVersionUID = -8236271998141415347L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();

        StringBuffer output = new StringBuffer(100);

        try {
            output.append("<html><head><title>Ping JNDI -- lookup of JDBC DataSource</title></head>"
                    + "<body><HR><FONT size=\"+2\" color=\"#000066\">Ping JNDI -- lookup of JDBC DataSource</FONT><HR><FONT size=\"-1\" color=\"#000066\">Init time : "
                    + initTime);
            hitCount++;
            output.append("</FONT><BR>Hit Count: " + hitCount);
            output.append("<HR></body></html>");
            out.println(output.toString());
        } catch (Exception e) {
            Log.error(e, "PingServlet2JNDI -- error look up of a JDBC DataSource");
            res.sendError(500, "PingServlet2JNDI Exception caught: " + e.toString());
        }

    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic JNDI look up of a JDBC DataSource";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2JNDI.java:PingServlet2JNDI.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;

import javax.json.Json;
import javax.json.stream.JsonGenerator;
import javax.json.stream.JsonParser;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingJSONP tests JSON generating and parsing 
 *
 */

@WebServlet(name = "PingJSONP", urlPatterns = { "/servlet/PingJSONP" })
public class PingJSONP extends HttpServlet {


    /**
     * 
     */
    private static final long serialVersionUID = -5348806619121122708L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        try {
            res.setContentType("text/html");

            ServletOutputStream out = res.getOutputStream();
            
            hitCount++;
            
            // JSON generate
            StringWriter sw = new StringWriter();
            JsonGenerator generator = Json.createGenerator(sw);
             
            generator.writeStartObject();
            generator.write("initTime",initTime);
            generator.write("hitCount", hitCount);
            generator.writeEnd();
            generator.flush();
            
            String generatedJSON =  sw.toString();
            StringBuffer parsedJSON = new StringBuffer(); 
            
            // JSON parse
            JsonParser parser = Json.createParser(new StringReader(generatedJSON));
            while (parser.hasNext()) {
               JsonParser.Event event = parser.next();
               switch(event) {
                  case START_ARRAY:
                  case END_ARRAY:
                  case START_OBJECT:
                  case END_OBJECT:
                  case VALUE_FALSE:
                  case VALUE_NULL:
                  case VALUE_TRUE:
                     break;
                  case KEY_NAME:
                      parsedJSON.append(parser.getString() + ":");
                     break;
                  case VALUE_STRING:
                  case VALUE_NUMBER:
                      parsedJSON.append(parser.getString() + " ");
                     break;
               }
            }
            
            out.println("<html><head><title>Ping JSONP</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Ping JSONP</FONT><BR>Generated JSON: " + generatedJSON + "<br>Parsed JSON: " + parsedJSON + "</body></html>");
        } catch (Exception e) {
            Log.error(e, "PingJSONP.doGet(...): general exception caught");
            res.sendError(500, e.toString());

        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic JSON generation and parsing in a servlet";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingJSONP.java:PingJSONP.<init>
// Node: StringWriter
// Node: createGenerator
// Node: writeStartObject
// Node: writeEnd
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.annotation.Resource;
import javax.enterprise.concurrent.ManagedExecutorService;
import javax.servlet.AsyncContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet(asyncSupported=true,name = "PingManagedExecutor", urlPatterns = { "/servlet/PingManagedExecutor" })
public class PingManagedExecutor extends HttpServlet{

	private static final long serialVersionUID = -4695386150928451234L;
	private static String initTime;
    private static int hitCount;

	@Resource 
	private ManagedExecutorService mes;
	
	 /**
     * forwards post requests to the doGet method Creation date: (03/18/2014
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
	protected void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {

    	final AsyncContext asyncContext = req.startAsync();
        final ServletOutputStream out = res.getOutputStream();
    	
    	try {
    		res.setContentType("text/html");
    		    		
    		out.println("<html><head><title>Ping ManagedExecutor</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Ping ManagedExecutor<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time : " + initTime
                    + "<BR><BR></FONT>  </body></html>");
    		   		   		    	
    		// Runnable task
    		mes.submit(new Runnable() {
    			@Override
    			public void run() {
    				try {
						out.println("<b>HitCount: " + ++hitCount  +"</b><br/>");
					} catch (IOException e) {
						e.printStackTrace();
					}
    				asyncContext.complete();
    			}
    		});   		    		
    		
    			 
    	} catch (Exception e) {
			e.printStackTrace();
		}  
    }	
    		
    	
    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Tests a ManagedExecutor";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;
    }
	
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingManagedExecutor.java:PingManagedExecutor.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.AsyncContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletInputStream;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

//import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet31Async tests fundamental dynamic HTML creation functionality through
 * server side servlet processing asynchronously.
 *
 */

@WebServlet(name = "PingServlet30Async", urlPatterns = { "/servlet/PingServlet30Async" }, asyncSupported=true)
public class PingServlet30Async extends HttpServlet {

    private static final long serialVersionUID = 8731300373855056660L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        res.setContentType("text/html");
                        
        AsyncContext ac = req.startAsync();
        StringBuilder sb = new StringBuilder();
        
        ServletInputStream input = req.getInputStream();
        byte[] b = new byte[1024];
        int len = -1;
        while ((len = input.read(b)) != -1) {
            String data = new String(b, 0, len);
            sb.append(data);
        }

        ServletOutputStream output = res.getOutputStream();
        
        output.println("<html><head><title>Ping Servlet 3.0 Async</title></head>"
                + "<body><hr/><br/><font size=\"+2\" color=\"#000066\">Ping Servlet 3.0 Async</font><br/>"
                + "<font size=\"+1\" color=\"#000066\">Init time : " + initTime
                + "</font><br/><br/><b>Hit Count: " + ++hitCount + "</b><br/>Data Received: "+ sb.toString() + "</body></html>");
        
        ac.complete();
    }       


    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doPost(req,res);
          
    }
    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet30Async.java:PingServlet30Async.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet(name = "PingReentryServlet", urlPatterns = { "/servlet/PingReentryServlet" })
public class PingReentryServlet extends HttpServlet {

    private static final long serialVersionUID = -2536027021580175706L;
    
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        try {
            res.setContentType("text/html");

            // The following 2 lines are the difference between PingServlet and
            // PingServletWriter
            // the latter uses a PrintWriter for output versus a binary output
            // stream.
            ServletOutputStream out = res.getOutputStream();
            // java.io.PrintWriter out = res.getWriter();
            int numReentriesLeft; 
            int sleepTime;
            
            if(req.getParameter("numReentries") != null){
                numReentriesLeft = Integer.parseInt(req.getParameter("numReentries"));
            } else {
                numReentriesLeft = 0;
            }
            
            if(req.getParameter("sleep") != null){
                sleepTime = Integer.parseInt(req.getParameter("sleep"));
            } else {
                sleepTime = 0;
            }
                
            if(numReentriesLeft <= 0) {
                Thread.sleep(sleepTime);
                out.println(numReentriesLeft);
            } else {
                String hostname = req.getServerName();
                int port = req.getServerPort();
                req.getContextPath();
                int saveNumReentriesLeft = numReentriesLeft;
                int nextNumReentriesLeft = numReentriesLeft - 1;
                
                // Recursively call into the same server, decrementing the counter by 1.
                String url = "http://" +  hostname + ":" + port + "/" + req.getRequestURI() + 
                        "?numReentries=" +  nextNumReentriesLeft +
                        "&sleep=" + sleepTime;
                URL obj = new URL(url);
                HttpURLConnection con = (HttpURLConnection) obj.openConnection();
                con.setRequestMethod("GET");
                con.setRequestProperty("User-Agent", "Mozilla/5.0");
                
                //Append the recursion count to the response and return it.
                BufferedReader in = new BufferedReader(
                        new InputStreamReader(con.getInputStream()));
                String inputLine;
                StringBuffer response = new StringBuffer();
         
                while ((inputLine = in.readLine()) != null) {
                    response.append(inputLine);
                }
                in.close();
                
                Thread.sleep(sleepTime);
                out.println(saveNumReentriesLeft + response.toString());
            }
        } catch (Exception e) {
            //Log.error(e, "PingReentryServlet.doGet(...): general exception caught");
            res.sendError(500, e.toString());

        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);

    }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingReentryServlet.java:PingReentryServlet.<init>
// Node: getServerName
// Node: getServerPort
// Node: getContextPath
// Node: getRequestURI
// Node: URL
// Node: openConnection
// Node: setRequestMethod
// Node: setRequestProperty
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingJDBCReadPrepStmt uses a prepared statement for database read access. This
 * primative uses
 * {@link com.ibm.websphere.samples.daytrader.direct.TradeDirect} to set the
 * price of a random stock (generated by
 * {@link com.ibm.websphere.samples.daytrader.util.TradeConfig}) through the use
 * of prepared statements.
 *
 */

@WebServlet(name = "PingJDBCRead", urlPatterns = { "/servlet/PingJDBCRead" })
public class PingJDBCRead extends HttpServlet {

    private static final long serialVersionUID = -8810390150632488526L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();
        String symbol = null;
        StringBuffer output = new StringBuffer(100);

        try {
            // TradeJDBC uses prepared statements so I am going to make use of
            // it's code.
            TradeDirect trade = new TradeDirect();
            symbol = TradeConfig.rndSymbol();

            QuoteDataBean quoteData = null;
            int iter = TradeConfig.getPrimIterations();
            for (int ii = 0; ii < iter; ii++) {
                quoteData = trade.getQuote(symbol);
            }

            output.append("<html><head><title>Ping JDBC Read w/ Prepared Stmt.</title></head>"
                    + "<body><HR><FONT size=\"+2\" color=\"#000066\">Ping JDBC Read w/ Prep Stmt:</FONT><HR><FONT size=\"-1\" color=\"#000066\">Init time : "
                    + initTime);
            hitCount++;
            output.append("<BR>Hit Count: " + hitCount);
            output.append("<HR>Quote Information <BR><BR>: " + quoteData.toHTML());
            output.append("<HR></body></html>");
            out.println(output.toString());
        } catch (Exception e) {
            Log.error(e, "PingJDBCRead w/ Prep Stmt -- error getting quote for symbol", symbol);
            res.sendError(500, "PingJDBCRead Exception caught: " + e.toString());
        }

    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic JDBC Read using a prepared statment, makes use of TradeJDBC class";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingJDBCRead.java:PingJDBCRead.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 *
 * PingServlet2Include tests servlet to servlet request dispatching. Servlet 1,
 * the controller, creates a new JavaBean object forwards the servlet request
 * with the JavaBean added to Servlet 2. Servlet 2 obtains access to the
 * JavaBean through the Servlet request object and provides the dynamic HTML
 * output based on the JavaBean data. PingServlet2Servlet is the initial servlet
 * that sends a request to {@link PingServlet2ServletRcv}
 *
 */
@WebServlet(name = "PingServlet2IncludeRcv", urlPatterns = { "/servlet/PingServlet2IncludeRcv" })
public class PingServlet2IncludeRcv extends HttpServlet {

    private static final long serialVersionUID = 2628801298561220872L;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        // do nothing but get included by PingServlet2Include
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2IncludeRcv.java:PingServlet2IncludeRcv.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet2Servlet tests servlet to servlet request dispatching. Servlet 1,
 * the controller, creates a new JavaBean object forwards the servlet request
 * with the JavaBean added to Servlet 2. Servlet 2 obtains access to the
 * JavaBean through the Servlet request object and provides the dynamic HTML
 * output based on the JavaBean data. PingServlet2Servlet is the initial servlet
 * that sends a request to {@link PingServlet2ServletRcv}
 *
 */
@WebServlet(name = "PingServlet2Servlet", urlPatterns = { "/servlet/PingServlet2Servlet" })
public class PingServlet2Servlet extends HttpServlet {
    private static final long serialVersionUID = -955942781902636048L;
    private static int hitCount = 0;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        PingBean ab;
        try {
            ab = new PingBean();
            hitCount++;
            ab.setMsg("Hit Count: " + hitCount);
            req.setAttribute("ab", ab);

            getServletConfig().getServletContext().getRequestDispatcher("/servlet/PingServlet2ServletRcv").forward(req, res);
        } catch (Exception ex) {
            Log.error(ex, "PingServlet2Servlet.doGet(...): general exception");
            res.sendError(500, "PingServlet2Servlet.doGet(...): general exception" + ex.toString());

        }
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2Servlet.java:PingServlet2Servlet.<init>
// Node: PingBean
// Node: forward
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

/**
 *
 * PingServletSetContentLength tests fundamental dynamic HTML creation
 * functionality through server side servlet processing.
 *
 */

@WebServlet(name = "PingServletLargeContentLength", urlPatterns = { "/servlet/PingServletLargeContentLength" })
public class PingServletLargeContentLength extends HttpServlet {



    /**
     * 
     */
    private static final long serialVersionUID = -7979576220528252408L;

    /**
     * forwards post requests to the doGet method Creation date: (02/07/2013
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        System.out.println("Length: " + req.getContentLengthLong());
        
        
        
        
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
       doPost(req,res);    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet, with " + "contentLength set by contentLength parameter.";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServletLargeContentLength.java:PingServletLargeContentLength.<init>
// Node: getContentLengthLong
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet2DB tests the path of a servlet making a JDBC connection to a
 * database
 *
 */

@WebServlet(name = "PingServlet2DB", urlPatterns = { "/servlet/PingServlet2DB" })
public class PingServlet2DB extends HttpServlet {

    private static final long serialVersionUID = -6456675185605592049L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();
        String symbol = null;
        StringBuffer output = new StringBuffer(100);

        try {
            // TradeJDBC uses prepared statements so I am going to make use of
            // it's code.
            TradeDirect trade = new TradeDirect();
            trade.getConnPublic();

            output.append("<html><head><title>PingServlet2DB.</title></head>"
                    + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2DB:</FONT><HR><FONT size=\"-1\" color=\"#000066\">Init time : " + initTime);
            hitCount++;
            output.append("<BR>Hit Count: " + hitCount);
            output.append("<HR></body></html>");
            out.println(output.toString());
        } catch (Exception e) {
            Log.error(e, "PingServlet2DB -- error getting connection to the database", symbol);
            res.sendError(500, "PingServlet2DB Exception caught: " + e.toString());
        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic JDBC Read using a prepared statment, makes use of TradeJDBC class";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2DB.java:PingServlet2DB.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet2Servlet tests servlet to servlet request dispatching. Servlet 1,
 * the controller, creates a new JavaBean object forwards the servlet request
 * with the JavaBean added to Servlet 2. Servlet 2 obtains access to the
 * JavaBean through the Servlet request object and provides the dynamic HTML
 * output based on the JavaBean data. PingServlet2ServletRcv receives a request
 * from {@link PingServlet2Servlet} and displays output.
 *
 */
@WebServlet(name = "PingServlet2ServletRcv", urlPatterns = { "/servlet/PingServlet2ServletRcv" })
public class PingServlet2ServletRcv extends HttpServlet {
    private static final long serialVersionUID = -5241563129216549706L;
    private static String initTime = null;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        PingBean ab;
        try {
            ab = (PingBean) req.getAttribute("ab");
            res.setContentType("text/html");
            PrintWriter out = res.getWriter();
            out.println("<html><head><title>Ping Servlet2Servlet</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">PingServlet2Servlet:<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time: "
                    + initTime + "</FONT><BR><BR><B>Message from Servlet: </B>" + ab.getMsg() + "</body></html>");
        } catch (Exception ex) {
            Log.error(ex, "PingServlet2ServletRcv.doGet(...): general exception");
            res.sendError(500, "PingServlet2ServletRcv.doGet(...): general exception" + ex.toString());
        }

    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2ServletRcv.java:PingServlet2ServletRcv.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingServlet2Include tests servlet to servlet request dispatching. Servlet 1,
 * the controller, creates a new JavaBean object forwards the servlet request
 * with the JavaBean added to Servlet 2. Servlet 2 obtains access to the
 * JavaBean through the Servlet request object and provides the dynamic HTML
 * output based on the JavaBean data. PingServlet2Servlet is the initial servlet
 * that sends a request to {@link PingServlet2ServletRcv}
 *
 */
@WebServlet(name = "PingServlet2Include", urlPatterns = { "/servlet/PingServlet2Include" })
public class PingServlet2Include extends HttpServlet {

    private static final long serialVersionUID = 1063447780151198793L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {

        try {
            res.setContentType("text/html");

            int iter = TradeConfig.getPrimIterations();
            for (int ii = 0; ii < iter; ii++) {
                getServletConfig().getServletContext().getRequestDispatcher("/servlet/PingServlet2IncludeRcv").include(req, res);
            }

            // ServletOutputStream out = res.getOutputStream();
            java.io.PrintWriter out = res.getWriter();
            out.println("<html><head><title>Ping Servlet 2 Include</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Ping Servlet 2 Include<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time : "
                    + initTime + "<BR><BR></FONT>  <B>Hit Count: " + hitCount++ + "</B></body></html>");
        } catch (Exception ex) {
            Log.error(ex, "PingServlet2Include.doGet(...): general exception");
            res.sendError(500, "PingServlet2Include.doGet(...): general exception" + ex.toString());
        }
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;
    }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2Include.java:PingServlet2Include.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingHTTPSession1 - SessionID tests fundamental HTTP session functionality by
 * creating a unique session ID for each individual user. The ID is stored in
 * the users session and is accessed and displayed on each user request.
 *
 */
@WebServlet(name = "PingSession1", urlPatterns = { "/servlet/PingSession1" })
public class PingSession1 extends HttpServlet {
    private static final long serialVersionUID = -3703858656588519807L;
    private static int count;
    // For each new session created, add a session ID of the form "sessionID:" +
    // count
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        HttpSession session = null;
        try {
            try {
                // get the users session, if the user does not have a session
                // create one.
                session = request.getSession(true);
            } catch (Exception e) {
                Log.error(e, "PingSession1.doGet(...): error getting session");
                // rethrow the exception for handling in one place.
                throw e;
            }

            // Get the session data value
            Integer ival = (Integer) session.getAttribute("sessiontest.counter");
            // if their is not a counter create one.
            if (ival == null) {
                ival = new Integer(count++);
                session.setAttribute("sessiontest.counter", ival);
            }
            String SessionID = "SessionID:" + ival.toString();

            // Output the page
            response.setContentType("text/html");
            response.setHeader("SessionKeyTest-SessionID", SessionID);

            PrintWriter out = response.getWriter();
            out.println("<html><head><title>HTTP Session Key Test</title></head><body><HR><BR><FONT size=\"+2\" color=\"#000066\">HTTP Session Test 1: Session Key<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time: "
                    + initTime + "</FONT><BR><BR>");
            hitCount++;
            out.println("<B>Hit Count: " + hitCount + "<BR>Your HTTP Session key is " + SessionID + "</B></body></html>");
        } catch (Exception e) {
            // log the excecption
            Log.error(e, "PingSession1.doGet(..l.): error.");
            // set the server responce to 500 and forward to the web app defined
            // error page
            response.sendError(500, "PingSession1.doGet(...): error. " + e.toString());
        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/

    @Override
    public String getServletInfo() {
        return "HTTP Session Key: Tests management of a read only unique id";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        count = 0;
        hitCount = 0;
        initTime = new java.util.Date().toString();

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingSession1.java:PingSession1.<init>
// Node: setHeader
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet extends PingServlet by using a PrintWriter for formatted output
 * vs. the output stream used by {@link PingServlet}.
 *
 */
@WebServlet(name = "PingServletWriter", urlPatterns = { "/servlet/PingServletWriter" })
public class PingServletWriter extends HttpServlet {

    private static final long serialVersionUID = -267847365014523225L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        try {
            res.setContentType("text/html");

            // The following 2 lines are the difference between PingServlet and
            // PingServletWriter
            // the latter uses a PrintWriter for output versus a binary output
            // stream.
            // ServletOutputStream out = res.getOutputStream();
            java.io.PrintWriter out = res.getWriter();
            hitCount++;
            out.println("<html><head><title>Ping Servlet Writer</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Ping Servlet Writer:<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time : "
                    + initTime + "<BR><BR></FONT>  <B>Hit Count: " + hitCount + "</B></body></html>");
        } catch (Exception e) {
            Log.error(e, "PingServletWriter.doGet(...): general exception caught");
            res.sendError(500, e.toString());
        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/

    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet using a PrintWriter";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServletWriter.java:PingServletWriter.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingHTTPSession3 tests the servers ability to manage and persist large
 * HTTPSession data objects. The servlet creates the large custom java object
 * {@link PingSession3Object}. This large session object is retrieved and stored
 * to the session on each user request. The default settings result in approx
 * 2024 bits being retrieved and stored upon each request.
 *
 */
@WebServlet(name = "PingSession3", urlPatterns = { "/servlet/PingSession3" })
public class PingSession3 extends HttpServlet {
    private static final long serialVersionUID = -6129599971684210414L;
    private static int NUM_OBJECTS = 2;
    private static String initTime = null;
    private static int hitCount = 0;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {

        PrintWriter out = response.getWriter();
        // Using a StringBuffer to output all at once.
        StringBuffer outputBuffer = new StringBuffer();
        HttpSession session = null;
        PingSession3Object[] sessionData;
        response.setContentType("text/html");

        // this is a general try/catch block. The catch block at the end of this
        // will forward the responce
        // to an error page if there is an exception
        try {

            try {
                session = request.getSession(true);
            } catch (Exception e) {
                Log.error(e, "PingSession3.doGet(...): error getting session");
                // rethrow the exception for handling in one place.
                throw e;

            }
            // Each PingSession3Object in the PingSession3Object array is 1K in
            // size
            // NUM_OBJECTS sets the size of the array to allocate and thus set
            // the size in KBytes of the session object
            // NUM_OBJECTS can be initialized by the servlet
            // Here we check for the request parameter to change the size and
            // invalidate the session if it exists
            // NOTE: Current user sessions will remain the same (i.e. when
            // NUM_OBJECTS is changed, all user thread must be restarted
            // for the change to fully take effect

            String num_objects;
            if ((num_objects = request.getParameter("num_objects")) != null) {
                // validate input
                try {
                    int x = Integer.parseInt(num_objects);
                    if (x > 0) {
                        NUM_OBJECTS = x;
                    }
                } catch (Exception e) {
                    Log.error(e, "PingSession3.doGet(...): input should be an integer, input=" + num_objects);
                } // revert to current value on exception

                outputBuffer.append("<html><head> Session object size set to " + NUM_OBJECTS + "K bytes </head><body></body></html>");
                if (session != null) {
                    session.invalidate();
                }
                out.print(outputBuffer.toString());
                out.close();
                return;
            }

            // Get the session data value
            sessionData = (PingSession3Object[]) session.getAttribute("sessiontest.sessionData");
            if (sessionData == null) {
                sessionData = new PingSession3Object[NUM_OBJECTS];
                for (int i = 0; i < NUM_OBJECTS; i++) {
                    sessionData[i] = new PingSession3Object();
                }
            }

            session.setAttribute("sessiontest.sessionData", sessionData);

            // Each PingSession3Object is about 1024 bits, there are 8 bits in a
            // byte.
            int num_bytes = (NUM_OBJECTS * 1024) / 8;
            response.setHeader("SessionTrackingTest-largeSessionData", num_bytes + "bytes");

            outputBuffer
                    .append("<html><head><title>Session Large Data Test</title></head><body><HR><BR><FONT size=\"+2\" color=\"#000066\">HTTP Session Test 3: Large Data<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time: ")
                    .append(initTime).append("</FONT><BR><BR>");
            hitCount++;
            outputBuffer.append("<B>Hit Count: ").append(hitCount)
                    .append("<BR>Session object updated. Session Object size = " + num_bytes + " bytes </B></body></html>");
            // output the Buffer to the printWriter.
            out.println(outputBuffer.toString());

        } catch (Exception e) {
            // log the excecption
            Log.error(e, "PingSession3.doGet(..l.): error.");
            // set the server responce to 500 and forward to the web app defined
            // error page
            response.sendError(500, "PingSession3.doGet(...): error. " + e.toString());
        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "HTTP Session Object: Tests management of a large custom session class";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingSession3.java:PingSession3.<init>
// Node: same
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet2JSP tests a call from a servlet to a JavaServer Page providing
 * server-side dynamic HTML through JSP scripting.
 *
 */
@WebServlet(name = "PingServlet2Jsp", urlPatterns = { "/servlet/PingServlet2Jsp" })
public class PingServlet2Jsp extends HttpServlet {
    private static final long serialVersionUID = -5199543766883932389L;
    private static int hitCount = 0;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        PingBean ab;
        try {
            ab = new PingBean();
            hitCount++;
            ab.setMsg("Hit Count: " + hitCount);
            req.setAttribute("ab", ab);

            getServletConfig().getServletContext().getRequestDispatcher("/PingServlet2Jsp.jsp").forward(req, res);
        } catch (Exception ex) {
            Log.error(ex, "PingServlet2Jsp.doGet(...): request error");
            res.sendError(500, "PingServlet2Jsp.doGet(...): request error" + ex.toString());

        }
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2Jsp.java:PingServlet2Jsp.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingHTTPSession2 session create/destroy further extends the previous test by
 * invalidating the HTTP Session on every 5th user access. This results in
 * testing HTTPSession create and destroy
 *
 */
@WebServlet(name = "PingSession2", urlPatterns = { "/servlet/PingSession2" })
public class PingSession2 extends HttpServlet {

    private static final long serialVersionUID = -273579463475455800L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
        HttpSession session = null;
        try {
            try {
                session = request.getSession(true);
            } catch (Exception e) {
                Log.error(e, "PingSession2.doGet(...): error getting session");
                // rethrow the exception for handling in one place.
                throw e;

            }

            // Get the session data value
            Integer ival = (Integer) session.getAttribute("sessiontest.counter");
            // if there is not a counter then create one.
            if (ival == null) {
                ival = new Integer(1);
            } else {
                ival = new Integer(ival.intValue() + 1);
            }
            session.setAttribute("sessiontest.counter", ival);
            // if the session count is equal to five invalidate the session
            if (ival.intValue() == 5) {
                session.invalidate();
            }

            try {
                // Output the page
                response.setContentType("text/html");
                response.setHeader("SessionTrackingTest-counter", ival.toString());

                PrintWriter out = response.getWriter();
                out.println("<html><head><title>Session Tracking Test 2</title></head><body><HR><BR><FONT size=\"+2\" color=\"#000066\">HTTP Session Test 2: Session create/invalidate <BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time: "
                        + initTime + "</FONT><BR><BR>");
                hitCount++;
                out.println("<B>Hit Count: " + hitCount + "<BR>Session hits: " + ival + "</B></body></html>");
            } catch (Exception e) {
                Log.error(e, "PingSession2.doGet(...): error getting session information");
                // rethrow the exception for handling in one place.
                throw e;
            }

        }

        catch (Exception e) {
            // log the excecption
            Log.error(e, "PingSession2.doGet(...): error.");
            // set the server responce to 500 and forward to the web app defined
            // error page
            response.sendError(500, "PingSession2.doGet(...): error. " + e.toString());
        }
    } // end of the method

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "HTTP Session Key: Tests management of a read/write unique id";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingSession2.java:PingSession2.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet tests fundamental dynamic HTML creation functionality through
 * server side servlet processing.
 *
 */

@WebServlet(name = "PingServlet", urlPatterns = { "/servlet/PingServlet" })
public class PingServlet extends HttpServlet {

	private static final long serialVersionUID = 7097023236709683760L;
	private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        try {
            res.setContentType("text/html");

            // The following 2 lines are the difference between PingServlet and
            // PingServletWriter
            // the latter uses a PrintWriter for output versus a binary output
            // stream.
            ServletOutputStream out = res.getOutputStream();
            // java.io.PrintWriter out = res.getWriter();
            hitCount++;
            out.println("<html><head><title>Ping Servlet</title></head>"
                    + "<body><HR><BR><FONT size=\"+2\" color=\"#000066\">Ping Servlet<BR></FONT><FONT size=\"+1\" color=\"#000066\">Init time : " + initTime
                    + "<BR><BR></FONT>  <B>Hit Count: " + hitCount + "</B></body></html>");
        } catch (Exception e) {
            Log.error(e, "PingServlet.doGet(...): general exception caught");
            res.sendError(500, e.toString());

        }
    }

    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet.java:PingServlet.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import java.util.Queue;
import java.util.concurrent.LinkedBlockingQueue;

import javax.servlet.AsyncContext;
import javax.servlet.ReadListener;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletInputStream;
import javax.servlet.ServletOutputStream;
import javax.servlet.WriteListener;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

//import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet31Async tests fundamental dynamic HTML creation functionality through
 * server side servlet processing asynchronously with non-blocking i/o.
 *
 */

@WebServlet(name = "PingServlet31Async", urlPatterns = { "/servlet/PingServlet31Async" }, asyncSupported=true)
public class PingServlet31Async extends HttpServlet {

    private static final long serialVersionUID = 8731300373855056660L;
    private static String initTime;
    private static int hitCount;

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        res.setContentType("text/html");
                
        AsyncContext ac = req.startAsync();
           
        ServletInputStream input = req.getInputStream();
        ReadListener readListener = new ReadListenerImpl(input, res, ac);
        input.setReadListener(readListener);
    }

    class ReadListenerImpl implements ReadListener {
        private ServletInputStream input = null;
        private HttpServletResponse res = null;
        private AsyncContext ac = null;
        private Queue<String> queue = new LinkedBlockingQueue<String>();

        ReadListenerImpl(ServletInputStream in, HttpServletResponse r, AsyncContext c) {
            input = in;
            res = r;
            ac = c;
        }
    
        public void onDataAvailable() throws IOException {
            StringBuilder sb = new StringBuilder();
            int len = -1;
            byte b[] = new byte[1024];
            
            while (input.isReady() && (len = input.read(b)) != -1) {
                String data = new String(b, 0, len);
                sb.append(data);
            }
            queue.add(sb.toString());
            
        }
    
        public void onAllDataRead() throws IOException {
            ServletOutputStream output = res.getOutputStream();
            WriteListener writeListener = new WriteListenerImpl(output, queue, ac);
            output.setWriteListener(writeListener);
        }
    
        public void onError(final Throwable t) {
            ac.complete();
            t.printStackTrace();
        }
    }
    
    class WriteListenerImpl implements WriteListener {
        private ServletOutputStream output = null;
        private Queue<String> queue = null;
        private AsyncContext ac = null;

        WriteListenerImpl(ServletOutputStream sos, Queue<String> q, AsyncContext c) {
            output = sos;
            queue = q;
            ac = c;
            
            try {
                output.print("<html><head><title>Ping Servlet 3.1 Async</title></head>"
                        + "<body><hr/><br/><font size=\"+2\" color=\"#000066\">Ping Servlet 3.1 Async</font>"
                        + "<br/><font size=\"+1\" color=\"#000066\">Init time : " + initTime
                        + "</font><br/><br/><b>Hit Count: " + ++hitCount + "</b><br/>Data Received: ");
            } catch (IOException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }

        public void onWritePossible() throws IOException {
            
            while (queue.peek() != null && output.isReady()) {
                String data = (String) queue.poll();
                output.print(data);
            }
            
            if (queue.peek() == null) {
                output.println("</body></html>");
                ac.complete();
            }
        }

        public void onError(final Throwable t) {
            ac.complete();
            t.printStackTrace();
        }
    }
        


    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doPost(req,res);          
    }
    /**
     * returns a string of information about the servlet
     *
     * @return info String: contains info about the servlet
     **/
    @Override
    public String getServletInfo() {
        return "Basic dynamic HTML generation through a servlet";
    }

    /**
     * called when the class is loaded to initialize the servlet
     *
     * @param config
     *            ServletConfig:
     **/
    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        initTime = new java.util.Date().toString();
        hitCount = 0;

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet31Async.java:PingServlet31Async.<init>
// Node: WriteListenerImpl
// Node: setWriteListener
// Node: onWritePossible
// Node: peek
// Node: poll
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;
import java.net.URL;
import java.net.URLConnection;

import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *
 * PingServlet2PDF tests a call to a servlet which then loads a PDF document.
 *
 */
@WebServlet(name = "PingServlet2PDF", urlPatterns = { "/servlet/PingServlet2PDF" })
public class PingServlet2PDF extends HttpServlet {

    private static final long serialVersionUID = -1321793174442755868L;
    private static int hitCount = 0;
    private static final int BUFFER_SIZE = 1024 * 8; // 8 KB

    /**
     * forwards post requests to the doGet method Creation date: (11/6/2000
     * 10:52:39 AM)
     *
     * @param res
     *            javax.servlet.http.HttpServletRequest
     * @param res2
     *            javax.servlet.http.HttpServletResponse
     */
    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    /**
     * this is the main method of the servlet that will service all get
     * requests.
     *
     * @param request
     *            HttpServletRequest
     * @param responce
     *            HttpServletResponce
     **/
    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        PingBean ab;
        BufferedInputStream bis = null;
        BufferedOutputStream bos = null;
        try {
            ab = new PingBean();
            hitCount++;
            ab.setMsg("Hit Count: " + hitCount);
            req.setAttribute("ab", ab);

            ServletOutputStream out = res.getOutputStream();

            // MIME type for pdf doc
            res.setContentType("application/pdf");

            // Open an InputStream to the PDF document
            String fileURL = "http://localhost:9080/daytrader/WAS_V7_64-bit_performance.pdf";
            URL url = new URL(fileURL);
            URLConnection conn = url.openConnection();
            bis = new BufferedInputStream(conn.getInputStream());

            // Transfer the InputStream (PDF Document) to OutputStream (servlet)
            bos = new BufferedOutputStream(out);
            byte[] buff = new byte[BUFFER_SIZE];
            int bytesRead;
            // Simple read/write loop.
            while (-1 != (bytesRead = bis.read(buff, 0, buff.length))) {
                bos.write(buff, 0, bytesRead);
            }

        } catch (Exception ex) {
            Log.error(ex, "PingServlet2Jsp.doGet(...): request error");
            res.sendError(500, "PingServlet2Jsp.doGet(...): request error" + ex.toString());

        }

        finally {
            if (bis != null) {
                bis.close();
            }
            if (bos != null) {
                bos.close();
            }
        }

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingServlet2PDF.java:PingServlet2PDF.<init>
// Node: BufferedInputStream
// Node: InputStream
// Node: OutputStream
// Node: BufferedOutputStream
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.ibm.websphere.samples.daytrader.web.prims;

import java.io.IOException;

import javax.servlet.ReadListener;
import javax.servlet.ServletException;
import javax.servlet.ServletInputStream;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpUpgradeHandler;
import javax.servlet.http.WebConnection;
import javax.servlet.annotation.WebServlet;

import com.ibm.websphere.samples.daytrader.util.Log;

@WebServlet(name = "PingUpgradeServlet", urlPatterns = { "/servlet/PingUpgradeServlet" }, asyncSupported=true)
public class PingUpgradeServlet extends HttpServlet {
    private static final long serialVersionUID = -6955518532146927509L;
   

    @Override
    protected void doGet(final HttpServletRequest req, final HttpServletResponse res) throws ServletException, IOException {
        doPost(req,res);
    }
    
    @Override
    protected void doPost(final HttpServletRequest req, final HttpServletResponse res) throws ServletException, IOException {
      
        if (Log.doTrace()) {
            Log.trace("PingUpgradeServlet:doPost");
        }
        
        if ("echo".equals(req.getHeader("Upgrade"))) {
            
            if (Log.doTrace()) {
                Log.trace("PingUpgradeServlet:doPost -- found echo, doing upgrade");
            }
            
            res.setStatus(101);
            res.setHeader("Upgrade", "echo");
            res.setHeader("Connection", "Upgrade");

            req.upgrade(Handler.class);          
          
        } else {
            
            if (Log.doTrace()) {
                Log.trace("PingUpgradeServlet:doPost -- did not find echo, no upgrade");
            }
            
            res.getWriter().println("No upgrade: " + req.getHeader("Upgrade"));
        }
    }

    public static class Handler implements HttpUpgradeHandler {
    
        @Override
        public void init(final WebConnection wc) {
            Listener listener = null;
            try {
                listener = new Listener(wc);
              
            } catch (IOException e1) {
                // TODO Auto-generated catch block
                e1.printStackTrace();
            }
      
            try {
                
                if (Log.doTrace()) {
                    Log.trace("PingUpgradeServlet$Handler.init() -- Initializing Handler");
                }
          
                // flush headers if any
                wc.getOutputStream().flush();
                wc.getInputStream().setReadListener(listener);
        
            } catch (IOException e) {
                throw new IllegalArgumentException(e);
            }
        }

        @Override
        public void destroy() {
            if (Log.doTrace()) {
                Log.trace("PingUpgradeServlet$Handler.destroy() -- Destroying Handler");
            }
        }
    }

    private static class Listener implements ReadListener {
        private final WebConnection connection;
        private ServletInputStream input = null;
        private ServletOutputStream output = null;
        
        private Listener(final WebConnection connection) throws IOException  {
            this.connection = connection;
            this.input = connection.getInputStream();
            this.output = connection.getOutputStream();
        }

        @Override
        public void onDataAvailable() throws IOException {
            
            if (Log.doTrace()) {
                Log.trace("PingUpgradeServlet$Listener.onDataAvailable() called");
            }
            
            byte[] data = new byte[1024];
            int len = -1;
            
            while (input.isReady()  && (len = input.read(data)) != -1) {
                    String dataRead = new String(data, 0, len);
                    
                    if (Log.doTrace()) {
                        Log.trace("PingUpgradeServlet$Listener.onDataAvailable() -- Adding data to queue -->" + dataRead + "<--");
                    }
                    
                    output.println(dataRead);
                    output.flush();
            }
            
            closeConnection();
        }

        private void closeConnection() {
            try {
                connection.close();
            } catch (Exception e) {
                if (Log.doTrace()) {
                    Log.error(e.toString());
                }
            }
        }
        
        
        @Override
        public void onAllDataRead() throws IOException {
            closeConnection();
        }

        @Override
        public void onError(final Throwable t) {
            closeConnection();
        }
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/PingUpgradeServlet.java:PingUpgradeServlet.<init>
// Node: getHeader
// Node: setStatus
// Node: upgrade
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;

import javax.ejb.EJB;
import javax.naming.InitialContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingServlet2Session2Entity tests key functionality of a servlet call to a
 * stateless SessionEJB, and then to a Entity EJB representing data in a
 * database. This servlet makes use of the Stateless Session EJB {@link Trade},
 * and then uses {@link TradeConfig} to generate a random stock symbol. The
 * stocks price is looked up using the Quote Entity EJB.
 *
 */
@WebServlet(name = "ejb3.PingServlet2Session2Entity", urlPatterns = { "/ejb3/PingServlet2Session2Entity" })
public class PingServlet2Session2Entity extends HttpServlet {

    private static final long serialVersionUID = -5043457201022265012L;

    private static String initTime;

    private static int hitCount;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal")
    private TradeSLSBBean tradeSLSBLocal;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();
        String symbol = null;
        QuoteDataBean quoteData = null;
        StringBuffer output = new StringBuffer(100);

        output.append("<html><head><title>PingServlet2Session2Entity</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2Session2Entity<BR></FONT>" + "<FONT size=\"-1\" color=\"#000066\">"
                + "PingServlet2Session2Entity tests the common path of a Servlet calling a Session EJB " + "which in turn calls an Entity EJB.<BR>");

        try {
            try {
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    symbol = TradeConfig.rndSymbol();
                    // getQuote will call findQuote which will instaniate the
                    // Quote Entity Bean
                    // and then will return a QuoteObject
                    quoteData = tradeSLSBLocal.getQuote(symbol);
                }
            } catch (Exception ne) {
                Log.error(ne, "PingServlet2Session2Entity.goGet(...): exception getting QuoteData through Trade");
                throw ne;
            }

            output.append("<HR>initTime: " + initTime).append("<BR>Hit Count: " + hitCount++);
            output.append("<HR>Quote Information<BR><BR>" + quoteData.toHTML());
            out.println(output.toString());

        } catch (Exception e) {
            Log.error(e, "PingServlet2Session2Entity.doGet(...): General Exception caught");
            res.sendError(500, "General Exception caught, " + e.toString());
        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, tests Servlet to Session to Entity EJB path";

    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();

        if (tradeSLSBLocal == null) {
            Log.error("PingServlet2Session2Entity:init - Injection of tradeSLSBLocal failed - performing JNDI lookup!");

            try {
                InitialContext context = new InitialContext();
                tradeSLSBLocal = (TradeSLSBBean) context.lookup("java:comp/env/ejb/TradeSLSBBean");
            } catch (Exception ex) {
                Log.error("PingServlet2Session2Entity:init - Lookup of tradeSLSBLocal failed!!!");
                ex.printStackTrace();
            }
        }
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2Session2Entity.java:PingServlet2Session2Entity.<init>
// Node: EJB
// Node: goGet
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;

import javax.ejb.EJB;
import javax.naming.InitialContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingServlet2Session2Entity tests key functionality of a servlet call to a
 * stateless SessionEJB, and then to a Entity EJB representing data in a
 * database. This servlet makes use of the Stateless Session EJB {@link Trade},
 * and then uses {@link TradeConfig} to generate a random stock symbol. The
 * stocks price is looked up using the Quote Entity EJB.
 *
 */
@WebServlet(name = "ejb3.PingServlet2Session2Entity2JSP", urlPatterns = { "/ejb3/PingServlet2Session2Entity2JSP" })
public class PingServlet2Session2Entity2JSP extends HttpServlet {

    private static final long serialVersionUID = -8966014710582651693L;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal")
    private TradeSLSBBean tradeSLSBLocal;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {
        String symbol = null;
        QuoteDataBean quoteData = null;
        ServletContext ctx = getServletConfig().getServletContext();

        try {
            try {
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    symbol = TradeConfig.rndSymbol();
                    // getQuote will call findQuote which will instaniate the
                    // Quote Entity Bean
                    // and then will return a QuoteObject
                    quoteData = tradeSLSBLocal.getQuote(symbol);
                }

                req.setAttribute("quoteData", quoteData);
                // req.setAttribute("hitCount", hitCount);
                // req.setAttribute("initTime", initTime);

                ctx.getRequestDispatcher("/quoteDataPrimitive.jsp").include(req, res);
            } catch (Exception ne) {
                Log.error(ne, "PingServlet2Session2Entity2JSP.goGet(...): exception getting QuoteData through Trade");
                throw ne;
            }

        } catch (Exception e) {
            Log.error(e, "PingServlet2Session2Entity2JSP.doGet(...): General Exception caught");
            res.sendError(500, "General Exception caught, " + e.toString());
        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, tests Servlet to Session to Entity EJB to JSP path";

    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        // hitCount = 0;
        // initTime = new java.util.Date().toString();

        if (tradeSLSBLocal == null) {
            Log.error("PingServlet2Session2Entity2JSP:init - Injection of tradeSLSBLocal failed - performing JNDI lookup!");

            try {
                InitialContext context = new InitialContext();
                tradeSLSBLocal = (TradeSLSBBean) context.lookup("java:comp/env/ejb/TradeSLSBBean");
            } catch (Exception ex) {
                Log.error("PingServlet2Session2EntityJSP:init - Lookup of tradeSLSBLocal failed!!!");
                ex.printStackTrace();
            }
        }
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2Session2Entity2JSP.java:PingServlet2Session2Entity2JSP.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;

import javax.ejb.EJB;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBBean;
import com.ibm.websphere.samples.daytrader.entities.AccountProfileDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * Primitive to test Entity Container Managed Relationshiop One to One Servlet
 * will generate a random userID and get the profile for that user using a
 * {@link trade.Account} Entity EJB This tests the common path of a Servlet
 * calling a Session to Entity EJB to get CMR One to One data
 *
 */
@WebServlet(name = "ejb3.PingServlet2Session2CMR2One2One", urlPatterns = { "/ejb3/PingServlet2Session2CMR2One2One" })
public class PingServlet2Session2CMROne2One extends HttpServlet {
    private static final long serialVersionUID = 567062418489199248L;

    private static String initTime;

    private static int hitCount;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal")
    private TradeSLSBBean tradeSLSBLocal;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();

        String userID = null;

        StringBuffer output = new StringBuffer(100);
        output.append("<html><head><title>Servlet2Session2CMROne20ne</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2Session2CMROne2One<BR></FONT>"
                + "<FONT size=\"-1\" color=\"#000066\"><BR>PingServlet2Session2CMROne2One uses the Trade Session EJB"
                + " to get the profile for a user using an EJB 3.0 CMR one to one relationship");
        try {

            AccountProfileDataBean accountProfileData = null;
            int iter = TradeConfig.getPrimIterations();
            for (int ii = 0; ii < iter; ii++) {
                userID = TradeConfig.rndUserID();
                // get the price and print the output.
                accountProfileData = tradeSLSBLocal.getAccountProfileData(userID);
            }

            output.append("<HR>initTime: " + initTime + "<BR>Hit Count: ").append(hitCount++);
            output.append("<HR>One to One CMR access of AccountProfile Information from Account Entity<BR><BR> " + accountProfileData.toHTML());
            output.append("</font><HR></body></html>");
            out.println(output.toString());
        } catch (Exception e) {
            Log.error(e, "PingServlet2Session2CMROne2One.doGet(...): error");
            // this will send an Error to teh web applications defined error
            // page.
            res.sendError(500, "PingServlet2Session2CMROne2One.doGet(...): error" + e.toString());

        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, tests Servlet to Entity EJB path";
    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2Session2CMROne2One.java:PingServlet2Session2CMROne2One.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;
import java.util.Collection;
import java.util.Iterator;

import javax.ejb.EJB;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBBean;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * Primitive to test Entity Container Managed Relationshiop One to One Servlet
 * will generate a random userID and get the profile for that user using a
 * {@link trade.Account} Entity EJB This tests the common path of a Servlet
 * calling a Session to Entity EJB to get CMR One to One data
 *
 */
@WebServlet(name = "ejb3.PingServlet2Session2CMR2One2Many", urlPatterns = { "/ejb3/PingServlet2Session2CMR2One2Many" })
public class PingServlet2Session2CMROne2Many extends HttpServlet {
    private static final long serialVersionUID = -8658929449987440032L;

    private static String initTime;

    private static int hitCount;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal")
    private TradeSLSBBean tradeSLSBLocal;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();

        String userID = null;

        StringBuffer output = new StringBuffer(100);
        output.append("<html><head><title>Servlet2Session2CMROne20ne</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2Session2CMROne2Many<BR></FONT>"
                + "<FONT size=\"-1\" color=\"#000066\"><BR>PingServlet2Session2CMROne2Many uses the Trade Session EJB"
                + " to get the orders for a user using an EJB 3.0 Entity CMR one to many relationship");
        try {

            Collection<?> orderDataBeans = null;
            int iter = TradeConfig.getPrimIterations();
            for (int ii = 0; ii < iter; ii++) {
                userID = TradeConfig.rndUserID();

                // get the users orders and print the output.
                orderDataBeans = tradeSLSBLocal.getOrders(userID);
            }

            output.append("<HR>initTime: " + initTime + "<BR>Hit Count: ").append(hitCount++);
            output.append("<HR>One to Many CMR access of Account Orders from Account Entity<BR> ");
            output.append("<HR>User: " + userID + " currently has " + orderDataBeans.size() + " stock orders:");
            Iterator<?> it = orderDataBeans.iterator();
            while (it.hasNext()) {
                OrderDataBean orderData = (OrderDataBean) it.next();
                output.append("<BR>" + orderData.toHTML());
            }
            output.append("</font><HR></body></html>");
            out.println(output.toString());
        } catch (Exception e) {
            Log.error(e, "PingServlet2Session2CMROne2Many.doGet(...): error");
            // this will send an Error to teh web applications defined error
            // page.
            res.sendError(500, "PingServlet2Session2CMROne2Many.doGet(...): error" + e.toString());

        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, tests Servlet to Entity EJB path";
    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2Session2CMROne2Many.java:PingServlet2Session2CMROne2Many.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;

import javax.ejb.EJB;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingServlet2TwoPhase tests key functionality of a TwoPhase commit In this
 * primitive a servlet calls a Session EJB which begins a global txn The Session
 * EJB then reads a DB row and sends a message to JMS Queue The txn is closed w/
 * a 2-phase commit
 *
 */
@WebServlet(name = "ejb3.PingServlet2TwoPhase", urlPatterns = { "/ejb3/PingServlet2TwoPhase" })
public class PingServlet2TwoPhase extends HttpServlet {

    private static final long serialVersionUID = -1563251786527079548L;

    private static String initTime;

    private static int hitCount;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal")
    private TradeSLSBBean tradeSLSBLocal;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();
        String symbol = null;
        QuoteDataBean quoteData = null;
        StringBuffer output = new StringBuffer(100);

        output.append("<html><head><title>PingServlet2TwoPhase</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2TwoPhase<BR></FONT>" + "<FONT size=\"-1\" color=\"#000066\">"
                + "PingServlet2TwoPhase tests the path of a Servlet calling a Session EJB "
                + "which in turn calls an Entity EJB to read a DB row (quote). The Session EJB " + "then posts a message to a JMS Queue. "
                + "<BR> These operations are wrapped in a 2-phase commit<BR>");

        try {

            try {
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    symbol = TradeConfig.rndSymbol();
                    // getQuote will call findQuote which will instaniate the
                    // Quote Entity Bean
                    // and then will return a QuoteObject
                    quoteData = tradeSLSBLocal.pingTwoPhase(symbol);

                }
            } catch (Exception ne) {
                Log.error(ne, "PingServlet2TwoPhase.goGet(...): exception getting QuoteData through Trade");
                throw ne;
            }

            output.append("<HR>initTime: " + initTime).append("<BR>Hit Count: " + hitCount++);
            output.append("<HR>Two phase ping selected a quote and sent a message to TradeBrokerQueue JMS queue<BR>Quote Information<BR><BR>"
                    + quoteData.toHTML());
            out.println(output.toString());

        } catch (Exception e) {
            Log.error(e, "PingServlet2TwoPhase.doGet(...): General Exception caught");
            res.sendError(500, "General Exception caught, " + e.toString());
        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, tests Servlet to Session to Entity EJB and JMS -- 2-phase commit path";

    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2TwoPhase.java:PingServlet2TwoPhase.<init>
// Node: row
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;

import javax.ejb.EJB;
import javax.naming.InitialContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * This primitive is designed to run inside the TradeApplication and relies upon
 * the {@link trade_client.TradeConfig} class to set configuration parameters.
 * PingServlet2SessionEJB tests key functionality of a servlet call to a
 * stateless SessionEJB. This servlet makes use of the Stateless Session EJB
 * {@link trade.Trade} by calling calculateInvestmentReturn with three random
 * numbers.
 *
 */
@WebServlet(name = "ejb3.PingServlet2SessionLocal", urlPatterns = { "/ejb3/PingServlet2SessionLocal" })
public class PingServlet2SessionLocal extends HttpServlet {

    private static final long serialVersionUID = 6854998080392777053L;

    private static String initTime;

    private static int hitCount;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal")
    private TradeSLSBLocal tradeSLSBLocal;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();
        // use a stringbuffer to avoid concatenation of Strings
        StringBuffer output = new StringBuffer(100);
        output.append("<html><head><title>PingServlet2SessionLocal</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2SessionLocal<BR></FONT>" + "<FONT size=\"-1\" color=\"#000066\">"
                + "Tests the basis path from a Servlet to a Session Bean.");

        try {

            try {
                // create three random numbers
                double rnd1 = Math.random() * 1000000;
                double rnd2 = Math.random() * 1000000;

                // use a function to do some work.
                double increase = 0.0;
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    increase = tradeSLSBLocal.investmentReturn(rnd1, rnd2);
                }

                // write out the output
                output.append("<HR>initTime: " + initTime);
                output.append("<BR>Hit Count: " + hitCount++);
                output.append("<HR>Investment Return Information <BR><BR>investment: " + rnd1);
                output.append("<BR>current Value: " + rnd2);
                output.append("<BR>investment return " + increase + "<HR></FONT></BODY></HTML>");
                out.println(output.toString());

            } catch (Exception e) {
                Log.error("PingServlet2Session.doGet(...):exception calling trade.investmentReturn ");
                throw e;
            }
        } // this is where I actually handle the exceptions
        catch (Exception e) {
            Log.error(e, "PingServlet2Session.doGet(...): error");
            res.sendError(500, "PingServlet2Session.doGet(...): error, " + e.toString());

        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, configured with trade runtime configs, tests Servlet to Session EJB path";

    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();

        if (tradeSLSBLocal == null) {
            Log.error("PingServlet2SessionLocal:init - Injection of TradeSLSBLocal failed - performing JNDI lookup!");

            try {
                InitialContext context = new InitialContext();
                tradeSLSBLocal = (TradeSLSBLocal) context.lookup("java:comp/env/ejb/TradeSLSBBean");
            } catch (Exception ex) {
                Log.error("PingServlet2SessionLocal:init - Lookup of TradeSLSBLocal failed!!!");
                ex.printStackTrace();
            }
        }
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2SessionLocal.java:to.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;

import javax.ejb.EJB;
import javax.naming.InitialContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBRemote;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * This primitive is designed to run inside the TradeApplication and relies upon
 * the {@link trade_client.TradeConfig} class to set configuration parameters.
 * PingServlet2SessionEJB tests key functionality of a servlet call to a
 * stateless SessionEJB. This servlet makes use of the Stateless Session EJB
 * {@link trade.Trade} by calling calculateInvestmentReturn with three random
 * numbers.
 *
 */
@WebServlet(name = "ejb3.PingServlet2SessionRemote", urlPatterns = { "/ejb3/PingServlet2SessionRemote" })
public class PingServlet2SessionRemote extends HttpServlet {

    private static final long serialVersionUID = -6328388347808212784L;

    private static String initTime;

    private static int hitCount;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBRemote")
    private TradeSLSBRemote tradeSLSBRemote;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();
        // use a stringbuffer to avoid concatenation of Strings
        StringBuffer output = new StringBuffer(100);
        output.append("<html><head><title>PingServlet2SessionRemote</title></head>" + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2SessionRemote<BR></FONT>"
                + "<FONT size=\"-1\" color=\"#000066\">" + "Tests the basis path from a Servlet to a Session Bean.");

        try {

            try {
                // create three random numbers
                double rnd1 = Math.random() * 1000000;
                double rnd2 = Math.random() * 1000000;

                // use a function to do some work.
                double increase = 0.0;
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    increase = tradeSLSBRemote.investmentReturn(rnd1, rnd2);
                }

                // write out the output
                output.append("<HR>initTime: " + initTime);
                output.append("<BR>Hit Count: " + hitCount++);
                output.append("<HR>Investment Return Information <BR><BR>investment: " + rnd1);
                output.append("<BR>current Value: " + rnd2);
                output.append("<BR>investment return " + increase + "<HR></FONT></BODY></HTML>");
                out.println(output.toString());

            } catch (Exception e) {
                Log.error("PingServlet2Session.doGet(...):exception calling trade.investmentReturn ");
                throw e;
            }
        } // this is where I actually handle the exceptions
        catch (Exception e) {
            Log.error(e, "PingServlet2Session.doGet(...): error");
            res.sendError(500, "PingServlet2Session.doGet(...): error, " + e.toString());

        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, configured with trade runtime configs, tests Servlet to Session EJB path";

    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();

        if (tradeSLSBRemote == null) {
            Log.error("PingServlet2Session:init - Injection of tradeSLSBRemote failed - performing JNDI lookup!");

            try {
                InitialContext context = new InitialContext();
                tradeSLSBRemote = (TradeSLSBRemote) context.lookup("java:comp/env/ejb/TradeSLSBBeanRemote");
            } catch (Exception ex) {
                Log.error("PingServlet2Session:init - Lookup of tradeSLSBRemote failed!!!");
                ex.printStackTrace();
            }
        }
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2SessionRemote.java:to.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;
import java.util.Collection;
import java.util.Iterator;

import javax.ejb.EJB;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBBean;
import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * PingServlet2Session2Entity tests key functionality of a servlet call to a
 * stateless SessionEJB, and then to a Entity EJB representing data in a
 * database. This servlet makes use of the Stateless Session EJB {@link Trade},
 * and then uses {@link TradeConfig} to generate a random user. The users
 * portfolio is looked up using the Holding Entity EJB returnin a collection of
 * Holdings
 *
 */
@WebServlet(name = "ejb3.PingServlet2Session2EntityCollection", urlPatterns = { "/ejb3/PingServlet2Session2EntityCollection" })
public class PingServlet2Session2EntityCollection extends HttpServlet {

    private static final long serialVersionUID = 6171380014749902308L;

    private static String initTime;

    private static int hitCount;

    @EJB(lookup="java:app/daytrader-ee7-ejb/TradeSLSBBean!com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal")
    private TradeSLSBBean tradeSLSBLocal;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();
        String userID = null;
        Collection<?> holdingDataBeans = null;
        StringBuffer output = new StringBuffer(100);

        output.append("<html><head><title>PingServlet2Session2EntityCollection</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2Session2EntityCollection<BR></FONT>" + "<FONT size=\"-1\" color=\"#000066\">"
                + "PingServlet2Session2EntityCollection tests the common path of a Servlet calling a Session EJB "
                + "which in turn calls a finder on an Entity EJB returning a collection of Entity EJBs.<BR>");

        try {

            try {
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    userID = TradeConfig.rndUserID();
                    // getQuote will call findQuote which will instaniate the
                    // Quote Entity Bean
                    // and then will return a QuoteObject
                    holdingDataBeans = tradeSLSBLocal.getHoldings(userID);
                    // trade.remove();
                }
            } catch (Exception ne) {
                Log.error(ne, "PingServlet2Session2EntityCollection.goGet(...): exception getting HoldingData collection through Trade for user " + userID);
                throw ne;
            }

            output.append("<HR>initTime: " + initTime).append("<BR>Hit Count: " + hitCount++);
            output.append("<HR>User: " + userID + " is currently holding " + holdingDataBeans.size() + " stock holdings:");
            Iterator<?> it = holdingDataBeans.iterator();
            while (it.hasNext()) {
                HoldingDataBean holdingData = (HoldingDataBean) it.next();
                output.append("<BR>" + holdingData.toHTML());
            }
            out.println(output.toString());

        } catch (Exception e) {
            Log.error(e, "PingServlet2Session2EntityCollection.doGet(...): General Exception caught");
            res.sendError(500, "General Exception caught, " + e.toString());
        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, tests Servlet to Session to Entity returning a collection of Entity EJBs";
    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2Session2EntityCollection.java:PingServlet2Session2EntityCollection.<init>
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.prims.ejb3;

import java.io.IOException;

import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 *
 * Primitive designed to run within the TradeApplication and makes use of
 * {@link trade_client.TradeConfig} for config parameters and random stock
 * symbols. Servlet will generate a random stock symbol and get the price of
 * that symbol using a {@link trade.Quote} Entity EJB This tests the common path
 * of a Servlet calling an Entity EJB to get data
 *
 */

public class PingServlet2Entity extends HttpServlet {
    private static final long serialVersionUID = -9004026114063894842L;

    private static String initTime;

    private static int hitCount;

    @PersistenceContext(unitName = "daytrader")
    private EntityManager em;

    @Override
    public void doPost(HttpServletRequest req, HttpServletResponse res) throws ServletException, IOException {
        doGet(req, res);
    }

    @Override
    public void doGet(HttpServletRequest req, HttpServletResponse res) throws IOException, ServletException {

        res.setContentType("text/html");
        java.io.PrintWriter out = res.getWriter();

        QuoteDataBean quote = null;
        String symbol = null;

        StringBuffer output = new StringBuffer(100);
        output.append("<html><head><title>Servlet2Entity</title></head>" + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2Entity<BR></FONT>"
                + "<FONT size=\"-1\" color=\"#000066\"><BR>PingServlet2Entity accesses an EntityManager"
                + " using a PersistenceContext annotaion and then gets the price of a random symbol (generated by TradeConfig)"
                + " through the EntityManager find method");
        try {
            // generate random symbol
            try {
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    // get a random symbol to look up and get the key to that
                    // symbol.
                    symbol = TradeConfig.rndSymbol();
                    // find the EntityInstance.
                    quote = em.find(QuoteDataBean.class, symbol);
                }
            } catch (Exception e) {
                Log.error("web_primtv.PingServlet2Entity.doGet(...): error performing find");
                throw e;
            }
            // get the price and print the output.

            output.append("<HR>initTime: " + initTime + "<BR>Hit Count: ").append(hitCount++);
            output.append("<HR>Quote Information<BR><BR> " + quote.toHTML());
            output.append("</font><HR></body></html>");
            out.println(output.toString());
        } catch (Exception e) {
            Log.error(e, "PingServlet2Entity.doGet(...): error");
            // this will send an Error to teh web applications defined error
            // page.
            res.sendError(500, "PingServlet2Entity.doGet(...): error" + e.toString());

        }
    }

    @Override
    public String getServletInfo() {
        return "web primitive, tests Servlet to Entity EJB path";
    }

    @Override
    public void init(ServletConfig config) throws ServletException {
        super.init(config);
        hitCount = 0;
        initTime = new java.util.Date().toString();
    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2Entity.java:PingServlet2Entity.<init>
// Node: PersistenceContext
// Node: symbol
/**
 * (C) Copyright IBM Corporation 2015.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.ibm.websphere.samples.daytrader.web.jsf;

import javax.enterprise.context.RequestScoped;
import javax.faces.context.ExternalContext;
import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.beans.RunStatsDataBean;
import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;
import com.ibm.websphere.samples.daytrader.web.TradeBuildDB;

@Named("tradeconfig")
@RequestScoped
public class TradeConfigJSF {

    @Inject
    private ExternalContext facesExternalContext;

    private String runtimeMode = TradeConfig.runTimeModeNames[TradeConfig.getRunTimeMode()];
    private String orderProcessingMode = TradeConfig.orderProcessingModeNames[TradeConfig.getOrderProcessingMode()];
    //private String cachingType = TradeConfig.cachingTypeNames[TradeConfig.getCachingType()];
    //private int distributedMapCacheSize = TradeConfig.getDistributedMapCacheSize();
    private int maxUsers = TradeConfig.getMAX_USERS();
    private int maxQuotes = TradeConfig.getMAX_QUOTES();
    private int marketSummaryInterval = TradeConfig.getMarketSummaryInterval();
    private String webInterface = TradeConfig.webInterfaceNames[TradeConfig.getWebInterface()];
    private int primIterations = TradeConfig.getPrimIterations();
    private int percentSentToWebsocket = TradeConfig.getPercentSentToWebsocket();
    private boolean publishQuotePriceChange = TradeConfig.getPublishQuotePriceChange();
    private boolean longRun = TradeConfig.getLongRun();
    private boolean displayOrderAlerts = TradeConfig.getDisplayOrderAlerts();
    private boolean useRemoteEJBInterface = TradeConfig.useRemoteEJBInterface();
    private boolean actionTrace = TradeConfig.getActionTrace();
    private boolean trace = TradeConfig.getTrace();
    private String[] runtimeModeList = TradeConfig.runTimeModeNames;
    private String[] orderProcessingModeList = TradeConfig.orderProcessingModeNames;
    //private String[] cachingTypeList = TradeConfig.cachingTypeNames;
    private String[] webInterfaceList = TradeConfig.webInterfaceNames;
    private String result = "";

    public void updateConfig() {
        String currentConfigStr = "\n\n########## Trade configuration update. Current config:\n\n";
        String runTimeModeStr = this.runtimeMode;
        if (runTimeModeStr != null) {
            try {
                for (int i = 0; i < runtimeModeList.length; i++) {
                    if (runTimeModeStr.equals(runtimeModeList[i])) {
                        TradeConfig.setRunTimeMode(i);
                    }
                }
            } catch (Exception e) {

                Log.error(e, "TradeConfigJSF.updateConfig(..): minor exception caught", "trying to set runtimemode to " + runTimeModeStr,
                        "reverting to current value");

            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tRunTimeMode:\t\t\t" + TradeConfig.runTimeModeNames[TradeConfig.getRunTimeMode()] + "\n";

        TradeConfig.setUseRemoteEJBInterface(useRemoteEJBInterface);
        currentConfigStr += "\t\tUse Remote EJB Interface:\t" + TradeConfig.useRemoteEJBInterface() + "\n";
        
        String orderProcessingModeStr = this.orderProcessingMode;
        if (orderProcessingModeStr != null) {
            try {
                for (int i = 0; i < orderProcessingModeList.length; i++) {
                    if (orderProcessingModeStr.equals(orderProcessingModeList[i])) {
                        TradeConfig.orderProcessingMode = i;
                    }
                }
            } catch (Exception e) {
                Log.error(e, "TradeConfigJSF.updateConfig(..): minor exception caught", "trying to set orderProcessing to " + orderProcessingModeStr,
                        "reverting to current value");

            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tOrderProcessingMode:\t\t" + TradeConfig.orderProcessingModeNames[TradeConfig.orderProcessingMode] + "\n";

        /*
        String cachingTypeStr = this.cachingType;
        if (cachingTypeStr != null) {
            try {
                for (int i = 0; i < cachingTypeList.length; i++) {
                    if (cachingTypeStr.equals(cachingTypeList[i])) {
                        TradeConfig.cachingType = i;
                    }
                }
            } catch (Exception e) {
                Log.error(e, "TradeConfigJSF.updateConfig(..): minor exception caught", "trying to set cachingType to " + cachingTypeStr,
                        "reverting to current value");

            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tCachingType:\t\t\t" + TradeConfig.cachingTypeNames[TradeConfig.cachingType] + "\n";

        int distMapCacheSize = this.distributedMapCacheSize;

        try {
            TradeConfig.setDistributedMapCacheSize(distMapCacheSize);
        } catch (Exception e) {
            Log.error(e, "TradeConfigJSF.updateConfig(..): minor exception caught", "trying to set distributedMapCacheSize", "reverting to current value");

        } // If the value is bad, simply revert to current

        currentConfigStr += "\t\tDMapCacheSize:\t\t\t" + TradeConfig.getDistributedMapCacheSize() + "\n";
		*/
        
        String webInterfaceStr = webInterface;
        if (webInterfaceStr != null) {
            try {
                for (int i = 0; i < webInterfaceList.length; i++) {
                    if (webInterfaceStr.equals(webInterfaceList[i])) {
                        TradeConfig.webInterface = i;
                    }
                }
            } catch (Exception e) {
                Log.error(e, "TradeConfigJSF.updateConfig(..): minor exception caught", "trying to set WebInterface to " + webInterfaceStr,
                        "reverting to current value");

            } // If the value is bad, simply revert to current
        }
        currentConfigStr += "\t\tWeb Interface:\t\t\t" + TradeConfig.webInterfaceNames[TradeConfig.webInterface] + "\n";

        TradeConfig.setMAX_USERS(maxUsers);
        TradeConfig.setMAX_QUOTES(maxQuotes);

        currentConfigStr += "\t\tTrade  Users:\t\t\t" + TradeConfig.getMAX_USERS() + "\n";
        currentConfigStr += "\t\tTrade Quotes:\t\t\t" + TradeConfig.getMAX_QUOTES() + "\n";

        TradeConfig.setMarketSummaryInterval(marketSummaryInterval);

        currentConfigStr += "\t\tMarket Summary Interval:\t" + TradeConfig.getMarketSummaryInterval() + "\n";

        TradeConfig.setPrimIterations(primIterations);

        currentConfigStr += "\t\tPrimitive Iterations:\t\t" + TradeConfig.getPrimIterations() + "\n";

        TradeConfig.setPublishQuotePriceChange(publishQuotePriceChange);
        currentConfigStr += "\t\tTradeStreamer MDB Enabled:\t" + TradeConfig.getPublishQuotePriceChange() + "\n";

        TradeConfig.setPercentSentToWebsocket(percentSentToWebsocket);
        currentConfigStr += "\t\t% of trades on Websocket:\t" + TradeConfig.getPercentSentToWebsocket() + "\n";
        
        TradeConfig.setLongRun(longRun);
        currentConfigStr += "\t\tLong Run Enabled:\t\t" + TradeConfig.getLongRun() + "\n";

        TradeConfig.setDisplayOrderAlerts(displayOrderAlerts);
        currentConfigStr += "\t\tDisplay Order Alerts:\t\t" + TradeConfig.getDisplayOrderAlerts() + "\n";

        Log.setTrace(trace);
        currentConfigStr += "\t\tTrace Enabled:\t\t\t" + TradeConfig.getTrace() + "\n";

        Log.setActionTrace(actionTrace);
        currentConfigStr += "\t\tAction Trace Enabled:\t\t" + TradeConfig.getActionTrace() + "\n";

        System.out.println(currentConfigStr);
        setResult("DayTrader Configuration Updated");
    }

    public String resetTrade() {
        RunStatsDataBean runStatsData = new RunStatsDataBean();
        TradeConfig currentConfig = new TradeConfig();
        HttpSession session = (HttpSession) facesExternalContext.getSession(true);
        try {
        	// Do not inject TradeAction on this class because we dont want the 
        	// config to initialiaze at startup. 
            TradeAction tradeAction = new TradeAction();
            runStatsData = tradeAction.resetTrade(false);
            session.setAttribute("runStatsData", runStatsData);
            session.setAttribute("tradeConfig", currentConfig);
            result += "Trade Reset completed successfully";

        } catch (Exception e) {
            result += "Trade Reset Error  - see log for details";
            session.setAttribute("result", result);
            Log.error(e, result);
        }

        return "stats";
    }

    public String populateDatabase() {

        try {
            new TradeBuildDB(new java.io.PrintWriter(System.out), null);
        } catch (Exception e) {
            e.printStackTrace();
        }       

        result = "TradeBuildDB: **** DayTrader Database Built - " + TradeConfig.getMAX_USERS() + " users created, " + TradeConfig.getMAX_QUOTES()
                + " quotes created. ****<br/>";
        result += "TradeBuildDB: **** Check System.Out for any errors. ****<br/>";

        return "database";
    }

    public String buildDatabaseTables() {
        try {

            //Find out the Database being used
            TradeDirect tradeDirect = new TradeDirect();

            String dbProductName = null;
            try {
                dbProductName = tradeDirect.checkDBProductName();
            } catch (Exception e) {
                Log.error(e, "TradeBuildDB: Unable to check DB Product name");
            }
            if (dbProductName == null) {
                result += "TradeBuildDB: **** Unable to check DB Product name, please check Database/AppServer configuration and retry ****<br/>";
                return "database";
            }

            String ddlFile = null;
            //Locate DDL file for the specified database
            try {
                result = result + "TradeBuildDB: **** Database Product detected: " + dbProductName + " ****<br/>";
                if (dbProductName.startsWith("DB2/")) { // if db is DB2
                    ddlFile = "/dbscripts/db2/Table.ddl";
                } else if (dbProductName.startsWith("DB2 UDB for AS/400")) { //if db is DB2 on IBM i
                  ddlFile = "/dbscripts/db2i/Table.ddl";
                } else if (dbProductName.startsWith("Apache Derby")) { //if db is Derby
                    ddlFile = "/dbscripts/derby/Table.ddl";
                } else if (dbProductName.startsWith("Oracle")) { // if the Db is Oracle
                    ddlFile = "/dbscripts/oracle/Table.ddl";
                } else { // Unsupported "Other" Database
                    ddlFile = "/dbscripts/derby/Table.ddl";
                    result = result + "TradeBuildDB: **** This Database is unsupported/untested use at your own risk ****<br/>";
                }

                result = result + "TradeBuildDB: **** The DDL file at path" + ddlFile + " will be used ****<br/>";
            } catch (Exception e) {
                Log.error(e, "TradeBuildDB: Unable to locate DDL file for the specified database");
                result = result + "TradeBuildDB: **** Unable to locate DDL file for the specified database ****<br/>";
                return "database";
            }

            new TradeBuildDB(new java.io.PrintWriter(System.out), facesExternalContext.getResourceAsStream(ddlFile));

            result = result + "TradeBuildDB: **** DayTrader Database Created, Check System.Out for any errors. ****<br/>";

        } catch (Exception e) {
            e.printStackTrace();
        }

        // Go to configure.xhtml
        return "database";
    }

    public void setRuntimeMode(String runtimeMode) {
        this.runtimeMode = runtimeMode;
    }

    public String getRuntimeMode() {
        return runtimeMode;
    }

    public void setOrderProcessingMode(String orderProcessingMode) {
        this.orderProcessingMode = orderProcessingMode;
    }

    public String getOrderProcessingMode() {
        return orderProcessingMode;
    }
    /*
    public void setCachingType(String cachingType) {
        this.cachingType = cachingType;
    }

    public String getCachingType() {
        return cachingType;
    }

    public void setDistributedMapCacheSize(int distributedMapCacheSize) {
        this.distributedMapCacheSize = distributedMapCacheSize;
    }

    public int getDistributedMapCacheSize() {
        return distributedMapCacheSize;
    }*/

    public void setMaxUsers(int maxUsers) {
        this.maxUsers = maxUsers;
    }

    public int getMaxUsers() {
        return maxUsers;
    }

    public void setmaxQuotes(int maxQuotes) {
        this.maxQuotes = maxQuotes;
    }

    public int getMaxQuotes() {
        return maxQuotes;
    }

    public void setMarketSummaryInterval(int marketSummaryInterval) {
        this.marketSummaryInterval = marketSummaryInterval;
    }

    public int getMarketSummaryInterval() {
        return marketSummaryInterval;
    }

    public void setPrimIterations(int primIterations) {
        this.primIterations = primIterations;
    }

    public int getPrimIterations() {
        return primIterations;
    }

    public void setPublishQuotePriceChange(boolean publishQuotePriceChange) {
        this.publishQuotePriceChange = publishQuotePriceChange;
    }

    public boolean isPublishQuotePriceChange() {
        return publishQuotePriceChange;
    }
    
    public void setPercentSentToWebsocket(int percentSentToWebsocket) {
        this. percentSentToWebsocket =  percentSentToWebsocket;
    }

    public int getPercentSentToWebsocket() {
        return  percentSentToWebsocket;
    }

    public void setDisplayOrderAlerts(boolean displayOrderAlerts) {
        this.displayOrderAlerts = displayOrderAlerts;
    }

    public boolean isDisplayOrderAlerts() {
        return displayOrderAlerts;
    }
    
    public void setUseRemoteEJBInterface(boolean useRemoteEJBInterface) {
        this.useRemoteEJBInterface = useRemoteEJBInterface;
    }

    public boolean isUseRemoteEJBInterface() {
        return useRemoteEJBInterface;
    }

    public void setLongRun(boolean longRun) {
        this.longRun = longRun;
    }

    public boolean isLongRun() {
        return longRun;
    }

    public void setTrace(boolean trace) {
        this.trace = trace;
    }

    public boolean isTrace() {
        return trace;
    }

    public void setRuntimeModeList(String[] runtimeModeList) {
        this.runtimeModeList = runtimeModeList;
    }

    public String[] getRuntimeModeList() {
        return runtimeModeList;
    }

    public void setOrderProcessingModeList(String[] orderProcessingModeList) {
        this.orderProcessingModeList = orderProcessingModeList;
    }

    public String[] getOrderProcessingModeList() {
        return orderProcessingModeList;
    }

    /*public void setCachingTypeList(String[] cachingTypeList) {
        this.cachingTypeList = cachingTypeList;
    }

    public String[] getCachingTypeList() {
        return cachingTypeList;
    }*/

    public void setWebInterface(String webInterface) {
        this.webInterface = webInterface;
    }

    public String getWebInterface() {
        return webInterface;
    }

    public void setWebInterfaceList(String[] webInterfaceList) {
        this.webInterfaceList = webInterfaceList;
    }

    public String[] getWebInterfaceList() {
        return webInterfaceList;
    }

    public void setActionTrace(boolean actionTrace) {
        this.actionTrace = actionTrace;
    }

    public boolean isActionTrace() {
        return actionTrace;
    }

    public void setResult(String result) {
        this.result = result;
    }

    public String getResult() {
        return result;
    }

}


// Node: buildDatabaseTables
