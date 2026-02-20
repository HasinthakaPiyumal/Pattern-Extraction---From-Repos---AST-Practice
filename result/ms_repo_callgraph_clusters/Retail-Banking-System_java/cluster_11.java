// Cluster 11

package com.cognizant.accountservice.exceptionhandling;

public class AccessDeniedException extends RuntimeException {

	private static final long serialVersionUID = 1L;

	public AccessDeniedException() {
		super();
	}

	public AccessDeniedException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/exceptionhandling/AccessDeniedException.java:AccessDeniedException.<init>
// Node: AccessDeniedException
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

// Node: tokenValidation
// Node: getRole
// Node: equalsIgnoreCase
// Node: hasCustomerPermission
// Node: when
// Node: thenReturn
// Node: thenThrow
// Node: assertThrows
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


// Node: hasPermissionTest1
// Node: AuthenticationResponse
// Node: isValid
// Node: hasPermissionTest2
// Node: hasCustomerPermissionTest1
// Node: hasCustomerPermissionTest2
// Node: hasEmployeePermissionTest1
// Node: hasEmployeePermissionTest2
// Node: updateBalanceTest
// Node: updateDepositBalanceTest
// Node: setValid
// Node: getValidity
// Node: equals
// Node: getRoleTest
// Node: setRole
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


// Node: getAccounTest
// Node: setisValidTest
package com.rulesservice.exception;

public class AccessDeniedException extends RuntimeException {

	private static final long serialVersionUID = 895616911464801474L;

	public AccessDeniedException() {
		super();
	}

	public AccessDeniedException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/exception/AccessDeniedException.java:AccessDeniedException.<init>
package com.rulesservice.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.rulesservice.exception.AccessDeniedException;
import com.rulesservice.feign.AuthorizationFeign;
import com.rulesservice.model.Account;
import com.rulesservice.model.AuthenticationResponse;
import com.rulesservice.model.RulesInput;

@Service
public class RulesServiceImpl implements RulesService {

	@Autowired
	AuthorizationFeign authorizationFeign;

	@Override
	public boolean evaluate(RulesInput account) {
		int min = 1000;
		double check = account.getCurrentBalance() - account.getAmount();
		if (check >= min)
			return true;
		else
			return false;
	}

	@Override
	public AuthenticationResponse hasPermission(String token) {
		AuthenticationResponse validity = authorizationFeign.getValidity(token);
		if (!authorizationFeign.getRole(validity.getUserid()).equals("EMPLOYEE"))
			throw new AccessDeniedException("NOT ALLOWED");
		else
			return validity;
	}

	@Override
	public double serviceCharges(Account account) {
		double detected = account.getCurrentBalance() / 10;
		if (account.getCurrentBalance() < 2000 && (account.getCurrentBalance() - detected) > 0) {
			return detected;
		} 
		return 0.0;
	}

}


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


// Node: hasPermissionTestFalse
// Node: assertFalse
package com.rulesservice.model;

import static org.junit.Assert.assertFalse;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

import com.rulesservice.service.RulesServiceImpl;

class RulesInputTest {
	RulesInput accInp = new RulesInput();
	RulesInput rul = new RulesInput(1000000003, 100, 10);
	RulesInput rul1 = new RulesInput(1000000004, 1100, 100);
	RulesServiceImpl rs = new RulesServiceImpl();

	@Test
	void EvaluateFalseTest() {

		assertFalse(rs.evaluate(rul));
	}

	@Test
	void EvaluateTrueTest() {

		assertTrue(rs.evaluate(rul1));
	}

	@Test
	void setAccountIdTest() {
		accInp.setAccountId(1000000001);
		assertEquals(1000000001, accInp.getAccountId());
	}

	@Test
	void setAmountTest() {
		accInp.setAmount(500);
		assertEquals(500, accInp.getAmount());
	}

	@Test
	void getAccountIdTest() {
		accInp.setAccountId(1000000003);
		assertTrue(accInp.getAccountId() == rul.getAccountId());
	}

	@Test
	void getCurrBalanceTest() {
		accInp.setCurrentBalance(500);
		assertTrue(accInp.getCurrentBalance() == 500);
	}

	@Test
	void getAmountTest() {
		accInp.setAmount(10);
		assertTrue(accInp.getAmount() == rul.getAmount());
	}

	ServiceResponse res = new ServiceResponse();

	@Test
	void setAccountIdTest1() {
		res.setAccountId(1);
		assertEquals(1, res.getAccountId());
	}

	@Test
	void setAmountTest2() {
		res.setMessage("abcd");
		assertEquals("abcd", res.getMessage());
	}

