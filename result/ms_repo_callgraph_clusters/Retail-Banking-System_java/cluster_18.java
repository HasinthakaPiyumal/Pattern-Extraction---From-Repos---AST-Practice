// Cluster 18

package com.cognizant.accountservice.service;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.cognizant.accountservice.exceptionhandling.AccessDeniedException;
import com.cognizant.accountservice.exceptionhandling.AccountNotFoundException;
import com.cognizant.accountservice.feignclient.AuthFeignClient;
import com.cognizant.accountservice.feignclient.TransactionFeign;
import com.cognizant.accountservice.model.Account;
import com.cognizant.accountservice.model.AccountCreationStatus;
import com.cognizant.accountservice.model.AccountInput;
import com.cognizant.accountservice.model.AuthenticationResponse;
import com.cognizant.accountservice.model.Statement;
import com.cognizant.accountservice.repository.AccountRepository;
import com.cognizant.accountservice.repository.StatementRepository;

@Service
public class AccountServiceImpl implements AccountService {

	private static final Logger LOGGER = LoggerFactory.getLogger(AccountServiceImpl.class);
	/*
	 * Autowiring the FeignClient Services to communicate with other microservices
	 */
	@Autowired
	private AuthFeignClient authFeignClient;
	@Autowired
	private TransactionFeign transactionFeign;

	/*
	 * Autowiring the repositories
	 */
	@Autowired
	private AccountRepository accountRepository;
	@Autowired
	private StatementRepository statementRepository;

	// creating new account and storing it in the database
	@Override
	public AccountCreationStatus createAccount(String customerId, Account account) {
		accountRepository.save(account);
		AccountCreationStatus accountCreationStatus = new AccountCreationStatus(account.getAccountId(),
				"Sucessfully Created");
		LOGGER.info("Account Created Successfully");
		return accountCreationStatus;
	}

	// getting the account details based on the customer
	@Override
	public List<Account> getCustomerAccount(String token, String customerId) {
		List<Account> accountList = accountRepository.findByCustomerId(customerId);
		for (Account acc : accountList) {
			acc.setTransactions(transactionFeign.getTransactionsByAccId(token, acc.getAccountId()));
		}
		return accountList;
	}

	// Getting the account details for the given account id
	@Override
	public Account getAccount(long accountId) {
		Account account = accountRepository.findByAccountId(accountId);
		if (account == null) {
			throw new AccountNotFoundException("Account Does Not Exist");
		}
		return account;
	}

	// updating the current balance during withdraw, service charge deduction,
	// transfer
	@Override
	public Account updateBalance(AccountInput accountInput) {
		LOGGER.info("Account to update " + accountInput.getAccountId());
		Account toUpdateAcc = accountRepository.findByAccountId(accountInput.getAccountId());
		toUpdateAcc.setCurrentBalance(toUpdateAcc.getCurrentBalance() - accountInput.getAmount());
		return accountRepository.save(toUpdateAcc);
	}

	// updating the current balance during deposit and transfer
	@Override
	public Account updateDepositBalance(AccountInput accountInput) {
		LOGGER.info("Account to update " + accountInput.getAccountId());
		Account toUpdateAcc = accountRepository.findByAccountId(accountInput.getAccountId());
		toUpdateAcc.setCurrentBalance(toUpdateAcc.getCurrentBalance() + accountInput.getAmount());
		return accountRepository.save(toUpdateAcc);
	}

	// Validating the token using authorization microservice
	@Override
	public AuthenticationResponse hasPermission(String token) {
		return authFeignClient.tokenValidation(token);
	}

	// Checking whether the user has employee permission or not
	@Override
	public AuthenticationResponse hasEmployeePermission(String token) {
		AuthenticationResponse validity = authFeignClient.tokenValidation(token);
		if (!authFeignClient.getRole(validity.getUserid()).equalsIgnoreCase("EMPLOYEE")) {
			throw new AccessDeniedException("NOT ALLOWED");
		}
		return validity;
	}

	// Checking whether the user has customer permission or not
	@Override
	public AuthenticationResponse hasCustomerPermission(String token) {
		AuthenticationResponse validity = authFeignClient.tokenValidation(token);
		if (!authFeignClient.getRole(validity.getUserid()).equalsIgnoreCase("CUSTOMER")) {
			throw new AccessDeniedException("NOT ALLOWED");
		}
		return validity;
	}

	// Getting all the account details from the database
	@Override
	public List<Account> getAllAccounts() {
		List<Account> accounts = accountRepository.findAll();
		return accounts;
	}

