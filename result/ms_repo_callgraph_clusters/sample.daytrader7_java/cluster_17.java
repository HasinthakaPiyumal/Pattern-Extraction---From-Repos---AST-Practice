// Cluster 17

// Node: currentTimeMillis
// Node: Resource
// Node: EJBException
// Node: persist
// Node: Timestamp
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


// Node: getOrderProcessingMode
// Node: newThread
// Node: CompleteOrderThread
// Node: start
// Node: try
// Node: createContext
// Node: createTextMessage
// Node: setStringProperty
// Node: setIntProperty
// Node: setBooleanProperty
// Node: setText
// Node: setLongProperty
// Node: createProducer
// Node: send
// Node: getMessage
// Node: isCompleted
// Node: getProfile
// Node: isBuy
// Node: createHolding
// Node: isSell
// Node: publishQuotePriceChange
// Node: userID
// Node: setProfile
// Node: setDoubleProperty
// Node: investmentReturn
// Node: pingTwoPhase
// Node: getText
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

import javax.ejb.Remote;

import com.ibm.websphere.samples.daytrader.TradeServices;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;

import java.math.BigDecimal;


@Remote
public interface TradeSLSBRemote extends TradeServices {
    public double investmentReturn(double investment, double NetValue) throws Exception;
    
    public QuoteDataBean pingTwoPhase(String symbol) throws Exception;

    public void publishQuotePriceChange(QuoteDataBean quote, BigDecimal oldPrice, BigDecimal changeFactor, double sharesTraded);
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/ejb3/TradeSLSBRemote.java:TradeSLSBRemote.<init>
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

import javax.ejb.Local;

import com.ibm.websphere.samples.daytrader.TradeServices;
import com.ibm.websphere.samples.daytrader.entities.QuoteDataBean;


@Local
public interface TradeSLSBLocal extends TradeServices {
    public double investmentReturn(double investment, double NetValue) throws Exception;
    
    public QuoteDataBean pingTwoPhase(String symbol) throws Exception;
    
    public void publishQuotePriceChange(QuoteDataBean quote, BigDecimal oldPrice, BigDecimal changeFactor, double sharesTraded);
}

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/ejb3/TradeSLSBLocal.java:TradeSLSBLocal.<init>
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

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.util.Collection;
import java.util.HashMap;
import java.util.Iterator;

import com.ibm.websphere.samples.daytrader.util.KeyBlock;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

public class KeySequenceDirect {

    private static HashMap<String, Collection<?>> keyMap = new HashMap<String, Collection<?>>();

    public static synchronized Integer getNextID(Connection conn, String keyName, boolean inSession, boolean inGlobalTxn) throws Exception {
        Integer nextID = null;
        // First verify we have allocated a block of keys
        // for this key name
        // Then verify the allocated block has not been depleted
        // allocate a new block if necessary
        if (keyMap.containsKey(keyName) == false) {
            allocNewBlock(conn, keyName, inSession, inGlobalTxn);
        }
        Collection<?> block = keyMap.get(keyName);

        Iterator<?> ids = block.iterator();
        if (ids.hasNext() == false) {
            ids = allocNewBlock(conn, keyName, inSession, inGlobalTxn).iterator();
        }
        // get and return a new unique key
        nextID = (Integer) ids.next();

        if (Log.doTrace()) {
            Log.trace("KeySequenceDirect:getNextID inSession(" + inSession + ") - return new PK ID for Entity type: " + keyName + " ID=" + nextID);
        }
        return nextID;
    }

