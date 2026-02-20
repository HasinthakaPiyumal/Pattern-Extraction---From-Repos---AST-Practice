// Cluster 11

// Node: RuntimeException
// Node: index
package pl.altkom.asc.lab.micronaut.poc.policy;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.Health;

import io.micronaut.context.ApplicationContext;
import io.micronaut.http.HttpStatus;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class HelloControllerTest {

    private static EmbeddedServer server;
    private static HelloTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(HelloTestClient.class, server.getURL());
    }

    @AfterAll
    public static void cleanup() {
        if (server != null) {
            server.stop();
        }
    }

    @Test
    public void testIndex() {
        assertEquals(HttpStatus.OK, client.index());
    }

    @Test
    public void testVersion() {
        Health actualInfo = client.version();
        Health expectedInfo = new Health("1.0", "OK");

        assertEquals(expectedInfo.toString(), actualInfo.toString());
        assertEquals(expectedInfo.getStatus(), actualInfo.getStatus());
        assertEquals(expectedInfo.getVer(), actualInfo.getVer());
    }
}


// Node: testIndex
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


// Node: SearchRequest
// Node: types
// Node: boolQuery
// Node: getFilterByProductCode
// Node: must
// Node: termQuery
// Node: getFilterBySalesDate
// Node: rangeQuery
// Node: gte
// Node: lt
// Node: dateHistogram
// Node: field
// Node: dateHistogramInterval
// Node: getAggregationUnit
// Node: toDateHistogramInterval
// Node: subAggregation
// Node: sum
// Node: SearchSourceBuilder
// Node: aggregation
// Node: source
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


// Node: terms
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic;

import io.micronaut.core.annotation.Introspected;
import lombok.Getter;
import lombok.Setter;

@Introspected
@Getter
@Setter
public class ElasticHealthCheckResult {
    private String status;

    public boolean isOk() {
        return "green".equals(status) || "yellow".equals(status);
    }
}


// Node: isOk
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


// Node: getFilterByAgentLogin
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


// Node: IndexRequest
// Node: type
// Node: id
// Node: setRefreshPolicy
// Node: stringifyObject
// Node: error
// Node: query
// Node: getHits
// Node: objectFromString
// Node: getSourceAsString
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import javax.inject.Singleton;
import java.io.IOException;

@Singleton
@Slf4j
@RequiredArgsConstructor
public class JsonConverter {
    private final ObjectMapper jsonMapper;

    public <T> String stringifyObject(T doc) {
        try {
            return jsonMapper.writeValueAsString(doc);
        } catch (JsonProcessingException e) {
            log.error("Failed to serialized policy to json", e);
            throw new RuntimeException("Failed to stringify object", e);
        }
    }

    public <T> T objectFromString(String src, Class<T> clazz) {
        try {
            return jsonMapper.readValue(src, clazz);
        } catch (IOException ioExc) {
            log.error("Failed to deserialize from string " + src, ioExc);
            throw new RuntimeException("Failed to create object from String", ioExc);
        }
    }
}



// Node: writeValueAsString
// Node: readValue
package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

import org.elasticsearch.search.aggregations.bucket.histogram.DateHistogramInterval;

public enum TimeAggregationUnit {
    DAY,
    WEEK,
    MONTH,
    YEAR;

