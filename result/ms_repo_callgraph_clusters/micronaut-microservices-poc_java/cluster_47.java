// Cluster 47

package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.bus;

import io.micronaut.context.ApplicationContext;
import pl.altkom.asc.lab.micronaut.poc.command.bus.Registry;

import javax.inject.Singleton;

@Singleton
public class PolicySearchRegistry extends Registry {
    public PolicySearchRegistry(ApplicationContext applicationContext) {
        super(applicationContext);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/infrastructure/adapters/bus/PolicySearchRegistry.java:PolicySearchRegistry.<init>
// Node: PolicySearchRegistry
