// Cluster 30

package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.bus;

import io.micronaut.context.ApplicationContext;
import pl.altkom.asc.lab.micronaut.poc.command.bus.Registry;

import javax.inject.Singleton;

@Singleton
public class PolicyRegistry extends Registry {
    public PolicyRegistry(ApplicationContext applicationContext) {
        super(applicationContext);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/bus/PolicyRegistry.java:PolicyRegistry.<init>
// Node: PolicyRegistry
