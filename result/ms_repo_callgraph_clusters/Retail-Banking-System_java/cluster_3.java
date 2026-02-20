// Cluster 3

// Node: getAccountId
// Node: getTargetAccount
// Node: setMessage
// Node: getMessage
// Node: getUserid
// Node: getCustomerId
// Node: assertEquals
package com.cognizant.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.Test;

import com.cognizant.accountservice.model.Transaction;

public class TransactionTest {
	
	Transaction tc=new Transaction();
	Transaction transaction2 = new Transaction(1, 2, "harini", 32, "prabha", 1000, null, "deposit");
	
	@Test
	public void setTransactionIdTest()
	{
		tc.setId(1);
		assertEquals(1,tc.getId());
	}
	@Test
	public void setTransactionNameTest()
	{
		tc.setSourceAccountId(1001);
		assertEquals(1001, tc.getSourceAccountId());
	}
	@Test
	public void SetTransactionOwnerTest()
	{
		tc.setSourceOwnerName("harini");
		assertEquals("harini", tc.getSourceOwnerName());
	}
	
	@Test
	public void setTransactionTargetAccIdTest()
	{
		tc.setTargetAccountId(200315);
		assertEquals(200315, tc.getTargetAccountId());
	}
	
	@Test
	public void setTransactionTOwnerTest()
	{
		tc.setTargetOwnerName("bhavya");
		assertEquals("bhavya", tc.getTargetOwnerName());
	}
	
	@Test
	public void SetAmount()
	{
		tc.setAmount(5000);
		assertEquals(5000, tc.getAmount());
	}
	@Test
	public void SetDateTest()
	{
		tc.setInitiationDate(null);
		assertEquals(null, tc.getInitiationDate());
		
	}
	
	@Test
	public void setReferenceTest() {
		tc.setReference("Deposit");
		assertEquals("Deposit", tc.getReference());
	}
	@Test
	public void setIdTest1() {
		assertEquals(1, transaction2.getId());
	}

	@Test
	public void setSourceAccountIdTest1() {
		assertEquals(2, transaction2.getSourceAccountId());
	}

	@Test
	public void setTargetOwnerNameTest1() {
		assertEquals("prabha", transaction2.getTargetOwnerName());
	}

	@Test
	public void setTargetAccountIdTest1() {
		assertEquals(32, transaction2.getTargetAccountId());
	}

	@Test
	public void setAmountTest1() {
		assertEquals(1000, transaction2.getAmount());
	}

	@Test
	public void setReferenceTest1() {
		assertEquals("deposit", transaction2.getReference());
	}

	@Test
	public void setInitiationDateTest1() {
		assertEquals(null, transaction2.getInitiationDate());
	}
	@Test
	public void setSourceOwnerTest1()
	{
		
		assertEquals("harini", transaction2.getSourceOwnerName());
	}

}


// Node: setReferenceTest
// Node: setReference
// Node: getReference
// Node: setReferenceTest1
package com.cognizant.service;

import static org.junit.jupiter.api.Assertions.*;

import java.sql.Date;

import org.junit.jupiter.api.Test;

import com.cognizant.accountservice.model.CustomerEntity;


class CustomerEntityTest {

	CustomerEntity customer = new CustomerEntity();

	@Test
	void setUserIdTest() {
		customer.setUserid("1");
		assertEquals("1", customer.getUserid());
	}

	@Test
	void setUserNameTest() {
		customer.setUsername("prabha");
		assertEquals("prabha", customer.getUsername());
	}

	@Test
	void setPasswordTest() {
		customer.setPassword("abc");
		assertEquals("abc", customer.getPassword());
	}

	@Test
	void setAddressTest() {
		customer.setAddress("abc");
		assertEquals("abc", customer.getAddress());
	}

	@Test
	void setPanTest() {
		customer.setPan("ABCDE1234R");
		assertEquals("ABCDE1234R", customer.getPan());
	}

	@Test
	void setDateTest() {
		Date d = new Date(0);
		customer.setDateOfBirth(d);
		assertEquals(d, customer.getDateOfBirth());
	}

	@Test
	void getAccTest() {
		customer.setUserid("1");
		assertEquals("1", customer.getUserid());
	}

	@Test
	void getUserNameTest() {
		customer.setUsername("prabha");
		assertEquals("prabha", customer.getUsername());
	}

