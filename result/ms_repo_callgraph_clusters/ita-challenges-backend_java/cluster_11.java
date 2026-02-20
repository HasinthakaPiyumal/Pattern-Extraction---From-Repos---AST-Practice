// Cluster 11

package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

@FeignClient(name = "itachallenge-challenge", url = "${redirect-api.challenge.url}")
public interface IChallengeClient {

    @GetMapping("/api-docs")
    @CircuitBreaker(name = "itachallenge-challenge", fallbackMethod = "getDefaultChallengeApi")
    String getSwaggerDocs();

    default String getDefaultChallengeApi(Exception exception) throws JsonProcessingException {
        return DefaultApi.getDefaultApi("challenge");
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/main/java/com/itachallenge/document/proxy/IChallengeClient.java:IChallengeClient.<init>
// Node: FeignClient
// Node: CircuitBreaker
// Node: getSwaggerDocs
// Node: getDefaultChallengeApi
// Node: getDefaultApi
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

@FeignClient(name = "itachallenge-auth", url = "${redirect-api.auth.url}")
public interface IAuthClient {

    @GetMapping("/api-docs")
    @CircuitBreaker(name = "itachallenge-auth", fallbackMethod = "getDefaultAuthApi")
    String getSwaggerDocs();

    default String getDefaultAuthApi(Exception exception) throws JsonProcessingException {
        return DefaultApi.getDefaultApi("auth");
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/main/java/com/itachallenge/document/proxy/IAuthClient.java:IAuthClient.<init>
// Node: getDefaultAuthApi
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

@FeignClient(name = "itachallenge-user", url = "${redirect-api.user.url}")
public interface IUserClient {

    @GetMapping("/api-docs")
    @CircuitBreaker(name = "itachallenge-user", fallbackMethod = "getDefaultUserApi")
    String getSwaggerDocs();

    default String getDefaultUserApi(Exception exception) throws JsonProcessingException {
        return DefaultApi.getDefaultApi("user");
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/main/java/com/itachallenge/document/proxy/IUserClient.java:IUserClient.<init>
// Node: getDefaultUserApi
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;

public class DefaultApi {
    public static String getDefaultApi(String apiName) {
        OpenAPI openAPIDefaultAuth = new OpenAPI();
        openAPIDefaultAuth.setInfo(new Info()
                .title("itachallenge-"+apiName.toUpperCase()+" API Documentation")
                .version("1.0")
                .description("API documentation for itachallenge-"+apiName+" is currently unavailable!."));
        ObjectMapper objectMapper = new ObjectMapper();
        try {
            return objectMapper.writeValueAsString(openAPIDefaultAuth);
        } catch (JsonProcessingException e) {
            throw new RuntimeException(e);
        }
    }
}


// Node: OpenAPI
// Node: setInfo
// Node: Info
// Node: version
// Node: ObjectMapper
// Node: writeValueAsString
package com.itachallenge.document.controller;

import com.itachallenge.document.config.OpenApiConfig;
import com.itachallenge.document.service.DocumentService;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;


import java.util.HashMap;
import java.util.Map;

@RestController
@Validated
@RequestMapping
public class DocumentController {

    private final OpenApiConfig openApiConfig;
    private final DocumentService documentService;
    private final Environment env;

    @Value("${spring.application.version}")
    private String version;

    @Value("${spring.application.name}")
    private String appName;

    public DocumentController(OpenApiConfig openApiConfig, DocumentService documentService, Environment env) {
        this.openApiConfig = openApiConfig;
        this.documentService = documentService;
        this.env = env;
    }

    @GetMapping(value = "/api-docs/{apiname}", produces = {"application/json"})
    public String getSelectedOpenAPI(@PathVariable String apiname) {
        OpenAPI openAPI = openApiConfig.allOpenAPI();
        return switch (apiname) {
            case "all" -> openAPI.toString();
            case "auth" -> documentService.getSwaggerAuthDocsStr();
            case "challenge" -> documentService.getSwaggerChallengeDocsStr();
            case "user" -> documentService.getSwaggerUserDocsStr();
            default -> documentService.getSwaggerDefaultDocsStr(apiname);
        };
    }

    @GetMapping("/version")
    public ResponseEntity<Map<String, String>> getVersion() {
        String appVersion = env.getProperty("spring.application.version");
        Map<String, String> versionMap = new HashMap<>();
        versionMap.put("version", appVersion);
        return new ResponseEntity<>(versionMap, HttpStatus.OK);
    }

}


// Node: getSelectedOpenAPI
// Node: allOpenAPI
// Node: getSwaggerAuthDocsStr
// Node: getSwaggerChallengeDocsStr
// Node: getSwaggerUserDocsStr
// Node: getSwaggerDefaultDocsStr
package com.itachallenge.document.service;

import com.itachallenge.document.proxy.*;
import org.springframework.stereotype.Service;


@Service
public class DocumentService implements IDocumentService{
    private final IChallengeClient challengeClient;
    private final IUserClient userClient;
    private final IAuthClient authClient;

    public DocumentService(IChallengeClient challengeClient,
                           IUserClient userClient1,
                           IAuthClient authClient) {
        this.challengeClient = challengeClient;
        this.userClient = userClient1;
        this.authClient = authClient;
    }

    @Override
    public String getSwaggerUserDocsStr() {
        return userClient.getSwaggerDocs();
    }
    @Override
    public String getSwaggerChallengeDocsStr() {
        return challengeClient.getSwaggerDocs();
    }
    @Override
    public String getSwaggerAuthDocsStr() {
        return authClient.getSwaggerDocs();
    }
    @Override
    public String getSwaggerDefaultDocsStr(String apiName) { return DefaultApi.getDefaultApi(apiName);}
}


package com.itachallenge.document.service;

public interface IDocumentService {
    String getSwaggerUserDocsStr();
    String getSwaggerChallengeDocsStr();
    String getSwaggerAuthDocsStr();

    String getSwaggerDefaultDocsStr(String apiName);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/main/java/com/itachallenge/document/service/IDocumentService.java:IDocumentService.<init>
package com.itachallenge.document.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.document.service.DocumentService;
import io.swagger.v3.core.util.Json;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Map;

@Configuration
public class OpenApiConfig {
    private final DocumentService documentService;

    public OpenApiConfig(DocumentService documentService) {
        this.documentService = documentService;
    }

    public static OpenAPI parseOpenApiSpec(String spec) {

        ObjectMapper objectMapper = Json.mapper();
        try {
            return objectMapper.readValue(spec, OpenAPI.class);
        } catch (Exception e) {
            throw new RuntimeException("Error parsing OpenAPI spec: " + e.getMessage());
        }
    }

    @Bean
    public OpenAPI allOpenAPI() {

        String jsonApiSpecChallenge = documentService.getSwaggerChallengeDocsStr();
        String jsonApiSpecUser = documentService.getSwaggerUserDocsStr();
        String jsonApiSpecAuth = documentService.getSwaggerAuthDocsStr();

        OpenAPI challengeApi = parseOpenApiSpec(jsonApiSpecChallenge);
        OpenAPI userApi = parseOpenApiSpec(jsonApiSpecUser);
        OpenAPI authApi = parseOpenApiSpec(jsonApiSpecAuth);

        OpenAPI allApi = new OpenAPI();

        allApi.setInfo(new Info()
                .title("ITA Challenges APIs Documentation")
                .version("1.0")
                .description("Centralized documentation for ITA Challenges APIs. Explore and understand the available services for authentication, challenges, user management, scoring, and more.")
        );
        allApi.setExtensions(Map.of(
                "itachallenge-challenge-api", challengeApi,
                "itachallenge-user-api", userApi,
                "itachallenge-auth-api", authApi
        ));

        return allApi;
    }
}



// Node: setExtensions
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.OpenAPI;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class UserClientImplTest {

    private IUserClient userClient;

    @BeforeEach
    void setUp() {
        userClient = new UserClientImpl(); // Instantiate your implementation class
    }

    @Test
    void testGetSwaggerDocs() {
        // Simulate fetching Swagger documentation from the user service
        String swaggerDocs = userClient.getSwaggerDocs();

        // Assert that the returned value is not null and not empty
        assertNotNull(swaggerDocs);
        assertFalse(swaggerDocs.isEmpty());
    }

    @Test
    void testGetDefaultUserApi() throws JsonProcessingException {
        // Implement the behavior of your getDefaultUserApi method
        String defaultUserApi = userClient.getDefaultUserApi(new RuntimeException("Simulate FeignClient failure"));

        // Implement assertions based on the expected behavior of getDefaultUserApi
        // For example, you can check if the returned string matches your expected JSON structure
        ObjectMapper objectMapper = new ObjectMapper();
        OpenAPI expectedOpenAPI = new OpenAPI();
        expectedOpenAPI.setInfo(new Info()
                .title("itachallenge-User API Documentation")
                .version("1.0")
                .description("API documentation for itachallenge-user is currently unavailable!."));
        String expectedJson = objectMapper.writeValueAsString(expectedOpenAPI);

        assertEquals(expectedJson, defaultUserApi);
    }
}


// Node: testGetSwaggerDocs
// Node: assertFalse
// Node: testGetDefaultUserApi
// Node: assertEquals
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Component;

@Component
public class AuthClientImpl implements IAuthClient {

    @Override
    @CircuitBreaker(name = "itachallenge-auth", fallbackMethod = "getDefaultAuthApi")
    public String getSwaggerDocs() {
        // Simulate fetching Swagger documentation from an external service
        // In a real scenario, you might use Feign or some other mechanism to call an external API
        return "Actual Swagger Docs from External Service";
    }

    @Override
    public String getDefaultAuthApi(Exception exception) throws JsonProcessingException {
        // Fallback method for getSwaggerDocs
        // You can customize the fallback behavior as needed
        OpenAPI openAPIDefaultAuth = new OpenAPI();
        openAPIDefaultAuth.setInfo(new Info()
                .title("itachallenge-Auth API Documentation")
                .version("1.0")
                .description("API documentation for itachallenge-auth is currently unavailable!."));

        ObjectMapper objectMapper = new ObjectMapper();
        return objectMapper.writeValueAsString(openAPIDefaultAuth);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/test/java/com/itachallenge/document/proxy/AuthClientImpl.java:AuthClientImpl.<init>
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Component;

@Component
public class ChallengeClientImpl implements IChallengeClient {

    @Override
    @CircuitBreaker(name = "itachallenge-challenge", fallbackMethod = "getDefaultChallengeApi")
    public String getSwaggerDocs() {
        // Simulate fetching Swagger documentation from an external service
        // In a real scenario, you might use Feign or some other mechanism to call an external API
        return "Actual Swagger Docs from Challenge Service";
    }

    @Override
    public String getDefaultChallengeApi(Exception exception) throws JsonProcessingException {
        // Fallback method for getSwaggerDocs
        // You can customize the fallback behavior as needed
        OpenAPI openAPIDefaultChallenge = new OpenAPI();
        openAPIDefaultChallenge.setInfo(new Info()
                .title("itachallenge-Challenge API Documentation")
                .version("1.0")
                .description("API documentation for itachallenge-challenge is currently unavailable!."));

        ObjectMapper objectMapper = new ObjectMapper();
        return objectMapper.writeValueAsString(openAPIDefaultChallenge);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/test/java/com/itachallenge/document/proxy/ChallengeClientImpl.java:ChallengeClientImpl.<init>
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.OpenAPI;
import org.springframework.stereotype.Component;

@Component
public class UserClientImpl implements IUserClient {

    @Override
    @CircuitBreaker(name = "itachallenge-user", fallbackMethod = "getDefaultUserApi")
    public String getSwaggerDocs() {
        // Simulate fetching Swagger documentation from an external service
        // In a real scenario, you might use Feign or some other mechanism to call an external API
        return "Actual Swagger Docs from User Service";
    }

    @Override
    public String getDefaultUserApi(Exception exception) throws JsonProcessingException {
        // Fallback method for getSwaggerDocs
        // You can customize the fallback behavior as needed
        OpenAPI openAPIDefaultUser = new OpenAPI();
        openAPIDefaultUser.setInfo(new Info()
                .title("itachallenge-User API Documentation")
                .version("1.0")
                .description("API documentation for itachallenge-user is currently unavailable!."));

        ObjectMapper objectMapper = new ObjectMapper();
        return objectMapper.writeValueAsString(openAPIDefaultUser);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/test/java/com/itachallenge/document/proxy/UserClientImpl.java:UserClientImpl.<init>
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class AuthClientImplTest {

    private AuthClientImpl authClient;

    @BeforeEach
    void setUp() {
        authClient = new AuthClientImpl(); // Instanciate your implementation class
    }

    @Test
    void testGetSwaggerDocs() {
        /// Simulate fetching Swagger documentation from an external service
        String swaggerDocs = authClient.getSwaggerDocs();

        // Assert that the returned value is not null or empty
        assertNotNull(swaggerDocs);
        Assertions.assertFalse(swaggerDocs.isEmpty());
    }

    @Test
    void testGetDefaultAuthApi() throws JsonProcessingException {
        // Implement the behavior of your getDefaultAuthApi method
        String defaultAuthApi = authClient.getDefaultAuthApi(new RuntimeException("Simulate FeignClient failure"));

        // Implement assertions based on the expected behavior of getDefaultAuthApi
        // For example, you can check if the returned string matches your expected JSON structure
        ObjectMapper objectMapper = new ObjectMapper();
        OpenAPI expectedOpenAPI = new OpenAPI();
        expectedOpenAPI.setInfo(new Info()
                .title("itachallenge-Auth API Documentation")
                .version("1.0")
                .description("API documentation for itachallenge-auth is currently unavailable!."));
        String expectedJson = objectMapper.writeValueAsString(expectedOpenAPI);

        assertEquals(expectedJson, defaultAuthApi);
    }
}

// Node: testGetDefaultAuthApi
package com.itachallenge.document.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.OpenAPI;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;

public class ChallengeClientImplTest {

    private IChallengeClient challengeClient;

    @BeforeEach
    void setUp() {
        challengeClient = new ChallengeClientImpl(); // Instantiate your implementation class
    }

    @Test
    void testGetSwaggerDocs() {
        // Simulate fetching Swagger documentation from the challenge service
        String swaggerDocs = challengeClient.getSwaggerDocs();

        // Assert that the returned value is not null and not empty
        assertNotNull(swaggerDocs);
        assertFalse(swaggerDocs.isEmpty());
    }

    @Test
    void testGetDefaultChallengeApi() throws JsonProcessingException {
        // Implement the behavior of your getDefaultChallengeApi method
        String defaultChallengeApi = challengeClient.getDefaultChallengeApi(new RuntimeException("Simulate FeignClient failure"));

        // Implement assertions based on the expected behavior of getDefaultChallengeApi
        // For example, you can check if the returned string matches your expected JSON structure
        ObjectMapper objectMapper = new ObjectMapper();
        OpenAPI expectedOpenAPI = new OpenAPI();
        expectedOpenAPI.setInfo(new Info()
                .title("itachallenge-Challenge API Documentation")
                .version("1.0")
                .description("API documentation for itachallenge-challenge is currently unavailable!."));
        String expectedJson = objectMapper.writeValueAsString(expectedOpenAPI);

        assertEquals(expectedJson, defaultChallengeApi);
    }
}


// Node: testGetDefaultChallengeApi
package com.itachallenge.document.controller;

import com.itachallenge.document.config.OpenApiConfig;
import com.itachallenge.document.service.DocumentService;
import io.swagger.v3.oas.models.OpenAPI;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.TestPropertySource;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.when;

@TestPropertySource(locations = "classpath:itachallenge-document/src/test/resources/application.yml")
class DocumentControllerTest {

    @Mock
    private OpenApiConfig openApiConfig;

    @Mock
    private DocumentService documentService;

    @Mock
    private Environment env;

    @InjectMocks
    private DocumentController documentController;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        documentController = new DocumentController(openApiConfig, documentService, env);
    }

    @Test
    void shouldReturnOpenAPIForAll() {
        // Arrange
        String expectedAuthDocs = "Auth Swagger Docs";
        String expectedChallengeDocs = "Challenge Swagger Docs";
        String expectedUserDocs = "User Swagger Docs";

        when(documentService.getSwaggerAuthDocsStr()).thenReturn(expectedAuthDocs);
        when(documentService.getSwaggerChallengeDocsStr()).thenReturn(expectedChallengeDocs);
        when(documentService.getSwaggerUserDocsStr()).thenReturn(expectedUserDocs);

        OpenAPI mockOpenAPI = new OpenAPI();
        when(openApiConfig.allOpenAPI()).thenReturn(mockOpenAPI);

        // Act and Assert for "auth"
        String authResult = documentController.getSelectedOpenAPI("auth");
        assertEquals(expectedAuthDocs, authResult);

        // Act and Assert for "challenge"
        String challengeResult = documentController.getSelectedOpenAPI("challenge");
        assertEquals(expectedChallengeDocs, challengeResult);


        // Act and Assert for "user"
        String userResult = documentController.getSelectedOpenAPI("user");
        assertEquals(expectedUserDocs, userResult);

        // Act and Assert for default case
        String defaultResult = documentController.getSelectedOpenAPI("all");
        assertEquals(mockOpenAPI.toString(), defaultResult);
    }


    @Test
    void shouldReturnCorrectAppVersion() {
        // Preparar
        String expectedVersion = "1.0.0-RELEASE";
        when(env.getProperty("spring.application.version")).thenReturn(expectedVersion);

        // Actuar
        ResponseEntity<Map<String, String>> responseEntity = documentController.getVersion();

        // Afirmar
        assertEquals(HttpStatus.OK, responseEntity.getStatusCode());
        Map<String, String> responseBody = responseEntity.getBody();
        Assertions.assertNotNull(responseBody);
        assertEquals(expectedVersion, responseBody.get("version"));
    }
}

// Node: shouldReturnOpenAPIForAll
package com.itachallenge.document.service;

import com.itachallenge.document.proxy.IAuthClient;
import com.itachallenge.document.proxy.IChallengeClient;
import com.itachallenge.document.proxy.IUserClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(MockitoExtension.class)
class DocumentServiceTest {

    @Mock
    private IChallengeClient challengeClient;

    @Mock
    private IUserClient userClient;

    @Mock
    private IAuthClient authClient;


    @InjectMocks
    private DocumentService documentService;

    @Test
    void shouldGetSwaggerUserDocsStr() {
        String expectedDocs = "User Swagger Docs";
        Mockito.when(userClient.getSwaggerDocs()).thenReturn(expectedDocs);

        String result = documentService.getSwaggerUserDocsStr();

        assertThat(result).isEqualTo(expectedDocs);
    }

    @Test
    void shouldGetSwaggerChallengeDocsStr() {
        String expectedDocs = "Challenge Swagger Docs";
        Mockito.when(challengeClient.getSwaggerDocs()).thenReturn(expectedDocs);

        String result = documentService.getSwaggerChallengeDocsStr();

        assertThat(result).isEqualTo(expectedDocs);
    }

    @Test
    void shouldGetSwaggerAuthDocsStr() {
        String expectedDocs = "Auth Swagger Docs";
        Mockito.when(authClient.getSwaggerDocs()).thenReturn(expectedDocs);

        String result = documentService.getSwaggerAuthDocsStr();

        assertThat(result).isEqualTo(expectedDocs);
    }

}


// Node: shouldGetSwaggerUserDocsStr
package com.itachallenge.document.config;

import com.itachallenge.document.service.DocumentService;
import io.swagger.v3.oas.models.OpenAPI;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;

@SpringBootTest
@TestPropertySource(locations = "classpath:application.yml")
class OpenApiConfigTest {

    @Mock
    private DocumentService documentService;

    @InjectMocks
    private OpenApiConfig openApiConfig;

    @Test
    void shouldCreateAllOpenAPI() {
        // Mock Swagger docs from DocumentService
        when(documentService.getSwaggerChallengeDocsStr()).thenReturn(
                """
                {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Challenge API",
                        "version": "1.0"
                    }
                }"""
        );

        when(documentService.getSwaggerUserDocsStr()).thenReturn(
                """
                {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "User API",
                        "version": "1.0"
                    }
                }"""
        );


        when(documentService.getSwaggerAuthDocsStr()).thenReturn(
                """
                {
                    "openapi": "3.0.0",
                    "info": {
                        "title": "Auth API",
                        "version": "1.0"
                    }
                }"""
        );

        // Perform test
        OpenAPI result = openApiConfig.allOpenAPI();

        // Assertions
        assertThat(result).isNotNull();
        assertThat(result.getInfo().getTitle()).isEqualTo("ITA Challenges APIs Documentation");
        assertThat(result.getInfo().getVersion()).isEqualTo("1.0");
        assertThat(result.getInfo().getDescription()).isEqualTo("Centralized documentation for ITA Challenges APIs. Explore and understand the available services for authentication, challenges, user management, scoring, and more.");

        // Verify extensions
        assertThat(result.getExtensions()).containsKey("itachallenge-challenge-api");
        assertThat(result.getExtensions()).containsKey("itachallenge-user-api");
        assertThat(result.getExtensions()).containsKey("itachallenge-auth-api");
    }
}

// Node: shouldCreateAllOpenAPI
// Node: getExtensions
// Node: containsKey
package com.itachallenge.errorcore.exception;

import org.springframework.http.HttpStatus;

import java.util.Arrays;
import java.util.Objects;

public record ApiCustomErrorInfo(HttpStatus status, String messageKey, Object[] messageArgs )  {
    public static ApiCustomErrorInfo of(HttpStatus status, String messageKey, Object[] messageArgs){
        return new ApiCustomErrorInfo(status,messageKey,messageArgs);
    }
    // ✅ equals() — use Arrays.equals for array fields
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof ApiCustomErrorInfo(HttpStatus status1, String key, Object[] args))) return false;
        return status == status1 &&
                Objects.equals(messageKey, key) &&
                Arrays.equals(messageArgs, args);
    }

    // ✅ hashCode() — use Arrays.hashCode for array fields
    @Override
    public int hashCode() {
        int result = Objects.hash(status, messageKey);
        result = 31 * result + Arrays.hashCode(messageArgs);
        return result;
    }

    // ✅ toString() — use Arrays.toString for array fields
    @Override
    public String toString() {
        return "ApiCustomErrorInfo{" +
                "status=" + status +
                ", messageKey='" + messageKey + '\'' +
                ", messageArgs=" + Arrays.toString(messageArgs) +
                '}';
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/main/java/com/itachallenge/errorcore/exception/ApiCustomErrorInfo.java:ApiCustomErrorInfo.<init>
// Node: ApiCustomErrorInfo
// Node: hashCode
// Node: hash
// Node: getStatus
package com.itachallenge.errorcore.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class APIErrorResponseTest {

    private ObjectMapper objectMapper;
    private final Logger log = LoggerFactory.getLogger(APIErrorResponseTest.class);
    private static final String LOG_TEMPLATE = "Serialized JSON: {}";

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
        objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);// ✅ Support for Instant serialization
        objectMapper.setSerializationInclusion(JsonInclude.Include.NON_EMPTY);
    }

    @Test
    @DisplayName("Serializes APIErrorResponse with multiple FieldErrorDto and metadata correctly")
    void shouldSerializeErrorResponseWithMultipleErrorsAndMetadata() throws Exception {
        APIErrorResponse response = APIErrorResponse.builder()
                .status(400)
                .error("Bad Request")
                .message("Validation failed")
                .path("/api/v1/challenges")
                .timestamp(Instant.parse("2025-10-06T09:00:00Z"))
                .errors(List.of(
                        FieldErrorDto.builder()
                                .objectName("challengeDto")
                                .field("title")
                                .message("The title cannot be empty")
                                .build(),
                        FieldErrorDto.builder()
                                .objectName("challengeDto")
                                .field("difficulty")
                                .message("The difficulty is invalid")
                                .build()
                ))
                .build();

        String json = objectMapper.writeValueAsString(response);
        log.info(LOG_TEMPLATE, json);

        assertThat(json)
                .startsWith("{").endsWith("}")
                .contains("\"status\":400")
                .contains("\"error\":\"Bad Request\"")
                .contains("\"message\":\"Validation failed\"")
                .contains("\"path\":\"/api/v1/challenges\"")
                .contains("\"timestamp\":\"2025-10-06T09:00:00Z\"")
                .contains("\"errors\"")
                .contains("\"objectName\":\"challengeDto\"")
                .contains("\"field\":\"title\"")
                .contains("\"message\":\"The title cannot be empty\"")
                .contains("\"field\":\"difficulty\"")
                .contains("\"message\":\"The difficulty is invalid\"");
    }

    @Test
    @DisplayName("Does not serialize empty error list when using @JsonInclude.NON_EMPTY")
    void shouldOmitEmptyErrorsList() throws Exception {
        APIErrorResponse response = APIErrorResponse.builder()
                .status(400)
                .error("Bad Request")
                .message("Empty error list")
                .path("/api/v1/challenges")
                .timestamp(Instant.parse("2025-10-06T09:10:00Z"))
                .errors(List.of()) // empty list
                .build();

        String json = objectMapper.writeValueAsString(response);
        log.info(LOG_TEMPLATE, json);

        assertThat(json)
                .doesNotContain("errors")
                .contains("\"status\":400")
                .contains("\"error\":\"Bad Request\"")
                .contains("\"message\":\"Empty error list\"")
                .contains("\"path\":\"/api/v1/challenges\"")
                .contains("\"timestamp\":\"2025-10-06T09:10:00Z\"");
    }
}


// Node: registerModule
// Node: JavaTimeModule
// Node: disable
// Node: shouldSerializeErrorResponseWithMultipleErrorsAndMetadata
// Node: parse
// Node: shouldOmitEmptyErrorsList
package com.itachallenge.user.exception;

public class UnmodificableSolutionException extends RuntimeException {
    public UnmodificableSolutionException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/UnmodificableSolutionException.java:UnmodificableSolutionException.<init>
// Node: UnmodificableSolutionException
// Node: addSolution
package com.itachallenge.user.repository;

import com.itachallenge.user.document.UserSolutionDocument;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface IUserSolutionRepository extends ReactiveMongoRepository<UserSolutionDocument, UUID> {

    Mono<UserSolutionDocument> findByUserIdAndChallengeIdAndLanguageId(UUID userId, UUID challengeId, UUID languageId);
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/repository/IUserSolutionRepository.java:IUserSolutionRepository.<init>
// Node: findByUserIdAndChallengeIdAndLanguageId
// Node: name
package com.itachallenge.user.service;

import com.itachallenge.user.document.SolutionAttemptDocument;
import com.itachallenge.user.document.UserSolutionDocument;
import com.itachallenge.user.document.enums.ChallengeStatus;
import com.itachallenge.user.document.enums.SolutionAction;
import com.itachallenge.user.dto.SubmitSolutionResponseDto;
import com.itachallenge.user.dto.UserSolutionRequestDto;
import com.itachallenge.user.dto.UserSolutionResponseDto;
import com.itachallenge.user.exception.BadRequestException;
import com.itachallenge.user.exception.UnmodificableSolutionException;
import com.itachallenge.user.repository.IUserSolutionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Service
public class UserSolutionServiceImpl implements IUserSolutionService {

    private static final Logger log = LoggerFactory.getLogger(UserSolutionServiceImpl.class);
    private final IUserSolutionRepository userSolutionRepository;
    private final IChallengeService challengeService;

    public UserSolutionServiceImpl(IUserSolutionRepository userSolutionRepository, IChallengeService challengeService) {
        this.userSolutionRepository = userSolutionRepository;
        this.challengeService = challengeService;
    }

    //TODO : to be moved to the challenge micro when we do the entire solutions refactor
    @Override
    public Mono<SubmitSolutionResponseDto> addSolution(UserSolutionRequestDto userSolutionDto) {
        if (SolutionAction.SUBMIT.equals(userSolutionDto.getAction())) {
            if (userSolutionDto.getSolutionText() == null || userSolutionDto.getSolutionText().isBlank()) {
                return Mono.error(new BadRequestException("Solution text is required when finalizing (SUBMIT)."));
            }
        }
        UUID challengeUuid = UUID.fromString(userSolutionDto.getChallengeId());
        UUID languageUuid = UUID.fromString(userSolutionDto.getLanguageId());
        UUID userUuid = UUID.fromString(userSolutionDto.getUserId());

        ChallengeStatus challengeStatus = determineStatus(userSolutionDto.getAction());
        SolutionAttemptDocument solutionAttempt = SolutionAttemptDocument.builder()
                .uuid(UUID.randomUUID())
                .solutionText(userSolutionDto.getSolutionText())
                .build();

        return saveValidSolution(userUuid, challengeUuid, languageUuid, challengeStatus, solutionAttempt)
                            .flatMap(this::buildSubmitSolutionResponse)
                            .doOnSuccess(response -> log.info("PUT request successfully processed for challenge {} and user {}.", challengeUuid, userUuid))
                            .doOnError(error -> log.error("PUT operation failed: {} for challenge {} and user {}.", error.getMessage(), challengeUuid, userUuid));
    }

    //TODO : to be moved to the challenge micro when we do the entire solutions refactor
    private ChallengeStatus determineStatus(SolutionAction action) {
        return switch (action) {
            case SAVE -> ChallengeStatus.IN_PROGRESS;
            case GIVE_UP -> ChallengeStatus.SUBMITTED_INCOMPLETE;
            case SUBMIT -> ChallengeStatus.SUBMITTED_COMPLETE;
        };
    }

    //TODO : to be moved to the challenge micro when we do the entire solutions refactor
    private Mono<UserSolutionDocument> saveValidSolution(UUID userUuid, UUID challengeUuid, UUID languageUuid, ChallengeStatus challengeStatus, SolutionAttemptDocument solutionAttempt) {
        return userSolutionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid)
                .flatMap(existingSolution -> {
                    if (ChallengeStatus.SUBMITTED_COMPLETE.equals(existingSolution.getStatus()) ||
                            ChallengeStatus.SUBMITTED_INCOMPLETE.equals(existingSolution.getStatus()))
                    {
                        return Mono.error(new UnmodificableSolutionException("Existing solution is already submitted and cannot be modified."));
                    }
                    existingSolution.setSolutionAttemptDocument(solutionAttempt);
                    existingSolution.setStatus(challengeStatus);
                    return userSolutionRepository.save(existingSolution);
                })
                .switchIfEmpty(Mono.defer(() -> {
                    UserSolutionDocument newSolution = UserSolutionDocument.builder()
                            .uuid(UUID.randomUUID())
                            .userId(userUuid)
                            .challengeId(challengeUuid)
                            .languageId(languageUuid)
                            .status(challengeStatus)
                            .solutionAttemptDocument(solutionAttempt)
                            .build();
                    return userSolutionRepository.save(newSolution);
                }));
    }

    //TODO : to be moved to the challenge micro when we do the entire solutions refactor
    private Mono<SubmitSolutionResponseDto> buildSubmitSolutionResponse(UserSolutionDocument savedDocument) {
        String solutionText = savedDocument.getSolutionAttemptDocument().getSolutionText();
        ChallengeStatus status = savedDocument.getStatus();

        if (ChallengeStatus.SUBMITTED_COMPLETE.equals(status)) {
            return challengeService.addChallengeToSolved(savedDocument.getChallengeId().toString())
                    .map(solvedDto -> SubmitSolutionResponseDto.builder()
                            .solutionText(solutionText)
                            .isSolved(solvedDto.isSolved())
                            .timesSolved(solvedDto.getTimesSolved())
                            .status(status.name())
                            .build());
        } else {
            // TODO: Enhance the response for non-ended statuses like IN_PROGRESS if additional info is needed
            return Mono.just(SubmitSolutionResponseDto.builder()
                    .solutionText(solutionText)
                    .isSolved(false)
                    .status(status.name())
                    .build());
        }
    }

    private Mono<UUID> validateAndParseUuid(String userId) {
        if (userId == null || userId.trim().isEmpty()) {
            return Mono.error(new BadRequestException("The 'userId' parameter cannot be null or empty."));
        }
        try {
            return Mono.just(UUID.fromString(userId.trim()));
        } catch (IllegalArgumentException ex) {
            return Mono.error(new BadRequestException("The 'userId' parameter must be a valid UUID: " + userId));
        }
    }
}


// Node: getAction
// Node: getSolutionText
// Node: finalizing
// Node: getChallengeId
// Node: getLanguageId
// Node: getUserId
// Node: determineStatus
// Node: uuid
// Node: solutionText
// Node: saveValidSolution
// Node: setSolutionAttemptDocument
// Node: setStatus
// Node: defer
// Node: userId
// Node: challengeId
// Node: languageId
// Node: solutionAttemptDocument
// Node: buildSubmitSolutionResponse
// Node: getSolutionAttemptDocument
// Node: addChallengeToSolved
// Node: isSolved
// Node: timesSolved
// Node: getTimesSolved
package com.itachallenge.user.service;

import com.itachallenge.user.dto.SolvedDto;
import reactor.core.publisher.Mono;

public interface IChallengeService {

    Mono<SolvedDto> addChallengeToSolved(String challengeId);

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/IChallengeService.java:IChallengeService.<init>
package com.itachallenge.user.service;

import com.itachallenge.user.dto.SubmitSolutionResponseDto;
import com.itachallenge.user.dto.UserSolutionRequestDto;
import com.itachallenge.user.dto.UserSolutionResponseDto;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface IUserSolutionService {
    Mono<SubmitSolutionResponseDto> addSolution(UserSolutionRequestDto userSolutionDto);
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/service/IUserSolutionService.java:IUserSolutionService.<init>
package com.itachallenge.userinteraction.document.bookmark;

import java.time.LocalDateTime;
import java.util.UUID;

import com.itachallenge.userinteraction.document.favorite.FavoriteDocument;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class BookmarkDocumentTest {

    @Test
    void constructor_shouldSetBaseInteractionFields() {
        UUID uuid = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        LocalDateTime createdAt = LocalDateTime.now();

        BookmarkDocument document = BookmarkDocument.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        assertEquals(uuid, document.getUuid());
        assertEquals(userId, document.getUserId());
        assertEquals(challengeId, document.getChallengeId());
        assertEquals(createdAt, document.getCreatedAt());
    }

    @Test
    void equalsHashCodeAndToString_shouldWorkWithSameIdentity() {
        UUID uuid = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        LocalDateTime createdAt = LocalDateTime.now();

        BookmarkDocument a = BookmarkDocument.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        BookmarkDocument b = BookmarkDocument.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        BookmarkDocument different = BookmarkDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        assertEquals(a, b);
        assertEquals(a.hashCode(), b.hashCode());

        assertNotEquals(a, different);
        assertNotEquals(a, null);
        assertNotEquals(a, "some string");

        assertNotNull(a.toString());
    }

}


// Node: constructor_shouldSetBaseInteractionFields
// Node: createdAt
// Node: getCreatedAt
// Node: equalsHashCodeAndToString_shouldWorkWithSameIdentity
// Node: assertNotEquals
package com.itachallenge.userinteraction.document.favorite;

import java.time.LocalDateTime;
import java.util.UUID;

import com.itachallenge.userinteraction.document.bookmark.BookmarkDocument;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class FavoriteDocumentTest {

    @Test
    void constructor_shouldSetBaseInteractionFields() {
        UUID uuid = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        LocalDateTime createdAt = LocalDateTime.now();

        FavoriteDocument document = FavoriteDocument.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        assertEquals(uuid, document.getUuid());
        assertEquals(userId, document.getUserId());
        assertEquals(challengeId, document.getChallengeId());
        assertEquals(createdAt, document.getCreatedAt());
    }

    @Test
    void equalsHashCodeAndToString_shouldWorkWithSameIdentity() {
        UUID uuid = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        LocalDateTime createdAt = LocalDateTime.now();

        FavoriteDocument a = FavoriteDocument.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        FavoriteDocument b = FavoriteDocument.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        FavoriteDocument different = FavoriteDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        assertEquals(a, b);
        assertEquals(a.hashCode(), b.hashCode());

        assertNotEquals(a, different);
        assertNotEquals(a, null);
        assertNotEquals(a, "some string");

        assertNotNull(a.toString());
    }
}


package com.itachallenge.user.controller;

import com.itachallenge.user.document.enums.SolutionAction;
import com.itachallenge.user.dto.SubmitSolutionResponseDto;
import com.itachallenge.user.dto.UserSolutionRequestDto;
import com.itachallenge.user.service.ExternalGithubService;
import com.itachallenge.user.service.IUserSolutionService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;

import static org.mockito.Mockito.when;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureWebTestClient
class UserControllerSpringTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private IUserSolutionService userSolutionService;

    @MockBean
    private ExternalGithubService externalGithubService;

    private String uri;
    private String userId;
    private String challengeId;
    private String languageId;
    private String solution;

    @BeforeEach
    void setUp() {
        uri = "/itachallenge/api/v1/user/solution";
        userId = "e20e8efe-f38f-4fdd-89b5-201da705b853";
        challengeId = "7f7e1c41-b122-4e8e-9778-86fd82734666";
        languageId = "f87bf12f-e8ea-4b8c-8bb6-12c02756c765";
        solution = "This is the submitted solution";
    }

    @Test
    void testAddSolution() {
        UserSolutionRequestDto requestDto = UserSolutionRequestDto.builder()
                .userId(userId)
                .challengeId(challengeId)
                .languageId(languageId)
                .action(SolutionAction.SUBMIT)
                .solutionText(solution)
                .build();

        SubmitSolutionResponseDto responseDto = SubmitSolutionResponseDto.builder()
                .solutionText(solution)
                .isSolved(true)
                .timesSolved(42)
                .build();

        when(userSolutionService.addSolution(org.mockito.ArgumentMatchers.any(UserSolutionRequestDto.class)))
                .thenReturn(Mono.just(responseDto));

        webTestClient.put()
                .uri(uri)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(requestDto)
                .exchange()
                .expectStatus().isOk()
                .expectBody(SubmitSolutionResponseDto.class)
                .value(res -> {
                    assertEquals(solution, res.getSolutionText());
                    assertTrue(res.getIsSolved());
                    assertEquals(42, res.getTimesSolved());
                });
    }
}


// Node: testAddSolution
// Node: action
// Node: getIsSolved
package com.itachallenge.user.document;

import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;


class SolutionAttemptDocumentTest {

    UUID uuid = UUID.randomUUID();
    String solutionText = "Ipsum...";
    SolutionAttemptDocument solutionAttemptDocument = new SolutionAttemptDocument(uuid, solutionText);
    SolutionAttemptDocument noArgsSolutionAttemptDocument = new SolutionAttemptDocument();

    @Test
    void getUuid_test(){
        assertEquals(uuid, solutionAttemptDocument.getUuid());
    }

    @Test
    void getSolutionText_test(){
        assertEquals(solutionText, solutionAttemptDocument.getSolutionText());
    }

    @Test
    void noArgsBuilder_test(){
        assertNotNull(noArgsSolutionAttemptDocument);
    }

    @Test
    void setSolutionDocument_test(){
        noArgsSolutionAttemptDocument.setUuid(uuid);
        noArgsSolutionAttemptDocument.setSolutionText(solutionText);
        assertEquals(solutionText, noArgsSolutionAttemptDocument.getSolutionText());
        assertEquals(uuid, noArgsSolutionAttemptDocument.getUuid());
    }
}




// Node: getUuid_test
// Node: getSolutionText_test
// Node: setSolutionDocument_test
package com.itachallenge.user.document;

import com.itachallenge.user.document.enums.Role;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

import java.util.*;

class UserDocumentTest {

    private UUID uuid;
    private String username;
    private Role role;
    private UserDocument userDocument;
    private Integer points;

    @BeforeEach
    void setUp() {
        uuid = UUID.randomUUID();
        username = "testUser";
        role = Role.ADMIN;
        points = 0;
        userDocument = UserDocument.builder()
                .uuid(uuid)
                .username(username)
                .role(role)
                .points(0)
                .build();
    }

    @Test
    void userDocumentCreation() {
        assertNotNull(userDocument);
        assertEquals(uuid, userDocument.getUuid());
        assertEquals(username, userDocument.getUsername());
        assertEquals(role, userDocument.getRole());
        assertEquals(points, userDocument.getPoints());
    }

    @Test
    void settersAndGetters() {
        UUID newUuid = UUID.randomUUID();
        String newUsername = "newUser";
        Role newRole = Role.USER;
        Integer newPoints = 0;

        userDocument.setUuid(newUuid);
        userDocument.setUsername(newUsername);
        userDocument.setRole(newRole);
        userDocument.setPoints(newPoints);

        assertEquals(newUuid, userDocument.getUuid());
        assertEquals(newUsername, userDocument.getUsername());
        assertEquals(newRole, userDocument.getRole());
        assertEquals(newPoints, userDocument.getPoints());
    }

    @Test
    void builderPattern() {
        UserDocument user = UserDocument.builder()
                .uuid(uuid)
                .username(username)
                .role(role)
                .points(points)
                .build();

        assertNotNull(user);
        assertEquals(uuid, user.getUuid());
        assertEquals(username, user.getUsername());
        assertEquals(role, user.getRole());
        assertEquals(points, user.getPoints());
    }

    @Test
    void noArgsConstructor() {
        UserDocument emptyUser = new UserDocument();
        assertNotNull(emptyUser);
        assertNull(emptyUser.getUuid());
        assertNull(emptyUser.getUsername());
        assertNull(emptyUser.getRole());
        assertEquals(0, emptyUser.getPoints());
    }

    @Test
    void allArgsConstructor() {
        UserDocument user = new UserDocument(uuid, username, role, points);
        assertNotNull(user);
        assertEquals(uuid, user.getUuid());
        assertEquals(username, user.getUsername());
        assertEquals(role, user.getRole());
        assertEquals(points, user.getPoints());
    }

    @Test
    void equalsAndHashCode() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user1.hashCode(), user2.hashCode());

        user2.setUsername("anotherUser");
        assertNotEquals(user1, user2);
    }

    @Test
    void equalsWithSameObject() {
        assertEquals(userDocument, userDocument);
    }

    @Test
    void equalsWithSameHashCode() {
        assertEquals(userDocument.hashCode(), userDocument.hashCode());
    }

    @Test
    void equalsAndHashCodeWithDifferentUUIDs() {
        UserDocument differentUser = new UserDocument(UUID.randomUUID(), username, role, points);

        assertNotEquals(userDocument, differentUser);
        assertNotEquals(userDocument.hashCode(), differentUser.hashCode());
    }

    @Test
    void equalsAndHashCodeWithDifferentUsernames() {
        UserDocument sameUuidDifferentUsername = new UserDocument(uuid, "differentUser", Role.USER, points);

        assertNotEquals(userDocument, sameUuidDifferentUsername);
        assertNotEquals(userDocument.hashCode(), sameUuidDifferentUsername.hashCode());
    }

    @Test
    void equalsAndHashCodeWithNullFields() {
        UserDocument userWithNullUuid = new UserDocument(null, username, role, points);
        UserDocument userWithNullUsername = new UserDocument(uuid, null, role, points);
        UserDocument userWithNullRole = new UserDocument(uuid, username, null, points);
        UserDocument userWithNullPoints = new UserDocument(uuid, username, role, 0);
        UserDocument completelyNullUser = new UserDocument(null, null, null, 0);

        assertNotEquals(userDocument, userWithNullUuid);
        assertNotEquals(userDocument, userWithNullUsername);
        assertNotEquals(userDocument, userWithNullRole);
        assertEquals(userDocument, userWithNullPoints);
        assertNotEquals(userDocument, completelyNullUser);

        assertNotEquals(userDocument.hashCode(), userWithNullUuid.hashCode());
        assertNotEquals(userDocument.hashCode(), userWithNullUsername.hashCode());
        assertNotEquals(userDocument.hashCode(), userWithNullRole.hashCode());
        assertEquals(userDocument.hashCode(), userWithNullPoints.hashCode());
        assertNotEquals(userDocument.hashCode(), completelyNullUser.hashCode());
    }

    @Test
    void equalsWithDifferentClass() {
        Object otherObject = new Object();
        assertNotEquals(userDocument, otherObject);
    }

    @Test
    void equalsWithNull() {
        assertNotEquals(null, userDocument);
    }

    @Test
    void equalsConsistencyTest() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user1, user2); // Repeated check for consistency
    }

    @Test
    void hashCodeConsistencyTest() {
        int initialHashCode = userDocument.hashCode();
        assertEquals(initialHashCode, userDocument.hashCode());
    }

    @Test
    void equalsTransitivityTest() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);
        UserDocument user3 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user2, user3);
        assertEquals(user1, user3);
    }

    @Test
    void equalsSymmetryTest() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1, user2);
        assertEquals(user2, user1);
    }

    @Test
    void hashCodeEqualityForEqualObjects() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, role, points);

        assertEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void hashCodeDifferenceForNonEqualObjects() {
        UserDocument user1 = new UserDocument(UUID.randomUUID(), "user1", Role.ADMIN, points);
        UserDocument user2 = new UserDocument(UUID.randomUUID(), "user2", Role.ADMIN, points);

        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithNullAttributes() {
        UserDocument user1 = new UserDocument(null, null, null, 0);
        UserDocument user2 = new UserDocument(null, null, null, 0);

        assertEquals(user1, user2);
        assertEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithOneNullUuid() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(null, username, role, points);

        assertNotEquals(user1, user2);
        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithOneNullUsername() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, null, role, points);

        assertNotEquals(user1, user2);
        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void equalsWithOneNullRole() {
        UserDocument user1 = new UserDocument(uuid, username, role, points);
        UserDocument user2 = new UserDocument(uuid, username, null, points);

        assertNotEquals(user1, user2);
        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void toStringHandlesNullValues() {
        UserDocument user = new UserDocument(null, null, null, 0);
        String s = user.toString();

        assertNotNull(s);
        assertTrue(s.contains("UserDocument"));
    }


    @Test
    void builderHandlesNullValues() {
        UserDocument user = UserDocument.builder()
                .uuid(null)
                .username(null)
                .role(null)
                .points(0)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
        assertEquals(0, user.getPoints());
    }

    @Test
    void settersHandleNullValues() {
        userDocument.setUuid(null);
        userDocument.setUsername(null);
        userDocument.setRole(null);
        userDocument.setPoints(null);

        assertNull(userDocument.getUuid());
        assertNull(userDocument.getUsername());
        assertNull(userDocument.getRole());
        assertNull(userDocument.getPoints());
    }

    @Test
    void hashCodeDifferentForDifferentObjects() {
        UserDocument user1 = new UserDocument(UUID.randomUUID(), "UserA", Role.ADMIN, points);
        UserDocument user2 = new UserDocument(UUID.randomUUID(), "UserB", Role.ADMIN, points);

        assertNotEquals(user1.hashCode(), user2.hashCode());
    }

    @Test
    void builderHandlesOnlyUuid() {
        UserDocument user = UserDocument.builder()
                .uuid(uuid)
                .build();

        assertNotNull(user);
        assertEquals(uuid, user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
    }

    @Test
    void builderHandlesOnlyUsername() {
        UserDocument user = UserDocument.builder()
                .username(username)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertEquals(username, user.getUsername());
        assertNull(user.getRole());
    }

    @Test
    void builderHandlesOnlyRole() {
        UserDocument user = UserDocument.builder()
                .role(role)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertEquals(role, user.getRole());
    }


    @Test
    void builderHandlesOnlyPoints() {
        UserDocument user = UserDocument.builder()
                .points(points)
                .build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
        assertEquals(points, user.getPoints());
    }

    @Test
    void builderCreatesNewInstances() {
        UserDocument user1 = UserDocument.builder().uuid(uuid).username(username).role(role)
                .build();

        UserDocument user2 = UserDocument.builder().uuid(uuid).username(username).role(role)
                .build();

        assertNotSame(user1, user2);
        assertEquals(user1, user2);
    }

    @Test
    void builderWithoutParametersCreatesValidObject() {
        UserDocument user = UserDocument.builder().build();

        assertNotNull(user);
        assertNull(user.getUuid());
        assertNull(user.getUsername());
        assertNull(user.getRole());
    }

    @Test
    void modifyingBuiltObjectDoesNotAffectOriginalBuilder() {
        UserDocument.UserDocumentBuilder builder = UserDocument.builder().uuid(uuid).username(username).role(role);

        UserDocument user1 = builder.build();
        UserDocument user2 = builder.uuid(UUID.randomUUID()).username("newUser").role(Role.USER)
                .build();

        assertNotEquals(user1, user2);
        assertNotEquals(user1.getUuid(), user2.getUuid());
        assertNotEquals(user1.getUsername(), user2.getUsername());
        assertNotEquals(user1.getRole(), user2.getRole());
    }
}


// Node: equalsAndHashCode
// Node: equalsWithSameObject
// Node: equalsWithSameHashCode
// Node: equalsAndHashCodeWithDifferentUUIDs
// Node: equalsAndHashCodeWithDifferentUsernames
// Node: equalsAndHashCodeWithNullFields
// Node: equalsWithDifferentClass
// Node: Object
// Node: equalsWithNull
// Node: equalsConsistencyTest
// Node: hashCodeConsistencyTest
// Node: equalsTransitivityTest
// Node: equalsSymmetryTest
// Node: hashCodeEqualityForEqualObjects
// Node: hashCodeDifferenceForNonEqualObjects
// Node: equalsWithNullAttributes
// Node: equalsWithOneNullUuid
// Node: equalsWithOneNullUsername
// Node: equalsWithOneNullRole
// Node: hashCodeDifferentForDifferentObjects
package com.itachallenge.user.document;

import com.itachallenge.user.document.enums.ChallengeStatus;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class UserSolutionDocumentTest {

    private final UUID uuid = UUID.randomUUID();
    private final UUID userId = UUID.randomUUID();
    private final UUID challengeId = UUID.randomUUID();
    private final UUID languageId  = UUID.randomUUID();
    private final ChallengeStatus challengeStatus = ChallengeStatus.SUBMITTED_COMPLETE;
    UUID solutionId1 = UUID.fromString("1e047ea2-b787-49e7-acea-d79e92be3909");
    String solutionText1 = "Ipsum.. 1";
    SolutionAttemptDocument solutionAttemptDocument1 = new SolutionAttemptDocument(solutionId1, solutionText1);
    UserSolutionDocument userSolutionDocument = new UserSolutionDocument(uuid, userId, challengeId, languageId, challengeStatus, solutionAttemptDocument1);
    UserSolutionDocument noArgsUserSolutionDocument = new UserSolutionDocument();

    @Test
    void getUuid(){
        assertEquals(uuid, userSolutionDocument.getUuid());
    }

    @Test
    void getUserId(){ assertEquals(userId, userSolutionDocument.getUserId());}

    @Test
    void getChallengeId(){
        assertEquals(challengeId, userSolutionDocument.getChallengeId());
    }

    @Test
    void getLanguageId(){
        assertEquals(languageId, userSolutionDocument.getLanguageId());
    }

    @Test
    void getStatus(){
        assertEquals(challengeStatus, userSolutionDocument.getStatus());
    }

    @Test
    void getSolutionAttemptDocument(){
        assertEquals(solutionAttemptDocument1, userSolutionDocument.getSolutionAttemptDocument());
    }

    @Test
    void noArgsBuilder_test(){
        assertNotNull(noArgsUserSolutionDocument);
    }
}




package com.itachallenge.user.document.enums;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.fasterxml.jackson.databind.exc.ValueInstantiationException;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class SolutionActionTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    void shouldDeserializeSaveIgnoringCase() throws Exception{
        String json = "\"SaVe\"";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertEquals(SolutionAction.SAVE, result);
    }

    @Test
    void shouldDeserializeGiveUpIgnoringCase() throws Exception {
        String json = "\"GivE_uP\"";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertEquals(SolutionAction.GIVE_UP, result);
    }

    @Test
    void shouldDeserializeSubmitWithSpaces() throws Exception {
        String json = "\"   submit   \"";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertEquals(SolutionAction.SUBMIT, result);
    }

    @Test
    void shouldThrowExceptionForInvalidValue() {
        String json = "\"INVALID_VALUE\"";

        ValueInstantiationException ex = assertThrows(
                ValueInstantiationException.class,
                () -> mapper.readValue(json, SolutionAction.class)
        );


        assertNotNull(ex.getCause());
        assertInstanceOf(IllegalArgumentException.class, ex.getCause());
        assertTrue(ex.getCause().getMessage().contains("Action must be one of"));
    }

    @Test
    void shouldReturnNullWhenJsonNull() throws Exception{
        String json = "null";
        SolutionAction result = mapper.readValue(json, SolutionAction.class);

        assertNull(result);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/document/enums/SolutionActionTest.java:SolutionActionTest.<init>
// Node: shouldDeserializeSaveIgnoringCase
// Node: shouldDeserializeGiveUpIgnoringCase
// Node: shouldDeserializeSubmitWithSpaces
package com.itachallenge.user.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.user.dto.SolvedDto;
import com.itachallenge.user.exception.BadRequestException;
import com.itachallenge.user.exception.InternalServerErrorException;
import com.itachallenge.user.exception.NotFoundException;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import okhttp3.mockwebserver.RecordedRequest;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;

public class ChallengeServiceImplTest {

    private MockWebServer mockWebServer;
    private ChallengeServiceImpl challengeService;

    private static final String SOLVED_URL = "/itachallenge/api/v1/challenge/solved/%s";
    public static final String X_SOLVED_MESSAGE = "X-Solved-Message";

    @BeforeEach
    void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

        challengeService = new ChallengeServiceImpl(
                WebClient.builder(),
                mockWebServer.url("").toString()
        );
    }

    @AfterEach
    void tearDown() throws IOException {
        mockWebServer.close();
    }

    @Test
    void addChallengeToSolved_AddedToUser_ReturnsTrue() throws Exception {
        String challengeId = "someId";

        SolvedDto solvedDto = new SolvedDto(true, 5);

        String responseBody = new ObjectMapper().writeValueAsString(solvedDto);

        mockWebServer.enqueue(new MockResponse()
                .setBody(responseBody)
                .setResponseCode(201)
                .addHeader("Content-Type", "application/json"));

        Mono<SolvedDto> result = challengeService.addChallengeToSolved(challengeId);

        StepVerifier.create(result)
                .assertNext(dto -> {
                    assertTrue(dto.isSolved(), "Expected isSolved to be true");
                    assertEquals(5, dto.getTimesSolved(), "Expected timesSolved to be 5");
                })
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(
                String.format(SOLVED_URL, challengeId),
                request.getRequestUrl().encodedPath());
    }


    @Test
    void addChallengeToSolved_NotAddedToUser_ReturnsFalse() throws InterruptedException {
        String challengeId = "someId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("{\"isSolved\":false,\"timesSolved\":0}")
                .setResponseCode(200)
                .addHeader("Content-Type", "application/json"));

        Mono<SolvedDto> result = challengeService.addChallengeToSolved(challengeId);

        StepVerifier.create(result)
                .assertNext(dto -> {
                    assertFalse(dto.isSolved());
                    assertEquals(0, dto.getTimesSolved());
                })
                .verifyComplete();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(String.format(SOLVED_URL, challengeId), request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToSolved_BadRequest_ReturnsError() throws InterruptedException {
        String challengeId = "someId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(400)
                .addHeader(X_SOLVED_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<SolvedDto> result = challengeService.addChallengeToSolved(challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(BadRequestException.class, throwable);
                    assertTrue(throwable.getMessage().contains(someErrorMessage));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(String.format(SOLVED_URL, challengeId), request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToSolved_ChallengeNotFound_ReturnsError() throws InterruptedException {
        String challengeId = "someId";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(404)
                .addHeader("Content-Type", "application/json"));

        Mono<SolvedDto> result = challengeService.addChallengeToSolved(challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(NotFoundException.class, throwable);
                    assertTrue(throwable.getMessage().contains("Challenge not found"));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(String.format(SOLVED_URL, challengeId), request.getRequestUrl().encodedPath());
    }

    @Test
    void addChallengeToSolved_InternalServerError_ReturnsError() throws InterruptedException {
        String challengeId = "someId";
        String someErrorMessage = "Some error message";

        mockWebServer.enqueue(new MockResponse()
                .setBody("false")
                .setResponseCode(500)
                .addHeader(X_SOLVED_MESSAGE, someErrorMessage)
                .addHeader("Content-Type", "application/json"));

        Mono<SolvedDto> result = challengeService.addChallengeToSolved(challengeId);

        StepVerifier.create(result)
                .expectErrorSatisfies(throwable -> {
                    assertInstanceOf(InternalServerErrorException.class, throwable);
                    assertTrue(throwable.getMessage().contains(someErrorMessage));
                })
                .verify();

        RecordedRequest request = mockWebServer.takeRequest();
        assertNotNull(request.getRequestUrl());
        assertEquals(String.format(SOLVED_URL, challengeId), request.getRequestUrl().encodedPath());
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/service/ChallengeServiceImplTest.java:ChallengeServiceImplTest.<init>
// Node: addChallengeToSolved_AddedToUser_ReturnsTrue
// Node: SolvedDto
// Node: addChallengeToSolved_NotAddedToUser_ReturnsFalse
// Node: addChallengeToSolved_BadRequest_ReturnsError
// Node: addChallengeToSolved_ChallengeNotFound_ReturnsError
// Node: addChallengeToSolved_InternalServerError_ReturnsError
package com.itachallenge.user.service;

import com.itachallenge.user.document.SolutionAttemptDocument;
import com.itachallenge.user.document.UserSolutionDocument;
import com.itachallenge.user.document.enums.ChallengeStatus;
import com.itachallenge.user.document.enums.SolutionAction;
import com.itachallenge.user.dto.SubmitSolutionResponseDto;
import com.itachallenge.user.dto.UserSolutionRequestDto;
import com.itachallenge.user.exception.BadRequestException;
import com.itachallenge.user.exception.UnmodificableSolutionException;
import com.itachallenge.user.repository.IUserSolutionRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureWebTestClient
@ExtendWith(SpringExtension.class)
class UserSolutionServiceImplTest {

    @Mock
    private IUserSolutionRepository userSolutionRepository;

    @Mock
    private IChallengeService challengeService;

    @MockBean
    private ExternalGithubService externalGithubService;

    @InjectMocks
    private UserSolutionServiceImpl userSolutionService;

    private UUID userUuid;
    private UUID challengeUuid;
    private UUID languageUuid;
    private String solutionText;

    @BeforeEach
    void setUp() {
        userUuid = UUID.randomUUID();
        challengeUuid = UUID.randomUUID();
        languageUuid = UUID.randomUUID();
        solutionText = "Test solution";
    }

    @Test
    @DisplayName("addSolution SAVE action updates existing IN_PROGRESS solution successfully")
    void addSolutionUpdatesExistingSolution() {
        UserSolutionRequestDto request = UserSolutionRequestDto.builder()
                .userId(userUuid.toString())
                .challengeId(challengeUuid.toString())
                .languageId(languageUuid.toString())
                .action(SolutionAction.SAVE)
                .solutionText(solutionText)
                .build();

        UserSolutionDocument existingSolution = UserSolutionDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userUuid)
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .status(com.itachallenge.user.document.enums.ChallengeStatus.IN_PROGRESS)
                .solutionAttemptDocument(SolutionAttemptDocument.builder().solutionText("Old solution").build())
                .build();

        UserSolutionDocument savedSolution = UserSolutionDocument.builder()
                .uuid(existingSolution.getUuid())
                .userId(userUuid)
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .status(com.itachallenge.user.document.enums.ChallengeStatus.IN_PROGRESS)
                .solutionAttemptDocument(SolutionAttemptDocument.builder().solutionText(solutionText).build())
                .build();

        when(userSolutionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.just(existingSolution));
        when(userSolutionRepository.save(any(UserSolutionDocument.class)))
                .thenReturn(Mono.just(savedSolution));

        Mono<SubmitSolutionResponseDto> result = userSolutionService.addSolution(request);

        StepVerifier.create(result)
                .assertNext(dto -> {
                    assertEquals(solutionText, dto.getSolutionText());
                    assertFalse(dto.getIsSolved());
                    assertNull(dto.getTimesSolved());
                    assertEquals("IN_PROGRESS", dto.getStatus());
                })
                .verifyComplete();

        verify(userSolutionRepository).findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid);
        verify(userSolutionRepository).save(any(UserSolutionDocument.class));
        verifyNoInteractions(challengeService);
    }

    @ParameterizedTest
    @ValueSource(strings = {"GIVE_UP", "SUBMIT"})
    @DisplayName("addSolution throws UnmodificableSolutionException if existing solution status is already submitted")
    void addSolutionThrowsExceptionIfSubmitted(SolutionAction action) {
        UserSolutionRequestDto request = UserSolutionRequestDto.builder()
                .userId(userUuid.toString())
                .challengeId(challengeUuid.toString())
                .languageId(languageUuid.toString())
                .action(action)
                .solutionText(solutionText)
                .build();

        UserSolutionDocument existingSolution = UserSolutionDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userUuid)
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .status(ChallengeStatus.SUBMITTED_COMPLETE)
                .solutionAttemptDocument(SolutionAttemptDocument.builder().solutionText("Old solution").build())
                .build();

        when(userSolutionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.just(existingSolution));

        StepVerifier.create(userSolutionService.addSolution(request))
                .expectErrorMatches(throwable ->
                        throwable instanceof UnmodificableSolutionException &&
                                throwable.getMessage().contains("Existing solution is already submitted and cannot be modified."))
                .verify();

        verify(userSolutionRepository).findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid);
        verifyNoMoreInteractions(userSolutionRepository);
        verifyNoInteractions(challengeService);
    }

    @ParameterizedTest
    @ValueSource(strings = {"GIVE_UP", "SUBMIT"})
    @DisplayName("addSolution throws UnmodificableSolutionException if existing solution status is already submitted")
    void addSolutionThrowsExceptionIfGivenUp(SolutionAction action) {
        UserSolutionRequestDto request = UserSolutionRequestDto.builder()
                .userId(userUuid.toString())
                .challengeId(challengeUuid.toString())
                .languageId(languageUuid.toString())
                .action(action)
                .solutionText(solutionText)
                .build();

        UserSolutionDocument existingSolution = UserSolutionDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userUuid)
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .status(ChallengeStatus.SUBMITTED_INCOMPLETE)
                .solutionAttemptDocument(SolutionAttemptDocument.builder().solutionText("Old solution").build())
                .build();

        when(userSolutionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.just(existingSolution));

        StepVerifier.create(userSolutionService.addSolution(request))
                .expectErrorMatches(throwable ->
                        throwable instanceof UnmodificableSolutionException &&
                                throwable.getMessage().contains("Existing solution is already submitted and cannot be modified."))
                .verify();

        verify(userSolutionRepository).findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid);
        verifyNoMoreInteractions(userSolutionRepository);
        verifyNoInteractions(challengeService);
    }

    @Test
    @DisplayName("addSolution creates new SUBMITTED_COMPLETE solution and returns response")
    void addSolutionNewSubmittedCompleteSolution() {
        UserSolutionRequestDto request = UserSolutionRequestDto.builder()
                .userId(userUuid.toString())
                .challengeId(challengeUuid.toString())
                .languageId(languageUuid.toString())
                .action(SolutionAction.SUBMIT)
                .solutionText(solutionText)
                .build();

        when(userSolutionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.empty());

        when(userSolutionRepository.save(any(UserSolutionDocument.class)))
                .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        when(challengeService.addChallengeToSolved(challengeUuid.toString()))
                .thenReturn(Mono.just(new com.itachallenge.user.dto.SolvedDto(true, 5)));

        Mono<SubmitSolutionResponseDto> result = userSolutionService.addSolution(request);

        StepVerifier.create(result)
                .assertNext(dto -> {
                    assertEquals(solutionText, dto.getSolutionText());
                    assertTrue(dto.getIsSolved());
                    assertEquals(5, dto.getTimesSolved());
                    assertEquals("SUBMITTED_COMPLETE", dto.getStatus());
                })
                .verifyComplete();

        verify(userSolutionRepository).findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid);
        verify(userSolutionRepository).save(any(UserSolutionDocument.class));
        verify(challengeService).addChallengeToSolved(challengeUuid.toString());
    }

    @Test
    @DisplayName("addSolution GIVE_UP action creates new SUBMITTED_INCOMPLETE solution and returns response")
    void addSolutionNewSubmittedIncompleteSolution() {
        UserSolutionRequestDto request = UserSolutionRequestDto.builder()
                .userId(userUuid.toString())
                .challengeId(challengeUuid.toString())
                .languageId(languageUuid.toString())
                .action(SolutionAction.GIVE_UP)
                .solutionText(solutionText)
                .build();

        when(userSolutionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.empty());

        when(userSolutionRepository.save(any(UserSolutionDocument.class)))
                .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        Mono<SubmitSolutionResponseDto> result = userSolutionService.addSolution(request);

        StepVerifier.create(result)
                .assertNext(dto -> {
                    assertEquals(solutionText, dto.getSolutionText());
                    assertFalse(dto.getIsSolved());
                    assertEquals("SUBMITTED_INCOMPLETE", dto.getStatus());
                })
                .verifyComplete();

        verify(userSolutionRepository).findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid);
        verify(userSolutionRepository).save(any(UserSolutionDocument.class));
        verifyNoInteractions(challengeService);
    }

    @Test
    @DisplayName("addSolution SAVE action creates new IN_PROGRESS solution and returns response")
    void addSolutionNewInProgressSolution() {
        UserSolutionRequestDto request = UserSolutionRequestDto.builder()
                .userId(userUuid.toString())
                .challengeId(challengeUuid.toString())
                .languageId(languageUuid.toString())
                .action(SolutionAction.SAVE)
                .solutionText(solutionText)
                .build();

        when(userSolutionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.empty());

        when(userSolutionRepository.save(any(UserSolutionDocument.class)))
                .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        Mono<SubmitSolutionResponseDto> result = userSolutionService.addSolution(request);

        StepVerifier.create(result)
                .assertNext(dto -> {
                    assertEquals(solutionText, dto.getSolutionText());
                    assertFalse(dto.getIsSolved());
                    assertEquals("IN_PROGRESS", dto.getStatus());
                })
                .verifyComplete();

        verify(userSolutionRepository).findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid);
        verify(userSolutionRepository).save(any(UserSolutionDocument.class));
        verifyNoInteractions(challengeService);
    }
    @Test
    @DisplayName("addSolution SUBMIT action with blank solution text throws BadRequestException")
    void addSolution_SubmitAction_BlankText_ThrowsException() {
        UserSolutionRequestDto request = UserSolutionRequestDto.builder()
                .userId(userUuid.toString())
                .challengeId(challengeUuid.toString())
                .languageId(languageUuid.toString())
                .action(SolutionAction.SUBMIT)
                .solutionText("   ") 
                .build();

        StepVerifier.create(userSolutionService.addSolution(request))
                .expectErrorMatches(throwable ->
                        throwable instanceof BadRequestException &&
                                throwable.getMessage().equals("Solution text is required when finalizing (SUBMIT)."))
                .verify();

        verifyNoInteractions(userSolutionRepository);
    }
}


// Node: addSolutionUpdatesExistingSolution
// Node: verifyNoInteractions
// Node: ValueSource
// Node: addSolutionThrowsExceptionIfSubmitted
// Node: verifyNoMoreInteractions
// Node: addSolutionThrowsExceptionIfGivenUp
// Node: addSolutionNewSubmittedCompleteSolution
// Node: thenAnswer
// Node: getArgument
// Node: addSolutionNewSubmittedIncompleteSolution
// Node: addSolutionNewInProgressSolution
// Node: addSolution_SubmitAction_BlankText_ThrowsException
package com.itachallenge.user.dto;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class SolvedDtoTest {

    @Test
    void testNoArgsConstructorAndSetters() {
        SolvedDto dto = new SolvedDto();
        dto.setSolved(true);
        dto.setTimesSolved(5);

        assertTrue(dto.isSolved());
        assertEquals(5, dto.getTimesSolved());
    }

    @Test
    void testAllArgsConstructor() {
        SolvedDto dto = new SolvedDto(false, 3);

        assertFalse(dto.isSolved());
        assertEquals(3, dto.getTimesSolved());
    }

    @Test
    void testEqualsAndHashCode() {
        SolvedDto dto1 = new SolvedDto(true, 2);
        SolvedDto dto2 = new SolvedDto(true, 2);
        SolvedDto dto3 = new SolvedDto(false, 5);

        assertEquals(dto1, dto2);
        assertEquals(dto1.hashCode(), dto2.hashCode());
        assertNotEquals(dto1, dto3);
    }

    @Test
    void testToString() {
        SolvedDto dto = new SolvedDto(true, 7);
        String result = dto.toString();

        assertTrue(result.contains("isSolved=true"));
        assertTrue(result.contains("timesSolved=7"));
    }
}


// Node: testNoArgsConstructorAndSetters
// Node: setSolved
// Node: setTimesSolved
// Node: testAllArgsConstructor
// Node: testEqualsAndHashCode
// Node: UserSolutionRequestDto
package com.itachallenge.user.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.user.document.enums.SolutionAction;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.*;
class UserSolutionRequestDtoTest {

    private UserSolutionRequestDto userSolutionRequestDto;
    String userID = UUID.randomUUID().toString();
    String challengeId = UUID.randomUUID().toString();
    String languageId = UUID.randomUUID().toString();
    SolutionAction action = SolutionAction.SAVE;
    String solutionText = "This is my solution";
    UserSolutionRequestDto solutionDto = new UserSolutionRequestDto();

    @BeforeEach
    void setUp() {
        userSolutionRequestDto = UserSolutionRequestDto.builder()
                .userId("validUserId")
                .challengeId("validChallengeId")
                .languageId("validLanguageId")
                .action(SolutionAction.SAVE)
                .solutionText("Valid solution text")
                .build();
    }

    @Test
    void testLombokGeneratedMethods() {
        UserSolutionRequestDto dto1 = UserSolutionRequestDto.builder().build();

        assertThat(dto1).isNotNull();
        assertThat(dto1.toString()).isNotEmpty();
        assertThat(dto1.getClass()).isEqualTo(UserSolutionRequestDto.class);
    }

    @Test
    void getterUserSolutionDto_test() {
        assertNotNull(userSolutionRequestDto);
        assertEquals("validUserId", userSolutionRequestDto.getUserId());
        assertEquals("validChallengeId", userSolutionRequestDto.getChallengeId());
        assertEquals("validLanguageId", userSolutionRequestDto.getLanguageId());
        assertEquals("Valid solution text", userSolutionRequestDto.getSolutionText());
        assertEquals(SolutionAction.SAVE, userSolutionRequestDto.getAction());
    }

    @Test
    void noArgsConstructor_GetterAndSetter_UserSolutionDto_test(){
        solutionDto.setUserId(userID);
        solutionDto.setChallengeId(challengeId);
        solutionDto.setLanguageId(languageId);
        solutionDto.setAction(SolutionAction.SAVE);
        solutionDto.setSolutionText(solutionText);

        assertThat(solutionDto.getUserId()).isEqualTo(userID);
        assertThat(solutionDto.getChallengeId()).isEqualTo(challengeId);
        assertThat(solutionDto.getLanguageId()).isEqualTo(languageId);
        assertThat(solutionDto.getAction()).isEqualTo(action);
        assertThat(solutionDto.getSolutionText()).isEqualTo(solutionText);
    }

    @Test
    void jsonSerialization_test() throws Exception{
        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(userSolutionRequestDto);
        assertTrue(json.contains("\"uuid_user\":\"validUserId\""));
        assertTrue(json.contains("\"uuid_language\":\"validLanguageId\""));
        assertTrue(json.contains("\"uuid_challenge\":\"validChallengeId\""));
        assertTrue(json.contains("\"solution_text\":\"Valid solution text\""));
        assertTrue(json.contains("\"action\":\"SAVE\""));
    }
    @Test
    void requiredArgsConstructor_userSolutionScoreDto_test(){
        UserSolutionRequestDto userSolutionRequestDto1 = new UserSolutionRequestDto(
                userID, challengeId, languageId, SolutionAction.SAVE, solutionText);
        assertThat(userSolutionRequestDto1.getUserId()).isEqualTo(userID);
        assertThat(userSolutionRequestDto1.getChallengeId()).isEqualTo(challengeId);
        assertThat(userSolutionRequestDto1.getLanguageId()).isEqualTo(languageId);
        assertThat(userSolutionRequestDto1.getAction()).isEqualTo(action);
        assertThat(userSolutionRequestDto1.getSolutionText()).isEqualTo(solutionText);
    }

    @Test
    void testInvalidUserId() {
        userSolutionRequestDto.setUserId("invalidUserId");
        assertEquals("invalidUserId", userSolutionRequestDto.getUserId());
    }

    @Test
    void testInvalidSolutionText() {
        userSolutionRequestDto.setSolutionText("");
        assertEquals("", userSolutionRequestDto.getSolutionText());
    }
}

// Node: getterUserSolutionDto_test
// Node: noArgsConstructor_GetterAndSetter_UserSolutionDto_test
// Node: setLanguageId
// Node: setAction
// Node: jsonSerialization_test
// Node: requiredArgsConstructor_userSolutionScoreDto_test
// Node: testInvalidUserId
// Node: testInvalidSolutionText
package com.itachallenge.user.dto;

import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

class SubmitSolutionResponseDtoTest {

    @Test
    void jsonSerialization_includesStatusField_withInProgressStatus() throws Exception {
        SubmitSolutionResponseDto dto = SubmitSolutionResponseDto.builder()
                .solutionText("print('Hola Mundo')")
                .isSolved(true)
                .timesSolved(3)
                .status("IN_PROGRESS")
                .build();

        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(dto);

        assertTrue(json.contains("\"status\":\"IN_PROGRESS\""));
    }

    @Test
    void jsonSerialization_includesStatusField_withEndedStatus() throws Exception {
        SubmitSolutionResponseDto dto = SubmitSolutionResponseDto.builder()
                .solutionText("print('Hola Mundo')")
                .isSolved(false)
                .timesSolved(3)
                .status("SUBMITTED_COMPLETE")
                .build();

        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(dto);

        assertTrue(json.contains("\"status\":\"SUBMITTED_COMPLETE\""));
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/dto/SubmitSolutionResponseDtoTest.java:SubmitSolutionResponseDtoTest.<init>
// Node: jsonSerialization_includesStatusField_withInProgressStatus
// Node: print
// Node: jsonSerialization_includesStatusField_withEndedStatus
package com.itachallenge.user.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.user.document.enums.ChallengeStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.*;

class UserSolutionResponseDtoTest {

    private UserSolutionResponseDto userSolutionResponseDto;
    String userId = UUID.randomUUID().toString();
    String challengeId = UUID.randomUUID().toString();
    String languageId = UUID.randomUUID().toString();
    String solutionText = "This is my solution";
    String status = ChallengeStatus.IN_PROGRESS.name();
    UserSolutionResponseDto solutionScoreDto = new UserSolutionResponseDto();
    UserSolutionResponseDto dto1 = UserSolutionResponseDto.builder().build();

    @BeforeEach
    public void setUp() {
        userSolutionResponseDto = UserSolutionResponseDto.builder()
                .userId("validUserId")
                .challengeId("validChallengeId")
                .languageId("validLanguageId")
                .solutionText("Valid solution text")
                .build();
    }

    @Test
    void lombokGeneratedMethods_test() {
        assertThat(dto1).isNotNull();
        assertThat(dto1.getClass()).isEqualTo(UserSolutionResponseDto.class);
    }

    @Test
    void getterUserSolutionScoreDto_test() {
        assertNotNull(userSolutionResponseDto);
        assertEquals("validUserId", userSolutionResponseDto.getUserId());
        assertEquals("validChallengeId", userSolutionResponseDto.getChallengeId());
        assertEquals("validLanguageId", userSolutionResponseDto.getLanguageId());
        assertEquals("Valid solution text", userSolutionResponseDto.getSolutionText());
    }

    @Test
    void noArgsConstructor_GetterAndSetter_UserSolutionScoreDto_test(){
        solutionScoreDto.setUserId(userId);
        solutionScoreDto.setChallengeId(challengeId);
        solutionScoreDto.setLanguageId(languageId);
        solutionScoreDto.setSolutionText(solutionText);

        assertThat(solutionScoreDto.getUserId()).isEqualTo(userId);
        assertThat(solutionScoreDto.getChallengeId()).isEqualTo(challengeId);
        assertThat(solutionScoreDto.getLanguageId()).isEqualTo(languageId);
        assertThat(solutionScoreDto.getSolutionText()).isEqualTo(solutionText);
    }

    @Test
    void jsonSerialization_test() throws Exception{
        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(userSolutionResponseDto);
        assertTrue(json.contains("\"uuid_user\":\"validUserId\""));
        assertTrue(json.contains("\"uuid_language\":\"validLanguageId\""));
        assertTrue(json.contains("\"uuid_challenge\":\"validChallengeId\""));
        assertTrue(json.contains("\"solution_text\":\"Valid solution text\""));
    }

    @Test
    void requiredArgsConstructor_userSolutionScoreDto_test(){
        UserSolutionResponseDto userSolutionResponseDto1 = new UserSolutionResponseDto(
                userId, challengeId, languageId, solutionText,status);
        assertThat(userSolutionResponseDto1.getUserId()).isEqualTo(userId);
        assertThat(userSolutionResponseDto1.getChallengeId()).isEqualTo(challengeId);
        assertThat(userSolutionResponseDto1.getLanguageId()).isEqualTo(languageId);
        assertThat(userSolutionResponseDto1.getSolutionText()).isEqualTo(solutionText);
        assertThat(userSolutionResponseDto1.getStatus()).isEqualTo(status);
    }

    @Test
    void jsonSerialization_includesStatusField_withEndedStatus() throws Exception {
        UserSolutionResponseDto dto = UserSolutionResponseDto.builder()
                .userId("validUserId")
                .challengeId("validChallengeId")
                .languageId("validLanguageId")
                .solutionText("Valid solution text")
                .status("SUBMITTED_COMPLETE")
                .build();

        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(dto);

        assertTrue(json.contains("\"status\":\"SUBMITTED_COMPLETE\""));
    }

    @Test
    void jsonSerialization_includesStatusField_withInProgressStatus() throws Exception {
        UserSolutionResponseDto dto = UserSolutionResponseDto.builder()
                .userId("validUserId")
                .challengeId("validChallengeId")
                .languageId("validLanguageId")
                .solutionText("Valid solution text")
                .status("IN_PROGRESS")
                .build();

        ObjectMapper mapper = new ObjectMapper();
        String json = mapper.writeValueAsString(dto);

        assertTrue(json.contains("\"status\":\"IN_PROGRESS\""));
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/dto/UserSolutionResponseDtoTest.java:UserSolutionResponseDtoTest.<init>
// Node: UserSolutionResponseDto
// Node: getterUserSolutionScoreDto_test
// Node: noArgsConstructor_GetterAndSetter_UserSolutionScoreDto_test
package com.itachallenge.user.dto.userinteraction;

import static org.junit.jupiter.api.Assertions.*;

import java.time.LocalDateTime;
import java.util.UUID;

import com.itachallenge.userinteraction.document.InteractionDocument;
import org.junit.jupiter.api.Test;

class InteractionDocumentTest {

    @Test
    void equalsHashCodeAndToString_shouldCoverMainBranches() {
        UUID uuid = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();
        LocalDateTime createdAt = LocalDateTime.now();

        InteractionDocument a = new InteractionDocument(uuid, userId, challengeId, createdAt) {};
        InteractionDocument sameValues = new InteractionDocument(uuid, userId, challengeId, createdAt) {};
        InteractionDocument differentUuid = new InteractionDocument(UUID.randomUUID(), userId, challengeId, createdAt) {};

        InteractionDocument empty1 = new InteractionDocument() {};
        InteractionDocument empty2 = new InteractionDocument() {};

        assertEquals(a, a);

        assertEquals(a, sameValues);
        assertEquals(a.hashCode(), sameValues.hashCode());

        assertNotEquals(a, differentUuid);

        assertNotEquals(a, null);

        assertNotEquals(a, "some string");

        assertEquals(empty1, empty2);
        assertEquals(empty1.hashCode(), empty2.hashCode());

        assertNotNull(a.toString());
        assertNotNull(empty1.toString());
    }
}


// Node: InteractionDocument
package com.itachallenge.user.dto.userinteraction.bookmark;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertEquals;

class BookmarkResponseDtoTest {

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // ISO-8601

    @Test
    void builder_shouldCreateDtoWithProvidedValues() {
        UUID uuid = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        UUID userId = UUID.fromString("123e4567-e89b-12d3-a456-426614174001");
        UUID challengeId = UUID.fromString("123e4567-e89b-12d3-a456-426614174002");
        LocalDateTime createdAt = LocalDateTime.of(2023, 1, 1, 12, 0);

        BookmarkResponseDto.BookmarkResponseDtoBuilder builder = BookmarkResponseDto.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt);

        assertNotNull(builder.toString());

        BookmarkResponseDto dto = builder.build();

        assertEquals(uuid, dto.getUuid());
        assertEquals(userId, dto.getUserId());
        assertEquals(challengeId, dto.getChallengeId());
        assertEquals(createdAt, dto.getCreatedAt());
    }

    @Test
    void jsonContract_shouldSerializeAndDeserializeCorrectly() throws Exception {
        UUID uuid = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        UUID userId = UUID.fromString("123e4567-e89b-12d3-a456-426614174001");
        UUID challengeId = UUID.fromString("123e4567-e89b-12d3-a456-426614174002");
        LocalDateTime createdAt = LocalDateTime.of(2023, 1, 1, 12, 0);

        BookmarkResponseDto dto = BookmarkResponseDto.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        String json = MAPPER.writeValueAsString(dto);
        JsonNode root = MAPPER.readTree(json);

        assertEquals(uuid.toString(),root.get("uuid_bookmark").asText());
        assertEquals(userId.toString(),root.get("user_id").asText());
        assertEquals(challengeId.toString(),root.get("challenge_id").asText());

        assertEquals(createdAt, LocalDateTime.parse(root.get("created_at").asText()));

        BookmarkResponseDto back = MAPPER.readValue(json, BookmarkResponseDto.class);
        assertEquals(uuid, back.getUuid());
        assertEquals(userId, back.getUserId());
        assertEquals(challengeId, back.getChallengeId());
        assertEquals(createdAt, back.getCreatedAt());
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/dto/userinteraction/bookmark/BookmarkResponseDtoTest.java:BookmarkResponseDtoTest.<init>
// Node: builder_shouldCreateDtoWithProvidedValues
// Node: jsonContract_shouldSerializeAndDeserializeCorrectly
// Node: readTree
// Node: asText
package com.itachallenge.user.dto.userinteraction.favorite;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.time.LocalDateTime;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

class FavoriteResponseDtoTest {

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // ISO-8601

    @Test
    void builder_creaDtoConValoresCorrectos() {
        UUID uuid = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        UUID userId = UUID.fromString("123e4567-e89b-12d3-a456-426614174001");
        UUID challengeId = UUID.fromString("123e4567-e89b-12d3-a456-426614174002");
        LocalDateTime createdAt = LocalDateTime.of(2023, 1, 1, 12, 0);

        FavoriteResponseDto.FavoriteResponseDtoBuilder builder = FavoriteResponseDto.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt);

        assertNotNull(builder.toString());

        FavoriteResponseDto dto = builder.build();

        assertEquals(uuid, dto.getUuid());
        assertEquals(userId, dto.getUserId());
        assertEquals(challengeId, dto.getChallengeId());
        assertEquals(createdAt, dto.getCreatedAt());
    }

    @Test
    void jsonContract_serializaYDeserializa() throws Exception {
        UUID uuid = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        UUID userId = UUID.fromString("123e4567-e89b-12d3-a456-426614174001");
        UUID challengeId = UUID.fromString("123e4567-e89b-12d3-a456-426614174002");
        LocalDateTime createdAt = LocalDateTime.of(2023, 1, 1, 12, 0);

        FavoriteResponseDto dto = FavoriteResponseDto.builder()
                .uuid(uuid)
                .userId(userId)
                .challengeId(challengeId)
                .createdAt(createdAt)
                .build();

        String json = MAPPER.writeValueAsString(dto);
        JsonNode root = MAPPER.readTree(json);

        assertEquals(uuid.toString(),        root.get("uuid_favorite").asText());
        assertEquals(userId.toString(),      root.get("user_id").asText());
        assertEquals(challengeId.toString(), root.get("challenge_id").asText());
        // comparar como LocalDateTime para evitar problemas de formato (segundos)
        assertEquals(createdAt, LocalDateTime.parse(root.get("created_at").asText()));

        // ida y vuelta
        FavoriteResponseDto back = MAPPER.readValue(json, FavoriteResponseDto.class);
        assertEquals(uuid, back.getUuid());
        assertEquals(userId, back.getUserId());
        assertEquals(challengeId, back.getChallengeId());
        assertEquals(createdAt, back.getCreatedAt());
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/dto/userinteraction/favorite/FavoriteResponseDtoTest.java:FavoriteResponseDtoTest.<init>
// Node: builder_creaDtoConValoresCorrectos
// Node: jsonContract_serializaYDeserializa
// Node: formato
package com.itachallenge.submission.exception;

public class UnmodifiableSubmissionException extends RuntimeException {

    public UnmodifiableSubmissionException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/submission/exception/UnmodifiableSubmissionException.java:UnmodifiableSubmissionException.<init>
// Node: UnmodifiableSubmissionException
package com.itachallenge.submission.mapper;

import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.submission.document.SubmissionDocument;

import java.util.Objects;

public final class SubmissionMapper {

    private SubmissionMapper() {
    }

    public static SubmissionDto toDto(SubmissionDocument doc) {
        Objects.requireNonNull(doc, "SubmissionDocument cannot be null");

        return SubmissionDto.builder()
                .userId(doc.getUserId().toString())
                .challengeId(doc.getChallengeId().toString())
                .languageId(doc.getLanguageId().toString())
                .status(doc.getStatus().name())
                .submissionText(doc.getSubmissionText())
                .build();
    }
}


// Node: toDto
// Node: submissionText
// Node: getSubmissionText
package com.itachallenge.submission.repository;

import com.itachallenge.submission.document.SubmissionDocument;
import org.springframework.data.mongodb.repository.ReactiveMongoRepository;
import org.springframework.stereotype.Repository;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Repository
public interface SubmissionRepository extends ReactiveMongoRepository<SubmissionDocument, UUID> {

    Flux<SubmissionDocument> findAllByUserId(UUID userId);

    Mono<SubmissionDocument> findByUserIdAndChallengeIdAndLanguageId(UUID userId, UUID challengeId, UUID languageId);
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/submission/repository/SubmissionRepository.java:SubmissionRepository.<init>
// Node: findAllByUserId
package com.itachallenge.submission.service;

import com.itachallenge.challenge.dto.submission.SubmissionActionResponseDto;
import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.challenge.dto.submission.SubmissionActionRequestDto;
import com.itachallenge.challenge.service.IChallengeService;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.submission.document.SubmissionDocument;
import com.itachallenge.submission.enums.SubmissionAction;
import com.itachallenge.submission.enums.SubmissionStatus;
import com.itachallenge.submission.exception.UnmodifiableSubmissionException;
import com.itachallenge.submission.mapper.SubmissionMapper;
import com.itachallenge.submission.repository.SubmissionRepository;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Service
public class SubmissionServiceImpl implements SubmissionService {
    private final SubmissionRepository submissionRepository;
    private final IChallengeService challengeService;


    public SubmissionServiceImpl(SubmissionRepository submissionRepository, IChallengeService challengeService) {
        this.submissionRepository = submissionRepository;
        this.challengeService = challengeService;
    }

    @Override
    public Flux<SubmissionDto> getAllSubmissionsByUser(String userId) {
        return validateAndParseUuid(userId)
                .flatMapMany(uuid ->
                        submissionRepository.findAllByUserId(uuid)
                                .map(SubmissionMapper::toDto)
                );
    }

    @Override
    public Mono<SubmissionActionResponseDto> processSubmissionAction(String userId, SubmissionActionRequestDto request) {

        Mono<UUID> userUuidMono = validateAndParseUuid(userId);

        Mono<UUID> challengeUuidMono = Mono.justOrEmpty(request.getChallengeId())
                .switchIfEmpty(Mono.error(new BadRequestException("The 'challengeId' parameter cannot be null.")));

        Mono<UUID> languageUuidMono = Mono.justOrEmpty(request.getLanguageId())
                .switchIfEmpty(Mono.error(new BadRequestException("The 'languageId' parameter cannot be null.")));


        return Mono.zip(userUuidMono, challengeUuidMono, languageUuidMono)
                .flatMap(tuple -> {
                    UUID userUuid = tuple.getT1();
                    UUID challengeUuid = tuple.getT2();
                    UUID languageUuid = tuple.getT3();

                    SubmissionAction action = request.getAction();
                    if (action == SubmissionAction.SUBMIT &&
                            (request.getSubmissionText() == null || request.getSubmissionText().isBlank())) {
                        return Mono.error(new BadRequestException("The 'submissionText' parameter cannot be blank when action is SUBMIT."));
                    }

                    SubmissionStatus targetStatus = action.toStatus();


                    return submissionRepository
                            .findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid)
                            .flatMap(existing -> {
                                if (existing.getStatus() == SubmissionStatus.SUBMITTED_COMPLETE
                                        || existing.getStatus() == SubmissionStatus.SUBMITTED_INCOMPLETE) {
                                    return Mono.error(new UnmodifiableSubmissionException(
                                            "Submission cannot be modified once submitted."));
                                }

                                existing.setStatus(targetStatus);
                                existing.setSubmissionText(request.getSubmissionText());
                                return submissionRepository.save(existing);
                            })
                            .switchIfEmpty(Mono.defer(() -> {
                                SubmissionDocument created = SubmissionDocument.builder()
                                        .submissionId(UUID.randomUUID())
                                        .userId(userUuid)
                                        .challengeId(challengeUuid)
                                        .languageId(languageUuid)
                                        .status(targetStatus)
                                        .submissionText(request.getSubmissionText())
                                        .build();

                                return submissionRepository.save(created);
                            }))
                            .flatMap(saved -> {
                                if (saved.getStatus() == SubmissionStatus.SUBMITTED_COMPLETE) {
                                    return challengeService.addChallengeToSolved(challengeUuid.toString())
                                            .map(solvedDto -> SubmissionActionResponseDto.builder()
                                                    .submissionText(saved.getSubmissionText())
                                                    .status(saved.getStatus().name())
                                                    .isSolved(true)
                                                    .timesSolved(solvedDto.getTimesSolved())
                                                    .build());
                                }

                                return Mono.just(SubmissionActionResponseDto.builder()
                                        .submissionText(saved.getSubmissionText())
                                        .status(saved.getStatus().name())
                                        .isSolved(false)
                                        .timesSolved(null)
                                        .build());
                            });
                });
    }


    private Mono<UUID> validateAndParseUuid(String userId) {
        if (userId == null || userId.trim().isEmpty()) {
            return Mono.error(new BadRequestException("The 'userId' parameter cannot be null or empty."));
        }
        return Mono.fromCallable(() -> UUID.fromString(userId.trim()))
                .onErrorMap(IllegalArgumentException.class,
                        ex -> new BadRequestException("The 'userId' parameter must be a valid UUID."));
    }

}

// Node: processSubmissionAction
// Node: justOrEmpty
// Node: getT3
// Node: toStatus
// Node: setSubmissionText
// Node: submissionId
package com.itachallenge.submission.service;

import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.challenge.dto.submission.SubmissionActionRequestDto;
import com.itachallenge.challenge.dto.submission.SubmissionActionResponseDto;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public interface SubmissionService {

    Flux<SubmissionDto> getAllSubmissionsByUser(String userId);

    Mono<SubmissionActionResponseDto> processSubmissionAction(String userId, SubmissionActionRequestDto request);


}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/submission/service/SubmissionService.java:SubmissionService.<init>
package com.itachallenge.submission.enums;

import com.itachallenge.common.exception.BadRequestException;

public enum SubmissionAction {

    SAVE,
    SUBMIT,
    GIVE_UP;

    public static SubmissionAction fromString(String action) {
        try {
            return SubmissionAction.valueOf(action.toUpperCase());
        } catch (Exception e) {
            throw new BadRequestException("Invalid submission action: " + action);
        }
    }

    public SubmissionStatus toStatus() {
        return switch (this) {
            case SAVE -> SubmissionStatus.IN_PROGRESS;
            case SUBMIT -> SubmissionStatus.SUBMITTED_COMPLETE;
            case GIVE_UP -> SubmissionStatus.SUBMITTED_INCOMPLETE;
        };
    }
}


package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.SolvedDto;
import com.itachallenge.challenge.service.IChallengeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@RestController
@Validated
@RequestMapping(value = "/itachallenge/api/v1/challenge/solved")
@RequiredArgsConstructor
public class ChallengeSolvedController {

    private static final Logger log = LoggerFactory.getLogger(ChallengeSolvedController.class);

    private final IChallengeService challengeService;

    @PostMapping("/{challengeId}")
    @Operation(
            operationId = "Add a challenge to User's solved challenges.",
            summary = "Add a challenge to solved challenges.",
            description = "The ID Challenge sent through the URI is added to the user's solved challenges. User Id is determined from the headers.",
            responses = {
                    @ApiResponse(responseCode = "200", content = {@Content(schema = @Schema(implementation = SolvedDto.class), mediaType = "application/json")}),
                    @ApiResponse(responseCode = "404", description = "The Challenge with given Id was not found."),
                    @ApiResponse(responseCode = "500", description = "Internal Server Error")
            }
    )
    public Mono<ResponseEntity<SolvedDto>> addChallengeToSolved(@PathVariable String challengeId) {
        return challengeService.addChallengeToSolved(challengeId)
                .map(solvedDto -> {
                    if (solvedDto.isSolved()) {
                        log.info("Challenge '{}' has increased his value timesSolved", challengeId);
                        return ResponseEntity.ok(solvedDto);
                    }
                    log.info("Challenge '{}' could not be found, so the value timesSoved has not been increased", challengeId);
                    return ResponseEntity.ok(solvedDto);
                });
    }

}


// Node: setTopic
// Node: IllegalStateException
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.itachallenge.challenge.enums.AssociationType;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.*;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Objects;
import java.util.UUID;

@Component
@JsonInclude(JsonInclude.Include.NON_EMPTY)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@NoArgsConstructor
@Builder(toBuilder = true)
@Getter
@Setter
public class ResourceDto {

    @JsonProperty(value = "resourceId", index = 0)
    @NotNull(message = "{resource.id.notNull}")
    private UUID resourceId;

    @JsonProperty(value = "title", index = 1)
    @NotEmpty(message = "{resource.title.notEmpty}")
    private String title;

    @JsonProperty(value = "description", index = 2)
    @NotEmpty(message = "{resource.description.notEmpty}")
    private String description;

    @JsonProperty(value = "url", index = 3)
    @NotEmpty(message = "{resource.url.notEmpty}")
    private String url;

    @JsonProperty(value = "topic", index = 4)
    @NotNull(message = "{resource.topic.notNull}")
    private Topic topic;

    @JsonProperty(value = "contentType", index = 5)
    @NotNull(message = "{resource.contentType.notNull}")
    private ResourceContentType contentType;

    @JsonProperty(value = "challengeIds", index = 6)
    @NotNull(message = "{resource.challengeIds.notNull}")
    private List<UUID> challengeIds;

    @JsonProperty(value = "associationType", index = 7)
    @NotNull(message = "{resource.associationType.notNull}")
    private AssociationType associationType;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ResourceDto that = (ResourceDto) o;
        return Objects.equals(resourceId, that.resourceId) &&
                Objects.equals(title, that.title) &&
                Objects.equals(description, that.description) &&
                Objects.equals(url, that.url) &&
                Objects.equals(topic, that.topic) &&
                Objects.equals(contentType, that.contentType) &&
                Objects.equals(challengeIds, that.challengeIds) &&
                Objects.equals(associationType, that.associationType);
    }

    @Override
    public int hashCode() {
        return Objects.hash(resourceId, title, description, url, topic, contentType, challengeIds, associationType);
    }

}

package com.itachallenge.challenge.dto;

import lombok.Getter;
import lombok.Setter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
@Getter @Setter
public class GenericResultDto<T> {

    private int offset;
    private int limit;
    private int count;
    private T[] results;

    @Autowired
    public GenericResultDto() {}

    public GenericResultDto(int offset, int limit, int count, T[] results) {
        this.offset = offset;
        this.limit = limit;
        this.count = count;
        this.results = results;
    }


    public void setInfo(int offset, int limit, int count, T[] results) {
        this.offset = offset;
        this.limit = limit;
        this.count = count;
        this.results = results;
    }

}

package com.itachallenge.submission.mapper;

import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.submission.document.SubmissionDocument;
import com.itachallenge.submission.enums.SubmissionStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

class SubmissionMapperTest {

    private static final String USER_ID_TEXT = "c4feec44-ac54-4e99-852b-9ba56c479ba5";
    private static final UUID USER_ID = UUID.fromString(USER_ID_TEXT);

    private static final String CHALLENGE_ID_TEXT = "c4feec44-ac54-4e99-852b-9ba56c476c47";
    private static final UUID CHALLENGE_ID = UUID.fromString(CHALLENGE_ID_TEXT);

    private static final String LANGUAGE_ID_TEXT = "c4feec44-ac54-4e99-852b-9ba56c47eec4";
    private static final UUID LANGUAGE_ID = UUID.fromString(LANGUAGE_ID_TEXT);

    private static final SubmissionStatus SUBMISSION_STATUS = SubmissionStatus.IN_PROGRESS;
    private static final String SUBMISSION_TEXT = "Hello World!!";

    private SubmissionDocument document;

    @BeforeEach
    void setUp() {
        document = mock(SubmissionDocument.class);
        when(document.getUserId()).thenReturn(USER_ID);
        when(document.getChallengeId()).thenReturn(CHALLENGE_ID);
        when(document.getLanguageId()).thenReturn(LANGUAGE_ID);
        when(document.getStatus()).thenReturn(SUBMISSION_STATUS);
        when(document.getSubmissionText()).thenReturn(SUBMISSION_TEXT);
    }

    @Test
    void toDto_shouldMapAllFields() {
        SubmissionDto dto = SubmissionMapper.toDto(document);

        assertEquals(USER_ID_TEXT, dto.getUserId());
        assertEquals(CHALLENGE_ID_TEXT, dto.getChallengeId());
        assertEquals(LANGUAGE_ID_TEXT, dto.getLanguageId());
        assertEquals(SUBMISSION_STATUS.name(), dto.getStatus());
        assertEquals(SUBMISSION_TEXT, dto.getSubmissionText());
    }

    @Test
    void toDto_nullDocument_shouldThrowNullPointerException() {
        NullPointerException ex = assertThrows(NullPointerException.class, () -> SubmissionMapper.toDto(null));
        assertEquals("SubmissionDocument cannot be null", ex.getMessage());
    }
}

// Node: toDto_shouldMapAllFields
// Node: toDto_nullDocument_shouldThrowNullPointerException
package com.itachallenge.submission.document;

import com.itachallenge.submission.enums.SubmissionStatus;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class SubmissionDocumentTest {

    private SubmissionDocument submissionDocumentAllArgs;
    private SubmissionDocument submissionDocumentNoArgs;

    private final String submissionIdText = "c4feec44-ac54-4e99-852b-9ba56c47e56f";
    private final UUID submissionId = UUID.fromString(submissionIdText);

    private final String userIdText = "c4feec44-ac54-4e99-852b-9ba56c479ba5";
    private final UUID userId = UUID.fromString(userIdText);

    private final String challengeIdText = "c4feec44-ac54-4e99-852b-9ba56c476c47";
    private final UUID challengeId = UUID.fromString(challengeIdText);

    private final String languageIdText = "c4feec44-ac54-4e99-852b-9ba56c47eec4";
    private final UUID languageId = UUID.fromString(languageIdText);
    private final SubmissionStatus submissionStatus = SubmissionStatus.IN_PROGRESS;

    private final String submissionText = "Hello World!!";

    @BeforeEach
    void setUp() {
        submissionDocumentAllArgs = new SubmissionDocument(submissionId, userId, challengeId, languageId, submissionStatus, submissionText);
        submissionDocumentNoArgs = new SubmissionDocument();
    }

    @DisplayName("Should create SubmissionDocument using AllArgsConstructor")
    @Test
    void shouldCreateDocumentWithAllArgsConstructor() {

        assertEquals(UUID.fromString(submissionIdText), submissionDocumentAllArgs.getSubmissionId());
        assertEquals(UUID.fromString(userIdText), submissionDocumentAllArgs.getUserId());
        assertEquals(SubmissionStatus.IN_PROGRESS, submissionDocumentAllArgs.getStatus());
    }

    @DisplayName("Should build SubmissionDocument correctly using Lombok Builder")
    @Test
    void shouldBuildDocumentCorrectly() {

        SubmissionDocument doc = SubmissionDocument.builder()
                .submissionId(submissionId)
                .userId(userId)
                .challengeId(challengeId)
                .languageId(languageId)
                .status(submissionStatus)
                .submissionText(submissionText)
                .build();

        assertEquals(UUID.fromString(submissionIdText), doc.getSubmissionId());
        assertEquals(UUID.fromString(userIdText), doc.getUserId());
        assertEquals(UUID.fromString(challengeIdText), doc.getChallengeId());
        assertEquals(UUID.fromString(languageIdText), doc.getLanguageId());
        assertEquals(SubmissionStatus.IN_PROGRESS, doc.getStatus());
    }

    @DisplayName("Should set and get fields correctly using Setters")
    @Test
    void shouldSetAndGetFieldsCorrectly() {

        submissionDocumentAllArgs.setSubmissionId(userId);

        assertEquals(UUID.fromString(userIdText), submissionDocumentAllArgs.getSubmissionId());
    }

    @DisplayName("Should return SubmissionId UUID correctly")
    @Test
    void shouldReturnUuidCorrectly() {
        assertEquals(UUID.fromString(submissionIdText), submissionDocumentAllArgs.getSubmissionId());
    }

    @DisplayName("Should return UserId UUID correctly")
    @Test
    void shouldReturnUserUuidCorrectly() {
        assertEquals(UUID.fromString(userIdText), submissionDocumentAllArgs.getUserId());
    }

    @DisplayName("Should return ChallengeId UUID correctly")
    @Test
    void shouldReturnChallengeUuidCorrectly() {
        assertEquals(UUID.fromString(challengeIdText), submissionDocumentAllArgs.getChallengeId());
    }

    @DisplayName("Should return LanguageId UUID correctly")
    @Test
    void shouldReturnLanguageUuidCorrectly() {
        assertEquals(UUID.fromString(languageIdText), submissionDocumentAllArgs.getLanguageId());
    }

    @DisplayName("Should return Status correctly")
    @Test
    void shouldReturnStatusCorrectly() {
        assertEquals(SubmissionStatus.IN_PROGRESS, submissionDocumentAllArgs.getStatus());
    }

    @DisplayName("Should return SubmissionText correctly")
    @Test
    void shouldReturnSubmissionAttemptDocumentCorrectly() {
        assertEquals(submissionText, submissionDocumentAllArgs.getSubmissionText());
    }

    @DisplayName("Should instantiate document using NoArgsConstructor")
    @Test
    void shouldInstantiateDocumentWithNoArgsConstructor() {
        assertNotNull(submissionDocumentNoArgs);
    }
}


// Node: shouldCreateDocumentWithAllArgsConstructor
// Node: getSubmissionId
// Node: shouldBuildDocumentCorrectly
// Node: shouldSetAndGetFieldsCorrectly
// Node: setSubmissionId
// Node: shouldReturnUuidCorrectly
// Node: shouldReturnUserUuidCorrectly
// Node: shouldReturnChallengeUuidCorrectly
// Node: shouldReturnLanguageUuidCorrectly
// Node: shouldReturnStatusCorrectly
// Node: shouldReturnSubmissionAttemptDocumentCorrectly
package com.itachallenge.submission.service;

import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.challenge.dto.submission.SubmissionActionRequestDto;
import com.itachallenge.challenge.service.IChallengeService;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.submission.document.SubmissionDocument;
import com.itachallenge.submission.enums.SubmissionAction;
import com.itachallenge.submission.enums.SubmissionStatus;
import com.itachallenge.submission.repository.SubmissionRepository;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import com.itachallenge.challenge.dto.SolvedDto;
import com.itachallenge.submission.exception.UnmodifiableSubmissionException;

import static org.mockito.ArgumentMatchers.anyString;

import java.util.UUID;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class SubmissionServiceImplTest {

    @Mock
    private SubmissionRepository submissionRepository;
    @Mock
    private IChallengeService challengeService;



    @InjectMocks
    private SubmissionServiceImpl submissionService;

    @Test
    void getAllSubmissionsByUser_shouldReturnSubmissionDocuments() {
        UUID userUuid = UUID.randomUUID();
        UUID challengeUuid = UUID.randomUUID();
        UUID languageUuid = UUID.randomUUID();

        String userId = userUuid.toString();
        String submissionText = "Hello World!!";

        SubmissionDocument document = SubmissionDocument.builder()
                .submissionId(UUID.randomUUID())
                .userId(userUuid)
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .status(SubmissionStatus.IN_PROGRESS)
                .submissionText(submissionText)
                .build();

        when(submissionRepository.findAllByUserId(userUuid))
                .thenReturn(Flux.just(document));

        Flux<SubmissionDto> result =
                submissionService.getAllSubmissionsByUser(userId);

        StepVerifier.create(result)
                .assertNext(submission -> {
                    Assertions.assertEquals(userUuid.toString(), submission.getUserId());
                    Assertions.assertEquals(challengeUuid.toString(), submission.getChallengeId());
                    Assertions.assertEquals(languageUuid.toString(), submission.getLanguageId());
                    Assertions.assertEquals(SubmissionStatus.IN_PROGRESS.name(), submission.getStatus());
                    Assertions.assertEquals(submissionText, submission.getSubmissionText());
                })
                .verifyComplete();
    }

    @Test
    void getAllSubmissionsByUser_shouldThrow_whenUserIdIsNull() {
        StepVerifier.create(submissionService.getAllSubmissionsByUser(null))
                .expectErrorMatches(ex ->
                        ex instanceof BadRequestException &&
                                ex.getMessage().contains("userId") &&
                                ex.getMessage().contains("cannot be null or empty"))
                .verify();
    }

    @Test
    void getAllSubmissionsByUser_shouldThrow_whenUserIdIsEmpty() {
        StepVerifier.create(submissionService.getAllSubmissionsByUser("   "))
                .expectErrorMatches(ex ->
                        ex instanceof BadRequestException &&
                                ex.getMessage().contains("userId") &&
                                ex.getMessage().contains("cannot be null or empty"))
                .verify();
    }

    @Test
    void getAllSubmissionsByUser_shouldThrow_whenUserIdIsInvalidUuid() {
        StepVerifier.create(submissionService.getAllSubmissionsByUser("not-a-uuid"))
                .expectErrorMatches(ex ->
                        ex instanceof BadRequestException &&
                                ex.getMessage().contains("userId") &&
                                ex.getMessage().contains("must be a valid UUID"))
                .verify();
    }

    @Test
    void createOrUpdateSubmission_shouldCreateInProgress_whenActionIsSave() {
        UUID userUuid = UUID.randomUUID();
        UUID challengeUuid = UUID.randomUUID();
        UUID languageUuid = UUID.randomUUID();

        SubmissionActionRequestDto request = SubmissionActionRequestDto.builder()
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .action(SubmissionAction.SAVE)
                .submissionText("draft text")
                .build();

        when(submissionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.empty());

        when(submissionRepository.save(any(SubmissionDocument.class)))
                .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        StepVerifier.create(submissionService.processSubmissionAction(userUuid.toString(), request))
                .assertNext(response -> {
                    Assertions.assertEquals("draft text", response.getSubmissionText());
                    Assertions.assertEquals(SubmissionStatus.IN_PROGRESS.name(), response.getStatus());
                    Assertions.assertFalse(response.getIsSolved());
                    Assertions.assertNull(response.getTimesSolved());
                })
                .verifyComplete();

        verify(challengeService, never()).addChallengeToSolved(anyString());
    }

    @Test
    void createOrUpdateSubmission_shouldSubmitComplete_andIncrementSolved() {
        UUID userUuid = UUID.randomUUID();
        UUID challengeUuid = UUID.randomUUID();
        UUID languageUuid = UUID.randomUUID();

        SubmissionDocument existing = SubmissionDocument.builder()
                .submissionId(UUID.randomUUID())
                .userId(userUuid)
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .status(SubmissionStatus.IN_PROGRESS)
                .submissionText("draft")
                .build();

        SubmissionActionRequestDto request = SubmissionActionRequestDto.builder()
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .action(SubmissionAction.SUBMIT)
                .submissionText("final")
                .build();

        when(submissionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.just(existing));

        when(submissionRepository.save(any(SubmissionDocument.class)))
                .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        when(challengeService.addChallengeToSolved(challengeUuid.toString()))
                .thenReturn(Mono.just(new SolvedDto(true, 3)));

        StepVerifier.create(submissionService.processSubmissionAction(userUuid.toString(), request))
                .assertNext(response -> {
                    Assertions.assertEquals(SubmissionStatus.SUBMITTED_COMPLETE.name(), response.getStatus());
                    Assertions.assertTrue(response.getIsSolved());
                    Assertions.assertEquals(3, response.getTimesSolved());
                })
                .verifyComplete();

        verify(challengeService).addChallengeToSolved(challengeUuid.toString());
    }

    @Test
    void createOrUpdateSubmission_shouldThrow_whenAlreadySubmitted() {
        UUID userUuid = UUID.randomUUID();
        UUID challengeUuid = UUID.randomUUID();
        UUID languageUuid = UUID.randomUUID();

        SubmissionDocument existing = SubmissionDocument.builder()
                .submissionId(UUID.randomUUID())
                .userId(userUuid)
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .status(SubmissionStatus.SUBMITTED_COMPLETE)
                .submissionText("done")
                .build();

        SubmissionActionRequestDto request = SubmissionActionRequestDto.builder()
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .action(SubmissionAction.SAVE)
                .submissionText("try change")
                .build();

        when(submissionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.just(existing));

        StepVerifier.create(submissionService.processSubmissionAction(userUuid.toString(), request))
                .expectError(UnmodifiableSubmissionException.class)
                .verify();

        verify(challengeService, never()).addChallengeToSolved(anyString());
    }

    @Test
    void createOrUpdateSubmission_shouldAllowEmptySubmissionText_whenActionIsSave() {
        UUID userUuid = UUID.randomUUID();
        UUID challengeUuid = UUID.randomUUID();
        UUID languageUuid = UUID.randomUUID();

        SubmissionActionRequestDto request = SubmissionActionRequestDto.builder()
                .challengeId(challengeUuid)
                .languageId(languageUuid)
                .action(SubmissionAction.SAVE)
                .submissionText("   ")
                .build();

        when(submissionRepository.findByUserIdAndChallengeIdAndLanguageId(userUuid, challengeUuid, languageUuid))
                .thenReturn(Mono.empty());

        when(submissionRepository.save(any(SubmissionDocument.class)))
                .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        StepVerifier.create(submissionService.processSubmissionAction(userUuid.toString(), request))
                .assertNext(response -> Assertions.assertEquals(SubmissionStatus.IN_PROGRESS.name(), response.getStatus()))
                .verifyComplete();
    }

}


// Node: getAllSubmissionsByUser_shouldReturnSubmissionDocuments
// Node: createOrUpdateSubmission_shouldCreateInProgress_whenActionIsSave
// Node: createOrUpdateSubmission_shouldSubmitComplete_andIncrementSolved
// Node: createOrUpdateSubmission_shouldThrow_whenAlreadySubmitted
// Node: createOrUpdateSubmission_shouldAllowEmptySubmissionText_whenActionIsSave
package com.itachallenge.submission.enums;

import com.itachallenge.common.exception.BadRequestException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import static org.junit.jupiter.api.Assertions.*;

class SubmissionStatusTest {

    @DisplayName("Should return SUBMITTED_COMPLETE status ignoring case")
    @ParameterizedTest
    @ValueSource(strings = {
            "SUBMITTED_COMPLETE", "submitted_complete", "Submitted_Complete"
    })
    void shouldReturnSubmittedCompleteIgnoringCase(String input) {
        // When
        SubmissionStatus result = SubmissionStatus.fromString(input);

        // Then
        assertEquals(SubmissionStatus.SUBMITTED_COMPLETE, result);
    }

    @DisplayName("Should return IN_PROGRESS status ignoring case")
    @ParameterizedTest
    @ValueSource(strings = {
            "IN_PROGRESS", "in_progress", "In_Progress"
    })
    void shouldReturnInProgressIgnoringCase(String input) {
        // When
        SubmissionStatus result = SubmissionStatus.fromString(input);

        // Then
        assertEquals(SubmissionStatus.IN_PROGRESS, result);
    }

    @DisplayName("Should return SUBMITTED_INCOMPLETE status ignoring case")
    @ParameterizedTest
    @ValueSource(strings = {
            "SUBMITTED_INCOMPLETE", "submitted_incomplete", "Submitted_Incomplete"
    })
    void shouldReturnSubmittedIncompleteIgnoringCase(String input) {
        // When
        SubmissionStatus result = SubmissionStatus.fromString(input);

        // Then
        assertEquals(SubmissionStatus.SUBMITTED_INCOMPLETE, result);
    }

    @DisplayName("Should return null when input status string is null")
    @Test
    void shouldReturnNullWhenInputIsNull() {
        assertThrows(BadRequestException.class, () ->
                SubmissionStatus.fromString(null)
        );
    }

    @DisplayName("Should return null when status value does not exist")
    @Test
    void shouldReturnNullWhenValueDoesNotExist() {
        String input = "UNKNOWN_STATUS";

        assertThrows(BadRequestException.class, () ->
                SubmissionStatus.fromString(input)
        );
    }
}


// Node: shouldReturnSubmittedCompleteIgnoringCase
// Node: shouldReturnInProgressIgnoringCase
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.SolvedDto;
import com.itachallenge.challenge.service.IChallengeService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class ChallengeSolvedControllerTest {

    private IChallengeService challengeService;
    private ChallengeSolvedController controller;

    @BeforeEach
    void setUp() {
        challengeService = mock(IChallengeService.class);
        controller = new ChallengeSolvedController(challengeService);
    }

    @Test
    void testAddChallengeToSolved_ReturnsOk_WhenSolvedIsTrue() {
        String challengeId = "123";
        SolvedDto solvedDto = new SolvedDto();
        solvedDto.setSolved(true);

        when(challengeService.addChallengeToSolved(challengeId))
                .thenReturn(Mono.just(solvedDto));

        StepVerifier.create(controller.addChallengeToSolved(challengeId))
                .assertNext(response -> {
                    assertEquals(HttpStatus.OK, response.getStatusCode());
                    assertNotNull(response.getBody());
                    assertTrue(response.getBody().isSolved());
                })
                .verifyComplete();
    }

    @Test
    void testAddChallengeToSolved_ReturnsOk_WhenSolvedIsFalse() {
        String challengeId = "456";
        SolvedDto solvedDto = new SolvedDto();
        solvedDto.setSolved(false);

        when(challengeService.addChallengeToSolved(challengeId))
                .thenReturn(Mono.just(solvedDto));

        StepVerifier.create(controller.addChallengeToSolved(challengeId))
                .assertNext(response -> {
                    assertEquals(HttpStatus.OK, response.getStatusCode());
                    assertNotNull(response.getBody());
                    assertFalse(response.getBody().isSolved());
                })
                .verifyComplete();
    }

    @Test
    void testAddChallengeToSolved_PropagatesError() {
        String challengeId = "999";
        when(challengeService.addChallengeToSolved(challengeId))
                .thenReturn(Mono.error(new RuntimeException("Test error")));

        StepVerifier.create(controller.addChallengeToSolved(challengeId))
                .expectErrorMatches(error ->
                        error instanceof RuntimeException &&
                                error.getMessage().equals("Test error"))
                .verify();
    }
}


// Node: testAddChallengeToSolved_ReturnsOk_WhenSolvedIsTrue
// Node: testAddChallengeToSolved_ReturnsOk_WhenSolvedIsFalse
package com.itachallenge.challenge.document;

import org.junit.jupiter.api.Test;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;

class SolutionTest {

    @Test
    void getUuid() {
        UUID uuid = UUID.randomUUID();
        SolutionDocument solution = new SolutionDocument(uuid, null, null);
        assertEquals(uuid, solution.getUuid());
    }

    @Test
    void getSolutionText() {
        String solutionText = "Solution Text";
        SolutionDocument solution = new SolutionDocument(null, solutionText, null);
        assertEquals(solutionText, solution.getSolutionText());
    }

    @Test
    void getIdLanguage() {
        UUID uuidLang = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        SolutionDocument solution = new SolutionDocument(null, null, uuidLang);
        assertEquals(uuidLang, solution.getIdLanguage());
    }
}


package com.itachallenge.challenge.document;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class DetailTest {

    @Test
    void getDescription() {
        String expectedDescription = "Description of the test";
        DetailDocument detail = new DetailDocument(expectedDescription);
        assertEquals(expectedDescription, detail.getDescription());
    }
}


package com.itachallenge.challenge.document;

import com.itachallenge.challenge.enums.Topic;
import org.junit.jupiter.api.Test;

import java.sql.Array;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.*;

import static java.time.LocalDateTime.now;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ChallengeTest {
    List<UUID> tags = List.of(UUID.randomUUID());

    @Test
    void getUuid() {
        UUID uuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument(uuid,
                null,
                null,
                null,
                null,
                null,
                null,
                Topic.LISTS,
                null,
                null,
                null,
                tags);
        assertEquals(uuid, challenge.getUuid());
    }

    @Test
    void getTitle() {
        String expectedTitle = "Test challenge";
        ChallengeDocument challenge = new ChallengeDocument(null,
                expectedTitle,
                null,
                null,
                null,
                null,
                null,
                Topic.COMPONENTS,
                null,
                null,
                null,
                tags);
        assertEquals(expectedTitle, challenge.getTitle());
    }

    @Test
    void getLevel() {
        String level = "Intermediate";
        ChallengeDocument challenge = new ChallengeDocument(null,
                null,
                level,
                null,
                null,
                null,
                null,
                Topic.COMPONENTS,
                null,
                null,
                null,
                tags);
        assertEquals(level, challenge.getLevel());
    }

    @Test
    void getCreationDate() {
        LocalDateTime creationDate = now();
        ChallengeDocument challenge = new ChallengeDocument(null,
                null,
                null,
                creationDate,
                null,
                null,
                null,
                Topic.COMPONENTS,
                null,
                null,
                null,
                tags);
        assertTrue(creationDate.truncatedTo(ChronoUnit.SECONDS).isEqual(challenge.getCreationDate().truncatedTo(ChronoUnit.SECONDS)));
    }

    @Test
    void getDetail() {
        DetailDocument detail = new DetailDocument(null);
        ChallengeDocument challenge = new ChallengeDocument(null,
                null,
                null,
                null,
                detail,
                null,
                null,
                Topic.COMPONENTS,
                null,
                null,
                null,
                tags);
        assertEquals(detail, challenge.getDetail());
    }

    @Test
    void getLanguages() {
        UUID uuid = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        UUID uuid2 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");
        Set<LanguageDocument> languages = Set.of(new LanguageDocument(uuid, "Javascript",
                "https://res.cloudinary.com/itachallenge/image/upload/v1739361249/language_icon_Javascript_asgn04.svg"),
                new LanguageDocument(uuid2, "Python", "https://res.cloudinary.com/itachallenge/image/upload/v1739361249/language_icon_Python_rphody.svg"));

        ChallengeDocument challenge = new ChallengeDocument(null, null, null, null, null, languages, null, Topic.COMPONENTS, null, null,null, tags);
        assertEquals(languages, challenge.getLanguages());
    }

    @Test
    void getSolutions() {
        List<UUID> solutions = List.of(UUID.randomUUID(),UUID.randomUUID());

        ChallengeDocument challenge = new ChallengeDocument(null,
                null,
                null,
                null,
                null,
                null,
                solutions,
                Topic.COMPONENTS,
                null,
                null,
                null,
                tags);
        assertEquals(solutions, challenge.getSolutions());
    }

    @Test
    void getTimesFavorite() {
        int timesFavorite = 20;

        ChallengeDocument challenge = new ChallengeDocument(null,
                null,
                null,
                null,
                null,
                null,
                null,
                Topic.COMPONENTS,
                timesFavorite,
                null,
                null,
                tags);
        assertEquals(timesFavorite, challenge.getTimesFavorite());
    }

    @Test
    void getTimesBookmark(){
        int timesBookmark = 30;

        ChallengeDocument challenge = new ChallengeDocument(null, null, null, null, null, null, null, Topic.COMPONENTS, null, timesBookmark,null, tags);
        assertEquals(timesBookmark, challenge.getTimesBookmark());
    }

    @Test
    void getTimesSolved() {
        int timesSolved = 21;

        ChallengeDocument challenge = new ChallengeDocument(null,
                null,
                null,
                null,
                null,
                null,
                null,
                Topic.COMPONENTS,
                null,
                null,
                timesSolved,
                tags);
        assertEquals(timesSolved, challenge.getTimesSolved());
    }

    @Test
    void getTagsTest() {
        UUID uuid = UUID.randomUUID();
        UUID idLanguage = UUID.randomUUID();
        TagDocument tag = new TagDocument(uuid, "POO", "bla bla bla",idLanguage);

        ChallengeDocument challenge = new ChallengeDocument(
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                Topic.COMPONENTS,
                20,
                null,
                null,
                List.of(tag.getIdTag())
        );

        assertTrue(challenge.getTags().contains(tag.getIdTag()));
        assertEquals(1, challenge.getTags().size());
    }

    @Test
    void increaseTimesSolved_whenTimesSolvedIsNull_shouldSetToOne() {
        ChallengeDocument challenge = ChallengeDocument.builder()
                .uuid(UUID.randomUUID())
                .timesSolved(null)
                .build();

        challenge.increaseTimesSolved();

        assertEquals(1, challenge.getTimesSolved());
    }

    @Test
    void increaseTimesSolved_whenTimesSolvedIsNonNull_shouldIncrementByOne() {
        ChallengeDocument challenge = ChallengeDocument.builder()
                .uuid(UUID.randomUUID())
                .timesSolved(3)
                .build();

        challenge.increaseTimesSolved();

        assertEquals(4, challenge.getTimesSolved());
    }

    @Test
    void setTagsTest() {
        UUID firstTagId = UUID.randomUUID();
        UUID secondTagId = UUID.randomUUID();
        List<UUID> tags = List.of(firstTagId, secondTagId);

        ChallengeDocument challenge = new ChallengeDocument(
                null, null, null, null, null, null, null,
                Topic.COMPONENTS,
                20,
                null,
                null,
                new ArrayList<UUID>() {
                }
        );

        challenge.setTags(tags);

        assertEquals(2, challenge.getTags().size(), "El challenge debería tener 2 tags");
        assertTrue(tags.contains(firstTagId), "Debe contener el primer tag");
        assertTrue(tags.contains(secondTagId), "Debe contener el nuevo tag");
    }
}

package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.*;
import com.itachallenge.challenge.dto.*;
import com.itachallenge.challenge.enums.DifficultyLevel;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.exception.*;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.ChallengeRepository;
import com.itachallenge.challenge.repository.LanguageRepository;
import com.itachallenge.challenge.repository.SolutionRepository;
import com.itachallenge.common.exception.BadRequestException;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import org.springframework.test.util.ReflectionTestUtils;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;
import static org.assertj.core.api.Assertions.assertThat;

class ChallengeServiceImplTest {

    @Mock
    private ChallengeRepository challengeRepository;
    @Mock
    private LanguageRepository languageRepository;
    @Mock
    private SolutionRepository solutionRepository;
    @Mock
    private DocumentToDtoConverter<ChallengeDocument, ChallengeDto> challengeConverter;
    @Mock
    private DocumentToDtoConverter<LanguageDocument, LanguageDto> languageConverter;
    @Mock
    private DocumentToDtoConverter<SolutionDocument, SolutionDto> solutionConverter;
    @Mock
    private IUserService userService;
    @Mock
    private ITagService tagService;
    @Mock
    private ILanguageService ILanguageService;

    @InjectMocks
    private ChallengeServiceImpl challengeService;

    String title = "Títol";
    String languageName = "language name";
    String languageImage = "https://image-default.com/default.png";
    private ChallengeCreateDto formData;
    private ChallengeDocument challengeDocument;
    private ChallengeDto challengeDto;
    private LanguageDocument languageDocument;
    private SolutionDocument solutionDocument;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);

        ReflectionTestUtils.setField(challengeService, "challengeRepository", challengeRepository);
        ReflectionTestUtils.setField(challengeService, "solutionRepository", solutionRepository);
        ReflectionTestUtils.setField(challengeService, "challengeConverter", challengeConverter);
        ReflectionTestUtils.setField(challengeService, "solutionConverter", solutionConverter);
        ReflectionTestUtils.setField(challengeService, "userService", userService);
        ReflectionTestUtils.setField(challengeService, "tagService", tagService);

        String description = "Detall";
        String level = "EASY";
        String solutionBody = "Solution Text";
        List<UUID> tags = new ArrayList<>();
        tags.add(UUID.randomUUID());

        formData = new ChallengeCreateDto(title, description, DifficultyLevel.valueOf(level),
                languageName, solutionBody, Topic.LISTS, tags);

        UUID challengeRandomId = UUID.randomUUID();
        UUID languageRandomId = UUID.randomUUID();
        UUID solutionsRandomId = UUID.randomUUID();

        LocalDateTime localDateTime = LocalDateTime.of(2023, 6, 5, 12, 30, 0);
        String creationDate = "2023-06-05";
        String descriptionDetailDocument = "Detall";

        DetailDocument detail = new DetailDocument(descriptionDetailDocument);
        solutionDocument = new SolutionDocument(solutionsRandomId, solutionBody, languageRandomId);

        Integer popularity = 0;
        Float percentage = 0.0f;

        languageDocument = new LanguageDocument(languageRandomId, languageName, languageImage);
        LanguageDto languageDto = new LanguageDto(languageRandomId, languageName, languageImage);

        challengeDocument = new ChallengeDocument(challengeRandomId, title, level, localDateTime, detail,
                Set.of(languageDocument), List.of(solutionsRandomId), Topic.COMPONENTS,
                20, 30, 40, tags);

        challengeDto = getChallengeDtoMocked(challengeRandomId, title, level, creationDate, detail,
                Set.of(languageDto),
                List.of(solutionsRandomId),
                popularity, percentage, tags);
    }


    @Test
    void getChallengeById_ValidId_ChallengeFound() {
        // Arrange
        UUID challengeId = UUID.randomUUID();
        ChallengeDocument challengeDocument = new ChallengeDocument();
        ChallengeDto challengeDto = new ChallengeDto();
        challengeDto.setChallengeId(challengeId);
        challengeDto.setLevel("EASY");

        when(challengeRepository.findByUuid(challengeId)).thenReturn(Mono.just(challengeDocument));
        when(challengeConverter.convertDocumentToDto(any(), any())).thenReturn(challengeDto);

        // Act
        Mono<ChallengeDto> result = challengeService.getChallengeById(challengeId.toString());

        // Assert
        StepVerifier.create(result)
                .expectNextMatches(dto -> dto.getChallengeId().equals(challengeId) &&
                        dto.getLevel().equals(challengeDto.getLevel())
                )
                .expectComplete()
                .verify();

        verify(challengeRepository).findByUuid(challengeId);
        verify(challengeConverter).convertDocumentToDto(any(), any());
    }

    @Test
    void getChallengeById_InvalidId_ErrorThrown() {
        // Arrange
        String invalidId = "invalid-id";

        // Act
        Mono<ChallengeDto> result = challengeService.getChallengeById(invalidId);

        // Assert
        StepVerifier.create(result)
                .expectError(BadUUIDException.class)
                .verify();

        verifyNoInteractions(challengeRepository);
        verifyNoInteractions(challengeConverter);
    }

    @Test
    void getChallengeByIdWhenNonexistentIdThenReturnsError_test() {

        String idString = "4f8a6c91-8a9d-49b0-9f2c-3e67d2b18b7d";

        UUID id = UUID.fromString(idString);

        when(challengeRepository.findByUuid(id)).thenReturn(Mono.empty());

        Mono<ChallengeDto> result = challengeService.getChallengeById(idString);

        StepVerifier.create(result)
                .expectErrorMatches(error ->
                        error instanceof ChallengeNotFoundException
                                && error.getMessage().equals("Challenge with id " + id + " not found.")
                );
    }

    @Test
    void getAllChallenges_ChallengesExist_ChallengesReturned() {
        // Arrange
        int offset = 1;
        int limit = 2;

        // Simulate a set of ChallengeDocument with non-null UUID
        ChallengeDocument challenge1 = new ChallengeDocument();
        challenge1.setUuid(UUID.randomUUID());
        ChallengeDocument challenge2 = new ChallengeDocument();
        challenge2.setUuid(UUID.randomUUID());

        // Simulate a set of ChallengeDto
        ChallengeDto challengeDto1 = new ChallengeDto();
        ChallengeDto challengeDto2 = new ChallengeDto();

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(challenge1, challenge2));
        when(challengeConverter.convertDocumentFluxToDtoFlux(any(), any())).thenReturn(Flux.just(challengeDto1, challengeDto2));
        when(challengeRepository.count()).thenReturn(Mono.just(100L));
        // Act
        Mono<GenericResultDto<ChallengeDto>> result = challengeService.getAllChallenges(offset, limit);

        // Assert
        verify(challengeRepository).findAllByUuidNotNullExcludingTestingValues();
        verify(challengeConverter).convertDocumentFluxToDtoFlux(any(), any());


        StepVerifier.create(result)
                .expectSubscription()
                .assertNext(resultDto -> {
                    Assertions.assertEquals(100, resultDto.getCount());
                    Assertions.assertEquals(offset, resultDto.getOffset());
                    Assertions.assertEquals(limit, resultDto.getLimit());
                    Assertions.assertEquals(2, resultDto.getResults().length);
                    Assertions.assertEquals(challengeDto1, resultDto.getResults()[0]);
                    Assertions.assertEquals(challengeDto2, resultDto.getResults()[1]);
                })
                .expectComplete()
                .verify();
    }

    @Test
    void testGetSolutions() {
        // Arrange
        String challengeStringId = "e5f71456-62db-4323-a8d2-1d473d28a931";
        String languageStringId = "b5f78901-28a1-49c7-98bd-1ee0a555c678";
        UUID languageId = UUID.fromString(languageStringId);
        UUID solutionId1 = UUID.fromString("c8a5440d-6466-463a-bccc-7fefbe9396e4");
        UUID solutionId2 = UUID.fromString("0864463e-eb7c-4bb3-b8bc-766d71ab38b5");

        ChallengeDocument challenge = new ChallengeDocument();
        challenge.setUuid(UUID.fromString(challengeStringId));
        SolutionDocument solution1 = new SolutionDocument(solutionId1, "Solution 1", languageId);
        SolutionDocument solution2 = new SolutionDocument(solutionId2, "Solution 2", languageId);
        challenge.setSolutions(Arrays.asList(solution1.getUuid(), solution2.getUuid()));
        SolutionDto solutionDto1 = new SolutionDto(solution1.getUuid(), solution1.getSolutionText(), solution1.getIdLanguage());
        SolutionDto solutionDto2 = new SolutionDto(solution2.getUuid(), solution2.getSolutionText(), solution2.getIdLanguage());
        List<SolutionDto> expectedSolutions = List.of(solutionDto1, solutionDto2);
        LanguageDocument languageDocument = new LanguageDocument();
        languageDocument.setIdLanguage(languageId);

        when(challengeRepository.findByUuid(challenge.getUuid())).thenReturn(Mono.just(challenge));
        when(solutionRepository.findById(solutionId1)).thenReturn(Mono.just(solution1));
        when(solutionRepository.findById(solutionId2)).thenReturn(Mono.just(solution2));
        when(solutionConverter.convertDocumentFluxToDtoFlux(any(), any())).thenReturn(Flux.fromIterable(expectedSolutions));
        when(languageRepository.findByIdLanguage(languageId)).thenReturn(Mono.just(languageDocument));

        // Act
        Mono<GenericResultDto<SolutionDto>> resultMono = challengeService.getSolutions(challengeStringId, languageStringId);

        // Assert
        StepVerifier.create(resultMono)
                .expectNextMatches(resultDto -> {
                    assertThat(resultDto.getOffset()).isZero();
                    assertThat(resultDto.getLimit()).isEqualTo(expectedSolutions.size());
                    assertThat(resultDto.getCount()).isEqualTo(expectedSolutions.size());
                    return true;
                })
                .verifyComplete();

        verify(challengeRepository).findByUuid(UUID.fromString(challengeStringId));
        verify(solutionRepository, times(2)).findById(any(UUID.class));
        verify(solutionConverter, times(1)).convertDocumentFluxToDtoFlux(any(), any());
    }

    @Test
    void testGetSolutions_InvalidChallengeId() {
        // Arrange
        String invalidChallengeStringId = "invalid_challenge_id";
        String languageStringId = "b5f78901-28a1-49c7-98bd-1ee0a555c678";

        // Act & Assert
        StepVerifier.create(challengeService.getSolutions(invalidChallengeStringId, languageStringId))
                .expectError(BadUUIDException.class)
                .verify();

        verify(challengeRepository, never()).findByUuid(any(UUID.class));
        verify(solutionRepository, never()).findById(any(UUID.class));
        verify(solutionConverter, never()).convertDocumentFluxToDtoFlux(any(), any());
    }

    @Test
    void testGetSolutions_InvalidLanguageId() {
        // Arrange
        String challengeStringId = "e5f71456-62db-4323-a8d2-1d473d28a931";
        String invalidLanguageStringId = "invalid_language_id";

        // Act & Assert
        StepVerifier.create(challengeService.getSolutions(challengeStringId, invalidLanguageStringId))
                .expectError(BadUUIDException.class)
                .verify();

        verify(challengeRepository, never()).findByUuid(any(UUID.class));
        verify(solutionRepository, never()).findById(any(UUID.class));
        verify(solutionConverter, never()).convertDocumentFluxToDtoFlux(any(), any());
    }

    @Test
    void testGetSolutions_ChallengeNotFound() {
        // Arrange
        String nonExistentChallengeStringId = "2f948de0-6f0c-4089-90b9-7f70a0812322";
        String languageStringId = "b5f78901-28a1-49c7-98bd-1ee0a555c678";
        LanguageDocument languageDocument = new LanguageDocument();
        languageDocument.setIdLanguage(UUID.fromString(languageStringId));

        // Simulate that the challenge with the specified UUID is not found
        when(challengeRepository.findByUuid(any(UUID.class))).thenReturn(Mono.empty());
        when(languageRepository.findByIdLanguage(UUID.fromString(languageStringId))).thenReturn(Mono.just(languageDocument));

        // Act & Assert
        StepVerifier.create(challengeService.getSolutions(nonExistentChallengeStringId, languageStringId))
                .expectError(ChallengeNotFoundException.class)
                .verify();

        verify(challengeRepository).findByUuid(any(UUID.class));
        verify(solutionRepository, never()).findById(any(UUID.class));
        verify(solutionConverter, never()).convertDocumentFluxToDtoFlux(any(), any());
    }

@Test
void addChallengeToSolved_WhenChallengeTimesSolvedIsNull_IncreasesTimesSolvedAndReturnsSolvedDTO() {
        UUID challengeUuid = UUID.randomUUID();

        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesSolved(null);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

    StepVerifier.create(challengeService.addChallengeToSolved(challengeUuid.toString()))
                        .expectNextMatches(solvedDto -> {
                                return solvedDto.getTimesSolved() == 1 &&
                                                solvedDto.isSolved();
                        })
                        .verifyComplete();

        Assertions.assertEquals(1, challenge.getTimesSolved());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(challengeRepository, times(1)).save(challenge);
}

@Test
void addChallengeToSolved_WhenChallengeTimesSolvedIsZero_IncreasesTimesSolvedAndReturnsSolvedDTO() {
        UUID challengeUuid = UUID.randomUUID();

        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesSolved(0);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

    StepVerifier.create(challengeService.addChallengeToSolved(challengeUuid.toString()))
                        .expectNextMatches(solvedDto -> {
                                return solvedDto.getTimesSolved() == 1 &&
                                                solvedDto.isSolved();
                        })
                        .verifyComplete();

        Assertions.assertEquals(1, challenge.getTimesSolved());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(challengeRepository, times(1)).save(challenge);
}

    @Test
    void addChallengeToSolved_AlwaysIncreasesTimesSolvedAndReturnsSolvedDTO() {
        UUID challengeUuid = UUID.randomUUID();

        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesSolved = 5;
        challenge.setTimesSolved(initialTimesSolved);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(challengeRepository.save(any(ChallengeDocument.class)))
                .thenAnswer(invocation -> Mono.just(invocation.getArgument(0)));

        StepVerifier.create(challengeService.addChallengeToSolved(challengeUuid.toString()))
                .expectNextMatches(solvedDto ->
                        solvedDto.getTimesSolved() == initialTimesSolved + 1 &&
                                solvedDto.isSolved()
                )
                .verifyComplete();

        Assertions.assertEquals(initialTimesSolved + 1, challenge.getTimesSolved());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(challengeRepository, times(1)).save(any());
    }


    @Test
    void addSolution_ValidChallengeIdAndLanguageId_SolutionAdded() {
        // Arrange
        String challengeStringId = "dcacb291-b4aa-4029-8e9b-284c8ca80296";
        String languageStringId = "660e1b18-0c0a-4262-a28a-85de9df6ac5f";
        UUID challengeId = UUID.fromString(challengeStringId);
        UUID languageId = UUID.fromString(languageStringId);
        UUID solutionId = UUID.randomUUID();

        SolutionDocument solution = new SolutionDocument(solutionId, "Solution 1", languageId);
        SolutionDto solutionDto = new SolutionDto(solutionId, "Solution 1", languageId, challengeId);
        ChallengeDocument challengeDocument = new ChallengeDocument();
        challengeDocument.setUuid(challengeId);
        LanguageDocument languageDocument = new LanguageDocument();
        languageDocument.setIdLanguage(languageId);

        when(challengeRepository.save(any(ChallengeDocument.class))).thenReturn(Mono.just(challengeDocument));
        when(challengeRepository.findByUuid(challengeId)).thenReturn(Mono.just(challengeDocument));
        when(ILanguageService.findByIdLanguage(languageId)).thenReturn(Mono.just(languageDocument));
        when(solutionRepository.save(any(SolutionDocument.class))).thenReturn(Mono.just(solution));
        when(solutionConverter.convertDocumentFluxToDtoFlux(any(), any())).thenReturn(Flux.just(solutionDto));


        // Act
        Mono<SolutionDto> resultMono = challengeService.addSolution(solutionDto);
        // Assert
        StepVerifier.create(resultMono)
                .expectNextMatches(resultDto -> {
                    assertThat(resultDto.getUuid()).isEqualTo(solutionId);
                    assertThat(resultDto.getSolutionText()).isEqualTo("Solution 1");
                    assertThat(resultDto.getIdLanguage()).isEqualTo(languageId);
                    assertThat(resultDto.getIdChallenge()).isEqualTo(challengeId);
                    return true;
                })
                .verifyComplete();

        verify(challengeRepository).findByUuid(challengeId);
        verify(solutionRepository).save(any(SolutionDocument.class));
        verify(solutionConverter).convertDocumentFluxToDtoFlux(any(), any());
    }

    @Test
    void updateResourceByUuid_Success() {
        // Arrange
        String resourceId = UUID.randomUUID().toString();
        Map<String, Object> updates = new HashMap<>();
        updates.put("fieldName", "newValue");

        ChallengeDocument resource = new ChallengeDocument();
        resource.setUuid(UUID.fromString(resourceId));

        when(challengeRepository.findByUuid(any(UUID.class))).thenReturn(Mono.just(resource));
        when(challengeRepository.save(any(ChallengeDocument.class))).thenReturn(Mono.just(resource));

        // Act
        Mono<String> result = challengeService.updateResourceByUuid(resourceId, updates);

        // Assert
        StepVerifier.create(result)
                .expectNext("Resource updated successfully")
                .verifyComplete();

        verify(challengeRepository, times(1)).findByUuid(any(UUID.class));
        verify(challengeRepository, times(1)).save(any(ChallengeDocument.class));
    }

    @Test
    void updateResourceByUuid_ResourceNotFound() {
        // Arrange
        String resourceId = UUID.randomUUID().toString();
        Map<String, Object> updates = new HashMap<>();

        when(challengeRepository.findByUuid(any(UUID.class))).thenReturn(Mono.empty());

        // Act
        Mono<String> result = challengeService.updateResourceByUuid(resourceId, updates);

        // Assert
        StepVerifier.create(result)
                .expectError(ResourceNotFoundException.class)
                .verify();

        verify(challengeRepository, times(1)).findByUuid(any(UUID.class));
        verify(challengeRepository, times(0)).save(any(ChallengeDocument.class));
    }

    @Test
    void updateResourceByUuid_InvalidUUID() {

        String invalidUUID = "invalidUUID";
        Map<String, Object> updates = new HashMap<>();


        Mono<String> result = challengeService.updateResourceByUuid(invalidUUID, updates);

        StepVerifier.create(result)
                .expectError(BadUUIDException.class)
                .verify();

        verify(challengeRepository, times(0)).findByUuid(any(UUID.class));
        verify(challengeRepository, times(0)).save(any(ChallengeDocument.class));
    }

    @Test
    void addChallenge_test_success() {
        when(ILanguageService.findFirstByLanguageName(eq(languageName))).thenReturn(Mono.just(languageDocument)); // Valid language
        when(solutionRepository.save(any(SolutionDocument.class))).thenReturn(Mono.just(solutionDocument));
        when(tagService.getValidatedTags(eq(formData.getTags()))).thenReturn(Mono.just(true));
        when(challengeRepository.save(any(ChallengeDocument.class))).thenReturn(Mono.just(challengeDocument));
        when(challengeConverter.convertDocumentToDto(any(ChallengeDocument.class), eq(ChallengeDto.class))).thenReturn(challengeDto);

        // Act & Assert
        StepVerifier.create(challengeService.addChallenge(formData))
                .expectNext(challengeDto)
                .verifyComplete();

        verify(ILanguageService, times(1)).findFirstByLanguageName(eq(languageName));
        verify(solutionRepository, times(1)).save(any(SolutionDocument.class));
        verify(tagService, times(1)).getValidatedTags(eq(formData.getTags()));
        verify(challengeRepository, times(1)).save(any(ChallengeDocument.class));
        verify(challengeConverter, times(1)).convertDocumentToDto(any(ChallengeDocument.class), eq(ChallengeDto.class));
    }

    @Test
    void addChallenge_test_NonExistentLanguage() {
        when(ILanguageService.findFirstByLanguageName(eq(languageName))).thenReturn(Mono.empty()); // Not found language

        // Act & Assert
        StepVerifier.create(challengeService.addChallenge(formData))
                .expectErrorMatches(throwable -> throwable instanceof LanguageNotFoundException)
                .verify();

        verify(ILanguageService, times(1)).findFirstByLanguageName(eq(languageName));
    }

    private ChallengeDto getChallengeDtoMocked(UUID challengeId, String title, String level, String creationDate, DetailDocument detail,
                                               Set<LanguageDto> languages,
                                               List<UUID> solutions, Integer popularity, Float percentage, List<UUID> tags) {
        ChallengeDto challengeDocMocked = mock(ChallengeDto.class);
        when(challengeDocMocked.getChallengeId()).thenReturn(challengeId);
        when(challengeDocMocked.getTitle()).thenReturn(title);
        when(challengeDocMocked.getLevel()).thenReturn(level);
        when(challengeDocMocked.getDetail()).thenReturn(detail);
        when(challengeDocMocked.getCreationDate()).thenReturn(creationDate);
        when(challengeDocMocked.getLanguages()).thenReturn(languages);
        when(challengeDocMocked.getSolutions()).thenReturn(solutions);
        when(challengeDocMocked.getPopularity()).thenReturn(popularity);
        when(challengeDocMocked.getPercentage()).thenReturn(percentage);
        when(challengeDocMocked.getTags()).thenReturn(tags);
        return challengeDocMocked;
    }
    
    @Test
    void addChallenge_test_invalidTags() {
        when(ILanguageService.findFirstByLanguageName(eq(languageName)))
                .thenReturn(Mono.just(languageDocument));
        when(solutionRepository.save(any(SolutionDocument.class)))
                .thenReturn(Mono.just(solutionDocument));
                when(tagService.getValidatedTags(eq(formData.getTags())))
                .thenReturn(Mono.just(false));
        
        StepVerifier.create(challengeService.addChallenge(formData))
                .expectErrorMatches(throwable ->
                        throwable instanceof TagNotFoundException
                                && throwable.getMessage().equals("One or more tags are invalid")
                )
                .verify();
        
        verify(challengeRepository, never()).save(any(ChallengeDocument.class));
        verify(tagService, times(1)).getValidatedTags(eq(formData.getTags()));
    }
    
    @Test
    void addChallenge_test_emptyTags() {
        formData.setTags(Collections.emptyList());
        when(ILanguageService.findFirstByLanguageName(eq(languageName)))
                .thenReturn(Mono.just(languageDocument));
        when(solutionRepository.save(any(SolutionDocument.class)))
                .thenReturn(Mono.just(solutionDocument));
        when(tagService.getValidatedTags(eq(Collections.emptyList())))
                .thenReturn(Mono.just(true));
        when(challengeRepository.save(any(ChallengeDocument.class)))
                .thenReturn(Mono.just(challengeDocument));
        when(challengeConverter.convertDocumentToDto(any(ChallengeDocument.class), eq(ChallengeDto.class)))
                .thenReturn(challengeDto);
        
        StepVerifier.create(challengeService.addChallenge(formData))
                .expectNext(challengeDto)
                .verifyComplete();
                
        verify(ILanguageService, times(1)).findFirstByLanguageName(eq(languageName));
        verify(solutionRepository, times(1)).save(any(SolutionDocument.class));
        verify(tagService, times(1)).getValidatedTags(eq(Collections.emptyList()));
        verify(challengeRepository, times(1)).save(any(ChallengeDocument.class));
        verify(challengeConverter, times(1))
                .convertDocumentToDto(any(ChallengeDocument.class), eq(ChallengeDto.class));
    }

    @Test
    void deleteChallengeById_NotFound() {

        String id = "2f948de0-6f0c-4089-90b9-7f70a0812322";
        UUID uuid = UUID.fromString(id);

        when(challengeRepository.findByUuid(uuid)).thenReturn(Mono.empty());

        when(challengeRepository.deleteByUuid(uuid)).thenReturn(Mono.empty());

        Mono<DeleteResponseDto> result = challengeService.deleteChallengeById(id);

        StepVerifier.create(result)
                .expectError(ChallengeNotFoundException.class)
                .verify();
    }




    @Test
    void getChallengesByTopic_WhenChallengesExist_ReturnsResult() {
        Topic topic = Topic.DEBUGGING;
        int offset = 0;
        int limit = 10;

        when(challengeRepository.findByTopic(topic)).thenReturn(Flux.just(challengeDocument));
        when(challengeConverter.convertDocumentToDto(any(ChallengeDocument.class), eq(ChallengeDto.class)))
                .thenReturn(challengeDto);

        StepVerifier.create(challengeService.getChallengesByTopic(topic, offset, limit))
                .expectNextMatches(result ->
                        result.getTotal() == 1 &&
                                result.getResults().size() == 1 &&
                                result.getResults().get(0).getChallengeId().equals(challengeDto.getChallengeId()))
                .verifyComplete();
    }


    @Test
    void getChallengesByTopic_WhenNoChallengesExist_ReturnsEmptyResult() {
        Topic topic = Topic.DEBUGGING;
        int page = 0;
        int size = 10;

        when(challengeRepository.findByTopic(topic)).thenReturn(Flux.empty());

        StepVerifier.create(challengeService.getChallengesByTopic(topic, page, size))
                .expectNextMatches(result ->
                        result.getTotal() == 0 &&
                                result.getResults().isEmpty())
                .verifyComplete();
    }

    @Test
    void getChallengesByTopic_WhenErrorOccurs_ReturnsError() {
        Topic topic = Topic.COMPONENTS;
        int offset = 0;
        int limit = 10;

        when(challengeRepository.findByTopic(topic)).thenReturn(Flux.error(new RuntimeException("Database error")));

        StepVerifier.create(challengeService.getChallengesByTopic(topic, offset, limit))
                .expectErrorMatches(error ->
                        error instanceof RuntimeException &&
                                error.getMessage().equals("Database error"))
                .verify();
    }

    @Test
    void addChallengeToBookmarks_WhenChallengeUuidNotValid_ReturnsError() {
        StepVerifier.create(challengeService.addChallengeToBookmarks("InvalidUuid", UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToSolved_WhenChallengeUuidNotValid_ReturnsError() {
        StepVerifier.create(challengeService.addChallengeToSolved("InvalidUuid"))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToBookmarks_WhenUserUuidNotValid_ReturnsError() {
        StepVerifier.create(challengeService.addChallengeToBookmarks(UUID.randomUUID().toString(), "InvalidUuid"))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToBookmarks_WhenChallengeUuidIsNull_ReturnsError() {
        StepVerifier.create(challengeService.addChallengeToBookmarks(null, UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToBookmarks_WhenUserUuidIsNull_ReturnsError() {
        StepVerifier.create(challengeService.addChallengeToBookmarks(UUID.randomUUID().toString(), null))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToBookmarks_WhenChallengeNotFound_ReturnsError() {
        String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";
        UUID challengeUuid = UUID.randomUUID();

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.empty());

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof ChallengeNotFoundException &&
                                error.getMessage().equals(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid.toString())))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
    }

    @Test
    void addChallengeToSolved_WhenChallengeNotFound_ReturnsError() {
        String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";
        UUID challengeUuid = UUID.randomUUID();

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.empty());

        StepVerifier.create(challengeService.addChallengeToSolved(challengeUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof ChallengeNotFoundException &&
                                error.getMessage().equals(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid.toString())))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
    }

    @Test
    void addChallengeToBookmarks_WhenUserNotFound_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new UserNotFoundException(message)));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToBookmarks_WhenUserServiceReturnsCustomBadRequestException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new BadRequestException(message)));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToBookmarks_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new InternalServerErrorException(message)));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToBookmarks_WhenUserServiceReturnsAnyException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new Exception(message)));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof Exception &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToBookmarks_WhenAdded_IncreasesTimesBookmarkAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesBookmark = 20;

        challenge.setTimesBookmark(initialTimesBookmark);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(bookmarkDto -> {
                    return bookmarkDto.getTimesBookmarked() == initialTimesBookmark + 1 &&
                            bookmarkDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesBookmark + 1, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void addChallengeToBookmarks_WhenAddedAndInitialTimesFavoriteIsNull_IncreasesTimesBookmarkAndReturnsBookmarkDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesBookmark(null);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesBookmarked() == 1 &&
                            favoriteDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(1, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void addChallengeToBookmarks_WhenNotAdded_NotIncreaseTimesBookmarkAndReturnsBookmarkDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesBookmark = 20;

        challenge.setTimesBookmark(initialTimesBookmark);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(bookmarkDto -> {
                    return bookmarkDto.getTimesBookmarked() == initialTimesBookmark &&
                            bookmarkDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesBookmark, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(0)).save(any());
    }

    @ParameterizedTest
    @MethodSource
    void addChallengeToBookmarks_WhenNotAddedAndTimesBookmarkIsNullOrZero_SetTimesBookmarkToOneAndReturnsBookmarkDTO(Integer timesBookmark) {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesBookmark(timesBookmark);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(challengeService.addChallengeToBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(bookmarkDto -> {
                    return bookmarkDto.getTimesBookmarked() == 1 &&
                            bookmarkDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(1, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    public static Stream<Integer> addChallengeToBookmarks_WhenNotAddedAndTimesBookmarkIsNullOrZero_SetTimesBookmarkToOneAndReturnsBookmarkDTO() {
        return Stream.of(null, 0);
    }

    public static Stream<Integer> addChallengeToSolved_WhenNotAddedAndTimesSolvedIsNullOrZero_SetTimesSolvedToOneAndReturnsSolvedDTO() {
        return Stream.of(null, 0);
    }

    @Test
    void getChallengesByFilter_ValidParams_FiltersAppliedCorrectly() {
        // Arrange
        String idLanguage = UUID.randomUUID().toString();  // ID de lenguaje válido (String)
        String level = "EASY";  // Dificultad válida
        List<UUID> tags = List.of(UUID.randomUUID());  // Tags válidos
        int offset = 0;
        int limit = 10;

        ChallengeDto challenge1 = new ChallengeDto();
        challenge1.setTitle("Challenge 1");
        challenge1.setLevel(level);

        GenericResultDto<ChallengeDto> expectedResult = new GenericResultDto<>();
        expectedResult.setInfo(offset, limit, 1, new ChallengeDto[]{challenge1});

        UUID challengeId = UUID.randomUUID();
        UUID languageId = UUID.fromString(idLanguage);  // ID de lenguaje para comparación
        ChallengeDocument challengeDocument = new ChallengeDocument(
                challengeId,
                "Challenge 1",
                level,
                LocalDateTime.now(),
                new DetailDocument("Description"),
                Set.of(new LanguageDocument(languageId, "Language Name", "image.png")),
                List.of(UUID.randomUUID()),
                Topic.COMPONENTS,
                0, 0, 0, tags
        );

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(challengeDocument));

        when(challengeConverter.convertDocumentToDto(any(), eq(ChallengeDto.class)))
                .thenReturn(challenge1);

        // Act
        Flux<GenericResultDto<ChallengeDto>> result = challengeService.getChallengesByFilter(
                Optional.of(idLanguage),
                Optional.of(level),
                Optional.of(tags),
                offset,
                limit);

        // Assert
        StepVerifier.create(result)
                .expectNextMatches(genericResultDto -> {
                    assertNotNull(genericResultDto);
                    assertEquals(1, genericResultDto.getCount());
                    assertEquals("Challenge 1", genericResultDto.getResults()[0].getTitle());
                    assertEquals(level, genericResultDto.getResults()[0].getLevel());
                    return true;
                })
                .verifyComplete();
    }

    @Test
    void getChallengesByFilter_NoLanguage_FilterAppliedCorrectly() {
        // Arrange
        String level = "EASY";
        List<UUID> tags = List.of(UUID.randomUUID());
        int offset = 0;
        int limit = 10;

        ChallengeDto challenge1 = new ChallengeDto();
        challenge1.setTitle("Challenge 1");
        challenge1.setLevel(level);

        GenericResultDto<ChallengeDto> expectedResult = new GenericResultDto<>();
        expectedResult.setInfo(offset, limit, 1, new ChallengeDto[]{challenge1});

        UUID challengeId = UUID.randomUUID();
        ChallengeDocument challengeDocument = new ChallengeDocument(
                challengeId,
                "Challenge 1",
                level,
                LocalDateTime.now(),
                new DetailDocument("Description"),
                Set.of(new LanguageDocument(UUID.randomUUID(), "Other Language", "image.png")),
                List.of(UUID.randomUUID()),
                Topic.COMPONENTS,
                0, 0, 0, tags
        );

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(challengeDocument));

        when(challengeConverter.convertDocumentToDto(any(), eq(ChallengeDto.class)))
                .thenReturn(challenge1);

        // Act
        Flux<GenericResultDto<ChallengeDto>> result = challengeService.getChallengesByFilter(
                Optional.empty(),  // No language filter
                Optional.of(level),
                Optional.of(tags),
                offset,
                limit);

        // Assert
        StepVerifier.create(result)
                .expectNextMatches(genericResultDto -> {
                    assertNotNull(genericResultDto);
                    assertEquals(1, genericResultDto.getCount());
                    assertEquals("Challenge 1", genericResultDto.getResults()[0].getTitle());
                    assertEquals(level, genericResultDto.getResults()[0].getLevel());
                    return true;
                })
                .verifyComplete();
    }

    @Test
    void getChallengesByFilter_InvalidLevel_NoChallengesReturned() {
        // Arrange
        String idLanguage = UUID.randomUUID().toString();
        String invalidLevel = "HARD";  // Nivel inválido
        List<UUID> tags = List.of(UUID.randomUUID());
        int offset = 0;
        int limit = 10;

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.empty());

        // Act
        Flux<GenericResultDto<ChallengeDto>> result = challengeService.getChallengesByFilter(
                Optional.of(UUID.randomUUID().toString()),
                Optional.of(invalidLevel),
                Optional.of(List.of(UUID.randomUUID())),
                offset,
                limit);

        // Assert
        StepVerifier.create(result)
                .expectNextMatches(genericResultDto -> {
                    assertNotNull(genericResultDto);
                    assertEquals(0, genericResultDto.getCount());
                    return true;
                });
    }

    @Test
    void getChallengesByFilter_EmptyTags_NoChallengesReturned() {
        // Arrange
        String idLanguage = UUID.randomUUID().toString();
        String level = "EASY";
        List<UUID> tags = List.of();  // Tags vacíos
        int offset = 0;
        int limit = 10;

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.empty());

        // Act
        Flux<GenericResultDto<ChallengeDto>> result = challengeService.getChallengesByFilter(
                Optional.of(idLanguage),
                Optional.of(level),
                Optional.of(tags),
                offset,
                limit);

        // Assert
        StepVerifier.create(result)
                .expectNextMatches(genericResultDto -> {
                    assertNotNull(genericResultDto);
                    assertEquals(0, genericResultDto.getCount());
                    return true;
                });
    }

    @Test
    void getRelatedChallenges_NoRelatedChallenges_ReturnsEmptyList() {
        // Arrange
        when(challengeRepository.findByUuid(challengeDocument.getUuid()))
                .thenReturn(Mono.just(challengeDocument));

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.empty());

        // Act & Assert
        StepVerifier.create(challengeService.getRelatedChallenges(challengeDocument.getUuid().toString()))
                .assertNext(result -> {
                    assertNotNull(result);
                    assertEquals(0, result.getCount());
                    assertEquals(0, result.getResults().length);
                })
                .verifyComplete();
    }

    @Test
    void getRelatedChallenges_LanguageIdEmpty_ShouldNotFilterByLanguage() {
        // Arrange
        ChallengeDocument baseChallenge = new ChallengeDocument(
                UUID.randomUUID(), title, challengeDocument.getLevel(), LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(), List.of(), Topic.COMPONENTS, 0, 0, 0, challengeDocument.getTags());

        ChallengeDocument other = new ChallengeDocument(
                UUID.randomUUID(), title, challengeDocument.getLevel(), LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(languageDocument), List.of(), Topic.COMPONENTS, 0, 0, 0, challengeDocument.getTags());

        when(challengeRepository.findByUuid(baseChallenge.getUuid()))
                .thenReturn(Mono.just(baseChallenge));
        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(other));
        when(challengeConverter.convertDocumentToDto(any(), eq(ChallengeDto.class)))
                .thenReturn(new ChallengeDto());

        // Act & Assert
        StepVerifier.create(challengeService.getRelatedChallenges(baseChallenge.getUuid().toString()))
                .assertNext(result -> assertEquals(1, result.getCount()))
                .verifyComplete();
    }

    @Test
    void getRelatedChallenges_ChallengeWithNullLanguageId_ShouldBeExcluded() {
        // Arrange
        LanguageDocument langNull = new LanguageDocument(null, "lang", "img");
        ChallengeDocument other = new ChallengeDocument(
                UUID.randomUUID(), title, challengeDocument.getLevel(), LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(langNull), List.of(), Topic.COMPONENTS, 0, 0, 0, challengeDocument.getTags());

        when(challengeRepository.findByUuid(challengeDocument.getUuid()))
                .thenReturn(Mono.just(challengeDocument));
        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(other));

        // Act & Assert
        StepVerifier.create(challengeService.getRelatedChallenges(challengeDocument.getUuid().toString()))
                .assertNext(result -> assertEquals(0, result.getCount()))
                .verifyComplete();
    }

    @Test
    void getRelatedChallenges_LevelEmpty_ShouldNotFilterByLevel() {
        // Arrange
        ChallengeDocument base = new ChallengeDocument(
                UUID.randomUUID(), title, null, LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(languageDocument), List.of(), Topic.COMPONENTS, 0, 0, 0, challengeDocument.getTags());

        ChallengeDocument other = new ChallengeDocument(
                UUID.randomUUID(), title, "MEDIUM", LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(languageDocument), List.of(), Topic.COMPONENTS, 0, 0, 0, challengeDocument.getTags());

        when(challengeRepository.findByUuid(base.getUuid()))
                .thenReturn(Mono.just(base));
        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(other));
        when(challengeConverter.convertDocumentToDto(any(), eq(ChallengeDto.class)))
                .thenReturn(new ChallengeDto());

        // Act & Assert
        StepVerifier.create(challengeService.getRelatedChallenges(base.getUuid().toString()))
                .assertNext(result -> assertEquals(1, result.getCount()))
                .verifyComplete();
    }

    @Test
    void getRelatedChallenges_TagsExistButChallengeHasNoTags_ShouldBeExcluded() {
        // Arrange
        ChallengeDocument other = new ChallengeDocument(
                UUID.randomUUID(), title, challengeDocument.getLevel(), LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(languageDocument), List.of(), Topic.COMPONENTS, 0, 0, 0, null);

        when(challengeRepository.findByUuid(challengeDocument.getUuid()))
                .thenReturn(Mono.just(challengeDocument));
        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(other));

        // Act & Assert
        StepVerifier.create(challengeService.getRelatedChallenges(challengeDocument.getUuid().toString()))
                .assertNext(result -> assertEquals(0, result.getCount()))
                .verifyComplete();
    }




    @Test
    void getRelatedChallenges_LessThanThreeRelatedChallenges_ReturnsAll() {
        // Arrange: se crean 2 retos relacionados compatibles en idioma, nivel y tags
        ChallengeDocument related1 = new ChallengeDocument(
                UUID.randomUUID(), title, challengeDocument.getLevel(), LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(languageDocument), List.of(), Topic.COMPONENTS,
                10, 20, 30, challengeDocument.getTags()
        );

        ChallengeDocument related2 = new ChallengeDocument(
                UUID.randomUUID(), title, challengeDocument.getLevel(), LocalDateTime.now(), challengeDocument.getDetail(),
                Set.of(languageDocument), List.of(), Topic.COMPONENTS,
                15, 25, 35, challengeDocument.getTags()
        );

        when(challengeRepository.findByUuid(challengeDocument.getUuid()))
                .thenReturn(Mono.just(challengeDocument));

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.just(related1, related2));

        when(challengeConverter.convertDocumentToDto(any(), eq(ChallengeDto.class)))
                .thenAnswer(invocation -> {
                    ChallengeDocument doc = invocation.getArgument(0);
                    ChallengeDto dto = new ChallengeDto();
                    dto.setChallengeId(doc.getUuid());
                    return dto;
                });

        // Act & Assert
        StepVerifier.create(challengeService.getRelatedChallenges(challengeDocument.getUuid().toString()))
                .assertNext(result -> {
                    assertNotNull(result);
                    assertEquals(2, result.getCount());
                    assertEquals(2, result.getResults().length);
                })
                .verifyComplete();
    }

