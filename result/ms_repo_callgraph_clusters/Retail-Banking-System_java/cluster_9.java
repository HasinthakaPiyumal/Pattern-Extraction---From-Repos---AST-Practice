// Cluster 9

package com.cognizant.accountservice.exceptionhandling;

import java.time.LocalDateTime;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import com.cognizant.accountservice.model.AccountErrorResponse;

@RestControllerAdvice
public class ControllerExceptionHandler {

	@ExceptionHandler(MinimumBalanceException.class)
	public ResponseEntity<AccountErrorResponse> minimumBalanceException(MinimumBalanceException exception,
			WebRequest request) {
		AccountErrorResponse response = new AccountErrorResponse(LocalDateTime.now(), HttpStatus.NOT_ACCEPTABLE,
				exception.getMessage(), "Minimum Balance Problem");
		return new ResponseEntity<>(response, HttpStatus.NOT_ACCEPTABLE);
	}

	@ExceptionHandler(AccountNotFoundException.class)
	public ResponseEntity<AccountErrorResponse> accountNotFoundException(AccountNotFoundException exception,
			WebRequest request) {
		AccountErrorResponse response = new AccountErrorResponse(LocalDateTime.now(), HttpStatus.NOT_ACCEPTABLE,
				exception.getMessage(), "Account not found");
		return new ResponseEntity<>(response, HttpStatus.NOT_ACCEPTABLE);
	}

	@ExceptionHandler(AccessDeniedException.class)
	public ResponseEntity<AccountErrorResponse> accessDeniedException(AccessDeniedException exception,
			WebRequest request) {
		AccountErrorResponse response = new AccountErrorResponse(LocalDateTime.now(), HttpStatus.NOT_ACCEPTABLE,
				exception.getMessage(), "Access Denied");
		return new ResponseEntity<>(response, HttpStatus.NOT_ACCEPTABLE);
	}

	@ExceptionHandler(Exception.class)
	public ResponseEntity<AccountErrorResponse> globalException(Exception exception, WebRequest request) {
		AccountErrorResponse response = new AccountErrorResponse(LocalDateTime.now(), HttpStatus.NOT_ACCEPTABLE,
				exception.getMessage(), "Error occurred");
		return new ResponseEntity<>(response, HttpStatus.NOT_ACCEPTABLE);
	}

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/exceptionhandling/ControllerExceptionHandler.java:ControllerExceptionHandler.<init>
// Node: ExceptionHandler
// Node: minimumBalanceException
// Node: AccountErrorResponse
// Node: accountNotFoundException
// Node: accessDeniedException
// Node: globalException
package com.cognizant.authenticationservice.exceptionhandling;

import java.time.LocalDateTime;

import org.springframework.http.HttpStatus;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import com.cognizant.authenticationservice.errorhandling.ErrorMessage;

import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.SignatureException;

@RestControllerAdvice
public class ControllerAdvice 
{
	//Exception Method for APPUSER not found
	@ExceptionHandler(UsernameNotFoundException.class)
	@ResponseStatus(HttpStatus.NOT_FOUND)
	public ErrorMessage userNotFoundException(UsernameNotFoundException userNotFoundException) 
	{
		return new ErrorMessage(HttpStatus.NOT_FOUND,LocalDateTime.now(),userNotFoundException.getMessage());
	}
	
	
	//Exception for jwt malfunctioned error
	@ExceptionHandler(MalformedJwtException.class)
	@ResponseStatus(HttpStatus.UNAUTHORIZED)
	public ErrorMessage tokenMalformedException() 
	{
		return new ErrorMessage(HttpStatus.UNAUTHORIZED,LocalDateTime.now(),"Not Authorized --> Token is Invalid..");
	}

	
	// Exception for JWT Signature unauthorized error
	@ExceptionHandler(SignatureException.class)
	@ResponseStatus(HttpStatus.UNAUTHORIZED)
	public ErrorMessage tokenSignatureException() 
	{
		return new ErrorMessage(HttpStatus.UNAUTHORIZED,LocalDateTime.now(),"Not Authorized --> Token is Invalid..");
	}


}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/main/java/com/cognizant/authenticationservice/exceptionhandling/ControllerAdvice.java:ControllerAdvice.<init>
// Node: userNotFoundException
// Node: ErrorMessage
// Node: tokenMalformedException
// Node: tokenSignatureException
// Node: UsernameNotFoundException
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/test/java/com/cognizant/authenticationservice/model/ErrorMessageTest.java:ErrorMessageTest.<init>
package com.rulesservice.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import com.rulesservice.model.ErrorDetails;

@RestControllerAdvice
public class GlobalExceptionHandler {

	@ExceptionHandler(MinimumBalanceException.class)
	public ResponseEntity<?> minBalance(MinimumBalanceException exception, WebRequest request) {
		ErrorDetails errorDetails = new ErrorDetails(exception.getMessage(), request.getDescription(false));
		return new ResponseEntity<>(errorDetails, HttpStatus.BAD_REQUEST);
	}

	@ExceptionHandler(AccessDeniedException.class)
	public ResponseEntity<?> AccessDenied(AccessDeniedException exception, WebRequest request) {
		ErrorDetails errorDetails = new ErrorDetails(exception.getMessage(), request.getDescription(false));
		return new ResponseEntity<>(errorDetails, HttpStatus.CONFLICT);
	}

	@ExceptionHandler(Exception.class)
	public ResponseEntity<?> globalExceptionHandling(Exception exception, WebRequest request) {
		ErrorDetails errorDetails = new ErrorDetails(exception.getMessage(), request.getDescription(false));
		return new ResponseEntity<>(errorDetails, HttpStatus.INTERNAL_SERVER_ERROR);
	}

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/exception/GlobalExceptionHandler.java:GlobalExceptionHandler.<init>
// Node: ErrorDetails
// Node: getDescription
// Node: AccessDenied
// Node: globalExceptionHandling
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/model/ErrorDetailsTest.java:ErrorDetailsTest.<init>
package com.cognizant.transactionservice.exception;

import java.time.LocalDateTime;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;

import com.cognizant.transactionservice.models.TransactionErrorResponse;

@RestControllerAdvice
public class GlobalExceptionHandler {

	@ExceptionHandler(MinimumBalanceException.class)
	public ResponseEntity<TransactionErrorResponse> nullPointer(MinimumBalanceException exception, WebRequest request) {
		TransactionErrorResponse response = new TransactionErrorResponse(LocalDateTime.now(), HttpStatus.NOT_ACCEPTABLE,
				exception.getMessage(), "Access Denied");
		return new ResponseEntity<>(response, HttpStatus.NOT_ACCEPTABLE);
	}

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/exception/GlobalExceptionHandler.java:GlobalExceptionHandler.<init>
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/ErrorTest.java:ErrorTest.<init>
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/exceptionHandling/ControllerAdvice.class:ControllerAdvice
// Node: src.main.java.com.retailbank.AuthenticationMS.exceptionHandling.ControllerAdvice
// Node: RestControllerAdvice
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/exception/GlobalExceptionHandler.class:GlobalExceptionHandler
// Node: src.main.java.com.cognizant.transactionservice.exception.GlobalExceptionHandler
// Node: src.main.java.com.cognizant.transactionservice.exception.MinimumBalanceException
// Node: WebRequest
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/exception/MinimumBalanceException.class:MinimumBalanceException
