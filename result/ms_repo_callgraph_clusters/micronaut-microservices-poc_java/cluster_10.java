// Cluster 10

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


// Node: TotalSalesQueryAdapter
// Node: SalesTrendsQueryAdapter
// Node: AgentSalesQueryAdapter
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/elastic/SalesTrendsQueryAdapter.java:SalesTrendsQueryAdapter.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/elastic/TotalSalesQueryAdapter.java:TotalSalesQueryAdapter.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/elastic/AgentSalesQueryAdapter.java:AgentSalesQueryAdapter.<init>