	@Test
	void setBalanceTest() {
		res.setBalance(2000.0);
		assertEquals(2000.0, res.getBalance());
	}
}


// Node: EvaluateFalseTest
package com.rulesservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AppUserTest {

	AppUser accInp = new AppUser();
	AppUser accInp2 = new AppUser("2","bhavya","bhavya","xyz","user");

	@Test
	void setAccountIdTest() {
		accInp.setUsername("bhavya");
		assertEquals("bhavya", accInp.getUsername());
	}

	@Test
	void setAmountTest() {
		accInp.setUserid("emp");
		assertEquals("emp", accInp.getUserid());
	}

	@Test
	public void setPasswoedTest() {
		accInp.setPassword("abc");
		assertEquals("abc", accInp.getPassword());
	}

	@Test
	public void setAuthTokenTest() {
		accInp.setAuthToken("token");
		assertEquals("token", accInp.getAuthToken());
	}

	@Test
	public void setRoleTest() {
		accInp.setRole("user");
		assertEquals("user", accInp.getRole());
	}
	
	@Test
	void getAccIdTest1() {
		assertEquals("2", accInp2.getUserid());
	}

	@Test
	void getRoleTest1() {
		assertEquals("user", accInp2.getRole());
	}

	@Test
	void getUsernameTest1() {
		assertEquals("bhavya", accInp2.getUsername());
	}

	@Test
	void getPasswordTest1() {
		assertEquals("bhavya", accInp2.getPassword());
	}

	@Test
	void getTokenTest1() {
		assertEquals("xyz", accInp2.getAuthToken());
	}
}

// Node: setRoleTest
// Node: getRoleTest1
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

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/model/AuthenticationResponseTest.java:AuthenticationResponseTest.<init>
package com.cognizant.customerservice.exception;

public class AccessDeniedException extends RuntimeException {

	private static final long serialVersionUID = 895616911464801474L;

	public AccessDeniedException() {
		super();
	}

	public AccessDeniedException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/exception/AccessDeniedException.java:AccessDeniedException.<init>
package com.cognizant.customerservice.service;

import java.util.List;
import java.util.Optional;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.cognizant.customerservice.exception.AccessDeniedException;
import com.cognizant.customerservice.feign.AccountFeign;
import com.cognizant.customerservice.feign.AuthorizationFeign;
import com.cognizant.customerservice.model.Account;
import com.cognizant.customerservice.model.AppUser;
import com.cognizant.customerservice.model.AuthenticationResponse;
import com.cognizant.customerservice.model.CustomerEntity;
import com.cognizant.customerservice.repository.CustomerRepository;

import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
public class CustomerServiceImpl implements CustomerService {

	private static final String CUSTOMER = "CUSTOMER";
	
	/**
	 * Autowiring the FeignClient Services to communicate with other microservices
	 */
	@Autowired
	AuthorizationFeign authorizationFeign;
	@Autowired
	AccountFeign accountFeign;

	/**
	 * Autowiring the repository
	 */
	@Autowired
	CustomerRepository customerRepo;

	/**
	 * Validating the token using authorization microservice
	 */
	@Override
	public AuthenticationResponse hasPermission(String token) {
		return authorizationFeign.getValidity(token);
	}

	/**
	 * Checking whether the user has employee permission or not
	 */
	@Override
	public AuthenticationResponse hasEmployeePermission(String token) {
		AuthenticationResponse validity = authorizationFeign.getValidity(token);
		if (!authorizationFeign.getRole(validity.getUserid()).equals("EMPLOYEE"))
			throw new AccessDeniedException("NOT ALLOWED");
		else
			return validity;
	}

	/**
	 * Checking whether the user has customer permission or not
	 */
	@Override
	public AuthenticationResponse hasCustomerPermission(String token) {
		AuthenticationResponse validity = authorizationFeign.getValidity(token);
		if (!authorizationFeign.getRole(validity.getUserid()).equals(CUSTOMER))
			throw new AccessDeniedException("NOT ALLOWED");
		else
			return validity;
	}

	/**
	 * Creating new customer and storing it in the database
	 */
	@Override
	public CustomerEntity createCustomer(String token, CustomerEntity customer) {

		CustomerEntity checkCustomerExists = getCustomerDetail(token, customer.getUserid());
		if (checkCustomerExists == null) {
			AppUser user = new AppUser(customer.getUserid(), customer.getUsername(), customer.getPassword(), null,CUSTOMER);
			authorizationFeign.createUser(user);
		}

		for (Account acc : customer.getAccounts()) {
			accountFeign.createAccount(token, customer.getUserid(), acc);
		}

		customerRepo.save(customer);
		log.info("Customer details saved.");
		return customer;
	}

