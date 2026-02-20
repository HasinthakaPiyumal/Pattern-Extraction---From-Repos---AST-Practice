// Cluster 10

// Node: save
package com.piggymetrics.statistics.controller;

import com.piggymetrics.statistics.domain.Account;
import com.piggymetrics.statistics.domain.timeseries.DataPoint;
import com.piggymetrics.statistics.service.StatisticsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.security.Principal;
import java.util.List;

@RestController
public class StatisticsController {

	@Autowired
	private StatisticsService statisticsService;

	@RequestMapping(value = "/current", method = RequestMethod.GET)
	public List<DataPoint> getCurrentAccountStatistics(Principal principal) {
		return statisticsService.findByAccountName(principal.getName());
	}

	@PreAuthorize("#oauth2.hasScope('server') or #accountName.equals('demo')")
	@RequestMapping(value = "/{accountName}", method = RequestMethod.GET)
	public List<DataPoint> getStatisticsByAccountName(@PathVariable String accountName) {
		return statisticsService.findByAccountName(accountName);
	}

	@PreAuthorize("#oauth2.hasScope('server')")
	@RequestMapping(value = "/{accountName}", method = RequestMethod.PUT)
	public void saveAccountStatistics(@PathVariable String accountName, @Valid @RequestBody Account account) {
		statisticsService.save(accountName, account);
	}
}


// Node: saveAccountStatistics
package com.piggymetrics.statistics.repository;

import com.piggymetrics.statistics.domain.timeseries.DataPoint;
import com.piggymetrics.statistics.domain.timeseries.DataPointId;
import org.springframework.data.repository.CrudRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DataPointRepository extends CrudRepository<DataPoint, DataPointId> {

	List<DataPoint> findByIdAccount(String account);

}


// Node: repos/cloned_ms_repos/piggymetrics/statistics-service/src/main/java/com/piggymetrics/statistics/repository/DataPointRepository.java:DataPointRepository.<init>
// Node: findByIdAccount
package com.piggymetrics.statistics.repository.converter;

import com.mongodb.DBObject;
import com.piggymetrics.statistics.domain.timeseries.DataPointId;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

import java.util.Date;

@Component
public class DataPointIdReaderConverter implements Converter<DBObject, DataPointId> {

	@Override
	public DataPointId convert(DBObject object) {

		Date date = (Date) object.get("date");
		String account = (String) object.get("account");

		return new DataPointId(account, date);
	}
}


// Node: convert
// Node: DataPointId
package com.piggymetrics.statistics.repository.converter;

import com.mongodb.BasicDBObject;
import com.mongodb.DBObject;
import com.piggymetrics.statistics.domain.timeseries.DataPointId;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

@Component
public class DataPointIdWriterConverter implements Converter<DataPointId, DBObject> {

	private static final int FIELDS = 2;

	@Override
	public DBObject convert(DataPointId id) {

		DBObject object = new BasicDBObject(FIELDS);

		object.put("date", id.getDate());
		object.put("account", id.getAccount());

		return object;
	}
}


// Node: BasicDBObject
// Node: getAccount
package com.piggymetrics.statistics.service;

import com.piggymetrics.statistics.domain.Currency;

import java.math.BigDecimal;
import java.util.Map;

public interface ExchangeRatesService {

	/**
	 * Requests today's foreign exchange rates from a provider
	 * or reuses values from the last request (if they are still relevant)
	 *
	 * @return current date rates
	 */
	Map<Currency, BigDecimal> getCurrentRates();

	/**
	 * Converts given amount to specified currency
	 *
	 * @param from {@link Currency}
	 * @param to {@link Currency}
	 * @param amount to be converted
	 * @return converted amount
	 */
	BigDecimal convert(Currency from, Currency to, BigDecimal amount);
}


// Node: repos/cloned_ms_repos/piggymetrics/statistics-service/src/main/java/com/piggymetrics/statistics/service/ExchangeRatesService.java:ExchangeRatesService.<init>
// Node: request
// Node: getCurrentRates
package com.piggymetrics.statistics.service;

import com.google.common.collect.ImmutableMap;
import com.piggymetrics.statistics.client.ExchangeRatesClient;
import com.piggymetrics.statistics.domain.Currency;
import com.piggymetrics.statistics.domain.ExchangeRatesContainer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.Map;

@Service
public class ExchangeRatesServiceImpl implements ExchangeRatesService {

	private static final Logger log = LoggerFactory.getLogger(ExchangeRatesServiceImpl.class);

