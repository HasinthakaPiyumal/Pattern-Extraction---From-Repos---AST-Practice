// Cluster 15

// Node: isExpired
// Node: getPolicyHolder
// Node: save
// Node: getNumber
// Node: createEvent
package pl.altkom.asc.lab.micronaut.poc.policy.commands;

import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandHandler;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.AgentRef;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Offer;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Person;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Policy;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyFactory;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.kafka.EventPublisher;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.dto.PolicyDto;

import java.time.LocalDate;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class CreatePolicyHandler implements CommandHandler<CreatePolicyResult, CreatePolicyCommand> {

    private final PolicyRepository policyRepository;
    private final OfferRepository offerRepository;
    private final PolicyFactory policyFactory = new PolicyFactory();
    private final EventPublisher eventPublisher;

    @Transactional
    @Override
    public CreatePolicyResult handle(CreatePolicyCommand cmd) {
        //get offer
        Offer offer = offerRepository.getByNumber(cmd.getOfferNumber());

        //if offer not expired and not already converted
        if (offer.isExpired(LocalDate.now())) {
            throw new RuntimeException("Offer has expired");
        }

        //create policy from offer
        Person policyHolder = new Person(cmd.getPolicyHolder().getFirstName(), cmd.getPolicyHolder().getLastName(), cmd.getPolicyHolder().getTaxId());
        AgentRef agent = AgentRef.of(cmd.getAgentLogin());
        Policy policy = policyFactory.fromOffer(offer, policyHolder, agent);

        //save policy and update offer
        policyRepository.save(policy);

        //publish events
        eventPublisher.policyRegisteredEvent(policy.getNumber(), createEvent(policy));

        return new CreatePolicyResult(policy.getNumber());
    }

    private PolicyRegisteredEvent createEvent(Policy policy) {
        return new PolicyRegisteredEvent(
                new PolicyDto(
                        policy.getNumber(),
                        policy.versions().lastVersion().getVersionValidityPeriod().getFrom(),
                        policy.versions().lastVersion().getVersionValidityPeriod().getTo(),
                        policy.versions().lastVersion().getPolicyHolder().getFullName(),
                        policy.versions().lastVersion().getProductCode(),
                        policy.versions().lastVersion().getTotalPremiumAmount(),
                        null
                )
        );
    }
}


// Node: PolicyRegisteredEvent
// Node: PolicyDto
// Node: versions
// Node: lastVersion
// Node: getVersionValidityPeriod
// Node: getFrom
// Node: getTo
// Node: getFullName
// Node: getTotalPremiumAmount
package pl.altkom.asc.lab.micronaut.poc.policy.commands;

import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandHandler;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Policy;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.kafka.EventPublisher;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyTerminatedEvent;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.dto.PolicyDto;
import pl.altkom.asc.lab.micronaut.poc.policy.shared.exceptions.BusinessException;

import javax.inject.Singleton;
import java.time.LocalDate;
import java.util.Optional;

@Singleton
@RequiredArgsConstructor
public class TerminatePolicyHandler implements CommandHandler<TerminatePolicyResult, TerminatePolicyCommand> {

    private final PolicyRepository policyRepository;
    private final EventPublisher eventPublisher;

    @Override
    public TerminatePolicyResult handle(TerminatePolicyCommand cmd) {
        Optional<Policy> policyOpt = policyRepository.findByNumber(cmd.getPolicyNumber());
        if (!policyOpt.isPresent())
            throw new BusinessException("POLICY NOT FOUND");

        Policy policy = policyOpt.get();
        policy.terminate(LocalDate.now());

        policyRepository.save(policy);

        eventPublisher.policyTerminatedEvent(policy.getNumber(), createEvent(policy));

        return TerminatePolicyResult.success(policy.getNumber());
    }

    private PolicyTerminatedEvent createEvent(Policy policy) {
        return new PolicyTerminatedEvent(new PolicyDto(
                policy.getNumber(),
                policy.versions().lastVersion().getVersionValidityPeriod().getFrom(),
                policy.versions().lastVersion().getVersionValidityPeriod().getTo(),
                policy.versions().lastVersion().getPolicyHolder().getFullName(),
                policy.versions().lastVersion().getProductCode(),
                policy.versions().lastVersion().getTotalPremiumAmount(),
                null
        ));
    }
}


// Node: findByNumber
// Node: isPresent
// Node: BusinessException
// Node: PolicyTerminatedEvent
package pl.altkom.asc.lab.micronaut.poc.policy.shared.exceptions;

import lombok.Getter;

public class BusinessException extends RuntimeException {
    protected static final Object[] EMPTY_ARGS = new Object[0];

    @Getter
    private String code = null;
    @Getter
    private Object[] args = EMPTY_ARGS;

    public BusinessException(String code) {
        super(code);
        this.code = code;
        this.args = EMPTY_ARGS;
    }

    public BusinessException(String code, String message) {
        super(message);
        this.code = code;
        this.args = EMPTY_ARGS;
    }

    public BusinessException(String code, String message, Object ... args) {
        super(message);
        this.code = code;
        this.args = args;
    }

