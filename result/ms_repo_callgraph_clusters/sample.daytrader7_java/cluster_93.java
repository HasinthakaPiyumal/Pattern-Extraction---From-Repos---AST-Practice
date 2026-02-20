// Cluster 93

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


// Node: getSumOfCashHoldings
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


