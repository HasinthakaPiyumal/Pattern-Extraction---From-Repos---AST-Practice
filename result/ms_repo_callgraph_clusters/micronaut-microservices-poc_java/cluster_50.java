// Cluster 50

package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.mock;

import pl.altkom.asc.lab.micronaut.poc.policy.domain.AgentRef;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Person;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Policy;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyVersion;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.vo.DateRange;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Collections;
import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;

@Replaces(PolicyRepository.class)
@Requires(env = Environment.TEST)
@Singleton
public class MockPolicyRepository implements PolicyRepository {

    private Map<String, Policy> policyMap = init();

    @Transactional
    @Override
    public Optional<Policy> findByNumber(String number) {
        return Optional.ofNullable(policyMap.get(number));
    }

    @Transactional
    @Override
    public Policy save(Policy policy) {
        policyMap.put(policy.getNumber(), policy);
        return policy;
    }

    private Map<String, Policy> init() {
        Map<String, Policy> map = new ConcurrentHashMap<>();

        map.put("1234", new Policy(1L, "1234", AgentRef.of("jimmy.solid"), new HashSet<>(
                Collections.singletonList(new PolicyVersion(2L,
                        null,
                        1L,
                        "HFI",
                        new Person("Mary", "Smith", "11111111111"),
                        "1234",
                        DateRange.between(LocalDate.of(2018, 2, 3), LocalDate.of(2019, 2, 3)),
                        DateRange.between(LocalDate.of(2018, 2, 3), LocalDate.of(2019, 2, 3)),
                        new HashSet<>(),
                        BigDecimal.TEN
                )))));
        map.put("1235", new Policy(2L, "1235", AgentRef.of("jimmy.solid"), new HashSet<>(
                Collections.singletonList(new PolicyVersion(1L,
                        null,
                        1L,
                        "HFI",
                        new Person("John", "Smith", "11111111111"),
                        "1234",
                        DateRange.between(LocalDate.of(2018, 2, 3), LocalDate.of(2019, 2, 3)),
                        DateRange.between(LocalDate.of(2018, 2, 3), LocalDate.of(2019, 2, 3)),
                        new HashSet<>(),
                        BigDecimal.TEN
                ))
        )));
        map.put("1236", new Policy(3L, "1236", AgentRef.of("admin"), new HashSet<>(
                Collections.singletonList(new PolicyVersion(3L,
                        null,
                        1L,
                        "HFI",
                        new Person("Johny", "Dip", "11111111111"),
                        "1234",
                        DateRange.between(LocalDate.of(2018, 2, 3), LocalDate.of(2019, 2, 3)),
                        DateRange.between(LocalDate.of(2018, 2, 3), LocalDate.of(2019, 2, 3)),
                        new HashSet<>(),
                        BigDecimal.TEN
                ))
        )));

        return map;
    }
}


// Node: ofNullable
// Node: fromPublisher
package pl.altkom.asc.lab.micronaut.poc.product.service.infrastructure.adapters.db;

import com.mongodb.client.model.Filters;
import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoCollection;
import io.reactivex.Flowable;
import io.reactivex.Maybe;
import io.reactivex.Single;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.Product;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.Products;

import javax.inject.Singleton;
import java.util.List;


@Singleton
@RequiredArgsConstructor
public class ProductsRepository implements Products {

    private final MongoClient mongoClient;

    @Override
    public Single<Product> add(Product product) {
        return Single.fromPublisher(
                getCollection().insertOne(product)
        ).map(success -> product);
    }

    @Override
    public Single<List<Product>> findAll() {
        return Flowable.fromPublisher(
                getCollection().find()
        ).toList();
    }

    @Override
    public Maybe<Product> findOne(String productCode) {
        return Flowable.fromPublisher(
                getCollection()
                        .find(Filters.eq("code", productCode))
                        .limit(1)
        ).firstElement();
    }

    private MongoCollection<Product> getCollection() {
        return mongoClient
                .getDatabase("products-demo")
                .getCollection("product", Product.class);
    }
}


// Node: getCollection
// Node: insertOne
// Node: findAll
// Node: findOne
// Node: eq
// Node: limit
// Node: firstElement
// Node: getDatabase
package pl.altkom.asc.lab.micronaut.poc.product.service.infrastructure.adapters.web;

import io.micronaut.http.annotation.Controller;
import io.reactivex.Maybe;
import io.reactivex.Single;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductOperations;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.Products;

import java.util.List;

@Controller("/products")
@RequiredArgsConstructor
public class ProductsController implements ProductOperations {

    private final Products products;

    @Override
    public Single<List<ProductDto>> getAll() {
        return products.findAll().map(ProductsAssembler::map);
    }

    @Override
    public Maybe<ProductDto> get(String productCode) {
        return products.findOne(productCode).map(ProductsAssembler::map);
    }
}


package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import io.reactivex.Maybe;
import io.reactivex.Single;

import java.util.List;

public interface Products {

    Single<Product> add(Product product);

    Single<List<Product>> findAll();

    Maybe<Product> findOne(String productCode);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/domain/Products.java:Products.<init>
// Node: findByPolicyNumber
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import io.micronaut.data.annotation.Query;
import io.micronaut.data.annotation.Repository;
import io.micronaut.data.jpa.annotation.EntityGraph;
import io.micronaut.data.repository.GenericRepository;
import pl.altkom.asc.lab.micronaut.poc.payment.service.api.v1.PolicyAccountDto;

import java.util.Collection;
import java.util.Optional;

@Repository
public interface PolicyAccountRepository extends GenericRepository<PolicyAccount, Long> {

    @EntityGraph(attributePaths = {"entries"})
    Optional<PolicyAccount> findByPolicyNumber(String policyNumber);

    @EntityGraph(attributePaths = {"entries"})
    @Query("FROM PolicyAccount p WHERE p.policyAccountNumber = :policyAccountNumber")
    Optional<PolicyAccount> findByPolicyAccountNumber(String policyAccountNumber);

    PolicyAccount save(PolicyAccount policyAccount);

    Collection<PolicyAccountDto> findAll();
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/PolicyAccountRepository.java:PolicyAccountRepository.<init>
// Node: EntityGraph
// Node: Query
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


package pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel;

import io.reactivex.Maybe;
import java.util.List;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQuery;

public interface PolicyViewRepository {

    Maybe<List<PolicyView>> findAll(FindPolicyQuery query);

    void save(PolicyView view);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/readmodel/PolicyViewRepository.java:PolicyViewRepository.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.queries.findpolicy;

import io.reactivex.Maybe;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.QueryHandler;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQuery;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyViewRepository;

import javax.inject.Singleton;

@Singleton
@RequiredArgsConstructor
public class FindPolicyQueryHandler implements QueryHandler<Maybe<FindPolicyQueryResult>, FindPolicyQuery> {

    private final PolicyViewRepository policyViewRepository;

    @Override
    public Maybe<FindPolicyQueryResult> handle(FindPolicyQuery query) {
        return policyViewRepository
                .findAll(query)
                .map(PolicyQueryResultAssembler::constructResult);
    }

}


