// Cluster 4

package com.cognizant.accountservice;

import java.util.Collections;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;

import com.cognizant.accountservice.controller.AccountController;

import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;


@SpringBootApplication
@EnableFeignClients
@EnableSwagger2
public class AccountserviceApplication {

	private static final Logger LOGGER = LoggerFactory.getLogger(AccountController.class);

	public static void main(String[] args) { 
		SpringApplication.run(AccountserviceApplication.class, args);
		LOGGER.info("Account microservice started....");
	}
	
	/*
	 * Adding Swaggar2 REST API Documentation bean
	 */
	@Bean
	public Docket swaggerConfiguration() {

		return new Docket(DocumentationType.SWAGGER_2).select()
				.apis(RequestHandlerSelectors.basePackage("com.cognizant.accountservice.controller")).build().apiInfo(apiInfo());
 
	}

	
	private ApiInfo apiInfo() {
		return new ApiInfo("Account Management Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("Peoples' Bank", "", "abc@email.com"), "License of API", "", Collections.emptyList());
	}

}


// Node: swaggerConfiguration
// Node: Docket
// Node: select
// Node: apis
// Node: basePackage
// Node: build
// Node: apiInfo
// Node: ApiInfo
// Node: Contact
// Node: emptyList
// Node: MinimumBalanceException
package com.cognizant.accountservice.exceptionhandling;

public class AccountNotFoundException extends RuntimeException {

	private static final long serialVersionUID = 1L;

	public AccountNotFoundException() {
		super();
	}

