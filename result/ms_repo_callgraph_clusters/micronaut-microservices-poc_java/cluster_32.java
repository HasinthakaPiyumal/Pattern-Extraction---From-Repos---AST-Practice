// Cluster 32

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


// Node: policyRef
// Node: PolicyRef
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


