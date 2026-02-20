// Cluster 18

// Node: getProperty
// Node: setup
// Node: initMocks
package com.piggymetrics.auth.service;

import com.piggymetrics.auth.domain.User;
import com.piggymetrics.auth.repository.UserRepository;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;

import java.util.Optional;

import static org.mockito.Mockito.*;
import static org.mockito.MockitoAnnotations.initMocks;

public class UserServiceTest {

	@InjectMocks
	private UserServiceImpl userService;

	@Mock
	private UserRepository repository;

	@Before
	public void setup() {
		initMocks(this);
	}

	@Test
	public void shouldCreateUser() {

		User user = new User();
		user.setUsername("name");
		user.setPassword("password");

		userService.create(user);
		verify(repository, times(1)).save(user);
	}

	@Test(expected = IllegalArgumentException.class)
	public void shouldFailWhenUserAlreadyExists() {

		User user = new User();
		user.setUsername("name");
		user.setPassword("password");

		when(repository.findById(user.getUsername())).thenReturn(Optional.of(new User()));
		userService.create(user);
	}
}


package com.piggymetrics.auth.service.security;

import com.piggymetrics.auth.domain.User;
import com.piggymetrics.auth.repository.UserRepository;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;

import java.util.Optional;

import static org.junit.Assert.assertEquals;
import static org.mockito.Matchers.any;
import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;

public class MongoUserDetailsServiceTest {

	@InjectMocks
	private MongoUserDetailsService service;

	@Mock
	private UserRepository repository;

	@Before
	public void setup() {
		initMocks(this);
	}

	@Test
	public void shouldLoadByUsernameWhenUserExists() {

		final User user = new User();

		when(repository.findById(any())).thenReturn(Optional.of(user));
		UserDetails loaded = service.loadUserByUsername("name");

		assertEquals(user, loaded);
	}

	@Test(expected = UsernameNotFoundException.class)
	public void shouldFailToLoadByUsernameWhenUserNotExists() {
		service.loadUserByUsername("name");
	}
}

// Node: hasLength
package com.piggymetrics.statistics.service;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.piggymetrics.statistics.domain.Account;
import com.piggymetrics.statistics.domain.Currency;
import com.piggymetrics.statistics.domain.Item;
import com.piggymetrics.statistics.domain.Saving;
import com.piggymetrics.statistics.domain.TimePeriod;
import com.piggymetrics.statistics.domain.timeseries.DataPoint;
import com.piggymetrics.statistics.domain.timeseries.ItemMetric;
import com.piggymetrics.statistics.domain.timeseries.StatisticMetric;
import com.piggymetrics.statistics.repository.DataPointRepository;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.mockito.AdditionalAnswers.returnsFirstArg;
import static org.mockito.Mockito.any;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;

public class StatisticsServiceImplTest {

	@InjectMocks
	private StatisticsServiceImpl statisticsService;

	@Mock
	private ExchangeRatesServiceImpl ratesService;

	@Mock
	private DataPointRepository repository;

	@Before
	public void setup() {
		initMocks(this);
	}

	@Test
	public void shouldFindDataPointListByAccountName() {
		final List<DataPoint> list = ImmutableList.of(new DataPoint());
		when(repository.findByIdAccount("test")).thenReturn(list);

		List<DataPoint> result = statisticsService.findByAccountName("test");
		assertEquals(list, result);
	}

	@Test(expected = IllegalArgumentException.class)
	public void shouldFailToFindDataPointWhenAccountNameIsNull() {
		statisticsService.findByAccountName(null);
	}

	@Test(expected = IllegalArgumentException.class)
	public void shouldFailToFindDataPointWhenAccountNameIsEmpty() {
		statisticsService.findByAccountName("");
	}