    private static Collection<?> allocNewBlock(Connection conn, String keyName, boolean inSession, boolean inGlobalTxn) throws Exception {
        try {

            if (inGlobalTxn == false && !inSession) {
                conn.commit(); // commit any pending txns
            }

            PreparedStatement stmt = conn.prepareStatement(getKeyForUpdateSQL);
            stmt.setString(1, keyName);
            ResultSet rs = stmt.executeQuery();

            if (!rs.next()) {
                // No keys found for this name - create a new one
                PreparedStatement stmt2 = conn.prepareStatement(createKeySQL);
                int keyVal = 0;
                stmt2.setString(1, keyName);
                stmt2.setInt(2, keyVal);
                stmt2.executeUpdate();
                stmt2.close();
                stmt.close();
                stmt = conn.prepareStatement(getKeyForUpdateSQL);
                stmt.setString(1, keyName);
                rs = stmt.executeQuery();
                rs.next();
            }

            int keyVal = rs.getInt("keyval");

            stmt.close();

            stmt = conn.prepareStatement(updateKeyValueSQL);
            stmt.setInt(1, keyVal + TradeConfig.KEYBLOCKSIZE);
            stmt.setString(2, keyName);
            stmt.executeUpdate();
            stmt.close();

            Collection<?> block = new KeyBlock(keyVal, keyVal + TradeConfig.KEYBLOCKSIZE - 1);
            keyMap.put(keyName, block);

            if (inGlobalTxn == false && !inSession) {
                conn.commit();
            }

            return block;
        } catch (Exception e) {
            String error = "KeySequenceDirect:allocNewBlock - failure to allocate new block of keys for Entity type: " + keyName;
            Log.error(e, error);
            throw new Exception(error + e.toString());
        }
    }

    private static final String getKeyForUpdateSQL = "select * from keygenejb kg where kg.keyname = ?  for update";

    private static final String createKeySQL = "insert into keygenejb " + "( keyname, keyval ) " + "VALUES (  ?  ,  ? )";

    private static final String updateKeyValueSQL = "update keygenejb set keyval = ? " + "where keyname = ?";

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/direct/KeySequenceDirect.java:KeySequenceDirect.<init>
// Node: getNextID
// Node: containsKey
// Node: allocNewBlock
// Node: inSession
// Node: commit
// Node: prepareStatement
// Node: setString
// Node: executeQuery
// Node: setInt
// Node: executeUpdate
// Node: getInt
// Node: KeyBlock
// Node: Exception
// Node: VALUES
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


// Node: getConn
// Node: getStatement
// Node: getQuoteDataFromResultSet
// Node: last
// Node: getBigDecimal
// Node: getDouble
// Node: rollBack
// Node: releaseConn
// Node: begin
// Node: setInGlobalTxn
// Node: getQuoteData
// Node: creditAccountBalance
// Node: negate
// Node: getOrderData
// Node: getInGlobalTxn
// Node: rollback
// Node: getHoldingData
// Node: updateHoldingStatus
// Node: getOrderDataFromResultSet
// Node: compareToIgnoreCase
// Node: updateOrderHolding
// Node: removeHolding
// Node: updateOrderStatus
// Node: anything
// Node: setTimestamp
// Node: setBigDecimal
// Node: setDouble
// Node: setNull
// Node: traceEnter
// Node: traceExit
// Node: getQuoteForUpdate
// Node: getHoldingDataFromResultSet
// Node: getAccountDataFromResultSet
// Node: getAccountDataForUpdate
// Node: getAccountProfileDataFromResultSet
// Node: updateQuoteVolume
// Node: updateQuotePriceVolumeInt
// Node: by
// Node: FinderException
// Node: setLastLogin
// Node: setLoginCount
// Node: getTimestamp
// Node: getMetaData
// Node: getDatabaseProductName
// Node: reset
// Node: createStatement
// Node: in
// Node: setNewUserCount
// Node: count
// Node: setTradeUserCount
// Node: setTradeStockCount
// Node: sum
// Node: setSumLoginCount
// Node: setSumLogoutCount
// Node: setHoldingCount
// Node: setOrderCount
// Node: setBuyOrderCount
// Node: setSellOrderCount
// Node: setCancelledOrderCount
// Node: setOpenOrderCount
// Node: setDeletedOrderCount
// Node: getDataSource
// Node: getConnection
// Node: setAutoCommit
// Node: getTransactionIsolation
// Node: getConnPublic
// Node: SUM
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

public class RunStatsDataBean implements Serializable {
    private static final long serialVersionUID = 4017778674103242167L;

    // Constructors
    public RunStatsDataBean() {
    }

    // count of trade users in the database (users w/ userID like 'uid:%')
    private int tradeUserCount;
    // count of trade stocks in the database (stocks w/ symbol like 's:%')
    private int tradeStockCount;

    // count of new registered users in this run (users w/ userID like 'ru:%')
    // -- random user
    private int newUserCount;

    // sum of logins by trade users
    private int sumLoginCount;
    // sum of logouts by trade users
    private int sumLogoutCount;

