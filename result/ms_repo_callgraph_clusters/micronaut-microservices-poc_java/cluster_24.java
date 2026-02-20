// Cluster 24

package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config;

import io.micronaut.context.annotation.ConfigurationProperties;
import lombok.Getter;
import lombok.Setter;

@ConfigurationProperties("elastic")
@Getter
@Setter
class ElasticSearchSettings {
    private String host;
    private int port;
    private int connectionTimeout;
    private int connectionRequestTimeout;
    private int socketTimeout;
    private int maxRetryTimeout;
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/elastic/config/ElasticSearchSettings.java:ElasticSearchSettings.<init>
// Node: ConfigurationProperties
package pl.altkom.asc.lab.micronaut.poc.payment.infrastructure.adapters.jobs;

import io.micronaut.context.annotation.ConfigurationProperties;
import lombok.Getter;
import lombok.Setter;

@ConfigurationProperties("payments")
@Getter
@Setter
class BankStatementImportJobCfg {
    private String importDir = "c:\\temp\\bank_imports";  
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/infrastructure/adapters/jobs/BankStatementImportJobCfg.java:BankStatementImportJobCfg.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db;

import io.micronaut.context.annotation.ConfigurationProperties;
import lombok.Getter;
import lombok.Setter;

@ConfigurationProperties("elastic")
@Getter
@Setter
class ElasticSearchSettings {
    private String host;
    private int port;
    private int connectionTimeout;
    private int connectionRequestTimeout;
    private int socketTimeout;
    private int maxRetryTimeout;
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/infrastructure/adapters/db/ElasticSearchSettings.java:ElasticSearchSettings.<init>