    @Test
    void getRelatedChallenges_InvalidUUID_ThrowsBadUUIDException() {
        String invalidId = "invalid-uuid";

        StepVerifier.create(challengeService.getRelatedChallenges(invalidId))
                .expectError(BadUUIDException.class)
                .verify();
    }


    @Test
    void getRelatedChallenges_MoreThanThreeRelatedChallenges_ReturnsThreeRandom() {
        // Arrange: 4 retos compatibles
        Integer[] indices = {0, 1, 2, 3};
        List<ChallengeDocument> relatedChallenges = Arrays.stream(indices)
                .map(i -> new ChallengeDocument(
                        UUID.randomUUID(), title, challengeDocument.getLevel(), LocalDateTime.now(), challengeDocument.getDetail(),
                        Set.of(languageDocument), List.of(), Topic.COMPONENTS,
                        10, 20, 30, challengeDocument.getTags()))
                .toList();

        when(challengeRepository.findByUuid(challengeDocument.getUuid()))
                .thenReturn(Mono.just(challengeDocument));

        when(challengeRepository.findAllByUuidNotNullExcludingTestingValues())
                .thenReturn(Flux.fromIterable(relatedChallenges));

        when(challengeConverter.convertDocumentToDto(any(), eq(ChallengeDto.class)))
                .thenAnswer(invocation -> {
                    ChallengeDocument doc = invocation.getArgument(0);
                    ChallengeDto dto = new ChallengeDto();
                    dto.setChallengeId(doc.getUuid());
                    return dto;
                });

        // Act & Assert
        StepVerifier.create(challengeService.getRelatedChallenges(challengeDocument.getUuid().toString()))
                .assertNext(result -> {
                    assertNotNull(result);
                    assertEquals(3, result.getCount());
                    assertEquals(3, result.getResults().length);
                })
                .verifyComplete();
    }


