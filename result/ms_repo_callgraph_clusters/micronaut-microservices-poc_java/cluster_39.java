// Cluster 39

// Node: divide
// Node: toMap
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


// Node: Quantity
// Node: zero
// Node: subtract
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


// Node: MonetaryAmount
// Node: getAmount
// Node: toValue
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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/vo/MonetaryAmount.java:MonetaryAmount.<init>
// Node: from
// Node: toBigDecimal
// Node: toWholeNumber
// Node: round
// Node: applies
// Node: apply
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


// Node: isEmpty
// Node: eval
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


