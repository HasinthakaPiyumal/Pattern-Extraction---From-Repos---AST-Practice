// Cluster 23

// Node: of
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


// Node: setDate
// Node: filter
// Node: findFirst
package com.piggymetrics.notification.repository;

import com.piggymetrics.notification.domain.Recipient;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface RecipientRepository extends CrudRepository<Recipient, String> {

	Recipient findByAccountName(String name);

	@Query("{ $and: [ {'scheduledNotifications.BACKUP.active': true }, { $where: 'this.scheduledNotifications.BACKUP.lastNotified < " +
			"new Date(new Date().setDate(new Date().getDate() - this.scheduledNotifications.BACKUP.frequency ))' }] }")
	List<Recipient> findReadyForBackup();

	@Query("{ $and: [ {'scheduledNotifications.REMIND.active': true }, { $where: 'this.scheduledNotifications.REMIND.lastNotified < " +
			"new Date(new Date().setDate(new Date().getDate() - this.scheduledNotifications.REMIND.frequency ))' }] }")
	List<Recipient> findReadyForRemind();

}


// Node: repos/cloned_ms_repos/piggymetrics/notification-service/src/main/java/com/piggymetrics/notification/repository/RecipientRepository.java:RecipientRepository.<init>
// Node: Query
// Node: findReadyForBackup
// Node: findReadyForRemind
// Node: setAccountName
// Node: getScheduledNotifications
// Node: values
// Node: getLastNotified
// Node: setLastNotified
package com.piggymetrics.notification.service;

import com.piggymetrics.notification.domain.NotificationType;
import com.piggymetrics.notification.domain.Recipient;
import com.piggymetrics.notification.repository.RecipientRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

import java.util.Date;
import java.util.List;

@Service
public class RecipientServiceImpl implements RecipientService {

	private final Logger log = LoggerFactory.getLogger(getClass());

	@Autowired
	private RecipientRepository repository;

	@Override
	public Recipient findByAccountName(String accountName) {
		Assert.hasLength(accountName);
		return repository.findByAccountName(accountName);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	public Recipient save(String accountName, Recipient recipient) {

		recipient.setAccountName(accountName);
		recipient.getScheduledNotifications().values()
				.forEach(settings -> {
					if (settings.getLastNotified() == null) {
						settings.setLastNotified(new Date());
					}
				});

		repository.save(recipient);

		log.info("recipient {} settings has been updated", recipient);

		return recipient;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	public List<Recipient> findReadyToNotify(NotificationType type) {
		switch (type) {
			case BACKUP:
				return repository.findReadyForBackup();
			case REMIND:
				return repository.findReadyForRemind();
			default:
				throw new IllegalArgumentException();
		}
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	public void markNotified(NotificationType type, Recipient recipient) {
		recipient.getScheduledNotifications().get(type).setLastNotified(new Date());
		repository.save(recipient);
	}
}


package com.piggymetrics.notification.domain;

import javax.validation.constraints.NotNull;
import java.util.Date;

public class NotificationSettings {

	@NotNull
	private Boolean active;

	@NotNull
	private Frequency frequency;

	private Date lastNotified;

	public Boolean getActive() {
		return active;
	}

	public void setActive(Boolean active) {
		this.active = active;
	}

	public Frequency getFrequency() {
		return frequency;
	}

	public void setFrequency(Frequency frequency) {
		this.frequency = frequency;
	}

	public Date getLastNotified() {
		return lastNotified;
	}

	public void setLastNotified(Date lastNotified) {
		this.lastNotified = lastNotified;
	}
}


// Node: getActive
// Node: setActive
// Node: getFrequency
// Node: setFrequency
package com.piggymetrics.notification.domain;

import java.util.stream.Stream;

public enum Frequency {

	WEEKLY(7), MONTHLY(30), QUARTERLY(90);

	private int days;

	Frequency(int days) {
		this.days = days;
	}

	public int getDays() {
		return days;
	}

	public static Frequency withDays(int days) {
		return Stream.of(Frequency.values())
				.filter(f -> f.getDays() == days)
				.findFirst()
				.orElseThrow(IllegalArgumentException::new);
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


// Node: setEmail
// Node: setScheduledNotifications
// Node: getStubRecipient
package com.piggymetrics.notification.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.collect.ImmutableMap;
import com.piggymetrics.notification.domain.Frequency;
import com.piggymetrics.notification.domain.NotificationSettings;
import com.piggymetrics.notification.domain.NotificationType;
import com.piggymetrics.notification.domain.Recipient;
import com.piggymetrics.notification.service.RecipientService;
import com.sun.security.auth.UserPrincipal;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@RunWith(SpringRunner.class)
@SpringBootTest
public class RecipientControllerTest {

	private static final ObjectMapper mapper = new ObjectMapper();

	@InjectMocks
	private RecipientController recipientController;

	@Mock
	private RecipientService recipientService;

	private MockMvc mockMvc;

	@Before
	public void setup() {
		initMocks(this);
		this.mockMvc = MockMvcBuilders.standaloneSetup(recipientController).build();
	}

	@Test
	public void shouldSaveCurrentRecipientSettings() throws Exception {

		Recipient recipient = getStubRecipient();
		String json = mapper.writeValueAsString(recipient);

		mockMvc.perform(put("/recipients/current").principal(new UserPrincipal(recipient.getAccountName())).contentType(MediaType.APPLICATION_JSON).content(json))
				.andExpect(status().isOk());
	}

	@Test
	public void shouldGetCurrentRecipientSettings() throws Exception {

		Recipient recipient = getStubRecipient();
		when(recipientService.findByAccountName(recipient.getAccountName())).thenReturn(recipient);

		mockMvc.perform(get("/recipients/current").principal(new UserPrincipal(recipient.getAccountName())))
				.andExpect(jsonPath("$.accountName").value(recipient.getAccountName()))
				.andExpect(status().isOk());
	}

	private Recipient getStubRecipient() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(true);
		remind.setFrequency(Frequency.WEEKLY);
		remind.setLastNotified(null);

		NotificationSettings backup = new NotificationSettings();
		backup.setActive(false);
		backup.setFrequency(Frequency.MONTHLY);
		backup.setLastNotified(null);

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.BACKUP, backup,
				NotificationType.REMIND, remind
		));

		return recipient;
	}
}

// Node: NotificationSettings
// Node: Recipient
package com.piggymetrics.notification.repository;

import com.google.common.collect.ImmutableMap;
import com.piggymetrics.notification.domain.Frequency;
import com.piggymetrics.notification.domain.NotificationSettings;
import com.piggymetrics.notification.domain.NotificationType;
import com.piggymetrics.notification.domain.Recipient;
import org.apache.commons.lang.time.DateUtils;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Date;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

@RunWith(SpringRunner.class)
@DataMongoTest
public class RecipientRepositoryTest {

	@Autowired
	private RecipientRepository repository;

	@Test
	public void shouldFindByAccountName() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(true);
		remind.setFrequency(Frequency.WEEKLY);
		remind.setLastNotified(new Date(0));

		NotificationSettings backup = new NotificationSettings();
		backup.setActive(false);
		backup.setFrequency(Frequency.MONTHLY);
		backup.setLastNotified(new Date());

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.BACKUP, backup,
				NotificationType.REMIND, remind
		));