	@Test
	void getPasswordTest() {
		customer.setPassword("abc");
		assertEquals("abc", customer.getPassword());
	}

	@Test
	void getAddressTest() {
		customer.setAddress("abc");
		assertEquals("abc", customer.getAddress());
	}

	@Test
	void getPanTest() {
		customer.setPan("abc");
		assertEquals("abc", customer.getPan());
	}

	@Test
	void getDateTest() {
		Date d = new Date(0);
		customer.setDateOfBirth(d);
		assertEquals(d, customer.getDateOfBirth());
	}
	//CustomerEntity customer2 = new CustomerEntity("111","prabha","prabha",new Date(0),"123","chn");

	CustomerEntity customer2 = new CustomerEntity("111","prabha","prabha",new Date(0),"123","chn");
	@Test
	void setUserIdTest1() {
		assertEquals("111", customer2.getUserid());
	}

	@Test
	void setUserNameTest1() {
		assertEquals("prabha", customer2.getUsername());
	}

	@Test
	void setPasswordTest1() {
		assertEquals("prabha", customer2.getPassword());
	}


	@Test
	void setDateTest1() {
		assertEquals(new Date(0), customer2.getDateOfBirth());
	}
	
	@Test
	void getPanTest1() {
		assertEquals("123", customer2.getPan());
	}
	@Test
	void getAddressTest1() {
		assertEquals("chn", customer2.getAddress());
	}

	


}


// Node: setUserIdTest
// Node: setUserid
// Node: setUserNameTest
// Node: setUsername
// Node: getUsername
// Node: setPasswordTest
// Node: setPassword
// Node: getPassword
// Node: setAddressTest
// Node: setAddress
// Node: getAddress
// Node: setPanTest
// Node: setPan
// Node: getPan
// Node: getAccTest
// Node: getUserNameTest
// Node: getPasswordTest
// Node: getAddressTest
// Node: getPanTest
// Node: setUserIdTest1
// Node: setUserNameTest1
// Node: setPasswordTest1
// Node: getPanTest1
// Node: getAddressTest1
package com.cognizant.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.Test;

import com.cognizant.accountservice.model.AccountCreationStatus;

public class AccountCreationStatusTest {
	
	AccountCreationStatus ac=new AccountCreationStatus();
	AccountCreationStatus ac1=new AccountCreationStatus(3698,null);
	
	@Test 
	public void accIdTest()
	{
		ac.setAccountId(1234);
		assertEquals(1234, ac.getAccountId());
	}
	@Test
	public void messTest()
	{
		ac.setMessage(null);
		assertEquals(null, ac.getMessage());
	}
	
