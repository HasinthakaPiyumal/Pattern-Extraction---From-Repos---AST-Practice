// Cluster 16

package pl.altkom.asc.lab.micronaut.poc.policy.commands;

import pl.altkom.asc.lab.micronaut.poc.command.bus.CommandHandler;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.AgentRef;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Offer;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Person;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.Policy;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyFactory;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.PolicyRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.kafka.EventPublisher;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.dto.PolicyDto;

import java.time.LocalDate;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import lombok.RequiredArgsConstructor;

@Singleton
@RequiredArgsConstructor
public class CreatePolicyHandler implements CommandHandler<CreatePolicyResult, CreatePolicyCommand> {

    private final PolicyRepository policyRepository;
    private final OfferRepository offerRepository;
    private final PolicyFactory policyFactory = new PolicyFactory();
    private final EventPublisher eventPublisher;

    @Transactional
    @Override
    public CreatePolicyResult handle(CreatePolicyCommand cmd) {
        //get offer
        Offer offer = offerRepository.getByNumber(cmd.getOfferNumber());

        //if offer not expired and not already converted
        if (offer.isExpired(LocalDate.now())) {
            throw new RuntimeException("Offer has expired");
        }

        //create policy from offer
        Person policyHolder = new Person(cmd.getPolicyHolder().getFirstName(), cmd.getPolicyHolder().getLastName(), cmd.getPolicyHolder().getTaxId());
        AgentRef agent = AgentRef.of(cmd.getAgentLogin());
        Policy policy = policyFactory.fromOffer(offer, policyHolder, agent);

        //save policy and update offer
        policyRepository.save(policy);

        //publish events
        eventPublisher.policyRegisteredEvent(policy.getNumber(), createEvent(policy));

        return new CreatePolicyResult(policy.getNumber());
    }

    private PolicyRegisteredEvent createEvent(Policy policy) {
        return new PolicyRegisteredEvent(
                new PolicyDto(
                        policy.getNumber(),
                        policy.versions().lastVersion().getVersionValidityPeriod().getFrom(),
                        policy.versions().lastVersion().getVersionValidityPeriod().getTo(),
                        policy.versions().lastVersion().getPolicyHolder().getFullName(),
                        policy.versions().lastVersion().getProductCode(),
                        policy.versions().lastVersion().getTotalPremiumAmount(),
                        null
                )
        );
    }
}


// Node: handle
// Node: getByNumber
// Node: getOfferNumber
// Node: getFirstName
// Node: getLastName
// Node: getTaxId
// Node: getAgentLogin
// Node: policyRegisteredEvent
// Node: CreatePolicyResult
// Node: policyTerminatedEvent
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.kafka;

import io.micronaut.configuration.kafka.annotation.KafkaClient;
import io.micronaut.configuration.kafka.annotation.KafkaKey;
import io.micronaut.configuration.kafka.annotation.Topic;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyTerminatedEvent;

@KafkaClient
public interface EventPublisher {

    @Topic("policy-registered")
    void policyRegisteredEvent(@KafkaKey String policyNumber, PolicyRegisteredEvent event);

    @Topic("policy-terminated")
    void policyTerminatedEvent(@KafkaKey String policyNumber, PolicyTerminatedEvent event);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/infrastructure/adapters/kafka/EventPublisher.java:EventPublisher.<init>
// Node: Topic
package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.mock;

import pl.altkom.asc.lab.micronaut.poc.policy.domain.Offer;
import pl.altkom.asc.lab.micronaut.poc.policy.domain.OfferRepository;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import javax.inject.Singleton;
import javax.transaction.Transactional;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;

@Replaces(OfferRepository.class)
@Requires(env = Environment.TEST)
@Singleton
public class MockOfferRepository implements OfferRepository {

    private Map<String, Offer> map = new ConcurrentHashMap<>();

    @Transactional
    @Override
    public Offer save(Offer offer) {
        map.put(offer.getNumber(), offer);
        return offer;
    }

    @Transactional
    @Override
    public Offer getByNumber(String number) {
        return map.get(number);
    }

}


package pl.altkom.asc.lab.micronaut.poc.policy.domain;

import io.micronaut.data.annotation.Repository;
import io.micronaut.data.repository.GenericRepository;

@Repository
public interface OfferRepository extends GenericRepository<Offer, Long> {
    Offer getByNumber(String number);

