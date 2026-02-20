// Cluster 12

// Node: QuoteDataBean
// Node: setPurchaseDate
// Node: setHolding
// Node: setCompletionDate
// Node: setAddress
// Node: setPassword
// Node: setFullName
// Node: setCreditCard
// Node: setEmail
// Node: setAccount
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

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/entities/AccountDataBean.java:AccountDataBean.<init>
// Node: Entity
// Node: Table
// Node: TableGenerator
// Node: GeneratedValue
// Node: Column
// Node: Temporal
// Node: OneToMany
// Node: OneToOne
// Node: JoinColumn
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


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/entities/HoldingDataBean.java:HoldingDataBean.<init>
// Node: Holding
// Node: Quote
// Node: ManyToOne
// Node: setHoldingID
// Node: setQuantity
// Node: setPurchasePrice
// Node: setQuoteID
// Node: setQuote
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

// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/entities/QuoteDataBean.java:QuoteDataBean.<init>
// Node: NamedQueries
// Node: NamedQuery
// Node: NamedNativeQueries
// Node: NamedNativeQuery
// Node: setSymbol
// Node: setCompanyName
// Node: setOpen
// Node: setLow
// Node: setHigh
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


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/entities/AccountProfileDataBean.java:AccountProfileDataBean.<init>
// Node: setUserID
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


// Node: repos/cloned_ms_repos/sample.daytrader7/daytrader-ee7-ejb/src/main/java/com/ibm/websphere/samples/daytrader/entities/OrderDataBean.java:OrderDataBean.<init>
// Node: orderType
// Node: orderStatus
// Node: openDate
// Node: setOrderID
// Node: setOrderType
// Node: setOpenDate
// Node: setOrderFee
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


