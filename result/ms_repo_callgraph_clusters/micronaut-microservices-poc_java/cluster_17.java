// Cluster 17

// Node: getBean
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config;

import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

import javax.inject.Singleton;

import io.micronaut.context.annotation.Factory;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Factory
@RequiredArgsConstructor
public class ElasticConfig {

    private final ElasticSearchSettings elasticSearchSettings;


    @Singleton
    public RestHighLevelClient restHighLevelClient() {
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


// Node: restHighLevelClient
// Node: RestHighLevelClient
// Node: HttpHost
// Node: getHost
// Node: getPort
// Node: setRequestConfigCallback
// Node: setConnectTimeout
// Node: getConnectionTimeout
// Node: setConnectionRequestTimeout
// Node: getConnectionRequestTimeout
// Node: setSocketTimeout
// Node: getSocketTimeout
// Node: setMaxRetryTimeoutMillis
// Node: getMaxRetryTimeout
package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import io.micronaut.context.event.BeanCreatedEvent;
import io.micronaut.context.event.BeanCreatedEventListener;

import javax.inject.Singleton;

@Singleton
public class ObjectMapperBeanEventListener implements BeanCreatedEventListener<ObjectMapper> {
    @Override
    public ObjectMapper onCreated(BeanCreatedEvent<ObjectMapper> event) {
        final ObjectMapper mapper = event.getBean();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }
}


// Node: onCreated
// Node: registerModule
// Node: JavaTimeModule
// Node: disable
package pl.altkom.asc.lab.micronaut.poc.dashboard.elastic;

import org.apache.http.HttpHost;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.PolicyElasticRepository;
import pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.elastic.config.JsonConverter;

import java.math.BigDecimal;
import java.time.LocalDate;

import static org.junit.jupiter.api.Assertions.assertNotNull;


public class PolicyElasticRepositoryTest extends EmbeddedElasticTest {

    @Test
    public void canIndexPolicy() {
        PolicyDocument policyDocument = new PolicyDocument(
                "111-111",
                LocalDate.of(2018, 1, 1),
                LocalDate.of(2018, 12, 31),
                "John Smith",
                "SAFE_HOUSE",
                BigDecimal.valueOf(1000),
                "m.smith"
        );

        PolicyElasticRepository repository = new PolicyElasticRepository(
                new RestHighLevelClient(RestClient.builder(new HttpHost("localhost", el.getHttpPort(), "http"))),
                new JsonConverter(objectMapper())
        );

        repository.save(policyDocument);

        PolicyDocument saved = repository.findByNumber("111-111");

        assertNotNull(saved);
    }
}


// Node: canIndexPolicy
// Node: PolicyElasticRepository
// Node: getHttpPort
// Node: JsonConverter
// Node: objectMapper
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


// Node: ObjectMapper
package pl.altkom.asc.lab.micronaut.poc.command.bus;

import io.micronaut.context.ApplicationContext;

class QueryProvider<H extends QueryHandler<?, ?>> {

    private final ApplicationContext applicationContext;
    private final Class<H> type;

    QueryProvider(ApplicationContext applicationContext, Class<H> type) {
        this.applicationContext = applicationContext;
        this.type = type;
    }

    H get() {
        return applicationContext.getBean(type);
    }
}


package pl.altkom.asc.lab.micronaut.poc.command.bus;

import io.micronaut.context.ApplicationContext;

class CommandProvider<H extends CommandHandler<?, ?>> {

    private final ApplicationContext applicationContext;
    private final Class<H> type;

    CommandProvider(ApplicationContext applicationContext, Class<H> type) {
        this.applicationContext = applicationContext;
        this.type = type;
    }

    H get() {
        return applicationContext.getBean(type);
    }
}


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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/infrastructure/adapters/db/ElasticClientAdapter.java:ElasticClientAdapter.<init>
// Node: ElasticClientAdapter
// Node: buildClient
