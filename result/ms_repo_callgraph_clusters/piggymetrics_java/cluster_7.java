// Cluster 7

// Node: create
package com.piggymetrics.auth.service;

import com.piggymetrics.auth.domain.User;

public interface UserService {

	void create(User user);

}


// Node: repos/cloned_ms_repos/piggymetrics/auth-service/src/main/java/com/piggymetrics/auth/service/UserService.java:UserService.<init>
package com.piggymetrics.auth.service;

import com.piggymetrics.auth.domain.User;
import com.piggymetrics.auth.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.util.Assert;

import java.util.Optional;

@Service
public class UserServiceImpl implements UserService {

	private final Logger log = LoggerFactory.getLogger(getClass());

	private static final BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();

	@Autowired
	private UserRepository repository;

	@Override
	public void create(User user) {

		Optional<User> existing = repository.findById(user.getUsername());
		existing.ifPresent(it-> {throw new IllegalArgumentException("user already exists: " + it.getUsername());});

		String hash = encoder.encode(user.getPassword());
		user.setPassword(hash);

		repository.save(user);

		log.info("new user has been created: {}", user.getUsername());
	}
}


// Node: findById
// Node: getUsername
// Node: ifPresent
// Node: IllegalArgumentException
// Node: encode
// Node: getPassword
// Node: setPassword
package com.piggymetrics.auth.service.security;

import com.piggymetrics.auth.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class MongoUserDetailsService implements UserDetailsService {

	@Autowired
	private UserRepository repository;

	@Override
	public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {

		return repository.findById(username).orElseThrow(()->new UsernameNotFoundException(username));
	}
}


// Node: repos/cloned_ms_repos/piggymetrics/auth-service/src/main/java/com/piggymetrics/auth/service/security/MongoUserDetailsService.java:MongoUserDetailsService.<init>
// Node: loadUserByUsername
// Node: orElseThrow
// Node: UsernameNotFoundException
package com.piggymetrics.auth.domain;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.List;

@Document(collection = "users")
public class User implements UserDetails {

	@Id
	private String username;

	private String password;

	@Override
	public String getPassword() {
		return password;
	}

	@Override
	public String getUsername() {
		return username;
	}

	@Override
	public List<GrantedAuthority> getAuthorities() {
		return null;
	}

	public void setUsername(String username) {
		this.username = username;
	}

	public void setPassword(String password) {
		this.password = password;
	}

	@Override
	public boolean isAccountNonExpired() {
		return true;
	}

	@Override
	public boolean isAccountNonLocked() {
		return true;
	}

	@Override
	public boolean isCredentialsNonExpired() {
		return true;
	}

	@Override
	public boolean isEnabled() {
		return true;
	}
}


// Node: setUsername
// Node: User
package com.piggymetrics.auth.repository;

import com.piggymetrics.auth.domain.User;
import com.piggymetrics.auth.service.security.MongoUserDetailsService;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.mongo.embedded.EmbeddedMongoAutoConfiguration;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.junit4.SpringRunner;

import java.util.Optional;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

@RunWith(SpringRunner.class)
@DataMongoTest
public class UserRepositoryTest {

	@Autowired
	private UserRepository repository;

	@Test
	public void shouldSaveAndFindUserByName() {

		User user = new User();
		user.setUsername("name");
		user.setPassword("password");
		repository.save(user);

		Optional<User> found = repository.findById(user.getUsername());
		assertTrue(found.isPresent());
		assertEquals(user.getUsername(), found.get().getUsername());
		assertEquals(user.getPassword(), found.get().getPassword());
	}
}


// Node: shouldSaveAndFindUserByName
// Node: assertTrue
// Node: isPresent
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


// Node: shouldCreateUser
// Node: times
// Node: shouldFailWhenUserAlreadyExists
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

// Node: shouldLoadByUsernameWhenUserExists
// Node: any
// Node: shouldFailToLoadByUsernameWhenUserNotExists
// Node: getSaving
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


// Node: getInterest
// Node: getDeposit
// Node: getCapitalization
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


package com.piggymetrics.account.controller;

import com.piggymetrics.account.domain.Account;
import com.piggymetrics.account.domain.User;
import com.piggymetrics.account.service.AccountService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.security.Principal;

@RestController
public class AccountController {

	@Autowired
	private AccountService accountService;

	@PreAuthorize("#oauth2.hasScope('server') or #name.equals('demo')")
	@RequestMapping(path = "/{name}", method = RequestMethod.GET)
	public Account getAccountByName(@PathVariable String name) {
		return accountService.findByName(name);
	}

	@RequestMapping(path = "/current", method = RequestMethod.GET)
	public Account getCurrentAccount(Principal principal) {
		return accountService.findByName(principal.getName());
	}

	@RequestMapping(path = "/current", method = RequestMethod.PUT)
	public void saveCurrentAccount(Principal principal, @Valid @RequestBody Account account) {
		accountService.saveChanges(principal.getName(), account);
	}

	@RequestMapping(path = "/", method = RequestMethod.POST)
	public Account createNewAccount(@Valid @RequestBody User user) {
		return accountService.create(user);
	}
}


// Node: createNewAccount
// Node: getDefault
package com.piggymetrics.account.domain;

import org.hibernate.validator.constraints.Length;

import javax.validation.constraints.NotNull;

public class User {

	@NotNull
	@Length(min = 3, max = 20)
	private String username;

	@NotNull
	@Length(min = 6, max = 40)
	private String password;

	public String getUsername() {
		return username;
	}

	public void setUsername(String username) {
		this.username = username;
	}

	public String getPassword() {
		return password;
	}

	public void setPassword(String password) {
		this.password = password;
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

public enum Currency {

	USD, EUR, RUB;

	public static Currency getDefault() {
		return USD;
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


// Node: getLastSeen
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


// Node: shouldCreateAccountWithGivenUser
// Node: intValue
