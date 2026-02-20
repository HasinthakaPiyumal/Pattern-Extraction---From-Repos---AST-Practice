// Cluster 44

package pl.altkom.asc.lab.micronaut.poc.auth;

import org.reactivestreams.Publisher;

import java.util.Optional;

import javax.inject.Singleton;

import io.micronaut.http.HttpRequest;
import io.micronaut.security.authentication.AuthenticationFailed;
import io.micronaut.security.authentication.AuthenticationProvider;
import io.micronaut.security.authentication.AuthenticationRequest;
import io.micronaut.security.authentication.AuthenticationResponse;
import io.reactivex.Flowable;
import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class AuthProvider implements AuthenticationProvider {

    //private final InsuranceAgents insuranceAgents;
    private final InsuranceAgentsRepository insuranceAgents;

    @Override
    public Publisher<AuthenticationResponse> authenticate(HttpRequest<?> httpRequest, AuthenticationRequest<?, ?> authenticationRequest) {
        Optional<InsuranceAgent> agent = insuranceAgents.findByLogin((String) authenticationRequest.getIdentity());

        if (agent.isPresent() && agent.get().passwordMatches((String) authenticationRequest.getSecret())) {
            return Flowable.just(createUserDetails(agent.get()));
        }

        return Flowable.just(new AuthenticationFailed());
    }

    private InsuranceAgentDetails createUserDetails(InsuranceAgent agent) {
        return new InsuranceAgentDetails(agent.login(), agent.avatar(), agent.availableProductCodes());
    }
}


// Node: authenticate
// Node: findByLogin
// Node: getIdentity
// Node: passwordMatches
// Node: getSecret
// Node: createUserDetails
// Node: AuthenticationFailed
// Node: InsuranceAgentDetails
// Node: login
// Node: avatar
// Node: availableProductCodes
package pl.altkom.asc.lab.micronaut.poc.auth;

import java.util.Arrays;
import java.util.Collection;
import java.util.List;
import java.util.UUID;

import io.micronaut.data.annotation.Id;
import io.micronaut.data.annotation.MappedEntity;



@MappedEntity
record InsuranceAgent(
    @Id UUID id,
    String login,
    String password,
    String avatar,
    String availableProducts) {

    InsuranceAgent(UUID id,String login, String password, String avatar, List<String> availableProducts) {
        this(id,login,password,avatar,String.join(";",availableProducts));
    }
    
    boolean passwordMatches(String passwordToTest) {
        return this.password.equals(passwordToTest);
    }

    public Collection<String> availableProductCodes() {
        return Arrays.asList(availableProducts.split(";"));
    }
}


// Node: split
package pl.altkom.asc.lab.micronaut.poc.auth;


import io.micronaut.security.authentication.UserDetails;
import lombok.Getter;

import java.util.Collection;

@Getter
class InsuranceAgentDetails extends UserDetails {

    private String avatarUrl;

    InsuranceAgentDetails(String username, String avatarUrl, Collection<String> roles) {
        super(username, roles);
        this.avatarUrl = avatarUrl;
   }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/auth/InsuranceAgentDetails.java:InsuranceAgentDetails.<init>
package pl.altkom.asc.lab.micronaut.poc.auth;

import java.util.Optional;

import io.micronaut.data.jdbc.annotation.JdbcRepository;
import io.micronaut.data.model.query.builder.sql.Dialect;
import io.micronaut.data.repository.CrudRepository;

@JdbcRepository(dialect = Dialect.H2)
public interface InsuranceAgentsRepository extends CrudRepository<InsuranceAgent,Long> {
    Optional<InsuranceAgent> findByLogin(String login);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/auth/InsuranceAgentsRepository.java:InsuranceAgentsRepository.<init>
// Node: JdbcRepository