		repository.save(recipient);

		Recipient found = repository.findByAccountName(recipient.getAccountName());
		assertEquals(recipient.getAccountName(), found.getAccountName());
		assertEquals(recipient.getEmail(), found.getEmail());

		assertEquals(recipient.getScheduledNotifications().get(NotificationType.BACKUP).getActive(),
				found.getScheduledNotifications().get(NotificationType.BACKUP).getActive());
		assertEquals(recipient.getScheduledNotifications().get(NotificationType.BACKUP).getFrequency(),
				found.getScheduledNotifications().get(NotificationType.BACKUP).getFrequency());
		assertEquals(recipient.getScheduledNotifications().get(NotificationType.BACKUP).getLastNotified(),
				found.getScheduledNotifications().get(NotificationType.BACKUP).getLastNotified());

		assertEquals(recipient.getScheduledNotifications().get(NotificationType.REMIND).getActive(),
				found.getScheduledNotifications().get(NotificationType.REMIND).getActive());
		assertEquals(recipient.getScheduledNotifications().get(NotificationType.REMIND).getFrequency(),
				found.getScheduledNotifications().get(NotificationType.REMIND).getFrequency());
		assertEquals(recipient.getScheduledNotifications().get(NotificationType.REMIND).getLastNotified(),
				found.getScheduledNotifications().get(NotificationType.REMIND).getLastNotified());
	}

	@Test
	public void shouldFindReadyForRemindWhenFrequencyIsWeeklyAndLastNotifiedWas8DaysAgo() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(true);
		remind.setFrequency(Frequency.WEEKLY);
		remind.setLastNotified(DateUtils.addDays(new Date(), -8));

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.REMIND, remind
		));

		repository.save(recipient);

		List<Recipient> found = repository.findReadyForRemind();
		assertFalse(found.isEmpty());
	}

	@Test
	public void shouldNotFindReadyForRemindWhenFrequencyIsWeeklyAndLastNotifiedWasYesterday() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(true);
		remind.setFrequency(Frequency.WEEKLY);
		remind.setLastNotified(DateUtils.addDays(new Date(), -1));

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.REMIND, remind
		));

		repository.save(recipient);

		List<Recipient> found = repository.findReadyForRemind();
		assertTrue(found.isEmpty());
	}

	@Test
	public void shouldNotFindReadyForRemindWhenNotificationIsNotActive() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(false);
		remind.setFrequency(Frequency.WEEKLY);
		remind.setLastNotified(DateUtils.addDays(new Date(), -30));

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.REMIND, remind
		));

		repository.save(recipient);

		List<Recipient> found = repository.findReadyForRemind();
		assertTrue(found.isEmpty());
	}

	@Test
	public void shouldNotFindReadyForBackupWhenFrequencyIsQuaterly() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(true);
		remind.setFrequency(Frequency.QUARTERLY);
		remind.setLastNotified(DateUtils.addDays(new Date(), -91));

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.BACKUP, remind
		));

		repository.save(recipient);

		List<Recipient> found = repository.findReadyForBackup();
		assertFalse(found.isEmpty());
	}
}

