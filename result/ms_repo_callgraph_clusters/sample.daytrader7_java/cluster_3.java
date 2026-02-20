// Cluster 3

// Node: equals
// Node: TradeAction
// Node: doActionTrace
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


// Node: getMarketSummary
// Node: getMarketSummaryInternal
// Node: openTSIA
// Node: buy
// Node: Double
// Node: updateQuotePriceVolume
// Node: Sell
// Node: sell
// Node: getOrderStatus
// Node: getSymbol
// Node: getQuantity
// Node: cancelOrder
// Node: orderCompleted
// Node: getOrders
// Node: getClosedOrders
// Node: createQuote
// Node: getAllQuotes
// Node: getQuote
// Node: length
// Node: getHoldings
// Node: getHolding
// Node: getAccountData
// Node: getAccountProfileData
// Node: updateAccountProfile
// Node: login
// Node: logout
// Node: register
// Node: BigDecimal
// Node: servlet
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

import java.math.BigDecimal;
import java.util.Collection;

import com.ibm.websphere.samples.daytrader.beans.MarketSummaryDataBean;
import com.ibm.websphere.samples.daytrader.beans.RunStatsDataBean;
import com.ibm.websphere.samples.daytrader.entities.AccountDataBean;
import com.ibm.websphere.samples.daytrader.entities.AccountProfileDataBean;
import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;

/**
 * TradeServices interface specifies the business methods provided by the Trade
 * online broker application. These business methods represent the features and
 * operations that can be performed by customers of the brokerage such as login,
 * logout, get a stock quote, buy or sell a stock, etc. This interface is
 * implemented by {@link Trade} providing an EJB implementation of these
 * business methods and also by {@link TradeDirect} providing a JDBC
 * implementation.
 *
 * @see Trade
 * @see TradeDirect
 *
 */

public interface TradeServices {

    /**
     * Compute and return a snapshot of the current market conditions This
     * includes the TSIA - an index of the price of the top 100 Trade stock
     * quotes The openTSIA ( the index at the open) The volume of shares traded,
     * Top Stocks gain and loss
     *
     * @return A snapshot of the current market summary
     */
    MarketSummaryDataBean getMarketSummary() throws Exception;

    /**
     * Purchase a stock and create a new holding for the given user. Given a
     * stock symbol and quantity to purchase, retrieve the current quote price,
     * debit the user's account balance, and add holdings to user's portfolio.
     * buy/sell are asynchronous, using J2EE messaging, A new order is created
     * and submitted for processing to the TradeBroker
     *
     * @param userID
     *            the customer requesting the stock purchase
     * @param symbol
     *            the symbol of the stock being purchased
     * @param quantity
     *            the quantity of shares to purchase
     * @return OrderDataBean providing the status of the newly created buy order
     */

    OrderDataBean buy(String userID, String symbol, double quantity, int orderProcessingMode) throws Exception;

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
    OrderDataBean sell(String userID, Integer holdingID, int orderProcessingMode) throws Exception;

    /**
     * Queue the Order identified by orderID to be processed
     *
     * Orders are submitted through JMS to a Trading Broker and completed
     * asynchronously. This method queues the order for processing
     *
     * The boolean twoPhase specifies to the server implementation whether or
     * not the method is to participate in a global transaction
     *
     * @param orderID
     *            the Order being queued for processing
     * @return OrderDataBean providing the status of the completed order
     */
    void queueOrder(Integer orderID, boolean twoPhase) throws Exception;

    /**
     * Complete the Order identefied by orderID Orders are submitted through JMS
     * to a Trading agent and completed asynchronously. This method completes
     * the order For a buy, the stock is purchased creating a holding and the
     * users account is debited For a sell, the stock holding is removed and the
     * users account is credited with the proceeds
     *
     * The boolean twoPhase specifies to the server implementation whether or
     * not the method is to participate in a global transaction
     *
     * @param orderID
     *            the Order to complete
     * @return OrderDataBean providing the status of the completed order
     */
    OrderDataBean completeOrder(Integer orderID, boolean twoPhase) throws Exception;

    /**
     * Cancel the Order identefied by orderID
     *
     * The boolean twoPhase specifies to the server implementation whether or
     * not the method is to participate in a global transaction
     *
     * @param orderID
     *            the Order to complete
     * @return OrderDataBean providing the status of the completed order
     */
    void cancelOrder(Integer orderID, boolean twoPhase) throws Exception;

    /**
     * Signify an order has been completed for the given userID
     *
     * @param userID
     *            the user for which an order has completed
     * @param orderID
     *            the order which has completed
     *
     */
    void orderCompleted(String userID, Integer orderID) throws Exception;

    /**
     * Get the collection of all orders for a given account
     *
     * @param userID
     *            the customer account to retrieve orders for
     * @return Collection OrderDataBeans providing detailed order information
     */
    Collection<?> getOrders(String userID) throws Exception;

    /**
     * Get the collection of completed orders for a given account that need to
     * be alerted to the user
     *
     * @param userID
     *            the customer account to retrieve orders for
     * @return Collection OrderDataBeans providing detailed order information
     */
    Collection<?> getClosedOrders(String userID) throws Exception;

    /**
     * Given a market symbol, price, and details, create and return a new
     * {@link QuoteDataBean}
     *
     * @param symbol
     *            the symbol of the stock
     * @param price
     *            the current stock price
     * @param details
     *            a short description of the stock or company
     * @return a new QuoteDataBean or null if Quote could not be created
     */
    QuoteDataBean createQuote(String symbol, String companyName, BigDecimal price) throws Exception;

    /**
     * Return a {@link QuoteDataBean} describing a current quote for the given
     * stock symbol
     *
     * @param symbol
     *            the stock symbol to retrieve the current Quote
     * @return the QuoteDataBean
     */
    QuoteDataBean getQuote(String symbol) throws Exception;

    /**
     * Return a {@link java.util.Collection} of {@link QuoteDataBean} describing
     * all current quotes
     *
     * @return A collection of QuoteDataBean
     */
    Collection<?> getAllQuotes() throws Exception;

    /**
     * Update the stock quote price and volume for the specified stock symbol
     *
     * @param symbol
     *            for stock quote to update
     * @param price
     *            the updated quote price
     * @return the QuoteDataBean describing the stock
     */
    QuoteDataBean updateQuotePriceVolume(String symbol, BigDecimal newPrice, double sharesTraded) throws Exception;

    /**
     * Return the portfolio of stock holdings for the specified customer as a
     * collection of HoldingDataBeans
     *
     * @param userID
     *            the customer requesting the portfolio
     * @return Collection of the users portfolio of stock holdings
     */
    Collection<?> getHoldings(String userID) throws Exception;

    /**
     * Return a specific user stock holding identifed by the holdingID
     *
     * @param holdingID
     *            the holdingID to return
     * @return a HoldingDataBean describing the holding
     */
    HoldingDataBean getHolding(Integer holdingID) throws Exception;

    /**
     * Return an AccountDataBean object for userID describing the account
     *
     * @param userID
     *            the account userID to lookup
     * @return User account data in AccountDataBean
     */
    AccountDataBean getAccountData(String userID) throws Exception;

    /**
     * Return an AccountProfileDataBean for userID providing the users profile
     *
     * @param userID
     *            the account userID to lookup
     * @param User
     *            account profile data in AccountProfileDataBean
     */
    AccountProfileDataBean getAccountProfileData(String userID) throws Exception;

    /**
     * Update userID's account profile information using the provided
     * AccountProfileDataBean object
     *
     * @param userID
     *            the account userID to lookup
     * @param User
     *            account profile data in AccountProfileDataBean
     */
    AccountProfileDataBean updateAccountProfile(AccountProfileDataBean profileData) throws Exception;

    /**
     * Attempt to authenticate and login a user with the given password
     *
     * @param userID
     *            the customer to login
     * @param password
     *            the password entered by the customer for authentication
     * @return User account data in AccountDataBean
     */
    AccountDataBean login(String userID, String password) throws Exception;

    /**
     * Logout the given user
     *
     * @param userID
     *            the customer to logout
     * @return the login status
     */

    void logout(String userID) throws Exception;

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
     * @param creditcard
     *            the customers creditcard number
     * @param initialBalance
     *            the amount to charge to the customers credit to open the
     *            account and set the initial balance
     * @return the userID if successful, null otherwise
     */
    AccountDataBean register(String userID, String password, String fullname, String address, String email, String creditcard, BigDecimal openBalance)
            throws Exception;

    /**
     * Reset the TradeData by - removing all newly registered users by scenario
     * servlet (i.e. users with userID's beginning with "ru:") * - removing all
     * buy/sell order pairs - setting logoutCount = loginCount
     *
     * return statistics for this benchmark run
     */
    RunStatsDataBean resetTrade(boolean deleteAll) throws Exception;
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/TradeServices.java:TradeServices.<init>
// Node: getOrderFee
// Node: multiply
// Node: add
// Node: getOrderID
// Node: iterator
// Node: hasNext
// Node: next
// Node: getLongRun
// Node: AccountProfileDataBean
// Node: size
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
package com.ibm.websphere.samples.daytrader.direct;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Collection;

import javax.enterprise.concurrent.ManagedThreadFactory;
import javax.jms.ConnectionFactory;
import javax.jms.JMSContext;
import javax.jms.JMSException;
import javax.jms.Queue;
import javax.jms.TextMessage;
import javax.jms.Topic;
import javax.naming.InitialContext;
import javax.sql.DataSource;
import javax.transaction.UserTransaction;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.TradeServices;
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
import com.ibm.websphere.samples.daytrader.util.MDBStats;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * TradeDirect uses direct JDBC and JMS access to a
 * <code>javax.sql.DataSource</code> to implement the business methods of the
 * Trade online broker application. These business methods represent the
 * features and operations that can be performed by customers of the brokerage
 * such as login, logout, get a stock quote, buy or sell a stock, etc. and are
 * specified in the {@link com.ibm.websphere.samples.daytrader.TradeServices}
 * interface
 *
 * Note: In order for this class to be thread-safe, a new TradeJDBC must be
 * created for each call to a method from the TradeInterface interface.
 * Otherwise, pooled connections may not be released.
 *
 * @see com.ibm.websphere.samples.daytrader.TradeServices
 *
 */

public class TradeDirect implements TradeServices {

    private static String dsName = TradeConfig.DATASOURCE;
    private static DataSource datasource = null;
    private static BigDecimal ZERO = new BigDecimal(0.0);
    private boolean inGlobalTxn = false;
    private boolean inSession = false;
   
    /**
     * Zero arg constructor for TradeDirect
     */
    public TradeDirect() {
        if (initialized == false) {
            init();
        }
    }

    public TradeDirect(boolean inSession) {
        if (initialized == false) {
            init();
        }

        this.inSession = inSession;
    }

    /**
     * @see TradeServices#getMarketSummary()
     */
    @Override
    public MarketSummaryDataBean getMarketSummary() throws Exception {

        MarketSummaryDataBean marketSummaryData = null;
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getMarketSummary - inSession(" + this.inSession + ")");
            }
            conn = getConn();
            PreparedStatement stmt = getStatement(conn, getTSIAQuotesOrderByChangeSQL, ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY);

            ArrayList<QuoteDataBean> topGainersData = new ArrayList<QuoteDataBean>(5);
            ArrayList<QuoteDataBean> topLosersData = new ArrayList<QuoteDataBean>(5);

            ResultSet rs = stmt.executeQuery();

            int count = 0;
            while (rs.next() && (count++ < 5)) {
                QuoteDataBean quoteData = getQuoteDataFromResultSet(rs);
                topLosersData.add(quoteData);
            }

            stmt.close();
            stmt = getStatement(conn, "select * from quoteejb q order by q.change1 DESC", ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY);
            rs = stmt.executeQuery();

            count = 0;
            while (rs.next() && (count++ < 5)) {
                QuoteDataBean quoteData = getQuoteDataFromResultSet(rs);
                topGainersData.add(quoteData);
            }

            /*
             * rs.last(); count = 0; while (rs.previous() && (count++ < 5) ) {
             * QuoteDataBean quoteData = getQuoteDataFromResultSet(rs);
             * topGainersData.add(quoteData); }
             */

            stmt.close();

            BigDecimal TSIA = ZERO;
            BigDecimal openTSIA = ZERO;
            double volume = 0.0;

            if ((topGainersData.size() > 0) || (topLosersData.size() > 0)) {

                stmt = getStatement(conn, getTSIASQL);
                rs = stmt.executeQuery();

                if (!rs.next()) {
                    Log.error("TradeDirect:getMarketSummary -- error w/ getTSIASQL -- no results");
                } else {
                    TSIA = rs.getBigDecimal("TSIA");
                }
                stmt.close();

                stmt = getStatement(conn, getOpenTSIASQL);
                rs = stmt.executeQuery();

                if (!rs.next()) {
                    Log.error("TradeDirect:getMarketSummary -- error w/ getOpenTSIASQL -- no results");
                } else {
                    openTSIA = rs.getBigDecimal("openTSIA");
                }
                stmt.close();

                stmt = getStatement(conn, getTSIATotalVolumeSQL);
                rs = stmt.executeQuery();

                if (!rs.next()) {
                    Log.error("TradeDirect:getMarketSummary -- error w/ getTSIATotalVolumeSQL -- no results");
                } else {
                    volume = rs.getDouble("totalVolume");
                }
                stmt.close();
            }
            commit(conn);

            marketSummaryData = new MarketSummaryDataBean(TSIA, openTSIA, volume, topGainersData, topLosersData);

        }

        catch (Exception e) {
            Log.error("TradeDirect:login -- error logging in user", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return marketSummaryData;

    }

    /**
     * @see TradeServices#buy(String, String, double)
     */
    @Override
    public OrderDataBean buy(String userID, String symbol, double quantity, int orderProcessingMode) throws Exception {

        final Connection conn = getConn();
        OrderDataBean orderData = null;
        UserTransaction txn = null;
         
        BigDecimal total;

        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:buy - inSession(" + this.inSession + ")", userID, symbol, new Double(quantity));
            }

            if (!inSession && orderProcessingMode == TradeConfig.ASYNCH_2PHASE) {
                if (Log.doTrace()) {
                    Log.trace("TradeDirect:buy create/begin global transaction");
                }
                // FUTURE the UserTransaction be looked up once
                txn = (javax.transaction.UserTransaction) context.lookup("java:comp/UserTransaction");
                txn.begin();
                setInGlobalTxn(true);
            }

           //conn = getConn();

            AccountDataBean accountData = getAccountData(conn, userID);
            QuoteDataBean quoteData = getQuoteData(conn, symbol);
            HoldingDataBean holdingData = null; // the buy operation will create
            // the holding

            orderData = createOrder(conn, accountData, quoteData, holdingData, "buy", quantity);

            // Update -- account should be credited during completeOrder
            BigDecimal price = quoteData.getPrice();
            BigDecimal orderFee = orderData.getOrderFee();
            total = (new BigDecimal(quantity).multiply(price)).add(orderFee);
            // subtract total from account balance
            creditAccountBalance(conn, accountData, total.negate());
            final Integer orderID = orderData.getOrderID();
            
            try {
                
                if (orderProcessingMode == TradeConfig.SYNCH) {
                    completeOrder(conn,orderID);
                } else  {
                    commit(conn);
                    queueOrder(orderID, true); // 2-phase
                }
            } catch (JMSException je) {
                Log.error("TradeBean:buy(" + userID + "," + symbol + "," + quantity + ") --> failed to queueOrder", je);
                /* On exception - cancel the order */

                cancelOrder(conn, orderData.getOrderID());
            }

            orderData = getOrderData(conn, orderData.getOrderID().intValue());

            if (txn != null) {
                if (Log.doTrace()) {
                    Log.trace("TradeDirect:buy committing global transaction");
                }
                txn.commit();
                setInGlobalTxn(false);
            } else {
                commit(conn);
            }
        } catch (Exception e) {
            Log.error("TradeDirect:buy error - rolling back", e);
            if (getInGlobalTxn()) {
                txn.rollback();
            } else {
                rollBack(conn, e);
            }
        } finally {
            releaseConn(conn);
        }

