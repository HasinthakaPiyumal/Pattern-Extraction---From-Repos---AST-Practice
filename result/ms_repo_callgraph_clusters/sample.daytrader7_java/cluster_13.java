// Cluster 13

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
package com.ibm.websphere.samples.daytrader;

import java.io.InputStream;
import java.math.BigDecimal;
import java.util.Collection;
//import java.util.Properties;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.DocumentBuilder;

import org.w3c.dom.Document;
import org.w3c.dom.NodeList;
import org.w3c.dom.Element;

import javax.naming.InitialContext;

import com.ibm.websphere.samples.daytrader.beans.MarketSummaryDataBean;
import com.ibm.websphere.samples.daytrader.beans.RunStatsDataBean;
import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBLocal;
import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBRemote;
import com.ibm.websphere.samples.daytrader.entities.AccountDataBean;
import com.ibm.websphere.samples.daytrader.entities.AccountProfileDataBean;
import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.FinancialUtils;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * The TradeAction class provides the generic client side access to each of the
 * Trade brokerage user operations. These include login, logout, buy, sell,
 * getQuote, etc. The TradeAction class does not handle user interface
 * processing and should be used by a class that is UI specific. For example,
 * {trade_client.TradeServletAction}manages a web interface to Trade, making
 * calls to TradeAction methods to actually performance each operation.
 */
public class TradeAction implements TradeServices {

	// This lock is used to serialize market summary operations.
    private static final Integer marketSummaryLock = new Integer(0);
    private static long nextMarketSummary = System.currentTimeMillis();
    private static MarketSummaryDataBean cachedMSDB = MarketSummaryDataBean.getRandomInstance();
        
    // make this static so the trade impl can be cached
    // - ejb3 mode is the only thing that really uses this
    // - can go back and update other modes to take advantage (ie. TradeDirect)
    private static TradeServices trade = null;
    private static TradeServices tradeLocal = null;
    private static TradeServices tradeRemote = null;
    
    static {
                      
        // Determine if JPA Shared L2 Class is enabled
        // Depends on the <shared-cache-mode> in the persistence.xml
        try {
            ClassLoader loader = Thread.currentThread().getContextClassLoader();  
            InputStream is = loader.getResourceAsStream ("META-INF/persistence.xml"); 
       
            DocumentBuilderFactory dbFactory = DocumentBuilderFactory.newInstance();
            DocumentBuilder dBuilder = dbFactory.newDocumentBuilder();
            Document doc = dBuilder.parse(is);
            doc.getDocumentElement().normalize();
           
            NodeList nList = doc.getElementsByTagName("shared-cache-mode");
            
            if (nList.getLength() != 0 && ((Element)nList.item(0)).getTextContent().equals("NONE")) {
                Log.log("JPA Shared L2 Cache disabled.");
            } else {
                Log.log("JPA Shared L2 Cache enabled.");
            }
        } catch (Exception e) {
            Log.log("Unable to determine if JPA Shared L2 Cache is enabled or disabled.");
            e.printStackTrace();
        }
                
    }

    public TradeAction() {
        if (Log.doTrace()) {
            Log.trace("TradeAction:TradeAction()");
        }
        createTrade();
    }

    public TradeAction(TradeServices trade) {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:TradeAction(trade)");
        }
        TradeAction.trade = trade;
    }

    private void createTrade() {
        if (TradeConfig.runTimeMode == TradeConfig.EJB3) {
            try {	     
            	
            	if (tradeLocal == null && tradeRemote == null ) {
            		InitialContext context = new InitialContext();
            		tradeLocal = (TradeSLSBLocal) context.lookup("java:comp/env/ejb/TradeSLSBBean");
            		tradeRemote = (TradeSLSBRemote) context.lookup("java:comp/env/ejb/TradeSLSBBeanRemote");
            	}
            	
            	// Determine local or remote interface.
            	if (!TradeConfig.useRemoteEJBInterface()) {
            		if (!(trade instanceof TradeSLSBLocal)) {
            			trade = tradeLocal;
            		}
            	} else if (!(trade instanceof TradeSLSBRemote)) {
            		/* TODO: For split tier this will need to be changed
            			I have not tried this yet with DT7 */
            		trade = tradeRemote;
            	}
            } catch (Exception e) {
                Log.error("TradeAction:TradeAction() Creation of Trade EJB 3 failed\n" + e);
                e.printStackTrace();
            }
        } else if (TradeConfig.runTimeMode == TradeConfig.DIRECT) {
            try {
                trade = new TradeDirect();
            } catch (Exception e) {
                Log.error("TradeAction:TradeAction() Creation of Trade Direct failed\n" + e);
                e.printStackTrace();
            }
        }
    }

    /**
     * Market Summary is inherently a heavy database operation. For servers that
     * have a caching story this is a great place to cache data that is good for
     * a period of time. In order to provide a flexible framework for this we
     * allow the market summary operation to be invoked on every transaction,
     * time delayed or never. This is configurable in the configuration panel.
     *
     * @return An instance of the market summary
     */
    @Override
    public MarketSummaryDataBean getMarketSummary() throws Exception {

        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getMarketSummary()");
        }

        // If EJB3 mode, then have the Singleton Bean handle this.
        if (TradeConfig.getRunTimeMode() == TradeConfig.EJB3)
        {
            if (Log.doActionTrace()) {
                Log.trace("TradeAction:getMarketSummary() -- EJB3 mode, using Singleton Bean");
            }
            return trade.getMarketSummary();
        }
                        
        if (TradeConfig.getMarketSummaryInterval() == 0) {
            return getMarketSummaryInternal();
        }
        if (TradeConfig.getMarketSummaryInterval() < 0) {
            return cachedMSDB;
        }

        /**
         * This is a little funky. If its time to fetch a new Market summary
         * then we'll synchronize access to make sure only one requester does
         * it. Others will merely return the old copy until the new
         * MarketSummary has been executed.
         */

        long currentTime = System.currentTimeMillis();

        if (currentTime > nextMarketSummary) {
            long oldNextMarketSummary = nextMarketSummary;
            boolean fetch = false;

            synchronized (marketSummaryLock) {
                /**
                 * Is it still ahead or did we miss lose the race? If we lost
                 * then let's get out of here as the work has already been done.
                 */
                if (oldNextMarketSummary == nextMarketSummary) {
                    fetch = true;
                    nextMarketSummary += TradeConfig.getMarketSummaryInterval() * 1000;

                    /**
                     * If the server has been idle for a while then its possible
                     * that nextMarketSummary could be way off. Rather than try
                     * and play catch up we'll simply get in sync with the
                     * current time + the interval.
                     */
                    if (nextMarketSummary < currentTime) {
                        nextMarketSummary = currentTime + TradeConfig.getMarketSummaryInterval() * 1000;
                    }
                }
            }

            /**
             * If we're the lucky one then let's update the MarketSummary
             */
            if (fetch) {
                cachedMSDB = getMarketSummaryInternal();
            }
        }

        return cachedMSDB;
    }

    /**
     * Compute and return a snapshot of the current market conditions This
     * includes the TSIA - an index of the price of the top 100 Trade stock
     * quotes The openTSIA ( the index at the open) The volume of shares traded,
     * Top Stocks gain and loss
     *
     * @return A snapshot of the current market summary
     */
    public MarketSummaryDataBean getMarketSummaryInternal() throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getMarketSummaryInternal()");
        }

        MarketSummaryDataBean marketSummaryData = null;
        marketSummaryData = trade.getMarketSummary();
        return marketSummaryData;
    }

    /**
     * Purchase a stock and create a new holding for the given user. Given a
     * stock symbol and quantity to purchase, retrieve the current quote price,
     * debit the user's account balance, and add holdings to user's portfolio.
     *
     * @param userID
     *            the customer requesting the stock purchase
     * @param symbol
     *            the symbol of the stock being purchased
     * @param quantity
     *            the quantity of shares to purchase
     * @return OrderDataBean providing the status of the newly created buy order
     */
    @Override
    public OrderDataBean buy(String userID, String symbol, double quantity, int orderProcessingMode) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:buy", userID, symbol, new Double(quantity), new Integer(orderProcessingMode));
        }
        OrderDataBean orderData = trade.buy(userID, symbol, quantity, orderProcessingMode);
        
        // after the purchase or sell of a stock, update the stocks volume and
        // price

        updateQuotePriceVolume(symbol, TradeConfig.getRandomPriceChangeFactor(), quantity);

        return orderData;
    }

    /**
     * Sell(SOAP 2.2 Wrapper converting int to Integer) a stock holding and
     * removed the holding for the given user. Given a Holding, retrieve current
     * quote, credit user's account, and reduce holdings in user's portfolio.
     *
     * @param userID
     *            the customer requesting the sell
     * @param holdingID
     *            the users holding to be sold
     * @return OrderDataBean providing the status of the newly created sell
     *         order
     */
    public OrderDataBean sell(String userID, int holdingID, int orderProcessingMode) throws Exception {
        return sell(userID, new Integer(holdingID), orderProcessingMode);
    }

    /**
     * Sell a stock holding and removed the holding for the given user. Given a
     * Holding, retrieve current quote, credit user's account, and reduce
     * holdings in user's portfolio.
     *
     * @param userID
     *            the customer requesting the sell
     * @param holdingID
     *            the users holding to be sold
     * @return OrderDataBean providing the status of the newly created sell
     *         order
     */
    @Override
    public OrderDataBean sell(String userID, Integer holdingID, int orderProcessingMode) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:sell", userID, holdingID, new Integer(orderProcessingMode));
        }
        OrderDataBean orderData = trade.sell(userID, holdingID, orderProcessingMode);
       

        if (!orderData.getOrderStatus().equalsIgnoreCase("cancelled")) {
            updateQuotePriceVolume(orderData.getSymbol(), TradeConfig.getRandomPriceChangeFactor(), orderData.getQuantity());
        }

        return orderData;
    }

    /**
     * Queue the Order identified by orderID to be processed
     * <p/>
     * Orders are submitted through JMS to a Trading Broker and completed
     * asynchronously. This method queues the order for processing
     * <p/>
     * The boolean twoPhase specifies to the server implementation whether or
     * not the method is to participate in a global transaction
     *
     * @param orderID
     *            the Order being queued for processing
     */
    @Override
    public void queueOrder(Integer orderID, boolean twoPhase) {
        throw new UnsupportedOperationException("TradeAction: queueOrder method not supported");
    }

    /**
     * Complete the Order identefied by orderID Orders are submitted through JMS
     * to a Trading agent and completed asynchronously. This method completes
     * the order For a buy, the stock is purchased creating a holding and the
     * users account is debited For a sell, the stock holding is removed and the
     * users account is credited with the proceeds
     * <p/>
     * The boolean twoPhase specifies to the server implementation whether or
     * not the method is to participate in a global transaction
     *
     * @param orderID
     *            the Order to complete
     * @return OrderDataBean providing the status of the completed order
     */
    @Override
    public OrderDataBean completeOrder(Integer orderID, boolean twoPhase) {
        throw new UnsupportedOperationException("TradeAction: completeOrder method not supported");
    }

    /**
     * Cancel the Order identified by orderID
     * <p/>
     * Orders are submitted through JMS to a Trading Broker and completed
     * asynchronously. This method queues the order for processing
     * <p/>
     * The boolean twoPhase specifies to the server implementation whether or
     * not the method is to participate in a global transaction
     *
     * @param orderID
     *            the Order being queued for processing
     */
    @Override
    public void cancelOrder(Integer orderID, boolean twoPhase) {
        throw new UnsupportedOperationException("TradeAction: cancelOrder method not supported");
    }

    @Override
    public void orderCompleted(String userID, Integer orderID) throws Exception {

        if (Log.doActionTrace()) {
            Log.trace("TradeAction:orderCompleted", userID, orderID);
        }
        if (Log.doTrace()) {
            Log.trace("OrderCompleted", userID, orderID);
        }
    }

    /**
     * Get the collection of all orders for a given account
     *
     * @param userID
     *            the customer account to retrieve orders for
     * @return Collection OrderDataBeans providing detailed order information
     */
    @Override
    public Collection<?> getOrders(String userID) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getOrders", userID);
        }
        Collection<?> orderDataBeans = trade.getOrders(userID);
        
        return orderDataBeans;
    }

    /**
     * Get the collection of completed orders for a given account that need to
     * be alerted to the user
     *
     * @param userID
     *            the customer account to retrieve orders for
     * @return Collection OrderDataBeans providing detailed order information
     */
    @Override
    public Collection<?> getClosedOrders(String userID) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getClosedOrders", userID);
        }
        
        Collection<?> orderDataBeans =  trade.getClosedOrders(userID);
        
        return orderDataBeans;
    }

    /**
     * Given a market symbol, price, and details, create and return a new
     * {@link QuoteDataBean}
     *
     * @param symbol
     *            the symbol of the stock
     * @param price
     *            the current stock price
     * @return a new QuoteDataBean or null if Quote could not be created
     */
    @Override
    public QuoteDataBean createQuote(String symbol, String companyName, BigDecimal price) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:createQuote", symbol, companyName, price);
        }
      
     
        return trade.createQuote(symbol, companyName, price);
    
    }

    /**
     * Return a collection of {@link QuoteDataBean}describing all current quotes
     *
     * @return the collection of QuoteDataBean
     */
    @Override
    public Collection<?> getAllQuotes() throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getAllQuotes");
        }
        
        return trade.getAllQuotes();
        
    }

    /**
     * Return a {@link QuoteDataBean}describing a current quote for the given
     * stock symbol
     *
     * @param symbol
     *            the stock symbol to retrieve the current Quote
     * @return the QuoteDataBean
     */
    @Override
    public QuoteDataBean getQuote(String symbol) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getQuote", symbol);
        }
        if ((symbol == null) || (symbol.length() == 0) || (symbol.length() > 10)) {
            if (Log.doActionTrace()) {
                Log.trace("TradeAction:getQuote   ---  primitive workload");
            }
            return new QuoteDataBean("Invalid symbol", "", 0.0, FinancialUtils.ZERO, FinancialUtils.ZERO, FinancialUtils.ZERO, FinancialUtils.ZERO, 0.0);
        }
        
        QuoteDataBean quoteData = trade.getQuote(symbol);
        
        return quoteData;
    }

    /**
     * Update the stock quote price for the specified stock symbol
     *
     * @param symbol
     *            for stock quote to update
     * @return the QuoteDataBean describing the stock
     */
    /* avoid data collision with synch */
    @Override
    public QuoteDataBean updateQuotePriceVolume(String symbol, BigDecimal changeFactor, double sharesTraded) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:updateQuotePriceVolume", symbol, changeFactor, new Double(sharesTraded));
        }
        QuoteDataBean quoteData = null;
        try {
        	quoteData = trade.updateQuotePriceVolume(symbol, changeFactor, sharesTraded);
        } catch (Exception e) {
            Log.error("TradeAction:updateQuotePrice -- ", e);
        }

        return quoteData;

    }

    /**
     * Return the portfolio of stock holdings for the specified customer as a
     * collection of HoldingDataBeans
     *
     * @param userID
     *            the customer requesting the portfolio
     * @return Collection of the users portfolio of stock holdings
     */
    @Override
    public Collection<?> getHoldings(String userID) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getHoldings", userID);
        }
        
        Collection<?> holdingDataBeans = trade.getHoldings(userID);
        
        return holdingDataBeans;
    }

    /**
     * Return a specific user stock holding identifed by the holdingID
     *
     * @param holdingID
     *            the holdingID to return
     * @return a HoldingDataBean describing the holding
     */
    @Override
    public HoldingDataBean getHolding(Integer holdingID) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getHolding", holdingID);
        }

        return trade.getHolding(holdingID);
    }

    /**
     * Return an AccountDataBean object for userID describing the account
     *
     * @param userID
     *            the account userID to lookup
     * @return User account data in AccountDataBean
     */
    @Override
    public AccountDataBean getAccountData(String userID) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getAccountData", userID);
        }
        AccountDataBean accountData = trade.getAccountData(userID);
        
        return accountData;
    }

    /**
     * Return an AccountProfileDataBean for userID providing the users profile
     *
     * @param userID
     *            the account userID to lookup
     */
    @Override
    public AccountProfileDataBean getAccountProfileData(String userID) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:getAccountProfileData", userID);
        }
        AccountProfileDataBean accountProfileData = trade.getAccountProfileData(userID);
        
        return accountProfileData;
    }

    /**
     * Update userID's account profile information using the provided
     * AccountProfileDataBean object
     *
     * @param accountProfileData
     *            account profile data in AccountProfileDataBean
     */
    @Override
    public AccountProfileDataBean updateAccountProfile(AccountProfileDataBean accountProfileData) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:updateAccountProfile", accountProfileData);
        }

        accountProfileData = trade.updateAccountProfile(accountProfileData);        
        return accountProfileData;
    }

    /**
     * Attempt to authenticate and login a user with the given password
     *
     * @param userID
     *            the customer to login
     * @param password
     *            the password entered by the customer for authentication
     * @return User account data in AccountDataBean
     */
    @Override
    public AccountDataBean login(String userID, String password) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:login", userID, password);
        }
        AccountDataBean accountData = trade.login(userID, password);
                
        return accountData;
    }

    /**
     * Logout the given user
     *
     * @param userID
     *            the customer to logout
     */
    @Override
    public void logout(String userID) throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:logout", userID);
        }
    
        trade.logout(userID);
        
    }

    /**
     * Register a new Trade customer. Create a new user profile, user registry
     * entry, account with initial balance, and empty portfolio.
     *
     * @param userID
     *            the new customer to register
     * @param password
     *            the customers password
     * @param fullname
     *            the customers fullname
     * @param address
     *            the customers street address
     * @param email
     *            the customers email address
     * @param creditCard
     *            the customers creditcard number
     * @param openBalance
     *            the amount to charge to the customers credit to open the
     *            account and set the initial balance
     * @return the userID if successful, null otherwise
     */
    @Override
    public AccountDataBean register(String userID, String password, String fullname, String address, String email, String creditCard, BigDecimal openBalance)
            throws Exception {
        if (Log.doActionTrace()) {
            Log.trace("TradeAction:register", userID, password, fullname, address, email, creditCard, openBalance);
        }
       
        return trade.register(userID, password, fullname, address, email, creditCard, openBalance);     
    }

    public AccountDataBean register(String userID, String password, String fullname, String address, String email, String creditCard, String openBalanceString)
            throws Exception {
        BigDecimal openBalance = new BigDecimal(openBalanceString);
        return register(userID, password, fullname, address, email, creditCard, openBalance);
    }

    /**
     * Reset the TradeData by - removing all newly registered users by scenario
     * servlet (i.e. users with userID's beginning with "ru:") * - removing all
     * buy/sell order pairs - setting logoutCount = loginCount
     *
     * return statistics for this benchmark run
     */
    @Override
    public RunStatsDataBean resetTrade(boolean deleteAll) throws Exception {
        RunStatsDataBean runStatsData = trade.resetTrade(deleteAll);
                
        return runStatsData;
    }
}


