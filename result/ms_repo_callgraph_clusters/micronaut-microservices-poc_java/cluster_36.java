// Cluster 36

// Node: info
package pl.altkom.asc.lab.micronaut.poc.payment.infrastructure.adapters.jobs;

import io.micronaut.context.annotation.Prototype;
import io.micronaut.scheduling.annotation.Scheduled;
import java.time.LocalDate;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import pl.altkom.asc.lab.micronaut.poc.payment.domain.InPaymentRegistrationService;

@Prototype
@Slf4j
@RequiredArgsConstructor
public class BankStatementImportJob {

    private final BankStatementImportJobCfg jobCfg;
    private final InPaymentRegistrationService inPaymentRegistrationService;

    @Scheduled(fixedRate = "8h")
    public void importBankStatement() {
       log.info("Starting bank statement import job");
       inPaymentRegistrationService.registerInPayments(jobCfg.getImportDir(), LocalDate.now());
       
    }
}


// Node: importBankStatement
// Node: registerInPayments
// Node: getImportDir
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVRecord;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.exceptions.BankStatementsFileNotFound;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.exceptions.BankStatementsFileReadingError;

import java.io.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

@Slf4j
class BankStatementFile {

    private final String path;
    private final String fileName;

    BankStatementFile(String path, LocalDate importDate) {
        this.path = path;
        this.fileName = constructFileNameFromDate(importDate);
    }

    boolean exists() {
        return new File(fullPath()).exists();
    }

    List<BankStatement> read() {
        try (Reader reader = new FileReader(fullPath())) {
            List<BankStatement> statements = new ArrayList<>();

            Iterable<CSVRecord> records = CSVFormat
                    .RFC4180
                    .withFirstRecordAsHeader()
                    .parse(reader);
            records.forEach(row -> statements.add(readRow(row)));

            return statements;
        } catch (FileNotFoundException ex) {
            log.error("Bank statement file not found. Looking for  " + path, ex);
            throw new BankStatementsFileNotFound(ex);
        } catch (IOException ex) {
            log.error("Error while processing file " + path, ex);
            throw new BankStatementsFileReadingError(ex);
        }
    }

    void markProcessed() {
        new File(fullPath()).renameTo(new File(processedFullPath()));
    }

    private BankStatement readRow(CSVRecord row) {
        String accountingDate = row.get(2);
        String accountNumber = row.get(3);
        String amountAsString = row.get(4);
        return new BankStatement(accountNumber, amountAsString, accountingDate);
    }

    private String constructFileNameFromDate(LocalDate importDate) {
        return String.format("bankStatements_%d_%d_%d.csv", importDate.getYear(), importDate.getMonthValue(), importDate.getDayOfMonth());
    }

    private String fullPath() {
        return path + File.separator + fileName;
    }

    private String processedFullPath() {
        return path + File.separator + "_processed_" + fileName;
    }

    @Getter
    class BankStatement {
        private final String accountNumber;
        private final BigDecimal amount;
        private final LocalDate accountingDate;

        BankStatement(String accountNumber, String amountAsString, String accountingDateAsIsoDateString) {
            this.accountNumber = accountNumber;
            this.amount = new BigDecimal(amountAsString);
            this.accountingDate = LocalDate.parse(accountingDateAsIsoDateString, DateTimeFormatter.ISO_DATE);
        }
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/BankStatementFile.java:BankStatementFile.<init>
// Node: BankStatementFile
// Node: constructFileNameFromDate
// Node: exists
// Node: File
// Node: fullPath
// Node: read
// Node: try
// Node: FileReader
// Node: withFirstRecordAsHeader
// Node: parse
// Node: readRow
// Node: BankStatementsFileNotFound
// Node: BankStatementsFileReadingError
// Node: markProcessed
// Node: renameTo
// Node: processedFullPath
// Node: BankStatement
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import pl.altkom.asc.lab.micronaut.poc.payment.domain.BankStatementFile.BankStatement;

import java.time.LocalDate;
import java.util.List;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class InPaymentRegistrationService {

    private final PolicyAccountRepository policyAccountRepository;

    @Transactional
    public void registerInPayments(String directory, LocalDate date) {
        BankStatementFile fileToImport = new BankStatementFile(directory, date);

        if (!fileToImport.exists()) {
            return;
        }

        List<BankStatement> bankStatements = fileToImport.read();
        bankStatements.forEach(this::registerInPayment);
        fileToImport.markProcessed();
    }

    private void registerInPayment(BankStatement bankStatement) {
        policyAccountRepository
                .findByPolicyAccountNumber(bankStatement.getAccountNumber())
                .ifPresent(account -> {
                    account.inPayment(bankStatement.getAmount(), bankStatement.getAccountingDate());
                });
    }
}


package pl.altkom.asc.lab.micronaut.poc.payment.init;

import java.util.Arrays;
import java.util.List;
import pl.altkom.asc.lab.micronaut.poc.payment.domain.PolicyAccount;

class DemoAccountsFactory {
    static List<PolicyAccount> demoAccounts() {
        return Arrays.asList(
                new PolicyAccount("POLICY_1", "231232132131"),
                new PolicyAccount("POLICY_2", "389hfswjfrh2032r"),
                new PolicyAccount("POLICY_3", "0rju130fhj20")
        );
    }
}


// Node: demoAccounts
package pl.altkom.asc.lab.micronaut.poc.payment.init;

import pl.altkom.asc.lab.micronaut.poc.payment.domain.PolicyAccount;
import pl.altkom.asc.lab.micronaut.poc.payment.domain.PolicyAccountRepository;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import io.micronaut.context.event.ApplicationEventListener;
import io.micronaut.runtime.server.event.ServerStartupEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Singleton
@Slf4j
@RequiredArgsConstructor
public class DataLoader  implements ApplicationEventListener<ServerStartupEvent> {
    private final PolicyAccountRepository policyAccountDb;