	@Test
	public void shouldSaveDataPoint() {

		/**
		 * Given
		 */

		Item salary = new Item();
		salary.setTitle("Salary");
		salary.setAmount(new BigDecimal(9100));
		salary.setCurrency(Currency.USD);
		salary.setPeriod(TimePeriod.MONTH);

		Item grocery = new Item();
		grocery.setTitle("Grocery");
		grocery.setAmount(new BigDecimal(500));
		grocery.setCurrency(Currency.RUB);
		grocery.setPeriod(TimePeriod.DAY);

		Item vacation = new Item();
		vacation.setTitle("Vacation");
		vacation.setAmount(new BigDecimal(3400));
		vacation.setCurrency(Currency.EUR);
		vacation.setPeriod(TimePeriod.YEAR);

		Saving saving = new Saving();
		saving.setAmount(new BigDecimal(1000));
		saving.setCurrency(Currency.EUR);
		saving.setInterest(new BigDecimal(3.2));
		saving.setDeposit(true);
		saving.setCapitalization(false);

		Account account = new Account();
		account.setIncomes(ImmutableList.of(salary));
		account.setExpenses(ImmutableList.of(grocery, vacation));
		account.setSaving(saving);

		final Map<Currency, BigDecimal> rates = ImmutableMap.of(
				Currency.EUR, new BigDecimal("0.8"),
				Currency.RUB, new BigDecimal("80"),
				Currency.USD, BigDecimal.ONE
		);

		/**
		 * When
		 */

		when(ratesService.convert(any(Currency.class),any(Currency.class),any(BigDecimal.class)))
				.then(i -> ((BigDecimal)i.getArgument(2))
						.divide(rates.get(i.getArgument(0)), 4, RoundingMode.HALF_UP));

		when(ratesService.getCurrentRates()).thenReturn(rates);

		when(repository.save(any(DataPoint.class))).then(returnsFirstArg());

		DataPoint dataPoint = statisticsService.save("test", account);

		/**
		 * Then
		 */

		final BigDecimal expectedExpensesAmount = new BigDecimal("17.8861");
		final BigDecimal expectedIncomesAmount = new BigDecimal("298.9802");
		final BigDecimal expectedSavingAmount = new BigDecimal("1250");

		final BigDecimal expectedNormalizedSalaryAmount = new BigDecimal("298.9802");
		final BigDecimal expectedNormalizedVacationAmount = new BigDecimal("11.6361");
		final BigDecimal expectedNormalizedGroceryAmount = new BigDecimal("6.25");

		assertEquals(dataPoint.getId().getAccount(), "test");
		assertEquals(dataPoint.getId().getDate(), Date.from(LocalDate.now().atStartOfDay().atZone(ZoneId.systemDefault()).toInstant()));

		assertTrue(expectedExpensesAmount.compareTo(dataPoint.getStatistics().get(StatisticMetric.EXPENSES_AMOUNT)) == 0);
		assertTrue(expectedIncomesAmount.compareTo(dataPoint.getStatistics().get(StatisticMetric.INCOMES_AMOUNT)) == 0);
		assertTrue(expectedSavingAmount.compareTo(dataPoint.getStatistics().get(StatisticMetric.SAVING_AMOUNT)) == 0);

		ItemMetric salaryItemMetric = dataPoint.getIncomes().stream()
				.filter(i -> i.getTitle().equals(salary.getTitle()))
				.findFirst().get();

		ItemMetric vacationItemMetric = dataPoint.getExpenses().stream()
				.filter(i -> i.getTitle().equals(vacation.getTitle()))
				.findFirst().get();

		ItemMetric groceryItemMetric = dataPoint.getExpenses().stream()
				.filter(i -> i.getTitle().equals(grocery.getTitle()))
				.findFirst().get();

		assertTrue(expectedNormalizedSalaryAmount.compareTo(salaryItemMetric.getAmount()) == 0);
		assertTrue(expectedNormalizedVacationAmount.compareTo(vacationItemMetric.getAmount()) == 0);
		assertTrue(expectedNormalizedGroceryAmount.compareTo(groceryItemMetric.getAmount()) == 0);

		assertEquals(rates, dataPoint.getRates());

		verify(repository, times(1)).save(dataPoint);
	}
}

package com.piggymetrics.statistics.service;

