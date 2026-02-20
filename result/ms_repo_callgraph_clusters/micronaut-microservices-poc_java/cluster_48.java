// Cluster 48

package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.bus;

import pl.altkom.asc.lab.micronaut.poc.command.bus.MicronautCommandBus;
import pl.altkom.asc.lab.micronaut.poc.command.bus.Registry;

import javax.inject.Singleton;

@Singleton
public class PolicySearchCommandBus extends MicronautCommandBus {
    public PolicySearchCommandBus(Registry registry) {
        super(registry);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/infrastructure/adapters/bus/PolicySearchCommandBus.java:PolicySearchCommandBus.<init>
// Node: PolicySearchCommandBus
