// Cluster 1

// Node: get
// Node: of
// Node: between
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import io.micronaut.core.util.StringUtils;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.Column;
import javax.persistence.Embeddable;

@Embeddable
@AllArgsConstructor
@NoArgsConstructor
@Getter
public class AgentRef {
    @Column(name = "agent_login")
    private String login;

    public static AgentRef of(String login) {
        if (StringUtils.isNotEmpty(login))
            return new AgentRef(login);

        return null;
    }
}


// Node: isNotEmpty
// Node: AgentRef
// Node: forEach
// Node: setScale
package pl.altkom.asc.lab.micronaut.poc.policy.domain.vo;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.Embeddable;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

@Embeddable
@Getter
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class DateRange {
    private LocalDate from;
    private LocalDate to;

    public static DateRange between(LocalDate from, LocalDate to) {
        return new DateRange(from, to);
    }

    public boolean contains(LocalDate eventDate) {
        if (eventDate.isAfter(to))
            return false;

        if (eventDate.isBefore(from))
            return false;

        return true;
    }

    public DateRange endOn(LocalDate endDate) {
        return DateRange.between(from, endDate);
    }

    public BigDecimal days() {
        return BigDecimal.valueOf(ChronoUnit.DAYS.between(from,to) + 1);
    }
}


// Node: DateRange
// Node: valueOf
package pl.altkom.asc.lab.micronaut.poc.policy.domain.vo;


import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.Embeddable;
import java.math.BigDecimal;
import java.math.RoundingMode;

@Embeddable
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Getter
public class Percent {
    private BigDecimal value;

    public static Percent of(BigDecimal value) {
        return new Percent(value);
    }

    public MonetaryAmount multiply(MonetaryAmount amount) {
        return new MonetaryAmount(amount.getAmount().multiply(toValue()));
    }

    private BigDecimal toValue() {
        return value.divide(new BigDecimal("100"), 9, RoundingMode.HALF_UP);
    }
}


// Node: Percent
// Node: BigDecimal
package pl.altkom.asc.lab.micronaut.poc.policy.domain.vo;

import java.math.BigDecimal;
import java.math.RoundingMode;

import javax.persistence.Embeddable;

import lombok.Getter;

@Embeddable
@Getter
public class MonetaryAmount implements Comparable<MonetaryAmount> {
    private final BigDecimal amount;

    public MonetaryAmount(BigDecimal amount) {
        this.amount = amount.setScale(2, RoundingMode.HALF_UP);
    }

    protected MonetaryAmount() {
        this.amount = BigDecimal.ZERO;
    }
    
    public static MonetaryAmount zero() {
        return from(new BigDecimal("0.00"));
    }

    public static MonetaryAmount from(BigDecimal amount) {
        if (amount == null) {
            throw new RuntimeException("Amount for MonetaryAmount cannot be null");
        }
        return new MonetaryAmount(amount);
    }

    public static MonetaryAmount from(String amount) {
        if (amount == null) {
            throw new RuntimeException("Amount for MonetaryAmount cannot be null");
        }
        return new MonetaryAmount(new BigDecimal(amount));
    }

    public static MonetaryAmount from(Long amount) {
        if (amount == null) {
            throw new RuntimeException("Amount for MonetaryAmount cannot be null");
        }
        return new MonetaryAmount(new BigDecimal(amount));
    }


    public MonetaryAmount add(MonetaryAmount monetaryAmount) {
        if (monetaryAmount == null) {
            throw new RuntimeException("Cant add null MonetaryAmount");
        }
        return new MonetaryAmount(amount.add(monetaryAmount.toBigDecimal()));
    }

    public MonetaryAmount subtract(MonetaryAmount monetaryAmount) {
        if (monetaryAmount == null) {
            throw new RuntimeException("Cant subtract null MonetaryAmount");
        }

        return new MonetaryAmount(amount.subtract(monetaryAmount.toBigDecimal()));
    }

    public boolean greaterThan(MonetaryAmount monetaryAmount) {
        return this.compareTo(monetaryAmount) == 1;
    }

    public boolean greaterOrEqual(MonetaryAmount monetaryAmount) {
        return this.compareTo(monetaryAmount) >= 0;
    }

    public boolean lowerThan(MonetaryAmount monetaryAmount) {
        return this.compareTo(monetaryAmount) == -1;
    }

    public boolean lowerOrEqual(MonetaryAmount monetaryAmount) {
        return this.compareTo(monetaryAmount) <= 0;
    }