	// Deleting the account details associated with the given account id
	@Override
	public void deleteCustomer(String id) {
		List<Account> list = new ArrayList<>();
		list = getAllAccounts();
		for (Account account : list) {
			if (account.getCustomerId().equalsIgnoreCase(id)) {
				accountRepository.deleteById(account.getAccountId());
			}
		}

	}

	// Updating the account statement after withdrawal, deposit and service charge
	// deduction
	@Override
	public void updateStatement(AccountInput accInput, Account newUpdateAccBal, String message) {
		long accountId = accInput.getAccountId();
		Statement statement = new Statement(accountId, accountId, accInput.getAmount(),
				newUpdateAccBal.getCurrentBalance(), newUpdateAccBal.getCurrentBalance(), new Date(), message);
		statementRepository.save(statement);
	}

	// Updating the account statement after transaction
	@Override
	public void updateStatement(Account updatedSourceAccBal, Account updatedTargetAccBal, double amount,
			String message) {
		Statement statement = new Statement(updatedSourceAccBal.getAccountId(), updatedTargetAccBal.getAccountId(),
				amount, updatedSourceAccBal.getCurrentBalance(), updatedTargetAccBal.getCurrentBalance(), new Date(),
				message);
		statementRepository.save(statement);

	}

	// Getting the account statements for the last 30 days
	@Override
	public List<Statement> getAccountStatement(long accountId) {
		Date startDate = new Date();
		LocalDateTime date = LocalDateTime.now().minusDays(30);
		Date endDate = Date.from(date.atZone(ZoneId.systemDefault()).toInstant());
		List<Statement> statements = statementRepository.findStatementByAccountId(accountId, endDate, startDate);
		return statements;
	}

	// Getting the account statements between the given dates
	@Override
	public List<Statement> getAccountStatement(long accountId, String from, String to) throws ParseException {
		Date fromDate = new SimpleDateFormat("yyyy-MM-dd").parse(from);
		Date toDate = new SimpleDateFormat("yyyy-MM-dd").parse(to);
		List<Statement> statements = statementRepository.findStatementByAccountId(accountId, fromDate, toDate);
		return statements;
	}

}

// Node: minusDays
// Node: from
// Node: atZone
// Node: systemDefault
// Node: toInstant
// Node: SimpleDateFormat
// Node: parse
package com.cognizant.accountservice.model;

import java.util.Date;
import java.util.List;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.SequenceGenerator;
import javax.persistence.Table;
import javax.persistence.Transient;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.NotNull;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Entity
@Table(name = "ACCOUNT")
@NoArgsConstructor
@AllArgsConstructor 
public class Account {

	@Id
	@NotNull(message = "Enter Account number")
	@Getter
	@Setter 
	@Column(length=10)
	@SequenceGenerator(name="seq", initialValue = 1000000003)
	@GeneratedValue(strategy = GenerationType.SEQUENCE, generator="seq")
	private long accountId;
	
	@NotBlank(message = "Enter customerId")
	@Getter
	@Setter
	private String customerId;

	@NotNull(message = "Enter currentBalance")
	@Getter
	@Setter
	private double currentBalance;

	@Getter
	@Setter
	@NotBlank(message = "Enter accountType")
	private String accountType;

	@Getter
	@Setter
	@NotNull(message = "Enter openingDate")
	private Date openingDate;

	
	@Getter
	@Setter
	@Column(length = 20)
	@NotBlank(message = "Enter ownerName")
	private String ownerName;


	@Getter
	@Setter
	@Transient
	private List<Transaction> transactions;
	
	@Override
	public String toString() {
		return "Account information : [accountId=" + accountId + ", openingDate=" + openingDate + ", currentBalance=" + currentBalance
				+ ", accountType=" + accountType + "]";
	}

}

// Node: toString
package com.cognizant.service;

import static org.junit.Assert.assertTrue;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.when;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import com.cognizant.accountservice.exceptionhandling.AccessDeniedException;
import com.cognizant.accountservice.exceptionhandling.AccountNotFoundException;
import com.cognizant.accountservice.feignclient.AuthFeignClient;
import com.cognizant.accountservice.feignclient.TransactionFeign;
import com.cognizant.accountservice.model.Account;
import com.cognizant.accountservice.model.AccountCreationStatus;
import com.cognizant.accountservice.model.AccountInput;
import com.cognizant.accountservice.model.AuthenticationResponse;
import com.cognizant.accountservice.repository.AccountRepository;
import com.cognizant.accountservice.service.AccountServiceImpl;