	private ExchangeRatesContainer container;

	@Autowired
	private ExchangeRatesClient client;

	/**
	 * {@inheritDoc}
	 */
	@Override
	public Map<Currency, BigDecimal> getCurrentRates() {

		if (container == null || !container.getDate().equals(LocalDate.now())) {
			container = client.getRates(Currency.getBase());
			log.info("exchange rates has been updated: {}", container);
		}

		return ImmutableMap.of(
				Currency.EUR, container.getRates().get(Currency.EUR.name()),
				Currency.RUB, container.getRates().get(Currency.RUB.name()),
				Currency.USD, BigDecimal.ONE
		);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	public BigDecimal convert(Currency from, Currency to, BigDecimal amount) {

		Assert.notNull(amount);

		Map<Currency, BigDecimal> rates = getCurrentRates();
		BigDecimal ratio = rates.get(to).divide(rates.get(from), 4, RoundingMode.HALF_UP);

		return amount.multiply(ratio);
	}
}


// Node: now
// Node: notNull
// Node: divide
// Node: multiply
package com.piggymetrics.statistics.service;

import com.google.common.collect.ImmutableMap;
import com.piggymetrics.statistics.domain.*;
import com.piggymetrics.statistics.domain.timeseries.DataPoint;
import com.piggymetrics.statistics.domain.timeseries.DataPointId;
import com.piggymetrics.statistics.domain.timeseries.ItemMetric;
import com.piggymetrics.statistics.domain.timeseries.StatisticMetric;
import com.piggymetrics.statistics.repository.DataPointRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class StatisticsServiceImpl implements StatisticsService {

	private final Logger log = LoggerFactory.getLogger(getClass());

	@Autowired
	private DataPointRepository repository;

	@Autowired
	private ExchangeRatesService ratesService;

	/**
	 * {@inheritDoc}
	 */
	@Override
	public List<DataPoint> findByAccountName(String accountName) {
		Assert.hasLength(accountName);
		return repository.findByIdAccount(accountName);
	}

	/**
	 * {@inheritDoc}
	 */
	@Override
	public DataPoint save(String accountName, Account account) {

		Instant instant = LocalDate.now().atStartOfDay()
				.atZone(ZoneId.systemDefault()).toInstant();

		DataPointId pointId = new DataPointId(accountName, Date.from(instant));

		Set<ItemMetric> incomes = account.getIncomes().stream()
				.map(this::createItemMetric)
				.collect(Collectors.toSet());

		Set<ItemMetric> expenses = account.getExpenses().stream()
				.map(this::createItemMetric)
				.collect(Collectors.toSet());

		Map<StatisticMetric, BigDecimal> statistics = createStatisticMetrics(incomes, expenses, account.getSaving());

		DataPoint dataPoint = new DataPoint();
		dataPoint.setId(pointId);
		dataPoint.setIncomes(incomes);
		dataPoint.setExpenses(expenses);
		dataPoint.setStatistics(statistics);
		dataPoint.setRates(ratesService.getCurrentRates());

		log.debug("new datapoint has been created: {}", pointId);

		return repository.save(dataPoint);
	}

	private Map<StatisticMetric, BigDecimal> createStatisticMetrics(Set<ItemMetric> incomes, Set<ItemMetric> expenses, Saving saving) {

		BigDecimal savingAmount = ratesService.convert(saving.getCurrency(), Currency.getBase(), saving.getAmount());

		BigDecimal expensesAmount = expenses.stream()
				.map(ItemMetric::getAmount)
				.reduce(BigDecimal.ZERO, BigDecimal::add);

		BigDecimal incomesAmount = incomes.stream()
				.map(ItemMetric::getAmount)
				.reduce(BigDecimal.ZERO, BigDecimal::add);

		return ImmutableMap.of(
				StatisticMetric.EXPENSES_AMOUNT, expensesAmount,
				StatisticMetric.INCOMES_AMOUNT, incomesAmount,
				StatisticMetric.SAVING_AMOUNT, savingAmount
		);
	}

	/**
	 * Normalizes given item amount to {@link Currency#getBase()} currency with
	 * {@link TimePeriod#getBase()} time period
	 */
	private ItemMetric createItemMetric(Item item) {

		BigDecimal amount = ratesService
				.convert(item.getCurrency(), Currency.getBase(), item.getAmount())
				.divide(item.getPeriod().getBaseRatio(), 4, RoundingMode.HALF_UP);

		return new ItemMetric(item.getTitle(), amount);
	}
}


// Node: atStartOfDay
// Node: atZone
// Node: systemDefault
// Node: toInstant
// Node: from
// Node: getIncomes
// Node: stream
// Node: map
// Node: collect
// Node: toSet
// Node: getExpenses
// Node: createStatisticMetrics
// Node: DataPoint
// Node: setId
// Node: setStatistics
// Node: getCurrency
// Node: getAmount
// Node: reduce
// Node: createItemMetric
// Node: getPeriod
// Node: getBaseRatio
// Node: ItemMetric
// Node: getTitle
package com.piggymetrics.statistics.service;

import com.piggymetrics.statistics.domain.Account;
import com.piggymetrics.statistics.domain.timeseries.DataPoint;

import java.util.List;

public interface StatisticsService {

