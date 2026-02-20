// Cluster 16

// Node: Statement
package com.cognizant.accountservice.model;

import java.util.Date;

import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.SequenceGenerator;
import javax.persistence.Table;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "STATEMENT")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Statement {
	@Id
	@SequenceGenerator(name="stat_id", initialValue = 150001)
	@GeneratedValue(strategy = GenerationType.SEQUENCE, generator="stat_id")
	private long transactionId;
	private long sourceId;
	private long targetId;
	private double amount;
	private double sourceBalance;
	private double targetBalance;
	private Date date;
	private String reference;
	public Statement(long sourceId, long targetId, double amount, double sourceBalance, double targetBalance,Date date,
			String reference) {
		super();
		this.sourceId = sourceId;
		this.targetId = targetId;
		this.amount = amount;
		this.sourceBalance = sourceBalance;
		this.targetBalance = targetBalance;
		this.date=date;
		this.reference = reference;
	}
	
	
	

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/model/Statement.java:Statement.<init>
// Node: Table
// Node: SequenceGenerator
// Node: GeneratedValue
package com.cognizant.accountservice.model;

import javax.validation.constraints.Min;
import javax.validation.constraints.Positive;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class TransactionInput {
	
	private AccountInput sourceAccount;
	private AccountInput targetAccount;
	@Positive(message = "Transfer amount must be positive")
	@Min(value = 1, message = "Amount must be larger than 1")
	private double amount;
	private String reference;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/model/TransactionInput.java:TransactionInput.<init>
// Node: Positive
// Node: Min
package com.cognizant.accountservice.model;

import javax.validation.constraints.NotNull;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@NoArgsConstructor
@AllArgsConstructor
public class AccountInput {
	
	
	@Getter
	@Setter
	@NotNull(message = "Account number is mandatory")
	private long accountId;
	@Getter
	@Setter
	@NotNull(message = "Amount is mandatory")
	private double amount;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/model/AccountInput.java:AccountInput.<init>
// Node: NotNull
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

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Account-MS/src/main/java/com/cognizant/accountservice/model/Account.java:Account.<init>
// Node: Column
// Node: NotBlank
package com.cognizant.authenticationservice.model;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;

import com.sun.istack.NotNull;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Entity
@Table(name = "appuser")
public class AppUser {
	
	@Id
	@Column(name = "userid", length = 20)
	@NotNull
	private String userid;
	
	@Column(name = "username", length = 20)
	private String username;
	
	@Column(name = "password")
	private String password;
	
	private String authToken;
	
	private String role;
}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/src/main/java/com/cognizant/authenticationservice/model/AppUser.java:AppUser.<init>
package com.rulesservice.model;

import javax.validation.constraints.NotNull;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class AccountInput {
	
	
	@NotNull(message = "Account number is mandatory")
	private long accountId;
	@NotNull(message = "Amount is mandatory")
	private double amount;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/model/AccountInput.java:AccountInput.<init>
package com.rulesservice.model;

import java.util.Date;
import java.util.List;
import javax.persistence.Column;
import javax.persistence.Id;
import javax.persistence.Transient;
import javax.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@NoArgsConstructor
@AllArgsConstructor
@Getter
@Setter
public class Account {

	@Id
	@NotNull(message = "Enter Account number")
	private long accountId;

	@NotNull(message = "Enter customerId")
	private String customerId;

	@NotNull(message = "Enter currentBalance")
	private double currentBalance;

	@NotNull(message = "Enter accountType")
	private String accountType;

	@NotNull(message = "Enter opening Date")
	private Date openingDate;

	@Column(length = 20)
	@NotNull(message = "Enter ownerName")
	private String ownerName;

	@Transient
	private List<Transaction> transactions;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/model/Account.java:Account.<init>
package com.rulesservice.model;

import javax.persistence.Column;
import javax.persistence.Id;
import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor


public class AppUser {
	
	@Id
	@Column(name = "userid", length = 20)
	private String userid;
	
	@Column(name = "username", length = 20)
	private String username;
	
	@Column(name = "password")
	private String password;
	
	private String authToken;
	
	private String role;
}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Rules-MS/src/main/java/com/rulesservice/model/AppUser.java:AppUser.<init>
package com.cognizant.customerservice.model;

import java.sql.Date;
import java.util.ArrayList;
import java.util.List;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.Table;
import javax.persistence.Transient;
import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;

import com.fasterxml.jackson.annotation.JsonFormat;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Entity
@Table
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class CustomerEntity {
	@Id
	@Column(name = "userid", length = 15, unique = true)
	@Pattern(regexp = "^[A-Za-z0-9_-]*$")
	private String userid;

	@Column(name = "username", length = 20)
	@NotBlank
	private String username;

	@Column(name = "password")
	@NotBlank
	private String password;

	@Column(name = "dateOfBirth")
	@JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd")
	private Date dateOfBirth;

	@Pattern(regexp = "^[A-Z]{5}+[0-9]{4}+[A-Z]{1}$")
	@Column(name = "pan", length = 10)
	@NotBlank
	private String pan;

	@Column(name = "address")
	@NotBlank
	private String address;

	@Transient
	private List<Account> accounts = new ArrayList<>();

}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/model/CustomerEntity.java:CustomerEntity.<init>
// Node: Pattern
// Node: JsonFormat
package com.cognizant.customerservice.model;

import java.time.LocalDateTime;

import javax.persistence.Table;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Table(name = "TRANSACTION")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class Transaction {

	private long id;

	private long sourceAccountId;

	private String sourceOwnerName;

	private long targetAccountId;

	private String targetOwnerName;

	private double amount;

	private LocalDateTime initiationDate;

	private String reference;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/model/Transaction.java:Transaction.<init>
package com.cognizant.customerservice.model;

import javax.persistence.Column;
import javax.validation.constraints.Pattern;
import javax.persistence.Id;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class AppUser {

	@Id
	@Pattern(regexp = "^[A-Za-z0-9]*$")
	@Column(name = "userid", length = 20)
	private String userid;

	@Pattern(regexp = "^[A-Za-z0-9]*$")
	@Column(name = "username", length = 20)
	private String username;

	@Column(name = "password")
	private String password;

	private String authToken;

	private String role;
}


// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Customer-MS/src/main/java/com/cognizant/customerservice/model/AppUser.java:AppUser.<init>
package com.cognizant.transactionservice.models;

import javax.validation.constraints.NotNull;

import lombok.AllArgsConstructor;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Setter
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class AccountInput1 {

	@NotNull(message = "Account number is mandatory")
	private long accountId;
	@NotNull(message = "Amount is mandatory")
	private double amount;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/models/AccountInput1.java:AccountInput1.<init>
package com.cognizant.transactionservice.models;

import javax.validation.constraints.Min;
import javax.validation.constraints.Positive;

import lombok.AllArgsConstructor;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Setter
@Getter
@AllArgsConstructor
@NoArgsConstructor
public class TransactionInput {

	private AccountInput1 sourceAccount;

	private AccountInput1 targetAccount;

	@Positive(message = "Transfer amount must be greater than 100")
	@Min(value = 1, message = "Amount must be larger than 100")
	private double amount;

	private String reference;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/models/TransactionInput.java:TransactionInput.<init>
package com.cognizant.transactionservice.models;

import javax.persistence.*;

import lombok.AllArgsConstructor;
import lombok.NoArgsConstructor;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Entity
@Table(name = "TRANSACTION")
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class Transaction {

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private long id;

	private long sourceAccountId;

	private String sourceOwnerName;

	private long targetAccountId;

	private String targetOwnerName;

	private double amount;

	private LocalDateTime initiationDate;

	private String reference;

}

// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/src/main/java/com/cognizant/transactionservice/models/Transaction.java:Transaction.<init>
// Node: java.lang.Override
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/model/AppUser.class:AppUser
// Node: Id
// Node: java.lang.SuppressWarnings
// Node: src.main.java.com.retailbank.AuthenticationMS.model.AppUser
// Node: Data
// Node: AllArgsConstructor
// Node: NoArgsConstructor
// Node: Entity
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/model/AuthenticationResponse.class:AuthenticationResponse
// Node: Lsrc.main.java.com.retailbank.AuthenticationMS.model.AuthenticationResponse
// Node: Getter
// Node: Setter
// Node: ToString
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Authentication-MS/bin/src/main/java/com/retailbank/AuthenticationMS/model/errorhandling/ErrorMessage.class:ErrorMessage
// Node: HttpStatus
// Node: LocalDateTime
// Node: src.main.java.com.retailbank.AuthenticationMS.model.errorhandling.ErrorMessage
// Node: List
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/repository/TransactionRepository.class:TransactionRepository
// Node: Long
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/util/TransactionInput.class:TransactionInput
// Node: src.main.java.com.cognizant.transactionservice.util.AccountInput
// Node: src.main.java.com.cognizant.transactionservice.util.TransactionInput
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/util/AccountInput.class:AccountInput
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/models/ErrorDetails.class:ErrorDetails
// Node: src.main.java.com.cognizant.transactionservice.models.ErrorDetails
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/models/Transaction.class:Transaction
// Node: src.main.java.com.cognizant.transactionservice.models.Transaction
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/models/AccountInput.class:AccountInput
// Node: src.main.java.com.cognizant.transactionservice.models.AccountInput
// Node: repos/cloned_ms_repos/Retail-Banking-System/Backend/Transaction-MS/bin/src/main/java/com/cognizant/transactionservice/models/Account.class:Account
// Node: Transient
// Node: src.main.java.com.cognizant.transactionservice.models.Account
