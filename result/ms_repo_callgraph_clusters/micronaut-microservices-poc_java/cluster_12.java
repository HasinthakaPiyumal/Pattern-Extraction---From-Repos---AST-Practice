// Cluster 12

// Node: now
// Node: add
// Node: Policy
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/queries/getpolicydetails/PolicyDetailsDtoAssembler.java:PolicyDetailsDtoAssembler.<init>
// Node: NoArgsConstructor
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.math.BigDecimal;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;

import javax.persistence.*;

@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Getter
public class Cover {
    @Id
    @GeneratedValue
    private Long id;

    private String code;
    
    private BigDecimal price;

    @JsonIgnore
    @ManyToOne
    @JoinColumn(name = "POLICY_VERSION_ID")
    private PolicyVersion policyVersion;

    public Cover(PolicyVersion policyVersion, String code, BigDecimal price) {
        this.policyVersion = policyVersion;
        this.code = code;
        this.price = price;
    }

    @Override
    public String toString() {
        return code + " - " + price;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/Cover.java:Cover.<init>
// Node: JoinColumn
// Node: Cover
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/PolicyVersionRef.java:PolicyVersionRef.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/AgentRef.java:AgentRef.<init>
// Node: Column
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/Offer.java:Offer.<init>
// Node: CollectionTable
// Node: MapKeyColumn
// Node: Enumerated
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import com.fasterxml.jackson.annotation.JsonIgnore;
import java.math.BigDecimal;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.vo.DateRange;

import javax.persistence.*;
import java.time.LocalDate;
import java.util.Set;

@Entity
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Getter
public class PolicyVersion {
    @Id
    @GeneratedValue
    private Long id;

    @JsonIgnore
    @ManyToOne
    @JoinColumn(name = "POLICY_ID")
    private Policy policy;

    private Long versionNumber;

    private String productCode;

    private Person policyHolder;

    private String accountNumber;

    @Embedded
    @AttributeOverrides({
            @AttributeOverride(name = "from", column = @Column(name = "cover_from")),
            @AttributeOverride(name = "to", column = @Column(name = "cover_to"))
    })
    private DateRange coverPeriod;

    @Embedded
    @AttributeOverrides({
            @AttributeOverride(name = "from", column = @Column(name = "version_from")),
            @AttributeOverride(name = "to", column = @Column(name = "version_to"))
    })
    private DateRange versionValidityPeriod;

    @OneToMany(mappedBy = "policyVersion", cascade = CascadeType.ALL)
    private Set<Cover> covers;
    
    private BigDecimal totalPremiumAmount;

    CoverCollection covers() {
        return new CoverCollection(this, covers);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/PolicyVersion.java:PolicyVersion.<init>
// Node: AttributeOverrides
// Node: AttributeOverride
// Node: OneToMany
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/Person.java:Person.<init>
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


package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import lombok.*;

import javax.persistence.Embeddable;

@Embeddable
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Getter
@EqualsAndHashCode
class PolicyRef {
    private String policyNumber;

    static PolicyRef of(Policy policy) {
        return new PolicyRef(policy.getNumber());
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/PolicyRef.java:PolicyRef.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/Policy.java:Policy.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/vo/DateRange.java:DateRange.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/vo/Quantity.java:Quantity.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/vo/Percent.java:Percent.<init>
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


// Node: BasePremiumCalculationRule
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


// Node: PercentMarkupRule
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


// Node: zeroPrice
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/Tariff.java:Tariff.<init>
// Node: Table
// Node: GeneratedValue
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/PercentMarkupRule.java:PercentMarkupRule.<init>
// Node: DiscriminatorValue
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.mvel2.MVEL;

import javax.persistence.*;
import java.math.BigDecimal;

@Entity
@DiscriminatorColumn(name = "type")
@Table(name = "discount_markup_rule")
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@NoArgsConstructor
@Getter
public abstract class DiscountMarkupRule {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "tariff_id")
    protected Tariff tariff;

    @Column(name = "apply_if_formula")
    protected String applyIfFormula;

    @Column(name = "param_value")
    protected BigDecimal paramValue;

    boolean applies(Calculation calculation) {
        return applyIfFormula == null || applyIfFormula.isEmpty()
                ? true
                : MVEL.eval(applyIfFormula, calculation.toMap(), Boolean.class);
    }

    public abstract Calculation apply(Calculation calculation);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/DiscountMarkupRule.java:DiscountMarkupRule.<init>
// Node: DiscriminatorColumn
// Node: Inheritance
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.mvel2.MVEL;

import javax.persistence.Column;
import javax.persistence.Embeddable;
import java.math.BigDecimal;

@Embeddable
@NoArgsConstructor
@Getter
public class BasePremiumCalculationRule {

    @Column(name = "cover_code")
    private String coverCode;

    @Column(name = "apply_if_formula")
    private String applyIfFormula;

    @Column(name = "price_formula")
    private String basePriceFormula;

    BasePremiumCalculationRule(String coverCode, String applyIfFormula, String basePriceFormula) {
        this.coverCode = coverCode;
        this.applyIfFormula = applyIfFormula;
        this.basePriceFormula = basePriceFormula;
    }

    boolean applies(Calculation calculation) {
        return applyIfFormula == null || applyIfFormula.isEmpty()
                ? true
                : MVEL.eval(applyIfFormula, calculation.toMap(), Boolean.class);
    }

    BigDecimal calculateBasePrice(Calculation calculation) {
        return MVEL.eval(basePriceFormula, calculation.toMap(), BigDecimal.class);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/BasePremiumCalculationRule.java:BasePremiumCalculationRule.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/infrastructure/adapters/web/ProductsAssembler.java:ProductsAssembler.<init>
package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.bson.codecs.pojo.annotations.BsonCreator;
import org.bson.codecs.pojo.annotations.BsonDiscriminator;
import org.bson.codecs.pojo.annotations.BsonProperty;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Getter
@NoArgsConstructor
@BsonDiscriminator
public class Product {
    private String code;
    private String name;
    private String image;
    private String description;
    private List<Cover> covers;
    private List<Question> questions;
    private int maxNumberOfInsured;
    private String icon;

    @BsonCreator
    public Product(
            @BsonProperty("code") String code,
            @BsonProperty("name") String name,
            @BsonProperty("image") String image,
            @BsonProperty("description") String description,
            @BsonProperty("covers") List<Cover> covers,
            @BsonProperty("questions") List<Question> questions,
            @BsonProperty("maxNumberOfInsured") int maxNumberOfInsured,
            @BsonProperty("icon") String icon) {
        this.code = code;
        this.name = name;
        this.image = image;
        this.description = description;
        this.covers = covers;
        this.questions = questions;
        this.maxNumberOfInsured = maxNumberOfInsured;
        this.icon = icon;
    }

    public Product(String code, String name, String image, String description, int maxNumberOfInsured, String icon) {
        this.code = code;
        this.name = name;
        this.image = image;
        this.description = description;
        this.maxNumberOfInsured = maxNumberOfInsured;
        this.covers = new ArrayList<>();
        this.questions = new ArrayList<>();
        this.icon = icon;
    }

    public void addCover(String code, String name, String description, boolean isOptional, BigDecimal sumInsured) {
        covers.add(new Cover(code, name, description, isOptional, sumInsured));
    }

    public void addQuestions(List<Question> questions) {
        if (this.questions == null) {
            this.questions = new ArrayList<>();
        }
        this.questions.addAll(questions);
    }
}


package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

import javax.persistence.DiscriminatorValue;
import javax.persistence.Entity;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@DiscriminatorValue(value = "expected_payment")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ExpectedPayment extends AccountingEntry {

    public ExpectedPayment(PolicyAccount policyAccount, LocalDate creationDate, LocalDate effectiveDate, BigDecimal amount) {
        super(policyAccount, creationDate, effectiveDate, amount);
    }

    @Override
    public BigDecimal apply(BigDecimal state) {
        return state.subtract(getAmount());
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/ExpectedPayment.java:ExpectedPayment.<init>
// Node: ExpectedPayment
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

import javax.persistence.DiscriminatorValue;
import javax.persistence.Entity;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@DiscriminatorValue(value = "outpayment")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class OutPayment extends AccountingEntry {

    public OutPayment(PolicyAccount policyAccount, LocalDate creationDate, LocalDate effectiveDate, BigDecimal amount) {
        super(policyAccount, creationDate, effectiveDate, amount);
    }

    @Override
    public BigDecimal apply(BigDecimal state) {
        return state.subtract(getAmount());
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/OutPayment.java:OutPayment.<init>
// Node: OutPayment
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

import javax.persistence.DiscriminatorValue;
import javax.persistence.Entity;
import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@DiscriminatorValue(value = "inpayment")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class InPayment extends AccountingEntry {

    public InPayment(PolicyAccount policyAccount, LocalDate creationDate, LocalDate effectiveDate, BigDecimal amount) {
        super(policyAccount, creationDate, effectiveDate, amount);
    }

    @Override
    public BigDecimal apply(BigDecimal state) {
        return state.add(getAmount());
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/InPayment.java:InPayment.<init>
// Node: InPayment
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/AccountingEntry.java:AccountingEntry.<init>
// Node: AccountingEntry
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/PolicyAccount.java:PolicyAccount.<init>
// Node: outPayment
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/readmodel/PolicyViewAssembler.java:PolicyViewAssembler.<init>
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/queries/findpolicy/PolicyListItemDtoAssembler.java:PolicyListItemDtoAssembler.<init>
