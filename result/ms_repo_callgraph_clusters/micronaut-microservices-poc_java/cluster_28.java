// Cluster 28

package pl.altkom.asc.lab.micronaut.poc.dashboard.elastic;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.PolicyElasticRepository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public class PolicyElasticRepositoryGetTotalSalesTest extends EmbeddedElasticTest {

    @BeforeAll
    public void seedData() {
        List<PolicyDocument> docs = Arrays.asList(
                new PolicyDocument(
                        "111-001",
                        LocalDate.of(2019, 1, 1),
                        LocalDate.of(2019, 12, 31),
                        "John Smith",
                        "SAFE_HOUSE",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-002",
                        LocalDate.of(2019, 2, 1),
                        LocalDate.of(2020, 1, 31),
                        "John Smith",
                        "SAFE_HOUSE",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-003",
                        LocalDate.of(2019, 2, 1),
                        LocalDate.of(2020, 2, 28),
                        "John Smith",
                        "SAFE_CAR",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-004",
                        LocalDate.of(2019, 3, 1),
                        LocalDate.of(2020, 3, 31),
                        "John Smith",
                        "SAFE_CAR",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-005",
                        LocalDate.of(2019, 4, 1),
                        LocalDate.of(2020, 4, 30),
                        "John Smith",
                        "SAFE_FARM",
                        BigDecimal.valueOf(1000),
                        "m.smith")
        );

        PolicyElasticRepository repository = policyElasticRepository();

        docs.forEach(d -> repository.save(d));
    }

    @Test
    public void canFindTotal() {
        TotalSalesQuery.Result total = policyElasticRepository().getTotalSales(TotalSalesQuery.builder()
                .filterByProductCode(null)
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,12,31)))
                .build()
        );

        assertEquals(Long.valueOf(5L), total.getTotal().getPoliciesCount());
        assertEquals(new BigDecimal("5000.00"), total.getTotal().getPremiumAmount());

        assertEquals(Long.valueOf(1L), total.getPerProductTotal().get("SAFE_FARM").getPoliciesCount());
        assertEquals(new BigDecimal("1000.0"), total.getPerProductTotal().get("SAFE_FARM").getPremiumAmount());
    }

    @Test
    public void canFindTotalFilteredByProduct() {
        TotalSalesQuery.Result total = policyElasticRepository().getTotalSales(TotalSalesQuery.builder()
                .filterByProductCode("SAFE_FARM")
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,12,31)))
                .build()
        );

        assertEquals(Long.valueOf(1L), total.getTotal().getPoliciesCount());
        assertEquals(new BigDecimal("1000.00"), total.getTotal().getPremiumAmount());

        assertEquals(Long.valueOf(1L), total.getPerProductTotal().get("SAFE_FARM").getPoliciesCount());
        assertEquals(new BigDecimal("1000.0"), total.getPerProductTotal().get("SAFE_FARM").getPremiumAmount());
    }

    @Test
    public void canFindTotalFilteredBySalesDates() {
        TotalSalesQuery.Result total = policyElasticRepository().getTotalSales(TotalSalesQuery.builder()
                .filterByProductCode(null)
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,2,28)))
                .build()
        );

        assertEquals(Long.valueOf(3L), total.getTotal().getPoliciesCount());
        assertEquals(new BigDecimal("3000.00"), total.getTotal().getPremiumAmount());

        assertEquals(Long.valueOf(2L), total.getPerProductTotal().get("SAFE_HOUSE").getPoliciesCount());
        assertEquals(new BigDecimal("2000.0"), total.getPerProductTotal().get("SAFE_HOUSE").getPremiumAmount());
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/dashboard/elastic/PolicyElasticRepositoryGetTotalSalesTest.java:PolicyElasticRepositoryGetTotalSalesTest.<init>
// Node: TestInstance
package pl.altkom.asc.lab.micronaut.poc.dashboard.elastic;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.AgentSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.PolicyElasticRepository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public class PolicyElasticRepositoryGetAgentSalesTest extends EmbeddedElasticTest {

    @BeforeAll
    public void seedData() {
        List<PolicyDocument> docs = Arrays.asList(
                new PolicyDocument(
                        "111-001",
                        LocalDate.of(2019, 1, 1),
                        LocalDate.of(2019, 12, 31),
                        "John Smith",
                        "SAFE_HOUSE",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-002",
                        LocalDate.of(2019, 2, 1),
                        LocalDate.of(2020, 1, 31),
                        "John Smith",
                        "SAFE_HOUSE",
                        BigDecimal.valueOf(1000),
                        "a.smith"),
                new PolicyDocument(
                        "111-003",
                        LocalDate.of(2019, 2, 1),
                        LocalDate.of(2020, 2, 28),
                        "John Smith",
                        "SAFE_CAR",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-004",
                        LocalDate.of(2019, 3, 1),
                        LocalDate.of(2020, 3, 31),
                        "John Smith",
                        "SAFE_CAR",
                        BigDecimal.valueOf(1000),
                        "a.smith"),
                new PolicyDocument(
                        "111-005",
                        LocalDate.of(2019, 4, 1),
                        LocalDate.of(2020, 4, 30),
                        "John Smith",
                        "SAFE_FARM",
                        BigDecimal.valueOf(1000),
                        "m.smith")
        );

        PolicyElasticRepository repository = policyElasticRepository();

        docs.forEach(d -> repository.save(d));
    }

    @Test
    public void canFindAgentSales() {
        AgentSalesQuery.Result agentSales = policyElasticRepository().getAgentSales(AgentSalesQuery.builder()
                .filterByProductCode(null)
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,12,31)))
                .build()
        );

        assertEquals(Long.valueOf(3L), agentSales.getPerAgentTotal().get("m.smith").getPoliciesCount());
        assertEquals(new BigDecimal("3000.0"), agentSales.getPerAgentTotal().get("m.smith").getPremiumAmount());

        assertEquals(Long.valueOf(2L), agentSales.getPerAgentTotal().get("a.smith").getPoliciesCount());
        assertEquals(new BigDecimal("2000.0"), agentSales.getPerAgentTotal().get("a.smith").getPremiumAmount());
    }

    @Test
    public void canFindAgentSalesFilteredByProduct() {
        AgentSalesQuery.Result agentSales = policyElasticRepository().getAgentSales(AgentSalesQuery.builder()
                .filterByProductCode("SAFE_HOUSE")
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,12,31)))
                .build()
        );

        assertEquals(Long.valueOf(1L), agentSales.getPerAgentTotal().get("m.smith").getPoliciesCount());
        assertEquals(new BigDecimal("1000.0"), agentSales.getPerAgentTotal().get("m.smith").getPremiumAmount());
    }

    @Test
    public void canFindAgentSalesFilteredBySalesDates() {
        AgentSalesQuery.Result agentSales = policyElasticRepository().getAgentSales(AgentSalesQuery.builder()
                .filterByProductCode(null)
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,3,31)))
                .build()
        );

        assertEquals(Long.valueOf(2L), agentSales.getPerAgentTotal().get("m.smith").getPoliciesCount());
        assertEquals(new BigDecimal("2000.0"), agentSales.getPerAgentTotal().get("m.smith").getPremiumAmount());

        assertEquals(Long.valueOf(2L), agentSales.getPerAgentTotal().get("a.smith").getPoliciesCount());
        assertEquals(new BigDecimal("2000.0"), agentSales.getPerAgentTotal().get("a.smith").getPremiumAmount());
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/dashboard/elastic/PolicyElasticRepositoryGetAgentSalesTest.java:PolicyElasticRepositoryGetAgentSalesTest.<init>
package pl.altkom.asc.lab.micronaut.poc.dashboard.elastic;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TimeAggregationUnit;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.PolicyElasticRepository;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public class PolicyElasticRepositoryGetSalesTrendsTest extends EmbeddedElasticTest {

    @BeforeAll
    public void seedData() {
        List<PolicyDocument> docs = Arrays.asList(
                new PolicyDocument(
                        "111-001",
                        LocalDate.of(2019, 1, 1),
                        LocalDate.of(2019, 12, 31),
                        "John Smith",
                        "SAFE_HOUSE",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-002",
                        LocalDate.of(2019, 2, 1),
                        LocalDate.of(2020, 1, 31),
                        "John Smith",
                        "SAFE_HOUSE",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-003",
                        LocalDate.of(2019, 2, 2),
                        LocalDate.of(2020, 2, 28),
                        "John Smith",
                        "SAFE_CAR",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-004",
                        LocalDate.of(2019, 3, 1),
                        LocalDate.of(2020, 3, 31),
                        "John Smith",
                        "SAFE_CAR",
                        BigDecimal.valueOf(1000),
                        "m.smith"),
                new PolicyDocument(
                        "111-005",
                        LocalDate.of(2019, 4, 1),
                        LocalDate.of(2020, 4, 30),
                        "John Smith",
                        "SAFE_FARM",
                        BigDecimal.valueOf(1000),
                        "m.smith")
        );

        PolicyElasticRepository repository = policyElasticRepository();

        docs.forEach(d -> repository.save(d));
    }

    @Test
    public void canFindSalesTrends() {
        SalesTrendsQuery.Result trends = policyElasticRepository().getSalesTrends(SalesTrendsQuery.builder()
                .filterByProductCode(null)
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,12,31)))
                .aggregationUnit(TimeAggregationUnit.MONTH)
                .build());

        assertEquals(4, trends.getPeriodSales().size());

        assertEquals("2019-01-01", trends.getPeriodSales().get(0).getPeriodDate().toString());
        assertEquals(Long.valueOf(1L), trends.getPeriodSales().get(0).getSales().getPoliciesCount());
        assertEquals(new BigDecimal("1000.00"), trends.getPeriodSales().get(0).getSales().getPremiumAmount());

        assertEquals("2019-02-01", trends.getPeriodSales().get(1).getPeriodDate().toString());
        assertEquals(Long.valueOf(2L), trends.getPeriodSales().get(1).getSales().getPoliciesCount());
        assertEquals(new BigDecimal("2000.00"), trends.getPeriodSales().get(1).getSales().getPremiumAmount());

        assertEquals("2019-03-01", trends.getPeriodSales().get(2).getPeriodDate().toString());
        assertEquals(Long.valueOf(1L), trends.getPeriodSales().get(2).getSales().getPoliciesCount());
        assertEquals(new BigDecimal("1000.00"), trends.getPeriodSales().get(2).getSales().getPremiumAmount());

        assertEquals("2019-04-01", trends.getPeriodSales().get(3).getPeriodDate().toString());
        assertEquals(Long.valueOf(1L), trends.getPeriodSales().get(3).getSales().getPoliciesCount());
        assertEquals(new BigDecimal("1000.00"), trends.getPeriodSales().get(3).getSales().getPremiumAmount());
    }

    @Test
    public void canFindSalesTrendsFilteredByProduct() {
        SalesTrendsQuery.Result trends = policyElasticRepository().getSalesTrends(SalesTrendsQuery.builder()
                .filterByProductCode("SAFE_HOUSE")
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019,1,1),LocalDate.of(2019,12,31)))
                .aggregationUnit(TimeAggregationUnit.MONTH)
                .build());

        assertEquals(2, trends.getPeriodSales().size());

        assertEquals("2019-01-01", trends.getPeriodSales().get(0).getPeriodDate().toString());
        assertEquals(Long.valueOf(1L), trends.getPeriodSales().get(0).getSales().getPoliciesCount());
        assertEquals(new BigDecimal("1000.00"), trends.getPeriodSales().get(0).getSales().getPremiumAmount());

        assertEquals("2019-02-01", trends.getPeriodSales().get(1).getPeriodDate().toString());
        assertEquals(Long.valueOf(1L), trends.getPeriodSales().get(1).getSales().getPoliciesCount());
        assertEquals(new BigDecimal("1000.00"), trends.getPeriodSales().get(1).getSales().getPremiumAmount());

    }


    @Test
    public void canFindSalesTrendsFilteredBySalesDates() {
        SalesTrendsQuery.Result trends = policyElasticRepository().getSalesTrends(SalesTrendsQuery.builder()
                .filterByProductCode(null)
                .filterBySalesDate(LocalDateRange.between(LocalDate.of(2019, 1, 1), LocalDate.of(2019, 1, 31)))
                .aggregationUnit(TimeAggregationUnit.MONTH)
                .build());

        assertEquals(1, trends.getPeriodSales().size());

        assertEquals("2019-01-01", trends.getPeriodSales().get(0).getPeriodDate().toString());
        assertEquals(Long.valueOf(1L), trends.getPeriodSales().get(0).getSales().getPoliciesCount());
        assertEquals(new BigDecimal("1000.00"), trends.getPeriodSales().get(0).getSales().getPremiumAmount());

    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/dashboard/elastic/PolicyElasticRepositoryGetSalesTrendsTest.java:PolicyElasticRepositoryGetSalesTrendsTest.<init>
