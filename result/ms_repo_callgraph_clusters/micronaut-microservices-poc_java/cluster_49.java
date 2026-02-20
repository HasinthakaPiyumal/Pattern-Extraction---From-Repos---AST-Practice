// Cluster 49

package pl.altkom.asc.lab.micronaut.poc.policy.infrastructure.adapters.web;

import io.micronaut.http.HttpStatus;
import io.micronaut.http.annotation.Controller;
import io.micronaut.http.annotation.Get;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.Health;

@Controller("/hello")
public class HelloController {

    @Get
    public HttpStatus index() {
        return HttpStatus.OK;
    }

    @Get("/version")
    public Health version() {
        return new Health("1.0", "OK");
    }
}


// Node: version
// Node: Health
// Node: getCode
package pl.altkom.asc.lab.micronaut.poc.policy;

import io.micronaut.http.HttpStatus;
import io.micronaut.http.annotation.Get;
import io.micronaut.http.client.annotation.Client;
import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.Health;

@Client(id = "/policy-service", path = "/hello")
public interface HelloTestClient {

    @Get
    HttpStatus index();

    @Get("/version")
    Health version();
}

// Node: repos/cloned_ms_repos/micronaut-microservices-poc/policy-service/src/test/java/pl/altkom/asc/lab/micronaut/poc/policy/HelloTestClient.java:HelloTestClient.<init>
package pl.altkom.asc.lab.micronaut.poc.policy;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import pl.altkom.asc.lab.micronaut.poc.policy.service.api.v1.Health;

import io.micronaut.context.ApplicationContext;
import io.micronaut.http.HttpStatus;
import io.micronaut.runtime.server.EmbeddedServer;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class HelloControllerTest {

    private static EmbeddedServer server;
    private static HelloTestClient client;

    @BeforeAll
    public static void setup() {
        server = ApplicationContext.run(EmbeddedServer.class);
        client = server.getApplicationContext().createBean(HelloTestClient.class, server.getURL());
    }

    @AfterAll
    public static void cleanup() {
        if (server != null) {
            server.stop();
        }
    }

    @Test
    public void testIndex() {
        assertEquals(HttpStatus.OK, client.index());
    }

    @Test
    public void testVersion() {
        Health actualInfo = client.version();
        Health expectedInfo = new Health("1.0", "OK");

        assertEquals(expectedInfo.toString(), actualInfo.toString());
        assertEquals(expectedInfo.getStatus(), actualInfo.getStatus());
        assertEquals(expectedInfo.getVer(), actualInfo.getVer());
    }
}


// Node: testVersion
// Node: getStatus
// Node: getVer
package pl.altkom.asc.lab.micronaut.poc.auth;

import io.micronaut.security.token.jwt.render.BearerAccessRefreshToken;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.util.Collection;

@NoArgsConstructor
class CustomBearerAccessRefreshToken extends BearerAccessRefreshToken {

    @Getter
    private String avatar;

