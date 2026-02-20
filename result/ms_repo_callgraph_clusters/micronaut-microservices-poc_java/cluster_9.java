// Cluster 9

package pl.altkom.asc.lab.micronaut.poc.dashboard.infrastructure.adapters.bus;

import pl.altkom.asc.lab.micronaut.poc.command.bus.MicronautCommandBus;
import pl.altkom.asc.lab.micronaut.poc.command.bus.Registry;

import javax.inject.Singleton;

@Singleton
public class DashboardCommandBus extends MicronautCommandBus {
    public DashboardCommandBus(Registry registry) {
        super(registry);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/infrastructure/adapters/bus/DashboardCommandBus.java:DashboardCommandBus.<init>
// Node: DashboardCommandBus
