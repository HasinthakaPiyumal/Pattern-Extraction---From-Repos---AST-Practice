// Cluster 0

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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/AccountserviceApplication.java:AccountserviceApplication.<init>
// Node: getLogger
// Node: info
package com.cognizant.accountservice.controller;

import java.text.ParseException;
import java.util.List;

import javax.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.cognizant.accountservice.exceptionhandling.MinimumBalanceException;
import com.cognizant.accountservice.feignclient.TransactionFeign;
import com.cognizant.accountservice.model.Account;
import com.cognizant.accountservice.model.AccountCreationStatus;
import com.cognizant.accountservice.model.AccountInput;
import com.cognizant.accountservice.model.MessageDetails;
import com.cognizant.accountservice.model.Statement;
import com.cognizant.accountservice.model.Transaction;
import com.cognizant.accountservice.model.TransactionInput;
import com.cognizant.accountservice.service.AccountServiceImpl;

@RestController
@CrossOrigin()
public class AccountController { 

	private static final Logger LOGGER = LoggerFactory.getLogger(AccountController.class);
	
	@Autowired
	private MessageDetails messageDetails;
	
	@Autowired
	private AccountServiceImpl accountServiceImpl;
	
	@Autowired
	private TransactionFeign transactionFeign; 
	
	/*
	 * Getting the account details for given account id
	 */
	@GetMapping("/getAccount/{accountId}")
	public ResponseEntity<Account> getAccount(@RequestHeader("Authorization") String token,@PathVariable long accountId) {
		accountServiceImpl.hasPermission(token);
		Account accountReturnObject = accountServiceImpl.getAccount(accountId);
		LOGGER.info("Account Details Returned Successfully");
		return new ResponseEntity<>(accountReturnObject, HttpStatus.OK);
	}
	
	/*
	 * Creating a new account for an existing customer
	 */
	@PostMapping("/createAccount/{customerId}")
	public ResponseEntity<?> createAccount(@RequestHeader("Authorization") String token,@PathVariable String customerId,@Valid @RequestBody Account account) {
		accountServiceImpl.hasEmployeePermission(token);
		AccountCreationStatus returnObjAccountCreationStatus = accountServiceImpl.createAccount(customerId, account);
		if (returnObjAccountCreationStatus == null) {
			LOGGER.error("Customer Creation Unsuccessful");
			return new ResponseEntity<>("Customer Creation Unsuccessful", HttpStatus.NOT_ACCEPTABLE);
		}
			
		LOGGER.info("Account Created Successfully");
		return new ResponseEntity<>(returnObjAccountCreationStatus, HttpStatus.CREATED);
	}
	
	/*
	 * Getting all the existing account details for the specified customer
	 */
	@GetMapping("/getAccounts/{customerId}")
	public ResponseEntity<List<Account>> getCustomerAccount(@RequestHeader("Authorization") String token,@PathVariable String customerId) {
		accountServiceImpl.hasPermission(token);
		LOGGER.info("Account List Returned");
		return new ResponseEntity<>(accountServiceImpl.getCustomerAccount(token, customerId), HttpStatus.OK);
	}

	/*
	 * Depositing amount in the specified account
	 */
	@PostMapping("/deposit")
	public ResponseEntity<Account> deposit(@RequestHeader("Authorization") String token,@RequestBody AccountInput accInput) {
		accountServiceImpl.hasPermission(token);
		transactionFeign.makeDeposit(token, accInput);
		//Updating the new current balance after deposit
		Account newUpdateAccBal = accountServiceImpl.updateDepositBalance(accInput);
		List<Transaction> list = transactionFeign.getTransactionsByAccId(token, accInput.getAccountId());
		newUpdateAccBal.setTransactions(list);
		accountServiceImpl.updateStatement(accInput,newUpdateAccBal,"Deposited");
		LOGGER.info("Amount Deposited");
		return new ResponseEntity<>(newUpdateAccBal, HttpStatus.OK);
	}

	/*
	 * Withdrawing amount from a specified account
	 */
	@PostMapping("/withdraw")
	public ResponseEntity<Account> withdraw(@RequestHeader("Authorization") String token, @RequestBody AccountInput accInput) {
		accountServiceImpl.hasPermission(token);
		try {
			transactionFeign.makeWithdraw(token, accInput);

		} catch (Exception e) {
			LOGGER.error("Minimum Balance 1000 should be maintaind");
			throw new MinimumBalanceException("Minimum Balance 1000 should be maintaind");
		}
		//Updating the new current balance after withdrawal
		Account newUpdateAccBal = accountServiceImpl.updateBalance(accInput);
		List<Transaction> list = transactionFeign.getTransactionsByAccId(token, accInput.getAccountId());
		newUpdateAccBal.setTransactions(list);
		accountServiceImpl.updateStatement(accInput,newUpdateAccBal,"Withdrawn");
		LOGGER.info("Amount withdrawn successfully");
		return new ResponseEntity<>(newUpdateAccBal, HttpStatus.OK);
	}
	
	/*
	 * Service charge deduction from the accounts that are having minimum balance
	 */
	@PostMapping("/servicecharge")
	public ResponseEntity<Account> servicecharge(@RequestHeader("Authorization") String token,@RequestBody AccountInput accInput) {
		accountServiceImpl.hasPermission(token);
		try {
			transactionFeign.makeServiceCharges(token, accInput);

		} catch (Exception e) {
			LOGGER.error("Minimum Balance 1000 should be maintaind");
			throw new MinimumBalanceException("Minimum Balance 1000 should be maintaind");
		}
		//Updating the new current balance after service charge deduction
		Account newUpdateAccBal = accountServiceImpl.updateBalance(accInput);
		List<Transaction> list = transactionFeign.getTransactionsByAccId(token, accInput.getAccountId());
		newUpdateAccBal.setTransactions(list);
		accountServiceImpl.updateStatement(accInput,newUpdateAccBal,"Service charge");
		LOGGER.info("Service charge deducted successfully");
		return new ResponseEntity<>(newUpdateAccBal, HttpStatus.OK);
	}