// Node: shouldFindByAccountName
// Node: shouldFindReadyForRemindWhenFrequencyIsWeeklyAndLastNotifiedWas8DaysAgo
// Node: addDays
// Node: assertFalse
// Node: isEmpty
// Node: shouldNotFindReadyForRemindWhenFrequencyIsWeeklyAndLastNotifiedWasYesterday
// Node: shouldNotFindReadyForRemindWhenNotificationIsNotActive
// Node: shouldNotFindReadyForBackupWhenFrequencyIsQuaterly
package com.piggymetrics.notification.service;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.piggymetrics.notification.domain.Frequency;
import com.piggymetrics.notification.domain.NotificationSettings;
import com.piggymetrics.notification.domain.NotificationType;
import com.piggymetrics.notification.domain.Recipient;
import com.piggymetrics.notification.repository.RecipientRepository;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;

import java.util.Date;
import java.util.List;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;

public class RecipientServiceImplTest {

	@InjectMocks
	private RecipientServiceImpl recipientService;

	@Mock
	private RecipientRepository repository;

	@Before
	public void setup() {
		initMocks(this);
	}

	@Test
	public void shouldFindByAccountName() {
		Recipient recipient = new Recipient();
		recipient.setAccountName("test");

		when(repository.findByAccountName(recipient.getAccountName())).thenReturn(recipient);
		Recipient found = recipientService.findByAccountName(recipient.getAccountName());

		assertEquals(recipient, found);
	}

	@Test(expected = IllegalArgumentException.class)
	public void shouldFailToFindRecipientWhenAccountNameIsEmpty() {
		recipientService.findByAccountName("");
	}

	@Test
	public void shouldSaveRecipient() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(true);
		remind.setFrequency(Frequency.WEEKLY);
		remind.setLastNotified(null);

		NotificationSettings backup = new NotificationSettings();
		backup.setActive(false);
		backup.setFrequency(Frequency.MONTHLY);
		backup.setLastNotified(new Date());

		Recipient recipient = new Recipient();
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.BACKUP, backup,
				NotificationType.REMIND, remind
		));

		Recipient saved = recipientService.save("test", recipient);

		verify(repository).save(recipient);
		assertNotNull(saved.getScheduledNotifications().get(NotificationType.REMIND).getLastNotified());
		assertEquals("test", saved.getAccountName());
	}

	@Test
	public void shouldFindReadyToNotifyWhenNotificationTypeIsBackup() {
		final List<Recipient> recipients = ImmutableList.of(new Recipient());
		when(repository.findReadyForBackup()).thenReturn(recipients);

		List<Recipient> found = recipientService.findReadyToNotify(NotificationType.BACKUP);
		assertEquals(recipients, found);
	}

	@Test
	public void shouldFindReadyToNotifyWhenNotificationTypeIsRemind() {
		final List<Recipient> recipients = ImmutableList.of(new Recipient());
		when(repository.findReadyForRemind()).thenReturn(recipients);

		List<Recipient> found = recipientService.findReadyToNotify(NotificationType.REMIND);
		assertEquals(recipients, found);
	}

	@Test
	public void shouldMarkAsNotified() {

		NotificationSettings remind = new NotificationSettings();
		remind.setActive(true);
		remind.setFrequency(Frequency.WEEKLY);
		remind.setLastNotified(null);

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");
		recipient.setScheduledNotifications(ImmutableMap.of(
				NotificationType.REMIND, remind
		));

		recipientService.markNotified(NotificationType.REMIND, recipient);
		assertNotNull(recipient.getScheduledNotifications().get(NotificationType.REMIND).getLastNotified());
		verify(repository).save(recipient);
	}
}

// Node: shouldSaveRecipient
// Node: shouldFindReadyToNotifyWhenNotificationTypeIsRemind
// Node: shouldMarkAsNotified
