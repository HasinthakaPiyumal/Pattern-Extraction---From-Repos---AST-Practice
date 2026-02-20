// Cluster 19

// Node: getPrice
// Node: getOpen
// Node: getVolume
// Node: getCompanyName
// Node: getLow
// Node: getHigh
// Node: getChange
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

// Node: setConfigParam
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


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/TradeScenarioServlet.java:TradeScenarioServlet.<init>
// Node: generator
// Node: getInitParameterNames
// Node: hasMoreElements
// Node: nextElement
// Node: getInitParameter
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

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-web/src/main/java/com/ibm/websphere/samples/daytrader/web/TradeAppServlet.java:TradeAppServlet.<init>
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


// Node: setSymbols
// Node: getSymbols
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


// Node: StringTokenizer
// Node: countTokens
// Node: nextToken
// Node: setQuotes