// Node: doTrace
// Node: trace
// Node: createTrade
// Node: queueOrder
// Node: UnsupportedOperationException
// Node: completeOrder
/**
 * (C) Copyright IBM Corporation 2015, 2021
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
package com.ibm.websphere.samples.daytrader.ejb3;

import java.math.BigDecimal;
import java.sql.Timestamp;
import java.util.Collection;
import java.util.Comparator;
import java.util.Iterator;
import java.util.List;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;
import javax.ejb.EJB;
import javax.ejb.EJBException;
import javax.ejb.SessionContext;
import javax.ejb.Stateless;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.ejb.TransactionManagement;
import javax.ejb.TransactionManagementType;
import javax.enterprise.concurrent.ManagedThreadFactory;
import javax.jms.JMSContext;
import javax.jms.Queue;
import javax.jms.QueueConnectionFactory;
import javax.jms.TextMessage;
import javax.jms.Topic;
import javax.jms.TopicConnectionFactory;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.persistence.TypedQuery;
import javax.persistence.criteria.CriteriaBuilder;
import javax.persistence.criteria.CriteriaQuery;
import javax.persistence.criteria.Root;
import javax.transaction.RollbackException;

import com.ibm.websphere.samples.daytrader.TradeAction;
//import com.ibm.websphere.samples.daytrader.TradeServices;
import com.ibm.websphere.samples.daytrader.beans.MarketSummaryDataBean;
import com.ibm.websphere.samples.daytrader.beans.RunStatsDataBean;
import com.ibm.websphere.samples.daytrader.entities.AccountDataBean;
import com.ibm.websphere.samples.daytrader.entities.AccountProfileDataBean;
import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.CompleteOrderThread;
import com.ibm.websphere.samples.daytrader.util.FinancialUtils;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Stateless
@TransactionAttribute(TransactionAttributeType.REQUIRED)
@TransactionManagement(TransactionManagementType.CONTAINER)
public class TradeSLSBBean implements TradeSLSBRemote, TradeSLSBLocal {
	
    @Resource(name = "jms/QueueConnectionFactory", authenticationType = javax.annotation.Resource.AuthenticationType.APPLICATION)
    private QueueConnectionFactory queueConnectionFactory;

    @Resource(name = "jms/TopicConnectionFactory", authenticationType = javax.annotation.Resource.AuthenticationType.APPLICATION)
    private TopicConnectionFactory topicConnectionFactory;

    @Resource(lookup = "jms/TradeStreamerTopic")
    private Topic tradeStreamerTopic;

    @Resource(lookup = "jms/TradeBrokerQueue")
    private Queue tradeBrokerQueue;
    
    @Resource 
    private ManagedThreadFactory managedThreadFactory;
	
    /* JBoss 
    @Resource(name = "java:/jms/QueueConnectionFactory", authenticationType = javax.annotation.Resource.AuthenticationType.APPLICATION)
    private QueueConnectionFactory queueConnectionFactory;

    @Resource(name = "java:/jms/TopicConnectionFactory", authenticationType = javax.annotation.Resource.AuthenticationType.APPLICATION)
    private TopicConnectionFactory topicConnectionFactory;

    @Resource(lookup = "java:/jms/TradeStreamerTopic")
    private Topic tradeStreamerTopic;
        
    @Resource(lookup = "java:/jms/TradeBrokerQueue")
    private Queue tradeBrokerQueue;
    */
    
    @PersistenceContext
    private EntityManager entityManager;

    @Resource
    private SessionContext context;
    
    @EJB
    MarketSummarySingleton marketSummarySingleton;

    /** Creates a new instance of TradeSLSBBean */
    public TradeSLSBBean() {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:ejbCreate  -- JNDI lookups of EJB and JMS resources");
        }
    }

    @Override
    public MarketSummaryDataBean getMarketSummary() {

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getMarketSummary -- getting market summary");
        }

        return marketSummarySingleton.getMarketSummaryDataBean();
    }

    @Override
    public OrderDataBean buy(String userID, String symbol, double quantity, int orderProcessingMode) {
        OrderDataBean order;
        BigDecimal total;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeSLSBBean:buy", userID, symbol, quantity, orderProcessingMode);
            }
            
            AccountProfileDataBean profile = entityManager.find(AccountProfileDataBean.class, userID);
            AccountDataBean account = profile.getAccount();
            QuoteDataBean quote = entityManager.find(QuoteDataBean.class, symbol);
            HoldingDataBean holding = null; // The holding will be created by
            // this buy order

            order = createOrder(account, quote, holding, "buy", quantity);
                      
            // UPDATE - account should be credited during completeOrder
            BigDecimal price = quote.getPrice();
            BigDecimal orderFee = order.getOrderFee();
            BigDecimal balance = account.getBalance();
            total = (new BigDecimal(quantity).multiply(price)).add(orderFee);
            account.setBalance(balance.subtract(total));
            final Integer orderID=order.getOrderID(); 
            
            if (orderProcessingMode == TradeConfig.SYNCH) {
                completeOrder(orderID, false);
            } else {
                entityManager.flush();
                queueOrder(orderID, true);
            }
        } catch (Exception e) {
            Log.error("TradeSLSBBean:buy(" + userID + "," + symbol + "," + quantity + ") --> failed", e);
            /* On exception - cancel the order */
            // TODO figure out how to do this with JPA
            // if (order != null) order.cancel();
            throw new EJBException(e);
        }
        return order;
    }

    @Override
    public OrderDataBean sell(final String userID, final Integer holdingID, int orderProcessingMode) {
        OrderDataBean order;
        BigDecimal total;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeSLSBBean:sell", userID, holdingID, orderProcessingMode);
            }
            
            AccountProfileDataBean profile = entityManager.find(AccountProfileDataBean.class, userID);
            AccountDataBean account = profile.getAccount();

            HoldingDataBean holding = entityManager.find(HoldingDataBean.class, holdingID);
            
            if (holding == null) {
                Log.error("TradeSLSBBean:sell User " + userID + " attempted to sell holding " + holdingID + " which has already been sold");

                OrderDataBean orderData = new OrderDataBean();
                orderData.setOrderStatus("cancelled");
                entityManager.persist(orderData);

                return orderData;
            }

            QuoteDataBean quote = holding.getQuote();
            double quantity = holding.getQuantity();
            order = createOrder(account, quote, holding, "sell", quantity);

            // UPDATE the holding purchase data to signify this holding is
            // "inflight" to be sold
            // -- could add a new holdingStatus attribute to holdingEJB
            holding.setPurchaseDate(new java.sql.Timestamp(0));

            // UPDATE - account should be credited during completeOrder
            BigDecimal price = quote.getPrice();
            BigDecimal orderFee = order.getOrderFee();
            BigDecimal balance = account.getBalance();
            total = (new BigDecimal(quantity).multiply(price)).subtract(orderFee);
            account.setBalance(balance.add(total));
            final Integer orderID=order.getOrderID();

            if (orderProcessingMode == TradeConfig.SYNCH) {
                completeOrder(orderID, false);
            } else {
                entityManager.flush();
                queueOrder(orderID, true);
            }

        } catch (Exception e) {
            Log.error("TradeSLSBBean:sell(" + userID + "," + holdingID + ") --> failed", e);
            // if (order != null) order.cancel();
            // UPDATE - handle all exceptions like:
            throw new EJBException("TradeSLSBBean:sell(" + userID + "," + holdingID + ")", e);
        }
        return order;
    }

    @Override
    public void queueOrder(Integer orderID, boolean twoPhase) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:queueOrder", orderID);
        }
                	
        if (TradeConfig.getOrderProcessingMode() == TradeConfig.ASYNCH_MANAGEDTHREAD) {
        
            Thread thread = managedThreadFactory.newThread(new CompleteOrderThread(orderID, twoPhase));
            
            thread.start();
        
        } else {
        
            try (JMSContext queueContext = queueConnectionFactory.createContext();) {
                TextMessage message = queueContext.createTextMessage();

                message.setStringProperty("command", "neworder");
                message.setIntProperty("orderID", orderID);
                message.setBooleanProperty("twoPhase", twoPhase);
                message.setText("neworder: orderID=" + orderID + " runtimeMode=EJB twoPhase=" + twoPhase);
                message.setLongProperty("publishTime", System.currentTimeMillis());
        		        		
                queueContext.createProducer().send(tradeBrokerQueue, message);
        		
            } catch (Exception e) {
                throw new EJBException(e.getMessage(), e); // pass the exception
            }
        }
    }

    @Override
    public OrderDataBean completeOrder(Integer orderID, boolean twoPhase) throws Exception {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:completeOrder", orderID + " twoPhase=" + twoPhase);
        }  
              
        OrderDataBean order = entityManager.find(OrderDataBean.class, orderID);
        
        if (order == null) {
            throw new EJBException("Error: attempt to complete Order that is null\n" + order);
        }
        
        order.getQuote();

        if (order.isCompleted()) {
            throw new EJBException("Error: attempt to complete Order that is already completed\n" + order);
        }

        AccountDataBean account = order.getAccount();
        QuoteDataBean quote = order.getQuote();
        HoldingDataBean holding = order.getHolding();
        BigDecimal price = order.getPrice();
        double quantity = order.getQuantity();

        String userID = account.getProfile().getUserID();

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBeanInternal:completeOrder--> Completing Order " + order.getOrderID() + "\n\t Order info: " + order + "\n\t Account info: "
                    + account + "\n\t Quote info: " + quote + "\n\t Holding info: " + holding);
        }

        if (order.isBuy()) {
            /*
             * Complete a Buy operation - create a new Holding for the Account -
             * deduct the Order cost from the Account balance
             */

            HoldingDataBean newHolding = createHolding(account, quote, quantity, price);
            order.setHolding(newHolding);
        }

        if (order.isSell()) {
            /*
             * Complete a Sell operation - remove the Holding from the Account -
             * deposit the Order proceeds to the Account balance
             */
            if (holding == null) {
                //Log.error("TradeSLSBBean:completeOrder -- Unable to sell order " + order.getOrderID() + " holding already sold");
                order.cancel();
                throw new EJBException("TradeSLSBBean:completeOrder -- Unable to sell order " + order.getOrderID() + " holding already sold");
            } else {
                entityManager.remove(holding);
                order.setHolding(null);
            }
            
            
        }
        order.setOrderStatus("closed");

        order.setCompletionDate(new java.sql.Timestamp(System.currentTimeMillis()));

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:completeOrder--> Completed Order " + order.getOrderID() + "\n\t Order info: " + order + "\n\t Account info: " + account
                    + "\n\t Quote info: " + quote + "\n\t Holding info: " + holding);
        }
        // if (Log.doTrace())
        // Log.trace("Calling TradeAction:orderCompleted from Session EJB using Session Object");
        // FUTURE All getEJBObjects could be local -- need to add local I/F

        TradeAction tradeAction = new TradeAction();
        tradeAction.orderCompleted(userID, orderID);

       
        
        return order;
    }

    @Override
    public void cancelOrder(Integer orderID, boolean twoPhase) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:cancelOrder", orderID + " twoPhase=" + twoPhase);
        }

        OrderDataBean order = entityManager.find(OrderDataBean.class, orderID);
        order.cancel();
    }

    @Override
    public void orderCompleted(String userID, Integer orderID) {
        throw new UnsupportedOperationException("TradeSLSBBean:orderCompleted method not supported");
    }

    @Override
    public Collection<OrderDataBean> getOrders(String userID) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getOrders", userID);
        }

        AccountProfileDataBean profile = entityManager.find(AccountProfileDataBean.class, userID);
        AccountDataBean account = profile.getAccount();
        return account.getOrders();
    }

    @Override
    public Collection<OrderDataBean> getClosedOrders(String userID) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getClosedOrders", userID);
        }

        try {
            /* I want to do a CriteriaUpdate here, but there are issues with JBoss/Hibernate */
            CriteriaBuilder criteriaBuilder = entityManager.getCriteriaBuilder();
            CriteriaQuery<OrderDataBean> criteriaQuery = criteriaBuilder.createQuery(OrderDataBean.class);
            Root<OrderDataBean> orders = criteriaQuery.from(OrderDataBean.class);
            criteriaQuery.select(orders);
            criteriaQuery.where(
              criteriaBuilder.equal(orders.get("orderStatus"), 
              criteriaBuilder.parameter(String.class, "p_status")),
              criteriaBuilder.equal(orders.get("account").get("profile").get("userID"),
              criteriaBuilder.parameter(String.class, "p_userid")));
            
            TypedQuery<OrderDataBean> q = entityManager.createQuery(criteriaQuery);
            q.setParameter("p_status", "closed");
            q.setParameter("p_userid", userID);
            List<OrderDataBean> results = q.getResultList();
            
            Iterator<OrderDataBean> itr = results.iterator();
            
            // Spin through the orders to remove or mark completed
            while (itr.hasNext()) {
                OrderDataBean order = itr.next();
                // TODO: Investigate ConncurrentModification Exceptions                                
                if (TradeConfig.getLongRun()) {
                    //Added this for Longruns (to prevent orderejb growth)
                    entityManager.remove(order); 
                }
                else {
                    order.setOrderStatus("completed");
                }
            }

            return results;
            
        } catch (Exception e) {
            Log.error("TradeSLSBBean.getClosedOrders", e);
            throw new EJBException("TradeSLSBBean.getClosedOrders - error", e);
        }
    }

    @Override
    public QuoteDataBean createQuote(String symbol, String companyName, BigDecimal price) {
        try {
            QuoteDataBean quote = new QuoteDataBean(symbol, companyName, 0, price, price, price, price, 0);
            entityManager.persist(quote);
            if (Log.doTrace()) {
                Log.trace("TradeSLSBBean:createQuote-->" + quote);
            }
            return quote;
        } catch (Exception e) {
            Log.error("TradeSLSBBean:createQuote -- exception creating Quote", e);
            throw new EJBException(e);
        }
    }

    @Override
    public QuoteDataBean getQuote(String symbol) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getQuote", symbol);
        }

        return entityManager.find(QuoteDataBean.class, symbol);
    }

    @Override
    public Collection<QuoteDataBean> getAllQuotes() {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getAllQuotes");
        }

        TypedQuery<QuoteDataBean> query = entityManager.createNamedQuery("quoteejb.allQuotes",QuoteDataBean.class);
        return query.getResultList();
    }

    @Override
    public QuoteDataBean updateQuotePriceVolume(String symbol, BigDecimal changeFactor, double sharesTraded) {
        if (!TradeConfig.getUpdateQuotePrices()) {
            return new QuoteDataBean();
        }

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:updateQuote", symbol, changeFactor);
        }

        TypedQuery<QuoteDataBean> q = entityManager.createNamedQuery("quoteejb.quoteForUpdate",QuoteDataBean.class);
        q.setParameter(1, symbol);
        QuoteDataBean quote = q.getSingleResult();

        BigDecimal oldPrice = quote.getPrice();
        BigDecimal openPrice = quote.getOpen();

        if (oldPrice.equals(TradeConfig.PENNY_STOCK_PRICE)) {
            changeFactor = TradeConfig.PENNY_STOCK_RECOVERY_MIRACLE_MULTIPLIER;
        } else if (oldPrice.compareTo(TradeConfig.MAXIMUM_STOCK_PRICE) > 0) {
            changeFactor = TradeConfig.MAXIMUM_STOCK_SPLIT_MULTIPLIER;
        }

        BigDecimal newPrice = changeFactor.multiply(oldPrice).setScale(2, BigDecimal.ROUND_HALF_UP);

        quote.setPrice(newPrice);
        quote.setChange(newPrice.subtract(openPrice).doubleValue());
        quote.setVolume(quote.getVolume() + sharesTraded);
        entityManager.merge(quote);

        context.getBusinessObject(TradeSLSBLocal.class).publishQuotePriceChange(quote, oldPrice, changeFactor, sharesTraded);
       
        return quote;
    }

    @Override
    public Collection<HoldingDataBean> getHoldings(String userID) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getHoldings", userID);
        }

        CriteriaBuilder criteriaBuilder = entityManager.getCriteriaBuilder();
        CriteriaQuery<HoldingDataBean> criteriaQuery = criteriaBuilder.createQuery(HoldingDataBean.class);
        Root<HoldingDataBean> holdings = criteriaQuery.from(HoldingDataBean.class);
        criteriaQuery.where(
          criteriaBuilder.equal(holdings.get("account").get("profile").get("userID"), 
          criteriaBuilder.parameter(String.class, "p_userid")));
        criteriaQuery.select(holdings);

        TypedQuery<HoldingDataBean> typedQuery = entityManager.createQuery(criteriaQuery);
        typedQuery.setParameter("p_userid", userID);
               
        return typedQuery.getResultList();
    }

    @Override
    public HoldingDataBean getHolding(Integer holdingID) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getHolding", holdingID);
        }
        return entityManager.find(HoldingDataBean.class, holdingID);
    }

    @Override
    public AccountDataBean getAccountData(String userID) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getAccountData", userID);
        }

        AccountProfileDataBean profile = entityManager.find(AccountProfileDataBean.class, userID);
        AccountDataBean account = profile.getAccount();

        // Added to populate transient field for account
        account.setProfileID(profile.getUserID());
        
        return account;
    }

    @Override
    public AccountProfileDataBean getAccountProfileData(String userID) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:getProfileData", userID);
        }

        return entityManager.find(AccountProfileDataBean.class, userID);
    }

    @Override
    public AccountProfileDataBean updateAccountProfile(AccountProfileDataBean profileData) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:updateAccountProfileData", profileData);
        }
             
        AccountProfileDataBean temp = entityManager.find(AccountProfileDataBean.class, profileData.getUserID());
        temp.setAddress(profileData.getAddress());
        temp.setPassword(profileData.getPassword());
        temp.setFullName(profileData.getFullName());
        temp.setCreditCard(profileData.getCreditCard());
        temp.setEmail(profileData.getEmail());

        entityManager.merge(temp);

        return temp;
    }

    @Override
    public AccountDataBean login(String userID, String password) throws RollbackException {
        AccountProfileDataBean profile = entityManager.find(AccountProfileDataBean.class, userID);

        if (profile == null) {
            throw new EJBException("No such user: " + userID);
        }
        
        AccountDataBean account = profile.getAccount();

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:login", userID, password);
        }
        account.login(password);
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:login(" + userID + "," + password + ") success" + account);
        }
        
        return account;
    }

    @Override
    public void logout(String userID) {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:logout", userID);
        }

        AccountProfileDataBean profile = entityManager.find(AccountProfileDataBean.class, userID);
        AccountDataBean account = profile.getAccount();

        account.logout();

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:logout(" + userID + ") success");
        }
        
    }

    @Override
    public AccountDataBean register(String userID, String password, String fullname, String address, String email, String creditcard, BigDecimal openBalance) {
        AccountDataBean account = null;
        AccountProfileDataBean profile = null;

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:register", userID, password, fullname, address, email, creditcard, openBalance);
        }

        // Check to see if a profile with the desired userID already exists
        profile = entityManager.find(AccountProfileDataBean.class, userID);

        if (profile != null) {
            Log.error("Failed to register new Account - AccountProfile with userID(" + userID + ") already exists");
            return null;
        } else {
            profile = new AccountProfileDataBean(userID, password, fullname, address, email, creditcard);
            account = new AccountDataBean(0, 0, null, new Timestamp(System.currentTimeMillis()), openBalance, openBalance, userID);

            profile.setAccount(account);
            account.setProfile(profile);

            entityManager.persist(profile);
            entityManager.persist(account);
        }

        return account;
    }

    @Override
    @TransactionAttribute(TransactionAttributeType.NOT_SUPPORTED)
    public RunStatsDataBean resetTrade(boolean deleteAll) throws Exception {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:resetTrade", deleteAll);
        }

        return new com.ibm.websphere.samples.daytrader.direct.TradeDirect(false).resetTrade(deleteAll);
    }

    @TransactionAttribute(TransactionAttributeType.REQUIRES_NEW)
    public void publishQuotePriceChange(QuoteDataBean quote, BigDecimal oldPrice, BigDecimal changeFactor, double sharesTraded) {
        if (!TradeConfig.getPublishQuotePriceChange()) {
            return;
        }
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:publishQuotePricePublishing -- quoteData = " + quote);
        }

        try (JMSContext topicContext = topicConnectionFactory.createContext();) {
    		TextMessage message = topicContext.createTextMessage();

    		message.setStringProperty("command", "updateQuote");
            message.setStringProperty("symbol", quote.getSymbol());
            message.setStringProperty("company", quote.getCompanyName());
            message.setStringProperty("price", quote.getPrice().toString());
            message.setStringProperty("oldPrice", oldPrice.toString());
            message.setStringProperty("open", quote.getOpen().toString());
            message.setStringProperty("low", quote.getLow().toString());
            message.setStringProperty("high", quote.getHigh().toString());
            message.setDoubleProperty("volume", quote.getVolume());
            message.setStringProperty("changeFactor", changeFactor.toString());
            message.setDoubleProperty("sharesTraded", sharesTraded);
            message.setLongProperty("publishTime", System.currentTimeMillis());
            message.setText("Update Stock price for " + quote.getSymbol() + " old price = " + oldPrice + " new price = " + quote.getPrice());
    		        		
    		topicContext.createProducer().send(tradeStreamerTopic, message);
    	} catch (Exception e) {
    		 throw new EJBException(e.getMessage(), e); // pass the exception
    	}
    }

    private OrderDataBean createOrder(AccountDataBean account, QuoteDataBean quote, HoldingDataBean holding, String orderType, double quantity) {

        OrderDataBean order;

        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:createOrder(orderID=" + " account=" + ((account == null) ? null : account.getAccountID()) + " quote="
                    + ((quote == null) ? null : quote.getSymbol()) + " orderType=" + orderType + " quantity=" + quantity);
        }
        try {
            order = new OrderDataBean(orderType, "open", new Timestamp(System.currentTimeMillis()), null, quantity, quote.getPrice().setScale(
                    FinancialUtils.SCALE, FinancialUtils.ROUND), TradeConfig.getOrderFee(orderType), account, quote, holding);
            entityManager.persist(order);
        } catch (Exception e) {
            Log.error("TradeSLSBBean:createOrder -- failed to create Order. The stock/quote may not exist in the database.", e);
            throw new EJBException("TradeSLSBBean:createOrder -- failed to create Order. Check that the symbol exists in the database.", e);
        }
        return order;
    }

    private HoldingDataBean createHolding(AccountDataBean account, QuoteDataBean quote, double quantity, BigDecimal purchasePrice) throws Exception {
        HoldingDataBean newHolding = new HoldingDataBean(quantity, purchasePrice, new Timestamp(System.currentTimeMillis()), account, quote);
        entityManager.persist(newHolding);
        return newHolding;
    }

    public double investmentReturn(double investment, double NetValue) throws Exception {
        if (Log.doTrace()) {
            Log.trace("TradeSLSBBean:investmentReturn");
        }

        double diff = NetValue - investment;
        double ir = diff / investment;
        return ir;
    }

    public QuoteDataBean pingTwoPhase(String symbol) throws Exception {
      
    	if (Log.doTrace()) {
    		Log.trace("TradeSLSBBean:pingTwoPhase", symbol);
    	}
                     
    	QuoteDataBean quoteData = null;
            
    	try (JMSContext queueContext = queueConnectionFactory.createContext();) {
    		// Get a Quote and send a JMS message in a 2-phase commit
    		quoteData = entityManager.find(QuoteDataBean.class, symbol);
                		    		
    		TextMessage message = queueContext.createTextMessage();

    		message.setStringProperty("command", "ping");
    		message.setLongProperty("publishTime", System.currentTimeMillis());
    		message.setText("Ping message for queue java:comp/env/jms/TradeBrokerQueue sent from TradeSLSBBean:pingTwoPhase at " + new java.util.Date());
    		queueContext.createProducer().send(tradeBrokerQueue, message);
    	} catch (Exception e) {
    		Log.error("TradeSLSBBean:pingTwoPhase -- exception caught", e);
    	}
            	
    	return quoteData;
    } 
    
    class quotePriceComparator implements Comparator<Object> {

        @Override
        public int compare(Object quote1, Object quote2) {
            double change1 = ((QuoteDataBean) quote1).getChange();
            double change2 = ((QuoteDataBean) quote2).getChange();
            return new Double(change2).compareTo(change1);
        }
    }

    @PostConstruct
    public void postConstruct() {
               
        if (Log.doTrace()) {
            Log.trace("updateQuotePrices: " + TradeConfig.getUpdateQuotePrices());
            Log.trace("publishQuotePriceChange: " + TradeConfig.getPublishQuotePriceChange());
        }
    }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/ejb3/TradeSLSBBean.java:TradeSLSBBean.<init>
