// Cluster 29

package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.bus;

import pl.altkom.asc.lab.micronaut.poc.command.bus.MicronautCommandBus;
import pl.altkom.asc.lab.micronaut.poc.command.bus.Registry;

import javax.inject.Singleton;

@Singleton
public class PolicyCommandBus extends MicronautCommandBus {
    public PolicyCommandBus(Registry registry) {
        super(registry);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/bus/PolicyCommandBus.java:PolicyCommandBus.<init>
// Node: PolicyCommandBus