    Offer save(Offer offer);
}




// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/domain/OfferRepository.java:OfferRepository.<init>
package pl.altkom.asc.lab.micronaut.poc.pricing.intrastructure.adapters.web;

import pl.altkom.asc.lab.micronaut.poc.pricing.commands.CalculatePriceHandler;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.PricingOperations;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceCommand;
import pl.altkom.asc.lab.micronaut.poc.pricing.service.api.v1.commands.calculateprice.CalculatePriceResult;

import io.micronaut.http.annotation.Controller;
import io.micronaut.scheduling.TaskExecutors;
import io.micronaut.scheduling.annotation.ExecuteOn;
import io.micronaut.validation.Validated;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Controller("/pricing")
@Validated
@RequiredArgsConstructor
@Slf4j
public class PricingController implements PricingOperations {

    private final CalculatePriceHandler calculatePriceHandler;

    @ExecuteOn(TaskExecutors.IO)
    @Override
    public CalculatePriceResult calculatePrice(CalculatePriceCommand cmd) {
        return calculatePriceHandler.handle(cmd);
    }
}


package pl.altkom.asc.lab.micronaut.poc.dashboard.domain;

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;

@KafkaListener(clientId = "policy-registered-dashboard-listener", offsetReset = OffsetReset.EARLIEST)
@RequiredArgsConstructor
public class PolicyRegisteredListener {

    private final PolicyRepository policyRepository;