	/**
	 * Finds account by given name
	 *
	 * @param accountName
	 * @return found account
	 */
	List<DataPoint> findByAccountName(String accountName);

	/**
	 * Converts given {@link Account} object to {@link DataPoint} with
	 * a set of significant statistic metrics.
	 *
	 * Compound {@link DataPoint#id} forces to rewrite the object
	 * for each account within a day.
	 *
	 * @param accountName
	 * @param account
	 */
	DataPoint save(String accountName, Account account);

}


// Node: repos/cloned_ms_repos/piggymetrics/statistics-service/src/main/java/com/piggymetrics/statistics/service/StatisticsService.java:StatisticsService.<init>
package com.piggymetrics.statistics.domain;

import org.hibernate.validator.constraints.Length;

import javax.validation.constraints.NotNull;
import java.math.BigDecimal;

public class Item {

	@NotNull
	@Length(min = 1, max = 20)
	private String title;

	@NotNull
	private BigDecimal amount;

	@NotNull
	private Currency currency;

	@NotNull
	private TimePeriod period;

	public String getTitle() {
		return title;
	}

	public void setTitle(String title) {
		this.title = title;
	}

	public BigDecimal getAmount() {
		return amount;
	}

	public void setAmount(BigDecimal amount) {
		this.amount = amount;
	}

	public Currency getCurrency() {
		return currency;
	}

	public void setCurrency(Currency currency) {
		this.currency = currency;
	}

	public TimePeriod getPeriod() {
		return period;
	}

	public void setPeriod(TimePeriod period) {
		this.period = period;
	}
}


package com.piggymetrics.statistics.domain;

import javax.validation.constraints.NotNull;
import java.math.BigDecimal;

public class Saving {

	@NotNull
	private BigDecimal amount;

	@NotNull
	private Currency currency;

	@NotNull
	private BigDecimal interest;

	@NotNull
	private Boolean deposit;

	@NotNull
	private Boolean capitalization;

	public BigDecimal getAmount() {
		return amount;
	}

	public void setAmount(BigDecimal amount) {
		this.amount = amount;
	}

	public Currency getCurrency() {
		return currency;
	}

	public void setCurrency(Currency currency) {
		this.currency = currency;
	}

	public BigDecimal getInterest() {
		return interest;
	}

	public void setInterest(BigDecimal interest) {
		this.interest = interest;
	}

	public Boolean getDeposit() {
		return deposit;
	}

	public void setDeposit(Boolean deposit) {
		this.deposit = deposit;
	}

	public Boolean getCapitalization() {
		return capitalization;
	}

	public void setCapitalization(Boolean capitalization) {
		this.capitalization = capitalization;
	}
}


package com.piggymetrics.statistics.domain;

import java.math.BigDecimal;

public enum TimePeriod {

	YEAR(365.2425), QUARTER(91.3106), MONTH(30.4368), DAY(1), HOUR(0.0416);

	private double baseRatio;

	TimePeriod(double baseRatio) {
		this.baseRatio = baseRatio;
	}

	public BigDecimal getBaseRatio() {
		return new BigDecimal(baseRatio);
	}

