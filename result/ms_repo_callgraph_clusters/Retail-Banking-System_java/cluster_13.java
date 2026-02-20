// Cluster 13

// Node: Date
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/service/CustomerEntityTest.java:CustomerEntityTest.<init>
// Node: CustomerEntity
// Node: setDateTest
// Node: setDateOfBirth
// Node: getDateOfBirth
// Node: getDateTest
// Node: setDateTest1
// Node: Account
// Node: generateToken
package com.cognizant.authenticationservice.service;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;

@Service
public class JwtUtil {

	private String secretkey = "${jwt.secret}";

	public String extractUsername(String token) {
		return extractClaim(token, Claims::getSubject);
	}

	public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
		final Claims claims = extractAllClaims(token);
		return claimsResolver.apply(claims);
	}

	private Claims extractAllClaims(String token) {
		return Jwts.parser().setSigningKey(secretkey).parseClaimsJws(token).getBody();
	}

	public String generateToken(UserDetails userDetails) {
		Map<String, Object> claims = new HashMap<>();
		return createToken(claims, userDetails.getUsername());
	}

	private String createToken(Map<String, Object> claims, String subject) {
		return  Jwts.builder().setClaims(claims).setSubject(subject)
				.setIssuedAt(new Date(System.currentTimeMillis()))
				.setExpiration(new Date(System.currentTimeMillis() + 1000*60*10))
				.signWith(SignatureAlgorithm.HS256, secretkey).compact();
	}
	
	public Boolean validateToken(String token) {
		try {
			Jwts.parser().setSigningKey(secretkey).parseClaimsJws(token).getBody();
			return true;
		}
		catch(Exception e) {
			return false;
		}
	}
}

// Node: createToken
// Node: builder
// Node: setClaims
// Node: setSubject
// Node: setIssuedAt
// Node: currentTimeMillis
// Node: setExpiration
// Node: signWith
// Node: compact
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/model/AccountTest.java:AccountTest.<init>
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerServiceTest/model/AccountTest.java:AccountTest.<init>
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerServiceTest/model/CustomerDetailResponsetest.java:CustomerDetailResponsetest.<init>
// Node: CustomerDetailsResponse
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/test/java/com/cognizant/CustomerServiceTest/model/CustomerEntityTest.java:CustomerEntityTest.<init>
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/AccountTest.java:AccountTest.<init>