    public boolean equalTo(MonetaryAmount monetaryAmount) {
        return this.compareTo(monetaryAmount) == 0;
    }

    public MonetaryAmount toWholeNumber() {
        return new MonetaryAmount(amount.setScale(0, RoundingMode.HALF_UP));
    }

    public MonetaryAmount round(int numberOfDecimalPlaces) {
        return new MonetaryAmount(amount.setScale(numberOfDecimalPlaces, RoundingMode.HALF_UP));
    }

    public static MonetaryAmount min(MonetaryAmount first, MonetaryAmount second) {
        return first.compareTo(second) < 0 ? first : second;
    }

    public static MonetaryAmount max(MonetaryAmount first, MonetaryAmount second) {
        return first.compareTo(second) >= 0 ? first : second;
    }

    public MonetaryAmount multiply(BigDecimal multiplier) {

        return new MonetaryAmount(amount.multiply(multiplier));
    }

    public MonetaryAmount multiply(Integer multiplier) {
        return new MonetaryAmount(amount.multiply(BigDecimal.valueOf(multiplier)));
    }

    public MonetaryAmount multiply(BigDecimal multiplier, RoundingMode rounding) {
        BigDecimal multiplication = amount.multiply(multiplier);
        return new MonetaryAmount(multiplication.setScale(2, rounding));
    }

    public MonetaryAmount multiply(Percent percent) {
        return percent.multiply(this);
    }

    public MonetaryAmount multiply(Quantity quantity) {
        return quantity.multiply(this);
    }

    public MonetaryAmount divide(Quantity qt) {
        return new MonetaryAmount(amount.divide(qt.getValue(), 2, RoundingMode.HALF_UP));
    }

    public BigDecimal toBigDecimal() {
        return new BigDecimal(amount.toString());
    }

    @Override
    public int compareTo(MonetaryAmount o) {
        return amount.compareTo(o.getAmount());
    }

    @Override
    public boolean equals(Object object) {
        if (!(object instanceof MonetaryAmount)) {
            return false;
        }
        return amount.equals(((MonetaryAmount) object).toBigDecimal());
    }

    @Override
    public int hashCode() {
        int hash = 17;
        hash = hash * 29 + amount.hashCode();
        return hash;
    }

    @Override
    public String toString() {
        return this.amount.toString();
    }
}


// Node: getValue
package pl.altkom.asc.lab.micronaut.poc.policy;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.domain.Offer;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferStatus;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.dto.PersonDto;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

import io.micronaut.context.ApplicationContext;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class PolicyControllerTest {

    private static EmbeddedServer server;
    private static PolicyTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(PolicyTestClient.class, server.getURL());
    }

    @Test
    public void testGetPolicyByNumber() {
        String policyNumber = "1234";
        GetPolicyDetailsQueryResult policy = client.get(policyNumber);

        assertNotNull(policy);
        assertNotNull(policy.getPolicy());
        assertEquals(policyNumber, policy.getPolicy().getNumber());
    }

    @Test
    public void testCreatePolicy() {
        //given: offer with number 111 exists
        Map<String, BigDecimal> coverPrices = new HashMap<>();
        coverPrices.put("C1", new BigDecimal("100"));
        coverPrices.put("C2", new BigDecimal("99"));
        Offer offer111 = new Offer(
                null,
                "111",
                "TRI",
                LocalDate.of(2018, 8, 1),
                LocalDate.of(2018, 8, 10),
                new HashMap<>(),
                new BigDecimal("199"),
                coverPrices,
                OfferStatus.NEW,
                LocalDate.now()
        );
        server.getApplicationContext().getBean(OfferRepository.class).save(offer111);

        //when policy creation is requested
        CreatePolicyCommand cmd = new CreatePolicyCommand(
                "111",
                new PersonDto("Timmy", "Lamb", "111111111116"),
                "admin");

        CreatePolicyResult result = client.create(cmd);

        //then policy is created and number is assigned
        assertNotNull(result);
        assertNotNull(result.getPolicyNumber());
    }

    @AfterAll
    public static void cleanup() {
        if (server != null)
            server.stop();

    }
}


// Node: testGetPolicyByNumber
// Node: assertEquals
package pl.altkom.asc.lab.micronaut.poc.policy;

import pl.altkom.asc.lab.micronaut.poc.policy.domain.AgentRef;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Person;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Policy;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyVersion;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.vo.DateRange;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.HashSet;

class PolicyBuilder {