    public DateHistogramInterval toDateHistogramInterval(){
        return switch (this) {
            case DAY-> DateHistogramInterval.DAY;
            case WEEK-> DateHistogramInterval.WEEK;
            case MONTH-> DateHistogramInterval.MONTH;
            case YEAR-> DateHistogramInterval.YEAR;
            default->
                throw new IllegalArgumentException("Invalid unit value");
        };
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


// Node: sleep
package pl.altkom.asc.lab.micronaut.poc.dashboard.elastic;

import pl.allegro.tech.embeddedelasticsearch.EmbeddedElastic;
import pl.allegro.tech.embeddedelasticsearch.PopularProperties;

import java.io.IOException;

public class DashboardEmbeddedElastic {
    private static EmbeddedElastic embeddedElastic = null;

    static EmbeddedElastic getInstance() {
        if (embeddedElastic == null) {
            try {
                embeddedElastic = createAndRun();
            } catch (IOException | InterruptedException e) {
                throw new RuntimeException("Cannot start embedded Elastic", e);
            }
        }
        return embeddedElastic;
    }

    private static EmbeddedElastic createAndRun() throws IOException, InterruptedException {
        return EmbeddedElastic.builder()
                .withElasticVersion("6.6.2")
                .withSetting(PopularProperties.TRANSPORT_TCP_PORT, 9350)
                .withSetting(PopularProperties.HTTP_PORT, 9351)
                .withSetting(PopularProperties.CLUSTER_NAME, "my_cluster")
                .build()
                .start();

    }
}


// Node: getInstance
// Node: createAndRun
// Node: withElasticVersion
// Node: withSetting
// Node: start
package pl.altkom.asc.lab.micronaut.poc.dashboard.elastic;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import pl.allegro.tech.embeddedelasticsearch.EmbeddedElastic;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.PolicyElasticRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config.JsonConverter;

public class EmbeddedElasticTest {
    protected EmbeddedElastic el = DashboardEmbeddedElastic.getInstance();

    protected PolicyElasticRepository policyElasticRepository() {
        return new PolicyElasticRepository(
                new RestHighLevelClient(RestClient.builder(new HttpHost("localhost", el.getHttpPort(), "http"))),
                new JsonConverter(objectMapper())
        );
    }

    protected ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/dashboard/elastic/EmbeddedElasticTest.java:EmbeddedElasticTest.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import javax.inject.Singleton;
import java.io.IOException;

@Singleton
@Slf4j
@RequiredArgsConstructor
class JsonConverter {
    private final ObjectMapper jsonMapper;

    <T> String stringifyObject(T doc) {
        try {
            return jsonMapper.writeValueAsString(doc);
        } catch (JsonProcessingException e) {
            log.error("Failed to serialized policy to json", e);
            return null;
        }
    }

    <T> T objectFromString(String src, Class<T> clazz) {
        try {
            return jsonMapper.readValue(src, clazz);
        } catch (IOException ioExc) {
            log.error("Failed to deserialize from string " + src, ioExc);
            return null;
        }
    }
}


package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db;

import io.reactivex.Maybe;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import javax.inject.Singleton;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.common.xcontent.XContentType;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.index.query.QueryStringQueryBuilder;
import org.elasticsearch.search.builder.SearchSourceBuilder;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyView;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyViewRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQuery;

@Singleton
@Slf4j
@RequiredArgsConstructor
public class ElasticPolicyViewRepository implements PolicyViewRepository {

    private static final String INDEX_NAME = "policy-views";

    private final ElasticClientAdapter elasticClientAdapter;
    private final JsonConverter jsonConverter;
    
    @Override
    public void save(PolicyView policy) {
        IndexRequest indexRequest = new IndexRequest(INDEX_NAME,"policyview", policy.getNumber());
        indexRequest.source(jsonConverter.stringifyObject(policy), XContentType.JSON);
        elasticClientAdapter.index(indexRequest).blockingGet();
    }
    
    @Override
    public Maybe<List<PolicyView>> findAll(FindPolicyQuery query) {
        SearchRequest searchRequest = new SearchRequest(INDEX_NAME);

        QueryStringQueryBuilder queryStringQueryBuilder = QueryBuilders.queryStringQuery(query.getQueryText())
                .field("number")
                .field("policyHolder");

        SearchSourceBuilder searchSourceBuilder = new SearchSourceBuilder();
        searchSourceBuilder.query(queryStringQueryBuilder).size(100);

        searchRequest.source(searchSourceBuilder);

        return elasticClientAdapter
                .search(searchRequest)
                .map(this::mapSearchResponse);
    }
    
    private List<PolicyView> mapSearchResponse(SearchResponse searchResponse) {
        return Arrays
                .stream(searchResponse.getHits().getHits())
                .map(hit -> jsonConverter.objectFromString(hit.getSourceAsString(), PolicyView.class))
                .collect(Collectors.toList());
    }
    
    
}


// Node: queryStringQuery
// Node: getQueryText
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db;

import io.reactivex.Maybe;
import lombok.extern.slf4j.Slf4j;
import org.apache.http.HttpHost;
import org.elasticsearch.action.ActionListener;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.index.IndexResponse;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import javax.inject.Singleton;

@Singleton
@Slf4j
public class ElasticClientAdapter {

    private final RestHighLevelClient restHighLevelClient;
    private final ElasticSearchSettings elasticSearchSettings;

    public ElasticClientAdapter(ElasticSearchSettings elasticSearchSettings) {
        this.elasticSearchSettings = elasticSearchSettings;
        this.restHighLevelClient = buildClient();
    }

    Maybe<IndexResponse> index(IndexRequest indexRequest) {
        return Maybe.create(sink -> {
            restHighLevelClient.indexAsync(indexRequest, new ActionListener<IndexResponse>() {
                @Override
                public void onResponse(IndexResponse indexResponse) {
                    sink.onSuccess(indexResponse);
                }

                @Override
                public void onFailure(Exception e) {
                    sink.onError(e);
                }
            });
        });
    }

    public Maybe<SearchResponse> search(SearchRequest searchRequest) {
        return Maybe.create(sink ->
                restHighLevelClient.searchAsync(searchRequest, new ActionListener<SearchResponse>() {
                    @Override
                    public void onResponse(SearchResponse searchResponse) {
                        sink.onSuccess(searchResponse);
                    }

                    @Override
                    public void onFailure(Exception e) {
                        sink.onError(e);
                    }
                }));
    }

    private RestHighLevelClient buildClient() {
        return new RestHighLevelClient(
                RestClient.builder(new HttpHost(elasticSearchSettings.getHost(), elasticSearchSettings.getPort()))
                        .setRequestConfigCallback(config -> config
                                .setConnectTimeout(elasticSearchSettings.getConnectionTimeout())
                                .setConnectionRequestTimeout(elasticSearchSettings.getConnectionRequestTimeout())
                                .setSocketTimeout(elasticSearchSettings.getSocketTimeout())
                        )
                        .setMaxRetryTimeoutMillis(elasticSearchSettings.getMaxRetryTimeout()));
    }
}


// Node: indexAsync