    @Test
    void removeChallengeFromBookmarks_WhenChallengeUuidNotValid_ReturnsError() {
        StepVerifier.create(challengeService.removeChallengeFromBookmarks("InvalidUuid", UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromBookmarks_WhenUserUuidNotValid_ReturnsError() {
        StepVerifier.create(challengeService.removeChallengeFromBookmarks(UUID.randomUUID().toString(), "InvalidUuid"))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromBookmarks_WhenChallengeUuidIsNull_ReturnsError() {
        StepVerifier.create(challengeService.removeChallengeFromBookmarks(null, UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromBookmarks_WhenUserUuidIsNull_ReturnsError() {
        StepVerifier.create(challengeService.removeChallengeFromBookmarks(UUID.randomUUID().toString(), null))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromBookmarks_WhenChallengeNotFound_ReturnsError() {
        String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";
        UUID challengeUuid = UUID.randomUUID();

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.empty());

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof ChallengeNotFoundException &&
                                error.getMessage().equals(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid.toString())))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
    }

    @Test
    void removeChallengeFromBookmarks_WhenUserNotFound_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new UserNotFoundException(message)));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromBookmarks_WhenUserServiceReturnsCustomBadRequestException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new BadRequestException(message)));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromBookmarks_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new InternalServerErrorException(message)));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromBookmarks_WhenUserServiceReturnsAnyException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new Exception(message)));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof Exception &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromBookmarks_WhenRemoved_DecreasesTimesBookmarkedAndReturnsBookmarkDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesBookmarked = 20;

        challenge.setTimesBookmark(initialTimesBookmarked);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(bookmarkDto -> {
                    return bookmarkDto.getTimesBookmarked() == initialTimesBookmarked - 1 &&
                            !bookmarkDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesBookmarked - 1, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void removeChallengeFromBookmarks_WhenRemovedAndInitialTimesBookmarkedIsNull_SetsTimesBookmarkedToZeroAndReturnsBookmarkDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesFavorite(null);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesBookmarked() == 0 &&
                            !favoriteDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(0, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void removeChallengeFromBookmarks_WhenRemovedAndInitialTimesBookmarkedIsZero_SetsTimesBookmarkedToZeroAndReturnsBookmarkDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesFavorite(0);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesBookmarked() == 0 &&
                            !favoriteDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(0, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void removeChallengeFromBookmarks_WhenNotRemoved_NotChangeTimesBookmarkedAndReturnsBookmarkDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesBookmarked = 20;

        challenge.setTimesBookmark(initialTimesBookmarked);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesBookmarked() == initialTimesBookmarked &&
                            !favoriteDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesBookmarked, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(0)).save(any());
    }

    @ParameterizedTest
    @MethodSource
    void removeChallengeFromBookmarks_WhenNotRemovedAndTimesBookmarkIsNullOrZero_SetTimesBookmarkedToZeroAndReturnsBookmarkDTO(Integer timesBookmarked) {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesBookmark(timesBookmarked);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(challengeService.removeChallengeFromBookmarks(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesBookmarked() == 0 &&
                            !favoriteDto.isBookmarked();
                })
                .verifyComplete();

        Assertions.assertEquals(0, challenge.getTimesBookmark());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    public static Stream<Integer> removeChallengeFromBookmarks_WhenNotRemovedAndTimesBookmarkIsNullOrZero_SetTimesBookmarkedToZeroAndReturnsBookmarkDTO() {
        return Stream.of(null, 0);
    }

    @Test
    void updateChallenge_success_test(){

        String challengeId = challengeDocument.getUuid().toString();
        AtomicReference<SolutionDocument> savedSolutionDocument = new AtomicReference<>();

        when(ILanguageService.findFirstByLanguageName(anyString()))
                .thenReturn(Mono.just(languageDocument));
        when(challengeRepository.findByUuid(UUID.fromString(challengeId))).thenReturn(Mono.just(challengeDocument));
        when(tagService.getValidatedTags(formData.getTags())).thenReturn(Mono.just(true));
        when(solutionRepository.save(any(SolutionDocument.class))).thenAnswer(resp -> {
            SolutionDocument solutionDocument1 = resp.getArgument(0);
            savedSolutionDocument.set(solutionDocument1);
            return Mono.just(solutionDocument1);
        });
        when(challengeRepository.save(any(ChallengeDocument.class)))
                .thenAnswer(resp -> {
                    ChallengeDocument updatedChallengeDocument = resp.getArgument(0);
                    return Mono.just(updatedChallengeDocument);
                });
        when(challengeConverter.convertDocumentToDto(any(ChallengeDocument.class), eq(ChallengeDto.class)))
                .thenAnswer(invocation -> buildChallengeDtoFromDocument(invocation.getArgument(0)));

        StepVerifier.create(challengeService.updateChallenge(challengeId, formData))
                .consumeNextWith(responseDto ->{
                    boolean languageMatch = responseDto.getLanguages().stream()
                            .anyMatch(lang -> formData.getLanguage().equals(lang.getLanguageName()));
                    SolutionDocument solutionDocument1 = savedSolutionDocument.get();

                    Assertions.assertAll(
                            () -> Assertions.assertEquals(challengeId, responseDto.getChallengeId().toString()),
                            () -> Assertions.assertEquals(formData.getChallengeTitle(), responseDto.getTitle()),
                            () -> Assertions.assertEquals(String.valueOf(formData.getLevel()), responseDto.getLevel()),
                            () -> Assertions.assertEquals("2023-06-05", responseDto.getCreationDate()),
                            () -> Assertions.assertEquals(formData.getDescription(), responseDto.getDetail().getDescription()),
                            () -> Assertions.assertEquals(challengeDocument.getTimesFavorite(), responseDto.getTimesFavorite()),
                            () -> Assertions.assertEquals(1, responseDto.getLanguages().size()),
                            () -> Assertions.assertTrue(languageMatch, "language does not match."),
                            () -> Assertions.assertEquals(formData.getSolution(), solutionDocument1.getSolutionText()),
                            () -> Assertions.assertEquals(formData.getTopic(), responseDto.getTopic()),
                            () -> Assertions.assertEquals(challengeDocument.getTimesBookmark(), responseDto.getTimesBookmark()),
                            () -> Assertions.assertEquals(formData.getTags(), responseDto.getTags())
                    );
                })
                .verifyComplete();
        verify(ILanguageService, times(1)).findFirstByLanguageName(languageName);
        verify(challengeRepository, times(1)).findByUuid(UUID.fromString(challengeId));
        verify(solutionRepository, times(1)).save(any(SolutionDocument.class));
        verify(challengeRepository, times(1)).save(any(ChallengeDocument.class));
        verify(challengeConverter, times(1)).convertDocumentToDto(any(ChallengeDocument.class), eq(ChallengeDto.class));
    }

    @Test
    void updateChallengeWhenChallengeDoesNotExist_returnsError_test(){
        String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";
        String challengeId = challengeDocument.getUuid().toString();
        when(ILanguageService.findFirstByLanguageName(anyString()))
                .thenReturn(Mono.just(languageDocument));
        when(challengeRepository.findByUuid(UUID.fromString(challengeId))).thenReturn(Mono.empty());

        StepVerifier.create(challengeService.updateChallenge(challengeId, formData))
                .expectErrorMatches(error ->
                        error instanceof ChallengeNotFoundException &&
                                error.getMessage().equals(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeId)))
                .verify();

        verify(ILanguageService, times(1)).findFirstByLanguageName(languageName);
        verify(challengeRepository, times(1)).findByUuid(UUID.fromString(challengeId));
        verifyNoInteractions(solutionRepository, challengeConverter, tagService);
        verifyNoMoreInteractions(challengeRepository);
    }

    @Test
    void updateChallengeWhenLanguageDoesNotExist_returnsError_test(){

        String LANGUAGE_NOT_FOUND_ERROR = "Language %s is not valid";
        String challengeId = challengeDocument.getUuid().toString();
        when(ILanguageService.findFirstByLanguageName(anyString()))
                .thenReturn(Mono.empty());

        StepVerifier.create(challengeService.updateChallenge(challengeId, formData))
                .expectErrorMatches(error ->
                        error instanceof LanguageNotFoundException &&
                                error.getMessage().equals(String.format(LANGUAGE_NOT_FOUND_ERROR, formData.getLanguage())))
                .verify();

        verify(ILanguageService, times(1)).findFirstByLanguageName(languageName);
        verifyNoInteractions(challengeRepository, solutionRepository, challengeConverter, tagService);
    }

    @Test
    void updateChallengeWhenChallengeIdNotValid_returnError_test(){
        String challengeId = "InvalidId";
        when(ILanguageService.findFirstByLanguageName(anyString())).thenReturn(Mono.just(languageDocument));
        StepVerifier.create(challengeService.updateChallenge(challengeId, formData))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
        verify(ILanguageService, times(1)).findFirstByLanguageName(languageName);
        verifyNoInteractions(challengeRepository, solutionRepository, challengeConverter, tagService);
    }

    @Test
    void updateChallengeWhenChallengeUuidIsNull_ReturnsError() {

        when(ILanguageService.findFirstByLanguageName(anyString())).thenReturn(Mono.just(languageDocument));

        StepVerifier.create(challengeService.updateChallenge(null, formData))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
        verify(ILanguageService, times(1)).findFirstByLanguageName(languageName);
        verifyNoInteractions(challengeRepository, solutionRepository, challengeConverter, tagService);
    }

    private ChallengeDto buildChallengeDtoFromDocument(ChallengeDocument doc) {
        Set<LanguageDto> languageDtos = doc.getLanguages().stream()
                .map(lang -> new LanguageDto(lang.getIdLanguage(), lang.getLanguageName(), lang.getLanguageImage()))
                .collect(Collectors.toSet());

        return ChallengeDto.builder()
                .challengeId(doc.getUuid())
                .title(doc.getTitle())
                .level(doc.getLevel())
                .creationDate(doc.getCreationDate().format(DateTimeFormatter.ofPattern("yyyy-MM-dd")))
                .detail(doc.getDetail())
                .languages(languageDtos)
                .solutions(doc.getSolutions())
                .topic(doc.getTopic())
                .timesFavorite(doc.getTimesFavorite())
                .tags(doc.getTags())
                .timesBookmark(doc.getTimesBookmark())
                .build();
    }
}

// Node: addChallengeToSolved_WhenChallengeTimesSolvedIsNull_IncreasesTimesSolvedAndReturnsSolvedDTO
// Node: addChallengeToSolved_WhenChallengeTimesSolvedIsZero_IncreasesTimesSolvedAndReturnsSolvedDTO
// Node: addChallengeToSolved_AlwaysIncreasesTimesSolvedAndReturnsSolvedDTO
package com.itachallenge.challenge.helper;

import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.dto.LanguageDto;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertEquals;


class LanguageDocumentToDtoConverterTest {

    private DocumentToDtoConverter<LanguageDocument, LanguageDto> mapper;

    private LanguageDocument languageDocument1;

    private LanguageDocument languageDocument2;

    private LanguageDto languageDto1;

    private LanguageDto languageDto2;


    @BeforeEach
    public void setUp() {
        mapper  = new DocumentToDtoConverter();

        UUID[] languageID = new UUID[]{UUID.randomUUID(), UUID.randomUUID()};
        String[] languageNames = new String[]{"Java", "Python"};

        languageDocument1 = new LanguageDocument(languageID[0], languageNames[0], "https://image-default.com/javascript.png");
        languageDocument2 = new LanguageDocument(languageID[1], languageNames[1], "https://image-default.com/python.png");

        languageDto1 = new LanguageDto(languageID[0], languageNames[0], "https://image-default.com/javascript.png");
        languageDto2 = new LanguageDto(languageID[1], languageNames[1], "https://image-default.com/python.png");

    }

    @Test
    @DisplayName("Conversion from document to dto when the field types and names perfectly match the source")
    void testConvertLanguageDocumentToLanguageDto() {
        // when
        LanguageDocument languageDocumentMocked = languageDocument1;
        LanguageDto resultDto = mapper.convertDocumentToDto(languageDocumentMocked, LanguageDto.class);
        LanguageDto expectedDto = languageDto1;

        // then
        assertEquals(expectedDto.getLanguageId(), resultDto.getLanguageId());
        assertEquals(expectedDto.getLanguageName(), resultDto.getLanguageName());
    }

    @Test
    @DisplayName("Test convertFluxEntityToFluxDto method")
    void testConvertFluxEntityToFluxDto() {
        Flux<LanguageDocument> documentFlux = Flux.just(languageDocument1, languageDocument2);
        Flux<LanguageDto> resultFlux = mapper.convertDocumentFluxToDtoFlux(documentFlux, LanguageDto.class);
        Flux<LanguageDto> expectedFlux = Flux.just(languageDto1, languageDto2);

        StepVerifier.create(resultFlux)
                .assertNext(languageDto -> {
                    Assertions.assertEquals(languageDto1.getLanguageId(), languageDto.getLanguageId());
                    Assertions.assertEquals(languageDto1.getLanguageName(), languageDto.getLanguageName());
                })
                .assertNext(languageDto -> {
                    Assertions.assertEquals(languageDto2.getLanguageId(), languageDto.getLanguageId());
                    Assertions.assertEquals(languageDto2.getLanguageName(), languageDto.getLanguageName());
                })
                .expectComplete()
                .verify();

        assertThat(expectedFlux.blockFirst()).usingRecursiveComparison().isEqualTo(resultFlux.blockFirst());
        assertThat(expectedFlux.blockLast()).usingRecursiveComparison().isEqualTo(resultFlux.blockLast());
    }

}



// Node: testConvertLanguageDocumentToLanguageDto
// Node: SneakyThrows
// Node: writerWithDefaultPrettyPrinter
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.challenge.helper.ResourceHelper;
import lombok.SneakyThrows;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertEquals;

@ExtendWith(SpringExtension.class)
@SpringBootTest
class LanguageDtoTest {

    @Autowired
    private ObjectMapper mapper;

    private final String languageJsonPath = "json/Language.json";

    private LanguageDto languageDto;

    @BeforeEach
    void setUp(){
        UUID uuid = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        languageDto = LanguageDtoTest.buildLanguageDto(uuid, "Javascript",
                "https://res.cloudinary.com/itachallenge/image/upload/v1739361249/language_icon_Javascript_asgn04.svg ");
    }

    @Test
    @DisplayName("Serialization LanguageDto test")
    @SneakyThrows({JsonProcessingException.class})
    void rightSerializationTest(){
        LanguageDto dtoSerializable = languageDto;
        String jsonResult = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(dtoSerializable);
        String jsonExpected = new ResourceHelper(languageJsonPath).readResourceAsString().orElse(null);

        ObjectMapper objectMapper = new ObjectMapper();
        Map<String, Object> expectedMap = objectMapper.readValue(jsonExpected, Map.class);
        Map<String, Object> resultMap = objectMapper.readValue(jsonResult, Map.class);

        String expectedImage = ((String) expectedMap.get("language_image")).trim();
        String resultImage = ((String) resultMap.get("language_image")).trim();

        expectedMap.put("language_image", expectedImage);
        resultMap.put("language_image", resultImage);

        assertEquals(objectMapper.writeValueAsString(expectedMap), objectMapper.writeValueAsString(resultMap));

    }

    @Test
    @DisplayName("Deserialization LanguageDto test")
    @SneakyThrows(IOException.class)
    void rightDeserializationTest(){
        String jsonDeserializable = new ResourceHelper(languageJsonPath).readResourceAsString().orElse(null);
        LanguageDto dtoResult = mapper.readValue(jsonDeserializable, LanguageDto.class);
        LanguageDto dtoExpected = languageDto;

        assertThat(dtoResult.getLanguageImage().trim()).isEqualTo(dtoExpected.getLanguageImage().trim());
    }

    @Test
    @DisplayName("LanguageDto image URL should not be null or empty")
    void languageImageShouldNotBeNullOrEmpty() {
        assertThat(languageDto.getLanguageImage()).isNotNull().isNotEmpty();
    }

    @Test
    @DisplayName("LanguageDto image URL should be a valid URL")
    void languageImageShouldBeAValidURL() {
        String imageUrl = languageDto.getLanguageImage().trim();
        System.out.println("Testing URL: " + imageUrl);
        String urlRegex = "^(https?|ftp)://[^\\s/$.?#].[^\\s]*$";
        assertThat(imageUrl).matches(Pattern.compile(urlRegex));
    }

    static LanguageDto buildLanguageDto(UUID languageId, String languageName, String languageImage){
        return new LanguageDto(languageId,languageName, languageImage);
    }

    private static String normalizeLineEndings(String json) {
        try {
            // Parse JSON string
            ObjectMapper mapper = new ObjectMapper();
            JsonNode jsonNode = mapper.readTree(json);

            // Convert back to JSON string with consistent formatting
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(jsonNode);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error normalizing line endings", e);
        }
    }
}


// Node: normalizeLineEndings
package com.itachallenge.challenge.dto;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(SpringExtension.class)
@SpringBootTest
class BookmarkDtoTest {

    @Test
    void testAllArgsConstructorAndGetters() {
        BookmarkDto dto = new BookmarkDto(true, 42);

        assertTrue(dto.isBookmarked());
        assertEquals(42, dto.getTimesBookmarked());
    }

    @Test
    void testNoArgsConstructorAndSetters() {
        BookmarkDto dto = new BookmarkDto();
        dto.setBookmarked(false);
        dto.setTimesBookmarked(10);

        assertFalse(dto.isBookmarked());
        assertEquals(10, dto.getTimesBookmarked());
    }

    @Test
    void testEqualsAndHashCode() {
        BookmarkDto dto1 = new BookmarkDto(true, 5);
        BookmarkDto dto2 = new BookmarkDto(true, 5);

        assertEquals(dto1, dto2);
        assertEquals(dto1.hashCode(), dto2.hashCode());
    }

    @Test
    void testNoArgsConstructorDefaultValues() {
        BookmarkDto dto = new BookmarkDto();

        assertFalse(dto.isBookmarked());
        assertEquals(0, dto.getTimesBookmarked());
    }

    @Test
    void testToString() {
        BookmarkDto dto = new BookmarkDto(true, 100);
        String result = dto.toString();

        assertTrue(result.contains("BookmarkDto"));
        assertTrue(result.contains("isBookmarked=true"));
        assertTrue(result.contains("timesBookmarked=100"));
    }
}


package com.itachallenge.challenge.dto;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class SolvedDtoTest {

    @Test
    void testNoArgsConstructorAndSetters() {
        SolvedDto dto = new SolvedDto();
        dto.setSolved(true);
        dto.setTimesSolved(5);

        assertTrue(dto.isSolved());
        assertEquals(5, dto.getTimesSolved());
    }

    @Test
    void testAllArgsConstructor() {
        SolvedDto dto = new SolvedDto(false, 3);

        assertFalse(dto.isSolved());
        assertEquals(3, dto.getTimesSolved());
    }

    @Test
    void testEqualsAndHashCode() {
        SolvedDto dto1 = new SolvedDto(true, 2);
        SolvedDto dto2 = new SolvedDto(true, 2);
        SolvedDto dto3 = new SolvedDto(false, 5);

        assertEquals(dto1, dto2);
        assertEquals(dto1.hashCode(), dto2.hashCode());
        assertNotEquals(dto1, dto3);
    }

    @Test
    void testToString() {
        SolvedDto dto = new SolvedDto(true, 7);
        String result = dto.toString();

        assertTrue(result.contains("isSolved=true"));
        assertTrue(result.contains("timesSolved=7"));
    }
}


package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.util.DefaultIndenter;
import com.fasterxml.jackson.core.util.DefaultPrettyPrinter;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.challenge.document.DetailDocument;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.helper.ResourceHelper;
import lombok.SneakyThrows;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import java.io.IOException;
import java.util.*;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.Assert.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

@ExtendWith(SpringExtension.class)
@SpringBootTest
class ChallengeDtoTest {

    @Autowired
    private ObjectMapper mapper;

    private final String challengeJsonPath = "json/ChallengeSerialized.json";

    private ChallengeDto challengeDtoToSerialize;

    private ChallengeDto challengeDtoFromDeserialization;

    @BeforeEach
    void setUp(){
        UUID uuid = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        UUID uuid2 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");
        LanguageDto firstLanguage = LanguageDtoTest.buildLanguageDto
                (uuid, "Javascript", "https://image-default.com/javascript.png");
        LanguageDto secondLanguage = LanguageDtoTest.buildLanguageDto
                (uuid2, "Python", "https://image-default.com/python.png");
        String title = "Sociis Industries";
        String description = "Test description";
        DetailDocument detail = new DetailDocument(description);


        challengeDtoToSerialize = buildChallengeWithBasicInfoDto(UUID.fromString("dcacb291-b4aa-4029-8e9b-284c8ca80296")
                , title, "EASY", "2023-06-05T12:30:00+02:00", detail,
                105, 23.58f,buildLanguagesSorted(firstLanguage, secondLanguage));

        challengeDtoFromDeserialization = buildChallengeWithBasicInfoDto(UUID.fromString("dcacb291-b4aa-4029-8e9b-284c8ca80296")
                , title, "EASY", "2023-06-05T12:30:00+02:00", detail,
                105, 23.58f,buildLanguages(firstLanguage, secondLanguage));
    }

    @Test
    @DisplayName("Serialization ChallengeDto test")
    @SneakyThrows({JsonProcessingException.class})
    void rightSerializationTest(){
        String jsonResult = mapper
                .writer(new DefaultPrettyPrinter().withArrayIndenter(DefaultIndenter.SYSTEM_LINEFEED_INSTANCE))
                .writeValueAsString(challengeDtoToSerialize);
        String jsonExpected = new ResourceHelper(challengeJsonPath).readResourceAsString().orElse(null);
        assertEquals(normalizeLineEndings(jsonExpected), normalizeLineEndings(jsonResult));
    }

    @Test
    @DisplayName("Deserialization ChallengeDto test")
    @SneakyThrows(IOException.class)
    void rightDeserializationTest(){
        String challengeJsonSource = new ResourceHelper(challengeJsonPath).readResourceAsString().orElse(null);
        ChallengeDto dtoResult = mapper.readValue(challengeJsonSource, ChallengeDto.class);
        assertThat(dtoResult).usingRecursiveComparison().isEqualTo(challengeDtoFromDeserialization);
    }

    static Set<LanguageDto> buildLanguagesSorted(LanguageDto firstLanguage, LanguageDto secondLanguage){
        LinkedHashSet<LanguageDto> languages = new LinkedHashSet<>();
        languages.add(firstLanguage);
        languages.add(secondLanguage);
        return languages;
    }

    static Set<LanguageDto> buildLanguages(LanguageDto firstLanguage, LanguageDto secondLanguage){
        return Set.copyOf(List.of(firstLanguage,secondLanguage));
    }

    static ChallengeDto buildChallengeWithBasicInfoDto
            (UUID id, String title, String level, String creationDate, DetailDocument detail,
             Integer popularity, Float percentage, Set<LanguageDto> languages){
        return ChallengeDto.builder()
                .challengeId(id)
                .title(title)
                .level(level)
                .creationDate(creationDate)
                .detail(detail)
                .popularity(popularity)
                .percentage(percentage)
                .languages(languages)
                .build();
    }

    private static String normalizeLineEndings(String json) {
        try {
            // Parse JSON string
            ObjectMapper mapper = new ObjectMapper();
            JsonNode jsonNode = mapper.readTree(json);

            // Convert back to JSON string with consistent formatting
            return mapper.writerWithDefaultPrettyPrinter().writeValueAsString(jsonNode);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error normalizing line endings", e);
        }
    }

    @Test
    @DisplayName("Test serialization with different Topic values")
    @SneakyThrows(JsonProcessingException.class)
    void testDifferentTopicValuesSerialization() {
        for (Topic topic : Topic.values()) {
            ChallengeDto challengeDto = buildChallengeWithBasicInfoDto(
                    UUID.randomUUID(), "Challenge with " + topic, "MEDIUM", "2023-06-05T12:30:00+02:00",
                    new DetailDocument("Description"), 50, 15.5f, Set.of());

            challengeDto.setTopic(topic);

            String jsonResult = mapper.writeValueAsString(challengeDto);

            assertTrue(jsonResult.contains("\"topic\":\"" + topic.name() + "\""));
        }
    }

        @Test
        @DisplayName("Test Topic - Null Topic value")
        @SneakyThrows(JsonProcessingException.class)
        void nullTopicSerializationTest() {
            ChallengeDto challengeDto = buildChallengeWithBasicInfoDto(
                    UUID.randomUUID(), "Challenge with no topic", "HARD", "2023-06-05T12:30:00+02:00",
                    new DetailDocument("Description"), 150, 40.5f, Set.of());

            challengeDto.setTopic(null);

            String jsonResult = mapper.writeValueAsString(challengeDto);

            assertFalse(jsonResult.contains("\"topic\""));
        }

    @Test
    @DisplayName("Test deserialization with missing Topic")
    @SneakyThrows(IOException.class)
    void testDeserializationWithMissingTopic() {
        String jsonSource = "{\"id_challenge\":\"09fabe32-7362-4bfb-ac05-b7bf854c6e0f\",\"challenge_title\":\"No Topic Challenge\",\"level\":\"EASY\",\"creation_date\":\"2023-06-05T12:30:00+02:00\",\"detail\":{\"description\":\"Test without topic\"},\"popularity\":75,\"percentage\":50.5,\"languages\":[]}";

        ChallengeDto dtoResult = mapper.readValue(jsonSource, ChallengeDto.class);

        assertNull(dtoResult.getTopic());
    }
}








// Node: buildChallengeWithBasicInfoDto
// Node: testDifferentTopicValuesSerialization
// Node: nullTopicSerializationTest
package com.itachallenge.challenge.dto;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;


@ExtendWith(SpringExtension.class)
@SpringBootTest
class MessageDtoTest {
    @Test
    void testMessage() {
        // Arrange
        String message = "Expected message";

        // Act
        MessageDto errorResponseMessage = new MessageDto(message);

        // Assert
        Assertions.assertEquals(message, errorResponseMessage.getMessage());
    }

    @Test
    void testNotExpectedMessage() {
        // Arrange
        String message = "Expected message";
        String notExpectedMessage = "Not expected message.";

        // Act
        MessageDto errorResponseMessage = new MessageDto(message);

        // Assert
        Assertions.assertNotEquals(notExpectedMessage, errorResponseMessage.getMessage());
    }

}


// Node: testMessage
// Node: testNotExpectedMessage
package com.itachallenge.challenge.dto.submission;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class SubmissionDtoTest {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private static final String USER_ID_TEXT = "c4feec44-ac54-4e99-852b-9ba56c479ba5";
    private static final String CHALLENGE_ID_TEXT = "c4feec44-ac54-4e99-852b-9ba56c476c47";
    private static final String LANGUAGE_ID_TEXT = "c4feec44-ac54-4e99-852b-9ba56c47eec4";
    private static final String STATUS = "IN_PROGRESS";
    private static final String SUBMISSION_TEXT = "Hello World!!";

    @Test
    void builder_shouldCreateDtoCorrectly() {
        SubmissionDto dto = SubmissionDto.builder()
                .userId(USER_ID_TEXT)
                .challengeId(CHALLENGE_ID_TEXT)
                .languageId(LANGUAGE_ID_TEXT)
                .status(STATUS)
                .submissionText(SUBMISSION_TEXT)
                .build();

        assertEquals(USER_ID_TEXT, dto.getUserId());
        assertEquals(CHALLENGE_ID_TEXT, dto.getChallengeId());
        assertEquals(LANGUAGE_ID_TEXT, dto.getLanguageId());
        assertEquals(STATUS, dto.getStatus());
        assertEquals(SUBMISSION_TEXT, dto.getSubmissionText());
    }

    @Test
    void jsonSerialization_shouldUseExpectedJsonPropertyNames() throws JsonProcessingException {
        SubmissionDto dto = SubmissionDto.builder()
                .userId(USER_ID_TEXT)
                .challengeId(CHALLENGE_ID_TEXT)
                .languageId(LANGUAGE_ID_TEXT)
                .status(STATUS)
                .submissionText(SUBMISSION_TEXT)
                .build();

        String json = OBJECT_MAPPER.writeValueAsString(dto);
        JsonNode node = OBJECT_MAPPER.readTree(json);

        assertEquals(USER_ID_TEXT, node.get("uuid_user").asText());
        assertEquals(CHALLENGE_ID_TEXT, node.get("uuid_challenge").asText());
        assertEquals(LANGUAGE_ID_TEXT, node.get("uuid_language").asText());
        assertEquals(STATUS, node.get("status").asText());
        assertEquals(SUBMISSION_TEXT, node.get("submission_text").asText());
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/submission/SubmissionDtoTest.java:SubmissionDtoTest.<init>
// Node: builder_shouldCreateDtoCorrectly
// Node: jsonSerialization_shouldUseExpectedJsonPropertyNames
package com.itachallenge.auth.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.Map;

@Service
public class AuthService implements IAuthService {

    private static final Logger log = LoggerFactory.getLogger(AuthService.class);
    private final WebClient.Builder webClientBuilder;

    private static final String KEY_IS_VALID = "isValid";
    private static final String KEY_USERNAME = "username";
    private static final String KEY_TOKEN = "token";
    private static final String CLIENT_ID_KEY = "client_id";
    private static final String CLIENT_SECRET_KEY = "client_secret";
    private static final String CODE_KEY = "code";
    private static final String ACCESS_TOKEN_KEY = "access_token";
    private static final String GITHUB_LOGIN_KEY = "login";

    private final String githubUserInfoUri;

    private final String githubTokenUri;

    private final String clientId;

    private final String clientSecret;

    public AuthService(WebClient.Builder webClientBuilder,
                       @Value("${spring.security.oauth2.client.provider.github.token-uri}") String githubTokenUri,
                       @Value("${spring.security.oauth2.client.provider.github.user-info-uri}") String githubUserInfoUri,
                       @Value("${spring.security.oauth2.client.registration.github.client-id}") String clientId,
                       @Value("${spring.security.oauth2.client.registration.github.client-secret}") String clientSecret
                       ) {
        this.webClientBuilder = webClientBuilder;
        this.githubTokenUri = githubTokenUri;
        this.githubUserInfoUri = githubUserInfoUri;
        this.clientId = clientId;
        this.clientSecret = clientSecret;
    }

    public Mono<String> exchangeCodeForToken(String code) {
        WebClient webClient = webClientBuilder.build();

        return webClient
                .post()
                .uri(githubTokenUri)
                .header("Accept", "application/json")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(createRequestBody(clientId, clientSecret, code))
                .retrieve()
                .bodyToMono(String.class)
                .flatMap(this::processTokenResponse)
                .onErrorResume(this::handleTokenError);
    }

    private Map<String, String> createRequestBody(String clientId, String clientSecret, String code) {
        Map<String, String> requestBody = new HashMap<>();
        requestBody.put(CLIENT_ID_KEY, clientId);
        requestBody.put(CLIENT_SECRET_KEY, clientSecret);
        requestBody.put(CODE_KEY, code);
        return requestBody;
    }

    private Mono<String> processTokenResponse(String response) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode jsonNode = objectMapper.readTree(response);

            if (jsonNode.has(ACCESS_TOKEN_KEY)) {
                String accessToken = jsonNode.get(ACCESS_TOKEN_KEY).asText();
                log.info("Access token obtained successfully");
                return Mono.just(accessToken);
            } else {
                log.error("GitHub OAuth error: {}", response);
                return Mono.error(new IllegalStateException("Failed to obtain access token"));
            }
        } catch (JsonProcessingException e) {
            log.error("Error processing GitHub OAuth response", e);
            return Mono.error(e);
        }
    }

    private Mono<String> handleTokenError(Throwable ex) {
        log.error("Error exchanging code for token: {}", ex.getMessage());
        return Mono.error(ex);
    }

    @Override
    public Mono<Map<String, Object>> validateTokenWithGithub(String token) {
        WebClient webClient = webClientBuilder.build();

        return webClient
                .get()
                .uri(githubUserInfoUri)
                .header("Authorization", "token " + token)
                .retrieve()
                .bodyToMono(String.class)
                .flatMap(response -> processGithubResponse(response, token))

                .onErrorResume(WebClientResponseException.class, this::handleGithubApiError)
                .onErrorResume(this::handleUnexpectedError);
    }

    private Mono<Map<String, Object>> processGithubResponse(String response, String token) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            JsonNode jsonNode = objectMapper.readTree(response);

            if (jsonNode.has(GITHUB_LOGIN_KEY)) {
                String githubUsername = jsonNode.get(GITHUB_LOGIN_KEY).asText();
                log.info("GitHub username extracted: {}", githubUsername);

                return Mono.just(createSuccessResult(githubUsername, token));
            } else {
                log.error("GitHub response does not contain a username: {}", response);
                return Mono.just(createErrorResult());
            }
        } catch (JsonProcessingException e) {
            log.error("Error processing GitHub response", e);
            return Mono.error(e);
        }
    }

    private Mono<Map<String, Object>> handleGithubApiError(WebClientResponseException ex) {
        log.error("GitHub API error: {}", ex.getStatusCode());
        return Mono.just(createErrorResult());
    }

    private Mono<Map<String, Object>> handleUnexpectedError(Throwable ex) {
        log.error("Unexpected error: {}", ex.getMessage());
        return Mono.just(createErrorResult());
    }

    private Map<String, Object> createSuccessResult(String username, String token) {
        Map<String, Object> result = new HashMap<>();
        result.put(KEY_IS_VALID, true);
        result.put(KEY_USERNAME, username);
        result.put(KEY_TOKEN, token);
        return result;
    }

    private Map<String, Object> createErrorResult() {
        Map<String, Object> errorResult = new HashMap<>();
        errorResult.put(KEY_IS_VALID, false);
        errorResult.put(KEY_USERNAME, null);
        return errorResult;
    }

}


// Node: processTokenResponse
// Node: has
