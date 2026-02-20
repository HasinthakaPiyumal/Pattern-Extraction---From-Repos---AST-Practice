// Cluster 27

// Node: asList
package pl.altkom.asc.lab.micronaut.poc.dashboard.init;

import lombok.Builder;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.LocalDateRange;
import pl.altkom.asc.lab.micronaut.poc.dashboard.domain.PolicyDocument;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

public class PolicyGenerator {
    private final LocalDateRange generationPeriod;
    private final List<String> agents;
    private final List<String> products;
    private List<String> policyHolders = Arrays.asList(
            "Mike Smith", "Tim Jones", "Berry Cline", "Marion Jones", "Larry Bird",
            "Tara Zane", "Leon Moulder", "Dana Savic", "Evelyn Crowford", "Andrews Eldritch"
    );

    @Builder
    public PolicyGenerator(LocalDateRange generationPeriod, List<String> agents, List<String> products) {
        this.generationPeriod = generationPeriod;
        this.agents = agents;
        this.products = products;
    }

    public List<PolicyDocument> generate() {
        List<PolicyDocument> policies = new ArrayList<>();

        LocalDate salesDate = generationPeriod.getFrom();

        while (!salesDate.isAfter(generationPeriod.getTo())) {
            final LocalDate theDate = salesDate;
            agents.forEach(agent ->
                products.forEach(product -> policies.addAll(generatePolicies(theDate, agent, product)))
            );
            salesDate = salesDate.plusDays(7);
        }

        return policies;
    }

    private List<PolicyDocument> generatePolicies(LocalDate salesDate, String agent, String product) {
        List<PolicyDocument> policiesForDay = new ArrayList<>();
        int numberOfPolicies = randomIntFromRange(1,2);
        for (int i=0; i<numberOfPolicies; i++) {
            PolicyDocument policy = new PolicyDocument(
                    policyNumber(i, salesDate, agent, product),
                    salesDate,
                    salesDate.plusYears(1).minusDays(1),
                    randomHolder(),
                    product,
                    randomPremium(product),
                    agent
            );
            policiesForDay.add(policy);
        }
        return policiesForDay;
    }

    private BigDecimal randomPremium(String product) {
        return new BigDecimal("1000.00");
    }

    private String randomHolder() {
        return policyHolders.get(randomIntFromRange(0,policyHolders.size()-1));
    }

    private String policyNumber(int i,LocalDate salesDate, String agent, String product) {
        return salesDate.getYear() + "/" + salesDate.getMonthValue() + "/" + salesDate.getDayOfMonth()
                + "/" + products.indexOf(product) + "/" + agents.indexOf(agent) + "/" + i;
    }