import com.google.common.collect.ImmutableMap;
import com.piggymetrics.statistics.client.ExchangeRatesClient;
import com.piggymetrics.statistics.domain.Currency;
import com.piggymetrics.statistics.domain.ExchangeRatesContainer;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;

import java.math.BigDecimal;
import java.util.Map;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;
import static org.mockito.Mockito.*;
import static org.mockito.MockitoAnnotations.initMocks;

public class ExchangeRatesServiceImplTest {

	@InjectMocks
	private ExchangeRatesServiceImpl ratesService;

	@Mock
	private ExchangeRatesClient client;

	@Before
	public void setup() {
		initMocks(this);
	}

	@Test
	public void shouldReturnCurrentRatesWhenContainerIsEmptySoFar() {

		ExchangeRatesContainer container = new ExchangeRatesContainer();
		container.setRates(ImmutableMap.of(
				Currency.EUR.name(), new BigDecimal("0.8"),
				Currency.RUB.name(), new BigDecimal("80")
		));

		when(client.getRates(Currency.getBase())).thenReturn(container);

		Map<Currency, BigDecimal> result = ratesService.getCurrentRates();
		verify(client, times(1)).getRates(Currency.getBase());

		assertEquals(container.getRates().get(Currency.EUR.name()), result.get(Currency.EUR));
		assertEquals(container.getRates().get(Currency.RUB.name()), result.get(Currency.RUB));
		assertEquals(BigDecimal.ONE, result.get(Currency.USD));
	}

	@Test
	public void shouldNotRequestRatesWhenTodaysContainerAlreadyExists() {

		ExchangeRatesContainer container = new ExchangeRatesContainer();
		container.setRates(ImmutableMap.of(
				Currency.EUR.name(), new BigDecimal("0.8"),
				Currency.RUB.name(), new BigDecimal("80")
		));

		when(client.getRates(Currency.getBase())).thenReturn(container);

		// initialize container
		ratesService.getCurrentRates();

		// use existing container
		ratesService.getCurrentRates();

		verify(client, times(1)).getRates(Currency.getBase());
	}

	@Test
	public void shouldConvertCurrency() {

		ExchangeRatesContainer container = new ExchangeRatesContainer();
		container.setRates(ImmutableMap.of(
				Currency.EUR.name(), new BigDecimal("0.8"),
				Currency.RUB.name(), new BigDecimal("80")
		));

		when(client.getRates(Currency.getBase())).thenReturn(container);

		final BigDecimal amount = new BigDecimal(100);
		final BigDecimal expectedConvertionResult = new BigDecimal("1.25");

		BigDecimal result = ratesService.convert(Currency.RUB, Currency.USD, amount);

		assertTrue(expectedConvertionResult.compareTo(result) == 0);
	}

	@Test(expected = IllegalArgumentException.class)
	public void shouldFailToConvertWhenAmountIsNull() {
		ratesService.convert(Currency.EUR, Currency.RUB, null);
	}
}

package com.piggymetrics.account.service;

import com.piggymetrics.account.client.AuthServiceClient;
import com.piggymetrics.account.client.StatisticsServiceClient;
import com.piggymetrics.account.domain.Account;
import com.piggymetrics.account.domain.Currency;
import com.piggymetrics.account.domain.Saving;
import com.piggymetrics.account.domain.User;
import com.piggymetrics.account.repository.AccountRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

import java.math.BigDecimal;
import java.util.Date;

@Service
public class AccountServiceImpl implements AccountService {

	private final Logger log = LoggerFactory.getLogger(getClass());

	@Autowired
	private StatisticsServiceClient statisticsClient;

	@Autowired
	private AuthServiceClient authClient;

	@Autowired
	private AccountRepository repository;