	public static TimePeriod getBase() {
		return DAY;
	}
}


package com.piggymetrics.statistics.domain;

import org.codehaus.jackson.annotate.JsonIgnoreProperties;
import org.springframework.data.mongodb.core.mapping.Document;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.List;

@Document(collection = "accounts")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Account {

	@Valid
	@NotNull
	private List<Item> incomes;

	@Valid
	@NotNull
	private List<Item> expenses;

	@Valid
	@NotNull
	private Saving saving;

	public List<Item> getIncomes() {
		return incomes;
	}

	public void setIncomes(List<Item> incomes) {
		this.incomes = incomes;
	}

	public List<Item> getExpenses() {
		return expenses;
	}

	public void setExpenses(List<Item> expenses) {
		this.expenses = expenses;
	}

	public Saving getSaving() {
		return saving;
	}

	public void setSaving(Saving saving) {
		this.saving = saving;
	}
}


package com.piggymetrics.statistics.domain.timeseries;

import com.piggymetrics.statistics.domain.Currency;
import com.piggymetrics.statistics.domain.TimePeriod;

import java.math.BigDecimal;

/**
 * Represents normalized {@link com.piggymetrics.statistics.domain.Item} object
 * with {@link Currency#getBase()} currency and {@link TimePeriod#getBase()} time period
 */
public class ItemMetric {

	private String title;

	private BigDecimal amount;

	public ItemMetric(String title, BigDecimal amount) {
		this.title = title;
		this.amount = amount;
	}

	public String getTitle() {
		return title;
	}

	public BigDecimal getAmount() {
		return amount;
	}

	@Override
	public boolean equals(Object o) {
		if (this == o) return true;
		if (o == null || getClass() != o.getClass()) return false;

		ItemMetric that = (ItemMetric) o;

		return title.equalsIgnoreCase(that.title);

	}

	@Override
	public int hashCode() {
		return title.hashCode();
	}
}


// Node: repos/cloned_ms_repos/piggymetrics/statistics-service/src/main/java/com/piggymetrics/statistics/domain/timeseries/ItemMetric.java:ItemMetric.<init>
package com.piggymetrics.statistics.domain.timeseries;

import com.piggymetrics.statistics.domain.Currency;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.math.BigDecimal;
import java.util.Map;
import java.util.Set;

/**
 * Represents daily time series data point containing
 * current account state
 */
@Document(collection = "datapoints")
public class DataPoint {

	@Id
	private DataPointId id;

	private Set<ItemMetric> incomes;

	private Set<ItemMetric> expenses;

	private Map<StatisticMetric, BigDecimal> statistics;

	private Map<Currency, BigDecimal> rates;

	public DataPointId getId() {
		return id;
	}

	public void setId(DataPointId id) {
		this.id = id;
	}

	public Set<ItemMetric> getIncomes() {
		return incomes;
	}

	public void setIncomes(Set<ItemMetric> incomes) {
		this.incomes = incomes;
	}

	public Set<ItemMetric> getExpenses() {
		return expenses;
	}

	public void setExpenses(Set<ItemMetric> expenses) {
		this.expenses = expenses;
	}

	public Map<StatisticMetric, BigDecimal> getStatistics() {
		return statistics;
	}

	public void setStatistics(Map<StatisticMetric, BigDecimal> statistics) {
		this.statistics = statistics;
	}

	public Map<Currency, BigDecimal> getRates() {
		return rates;
	}

	public void setRates(Map<Currency, BigDecimal> rates) {
		this.rates = rates;
	}
}


// Node: getId
// Node: getStatistics
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


// Node: repos/cloned_ms_repos/piggymetrics/statistics-service/src/main/java/com/piggymetrics/statistics/domain/timeseries/DataPointId.java:DataPointId.<init>
package com.piggymetrics.statistics.repository;

import com.google.common.collect.ImmutableMap;
import com.google.common.collect.Sets;
import com.piggymetrics.statistics.domain.timeseries.DataPoint;
import com.piggymetrics.statistics.domain.timeseries.DataPointId;
import com.piggymetrics.statistics.domain.timeseries.ItemMetric;
import com.piggymetrics.statistics.domain.timeseries.StatisticMetric;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.test.context.junit4.SpringRunner;

import java.math.BigDecimal;
import java.util.Date;
import java.util.List;

import static org.junit.Assert.assertEquals;

@RunWith(SpringRunner.class)
@DataMongoTest
public class DataPointRepositoryTest {

	@Autowired
	private DataPointRepository repository;