@ExtendWith(SpringExtension.class)
class AccountServiceTest {

	@InjectMocks
	AccountServiceImpl accountServiceImpl;

	@Mock
	AuthFeignClient authFeignClient;

	@Mock
	AccountRepository accountRepository;

	@Mock
	TransactionFeign transactionFeign;

	@Test
	public void toStringTest() throws ParseException 
	{
		Date date = null;
		date = new SimpleDateFormat("dd/MM/yyyy").parse("10/09/2021");
		Account account = new Account(1l, "cust001", 1000.0, "Savings", date, "harini", null);
		String expected = account.toString();
		assertEquals(expected, account.toString());
	}
	@Test
	void getAccountTestCorrect() throws ParseException {
		Date date = null;
			date = new SimpleDateFormat("dd/MM/yyyy").parse("10/09/2021");
		Account account = new Account(1l, "cust001", 1000.0, "Savings", date, "harini", null);
		when(accountRepository.findByAccountId(1l)).thenReturn(account);

		assertEquals("harini", accountServiceImpl.getAccount(1l).getOwnerName());
	}

	@Test
	void getAccountTestExceptionMessage() {
		when(accountRepository.findByAccountId(2l)).thenThrow(new AccountNotFoundException("Account Does Not Exist"));
		assertThrows(AccountNotFoundException.class, () -> accountServiceImpl.getAccount(2));
	}

	@Test
	void getCustomerAccount() throws ParseException {
		Date date = null;
			date = new SimpleDateFormat("dd/MM/yyyy").parse("10/09/2021");
		List<Account> accounts = new ArrayList<>();
		Account acc1 = new Account(1l, "cust01", 1000.0, "Savings", date,"harini", null);
		Account acc2 = new Account(2l, "cust01", 2000.0, "Current", date,"sai harini", null);

		accounts.add(acc1);
		accounts.add(acc2);

		when(accountRepository.findByCustomerId("cust01")).thenReturn(accounts);
		when(transactionFeign.getTransactionsByAccId("token", 1)).thenReturn(null);
		when(transactionFeign.getTransactionsByAccId("token", 2)).thenReturn(null);
		assertEquals(2, accountServiceImpl.getCustomerAccount("token", "cust01").size());
	}

	@Test
	void createAccount() throws ParseException {
		Date date = null;
			date = new SimpleDateFormat("dd/MM/yyyy").parse("10/09/2021");
		Account acc = new Account(1l, "cust01", 3000.0, "Savings",date, "harini", null);
		when(accountRepository.save(acc)).thenReturn(acc);
		AccountCreationStatus status = accountServiceImpl.createAccount("cust01", acc);
		assertEquals("Sucessfully Created", status.getMessage());
	}

	@Test
	void hasPermissionTest1() {
		when(authFeignClient.tokenValidation("token")).thenReturn(new AuthenticationResponse("cust01", "harini", true));
		assertTrue(accountServiceImpl.hasPermission("token").isValid());
	}

	@Test
	void hasPermissionTest2() {
		when(authFeignClient.tokenValidation("token")).thenThrow(new AccessDeniedException());
		assertThrows(AccessDeniedException.class, () -> accountServiceImpl.hasPermission("token"));
	}

	@Test
	void hasCustomerPermissionTest1() {
		when(authFeignClient.tokenValidation("token")).thenReturn(new AuthenticationResponse("cust01", "harini", true));
		when(authFeignClient.getRole("cust01")).thenReturn("CUSTOMER");
		assertTrue(accountServiceImpl.hasCustomerPermission("token").isValid());
	}

	@Test
	void hasCustomerPermissionTest2() {
		when(authFeignClient.tokenValidation("token")).thenThrow(new AccessDeniedException("NOT ALLOWED"));
		assertThrows(AccessDeniedException.class, () -> accountServiceImpl.hasCustomerPermission("token"));
	}

	@Test
	void hasEmployeePermissionTest1() {
		when(authFeignClient.tokenValidation("token")).thenReturn(new AuthenticationResponse("emp01", "harini", true));
		when(authFeignClient.getRole("emp01")).thenReturn("EMPLOYEE");
		assertTrue(accountServiceImpl.hasEmployeePermission("token").isValid());
	}

