// Cluster 13

// Node: getYear
// Node: getDayOfMonth
// Node: generatePolicies
package pl.altkom.asc.lab.micronaut.poc.dashboard.init;

import lombok.Builder;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

public class PolicyGenerator {
    private final LocalDateRange generationPeriod;
    private final List<String> agents;
    private final List<String> products;
    private List<String> policyHolders = Arrays.asList(
            "Mike Smith", "Tim Jones", "Berry Cline", "Marion Jones", "Larry Bird",
            "Tara Zane", "Leon Moulder", "Dana Savic", "Evelyn Crowford", "Andrews Eldritch"
    );

    @Builder
    public PolicyGenerator(LocalDateRange generationPeriod, List<String> agents, List<String> products) {
        this.generationPeriod = generationPeriod;
        this.agents = agents;
        this.products = products;
    }

    public List<PolicyDocument> generate() {
        List<PolicyDocument> policies = new ArrayList<>();

        LocalDate salesDate = generationPeriod.getFrom();

        while (!salesDate.isAfter(generationPeriod.getTo())) {
            final LocalDate theDate = salesDate;
            agents.forEach(agent ->
                products.forEach(product -> policies.addAll(generatePolicies(theDate, agent, product)))
            );
            salesDate = salesDate.plusDays(7);
        }

        return policies;
    }

    private List<PolicyDocument> generatePolicies(LocalDate salesDate, String agent, String product) {
        List<PolicyDocument> policiesForDay = new ArrayList<>();
        int numberOfPolicies = randomIntFromRange(1,2);
        for (int i=0; i<numberOfPolicies; i++) {
            PolicyDocument policy = new PolicyDocument(
                    policyNumber(i, salesDate, agent, product),
                    salesDate,
                    salesDate.plusYears(1).minusDays(1),
                    randomHolder(),
                    product,
                    randomPremium(product),
                    agent
            );
            policiesForDay.add(policy);
        }
        return policiesForDay;
    }

    private BigDecimal randomPremium(String product) {
        return new BigDecimal("1000.00");
    }

    private String randomHolder() {
        return policyHolders.get(randomIntFromRange(0,policyHolders.size()-1));
    }

    private String policyNumber(int i,LocalDate salesDate, String agent, String product) {
        return salesDate.getYear() + "/" + salesDate.getMonthValue() + "/" + salesDate.getDayOfMonth()
                + "/" + products.indexOf(product) + "/" + agents.indexOf(agent) + "/" + i;
    }

    private int randomIntFromRange(int min, int max) {
        return ThreadLocalRandom.current().nextInt(min,max);
    }
}


// Node: randomIntFromRange
// Node: policyNumber
// Node: plusYears
// Node: minusDays
// Node: randomHolder
// Node: randomPremium
// Node: getMonthValue
// Node: indexOf
// Node: current
// Node: nextInt
package pl.altkom.asc.lab.micronaut.poc.dashboard.init;


import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.ElasticHealthCheck;

import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;

import javax.inject.Singleton;

import io.micronaut.context.event.ApplicationEventListener;
import io.micronaut.runtime.server.event.ServerStartupEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Singleton
@RequiredArgsConstructor
public class DataLoader implements ApplicationEventListener<ServerStartupEvent> {
    private final PolicyRepository policyRepository;
    private final ElasticHealthCheck elasticHealthCheck;

    @Override
    public void onApplicationEvent(ServerStartupEvent event) {
        waitForElasticSearch();
        savePolicies(generatePolicies());
    }

    private void waitForElasticSearch() {
        var retries = 0;
        while (retries<3) {
            try {
                var health = elasticHealthCheck.health();

                if (health.isOk())
                    return;
            } catch (Exception e) {

            }

            retries++;
            try {
                TimeUnit.SECONDS.sleep(3);
            } catch (InterruptedException e) {

            }
        }

        throw new RuntimeException("Cannot connect to elastic search");
    }

    private void savePolicies(List<PolicyDocument> docs) {
        log.info("Docs to save " + docs.size());
        for (int i = 0; i < docs.size(); i++) {
            policyRepository.save(docs.get(i));
            if (i % 100 == 0) {
                log.info(i + " docs saved");
            }
        }
        log.info("Docs saved.");
    }

    private List<PolicyDocument> generatePolicies() {
        List<String> agents = Arrays.asList("jimmy.solid", "danny.solid", "admin", "agent1", "annn.wolf");
        List<String> products = Arrays.asList("TRI", "HSI", "FAI", "CAR");
        LocalDateRange generationPeriod = LocalDateRange.between(
                LocalDate.now().minusMonths(12),
                LocalDate.now()
        );
        return PolicyGenerator.builder()
                .agents(agents)
                .products(products)
                .generationPeriod(generationPeriod)
                .build()
                .generate();
    }
}


// Node: waitForElasticSearch
// Node: savePolicies
// Node: minusMonths
// Node: agents
// Node: products
// Node: generationPeriod
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


// Node: format
