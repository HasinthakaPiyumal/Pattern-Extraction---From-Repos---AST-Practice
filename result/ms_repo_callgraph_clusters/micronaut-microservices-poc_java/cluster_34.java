// Cluster 34

// Node: getPolicyNumber
// Node: getAccountNumber
package pl.altkom.asc.lab.micronaut.poc.payment.infrastructure.adapters.web;

import pl.altkom.asc.lab.micronaut.poc.payment.domain.PolicyAccountRepository;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountBalanceDto;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountDto;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.exceptions.PolicyAccountNotFound;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.operations.PaymentOperations;

import java.time.LocalDate;
import java.util.Collection;

import io.micronaut.configuration.hystrix.annotation.HystrixCommand;
import io.micronaut.http.annotation.Controller;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import lombok.RequiredArgsConstructor;

@Controller("/payment")
@RequiredArgsConstructor
public class PaymentController implements PaymentOperations {

    private final PolicyAccountRepository policyAccountRepository;

    @Override
    @HystrixCommand
    @ExecuteOn(TaskExecutors.IO)
    public Collection<PolicyAccountDto> accounts() {
        return policyAccountRepository.findAll();
    }

    @Override
    @HystrixCommand
    @ExecuteOn(TaskExecutors.IO)
    public PolicyAccountBalanceDto accountBalance(String accountNumber) {
        return policyAccountRepository.findByPolicyAccountNumber(accountNumber)
                .map(account -> new PolicyAccountBalanceDto(
                        account.getPolicyNumber(),
                        account.getPolicyAccountNumber(),
                        account.balanceAt(LocalDate.now()),
                        account.getCreated(),
                        account.getUpdated()))
                .orElseThrow(() -> new PolicyAccountNotFound(accountNumber));
    }
}


// Node: findByPolicyAccountNumber
// Node: getPolicyAccountNumber
// Node: getCreated
// Node: getUpdated
// Node: PolicyAccountNotFound
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


// Node: registerInPayment
// Node: ifPresent
// Node: getAccountingDate
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


// Node: addIfNotExists
package pl.altkom.asc.lab.micronaut.poc.payment.domain;


import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountDto;

public class MockPolicyAccountRepository implements PolicyAccountRepository {

    private Map<String, PolicyAccount> policyAccountMap = init();

    private LinkedHashMap<String, PolicyAccount> init() {
        LinkedHashMap<String, PolicyAccount> map = new LinkedHashMap<>();

        map.put("PA1", new PolicyAccount("POLICY_1", "231232132131"));
        map.put("PA2", new PolicyAccount("POLICY_2", "389hfswjfrh2032r"));
        map.put("PA3", new PolicyAccount("POLICY_3", "0rju130fhj20"));

        return map;
    }

    @Override
    public Optional<PolicyAccount> findByPolicyNumber(String policyNumber) {
        return Optional.ofNullable(policyAccountMap.get(policyNumber));
    }

    @Override
    public PolicyAccount save(PolicyAccount policyAccount) {
        policyAccountMap.put(policyAccount.getPolicyNumber(), policyAccount);
        return policyAccount;
    }

    @Override
    public Collection<PolicyAccountDto> findAll() {
        return policyAccountMap
                .values()
                .stream()
                .map(this::mapToDto)
                .collect(Collectors.toList());
    }
    
    @Override
    public Optional<PolicyAccount> findByPolicyAccountNumber(String accountNumber) {
        return policyAccountMap.values().stream()
                .filter(ac -> ac.getPolicyAccountNumber().equals(accountNumber))
                .findFirst();
    }
    
    
    private PolicyAccountDto mapToDto(PolicyAccount entity){
        return new PolicyAccountDto(
                entity.getPolicyAccountNumber(),
                entity.getPolicyNumber(),
                entity.getCreated(),
                entity.getUpdated());
    }
}


// Node: mapToDto
// Node: PolicyAccountDto
package pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.exceptions;

public class PolicyAccountNotFound extends RuntimeException {
    public PolicyAccountNotFound(String accountNumber) {
        super("Policy Account not found. Looking for account with number: " + accountNumber);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/service/api/v1/exceptions/PolicyAccountNotFound.java:PolicyAccountNotFound.<init>