// Node: TransactionAttribute
// Node: TransactionManagement
// Node: TradeSLSBBean
// Node: getMarketSummaryDataBean
// Node: find
// Node: getAccount
// Node: createOrder
// Node: setBalance
// Node: flush
// Node: cancel
// Node: setOrderStatus
// Node: getUserID
// Node: remove
// Node: getCriteriaBuilder
// Node: createQuery
// Node: from
// Node: select
// Node: where
// Node: equal
// Node: get
// Node: parameter
// Node: setParameter
// Node: getResultList
// Node: Longruns
// Node: createNamedQuery
// Node: getUpdateQuotePrices
// Node: getSingleResult
// Node: getAddress
// Node: getPassword
// Node: getFullName
// Node: getCreditCard
// Node: getEmail
// Node: postConstruct
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
package com.ibm.websphere.samples.daytrader.ejb3;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

import javax.annotation.PostConstruct;
import javax.ejb.Lock;
import javax.ejb.LockType;
import javax.ejb.Schedule;
import javax.ejb.Singleton;
import javax.persistence.EntityManager;
import javax.persistence.PersistenceContext;
import javax.persistence.TypedQuery;
import javax.persistence.criteria.CriteriaBuilder;
import javax.persistence.criteria.CriteriaQuery;
import javax.persistence.criteria.Root;

import com.ibm.websphere.samples.daytrader.beans.MarketSummaryDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.FinancialUtils;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Singleton
public class MarketSummarySingleton {
    
    private MarketSummaryDataBean marketSummaryDataBean;
    
    @PersistenceContext
    private EntityManager entityManager;
    
    @PostConstruct 
    private void setup () {
        updateMarketSummary();
    }
    