    static Policy build() {
        return new Policy(1L,
                "P1212121",
                AgentRef.of("admin"),
                new HashSet<>(Arrays.asList(
                        new PolicyVersion(
                                1L,
                                null,
                                1L,
                                "Pakiet Gold",
                                new Person("Jan", "Nowak", "111111116"),
                                "2738123834783247723",
                                DateRange.between(LocalDate.of(2018, 1, 1), LocalDate.of(2018, 12, 31)),
                                DateRange.between(LocalDate.of(2018, 1, 1), LocalDate.of(9999, 12, 31)),
                                null,
                                new BigDecimal("199")
                        ),
                        new PolicyVersion(
                                2L,
                                null,
                                2L,
                                "Pakiet Gold",
                                new Person("Jan", "Nowak", "111111116"),
                                "2738123834783247723",
                                DateRange.between(LocalDate.of(2018, 1, 1), LocalDate.of(2018, 12, 31)),
                                DateRange.between(LocalDate.of(2018, 1, 1), LocalDate.of(9999, 12, 31)),
                                null,
                                new BigDecimal("199")
                        )
                )));
    }
}


// Node: build
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

@Getter
public class Calculation {

    private String productCode;
    private LocalDate policyFrom;
    private LocalDate policyTo;
    private BigDecimal totalPremium;
    private Map<String, Cover> covers = new HashMap<>();
    private Map<String, Object> subject = new HashMap<>();

    public Calculation(String productCode,
                       LocalDate policyFrom,
                       LocalDate policyTo,
                       Iterable<String> selectedCovers,
                       Map<String, Object> subject) {
        this.productCode = productCode;
        this.policyFrom = policyFrom;
        this.policyTo = policyTo;
        this.totalPremium = BigDecimal.ZERO;
        selectedCovers.forEach(this::zeroPrice);
        this.subject = subject;
    }

    Map<String, Object> toMap() {
        Map<String, Object> context = new HashMap<>();

        context.put("policyFrom", policyFrom);
        context.put("policyTo", policyTo);
        for (Cover cover : covers.values()) {
            context.put(cover.getCode(), cover);
        }
        context.putAll(subject);

        return context;
    }