    CustomBearerAccessRefreshToken(String username,
                                   Collection<String> roles,
                                   Integer expiresIn,
                                   String accessToken,
                                   String refreshToken,
                                   String tokenType,
                                   String avatar) {
        super(username, roles, expiresIn, accessToken, refreshToken, tokenType);
        this.avatar = avatar;

    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/auth-service/src/main/java/pl/altkom/asc/lab/micronaut/poc/auth/CustomBearerAccessRefreshToken.java:CustomBearerAccessRefreshToken.<init>
// Node: CustomBearerAccessRefreshToken
package pl.altkom.asc.lab.micronaut.poc.auth;

import com.nimbusds.jwt.JWTClaimsSet;
import io.micronaut.context.annotation.Replaces;
import io.micronaut.runtime.ApplicationConfiguration;
import io.micronaut.security.authentication.UserDetails;
import io.micronaut.security.token.config.TokenConfiguration;
import io.micronaut.security.token.jwt.generator.claims.ClaimsAudienceProvider;
import io.micronaut.security.token.jwt.generator.claims.JWTClaimsSetGenerator;
import io.micronaut.security.token.jwt.generator.claims.JwtIdGenerator;

import javax.annotation.Nullable;
import javax.inject.Singleton;

@Singleton
@Replaces(bean = JWTClaimsSetGenerator.class)
public class InsuranceAgentJWTClaimsSetGenerator extends JWTClaimsSetGenerator {

    public InsuranceAgentJWTClaimsSetGenerator(TokenConfiguration tokenConfiguration,
                                               @Nullable JwtIdGenerator jwtIdGenerator,
                                               @Nullable ClaimsAudienceProvider claimsAudienceProvider,
                                               @Nullable ApplicationConfiguration applicationConfiguration) {
        super(tokenConfiguration, jwtIdGenerator, claimsAudienceProvider, applicationConfiguration);
    }

    @Override
    protected void populateWithUserDetails(JWTClaimsSet.Builder builder, UserDetails userDetails) {
        super.populateWithUserDetails(builder, userDetails);
        if (userDetails instanceof InsuranceAgentDetails) {
            builder.claim("avatar", ((InsuranceAgentDetails) userDetails).getAvatarUrl());
        }
    }
}


// Node: populateWithUserDetails
// Node: claim
// Node: getAvatarUrl
package pl.altkom.asc.lab.micronaut.poc.auth;

import io.micronaut.context.annotation.Replaces;
import io.micronaut.http.HttpHeaderValues;
import io.micronaut.security.authentication.UserDetails;
import io.micronaut.security.token.jwt.render.AccessRefreshToken;
import io.micronaut.security.token.jwt.render.BearerAccessRefreshToken;
import io.micronaut.security.token.jwt.render.BearerTokenRenderer;

@Replaces(bean = BearerTokenRenderer.class)
public class CustomBearerTokenRenderer extends BearerTokenRenderer {

    private final String BEARER_TOKEN_TYPE = HttpHeaderValues.AUTHORIZATION_PREFIX_BEARER;

    @Override
    public AccessRefreshToken render(UserDetails userDetails, Integer expiresIn, String accessToken, String refreshToken) {
        if (userDetails instanceof InsuranceAgentDetails) {
            return new CustomBearerAccessRefreshToken(
                    userDetails.getUsername(),
                    userDetails.getRoles(),
                    expiresIn,
                    accessToken,
                    refreshToken,
                    BEARER_TOKEN_TYPE,
                    ((InsuranceAgentDetails) userDetails).getAvatarUrl()
            );
        }

        return new BearerAccessRefreshToken(
                userDetails.getUsername(),
                userDetails.getRoles(),
                expiresIn,
                accessToken,
                refreshToken,
                BEARER_TOKEN_TYPE);
    }
}


// Node: render
// Node: getUsername
// Node: getRoles
// Node: BearerAccessRefreshToken
package pl.altkom.asc.lab.micronaut.poc.auth;

import org.junit.jupiter.api.Test;

import javax.inject.Inject;

import io.micronaut.context.annotation.Property;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.HttpStatus;
import io.micronaut.http.client.RxHttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.http.client.exceptions.HttpClientResponseException;
import io.micronaut.runtime.server.EmbeddedServer;
import io.micronaut.security.authentication.UsernamePasswordCredentials;
import io.micronaut.security.token.jwt.render.BearerAccessRefreshToken;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.fail;

@MicronautTest
@Property(name = "micronaut.server.port", value = "-1")
public class LoginTest {
    @Inject
    private EmbeddedServer server;

    @Inject
    @Client("/")
    private RxHttpClient httpClient;

    @Test
    public void canLoginWithValidCredentials() {
        UsernamePasswordCredentials upc = new UsernamePasswordCredentials("jimmy.solid","secret");
        HttpRequest loginRequest = HttpRequest.POST("/login", upc);
        HttpResponse<BearerAccessRefreshToken> rsp = httpClient.toBlocking().exchange(loginRequest, BearerAccessRefreshToken.class);
        
        assertThat(rsp.getStatus().getCode()).isEqualTo(200);
        assertThat(rsp.getBody().get().getUsername()).isEqualTo("jimmy.solid");
    }
    
    
    @Test
    public void cantLoginWithInvalidCredentials() {
        try {
            UsernamePasswordCredentials upc = new UsernamePasswordCredentials("jimmy.solid","secret111");
            HttpRequest loginRequest = HttpRequest.POST("/login", upc);
            HttpResponse<BearerAccessRefreshToken> rsp = httpClient.toBlocking().exchange(loginRequest, BearerAccessRefreshToken.class);
            fail();
        } catch (HttpClientResponseException ex) {
            assertThat(ex.getStatus().getCode()).isEqualTo(HttpStatus.UNAUTHORIZED.getCode());
        }
        
    }

}


// Node: canLoginWithValidCredentials
// Node: UsernamePasswordCredentials
// Node: POST
// Node: toBlocking
// Node: exchange
// Node: assertThat
// Node: isEqualTo
// Node: getBody
// Node: cantLoginWithInvalidCredentials
// Node: fail
package pl.altkom.asc.lab.micronaut.poc.auth;

import org.junit.jupiter.api.Test;

import javax.inject.Inject;

import io.micronaut.context.annotation.Property;
import io.micronaut.http.HttpMethod;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.client.RxHttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.runtime.server.EmbeddedServer;
import io.micronaut.security.authentication.Authentication;
import io.micronaut.security.authentication.UsernamePasswordCredentials;
import io.micronaut.security.token.jwt.render.AccessRefreshToken;
import io.micronaut.security.token.jwt.validator.JwtTokenValidator;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;
import io.reactivex.Flowable;

import static org.assertj.core.api.Assertions.assertThat;

@MicronautTest
@Property(name = "micronaut.server.port", value = "-1")
public class CustomClaimsTest {
    @Inject
    private EmbeddedServer server;

    @Inject
    @Client("/")
    private RxHttpClient httpClient;

    @Test
    public void testCustomClaimsArePresentInJwt() {
        //when:
        HttpRequest request = HttpRequest.create(HttpMethod.POST, "/login")
                .accept(MediaType.APPLICATION_JSON_TYPE)
                .body(new UsernamePasswordCredentials("jimmy.solid", "secret"));
        HttpResponse<AccessRefreshToken> rsp = httpClient.toBlocking().exchange(request, AccessRefreshToken.class);

        //then:
        assertThat(rsp.getStatus().getCode()).isEqualTo(200);
        assertThat(rsp.body()).isNotNull();
        assertThat(rsp.body().getAccessToken()).isNotNull();
        assertThat(rsp.body().getRefreshToken()).isNull();

        //when:
        String accessToken = rsp.body().getAccessToken();
        JwtTokenValidator tokenValidator = server.getApplicationContext().getBean(JwtTokenValidator.class);
        Authentication authentication = Flowable
                .fromPublisher(tokenValidator.validateToken(accessToken,request))
                .blockingFirst();

        //then:
        assertThat(authentication.getAttributes()).isNotNull();
        assertThat(authentication.getAttributes()).containsKey("roles");
        assertThat(authentication.getAttributes()).containsKey("iss");
        assertThat(authentication.getAttributes()).containsKey("exp");
        assertThat(authentication.getAttributes()).containsKey("iat");
        assertThat(authentication.getAttributes()).containsKey("avatar");
        assertThat(authentication.getAttributes().get("avatar")).isEqualTo("static/avatars/jimmy_solid.png");
    }
}


// Node: testCustomClaimsArePresentInJwt
// Node: accept
// Node: body
// Node: isNotNull
// Node: getAccessToken
// Node: getRefreshToken
// Node: isNull
// Node: validateToken
// Node: blockingFirst
// Node: getAttributes
// Node: containsKey
package pl.altkom.asc.lab.micronaut.poc.auth;

import org.junit.jupiter.api.Test;

import javax.inject.Inject;

import io.micronaut.context.annotation.Property;
import io.micronaut.http.HttpMethod;
import io.micronaut.http.HttpRequest;
import io.micronaut.http.HttpResponse;
import io.micronaut.http.MediaType;
import io.micronaut.http.client.RxHttpClient;
import io.micronaut.http.client.annotation.Client;
import io.micronaut.runtime.server.EmbeddedServer;
import io.micronaut.security.authentication.UsernamePasswordCredentials;
import io.micronaut.test.extensions.junit5.annotation.MicronautTest;

import static org.assertj.core.api.Assertions.assertThat;

@MicronautTest
@Property(name = "micronaut.server.port", value = "-1")
public class CustomLoginHandlerTest {
    @Inject
    private EmbeddedServer server;

    @Inject
    @Client("/")
    private RxHttpClient httpClient;

    @Test
    public void customLoginHandler() {
        //when:
        HttpRequest request = HttpRequest.create(HttpMethod.POST, "/login")
                .accept(MediaType.APPLICATION_JSON_TYPE)
                .body(new UsernamePasswordCredentials("jimmy.solid", "secret"));
        HttpResponse<CustomBearerAccessRefreshToken> rsp = httpClient.toBlocking().exchange(request, CustomBearerAccessRefreshToken.class);

        //then:
        assertThat(rsp.getStatus().getCode()).isEqualTo(200);
        assertThat(rsp.body()).isNotNull();
        assertThat(rsp.body().getAccessToken()).isNotNull();
        assertThat(rsp.body().getRefreshToken()).isNull();
        assertThat(rsp.body().getAvatar()).isNotNull();
        assertThat(rsp.body().getAvatar()).isEqualTo("static/avatars/jimmy_solid.png");
    }
}


// Node: customLoginHandler
// Node: getAvatar
package pl.altkom.asc.lab.micronaut.poc.pricing.domain;

import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

@Getter
public class Calculation {

    private String productCode;
    private LocalDate policyFrom;
    private LocalDate policyTo;
    private BigDecimal totalPremium;
    private Map<String, Cover> covers = new HashMap<>();
    private Map<String, Object> subject = new HashMap<>();

    public Calculation(String productCode,
                       LocalDate policyFrom,
                       LocalDate policyTo,
                       Iterable<String> selectedCovers,
                       Map<String, Object> subject) {
        this.productCode = productCode;
        this.policyFrom = policyFrom;
        this.policyTo = policyTo;
        this.totalPremium = BigDecimal.ZERO;
        selectedCovers.forEach(this::zeroPrice);
        this.subject = subject;
    }

    Map<String, Object> toMap() {
        Map<String, Object> context = new HashMap<>();

        context.put("policyFrom", policyFrom);
        context.put("policyTo", policyTo);
        for (Cover cover : covers.values()) {
            context.put(cover.getCode(), cover);
        }
        context.putAll(subject);

        return context;
    }


    void updateTotal() {
        totalPremium = covers
                .values()
                .stream()
                .filter(c -> c.getPrice() != null)
                .map(Cover::getPrice)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
    }

    private void zeroPrice(String cover) {
        covers.put(cover, new Cover(cover, BigDecimal.ZERO));
    }
}


// Node: putAll
package pl.altkom.asc.lab.micronaut.poc.product.service.infrastructure.adapters.web;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.CoverDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.ProductDto;
import pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.questions.*;
import pl.altkom.asc.lab.micronaut.poc.product.service.domain.*;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
final class ProductsAssembler {

    static List<ProductDto> map(List<Product> products) {
        return products.stream()
                .map(ProductsAssembler::map)
                .collect(Collectors.toList());
    }

    static ProductDto map(Product product) {
        return ProductDto.builder()
                .code(product.getCode())
                .name(product.getName())
                .image(product.getImage())
                .description(product.getDescription())
                .covers(mapCovers(product))
                .questions(mapQuestions(product))
                .maxNumberOfInsured(product.getMaxNumberOfInsured())
                .icon(product.getIcon())
                .build();
    }

    private static List<QuestionDto> mapQuestions(Product product) {
        return product.getQuestions().stream()
                .map(ProductsAssembler::mapQuestion)
                .collect(Collectors.toList());
    }

    private static List<CoverDto> mapCovers(Product product) {
        return product.getCovers().stream()
                .map(ProductsAssembler::mapCover)
                .collect(Collectors.toList());
    }

    private static CoverDto mapCover(Cover cover) {
        return new CoverDto(
                cover.getCode(),
                cover.getName(),
                cover.getDescription(),
                cover.isOptional(),
                cover.getSumInsured()
        );
    }

    private static QuestionDto mapQuestion(Question question) {
        QuestionDto dto = mapToNumericIfFit(question);

        dto = dto == null ? mapToDateIfFit(question) : dto;
        dto = dto == null ? mapToChoiceIfFit(question) : dto;

        return dto;
    }

    private static QuestionDto mapToChoiceIfFit(Question question) {
        if (!(question instanceof ChoiceQuestion))
            return null;

        return new ChoiceQuestionDto(question.getCode(), question.getIndex(), question.getText(), mapChoices(question));
    }

    private static List<ChoiceDto> mapChoices(Question question) {
        List<Choice> choices = ((ChoiceQuestion) question).getChoices();

        if (choices == null)
            return new ArrayList<>();

        return choices.stream()
                .map(x -> new ChoiceDto(x.getCode(), x.getLabel()))
                .collect(Collectors.toList());
    }

    private static QuestionDto mapToDateIfFit(Question question) {
        if (!(question instanceof DateQuestion))
            return null;

        return new DateQuestionDto(question.getCode(), question.getIndex(), question.getText());
    }

    private static QuestionDto mapToNumericIfFit(Question question) {
        if (!(question instanceof NumericQuestion))
            return null;

        return new NumericQuestionDto(question.getCode(), question.getIndex(), question.getText());
    }

}


// Node: mapQuestion
// Node: mapToNumericIfFit
// Node: mapToDateIfFit
// Node: mapToChoiceIfFit
// Node: ChoiceQuestionDto
// Node: getIndex
// Node: getText
// Node: mapChoices
// Node: DateQuestionDto
// Node: NumericQuestionDto
package pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.questions;

import java.util.List;

import io.micronaut.core.annotation.Introspected;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Introspected
@NoArgsConstructor
@Getter
public class ChoiceQuestionDto extends QuestionDto {
    private List<ChoiceDto> choices;

    public ChoiceQuestionDto(String code, int index, String text, List<ChoiceDto> choices) {
        super(code, index, text);
        this.choices = choices;
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/api/v1/questions/ChoiceQuestionDto.java:ChoiceQuestionDto.<init>
package pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.questions;

import io.micronaut.core.annotation.Introspected;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Introspected
@NoArgsConstructor
@Getter
public class NumericQuestionDto extends QuestionDto {
    public NumericQuestionDto(String code, int index, String text) {
        super(code, index, text);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/api/v1/questions/NumericQuestionDto.java:NumericQuestionDto.<init>
package pl.altkom.asc.lab.micronaut.poc.product.service.api.v1.questions;

import io.micronaut.core.annotation.Introspected;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Introspected
@NoArgsConstructor
@Getter
public class DateQuestionDto extends QuestionDto {
    public DateQuestionDto(String code, int index, String text) {
        super(code, index, text);
    }
}


// Node: repos/cloned_ms_repos/micronaut-microservices-poc/product-service-api/src/main/java/pl/altkom/asc/lab/micronaut/poc/product/service/api/v1/questions/DateQuestionDto.java:DateQuestionDto.<init>
