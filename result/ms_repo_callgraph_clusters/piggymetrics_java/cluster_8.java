// Cluster 8

package com.piggymetrics.statistics.domain;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true, value = {"date"})
public class ExchangeRatesContainer {

	private LocalDate date = LocalDate.now();

	private Currency base;

	private Map<String, BigDecimal> rates;

	public LocalDate getDate() {
		return date;
	}

	public void setDate(LocalDate date) {
		this.date = date;
	}

	public Currency getBase() {
		return base;
	}

	public void setBase(Currency base) {
		this.base = base;
	}

	public Map<String, BigDecimal> getRates() {
		return rates;
	}

	public void setRates(Map<String, BigDecimal> rates) {
		this.rates = rates;
	}

	@Override
	public String toString() {
		return "RateList{" +
				"date=" + date +
				", base=" + base +
				", rates=" + rates +
				'}';
	}
}


// Node: toString
package com.piggymetrics.statistics.domain.timeseries;

import java.io.Serializable;
import java.util.Date;

public class DataPointId implements Serializable {

	private static final long serialVersionUID = 1L;

	private String account;

	private Date date;

	public DataPointId(String account, Date date) {
		this.account = account;
		this.date = date;
	}

	public String getAccount() {
		return account;
	}

	public Date getDate() {
		return date;
	}

	@Override
	public String toString() {
		return "DataPointId{" +
				"account='" + account + '\'' +
				", date=" + date +
				'}';
	}
}


package com.piggymetrics.notification.domain;

import org.hibernate.validator.constraints.Email;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Map;

@Document(collection = "recipients")
public class Recipient {

	@Id
	private String accountName;

	@NotNull
	@Email
	private String email;

	@Valid
	private Map<NotificationType, NotificationSettings> scheduledNotifications;

	public String getAccountName() {
		return accountName;
	}

	public void setAccountName(String accountName) {
		this.accountName = accountName;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public Map<NotificationType, NotificationSettings> getScheduledNotifications() {
		return scheduledNotifications;
	}

	public void setScheduledNotifications(Map<NotificationType, NotificationSettings> scheduledNotifications) {
		this.scheduledNotifications = scheduledNotifications;
	}

	@Override
	public String toString() {
		return "Recipient{" +
				"accountName='" + accountName + '\'' +
				", email='" + email + '\'' +
				'}';
	}
}