	/**
	 * Getting the customer details based on the customer id
	 */
	@Override
	public CustomerEntity getCustomerDetail(String token, String id) {
		Optional<CustomerEntity> customer = customerRepo.findById(id);
		if (!customer.isPresent())
			return null;
		log.info("Customer details fetched.");
		List<Account> list = accountFeign.getCustomerAccount(token, id);
		customer.get().setAccounts(list);
		return customer.get();
	}

	/**
	 * Deleting the customer details associated with the given customer id
	 */
	@Override
	public boolean deleteCustomer(String id) {
		CustomerEntity customer = customerRepo.findById(id).get();
		if (customer != null)
			customerRepo.deleteById(id);
		else
			return false;
		log.info("Customer details deleted.");
		return true;
	}
	
	/**
	 * Updating the customer details based on customer id
	 */
	@Override
	public CustomerEntity updateCustomer(String token, CustomerEntity customer) {
		CustomerEntity toUpdate = customerRepo.findById(customer.getUserid()).get();
		toUpdate.setAccounts(customer.getAccounts());
		for (Account acc : customer.getAccounts()) {
			accountFeign.createAccount(token, customer.getUserid(), acc);
		}
		return customerRepo.save(toUpdate);
	}
	
	/**
	 * Saving customer record in the database
	 */
	@Override
	public CustomerEntity saveCustomer(String token, CustomerEntity customer) {
		CustomerEntity checkCustomerExists = getCustomerDetail(token, customer.getUserid());
		if (checkCustomerExists == null) {
			AppUser user = new AppUser(customer.getUserid(), customer.getUsername(), customer.getPassword(), null,	CUSTOMER);
			authorizationFeign.createUser(user);
		}
		log.info("Customer details saved.");
		return customerRepo.save(customer);
	}

}


package com.cognizant.customerservice.model;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@ToString
@NoArgsConstructor
@AllArgsConstructor
public class AuthenticationResponse {
	
	public AuthenticationResponse(boolean isValid) {
		super();
		this.isValid = isValid;
	}
	@Getter
	@Setter
	private String userid;
	@Getter
	@Setter
	private String name;
	@Getter
	@Setter
	private boolean isValid;
	
}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/model/AuthenticationResponse.java:AuthenticationResponse.<init>
package com.cognizant.CustomerServiceTest.model;

import static org.junit.Assert.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.AppUser;


class AppUserTest {
	AppUser accInp = new AppUser();
	AppUser accInp2 = new AppUser("2","prabha","prabha","xyz","user");

	@Test
	void setAccountIdTest() {
		accInp.setUserid("1");
		assertEquals("1", accInp.getUserid());
	}

	@Test
	void setRoleTest() {
		accInp.setRole("user");
		assertEquals("user", accInp.getRole());
	}

	@Test
	void setUsernameTest() {
		accInp.setUsername("1");
		assertEquals("1", accInp.getUsername());
	}

	@Test
	void setPassTest() {
		accInp.setPassword("user");
		assertEquals("user", accInp.getPassword());
	}

	@Test
	void setAuthTokenTest() {
		accInp.setAuthToken("user");
		assertEquals("user", accInp.getAuthToken());
	}

	@Test
	void getAccIdTest() {
		accInp.setUserid("1");
		assertEquals("1", accInp.getUserid());
	}

	@Test
	void getRoleTest() {
		accInp.setRole("user");
		assertEquals("user", accInp.getRole());
	}

	@Test
	void getUsernameTest() {
		accInp.setUsername("1");
		assertEquals("1", accInp.getUsername());
	}

	@Test
	void getPasswordTest() {
		accInp.setPassword("user");
		assertEquals("user", accInp.getPassword());
	}

	@Test
	void getTokenTest() {
		accInp.setAuthToken("token");
		assertEquals("token", accInp.getAuthToken());
	}

	@Test
	void getAccIdTest1() {
		assertEquals("2", accInp2.getUserid());
	}

	@Test
	void getRoleTest1() {
		assertEquals("user", accInp2.getRole());
	}

	@Test
	void getUsernameTest1() {
		assertEquals("prabha", accInp2.getUsername());
	}

	@Test
	void getPasswordTest1() {
		assertEquals("prabha", accInp2.getPassword());
	}

	@Test
	void getTokenTest1() {
		assertEquals("xyz", accInp2.getAuthToken());
	}
	
	

}


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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerServiceTest/model/AuthenticationresponcetTest.java:AuthenticationresponcetTest.<init>
// Node: setIsvalid