    // count of holdings of trade users
    private int holdingCount;

    // count of orders of trade users
    private int orderCount;
    // count of buy orders of trade users
    private int buyOrderCount;
    // count of sell orders of trade users
    private int sellOrderCount;
    // count of cancelled orders of trade users
    private int cancelledOrderCount;
    // count of open orders of trade users
    private int openOrderCount;
    // count of orders deleted during this trade Reset
    private int deletedOrderCount;

    @Override
    public String toString() {
        return "\n\tRunStatsData for reset at " + new java.util.Date() + "\n\t\t      tradeUserCount: " + getTradeUserCount() + "\n\t\t        newUserCount: "
                + getNewUserCount() + "\n\t\t       sumLoginCount: " + getSumLoginCount() + "\n\t\t      sumLogoutCount: " + getSumLogoutCount()
                + "\n\t\t        holdingCount: " + getHoldingCount() + "\n\t\t          orderCount: " + getOrderCount() + "\n\t\t       buyOrderCount: "
                + getBuyOrderCount() + "\n\t\t      sellOrderCount: " + getSellOrderCount() + "\n\t\t cancelledOrderCount: " + getCancelledOrderCount()
                + "\n\t\t      openOrderCount: " + getOpenOrderCount() + "\n\t\t   deletedOrderCount: " + getDeletedOrderCount();
    }

    /**
     * Gets the tradeUserCount
     *
     * @return Returns a int
     */
    public int getTradeUserCount() {
        return tradeUserCount;
    }

    /**
     * Sets the tradeUserCount
     *
     * @param tradeUserCount
     *            The tradeUserCount to set
     */
    public void setTradeUserCount(int tradeUserCount) {
        this.tradeUserCount = tradeUserCount;
    }

    /**
     * Gets the newUserCount
     *
     * @return Returns a int
     */
    public int getNewUserCount() {
        return newUserCount;
    }

    /**
     * Sets the newUserCount
     *
     * @param newUserCount
     *            The newUserCount to set
     */
    public void setNewUserCount(int newUserCount) {
        this.newUserCount = newUserCount;
    }

    /**
     * Gets the sumLoginCount
     *
     * @return Returns a int
     */
    public int getSumLoginCount() {
        return sumLoginCount;
    }

    /**
     * Sets the sumLoginCount
     *
     * @param sumLoginCount
     *            The sumLoginCount to set
     */
    public void setSumLoginCount(int sumLoginCount) {
        this.sumLoginCount = sumLoginCount;
    }

    /**
     * Gets the sumLogoutCount
     *
     * @return Returns a int
     */
    public int getSumLogoutCount() {
        return sumLogoutCount;
    }

    /**
     * Sets the sumLogoutCount
     *
     * @param sumLogoutCount
     *            The sumLogoutCount to set
     */
    public void setSumLogoutCount(int sumLogoutCount) {
        this.sumLogoutCount = sumLogoutCount;
    }

    /**
     * Gets the holdingCount
     *
     * @return Returns a int
     */
    public int getHoldingCount() {
        return holdingCount;
    }

    /**
     * Sets the holdingCount
     *
     * @param holdingCount
     *            The holdingCount to set
     */
    public void setHoldingCount(int holdingCount) {
        this.holdingCount = holdingCount;
    }

    /**
     * Gets the buyOrderCount
     *
     * @return Returns a int
     */
    public int getBuyOrderCount() {
        return buyOrderCount;
    }

    /**
     * Sets the buyOrderCount
     *
     * @param buyOrderCount
     *            The buyOrderCount to set
     */
    public void setBuyOrderCount(int buyOrderCount) {
        this.buyOrderCount = buyOrderCount;
    }

    /**
     * Gets the sellOrderCount
     *
     * @return Returns a int
     */
    public int getSellOrderCount() {
        return sellOrderCount;
    }

    /**
     * Sets the sellOrderCount
     *
     * @param sellOrderCount
     *            The sellOrderCount to set
     */
    public void setSellOrderCount(int sellOrderCount) {
        this.sellOrderCount = sellOrderCount;
    }

    /**
     * Gets the cancelledOrderCount
     *
     * @return Returns a int
     */
    public int getCancelledOrderCount() {
        return cancelledOrderCount;
    }

