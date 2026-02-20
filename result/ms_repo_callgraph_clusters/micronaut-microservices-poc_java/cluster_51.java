// Cluster 51

package pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery;

import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.dto.SalesDto;

import java.util.Map;

import io.micronaut.core.annotation.Introspected;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.Singular;

@Introspected
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class GetAgentsSalesQueryResult {
    @Singular("agentTotal")
    private Map<String, SalesDto> perAgentTotal;
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/service/api/v1/queries/getagentssalesquery/GetAgentsSalesQueryResult.java:GetAgentsSalesQueryResult.<init>
// Node: Singular
package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.Singular;

import java.util.Map;

@AllArgsConstructor
@Getter
@Builder
public class TotalSalesQuery {
    private String filterByProductCode;
    private LocalDateRange filterBySalesDate;

    @AllArgsConstructor
    @Builder
    @Getter
    public static class Result {
        private SalesResult total;
        @Singular("productTotal")
        private Map<String, SalesResult> perProductTotal;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/domain/TotalSalesQuery.java:TotalSalesQuery.<init>
package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.Singular;

import java.util.Map;

@AllArgsConstructor
@Getter
@Builder
public class AgentSalesQuery {
    private String filterByAgentLogin;
    private String filterByProductCode;
    private LocalDateRange filterBySalesDate;

    @AllArgsConstructor
    @Builder
    @Getter
    public static class Result {
        @Singular("agentTotal")
        private Map<String, SalesResult> perAgentTotal;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/domain/AgentSalesQuery.java:AgentSalesQuery.<init>