    @Topic("policy-registered")
    void onPolicyRegistered(PolicyRegisteredEvent event) {
        policyRepository.save(new PolicyDocument(
                event.getPolicy().getNumber(),
                event.getPolicy().getFrom(),
                event.getPolicy().getTo(),
                event.getPolicy().getPolicyHolder(),
                event.getPolicy().getProductCode(),
                event.getPolicy().getTotalPremium(),
                event.getPolicy().getAgentLogin()
        ));
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/domain/PolicyRegisteredListener.java:PolicyRegisteredListener.<init>
// Node: KafkaListener
package pl.altkom.asc.lab.micronaut.poc.payment.domain;

import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.dto.PolicyDto;

import java.util.Optional;

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
@KafkaListener(offsetReset = OffsetReset.EARLIEST)
public class PolicyRegisteredListener {

    private final PolicyAccountRepository policyAccountRepository;
    private final PolicyAccountNumberGenerator policyAccountNumberGenerator;

    @Topic("policy-registered")
    void onPolicyRegistered(PolicyRegisteredEvent event) {
        Optional<PolicyAccount> accountOpt = policyAccountRepository.findByPolicyNumber(event.getPolicy().getNumber());

        if (!accountOpt.isPresent())
            createAccount(event.getPolicy());
    }

    private void createAccount(PolicyDto policy) {
        PolicyAccount newAccount = new PolicyAccount(policy.getNumber(), policyAccountNumberGenerator.generate());
        newAccount.expectedPayment(policy.getTotalPremium(),policy.getFrom());
        policyAccountRepository.save(newAccount);
    }

}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/payment-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/payment/domain/PolicyRegisteredListener.java:PolicyRegisteredListener.<init>
package pl.altkom.asc.lab.micronaut.poc.command.bus;

import io.micronaut.context.ApplicationContext;
import io.micronaut.core.reflect.GenericTypeUtils;
import io.micronaut.inject.BeanDefinition;
import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Command;
import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Query;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;

@SuppressWarnings("unchecked")
public class Registry {

    private Map<Class<? extends Command>, CommandProvider> commandProviderMap = new HashMap<>();
    private Map<Class<? extends Query>, QueryProvider> queryProviderMap = new HashMap<>();

    public Registry(ApplicationContext applicationContext) {
        Collection<BeanDefinition<CommandHandler>> commandHandlers = applicationContext.getBeanDefinitions(CommandHandler.class);
        commandHandlers.forEach(x -> registerCommand(applicationContext, x));

        Collection<BeanDefinition<QueryHandler>> queryHandlers = applicationContext.getBeanDefinitions(QueryHandler.class);
        queryHandlers.forEach(x -> registerQuery(applicationContext, x));
    }

    private void registerCommand(ApplicationContext applicationContext, BeanDefinition<CommandHandler> bean) {
        Class<CommandHandler> handlerClass = bean.getBeanType();
        Class<?>[] generics = GenericTypeUtils.resolveInterfaceTypeArguments(handlerClass, CommandHandler.class);
        Class<? extends Command> commandType = (Class<? extends Command>) generics[1];
        commandProviderMap.put(commandType, new CommandProvider(applicationContext, handlerClass));
    }

    private void registerQuery(ApplicationContext applicationContext, BeanDefinition<QueryHandler> bean) {
        Class<QueryHandler> handlerClass = bean.getBeanType();
        Class<?>[] generics = GenericTypeUtils.resolveInterfaceTypeArguments(handlerClass, QueryHandler.class);
        Class<? extends Query> queryType = (Class<? extends Query>) generics[1];
        queryProviderMap.put(queryType, new QueryProvider(applicationContext, handlerClass));
    }

    <R, C extends Command<R>> CommandHandler<R, C> getCmd(Class<C> commandClass) {
        return commandProviderMap.get(commandClass).get();
    }

    <R, C extends Query<R>> QueryHandler<R, C> getQuery(Class<C> commandClass) {
        return queryProviderMap.get(commandClass).get();
    }
}


// Node: getCmd
// Node: getQuery
package pl.altkom.asc.lab.micronaut.poc.command.bus;

import lombok.RequiredArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Command;
import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Query;

import javax.inject.Singleton;

@RequiredArgsConstructor
public class MicronautCommandBus implements CommandBus {

    private final Registry registry;

    @Override
    public <R, C extends Command<R>> R executeCommand(C command) {
        CommandHandler<R, C> commandHandler = (CommandHandler<R, C>) registry.getCmd(command.getClass());
        return commandHandler.handle(command);
    }

    @Override
    public <R, Q extends Query<R>> R executeQuery(Q query) {
        QueryHandler<R, Q> commandHandler = (QueryHandler<R, Q>) registry.getQuery(query.getClass());
        return commandHandler.handle(query);
    }
}


// Node: getClass
package pl.altkom.asc.lab.micronaut.poc.command.bus;

import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Query;

public interface QueryHandler<R, C extends Query<R>> {
    R handle(C var1);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/command-bus/src/main/java/pl/altkom/asc/lab/micronaut/poc/command/bus/QueryHandler.java:QueryHandler.<init>
package pl.altkom.asc.lab.micronaut.poc.command.bus;

import pl.altkom.asc.lab.micronaut.poc.command.bus.api.Command;

public interface CommandHandler<R, C extends Command<R>> {
    R handle(C command);
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/command-bus/src/main/java/pl/altkom/asc/lab/micronaut/poc/command/bus/CommandHandler.java:CommandHandler.<init>
package pl.altkom.asc.lab.micronaut.poc.gateway.client.v1.fallback;

import io.micronaut.retry.annotation.Fallback;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.PolicyOperations;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.createpolicy.CreatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyCommand;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.commands.terminatepolicy.TerminatePolicyResult;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.queries.getpolicydetails.GetPolicyDetailsQueryResult;

import javax.inject.Singleton;
import javax.validation.constraints.NotNull;

@Singleton
@Fallback
public class PolicyGatewayClientFallback implements PolicyOperations {

    @Override
    public GetPolicyDetailsQueryResult get(@NotNull String policyNumber) {
        return GetPolicyDetailsQueryResult.empty();
    }

    @Override
    public CreatePolicyResult create(@NotNull CreatePolicyCommand cmd) {
        return new CreatePolicyResult(null);
    }

    @Override
    public TerminatePolicyResult terminate(@NotNull TerminatePolicyCommand cmd) {
        return TerminatePolicyResult.empty();
    }
}


package pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel;

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyTerminatedEvent;

@KafkaListener(clientId = "policy-terminated-listener", offsetReset = OffsetReset.EARLIEST)
public class PolicyTerminatedListener extends AbstractPolicyListener {

    @Topic("policy-terminated")
    void onPolicyTerminated(PolicyTerminatedEvent event) {
        saveMappedPolicy(event.getPolicy());
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/readmodel/PolicyTerminatedListener.java:PolicyTerminatedListener.<init>
package pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel;

import io.micronaut.configuration.kafka.annotation.KafkaListener;
import io.micronaut.configuration.kafka.annotation.OffsetReset;
import io.micronaut.configuration.kafka.annotation.Topic;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.events.PolicyRegisteredEvent;

@KafkaListener(clientId = "policy-registered-listener", offsetReset = OffsetReset.EARLIEST)
public class PolicyRegisteredListener extends AbstractPolicyListener {

    @Topic("policy-registered")
    void onPolicyRegistered(PolicyRegisteredEvent event) {
        saveMappedPolicy(event.getPolicy());
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/readmodel/PolicyRegisteredListener.java:PolicyRegisteredListener.<init>