    /* Update Market Summary every 20 seconds */
    @Schedule(second = "*/20",minute = "*", hour = "*", persistent = false)
    private void updateMarketSummary() { 
        
        if (Log.doTrace()) {
            Log.trace("MarketSummarySingleton:updateMarketSummary -- updating market summary");
        }
                        
        if (TradeConfig.getRunTimeMode() != TradeConfig.EJB3)
        {
            if (Log.doTrace()) {
                Log.trace("MarketSummarySingleton:updateMarketSummary -- Not EJB3 Mode, so not updating");
            }
            return; // Only do the actual work if in EJB3 Mode
        }
        
        List<QuoteDataBean> quotes;
        
        try {        
        	// Find Trade Stock Index Quotes (Top 100 quotes) ordered by their change in value
        	CriteriaBuilder criteriaBuilder = entityManager.getCriteriaBuilder();
        	CriteriaQuery<QuoteDataBean> criteriaQuery = criteriaBuilder.createQuery(QuoteDataBean.class);
        	Root<QuoteDataBean> quoteRoot = criteriaQuery.from(QuoteDataBean.class);
        	criteriaQuery.orderBy(criteriaBuilder.desc(quoteRoot.get("change1")));
        	criteriaQuery.select(quoteRoot);
        	TypedQuery<QuoteDataBean> q = entityManager.createQuery(criteriaQuery);
        	quotes = q.getResultList();
        } catch (Exception e) {
        	Log.debug("Warning: The database has not been configured. If this is the first time the application has been started, please create and populate the database tables. Then restart the server.");
        	return;
        }	
                
        /* TODO: Make this cleaner? */
        QuoteDataBean[] quoteArray = quotes.toArray(new QuoteDataBean[quotes.size()]);
        ArrayList<QuoteDataBean> topGainers = new ArrayList<QuoteDataBean>(5);
        ArrayList<QuoteDataBean> topLosers = new ArrayList<QuoteDataBean>(5);
        BigDecimal TSIA = FinancialUtils.ZERO;
        BigDecimal openTSIA = FinancialUtils.ZERO;
        double totalVolume = 0.0;

        if (quoteArray.length > 5) {
            for (int i = 0; i < 5; i++) {
                topGainers.add(quoteArray[i]);
            }
            for (int i = quoteArray.length - 1; i >= quoteArray.length - 5; i--) {
                topLosers.add(quoteArray[i]);
            }

            for (QuoteDataBean quote : quoteArray) {
                BigDecimal price = quote.getPrice();
                BigDecimal open = quote.getOpen();
                double volume = quote.getVolume();
                TSIA = TSIA.add(price);
                openTSIA = openTSIA.add(open);
                totalVolume += volume;
            }
            TSIA = TSIA.divide(new BigDecimal(quoteArray.length), FinancialUtils.ROUND);
            openTSIA = openTSIA.divide(new BigDecimal(quoteArray.length), FinancialUtils.ROUND);
        }
        
        setMarketSummaryDataBean(new MarketSummaryDataBean(TSIA, openTSIA, totalVolume, topGainers, topLosers));
    }

    @Lock(LockType.READ)
    public MarketSummaryDataBean getMarketSummaryDataBean() {       
        return marketSummaryDataBean;
    }

    @Lock(LockType.WRITE)
    public void setMarketSummaryDataBean(MarketSummaryDataBean marketSummaryDataBean) {
        this.marketSummaryDataBean = marketSummaryDataBean;
    }

}


// Node: setup
// Node: updateMarketSummary
// Node: Schedule
// Node: orderBy
// Node: desc
// Node: setMarketSummaryDataBean
// Node: Lock
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
package com.ibm.websphere.samples.daytrader.ejb3;

import javax.annotation.Resource;
import javax.ejb.ActivationConfigProperty;
import javax.ejb.EJB;
import javax.ejb.MessageDriven;
import javax.ejb.MessageDrivenContext;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.ejb.TransactionManagement;
import javax.ejb.TransactionManagementType;
import javax.jms.Message;
import javax.jms.MessageListener;
import javax.jms.TextMessage;

import com.ibm.websphere.samples.daytrader.TradeServices;
import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.MDBStats;
import com.ibm.websphere.samples.daytrader.util.TimerStat;

@TransactionAttribute(TransactionAttributeType.REQUIRED)
@TransactionManagement(TransactionManagementType.CONTAINER)
@MessageDriven(activationConfig = { @ActivationConfigProperty(propertyName = "acknowledgeMode", propertyValue = "Auto-acknowledge"),
        @ActivationConfigProperty(propertyName = "destinationType", propertyValue = "javax.jms.Queue"),
        @ActivationConfigProperty(propertyName = "destination", propertyValue = "TradeBrokerQueue"),
        @ActivationConfigProperty(propertyName = "subscriptionDurability", propertyValue = "NonDurable") })
public class DTBroker3MDB implements MessageListener {
    private final MDBStats mdbStats;
    private int statInterval = 10000;

    
    // TODO: Using local interface, make it configurable to use remote?
    @EJB
    private TradeSLSBLocal tradeSLSB;

    @Resource
    public MessageDrivenContext mdc;

    public DTBroker3MDB() {
        if (Log.doTrace()) {
            Log.trace("DTBroker3MDB:DTBroker3MDB()");
        }
        if (statInterval <= 0) {
            statInterval = 10000;
        }
        mdbStats = MDBStats.getInstance();
    }

    @Override
    public void onMessage(Message message) {
        try {
            if (Log.doTrace()) {
                Log.trace("TradeBroker:onMessage -- received message -->" + ((TextMessage) message).getText() + "command-->"
                        + message.getStringProperty("command") + "<--");
            }

            if (message.getJMSRedelivered()) {
                Log.log("DTBroker3MDB: The following JMS message was redelivered due to a rollback:\n" + ((TextMessage) message).getText());
                // Order has been cancelled -- ignore returned messages
                return;
            }
            String command = message.getStringProperty("command");
            if (command == null) {
                Log.debug("DTBroker3MDB:onMessage -- received message with null command. Message-->" + message);
                return;
            }
            if (command.equalsIgnoreCase("neworder")) {
                /* Get the Order ID and complete the Order */
                Integer orderID = new Integer(message.getIntProperty("orderID"));
                boolean twoPhase = message.getBooleanProperty("twoPhase");
                boolean direct = message.getBooleanProperty("direct");
                long publishTime = message.getLongProperty("publishTime");
                long receiveTime = System.currentTimeMillis();

                TradeServices trade = null;

                try {
                    trade = getTrade(direct);

                    if (Log.doTrace()) {
                        Log.trace("DTBroker3MDB:onMessage - completing order " + orderID + " twoPhase=" + twoPhase + " direct=" + direct);
                    }

                    trade.completeOrder(orderID, twoPhase);

                    TimerStat currentStats = mdbStats.addTiming("DTBroker3MDB:neworder", publishTime, receiveTime);

                    if ((currentStats.getCount() % statInterval) == 0) {
                        Log.log(" DTBroker3MDB: processed " + statInterval + " stock trading orders." +
                                " Total NewOrders process = " + currentStats.getCount() +
                                "Time (in seconds):" +
                                " min: " +currentStats.getMinSecs()+
                                " max: " +currentStats.getMaxSecs()+
                                " avg: " +currentStats.getAvgSecs());
                    }
                } catch (Exception e) {
                    Log.error("DTBroker3MDB:onMessage Exception completing order: " + orderID + "\n", e);
                    mdc.setRollbackOnly();
                    /*
                     * UPDATE - order is cancelled in trade if an error is
                     * caught try { trade.cancelOrder(orderID, twoPhase); }
                     * catch (Exception e2) { Log.error("order cancel failed",
                     * e); }
                     */
                }
            } else if (command.equalsIgnoreCase("ping")) {
                if (Log.doTrace()) {
                    Log.trace("DTBroker3MDB:onMessage  received test command -- message: " + ((TextMessage) message).getText());
                }

                long publishTime = message.getLongProperty("publishTime");
                long receiveTime = System.currentTimeMillis();

                TimerStat currentStats = mdbStats.addTiming("DTBroker3MDB:ping", publishTime, receiveTime);

                if ((currentStats.getCount() % statInterval) == 0) {
                    Log.log(" DTBroker3MDB: received " + statInterval + " ping messages." +
                            " Total ping message count = " + currentStats.getCount() +
                            " Time (in seconds):" +
                            " min: " +currentStats.getMinSecs()+
                            " max: " +currentStats.getMaxSecs()+
                            " avg: " +currentStats.getAvgSecs());
                }
            } else {
                Log.error("DTBroker3MDB:onMessage - unknown message request command-->" + command + "<-- message=" + ((TextMessage) message).getText());
            }
        } catch (Throwable t) {
            // JMS onMessage should handle all exceptions
            Log.error("DTBroker3MDB: Error rolling back transaction", t);
            mdc.setRollbackOnly();
        }
    }

