// Cluster 33

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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/infrastructure/adapters/jobs/BankStatementImportJob.java:BankStatementImportJob.<init>
// Node: Scheduled