    /**
     * Sets the cancelledOrderCount
     *
     * @param cancelledOrderCount
     *            The cancelledOrderCount to set
     */
    public void setCancelledOrderCount(int cancelledOrderCount) {
        this.cancelledOrderCount = cancelledOrderCount;
    }

    /**
     * Gets the openOrderCount
     *
     * @return Returns a int
     */
    public int getOpenOrderCount() {
        return openOrderCount;
    }

    /**
     * Sets the openOrderCount
     *
     * @param openOrderCount
     *            The openOrderCount to set
     */
    public void setOpenOrderCount(int openOrderCount) {
        this.openOrderCount = openOrderCount;
    }

    /**
     * Gets the deletedOrderCount
     *
     * @return Returns a int
     */
    public int getDeletedOrderCount() {
        return deletedOrderCount;
    }

    /**
     * Sets the deletedOrderCount
     *
     * @param deletedOrderCount
     *            The deletedOrderCount to set
     */
    public void setDeletedOrderCount(int deletedOrderCount) {
        this.deletedOrderCount = deletedOrderCount;
    }

    /**
     * Gets the orderCount
     *
     * @return Returns a int
     */
    public int getOrderCount() {
        return orderCount;
    }

    /**
     * Sets the orderCount
     *
     * @param orderCount
     *            The orderCount to set
     */
    public void setOrderCount(int orderCount) {
        this.orderCount = orderCount;
    }

    /**
     * Gets the tradeStockCount
     *
     * @return Returns a int
     */
    public int getTradeStockCount() {
        return tradeStockCount;
    }

