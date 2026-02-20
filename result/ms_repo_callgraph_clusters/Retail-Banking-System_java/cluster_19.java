// Cluster 19

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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/test/java/com/cognizant/service/TransactionTest.java:TransactionTest.<init>
// Node: setTransactionIdTest
// Node: setId
// Node: getId
// Node: setTransactionNameTest
// Node: getSourceAccountId
// Node: SetTransactionOwnerTest
// Node: getSourceOwnerName
// Node: setTransactionTargetAccIdTest
// Node: getTargetAccountId
// Node: setTransactionTOwnerTest
// Node: getTargetOwnerName
// Node: SetAmount
// Node: SetDateTest
// Node: getInitiationDate
// Node: setIdTest1
// Node: setSourceAccountIdTest1
// Node: setTargetOwnerNameTest1
// Node: setTargetAccountIdTest1
// Node: setInitiationDateTest1
// Node: setSourceOwnerTest1
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


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/test/java/com/rulesservice/model/TransactionTest.java:TransactionTest.<init>
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


// Node: setIdTest
// Node: setSourceAccountIdTest
// Node: setTargetOwnerNameTest
// Node: setTargetAccountIdTest
// Node: setInitiationDateTest
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