	/*
	 * Transferring amount from one account to another account
	 */
	@PostMapping("/transaction")
	public ResponseEntity<?> transaction(@RequestHeader("Authorization") String token, @RequestBody TransactionInput transInput) {
		accountServiceImpl.hasPermission(token);
		boolean status = true;
		try {
			status = transactionFeign.makeTransfer(token, transInput);

		} catch (Exception e) {
			LOGGER.error("Minimum Balance 1000 should be maintaind");
			throw new MinimumBalanceException("Minimum Balance 1000 should be maintaind");
		}
		if (status == false) {
			return new ResponseEntity<>("Transaction Failed", HttpStatus.NOT_IMPLEMENTED);
		}
		//Updating the source account
		Account updatedSourceAccBal = accountServiceImpl.updateBalance(transInput.getSourceAccount());
		List<Transaction> sourceAcc = transactionFeign.getTransactionsByAccId(token,transInput.getSourceAccount().getAccountId());
		updatedSourceAccBal.setTransactions(sourceAcc);
		
		//Updating the target account
		Account updatedTargetAccBal = accountServiceImpl.updateDepositBalance(transInput.getTargetAccount());
		List<Transaction> targetAcc = transactionFeign.getTransactionsByAccId(token,transInput.getTargetAccount().getAccountId());
		updatedTargetAccBal.setTransactions(targetAcc);
		
		//Updating the account statement
		accountServiceImpl.updateStatement(updatedSourceAccBal,updatedTargetAccBal,transInput.getAmount(),"Transferred");
		LOGGER.info("Transaction completed successfully from Account " + transInput.getSourceAccount().getAccountId()+ " to Target Account " + transInput.getTargetAccount().getAccountId());
		messageDetails.setMessage("Transaction Successfully Done..");
		return new ResponseEntity<>(messageDetails,HttpStatus.OK);
	}

	/*
	 * Checking the current balance of the specified account
	 */
	@PostMapping("/checkBalance")
	public ResponseEntity<Account> checkAccountBalance(@RequestHeader("Authorization") String token,@Valid @RequestBody AccountInput accountInput) {
		accountServiceImpl.hasPermission(token);
		Account account = accountServiceImpl.getAccount(accountInput.getAccountId());
		return new ResponseEntity<>(account, HttpStatus.OK);
	}
	
	/*
	 * Getting all the existing accounts irrespective of customers
	 */
	@GetMapping("/find")
	public ResponseEntity<List<Account>> getAllAccount(@RequestHeader("Authorization") String token) {
		accountServiceImpl.hasPermission(token);
		List<Account> account = accountServiceImpl.getAllAccounts();
		return new ResponseEntity<>(account, HttpStatus.OK);
	}
	
	/*
	 * Deleting the given account from the database
	 */
	@DeleteMapping("deleteCustomer/{id}")
	@ResponseStatus(code = HttpStatus.OK)
	public ResponseEntity<?> deleteCustomer(@RequestHeader("Authorization") String token, @PathVariable String id) {

		System.out.println("Starting deletion of account " + id);
		accountServiceImpl.deleteCustomer(id);
		System.out.println("Deleted");
		return new ResponseEntity<>("Account Deleted successfully", HttpStatus.OK);
	}
	
	/*
	 * Getting account statement of an account for the past one month 
	 */
	@GetMapping("/getAccountStatement/{accountId}")
	public ResponseEntity<List<Statement>> getAccountStatement(@RequestHeader("Authorization") String token,@PathVariable long accountId) {
		accountServiceImpl.hasPermission(token);
		List<Statement> statements = accountServiceImpl.getAccountStatement(accountId);
		LOGGER.info("Account Statement Returned Successfully");
		return new ResponseEntity<>(statements, HttpStatus.OK);
	}
		