	@Test
	public void shouldSaveDataPoint() {

		ItemMetric salary = new ItemMetric("salary", new BigDecimal(20_000));

		ItemMetric grocery = new ItemMetric("grocery", new BigDecimal(1_000));
		ItemMetric vacation = new ItemMetric("vacation", new BigDecimal(2_000));

		DataPointId pointId = new DataPointId("test-account", new Date(0));

		DataPoint point = new DataPoint();
		point.setId(pointId);
		point.setIncomes(Sets.newHashSet(salary));
		point.setExpenses(Sets.newHashSet(grocery, vacation));
		point.setStatistics(ImmutableMap.of(
				StatisticMetric.SAVING_AMOUNT, new BigDecimal(400_000),
				StatisticMetric.INCOMES_AMOUNT, new BigDecimal(20_000),
				StatisticMetric.EXPENSES_AMOUNT, new BigDecimal(3_000)
		));

		repository.save(point);

		List<DataPoint> points = repository.findByIdAccount(pointId.getAccount());
		assertEquals(1, points.size());
		assertEquals(pointId.getDate(), points.get(0).getId().getDate());
		assertEquals(point.getStatistics().size(), points.get(0).getStatistics().size());
		assertEquals(point.getIncomes().size(), points.get(0).getIncomes().size());
		assertEquals(point.getExpenses().size(), points.get(0).getExpenses().size());
	}

	@Test
	public void shouldRewriteDataPointWithinADay() {

		final BigDecimal earlyAmount = new BigDecimal(100);
		final BigDecimal lateAmount = new BigDecimal(200);

		DataPointId pointId = new DataPointId("test-account", new Date(0));

		DataPoint earlier = new DataPoint();
		earlier.setId(pointId);
		earlier.setStatistics(ImmutableMap.of(
				StatisticMetric.SAVING_AMOUNT, earlyAmount
		));

		repository.save(earlier);

		DataPoint later = new DataPoint();
		later.setId(pointId);
		later.setStatistics(ImmutableMap.of(
				StatisticMetric.SAVING_AMOUNT, lateAmount
		));

		repository.save(later);

		List<DataPoint> points = repository.findByIdAccount(pointId.getAccount());

		assertEquals(1, points.size());
		assertEquals(lateAmount, points.get(0).getStatistics().get(StatisticMetric.SAVING_AMOUNT));
	}
}


// Node: shouldSaveDataPoint
// Node: newHashSet
// Node: shouldRewriteDataPointWithinADay
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

// Node: then
// Node: getArgument
// Node: returnsFirstArg
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

// Node: shouldFailToConvertWhenAmountIsNull
package com.piggymetrics.account.domain;

import org.hibernate.validator.constraints.Length;

import javax.validation.constraints.NotNull;
import java.math.BigDecimal;

public class Item {

	@NotNull
	@Length(min = 1, max = 20)
	private String title;

	@NotNull
	private BigDecimal amount;

	@NotNull
	private Currency currency;

	@NotNull
	private TimePeriod period;

	@NotNull
	private String icon;

	public String getTitle() {
		return title;
	}

	public void setTitle(String title) {
		this.title = title;
	}

	public BigDecimal getAmount() {
		return amount;
	}

	public void setAmount(BigDecimal amount) {
		this.amount = amount;
	}

	public Currency getCurrency() {
		return currency;
	}

	public void setCurrency(Currency currency) {
		this.currency = currency;
	}

	public TimePeriod getPeriod() {
		return period;
	}

	public void setPeriod(TimePeriod period) {
		this.period = period;
	}

	public String getIcon() {
		return icon;
	}

	public void setIcon(String icon) {
		this.icon = icon;
	}
}


package com.piggymetrics.account.domain;

import javax.validation.constraints.NotNull;
import java.math.BigDecimal;

public class Saving {

	@NotNull
	private BigDecimal amount;

	@NotNull
	private Currency currency;

	@NotNull
	private BigDecimal interest;

	@NotNull
	private Boolean deposit;

	@NotNull
	private Boolean capitalization;

	public BigDecimal getAmount() {
		return amount;
	}

	public void setAmount(BigDecimal amount) {
		this.amount = amount;
	}

	public Currency getCurrency() {
		return currency;
	}

	public void setCurrency(Currency currency) {
		this.currency = currency;
	}

	public BigDecimal getInterest() {
		return interest;
	}

	public void setInterest(BigDecimal interest) {
		this.interest = interest;
	}

	public Boolean getDeposit() {
		return deposit;
	}

	public void setDeposit(Boolean deposit) {
		this.deposit = deposit;
	}

	public Boolean getCapitalization() {
		return capitalization;
	}

	public void setCapitalization(Boolean capitalization) {
		this.capitalization = capitalization;
	}
}


package com.piggymetrics.account.domain;

import org.codehaus.jackson.annotate.JsonIgnoreProperties;
import org.hibernate.validator.constraints.Length;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Date;
import java.util.List;

@Document(collection = "accounts")
@JsonIgnoreProperties(ignoreUnknown = true)
public class Account {