    private TradeServices getTrade(boolean direct) throws Exception {
        TradeServices trade;
        if (direct) {
            trade = new TradeDirect();
        } else {
            trade = tradeSLSB;
        }

        return trade;
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/ejb3/DTBroker3MDB.java:DTBroker3MDB.<init>
// Node: MessageDriven
// Node: ActivationConfigProperty
// Node: DTBroker3MDB
// Node: getInstance
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
package com.ibm.websphere.samples.daytrader.ejb3;

import javax.annotation.Resource;
import javax.ejb.ActivationConfigProperty;
import javax.ejb.MessageDriven;
import javax.ejb.MessageDrivenContext;
import javax.ejb.TransactionAttribute;
import javax.ejb.TransactionAttributeType;
import javax.ejb.TransactionManagement;
import javax.ejb.TransactionManagementType;
import javax.enterprise.event.Event;
import javax.inject.Inject;
import javax.jms.Message;
import javax.jms.MessageListener;
import javax.jms.TextMessage;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.MDBStats;
import com.ibm.websphere.samples.daytrader.util.TimerStat;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;
import com.ibm.websphere.samples.daytrader.util.WebSocketJMSMessage;

@TransactionAttribute(TransactionAttributeType.REQUIRED)
@TransactionManagement(TransactionManagementType.CONTAINER)
@MessageDriven(activationConfig = { @ActivationConfigProperty(propertyName = "acknowledgeMode", propertyValue = "Auto-acknowledge"),
        @ActivationConfigProperty(propertyName = "destinationType", propertyValue = "javax.jms.Topic"),
        @ActivationConfigProperty(propertyName = "destination", propertyValue = "TradeStreamerTopic"),
        @ActivationConfigProperty(propertyName = "subscriptionDurability", propertyValue = "NonDurable") })
public class DTStreamer3MDB implements MessageListener {

    private final MDBStats mdbStats;
    private int statInterval = 10000;

    @Resource
    public MessageDrivenContext mdc;

    /** Creates a new instance of TradeSteamerMDB */
    public DTStreamer3MDB() {
        if (Log.doTrace()) {
            Log.trace("DTStreamer3MDB:DTStreamer3MDB()");
        }
        if (statInterval <= 0) {
            statInterval = 10000;
        }
        mdbStats = MDBStats.getInstance();
    }

    @Inject
    @WebSocketJMSMessage
    Event<Message> jmsEvent;

    @Override
    public void onMessage(Message message) {

        try {
            if (Log.doTrace()) {
                Log.trace("DTStreamer3MDB:onMessage -- received message -->" + ((TextMessage) message).getText() + "command-->"
                        + message.getStringProperty("command") + "<--");
            }
            String command = message.getStringProperty("command");
            if (command == null) {
                Log.debug("DTStreamer3MDB:onMessage -- received message with null command. Message-->" + message);
                return;
            }
            if (command.equalsIgnoreCase("updateQuote")) {
                if (Log.doTrace()) {
                    Log.trace("DTStreamer3MDB:onMessage -- received message -->" + ((TextMessage) message).getText() + "\n\t symbol = "
                            + message.getStringProperty("symbol") + "\n\t current price =" + message.getStringProperty("price") + "\n\t old price ="
                            + message.getStringProperty("oldPrice"));
                }
                long publishTime = message.getLongProperty("publishTime");
                long receiveTime = System.currentTimeMillis();

                TimerStat currentStats = mdbStats.addTiming("DTStreamer3MDB:udpateQuote", publishTime, receiveTime);

                if ((currentStats.getCount() % statInterval) == 0) {
                    Log.log(" DTStreamer3MDB: " + statInterval + " prices updated:" +
                            " Total message count = " + currentStats.getCount() +
                            " Time (in seconds):" +
                            " min: " +currentStats.getMinSecs()+
                            " max: " +currentStats.getMaxSecs()+
                            " avg: " +currentStats.getAvgSecs() );
                }
                
                // Fire message to Websocket Endpoint
                // Limit Symbols that get sent with percentageToWebSocket (default 5%).
                int symbolNumber = new Integer(message.getStringProperty("symbol").substring(2));
                
                if ( symbolNumber < TradeConfig.getMAX_QUOTES() * TradeConfig.getPercentSentToWebsocket() * 0.01) {
                	jmsEvent.fire(message);
                }
                
            } else if (command.equalsIgnoreCase("ping")) {
                if (Log.doTrace()) {
                    Log.trace("DTStreamer3MDB:onMessage  received ping command -- message: " + ((TextMessage) message).getText());
                }

                long publishTime = message.getLongProperty("publishTime");
                long receiveTime = System.currentTimeMillis();

                TimerStat currentStats = mdbStats.addTiming("DTStreamer3MDB:ping", publishTime, receiveTime);

                if ((currentStats.getCount() % statInterval) == 0) {
                    Log.log(" DTStreamer3MDB: received " + statInterval + " ping messages." +
                            " Total message count = " + currentStats.getCount() +
                            " Time (in seconds):" +
                            " min: " +currentStats.getMinSecs()+
                            " max: " +currentStats.getMaxSecs()+
                            " avg: " +currentStats.getAvgSecs());
                }
            } else {
                Log.error("DTStreamer3MDB:onMessage - unknown message request command-->" + command + "<-- message=" + ((TextMessage) message).getText());
            }
        } catch (Throwable t) {
            // JMS onMessage should handle all exceptions
            Log.error("DTStreamer3MDB: Exception", t);
             //UPDATE - Not rolling back for now -- so error messages are not redelivered
             mdc.setRollbackOnly();
        }
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/ejb3/DTStreamer3MDB.java:DTStreamer3MDB.<init>
// Node: DTStreamer3MDB
// Node: getString
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


// Node: nextUserID
// Node: getNextUserIDFromDeck
// Node: shuffle
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

/**
 *
 * To change this generated comment edit the template variable "typecomment":
 * Window>Preferences>Java>Templates. To enable and disable the creation of type
 * comments go to Window>Preferences>Java>Code Generation.
 */
public class MDBStats extends java.util.HashMap<String, TimerStat> {

    private static final long serialVersionUID = -3759835921094193760L;
    // Singleton class
    private static MDBStats mdbStats = null;

    private MDBStats() {
    }

    public static synchronized MDBStats getInstance() {
        if (mdbStats == null) {
            mdbStats = new MDBStats();
        }
        return mdbStats;
    }

    public TimerStat addTiming(String type, long sendTime, long recvTime) {
        TimerStat stats = null;
        synchronized (type) {

            stats = get(type);
            if (stats == null) {
                stats = new TimerStat();
            }

            long time = recvTime - sendTime;
            if (time > stats.getMax()) {
                stats.setMax(time);
            }
            if (time < stats.getMin()) {
                stats.setMin(time);
            }
            stats.setCount(stats.getCount() + 1);
            stats.setTotalTime(stats.getTotalTime() + time);

            put(type, stats);
        }
        return stats;
    }

    public synchronized void reset() {
        clear();
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/util/MDBStats.java:MDBStats.<init>
// Node: MDBStats
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

import java.util.AbstractSequentialList;
import java.util.ListIterator;

public class KeyBlock extends AbstractSequentialList<Object> {

    // min and max provide range of valid primary keys for this KeyBlock
    private int min = 0;
    private int max = 0;
    private int index = 0;

    /**
     * Constructor for KeyBlock
     */
    public KeyBlock() {
        super();
        min = 0;
        max = 0;
        index = min;
    }

    /**
     * Constructor for KeyBlock
     */
    public KeyBlock(int min, int max) {
        super();
        this.min = min;
        this.max = max;
        index = min;
    }

    /**
     * @see AbstractCollection#size()
     */
    @Override
    public int size() {
        return (max - min) + 1;
    }

    /**
     * @see AbstractSequentialList#listIterator(int)
     */
    @Override
    public ListIterator<Object> listIterator(int arg0) {
        return new KeyBlockIterator();
    }

    class KeyBlockIterator implements ListIterator<Object> {

        /**
         * @see ListIterator#hasNext()
         */
        @Override
        public boolean hasNext() {
            return index <= max;
        }

        /**
         * @see ListIterator#next()
         */
        @Override
        public synchronized Object next() {
            if (index > max) {
                throw new java.lang.RuntimeException("KeyBlock:next() -- Error KeyBlock depleted");
            }
            return new Integer(index++);
        }

        /**
         * @see ListIterator#hasPrevious()
         */
        @Override
        public boolean hasPrevious() {
            return index > min;
        }

        /**
         * @see ListIterator#previous()
         */
        @Override
        public Object previous() {
            return new Integer(--index);
        }

        /**
         * @see ListIterator#nextIndex()
         */
        @Override
        public int nextIndex() {
            return index - min;
        }

        /**
         * @see ListIterator#previousIndex()
         */
        @Override
        public int previousIndex() {
            throw new UnsupportedOperationException("KeyBlock: previousIndex() not supported");
        }

        /**
         * @see ListIterator#add()
         */
        @Override
        public void add(Object o) {
            throw new UnsupportedOperationException("KeyBlock: add() not supported");
        }

        /**
         * @see ListIterator#remove()
         */
        @Override
        public void remove() {
            throw new UnsupportedOperationException("KeyBlock: remove() not supported");
        }

        /**
         * @see ListIterator#set(Object)
         */
        @Override
        public void set(Object arg0) {
        }
    }
}

// Node: set
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
package com.ibm.websphere.samples.daytrader.entities;

import java.io.Serializable;
import java.math.BigDecimal;
import java.sql.Timestamp;
import java.util.Collection;
import java.util.Date;

import javax.ejb.EJBException;
import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.OneToMany;
import javax.persistence.OneToOne;
import javax.persistence.Table;
import javax.persistence.TableGenerator;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;
import javax.persistence.Transient;
import javax.validation.constraints.NotNull;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Entity(name = "accountejb")
@Table(name = "accountejb")
public class AccountDataBean implements Serializable {

    private static final long serialVersionUID = 8437841265136840545L;

    /* Accessor methods for persistent fields */
    @TableGenerator(name = "accountIdGen", table = "KEYGENEJB", pkColumnName = "KEYNAME", valueColumnName = "KEYVAL", pkColumnValue = "account", allocationSize = 1000)
    @Id
    @GeneratedValue(strategy = GenerationType.TABLE, generator = "accountIdGen")
    @Column(name = "ACCOUNTID", nullable = false)
    private Integer accountID; /* accountID */

    @NotNull
    @Column(name = "LOGINCOUNT", nullable = false)
    private int loginCount; /* loginCount */

    @NotNull
    @Column(name = "LOGOUTCOUNT", nullable = false)
    private int logoutCount; /* logoutCount */

    @Column(name = "LASTLOGIN")
    @Temporal(TemporalType.TIMESTAMP)
    private Date lastLogin; /* lastLogin Date */

    @Column(name = "CREATIONDATE")
    @Temporal(TemporalType.TIMESTAMP)
    private Date creationDate; /* creationDate */

    @Column(name = "BALANCE")
    private BigDecimal balance; /* balance */

    @Column(name = "OPENBALANCE")
    private BigDecimal openBalance; /* open balance */

    @OneToMany(mappedBy = "account", fetch = FetchType.LAZY)
    private Collection<OrderDataBean> orders;

    @OneToMany(mappedBy = "account", fetch = FetchType.LAZY)
    private Collection<HoldingDataBean> holdings;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "PROFILE_USERID")
    private AccountProfileDataBean profile;

    /*
     * Accessor methods for relationship fields are only included for the
     * AccountProfile profileID
     */
    @Transient
    private String profileID;

    public AccountDataBean() {
    }

    public AccountDataBean(Integer accountID, int loginCount, int logoutCount, Date lastLogin, Date creationDate, BigDecimal balance, BigDecimal openBalance,
            String profileID) {
        setAccountID(accountID);
        setLoginCount(loginCount);
        setLogoutCount(logoutCount);
        setLastLogin(lastLogin);
        setCreationDate(creationDate);
        setBalance(balance);
        setOpenBalance(openBalance);
        setProfileID(profileID);
    }

    public AccountDataBean(int loginCount, int logoutCount, Date lastLogin, Date creationDate, BigDecimal balance, BigDecimal openBalance, String profileID) {
        setLoginCount(loginCount);
        setLogoutCount(logoutCount);
        setLastLogin(lastLogin);
        setCreationDate(creationDate);
        setBalance(balance);
        setOpenBalance(openBalance);
        setProfileID(profileID);
    }

    public static AccountDataBean getRandomInstance() {
        return new AccountDataBean(new Integer(TradeConfig.rndInt(100000)), // accountID
                TradeConfig.rndInt(10000), // loginCount
                TradeConfig.rndInt(10000), // logoutCount
                new java.util.Date(), // lastLogin
                new java.util.Date(TradeConfig.rndInt(Integer.MAX_VALUE)), // creationDate
                TradeConfig.rndBigDecimal(1000000.0f), // balance
                TradeConfig.rndBigDecimal(1000000.0f), // openBalance
                TradeConfig.rndUserID() // profileID
        );
    }

    @Override
    public String toString() {
        return "\n\tAccount Data for account: " + getAccountID() + "\n\t\t   loginCount:" + getLoginCount() + "\n\t\t  logoutCount:" + getLogoutCount()
                + "\n\t\t    lastLogin:" + getLastLogin() + "\n\t\t creationDate:" + getCreationDate() + "\n\t\t      balance:" + getBalance()
                + "\n\t\t  openBalance:" + getOpenBalance() + "\n\t\t    profileID:" + getProfileID();
    }

    public String toHTML() {
        return "<BR>Account Data for account: <B>" + getAccountID() + "</B>" + "<LI>   loginCount:" + getLoginCount() + "</LI>" + "<LI>  logoutCount:"
                + getLogoutCount() + "</LI>" + "<LI>    lastLogin:" + getLastLogin() + "</LI>" + "<LI> creationDate:" + getCreationDate() + "</LI>"
                + "<LI>      balance:" + getBalance() + "</LI>" + "<LI>  openBalance:" + getOpenBalance() + "</LI>" + "<LI>    profileID:" + getProfileID()
                + "</LI>";
    }

    public void print() {
        Log.log(this.toString());
    }

    public Integer getAccountID() {
        return accountID;
    }

    public void setAccountID(Integer accountID) {
        this.accountID = accountID;
    }

    public int getLoginCount() {
        return loginCount;
    }

    public void setLoginCount(int loginCount) {
        this.loginCount = loginCount;
    }

    public int getLogoutCount() {
        return logoutCount;
    }

    public void setLogoutCount(int logoutCount) {
        this.logoutCount = logoutCount;
    }

    public Date getLastLogin() {
        return lastLogin;
    }

    public void setLastLogin(Date lastLogin) {
        this.lastLogin = lastLogin;
    }

    public Date getCreationDate() {
        return creationDate;
    }

    public void setCreationDate(Date creationDate) {
        this.creationDate = creationDate;
    }

    public BigDecimal getBalance() {
        return balance;
    }

    public void setBalance(BigDecimal balance) {
        this.balance = balance;
    }

    public BigDecimal getOpenBalance() {
        return openBalance;
    }

    public void setOpenBalance(BigDecimal openBalance) {
        this.openBalance = openBalance;
    }

    public String getProfileID() {
        return profileID;
    }

    public void setProfileID(String profileID) {
        this.profileID = profileID;
    }

    /*
     * Disabled for D185273 public String getUserID() { return getProfileID(); }
     */

    public Collection<OrderDataBean> getOrders() {
        return orders;
    }

    public void setOrders(Collection<OrderDataBean> orders) {
        this.orders = orders;
    }

    public Collection<HoldingDataBean> getHoldings() {
        return holdings;
    }

    public void setHoldings(Collection<HoldingDataBean> holdings) {
        this.holdings = holdings;
    }

    public AccountProfileDataBean getProfile() {
        return profile;
    }

    public void setProfile(AccountProfileDataBean profile) {
        this.profile = profile;
    }

    public void login(String password) {
        AccountProfileDataBean profile = getProfile();
        if ((profile == null) || (profile.getPassword().equals(password) == false)) {
            String error = "AccountBean:Login failure for account: " + getAccountID()
                    + ((profile == null) ? "null AccountProfile" : "\n\tIncorrect password-->" + profile.getUserID() + ":" + profile.getPassword());
            throw new EJBException(error);
        }

        setLastLogin(new Timestamp(System.currentTimeMillis()));
        setLoginCount(getLoginCount() + 1);
    }

    public void logout() {
        setLogoutCount(getLogoutCount() + 1);
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (this.accountID != null ? this.accountID.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        
        if (!(object instanceof AccountDataBean)) {
            return false;
        }
        AccountDataBean other = (AccountDataBean) object;

        if (this.accountID != other.accountID && (this.accountID == null || !this.accountID.equals(other.accountID))) {
            return false;
        }

        return true;
    }
}

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
package com.ibm.websphere.samples.daytrader.entities;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.Table;
import javax.persistence.TableGenerator;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;
import javax.persistence.Transient;
import javax.validation.constraints.NotNull;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Entity(name = "holdingejb")
@Table(name = "holdingejb")
public class HoldingDataBean implements Serializable {

    /* persistent/relationship fields */

    private static final long serialVersionUID = -2338411656251935480L;

    @Id
    @TableGenerator(name = "holdingIdGen", table = "KEYGENEJB", pkColumnName = "KEYNAME", valueColumnName = "KEYVAL", pkColumnValue = "holding", allocationSize = 1000)
    @GeneratedValue(strategy = GenerationType.TABLE, generator = "holdingIdGen")
    @Column(name = "HOLDINGID", nullable = false)
    private Integer holdingID; /* holdingID */

    @NotNull
    @Column(name = "QUANTITY", nullable = false)
    private double quantity; /* quantity */

    @Column(name = "PURCHASEPRICE")
    private BigDecimal purchasePrice; /* purchasePrice */

    @Column(name = "PURCHASEDATE")
    @Temporal(TemporalType.TIMESTAMP)
    private Date purchaseDate; /* purchaseDate */

    @Transient
    private String quoteID; /* Holding(*) ---> Quote(1) */

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "ACCOUNT_ACCOUNTID")
    private AccountDataBean account;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "QUOTE_SYMBOL")
    private QuoteDataBean quote;

    public HoldingDataBean() {
    }

    public HoldingDataBean(Integer holdingID, double quantity, BigDecimal purchasePrice, Date purchaseDate, String quoteID) {
        setHoldingID(holdingID);
        setQuantity(quantity);
        setPurchasePrice(purchasePrice);
        setPurchaseDate(purchaseDate);
        setQuoteID(quoteID);
    }

    public HoldingDataBean(double quantity, BigDecimal purchasePrice, Date purchaseDate, AccountDataBean account, QuoteDataBean quote) {
        setQuantity(quantity);
        setPurchasePrice(purchasePrice);
        setPurchaseDate(purchaseDate);
        setAccount(account);
        setQuote(quote);
    }

    public static HoldingDataBean getRandomInstance() {
        return new HoldingDataBean(new Integer(TradeConfig.rndInt(100000)), // holdingID
                TradeConfig.rndQuantity(), // quantity
                TradeConfig.rndBigDecimal(1000.0f), // purchasePrice
                new java.util.Date(TradeConfig.rndInt(Integer.MAX_VALUE)), // purchaseDate
                TradeConfig.rndSymbol() // symbol
        );
    }

    @Override
    public String toString() {
        return "\n\tHolding Data for holding: " + getHoldingID() + "\n\t\t      quantity:" + getQuantity() + "\n\t\t purchasePrice:" + getPurchasePrice()
                + "\n\t\t  purchaseDate:" + getPurchaseDate() + "\n\t\t       quoteID:" + getQuoteID();
    }

    public String toHTML() {
        return "<BR>Holding Data for holding: " + getHoldingID() + "</B>" + "<LI>      quantity:" + getQuantity() + "</LI>" + "<LI> purchasePrice:"
                + getPurchasePrice() + "</LI>" + "<LI>  purchaseDate:" + getPurchaseDate() + "</LI>" + "<LI>       quoteID:" + getQuoteID() + "</LI>";
    }

    public void print() {
        Log.log(this.toString());
    }

    public Integer getHoldingID() {
        return holdingID;
    }

    public void setHoldingID(Integer holdingID) {
        this.holdingID = holdingID;
    }

    public double getQuantity() {
        return quantity;
    }

    public void setQuantity(double quantity) {
        this.quantity = quantity;
    }

    public BigDecimal getPurchasePrice() {
        return purchasePrice;
    }

    public void setPurchasePrice(BigDecimal purchasePrice) {
        this.purchasePrice = purchasePrice;
    }

    public Date getPurchaseDate() {
        return purchaseDate;
    }

    public void setPurchaseDate(Date purchaseDate) {
        this.purchaseDate = purchaseDate;
    }

    public String getQuoteID() {
        if (quote != null) {
            return quote.getSymbol();
        }
        return quoteID;
    }

    public void setQuoteID(String quoteID) {
        this.quoteID = quoteID;
    }

    public AccountDataBean getAccount() {
        return account;
    }

    public void setAccount(AccountDataBean account) {
        this.account = account;
    }

    public QuoteDataBean getQuote() {
        return quote;
    }

    public void setQuote(QuoteDataBean quote) {
        this.quote = quote;
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (this.holdingID != null ? this.holdingID.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        
        if (!(object instanceof HoldingDataBean)) {
            return false;
        }
        HoldingDataBean other = (HoldingDataBean) object;

        if (this.holdingID != other.holdingID && (this.holdingID == null || !this.holdingID.equals(other.holdingID))) {
            return false;
        }

        return true;
    }
}


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
package com.ibm.websphere.samples.daytrader.entities;

//import java.sql.Timestamp;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.Id;
import javax.persistence.OneToOne;
import javax.persistence.Table;
import javax.validation.constraints.NotNull;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Entity(name = "accountprofileejb")
@Table(name = "accountprofileejb")
public class AccountProfileDataBean implements java.io.Serializable {

    /* Accessor methods for persistent fields */

    private static final long serialVersionUID = 2794584136675420624L;

    @Id
    @NotNull
    @Column(name = "USERID", nullable = false)
    private String userID; /* userID */

    @Column(name = "PASSWD")
    private String passwd; /* password */

    @Column(name = "FULLNAME")
    private String fullName; /* fullName */

    @Column(name = "ADDRESS")
    private String address; /* address */

    @Column(name = "EMAIL")
    private String email; /* email */

    @Column(name = "CREDITCARD")
    private String creditCard; /* creditCard */

    @OneToOne(mappedBy = "profile", fetch = FetchType.LAZY)
    private AccountDataBean account;

    public AccountProfileDataBean() {
    }

    public AccountProfileDataBean(String userID, String password, String fullName, String address, String email, String creditCard) {
        setUserID(userID);
        setPassword(password);
        setFullName(fullName);
        setAddress(address);
        setEmail(email);
        setCreditCard(creditCard);
    }

    public static AccountProfileDataBean getRandomInstance() {
        return new AccountProfileDataBean(TradeConfig.rndUserID(), // userID
                TradeConfig.rndUserID(), // passwd
                TradeConfig.rndFullName(), // fullname
                TradeConfig.rndAddress(), // address
                TradeConfig.rndEmail(TradeConfig.rndUserID()), // email
                TradeConfig.rndCreditCard() // creditCard
        );
    }

    @Override
    public String toString() {
        return "\n\tAccount Profile Data for userID:" + getUserID() + "\n\t\t   passwd:" + getPassword() + "\n\t\t   fullName:" + getFullName()
                + "\n\t\t    address:" + getAddress() + "\n\t\t      email:" + getEmail() + "\n\t\t creditCard:" + getCreditCard();
    }

    public String toHTML() {
        return "<BR>Account Profile Data for userID: <B>" + getUserID() + "</B>" + "<LI>   passwd:" + getPassword() + "</LI>" + "<LI>   fullName:"
                + getFullName() + "</LI>" + "<LI>    address:" + getAddress() + "</LI>" + "<LI>      email:" + getEmail() + "</LI>" + "<LI> creditCard:"
                + getCreditCard() + "</LI>";
    }

    public void print() {
        Log.log(this.toString());
    }

    public String getUserID() {
        return userID;
    }

    public void setUserID(String userID) {
        this.userID = userID;
    }

    public String getPassword() {
        return passwd;
    }

    public void setPassword(String password) {
        this.passwd = password;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getCreditCard() {
        return creditCard;
    }

    public void setCreditCard(String creditCard) {
        this.creditCard = creditCard;
    }

    public AccountDataBean getAccount() {
        return account;
    }

    public void setAccount(AccountDataBean account) {
        this.account = account;
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (this.userID != null ? this.userID.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
       
        if (!(object instanceof AccountProfileDataBean)) {
            return false;
        }
        AccountProfileDataBean other = (AccountProfileDataBean) object;

        if (this.userID != other.userID && (this.userID == null || !this.userID.equals(other.userID))) {
            return false;
        }

        return true;
    }
}


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
package com.ibm.websphere.samples.daytrader.entities;

import java.io.Serializable;
import java.math.BigDecimal;
//import java.sql.Timestamp;
import java.util.Date;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.FetchType;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.JoinColumn;
import javax.persistence.ManyToOne;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.OneToOne;
import javax.persistence.Table;
import javax.persistence.TableGenerator;
import javax.persistence.Temporal;
import javax.persistence.TemporalType;
import javax.persistence.Transient;
import javax.validation.constraints.NotNull;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Entity(name = "orderejb")
@Table(name = "orderejb")
@NamedQueries({
        @NamedQuery(name = "orderejb.findByOrderfee", query = "SELECT o FROM orderejb o WHERE o.orderFee = :orderfee"),
        @NamedQuery(name = "orderejb.findByCompletiondate", query = "SELECT o FROM orderejb o WHERE o.completionDate = :completiondate"),
        @NamedQuery(name = "orderejb.findByOrdertype", query = "SELECT o FROM orderejb o WHERE o.orderType = :ordertype"),
        @NamedQuery(name = "orderejb.findByOrderstatus", query = "SELECT o FROM orderejb o WHERE o.orderStatus = :orderstatus"),
        @NamedQuery(name = "orderejb.findByPrice", query = "SELECT o FROM orderejb o WHERE o.price = :price"),
        @NamedQuery(name = "orderejb.findByQuantity", query = "SELECT o FROM orderejb o WHERE o.quantity = :quantity"),
        @NamedQuery(name = "orderejb.findByOpendate", query = "SELECT o FROM orderejb o WHERE o.openDate = :opendate"),
        @NamedQuery(name = "orderejb.findByOrderid", query = "SELECT o FROM orderejb o WHERE o.orderID = :orderid"),
        @NamedQuery(name = "orderejb.findByAccountAccountid", query = "SELECT o FROM orderejb o WHERE o.account.accountID = :accountAccountid"),
        @NamedQuery(name = "orderejb.findByQuoteSymbol", query = "SELECT o FROM orderejb o WHERE o.quote.symbol = :quoteSymbol"),
        @NamedQuery(name = "orderejb.findByHoldingHoldingid", query = "SELECT o FROM orderejb o WHERE o.holding.holdingID = :holdingHoldingid"),
        @NamedQuery(name = "orderejb.closedOrders", query = "SELECT o FROM orderejb o WHERE o.orderStatus = 'closed' AND o.account.profile.userID  = :userID"),
        @NamedQuery(name = "orderejb.completeClosedOrders", query = "UPDATE orderejb o SET o.orderStatus = 'completed' WHERE o.orderStatus = 'closed' AND o.account.profile.userID  = :userID") })
public class OrderDataBean implements Serializable {

    private static final long serialVersionUID = 120650490200739057L;

    @Id
    @TableGenerator(name = "orderIdGen", table = "KEYGENEJB", pkColumnName = "KEYNAME", valueColumnName = "KEYVAL", pkColumnValue = "order", allocationSize = 1000)
    @GeneratedValue(strategy = GenerationType.TABLE, generator = "orderIdGen")
    @Column(name = "ORDERID", nullable = false)
    private Integer orderID; /* orderID */

    @Column(name = "ORDERTYPE")
    private String orderType; /* orderType (buy, sell, etc.) */

    @Column(name = "ORDERSTATUS")
    private String orderStatus; /*
                                 * orderStatus (open, processing, completed,
                                 * closed, cancelled)
                                 */

    @Column(name = "OPENDATE")
    @Temporal(TemporalType.TIMESTAMP)
    private Date openDate; /* openDate (when the order was entered) */

    @Column(name = "COMPLETIONDATE")
    @Temporal(TemporalType.TIMESTAMP)
    private Date completionDate; /* completionDate */

    @NotNull
    @Column(name = "QUANTITY", nullable = false)
    private double quantity; /* quantity */

    @Column(name = "PRICE")
    private BigDecimal price; /* price */

    @Column(name = "ORDERFEE")
    private BigDecimal orderFee; /* price */

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "ACCOUNT_ACCOUNTID")
    private AccountDataBean account;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "QUOTE_SYMBOL")
    private QuoteDataBean quote;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "HOLDING_HOLDINGID")
    private HoldingDataBean holding;

    /* Fields for relationship fields are not kept in the Data Bean */
    @Transient
    private String symbol;

    public OrderDataBean() {
    }

    public OrderDataBean(Integer orderID, String orderType, String orderStatus, Date openDate, Date completionDate, double quantity, BigDecimal price,
            BigDecimal orderFee, String symbol) {
        setOrderID(orderID);
        setOrderType(orderType);
        setOrderStatus(orderStatus);
        setOpenDate(openDate);
        setCompletionDate(completionDate);
        setQuantity(quantity);
        setPrice(price);
        setOrderFee(orderFee);
        setSymbol(symbol);
    }

    public OrderDataBean(String orderType, String orderStatus, Date openDate, Date completionDate, double quantity, BigDecimal price, BigDecimal orderFee,
            AccountDataBean account, QuoteDataBean quote, HoldingDataBean holding) {
        setOrderType(orderType);
        setOrderStatus(orderStatus);
        setOpenDate(openDate);
        setCompletionDate(completionDate);
        setQuantity(quantity);
        setPrice(price);
        setOrderFee(orderFee);
        setAccount(account);
        setQuote(quote);
        setHolding(holding);
    }

    public static OrderDataBean getRandomInstance() {
        return new OrderDataBean(new Integer(TradeConfig.rndInt(100000)), TradeConfig.rndBoolean() ? "buy" : "sell", "open", new java.util.Date(
                TradeConfig.rndInt(Integer.MAX_VALUE)), new java.util.Date(TradeConfig.rndInt(Integer.MAX_VALUE)), TradeConfig.rndQuantity(),
                TradeConfig.rndBigDecimal(1000.0f), TradeConfig.rndBigDecimal(1000.0f), TradeConfig.rndSymbol());
    }

    @Override
    public String toString() {
        return "Order " + getOrderID() + "\n\t      orderType: " + getOrderType() + "\n\t    orderStatus: " + getOrderStatus() + "\n\t       openDate: "
                + getOpenDate() + "\n\t completionDate: " + getCompletionDate() + "\n\t       quantity: " + getQuantity() + "\n\t          price: "
                + getPrice() + "\n\t       orderFee: " + getOrderFee() + "\n\t         symbol: " + getSymbol();
    }

    public String toHTML() {
        return "<BR>Order <B>" + getOrderID() + "</B>" + "<LI>      orderType: " + getOrderType() + "</LI>" + "<LI>    orderStatus: " + getOrderStatus()
                + "</LI>" + "<LI>       openDate: " + getOpenDate() + "</LI>" + "<LI> completionDate: " + getCompletionDate() + "</LI>"
                + "<LI>       quantity: " + getQuantity() + "</LI>" + "<LI>          price: " + getPrice() + "</LI>" + "<LI>       orderFee: " + getOrderFee()
                + "</LI>" + "<LI>         symbol: " + getSymbol() + "</LI>";
    }

    public void print() {
        Log.log(this.toString());
    }

    public Integer getOrderID() {
        return orderID;
    }

    public void setOrderID(Integer orderID) {
        this.orderID = orderID;
    }

    public String getOrderType() {
        return orderType;
    }

    public void setOrderType(String orderType) {
        this.orderType = orderType;
    }

    public String getOrderStatus() {
        return orderStatus;
    }

    public void setOrderStatus(String orderStatus) {
        this.orderStatus = orderStatus;
    }

    public Date getOpenDate() {
        return openDate;
    }

    public void setOpenDate(Date openDate) {
        this.openDate = openDate;
    }

    public Date getCompletionDate() {
        return completionDate;
    }

    public void setCompletionDate(Date completionDate) {
        this.completionDate = completionDate;
    }

    public double getQuantity() {
        return quantity;
    }

    public void setQuantity(double quantity) {
        this.quantity = quantity;
    }

    public BigDecimal getPrice() {
        return price;
    }

    public void setPrice(BigDecimal price) {
        this.price = price;
    }

    public BigDecimal getOrderFee() {
        return orderFee;
    }

    public void setOrderFee(BigDecimal orderFee) {
        this.orderFee = orderFee;
    }

    public String getSymbol() {
        if (quote != null) {
            return quote.getSymbol();
        }
        return symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public AccountDataBean getAccount() {
        return account;
    }

    public void setAccount(AccountDataBean account) {
        this.account = account;
    }

    public QuoteDataBean getQuote() {
        return quote;
    }

    public void setQuote(QuoteDataBean quote) {
        this.quote = quote;
    }

    public HoldingDataBean getHolding() {
        return holding;
    }

    public void setHolding(HoldingDataBean holding) {
        this.holding = holding;
    }

    public boolean isBuy() {
        String orderType = getOrderType();
        if (orderType.compareToIgnoreCase("buy") == 0) {
            return true;
        }
        return false;
    }

    public boolean isSell() {
        String orderType = getOrderType();
        if (orderType.compareToIgnoreCase("sell") == 0) {
            return true;
        }
        return false;
    }

    public boolean isOpen() {
        String orderStatus = getOrderStatus();
        if ((orderStatus.compareToIgnoreCase("open") == 0) || (orderStatus.compareToIgnoreCase("processing") == 0)) {
            return true;
        }
        return false;
    }

    public boolean isCompleted() {
        String orderStatus = getOrderStatus();
        if ((orderStatus.compareToIgnoreCase("completed") == 0) || (orderStatus.compareToIgnoreCase("alertcompleted") == 0)
                || (orderStatus.compareToIgnoreCase("cancelled") == 0)) {
            return true;
        }
        return false;
    }

    public boolean isCancelled() {
        String orderStatus = getOrderStatus();
        if (orderStatus.compareToIgnoreCase("cancelled") == 0) {
            return true;
        }
        return false;
    }

    public void cancel() {
        setOrderStatus("cancelled");
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (this.orderID != null ? this.orderID.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        
        if (!(object instanceof OrderDataBean)) {
            return false;
        }
        OrderDataBean other = (OrderDataBean) object;
        if (this.orderID != other.orderID && (this.orderID == null || !this.orderID.equals(other.orderID))) {
            return false;
        }
        return true;
    }
}


// Node: onOpen
// Node: createParser
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

import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

/** This class a simple websocket that sends the number of times it has been pinged. */

@ServerEndpoint(value = "/pingTextAsync")
public class PingWebSocketTextAsync {

    private Session currentSession = null;
    private Integer hitCount = null;
   
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
        hitCount = 0;
    }

    @OnMessage
    public void ping(String text) {

        hitCount++;
        currentSession.getAsyncRemote().sendText(hitCount.toString());
    }

    @OnError
    public void onError(Throwable t) {
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {
     
    }

}


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
//import java.util.Collections;
//import java.util.HashSet;
//import java.util.Set;

import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

/** This class a simple websocket that sends the number of times it has been pinged. */

@ServerEndpoint(value = "/pingTextSync")
public class PingWebSocketTextSync {

    private Session currentSession = null;
    private Integer hitCount = null;
   
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
        hitCount = 0;
    }

    @OnMessage
    public void ping(String text) {
        hitCount++;
    
        try {
            currentSession.getBasicRemote().sendText(hitCount.toString());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @OnError
    public void onError(Throwable t) {
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {
               
    }

}


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
import java.nio.ByteBuffer;

import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

/** This class a simple websocket that echos the binary it has been sent. */

@ServerEndpoint(value = "/pingBinary")
public class PingWebSocketBinary {

    private Session currentSession = null;
   
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
    }

    @OnMessage
    public void ping(ByteBuffer data) {       
        currentSession.getAsyncRemote().sendBinary(data);
    }

    @OnError
    public void onError(Throwable t) {
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {

        try {
            if (session.isOpen()) {
                session.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

}


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

// Node: Listener
// Node: IllegalArgumentException
/**
 * (C) Copyright IBM Corporation 2015, 2025.
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
package com.ibm.websphere.samples.daytrader.web.websocket;

import java.io.IOException;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

import javax.annotation.Resource;
import javax.enterprise.concurrent.ManagedScheduledExecutorService;
import javax.enterprise.event.Observes;
import javax.jms.Message;
import javax.json.Json;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;
import javax.json.JsonValue;
import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.WebSocketJMSMessage;


/** This class is a WebSocket EndPoint that sends the Market Summary in JSON form when requested 
 *  and sends stock price changes when received from an MDB through a CDI event
 * */

@ServerEndpoint(value = "/marketsummary",decoders=ActionDecoder.class)
public class MarketSummaryWebSocket {

    @Resource
    private ManagedScheduledExecutorService managedScheduledExecutorService;

	private static final List<Session> SESSIONS = new CopyOnWriteArrayList<>();
    private static final int SCHEDULER_PERIOD = Integer.parseInt(System.getProperty("dt.ws.period", "2"));
    private final CountDownLatch latch = new CountDownLatch(1);

    private static boolean sendRecentQuotePriceChangeList = false;
    private static ScheduledFuture<?> scheduler = null;


    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onOpen -- session -->" + session + "<--");
        }

        synchronized(SESSIONS) {
            if (SESSIONS.size() == 0) {
                 if (Log.doTrace()) {
                    Log.trace("MarketSummaryWebSocket:onOpen -- start scheduler");
                 }
                startScheduler();
            }

            SESSIONS.add(session);
        }
  
        latch.countDown();
    } 
    
    @OnMessage
    public void sendMarketSummary(ActionMessage message, Session currentSession) {

        String action = message.getDecodedAction();
        
        if (Log.doTrace()) {
            if (action != null ) {
                Log.trace("MarketSummaryWebSocket:sendMarketSummary -- received -->" + action + "<--");
            } else {
                Log.trace("MarketSummaryWebSocket:sendMarketSummary -- received -->null<--");
            }
        }

        // Make sure onopen is finished
        try {
            latch.await();
        } catch (InterruptedException e) {
            e.printStackTrace();
            return;
        }
        
        if (action != null && action.equals("update")) {
            TradeAction tAction = new TradeAction();
                            
            JsonObject mkSummary = null;
            try {
                mkSummary = tAction.getMarketSummary().toJSON();
            } catch (Exception e) {
                e.printStackTrace();
                return;
            }

            if (Log.doTrace()) {
                Log.trace("MarketSummaryWebSocket:sendMarketSummary -- sending -->" + mkSummary + "<--");
            }
                            
            if (RecentStockChangeList.isEmpty()) {
                synchronized (currentSession) {
                    if (currentSession.isOpen()) {
                        try {
                            currentSession.getBasicRemote().sendText(mkSummary.toString());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }
                }   
            }
            else { // Merge Objects 
                JsonObject recentChangeList = RecentStockChangeList.stockChangesInJSON();
                if (currentSession.isOpen()) {
                    try {
                        currentSession.getBasicRemote().sendText(mergeJsonObjects(mkSummary,recentChangeList).toString());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                } 
            }
        }
    }

    @OnError
    public void onError(Throwable t, Session currentSession) {
        if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onError -- session -->" + currentSession + "<--");
        }
        t.printStackTrace();
    }

    @OnClose
    public void onClose(Session session, CloseReason reason) {

        if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onClose -- session -->" + session + "<--");
        }

        synchronized(SESSIONS) {
            SESSIONS.remove(session);
            if (SESSIONS.size() == 0) {  
                if (Log.doTrace()) {
                    Log.trace("MarketSummaryWebSocket:onClose -- cancel scheduler");
                }
                scheduler.cancel(false);
            }
        }

    }
    
    public static void onJMSMessage(@Observes @WebSocketJMSMessage Message message) {
    	
    	if (Log.doTrace()) {
            Log.trace("MarketSummaryWebSocket:onJMSMessage");
        }
        RecentStockChangeList.addStockChange(message);
        sendRecentQuotePriceChangeList = true;
    }    

    private void sendRecentQuotePriceChangeList() {
        JsonObject stockChangeJson = RecentStockChangeList.stockChangesInJSON();
  
        for (Session session : SESSIONS) {
            synchronized (session) {
                if (session.isOpen()) {
                    try {
                        session.getBasicRemote().sendText(stockChangeJson.toString());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }      
                }
            }
        }
    }
    

    private void startScheduler() {
		scheduler = managedScheduledExecutorService.scheduleAtFixedRate(() -> {
        Log.trace("MarketSummaryWebSocket: Executing static scheduled task at: " + System.currentTimeMillis());
        if (sendRecentQuotePriceChangeList) {
          Log.trace("MarketSummaryWebSocket: sendList = true");
          sendRecentQuotePriceChangeList();
          sendRecentQuotePriceChangeList = false;
        } else {
          Log.trace("MarketSummaryWebSocket: sendList = false");
        }
      }, 1, SCHEDULER_PERIOD, TimeUnit.SECONDS);
	}
    
    private JsonObject mergeJsonObjects(JsonObject obj1, JsonObject obj2) {
        
        JsonObjectBuilder jObjectBuilder = Json.createObjectBuilder();
        
        Set<String> keys1 = obj1.keySet();
        Iterator<String> iter1 = keys1.iterator();
        
        while(iter1.hasNext()) {
            String key = (String)iter1.next();
            JsonValue value = obj1.get(key);
            
            jObjectBuilder.add(key, value);
            
        }
        
        Set<String> keys2 = obj2.keySet();
        Iterator<String> iter2 = keys2.iterator();
        
        while(iter2.hasNext()) {
            String key = (String)iter2.next();
            JsonValue value = obj2.get(key);
            
            jObjectBuilder.add(key, value);
            
        }
        
        return jObjectBuilder.build();
    }
}



// Node: startScheduler
// Node: countDown
// Node: onJMSMessage
// Node: addStockChange
// Node: sendRecentQuotePriceChangeList
// Node: scheduleAtFixedRate
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
package com.ibm.websphere.samples.daytrader.web.websocket;

import java.io.StringReader;

import javax.json.Json;
import javax.json.stream.JsonParser;

import com.ibm.websphere.samples.daytrader.util.Log;

/**
 *  Licensed to the Apache Software Foundation (ASF) under one or more
 *  contributor license agreements.  See the NOTICE file distributed with
 *  this work for additional information regarding copyright ownership.
 *  The ASF licenses this file to You under the Apache License, Version 2.0
 *  (the "License"); you may not use this file except in compliance with
 *  the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */
public class ActionMessage {
    
    String decodedAction = null;
    
    public ActionMessage() {  
    }
    
    public void doDecoding(String jsonText) {
              
        String keyName = null;
        try 
        {
            // JSON parse
            JsonParser parser = Json.createParser(new StringReader(jsonText));
            while (parser.hasNext()) {
                JsonParser.Event event = parser.next();
                switch(event) {
                case KEY_NAME:
                    keyName=parser.getString();
                    break;
                case VALUE_STRING:
                    if (keyName != null && keyName.equals("action")) {
                        decodedAction=parser.getString();
                    }
                    break;
                default:
                    break;
                }
            }
        } catch (Exception e) {
            Log.error("ActionMessage:doDecoding(" + jsonText + ") --> failed", e);
        }
        
        if (Log.doTrace()) {
            if (decodedAction != null ) {
                Log.trace("ActionMessage:doDecoding -- decoded action -->" + decodedAction + "<--");
            } else {
                Log.trace("ActionMessage:doDecoding -- decoded action -->null<--");
            }
        }
        
    }
    
    public String getDecodedAction() {
        return decodedAction;
    }
    
}



// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/websocket/ActionMessage.java:ActionMessage.<init>
// Node: Foundation
// Node: ActionMessage
// Node: doDecoding
// Node: decode
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
package com.ibm.websphere.samples.daytrader.web.websocket;

import javax.websocket.DecodeException;
import javax.websocket.Decoder;
import javax.websocket.EndpointConfig;

import com.ibm.websphere.samples.daytrader.util.Log;

// This is coded to be a Text type decoder expecting JSON format. 
// It will decode incoming messages into object of type String
public class ActionDecoder implements Decoder.Text<ActionMessage> {

    public ActionDecoder() {
    }
    
    @Override
    public void destroy() {
    }

    @Override
    public void init(EndpointConfig config) {
    }

    @Override
    public ActionMessage decode(String jsonText) throws DecodeException {
       
        if (Log.doTrace()) {
            Log.trace("ActionDecoder:decode -- received -->" + jsonText + "<--");
        }

        ActionMessage actionMessage = new ActionMessage();
        actionMessage.doDecoding(jsonText);
        return actionMessage;

    }

    @Override
    public boolean willDecode(String s) {
        return true;
    }

}


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

import java.math.BigDecimal;
import java.util.Date;

public class OrderData {
    private Integer orderID;
    private String orderStatus;
    private Date openDate;
    private Date completionDate;
    private BigDecimal orderFee;
    private String orderType;
    private double quantity;
    private String symbol;
    private BigDecimal total;
    private BigDecimal price;

    public OrderData(Integer orderID, String orderStatus, Date openDate, Date completeDate, BigDecimal orderFee, String orderType, double quantity,
            String symbol) {
        this.orderID = orderID;
        this.completionDate = completeDate;
        this.openDate = openDate;
        this.orderFee = orderFee;
        this.orderType = orderType;
        this.orderStatus = orderStatus;
        this.quantity = quantity;
        this.symbol = symbol;
    }
    
    public OrderData(Integer orderID, String orderStatus, Date openDate, Date completeDate, BigDecimal orderFee, String orderType, double quantity,
            String symbol, BigDecimal price) {
        this.orderID = orderID;
        this.completionDate = completeDate;
        this.openDate = openDate;
        this.orderFee = orderFee;
        this.orderType = orderType;
        this.orderStatus = orderStatus;
        this.quantity = quantity;
        this.symbol = symbol;
        this.price = price;
        this.total = price.multiply(new BigDecimal(quantity));

    }

    public void setOrderID(Integer orderID) {
        this.orderID = orderID;
    }

    public Integer getOrderID() {
        return orderID;
    }

    public void setOrderStatus(String orderStatus) {
        this.orderStatus = orderStatus;
    }

    public String getOrderStatus() {
        return orderStatus;
    }

    public void setOpenDate(Date openDate) {
        this.openDate = openDate;
    }

    public Date getOpenDate() {
        return openDate;
    }

    public void setCompletionDate(Date completionDate) {
        this.completionDate = completionDate;
    }

    public Date getCompletionDate() {
        return completionDate;
    }

    public void setOrderFee(BigDecimal orderFee) {
        this.orderFee = orderFee;
    }

    public BigDecimal getOrderFee() {
        return orderFee;
    }

    public void setOrderType(String orderType) {
        this.orderType = orderType;
    }

    public String getOrderType() {
        return orderType;
    }

    public void setQuantity(double quantity) {
        this.quantity = quantity;
    }

    public double getQuantity() {
        return quantity;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public String getSymbol() {
        return symbol;
    }

    public void setTotal(BigDecimal total) {
        this.total = total;
    }

    public BigDecimal getTotal() {
        return total;
    }

    public void setPrice(BigDecimal price) {
        this.price = price;
    }

    public BigDecimal getPrice() {
        return price;
    }

}


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

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Iterator;

import javax.annotation.PostConstruct;
import javax.enterprise.context.RequestScoped;
import javax.faces.component.html.HtmlDataTable;
import javax.faces.context.ExternalContext;
import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.FinancialUtils;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Named("portfolio")
@RequestScoped
public class PortfolioJSF {
    @Inject
    private ExternalContext facesExternalContext;

    @Inject
    private TradeAction tradeAction;

    private BigDecimal balance;
    private BigDecimal openBalance;
    private Integer numberHoldings;
    private BigDecimal holdingsTotal;
    private BigDecimal sumOfCashHoldings;
    private BigDecimal totalGain = new BigDecimal(0.0);
    private BigDecimal totalValue = new BigDecimal(0.0);
    private BigDecimal totalBasis = new BigDecimal(0.0);
    private BigDecimal totalGainPercent = new BigDecimal(0.0);
    private ArrayList<HoldingData> holdingDatas;
    private HtmlDataTable dataTable;

    @PostConstruct
    public void getPortfolio() {
        try {

            HttpSession session = (HttpSession) facesExternalContext.getSession(true);
            String userID = (String) session.getAttribute("uidBean");
            Collection<?> holdingDataBeans = tradeAction.getHoldings(userID);

            numberHoldings = holdingDataBeans.size();

            // Walk through the collection of user holdings and creating a list
            // of quotes
            if (holdingDataBeans.size() > 0) {
                Iterator<?> it = holdingDataBeans.iterator();
                holdingDatas = new ArrayList<HoldingData>(holdingDataBeans.size());

                while (it.hasNext()) {
                    HoldingDataBean holdingData = (HoldingDataBean) it.next();
                    QuoteDataBean quoteData = tradeAction.getQuote(holdingData.getQuoteID());

                    BigDecimal basis = holdingData.getPurchasePrice().multiply(new BigDecimal(holdingData.getQuantity()));
                    BigDecimal marketValue = quoteData.getPrice().multiply(new BigDecimal(holdingData.getQuantity()));
                    totalBasis = totalBasis.add(basis);
                    totalValue = totalValue.add(marketValue);
                    BigDecimal gain = marketValue.subtract(basis);
                    totalGain = totalGain.add(gain);

                    HoldingData h = new HoldingData();
                    h.setHoldingID(holdingData.getHoldingID());
                    h.setPurchaseDate(holdingData.getPurchaseDate());
                    h.setQuoteID(holdingData.getQuoteID());
                    h.setQuantity(holdingData.getQuantity());
                    h.setPurchasePrice(holdingData.getPurchasePrice());
                    h.setBasis(basis);
                    h.setGain(gain);
                    h.setMarketValue(marketValue);
                    h.setPrice(quoteData.getPrice());
                    holdingDatas.add(h);

                }
                // dataTable
                setTotalGainPercent(FinancialUtils.computeGainPercent(totalValue, totalBasis));

            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public String sell() {

        HttpSession session = (HttpSession) facesExternalContext.getSession(true);
        String userID = (String) session.getAttribute("uidBean");
        TradeAction tAction = new TradeAction();
        OrderDataBean orderDataBean = null;
        HoldingData holdingData = (HoldingData) dataTable.getRowData();

        try {
            orderDataBean = tAction.sell(userID, holdingData.getHoldingID(), TradeConfig.orderProcessingMode);
            holdingDatas.remove(holdingData);
        } catch (Exception e) {
            e.printStackTrace();
        }

        OrderData orderData = new OrderData(orderDataBean.getOrderID(), orderDataBean.getOrderStatus(), orderDataBean.getOpenDate(),
                orderDataBean.getCompletionDate(), orderDataBean.getOrderFee(), orderDataBean.getOrderType(), orderDataBean.getQuantity(),
                orderDataBean.getSymbol());
        session.setAttribute("orderData", orderData);
        return "sell";
    }

    public void setDataTable(HtmlDataTable dataTable) {
        this.dataTable = dataTable;
    }

    public HtmlDataTable getDataTable() {
        return dataTable;
    }

    public void setBalance(BigDecimal balance) {
        this.balance = balance;
    }

    public BigDecimal getBalance() {
        return balance;
    }

    public void setOpenBalance(BigDecimal openBalance) {
        this.openBalance = openBalance;
    }

    public BigDecimal getOpenBalance() {
        return openBalance;
    }

    public void setHoldingsTotal(BigDecimal holdingsTotal) {
        this.holdingsTotal = holdingsTotal;
    }

    public BigDecimal getHoldingsTotal() {
        return holdingsTotal;
    }

    public void setSumOfCashHoldings(BigDecimal sumOfCashHoldings) {
        this.sumOfCashHoldings = sumOfCashHoldings;
    }

    public BigDecimal getSumOfCashHoldings() {
        return sumOfCashHoldings;
    }

    public void setNumberHoldings(Integer numberHoldings) {
        this.numberHoldings = numberHoldings;
    }

    public Integer getNumberHoldings() {
        return numberHoldings;
    }

    public void setTotalGain(BigDecimal totalGain) {
        this.totalGain = totalGain;
    }

    public BigDecimal getTotalGain() {
        return totalGain;
    }

    public void setTotalValue(BigDecimal totalValue) {
        this.totalValue = totalValue;
    }

    public BigDecimal getTotalValue() {
        return totalValue;
    }

    public void setTotalBasis(BigDecimal totalBasis) {
        this.totalBasis = totalBasis;
    }

    public BigDecimal getTotalBasis() {
        return totalBasis;
    }

    public void setHoldingDatas(ArrayList<HoldingData> holdingDatas) {
        this.holdingDatas = holdingDatas;
    }

    public ArrayList<HoldingData> getHoldingDatas() {
        return holdingDatas;
    }

    public void setTotalGainPercent(BigDecimal totalGainPercent) {
        this.totalGainPercent = totalGainPercent;
    }

    public BigDecimal getTotalGainPercent() {
        return totalGainPercent;
    }

    public String getTotalGainPercentHTML() {
        return FinancialUtils.printGainPercentHTML(totalGainPercent);
    }
}


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

import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.faces.application.FacesMessage;
import javax.faces.component.UIComponent;
import javax.faces.context.FacesContext;
import javax.faces.validator.FacesValidator;
import javax.faces.validator.Validator;
import javax.faces.validator.ValidatorException;

import com.ibm.websphere.samples.daytrader.util.Log;

@FacesValidator("loginValidator")
public class LoginValidator implements Validator{

  static String loginRegex = "uid:\\d+";
  static Pattern pattern = Pattern.compile(loginRegex);
  static Matcher matcher;

  // Simple JSF validator to make sure username starts with uid: and at least 1 number.
  public LoginValidator() {
  }

  @Override
  public void validate(FacesContext context, UIComponent component, Object value) throws ValidatorException {
	  if (Log.doTrace()) {
		  Log.trace("LoginValidator.validate","Validating submitted login name -- " + value.toString());
	  }
	  matcher = pattern.matcher(value.toString());
    
	  if (!matcher.matches()) {
		  FacesMessage msg = new FacesMessage("Username validation failed. Please provide username in this format: uid:#");
		  msg.setSeverity(FacesMessage.SEVERITY_ERROR);
      
		  throw new ValidatorException(msg);
	  }
  	}
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/jsf/LoginValidator.java:LoginValidator.<init>
// Node: FacesValidator
// Node: compile
// Node: LoginValidator
// Node: validate
// Node: matcher
// Node: matches
// Node: FacesMessage
// Node: setSeverity
// Node: ValidatorException
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

import java.io.Serializable;
import java.math.BigDecimal;

import javax.enterprise.context.SessionScoped;
import javax.faces.context.ExternalContext;
import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.entities.AccountDataBean;
import com.ibm.websphere.samples.daytrader.entities.AccountProfileDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;

@Named("tradeapp")
@SessionScoped
public class TradeAppJSF implements Serializable {
	
    @Inject
    private ExternalContext facesExternalContext;

    @Inject
    private TradeAction tradeAction;

    private static final long serialVersionUID = 2L;
    private String userID = "uid:0";
    private String password = "xxx";
    private String cpassword;
    private String results;
    private String fullname;
    private String address;
    private String email;
    private String ccn;
    private String money;

    public String login() {
        try {        	
            AccountDataBean accountData = tradeAction.login(userID, password);

            AccountProfileDataBean accountProfileData = tradeAction.getAccountProfileData(userID);
            if (accountData != null) {
                HttpSession session = (HttpSession) facesExternalContext.getSession(true);

                session.setAttribute("uidBean", userID);
                session.setAttribute("sessionCreationDate", new java.util.Date());
                setResults("Ready to Trade");

                // Get account profile information
                setAddress(accountProfileData.getAddress());
                setCcn(accountProfileData.getCreditCard());
                setEmail(accountProfileData.getEmail());
                setFullname(accountProfileData.getFullName());
                setCpassword(accountProfileData.getPassword());
                return "Ready to Trade";
            } else {
                Log.log("TradeServletAction.doLogin(...)", "Error finding account for user " + userID + "",
                        "user entered a bad username or the database is not populated");
                throw new NullPointerException("User does not exist or password is incorrect!");
            }
        }

        catch (Exception se) {
            // Go to welcome page
            setResults("Could not find account");
            return "welcome";
        }
    }

    public String register() {
        TradeAction tAction = new TradeAction();
        // Validate user passwords match and are atleast 1 char in length
        try {
            if ((password.equals(cpassword)) && (password.length() >= 1)) {
                AccountDataBean accountData = tAction.register(userID, password, fullname, address, email, ccn, new BigDecimal(money));

                if (accountData == null) {
                    setResults("Registration operation failed;");
                    // Go to register page
                    return "Registration operation failed";

                } else {
                    login();
                    setResults("Registration operation succeeded;  Account " + accountData.getAccountID() + " has been created.");
                    return "Registration operation succeeded";
                }
            }

            else {
                // Password validation failed
                setResults("Registration operation failed, your passwords did not match");
                // Go to register page
                return "Registration operation failed";
            }
        }

        catch (Exception e) {
            // log the exception with error page
            Log.log("TradeServletAction.doRegister(...)" + " exception user =" + userID);
            try {
                throw new Exception("TradeServletAction.doRegister(...)" + " exception user =" + userID, e);
            } catch (Exception e1) {
                e1.printStackTrace();
            }

        }
        return "Registration operation succeeded";
    }

    public String updateProfile() {
        TradeAction tAction = new TradeAction();
        // First verify input data
        boolean doUpdate = true;

        if (password.equals(cpassword) == false) {
            results = "Update profile error: passwords do not match";
            doUpdate = false;
        }

        AccountProfileDataBean accountProfileData = new AccountProfileDataBean(userID, password, fullname, address, email, ccn);

        try {
            if (doUpdate) {
                accountProfileData = tAction.updateAccountProfile(accountProfileData);
                results = "Account profile update successful";
            }

        } catch (java.lang.IllegalArgumentException e) {
            // this is a user error so I will
            // forward them to another page rather than throw a 500
            setResults("invalid argument, check userID is correct, and the database is populated" + userID);
            Log.error(e, "TradeServletAction.doAccount(...)", "illegal argument, information should be in exception string",
                    "treating this as a user error and forwarding on to a new page");
        } catch (Exception e) {
            // log the exception with error page
            e.printStackTrace();
        }
        // Go to account.xhtml
        return "Go to account";
    }

    public String logout() {
        TradeAction tAction = new TradeAction();
        try {
        	setResults("");
            tAction.logout(userID);
        } catch (java.lang.IllegalArgumentException e) {
            // this is a user error so I will
            // forward them to another page, at the end of the page.
            setResults("illegal argument:" + e.getMessage());

            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error(e, "TradeServletAction.doLogout(...)", "illegal argument, information should be in exception string",
                    "treating this as a user error and forwarding on to a new page");
        } catch (Exception e) {
            // log the exception and foward to a error page
            Log.error(e, "TradeAppJSF.logout():", "Error logging out" + userID, "fowarding to an error page");
        }

        HttpSession session = (HttpSession) facesExternalContext.getSession(false);

        if (session != null) {
            session.invalidate();
        }
        
        // Added to actually remove a user from the authentication cache
        try {
            ((HttpServletRequest) facesExternalContext.getRequest()).logout();
        } catch (ServletException e) {
            Log.error(e, "TradeAppJSF.logout():", "Error logging out request" + userID, "fowarding to an error page");
        }
        
        // Go to welcome page
        return "welcome";
    }

    public String getUserID() {
        return userID;
    }

    public void setUserID(String userID) {
        this.userID = userID;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getCpassword() {
        return cpassword;
    }

    public void setCpassword(String cpassword) {
        this.cpassword = cpassword;
    }

    public String getFullname() {
        return fullname;
    }

    public void setFullname(String fullname) {
        this.fullname = fullname;
    }

    public String getResults() {
    	String tempResults=results;
    	results="";
        return tempResults;
    }

    public void setResults(String results) {
        this.results = results;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getCcn() {
        return ccn;
    }

    public void setCcn(String ccn) {
        this.ccn = ccn;
    }

    public String getMoney() {
        return money;
    }

    public void setMoney(String money) {
        this.money = money;
    }
};


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

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Iterator;

import javax.annotation.PostConstruct;
import javax.enterprise.context.RequestScoped;
import javax.faces.context.ExternalContext;
import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.entities.AccountDataBean;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.util.FinancialUtils;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Named("accountdata")
@RequestScoped
public class AccountDataJSF {
    @Inject
    private ExternalContext facesExternalContext;

    @Inject
    private TradeAction tradeAction;

    private Date sessionCreationDate;
    private Date currentTime;
    private String profileID;
    private Integer accountID;
    private Date creationDate;
    private int loginCount;
    private Date lastLogin;
    private int logoutCount;
    private BigDecimal balance;
    private BigDecimal openBalance;
    private Integer numberHoldings;
    private BigDecimal holdingsTotal;
    private BigDecimal sumOfCashHoldings;
    private BigDecimal gain;
    private BigDecimal gainPercent;

    private OrderData[] closedOrders;
    private OrderData[] allOrders;  
    
    private Integer numberOfOrders = 0;
	private Integer numberOfOrderRows = 5;
	    
	public void toggleShowAllRows() {
		setNumberOfOrderRows(0);
	}
	
    @PostConstruct
    public void home() {

        try {
            HttpSession session = (HttpSession) facesExternalContext.getSession(true);

            // Get the data and then parse
            String userID = (String) session.getAttribute("uidBean");
            AccountDataBean accountData = tradeAction.getAccountData(userID);
            Collection<?> holdingDataBeans = tradeAction.getHoldings(userID); 
                      
            if (TradeConfig.getDisplayOrderAlerts()) {

                Collection<?> closedOrders = tradeAction.getClosedOrders(userID);

                if (closedOrders != null && closedOrders.size() > 0) {
                    session.setAttribute("closedOrders", closedOrders);
                    OrderData[] orderjsfs = new OrderData[closedOrders.size()];
                    Iterator<?> it = closedOrders.iterator();
                    int i = 0;

                    while (it.hasNext()) {
                        OrderDataBean order = (OrderDataBean) it.next();
                        OrderData r = new OrderData(order.getOrderID(), order.getOrderStatus(), order.getOpenDate(), order.getCompletionDate(),
                                order.getOrderFee(), order.getOrderType(), order.getQuantity(), order.getSymbol());
                        orderjsfs[i] = r;
                        i++;
                    }

                    setClosedOrders(orderjsfs);
                }
            }

            Collection<?> orderDataBeans = (TradeConfig.getLongRun() ? new ArrayList<Object>() : (Collection<?>) tradeAction.getOrders(userID));

            if (orderDataBeans != null && orderDataBeans.size() > 0) {
                session.setAttribute("orderDataBeans", orderDataBeans);
                OrderData[] orderjsfs = new OrderData[orderDataBeans.size()];
                Iterator<?> it = orderDataBeans.iterator();
                int i = 0;

                while (it.hasNext()) {
                    OrderDataBean order = (OrderDataBean) it.next();
                    OrderData r = new OrderData(order.getOrderID(), order.getOrderStatus(), order.getOpenDate(), order.getCompletionDate(),
                            order.getOrderFee(), order.getOrderType(), order.getQuantity(), order.getSymbol(),order.getPrice());
                    orderjsfs[i] = r;
                    i++;
                }
                setNumberOfOrders(orderDataBeans.size());
                setAllOrders(orderjsfs);
            }

            setSessionCreationDate((Date) session.getAttribute("sessionCreationDate"));
            setCurrentTime(new java.util.Date());
            doAccountData(accountData, holdingDataBeans);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void doAccountData(AccountDataBean accountData, Collection<?> holdingDataBeans) {
        setProfileID(accountData.getProfileID());
        setAccountID(accountData.getAccountID());
        setCreationDate(accountData.getCreationDate());
        setLoginCount(accountData.getLoginCount());
        setLogoutCount(accountData.getLogoutCount());
        setLastLogin(accountData.getLastLogin());
        setOpenBalance(accountData.getOpenBalance());
        setBalance(accountData.getBalance());
        setNumberHoldings(holdingDataBeans.size());
        setHoldingsTotal(FinancialUtils.computeHoldingsTotal(holdingDataBeans));
        setSumOfCashHoldings(balance.add(holdingsTotal));
        setGain(FinancialUtils.computeGain(sumOfCashHoldings, openBalance));
        setGainPercent(FinancialUtils.computeGainPercent(sumOfCashHoldings, openBalance));
    }

    public Date getSessionCreationDate() {
        return sessionCreationDate;
    }

    public void setSessionCreationDate(Date sessionCreationDate) {
        this.sessionCreationDate = sessionCreationDate;
    }

    public Date getCurrentTime() {
        return currentTime;
    }

    public void setCurrentTime(Date currentTime) {
        this.currentTime = currentTime;
    }

    public String getProfileID() {
        return profileID;
    }

    public void setProfileID(String profileID) {
        this.profileID = profileID;
    }

    public void setAccountID(Integer accountID) {
        this.accountID = accountID;
    }

    public Integer getAccountID() {
        return accountID;
    }

    public void setCreationDate(Date creationDate) {
        this.creationDate = creationDate;
    }

    public Date getCreationDate() {
        return creationDate;
    }

    public void setLoginCount(int loginCount) {
        this.loginCount = loginCount;
    }

    public int getLoginCount() {
        return loginCount;
    }

    public void setBalance(BigDecimal balance) {
        this.balance = balance;
    }

    public BigDecimal getBalance() {
        return balance;
    }

    public void setOpenBalance(BigDecimal openBalance) {
        this.openBalance = openBalance;
    }

    public BigDecimal getOpenBalance() {
        return openBalance;
    }

    public void setHoldingsTotal(BigDecimal holdingsTotal) {
        this.holdingsTotal = holdingsTotal;
    }

    public BigDecimal getHoldingsTotal() {
        return holdingsTotal;
    }

    public void setSumOfCashHoldings(BigDecimal sumOfCashHoldings) {
        this.sumOfCashHoldings = sumOfCashHoldings;
    }

    public BigDecimal getSumOfCashHoldings() {
        return sumOfCashHoldings;
    }

    public void setGain(BigDecimal gain) {
        this.gain = gain;
    }

    public BigDecimal getGain() {
        return gain;
    }

    public void setGainPercent(BigDecimal gainPercent) {
        this.gainPercent = gainPercent.setScale(2);
    }

    public BigDecimal getGainPercent() {
        return gainPercent;
    }

    public void setNumberHoldings(Integer numberHoldings) {
        this.numberHoldings = numberHoldings;
    }

    public Integer getNumberHoldings() {
        return numberHoldings;
    }

    public OrderData[] getClosedOrders() {
        return closedOrders;
    }

    public void setClosedOrders(OrderData[] closedOrders) {
        this.closedOrders = closedOrders;
    }

    public void setLastLogin(Date lastLogin) {
        this.lastLogin = lastLogin;
    }

    public Date getLastLogin() {
        return lastLogin;
    }

    public void setLogoutCount(int logoutCount) {
        this.logoutCount = logoutCount;
    }

    public int getLogoutCount() {
        return logoutCount;
    }

    public void setAllOrders(OrderData[] allOrders) {
        this.allOrders = allOrders;
    }

    public OrderData[] getAllOrders() {
        return allOrders;
    }

    public String getGainHTML() {
        return FinancialUtils.printGainHTML(gain);
    }

    public String getGainPercentHTML() {
        return FinancialUtils.printGainPercentHTML(gainPercent);
    }

	public Integer getNumberOfOrderRows() {
		return numberOfOrderRows;
	}

	public void setNumberOfOrderRows(Integer numberOfOrderRows) {
		this.numberOfOrderRows = numberOfOrderRows;
	}

    public Integer getNumberOfOrders() {
        return numberOfOrders;
    }

    public void setNumberOfOrders(Integer numberOfOrders) {
        this.numberOfOrders = numberOfOrders;
    }
}


