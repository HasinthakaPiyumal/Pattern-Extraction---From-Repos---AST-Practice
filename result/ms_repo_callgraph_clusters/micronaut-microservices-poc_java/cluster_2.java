// Cluster 2

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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/BasePremiumCalculationRuleList.java:BasePremiumCalculationRuleList.<init>
// Node: BasePremiumCalculationRuleList
// Node: addBasePriceRule
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/pricing-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/pricing/domain/DiscountMarkupRuleList.java:DiscountMarkupRuleList.<init>
// Node: DiscountMarkupRuleList
// Node: addPercentMarkup
// Node: updateTotal
// Node: Tariff
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


// Node: rules
// Node: discountMarkupRules
// Node: calcBasePrices
// Node: applyDiscounts
// Node: buildResponse
package pl.altkom.asc.lab.micronaut.poc.pricing.init;

import pl.altkom.asc.lab.micronaut.poc.pricing.domain.Tariff;

import java.math.BigDecimal;

class DemoTariffsFactory {

    static Tariff travel() {
        Tariff t = new Tariff("TRI");

        t.rules().addBasePriceRule("C1", null, "(NUM_OF_ADULTS) * (DESTINATION == 'EUR' ? 26.00B : 34.00B)");
        t.rules().addBasePriceRule("C2", null, "(NUM_OF_ADULTS + NUM_OF_CHILDREN) * 26.00B");
        t.rules().addBasePriceRule("C3", null, "(NUM_OF_ADULTS + NUM_OF_CHILDREN) * 10.00B");

        t.discountMarkupRules().addPercentMarkup("DESTINATION == 'WORLD'", new BigDecimal("1.50"));

        return t;
    }

    static Tariff house() {
        Tariff t = new Tariff("HSI");

        t.rules().addBasePriceRule("C1", "TYP == 'APT'", "AREA * 1.25B");
        t.rules().addBasePriceRule("C1", "TYP == 'HOUSE'", "AREA * 1.50B");

        t.rules().addBasePriceRule("C2", "TYP == 'APT'", "AREA * 0.25B");
        t.rules().addBasePriceRule("C2", "TYP == 'HOUSE'", "AREA * 0.45B");

        t.rules().addBasePriceRule("C3", null, "30B");
        t.rules().addBasePriceRule("C4", null, "50B");

        t.discountMarkupRules().addPercentMarkup("FLOOD == 'YES'", new BigDecimal("1.50"));
        t.discountMarkupRules().addPercentMarkup("NUM_OF_CLAIM > 1 ", new BigDecimal("1.25"));

        return t;
    }

    static Tariff farm() {
        Tariff t = new Tariff("FAI");

        t.rules().addBasePriceRule("C1", null, "10B");
        t.rules().addBasePriceRule("C2", null, "20B");
        t.rules().addBasePriceRule("C3", null, "30B");
        t.rules().addBasePriceRule("C4", null, "40B");

        t.discountMarkupRules().addPercentMarkup("FLOOD == 'YES'", new BigDecimal("1.50"));
        t.discountMarkupRules().addPercentMarkup("NUM_OF_CLAIM > 2", new BigDecimal("2.00"));

        return t;
    }

    static Tariff car() {
        Tariff t = new Tariff("CAR");

        t.rules().addBasePriceRule("C1", null, "100B");
        t.discountMarkupRules().addPercentMarkup("NUM_OF_CLAIM > 2", new BigDecimal("50.00"));

        return t;
    }
}


package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import java.math.BigDecimal;

class TariffsFactory {

    static Tariff travel() {
        Tariff t = new Tariff("TRI");

        t.rules().addBasePriceRule("C1", null, "(NUM_OF_ADULTS) * (DESTINATION == 'EUR' ? 26.00B : 34.00B)");
        t.rules().addBasePriceRule("C2", null, "(NUM_OF_ADULTS + NUM_OF_CHILDREN) * 26.00B");
        t.rules().addBasePriceRule("C3", null, "(NUM_OF_ADULTS + NUM_OF_CHILDREN) * 10.00B");

        t.discountMarkupRules().addPercentMarkup("DESTINATION == 'WORLD'", new BigDecimal("1.50"));

        return t;
    }

    static Tariff house() {
        Tariff t = new Tariff("HSI");

        t.rules().addBasePriceRule("C1", "TYP == 'APT'", "AREA * 1.25B");
        t.rules().addBasePriceRule("C1", "TYP == 'HOUSE'", "AREA * 1.50B");

        t.rules().addBasePriceRule("C2", "TYP == 'APT'", "AREA * 0.25B");
        t.rules().addBasePriceRule("C2", "TYP == 'HOUSE'", "AREA * 0.45B");

        t.rules().addBasePriceRule("C3", null, "30B");
        t.rules().addBasePriceRule("C4", null, "50B");

        t.discountMarkupRules().addPercentMarkup("FLOOD == 'YES'", new BigDecimal("1.50"));
        t.discountMarkupRules().addPercentMarkup("NUM_OF_CLAIM > 1 ", new BigDecimal("1.25"));

        return t;
    }

    static Tariff car() {
        Tariff t = new Tariff("CAR");

        t.rules().addBasePriceRule("C1", null, "100B");
        t.discountMarkupRules().addPercentMarkup("NUM_OF_CLAIM > 2", new BigDecimal("50.00"));

        return t;
    }
}