	/**
	 * {@inheritDoc}
	 */
	@Override
	public Account findByName(String accountName) {
		Assert.hasLength(accountName);
		return repository.findByName(accountName);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	public Account create(User user) {

		Account existing = repository.findByName(user.getUsername());
		Assert.isNull(existing, "account already exists: " + user.getUsername());

		authClient.createUser(user);

		Saving saving = new Saving();
		saving.setAmount(new BigDecimal(0));
		saving.setCurrency(Currency.getDefault());
		saving.setInterest(new BigDecimal(0));
		saving.setDeposit(false);
		saving.setCapitalization(false);

		Account account = new Account();
		account.setName(user.getUsername());
		account.setLastSeen(new Date());
		account.setSaving(saving);

		repository.save(account);

		log.info("new account has been created: " + account.getName());

		return account;
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	public void saveChanges(String name, Account update) {

		Account account = repository.findByName(name);
		Assert.notNull(account, "can't find account with name " + name);

		account.setIncomes(update.getIncomes());
		account.setExpenses(update.getExpenses());
		account.setSaving(update.getSaving());
		account.setNote(update.getNote());
		account.setLastSeen(new Date());
		repository.save(account);

		log.debug("account {} changes has been saved", name);

		statisticsClient.updateStatistics(name, account);
	}
}


package com.piggymetrics.account.service;

import com.piggymetrics.account.client.AuthServiceClient;
import com.piggymetrics.account.client.StatisticsServiceClient;
import com.piggymetrics.account.domain.*;
import com.piggymetrics.account.repository.AccountRepository;
import org.junit.Before;
import org.junit.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;

import java.math.BigDecimal;
import java.util.Arrays;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.mockito.Mockito.*;
import static org.mockito.MockitoAnnotations.initMocks;

public class AccountServiceTest {

	@InjectMocks
	private AccountServiceImpl accountService;

	@Mock
	private StatisticsServiceClient statisticsClient;

	@Mock
	private AuthServiceClient authClient;

	@Mock
	private AccountRepository repository;

	@Before
	public void setup() {
		initMocks(this);
	}

	@Test
	public void shouldFindByName() {

		final Account account = new Account();
		account.setName("test");

		when(accountService.findByName(account.getName())).thenReturn(account);
		Account found = accountService.findByName(account.getName());

		assertEquals(account, found);
	}

	@Test(expected = IllegalArgumentException.class)
	public void shouldFailWhenNameIsEmpty() {
		accountService.findByName("");
	}

	@Test
	public void shouldCreateAccountWithGivenUser() {

		User user = new User();
		user.setUsername("test");

		Account account = accountService.create(user);

		assertEquals(user.getUsername(), account.getName());
		assertEquals(0, account.getSaving().getAmount().intValue());
		assertEquals(Currency.getDefault(), account.getSaving().getCurrency());
		assertEquals(0, account.getSaving().getInterest().intValue());
		assertEquals(false, account.getSaving().getDeposit());
		assertEquals(false, account.getSaving().getCapitalization());
		assertNotNull(account.getLastSeen());

		verify(authClient, times(1)).createUser(user);
		verify(repository, times(1)).save(account);
	}

	@Test
	public void shouldSaveChangesWhenUpdatedAccountGiven() {

		Item grocery = new Item();
		grocery.setTitle("Grocery");
		grocery.setAmount(new BigDecimal(10));
		grocery.setCurrency(Currency.USD);
		grocery.setPeriod(TimePeriod.DAY);
		grocery.setIcon("meal");

		Item salary = new Item();
		salary.setTitle("Salary");
		salary.setAmount(new BigDecimal(9100));
		salary.setCurrency(Currency.USD);
		salary.setPeriod(TimePeriod.MONTH);
		salary.setIcon("wallet");

		Saving saving = new Saving();
		saving.setAmount(new BigDecimal(1500));
		saving.setCurrency(Currency.USD);
		saving.setInterest(new BigDecimal("3.32"));
		saving.setDeposit(true);
		saving.setCapitalization(false);

		final Account update = new Account();
		update.setName("test");
		update.setNote("test note");
		update.setIncomes(Arrays.asList(salary));
		update.setExpenses(Arrays.asList(grocery));
		update.setSaving(saving);

		final Account account = new Account();

		when(accountService.findByName("test")).thenReturn(account);
		accountService.saveChanges("test", update);

		assertEquals(update.getNote(), account.getNote());
		assertNotNull(account.getLastSeen());

		assertEquals(update.getSaving().getAmount(), account.getSaving().getAmount());
		assertEquals(update.getSaving().getCurrency(), account.getSaving().getCurrency());
		assertEquals(update.getSaving().getInterest(), account.getSaving().getInterest());
		assertEquals(update.getSaving().getDeposit(), account.getSaving().getDeposit());
		assertEquals(update.getSaving().getCapitalization(), account.getSaving().getCapitalization());

		assertEquals(update.getExpenses().size(), account.getExpenses().size());
		assertEquals(update.getIncomes().size(), account.getIncomes().size());

		assertEquals(update.getExpenses().get(0).getTitle(), account.getExpenses().get(0).getTitle());
		assertEquals(0, update.getExpenses().get(0).getAmount().compareTo(account.getExpenses().get(0).getAmount()));
		assertEquals(update.getExpenses().get(0).getCurrency(), account.getExpenses().get(0).getCurrency());
		assertEquals(update.getExpenses().get(0).getPeriod(), account.getExpenses().get(0).getPeriod());
		assertEquals(update.getExpenses().get(0).getIcon(), account.getExpenses().get(0).getIcon());
		
		assertEquals(update.getIncomes().get(0).getTitle(), account.getIncomes().get(0).getTitle());
		assertEquals(0, update.getIncomes().get(0).getAmount().compareTo(account.getIncomes().get(0).getAmount()));
		assertEquals(update.getIncomes().get(0).getCurrency(), account.getIncomes().get(0).getCurrency());
		assertEquals(update.getIncomes().get(0).getPeriod(), account.getIncomes().get(0).getPeriod());
		assertEquals(update.getIncomes().get(0).getIcon(), account.getIncomes().get(0).getIcon());
		
		verify(repository, times(1)).save(account);
		verify(statisticsClient, times(1)).updateStatistics("test", account);
	}

	@Test(expected = IllegalArgumentException.class)
	public void shouldFailWhenNoAccountsExistedWithGivenName() {
		final Account update = new Account();
		update.setIncomes(Arrays.asList(new Item()));
		update.setExpenses(Arrays.asList(new Item()));

		when(accountService.findByName("test")).thenReturn(null);
		accountService.saveChanges("test", update);
	}
}


package com.piggymetrics.account.client;

import com.piggymetrics.account.domain.Account;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.rule.OutputCapture;
import org.springframework.test.context.junit4.SpringRunner;

import static org.hamcrest.Matchers.containsString;

/**
 * @author cdov
 */
@RunWith(SpringRunner.class)
@SpringBootTest(properties = {
        "feign.hystrix.enabled=true"
})
public class StatisticsServiceClientFallbackTest {
    @Autowired
    private StatisticsServiceClient statisticsServiceClient;

    @Rule
    public final OutputCapture outputCapture = new OutputCapture();

    @Before
    public void setup() {
        outputCapture.reset();
    }

    @Test
    public void testUpdateStatisticsWithFailFallback(){
        statisticsServiceClient.updateStatistics("test", new Account());

        outputCapture.expect(containsString("Error during update statistics for account: test"));

    }

}



// Node: reset
package com.piggymetrics.notification.service;

import com.piggymetrics.notification.domain.NotificationType;
import com.piggymetrics.notification.domain.Recipient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.core.env.Environment;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import javax.mail.MessagingException;
import javax.mail.internet.MimeMessage;
import java.io.IOException;
import java.text.MessageFormat;

@Service
@RefreshScope
public class EmailServiceImpl implements EmailService {

	private final Logger log = LoggerFactory.getLogger(getClass());

	@Autowired
	private JavaMailSender mailSender;

	@Autowired
	private Environment env;

	@Override
	public void send(NotificationType type, Recipient recipient, String attachment) throws MessagingException, IOException {

		final String subject = env.getProperty(type.getSubject());
		final String text = MessageFormat.format(env.getProperty(type.getText()), recipient.getAccountName());

		MimeMessage message = mailSender.createMimeMessage();

		MimeMessageHelper helper = new MimeMessageHelper(message, true);
		helper.setTo(recipient.getEmail());
		helper.setSubject(subject);
		helper.setText(text);

		if (StringUtils.hasLength(attachment)) {
			helper.addAttachment(env.getProperty(type.getAttachment()), new ByteArrayResource(attachment.getBytes()));
		}

		mailSender.send(message);

		log.info("{} email notification has been send to {}", type, recipient.getEmail());
	}
}


// Node: repos/cloned_ms_repos/piggymetrics/notification-service/src/main/java/com/piggymetrics/notification/service/EmailServiceImpl.java:EmailServiceImpl.<init>
// Node: getSubject
// Node: format
// Node: getText
// Node: createMimeMessage
// Node: MimeMessageHelper
// Node: setTo
// Node: getEmail
// Node: setSubject
// Node: setText
// Node: addAttachment
// Node: getAttachment
// Node: ByteArrayResource
// Node: getBytes
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

public enum NotificationType {

	BACKUP("backup.email.subject", "backup.email.text", "backup.email.attachment"),
	REMIND("remind.email.subject", "remind.email.text", null);

	private String subject;
	private String text;
	private String attachment;

	NotificationType(String subject, String text, String attachment) {
		this.subject = subject;
		this.text = text;
		this.attachment = attachment;
	}

	public String getSubject() {
		return subject;
	}

	public String getText() {
		return text;
	}

	public String getAttachment() {
		return attachment;
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

package com.piggymetrics.notification.service;

import com.piggymetrics.notification.domain.NotificationType;
import com.piggymetrics.notification.domain.Recipient;
import org.junit.Before;
import org.junit.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Captor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.springframework.core.env.Environment;
import org.springframework.mail.javamail.JavaMailSender;

import javax.mail.MessagingException;
import javax.mail.Session;
import javax.mail.internet.MimeMessage;
import java.io.IOException;
import java.util.Properties;

import static org.junit.Assert.assertEquals;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.mockito.MockitoAnnotations.initMocks;

public class EmailServiceImplTest {

	@InjectMocks
	private EmailServiceImpl emailService;

	@Mock
	private JavaMailSender mailSender;

	@Mock
	private Environment env;

	@Captor
	private ArgumentCaptor<MimeMessage> captor;

	@Before
	public void setup() {
		initMocks(this);
		when(mailSender.createMimeMessage())
				.thenReturn(new MimeMessage(Session.getDefaultInstance(new Properties())));
	}

	@Test
	public void shouldSendBackupEmail() throws MessagingException, IOException {

		final String subject = "subject";
		final String text = "text";
		final String attachment = "attachment.json";

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");

		when(env.getProperty(NotificationType.BACKUP.getSubject())).thenReturn(subject);
		when(env.getProperty(NotificationType.BACKUP.getText())).thenReturn(text);
		when(env.getProperty(NotificationType.BACKUP.getAttachment())).thenReturn(attachment);

		emailService.send(NotificationType.BACKUP, recipient, "{\"name\":\"test\"");

		verify(mailSender).send(captor.capture());

		MimeMessage message = captor.getValue();
		assertEquals(subject, message.getSubject());
		// TODO check other fields
	}

	@Test
	public void shouldSendRemindEmail() throws MessagingException, IOException {

		final String subject = "subject";
		final String text = "text";

		Recipient recipient = new Recipient();
		recipient.setAccountName("test");
		recipient.setEmail("test@test.com");

		when(env.getProperty(NotificationType.REMIND.getSubject())).thenReturn(subject);
		when(env.getProperty(NotificationType.REMIND.getText())).thenReturn(text);

		emailService.send(NotificationType.REMIND, recipient, null);

		verify(mailSender).send(captor.capture());

		MimeMessage message = captor.getValue();
		assertEquals(subject, message.getSubject());
		// TODO check other fields
	}
}

// Node: MimeMessage
// Node: getDefaultInstance
// Node: Properties
// Node: shouldSendBackupEmail
// Node: capture
// Node: shouldSendRemindEmail
