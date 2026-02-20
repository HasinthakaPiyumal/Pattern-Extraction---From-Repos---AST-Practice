// Cluster 41

package pl.altkom.asc.lab.micronaut.poc.gateway;

import io.micronaut.runtime.Micronaut;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Contact;
import io.swagger.v3.oas.annotations.info.Info;

@OpenAPIDefinition(
        info = @Info(
                title = "LAB Insurance Sales Portal API",
                version = "1.0",
                contact = @Contact(url = "http://altkomsoftware.pl", name = "ASCLAB", email = "lab@altkomsoftware.pl")
        )
)
public class AgentPortalGatewayApplication {
    public static void main(String[] args) {
        Micronaut.run(AgentPortalGatewayApplication.class);
    }
}

// Node: repos/cloned_ms_repos/micronaut-microservices-poc/agent-portal-gateway/src/main/java/pl/altkom/asc/lab/micronaut/poc/gateway/AgentPortalGatewayApplication.java:AgentPortalGatewayApplication.<init>
// Node: OpenAPIDefinition
// Node: Info
// Node: Contact
