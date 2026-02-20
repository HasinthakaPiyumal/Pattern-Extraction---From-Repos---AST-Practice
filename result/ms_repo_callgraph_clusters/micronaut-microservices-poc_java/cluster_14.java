// Cluster 14

// Node: Person
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.annotations;

import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;

import javax.sql.DataSource;
import java.lang.annotation.*;

@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.PACKAGE, ElementType.TYPE})
@Requires(property = "datasources.default.url")
@Requires(notEnv = Environment.TEST)
public @interface RequiresJdbc {
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/annotations/RequiresJdbc.java:RequiresJdbc.<init>
// Node: Retention
// Node: Target
// Node: Requires
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.mock;

import pl.altkom.asc.lab.micronaut.poc.policy.domain.Offer;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferRepository;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;

@Replaces(OfferRepository.class)
@Requires(env = Environment.TEST)
@Singleton
public class MockOfferRepository implements OfferRepository {

    private Map<String, Offer> map = new ConcurrentHashMap<>();

    @Transactional
    @Override
    public Offer save(Offer offer) {
        map.put(offer.getNumber(), offer);
        return offer;
    }

    @Transactional
    @Override
    public Offer getByNumber(String number) {
        return map.get(number);
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/mock/MockOfferRepository.java:MockOfferRepository.<init>
// Node: Replaces
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/mock/MockPolicyRepository.java:MockPolicyRepository.<init>
// Node: init
// Node: singletonList
// Node: PolicyVersion
package pl.altkom.asc.lab.micronaut.poc.auth;

import com.nimbusds.jwt.JWTClaimsSet;
import io.micronaut.context.annotation.Replaces;
import io.micronaut.runtime.ApplicationConfiguration;
import io.micronaut.security.authentication.UserDetails;
import io.micronaut.security.token.config.TokenConfiguration;
import io.micronaut.security.token.jwt.generator.claims.ClaimsAudienceProvider;
import io.micronaut.security.token.jwt.generator.claims.JWTClaimsSetGenerator;
import io.micronaut.security.token.jwt.generator.claims.JwtIdGenerator;

import javax.annotation.Nullable;
import javax.inject.Singleton;

@Singleton
@Replaces(bean = JWTClaimsSetGenerator.class)
public class InsuranceAgentJWTClaimsSetGenerator extends JWTClaimsSetGenerator {

    public InsuranceAgentJWTClaimsSetGenerator(TokenConfiguration tokenConfiguration,
                                               @Nullable JwtIdGenerator jwtIdGenerator,
                                               @Nullable ClaimsAudienceProvider claimsAudienceProvider,
                                               @Nullable ApplicationConfiguration applicationConfiguration) {
        super(tokenConfiguration, jwtIdGenerator, claimsAudienceProvider, applicationConfiguration);
    }

    @Override
    protected void populateWithUserDetails(JWTClaimsSet.Builder builder, UserDetails userDetails) {
        super.populateWithUserDetails(builder, userDetails);
        if (userDetails instanceof InsuranceAgentDetails) {
            builder.claim("avatar", ((InsuranceAgentDetails) userDetails).getAvatarUrl());
        }
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/auth/InsuranceAgentJWTClaimsSetGenerator.java:InsuranceAgentJWTClaimsSetGenerator.<init>
// Node: InsuranceAgentJWTClaimsSetGenerator
package pl.altkom.asc.lab.micronaut.poc.auth;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.http.HttpHeaderValues;
import io.micronaut.security.authentication.UserDetails;
import io.micronaut.security.token.jwt.render.AccessRefreshToken;
import io.micronaut.security.token.jwt.render.BearerAccessRefreshToken;
import io.micronaut.security.token.jwt.render.BearerTokenRenderer;

@Replaces(bean = BearerTokenRenderer.class)
public class CustomBearerTokenRenderer extends BearerTokenRenderer {

    private final String BEARER_TOKEN_TYPE = HttpHeaderValues.AUTHORIZATION_PREFIX_BEARER;

    @Override
    public AccessRefreshToken render(UserDetails userDetails, Integer expiresIn, String accessToken, String refreshToken) {
        if (userDetails instanceof InsuranceAgentDetails) {
            return new CustomBearerAccessRefreshToken(
                    userDetails.getUsername(),
                    userDetails.getRoles(),
                    expiresIn,
                    accessToken,
                    refreshToken,
                    BEARER_TOKEN_TYPE,
                    ((InsuranceAgentDetails) userDetails).getAvatarUrl()
            );
        }

        return new BearerAccessRefreshToken(
                userDetails.getUsername(),
                userDetails.getRoles(),
                expiresIn,
                accessToken,
                refreshToken,
                BEARER_TOKEN_TYPE);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/auth/CustomBearerTokenRenderer.java:CustomBearerTokenRenderer.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/MockPolicyAccountRepository.java:MockPolicyAccountRepository.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.mock;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db.ElasticPolicyViewRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyView;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyViewRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQuery;

import javax.inject.Singleton;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Replaces(ElasticPolicyViewRepository.class)
@Requires(env = Environment.TEST)
@Singleton
public class MockPolicyViewRepository implements PolicyViewRepository {

    private Map<String, PolicyView> policyMap = init();

    private Map<String, PolicyView> init() {
        Map<String, PolicyView> map = new LinkedHashMap<>();

        map.put("1234", new PolicyView(
                "1234",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1235", new PolicyView(
                "1235",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1236", new PolicyView("1236",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1237", new PolicyView("1237",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );

        return map;
    }

    @Override
    public Maybe<List<PolicyView>> findAll(FindPolicyQuery query) {
        return Maybe.just(new ArrayList<>(policyMap.values()));
    }

    @Override
    public void save(PolicyView policy) {
        policyMap.put(policy.getNumber(), policy);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/infrastructure/adapters/mock/MockPolicyViewRepository.java:MockPolicyViewRepository.<init>
package pl.altkom.asc.lab.micronaut.poc.documents.infrastructure.annotations;

import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;

import java.lang.annotation.*;

@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.PACKAGE, ElementType.TYPE})
@Requires(property = "datasources.default.url", notEnv = Environment.TEST)
public @interface RequiresJdbc {
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/documents-service/src/main/kotlin/pl/altkom/asc/lab/micronaut/poc/documents/infrastructure/annotations/RequiresJdbc.java:RequiresJdbc.<init>