	public AccountNotFoundException(String message) {
		super(message);
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/exceptionhandling/AccountNotFoundException.java:AccountNotFoundException.<init>
// Node: AccountNotFoundException
package com.cognizant.accountservice.exceptionhandling;

public class MinimumBalanceException extends RuntimeException {

	private static final long serialVersionUID = 1L;

	public MinimumBalanceException() {
		super();
	}

	public MinimumBalanceException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/exceptionhandling/MinimumBalanceException.java:MinimumBalanceException.<init>
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

package com.cognizant.accountservice.exception;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.Test;

import com.cognizant.accountservice.exceptionhandling.MinimumBalanceException;

public class MinimumBalanceTest {
	
	@Test
	public void MinimumException() {
		
		MinimumBalanceException e1=new  MinimumBalanceException("hello");
		MinimumBalanceException e2=new  MinimumBalanceException("hello");
		assertThat(e1).isNotEqualTo(e2);
		
	}
	
	@Test
	public void MinimumExceptionNull() {
		
		MinimumBalanceException e1=new  MinimumBalanceException();
		MinimumBalanceException e2=new  MinimumBalanceException();
		assertThat(e1).isNotEqualTo(e2);
		
	}

}


// Node: MinimumException
// Node: assertThat
// Node: isNotEqualTo
// Node: MinimumExceptionNull
package com.cognizant.accountservice.exception;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.Test;

import com.cognizant.accountservice.exceptionhandling.AccountNotFoundException;

public class AccountNotFoundTest {
	
	@Test
	public void AccountException() {
		
		AccountNotFoundException e1=new AccountNotFoundException("hello");
		AccountNotFoundException e2=new AccountNotFoundException("hello");
		assertThat(e1).isNotEqualTo(e2);
		
	}
	
	@Test
	public void AccountExceptionNull() {
		
		AccountNotFoundException e1=new AccountNotFoundException();
		AccountNotFoundException e2=new AccountNotFoundException();
		assertThat(e1).isNotEqualTo(e2);
		
	}

}


// Node: AccountException
// Node: AccountExceptionNull
package com.cognizant.authenticationservice.exceptionhandling;

//Class for APPUSER is not found in DB
public class AppUserNotFoundException extends Exception 
{
	/**
	*
	*
	* @author Authentication MS
	*/
	private static final long serialVersionUID = 1L;
	
	public AppUserNotFoundException() 
	{
		super();
		//Empty Constructor
	}

	public AppUserNotFoundException(final String message) 
	{
		//Constructor for AppUserNotFoundException
		super(message);
	}
}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/main/java/com/cognizant/authenticationservice/exceptionhandling/AppUserNotFoundException.java:AppUserNotFoundException.<init>
// Node: AppUserNotFoundException
package com.cognizant.authenticationservice.model;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.Test;

import com.cognizant.authenticationservice.exceptionhandling.AppUserNotFoundException;

public class AppUserNotFountTest {
	
	@Test
	public void appTest()
	{
		AppUserNotFoundException ae=new AppUserNotFoundException();
		AppUserNotFoundException ae1=new AppUserNotFoundException();
		assertThat(ae).isNotEqualTo(ae1);
	}
	
	@Test
	public void appTest1()
	{
		AppUserNotFoundException ae=new AppUserNotFoundException("hello");
		AppUserNotFoundException ae1=new AppUserNotFoundException("hello");
		assertThat(ae).isNotEqualTo(ae1);
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/test/java/com/cognizant/authenticationservice/model/AppUserNotFountTest.java:AppUserNotFountTest.<init>
// Node: appTest
// Node: appTest1
package com.rulesservice;

import java.util.Collections;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@EnableFeignClients
@EnableSwagger2
@SpringBootApplication
public class RulesServiceApplication {

	public static void main(String[] args) {
		SpringApplication.run(RulesServiceApplication.class, args);
	}

	@Bean
	public Docket swaggerConfiguration() {

		return new Docket(DocumentationType.SWAGGER_2).select()
				.apis(RequestHandlerSelectors.basePackage("com.rulesservice.controller")).build().apiInfo(apiInfo());

	}

	private ApiInfo apiInfo() {
		return new ApiInfo("RulesService", "MFPE project service", "API", "Terms of service",
				new Contact("Peoples Bank", "", "abcbanking@gmail.com"), "License of API", "", Collections.emptyList());
	}
}


package com.rulesservice.exception;

public class MinimumBalanceException extends RuntimeException {

	private static final long serialVersionUID = 1L;

	public MinimumBalanceException() {
		super();
	}

	public MinimumBalanceException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/exception/MinimumBalanceException.java:MinimumBalanceException.<init>
// Node: minBalance
package com.rulesservice.model;


public class MinimumBalanceException extends RuntimeException{

	
	private static final long serialVersionUID = 1L;

	public MinimumBalanceException() {
		super();
	}

	
	public MinimumBalanceException(String message) {
		super(message);
	}

	
	
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/model/MinimumBalanceException.java:MinimumBalanceException.<init>
package com.rulesservice.model;

import static org.assertj.core.api.Assertions.assertThat;
import org.junit.Test;

public class MinimumBalanceTest {

	@Test
	public void minBalance() {
		MinimumBalanceException mb = new MinimumBalanceException();
		MinimumBalanceException mb2 = new MinimumBalanceException();
		assertThat(mb).isNotEqualTo(mb2);
	}

	@Test
	public void minBalance2() {
		MinimumBalanceException mb = new MinimumBalanceException("balance error");
		MinimumBalanceException mb2 = new MinimumBalanceException("balance error");
		assertThat(mb).isNotEqualTo(mb2);
	}

}


// Node: minBalance2
package com.cognizant.customerservice.exception;

public class ConsumerAlreadyExistException extends RuntimeException {

	private static final long serialVersionUID = -2862505141325062716L;

	public ConsumerAlreadyExistException() {
		super();
	}

	public ConsumerAlreadyExistException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/exception/ConsumerAlreadyExistException.java:ConsumerAlreadyExistException.<init>
// Node: ConsumerAlreadyExistException
package com.cognizant.customerservice.exception;

public class CustomerNotFoundException extends RuntimeException {

	private static final long serialVersionUID = 1L;

	public CustomerNotFoundException() {
		super();
	}

	public CustomerNotFoundException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/exception/CustomerNotFoundException.java:CustomerNotFoundException.<init>
// Node: CustomerNotFoundException
package com.cognizant.customerservice.exception;

public class LoginFailedException extends RuntimeException {

	private static final long serialVersionUID = 1L;

	public LoginFailedException() {
		super();
	}

	public LoginFailedException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/exception/LoginFailedException.java:LoginFailedException.<init>
// Node: LoginFailedException
package com.cognizant.CustomerService.test;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.Test;

import com.cognizant.customerservice.exception.ConsumerAlreadyExistException;

public class CustomerAlreadyExistTest {
	
	
	@Test
	public void customerAlreadyExist() {
		ConsumerAlreadyExistException e1 = new ConsumerAlreadyExistException("hi");
		ConsumerAlreadyExistException e2 = new ConsumerAlreadyExistException("hi");
		assertThat(e1).isNotEqualTo(e2);
	}
	@Test
	public void customerAlreadyExist2() {
		ConsumerAlreadyExistException e1 = new ConsumerAlreadyExistException();
		ConsumerAlreadyExistException e2 = new ConsumerAlreadyExistException();
		assertThat(e1).isNotEqualTo(e2);
	}
	
	@Test
	public void customerAlreadyExist1() {
		ConsumerAlreadyExistException e1 = new ConsumerAlreadyExistException("hello");
		ConsumerAlreadyExistException e2 = new ConsumerAlreadyExistException("hello");
		assertThat(e1).isNotEqualTo(e2);
	}

}


// Node: customerAlreadyExist
// Node: customerAlreadyExist2
// Node: customerAlreadyExist1
package com.cognizant.CustomerService.test;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.Test;

import com.cognizant.customerservice.exception.AccessDeniedException;

public class AccessDeniedTest {
	
	//AccessDeniedTest accessDeniedTest=mock(AccessDeniedTest.class);
	@Test
	public void AccessException() {
		
		AccessDeniedException e1=new AccessDeniedException("hello");
		AccessDeniedException e2=new AccessDeniedException("hello");
		assertThat(e1).isNotEqualTo(e2);
		
	}
	
	@Test
	public void AccessExceptionNull() {
		
		AccessDeniedException e1=new AccessDeniedException();
		AccessDeniedException e2=new AccessDeniedException();
		assertThat(e1).isNotEqualTo(e2);
		
	}
	


}


// Node: AccessException
// Node: AccessExceptionNull
package com.cognizant.CustomerService.test;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.exception.LoginFailedException;

public class LoginFailedExceptionTest {
	
	@Test
	void loginTest()
	{
		LoginFailedException l1=new LoginFailedException("harini");
		LoginFailedException l2=new LoginFailedException("harini");
		assertThat(l1).isNotEqualTo(l2);
	}
	
	@Test
	void loginTest2()
	{
		LoginFailedException l1=new LoginFailedException();
		LoginFailedException l2=new LoginFailedException();
		assertThat(l1).isNotEqualTo(l2);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerService/test/LoginFailedExceptionTest.java:LoginFailedExceptionTest.<init>
// Node: loginTest
// Node: loginTest2
package com.cognizant.CustomerService.test;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.exception.CustomerNotFoundException;

public class CustomerNotFountTest {
	

	@Test
	void customerTest()
	{
		CustomerNotFoundException l1=new CustomerNotFoundException("prabha");
		CustomerNotFoundException l2=new CustomerNotFoundException("prabha");
		assertThat(l1).isNotEqualTo(l2);
	}
	
	@Test
	void customerTest2()
	{
		CustomerNotFoundException l1=new CustomerNotFoundException();
		CustomerNotFoundException l2=new CustomerNotFoundException();
		assertThat(l1).isNotEqualTo(l2);
	}
	

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerService/test/CustomerNotFountTest.java:CustomerNotFountTest.<init>
// Node: customerTest
// Node: customerTest2
package com.cognizant.CustomerService.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.Assert.assertEquals;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.sql.Date;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit4.SpringJUnit4ClassRunner;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import com.cognizant.customerservice.model.AuthenticationResponse;
import com.cognizant.customerservice.CustomerServiceApplication;
import com.cognizant.customerservice.model.AppUser;
import com.cognizant.customerservice.model.CustomerEntity;
import com.cognizant.customerservice.service.CustomerService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;

@SpringBootTest
@RunWith(SpringJUnit4ClassRunner.class)
@ContextConfiguration(classes = { CustomerServiceApplication.class })
public class CustomerTests {

	public String token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJFTVBMT1lFRTEwMSIsImV4cCI6MTYwODU3MDk1MSwiaWF0IjoxNjA4MzU0OTUxfQ.CLuewsfeFIYwVIGftqkMGhvuEf4PqP4Fl8TKKIifNtw";

	private MockMvc mockMvc;

	@Autowired
	private WebApplicationContext wc;
	@MockBean
	private CustomerService customerService;

	List<AppUser> employees = new ArrayList<AppUser>();
	static ObjectMapper MAPPER = new ObjectMapper();

	@Before
	public void setUp() throws JsonProcessingException, Exception {
		mockMvc = MockMvcBuilders.webAppContextSetup(wc).build();
	}

	@Test
	public void createCustomer() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = null;
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/createCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(400)).andReturn();

	}

	@Test
	public void saveCustomerNull() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = null;
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/saveCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(400)).andReturn();

	}

	@Test
	public void saveCustomers() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCDE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("1234");
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/saveCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(200)).andReturn();

	}

	@Test
	public void saveCustomers2() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCFE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("12345");
		String json = MAPPER.writeValueAsString(ce);
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/saveCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(200)).andReturn();

	}

	@Test
	public void updateCustomers() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCDE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("CUSTOMER101");
		String json = MAPPER.writeValueAsString(ce);
		when(customerService.hasEmployeePermission("token"))
				.thenReturn(new AuthenticationResponse("CUSTOMER101", "cust", true));
		@SuppressWarnings("unused")
		MvcResult andReturn = mockMvc
				.perform(MockMvcRequestBuilders.post("/updateCustomer").header("Authorization", "Bearer " + token)
						.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(200)).andReturn();

	}

	@Test
	public void getCustomersSuccess() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCFE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("CUSTOMER101");
		when(customerService.hasPermission("token"))
				.thenReturn(new AuthenticationResponse("CUSTOMER101", "cust", true));
		when(customerService.getCustomerDetail("token", "CUSTOMER101")).thenReturn(ce);
		mockMvc.perform(get("/getCustomerDetails/CUSTOMER101").header("Authorization", "token"))
				.andExpect(status().isOk());
	}

	@Test
	public void getCustomersfail() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCFE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("CUSTOMER101");
		when(customerService.hasEmployeePermission(token))
				.thenReturn(new AuthenticationResponse("CUSTOMER101", "cust", true));
		when(customerService.getCustomerDetail(token, "CUSTOMER101")).thenReturn(ce);
		mockMvc.perform(MockMvcRequestBuilders.get("/getCustomerDetails/CUSTOMER101").header("Authorization",
				"Bearer " + token)).andExpect(status().is(406));

	}

	@Test
	public void unsuccesfulCustomer() throws JsonProcessingException, Exception {
		System.err.println(token);
		CustomerEntity ce = new CustomerEntity();
		ce.setAddress("Hyderabad");
		ce.setDateOfBirth(new Date(60));
		ce.setPan("ABCDE1234R");
		ce.setPassword("prabha");
		ce.setUsername("prabha");
		ce.setUserid("1234");
		String json = MAPPER.writeValueAsString(ce);
		mockMvc.perform(MockMvcRequestBuilders.post("/createCustomer").header("Authorization", "Bearer " + token)
				.content(json).contentType(MediaType.APPLICATION_JSON).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().is(406)).andReturn();
	}

	@Test
	public void withoutValidate() throws Exception {
		MvcResult andReturn = mockMvc.perform(MockMvcRequestBuilders.get("/check")
				.header("Authorization", "Bearer " + token).accept(MediaType.APPLICATION_JSON))
				.andExpect(status().isOk()).andReturn();
		String contentAsString = andReturn.getResponse().getContentAsString();
		assertEquals("Your Token is valid", contentAsString);
	}

	@Test
	public void deleteNotPresentEmployeeAPI() throws Exception {
		mockMvc.perform(MockMvcRequestBuilders.delete("/deleteCustomer/CUSTOMER101", 1).header("Authorization",
				"Bearer " + token)).andExpect(status().is(406));
	}


	@Test
	public void AppInfoCheck() {
		ApiInfo a1 = new ApiInfo("Customer Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("ABC", "", "abc@email.com"), "License of API", "", Collections.emptyList());
		ApiInfo a2 = new ApiInfo("Customer Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("ABC", "", "abc@email.com"), "License of API", "", Collections.emptyList());
		assertThat(a1).isNotEqualTo(a2);
	}

}

// Node: AppInfoCheck
package com.cognizant.transactionservice;

import java.util.Collections;

import org.springframework.boot.SpringApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.Bean;

import lombok.extern.slf4j.Slf4j;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.ApiInfo;
import springfox.documentation.service.Contact;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@EnableSwagger2
@Slf4j
public class TransactionserviceApplication {

	public static void main(String[] args) {
		log.info("TransactionserviceApplication is started");
		SpringApplication.run(TransactionserviceApplication.class, args);
	}

	@Bean
	public Docket swaggerConfiguration() {

		return new Docket(DocumentationType.SWAGGER_2).select()
				.apis(RequestHandlerSelectors.basePackage("com.cognizant.transactionservice.controller")).build()
				.apiInfo(apiInfo());

	}

	private ApiInfo apiInfo() {
		return new ApiInfo("Transaction Service", "Retail Banking Project", "API", "Terms of service",
				new Contact("Peoples' Bank", "", "abc@email.com"), "License of API", "", Collections.emptyList());
	}

}


package com.cognizant.transactionservice.exception;

public class MinimumBalanceException extends RuntimeException {

	private static final long serialVersionUID = 1L;

	public MinimumBalanceException(String message) {
		super(message);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/exception/MinimumBalanceException.java:MinimumBalanceException.<init>
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/AuthenticationMsApplication.class:AuthenticationMsApplication
// Node: src.main.java.com.retailbank.AuthenticationMS.AuthenticationMsApplication
// Node: SpringBootApplication
// Node: Bean
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/TransactionserviceApplication.class:TransactionserviceApplication
// Node: src.main.java.com.cognizant.transactionservice.TransactionserviceApplication
// Node: EnableFeignClients
// Node: EnableSwagger2
