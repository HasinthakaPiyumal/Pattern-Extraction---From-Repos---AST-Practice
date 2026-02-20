// Cluster 23

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


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/shared/specification/NotSpecification.java:NotSpecification.<init>
// Node: NotSpecification
