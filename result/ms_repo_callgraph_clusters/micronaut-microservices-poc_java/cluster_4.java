// Cluster 4

package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import io.micronaut.core.annotation.Introspected;

@Introspected
public class TextQuestionAnswer extends QuestionAnswer<String> {
    @JsonCreator
    public TextQuestionAnswer(@JsonProperty("questionCode") String questionCode, @JsonProperty("answer") String answer) {
        super(questionCode, answer);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/service/api/v1/commands/createoffer/dto/TextQuestionAnswer.java:TextQuestionAnswer.<init>
// Node: TextQuestionAnswer
// Node: JsonProperty
package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import io.micronaut.core.annotation.Introspected;

@Introspected
public class ChoiceQuestionAnswer extends QuestionAnswer<String> {
    @JsonCreator
    public ChoiceQuestionAnswer(@JsonProperty("questionCode") String questionCode, @JsonProperty("answer") String answer) {
        super(questionCode, answer);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/service/api/v1/commands/createoffer/dto/ChoiceQuestionAnswer.java:ChoiceQuestionAnswer.<init>
// Node: ChoiceQuestionAnswer
package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.math.BigDecimal;

import io.micronaut.core.annotation.Introspected;

@Introspected
public class NumericQuestionAnswer extends QuestionAnswer<BigDecimal> {
    @JsonCreator
    public NumericQuestionAnswer(@JsonProperty("questionCode") String questionCode, @JsonProperty("answer") BigDecimal answer) {
        super(questionCode, answer);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/service/api/v1/commands/createoffer/dto/NumericQuestionAnswer.java:NumericQuestionAnswer.<init>
// Node: NumericQuestionAnswer
package pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto;

import io.micronaut.core.annotation.Introspected;

@Introspected
public class TextQuestionAnswer extends QuestionAnswer<String> {
    public TextQuestionAnswer(String questionCode, String answer) {
        super(questionCode, answer);
    }
}



// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/service/api/v1/commands/calculateprice/dto/TextQuestionAnswer.java:TextQuestionAnswer.<init>
package pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto;

import io.micronaut.core.annotation.Introspected;

@Introspected
public class ChoiceQuestionAnswer extends QuestionAnswer<String> {
    public ChoiceQuestionAnswer(String questionCode, String answer) {
        super(questionCode, answer);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/service/api/v1/commands/calculateprice/dto/ChoiceQuestionAnswer.java:ChoiceQuestionAnswer.<init>
package pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto;

import java.math.BigDecimal;

import io.micronaut.core.annotation.Introspected;

@Introspected
public class NumericQuestionAnswer extends QuestionAnswer<BigDecimal> {
    public NumericQuestionAnswer(String questionCode, BigDecimal answer) {
        super(questionCode, answer);
    }
}



// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/service/api/v1/commands/calculateprice/dto/NumericQuestionAnswer.java:NumericQuestionAnswer.<init>
// Node: fromOffer
// Node: getProductCode
package pl.altkom.asc.lab.micronaut.poc.policy.commands;

import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandHandler;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Offer;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferFactory;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.restclient.PricingClient;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.CreateOfferResult;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.ChoiceQuestionAnswer;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.NumericQuestionAnswer;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.QuestionAnswer;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.TextQuestionAnswer;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class CreateOfferHandler implements CommandHandler<CreateOfferResult, CreateOfferCommand> {

    private final OfferRepository offerRepository;
    private final PricingClient pricingOperations;

    @Transactional
    @Override
    public CreateOfferResult handle(CreateOfferCommand cmd) {
        //calculate price
        CalculatePriceCommand calcPriceCmd = constructPriceCmd(cmd);
        CalculatePriceResult price = pricingOperations.calculatePrice(calcPriceCmd);

        //create & save offer
        Offer offer = OfferFactory.offerFromPrice(calcPriceCmd, price);
        offerRepository.save(offer);

        //return result
        return constructResult(offer);
    }

    private CalculatePriceCommand constructPriceCmd(CreateOfferCommand cmd) {
        return new CalculatePriceCommand(
                cmd.getProductCode(),
                cmd.getPolicyFrom(),
                cmd.getPolicyTo(),
                cmd.getSelectedCovers(),
                constructAnswers(cmd.getAnswers()));
    }

    private CreateOfferResult constructResult(Offer offer) {
        return new CreateOfferResult(
                offer.getNumber(),
                offer.getTotalPrice(),
                offer.getCoversPrices());
    }

    private List<QuestionAnswer> constructAnswers(List<pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto.QuestionAnswer> answers) {
        List<QuestionAnswer> result = new ArrayList<>();
        for (pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto.QuestionAnswer answer : answers) {
            if (answer instanceof pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto.TextQuestionAnswer) {
                result.add(new TextQuestionAnswer(answer.getQuestionCode(), (String) answer.getAnswer()));
            } else if (answer instanceof pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto.ChoiceQuestionAnswer) {
                result.add(new ChoiceQuestionAnswer(answer.getQuestionCode(), (String) answer.getAnswer()));
            } else if (answer instanceof pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer.dto.NumericQuestionAnswer) {
                result.add(new NumericQuestionAnswer(answer.getQuestionCode(), (BigDecimal) answer.getAnswer()));
            }
        }
        return result;
    }
}


// Node: constructPriceCmd
// Node: offerFromPrice
// Node: constructResult
// Node: CalculatePriceCommand
// Node: getPolicyFrom
// Node: getPolicyTo
// Node: getSelectedCovers
// Node: constructAnswers
// Node: getAnswers
// Node: getTotalPrice
// Node: getCoversPrices
// Node: getQuestionCode
// Node: getAnswer
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


// Node: toString
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import java.util.UUID;

public class PolicyFactory {

    public Policy fromOffer(Offer offer, Person policyHolder, AgentRef agent) {
        Policy policy = new Policy(UUID.randomUUID().toString(), agent);
        policy.addVersion(offer, policyHolder);
        return policy;
    }


}


// Node: randomUUID
// Node: addVersion
package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.QuestionAnswer;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

public class OfferFactory {
    public static Offer offerFromPrice(CalculatePriceCommand calcPriceCmd, CalculatePriceResult calcPriceResult) {
        return new Offer(
                null,
                UUID.randomUUID().toString(),
                calcPriceCmd.getProductCode(),
                calcPriceCmd.getPolicyFrom(),
                calcPriceCmd.getPolicyTo(),
                constructAnswers(calcPriceCmd.getAnswers()),
                calcPriceResult.getTotalPrice(),
                calcPriceResult.getCoversPrices(),
                OfferStatus.NEW,
                LocalDate.now());
    }

    private static Map<String, String> constructAnswers(List<QuestionAnswer> answers) {
        return answers.stream()
                .collect(Collectors.toMap(QuestionAnswer::getQuestionCode,
                        a -> a.getAnswer() != null ? a.getAnswer().toString() : null)
                );
    }
}


// Node: Offer
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


// Node: assertNotNull
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


// Node: testCreatePolicy
// Node: CreatePolicyCommand
// Node: PersonDto
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


// Node: getByCode
// Node: toCalculation
// Node: resultFromCalculation
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import java.util.Optional;
import io.micronaut.data.repository.CrudRepository;
import io.micronaut.data.annotation.*;
import io.micronaut.data.model.*;

@Repository
public interface Tariffs extends CrudRepository<Tariff, Long>  {

    Optional<Tariff> findByCode(String code);
    
    Tariff getByCode(String code);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/Tariffs.java:Tariffs.<init>
// Node: findByCode
package pl.altkom.asc.lab.micronaut.poc.pricing;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.ChoiceQuestionAnswer;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.dto.NumericQuestionAnswer;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.Arrays;

import javax.validation.ConstraintViolationException;

import io.micronaut.context.ApplicationContext;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;


public class PricingControllerTest {

    private static EmbeddedServer server;
    private static PricingTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(PricingTestClient.class, server.getURL());
    }

    @Test
    public void exceptionWhenCommandIsNull() {
        assertThrows(ConstraintViolationException.class, () -> client.calculatePrice(null));
    }

    @Test
    public void canCalculateTravelPolicyPrice() {
        CalculatePriceCommand cmd = new CalculatePriceCommand(
                "TRI",
                LocalDate.of(2017, 4, 16),
                LocalDate.of(2018, 4, 15),
                Arrays.asList("C1", "C2"),
                Arrays.asList(
                        new NumericQuestionAnswer("NUM_OF_ADULTS", new BigDecimal("1")),
                        new NumericQuestionAnswer("NUM_OF_CHILDREN", new BigDecimal("1")),
                        new ChoiceQuestionAnswer("DESTINATION", "EUR")
                )
        );

        CalculatePriceResult result = client.calculatePrice(cmd);

        assertNotNull(result);
        assertEquals(new BigDecimal("78"), result.getTotalPrice(),"Total premium should be 78");
        assertEquals(new BigDecimal("26"), result.getCoversPrices().get("C1"),"C1 premium should be 26");
        assertEquals(new BigDecimal("52"), result.getCoversPrices().get("C2"),"C2 should be 52");
    }

    @Test
    public void canCalculateHousePolicyPrice() {
        CalculatePriceCommand cmd = new CalculatePriceCommand(
                "HSI",
                LocalDate.of(2017, 4, 16),
                LocalDate.of(2018, 4, 15),
                Arrays.asList("C1", "C2", "C3"),
                Arrays.asList(
                        new NumericQuestionAnswer("AREA", new BigDecimal("95")),
                        new NumericQuestionAnswer("NUM_OF_CLAIM", new BigDecimal("1")),
                        new ChoiceQuestionAnswer("FLOOD", "NO"),
                        new ChoiceQuestionAnswer("TYP", "APT")
                )
        );

        CalculatePriceResult result = client.calculatePrice(cmd);

        assertNotNull(result);
        assertEquals(new BigDecimal("172.50"), result.getTotalPrice(),"Total premium should be 172.50");
        assertEquals(new BigDecimal("118.75"), result.getCoversPrices().get("C1"),"C1 premium should be 118.75");
        assertEquals(new BigDecimal("23.75"), result.getCoversPrices().get("C2"),"C2 should be 23.75");
        assertEquals(new BigDecimal("30"), result.getCoversPrices().get("C3"),"C3 should be 30");
    }

    @AfterAll
    public static void cleanup() {
        if (server != null)
            server.stop();
    }
}


// Node: canCalculateTravelPolicyPrice
// Node: canCalculateHousePolicyPrice
package pl.altkom.asc.lab.micronaut.poc.payment.infrastructure.adapters.mock;

import pl.altkom.asc.lab.micronaut.poc.payment.domain.PolicyAccountNumberGenerator;

import javax.inject.Singleton;
import java.util.UUID;

@Singleton
public class MockPolicyAccountNumberGenerator implements PolicyAccountNumberGenerator {

    @Override
    public String generate() {
        return UUID.randomUUID().toString();
    }
}