    @Transactional
    @Override
    public void onApplicationEvent(ServerStartupEvent event) {
        DemoAccountsFactory.demoAccounts().forEach(this::addIfNotExists);
        log.info("Demo data added");
    }
    
    private void addIfNotExists(PolicyAccount account) {
        if (!policyAccountDb.findByPolicyAccountNumber(account.getPolicyAccountNumber()).isPresent()) {
            policyAccountDb.save(account);
        }
    }
}


package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import com.google.common.io.Files;

import org.junit.jupiter.api.Test;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.Month;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class InPaymentRegistrationServiceTest {
    @Test
    public void canReadStatementsFile() throws IOException {
        PolicyAccountRepository policyAccountRepository = new MockPolicyAccountRepository();
        InPaymentRegistrationService inPaymentRegistrationService = new InPaymentRegistrationService(policyAccountRepository);
        PolicyAccount account231232132131 = policyAccountRepository.findByPolicyAccountNumber("231232132131").get();
        assertEquals(BigDecimal.ZERO, account231232132131.balanceAt(LocalDate.of(2019,12,31)));
        File testData  = createTestData();
                
        inPaymentRegistrationService.registerInPayments(testData.getParent(), LocalDate.of(2018, Month.AUGUST, 2));
        
        testData.delete();
        assertEquals(new BigDecimal("10.21"), account231232132131.balanceAt(LocalDate.of(2019,12,31)));
    }
    
    private File createTestData() throws IOException {
        File tempDir = Files.createTempDir();
        File testFile = new File(tempDir, "bankStatements_2018_8_2.csv");
        try (FileWriter writer = new FileWriter(testFile)) {
            writer.append("TransactionId,TransactionType,AccountingDate,AccountNumber,Amount\r\n");
            writer.append("1,A,2018-08-01,231232132131,10.21\r\n");
            writer.append("1,A,2018-08-01,0rju130fhj20,99.25\r\n");
            return testFile;
        } 
    }
    
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/InPaymentRegistrationServiceTest.java:InPaymentRegistrationServiceTest.<init>
// Node: canReadStatementsFile
// Node: MockPolicyAccountRepository
// Node: InPaymentRegistrationService
// Node: createTestData
// Node: getParent
// Node: delete
// Node: createTempDir
// Node: FileWriter
// Node: append
package pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.exceptions;

public class BankStatementsFileNotFound extends RuntimeException {
    public BankStatementsFileNotFound(Throwable cause) {
        super(cause);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/service/api/v1/exceptions/BankStatementsFileNotFound.java:BankStatementsFileNotFound.<init>
package pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.exceptions;

public class BankStatementsFileReadingError extends RuntimeException {
    public BankStatementsFileReadingError(Throwable cause) {
        super(cause);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/service/api/v1/exceptions/BankStatementsFileReadingError.java:BankStatementsFileReadingError.<init>
package pl.altkom.asc.lab.micronaut.poc.chat.service.infrastructure.adapters.web;

import io.micronaut.websocket.WebSocketBroadcaster;
import io.micronaut.websocket.WebSocketSession;
import io.micronaut.websocket.annotation.OnClose;
import io.micronaut.websocket.annotation.OnMessage;
import io.micronaut.websocket.annotation.OnOpen;
import io.micronaut.websocket.annotation.ServerWebSocket;
import lombok.extern.slf4j.Slf4j;

import java.util.function.Predicate;

@Slf4j
@ServerWebSocket("/ws/chat/{topic}/{username}")
public class ChatWebSocket {

    private WebSocketBroadcaster broadcaster;

    public ChatWebSocket(WebSocketBroadcaster broadcaster) {
        this.broadcaster = broadcaster;
    }

    @OnOpen
    public void onOpen(String topic, String username, WebSocketSession session) {
        String msg = "[" + username + "] Joined!";
        log.info(msg);
        broadcaster.broadcastSync(formatStartCloseMessages(msg), isValid(topic, session));
    }

    @OnMessage
    public void onMessage(
            String topic,
            String username,
            String message,
            WebSocketSession session) {
        String msg = "[" + username + "] " + message;
        log.info(msg);
        broadcaster.broadcastSync(message, isValid(topic, session));
    }

    @OnClose
    public void onClose(
            String topic,
            String username,
            WebSocketSession session) {
        String msg = "[" + username + "] Disconnected!";
        log.info(msg);
        broadcaster.broadcastSync(formatStartCloseMessages(msg), isValid(topic, session));
    }

    private Predicate<WebSocketSession> isValid(String topic, WebSocketSession session) {
        return s -> s != session && topic.equalsIgnoreCase(s.getUriVariables().get("topic", String.class, null));
    }

    private String formatStartCloseMessages(String msg) {
        return "<p>" + msg + "</p>";
    }
}


// Node: onOpen
// Node: broadcastSync
// Node: formatStartCloseMessages
// Node: onMessage
// Node: onClose
