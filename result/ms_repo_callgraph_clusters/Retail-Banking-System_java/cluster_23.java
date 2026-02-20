// Cluster 23

package com.cognizant.service;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.Test;

import com.cognizant.accountservice.model.AccountErrorResponse;

public class AccountErrorTest {
	
	AccountErrorResponse re=new AccountErrorResponse();
	AccountErrorResponse re1=new AccountErrorResponse(null,null,"invalid login","invalid");

	@Test
	public void dateTest()
	{
		re.setTimestamp(null);
		assertEquals(null, re.getTimestamp());
	}
	@Test
	public void statusTest()
	{
		re.setStatus(null);
		assertEquals(null, re.getStatus());
	}
	@Test
	public void reasonTest()
	{
		re.setReason("invalid login");
		assertEquals("invalid login", re.getReason());
	}
	@Test
	public void messageTest()
	{
		re.setMessage("invalid");
		assertEquals("invalid", re.getMessage());
	}
	
	@Test
	public void dateTest1()
	{
		assertEquals(null, re.getTimestamp());
	}
	@Test
	public void statusTest1()
	{

		assertEquals(null, re1.getStatus());
	}
	@Test
	public void reasonTest1()
	{
		assertEquals("invalid login", re1.getReason());
	}
	@Test
	public void messageTest1()
	{

		assertEquals("invalid", re1.getMessage());
	}
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/service/AccountErrorTest.java:AccountErrorTest.<init>
// Node: dateTest
// Node: setTimestamp
// Node: getTimestamp
// Node: statusTest
// Node: setStatus
// Node: getStatus
// Node: reasonTest
// Node: setReason
// Node: getReason
// Node: messageTest
// Node: dateTest1
// Node: statusTest1
// Node: reasonTest1
// Node: messageTest1
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


// Node: setTimestampTest
// Node: setStatusTest
// Node: setTimestampTest1
// Node: setStatusTest1
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


// Node: setReasonTest
// Node: setTimeStampTest
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