    private int randomIntFromRange(int min, int max) {
        return ThreadLocalRandom.current().nextInt(min,max);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/dashboard-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/dashboard/init/PolicyGenerator.java:PolicyGenerator.<init>
// Node: PolicyGenerator
// Node: addAll
package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.bson.codecs.pojo.annotations.BsonCreator;
import org.bson.codecs.pojo.annotations.BsonProperty;

import java.math.BigDecimal;


@Getter
@NoArgsConstructor
public class Cover {
    private String code;
    private String name;
    private String description;
    private boolean optional;
    private BigDecimal sumInsured;

    @BsonCreator
    public Cover(
            @BsonProperty("code") String code,
            @BsonProperty("name") String name,
            @BsonProperty("description") String description,
            @BsonProperty("optional") boolean optional,
            @BsonProperty("sumInsured") BigDecimal sumInsured) {
        this.code = code;
        this.name = name;
        this.description = description;
        this.optional = optional;
        this.sumInsured = sumInsured;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/domain/Cover.java:Cover.<init>
// Node: BsonProperty
package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.bson.codecs.pojo.annotations.BsonCreator;
import org.bson.codecs.pojo.annotations.BsonProperty;

import java.util.Arrays;
import java.util.List;

@NoArgsConstructor
@Getter
public class ChoiceQuestion extends Question {
    private List<Choice> choices;

    @BsonCreator
    public ChoiceQuestion(
            @BsonProperty("code") String code,
            @BsonProperty("index") int index,
            @BsonProperty("text") String text,
            @BsonProperty("choices") List<Choice> choices) {
        super(code, index, text);
        this.choices = choices;
    }

    public static List<Choice> yesNoChoice() {
        return Arrays.asList(
                new Choice("YES", "Yes"),
                new Choice("NO", "No")
        );
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/domain/ChoiceQuestion.java:ChoiceQuestion.<init>
// Node: ChoiceQuestion
// Node: yesNoChoice
// Node: Choice
package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.bson.codecs.pojo.annotations.BsonCreator;
import org.bson.codecs.pojo.annotations.BsonProperty;

@NoArgsConstructor
@Getter
public class NumericQuestion extends Question {
    @BsonCreator
    public NumericQuestion(@BsonProperty("code") String code,
                           @BsonProperty("index") int index,
                           @BsonProperty("text") String text) {
        super(code, index, text);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/domain/NumericQuestion.java:NumericQuestion.<init>
// Node: NumericQuestion
package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.bson.codecs.pojo.annotations.BsonCreator;
import org.bson.codecs.pojo.annotations.BsonProperty;

@NoArgsConstructor
@Getter
public class DateQuestion extends Question {
    @BsonCreator
    public DateQuestion(
            @BsonProperty("code") String code,
            @BsonProperty("index") int index,
            @BsonProperty("text") String text) {
        super(code, index, text);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/domain/DateQuestion.java:DateQuestion.<init>
// Node: DateQuestion
package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.bson.codecs.pojo.annotations.BsonCreator;
import org.bson.codecs.pojo.annotations.BsonDiscriminator;
import org.bson.codecs.pojo.annotations.BsonProperty;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Getter
@NoArgsConstructor
@BsonDiscriminator
public class Product {
    private String code;
    private String name;
    private String image;
    private String description;
    private List<Cover> covers;
    private List<Question> questions;
    private int maxNumberOfInsured;
    private String icon;

    @BsonCreator
    public Product(
            @BsonProperty("code") String code,
            @BsonProperty("name") String name,
            @BsonProperty("image") String image,
            @BsonProperty("description") String description,
            @BsonProperty("covers") List<Cover> covers,
            @BsonProperty("questions") List<Question> questions,
            @BsonProperty("maxNumberOfInsured") int maxNumberOfInsured,
            @BsonProperty("icon") String icon) {
        this.code = code;
        this.name = name;
        this.image = image;
        this.description = description;
        this.covers = covers;
        this.questions = questions;
        this.maxNumberOfInsured = maxNumberOfInsured;
        this.icon = icon;
    }

    public Product(String code, String name, String image, String description, int maxNumberOfInsured, String icon) {
        this.code = code;
        this.name = name;
        this.image = image;
        this.description = description;
        this.maxNumberOfInsured = maxNumberOfInsured;
        this.covers = new ArrayList<>();
        this.questions = new ArrayList<>();
        this.icon = icon;
    }

    public void addCover(String code, String name, String description, boolean isOptional, BigDecimal sumInsured) {
        covers.add(new Cover(code, name, description, isOptional, sumInsured));
    }

    public void addQuestions(List<Question> questions) {
        if (this.questions == null) {
            this.questions = new ArrayList<>();
        }
        this.questions.addAll(questions);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/domain/Product.java:Product.<init>
// Node: Product
// Node: addCover
// Node: addQuestions
package pl.altkom.asc.lab.micronaut.poc.product.service.domain;

import lombok.Getter;
import lombok.NoArgsConstructor;
import org.bson.codecs.pojo.annotations.BsonCreator;
import org.bson.codecs.pojo.annotations.BsonProperty;

@Getter
@NoArgsConstructor
public class Choice {
    private String code;
    private String label;

    @BsonCreator
    public Choice(@BsonProperty("code") String code, @BsonProperty("label") String label) {
        this.code = code;
        this.label = label;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/domain/Choice.java:Choice.<init>
package pl.altkom.asc.lab.micronaut.poc.product.service.init;

import pl.altkom.asc.lab.micronaut.poc.product.service.domain.Choice;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.ChoiceQuestion;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.NumericQuestion;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.Product;

import java.math.BigDecimal;
import java.util.Arrays;

class DemoProductsFactory {

    static Product travel() {
        Product p = new Product(
                "TRI",
                "Safe Traveller",
                "/static/travel.jpg",
                "Travel insurance",
                10,
                "plane");

        p.addCover("C1", "Luggage", "", false, new BigDecimal("5000"));
        p.addCover("C2", "Illness", "", false, new BigDecimal("5000"));
        p.addCover("C3", "Assistance", "", true, null);

        p.addQuestions(Arrays.asList(
                new ChoiceQuestion("DESTINATION", 1, "Destination", Arrays.asList(
                        new Choice("EUR", "Europe"),
                        new Choice("WORLD", "World"),
                        new Choice("PL", "Poland")
                )),
                new NumericQuestion("NUM_OF_ADULTS", 2, "Number of adults"),
                new NumericQuestion("NUM_OF_CHILDREN", 3, "Number of children")
        ));
        return p;
    }

    static Product house() {
        Product p = new Product(
                "HSI",
                "Happy House",
                "/static/house.jpg",
                "House insurance",
                5,
                "building");

        p.addCover("C1", "Fire", "", false, new BigDecimal("200000"));
        p.addCover("C2", "Flood", "", false, new BigDecimal("100000"));
        p.addCover("C3", "Theft", "", false, new BigDecimal("50000"));
        p.addCover("C4", "Assistance", "", true, null);

        p.addQuestions(Arrays.asList(
                new ChoiceQuestion("TYP", 1, "Apartment / House", Arrays.asList(
                        new Choice("APT", "Apartment"),
                        new Choice("HOUSE", "House")
                )),
                new NumericQuestion("AREA", 2, "Area"),
                new NumericQuestion("NUM_OF_CLAIM", 3, "Number of claims in last 5 years"),
                new ChoiceQuestion("FLOOD", 4, "Located in flood risk area", ChoiceQuestion.yesNoChoice())
        ));
        return p;
    }

    static Product farm() {
        Product p = new Product(
                "FAI",
                "Happy farm",
                "/static/farm.jpg",
                "Farm insurance",
                1,
                "apple");

        p.addCover("C1", "Crops", "", false, new BigDecimal("200000"));
        p.addCover("C2", "Flood", "", false, new BigDecimal("100000"));
        p.addCover("C3", "Fire", "", false, new BigDecimal("50000"));
        p.addCover("C4", "Equipment", "", true, new BigDecimal("300000"));

        p.addQuestions(Arrays.asList(
                new ChoiceQuestion("TYP", 1, "Cultivation type", Arrays.asList(
                        new Choice("ZB", "Crop"),
                        new Choice("KW", "Vegetable")
                )),
                new NumericQuestion("AREA", 2, "Area"),
                new NumericQuestion("NUM_OF_CLAIM", 3, "Number of claims in last 5 years"),
                new ChoiceQuestion("FLOOD", 4, "Located in flood risk area", ChoiceQuestion.yesNoChoice())
        ));
        return p;
    }

    static Product car() {
        Product p = new Product(
                "CAR",
                "Happy Driver",
                "/static/car.jpg",
                "Car insurance",
                1,
                "car");

        p.addCover("C1", "Assistance", "", true, null);
        p.addQuestions(Arrays.asList(
                new NumericQuestion("NUM_OF_CLAIM", 3, "Number of claims in last 5 years")
        ));

        return p;
    }
}


// Node: blockingGet
// Node: isValid
package pl.altkom.asc.lab.micronaut.poc.chat.service.infrastructure.adapters.web;

import io.micronaut.websocket.WebSocketBroadcaster;
import io.micronaut.websocket.WebSocketSession;
import io.micronaut.websocket.annotation.OnClose;
import io.micronaut.websocket.annotation.OnMessage;
import io.micronaut.websocket.annotation.OnOpen;
import io.micronaut.websocket.annotation.ServerWebSocket;
import lombok.extern.slf4j.Slf4j;

import java.util.function.Predicate;

@Slf4j
@ServerWebSocket("/ws/chat/{topic}/{username}")
public class ChatWebSocket {

    private WebSocketBroadcaster broadcaster;

    public ChatWebSocket(WebSocketBroadcaster broadcaster) {
        this.broadcaster = broadcaster;
    }

    @OnOpen
    public void onOpen(String topic, String username, WebSocketSession session) {
        String msg = "[" + username + "] Joined!";
        log.info(msg);
        broadcaster.broadcastSync(formatStartCloseMessages(msg), isValid(topic, session));
    }

    @OnMessage
    public void onMessage(
            String topic,
            String username,
            String message,
            WebSocketSession session) {
        String msg = "[" + username + "] " + message;
        log.info(msg);
        broadcaster.broadcastSync(message, isValid(topic, session));
    }

    @OnClose
    public void onClose(
            String topic,
            String username,
            WebSocketSession session) {
        String msg = "[" + username + "] Disconnected!";
        log.info(msg);
        broadcaster.broadcastSync(formatStartCloseMessages(msg), isValid(topic, session));
    }

    private Predicate<WebSocketSession> isValid(String topic, WebSocketSession session) {
        return s -> s != session && topic.equalsIgnoreCase(s.getUriVariables().get("topic", String.class, null));
    }

    private String formatStartCloseMessages(String msg) {
        return "<p>" + msg + "</p>";
    }
}


// Node: equalsIgnoreCase
// Node: getUriVariables
package pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Builder
@Getter
@NoArgsConstructor
@AllArgsConstructor
public class PolicyView {
    private String number;
    private LocalDate dateFrom;
    private LocalDate dateTo;
    private String policyHolder;

    public PolicyView(String number) {
        this.number = number;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-search-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/policy/search/readmodel/PolicyView.java:PolicyView.<init>
// Node: PolicyView
package pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.mock;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.context.annotation.Requires;
import io.micronaut.context.env.Environment;
import io.reactivex.Maybe;
import pl.altkom.asc.lab.micronaut.poc.policy.search.infrastructure.adapters.db.ElasticPolicyViewRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyView;
import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyViewRepository;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQuery;

import javax.inject.Singleton;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Replaces(ElasticPolicyViewRepository.class)
@Requires(env = Environment.TEST)
@Singleton
public class MockPolicyViewRepository implements PolicyViewRepository {

    private Map<String, PolicyView> policyMap = init();

    private Map<String, PolicyView> init() {
        Map<String, PolicyView> map = new LinkedHashMap<>();

        map.put("1234", new PolicyView(
                "1234",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1235", new PolicyView(
                "1235",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1236", new PolicyView("1236",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );
        map.put("1237", new PolicyView("1237",
                LocalDate.of(2019, 1, 1),
                LocalDate.of(2020, 1, 1),
                "Xxxx Yyyy")
        );

        return map;
    }

    @Override
    public Maybe<List<PolicyView>> findAll(FindPolicyQuery query) {
        return Maybe.just(new ArrayList<>(policyMap.values()));
    }

    @Override
    public void save(PolicyView policy) {
        policyMap.put(policy.getNumber(), policy);
    }
}


package pl.altkom.asc.lab.micronaut.poc;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;

import io.micronaut.context.ApplicationContext;
import io.micronaut.runtime.server.EmbeddedServer;

public class PolicySearchControllerTest {

    private static EmbeddedServer server;
    private static PolicySearchTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(PolicySearchTestClient.class, server.getURL());
    }

    @Test
    public void testPolicies() {
        FindPolicyQueryResult policies = client.policies("1234").blockingGet();

        Assertions.assertNotNull(policies);
        Assertions.assertNotNull(policies.getPolicies());
        Assertions.assertFalse(policies.getPolicies().isEmpty());
    }

    @AfterAll
    public static void cleanup() {
        if (server != null)
            server.stop();

    }
}


// Node: testPolicies
// Node: getPolicies
// Node: assertFalse
package pl.altkom.asc.lab.micronaut.poc.policy.search.queries.findpolicy;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.search.readmodel.PolicyView;
import pl.altkom.asc.lab.micronaut.poc.policy.search.service.api.v1.queries.findpolicy.FindPolicyQueryResult;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class PolicyQueryResultAssemblerTest {

    @Test
    public void shouldSortResultsByDescendingStartDate() {
        PolicyQueryResultAssembler assembler = new PolicyQueryResultAssembler();
        List<PolicyView> policies = new ArrayList<>(Arrays.asList(
                new PolicyView("1", LocalDate.of(2015,11,1), LocalDate.of(2016,10,30), "Tom Hanks"),
                new PolicyView("2", LocalDate.of(2015,11,3), LocalDate.of(2016,10,30), "Alanis Morissette"),
                new PolicyView("3", LocalDate.of(2015,11,2), LocalDate.of(2016,10,30), "Andy Warhol")
        ));

        FindPolicyQueryResult result = assembler.constructResult(policies);

        Assertions.assertTrue(result.getPolicies().get(0).getNumber().equalsIgnoreCase("2"));
        Assertions.assertTrue(result.getPolicies().get(1).getNumber().equalsIgnoreCase("3"));
        Assertions.assertTrue(result.getPolicies().get(2).getNumber().equalsIgnoreCase("1"));
    }


    @Test
    public void shouldHandleNullStartDatesAndPlaceThemAtTheEnd() {
        PolicyQueryResultAssembler assembler = new PolicyQueryResultAssembler();
        List<PolicyView> policies = new ArrayList<>(Arrays.asList(
                new PolicyView("1", LocalDate.of(2015,11,1), LocalDate.of(2016,10,30), "Tom Hanks"),
                new PolicyView("2", null, null, "Alanis Morissette"),
                new PolicyView("3", LocalDate.of(2015,11,2), LocalDate.of(2016,10,30), "Andy Warhol")
        ));

        FindPolicyQueryResult result = assembler.constructResult(policies);

        Assertions.assertTrue(result.getPolicies().get(2).getNumber().equalsIgnoreCase("2"));

    }
}


// Node: shouldSortResultsByDescendingStartDate
// Node: PolicyQueryResultAssembler
// Node: assertTrue
// Node: shouldHandleNullStartDatesAndPlaceThemAtTheEnd
