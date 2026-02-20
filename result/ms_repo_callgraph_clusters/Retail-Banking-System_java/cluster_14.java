// Cluster 14

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

// Node: nullPointer
// Node: TransactionErrorResponse
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/test/java/com/cognizant/transactionservice/model/TransactionErrorResponseTest.java:TransactionErrorResponseTest.<init>