	/*
	 * Getting account statement of an account between the given dates
	 */
	@GetMapping("/getAccountStatement/{accountId}/{from}/{to}")
	public ResponseEntity<List<Statement>> getAccountStatement(@RequestHeader("Authorization") String token,@PathVariable long accountId,@PathVariable String from, @PathVariable String to) throws ParseException {
		accountServiceImpl.hasPermission(token);
		List<Statement> statements = accountServiceImpl.getAccountStatement(accountId,from,to);
		LOGGER.info("Account Statement from "+from+" to "+to+" Returned Successfully");
		return new ResponseEntity<>(statements, HttpStatus.OK);
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/controller/AccountController.java:AccountController.<init>
// Node: CrossOrigin
// Node: GetMapping
// Node: getAccount
// Node: RequestHeader
// Node: hasPermission
// Node: PostMapping
// Node: createAccount
// Node: hasEmployeePermission
// Node: error
// Node: getCustomerAccount
// Node: deposit
// Node: makeDeposit
// Node: updateDepositBalance
// Node: getTransactionsByAccId
// Node: setTransactions
// Node: updateStatement
// Node: withdraw
// Node: makeWithdraw
// Node: updateBalance
// Node: servicecharge
// Node: makeServiceCharges
// Node: transaction
// Node: makeTransfer
// Node: checkAccountBalance
// Node: getAllAccount
// Node: getAllAccounts
// Node: DeleteMapping
// Node: ResponseStatus
// Node: deleteCustomer
// Node: getAccountStatement
// Node: findByCustomerId
// Node: now
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

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/service/AccountServiceImpl.java:AccountServiceImpl.<init>
// Node: save
// Node: findAll
// Node: deleteById
package com.cognizant.accountservice.service;

import java.text.ParseException;
import java.util.List;

import com.cognizant.accountservice.model.Account;
import com.cognizant.accountservice.model.AccountCreationStatus;
import com.cognizant.accountservice.model.AccountInput;
import com.cognizant.accountservice.model.AuthenticationResponse;
import com.cognizant.accountservice.model.Statement;

public interface AccountService {

	public AccountCreationStatus createAccount(String customerId, Account account);

	public List<Account> getCustomerAccount(String token, String customerId);

	public Account getAccount(long accountId);

	public AuthenticationResponse hasPermission(String token);

	public AuthenticationResponse hasEmployeePermission(String token);

	public AuthenticationResponse hasCustomerPermission(String token);

	public Account updateDepositBalance(AccountInput accountInput);

	public Account updateBalance(AccountInput accountInput);

	public List<Account> getAllAccounts();

	List<Statement> getAccountStatement(long accountId);

	List<Statement> getAccountStatement(long accountId, String from, String to) throws ParseException;

	void updateStatement(Account updatedSourceAccBal, Account updatedTargetAccBal, double amount, String message);

	void updateStatement(AccountInput accInput, Account newUpdateAccBal, String message);

	void deleteCustomer(String id);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/service/AccountService.java:AccountService.<init>
package com.cognizant.accountservice.feignclient;

import java.util.List;

import javax.validation.Valid;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;

import com.cognizant.accountservice.model.Account;
import com.cognizant.accountservice.model.AccountInput;
import com.cognizant.accountservice.model.Transaction;
import com.cognizant.accountservice.model.TransactionInput;

@FeignClient(name = "transaction-ms", url = "${accountms.feign.url.transactionservice}")
public interface TransactionFeign {

	@PostMapping("/deposit")
	public ResponseEntity<?> makeDeposit(@RequestHeader("Authorization") String token,
			@Valid @RequestBody AccountInput accountInput);

	@PostMapping("/withdraw")
	public boolean makeWithdraw(@RequestHeader("Authorization") String token,
			@Valid @RequestBody AccountInput accountInput);

	@PostMapping(value = "/accounts", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
	public Account checkAccountBalance(@Valid @RequestBody AccountInput accountInput);

	@PostMapping(value = "/transactions")
	public boolean makeTransfer(@RequestHeader("Authorization") String token,
			@Valid @RequestBody TransactionInput transactionInput);

	@GetMapping(value = "/getAllTransByAccId/{id}")
	public List<Transaction> getTransactionsByAccId(@RequestHeader("Authorization") String token,
			@PathVariable("id") long accId);

	@PostMapping(value = "/servicecharge")
	public boolean makeServiceCharges(@RequestHeader("Authorization") String token,
			@Valid @RequestBody AccountInput accountInput);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/feignclient/TransactionFeign.java:TransactionFeign.<init>
// Node: FeignClient
// Node: PathVariable
package com.cognizant.accountservice.feignclient;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;

import com.cognizant.accountservice.model.AuthenticationResponse;


@FeignClient(name = "auth-ms", url = "${accountms.feign.url.auththenticationms}")
public interface AuthFeignClient {


	@GetMapping("/validateToken")
	public AuthenticationResponse tokenValidation(@RequestHeader("Authorization") String token);

	@GetMapping("/role/{id}")
	public String getRole(@PathVariable("id") String id);

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/feignclient/AuthFeignClient.java:AuthFeignClient.<init>
package com.cognizant.accountservice.feignclient;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import com.cognizant.accountservice.model.CustomerEntity;

@FeignClient(name = "customer", url = "${accountms.feign.url.customerms}")
public interface CustomerFeignProxy {

	@GetMapping("/getCustomerDetails/{id}")
	public CustomerEntity getCustomerDetails(@PathVariable(name = "id") String id);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/feignclient/CustomerFeignProxy.java:CustomerFeignProxy.<init>
// Node: getCustomerDetails
// Node: Transaction
// Node: setSourceAccountId
// Node: setSourceOwnerName
// Node: setTargetAccountId
// Node: setTargetOwnerName
// Node: setInitiationDate
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


// Node: getAccountTestExceptionMessage
// Node: add
// Node: size
// Node: AccountInput
package com.cognizant.service;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.accountservice.model.AccountInput;
import com.cognizant.accountservice.model.TransactionInput;

class TransactionInputTest {

	TransactionInput input = new TransactionInput();
	
	AccountInput accIp = new AccountInput(1, 2000);
	AccountInput accIp2 = new AccountInput(1, 2000);
	TransactionInput input1 = new TransactionInput(accIp,accIp2,3000,"withdraw");
	@Test
	void setSourceAccountTest() {
		input.setSourceAccount(accIp);
		assertEquals(2000, input.getSourceAccount().getAmount());
	}

	@Test
	void setTargetAccountTest() {
		input.setTargetAccount(accIp);
		assertEquals(1, input.getTargetAccount().getAccountId());
	}

	@Test
	void setAmountTest() {
		input.setAmount(1000);
		assertEquals(1000, input.getAmount());
	}

	@Test
	void setReferenceTest() {
		input.setReference("Withdraw");
		assertEquals("Withdraw", input.getReference());
	}
	
	
	@Test
	void setSourceAccountTest1() {
		assertEquals(2000, input1.getSourceAccount().getAmount());
	}

	@Test
	void setTargetAccountTest1() {
		input.setTargetAccount(accIp);
		assertEquals(1, input1.getTargetAccount().getAccountId());
	}

	@Test
	void setAmountTest1() {
		assertEquals(3000, input1.getAmount());
	}

	@Test
	void setReferenceTest1() {
		assertEquals("withdraw", input1.getReference());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/service/TransactionInputTest.java:TransactionInputTest.<init>
// Node: TransactionInput
// Node: get
package com.cognizant.authenticationservice.controller;

import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.cognizant.authenticationservice.exceptionhandling.AppUserNotFoundException;
import com.cognizant.authenticationservice.model.AppUser;
import com.cognizant.authenticationservice.model.AuthenticationResponse;
import com.cognizant.authenticationservice.repository.UserRepository;
import com.cognizant.authenticationservice.service.CustomerDetailsService;
import com.cognizant.authenticationservice.service.LoginService;
import com.cognizant.authenticationservice.service.Validationservice;

import lombok.extern.slf4j.Slf4j;

/**
 * The AuthController class for request controller
 *
 */
@Slf4j
@RestController
@CrossOrigin()
public class AuthController {

	// Users Repository
	@Autowired
	private UserRepository userRepository;

	// Service class login
	@Autowired
	private LoginService loginService;

	// Service class for login
	@Autowired
	private Validationservice validationService;

	@Autowired
	private CustomerDetailsService customerService;

	/**
	 * The health method to check app
	 *
	 */
	@GetMapping("/health")
	public ResponseEntity<String> healthCheckup() {
		log.info("Health Check for Authentication Microservice");
		log.info("health checkup ----->{}", "up");
		return new ResponseEntity<>("UP", HttpStatus.OK);
	}

	/**
	 * The login method with post request
	 *
	 */

	@PostMapping("/login")
	public ResponseEntity<AppUser> login(@RequestBody AppUser appUserloginCredentials)
			throws UsernameNotFoundException, AppUserNotFoundException {
		AppUser user = loginService.userLogin(appUserloginCredentials);
		log.info("Credentials ----->{}", user);
		return new ResponseEntity<>(user, HttpStatus.ACCEPTED);
	}

	/**
	 * The token validation method
	 *
	 */
	@GetMapping("/validateToken")
	public AuthenticationResponse getValidity(@RequestHeader("Authorization") final String token) {
		log.info("Token Validation ----->{}", token);
		return validationService.validate(token);
	}

	/**
	 * The user is created with login credentials
	 *
	 */
	@PostMapping("/createUser")
	public ResponseEntity<?> createUser(@RequestBody AppUser appUserCredentials) {
		AppUser createduser = null;
		try {
			createduser = userRepository.save(appUserCredentials);
		} catch (Exception e) {
			return new ResponseEntity<String>("Not created", HttpStatus.NOT_ACCEPTABLE);
		}
		log.info("user creation---->{}", createduser);
		return new ResponseEntity<>(createduser, HttpStatus.CREATED);

	}

	/**
	 * The find users method to find all users
	 *
	 */
	@PreAuthorize("hasRole('ROLE_EMPLOYEE')")
	@GetMapping("/find")
	public ResponseEntity<List<AppUser>> findUsers(@RequestHeader("Authorization") final String token) {
		List<AppUser> createduser = new ArrayList<>();
		List<AppUser> findAll = userRepository.findAll();
		findAll.forEach(emp -> createduser.add(emp));
		System.out.println(createduser);
		log.info("All Users  ----->{}", findAll);
		return new ResponseEntity<>(createduser, HttpStatus.CREATED);

	}

	@GetMapping("/role/{id}")
	public String getRole(@PathVariable("id") String id) {
		return userRepository.findById(id).get().getRole();
	}

	@DeleteMapping("deleteCustomer/{id}")
	@ResponseStatus(code = HttpStatus.OK)
	public ResponseEntity<?> deleteCustomer(@RequestHeader("Authorization") String token, @PathVariable String id) {

		System.out.println("Starting deletion of-->" + id);
		customerService.deleteCustomer(id);
		System.out.println("Deleted");
		return new ResponseEntity<>("Deleted SUCCESSFULLY", HttpStatus.OK);
	}

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/main/java/com/cognizant/authenticationservice/controller/AuthController.java:for.<init>
// Node: healthCheckup
// Node: login
// Node: userLogin
// Node: validate
// Node: createUser
// Node: PreAuthorize
// Node: findUsers
// Node: forEach
// Node: findById
package com.cognizant.authenticationservice.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Component;

import com.cognizant.authenticationservice.exceptionhandling.AppUserNotFoundException;
import com.cognizant.authenticationservice.model.AppUser;
import com.cognizant.authenticationservice.repository.UserRepository;

import lombok.extern.slf4j.Slf4j;


@Component
@Slf4j
public class LoginService {

	@Autowired
	private JwtUtil jwtutil;
	@Autowired
	private BCryptPasswordEncoder encoder;
	
	@Autowired
	private CustomerDetailsService customerDetailservice;

	@Autowired
	private UserRepository userRepo;
	
	public AppUser userLogin(AppUser appuser) throws AppUserNotFoundException {
		final UserDetails userdetails = customerDetailservice.loadUserByUsername(appuser.getUserid());
		String userid = "";
		String role="";
		String token = "";
		
		AppUser user = null;
		user = userRepo.findById(appuser.getUserid()).orElse(null); //.get()
		
		log.info("Password From DB-->{}" ,userdetails.getPassword());
		log.info("Password From Request-->{}", encoder.encode(appuser.getPassword()) );
		
		

		if (userdetails.getPassword().equals(appuser.getPassword()) && appuser.getRole().equals(user.getRole()) ) {
			userid = appuser.getUserid();
			token = jwtutil.generateToken(userdetails);
			role = appuser.getRole();
			return new AppUser(userid, null, null, token,role);
		} else {
			throw new AppUserNotFoundException("Username/Password is incorrect...Please check");
		}
	}
}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/main/java/com/cognizant/authenticationservice/service/LoginService.java:LoginService.<init>
// Node: loadUserByUsername
// Node: orElse
// Node: encode
package com.cognizant.authenticationservice.service;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.cognizant.authenticationservice.model.AppUser;
import com.cognizant.authenticationservice.repository.UserRepository;

@Service
public class CustomerDetailsService implements UserDetailsService {

	// Class to Implement UserDetailsService in Spring security

	@Autowired
	private UserRepository userRepo;

	@Override
	public UserDetails loadUserByUsername(String userid) throws UsernameNotFoundException {

		AppUser user = null;
		user = userRepo.findById(userid).orElse(null); //.get()

		if (user != null) {
			List<GrantedAuthority> grantedAuthorities = AuthorityUtils
					.commaSeparatedStringToAuthorityList("ROLE_" + user.getRole());
			return new User(user.getUserid(), user.getPassword(), grantedAuthorities);
		} else {
			throw new UsernameNotFoundException("Username/Password is Invalid...Please Check");
		}
	}

	public void deleteCustomer(String id) {
		// TODO Auto-generated method stub
		userRepo.deleteById(id);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/main/java/com/cognizant/authenticationservice/service/CustomerDetailsService.java:CustomerDetailsService.<init>
// Node: commaSeparatedStringToAuthorityList
// Node: User
package com.cognizant.authenticationservice.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import com.cognizant.authenticationservice.model.AuthenticationResponse;
import com.cognizant.authenticationservice.repository.UserRepository;

@Component
public class Validationservice {

	@Autowired
	private JwtUtil jwtutil;
	@Autowired
	private UserRepository userRepo;

	public AuthenticationResponse validate(String token) {
		AuthenticationResponse authenticationResponse = new AuthenticationResponse();
		String jwt = token;
		
		if (jwtutil.validateToken(jwt)) {
			authenticationResponse.setUserid(jwtutil.extractUsername(jwt));
			authenticationResponse.setValid(true);
			authenticationResponse.setName(userRepo.findById(jwtutil.extractUsername(jwt)).get().getUsername());
		} else {
			authenticationResponse.setValid(false);
		}
		return authenticationResponse;
	}
}

// Node: getBody
package com.rulesservice.feign;

import java.util.List;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;

import com.rulesservice.model.Account;
import com.rulesservice.model.AccountInput;

@FeignClient(name = "account-ms", url = "${feign.url-account-service}")
public interface AccountFeign {

	@PostMapping("/servicecharge")
	public ResponseEntity<Account> servicecharge(@RequestHeader("Authorization") String token,
			@RequestBody AccountInput accInput);

	@GetMapping("/find")
	public ResponseEntity<List<Account>> getAllacc(@RequestHeader("Authorization") String token);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/feign/AccountFeign.java:AccountFeign.<init>
// Node: getAllacc
package com.rulesservice.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import com.rulesservice.model.AppUser;
import com.rulesservice.model.AuthenticationResponse;

@FeignClient(name = "auth-service", url = "${feign.url-auth-service}")
@Component
public interface AuthorizationFeign {

	@PostMapping(value = "/createUser")
	public ResponseEntity<?> createUser(@RequestBody AppUser appUserCredentials);

	@PostMapping(value = "/login")
	public ResponseEntity<?> login(@RequestBody AppUser appUserloginCredentials) throws Exception;

	@GetMapping(value = "/validateToken")
	public AuthenticationResponse getValidity(@RequestHeader("Authorization") String token);

	@GetMapping("/role/{id}")
	public String getRole(@PathVariable("id") String id);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/feign/AuthorizationFeign.java:AuthorizationFeign.<init>
package com.rulesservice.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import com.rulesservice.exception.MinimumBalanceException;
import com.rulesservice.feign.AccountFeign;
import com.rulesservice.model.Account;
import com.rulesservice.model.AccountInput;
import com.rulesservice.model.RulesInput;
import com.rulesservice.service.RulesService;

@RestController
@CrossOrigin()
public class RulesController {

	private static final String INVALID = "Send Valid Details.";
	@Autowired
	public RulesService rulesService;
	@Autowired
	AccountFeign accountFeign;

	@PostMapping("/evaluateMinBal")
	public ResponseEntity<?> evaluate(@RequestBody RulesInput account) throws MinimumBalanceException {
		if (account.getCurrentBalance() == 0) {
			throw new MinimumBalanceException(INVALID);
		} else {
			boolean status = rulesService.evaluate(account);

			return new ResponseEntity<Boolean>(status, HttpStatus.OK);
		}
	}

	@PostMapping("/serviceCharges")
	public ResponseEntity<?> serviceCharges(@RequestHeader("Authorization") String token) {
		rulesService.hasPermission(token);
		try {
			List<Account> body = accountFeign.getAllacc(token).getBody();
			for (Account acc : body) {
				if (rulesService.serviceCharges(acc) > 0) {
					accountFeign.servicecharge(token,
							new AccountInput(acc.getAccountId(), rulesService.serviceCharges(acc)));
				}
			}
		} catch (Exception e) {
			System.out.println(e);
		}

		return ResponseEntity.ok(accountFeign.getAllacc(token).getBody());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/controller/RulesController.java:RulesController.<init>
// Node: evaluate
// Node: serviceCharges
// Node: ok
package com.rulesservice.service;

import com.rulesservice.model.Account;
import com.rulesservice.model.AuthenticationResponse;
import com.rulesservice.model.RulesInput;

public interface RulesService {

	public boolean evaluate(RulesInput account);

	public AuthenticationResponse hasPermission(String token);

	public double serviceCharges(Account account);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/service/RulesService.java:RulesService.<init>
// Node: RulesInput
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


// Node: EvaluateTest
// Node: RulesServiceImpl
// Node: EvaluateTest2
// Node: EvaluateTest3
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/model/RulesInputTest.java:RulesInputTest.<init>
package com.rulesservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class AccountInputTest {

	AccountInput accInp = new AccountInput();
	AccountInput accInp2 = new AccountInput(1, 1000);

	@Test
	void setAccountIdTest() {
		accInp.setAccountId(1);
		assertEquals(1, accInp.getAccountId());
	}

	@Test
	void setAmountTest() {
		accInp.setAmount(500);
		assertEquals(500, accInp.getAmount());
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/model/AccountInputTest.java:AccountInputTest.<init>
package com.cognizant.customerservice.feign;

import java.util.List;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;

import com.cognizant.customerservice.model.Account;
import com.cognizant.customerservice.model.AccountCreationStatus;

@FeignClient(name = "account-ms", url = "${feign.url-account-service}")
public interface AccountFeign {

	@PostMapping("/createAccount/{customerId}")
	public AccountCreationStatus createAccount(@RequestHeader("Authorization") String token,
			@PathVariable String customerId, @RequestBody Account account);

	@GetMapping("/getAccounts/{customerId}")
	public List<Account> getCustomerAccount(@RequestHeader("Authorization") String token,
			@PathVariable String customerId);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/feign/AccountFeign.java:AccountFeign.<init>
package com.cognizant.customerservice.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;

import com.cognizant.customerservice.model.AppUser;
import com.cognizant.customerservice.model.AuthenticationResponse;

@FeignClient(name = "auth-service", url = "${feign.url-auth-service}")
@Component
public interface AuthorizationFeign {

	@PostMapping(value = "/createUser")
	public ResponseEntity<?> createUser(@RequestBody AppUser appUserCredentials);

	@PostMapping(value = "/login")
	public ResponseEntity<?> login(@RequestBody AppUser appUserloginCredentials);

	@GetMapping(value = "/validateToken")
	public AuthenticationResponse getValidity(@RequestHeader("Authorization") String token);

	@GetMapping("/role/{id}")
	public String getRole(@PathVariable("id") String id);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/feign/AuthorizationFeign.java:AuthorizationFeign.<init>
package com.cognizant.customerservice.controller;

import java.net.BindException;
import java.time.DateTimeException;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import com.cognizant.customerservice.feign.AuthorizationFeign;
import com.cognizant.customerservice.model.CustomerEntity;
import com.cognizant.customerservice.model.MessageDetails;
import com.cognizant.customerservice.service.CustomerService;

@RestController
@CrossOrigin()
public class CustomerController {

	@Autowired
	private CustomerService customerService;
	
	@Autowired
	private MessageDetails messageDetails;
	
	@Autowired
	AuthorizationFeign authorizationFeign;

	/*
	 * Creating a new customer and storing but first checking error on BindingResult
	 */
	@PostMapping("/createCustomer")
	public ResponseEntity<?> createCustomer(@RequestHeader("Authorization") String token,
			@Valid @RequestBody CustomerEntity customer, BindingResult bindingResult)
			throws DateTimeException, BindException {
		if (bindingResult.hasErrors()) {
			throw new BindException();
		}
		customerService.hasEmployeePermission(token);
		CustomerEntity customerEntity = customerService.createCustomer(token, customer);
		if (customerEntity != null)
			return new ResponseEntity<>(customerEntity, HttpStatus.CREATED);
		else
			return new ResponseEntity<>("Customer Creation is UNSUCCESSFUL", HttpStatus.NOT_ACCEPTABLE);
	}

	/*
	 * Creating a new customer and storing without checking error on BindingResult
	 */
	@PostMapping("/saveCustomer")
	public CustomerEntity saveCustomer(@RequestHeader("Authorization") String token,
			@Valid @RequestBody CustomerEntity customer) {
		customerService.hasEmployeePermission(token);
		CustomerEntity customerEntity = customerService.saveCustomer(token, customer);
		if (customerEntity != null)
			return customerEntity;
		else
			return null;
	}

	/*
	 * Updating existing customer details
	 */
	@PostMapping("/updateCustomer")
	public CustomerEntity updateCustomer(@RequestHeader("Authorization") String token,
			@Valid @RequestBody CustomerEntity customer) {
		customerService.hasEmployeePermission(token);
		return customerService.updateCustomer(token, customer);
	}

	/*
	 * Getting customer details by given customer id
	 */
	@GetMapping("/getCustomerDetails/{id}")
	public ResponseEntity<?> getCustomerDetails(@RequestHeader("Authorization") String token, @PathVariable String id) {
		customerService.hasPermission(token);
		CustomerEntity toReturnCustomerDetails = customerService.getCustomerDetail(token, id);
		if (toReturnCustomerDetails == null)
			return new ResponseEntity<>("Customer Userid " + id + " DOES NOT EXISTS", HttpStatus.NOT_ACCEPTABLE);
		toReturnCustomerDetails.setPassword(null);
		return new ResponseEntity<>(toReturnCustomerDetails, HttpStatus.OK);
	}
	
	/*
	 * Deleting customer details with given customer id
	 */	
	@DeleteMapping("/deleteCustomer/{id}")
	public ResponseEntity<?> deleteCustomer(@RequestHeader("Authorization") String token, @PathVariable String id) {
		customerService.hasPermission(token);
		CustomerEntity toReturnCustomerDetails = customerService.getCustomerDetail(token, id);
		if (toReturnCustomerDetails == null)
			return new ResponseEntity<>("Customer Userid " + id + " DOES NOT EXISTS", HttpStatus.NOT_ACCEPTABLE);
		toReturnCustomerDetails.setPassword(null);
		boolean deleteCustomer = customerService.deleteCustomer(id);
		if(deleteCustomer) {
			
			messageDetails.setMessage("CUSTOMER DELETED");
			return new ResponseEntity<>(messageDetails, HttpStatus.OK);			
		}
		return new ResponseEntity<>("Customer Userid " + id + " DOES NOT EXISTS", HttpStatus.NOT_ACCEPTABLE);
	}

	/*
	 * Checking Token is valid or not
	 */	
	@GetMapping("/check")
	public String checkAccessWWithoutValidation(@RequestHeader("Authorization") String token) {
		customerService.hasEmployeePermission(token);
		return "Your Token is valid";
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/controller/CustomerController.java:CustomerController.<init>
// Node: createCustomer
// Node: hasErrors
// Node: BindException
// Node: saveCustomer
// Node: updateCustomer
// Node: getCustomerDetail
// Node: checkAccessWWithoutValidation
package com.cognizant.customerservice.service;

import com.cognizant.customerservice.model.AuthenticationResponse;
import com.cognizant.customerservice.model.CustomerEntity;

public interface CustomerService {

	public CustomerEntity createCustomer(String token, CustomerEntity customer);

	public CustomerEntity getCustomerDetail(String token, String id);
	
	public CustomerEntity saveCustomer(String token, CustomerEntity customer);

	public CustomerEntity updateCustomer(String token, CustomerEntity customer);

	public AuthenticationResponse hasEmployeePermission(String token);

	public boolean deleteCustomer(String id);

	public AuthenticationResponse hasCustomerPermission(String token);

	public AuthenticationResponse hasPermission(String token);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/service/CustomerService.java:CustomerService.<init>
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


// Node: getAccounts
// Node: isPresent
// Node: setAccounts
package com.cognizant.CustomerServiceTest.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.Transaction;


class TransactionTest {

	Transaction transaction = new Transaction();
	Transaction transaction2 = new Transaction(1l, 1l, "gayathri", 3l, "prabha", 1000, null, "deposit");

	@Test
	void setIdTest() {
		transaction.setId(1);
		assertEquals(1, transaction.getId());
	}

	@Test
	void setSourceAccountIdTest() {
		transaction.setSourceAccountId(1);
		assertEquals(1, transaction.getSourceAccountId());
	}

	@Test
	void setTargetOwnerNameTest() {
		transaction.setTargetOwnerName("gayathri");
		assertEquals("gayathri", transaction.getTargetOwnerName());
	}

	@Test
	void setTargetAccountIdTest() {
		transaction.setTargetAccountId(1);
		;
		assertEquals(1, transaction.getTargetAccountId());
	}

	@Test
	void setAmountTest() {
		transaction.setAmount(1000);
		assertEquals(1000, transaction.getAmount());
	}

	@Test
	void setReferenceTest() {
		transaction.setReference("Deposit");
		assertEquals("Deposit", transaction.getReference());
	}

	@Test
	void setInitiationDateTest() {
		transaction.setInitiationDate(null);
		assertEquals(null, transaction.getInitiationDate());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerServiceTest/model/TransactionTest.java:TransactionTest.<init>
package com.cognizant.transactionservice.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;

import com.cognizant.transactionservice.models.Account;

@FeignClient(name = "account-ms", url = "${feign.url-account-service}")
public interface AccountFeign {

	@GetMapping("/getAccount/{accountId}")
	public Account getAccount(@RequestHeader("Authorization") String token,
			@PathVariable(name = "accountId") long accountId);

	@PostMapping("/updateAccount")
	public boolean updateAccount(Account sourceAccount);

	@GetMapping("/updateAccountById/{id}")
	public boolean updateAccountById(@PathVariable("id") long accId, double currentBalance);

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/feign/AccountFeign.java:AccountFeign.<init>
// Node: updateAccount
// Node: updateAccountById
package com.cognizant.transactionservice.feign;

import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;

import com.cognizant.transactionservice.exception.MinimumBalanceException;
import com.cognizant.transactionservice.models.RulesInput;


@FeignClient(name = "rules-ms", url = "${feign.url-rule-service}")
public interface RulesFeign {
	
	
	@PostMapping("/evaluateMinBal")
	public ResponseEntity<?> evaluate(@RequestBody RulesInput account)throws MinimumBalanceException ;
	
	
	@PostMapping("/serviceCharges")
	public ResponseEntity<?> serviceCharges(@RequestHeader("Authorization") String token,@RequestBody RulesInput account);
	

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/feign/RulesFeign.java:RulesFeign.<init>
package com.cognizant.transactionservice.controller;

import java.util.List;

import javax.validation.Valid;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RestController;

import com.cognizant.transactionservice.feign.AccountFeign;
import com.cognizant.transactionservice.feign.RulesFeign;
import com.cognizant.transactionservice.models.AccountInput1;
import com.cognizant.transactionservice.models.Transaction;
import com.cognizant.transactionservice.models.TransactionInput;
import com.cognizant.transactionservice.repository.TransactionRepository;
import com.cognizant.transactionservice.service.TransactionServiceInterface;

import lombok.extern.slf4j.Slf4j;

@RestController
@Slf4j
@CrossOrigin()
public class TransactionRestController {


	
	@Autowired
	AccountFeign accountFeign;

	@Autowired
	RulesFeign rulesFeign;

	@Autowired
	TransactionRepository transRepo;

	@Autowired
	TransactionServiceInterface transactionService;

	@PostMapping(value = "/transactions")
	public boolean makeTransfer(@RequestHeader("Authorization") String token,
			@Valid @RequestBody TransactionInput transactionInput) {
		log.info("inside transaction method");
		if (transactionInput != null) {
			boolean isComplete = transactionService.makeTransfer(token, transactionInput);

			return isComplete;
		} else {
			return false;
		}
	}
     

	@GetMapping(value = "/getAllTransByAccId/{id}")
	public List<Transaction> getTransactionsByAccId(@RequestHeader("Authorization") String token,
			@PathVariable("id") long accId) {
		List<Transaction> slist = transRepo.findBySourceAccountIdOrTargetAccountIdOrderByInitiationDate(accId, accId);
		return slist;
	}

	@PostMapping(value = "/withdraw")
	public boolean makeWithdraw(@RequestHeader("Authorization") String token,
			@Valid @RequestBody AccountInput1 accountInput1) {
		transactionService.makeWithdraw(token, accountInput1);
		return true;
	}

	@PostMapping(value = "/servicecharge")
	public boolean makeServiceCharges(@RequestHeader("Authorization") String token,
			@Valid @RequestBody AccountInput1 accountInput1) {
		transactionService.makeServiceCharges(token, accountInput1);
		return true;
	}
	


	@PostMapping(value = "/deposit")
	public ResponseEntity<?> makeDeposit(@RequestHeader("Authorization") String token,
			@Valid @RequestBody AccountInput1 accountInput1) {
		transactionService.makeDeposit(token, accountInput1);
		return new ResponseEntity<>(true, HttpStatus.OK);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/controller/TransactionRestController.java:TransactionRestController.<init>
// Node: findBySourceAccountIdOrTargetAccountIdOrderByInitiationDate
package com.cognizant.transactionservice.repository;

import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.cognizant.transactionservice.models.Transaction;

public interface TransactionRepository extends JpaRepository<Transaction, Long> {

	List<Transaction> findBySourceAccountIdOrTargetAccountIdOrderByInitiationDate(long id, long id2);

	List<Transaction> findByTargetAccountIdOrderByInitiationDate(long accId);

	List<Transaction> findBySourceAccountIdOrderByInitiationDate(int i);
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/repository/TransactionRepository.java:TransactionRepository.<init>
// Node: findByTargetAccountIdOrderByInitiationDate
// Node: findBySourceAccountIdOrderByInitiationDate
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/service/TransactionService.java:TransactionService.<init>
// Node: booleanValue
package com.cognizant.transactionservice.service;

import com.cognizant.transactionservice.models.AccountInput1;
import com.cognizant.transactionservice.models.TransactionInput;

public interface TransactionServiceInterface {

	public boolean makeTransfer(String token, TransactionInput transactionInput);

	public boolean makeWithdraw(String token, AccountInput1 accountInput1);

	public boolean makeDeposit(String token, AccountInput1 accountInput1);

	public boolean makeServiceCharges(String token, AccountInput1 accountInput1);
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/service/TransactionServiceInterface.java:TransactionServiceInterface.<init>
package com.cognizant.transactionservice.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.AccountInput1;

class AccountInputTest {

	AccountInput1 accInp = new AccountInput1();
	AccountInput1 accInp1 = new AccountInput1(1, 100);

	@Test
	void setAccountIdTest() {
		accInp.setAccountId(1);
		assertEquals(1, accInp.getAccountId());
	}

	@Test
	void setAmountTest() {
		accInp.setAmount(500);
		assertEquals(500, accInp.getAmount());
	}

	@Test
	void testMakeTransfer() {
		assertTrue(true);
	}
	@Test
	void getAccountIdTest() {
		accInp.setAccountId(1);
		assertTrue(accInp.getAccountId() == 1);
	}

	@Test
	void getAmountTest() {
		accInp.setAmount(500);
		assertTrue(accInp.getAmount() == 500);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/AccountInputTest.java:AccountInputTest.<init>
// Node: AccountInput1
package com.cognizant.transactionservice.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.AccountInput;


class AccountInput2Test {

	AccountInput accInp = new AccountInput();
	AccountInput accInp1 = new AccountInput(1, 100, 1000);

	@Test
	void setAccountIdTest() {
		accInp.setAccountId(1);
		assertEquals(1, accInp.getAccountId());
	}

	@Test
	void setAmountTest() {
		accInp.setAmount(500);
		assertEquals(500, accInp.getAmount());
	}

	@Test
	void setCurrtentBalTest() {
		accInp.setCurrentBalance(100);
		assertEquals(100, accInp.getCurrentBalance());
	}

	@Test
	void getAccountIdTest() {
		accInp.setAccountId(1);
		assertTrue(accInp.getAccountId() == 1);
	}

	@Test
	void getAmountTest() {
		accInp.setAmount(500);
		assertTrue(accInp.getAmount() == 500);
	}

	@Test
	void getCurrtentBalTest() {
		accInp.setCurrentBalance(500);
		assertTrue(accInp.getCurrentBalance() == 500);
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/AccountInput2Test.java:AccountInput2Test.<init>
package com.cognizant.transactionservice.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.Transaction;


class TransactionTest {

	Transaction transaction = new Transaction();
	Transaction transaction2 = new Transaction(1l, 1l, "Aman A", 3l, "Pratik A", 1000, null, "deposit");

	@Test
	void setIdTest() {
		transaction.setId(1);
		assertEquals(1, transaction.getId());
	}

	@Test
	void setSourceAccountIdTest() {
		transaction.setSourceAccountId(1);
		assertEquals(1, transaction.getSourceAccountId());
	}

	@Test
	void setTargetOwnerNameTest() {
		transaction.setTargetOwnerName("Aman A");
		assertEquals("Aman A", transaction.getTargetOwnerName());
	}

	@Test
	void setTargetAccountIdTest() {
		transaction.setTargetAccountId(1);
		;
		assertEquals(1, transaction.getTargetAccountId());
	}

	@Test
	void setAmountTest() {
		transaction.setAmount(1000);
		assertEquals(1000, transaction.getAmount());
	}

	@Test
	void setReferenceTest() {
		transaction.setReference("Deposit");
		assertEquals("Deposit", transaction.getReference());
	}

	@Test
	void setInitiationDateTest() {
		transaction.setInitiationDate(null);
		assertEquals(null, transaction.getInitiationDate());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/TransactionTest.java:TransactionTest.<init>
package com.cognizant.transactionservice.model;

import static org.junit.Assert.assertEquals;
import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.RulesInput;

class RulesTest {

	RulesInput accInp = new RulesInput();
	RulesInput rul = new RulesInput(1, 100, 10);

	@Test
	void setAccountIdTest() {
		accInp.setAccountId(1);
		assertEquals(1, accInp.getAccountId());
	}

	@Test
	void setAmountTest() {
		accInp.setAmount(500);
		assertEquals(500, accInp.getAmount(), 0.0);
	}

	@Test
	void setCurrBalanceTest() {
		accInp.setCurrentBalance(500);
		assertEquals(500, accInp.getCurrentBalance(), 0.0);
	}

	@Test
	void getAccountIdTest() {
		accInp.setAccountId(1);
		assertTrue(accInp.getAccountId() == 1);
	}

	@Test
	void getCurrBalanceTest() {
		accInp.setCurrentBalance(500);
		assertTrue(accInp.getCurrentBalance() == 500);
	}

	@Test
	void getAmountTest() {
		accInp.setAmount(500);
		assertTrue(accInp.getAmount() == 500);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/RulesTest.java:RulesTest.<init>
package com.cognizant.transactionservice.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.AccountInput1;
import com.cognizant.transactionservice.models.TransactionInput;

class TransactionInputTest {

TransactionInput input = new TransactionInput();
	
	AccountInput1 accIp = new AccountInput1(1, 2000);
	AccountInput1 accIp2 = new AccountInput1(1, 2000);
	TransactionInput input1 = new TransactionInput(accIp,accIp2,3000,"withdraw");
	@Test
	void setSourceAccountTest() {
		input.setSourceAccount(accIp);
		assertEquals(2000, input.getSourceAccount().getAmount());
	}

	@Test
	void setTargetAccountTest() {
		input.setTargetAccount(accIp);
		assertEquals(1, input.getTargetAccount().getAccountId());
	}

	@Test
	void setAmountTest() {
		input.setAmount(1000);
		assertEquals(1000, input.getAmount());
	}

	@Test
	void setReferenceTest() {
		input.setReference("Withdraw");
		assertEquals("Withdraw", input.getReference());
	}
	
	
	@Test
	void setSourceAccountTest1() {
		assertEquals(2000, input1.getSourceAccount().getAmount());
	}

	@Test
	void setTargetAccountTest1() {
		input.setTargetAccount(accIp);
		assertEquals(1, input1.getTargetAccount().getAccountId());
	}

	@Test
	void setAmountTest1() {
		assertEquals(3000, input1.getAmount());
	}

	@Test
	void setReferenceTest1() {
		assertEquals("withdraw", input1.getReference());
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/TransactionInputTest.java:TransactionInputTest.<init>
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/controller/AuthController.class:AuthController
// Node: LoginService
// Node: Validationservice
// Node: src.main.java.com.retailbank.AuthenticationMS.controller.AuthController
// Node: ResponseEntity
// Node: RequestBody
// Node: Slf4j
// Node: RestController
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/feign/RulesFeign.class:RulesFeign
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/feign/AccountFeign.class:AccountFeign
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/controller/TransactionRestController.class:TransactionRestController
// Node: AccountFeign
// Node: RulesFeign
// Node: TransactionRepository
// Node: TransactionService
// Node: src.main.java.com.cognizant.transactionservice.controller.TransactionRestController
// Node: Valid
// Node: MethodArgumentNotValidException
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/controller/AccountRestController.class:AccountRestController
// Node: src.main.java.com.cognizant.transactionservice.controller.AccountRestController
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/service/TransactionService.class:TransactionService
// Node: src.main.java.com.cognizant.transactionservice.service.TransactionService