    /**
     * Sets the tradeStockCount
     *
     * @param tradeStockCount
     *            The tradeStockCount to set
     */
    public void setTradeStockCount(int tradeStockCount) {
        this.tradeStockCount = tradeStockCount;
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

import javax.ejb.EJBException;
import javax.naming.InitialContext;
import javax.transaction.UserTransaction;

import com.ibm.websphere.samples.daytrader.TradeServices;
import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.ejb3.TradeSLSBBean;

public class CompleteOrderThread implements Runnable {

        final Integer orderID;
        boolean twoPhase;
        
        
        public CompleteOrderThread (Integer id, boolean twoPhase) {
            orderID = id;
            this.twoPhase = twoPhase;
        }
        
        @Override
        public void run() {
            TradeServices trade;
            UserTransaction ut = null;
            
            try {
                // TODO: Sometimes, rarely, the commit does not complete before the find in completeOrder (leads to null order)
                // Adding delay here for now, will try to find a better solution in the future.
                Thread.sleep(500);
                
                InitialContext context = new InitialContext();
                ut = (UserTransaction) context.lookup("java:comp/UserTransaction");
                
                ut.begin();
                
                if (TradeConfig.getRunTimeMode() == TradeConfig.EJB3) {
                    trade = (TradeSLSBBean) context.lookup("java:module/TradeSLSBBean");
                } else {
                    trade = new TradeDirect(); 
                }
                
                trade.completeOrder(orderID, twoPhase);
                
                ut.commit();
            } catch (Exception e) {
                
                try {
                    ut.rollback();
                } catch (Exception e1) {
                    throw new EJBException(e1);
                } 
                throw new EJBException(e);
            } 
        }
}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/util/CompleteOrderThread.java:CompleteOrderThread.<init>
// Node: sleep
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


// Node: clear
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

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/util/KeyBlock.java:KeyBlock.<init>
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


// Node: isCancelled
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

import java.io.InputStream;
import java.util.Properties;

import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;
import javax.servlet.annotation.WebListener;

import com.ibm.websphere.samples.daytrader.direct.TradeDirect;
import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

@WebListener()
public class TradeWebContextListener implements ServletContextListener {

    // receieve trade web app startup/shutown events to start(initialized)/stop
    // TradeDirect
    @Override
    public void contextInitialized(ServletContextEvent event) {
        Log.trace("TradeWebContextListener contextInitialized -- initializing TradeDirect");
        
        // Load settings from properties file (if it exists)
        Properties prop = new Properties();
        InputStream stream =  event.getServletContext().getResourceAsStream("/properties/daytrader.properties");
        
        try {
            prop.load(stream);
            System.out.println("Settings from daytrader.properties: " + prop);
            TradeConfig.setRunTimeMode(Integer.parseInt(prop.getProperty("runtimeMode")));
            TradeConfig.setUseRemoteEJBInterface(Boolean.parseBoolean(prop.getProperty("useRemoteEJBInterface")));
            TradeConfig.setOrderProcessingMode(Integer.parseInt(prop.getProperty("orderProcessingMode")));
            TradeConfig.setWebInterface(Integer.parseInt(prop.getProperty("webInterface")));
            //TradeConfig.setCachingType(Integer.parseInt(prop.getProperty("cachingType")));
            //TradeConfig.setDistributedMapCacheSize(Integer.parseInt(prop.getProperty("cacheSize")));
            TradeConfig.setMAX_USERS(Integer.parseInt(prop.getProperty("maxUsers")));
            TradeConfig.setMAX_QUOTES(Integer.parseInt(prop.getProperty("maxQuotes")));
            TradeConfig.setMarketSummaryInterval(Integer.parseInt(prop.getProperty("marketSummaryInterval")));
            TradeConfig.setPrimIterations(Integer.parseInt(prop.getProperty("primIterations")));
            TradeConfig.setPublishQuotePriceChange(Boolean.parseBoolean(prop.getProperty("publishQuotePriceChange")));
            TradeConfig.setPercentSentToWebsocket(Integer.parseInt(prop.getProperty("percentSentToWebsocket")));
            TradeConfig.setDisplayOrderAlerts(Boolean.parseBoolean(prop.getProperty("displayOrderAlerts")));
            TradeConfig.setLongRun(Boolean.parseBoolean(prop.getProperty("longRun")));
            TradeConfig.setTrace(Boolean.parseBoolean(prop.getProperty("trace")));
            TradeConfig.setActionTrace(Boolean.parseBoolean(prop.getProperty("actionTrace")));
        } catch (Exception e) {
            System.out.println("daytrader.properties not found");
        }
        
        TradeDirect.init();
    }

    @Override
    public void contextDestroyed(ServletContextEvent event) {
        Log.trace("TradeWebContextListener  contextDestroy calling TradeDirect:destroy()");
        // TradeDirect.destroy();
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/TradeWebContextListener.java:TradeWebContextListener.<init>
// Node: WebListener
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


// Node: Runnable
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

import javax.enterprise.concurrent.ManagedThreadFactory;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.websocket.CloseReason;
import javax.websocket.EndpointConfig;
import javax.websocket.OnClose;
import javax.websocket.OnError;
import javax.websocket.OnMessage;
import javax.websocket.OnOpen;
import javax.websocket.Session;
import javax.websocket.server.ServerEndpoint;

import com.ibm.websphere.samples.daytrader.web.websocket.JsonDecoder;
import com.ibm.websphere.samples.daytrader.web.websocket.JsonEncoder;
import com.ibm.websphere.samples.daytrader.web.websocket.JsonMessage;

/** This class a simple websocket that sends the number of times it has been pinged. */

@ServerEndpoint(value = "/pingWebSocketJson",encoders=JsonEncoder.class ,decoders=JsonDecoder.class)
public class PingWebSocketJson {

    private Session currentSession = null;
    private Integer sentHitCount = null;
    private Integer receivedHitCount = null;
       
    @OnOpen
    public void onOpen(final Session session, EndpointConfig ec) {
        currentSession = session;
        sentHitCount = 0;
        receivedHitCount = 0;
        
        
        InitialContext context;
        ManagedThreadFactory mtf = null;
        
        try {
            context = new InitialContext();
            mtf = (ManagedThreadFactory) context.lookup("java:comp/DefaultManagedThreadFactory");
        
        } catch (NamingException e1) {
            // TODO Auto-generated catch block
            e1.printStackTrace();
        }
        
        Thread thread = mtf.newThread(new Runnable() {

            @Override
            public void run() {
                
                try {
                
                    Thread.sleep(500);
                    
                    while (currentSession.isOpen()) {
                        sentHitCount++;
                    
                        JsonMessage response = new JsonMessage();
                        response.setKey("sentHitCount");
                        response.setValue(sentHitCount.toString());
                        currentSession.getAsyncRemote().sendObject(response);

                        Thread.sleep(100);
                    }
                    
                           
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
                
        });
        
        thread.start();
        
    }

    @OnMessage
    public void ping(JsonMessage message) throws IOException {
        receivedHitCount++;
        JsonMessage response = new JsonMessage();
        response.setKey("receivedHitCount");
        response.setValue(receivedHitCount.toString());
        currentSession.getAsyncRemote().sendObject(response);
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


// Node: submit
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

import javax.annotation.Resource;
import javax.jms.Connection;
import javax.jms.ConnectionFactory;
import javax.jms.JMSContext;
import javax.jms.TextMessage;
import javax.jms.Topic;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * This primitive is designed to run inside the TradeApplication and relies upon
 * the {@link com.ibm.websphere.samples.daytrader.util.TradeConfig} class to set
 * configuration parameters. PingServlet2MDBQueue tests key functionality of a
 * servlet call to a post a message to an MDB Topic. The TradeStreamerMDB (and
 * any other subscribers) receives the message This servlet makes use of the MDB
 * EJB {@link com.ibm.websphere.samples.daytrader.ejb3.DTStreamer3MDB} by
 * posting a message to the MDB Topic
 */
@WebServlet(name = "ejb3.PingServlet2MDBTopic", urlPatterns = { "/ejb3/PingServlet2MDBTopic" })
public class PingServlet2MDBTopic extends HttpServlet {

    private static final long serialVersionUID = 5925470158886928225L;

    private static String initTime;

    private static int hitCount;

    @Resource(name = "jms/TopicConnectionFactory")
    private ConnectionFactory topicConnectionFactory;

    @Resource(name = "jms/StreamerTopic")
    private Topic tradeStreamerTopic;

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
        output.append("<html><head><title>PingServlet2MDBTopic</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2MDBTopic<BR></FONT>" + "<FONT size=\"-1\" color=\"#000066\">"
                + "Tests the basic operation of a servlet posting a message to an EJB MDB (and other subscribers) through a JMS Topic.<BR>"
                + "<FONT color=\"red\"><B>Note:</B> Not intended for performance testing.</FONT>");

        // we only want to look up the JMS resources once
        try {

            Connection conn = topicConnectionFactory.createConnection();

            try {
                TextMessage message = null;
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    /*Session sess = conn.createSession(false, Session.AUTO_ACKNOWLEDGE);
                    try {
                        MessageProducer producer = sess.createProducer(tradeStreamerTopic);
                        message = sess.createTextMessage();

                        String command = "ping";
                        message.setStringProperty("command", command);
                        message.setLongProperty("publishTime", System.currentTimeMillis());
                        message.setText("Ping message for topic java:comp/env/jms/TradeStreamerTopic sent from PingServlet2MDBTopic at " + new java.util.Date());

                        producer.send(message);
                    } finally {
                        sess.close();
                    }*/
                	
                	JMSContext context = topicConnectionFactory.createContext();
            		
            		message = context.createTextMessage();

            		message.setStringProperty("command", "ping");
                    message.setLongProperty("publishTime", System.currentTimeMillis());
                    message.setText("Ping message for topic java:comp/env/jms/TradeStreamerTopic sent from PingServlet2MDBTopic at " + new java.util.Date());
              		
            		context.createProducer().send(tradeStreamerTopic, message);
                }

                // write out the output
                output.append("<HR>initTime: ").append(initTime);
                output.append("<BR>Hit Count: ").append(hitCount++);
                output.append("<HR>Posted Text message to java:comp/env/jms/TradeStreamerTopic topic");
                output.append("<BR>Message: ").append(message);
                output.append("<BR><BR>Message text: ").append(message.getText());
                output.append("<BR><HR></FONT></BODY></HTML>");
                out.println(output.toString());

            } catch (Exception e) {
                Log.error("PingServlet2MDBTopic.doGet(...):exception posting message to TradeStreamerTopic topic");
                throw e;
            } finally {
                conn.close();
            }
        } // this is where I actually handle the exceptions
        catch (Exception e) {
            Log.error(e, "PingServlet2MDBTopic.doGet(...): error");
            res.sendError(500, "PingServlet2MDBTopic.doGet(...): error, " + e.toString());

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
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2MDBTopic.java:to.<init>
// Node: TradeStreamerMDB
// Node: MDB
// Node: createConnection
// Node: createSession
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

import javax.annotation.Resource;
import javax.jms.Connection;
import javax.jms.ConnectionFactory;
import javax.jms.JMSContext;
import javax.jms.Queue;
import javax.jms.TextMessage;
import javax.servlet.ServletConfig;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import com.ibm.websphere.samples.daytrader.util.Log;
import com.ibm.websphere.samples.daytrader.util.TradeConfig;

/**
 * This primitive is designed to run inside the TradeApplication and relies upon
 * the {@link com.ibm.websphere.samples.daytrader.util.TradeConfig} class to set
 * configuration parameters. PingServlet2MDBQueue tests key functionality of a
 * servlet call to a post a message to an MDB Queue. The TradeBrokerMDB receives
 * the message This servlet makes use of the MDB EJB
 * {@link com.ibm.websphere.samples.daytrader.ejb3.DTBroker3MDB} by posting a
 * message to the MDB Queue
 */
@WebServlet(name = "ejb3.PingServlet2MDBQueue", urlPatterns = { "/ejb3/PingServlet2MDBQueue" })
public class PingServlet2MDBQueue extends HttpServlet {

    private static final long serialVersionUID = 2637271552188745216L;

    private static String initTime;

    private static int hitCount;

    @Resource(name = "jms/QueueConnectionFactory")
    private ConnectionFactory queueConnectionFactory;

    @Resource(name = "jms/BrokerQueue")
    private Queue tradeBrokerQueue;

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
        output.append("<html><head><title>PingServlet2MDBQueue</title></head>"
                + "<body><HR><FONT size=\"+2\" color=\"#000066\">PingServlet2MDBQueue<BR></FONT>" + "<FONT size=\"-1\" color=\"#000066\">"
                + "Tests the basic operation of a servlet posting a message to an EJB MDB through a JMS Queue.<BR>"
                + "<FONT color=\"red\"><B>Note:</B> Not intended for performance testing.</FONT>");

        try {
            Connection conn = queueConnectionFactory.createConnection();

            try {
                TextMessage message = null;
                int iter = TradeConfig.getPrimIterations();
                for (int ii = 0; ii < iter; ii++) {
                    /*Session sess = conn.createSession(false, Session.AUTO_ACKNOWLEDGE);
                    try {
                        MessageProducer producer = sess.createProducer(tradeBrokerQueue);

                        message = sess.createTextMessage();

                        String command = "ping";
                        message.setStringProperty("command", command);
                        message.setLongProperty("publishTime", System.currentTimeMillis());
                        message.setText("Ping message for queue java:comp/env/jms/TradeBrokerQueue sent from PingServlet2MDBQueue at " + new java.util.Date());
                        producer.send(message);
                    } finally {
                        sess.close();
                    }*/
                	
                	JMSContext context = queueConnectionFactory.createContext();
            		
            		message = context.createTextMessage();

            		message.setStringProperty("command", "ping");
                    message.setLongProperty("publishTime", System.currentTimeMillis());
                    message.setText("Ping message for queue java:comp/env/jms/TradeBrokerQueue sent from PingServlet2MDBQueue at " + new java.util.Date());
              		
            		context.createProducer().send(tradeBrokerQueue, message);
                }

                // write out the output
                output.append("<HR>initTime: ").append(initTime);
                output.append("<BR>Hit Count: ").append(hitCount++);
                output.append("<HR>Posted Text message to java:comp/env/jms/TradeBrokerQueue destination");
                output.append("<BR>Message: ").append(message);
                output.append("<BR><BR>Message text: ").append(message.getText());
                output.append("<BR><HR></FONT></BODY></HTML>");
                out.println(output.toString());

            } catch (Exception e) {
                Log.error("PingServlet2MDBQueue.doGet(...):exception posting message to TradeBrokerQueue destination ");
                throw e;
            } finally {
                conn.close();
            }
        } // this is where I actually handle the exceptions
        catch (Exception e) {
            Log.error(e, "PingServlet2MDBQueue.doGet(...): error");
            res.sendError(500, "PingServlet2MDBQueue.doGet(...): error, " + e.toString());

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
    }

}


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/prims/ejb3/PingServlet2MDBQueue.java:to.<init>
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


