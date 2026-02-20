// Cluster 3

package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createoffer;

import java.math.BigDecimal;
import java.util.Map;

import io.micronaut.core.annotation.Introspected;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Introspected
@Getter
@Setter
@AllArgsConstructor
@NoArgsConstructor
public class CreateOfferResult {
    private String offerNumber;
    private BigDecimal totalPrice;
    private Map<String, BigDecimal> coversPrices;

    public static CreateOfferResult empty() {
        return new CreateOfferResult();
    }
}


// Node: empty
// Node: CreateOfferResult
package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy;

import io.micronaut.core.annotation.Introspected;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Introspected
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class TerminatePolicyResult {

    private String policyNumber;

    public static TerminatePolicyResult success(String policyNumber) {
        return new TerminatePolicyResult(policyNumber);
    }

    public static TerminatePolicyResult empty() {
        return new TerminatePolicyResult();
    }
}


// Node: success
// Node: TerminatePolicyResult
package pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails;

import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.dto.PolicyDetailsDto;

import io.micronaut.core.annotation.Introspected;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Introspected
@AllArgsConstructor
@NoArgsConstructor
@Getter
public class GetPolicyDetailsQueryResult {
    private PolicyDetailsDto policy;

    public static GetPolicyDetailsQueryResult empty() {
        return new GetPolicyDetailsQueryResult(new PolicyDetailsDto());
    }
}


// Node: GetPolicyDetailsQueryResult
// Node: PolicyDetailsDto
package pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice;

import java.math.BigDecimal;
import java.util.Map;

import io.micronaut.core.annotation.Introspected;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Introspected
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class CalculatePriceResult {
    private BigDecimal totalPrice;
    private Map<String, BigDecimal> coversPrices;

    public static CalculatePriceResult empty() {
        return new CalculatePriceResult();
    }
}


// Node: CalculatePriceResult
package pl.altkom.asc.lab.micronaut.poc.policy.shared.specification;

import lombok.Getter;

@Getter
public abstract class Specification<T> {
    private static final Object[] EMPTY_PARAMS = new Object[0];

    private String errorCode;
    private Object[] errorParams = EMPTY_PARAMS;
    private String errorMessage;

    public abstract boolean isSatisfiedBy(T objectToCheck);

    public void ensureIsSatisfiedBy(T objectToCheck) {
        if (!isSatisfiedBy(objectToCheck)) {
            //checkNotNull(getErrorCode(), "Error Code is required. Use empty(code, params) method");
            throw new SpecificationNotSatisfiedException(getErrorCode(), getErrorParams());
        }
    }

    public Specification<T> and(Specification<T> specification) {
        return new AndSpecification<>(this, specification);
    }

    public Specification<T> or(Specification<T> specification) {
        return new OrSpecification<>(this, specification);
    }

    public Specification<T> not() {
        return new NotSpecification<>(this);
    }

    protected boolean failure(String errorCode, Object... errorParams) {
        this.errorCode = errorCode;
        this.errorParams = errorParams;
        return false;
    }

    protected boolean failure(String errorCode) {
        return failure(errorCode, EMPTY_PARAMS);
    }

    protected boolean failureWithMessage(String errorCode, String errorMessage, Object... errorParams) {
        this.errorMessage = errorMessage;
        return failure(errorCode, errorParams);
    }

    protected boolean success() {
        this.errorParams = EMPTY_PARAMS;
        return true;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/shared/specification/Specification.java:Specification.<init>
// Node: isSatisfiedBy
// Node: ensureIsSatisfiedBy
// Node: checkNotNull
// Node: getErrorCode
// Node: SpecificationNotSatisfiedException
// Node: getErrorParams
// Node: failure
// Node: failureWithMessage
package pl.altkom.asc.lab.micronaut.poc.policy.shared.specification;

public class AndSpecification<T> extends Specification<T> {
    private final Specification<T> leftSpec;
    private final Specification<T> rightSpec;

    public AndSpecification(Specification<T> leftSpec, Specification<T> rightSpec) {
        this.leftSpec = leftSpec;
        this.rightSpec = rightSpec;
    }


    @Override
    public boolean isSatisfiedBy(T objectToCheck) {
        if (!leftSpec.isSatisfiedBy(objectToCheck)){
            return failure(leftSpec.getErrorCode(), leftSpec.getErrorParams());
        }

        if (!rightSpec.isSatisfiedBy(objectToCheck)){
            return failure(rightSpec.getErrorCode(), rightSpec.getErrorParams());
        }

        return success();
    }
}


package pl.altkom.asc.lab.micronaut.poc.policy.shared.specification;

public class OrSpecification<T> extends Specification<T> {
    private final Specification<T> leftSpec;
    private final Specification<T> rightSpec;

    public OrSpecification(Specification<T> leftSpec, Specification<T> rightSpec) {
        this.leftSpec = leftSpec;
        this.rightSpec = rightSpec;
    }

    @Override
    public boolean isSatisfiedBy(T objectToCheck) {
        if (!leftSpec.isSatisfiedBy(objectToCheck) && !rightSpec.isSatisfiedBy(objectToCheck)){
            return failure(leftSpec.getErrorCode(), leftSpec.getErrorParams());
        }

        return success();
    }
}


package pl.altkom.asc.lab.micronaut.poc.policy.shared.specification;

public class NotSpecification<T> extends Specification<T> {
    private final Specification<T> spec;

    public NotSpecification(Specification<T> spec) {
        this.spec = spec;
    }

    @Override
    public boolean isSatisfiedBy(T objectToCheck) {
        if (spec.isSatisfiedBy(objectToCheck)){
            return failure(spec.getErrorCode(), spec.getErrorParams());
        }

        return success();
    }
}


package pl.altkom.asc.lab.micronaut.poc.policy.shared.specification;


import pl.altkom.asc.lab.micronaut.poc.policy.shared.exceptions.BusinessException;

public class SpecificationNotSatisfiedException extends BusinessException {
    public SpecificationNotSatisfiedException(String errorCode,Object[] params){
        super(errorCode, params);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/shared/specification/SpecificationNotSatisfiedException.java:SpecificationNotSatisfiedException.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.fallback;

import io.micronaut.retry.annotation.Fallback;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.PolicyOperations;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import javax.inject.Singleton;
import javax.validation.constraints.NotNull;

@Singleton
@Fallback
public class PolicyGatewayClientFallback implements PolicyOperations {

    @Override
    public GetPolicyDetailsQueryResult get(@NotNull String policyNumber) {
        return GetPolicyDetailsQueryResult.empty();
    }

    @Override
    public CreatePolicyResult create(@NotNull CreatePolicyCommand cmd) {
        return new CreatePolicyResult(null);
    }

    @Override
    public TerminatePolicyResult terminate(@NotNull TerminatePolicyCommand cmd) {
        return TerminatePolicyResult.empty();
    }
}


package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.fallback;

import io.micronaut.retry.annotation.Fallback;
import io.reactivex.Maybe;
import io.reactivex.Single;
import pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.ProductGatewayClient;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;

import javax.inject.Singleton;
import java.util.Collections;
import java.util.List;

@Singleton
@Fallback
public class ProductGatewayClientFallback implements ProductGatewayClient {

    @Override
    public Single<List<ProductDto>> getAll() {
        return Single.just(Collections.emptyList());
    }

    @Override
    public Maybe<ProductDto> get(String productCode) {
        return Maybe.empty();
    }
}