    public BusinessException(String code, Object ... args) {
        super(code);
        this.code = code;
        this.args = args;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/shared/exceptions/BusinessException.java:BusinessException.<init>
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


// Node: put
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


package pl.altkom.asc.lab.micronaut.poc.policy.queries.getpolicydetails;

import pl.altkom.asc.lab.micronaut.poc.command.bus.QueryHandler;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Policy;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQuery;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;
import pl.altkom.asc.lab.micronaut.poc.policy.shared.exceptions.BusinessException;

import java.util.Optional;

import javax.inject.Singleton;

import io.micronaut.transaction.annotation.ReadOnly;
import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class GetPolicyDetailsQueryHandler implements QueryHandler<GetPolicyDetailsQueryResult, GetPolicyDetailsQuery> {

    private final PolicyRepository policyRepository;

    @ReadOnly
    @Override
    public GetPolicyDetailsQueryResult handle(GetPolicyDetailsQuery query) {
        Optional<Policy> policyOpt = policyRepository.findByNumber(query.getNumber());
        if (!policyOpt.isPresent())
            throw new BusinessException("POLICY NOT FOUND");

        return new GetPolicyDetailsQueryResult(PolicyDetailsDtoAssembler.map(policyOpt.get()));
    }
}


// Node: map
package pl.altkom.asc.lab.micronaut.poc.policy.queries.getpolicydetails;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Cover;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Policy;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyVersion;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.dto.PolicyDetailsDto;

import java.util.stream.Collectors;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
final class PolicyDetailsDtoAssembler {

    static PolicyDetailsDto map(Policy policy) {
        PolicyVersion policyVersion = policy.versions().lastVersion();

        return new PolicyDetailsDto(
                policy.getNumber(),
                policyVersion.getVersionValidityPeriod().getFrom(),
                policyVersion.getVersionValidityPeriod().getTo(),
                policyVersion.getPolicyHolder().getFullName(),
                policyVersion.getTotalPremiumAmount(),
                policyVersion.getProductCode(),
                policyVersion.getAccountNumber(),
                policyVersion.getCovers().stream()
                        .map(Cover::toString)
                        .sorted()
                        .collect(Collectors.toSet())
        );
    }
}


// Node: getCovers
// Node: stream
// Node: sorted
// Node: collect
// Node: toSet
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import lombok.*;

import javax.persistence.Embeddable;

@Embeddable
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Getter
@EqualsAndHashCode
public class PolicyVersionRef {

    private String policyNumber;
    private Long versionNumber;

    static PolicyVersionRef of(PolicyVersion policyVersion) {
        return new PolicyVersionRef(policyVersion.getPolicy().getNumber(), policyVersion.getVersionNumber());
    }

    public PolicyRef policyRef() {
        return new PolicyRef(policyNumber);
    }
}


// Node: PolicyVersionRef
// Node: getPolicy
// Node: getVersionNumber
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.vo.DateRange;
import pl.altkom.asc.lab.micronaut.poc.policy.shared.exceptions.BusinessException;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@RequiredArgsConstructor
public class PolicyVersionCollection {

    private final Policy policy;
    private final Set<PolicyVersion> versions;

    public PolicyVersion withNumber(Long number) {
        return versions
                .stream()
                .filter(v -> v.getVersionNumber().equals(number))
                .findFirst()
                .orElseThrow(() -> new BusinessException("POLICY NOT FOUND"));
    }

    public PolicyVersion lastVersion() {
        return versions
                .stream()
                .min(Comparators.BY_VERSION_NUMBER_DESC)
                .orElseThrow(() -> new BusinessException("POLICY NOT FOUND"));
    }


    PolicyVersion add(
            Long versionNumber,
            String productCode,
            Person policyHolder,
            String accountNumber,
            DateRange coverPeriod,
            DateRange versionPeriod,
            BigDecimal totalPremiumAmount,
            Map<String, BigDecimal> coversPrices) {

        if (hasVersion(versionNumber)) {
            throw new BusinessException("POLVEREXISTS", new Object[]{policy.getNumber(), versionNumber});
        }

        PolicyVersion ver = new PolicyVersion(
                null,
                policy,
                versionNumber,
                productCode,
                policyHolder,
                accountNumber,
                coverPeriod,
                versionPeriod,
                new HashSet<>(),
                totalPremiumAmount
        );
        versions.add(ver);
        coversPrices.forEach((key, value) -> ver.covers().add(key, value));

        return ver;
    }

    void addTerminalVersion(LocalDate terminationDate) {
        PolicyVersion baseVersion = lastVersion();

        DateRange newCoverPeriod = baseVersion.getCoverPeriod().endOn(terminationDate);

        DateRange newVersionPeriod = DateRange.between(
                terminationDate.plusDays(1),
                baseVersion.getVersionValidityPeriod().getTo());

        BigDecimal correctionFactor = newCoverPeriod.days().divide(
                baseVersion.getCoverPeriod().days(),
                20,
                RoundingMode.HALF_UP);
        Map<String, BigDecimal> correctedCovers = baseVersion
                .covers()
                .correct(correctionFactor);

        add(
                baseVersion.getVersionNumber()+1L,
                baseVersion.getProductCode(),
                baseVersion.getPolicyHolder(),
                baseVersion.getAccountNumber(),
                newCoverPeriod,
                newVersionPeriod,
                correctedCovers.values().stream().reduce(BigDecimal.ZERO, BigDecimal::add),
                correctedCovers);
    }

    private boolean hasVersion(Long versionNumber) {
        return versions.stream().anyMatch(v -> v.getVersionNumber().equals(versionNumber));
    }

    static class Comparators {
        static final Comparator<PolicyVersion> BY_VERSION_NUMBER_ASC = Comparator.comparing(PolicyVersion::getVersionNumber);
        static final Comparator<PolicyVersion> BY_VERSION_NUMBER_DESC = (v1, v2) -> v2.getVersionNumber().compareTo(v1.getVersionNumber());
    }
}


// Node: withNumber
// Node: filter
// Node: equals
// Node: findFirst
// Node: orElseThrow
// Node: hasVersion
// Node: addTerminalVersion
// Node: getCoverPeriod
// Node: endOn
// Node: plusDays
// Node: days
// Node: correct
// Node: values
// Node: reduce
// Node: anyMatch
// Node: comparing
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Map;

@Entity
@Getter
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Offer {
    @Id
    @GeneratedValue
    private Long id;

    @Column(name = "number")
    private String number;

    @Column(name = "product_code")
    private String productCode;

    @Column(name = "policy_from")
    private LocalDate policyFrom;

    @Column(name = "policy_to")
    private LocalDate policyTo;

    @ElementCollection
    @CollectionTable(name = "offer_answers", joinColumns = @JoinColumn(name = "offer_id"))
    @MapKeyColumn(name = "question_code")
    @Column(name = "answer")
    private Map<String, String> answers;

    @Column(name = "total_price")
    private BigDecimal totalPrice;

    @ElementCollection
    @CollectionTable(name = "offer_cover", joinColumns = @JoinColumn(name = "offer_id"))
    @MapKeyColumn(name = "cover_code")
    @Column(name = "price")
    private Map<String, BigDecimal> coversPrices;

    @Enumerated(EnumType.STRING)
    @Column(name = "status")
    private OfferStatus status;
    
    @Column(name = "creation_date")
    private LocalDate creationDate;

    /*
    Offers are valid only for 30 days
    */
    public boolean isExpired(LocalDate theDate) {
        return creationDate.plusDays(30).isBefore(theDate);
    }
}


// Node: isBefore
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import lombok.*;

import javax.persistence.Embeddable;

@Embeddable
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
@Getter
public class Person {
    private String firstName;
    private String lastName;
    private String pesel;

    public String getFullName() {
        return firstName + " " + lastName;
    }
}


package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import io.micronaut.data.annotation.Repository;
import io.micronaut.data.repository.GenericRepository;

import java.util.Optional;

@Repository
public interface PolicyRepository extends GenericRepository<Policy, Long> {
    Optional<Policy> findByNumber(String number);

    Policy save(Policy policy);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/PolicyRepository.java:PolicyRepository.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import lombok.RequiredArgsConstructor;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

@RequiredArgsConstructor
public class CoverCollection {
    private final PolicyVersion policyVersion;
    private final Set<Cover> covers;

    Cover add(String code, BigDecimal price) {
        Cover cover = new Cover(policyVersion, code, price);
        covers.add(cover);
        return cover;
    }

    public Map<String, BigDecimal> correct(BigDecimal correctionFactor) {
        Map<String,BigDecimal> correctedValues = new HashMap<>();
        covers.forEach(c -> correctedValues.put(
                c.getCode(),
                c.getPrice().multiply(correctionFactor).setScale(2, RoundingMode.HALF_UP)));
        return correctedValues;
    }
}


// Node: getPrice
// Node: multiply
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.vo.DateRange;
import pl.altkom.asc.lab.micronaut.poc.policy.shared.exceptions.BusinessException;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

@Entity
@Getter
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Policy {

    @Id
    @GeneratedValue
    private Long id;

    @Column(name = "number")
    private String number;

    @Embedded
    private AgentRef agent;

    @OneToMany(mappedBy = "policy", cascade = CascadeType.ALL)
    private Set<PolicyVersion> versions;

    public Policy(String number, AgentRef agent) {
        this.number = number;
        this.versions = new HashSet<>();
        this.agent = agent;
    }

    public PolicyVersionCollection versions() {
        return new PolicyVersionCollection(this, versions);
    }

    public void terminate(LocalDate terminationDate) {
        PolicyVersion lastVersion = versions().lastVersion();

        if (!lastVersion.getCoverPeriod().contains(terminationDate))
        {
            throw new BusinessException("TERMINATION_DATE_OUTSIDE_VALIDITY_PERIOD");
        }


        versions().addTerminalVersion(terminationDate);
    }

    void addVersion(Offer offer, Person policyHolder) {
        versions().add(
                1L,
                offer.getProductCode(),
                policyHolder,
                UUID.randomUUID().toString(),
                DateRange.between(offer.getPolicyFrom(), offer.getPolicyTo()),
                DateRange.between(offer.getPolicyFrom(), offer.getPolicyTo()),
                offer.getTotalPrice(),
                offer.getCoversPrices()
        );
    }
}


// Node: PolicyVersionCollection
// Node: contains
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


// Node: isAfter
package pl.altkom.asc.lab.micronaut.poc.policy.domain.vo;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.Embeddable;
import java.math.BigDecimal;

@Embeddable
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Getter
public class Quantity {

    private BigDecimal value;

    public static Quantity of(BigDecimal value) {
        return new Quantity(value);
    }

    public static Quantity zero() {
        return new Quantity(BigDecimal.ZERO);
    }

    public MonetaryAmount multiply(MonetaryAmount amount) {
        return amount.multiply(value);
    }

    public static Quantity min(Quantity q1, Quantity q2) {
        return q1.value.compareTo(q2.value) >= 1 ? q2 : q1;
    }

    public static Quantity max(Quantity q1, Quantity q2) {
        return q1.value.compareTo(q2.value) >= 1 ? q1 : q2;
    }

    public Quantity add(Quantity qt){
        return new Quantity(qt.value.add(value));
    }

    public Quantity subtract(Quantity qt) { return new Quantity(value.subtract(qt.value)); }
}


package pl.altkom.asc.lab.micronaut.poc.auth;

import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.UUID;

import io.micronaut.data.annotation.Id;
import io.micronaut.data.annotation.MappedEntity;



@MappedEntity
record InsuranceAgent(
    @Id UUID id,
    String login,
    String password,
    String avatar,
    String availableProducts) {

    InsuranceAgent(UUID id,String login, String password, String avatar, List<String> availableProducts) {
        this(id,login,password,avatar,String.join(";",availableProducts));
    }
    
    boolean passwordMatches(String passwordToTest) {
        return this.password.equals(passwordToTest);
    }

    public Collection<String> availableProductCodes() {
        return Arrays.asList(availableProducts.split(";"));
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/auth/InsuranceAgent.java:InsuranceAgent.<init>
// Node: InsuranceAgent
// Node: join
package pl.altkom.asc.lab.micronaut.poc.auth;

import java.util.Arrays;
import java.util.UUID;

import javax.inject.Singleton;

import io.micronaut.context.event.ApplicationEventListener;
import io.micronaut.runtime.server.event.ServerStartupEvent;
import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class DataLoader implements ApplicationEventListener<ServerStartupEvent> {
    private final InsuranceAgentsRepository insuranceAgentsRepository;

    @Override
    public void onApplicationEvent(ServerStartupEvent event) {
        if (!insuranceAgentsRepository.findByLogin("admin").isPresent()) {
            insuranceAgentsRepository.save(new InsuranceAgent(UUID.randomUUID(), "admin", "admin", "static/avatars/admin.png", Arrays.asList("TRI", "HSI")));
        }

        if (!insuranceAgentsRepository.findByLogin("jimmy.solid").isPresent()) {
            insuranceAgentsRepository.save(new InsuranceAgent(UUID.randomUUID(), "jimmy.solid", "secret", "static/avatars/jimmy_solid.png", Arrays.asList("TRI", "HSI", "FAI", "CAR")));
        }

        if (!insuranceAgentsRepository.findByLogin("danny.solid").isPresent()) {
            insuranceAgentsRepository.save(new InsuranceAgent(UUID.randomUUID(),"danny.solid", "secret", "static/avatars/danny_solid.png", Arrays.asList("TRI", "HSI")));
        }

        if (!insuranceAgentsRepository.findByLogin("agent1").isPresent()) {
            insuranceAgentsRepository.save(new InsuranceAgent(UUID.randomUUID(),"agent1", "agent1", "static/avatars/agent1.png", Arrays.asList("TRI", "HSI")));
        }
    }
}


// Node: onApplicationEvent
// Node: Calculation
package pl.altkom.asc.lab.micronaut.poc.pricing.commands;

import pl.altkom.asc.lab.micronaut.poc.pricing.domain.Calculation;
import pl.altkom.asc.lab.micronaut.poc.pricing.domain.Tariff;
import pl.altkom.asc.lab.micronaut.poc.pricing.domain.Tariffs;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.QuestionAnswer;

import java.util.Map;
import java.util.stream.Collectors;

import javax.inject.Singleton;

import io.micronaut.transaction.annotation.ReadOnly;
import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class CalculatePriceHandler {

    private final Tariffs tariffs;

    @ReadOnly
    public CalculatePriceResult handle(CalculatePriceCommand calculatePriceCommand) {
        Tariff tariff = tariffs.getByCode(calculatePriceCommand.getProductCode());
        Calculation calculation = tariff.calculatePrice(toCalculation(calculatePriceCommand));

        return resultFromCalculation(calculation);
    }

    private Calculation toCalculation(CalculatePriceCommand calculatePriceCommand) {
        return new Calculation(
                calculatePriceCommand.getProductCode(),
                calculatePriceCommand.getPolicyFrom(),
                calculatePriceCommand.getPolicyTo(),
                calculatePriceCommand.getSelectedCovers(),
                calculatePriceCommand.getAnswers().stream()
                        .collect(Collectors.toMap(QuestionAnswer::getQuestionCode, QuestionAnswer::getAnswer))
        );
    }

    private CalculatePriceResult resultFromCalculation(Calculation calculation) {
        return new CalculatePriceResult(
                calculation.getTotalPremium(),
                calculation.getCovers().entrySet().stream()
                        .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().getPrice()))
        );
    }
}


// Node: getTotalPremium
// Node: entrySet
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import java.math.BigDecimal;
import java.util.List;
import java.util.stream.Collectors;

public class BasePremiumCalculationRuleList {

    private List<BasePremiumCalculationRule> basePriceCalculationRules;

    BasePremiumCalculationRuleList(List<BasePremiumCalculationRule> basePriceCalculationRules) {
        this.basePriceCalculationRules = basePriceCalculationRules;
    }

    public void addBasePriceRule(String coverCode, String applyIfFormula, String basePriceFormula) {
        BasePremiumCalculationRule rule = new BasePremiumCalculationRule(coverCode, applyIfFormula, basePriceFormula);
        basePriceCalculationRules.add(rule);
    }


    BigDecimal calculateBasePriceFor(Cover cover, Calculation calculation) {
        return getRulesFor(cover.getCode())
                .stream()
                .filter(r -> r.applies(calculation))
                .map(r -> r.calculateBasePrice(calculation))
                .findFirst()
                .orElse(null);
    }

    private List<BasePremiumCalculationRule> getRulesFor(String coverCode) {
        return basePriceCalculationRules
                .stream()
                .filter(r -> r.getCoverCode().equals(coverCode))
                .collect(Collectors.toList());
    }
}


// Node: calculateBasePriceFor
// Node: getRulesFor
// Node: calculateBasePrice
// Node: orElse
// Node: getCoverCode
// Node: toList
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import java.math.BigDecimal;
import java.util.List;

public class DiscountMarkupRuleList {

    private Tariff tariff;
    private List<DiscountMarkupRule> discountMarkupRules;

    DiscountMarkupRuleList(Tariff tariff, List<DiscountMarkupRule> discountMarkupRules) {
        this.tariff = tariff;
        this.discountMarkupRules = discountMarkupRules;
    }

    public void addPercentMarkup(String applyIfFormula, BigDecimal markup){
        discountMarkupRules.add(new PercentMarkupRule(tariff, applyIfFormula, markup));
    }

    void apply(Calculation calculation) {
        discountMarkupRules
                .stream()
                .filter(r -> r.applies(calculation))
                .forEach(r -> r.apply(calculation));
    }
}


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


package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "tariff")
@NoArgsConstructor
@Getter
public class Tariff {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @Column(name = "code")
    private String code;

    @ElementCollection
    @CollectionTable(name = "base_price_rules", joinColumns = @JoinColumn(name = "tariff_id"))
    private List<BasePremiumCalculationRule> basePriceCalculationRules;

    @OneToMany(mappedBy = "tariff", cascade = CascadeType.ALL, fetch = FetchType.EAGER)
    private List<DiscountMarkupRule> discountMarkupRules;
    
    public Tariff( String code) {
        this.code = code;
        this.basePriceCalculationRules = new ArrayList<>();
        this.discountMarkupRules = new ArrayList<>();
    }

    public BasePremiumCalculationRuleList rules() {
        return new BasePremiumCalculationRuleList(basePriceCalculationRules);
    }

    public DiscountMarkupRuleList discountMarkupRules() {
        return new DiscountMarkupRuleList(this, discountMarkupRules);
    }

    public Calculation calculatePrice(Calculation calculation) {
        calcBasePrices(calculation);
        applyDiscounts(calculation);
        buildResponse(calculation);

        return calculation;
    }

    private void calcBasePrices(Calculation calculation) {
        for (Cover c : calculation.getCovers().values()) {
            c.setPrice(rules().calculateBasePriceFor(c, calculation));
        }
    }

    private void applyDiscounts(Calculation calculation) {
        discountMarkupRules().apply(calculation);
    }

    private void buildResponse(Calculation calculation) {
        calculation.updateTotal();
    }

}


// Node: setPrice
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import java.math.BigDecimal;
import java.math.RoundingMode;

import javax.persistence.DiscriminatorValue;
import javax.persistence.Entity;

import lombok.NoArgsConstructor;

@Entity
@DiscriminatorValue("perc_markup")
@NoArgsConstructor
public class PercentMarkupRule extends DiscountMarkupRule {

    PercentMarkupRule(Tariff tariff, String applyIfFormula, BigDecimal paramValue) {
        this.tariff = tariff;
        this.applyIfFormula = applyIfFormula;
        this.paramValue = paramValue;
    }

    @Override
    public Calculation apply(Calculation calculation) {
        for (Cover cover : calculation.getCovers().values()) {
            cover.setPrice(cover.getPrice()
                    .multiply(paramValue)
                    .setScale(2, RoundingMode.HALF_UP)
            );
        }
        return calculation;
    }


}


// Node: travel
// Node: house
// Node: farm
// Node: car
package pl.altkom.asc.lab.micronaut.poc.pricing.init;

import pl.altkom.asc.lab.micronaut.poc.pricing.domain.Tariffs;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import io.micronaut.context.event.ApplicationEventListener;
import io.micronaut.runtime.server.event.ServerStartupEvent;
import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class DataLoader implements ApplicationEventListener<ServerStartupEvent> {

    private final Tariffs tariffsDb;

    @Transactional
    @Override
    public void onApplicationEvent(ServerStartupEvent event) {
        if (!tariffsDb.findByCode("HSI").isPresent()) {
            tariffsDb.save(DemoTariffsFactory.house());
        }
        
        if (!tariffsDb.findByCode("TRI").isPresent()) {
            tariffsDb.save(DemoTariffsFactory.travel());
        }

        if (!tariffsDb.findByCode("FAI").isPresent()) {
            tariffsDb.save(DemoTariffsFactory.farm());
        }

        if (!tariffsDb.findByCode("CAR").isPresent()) {
            tariffsDb.save(DemoTariffsFactory.car());
        }
    }
}


package pl.altkom.asc.lab.micronaut.poc.pricing.domain;


import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;


public class TariffTest {
    @Test
    public void canCalculateTravelPolicyPrice() {
        Map<String, Object> subject = new HashMap<>();
        subject.put("NUM_OF_ADULTS", new BigDecimal("1"));
        subject.put("NUM_OF_CHILDREN", new BigDecimal("1"));
        subject.put("DESTINATION", "EUR");

        Calculation calculation = new Calculation(
                "TRI",
                LocalDate.of(2017, 4, 16),
                LocalDate.of(2017, 4, 20),
                Arrays.asList("C1", "C2", "C3"),
                subject);

        Tariff tariff = TariffsFactory.travel();

        calculation = tariff.calculatePrice(calculation);

        assertEquals(new BigDecimal("98.00"), calculation.getTotalPremium(), "Total premium should be 78");
        assertEquals(new BigDecimal("26.00"), calculation.getCovers().get("C1").getPrice(), "C1 premium should be 26");
        assertEquals(new BigDecimal("52.00"), calculation.getCovers().get("C2").getPrice(), "C2 should be 52");
        assertEquals(new BigDecimal("20.00"), calculation.getCovers().get("C3").getPrice(),"C3 should be 20");
    }

    @Test
    public void canCalculateHousePolicyPrice() {
        Map<String, Object> subject = new HashMap<>();
        subject.put("TYP", "APT");
        subject.put("AREA", new BigDecimal("95"));
        subject.put("NUM_OF_CLAIM", 1);
        subject.put("FLOOD", "NO");

        Calculation calculation = new Calculation(
                "HSI",
                LocalDate.of(2017, 4, 16),
                LocalDate.of(2018, 4, 15),
                Arrays.asList("C1", "C2", "C3"),
                subject);

        Tariff tariff = TariffsFactory.house();

        calculation = tariff.calculatePrice(calculation);

        assertEquals(new BigDecimal("172.50"), calculation.getTotalPremium(),"Total premium should be 172.50");
        assertEquals(new BigDecimal("118.75"), calculation.getCovers().get("C1").getPrice(),"C1 premium should be 118.75");
        assertEquals(new BigDecimal("23.75"), calculation.getCovers().get("C2").getPrice(),"C2 should be 23.75");
        assertEquals(new BigDecimal("30"), calculation.getCovers().get("C3").getPrice(),"C3 should be 30");
    }

    @Test
    public void canCalculateCarPolicyPrice() {
        Map<String, Object> subject = new HashMap<>();
        subject.put("NUM_OF_CLAIM", 1);

        Calculation calculation = new Calculation(
                "CAR",
                LocalDate.of(2017, 4, 16),
                LocalDate.of(2018, 4, 15),
                Collections.singletonList("C1"),
                subject);

        Tariff tariff = TariffsFactory.car();

        calculation = tariff.calculatePrice(calculation);

        assertEquals(new BigDecimal("100"), calculation.getTotalPremium(),"Total premium should be 100");
        assertEquals(new BigDecimal("100"), calculation.getCovers().get("C1").getPrice(),"C1 premium should be 100");
    }
}


// Node: canCalculateCarPolicyPrice
package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;

@KafkaListener(clientId = "policy-registered-dashboard-listener", offsetReset = OffsetReset.EARLIEST)
@RequiredArgsConstructor
public class PolicyRegisteredListener {

    private final PolicyRepository policyRepository;

    @Topic("policy-registered")
    void onPolicyRegistered(PolicyRegisteredEvent event) {
        policyRepository.save(new PolicyDocument(
                event.getPolicy().getNumber(),
                event.getPolicy().getFrom(),
                event.getPolicy().getTo(),
                event.getPolicy().getPolicyHolder(),
                event.getPolicy().getProductCode(),
                event.getPolicy().getTotalPremium(),
                event.getPolicy().getAgentLogin()
        ));
    }
}


// Node: onPolicyRegistered
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


// Node: generate
package pl.altkom.asc.lab.micronaut.poc.product.service.infrastructure.adapters.web;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.CoverDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.questions.*;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
final class ProductsAssembler {

    static List<ProductDto> map(List<Product> products) {
        return products.stream()
                .map(ProductsAssembler::map)
                .collect(Collectors.toList());
    }

    static ProductDto map(Product product) {
        return ProductDto.builder()
                .code(product.getCode())
                .name(product.getName())
                .image(product.getImage())
                .description(product.getDescription())
                .covers(mapCovers(product))
                .questions(mapQuestions(product))
                .maxNumberOfInsured(product.getMaxNumberOfInsured())
                .icon(product.getIcon())
                .build();
    }

    private static List<QuestionDto> mapQuestions(Product product) {
        return product.getQuestions().stream()
                .map(ProductsAssembler::mapQuestion)
                .collect(Collectors.toList());
    }

    private static List<CoverDto> mapCovers(Product product) {
        return product.getCovers().stream()
                .map(ProductsAssembler::mapCover)
                .collect(Collectors.toList());
    }

    private static CoverDto mapCover(Cover cover) {
        return new CoverDto(
                cover.getCode(),
                cover.getName(),
                cover.getDescription(),
                cover.isOptional(),
                cover.getSumInsured()
        );
    }

    private static QuestionDto mapQuestion(Question question) {
        QuestionDto dto = mapToNumericIfFit(question);

        dto = dto == null ? mapToDateIfFit(question) : dto;
        dto = dto == null ? mapToChoiceIfFit(question) : dto;

        return dto;
    }

    private static QuestionDto mapToChoiceIfFit(Question question) {
        if (!(question instanceof ChoiceQuestion))
            return null;

        return new ChoiceQuestionDto(question.getCode(), question.getIndex(), question.getText(), mapChoices(question));
    }

    private static List<ChoiceDto> mapChoices(Question question) {
        List<Choice> choices = ((ChoiceQuestion) question).getChoices();

        if (choices == null)
            return new ArrayList<>();

        return choices.stream()
                .map(x -> new ChoiceDto(x.getCode(), x.getLabel()))
                .collect(Collectors.toList());
    }

    private static QuestionDto mapToDateIfFit(Question question) {
        if (!(question instanceof DateQuestion))
            return null;

        return new DateQuestionDto(question.getCode(), question.getIndex(), question.getText());
    }

    private static QuestionDto mapToNumericIfFit(Question question) {
        if (!(question instanceof NumericQuestion))
            return null;

        return new NumericQuestionDto(question.getCode(), question.getIndex(), question.getText());
    }

}


// Node: getQuestions
// Node: getChoices
// Node: ChoiceDto
// Node: getLabel
package pl.altkom.asc.lab.micronaut.poc.product.service.init;

import io.micronaut.context.event.ApplicationEventListener;
import io.micronaut.runtime.server.event.ServerStartupEvent;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.Product;
import pl.altkom.asc.lab.micronaut.poc.product.service.infrastructure.adapters.db.ProductsRepository;

import javax.inject.Singleton;
import java.util.List;

@Singleton
@RequiredArgsConstructor
public class DataLoader implements ApplicationEventListener<ServerStartupEvent> {

    private final ProductsRepository productsRepository;

    @Override
    public void onApplicationEvent(ServerStartupEvent serverStartupEvent) {
        List<Product> allProducts = productsRepository.findAll().blockingGet();

        if (allProducts.stream().noneMatch(p -> p.getCode().equals("CAR"))) {
            productsRepository.add(DemoProductsFactory.car()).blockingGet();
        }

        if (allProducts.stream().noneMatch(p -> p.getCode().equals("FAI"))) {
            productsRepository.add(DemoProductsFactory.farm()).blockingGet();
        }

        if (allProducts.stream().noneMatch(p -> p.getCode().equals("HSI"))) {
            productsRepository.add(DemoProductsFactory.house()).blockingGet();
        }

        if (allProducts.stream().noneMatch(p -> p.getCode().equals("TRI"))) {
            productsRepository.add(DemoProductsFactory.travel()).blockingGet();
        }
    }
}


// Node: noneMatch
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

public interface PolicyAccountNumberGenerator {
    String generate();
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/PolicyAccountNumberGenerator.java:PolicyAccountNumberGenerator.<init>
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.dto.PolicyDto;

import java.util.Optional;

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@KafkaListener(offsetReset = OffsetReset.EARLIEST)
public class PolicyRegisteredListener {

    private final PolicyAccountRepository policyAccountRepository;
    private final PolicyAccountNumberGenerator policyAccountNumberGenerator;

    @Topic("policy-registered")
    void onPolicyRegistered(PolicyRegisteredEvent event) {
        Optional<PolicyAccount> accountOpt = policyAccountRepository.findByPolicyNumber(event.getPolicy().getNumber());

        if (!accountOpt.isPresent())
            createAccount(event.getPolicy());
    }

    private void createAccount(PolicyDto policy) {
        PolicyAccount newAccount = new PolicyAccount(policy.getNumber(), policyAccountNumberGenerator.generate());
        newAccount.expectedPayment(policy.getTotalPremium(),policy.getFrom());
        policyAccountRepository.save(newAccount);
    }

}


// Node: createAccount
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;


@Entity
@Inheritance
@Table(name = "accounting_entry")
@DiscriminatorColumn(name = "entry_type")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Getter
public abstract class AccountingEntry {

    @Id
    @GeneratedValue
    private Long id;

    @ManyToOne
    @JoinColumn(name = "policy_account_id")
    private PolicyAccount policyAccount;

    @Column(name = "creation_date")
    private LocalDate creationDate;

    @Column(name = "effective_date")
    private LocalDate effectiveDate;

    @Column(name = "amount")
    private BigDecimal amount;

    AccountingEntry(PolicyAccount policyAccount, LocalDate creationDate, LocalDate effectiveDate, BigDecimal amount) {
        this.policyAccount = policyAccount;
        this.creationDate = creationDate;
        this.effectiveDate = effectiveDate;
        this.amount = amount;
    }

    public abstract BigDecimal apply(BigDecimal state);

    boolean isEffectiveOn(LocalDate theDate) {
        return this.effectiveDate.isBefore(theDate) || this.effectiveDate.equals(theDate);
    }
}


// Node: isEffectiveOn
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import io.micronaut.data.annotation.DateCreated;
import io.micronaut.data.annotation.DateUpdated;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;
import lombok.Setter;

@Entity
@Table(name = "policy_account")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Getter
public class PolicyAccount {

    @Id
    @GeneratedValue
    private Long id;

    @Column(name = "policy_number")
    private String policyNumber;

    @Column(name = "policy_account_number")
    private String policyAccountNumber;

    @OneToMany(mappedBy = "policyAccount", cascade = CascadeType.ALL)
    private List<AccountingEntry> entries;
    
    @Setter
    @DateCreated
    @Column(name = "created")
    private Date created;
    
    @Setter
    @DateUpdated
    @Column(name = "updated")
    private Date updated;

    public PolicyAccount(String policyNumber, String policyAccountNumber) {
        this.policyNumber = policyNumber;
        this.policyAccountNumber = policyAccountNumber;
        this.entries = new ArrayList<>();
    }

    void expectedPayment(BigDecimal amount, LocalDate dueDate) {
        entries.add(new ExpectedPayment(this, LocalDate.now(), dueDate, amount));
    }

    void inPayment(BigDecimal amount, LocalDate incomeDate) {
        entries.add(new InPayment(this, LocalDate.now(), incomeDate, amount));
    }

    void outPayment(BigDecimal amount, LocalDate paymentReleaseDate) {
        entries.add(new OutPayment(this, LocalDate.now(), paymentReleaseDate, amount));
    }

    public BigDecimal balanceAt(LocalDate effectiveDate) {
        List<AccountingEntry> effectiveEntries = entries.stream()
                .sorted(Comparator.comparing(AccountingEntry::getCreationDate))
                .filter(e -> e.isEffectiveOn(effectiveDate))
                .collect(Collectors.toList());

        BigDecimal balance = BigDecimal.ZERO;
        for (AccountingEntry entry : effectiveEntries) {
            balance = entry.apply(balance);
        }

        return balance;
    }
}


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

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyTerminatedEvent;

@KafkaListener(clientId = "policy-terminated-listener", offsetReset = OffsetReset.EARLIEST)
public class PolicyTerminatedListener extends AbstractPolicyListener {

    @Topic("policy-terminated")
    void onPolicyTerminated(PolicyTerminatedEvent event) {
        saveMappedPolicy(event.getPolicy());
    }
}


// Node: onPolicyTerminated
// Node: saveMappedPolicy
package pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.dto.PolicyDto;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
final class PolicyViewAssembler {

    static PolicyView map(PolicyDto policy) {
        return PolicyView.builder()
                .number(policy.getNumber())
                .dateFrom(policy.getFrom())
                .dateTo(policy.getTo())
                .policyHolder(policy.getPolicyHolder())
                .build();
    }
}


// Node: number
// Node: dateFrom
// Node: dateTo
// Node: policyHolder
package pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel;

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;

@KafkaListener(clientId = "policy-registered-listener", offsetReset = OffsetReset.EARLIEST)
public class PolicyRegisteredListener extends AbstractPolicyListener {

    @Topic("policy-registered")
    void onPolicyRegistered(PolicyRegisteredEvent event) {
        saveMappedPolicy(event.getPolicy());
    }
}


package pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel;

import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.dto.PolicyDto;

import javax.inject.Inject;

abstract class AbstractPolicyListener {

    @Inject
    private PolicyViewRepository policyViewRepository;

    void saveMappedPolicy(PolicyDto policy) {
        PolicyView view = PolicyViewAssembler.map(policy);
        policyViewRepository.save(view);
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


// Node: mapSearchResponse
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


package pl.altkom.asc.lab.micronaut.poc.policy.search.queries.findpolicy;

import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyView;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.dto.PolicyListItemDto;

import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

class PolicyQueryResultAssembler {

    static FindPolicyQueryResult constructResult(List<PolicyView> policies) {
        return new FindPolicyQueryResult(
                policies.stream()
                        .map(PolicyListItemDtoAssembler::map)
                        .sorted(Comparator.comparing(PolicyListItemDto::getDateFrom, Comparator.nullsLast(Comparator.reverseOrder())))
                        .collect(Collectors.toList())
        );
    }
}

// Node: nullsLast
// Node: reverseOrder
package pl.altkom.asc.lab.micronaut.poc.policy.search.queries.findpolicy;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.dto.PolicyListItemDto;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyView;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
final class PolicyListItemDtoAssembler {

    static PolicyListItemDto map(PolicyView policy) {
        return new PolicyListItemDto(
                policy.getNumber(),
                policy.getDateFrom(),
                policy.getDateTo(),
                policy.getPolicyHolder()
        );
    }
}


// Node: PolicyListItemDto
// Node: getDateFrom
// Node: getDateTo