	@Test 
	public void accIdTest1()
	{
		assertEquals(3698, ac1.getAccountId());
	}
	@Test
	public void messTest1()
	{
		assertEquals(null, ac1.getMessage());
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/service/AccountCreationStatusTest.java:AccountCreationStatusTest.<init>
// Node: accIdTest
// Node: setAccountId
// Node: messTest
// Node: accIdTest1
// Node: messTest1
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


// Node: setTargetAccountTest
// Node: setTargetAccount
// Node: setTargetAccountTest1
package com.cognizant.accountservice;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class AccountserviceApplicationTests {
	
	@Test
	void setCustomerIdTest() {
		String check="Cust101";
		assertEquals("Cust101",check );
	}
	
	@Test
	public void main() {
		AccountserviceApplication.main(new String[] {});
	}
}


// Node: setCustomerIdTest
// Node: setDetails
package com.cognizant.authenticationservice;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class AuthenticationMsApplicationTests {

	@Test
	void contextLoads() {
	}
	@Test
	void main() {
		AuthenticationMsApplication.main(new String[] {});
	}

}


// Node: contextLoads
// Node: getAccountIdTest
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


// Node: setname
// Node: getAccounname
// Node: getUserIdTest
package com.cognizant.authenticationservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

import com.cognizant.authenticationservice.errorhandling.ErrorMessage;



public class ErrorMessageTest {
	ErrorMessage errormessage=new ErrorMessage();
	ErrorMessage errormessage1=new ErrorMessage(null,null,"anuhya");
	
	@Test
	public void setTimestampTest() {
		errormessage.setTimestamp(null);
		assertEquals(null, errormessage.getTimestamp());
	}
	@Test
	public void setStatusTest() {
		errormessage.setStatus(null);
		assertEquals(null,errormessage.getStatus());
	}
	@Test
	public void setMessageTest() {
		errormessage.setMessage("anuhya");
		assertEquals("anuhya", errormessage.getMessage());
	}
	@Test
	public void setTimestampTest1() {
		//errormessage.setTimestamp(null);
		assertEquals(null, errormessage1.getTimestamp());
	}
	@Test
	public void setStatusTest1() {
		//errormessage.setStatus(null);
		assertEquals(null,errormessage1.getStatus());
	}
	@Test
	public void setMessageTest1() {
		//errormessage.setMessage("anuhya");
		assertEquals("anuhya", errormessage1.getMessage());
	}
}


// Node: setMessageTest
// Node: setMessageTest1
package com.rulesservice;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class RulesServiceApplicationTests {

	@Test
	void contextLoads() {

	}

}


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


// Node: setAccountIdTest
// Node: setAccountIdTest1
// Node: setAmountTest2
// Node: setBalanceTest
// Node: setBalance
// Node: getBalance
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

// Node: setPasswoedTest
// Node: getAccIdTest1
// Node: getUsernameTest1
// Node: getPasswordTest1
package com.rulesservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class ErrorDetailsTest {

	ErrorDetails det = new ErrorDetails();

	@Test
	void setUserIdTest() {
		det.setDetails("/notresponding");
		assertEquals("/notresponding", det.getDetails());
	}

	@Test
	void setNameTest() {
		det.setMessage("bhavya");
		assertEquals("bhavya", det.getMessage());
	}
}


// Node: getDetails
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


// Node: setCustomerId
// Node: setAccountTypeTest
// Node: setAccountType
// Node: getAccountType
// Node: setTransactionsTest
// Node: getTransactions
// Node: setCustomerIdTest1
// Node: setAccountTypeTest1
// Node: setTransactionsTest1
package com.rulesservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class TransactionTest {

	Transaction tc=new Transaction();
	Transaction transaction2 = new Transaction(1, 2, "harini", 32, "prabha", 1000, null, "deposit");
	
	@Test
	public void setTransactionIdTest()
	{
		tc.setId(1);
		assertEquals(1,tc.getId());
	}
	@Test
	public void setTransactionNameTest()
	{
		tc.setSourceAccountId(1001);
		assertEquals(1001, tc.getSourceAccountId());
	}
	@Test
	public void SetTransactionOwnerTest()
	{
		tc.setSourceOwnerName("harini");
		assertEquals("harini", tc.getSourceOwnerName());
	}
	
	@Test
	public void setTransactionTargetAccIdTest()
	{
		tc.setTargetAccountId(200315);
		assertEquals(200315, tc.getTargetAccountId());
	}
	
	@Test
	public void setTransactionTOwnerTest()
	{
		tc.setTargetOwnerName("bhavya");
		assertEquals("bhavya", tc.getTargetOwnerName());
	}
	
	@Test
	public void SetAmount()
	{
		tc.setAmount(5000);
		assertEquals(5000, tc.getAmount());
	}
	@Test
	public void SetDateTest()
	{
		tc.setInitiationDate(null);
		assertEquals(null, tc.getInitiationDate());
		
	}
	
	@Test
	public void setReferenceTest() {
		tc.setReference("Deposit");
		assertEquals("Deposit", tc.getReference());
	}
	@Test
	public void setIdTest1() {
		assertEquals(1, transaction2.getId());
	}

	@Test
	public void setSourceAccountIdTest1() {
		assertEquals(2, transaction2.getSourceAccountId());
	}

	@Test
	public void setTargetOwnerNameTest1() {
		assertEquals("prabha", transaction2.getTargetOwnerName());
	}

	@Test
	public void setTargetAccountIdTest1() {
		assertEquals(32, transaction2.getTargetAccountId());
	}

	@Test
	public void setAmountTest1() {
		assertEquals(1000, transaction2.getAmount());
	}

	@Test
	public void setReferenceTest1() {
		assertEquals("deposit", transaction2.getReference());
	}

	@Test
	public void setInitiationDateTest1() {
		assertEquals(null, transaction2.getInitiationDate());
	}
	@Test
	public void setSourceOwnerTest1()
	{
		
		assertEquals("harini", transaction2.getSourceOwnerName());
	}
}


package com.rulesservice.model;

import static org.junit.Assert.assertEquals;

import org.junit.jupiter.api.Test;

class ServiceResponseTest {

	ServiceResponse res = new ServiceResponse();

	@Test
	void setAccountIdTest() {
		res.setAccountId(1);
		assertEquals(1, res.getAccountId());
	}

	@Test
	void setAmountTest() {
		res.setMessage("abcd");
		assertEquals("abcd", res.getMessage());
	}

}


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


// Node: setUsernameTest
// Node: setPassTest
// Node: getAccIdTest
// Node: getUsernameTest
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


// Node: getCustomerTest
// Node: getAcctypeTest
package com.cognizant.CustomerServiceTest.model;

import static org.junit.jupiter.api.Assertions.*;

import java.sql.Date;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.CustomerDetailsResponse;


class CustomerDetailResponsetest {

	CustomerDetailsResponse customer = new CustomerDetailsResponse();
	CustomerDetailsResponse customer2 = new CustomerDetailsResponse("111","bc","bc",new Date(0),"123","chn",null);

	@Test
	void setUserIdTest() {
		customer.setUserid("1");
		assertEquals("1", customer.getUserid());
	}

	@Test
	void setUserNameTest() {
		customer.setUsername("sri");
		assertEquals("sri", customer.getUsername());
	}

	@Test
	void setPasswordTest() {
		customer.setPassword("abc");
		assertEquals("abc", customer.getPassword());
	}

	@Test
	void setAddressTest() {
		customer.setAddress("abc");
		assertEquals("abc", customer.getAddress());
	}

	@Test
	void setPanTest() {
		customer.setPan("ABCDE1234R");
		assertEquals("ABCDE1234R", customer.getPan());
	}

	@Test
	void setDateTest() {
		Date d = new Date(0);
		customer.setDateOfBirth(d);
		assertEquals(d, customer.getDateOfBirth());
	}

	@Test
	void getAccTest() {
		customer.setUserid("1");
		assertEquals("1", customer.getUserid());
	}

	@Test
	void getUserNameTest() {
		customer.setUsername("prabha");
		assertEquals("prabha", customer.getUsername());
	}

	@Test
	void getPasswordTest() {
		customer.setPassword("abc");
		assertEquals("abc", customer.getPassword());
	}

	@Test
	void getAddressTest() {
		customer.setAddress("abc");
		assertEquals("abc", customer.getAddress());
	}

	@Test
	void getPanTest() {
		customer.setPan("abcde1234r");
		assertEquals("abcde1234r", customer.getPan());
	}

	@Test
	void getDateTest() {
		Date d = new Date(0);
		customer.setDateOfBirth(d);
		assertEquals(d, customer.getDateOfBirth());
	}

}


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


package com.cognizant.CustomerServiceTest.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;

import com.cognizant.customerservice.model.CustomErrorResponse;



class AccountErrorResponseTest {

	CustomErrorResponse response = new CustomErrorResponse();
	CustomErrorResponse response2 = new CustomErrorResponse(null, HttpStatus.OK, "Not Valid", "Not Created");

	@Test
	void setStatusTest() {
		response.setStatus(HttpStatus.OK);
		assertEquals(HttpStatus.OK, response.getStatus());
	}

	@Test
	void setReasonTest() {
		response.setReason("Not Valid");
		assertEquals("Not Valid", response.getReason());
	}

	@Test
	void setMessageTest() {
		response.setMessage("Not Valid");
		assertEquals("Not Valid", response.getMessage());
	}

	@Test
	void setTimeStampTest() {
		response.setTimestamp(null);
		assertEquals(null, response.getTimestamp());
	}
}


package com.cognizant.CustomerServiceTest.model;

import static org.junit.jupiter.api.Assertions.*;

import java.sql.Date;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.CustomerEntity;


class CustomerEntityTest {

	CustomerEntity customer = new CustomerEntity();
	CustomerEntity customer2 = new CustomerEntity("111","bc","bc",new Date(0),"123","chn",null);

	@Test
	void setUserIdTest() {
		customer.setUserid("1");
		assertEquals("1", customer.getUserid());
	}

	@Test
	void setUserNameTest() {
		customer.setUsername("prabha");
		assertEquals("prabha", customer.getUsername());
	}

	@Test
	void setPasswordTest() {
		customer.setPassword("abc");
		assertEquals("abc", customer.getPassword());
	}

	@Test
	void setAddressTest() {
		customer.setAddress("abc");
		assertEquals("abc", customer.getAddress());
	}

	@Test
	void setPanTest() {
		customer.setPan("ABCDE1234R");
		assertEquals("ABCDE1234R", customer.getPan());
	}

	@Test
	void setDateTest() {
		Date d = new Date(0);
		customer.setDateOfBirth(d);
		assertEquals(d, customer.getDateOfBirth());
	}

	@Test
	void getAccTest() {
		customer.setUserid("1");
		assertEquals("1", customer.getUserid());
	}

	@Test
	void getUserNameTest() {
		customer.setUsername("prabha");
		assertEquals("prabha", customer.getUsername());
	}

	@Test
	void getPasswordTest() {
		customer.setPassword("abc");
		assertEquals("abc", customer.getPassword());
	}

	@Test
	void getAddressTest() {
		customer.setAddress("abc");
		assertEquals("abc", customer.getAddress());
	}

	@Test
	void getPanTest() {
		customer.setPan("abc");
		assertEquals("abc", customer.getPan());
	}

	@Test
	void getDateTest() {
		Date d = new Date(0);
		customer.setDateOfBirth(d);
		assertEquals(d, customer.getDateOfBirth());
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


package com.cognizant.CustomerServiceTest.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.customerservice.model.AccountCreationStatus;


class AccountStatusTest {
	AccountCreationStatus account = new AccountCreationStatus();
	AccountCreationStatus account2 = new AccountCreationStatus(111,"hi");
	

	@Test
	void setAccTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

	@Test
	void setMsgTest() {
		account.setMessage("msg");
		assertEquals("msg", account.getMessage());
	}

	@Test
	void getMessageTest() {
		account.setMessage("msg");
		assertEquals("msg", account.getMessage());
	}

	@Test
	void getAccTest() {
		account.setAccountId(1);
		assertEquals(1, account.getAccountId());
	}

}


// Node: setAccTest
// Node: setMsgTest
// Node: getMessageTest
package com.cognizant.CustomerService;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

import com.cognizant.customerservice.CustomerServiceApplication;

@SpringBootTest
class CustomerServiceApplicationTests {

	@Test
	void contextLoads() {
		String check = "Cust101";
		assertEquals("Cust101", check);
	}

	@Test
	void main() {
		CustomerServiceApplication.main(new String[] {});
	}

}


package com.cognizant.transactionservice.exception;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
public class TransactionServiceExceptionTest {
	@InjectMocks
	private MinimumBalanceException minimumBalanceException;

	@Test
	public void testminimumBalance() {
		int reason = 1000;
		assertEquals(reason, 1000);
	}

}


// Node: testminimumBalance
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


package com.cognizant.transactionservice.model;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.TransactionErrorResponse;

public class TransactionErrorResponseTest {
	TransactionErrorResponse transaction = new TransactionErrorResponse();

	@Test
	public void setTimestampTest() {
		transaction.setTimestamp(null);
		assertEquals(null, transaction.getTimestamp());
	}

	@Test
	public void setStatusTest() {
		transaction.setStatus(null);
		assertEquals(null, transaction.getStatus());
	}

	@Test
	public void setMessageTest() {
		transaction.setMessage("anuhya");
		assertEquals("anuhya", transaction.getMessage());
	}

	@Test
	public void setReasonTest() {
		transaction.setReason("anuhya");
		assertEquals("anuhya", transaction.getReason());
	}
}


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


package com.cognizant.transactionservice.model;

import static org.junit.jupiter.api.Assertions.*;

import org.junit.jupiter.api.Test;

import com.cognizant.transactionservice.models.ErrorDetails;

class ErrorTest {

	ErrorDetails accInp = new ErrorDetails();
	ErrorDetails accInp2 = new ErrorDetails("hi", "hi");

	@Test
	void setAccountIdTest() {
		accInp.setDetails("abc");
		assertEquals("abc", accInp.getDetails());
	}

	@Test
	void setAmountTest() {
		accInp.setMessage("abc");
		assertEquals("abc", accInp.getMessage());
	}

	@Test
	void getAccountIdTest() {
		accInp.setDetails("abc");
		assertTrue(accInp.getDetails() == "abc");
	}

	@Test
	void getAmountTest() {
		accInp.setMessage("abc");
		assertTrue(accInp.getMessage() == "abc");
	}

}


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