	@Id
	private String name;

	private Date lastSeen;

	@Valid
	private List<Item> incomes;

	@Valid
	private List<Item> expenses;

	@Valid
	@NotNull
	private Saving saving;

	@Length(min = 0, max = 20_000)
	private String note;

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	public Date getLastSeen() {
		return lastSeen;
	}

	public void setLastSeen(Date lastSeen) {
		this.lastSeen = lastSeen;
	}

	public List<Item> getIncomes() {
		return incomes;
	}

	public void setIncomes(List<Item> incomes) {
		this.incomes = incomes;
	}

	public List<Item> getExpenses() {
		return expenses;
	}

	public void setExpenses(List<Item> expenses) {
		this.expenses = expenses;
	}

	public Saving getSaving() {
		return saving;
	}

	public void setSaving(Saving saving) {
		this.saving = saving;
	}

	public String getNote() {
		return note;
	}

	public void setNote(String note) {
		this.note = note;
	}
}


package com.piggymetrics.account.repository;

import com.piggymetrics.account.domain.Account;
import com.piggymetrics.account.domain.Currency;
import com.piggymetrics.account.domain.Item;
import com.piggymetrics.account.domain.Saving;
import com.piggymetrics.account.domain.TimePeriod;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.test.context.junit4.SpringRunner;

import java.math.BigDecimal;
import java.util.Arrays;
import java.util.Date;

import static org.junit.Assert.assertEquals;

@RunWith(SpringRunner.class)
@DataMongoTest
public class AccountRepositoryTest {

	@Autowired
	private AccountRepository repository;

	@Test
	public void shouldFindAccountByName() {

		Account stub = getStubAccount();
		repository.save(stub);

		Account found = repository.findByName(stub.getName());
		assertEquals(stub.getLastSeen(), found.getLastSeen());
		assertEquals(stub.getNote(), found.getNote());
		assertEquals(stub.getIncomes().size(), found.getIncomes().size());
		assertEquals(stub.getExpenses().size(), found.getExpenses().size());
	}

	private Account getStubAccount() {

		Saving saving = new Saving();
		saving.setAmount(new BigDecimal(1500));
		saving.setCurrency(Currency.USD);
		saving.setInterest(new BigDecimal("3.32"));
		saving.setDeposit(true);
		saving.setCapitalization(false);

		Item vacation = new Item();
		vacation.setTitle("Vacation");
		vacation.setAmount(new BigDecimal(3400));
		vacation.setCurrency(Currency.EUR);
		vacation.setPeriod(TimePeriod.YEAR);
		vacation.setIcon("tourism");

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

		Account account = new Account();
		account.setName("test");
		account.setNote("test note");
		account.setLastSeen(new Date());
		account.setSaving(saving);
		account.setExpenses(Arrays.asList(grocery, vacation));
		account.setIncomes(Arrays.asList(salary));

		return account;
	}
}


// Node: shouldFindAccountByName
// Node: getStubAccount
package com.piggymetrics.notification.controller;

import com.piggymetrics.notification.domain.Recipient;
import com.piggymetrics.notification.service.RecipientService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;
import java.security.Principal;

@RestController
@RequestMapping("/recipients")
public class RecipientController {

	@Autowired
	private RecipientService recipientService;

	@RequestMapping(path = "/current", method = RequestMethod.GET)
	public Object getCurrentNotificationsSettings(Principal principal) {
		return recipientService.findByAccountName(principal.getName());
	}

	@RequestMapping(path = "/current", method = RequestMethod.PUT)
	public Object saveCurrentNotificationsSettings(Principal principal, @Valid @RequestBody Recipient recipient) {
		return recipientService.save(principal.getName(), recipient);
	}
}


// Node: saveCurrentNotificationsSettings
package com.piggymetrics.notification.repository.converter;

import com.piggymetrics.notification.domain.Frequency;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

@Component
public class FrequencyReaderConverter implements Converter<Integer, Frequency> {

	@Override
	public Frequency convert(Integer days) {
		return Frequency.withDays(days);
	}
}


// Node: withDays
package com.piggymetrics.notification.repository.converter;

import com.piggymetrics.notification.domain.Frequency;
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

@Component
public class FrequencyWriterConverter implements Converter<Frequency, Integer> {

	@Override
	public Integer convert(Frequency frequency) {
		return frequency.getDays();
	}
}


// Node: getDays
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