    void updateTotal() {
        totalPremium = covers
                .values()
                .stream()
                .filter(c -> c.getPrice() != null)
                .map(Cover::getPrice)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    private void zeroPrice(String cover) {
        covers.put(cover, new Cover(cover, BigDecimal.ZERO));
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/Calculation.java:Calculation.<init>
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.AgentSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TotalSalesQuery;

abstract class QueryAdapter<TQuery, TQueryResult> {
    protected TQuery query;

    QueryAdapter(TQuery query) {
        this.query = query;
    }

    abstract SearchRequest buildQuery();
    abstract TQueryResult extractResult(SearchResponse searchResponse);

    static TotalSalesQueryAdapter of(TotalSalesQuery query) {
        return new TotalSalesQueryAdapter(query);
    }

    static SalesTrendsQueryAdapter of(SalesTrendsQuery query) {
        return new SalesTrendsQueryAdapter(query);
    }

    static AgentSalesQueryAdapter of(AgentSalesQuery query) {
        return new AgentSalesQueryAdapter(query);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/elastic/QueryAdapter.java:QueryAdapter.<init>
// Node: QueryAdapter
// Node: buildQuery
// Node: extractResult
// Node: size
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.index.query.BoolQueryBuilder;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.index.query.RangeQueryBuilder;
import org.elasticsearch.search.aggregations.AggregationBuilder;
import org.elasticsearch.search.aggregations.AggregationBuilders;
import org.elasticsearch.search.aggregations.bucket.filter.Filter;
import org.elasticsearch.search.aggregations.bucket.histogram.DateHistogramAggregationBuilder;
import org.elasticsearch.search.aggregations.bucket.histogram.Histogram;
import org.elasticsearch.search.aggregations.metrics.sum.Sum;
import org.elasticsearch.search.builder.SearchSourceBuilder;
import org.joda.time.DateTime;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesTrendsQuery;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;

public class SalesTrendsQueryAdapter extends QueryAdapter<SalesTrendsQuery,SalesTrendsQuery.Result> {
    public SalesTrendsQueryAdapter(SalesTrendsQuery query) {
        super(query);
    }

    @Override
    SearchRequest buildQuery() {
        SearchRequest searchRequest = new SearchRequest("policy_stats")
                .types("policy_type");

        BoolQueryBuilder filterBuilder = QueryBuilders.boolQuery();
        if (query.getFilterByProductCode()!=null) {
            filterBuilder.must(QueryBuilders.termQuery("productCode.keyword", query.getFilterByProductCode()));
        }
        if (query.getFilterBySalesDate()!=null){
            RangeQueryBuilder datesRange = QueryBuilders
                    .rangeQuery("from")
                    .gte(query.getFilterBySalesDate().getFrom().toString())
                    .lt(query.getFilterBySalesDate().getTo().toString());
            filterBuilder.must(datesRange);
        }
        AggregationBuilder aggBuilder = AggregationBuilders.filter("agg_filter",filterBuilder);

        DateHistogramAggregationBuilder histBuilder = AggregationBuilders
                .dateHistogram("sales")
                .field("from")
                .dateHistogramInterval(query.getAggregationUnit().toDateHistogramInterval())
                .subAggregation(AggregationBuilders.sum("total_premium").field("totalPremium"));
        aggBuilder.subAggregation(histBuilder);

        SearchSourceBuilder srcBuilder = new SearchSourceBuilder()
                .aggregation(aggBuilder)
                .size(0);
        searchRequest.source(srcBuilder);

        return searchRequest;
    }

    @Override
    SalesTrendsQuery.Result extractResult(SearchResponse searchResponse) {
        SalesTrendsQuery.Result.ResultBuilder result = SalesTrendsQuery.Result.builder();

        Filter filterAgg = searchResponse.getAggregations().get("agg_filter");
        Histogram agg = filterAgg.getAggregations().get("sales");
        for (Histogram.Bucket b : agg.getBuckets()){
            DateTime key = (DateTime)b.getKey();
            Sum sum = b.getAggregations().get("total_premium");
            result.periodSale(
                    new SalesTrendsQuery.PeriodSales(
                            LocalDate.of(key.getYear(),key.getMonthOfYear(),key.getDayOfMonth()),
                            b.getKeyAsString(),
                            SalesResult.of(b.getDocCount(), BigDecimal.valueOf(sum.getValue()).setScale(2, RoundingMode.HALF_UP))
                    )
            );
        }

        return result.build();
    }
}


// Node: builder
// Node: getAggregations
// Node: getBuckets
// Node: getKey
// Node: periodSale
// Node: PeriodSales
// Node: getMonthOfYear
// Node: getKeyAsString
// Node: getDocCount
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.index.query.BoolQueryBuilder;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.index.query.RangeQueryBuilder;
import org.elasticsearch.search.aggregations.AggregationBuilder;
import org.elasticsearch.search.aggregations.AggregationBuilders;
import org.elasticsearch.search.aggregations.bucket.filter.Filter;
import org.elasticsearch.search.aggregations.bucket.terms.Terms;
import org.elasticsearch.search.aggregations.bucket.terms.TermsAggregationBuilder;
import org.elasticsearch.search.aggregations.metrics.sum.Sum;
import org.elasticsearch.search.builder.SearchSourceBuilder;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TotalSalesQuery;

import java.math.BigDecimal;
import java.math.RoundingMode;

class TotalSalesQueryAdapter extends QueryAdapter<TotalSalesQuery, TotalSalesQuery.Result> {

    public TotalSalesQueryAdapter(TotalSalesQuery query) {
        super(query);
    }

    @Override
    SearchRequest buildQuery() {
        SearchRequest searchRequest = new SearchRequest("policy_stats")
                .types("policy_type");

        BoolQueryBuilder filterBuilder = QueryBuilders.boolQuery();
        if (query.getFilterByProductCode()!=null) {
            filterBuilder.must(QueryBuilders.termQuery("productCode.keyword", query.getFilterByProductCode()));
        }
        if (query.getFilterBySalesDate()!=null){
            RangeQueryBuilder datesRange = QueryBuilders
                    .rangeQuery("from")
                    .gte(query.getFilterBySalesDate().getFrom().toString())
                    .lt(query.getFilterBySalesDate().getTo().toString());
            filterBuilder.must(datesRange);
        }
        AggregationBuilder aggBuilder = AggregationBuilders.filter("agg_filter",filterBuilder);

        TermsAggregationBuilder sumAggBuilder = AggregationBuilders
                .terms("count_by_product")
                .field("productCode.keyword")
                .subAggregation(AggregationBuilders.sum("total_premium").field("totalPremium"));
        aggBuilder.subAggregation(sumAggBuilder);

        SearchSourceBuilder srcBuilder = new SearchSourceBuilder()
                .aggregation(aggBuilder)
                .size(0);
        searchRequest.source(srcBuilder);

        return searchRequest;
    }

    @Override
    TotalSalesQuery.Result extractResult(SearchResponse searchResponse) {
        TotalSalesQuery.Result.ResultBuilder result = TotalSalesQuery.Result.builder();
        long count = 0;
        BigDecimal amount = BigDecimal.ZERO;
        Filter filterAgg = searchResponse.getAggregations().get("agg_filter");
        Terms products = filterAgg.getAggregations().get("count_by_product");
        for (Terms.Bucket b : products.getBuckets()){
            count += b.getDocCount();
            Sum sum = b.getAggregations().get("total_premium");
            amount = amount.add(BigDecimal.valueOf(sum.getValue()).setScale(2, RoundingMode.HALF_UP));
            result.productTotal(b.getKeyAsString(), SalesResult.of(b.getDocCount(),BigDecimal.valueOf(sum.getValue())));
        }
        result.total(SalesResult.of(count,amount));

        return result.build();
    }

}


// Node: productTotal
// Node: total
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.index.query.BoolQueryBuilder;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.index.query.RangeQueryBuilder;
import org.elasticsearch.search.aggregations.AggregationBuilder;
import org.elasticsearch.search.aggregations.AggregationBuilders;
import org.elasticsearch.search.aggregations.bucket.filter.Filter;
import org.elasticsearch.search.aggregations.bucket.terms.Terms;
import org.elasticsearch.search.aggregations.bucket.terms.TermsAggregationBuilder;
import org.elasticsearch.search.aggregations.metrics.sum.Sum;
import org.elasticsearch.search.builder.SearchSourceBuilder;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.AgentSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesResult;

import java.math.BigDecimal;

public class AgentSalesQueryAdapter extends QueryAdapter<AgentSalesQuery, AgentSalesQuery.Result> {
    public AgentSalesQueryAdapter(AgentSalesQuery query) {
        super(query);
    }

    @Override
    SearchRequest buildQuery() {
        SearchRequest searchRequest = new SearchRequest("policy_stats")
                .types("policy_type");

        BoolQueryBuilder filterBuilder = QueryBuilders.boolQuery();
        if (query.getFilterByAgentLogin() != null) {
            filterBuilder.must(QueryBuilders.termQuery("agentLogin.keyword", query.getFilterByAgentLogin()));
        }
        if (query.getFilterByProductCode() != null) {
            filterBuilder.must(QueryBuilders.termQuery("productCode.keyword", query.getFilterByProductCode()));
        }
        if (query.getFilterBySalesDate() != null) {
            RangeQueryBuilder datesRange = QueryBuilders
                    .rangeQuery("from")
                    .gte(query.getFilterBySalesDate().getFrom().toString())
                    .lt(query.getFilterBySalesDate().getTo().toString());
            filterBuilder.must(datesRange);
        }
        AggregationBuilder aggBuilder = AggregationBuilders.filter("agg_filter", filterBuilder);

        TermsAggregationBuilder sumAggBuilder = AggregationBuilders
                .terms("count_by_agent")
                .field("agentLogin.keyword")
                .subAggregation(AggregationBuilders.sum("total_premium").field("totalPremium"));
        aggBuilder.subAggregation(sumAggBuilder);

        SearchSourceBuilder srcBuilder = new SearchSourceBuilder()
                .aggregation(aggBuilder)
                .size(0);
        searchRequest.source(srcBuilder);

        return searchRequest;
    }

    @Override
    AgentSalesQuery.Result extractResult(SearchResponse searchResponse) {
        AgentSalesQuery.Result.ResultBuilder result = AgentSalesQuery.Result.builder();
        Filter filterAgg = searchResponse.getAggregations().get("agg_filter");
        Terms agents = filterAgg.getAggregations().get("count_by_agent");

        for (Terms.Bucket b : agents.getBuckets()) {
            Sum sum = b.getAggregations().get("total_premium");
            result.agentTotal(
                    b.getKeyAsString(),
                    SalesResult.of(b.getDocCount(), BigDecimal.valueOf(sum.getValue()))
            );
        }

        return result.build();
    }
}


// Node: agentTotal
// Node: executeSearch
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;
import org.elasticsearch.index.query.BoolQueryBuilder;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.search.SearchHit;
import org.elasticsearch.search.builder.SearchSourceBuilder;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.AgentSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config.JsonConverter;

import java.io.IOException;

import javax.inject.Singleton;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Singleton
@RequiredArgsConstructor
public class PolicyElasticRepository implements PolicyRepository {

    private final RestHighLevelClient esClient;
    private final JsonConverter jsonConverter;

    public void save(PolicyDocument policyDocument) {
        IndexRequest indexRequest = new IndexRequest("policy_stats")
                .type("policy_type")
                .id(policyDocument.getNumber())
                .setRefreshPolicy("true")
                .source(jsonConverter.stringifyObject(policyDocument), XContentType.JSON);

        try {
            esClient.index(indexRequest);
        } catch (IOException e) {
            log.error("Error while saving policy", e);
            throw new RuntimeException("Error while executing query", e);
        }
    }

    public PolicyDocument findByNumber(String number) {
        SearchRequest searchRequest = new SearchRequest("policy_stats")
                .types("policy_type");

        BoolQueryBuilder filterBuilder = QueryBuilders.boolQuery();

        filterBuilder.must(QueryBuilders.termQuery("number.keyword", number));

        SearchSourceBuilder srcBuilder = new SearchSourceBuilder()
                .query(filterBuilder)
                .size(10);

        searchRequest.source(srcBuilder);

        SearchResponse searchResponse = executeSearch(searchRequest);

        SearchHit[] hits = searchResponse.getHits().getHits();

        return hits.length > 0
                ? jsonConverter.objectFromString(hits[0].getSourceAsString(), PolicyDocument.class)
                : null;
    }

    public TotalSalesQuery.Result getTotalSales(TotalSalesQuery query) {
        TotalSalesQueryAdapter queryAdapter = QueryAdapter.of(query);
        SearchResponse searchResponse = executeSearch(queryAdapter.buildQuery());
        return queryAdapter.extractResult(searchResponse);
    }

    public SalesTrendsQuery.Result getSalesTrends(SalesTrendsQuery query) {
        SalesTrendsQueryAdapter queryAdapter = QueryAdapter.of(query);
        SearchResponse searchResponse = executeSearch(queryAdapter.buildQuery());
        return queryAdapter.extractResult(searchResponse);
    }

    public AgentSalesQuery.Result getAgentSales(AgentSalesQuery query) {
        AgentSalesQueryAdapter queryAdapter = QueryAdapter.of(query);
        SearchResponse searchResponse = executeSearch(queryAdapter.buildQuery());
        return queryAdapter.extractResult(searchResponse);
    }

    private SearchResponse executeSearch(SearchRequest request) {
        try {
            return esClient.search(request);
        } catch (IOException e) {
            throw new RuntimeException("Failed to execute search", e);
        }
    }
}


// Node: getTotalSales
// Node: getSalesTrends
// Node: getAgentSales
package pl.altkom.asc.lab.micronaut.poc.dashboard.queries.getagentssales;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.AgentSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.dto.SalesDto;

import java.util.HashMap;

public class GetAgentsSalesQueryResultAssembler {

    public static GetAgentsSalesQueryResult assemble(AgentSalesQuery.Result agentsSales) {
        GetAgentsSalesQueryResult result = new GetAgentsSalesQueryResult(new HashMap<>());
        agentsSales.getPerAgentTotal().forEach((agent,sales) ->
            result.getPerAgentTotal().put(agent, new SalesDto(sales.getPoliciesCount(), sales.getPremiumAmount()))
        );
        return result;
    }
}


// Node: assemble
// Node: GetAgentsSalesQueryResult
// Node: getPerAgentTotal
// Node: SalesDto
// Node: getPoliciesCount
// Node: getPremiumAmount
package pl.altkom.asc.lab.micronaut.poc.dashboard.queries.getagentssales;

import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.QueryHandler;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.AgentSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getagentssalesquery.GetAgentsSalesQueryResult;

import javax.inject.Singleton;

@Singleton
@RequiredArgsConstructor
public class GetAgentsSalesQueryHandler implements QueryHandler<GetAgentsSalesQueryResult, GetAgentsSalesQuery> {

    private final PolicyRepository policyRepository;

    @Override
    public GetAgentsSalesQueryResult handle(GetAgentsSalesQuery query) {
        AgentSalesQuery.Result agentsSales = policyRepository.getAgentSales(AgentSalesQuery.builder()
                .filterByAgentLogin(query.getAgentLogin())
                .filterByProductCode(query.getProductCode())
                .filterBySalesDate(LocalDateRange.between(query.getSaleDateFrom(),query.getSaleDateTo()))
                .build());
        return GetAgentsSalesQueryResultAssembler.assemble(agentsSales);
    }
}


// Node: filterByAgentLogin
// Node: filterByProductCode
// Node: filterBySalesDate
// Node: getSaleDateFrom
// Node: getSaleDateTo
package pl.altkom.asc.lab.micronaut.poc.dashboard.queries.getsalestrends;

import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.QueryHandler;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TimeAggregationUnit;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQueryResult;

import javax.inject.Singleton;

@Singleton
@RequiredArgsConstructor
public class GetSalesTrendsQueryHandler implements QueryHandler<GetSalesTrendsQueryResult, GetSalesTrendsQuery> {

    private final PolicyRepository policyRepository;

    @Override
    public GetSalesTrendsQueryResult handle(GetSalesTrendsQuery query) {
        SalesTrendsQuery.Result salesTrends = policyRepository.getSalesTrends(SalesTrendsQuery.builder()
                .filterByProductCode(query.getProductCode())
                .filterBySalesDate(LocalDateRange.between(query.getSaleDateFrom(),query.getSaleDateTo()))
                .aggregationUnit(TimeAggregationUnit.valueOf(query.getAggregationUnitCode()))
                .build());
        return GetSalesTrendsQueryResultAssembler.assemble(salesTrends);
    }
}


// Node: aggregationUnit
// Node: getAggregationUnitCode
package pl.altkom.asc.lab.micronaut.poc.dashboard.queries.getsalestrends;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.SalesTrendsQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.GetSalesTrendsQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.getsalestrendsquery.dto.PeriodSalesDto;

import java.util.ArrayList;

public class GetSalesTrendsQueryResultAssembler {

    public static GetSalesTrendsQueryResult assemble(SalesTrendsQuery.Result salesTrands) {
        GetSalesTrendsQueryResult result = new GetSalesTrendsQueryResult(new ArrayList<>());
        salesTrands.getPeriodSales().forEach(periodSales ->
                result.getPeriodSales().add(new PeriodSalesDto(
                        periodSales.getPeriodDate(),
                        periodSales.getPeriod(),
                        periodSales.getSales().getPoliciesCount(),
                        periodSales.getSales().getPremiumAmount()
                )));
        return result;
    }
}


// Node: GetSalesTrendsQueryResult
// Node: getPeriodSales
// Node: PeriodSalesDto
// Node: getPeriodDate
// Node: getPeriod
// Node: getSales
package pl.altkom.asc.lab.micronaut.poc.dashboard.queries.gettotalsales;

import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.QueryHandler;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQueryResult;

import javax.inject.Singleton;


@Singleton
@RequiredArgsConstructor
public class GetTotalSalesQueryHandler implements QueryHandler<GetTotalSalesQueryResult, GetTotalSalesQuery> {

    private final PolicyRepository policyRepository;

    @Override
    public GetTotalSalesQueryResult handle(GetTotalSalesQuery query) {
        TotalSalesQuery.Result totalSales = policyRepository.getTotalSales(TotalSalesQuery.builder()
                .filterByProductCode(query.getProductCode())
                .filterBySalesDate(LocalDateRange.between(query.getSaleDateFrom(), query.getSaleDateTo()))
                .build());
        return GetTotalSalesQueryResultAssembler.assemble(totalSales);
    }
}


package pl.altkom.asc.lab.micronaut.poc.dashboard.queries.gettotalsales;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.TotalSalesQuery;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.GetTotalSalesQueryResult;
import pl.altkom.asc.lab.micronaut.poc.dashboard.service.api.v1.queries.gettotalsalesquery.dto.SalesDto;

import java.util.HashMap;

class GetTotalSalesQueryResultAssembler {
    static GetTotalSalesQueryResult assemble(TotalSalesQuery.Result queryResult) {
        GetTotalSalesQueryResult result = new GetTotalSalesQueryResult(
            new SalesDto(queryResult.getTotal().getPoliciesCount(), queryResult.getTotal().getPremiumAmount()),
            new HashMap<>()
        );
        queryResult.getPerProductTotal().forEach((k,v) ->
            result.getPerProductTotal().put(k, new SalesDto(v.getPoliciesCount(),v.getPremiumAmount()))
        );
        return result;
    }
}


// Node: GetTotalSalesQueryResult
// Node: getTotal
// Node: getPerProductTotal
package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.LocalDate;

@AllArgsConstructor(access = AccessLevel.PROTECTED)
@Getter
public class LocalDateRange {
    private final LocalDate from;
    private final LocalDate to;

    public static LocalDateRange between(LocalDate from, LocalDate to) {
        return new LocalDateRange(from,to);
    }
}


// Node: LocalDateRange
// Node: PolicyDocument
package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

public interface PolicyRepository {

    void save(PolicyDocument policyDocument);

    PolicyDocument findByNumber(String number);

    TotalSalesQuery.Result getTotalSales(TotalSalesQuery query);

    SalesTrendsQuery.Result getSalesTrends(SalesTrendsQuery query);

    AgentSalesQuery.Result getAgentSales(AgentSalesQuery query);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/domain/PolicyRepository.java:PolicyRepository.<init>
package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.math.BigDecimal;

@AllArgsConstructor
@Getter
public class SalesResult {
    private Long policiesCount;
    private BigDecimal premiumAmount;

    public static SalesResult of(Long count,BigDecimal total) {
        return new SalesResult(count,total);
    }
}


// Node: SalesResult
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


// Node: seedData
// Node: policyElasticRepository
// Node: canFindTotal
// Node: canFindTotalFilteredByProduct
// Node: canFindTotalFilteredBySalesDates
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


// Node: canFindAgentSales
// Node: canFindAgentSalesFilteredByProduct
// Node: canFindAgentSalesFilteredBySalesDates
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


// Node: canFindSalesTrends
// Node: canFindSalesTrendsFilteredByProduct
// Node: canFindSalesTrendsFilteredBySalesDates
// Node: balanceAt
// Node: PolicyAccount
// Node: expectedPayment
// Node: inPayment
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;

public class PolicyAccountTest {
    @Test
    public void canRegisterInPayment() {
        PolicyAccount account = new PolicyAccount("A", "A");
        account.inPayment(new BigDecimal("10"), LocalDate.of(2018,1,1));
        
        Assertions.assertEquals(1, account.getEntries().size(),"one entry present");
        Assertions.assertEquals(new BigDecimal("10"), account.balanceAt(LocalDate.of(2018,1,1)),"balance is 10");
    }
    
    @Test
    public void canRegisterOutpayment() {
        PolicyAccount account = new PolicyAccount("A", "A");
        account.outPayment(new BigDecimal("10"), LocalDate.of(2018,1,1));

        Assertions.assertEquals(1, account.getEntries().size(),"one entry present");
        Assertions.assertEquals(new BigDecimal("-10"), account.balanceAt(LocalDate.of(2018,1,1)),"balance is -10");
    }
    
    @Test
    public void canRegisterExpectdPayment() {
        PolicyAccount account = new PolicyAccount("A", "A");
        account.expectedPayment(new BigDecimal("10"), LocalDate.of(2018,1,1));

        Assertions.assertEquals(1, account.getEntries().size(), "one entry present");
        Assertions.assertEquals(new BigDecimal("-10"), account.balanceAt(LocalDate.of(2018,1,1)),"balance is -10");
    }
    
    @Test
    public void canProperlyCalculateBalance() {
        PolicyAccount account = new PolicyAccount("A", "A");
        account.expectedPayment(new BigDecimal("10"), LocalDate.of(2018,1,1));
        account.expectedPayment(new BigDecimal("10"), LocalDate.of(2018,6,1));
        account.inPayment(new BigDecimal("15"), LocalDate.of(2018,1,7));

        Assertions.assertEquals(new BigDecimal("-10"), account.balanceAt(LocalDate.of(2018,1,1)),"balance at 2018-1-1  is -10");
        Assertions.assertEquals(new BigDecimal("5"), account.balanceAt(LocalDate.of(2018,1,7)),"balance at 2018-1-7  is 5");
        Assertions.assertEquals(new BigDecimal("-5"), account.balanceAt(LocalDate.of(2018,6,1)),"balance at 2018-6-1  is -5");
    }
}


// Node: canRegisterInPayment
// Node: getEntries
// Node: canRegisterOutpayment
// Node: canRegisterExpectdPayment
// Node: canProperlyCalculateBalance
package pl.altkom.asc.lab.micronaut.poc.gateway;

import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import io.micronaut.security.annotation.Secured;
import io.micronaut.security.rules.SecurityRule;
import io.reactivex.Maybe;
import io.reactivex.Single;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.ProductGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;

import javax.inject.Inject;
import java.util.List;

@Secured(SecurityRule.IS_AUTHENTICATED)
@Controller("/api/products")
public class ProductGatewayController {

    @Inject
    private ProductGatewayClient client;

    @Get
    public Single<List<ProductDto>> getAll() {
        return client.getAll();
    }

    @Get("/{productCode}")
    public Maybe<ProductDto> get(String productCode) {
        return client.get(productCode);
    }
}