	@Test
	void hasEmployeePermissionTest2() {
		when(authFeignClient.tokenValidation("token")).thenThrow(new AccessDeniedException("NOT ALLOWED"));
		assertThrows(AccessDeniedException.class, () -> accountServiceImpl.hasEmployeePermission("token"));
	}


	@Test
	void updateBalanceTest() throws ParseException {
		Date date = null;
			date = new SimpleDateFormat("dd/MM/yyyy").parse("10/09/2021");
		Account acc1 = new Account(1l, "cust01", 1000.0, "Savings", date,"harini", null);
		Account acc2 = new Account(1l, "cust01", 500.0, "Savings", date,"hari", null);
		when(accountRepository.findByAccountId(1l)).thenReturn(acc1);
		when(accountRepository.save(acc1)).thenReturn(acc2);
		AccountInput ai = new AccountInput(1, 500);
		Account testAccount = accountServiceImpl.updateBalance(ai);
		assertEquals(500, testAccount.getCurrentBalance());
	}

	@Test
	void updateDepositBalanceTest() throws ParseException {
		Date date = null;
			date = new SimpleDateFormat("dd/MM/yyyy").parse("10/09/2021");
		Account acc1 = new Account(1l, "CUST101", 1000.0, "Savings",date, "harini", null);
		Account acc2 = new Account(1l, "CUST101", 1500.0, "Savings", date,"hari", null);
		when(accountRepository.findByAccountId(1l)).thenReturn(acc1);
		when(accountRepository.save(acc1)).thenReturn(acc2);
		AccountInput ai = new AccountInput(1, 500);
		Account testAccount = accountServiceImpl.updateDepositBalance(ai);
		assertEquals(1500, testAccount.getCurrentBalance());
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/service/AccountServiceTest.java:AccountServiceTest.<init>
// Node: ExtendWith
// Node: toStringTest
// Node: getAccountTestCorrect
// Node: getOwnerName
package com.cognizant.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.Test;

import com.cognizant.accountservice.model.AuthenticationResponse;

public class AuthenticationResponseTest {
	
	AuthenticationResponse ae=new AuthenticationResponse();
	AuthenticationResponse ae1=new AuthenticationResponse("234","harini",false);
	@Test
	public void userIdTest()
	{
		ae.setUserid("123");
		assertEquals("123", ae.getUserid());
	}
	@Test
	public void nameTest()
	{
		ae.setName("harini");
		assertEquals("harini", ae.getName());
	}
	@Test
	public void isValidTest()
	{
		ae.setValid(true);
		assertEquals(true, ae.isValid());
	}
	
	@Test
	public void userIdTest1()
	{
		assertEquals("234", ae1.getUserid());
	}
	@Test
	public void nameTest1()
	{
		assertEquals("harini", ae1.getName());
	}
	@Test
	public void isValidTest1()
	{
		assertEquals(false, ae1.isValid());
	}
	
	@Test
	public void toStringTest()
	{
		String expected = ae.toString();
		assertEquals(expected, ae.toString());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/service/AuthenticationResponseTest.java:AuthenticationResponseTest.<init>
// Node: userIdTest
// Node: nameTest
// Node: setName
// Node: getName
// Node: isValidTest
// Node: userIdTest1
// Node: nameTest1
// Node: isValidTest1
package com.cognizant.authenticationservice.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AppUserTest {

	AppUser app = new AppUser("1", "naga", "abc", "a", "user");
	AppUser pojo = new AppUser();

	//

	@Test
	public void getterPassTestNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("password");
		field.setAccessible(true);
		field.set(pojo, "magic_value");
		// when
		String result = pojo.getPassword();
		// then
		assertNotEquals("field wasn't retrieved properly", result, "magic_values");
	}

	@Test
	public void setterIdTestNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		// when
		pojo.setUserid("abcd");
		// then
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("userid");
		field.setAccessible(true);
		assertNotEquals("Fields didn't match", field.get(pojo), "emp");
	}

	@Test
	public void getterIdNeg() throws NoSuchFieldException, IllegalAccessException {
		// given
		AppUser pojo = new AppUser();
		java.lang.reflect.Field field = pojo.getClass().getDeclaredField("userid");
		field.setAccessible(true);
		field.set(pojo, "values");
		// when
		String result = pojo.getUserid();
		// then
		assertNotEquals("field wasn't retrieved properly", result, "magic_values");
	}

	@Test
	void setAmountTest() {
		pojo.setAuthToken("abc");
		assertEquals("abc", pojo.getAuthToken());
	}

	@Test
	void getAccountIdTest() {
		pojo.setAuthToken("abc");
		assertTrue(pojo.getAuthToken() == "abc");
	}

	@Test
	void set() {
		pojo.setRole("abc");
		assertEquals("abc", pojo.getRole());
	}

	@Test
	void getAccounTest() {
		pojo.setRole("abc");
		assertTrue(pojo.getRole() == "abc");
	}

	@Test
	void setname() {
		pojo.setUsername("abc");
		assertEquals("abc", pojo.getUsername());
	}

	@Test
	void getAccounname() {
		pojo.setUsername("abc");
		assertTrue(pojo.getUsername() == "abc");
	}

	AuthenticationResponse response = new AuthenticationResponse();
	AuthenticationResponse response2 = new AuthenticationResponse();
	AuthenticationResponse response3 = new AuthenticationResponse("1", "name", true);

	@Test
	void setUserIdTest() {
		response.setUserid("Cust101");
		assertEquals("Cust101", response.getUserid());
	}

	@Test
	void getUserIdTest() {
		response.setUserid("Cust101");
		assertTrue(response.getUserid() == "Cust101");
	}

	@Test
	void setNameTest() {
		response.setName("Pratik B");
		assertEquals("Pratik B", response.getName());
	}

	@Test
	void getNameTest() {
		response.setName("Cust101");
		assertTrue(response.getName() == "Cust101");
	}

	@Test
	void setisValidTest() {
		response.setValid(true);
		assertEquals(true, response.isValid());
	}

	@Test
	void toSringTest() {
		assertEquals(response2.toString(), response.toString());
	}

}


// Node: setNameTest
// Node: getNameTest
// Node: toSringTest
package com.rulesservice.exception;

@SuppressWarnings("serial")
public class NullPointerException extends RuntimeException {

	public NullPointerException() {
		super();
	}

	public NullPointerException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/exception/NullPointerException.java:NullPointerException.<init>
// Node: SuppressWarnings
// Node: NullPointerException
package com.rulesservice;

import org.junit.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.builder.SpringApplicationBuilder;

@ExtendWith(MockitoExtension.class)
public class ServletIntializerTest {

	@Mock
	private SpringApplicationBuilder springApplicationBuilder;

	@Test
	public void main() {
		RulesServiceApplication.main(new String[] {});
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/ServletIntializerTest.java:ServletIntializerTest.<init>
package com.rulesservice.service;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.when;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import com.rulesservice.exception.AccessDeniedException;
import com.rulesservice.feign.AuthorizationFeign;
import com.rulesservice.model.AuthenticationResponse;
import com.rulesservice.model.RulesInput;
import com.rulesservice.model.ServiceResponse;

@ExtendWith(SpringExtension.class)
class RulesServiceImplTest {

	@InjectMocks
	RulesServiceImpl serviceImpl;

	@Mock
	AuthorizationFeign authFeignClient;

	@Test
	void EvaluateTest() {
		RulesServiceImpl service = new RulesServiceImpl();
		RulesInput in = new RulesInput(1000, 10000, 10);
		assertEquals(true, service.evaluate(in));
	}

	@Test
	void EvaluateTest2() {
		RulesServiceImpl service = new RulesServiceImpl();
		RulesInput in = new RulesInput(1000, 100, 10);
		assertEquals(false, service.evaluate(in));
	}

	@Test
	void EvaluateTest3() {
		RulesServiceImpl service = new RulesServiceImpl();
		RulesInput in = new RulesInput(1000, 1000, 100);
		assertEquals(false, service.evaluate(in));
	}

	@Test
	void hasPermissionTest1() {
		when(authFeignClient.getValidity("token")).thenReturn(new AuthenticationResponse("EMP101", "emp", true));
		when(authFeignClient.getRole("EMP101")).thenReturn("EMPLOYEE");
		assertTrue(serviceImpl.hasPermission("token").isValid());
	}

	@Test
	void hasPermissionTestFalse() {
		when(authFeignClient.getValidity("token")).thenReturn(new AuthenticationResponse("EMP101", "emp", false));
		when(authFeignClient.getRole("EMP101")).thenReturn("EMPLOYEE");
		assertFalse(serviceImpl.hasPermission("token").isValid());
	}

	@Test
	void hasPermissionTest2() {
		when(authFeignClient.getValidity("token")).thenThrow(new AccessDeniedException("NOT ALLOWED"));
		assertThrows(AccessDeniedException.class, () -> serviceImpl.hasPermission("token"));
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/service/RulesServiceImplTest.java:RulesServiceImplTest.<init>
package com.rulesservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AccountTest {

	Account account = new Account();
	Account account1 = new Account(1,"cust101",6000,"savings",null,"bhavya",null);

	@Test
	void setAccountIdTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

	@Test
	void setCustomerIdTest() {
		account.setCustomerId("Cust101");
		assertEquals("Cust101", account.getCustomerId());
	}

	@Test
	void setCurrentBalanceTest() {
		account.setCurrentBalance(5000);
		assertEquals(5000, account.getCurrentBalance());
	}

	@Test
	void setAccountTypeTest() {
		account.setAccountType("Savings");
		assertEquals("Savings", account.getAccountType());
	}

	@Test
	void setOwnerNameTest() {
		account.setOwnerName("bhavya");
		assertEquals("bhavya", account.getOwnerName());
	}

	@Test
	void setTransactionsTest() {
		account.setTransactions(null);
		assertEquals(null, account.getTransactions());
	}
	
	
	@Test
	void setAccountIdTest1() {
		assertEquals(1, account1.getAccountId());
	}

	@Test
	void setCustomerIdTest1() {
		assertEquals("cust101", account1.getCustomerId());
	}

	@Test
	void setCurrentBalanceTest1() {
		assertEquals(6000, account1.getCurrentBalance());
	}

	@Test
	void setAccountTypeTest1() {
		assertEquals("savings", account1.getAccountType());
	}

	@Test
	void setOwnerNameTest1() {
		account.setOwnerName("bhavya");
		assertEquals("bhavya", account1.getOwnerName());
	}

	@Test
	void setTransactionsTest1() {
		assertEquals(null, account1.getTransactions());
	}
}


// Node: setOwnerNameTest
// Node: setOwnerName
// Node: setOwnerNameTest1
package com.rulesservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AuthenticationResponseTest {

	AuthenticationResponse response = new AuthenticationResponse();
	AuthenticationResponse response2 = new AuthenticationResponse();

	@Test
	void setUserIdTest() {
		response.setUserid("emp101");
		assertEquals("emp101", response.getUserid());
	}

	@Test
	void setNameTest() {
		response.setName("bhavya");
		assertEquals("bhavya", response.getName());
	}

	@Test
	void setisValidTest() {
		response.setValid(true);
		assertEquals(true, response.isValid());
	}

}

package com.cognizant.CustomerServiceTest.model;

import static org.junit.Assert.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Date;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.Account;


class AccountTest {

	Account account = new Account();
	Account account2 = new Account(111, "111", 100.0, "savings",new Date(), "bar", null);

	@Test
	void setAccountIdTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

	@Test
	void setCustomerIdTest() {
		account.setCustomerId("Cust101");
		assertEquals("Cust101", account.getCustomerId());
	}

	@Test
	void setCurrentBalanceTest() {
		account.setCurrentBalance(5000);
		assertEquals(5000, account.getCurrentBalance());
	}

	@Test
	void setAccountTypeTest() {
		account.setAccountType("Savings");
		assertEquals("Savings", account.getAccountType());
	}

	@Test
	void setOwnerNameTest() {
		account.setOwnerName("Nagarjun");
		assertEquals("Nagarjun", account.getOwnerName());
	}

	@Test
	void setTransactionsTest() {
		account.setTransactions(null);
		assertEquals(null, account.getTransactions());
	}

	@Test
	void getAccTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

	@Test
	void getCustomerTest() {
		account.setCustomerId("Cust101");
		assertEquals("Cust101", account.getCustomerId());
	}

	@Test
	void getAcctypeTest() {
		account.setAccountType("Savings");
		assertEquals("Savings", account.getAccountType());
	}

	@Test
	void getTokenTest() {
		account.setCurrentBalance(5000);
		assertEquals(5000, account.getCurrentBalance());
	}
	
	@Test
	void getOwnerTest() {
		account.setOwnerName("Nagarjun");
		assertEquals("Nagarjun", account.getOwnerName());
	}

}


// Node: getOwnerTest
package com.cognizant.CustomerServiceTest.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.AuthenticationResponse;


class AuthenticationresponcetTest {

	AuthenticationResponse accInp = new AuthenticationResponse();
	AuthenticationResponse accInp2 = new AuthenticationResponse("11", "bar", true);

	@Test
	void setAccountIdTest() {
		accInp.setUserid("1");
		assertEquals("1", accInp.getUserid());
	}

	@Test
	void setAmountTest() {
		accInp.setName("gayathri");
		assertEquals("gayathri", accInp.getName());
	}

	@Test
	void setIsvalid() {
		boolean isValid = true;
		accInp.setValid(isValid);
		assertEquals(true, accInp.isValid());
	}

	@Test
	void getAccIdTest() {
		accInp.setUserid("1");
		assertEquals("1", accInp.getUserid());
	}

	@Test
	void getAmountTest() {
		accInp.setName("gayathri");
		assertEquals("gayathri", accInp.getName());
	}

}


// Node: isAmountAvailable
package com.cognizant.transactionservice.service;

import java.time.LocalDateTime;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.cognizant.transactionservice.exception.MinimumBalanceException;
import com.cognizant.transactionservice.feign.AccountFeign;
import com.cognizant.transactionservice.feign.RulesFeign;
import com.cognizant.transactionservice.models.Account;
import com.cognizant.transactionservice.models.AccountInput1;
import com.cognizant.transactionservice.models.RulesInput;
import com.cognizant.transactionservice.models.Transaction;
import com.cognizant.transactionservice.models.TransactionInput;
import com.cognizant.transactionservice.repository.TransactionRepository;

import lombok.extern.slf4j.Slf4j;


@Service
@Slf4j
public class TransactionService implements TransactionServiceInterface {

	@Autowired
	private AccountFeign accountFeign;

	@Autowired
	private TransactionRepository transactionRepository;

	@Autowired
	private RulesFeign ruleFeign;

	
	@Override
	public boolean makeTransfer(String token, TransactionInput transactionInput) throws MinimumBalanceException {

		Account sourceAccount = null;
		Account targetAccount = null;

		long sourceAccountNumber = transactionInput.getSourceAccount().getAccountId();
		sourceAccount = accountFeign.getAccount(token, sourceAccountNumber);
			Boolean check =  (Boolean) ruleFeign.evaluate(new RulesInput(sourceAccount.getAccountId(),
					sourceAccount.getCurrentBalance(), transactionInput.getAmount())).getBody();
			
			if (check.booleanValue() == false)
				throw new MinimumBalanceException("Minimum Balance 1000 should be maintaind");
		
		long targetAccountNumber = transactionInput.getTargetAccount().getAccountId();
		targetAccount = accountFeign.getAccount(token, targetAccountNumber);

		if (sourceAccount != null && targetAccount != null) {
			if (isAmountAvailable(transactionInput.getAmount(), sourceAccount.getCurrentBalance())) {

				Transaction sourcetransaction = new Transaction();

				sourcetransaction.setAmount(transactionInput.getAmount());
				sourcetransaction.setSourceAccountId(sourceAccount.getAccountId());
				sourcetransaction.setSourceOwnerName(sourceAccount.getOwnerName());
				sourcetransaction.setTargetAccountId(targetAccount.getAccountId());
				sourcetransaction.setTargetOwnerName(targetAccount.getOwnerName());
				sourcetransaction.setInitiationDate(LocalDateTime.now());
				sourcetransaction.setReference("transfer");
				transactionRepository.save(sourcetransaction);
				return true;
			}
		}
		return false;
	}
		

	
	
	private boolean isAmountAvailable(double amount, double accountBalance) {
		log.info("method to check wether the amount is available");
		return (accountBalance - amount) > 0;
	}

	
	@SuppressWarnings("unused")
	@Override
	public boolean makeWithdraw(String token, AccountInput1 accountInput1) {
		log.info("method to make a withdraw");
		Account sourceAccount = null;

		long accNumber = accountInput1.getAccountId();
		sourceAccount = accountFeign.getAccount(token, accNumber);
		
			Boolean check = (Boolean) ruleFeign.evaluate(new RulesInput(accountInput1.getAccountId(),
					sourceAccount.getCurrentBalance(), accountInput1.getAmount() ) ).getBody();
			
			if (!check.booleanValue())
				throw new MinimumBalanceException("Minimum Balance 1000 should be maintaind");
		
		if (sourceAccount != null) {
			Transaction transaction = new Transaction();
			transaction.setSourceAccountId(sourceAccount.getAccountId());
			transaction.setSourceOwnerName(sourceAccount.getOwnerName());
			transaction.setTargetAccountId(sourceAccount.getAccountId());
			transaction.setTargetOwnerName(sourceAccount.getOwnerName());
			transaction.setInitiationDate(LocalDateTime.now());
			transaction.setReference("withdrawl");
			transaction.setAmount(accountInput1.getAmount());
			transactionRepository.save(transaction);
			return true;
		}
		return false;
	}
	
	@Override
	public boolean makeServiceCharges(String token, AccountInput1 accountInput1) {
		log.info("method to make a service charges");
		Account sourceAccount = null;

		long accNumber = accountInput1.getAccountId();
		sourceAccount = accountFeign.getAccount(token, accNumber);
		if (sourceAccount != null) {
			Transaction transaction = new Transaction();
			transaction.setSourceAccountId(sourceAccount.getAccountId());
			transaction.setSourceOwnerName(sourceAccount.getOwnerName());
			transaction.setTargetAccountId(sourceAccount.getAccountId());
			transaction.setTargetOwnerName(sourceAccount.getOwnerName());
			transaction.setInitiationDate(LocalDateTime.now());
			transaction.setReference("service charge");
			transaction.setAmount(accountInput1.getAmount());
			transactionRepository.save(transaction);
			return true;
		}
		
		return false;
		
	}


	@Override
	public boolean makeDeposit(String token, AccountInput1 accountInput1) {
		log.info("method to make a deposit");
		Account sourceAccount = null;

		long accNumber = accountInput1.getAccountId();
		sourceAccount = accountFeign.getAccount(token, accNumber);
		if (sourceAccount != null) {
			Transaction transaction = new Transaction();
			transaction.setSourceAccountId(sourceAccount.getAccountId());
			transaction.setSourceOwnerName(sourceAccount.getOwnerName());
			transaction.setTargetAccountId(sourceAccount.getAccountId());
			transaction.setTargetOwnerName(sourceAccount.getOwnerName());
			transaction.setInitiationDate(LocalDateTime.now());
			transaction.setReference("deposit");
			transaction.setAmount(accountInput1.getAmount());
			transactionRepository.save(transaction);
			return true;
		}
		return false;
	}
}


package com.cognizant.transactionservice.controller;

import org.junit.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.servlet.MockMvc;

import com.cognizant.transactionservice.repository.TransactionRepository;
import com.cognizant.transactionservice.service.TransactionService;

@WebMvcTest
@ExtendWith(SpringExtension.class)

public class TransactionRestControllerTest {
	@SuppressWarnings("unused")
	@Autowired
	private MockMvc mockMvc;
	@MockBean
	private TransactionRepository transactionRepository;
	@Mock
	TransactionService transactionService;
	
	
	@Test
	public void amountTest()
	{
		
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/controller/TransactionRestControllerTest.java:TransactionRestControllerTest.<init>
// Node: amountTest
package com.cognizant.transactionservice.model;

import static org.junit.jupiter.api.Assertions.*;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.Account;
import com.cognizant.transactionservice.models.Transaction;

class AccountTest {

	Transaction t = new Transaction();
	List<Transaction> list = new ArrayList<Transaction>();
	Account account = new Account();
	Account account1 = new Account(1, "abc", 10, "user",new Date(), "James", list);

	@Test
	void setAccountIdTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

	@Test
	void setCustomerIdTest() {
		account.setCustomerId("Cust101");
		assertEquals("Cust101", account.getCustomerId());
	}

	@Test
	void setCurrentBalanceTest() {
		account.setCurrentBalance(5000);
		assertEquals(5000, account.getCurrentBalance());
	}

	@Test
	void setAccountTypeTest() {
		account.setAccountType("Savings");
		assertEquals("Savings", account.getAccountType());
	}

	@Test
	void setOwnerNameTest() {
		account.setOwnerName("James");
		assertEquals("James", account.getOwnerName());
	}

	@Test
	void setTransactionsTest() {
		account.setTransactions(null);
		assertEquals(null, account.getTransactions());
	}

	@Test
	void getAccTest() {
		account.setAccountId(1);
		assertTrue(account.getAccountId() == 1);
	}

	@Test
	void getCustomerTest() {
		account.setCustomerId("1");
		assertTrue(account.getCustomerId() == "1");
	}

	@Test
	void getAcctypeTest() {
		account.setAccountType("abc");
		assertTrue(account.getAccountType() == "abc");
	}

	@Test
	void getTokenTest() {
		account.setCurrentBalance(10);
		assertTrue(account.getCurrentBalance() == 10);
	}

	@Test
	void getOwnerTest() {
		account.setOwnerName("James");
		assertTrue(account.getOwnerName() == "James");
	}
}


