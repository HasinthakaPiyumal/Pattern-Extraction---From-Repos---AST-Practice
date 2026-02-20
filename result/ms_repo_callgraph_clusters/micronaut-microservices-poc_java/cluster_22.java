// Cluster 22

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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/shared/specification/OrSpecification.java:OrSpecification.<init>
// Node: OrSpecification