        return orderData;
    }

    /**
     * @see TradeServices#sell(String, Integer)
     */
    @Override
    public OrderDataBean sell(String userID, Integer holdingID, int orderProcessingMode) throws Exception {
        Connection conn = null;
        OrderDataBean orderData = null;
        UserTransaction txn = null;

        /*
         * total = (quantity * purchasePrice) + orderFee
         */
        BigDecimal total;

        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:sell - inSession(" + this.inSession + ")", userID, holdingID);
            }

            if (!inSession && orderProcessingMode == TradeConfig.ASYNCH_2PHASE) {
                if (Log.doTrace()) {
                    Log.trace("TradeDirect:sell create/begin global transaction");
                    // FUTURE the UserTransaction be looked up once
                }

                txn = (javax.transaction.UserTransaction) context.lookup("java:comp/UserTransaction");
                txn.begin();
                setInGlobalTxn(true);
            }

            conn = getConn();

            AccountDataBean accountData = getAccountData(conn, userID);
            HoldingDataBean holdingData = getHoldingData(conn, holdingID.intValue());
            QuoteDataBean quoteData = null;
            if (holdingData != null) {
                quoteData = getQuoteData(conn, holdingData.getQuoteID());
            }

            if ((accountData == null) || (holdingData == null) || (quoteData == null)) {
                String error = "TradeDirect:sell -- error selling stock -- unable to find:  \n\taccount=" + accountData + "\n\tholding=" + holdingData
                        + "\n\tquote=" + quoteData + "\nfor user: " + userID + " and holdingID: " + holdingID;
                Log.error(error);
                if (getInGlobalTxn()) {
                    txn.rollback();
                } else {
                    rollBack(conn, new Exception(error));
                }
                return orderData;
            }

            double quantity = holdingData.getQuantity();

            orderData = createOrder(conn, accountData, quoteData, holdingData, "sell", quantity);

            // Set the holdingSymbol purchaseDate to selling to signify the sell
            // is "inflight"
            updateHoldingStatus(conn, holdingData.getHoldingID(), holdingData.getQuoteID());

            // UPDATE -- account should be credited during completeOrder
            BigDecimal price = quoteData.getPrice();
            BigDecimal orderFee = orderData.getOrderFee();
            total = (new BigDecimal(quantity).multiply(price)).subtract(orderFee);
            creditAccountBalance(conn, accountData, total);
            
            try {
                if (orderProcessingMode == TradeConfig.SYNCH) {
                    completeOrder(conn, orderData.getOrderID());
                } else {
                    commit(conn);
                    queueOrder(orderData.getOrderID(), true);
                }
            } catch (JMSException je) {
                Log.error("TradeBean:sell(" + userID + "," + holdingID + ") --> failed to queueOrder", je);
                /* On exception - cancel the order */

                cancelOrder(conn, orderData.getOrderID());
            }

            orderData = getOrderData(conn, orderData.getOrderID().intValue());

            if (txn != null) {
                if (Log.doTrace()) {
                    Log.trace("TradeDirect:sell committing global transaction");
                }
                txn.commit();
                setInGlobalTxn(false);
            } else {
                commit(conn);
            }
        } catch (Exception e) {
            Log.error("TradeDirect:sell error", e);
            if (getInGlobalTxn()) {
                txn.rollback();
            } else {
                rollBack(conn, e);
            }
        } finally {
            releaseConn(conn);
        }

        return orderData;
    }

    /**
     * @see TradeServices#queueOrder(Integer)
     */
    @Override
    public void queueOrder(Integer orderID, boolean twoPhase) throws Exception {
        if (Log.doTrace()) {
            Log.trace("TradeDirect:queueOrder - inSession(" + this.inSession + ")", orderID);
        }
        
        if (TradeConfig.getOrderProcessingMode() == TradeConfig.ASYNCH_MANAGEDTHREAD) {
            
            try {
                //TODO: Do I need this lookup every time? 
                ManagedThreadFactory managedThreadFactory = (ManagedThreadFactory) context.lookup("java:comp/DefaultManagedThreadFactory");
                Thread thread = managedThreadFactory.newThread(new CompleteOrderThread(orderID, twoPhase));
                thread.start();
            } catch (Exception e) {
                e.printStackTrace();
            }
        } else { 

            try (JMSContext context = qConnFactory.createContext();){	
                TextMessage message = context.createTextMessage();

                message.setStringProperty("command", "neworder");
                message.setIntProperty("orderID", orderID.intValue());
                message.setBooleanProperty("twoPhase", twoPhase);
                message.setBooleanProperty("direct", true);
                message.setLongProperty("publishTime", System.currentTimeMillis());
                message.setText("neworder: orderID=" + orderID + " runtimeMode=Direct twoPhase=" + twoPhase);
    		        		
                context.createProducer().send(brokerQueue, message);
            } catch (Exception e) {
                throw e; // pass the exception
            }
        }
    }

    /**
     * @see TradeServices#completeOrder(Integer)
     */
    @Override
    public OrderDataBean completeOrder(Integer orderID, boolean twoPhase) throws Exception {
        OrderDataBean orderData = null;
        Connection conn = null;

        try { // twoPhase

            if (Log.doTrace()) {
                Log.trace("TradeDirect:completeOrder - inSession(" + this.inSession + ")", orderID);
            }
            setInGlobalTxn(!inSession && twoPhase);
            conn = getConn();
            orderData = completeOrder(conn, orderID);
           
            commit(conn);

        } catch (Exception e) {
            Log.error("TradeDirect:completeOrder -- error completing order", e);
            rollBack(conn, e);
            cancelOrder(orderID, twoPhase);
        } finally {
            releaseConn(conn);
        }

        return orderData;

    }

    private OrderDataBean completeOrder(Connection conn, Integer orderID) throws Exception {
        //conn = getConn();
        OrderDataBean orderData = null;
        if (Log.doTrace()) {
            Log.trace("TradeDirect:completeOrderInternal - inSession(" + this.inSession + ")", orderID);
        }

        PreparedStatement stmt = getStatement(conn, getOrderSQL);
        stmt.setInt(1, orderID.intValue());

        ResultSet rs = stmt.executeQuery();

        if (!rs.next()) {
            Log.error("TradeDirect:completeOrder -- unable to find order: " + orderID);
            stmt.close();
            return orderData;
        }
        orderData = getOrderDataFromResultSet(rs);

        String orderType = orderData.getOrderType();
        String orderStatus = orderData.getOrderStatus();

        // if (order.isCompleted())
        if ((orderStatus.compareToIgnoreCase("completed") == 0) || (orderStatus.compareToIgnoreCase("alertcompleted") == 0)
                || (orderStatus.compareToIgnoreCase("cancelled") == 0)) {
            throw new Exception("TradeDirect:completeOrder -- attempt to complete Order that is already completed");
        }

        int accountID = rs.getInt("account_accountID");
        String quoteID = rs.getString("quote_symbol");
        int holdingID = rs.getInt("holding_holdingID");

        BigDecimal price = orderData.getPrice();
        double quantity = orderData.getQuantity();

        // get the data for the account and quote
        // the holding will be created for a buy or extracted for a sell

        /*
         * Use the AccountID and Quote Symbol from the Order AccountDataBean
         * accountData = getAccountData(accountID, conn); QuoteDataBean
         * quoteData = getQuoteData(conn, quoteID);
         */
        String userID = getAccountProfileData(conn, new Integer(accountID)).getUserID();

        HoldingDataBean holdingData = null;

        if (Log.doTrace()) {
            Log.trace("TradeDirect:completeOrder--> Completing Order " + orderData.getOrderID() + "\n\t Order info: " + orderData + "\n\t Account info: "
                    + accountID + "\n\t Quote info: " + quoteID);
        }

        // if (order.isBuy())
        if (orderType.compareToIgnoreCase("buy") == 0) {
            /*
             * Complete a Buy operation - create a new Holding for the Account -
             * deduct the Order cost from the Account balance
             */

            holdingData = createHolding(conn, accountID, quoteID, quantity, price);
            updateOrderHolding(conn, orderID.intValue(), holdingData.getHoldingID().intValue());
        }

        // if (order.isSell()) {
        if (orderType.compareToIgnoreCase("sell") == 0) {
            /*
             * Complete a Sell operation - remove the Holding from the Account -
             * deposit the Order proceeds to the Account balance
             */
            holdingData = getHoldingData(conn, holdingID);
            if (holdingData == null) {
                Log.debug("TradeDirect:completeOrder:sell -- user: " + userID + " already sold holding: " + holdingID);
            } else {
                removeHolding(conn, holdingID, orderID.intValue());
            }

        }

        updateOrderStatus(conn, orderData.getOrderID(), "closed");

        if (Log.doTrace()) {
            Log.trace("TradeDirect:completeOrder--> Completed Order " + orderData.getOrderID() + "\n\t Order info: " + orderData + "\n\t Account info: "
                    + accountID + "\n\t Quote info: " + quoteID + "\n\t Holding info: " + holdingData);
        }

        stmt.close();
        
        commit(conn);

        // commented out following call
        // - orderCompleted doesn't really do anything (think it was a hook for
        // old Trade caching code)

        // signify this order for user userID is complete
        // This call does not work here for Sync
        if (TradeConfig.orderProcessingMode != TradeConfig.SYNCH) {
            TradeAction tradeAction = new TradeAction(this);
            tradeAction.orderCompleted(userID, orderID);
        }

        return orderData;
    }

    /**
     * @see TradeServices#cancelOrder(Integer, boolean)
     */
    @Override
    public void cancelOrder(Integer orderID, boolean twoPhase) throws Exception {

        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:cancelOrder - inSession(" + this.inSession + ")", orderID);
            }
            setInGlobalTxn(!inSession && twoPhase);
            conn = getConn();
            cancelOrder(conn, orderID);
            commit(conn);

        } catch (Exception e) {
            Log.error("TradeDirect:cancelOrder -- error cancelling order: " + orderID, e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
    }

    private void cancelOrder(Connection conn, Integer orderID) throws Exception {
        updateOrderStatus(conn, orderID, "cancelled");
    }

    @Override
    public void orderCompleted(String userID, Integer orderID) throws Exception {
        throw new UnsupportedOperationException("TradeDirect:orderCompleted method not supported");
    }

    private HoldingDataBean createHolding(Connection conn, int accountID, String symbol, double quantity, BigDecimal purchasePrice) throws Exception {

        Timestamp purchaseDate = new Timestamp(System.currentTimeMillis());
        PreparedStatement stmt = getStatement(conn, createHoldingSQL);

        Integer holdingID = KeySequenceDirect.getNextID(conn, "holding", inSession, getInGlobalTxn());
        stmt.setInt(1, holdingID.intValue());
        stmt.setTimestamp(2, purchaseDate);
        stmt.setBigDecimal(3, purchasePrice);
        stmt.setDouble(4, quantity);
        stmt.setString(5, symbol);
        stmt.setInt(6, accountID);
        stmt.executeUpdate();

        stmt.close();

        return getHoldingData(conn, holdingID.intValue());
    }

    private void removeHolding(Connection conn, int holdingID, int orderID) throws Exception {
        PreparedStatement stmt = getStatement(conn, removeHoldingSQL);

        stmt.setInt(1, holdingID);
        stmt.executeUpdate();
        stmt.close();

        // set the HoldingID to NULL for the purchase and sell order now that
        // the holding as been removed
        stmt = getStatement(conn, removeHoldingFromOrderSQL);

        stmt.setInt(1, holdingID);
        stmt.executeUpdate();
        stmt.close();

    }

    private OrderDataBean createOrder(Connection conn, AccountDataBean accountData, QuoteDataBean quoteData, HoldingDataBean holdingData, String orderType,
            double quantity) throws Exception {

        Timestamp currentDate = new Timestamp(System.currentTimeMillis());

        PreparedStatement stmt = getStatement(conn, createOrderSQL);

        Integer orderID = KeySequenceDirect.getNextID(conn, "order", inSession, getInGlobalTxn());
        stmt.setInt(1, orderID.intValue());
        stmt.setString(2, orderType);
        stmt.setString(3, "open");
        stmt.setTimestamp(4, currentDate);
        stmt.setDouble(5, quantity);
        stmt.setBigDecimal(6, quoteData.getPrice().setScale(FinancialUtils.SCALE, FinancialUtils.ROUND));
        stmt.setBigDecimal(7, TradeConfig.getOrderFee(orderType));
        stmt.setInt(8, accountData.getAccountID().intValue());
        if (holdingData == null) {
            stmt.setNull(9, java.sql.Types.INTEGER);
        } else {
            stmt.setInt(9, holdingData.getHoldingID().intValue());
        }
        stmt.setString(10, quoteData.getSymbol());
        stmt.executeUpdate();

        stmt.close();

        return getOrderData(conn, orderID.intValue());
    }

    /**
     * @see TradeServices#getOrders(String)
     */
    @Override
    public Collection<OrderDataBean> getOrders(String userID) throws Exception {
        Collection<OrderDataBean> orderDataBeans = new ArrayList<OrderDataBean>();
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getOrders - inSession(" + this.inSession + ")", userID);
            }

            conn = getConn();
            PreparedStatement stmt = getStatement(conn, getOrdersByUserSQL);
            stmt.setString(1, userID);

            ResultSet rs = stmt.executeQuery();

            // TODO: return top 5 orders for now -- next version will add a
            // getAllOrders method
            // also need to get orders sorted by order id descending
            int i = 0;
            while ((rs.next()) && (i++ < 5)) {
                OrderDataBean orderData = getOrderDataFromResultSet(rs);
                orderDataBeans.add(orderData);
            }

            stmt.close();
            commit(conn);

        } catch (Exception e) {
            Log.error("TradeDirect:getOrders -- error getting user orders", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return orderDataBeans;
    }

    /**
     * @see TradeServices#getClosedOrders(String)
     */
    @Override
    public Collection<OrderDataBean> getClosedOrders(String userID) throws Exception {
        Collection<OrderDataBean> orderDataBeans = new ArrayList<OrderDataBean>();
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getClosedOrders - inSession(" + this.inSession + ")", userID);
            }

            conn = getConn();
            PreparedStatement stmt = getStatement(conn, getClosedOrdersSQL);
            stmt.setString(1, userID);

            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                OrderDataBean orderData = getOrderDataFromResultSet(rs);
                orderData.setOrderStatus("completed");
                updateOrderStatus(conn, orderData.getOrderID(), orderData.getOrderStatus());
                orderDataBeans.add(orderData);

            }

            stmt.close();
            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:getOrders -- error getting user orders", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return orderDataBeans;
    }

    /**
     * @see TradeServices#createQuote(String, String, BigDecimal)
     */
    @Override
    public QuoteDataBean createQuote(String symbol, String companyName, BigDecimal price) throws Exception {

        QuoteDataBean quoteData = null;
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.traceEnter("TradeDirect:createQuote - inSession(" + this.inSession + ")");
            }

            price = price.setScale(FinancialUtils.SCALE, FinancialUtils.ROUND);
            double volume = 0.0, change = 0.0;

            conn = getConn();
            PreparedStatement stmt = getStatement(conn, createQuoteSQL);
            stmt.setString(1, symbol); // symbol
            stmt.setString(2, companyName); // companyName
            stmt.setDouble(3, volume); // volume
            stmt.setBigDecimal(4, price); // price
            stmt.setBigDecimal(5, price); // open
            stmt.setBigDecimal(6, price); // low
            stmt.setBigDecimal(7, price); // high
            stmt.setDouble(8, change); // change

            stmt.executeUpdate();
            stmt.close();
            commit(conn);

            quoteData = new QuoteDataBean(symbol, companyName, volume, price, price, price, price, change);
            if (Log.doTrace()) {
                Log.traceExit("TradeDirect:createQuote");
            }
        } catch (Exception e) {
            Log.error("TradeDirect:createQuote -- error creating quote", e);
        } finally {
            releaseConn(conn);
        }
        return quoteData;
    }

    /**
     * @see TradeServices#getQuote(String)
     */

    @Override
    public QuoteDataBean getQuote(String symbol) throws Exception {
        QuoteDataBean quoteData = null;
        Connection conn = null;

        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getQuote - inSession(" + this.inSession + ")", symbol);
            }

            conn = getConn();
            quoteData = getQuote(conn, symbol);
            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:getQuote -- error getting quote", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return quoteData;
    }

    private QuoteDataBean getQuote(Connection conn, String symbol) throws Exception {
        QuoteDataBean quoteData = null;
        PreparedStatement stmt = getStatement(conn, getQuoteSQL);
        stmt.setString(1, symbol); // symbol

        ResultSet rs = stmt.executeQuery();

        if (!rs.next()) {
            Log.error("TradeDirect:getQuote -- failure no result.next() for symbol: " + symbol);
        } else {
            quoteData = getQuoteDataFromResultSet(rs);
        }

        stmt.close();

        return quoteData;
    }

    private QuoteDataBean getQuoteForUpdate(Connection conn, String symbol) throws Exception {
        QuoteDataBean quoteData = null;
        PreparedStatement stmt = getStatement(conn, getQuoteForUpdateSQL);
        stmt.setString(1, symbol); // symbol

        ResultSet rs = stmt.executeQuery();

        if (!rs.next()) {
            Log.error("TradeDirect:getQuote -- failure no result.next()");
        } else {
            quoteData = getQuoteDataFromResultSet(rs);
        }

        stmt.close();

        return quoteData;
    }

    /**
     * @see TradeServices#getAllQuotes(String)
     */
    @Override
    public Collection<QuoteDataBean> getAllQuotes() throws Exception {
        Collection<QuoteDataBean> quotes = new ArrayList<QuoteDataBean>();
        QuoteDataBean quoteData = null;

        Connection conn = null;
        try {
            conn = getConn();

            PreparedStatement stmt = getStatement(conn, getAllQuotesSQL);

            ResultSet rs = stmt.executeQuery();

            while (!rs.next()) {
                quoteData = getQuoteDataFromResultSet(rs);
                quotes.add(quoteData);
            }

            stmt.close();
        } catch (Exception e) {
            Log.error("TradeDirect:getAllQuotes", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }

        return quotes;
    }

    /**
     * @see TradeServices#getHoldings(String)
     */
    @Override
    public Collection<HoldingDataBean> getHoldings(String userID) throws Exception {
        Collection<HoldingDataBean> holdingDataBeans = new ArrayList<HoldingDataBean>();
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getHoldings - inSession(" + this.inSession + ")", userID);
            }

            conn = getConn();
            PreparedStatement stmt = getStatement(conn, getHoldingsForUserSQL);
            stmt.setString(1, userID);

            ResultSet rs = stmt.executeQuery();

            while (rs.next()) {
                HoldingDataBean holdingData = getHoldingDataFromResultSet(rs);
                holdingDataBeans.add(holdingData);
            }

            stmt.close();
            commit(conn);

        } catch (Exception e) {
            Log.error("TradeDirect:getHoldings -- error getting user holings", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return holdingDataBeans;
    }

    /**
     * @see TradeServices#getHolding(Integer)
     */
    @Override
    public HoldingDataBean getHolding(Integer holdingID) throws Exception {
        HoldingDataBean holdingData = null;
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getHolding - inSession(" + this.inSession + ")", holdingID);
            }

            conn = getConn();
            holdingData = getHoldingData(holdingID.intValue());

            commit(conn);

        } catch (Exception e) {
            Log.error("TradeDirect:getHolding -- error getting holding " + holdingID + "", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return holdingData;
    }

    /**
     * @see TradeServices#getAccountData(String)
     */
    @Override
    public AccountDataBean getAccountData(String userID) throws Exception {
        try {
            AccountDataBean accountData = null;
            Connection conn = null;
            try {
                if (Log.doTrace()) {
                    Log.trace("TradeDirect:getAccountData - inSession(" + this.inSession + ")", userID);
                }

                conn = getConn();
                accountData = getAccountData(conn, userID);
                commit(conn);

            } catch (Exception e) {
                Log.error("TradeDirect:getAccountData -- error getting account data", e);
                rollBack(conn, e);
            } finally {
                releaseConn(conn);
            }
            return accountData;
        } catch (Exception e) {
            throw new Exception(e.getMessage(), e);
        }
    }

    private AccountDataBean getAccountData(Connection conn, String userID) throws Exception {
        PreparedStatement stmt = getStatement(conn, getAccountForUserSQL);
        stmt.setString(1, userID);
        ResultSet rs = stmt.executeQuery();
        AccountDataBean accountData = getAccountDataFromResultSet(rs);
        stmt.close();
        return accountData;
    }

    /*private AccountDataBean getAccountDataForUpdate(Connection conn,
            String userID) throws Exception {
        PreparedStatement stmt = getStatement(conn,
                getAccountForUserForUpdateSQL);
        stmt.setString(1, userID);
        ResultSet rs = stmt.executeQuery();
        AccountDataBean accountData = getAccountDataFromResultSet(rs);
        stmt.close();
        return accountData;
    }*/

    /**
     * @see TradeServices#getAccountData(String)
     */
    public AccountDataBean getAccountData(int accountID) throws Exception {
        AccountDataBean accountData = null;
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getAccountData - inSession(" + this.inSession + ")", new Integer(accountID));
            }

            conn = getConn();
            accountData = getAccountData(accountID, conn);
            commit(conn);

        } catch (Exception e) {
            Log.error("TradeDirect:getAccountData -- error getting account data", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return accountData;
    }

    private AccountDataBean getAccountData(int accountID, Connection conn) throws Exception {
        PreparedStatement stmt = getStatement(conn, getAccountSQL);
        stmt.setInt(1, accountID);
        ResultSet rs = stmt.executeQuery();
        AccountDataBean accountData = getAccountDataFromResultSet(rs);
        stmt.close();
        return accountData;
    }

    /*
    private AccountDataBean getAccountDataForUpdate(int accountID,
            Connection conn) throws Exception {
        PreparedStatement stmt = getStatement(conn, getAccountForUpdateSQL);
        stmt.setInt(1, accountID);
        ResultSet rs = stmt.executeQuery();
        AccountDataBean accountData = getAccountDataFromResultSet(rs);
        stmt.close();
        return accountData;
    }
     */

    /*
    private QuoteDataBean getQuoteData(String symbol) throws Exception {
        QuoteDataBean quoteData = null;
        Connection conn = null;
        try {
            conn = getConn();
            quoteData = getQuoteData(conn, symbol);
            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:getQuoteData -- error getting data", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return quoteData;
    }
     */

    private QuoteDataBean getQuoteData(Connection conn, String symbol) throws Exception {
        QuoteDataBean quoteData = null;
        PreparedStatement stmt = getStatement(conn, getQuoteSQL);
        stmt.setString(1, symbol);
        ResultSet rs = stmt.executeQuery();
        if (!rs.next()) {
            Log.error("TradeDirect:getQuoteData -- could not find quote for symbol=" + symbol);
        } else {
            quoteData = getQuoteDataFromResultSet(rs);
        }
        stmt.close();
        return quoteData;
    }

    private HoldingDataBean getHoldingData(int holdingID) throws Exception {
        HoldingDataBean holdingData = null;
        Connection conn = null;
        try {
            conn = getConn();
            holdingData = getHoldingData(conn, holdingID);
            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:getHoldingData -- error getting data", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return holdingData;
    }

    private HoldingDataBean getHoldingData(Connection conn, int holdingID) throws Exception {
        HoldingDataBean holdingData = null;
        PreparedStatement stmt = getStatement(conn, getHoldingSQL);
        stmt.setInt(1, holdingID);
        ResultSet rs = stmt.executeQuery();
        if (!rs.next()) {
            Log.error("TradeDirect:getHoldingData -- no results -- holdingID=" + holdingID);
        } else {
            holdingData = getHoldingDataFromResultSet(rs);
        }

        stmt.close();
        return holdingData;
    }

    /*
    private OrderDataBean getOrderData(int orderID) throws Exception {
        OrderDataBean orderData = null;
        Connection conn = null;
        try {
            conn = getConn();
            orderData = getOrderData(conn, orderID);
            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:getOrderData -- error getting data", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return orderData;
    }
     */

    private OrderDataBean getOrderData(Connection conn, int orderID) throws Exception {
        OrderDataBean orderData = null;
        if (Log.doTrace()) {
            Log.trace("TradeDirect:getOrderData(conn, " + orderID + ")");
        }
        PreparedStatement stmt = getStatement(conn, getOrderSQL);
        stmt.setInt(1, orderID);
        ResultSet rs = stmt.executeQuery();
        if (!rs.next()) {
            Log.error("TradeDirect:getOrderData -- no results for orderID:" + orderID);
        } else {
            orderData = getOrderDataFromResultSet(rs);
        }
        stmt.close();
        return orderData;
    }

    /**
     * @see TradeServices#getAccountProfileData(String)
     */
    @Override
    public AccountProfileDataBean getAccountProfileData(String userID) throws Exception {
        AccountProfileDataBean accountProfileData = null;
        Connection conn = null;

        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getAccountProfileData - inSession(" + this.inSession + ")", userID);
            }

            conn = getConn();
            accountProfileData = getAccountProfileData(conn, userID);
            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:getAccountProfileData -- error getting profile data", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return accountProfileData;
    }

    private AccountProfileDataBean getAccountProfileData(Connection conn, String userID) throws Exception {
        PreparedStatement stmt = getStatement(conn, getAccountProfileSQL);
        stmt.setString(1, userID);

        ResultSet rs = stmt.executeQuery();

        AccountProfileDataBean accountProfileData = getAccountProfileDataFromResultSet(rs);
        stmt.close();
        return accountProfileData;
    }

    /*
    private AccountProfileDataBean getAccountProfileData(Integer accountID)
    throws Exception {
        AccountProfileDataBean accountProfileData = null;
        Connection conn = null;

        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:getAccountProfileData", accountID);
            }

            conn = getConn();
            accountProfileData = getAccountProfileData(conn, accountID);
            commit(conn);
        } catch (Exception e) {
            Log.error(
                    "TradeDirect:getAccountProfileData -- error getting profile data",
                    e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return accountProfileData;
    }
     */

    private AccountProfileDataBean getAccountProfileData(Connection conn, Integer accountID) throws Exception {
        PreparedStatement stmt = getStatement(conn, getAccountProfileForAccountSQL);
        stmt.setInt(1, accountID.intValue());

        ResultSet rs = stmt.executeQuery();

        AccountProfileDataBean accountProfileData = getAccountProfileDataFromResultSet(rs);
        stmt.close();
        return accountProfileData;
    }

    /**
     * @see TradeServices#updateAccountProfile(AccountProfileDataBean)
     */
    @Override
    public AccountProfileDataBean updateAccountProfile(AccountProfileDataBean profileData) throws Exception {
        AccountProfileDataBean accountProfileData = null;
        Connection conn = null;

        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:updateAccountProfileData - inSession(" + this.inSession + ")", profileData.getUserID());
            }

            conn = getConn();
            updateAccountProfile(conn, profileData);

            accountProfileData = getAccountProfileData(conn, profileData.getUserID());
            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:getAccountProfileData -- error getting profile data", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return accountProfileData;
    }

    private void creditAccountBalance(Connection conn, AccountDataBean accountData, BigDecimal credit) throws Exception {
        PreparedStatement stmt = getStatement(conn, creditAccountBalanceSQL);

        stmt.setBigDecimal(1, credit);
        stmt.setInt(2, accountData.getAccountID().intValue());

        stmt.executeUpdate();
        stmt.close();

    }

    // Set Timestamp to zero to denote sell is inflight
    // UPDATE -- could add a "status" attribute to holding
    private void updateHoldingStatus(Connection conn, Integer holdingID, String symbol) throws Exception {
        Timestamp ts = new Timestamp(0);
        PreparedStatement stmt = getStatement(conn, "update holdingejb set purchasedate= ? where holdingid = ?");

        stmt.setTimestamp(1, ts);
        stmt.setInt(2, holdingID.intValue());
        stmt.executeUpdate();
        stmt.close();
    }

    private void updateOrderStatus(Connection conn, Integer orderID, String status) throws Exception {
        PreparedStatement stmt = getStatement(conn, updateOrderStatusSQL);

        stmt.setString(1, status);
        stmt.setTimestamp(2, new Timestamp(System.currentTimeMillis()));
        stmt.setInt(3, orderID.intValue());
        stmt.executeUpdate();
        stmt.close();
    }

    private void updateOrderHolding(Connection conn, int orderID, int holdingID) throws Exception {
        PreparedStatement stmt = getStatement(conn, updateOrderHoldingSQL);

        stmt.setInt(1, holdingID);
        stmt.setInt(2, orderID);
        stmt.executeUpdate();
        stmt.close();
    }

    private void updateAccountProfile(Connection conn, AccountProfileDataBean profileData) throws Exception {
        PreparedStatement stmt = getStatement(conn, updateAccountProfileSQL);

        stmt.setString(1, profileData.getPassword());
        stmt.setString(2, profileData.getFullName());
        stmt.setString(3, profileData.getAddress());
        stmt.setString(4, profileData.getEmail());
        stmt.setString(5, profileData.getCreditCard());
        stmt.setString(6, profileData.getUserID());

        stmt.executeUpdate();
        stmt.close();
    }

    /*
    private void updateQuoteVolume(Connection conn, QuoteDataBean quoteData,
            double quantity) throws Exception {
        PreparedStatement stmt = getStatement(conn, updateQuoteVolumeSQL);

        stmt.setDouble(1, quantity);
        stmt.setString(2, quoteData.getSymbol());

        stmt.executeUpdate();
        stmt.close();
    }
     */

    @Override
    public QuoteDataBean updateQuotePriceVolume(String symbol, BigDecimal changeFactor, double sharesTraded) throws Exception {
        return updateQuotePriceVolumeInt(symbol, changeFactor, sharesTraded, TradeConfig.getPublishQuotePriceChange());
    }

    /**
     * Update a quote's price and volume
     *
     * @param symbol
     *            The PK of the quote
     * @param changeFactor
     *            the percent to change the old price by (between 50% and 150%)
     * @param sharedTraded
     *            the ammount to add to the current volume
     * @param publishQuotePriceChange
     *            used by the PingJDBCWrite Primitive to ensure no JMS is used,
     *            should be true for all normal calls to this API
     */
    public QuoteDataBean updateQuotePriceVolumeInt(String symbol, BigDecimal changeFactor, double sharesTraded, boolean publishQuotePriceChange)
            throws Exception {

        if (TradeConfig.getUpdateQuotePrices() == false) {
            return new QuoteDataBean();
        }

        QuoteDataBean quoteData = null;
        Connection conn = null;

        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:updateQuotePriceVolume - inSession(" + this.inSession + ")", symbol, changeFactor, new Double(sharesTraded));
            }

            conn = getConn();

            quoteData = getQuoteForUpdate(conn, symbol);
            BigDecimal oldPrice = quoteData.getPrice();
            BigDecimal openPrice = quoteData.getOpen();

            double newVolume = quoteData.getVolume() + sharesTraded;

            if (oldPrice.equals(TradeConfig.PENNY_STOCK_PRICE)) {
                changeFactor = TradeConfig.PENNY_STOCK_RECOVERY_MIRACLE_MULTIPLIER;
            } else if (oldPrice.compareTo(TradeConfig.MAXIMUM_STOCK_PRICE) > 0) {
                changeFactor = TradeConfig.MAXIMUM_STOCK_SPLIT_MULTIPLIER;
            }

            BigDecimal newPrice = changeFactor.multiply(oldPrice).setScale(2, BigDecimal.ROUND_HALF_UP);
            double change = newPrice.subtract(openPrice).doubleValue();

            updateQuotePriceVolume(conn, quoteData.getSymbol(), newPrice, newVolume, change);
            quoteData = getQuote(conn, symbol);

            commit(conn);

            if (publishQuotePriceChange) {
                publishQuotePriceChange(quoteData, oldPrice, changeFactor, sharesTraded);
            }

        } catch (Exception e) {
            Log.error("TradeDirect:updateQuotePriceVolume -- error updating quote price/volume for symbol:" + symbol);
            rollBack(conn, e);
            throw e;
        } finally {
            releaseConn(conn);
        }
        return quoteData;
    }

    private void updateQuotePriceVolume(Connection conn, String symbol, BigDecimal newPrice, double newVolume, double change) throws Exception {

        PreparedStatement stmt = getStatement(conn, updateQuotePriceVolumeSQL);

        stmt.setBigDecimal(1, newPrice);
        stmt.setDouble(2, change);
        stmt.setDouble(3, newVolume);
        stmt.setString(4, symbol);

        stmt.executeUpdate();
        stmt.close();
    }

    private void publishQuotePriceChange(QuoteDataBean quoteData, BigDecimal oldPrice, BigDecimal changeFactor, double sharesTraded) throws Exception {
        if (Log.doTrace()) {
            Log.trace("TradeDirect:publishQuotePrice PUBLISHING to MDB quoteData = " + quoteData);
        }
        
        try (JMSContext context = tConnFactory.createContext();){
    		TextMessage message = context.createTextMessage();

    		message.setStringProperty("command", "updateQuote");
            message.setStringProperty("symbol", quoteData.getSymbol());
            message.setStringProperty("company", quoteData.getCompanyName());
            message.setStringProperty("price", quoteData.getPrice().toString());
            message.setStringProperty("oldPrice", oldPrice.toString());
            message.setStringProperty("open", quoteData.getOpen().toString());
            message.setStringProperty("low", quoteData.getLow().toString());
            message.setStringProperty("high", quoteData.getHigh().toString());
            message.setDoubleProperty("volume", quoteData.getVolume());

            message.setStringProperty("changeFactor", changeFactor.toString());
            message.setDoubleProperty("sharesTraded", sharesTraded);
            message.setLongProperty("publishTime", System.currentTimeMillis());
            message.setText("Update Stock price for " + quoteData.getSymbol() + " old price = " + oldPrice + " new price = " + quoteData.getPrice());

      		
    		context.createProducer().send(streamerTopic, message);

        } catch (Exception e) {
            throw e; // pass exception back

        }
    }

    /**
     * @see TradeServices#login(String, String)
     */

    @Override
    public AccountDataBean login(String userID, String password) throws Exception {

        AccountDataBean accountData = null;
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect:login - inSession(" + this.inSession + ")", userID, password);
            }

            conn = getConn();
            PreparedStatement stmt = getStatement(conn, getAccountProfileSQL);
            stmt.setString(1, userID);

            ResultSet rs = stmt.executeQuery();
            if (!rs.next()) {
                Log.error("TradeDirect:login -- failure to find account for" + userID);
                throw new javax.ejb.FinderException("Cannot find account for" + userID);
            }

            String pw = rs.getString("passwd");
            stmt.close();
            if ((pw == null) || (pw.equals(password) == false)) {
                String error = "TradeDirect:Login failure for user: " + userID + "\n\tIncorrect password-->" + userID + ":" + password;
                Log.error(error);
                throw new Exception(error);
            }

            stmt = getStatement(conn, loginSQL);
            stmt.setTimestamp(1, new Timestamp(System.currentTimeMillis()));
            stmt.setString(2, userID);

            stmt.executeUpdate();
            stmt.close();

            stmt = getStatement(conn, getAccountForUserSQL);
            stmt.setString(1, userID);
            rs = stmt.executeQuery();

            accountData = getAccountDataFromResultSet(rs);

            stmt.close();

            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:login -- error logging in user", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
        return accountData;

        /*
         * setLastLogin( new Timestamp(System.currentTimeMillis()) );
         * setLoginCount( getLoginCount() + 1 );
         */
    }

    /**
     * @see TradeServices#logout(String)
     */
    @Override
    public void logout(String userID) throws Exception {
        if (Log.doTrace()) {
            Log.trace("TradeDirect:logout - inSession(" + this.inSession + ")", userID);
        }
        Connection conn = null;
        try {
            conn = getConn();
            PreparedStatement stmt = getStatement(conn, logoutSQL);
            stmt.setString(1, userID);
            stmt.executeUpdate();
            stmt.close();

            commit(conn);
        } catch (Exception e) {
            Log.error("TradeDirect:logout -- error logging out user", e);
            rollBack(conn, e);
        } finally {
            releaseConn(conn);
        }
    }

    /**
     * @see TradeServices#register(String, String, String, String, String,
     *      String, BigDecimal, boolean)
     */

    @Override
    public AccountDataBean register(String userID, String password, String fullname, String address, String email, String creditcard, BigDecimal openBalance)
            throws Exception {

        AccountDataBean accountData = null;
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.traceEnter("TradeDirect:register - inSession(" + this.inSession + ")");
            }

            conn = getConn();
            PreparedStatement stmt = getStatement(conn, createAccountSQL);

            Integer accountID = KeySequenceDirect.getNextID(conn, "account", inSession, getInGlobalTxn());
            BigDecimal balance = openBalance;
            Timestamp creationDate = new Timestamp(System.currentTimeMillis());
            Timestamp lastLogin = creationDate;
            int loginCount = 0;
            int logoutCount = 0;

            stmt.setInt(1, accountID.intValue());
            stmt.setTimestamp(2, creationDate);
            stmt.setBigDecimal(3, openBalance);
            stmt.setBigDecimal(4, balance);
            stmt.setTimestamp(5, lastLogin);
            stmt.setInt(6, loginCount);
            stmt.setInt(7, logoutCount);
            stmt.setString(8, userID);
            stmt.executeUpdate();
            stmt.close();

            stmt = getStatement(conn, createAccountProfileSQL);
            stmt.setString(1, userID);
            stmt.setString(2, password);
            stmt.setString(3, fullname);
            stmt.setString(4, address);
            stmt.setString(5, email);
            stmt.setString(6, creditcard);
            stmt.executeUpdate();
            stmt.close();

            commit(conn);

            accountData = new AccountDataBean(accountID, loginCount, logoutCount, lastLogin, creationDate, balance, openBalance, userID);
            if (Log.doTrace()) {
                Log.traceExit("TradeDirect:register");
            }
        } catch (Exception e) {
            Log.error("TradeDirect:register -- error registering new user", e);
        } finally {
            releaseConn(conn);
        }
        return accountData;
    }

    private AccountDataBean getAccountDataFromResultSet(ResultSet rs) throws Exception {
        AccountDataBean accountData = null;

        if (!rs.next()) {
            Log.error("TradeDirect:getAccountDataFromResultSet -- cannot find account data");
        } else {
            accountData = new AccountDataBean(new Integer(rs.getInt("accountID")), rs.getInt("loginCount"), rs.getInt("logoutCount"),
                    rs.getTimestamp("lastLogin"), rs.getTimestamp("creationDate"), rs.getBigDecimal("balance"), rs.getBigDecimal("openBalance"),
                    rs.getString("profile_userID"));
        }
        return accountData;
    }

    private AccountProfileDataBean getAccountProfileDataFromResultSet(ResultSet rs) throws Exception {
        AccountProfileDataBean accountProfileData = null;

        if (!rs.next()) {
            Log.error("TradeDirect:getAccountProfileDataFromResultSet -- cannot find accountprofile data");
        } else {
            accountProfileData = new AccountProfileDataBean(rs.getString("userID"), rs.getString("passwd"), rs.getString("fullName"), rs.getString("address"),
                    rs.getString("email"), rs.getString("creditCard"));
        }

        return accountProfileData;
    }

    private HoldingDataBean getHoldingDataFromResultSet(ResultSet rs) throws Exception {
        HoldingDataBean holdingData = null;

        holdingData = new HoldingDataBean(new Integer(rs.getInt("holdingID")), rs.getDouble("quantity"), rs.getBigDecimal("purchasePrice"),
                rs.getTimestamp("purchaseDate"), rs.getString("quote_symbol"));
        return holdingData;
    }

    private QuoteDataBean getQuoteDataFromResultSet(ResultSet rs) throws Exception {
        QuoteDataBean quoteData = null;

        quoteData = new QuoteDataBean(rs.getString("symbol"), rs.getString("companyName"), rs.getDouble("volume"), rs.getBigDecimal("price"),
                rs.getBigDecimal("open1"), rs.getBigDecimal("low"), rs.getBigDecimal("high"), rs.getDouble("change1"));
        return quoteData;
    }

    private OrderDataBean getOrderDataFromResultSet(ResultSet rs) throws Exception {
        OrderDataBean orderData = null;

        orderData = new OrderDataBean(new Integer(rs.getInt("orderID")), rs.getString("orderType"), rs.getString("orderStatus"), rs.getTimestamp("openDate"),
                rs.getTimestamp("completionDate"), rs.getDouble("quantity"), rs.getBigDecimal("price"), rs.getBigDecimal("orderFee"),
                rs.getString("quote_symbol"));
        return orderData;
    }

    public String checkDBProductName() throws Exception {
        Connection conn = null;
        String dbProductName = null;

        try {
            if (Log.doTrace()) {
                Log.traceEnter("TradeDirect:checkDBProductName");
            }

            conn = getConn();
            DatabaseMetaData dbmd = conn.getMetaData();
            dbProductName = dbmd.getDatabaseProductName();
        } catch (SQLException e) {
            Log.error(e, "TradeDirect:checkDBProductName() -- Error checking the Daytrader Database Product Name");
        } finally {
            releaseConn(conn);
        }
        return dbProductName;
    }

    public boolean recreateDBTables(Object[] sqlBuffer, java.io.PrintWriter out) throws Exception {
        // Clear MDB Statistics
        MDBStats.getInstance().reset();

        Connection conn = null;
        boolean success = false;
        try {
            if (Log.doTrace()) {
                Log.traceEnter("TradeDirect:recreateDBTables");
            }

            conn = getConn();
            Statement stmt = conn.createStatement();
            int bufferLength = sqlBuffer.length;
            for (int i = 0; i < bufferLength; i++) {
                try {
                    stmt.executeUpdate((String) sqlBuffer[i]);
                    // commit(conn);
                } catch (SQLException ex) {
                    // Ignore DROP statements as tables won't always exist.
                    if (((String) sqlBuffer[i]).indexOf("DROP ") < 0) {
                        Log.error("TradeDirect:recreateDBTables SQL Exception thrown on executing the foll sql command: " + sqlBuffer[i], ex);
                        out.println("<BR>SQL Exception thrown on executing the foll sql command: <I>" + sqlBuffer[i] + "</I> . Check log for details.</BR>");
                    }
                }
            }
            stmt.close();
            commit(conn);
            success = true;
        } catch (Exception e) {
            Log.error(e, "TradeDirect:recreateDBTables() -- Error dropping and recreating the database tables");
        } finally {
            releaseConn(conn);
        }
        return success;
    }

    @Override
    public RunStatsDataBean resetTrade(boolean deleteAll) throws Exception {
        // Clear MDB Statistics
        MDBStats.getInstance().reset();
        // Reset Trade

        RunStatsDataBean runStatsData = new RunStatsDataBean();
        Connection conn = null;
        try {
            if (Log.doTrace()) {
                Log.traceEnter("TradeDirect:resetTrade deleteAll rows=" + deleteAll);
            }

            conn = getConn();
            PreparedStatement stmt = null;
            ResultSet rs = null;

            if (deleteAll) {
                try {
                    stmt = getStatement(conn, "delete from quoteejb");
                    stmt.executeUpdate();
                    stmt.close();
                    stmt = getStatement(conn, "delete from accountejb");
                    stmt.executeUpdate();
                    stmt.close();
                    stmt = getStatement(conn, "delete from accountprofileejb");
                    stmt.executeUpdate();
                    stmt.close();
                    stmt = getStatement(conn, "delete from holdingejb");
                    stmt.executeUpdate();
                    stmt.close();
                    stmt = getStatement(conn, "delete from orderejb");
                    stmt.executeUpdate();
                    stmt.close();
                    // FUTURE: - DuplicateKeyException - For now, don't start at
                    // zero as KeySequenceDirect and KeySequenceBean will still
                    // give out
                    // the cached Block and then notice this change. Better
                    // solution is
                    // to signal both classes to drop their cached blocks
                    // stmt = getStatement(conn, "delete from keygenejb");
                    // stmt.executeUpdate();
                    // stmt.close();
                    commit(conn);
                } catch (Exception e) {
                    Log.error(e, "TradeDirect:resetTrade(deleteAll) -- Error deleting Trade users and stock from the Trade database");
                }
                return runStatsData;
            }

            stmt = getStatement(conn, "delete from holdingejb where holdingejb.account_accountid is null");
            stmt.executeUpdate();
            stmt.close();

            // Count and Delete newly registered users (users w/ id that start
            // "ru:%":
            stmt = getStatement(conn, "delete from accountprofileejb where userid like 'ru:%'");
            stmt.executeUpdate();
            stmt.close();

            stmt = getStatement(conn, "delete from orderejb where account_accountid in (select accountid from accountejb a where a.profile_userid like 'ru:%')");
            stmt.executeUpdate();
            stmt.close();

            stmt = getStatement(conn,
                    "delete from holdingejb where account_accountid in (select accountid from accountejb a where a.profile_userid like 'ru:%')");
            stmt.executeUpdate();
            stmt.close();

            stmt = getStatement(conn, "delete from accountejb where profile_userid like 'ru:%'");
            int newUserCount = stmt.executeUpdate();
            runStatsData.setNewUserCount(newUserCount);
            stmt.close();

            // Count of trade users
            stmt = getStatement(conn, "select count(accountid) as \"tradeUserCount\" from accountejb a where a.profile_userid like 'uid:%'");
            rs = stmt.executeQuery();
            rs.next();
            int tradeUserCount = rs.getInt("tradeUserCount");
            runStatsData.setTradeUserCount(tradeUserCount);
            stmt.close();

            rs.close();
            // Count of trade stocks
            stmt = getStatement(conn, "select count(symbol) as \"tradeStockCount\" from quoteejb a where a.symbol like 's:%'");
            rs = stmt.executeQuery();
            rs.next();
            int tradeStockCount = rs.getInt("tradeStockCount");
            runStatsData.setTradeStockCount(tradeStockCount);
            stmt.close();

            // Count of trade users login, logout
            stmt = getStatement(conn,
                    "select sum(loginCount) as \"sumLoginCount\", sum(logoutCount) as \"sumLogoutCount\" from accountejb a where  a.profile_userID like 'uid:%'");
            rs = stmt.executeQuery();
            rs.next();
            int sumLoginCount = rs.getInt("sumLoginCount");
            int sumLogoutCount = rs.getInt("sumLogoutCount");
            runStatsData.setSumLoginCount(sumLoginCount);
            runStatsData.setSumLogoutCount(sumLogoutCount);
            stmt.close();

            rs.close();
            // Update logoutcount and loginCount back to zero

            stmt = getStatement(conn, "update accountejb set logoutCount=0,loginCount=0 where profile_userID like 'uid:%'");
            stmt.executeUpdate();
            stmt.close();

            // count holdings for trade users
            stmt = getStatement(conn, "select count(holdingid) as \"holdingCount\" from holdingejb h where h.account_accountid in "
                    + "(select accountid from accountejb a where a.profile_userid like 'uid:%')");

            rs = stmt.executeQuery();
            rs.next();
            int holdingCount = rs.getInt("holdingCount");
            runStatsData.setHoldingCount(holdingCount);
            stmt.close();
            rs.close();

            // count orders for trade users
            stmt = getStatement(conn, "select count(orderid) as \"orderCount\" from orderejb o where o.account_accountid in "
                    + "(select accountid from accountejb a where a.profile_userid like 'uid:%')");

            rs = stmt.executeQuery();
            rs.next();
            int orderCount = rs.getInt("orderCount");
            runStatsData.setOrderCount(orderCount);
            stmt.close();
            rs.close();

            // count orders by type for trade users
            stmt = getStatement(conn, "select count(orderid) \"buyOrderCount\"from orderejb o where (o.account_accountid in "
                    + "(select accountid from accountejb a where a.profile_userid like 'uid:%')) AND " + " (o.orderType='buy')");

            rs = stmt.executeQuery();
            rs.next();
            int buyOrderCount = rs.getInt("buyOrderCount");
            runStatsData.setBuyOrderCount(buyOrderCount);
            stmt.close();
            rs.close();

            // count orders by type for trade users
            stmt = getStatement(conn, "select count(orderid) \"sellOrderCount\"from orderejb o where (o.account_accountid in "
                    + "(select accountid from accountejb a where a.profile_userid like 'uid:%')) AND " + " (o.orderType='sell')");

            rs = stmt.executeQuery();
            rs.next();
            int sellOrderCount = rs.getInt("sellOrderCount");
            runStatsData.setSellOrderCount(sellOrderCount);
            stmt.close();
            rs.close();

            // Delete cancelled orders
            stmt = getStatement(conn, "delete from orderejb where orderStatus='cancelled'");
            int cancelledOrderCount = stmt.executeUpdate();
            runStatsData.setCancelledOrderCount(cancelledOrderCount);
            stmt.close();
            rs.close();

            // count open orders by type for trade users
            stmt = getStatement(conn, "select count(orderid) \"openOrderCount\"from orderejb o where (o.account_accountid in "
                    + "(select accountid from accountejb a where a.profile_userid like 'uid:%')) AND " + " (o.orderStatus='open')");

            rs = stmt.executeQuery();
            rs.next();
            int openOrderCount = rs.getInt("openOrderCount");
            runStatsData.setOpenOrderCount(openOrderCount);

            stmt.close();
            rs.close();
            // Delete orders for holding which have been purchased and sold
            stmt = getStatement(conn, "delete from orderejb where holding_holdingid is null");
            int deletedOrderCount = stmt.executeUpdate();
            runStatsData.setDeletedOrderCount(deletedOrderCount);
            stmt.close();
            rs.close();

            commit(conn);

            System.out.println("TradeDirect:reset Run stats data\n\n" + runStatsData);
        } catch (Exception e) {
            Log.error(e, "Failed to reset Trade");
            rollBack(conn, e);
            throw e;
        } finally {
            releaseConn(conn);
        }
        return runStatsData;

    }

    private void releaseConn(Connection conn) throws Exception {
        try {
            if (conn != null) {
                conn.close();
                if (Log.doTrace()) {
                    synchronized (lock) {
                        connCount--;
                    }
                    Log.trace("TradeDirect:releaseConn -- connection closed, connCount=" + connCount);
                }
            }
        } catch (Exception e) {
            Log.error("TradeDirect:releaseConnection -- failed to close connection", e);
        }
    }

    /*
     * Lookup the TradeData datasource
     */
    private void getDataSource() throws Exception {
        datasource = (DataSource) context.lookup(dsName);
    }

    /*
     * Allocate a new connection to the datasource
     */
    private static int connCount = 0;

    private static Integer lock = new Integer(0);

    private Connection getConn() throws Exception {

        Connection conn = null;
        if (datasource == null) {
            getDataSource();
        }
        conn = datasource.getConnection();      
        
        if (!this.inGlobalTxn) {
        	conn.setAutoCommit(false);
        }
        if (Log.doTrace()) {
            synchronized (lock) {
                connCount++;
            }
            Log.trace("TradeDirect:getConn -- new connection allocated, IsolationLevel=" + conn.getTransactionIsolation() + " connectionCount = " + connCount);
        }

        return conn;
    }

    public Connection getConnPublic() throws Exception {
        return getConn();
    }

    /*
     * Commit the provided connection if not under Global Transaction scope -
     * conn.commit() is not allowed in a global transaction. the txn manager
     * will perform the commit
     */
    private void commit(Connection conn) throws Exception {
        if (!inSession) {
            if ((getInGlobalTxn() == false) && (conn != null)) {
                conn.commit();
            }
        }
    }

    /*
     * Rollback the statement for the given connection
     */
    private void rollBack(Connection conn, Exception e) throws Exception {
        if (!inSession) {
            Log.log("TradeDirect:rollBack -- rolling back conn due to previously caught exception -- inGlobalTxn=" + getInGlobalTxn());
            if ((getInGlobalTxn() == false) && (conn != null)) {
                conn.rollback();
            } else {
                throw e; // Throw the exception
                // so the Global txn manager will rollBack
            }
        }
    }

    /*
     * Allocate a new prepared statment for this connection
     */
    private PreparedStatement getStatement(Connection conn, String sql) throws Exception {
        return conn.prepareStatement(sql);
    }

    private PreparedStatement getStatement(Connection conn, String sql, int type, int concurrency) throws Exception {
        return conn.prepareStatement(sql, type, concurrency);
    }

    private static final String createQuoteSQL = "insert into quoteejb " + "( symbol, companyName, volume, price, open1, low, high, change1 ) "
            + "VALUES (  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  )";

    private static final String createAccountSQL = "insert into accountejb "
            + "( accountid, creationDate, openBalance, balance, lastLogin, loginCount, logoutCount, profile_userid) "
            + "VALUES (  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  )";

    private static final String createAccountProfileSQL = "insert into accountprofileejb " + "( userid, passwd, fullname, address, email, creditcard ) "
            + "VALUES (  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  )";

    private static final String createHoldingSQL = "insert into holdingejb "
            + "( holdingid, purchaseDate, purchasePrice, quantity, quote_symbol, account_accountid ) " + "VALUES (  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ? )";

    private static final String createOrderSQL = "insert into orderejb "
            + "( orderid, ordertype, orderstatus, opendate, quantity, price, orderfee, account_accountid,  holding_holdingid, quote_symbol) "
            + "VALUES (  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  ,  ?  , ? , ? , ?)";

    private static final String removeHoldingSQL = "delete from holdingejb where holdingid = ?";

    private static final String removeHoldingFromOrderSQL = "update orderejb set holding_holdingid=null where holding_holdingid = ?";

    private static final String updateAccountProfileSQL = "update accountprofileejb set " + "passwd = ?, fullname = ?, address = ?, email = ?, creditcard = ? "
            + "where userid = (select profile_userid from accountejb a " + "where a.profile_userid=?)";

    private static final String loginSQL = "update accountejb set lastLogin=?, logincount=logincount+1 " + "where profile_userid=?";

    private static final String logoutSQL = "update accountejb set logoutcount=logoutcount+1 " + "where profile_userid=?";

    private static final String getAccountSQL = "select * from accountejb a where a.accountid = ?";

    private static final String getAccountProfileSQL = "select * from accountprofileejb ap where ap.userid = "
            + "(select profile_userid from accountejb a where a.profile_userid=?)";

    private static final String getAccountProfileForAccountSQL = "select * from accountprofileejb ap where ap.userid = "
            + "(select profile_userid from accountejb a where a.accountid=?)";

    private static final String getAccountForUserSQL = "select * from accountejb a where a.profile_userid = "
            + "( select userid from accountprofileejb ap where ap.userid = ?)";

    private static final String getHoldingSQL = "select * from holdingejb h where h.holdingid = ?";

    private static final String getHoldingsForUserSQL = "select * from holdingejb h where h.account_accountid = "
            + "(select a.accountid from accountejb a where a.profile_userid = ?)";

    private static final String getOrderSQL = "select * from orderejb o where o.orderid = ?";

    private static final String getOrdersByUserSQL = "select * from orderejb o where o.account_accountid = "
            + "(select a.accountid from accountejb a where a.profile_userid = ?)";

    private static final String getClosedOrdersSQL = "select * from orderejb o " + "where o.orderstatus = 'closed' AND o.account_accountid = "
            + "(select a.accountid from accountejb a where a.profile_userid = ?)";

    private static final String getQuoteSQL = "select * from quoteejb q where q.symbol=?";

    private static final String getAllQuotesSQL = "select * from quoteejb q";

    private static final String getQuoteForUpdateSQL = "select * from quoteejb q where q.symbol=? For Update";

    private static final String getTSIAQuotesOrderByChangeSQL = "select * from quoteejb q order by q.change1";

    private static final String getTSIASQL = "select SUM(price)/count(*) as TSIA from quoteejb q ";

    private static final String getOpenTSIASQL = "select SUM(open1)/count(*) as openTSIA from quoteejb q ";

    private static final String getTSIATotalVolumeSQL = "select SUM(volume) as totalVolume from quoteejb q ";

    private static final String creditAccountBalanceSQL = "update accountejb set " + "balance = balance + ? " + "where accountid = ?";

    private static final String updateOrderStatusSQL = "update orderejb set " + "orderstatus = ?, completiondate = ? " + "where orderid = ?";

    private static final String updateOrderHoldingSQL = "update orderejb set " + "holding_holdingID = ? " + "where orderid = ?";

    private static final String updateQuotePriceVolumeSQL = "update quoteejb set " + "price = ?, change1 = ?, volume = ? " + "where symbol = ?";

    private static boolean initialized = false;

    public static synchronized void init() {
        if (initialized) {
            return;
        }
        if (Log.doTrace()) {
            Log.trace("TradeDirect:init -- *** initializing");
        }
        try {
            if (Log.doTrace()) {
                Log.trace("TradeDirect: init");
            }
            context = new InitialContext();
            datasource = (DataSource) context.lookup(dsName);
        } catch (Exception e) {
            Log.error("TradeDirect:init -- error on JNDI lookups of DataSource -- TradeDirect will not work", e);
            return;
        }
        
        try {
            qConnFactory = (ConnectionFactory) context.lookup("java:comp/env/jms/QueueConnectionFactory");
        } catch (Exception e) {
            Log.error("TradeDirect:init  Unable to locate QueueConnectionFactory.\n\t -- Asynchronous mode will not work correctly and Quote Price change publishing will be disabled");
            TradeConfig.setPublishQuotePriceChange(false);
        }

        try {
            brokerQueue = (Queue) context.lookup("java:comp/env/jms/TradeBrokerQueue");
        } catch (Exception e) {
            try {
                brokerQueue = (Queue) context.lookup("jms/TradeBrokerQueue");
            } catch (Exception e2) {
                Log.error("TradeDirect:init  Unable to locate TradeBrokerQueue.\n\t -- Asynchronous mode will not work correctly and Quote Price change publishing will be disabled");
                TradeConfig.setPublishQuotePriceChange(false);
            }
        }

        try {
            tConnFactory = (ConnectionFactory) context.lookup("java:comp/env/jms/TopicConnectionFactory");
        } catch (Exception e) {
            Log.error("TradeDirect:init  Unable to locate TopicConnectionFactory.\n\t -- Asynchronous mode will not work correctly and Quote Price change publishing will be disabled");
            TradeConfig.setPublishQuotePriceChange(false);
        }

        try {
            streamerTopic = (Topic) context.lookup("java:comp/env/jms/TradeStreamerTopic");
        } catch (Exception e) {
            try {
                streamerTopic = (Topic) context.lookup("jms/TradeStreamerTopic");
            } catch (Exception e2) {
                Log.error("TradeDirect:init  Unable to locate TradeStreamerTopic.\n\t -- Asynchronous mode will not work correctly and Quote Price change publishing will be disabled");
                TradeConfig.setPublishQuotePriceChange(false);
            }
        }
        
        		
        if (Log.doTrace()) {
            Log.trace("TradeDirect:init -- +++ initialized");
        }

        initialized = true;
    }

    public static void destroy() {
        try {
            if (!initialized) {
                return;
            }
            Log.trace("TradeDirect:destroy");
        } catch (Exception e) {
            Log.error("TradeDirect:destroy", e);
        }
    }

    private static InitialContext context;

    private static ConnectionFactory qConnFactory;

    private static Queue brokerQueue;

    private static ConnectionFactory tConnFactory;

    private static Topic streamerTopic;
     
    /**
     * Gets the inGlobalTxn
     *
     * @return Returns a boolean
     */
    private boolean getInGlobalTxn() {
        return inGlobalTxn;
    }

    /**
     * Sets the inGlobalTxn
     *
     * @param inGlobalTxn
     *            The inGlobalTxn to set
     */
    private void setInGlobalTxn(boolean inGlobalTxn) {
        this.inGlobalTxn = inGlobalTxn;
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/direct/TradeDirect.java:to.<init>
// Node: getQuoteID
// Node: getHoldingID
// Node: getOrderType
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
package com.ibm.websphere.samples.daytrader.beans;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.Iterator;

import javax.json.Json;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;

import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.FinancialUtils;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

public class MarketSummaryDataBean implements Serializable {

    private static final long serialVersionUID = 650652242288745600L;
    private BigDecimal TSIA; /* Trade Stock Index Average */
    private BigDecimal openTSIA; /* Trade Stock Index Average at the open */
    private double volume; /* volume of shares traded */
    private Collection<QuoteDataBean> topGainers; /*
                                                   * Collection of top gaining
                                                   * stocks
                                                   */
    private Collection<QuoteDataBean> topLosers; /*
                                                  * Collection of top losing
                                                  * stocks
                                                  */
    // FUTURE private Collection topVolume; /* Collection of top stocks by
    // volume */
    private Date summaryDate; /* Date this summary was taken */

    // cache the gainPercent once computed for this bean
    private BigDecimal gainPercent = null;

    public MarketSummaryDataBean() {
    }

    public MarketSummaryDataBean(BigDecimal TSIA, BigDecimal openTSIA, double volume, Collection<QuoteDataBean> topGainers, Collection<QuoteDataBean> topLosers// , Collection topVolume
    ) {
        setTSIA(TSIA);
        setOpenTSIA(openTSIA);
        setVolume(volume);
        setTopGainers(topGainers);
        setTopLosers(topLosers);
        setSummaryDate(new java.sql.Date(System.currentTimeMillis()));
        gainPercent = FinancialUtils.computeGainPercent(getTSIA(), getOpenTSIA());

    }

    public static MarketSummaryDataBean getRandomInstance() {
        Collection<QuoteDataBean> gain = new ArrayList<QuoteDataBean>();
        Collection<QuoteDataBean> lose = new ArrayList<QuoteDataBean>();

        for (int ii = 0; ii < 5; ii++) {
            QuoteDataBean quote1 = QuoteDataBean.getRandomInstance();
            QuoteDataBean quote2 = QuoteDataBean.getRandomInstance();

            gain.add(quote1);
            lose.add(quote2);
        }

        return new MarketSummaryDataBean(TradeConfig.rndBigDecimal(1000000.0f), TradeConfig.rndBigDecimal(1000000.0f), TradeConfig.rndQuantity(), gain, lose);
    }

    @Override
    public String toString() {
        String ret = "\n\tMarket Summary at: " + getSummaryDate() + "\n\t\t        TSIA:" + getTSIA() + "\n\t\t    openTSIA:" + getOpenTSIA()
                + "\n\t\t        gain:" + getGainPercent() + "\n\t\t      volume:" + getVolume();

        if ((getTopGainers() == null) || (getTopLosers() == null)) {
            return ret;
        }
        ret += "\n\t\t   Current Top Gainers:";
        Iterator<QuoteDataBean> it = getTopGainers().iterator();
        while (it.hasNext()) {
            QuoteDataBean quoteData = it.next();
            ret += ("\n\t\t\t" + quoteData.toString());
        }
        ret += "\n\t\t   Current Top Losers:";
        it = getTopLosers().iterator();
        while (it.hasNext()) {
            QuoteDataBean quoteData = it.next();
            ret += ("\n\t\t\t" + quoteData.toString());
        }
        return ret;
    }

    public String toHTML() {
        String ret = "<BR>Market Summary at: " + getSummaryDate() + "<LI>        TSIA:" + getTSIA() + "</LI>" + "<LI>    openTSIA:" + getOpenTSIA() + "</LI>"
                + "<LI>      volume:" + getVolume() + "</LI>";
        if ((getTopGainers() == null) || (getTopLosers() == null)) {
            return ret;
        }
        ret += "<BR> Current Top Gainers:";
        Iterator<QuoteDataBean> it = getTopGainers().iterator();

        while (it.hasNext()) {
            QuoteDataBean quoteData = it.next();
            ret += ("<LI>" + quoteData.toString() + "</LI>");
        }
        ret += "<BR>   Current Top Losers:";
        it = getTopLosers().iterator();
        while (it.hasNext()) {
            QuoteDataBean quoteData = it.next();
            ret += ("<LI>" + quoteData.toString() + "</LI>");
        }
        return ret;
    }

    public JsonObject toJSON() {
        
        JsonObjectBuilder jObjectBuilder = Json.createObjectBuilder();
        
        int i = 1;
        for (Iterator<QuoteDataBean> iterator = topGainers.iterator(); iterator.hasNext();) {
            QuoteDataBean quote = iterator.next();

            jObjectBuilder.add("gainer" + i + "_stock",quote.getSymbol());
            jObjectBuilder.add("gainer" + i + "_price","$" + quote.getPrice());
            jObjectBuilder.add("gainer" + i + "_change",quote.getChange());
            i++;
        }

        i = 1;
        for (Iterator<QuoteDataBean> iterator = topLosers.iterator(); iterator.hasNext();) {
            QuoteDataBean quote = iterator.next();

            jObjectBuilder.add("loser" + i + "_stock",quote.getSymbol());
            jObjectBuilder.add("loser" + i + "_price","$" + quote.getPrice());
            jObjectBuilder.add("loser" + i + "_change",quote.getChange());
            i++;
        }

        jObjectBuilder.add("tsia", TSIA);
        jObjectBuilder.add("volume",volume);
        jObjectBuilder.add("date", summaryDate.toString());

        return jObjectBuilder.build();
        
    }

    public void print() {
        Log.log(this.toString());
    }

    public BigDecimal getGainPercent() {
        if (gainPercent == null) {
            gainPercent = FinancialUtils.computeGainPercent(getTSIA(), getOpenTSIA());
        }
        return gainPercent;
    }

    /**
     * Gets the tSIA
     *
     * @return Returns a BigDecimal
     */
    public BigDecimal getTSIA() {
        return TSIA;
    }

    /**
     * Sets the tSIA
     *
     * @param tSIA
     *            The tSIA to set
     */
    public void setTSIA(BigDecimal tSIA) {
        TSIA = tSIA;
    }

    /**
     * Gets the openTSIA
     *
     * @return Returns a BigDecimal
     */
    public BigDecimal getOpenTSIA() {
        return openTSIA;
    }

    /**
     * Sets the openTSIA
     *
     * @param openTSIA
     *            The openTSIA to set
     */
    public void setOpenTSIA(BigDecimal openTSIA) {
        this.openTSIA = openTSIA;
    }

    /**
     * Gets the volume
     *
     * @return Returns a BigDecimal
     */
    public double getVolume() {
        return volume;
    }

    /**
     * Sets the volume
     *
     * @param volume
     *            The volume to set
     */
    public void setVolume(double volume) {
        this.volume = volume;
    }

    /**
     * Gets the topGainers
     *
     * @return Returns a Collection
     */
    public Collection<QuoteDataBean> getTopGainers() {
        return topGainers;
    }

    /**
     * Sets the topGainers
     *
     * @param topGainers
     *            The topGainers to set
     */
    public void setTopGainers(Collection<QuoteDataBean> topGainers) {
        this.topGainers = topGainers;
    }

    /**
     * Gets the topLosers
     *
     * @return Returns a Collection
     */
    public Collection<QuoteDataBean> getTopLosers() {
        return topLosers;
    }

    /**
     * Sets the topLosers
     *
     * @param topLosers
     *            The topLosers to set
     */
    public void setTopLosers(Collection<QuoteDataBean> topLosers) {
        this.topLosers = topLosers;
    }

    /**
     * Gets the summaryDate
     *
     * @return Returns a Date
     */
    public Date getSummaryDate() {
        return summaryDate;
    }

    /**
     * Sets the summaryDate
     *
     * @param summaryDate
     *            The summaryDate to set
     */
    public void setSummaryDate(Date summaryDate) {
        this.summaryDate = summaryDate;
    }

}

// Node: getSummaryDate
// Node: getTopGainers
// Node: getTopLosers
// Node: createObjectBuilder
// Node: build
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


// Node: getPage
// Node: trim
// Node: getDisplayOrderAlerts
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

import java.util.Collection;
import java.util.Iterator;
import java.util.logging.Level;
import java.util.logging.Logger;



public class Log {
    
    private final static Logger log = Logger.getLogger("daytrader");
    

    // A general purpose, high performance logging, tracing, statistic service

    public static void log(String message) {
       log.log(Level.INFO, message);
    }

    public static void log(String msg1, String msg2) {
        log(msg1 + msg2);
    }

    public static void log(String msg1, String msg2, String msg3) {
        log(msg1 + msg2 + msg3);
    }

    public static void error(String message) {
        message = "Error: " + message;
        log.severe(message);
    }

    public static void error(String message, Throwable e) {
        error(message + "\n\t" + e.toString());
        e.printStackTrace(System.out);
    }

    public static void error(String msg1, String msg2, Throwable e) {
        error(msg1 + "\n" + msg2 + "\n\t", e);
    }

    public static void error(String msg1, String msg2, String msg3, Throwable e) {
        error(msg1 + "\n" + msg2 + "\n" + msg3 + "\n\t", e);
    }

    public static void error(Throwable e, String message) {
        error(message + "\n\t", e);
        e.printStackTrace(System.out);
    }

    public static void error(Throwable e, String msg1, String msg2) {
        error(msg1 + "\n" + msg2 + "\n\t", e);
    }

    public static void error(Throwable e, String msg1, String msg2, String msg3) {
        error(msg1 + "\n" + msg2 + "\n" + msg3 + "\n\t", e);
    }

    public static void trace(String message) {
        log.log(Level.FINE, message + " threadID=" + Thread.currentThread());
    }

    public static void trace(String message, Object parm1) {
        trace(message + "(" + parm1 + ")");
    }

    public static void trace(String message, Object parm1, Object parm2) {
        trace(message + "(" + parm1 + ", " + parm2 + ")");
    }

    public static void trace(String message, Object parm1, Object parm2, Object parm3) {
        trace(message + "(" + parm1 + ", " + parm2 + ", " + parm3 + ")");
    }

    public static void trace(String message, Object parm1, Object parm2, Object parm3, Object parm4) {
        trace(message + "(" + parm1 + ", " + parm2 + ", " + parm3 + ")" + ", " + parm4);
    }

    public static void trace(String message, Object parm1, Object parm2, Object parm3, Object parm4, Object parm5) {
        trace(message + "(" + parm1 + ", " + parm2 + ", " + parm3 + ")" + ", " + parm4 + ", " + parm5);
    }

    public static void trace(String message, Object parm1, Object parm2, Object parm3, Object parm4, Object parm5, Object parm6) {
        trace(message + "(" + parm1 + ", " + parm2 + ", " + parm3 + ")" + ", " + parm4 + ", " + parm5 + ", " + parm6);
    }

    public static void trace(String message, Object parm1, Object parm2, Object parm3, Object parm4, Object parm5, Object parm6, Object parm7) {
        trace(message + "(" + parm1 + ", " + parm2 + ", " + parm3 + ")" + ", " + parm4 + ", " + parm5 + ", " + parm6 + ", " + parm7);
    }

    public static void traceEnter(String message) {
        log.log(Level.FINE,"Method enter --" + message);
    }

    public static void traceExit(String message) {
        log.log(Level.FINE,"Method exit  --" + message);
    }

    public static void stat(String message) {
        log(message);
    }

    public static void debug(String message) {
        log.log(Level.INFO,message);
    }

    public static void print(String message) {
        log(message);
    }

    public static void printObject(Object o) {
        log("\t" + o.toString());
    }

    public static void printCollection(Collection<?> c) {
        log("\t---Log.printCollection -- collection size=" + c.size());
        Iterator<?> it = c.iterator();

        while (it.hasNext()) {
            log("\t\t" + it.next().toString());
        }
        log("\t---Log.printCollection -- complete");
    }

    public static void printCollection(String message, Collection<?> c) {
        log(message);
        printCollection(c);
    }

    public static boolean doActionTrace() {
        return getTrace() || getActionTrace();
    }

    public static boolean doTrace() {
        return getTrace();
    }

    public static boolean doDebug() {
        return true;
    }

    public static boolean doStat() {
        return true;
    }

    /**
     * Gets the trace
     *
     * @return Returns a boolean
     */
    public static boolean getTrace() {
        return TradeConfig.getTrace();
    }

    /**
     * Gets the trace value for Trade actions only
     *
     * @return Returns a boolean
     */
    public static boolean getActionTrace() {
        return TradeConfig.getActionTrace();
    }

    /**
     * Sets the trace
     *
     * @param trace
     *            The trace to set
     */
    public static void setTrace(boolean traceValue) {
        TradeConfig.setTrace(traceValue);
    }

    /**
     * Sets the trace value for Trade actions only
     *
     * @param trace
     *            The trace to set
     */
    public static void setActionTrace(boolean traceValue) {
        TradeConfig.setActionTrace(traceValue);
    }
}


// Node: printCollection
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

// Node: listIterator
// Node: KeyBlockIterator
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
import java.util.Collection;
import java.util.Iterator;

import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;

public class FinancialUtils {

    public static final int ROUND = BigDecimal.ROUND_HALF_UP;
    public static final int SCALE = 2;
    public static final BigDecimal ZERO = (new BigDecimal(0.00)).setScale(SCALE);
    public static final BigDecimal ONE = (new BigDecimal(1.00)).setScale(SCALE);
    public static final BigDecimal HUNDRED = (new BigDecimal(100.00)).setScale(SCALE);

    public static BigDecimal computeGain(BigDecimal currentBalance, BigDecimal openBalance) {
        return currentBalance.subtract(openBalance).setScale(SCALE);
    }

    public static BigDecimal computeGainPercent(BigDecimal currentBalance, BigDecimal openBalance) {
        if (openBalance.doubleValue() == 0.0) {
            return ZERO;
        }
        BigDecimal gainPercent = currentBalance.divide(openBalance, ROUND).subtract(ONE).multiply(HUNDRED);
        return gainPercent;
    }

    public static BigDecimal computeHoldingsTotal(Collection<?> holdingDataBeans) {
        BigDecimal holdingsTotal = new BigDecimal(0.0).setScale(SCALE);
        if (holdingDataBeans == null) {
            return holdingsTotal;
        }
        Iterator<?> it = holdingDataBeans.iterator();
        while (it.hasNext()) {
            HoldingDataBean holdingData = (HoldingDataBean) it.next();
            BigDecimal total = holdingData.getPurchasePrice().multiply(new BigDecimal(holdingData.getQuantity()));
            holdingsTotal = holdingsTotal.add(total);
        }
        return holdingsTotal.setScale(SCALE);
    }

    public static String printGainHTML(BigDecimal gain) {
        String htmlString, arrow;
        if (gain.doubleValue() < 0.0) {
            htmlString = "<FONT color=\"#ff0000\">";
            arrow = "arrowdown.gif";
        } else {
            htmlString = "<FONT color=\"#009900\">";
            arrow = "arrowup.gif";
        }

        htmlString += gain.setScale(SCALE, ROUND) + "</FONT><IMG src=\"images/" + arrow + "\" width=\"10\" height=\"10\" border=\"0\"></IMG>";
        return htmlString;
    }

    public static String printChangeHTML(double change) {
        String htmlString, arrow;
        if (change < 0.0) {
            htmlString = "<FONT color=\"#ff0000\">";
            arrow = "arrowdown.gif";
        } else {
            htmlString = "<FONT color=\"#009900\">";
            arrow = "arrowup.gif";
        }

        htmlString += change + "</FONT><IMG src=\"images/" + arrow + "\" width=\"10\" height=\"10\" border=\"0\"></IMG>";
        return htmlString;
    }

    public static String printGainPercentHTML(BigDecimal gain) {
        String htmlString, arrow;
        if (gain.doubleValue() < 0.0) {
            htmlString = "(<B><FONT color=\"#ff0000\">";
            arrow = "arrowdown.gif";
        } else {
            htmlString = "(<B><FONT color=\"#009900\">+";
            arrow = "arrowup.gif";
        }

        htmlString += gain.setScale(SCALE, ROUND);
        htmlString += "%</FONT></B>)<IMG src=\"images/" + arrow + "\" width=\"10\" height=\"10\" border=\"0\"></IMG>";
        return htmlString;
    }

    public static String printQuoteLink(String symbol) {
        return "<A href=\"app?action=quotes&symbols=" + symbol + "\">" + symbol + "</A>";
    }

}

// Node: getPurchasePrice
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


// Node: getPurchaseDate
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

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.NamedNativeQueries;
import javax.persistence.NamedNativeQuery;
import javax.persistence.NamedQueries;
import javax.persistence.NamedQuery;
import javax.persistence.Table;
import javax.validation.constraints.NotNull;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Entity(name = "quoteejb")
@Table(name = "quoteejb")
@NamedQueries({
        @NamedQuery(name = "quoteejb.allQuotes", query = "SELECT q FROM quoteejb q")})
@NamedNativeQueries({ @NamedNativeQuery(name = "quoteejb.quoteForUpdate", query = "select * from quoteejb q where q.symbol=? for update", resultClass = com.ibm.websphere.samples.daytrader.entities.QuoteDataBean.class) })
public class QuoteDataBean implements Serializable {

    /* Accessor methods for persistent fields */

    private static final long serialVersionUID = 1847932261895838791L;

    @Id
    @NotNull
    @Column(name = "SYMBOL", nullable = false)
    private String symbol; /* symbol */

    @Column(name = "COMPANYNAME")
    private String companyName; /* companyName */

    @NotNull
    @Column(name = "VOLUME", nullable = false)
    private double volume; /* volume */

    @Column(name = "PRICE")
    private BigDecimal price; /* price */

    @Column(name = "OPEN1")
    private BigDecimal open1; /* open1 price */

    @Column(name = "LOW")
    private BigDecimal low; /* low price */

    @Column(name = "HIGH")
    private BigDecimal high; /* high price */

    @NotNull
    @Column(name = "CHANGE1", nullable = false)
    private double change1; /* price change */

    /* Accessor methods for relationship fields are not kept in the DataBean */

    public QuoteDataBean() {
    }

    public QuoteDataBean(String symbol, String companyName, double volume, BigDecimal price, BigDecimal open, BigDecimal low, BigDecimal high, double change) {
        setSymbol(symbol);
        setCompanyName(companyName);
        setVolume(volume);
        setPrice(price);
        setOpen(open);
        setLow(low);
        setHigh(high);
        setChange(change);
    }

    public static QuoteDataBean getRandomInstance() {
        return new QuoteDataBean(TradeConfig.rndSymbol(), // symbol
                TradeConfig.rndSymbol() + " Incorporated", // Company Name
                TradeConfig.rndFloat(100000), // volume
                TradeConfig.rndBigDecimal(1000.0f), // price
                TradeConfig.rndBigDecimal(1000.0f), // open1
                TradeConfig.rndBigDecimal(1000.0f), // low
                TradeConfig.rndBigDecimal(1000.0f), // high
                TradeConfig.rndFloat(100000) // volume
        );
    }

    // Create a "zero" value quoteDataBean for the given symbol
    public QuoteDataBean(String symbol) {
        setSymbol(symbol);
    }

    @Override
    public String toString() {
        return "\n\tQuote Data for: " + getSymbol() + "\n\t\t companyName: " + getCompanyName() + "\n\t\t      volume: " + getVolume() + "\n\t\t       price: "
                + getPrice() + "\n\t\t        open1: " + getOpen() + "\n\t\t         low: " + getLow() + "\n\t\t        high: " + getHigh()
                + "\n\t\t      change1: " + getChange();
    }

    public String toHTML() {
        return "<BR>Quote Data for: " + getSymbol() + "<LI> companyName: " + getCompanyName() + "</LI>" + "<LI>      volume: " + getVolume() + "</LI>"
                + "<LI>       price: " + getPrice() + "</LI>" + "<LI>        open1: " + getOpen() + "</LI>" + "<LI>         low: " + getLow() + "</LI>"
                + "<LI>        high: " + getHigh() + "</LI>" + "<LI>      change1: " + getChange() + "</LI>";
    }

    public void print() {
        Log.log(this.toString());
    }

    public String getSymbol() {
        return symbol;
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public String getCompanyName() {
        return companyName;
    }

    public void setCompanyName(String companyName) {
        this.companyName = companyName;
    }

    public BigDecimal getPrice() {
        return price;
    }

    public void setPrice(BigDecimal price) {
        this.price = price;
    }

    public BigDecimal getOpen() {
        return open1;
    }

    public void setOpen(BigDecimal open) {
        this.open1 = open;
    }

    public BigDecimal getLow() {
        return low;
    }

    public void setLow(BigDecimal low) {
        this.low = low;
    }

    public BigDecimal getHigh() {
        return high;
    }

    public void setHigh(BigDecimal high) {
        this.high = high;
    }

    public double getChange() {
        return change1;
    }

    public void setChange(double change) {
        this.change1 = change;
    }

    public double getVolume() {
        return volume;
    }

    public void setVolume(double volume) {
        this.volume = volume;
    }

    @Override
    public int hashCode() {
        int hash = 0;
        hash += (this.symbol != null ? this.symbol.hashCode() : 0);
        return hash;
    }

    @Override
    public boolean equals(Object object) {
        
        if (!(object instanceof QuoteDataBean)) {
            return false;
        }
        QuoteDataBean other = (QuoteDataBean) object;
        if (this.symbol != other.symbol && (this.symbol == null || !this.symbol.equals(other.symbol))) {
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


// Node: getOpenDate
// Node: getCompletionDate
// Node: getSession
// Node: getAttribute
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
import java.util.Collection;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.FilterConfig;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.annotation.WebFilter;
import javax.servlet.http.HttpServletRequest;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.TradeServices;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@WebFilter(filterName = "OrdersAlertFilter", urlPatterns = "/app")
public class OrdersAlertFilter implements Filter {

    /**
     * Constructor for CompletedOrdersAlertFilter
     */
    public OrdersAlertFilter() {
        super();
    }

    /**
     * @see Filter#init(FilterConfig)
     */
    private FilterConfig filterConfig = null;

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        this.filterConfig = filterConfig;
    }

    /**
     * @see Filter#doFilter(ServletRequest, ServletResponse, FilterChain)
     */
    @Override
    public void doFilter(ServletRequest req, ServletResponse resp, FilterChain chain) throws IOException, ServletException {
        if (filterConfig == null) {
            return;
        }

        if (TradeConfig.getDisplayOrderAlerts() == true) {

            try {
                String action = req.getParameter("action");
                if (action != null) {
                    action = action.trim();
                    if ((action.length() > 0) && (!action.equals("logout"))) {
                        String userID;
                        if (action.equals("login")) {
                            userID = req.getParameter("uid");
                        } else {
                            userID = (String) ((HttpServletRequest) req).getSession().getAttribute("uidBean");
                        }

                        if ((userID != null) && (userID.trim().length() > 0)) {
                            TradeServices tAction = null;
                            tAction = new TradeAction();
                            Collection<?> closedOrders = tAction.getClosedOrders(userID);
                            if ((closedOrders != null) && (closedOrders.size() > 0)) {
                                req.setAttribute("closedOrders", closedOrders);
                            }
                            if (Log.doTrace()) {
                                Log.printCollection("OrderAlertFilter: userID=" + userID + " closedOrders=", closedOrders);
                            }
                        }
                    }
                }
            } catch (Exception e) {
                Log.error(e, "OrdersAlertFilter - Error checking for closedOrders");
            }
        }

        chain.doFilter(req, resp/* wrapper */);
    }

    /**
     * @see Filter#destroy()
     */
    @Override
    public void destroy() {
        this.filterConfig = null;
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/OrdersAlertFilter.java:OrdersAlertFilter.<init>
// Node: OrdersAlertFilter
// Node: TradeServletAction
// Node: doWelcome
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

// Node: doLogin
// Node: doRegister
// Node: doQuotes
// Node: doBuy
// Node: doSell
// Node: doPortfolio
// Node: doLogout
// Node: doHome
// Node: doAccount
// Node: doAccountUpdate
// Node: doMarketSummary
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
import java.util.ArrayList;
import java.util.Collection;
import java.util.Iterator;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.TradeServices;
import com.ibm.websphere.samples.daytrader.entities.AccountDataBean;
import com.ibm.websphere.samples.daytrader.entities.AccountProfileDataBean;
import com.ibm.websphere.samples.daytrader.entities.HoldingDataBean;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * TradeServletAction provides servlet specific client side access to each of
 * the Trade brokerage user operations. These include login, logout, buy, sell,
 * getQuote, etc. TradeServletAction manages a web interface to Trade handling
 * HttpRequests/HttpResponse objects and forwarding results to the appropriate
 * JSP page for the web interface. TradeServletAction invokes
 * {@link TradeAction} methods to actually perform each trading operation.
 *
 */
public class TradeServletAction {

    private TradeServices tAction = null;

    TradeServletAction() {
        tAction = new TradeAction();
    }

    /**
     * Display User Profile information such as address, email, etc. for the
     * given Trader Dispatch to the Trade Account JSP for display
     *
     * @param userID
     *            The User to display profile info
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @param results
     *            A short description of the results/success of this web request
     *            provided on the web page
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doAccount(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String results) throws javax.servlet.ServletException,
            java.io.IOException {
        try {

            AccountDataBean accountData = tAction.getAccountData(userID);
            AccountProfileDataBean accountProfileData = tAction.getAccountProfileData(userID);
            Collection<?> orderDataBeans = (TradeConfig.getLongRun() ? new ArrayList<Object>() : (Collection<?>) tAction.getOrders(userID));

            req.setAttribute("accountData", accountData);
            req.setAttribute("accountProfileData", accountProfileData);
            req.setAttribute("orderDataBeans", orderDataBeans);
            req.setAttribute("results", results);
            requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.ACCOUNT_PAGE));
        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // forward them to another page rather than throw a 500
            req.setAttribute("results", results + "could not find account for userID = " + userID);
            requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.HOME_PAGE));
            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error("TradeServletAction.doAccount(...)", "illegal argument, information should be in exception string", e);
        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.doAccount(...)" + " exception user =" + userID, e);
        }

    }

    /**
     * Update User Profile information such as address, email, etc. for the
     * given Trader Dispatch to the Trade Account JSP for display If any in put
     * is incorrect revert back to the account page w/ an appropriate message
     *
     * @param userID
     *            The User to upddate profile info
     * @param password
     *            The new User password
     * @param cpassword
     *            Confirm password
     * @param fullname
     *            The new User fullname info
     * @param address
     *            The new User address info
     * @param cc
     *            The new User credit card info
     * @param email
     *            The new User email info
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doAccountUpdate(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String password, String cpassword,
            String fullName, String address, String creditcard, String email) throws javax.servlet.ServletException, java.io.IOException {
        String results = "";

        // First verify input data
        boolean doUpdate = true;
        if (password.equals(cpassword) == false) {
            results = "Update profile error: passwords do not match";
            doUpdate = false;
        } else if (password.length() <= 0 || fullName.length() <= 0 || address.length() <= 0 || creditcard.length() <= 0 || email.length() <= 0) {
            results = "Update profile error: please fill in all profile information fields";
            doUpdate = false;
        }
        AccountProfileDataBean accountProfileData = new AccountProfileDataBean(userID, password, fullName, address, email, creditcard);
        try {
            if (doUpdate) {
                accountProfileData = tAction.updateAccountProfile(accountProfileData);
                results = "Account profile update successful";
            }

        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // forward them to another page rather than throw a 500
            req.setAttribute("results", results + "invalid argument, check userID is correct, and the database is populated" + userID);
            Log.error(e, "TradeServletAction.doAccount(...)", "illegal argument, information should be in exception string",
                    "treating this as a user error and forwarding on to a new page");
        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.doAccountUpdate(...)" + " exception user =" + userID, e);
        }
        doAccount(ctx, req, resp, userID, results);
    }

    /**
     * Buy a new holding of shares for the given trader Dispatch to the Trade
     * Portfolio JSP for display
     *
     * @param userID
     *            The User buying shares
     * @param symbol
     *            The stock to purchase
     * @param amount
     *            The quantity of shares to purchase
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doBuy(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String symbol, String quantity) throws ServletException,
            IOException {

        String results = "";

        try {
            OrderDataBean orderData = tAction.buy(userID, symbol, new Double(quantity).doubleValue(), TradeConfig.orderProcessingMode);

            req.setAttribute("orderData", orderData);
            req.setAttribute("results", results);
        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // forward them to another page rather than throw a 500
            req.setAttribute("results", results + "illegal argument:");
            requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.HOME_PAGE));
            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error(e, "TradeServletAction.doBuy(...)", "illegal argument. userID = " + userID, "symbol = " + symbol);
        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.buy(...)" + " exception buying stock " + symbol + " for user " + userID, e);
        }
        requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.ORDER_PAGE));
    }

    /**
     * Create the Trade Home page with personalized information such as the
     * traders account balance Dispatch to the Trade Home JSP for display
     *
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @param results
     *            A short description of the results/success of this web request
     *            provided on the web page
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doHome(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String results) throws javax.servlet.ServletException,
            java.io.IOException {

        try {
            AccountDataBean accountData = tAction.getAccountData(userID);
            Collection<?> holdingDataBeans = tAction.getHoldings(userID);

            // Edge Caching:
            // Getting the MarketSummary has been moved to the JSP
            // MarketSummary.jsp. This makes the MarketSummary a
            // standalone "fragment", and thus is a candidate for
            // Edge caching.
            // marketSummaryData = tAction.getMarketSummary();

            req.setAttribute("accountData", accountData);
            req.setAttribute("holdingDataBeans", holdingDataBeans);
            // See Edge Caching above
            // req.setAttribute("marketSummaryData", marketSummaryData);
            req.setAttribute("results", results);
        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // forward them to another page rather than throw a 500
            req.setAttribute("results", results + "check userID = " + userID + " and that the database is populated");
            requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.HOME_PAGE));
            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error("TradeServletAction.doHome(...)" + "illegal argument, information should be in exception string"
                    + "treating this as a user error and forwarding on to a new page", e);
        } catch (javax.ejb.FinderException e) {
            // this is a user error so I will
            // forward them to another page rather than throw a 500
            req.setAttribute("results", results + "\nCould not find account for + " + userID);
            // requestDispatch(ctx, req, resp,
            // TradeConfig.getPage(TradeConfig.HOME_PAGE));
            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error("TradeServletAction.doHome(...)" + "Error finding account for user " + userID
                    + "treating this as a user error and forwarding on to a new page", e);
        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.doHome(...)" + " exception user =" + userID, e);
        }

        requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.HOME_PAGE));
    }

    /**
     * Login a Trade User. Dispatch to the Trade Home JSP for display
     *
     * @param userID
     *            The User to login
     * @param passwd
     *            The password supplied by the trader used to authenticate
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @param results
     *            A short description of the results/success of this web request
     *            provided on the web page
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doLogin(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String passwd) throws javax.servlet.ServletException,
            java.io.IOException {

        String results = "";
        try {
            // Got a valid userID and passwd, attempt login

            AccountDataBean accountData = tAction.login(userID, passwd);

            if (accountData != null) {
                HttpSession session = req.getSession(true);
                session.setAttribute("uidBean", userID);
                session.setAttribute("sessionCreationDate", new java.util.Date());

                results = "Ready to Trade";
                doHome(ctx, req, resp, userID, results);
                return;
            } else {
                req.setAttribute("results", results + "\nCould not find account for + " + userID);
                // log the exception with an error level of 3 which means,
                // handled exception but would invalidate a automation run
                Log.log("TradeServletAction.doLogin(...)", "Error finding account for user " + userID + "",
                        "user entered a bad username or the database is not populated");
            }
        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // forward them to another page rather than throw a 500
            req.setAttribute("results", results + "illegal argument:" + e.getMessage());
            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error(e, "TradeServletAction.doLogin(...)", "illegal argument, information should be in exception string",
                    "treating this as a user error and forwarding on to a new page");

        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.doLogin(...)" + "Exception logging in user " + userID + "with password" + passwd, e);
        }

        requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.WELCOME_PAGE));

    }

    /**
     * Logout a Trade User Dispatch to the Trade Welcome JSP for display
     *
     * @param userID
     *            The User to logout
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @param results
     *            A short description of the results/success of this web request
     *            provided on the web page
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doLogout(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID) throws ServletException, IOException {
        String results = "";

        try {
            tAction.logout(userID);

        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // forward them to another page, at the end of the page.
            req.setAttribute("results", results + "illegal argument:" + e.getMessage());

            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error(e, "TradeServletAction.doLogout(...)", "illegal argument, information should be in exception string",
                    "treating this as a user error and forwarding on to a new page");
        } catch (Exception e) {
            // log the exception and foward to a error page
            Log.error(e, "TradeServletAction.doLogout(...):", "Error logging out" + userID, "fowarding to an error page");
            // set the status_code to 500
            throw new ServletException("TradeServletAction.doLogout(...)" + "exception logging out user " + userID, e);
        }
        HttpSession session = req.getSession();
        if (session != null) {
            session.invalidate();
        }
        
        // Added to actually remove a user from the authentication cache
        req.logout();

        Object o = req.getAttribute("TSS-RecreateSessionInLogout");
        if (o != null && ((Boolean) o).equals(Boolean.TRUE)) {
            // Recreate Session object before writing output to the response
            // Once the response headers are written back to the client the
            // opportunity
            // to create a new session in this request may be lost
            // This is to handle only the TradeScenarioServlet case
            session = req.getSession(true);
        }
        requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.WELCOME_PAGE));
    }

    /**
     * Retrieve the current portfolio of stock holdings for the given trader
     * Dispatch to the Trade Portfolio JSP for display
     *
     * @param userID
     *            The User requesting to view their portfolio
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @param results
     *            A short description of the results/success of this web request
     *            provided on the web page
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doPortfolio(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String results) throws ServletException, IOException {

        try {
            // Get the holdiings for this user

            Collection<QuoteDataBean> quoteDataBeans = new ArrayList<QuoteDataBean>();
            Collection<?> holdingDataBeans = tAction.getHoldings(userID);

            // Walk through the collection of user
            // holdings and creating a list of quotes
            if (holdingDataBeans.size() > 0) {

                Iterator<?> it = holdingDataBeans.iterator();
                while (it.hasNext()) {
                    HoldingDataBean holdingData = (HoldingDataBean) it.next();
                    QuoteDataBean quoteData = tAction.getQuote(holdingData.getQuoteID());
                    quoteDataBeans.add(quoteData);
                }
            } else {
                results = results + ".  Your portfolio is empty.";
            }
            req.setAttribute("results", results);
            req.setAttribute("holdingDataBeans", holdingDataBeans);
            req.setAttribute("quoteDataBeans", quoteDataBeans);
            requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.PORTFOLIO_PAGE));
        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // forward them to another page rather than throw a 500
            req.setAttribute("results", results + "illegal argument:" + e.getMessage());
            requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.PORTFOLIO_PAGE));
            // log the exception with an error level of 3 which means, handled
            // exception but would invalidate a automation run
            Log.error(e, "TradeServletAction.doPortfolio(...)", "illegal argument, information should be in exception string", "user error");
        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.doPortfolio(...)" + " exception user =" + userID, e);
        }
    }

    /**
     * Retrieve the current Quote for the given stock symbol Dispatch to the
     * Trade Quote JSP for display
     *
     * @param userID
     *            The stock symbol used to get the current quote
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doQuotes(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String symbols) throws ServletException, IOException {

        // Edge Caching:
        // Getting Quotes has been moved to the JSP
        // Quote.jsp. This makes each Quote a
        // standalone "fragment", and thus is a candidate for
        // Edge caching.
        //

        requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.QUOTE_PAGE));
    }

    /**
     * Register a new trader given the provided user Profile information such as
     * address, email, etc. Dispatch to the Trade Home JSP for display
     *
     * @param userID
     *            The User to create
     * @param passwd
     *            The User password
     * @param fullname
     *            The new User fullname info
     * @param ccn
     *            The new User credit card info
     * @param money
     *            The new User opening account balance
     * @param address
     *            The new User address info
     * @param email
     *            The new User email info
     * @return The userID of the new trader
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doRegister(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String passwd, String cpasswd, String fullname,
            String ccn, String openBalanceString, String email, String address) throws ServletException, IOException {
        String results = "";

        try {
            // Validate user passwords match and are atleast 1 char in length
            if ((passwd.equals(cpasswd)) && (passwd.length() >= 1)) {

                AccountDataBean accountData = tAction.register(userID, passwd, fullname, address, email, ccn, new BigDecimal(openBalanceString));
                if (accountData == null) {
                    results = "Registration operation failed;";
                    System.out.println(results);
                    req.setAttribute("results", results);
                    requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.REGISTER_PAGE));
                } else {
                    doLogin(ctx, req, resp, userID, passwd);
                    results = "Registration operation succeeded;  Account " + accountData.getAccountID() + " has been created.";
                    req.setAttribute("results", results);

                }
            } else {
                // Password validation failed
                results = "Registration operation failed, your passwords did not match";
                System.out.println(results);
                req.setAttribute("results", results);
                requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.REGISTER_PAGE));
            }

        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.doRegister(...)" + " exception user =" + userID, e);
        }
    }

    /**
     * Sell a current holding of stock shares for the given trader. Dispatch to
     * the Trade Portfolio JSP for display
     *
     * @param userID
     *            The User buying shares
     * @param symbol
     *            The stock to sell
     * @param indx
     *            The unique index identifying the users holding to sell
     * @param ctx
     *            the servlet context
     * @param req
     *            the HttpRequest object
     * @param resp
     *            the HttpResponse object
     * @exception javax.servlet.ServletException
     *                If a servlet specific exception is encountered
     * @exception javax.io.IOException
     *                If an exception occurs while writing results back to the
     *                user
     *
     */
    void doSell(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, Integer holdingID) throws ServletException, IOException {
        String results = "";
        try {
            OrderDataBean orderData = tAction.sell(userID, holdingID, TradeConfig.orderProcessingMode);

            req.setAttribute("orderData", orderData);
            req.setAttribute("results", results);
        } catch (java.lang.IllegalArgumentException e) { // this is a user
            // error so I will
            // just log the exception and then later on I will redisplay the
            // portfolio page
            // because this is just a user exception
            Log.error(e, "TradeServletAction.doSell(...)", "illegal argument, information should be in exception string", "user error");
        } catch (Exception e) {
            // log the exception with error page
            throw new ServletException("TradeServletAction.doSell(...)" + " exception selling holding " + holdingID + " for user =" + userID, e);
        }
        requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.ORDER_PAGE));
    }

    void doWelcome(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String status) throws ServletException, IOException {

        req.setAttribute("results", status);
        requestDispatch(ctx, req, resp, null, TradeConfig.getPage(TradeConfig.WELCOME_PAGE));
    }

    private void requestDispatch(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID, String page) throws ServletException,
            IOException {

        ctx.getRequestDispatcher(page).include(req, resp);
    }

    void doMarketSummary(ServletContext ctx, HttpServletRequest req, HttpServletResponse resp, String userID) throws ServletException, IOException {
        req.setAttribute("results", "test");
        requestDispatch(ctx, req, resp, userID, TradeConfig.getPage(TradeConfig.MARKET_SUMMARY_PAGE));

    }
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/TradeServletAction.java:TradeServletAction.<init>
// Node: requestDispatch
// Node: ServletException
// Node: invalidate
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



// Node: keySet
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

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;

import javax.jms.Message;
import javax.json.Json;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;


/** This class is a holds the last 5 stock changes, used by the MarketSummary WebSocket
 * */

public class RecentStockChangeList {

    private static List<Message> stockChanges = Collections.synchronizedList(new LinkedList<Message>());
       
    public static void addStockChange(Message message) {
        
        stockChanges.add(0, message);
        
        // Add stock, remove if needed
        if(stockChanges.size() > 5) {
            stockChanges.remove(5);
        }
    }
    
    public static JsonObject stockChangesInJSON() {
        
        JsonObjectBuilder jObjectBuilder = Json.createObjectBuilder();
        
        try {
            int i = 1;
            
            List<Message> temp = new LinkedList<Message>(stockChanges);
                        
            for (Iterator<Message> iterator = temp.iterator(); iterator.hasNext();) {
                Message message = iterator.next();
                            
                jObjectBuilder.add("change" + i + "_stock", message.getStringProperty("symbol"));
                jObjectBuilder.add("change" + i + "_price","$" + message.getStringProperty("price"));          
                            
                BigDecimal change = new BigDecimal(message.getStringProperty("price")).subtract(new BigDecimal(message.getStringProperty("oldPrice")));
                change.setScale(2, RoundingMode.HALF_UP);
                
                jObjectBuilder.add("change" + i + "_change", change.toString());
                
                i++;
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        
        return jObjectBuilder.build();
    }
    
    public static boolean isEmpty() {
        return stockChanges.isEmpty();
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

import javax.annotation.PostConstruct;
import javax.faces.context.ExternalContext;
import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Named("orderdata")
public class OrderDataJSF {
    @Inject
    private ExternalContext facesExternalContext;

    @Inject
    private TradeAction tradeAction;

    private OrderData[] allOrders;
    private OrderData orderData;

    public OrderDataJSF() {
    }

    public void getAllOrder() {
        try {
            HttpSession session = (HttpSession) facesExternalContext.getSession(true);
            String userID = (String) session.getAttribute("uidBean");

            ArrayList<?> orderDataBeans = (TradeConfig.getLongRun() ? new ArrayList<Object>() : (ArrayList<?>) tradeAction.getOrders(userID));
            OrderData[] orders = new OrderData[orderDataBeans.size()];

            int count = 0;

            for (Object order : orderDataBeans) {
                OrderData r = new OrderData(((OrderDataBean) order).getOrderID(), ((OrderDataBean) order).getOrderStatus(),
                        ((OrderDataBean) order).getOpenDate(), ((OrderDataBean) order).getCompletionDate(), ((OrderDataBean) order).getOrderFee(),
                        ((OrderDataBean) order).getOrderType(), ((OrderDataBean) order).getQuantity(), ((OrderDataBean) order).getSymbol());
                r.setPrice(((OrderDataBean) order).getPrice());
                r.setTotal(r.getPrice().multiply(new BigDecimal(r.getQuantity())));
                orders[count] = r;
                count++;
            }

            setAllOrders(orders);
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    @PostConstruct
    public void getOrder() {
        HttpSession session = (HttpSession) facesExternalContext.getSession(true);
        OrderData order = (OrderData) session.getAttribute("orderData");

        if (order != null) {
            setOrderData(order);
        }
    }

    public void setAllOrders(OrderData[] allOrders) {
        this.allOrders = allOrders;
    }

    public OrderData[] getAllOrders() {
        return allOrders;
    }

    public void setOrderData(OrderData orderData) {
        this.orderData = orderData;
    }

    public OrderData getOrderData() {
        return orderData;
    }
}


// Node: getAllOrder
// Node: OrderData
// Node: setTotal
// Node: setAllOrders
// Node: getOrder
// Node: setOrderData
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
import java.text.DecimalFormat;

import com.ibm.websphere.samples.daytrader.util.FinancialUtils;

public class QuoteData {
    private BigDecimal price;
    private BigDecimal open;
    private String symbol;
    private BigDecimal high;
    private BigDecimal low;
    private String companyName;
    private double volume;
    private double change;
    private String range;
    private BigDecimal gainPercent;
    private BigDecimal gain;

    public QuoteData(BigDecimal price, BigDecimal open, String symbol) {
        this.open = open;
        this.price = price;
        this.symbol = symbol;
        this.change = price.subtract(open).setScale(2).doubleValue();
    }

    public QuoteData(BigDecimal open, BigDecimal price, String symbol, BigDecimal high, BigDecimal low, String companyName, Double volume, Double change) {
        this.open = open;
        this.price = price;
        this.symbol = symbol;
        this.high = high;
        this.low = low;
        this.companyName = companyName;
        this.volume = volume;
        this.change = change;
        this.range = high.toString() + "-" + low.toString();
        this.gainPercent = FinancialUtils.computeGainPercent(price, open).setScale(2);
        this.gain = FinancialUtils.computeGain(price, open).setScale(2);
    }

    public void setSymbol(String symbol) {
        this.symbol = symbol;
    }

    public String getSymbol() {
        return symbol;
    }

    public void setPrice(BigDecimal price) {
        this.price = price;
    }

    public BigDecimal getPrice() {
        return price;
    }

    public void setOpen(BigDecimal open) {
        this.open = open;
    }

    public BigDecimal getOpen() {
        return open;
    }

    public void setHigh(BigDecimal high) {
        this.high = high;
    }

    public BigDecimal getHigh() {
        return high;
    }

    public void setLow(BigDecimal low) {
        this.low = low;
    }

    public BigDecimal getLow() {
        return low;
    }

    public void setCompanyName(String companyName) {
        this.companyName = companyName;
    }

    public String getCompanyName() {
        return companyName;
    }

    public void setVolume(double volume) {
        this.volume = volume;
    }

    public double getVolume() {
        return volume;
    }

    public void setChange(double change) {
        this.change = change;
    }

    public double getChange() {
        return change;
    }

    public void setRange(String range) {
        this.range = range;
    }

    public String getRange() {
        return range;
    }

    public void setGainPercent(BigDecimal gainPercent) {
        this.gainPercent = gainPercent.setScale(2);
    }

    public BigDecimal getGainPercent() {
        return gainPercent;
    }

    public void setGain(BigDecimal gain) {
        this.gain = gain;
    }

    public BigDecimal getGain() {
        return gain;
    }

    public String getGainPercentHTML() {
        return FinancialUtils.printGainPercentHTML(gainPercent);
    }

    public String getGainHTML() {
        return FinancialUtils.printGainHTML(gain);
    }

    public String getChangeHTML() {
        String htmlString, arrow;
        if (change < 0.0) {
            htmlString = "<FONT color=\"#cc0000\">";
            arrow = "arrowdown.gif";
        } else {
            htmlString = "<FONT color=\"#009900\">";
            arrow = "arrowup.gif";
        }
        DecimalFormat df = new DecimalFormat("####0.00");

        htmlString += df.format(change) + "</FONT><IMG src=\"images/" + arrow + "\" width=\"10\" height=\"10\" border=\"0\"></IMG>";
        return htmlString;
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

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

import javax.enterprise.context.SessionScoped;
import javax.inject.Named;

import com.ibm.websphere.samples.daytrader.util.FinancialUtils;

@Named
@SessionScoped
public class HoldingData implements Serializable {

    private static final long serialVersionUID = -4760036695773749721L;

    private Integer holdingID;
    private double quantity;
    private BigDecimal purchasePrice;
    private Date purchaseDate;
    private String quoteID;
    private BigDecimal price;
    private BigDecimal basis;
    private BigDecimal marketValue;
    private BigDecimal gain;

    public void setHoldingID(Integer holdingID) {
        this.holdingID = holdingID;
    }

    public Integer getHoldingID() {
        return holdingID;
    }

    public void setQuantity(double quantity) {
        this.quantity = quantity;
    }

    public double getQuantity() {
        return quantity;
    }

    public void setPurchasePrice(BigDecimal purchasePrice) {
        this.purchasePrice = purchasePrice;
    }

    public BigDecimal getPurchasePrice() {
        return purchasePrice;
    }

    public void setPurchaseDate(Date purchaseDate) {
        this.purchaseDate = purchaseDate;
    }

    public Date getPurchaseDate() {
        return purchaseDate;
    }

    public void setQuoteID(String quoteID) {
        this.quoteID = quoteID;
    }

    public String getQuoteID() {
        return quoteID;
    }

    public void setPrice(BigDecimal price) {
        this.price = price;
    }

    public BigDecimal getPrice() {
        return price;
    }

    public void setBasis(BigDecimal basis) {
        this.basis = basis;
    }

    public BigDecimal getBasis() {
        return basis;
    }

    public void setMarketValue(BigDecimal marketValue) {
        this.marketValue = marketValue;
    }

    public BigDecimal getMarketValue() {
        return marketValue;
    }

    public void setGain(BigDecimal gain) {
        this.gain = gain;
    }

    public BigDecimal getGain() {
        return gain;
    }

    public String getGainHTML() {
        return FinancialUtils.printGainHTML(gain);
    }
}


// Node: setBasis
// Node: setMarketValue
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
import javax.enterprise.inject.Produces;

import com.ibm.websphere.samples.daytrader.TradeAction;

public class TradeActionProducer {
	@Produces
    @RequestScoped
    public TradeAction produceTradeAction() {
        return new TradeAction();
    }
}


// Node: produceTradeAction
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


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/jsf/OrderData.java:OrderData.<init>
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


// Node: getPortfolio
// Node: HoldingData
// Node: setTotalGainPercent
// Node: getRowData
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
import java.math.RoundingMode;
import java.util.Collection;
import java.util.Date;
import java.util.Iterator;

import javax.annotation.PostConstruct;
import javax.enterprise.context.RequestScoped;
import javax.inject.Inject;
import javax.inject.Named;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.beans.MarketSummaryDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.FinancialUtils;

@Named("marketdata")
@RequestScoped
public class MarketSummaryJSF {
    @Inject
    private TradeAction tradeAction;

    private BigDecimal TSIA;
    private BigDecimal openTSIA;
    private double volume;
    private QuoteData[] topGainers;
    private QuoteData[] topLosers;
    private Date summaryDate;

    // cache the gainPercent once computed for this bean
    private BigDecimal gainPercent = null;

    @PostConstruct
    public void getMarketSummary() {
        try {
            MarketSummaryDataBean marketSummaryData = tradeAction.getMarketSummary();
            setSummaryDate(marketSummaryData.getSummaryDate());
            setTSIA(marketSummaryData.getTSIA());
            setVolume(marketSummaryData.getVolume());
            setGainPercent(marketSummaryData.getGainPercent());

            Collection<?> topGainers = marketSummaryData.getTopGainers();

            Iterator<?> gainers = topGainers.iterator();
            int count = 0;
            QuoteData[] gainerjsfs = new QuoteData[5];

            while (gainers.hasNext() && (count < 5)) {
                QuoteDataBean quote = (QuoteDataBean) gainers.next();
                QuoteData r = new QuoteData(quote.getPrice(), quote.getOpen(), quote.getSymbol());
                gainerjsfs[count] = r;
                count++;
            }

            setTopGainers(gainerjsfs);

            Collection<?> topLosers = marketSummaryData.getTopLosers();

            QuoteData[] loserjsfs = new QuoteData[5];
            count = 0;
            Iterator<?> losers = topLosers.iterator();

            while (losers.hasNext() && (count < 5)) {
                QuoteDataBean quote = (QuoteDataBean) losers.next();
                QuoteData r = new QuoteData(quote.getPrice(), quote.getOpen(), quote.getSymbol());
                loserjsfs[count] = r;
                count++;
            }

            setTopLosers(loserjsfs);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public void setTSIA(BigDecimal tSIA) {
        TSIA = tSIA;
    }

    public BigDecimal getTSIA() {
        return TSIA;
    }

    public void setOpenTSIA(BigDecimal openTSIA) {
        this.openTSIA = openTSIA;
    }

    public BigDecimal getOpenTSIA() {
        return openTSIA;
    }

    public void setVolume(double volume) {
        this.volume = volume;
    }

    public double getVolume() {
        return volume;
    }

    public void setTopGainers(QuoteData[] topGainers) {
        this.topGainers = topGainers;
    }

    public QuoteData[] getTopGainers() {
        return topGainers;
    }

    public void setTopLosers(QuoteData[] topLosers) {
        this.topLosers = topLosers;
    }

    public QuoteData[] getTopLosers() {
        return topLosers;
    }

    public void setSummaryDate(Date summaryDate) {
        this.summaryDate = summaryDate;
    }

    public Date getSummaryDate() {
        return summaryDate;
    }

    public void setGainPercent(BigDecimal gainPercent) {
        this.gainPercent = gainPercent.setScale(2,RoundingMode.HALF_UP);
    }

    public BigDecimal getGainPercent() {
        return gainPercent;
    }

    public String getGainPercentHTML() {
        return FinancialUtils.printGainPercentHTML(gainPercent);
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

import javax.annotation.PostConstruct;
import javax.enterprise.context.RequestScoped;
import javax.faces.component.html.HtmlDataTable;
import javax.faces.context.ExternalContext;
import javax.inject.Inject;
import javax.inject.Named;
import javax.servlet.http.HttpSession;

import com.ibm.websphere.samples.daytrader.TradeAction;
import com.ibm.websphere.samples.daytrader.entities.OrderDataBean;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@Named("quotedata")
@RequestScoped
public class QuoteJSF {

    @Inject
    private ExternalContext facesExternalContext;

    @Inject
    private TradeAction tradeAction;

    private QuoteData[] quotes;
    private String symbols = null;
    private HtmlDataTable dataTable;
    private Integer quantity = 100;

    @PostConstruct
    public void getAllQuotes() {
        getQuotesBySymbols();
    }

    public String getQuotesBySymbols() {
        HttpSession session = (HttpSession) facesExternalContext.getSession(true);

        if (symbols == null && (session.getAttribute("symbols") == null)) {
            setSymbols("s:0,s:1,s:2,s:3,s:4");
            session.setAttribute("symbols", getSymbols());
        } else if (symbols == null && session.getAttribute("symbols") != null) {
            setSymbols((String) session.getAttribute("symbols"));
        }

        else {
            session.setAttribute("symbols", getSymbols());
        }

        java.util.StringTokenizer st = new java.util.StringTokenizer(symbols, " ,");
        QuoteData[] quoteDatas = new QuoteData[st.countTokens()];
        int count = 0;

        while (st.hasMoreElements()) {
            String symbol = st.nextToken();

            try {
                QuoteDataBean quoteData = tradeAction.getQuote(symbol);
                quoteDatas[count] = new QuoteData(quoteData.getOpen(), quoteData.getPrice(), quoteData.getSymbol(), quoteData.getHigh(), quoteData.getLow(),
                        quoteData.getCompanyName(), quoteData.getVolume(), quoteData.getChange());
                count++;
            } catch (Exception e) {
                Log.error(e.toString());
            }
        }
        setQuotes(quoteDatas);
        return "quotes";
    }

    public String buy() {
        HttpSession session = (HttpSession) facesExternalContext.getSession(true);
        String userID = (String) session.getAttribute("uidBean");
        QuoteData quoteData = (QuoteData) dataTable.getRowData();
        OrderDataBean orderDataBean;

        try {
            orderDataBean = tradeAction.buy(userID, quoteData.getSymbol(), new Double(this.quantity).doubleValue(), TradeConfig.orderProcessingMode);
            OrderData orderData = new OrderData(orderDataBean.getOrderID(), orderDataBean.getOrderStatus(), orderDataBean.getOpenDate(),
                    orderDataBean.getCompletionDate(), orderDataBean.getOrderFee(), orderDataBean.getOrderType(), orderDataBean.getQuantity(),
                    orderDataBean.getSymbol());
            session.setAttribute("orderData", orderData);
        } catch (Exception e) {
            Log.error(e.toString());
            e.printStackTrace();
        }
        return "buy";
    }

    public void setQuotes(QuoteData[] quotes) {
        this.quotes = quotes;
    }

    public QuoteData[] getQuotes() {
        return quotes;
    }

    public void setSymbols(String symbols) {
        this.symbols = symbols;
    }

    public String getSymbols() {
        return symbols;
    }

    public void setDataTable(HtmlDataTable dataTable) {
        this.dataTable = dataTable;
    }

    public HtmlDataTable getDataTable() {
        return dataTable;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }

    public Integer getQuantity() {
        return quantity;
    }
}


// Node: getQuotesBySymbols
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


// Node: setResults
// Node: setCcn
// Node: setFullname
// Node: setCpassword
// Node: NullPointerException
// Node: updateProfile
// Node: getRequest
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


// Node: home
// Node: setClosedOrders
// Node: setNumberOfOrders
// Node: setSessionCreationDate
// Node: setCurrentTime
