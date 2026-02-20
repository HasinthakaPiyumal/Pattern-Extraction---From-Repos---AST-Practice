// Cluster 18

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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/test/java/com/itachallenge/document/controller/DocumentControllerTest.java:DocumentControllerTest.<init>
// Node: TestPropertySource
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/test/java/com/itachallenge/document/service/DocumentServiceTest.java:DocumentServiceTest.<init>
// Node: ExtendWith
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-document/src/test/java/com/itachallenge/document/config/OpenApiConfigTest.java:OpenApiConfigTest.<init>
package com.itachallenge.errorcore.integrationTest;

import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.errorcore.builder.ErrorResponseBuilder;
import com.itachallenge.errorcore.config.ErrorHandlingConfig;
import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.exception.ApiCustomErrorInfo;
import com.itachallenge.errorcore.exception.BaseApiException;
import com.itachallenge.errorcore.exceptionhandler.GlobalExceptionHandler;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.validation.Path;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.MessageSource;
import org.springframework.core.MethodParameter;
import org.springframework.core.codec.DecodingException;
import org.springframework.http.HttpInputMessage;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;

import java.lang.reflect.Method;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = { ErrorHandlingConfig.class })
class ErrorCoreIntegrationTest {

    @Autowired
    private MessageSource messageSource;

    @Autowired
    private ErrorResponseBuilder errorResponseBuilder;

    @Autowired
    private GlobalExceptionHandler handler;

    private HttpServletRequest request;

    @BeforeEach
    void setup() {
        request = mock(HttpServletRequest.class);
        when(request.getRequestURI()).thenReturn("/api/test");
    }

    // --- Dummy Controller & DTO for MethodParameter simulation ---
    static class EmptyController {
        public void handle(EmptyDto dto) {
            /* the method is just for testing -  hence its emptyness*/
        }
    }

    static class EmptyDto {
        @SuppressWarnings("unused")
        private String name;
    }

    @Test
    void handleAny_shouldReturnInternalServerError() {
        Exception ex = new Exception("Unexpected error");
        ResponseEntity<APIErrorResponse> response = handler.handleAny(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getStatus()).isEqualTo(500);
    }

    @Test
    void handleApiCustomException_shouldReturnCustomStatusAndText() {

        BaseApiException ex = mock(BaseApiException.class);
        when(ex.getMessage()).thenReturn("status.exception.401");
        when(ex.getInfo()).thenReturn(ApiCustomErrorInfo.of(HttpStatus.FORBIDDEN,"status.exception.401",new Object[]{}));
        ResponseEntity<APIErrorResponse> response = handler.handleApiCustomException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.FORBIDDEN);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("You are not authorized to perform this action.");
    }

    @Test
    void handleIllegalArgument_shouldReturnBadRequest() {
        IllegalArgumentException ex = new IllegalArgumentException("Invalid input");

        ResponseEntity<APIErrorResponse> response = handler.handleIllegalArgument(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Illegal argument in request.");
    }

    @Test
    void handleValidationExceptions_shouldReturnBadRequest_withSingleViolation() {
        // Given
        Path mockPath = mock(Path.class);
        when(mockPath.toString()).thenReturn("testField");

        ConstraintViolation<EmptyDto> violation = mock(ConstraintViolation.class);
        when(violation.getMessage()).thenReturn("must not be null");
        when(violation.getPropertyPath()).thenReturn(mockPath);
        when(violation.getRootBeanClass()).thenReturn(EmptyDto.class);

        Set<ConstraintViolation<?>> violations = Set.of(violation);
        ConstraintViolationException ex = new ConstraintViolationException("Validation failed", violations);

        // When
        ResponseEntity<APIErrorResponse> response = handler.handleValidationExceptions(ex, request);

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).contains("One or more request parameters failed validation.");
        assertThat(response.getBody().getErrors().getFirst().getObjectName()).isEqualTo("EmptyDto");
        assertThat(response.getBody().getErrors().getFirst().getMessage()).isEqualTo("Validation failed for parameter 'testField': must not be null");
    }

    @Test
    void handleTypeMismatch_shouldReturnBadRequest() throws NoSuchMethodException {
        // Given: we need a MethodParameter for a method argument of type Integer
        Method method = EmptyController.class.getDeclaredMethod("handle", EmptyDto.class);
        MethodParameter parameter = new MethodParameter(method, 0);

        MethodArgumentTypeMismatchException ex =
                new MethodArgumentTypeMismatchException("abc", EmptyDto.class, "dto", parameter, new IllegalArgumentException());

        // When
        ResponseEntity<APIErrorResponse> response = handler.handleTypeMismatchException(ex, request);

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).contains("Parameter 'dto' has invalid value 'abc'. Expected type: EmptyDto");
    }

    @Test
    void handleMethodArgumentNotValid_shouldReturnBadRequest() throws NoSuchMethodException {
        // Fake method parameter
        Method method = EmptyController.class.getDeclaredMethod("handle", EmptyDto.class);
        MethodParameter param = new MethodParameter(method, 0);

        // Simulate validation error
        EmptyDto dto = new EmptyDto();
        BeanPropertyBindingResult bindingResult = new BeanPropertyBindingResult(dto, "dummyDto");
        bindingResult.addError(new FieldError("emptyDto", "name", dto, false,
                new String[]{"validation.bad_request"}, null, null));

        MethodArgumentNotValidException ex = new MethodArgumentNotValidException(param, bindingResult);

        ResponseEntity<APIErrorResponse> response = handler.handleMethodArgumentNotValidException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getErrors()).hasSize(1);
        assertThat(response.getBody().getErrors().getFirst().getMessage()).isEqualTo("Invalid or malformed request.");
    }

    @Test
    void handleResponseStatusException_shouldReturnStatusFromException() {
        ResponseStatusException ex = new ResponseStatusException(HttpStatus.NOT_FOUND, "Resource not found");

        ResponseEntity<APIErrorResponse> response = handler.handleResponseStatusException(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("The requested resource could not be found.");
    }

    @Test
    void handleInvalidFormat_shouldReturnBadRequest() {
        InvalidFormatException ex = new InvalidFormatException(null, "Bad format", "123", Integer.class);

        ResponseEntity<APIErrorResponse> response = handler.handleInvalidFormat(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Invalid or malformed request.");
    }

    @Test
    void handleWebFluxBindingErrors_shouldReturnBadRequest() {
        DecodingException ex = new DecodingException("Unreadable message");
        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Invalid or malformed request.");
    }

    @Test
    void handleWebFluxBindingErrors_shouldHandleNestedInvalidFormat() {
        HttpInputMessage message = mock(HttpInputMessage.class);
        InvalidFormatException root = new InvalidFormatException(null, "Invalid format", "abc", Integer.class);
        HttpMessageNotReadableException ex = new HttpMessageNotReadableException("Outer", root,message);

        ResponseEntity<APIErrorResponse> response = handler.handleWebFluxBindingErrors(ex, request);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.BAD_REQUEST);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().getMessage()).isEqualTo("Invalid or malformed request.");
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/test/java/com/itachallenge/errorcore/integrationTest/ErrorCoreIntegrationTest.java:ErrorCoreIntegrationTest.<init>
// Node: ContextConfiguration
package com.itachallenge;

import com.itachallenge.githubcore.config.GithubServiceConfig;
import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.context.annotation.Import;

@SpringBootApplication
@Import(GithubServiceConfig.class)
@EnableDiscoveryClient
@OpenAPIDefinition(info = @Info(title = "Ita Backend User", version = "1.0", description = "Description"))
public class App {

    public static void main(String[] args) {
        SpringApplication.run(App.class, args);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/App.java:App.<init>
// Node: Import
// Node: OpenAPIDefinition
// Node: ofSeconds
package com.itachallenge.userinteraction.service.bookmark;
import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.repository.UserRepository;
import com.itachallenge.userinteraction.document.bookmark.BookmarkDocument;
import com.itachallenge.userinteraction.repository.bookmark.BookmarkRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.mockito.junit.jupiter.MockitoExtension;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.*;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class BookmarkServiceImplTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private BookmarkRepository bookmarkRepository;

    @InjectMocks
    private BookmarkServiceImpl bookmarkService;

    private AutoCloseable mocks;

    private static final String USER_NOT_FOUND_WITH_ID = "User not found with id: ";

    @BeforeEach
    void setUp() {
        mocks = MockitoAnnotations.openMocks(this);
        bookmarkService = new BookmarkServiceImpl(userRepository, bookmarkRepository);
    }

    @AfterEach
    void tearDown() throws Exception {
        if (mocks != null) mocks.close();
    }

    @Test
    @DisplayName("getUserBookmarks returns an empty set when the user exists but has no bookmarks")
    void getUserBookmarks_WhenUserHasNoBookmarks_ReturnsEmptySet() {
        UUID userId = UUID.randomUUID();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(true));
        when(bookmarkRepository.findByUserId(userId)).thenReturn(Flux.empty());

        StepVerifier.create(bookmarkService.getUserBookmarks(userId.toString()))
                .expectNextMatches(Set::isEmpty)
                .verifyComplete();

        verify(userRepository, times(1)).existsById(userId);
        verify(bookmarkRepository, times(1)).findByUserId(userId);
    }

    @Test
    @DisplayName("getUserBookmarks returns bookmarks when the user exists")
    void getUserBookmarks_WhenUserExistsWithFavorites_ReturnsBookmarks() {
        UUID userId = UUID.randomUUID();
        UUID challengeId1 = UUID.randomUUID();
        UUID challengeId2 = UUID.randomUUID();

        BookmarkDocument fav1 = BookmarkDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId1)
                .build();
        BookmarkDocument fav2 = BookmarkDocument.builder()
                .uuid(UUID.randomUUID())
                .userId(userId)
                .challengeId(challengeId2)
                .build();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(true));
        when(bookmarkRepository.findByUserId(userId)).thenReturn(Flux.just(fav1, fav2));

        StepVerifier.create(bookmarkService.getUserBookmarks(userId.toString()))
                .expectNextMatches(bookmarks -> bookmarks.contains(challengeId1) && bookmarks.contains(challengeId2))
                .verifyComplete();

        verify(userRepository, times(1)).existsById(userId);
        verify(bookmarkRepository, times(1)).findByUserId(userId);
    }

    @Test
    @DisplayName("getUserBookmarks throws NotFoundException when the user does not exist")
    void getUserBookmarks_WhenUserNotFound_ThrowsNotFoundException() {
        UUID userId = UUID.randomUUID();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(false));

        StepVerifier.create(bookmarkService.getUserBookmarks(userId.toString()))
                .expectErrorMatches(error ->
                        error instanceof NotFoundException &&
                                error.getMessage().equals(USER_NOT_FOUND_WITH_ID + userId))
                .verify();

        verify(userRepository, times(1)).existsById(userId);
        verify(bookmarkRepository, times(0)).findByUserId(userId);
    }

    @Test
    @DisplayName("getUserBookmarks throws BadUUIDException when the UUID format is invalid")
    void getUserBookmarks_WhenInvalidUUID_ThrowsBadUUIDException() {
        String invalidUUID = "invalid-uuid";

        StepVerifier.create(bookmarkService.getUserBookmarks(invalidUUID))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format"))
                .verify();

        verify(userRepository, times(0)).existsById((UUID) any());
        verify(bookmarkRepository, times(0)).findByUserId(any());
    }

    @Test
    @DisplayName("getUserBookmarks propagates repository errors correctly")
    void getUserBookmarks_WhenRepositoryError_PropagatesError() {
        UUID userId = UUID.randomUUID();

        when(userRepository.existsById(userId)).thenReturn(Mono.just(true));
        when(bookmarkRepository.findByUserId(userId)).thenReturn(Flux.error(new RuntimeException("DB error")));

        StepVerifier.create(bookmarkService.getUserBookmarks(userId.toString()))
                .expectErrorMatches(error ->
                        error instanceof RuntimeException &&
                                error.getMessage().equals("DB error"))
                .verify();

        verify(userRepository, times(1)).existsById(userId);
        verify(bookmarkRepository, times(1)).findByUserId(userId);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/userinteraction/service/bookmark/BookmarkServiceImplTest.java:BookmarkServiceImplTest.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/controller/UserControllerSpringTest.java:UserControllerSpringTest.<init>
// Node: SpringBootTest
package com.itachallenge.user.controller;
import com.itachallenge.user.exception.UserGlobalExceptionHandler;
import com.itachallenge.user.dto.AdminCreateUserRequestDto;
import com.itachallenge.user.dto.AdminCreateUserResponseDto;
import com.itachallenge.user.exception.UsernameAlreadyExistsException;
import com.itachallenge.user.service.AdminCreateUserService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@WebFluxTest(controllers = AdminCreateUserController.class)
@ContextConfiguration(classes = { AdminCreateUserController.class })
@Import(UserGlobalExceptionHandler.class)
class AdminCreateUserControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private AdminCreateUserService adminCreateUserService;

    @Test
    @DisplayName("Test: POST /admin/users/create with new user should return 201 Created")
    void createUser_withNewUser_shouldReturn201Created() {

        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("newUser");

        AdminCreateUserResponseDto serviceResponse = AdminCreateUserResponseDto.builder()
                .userId(UUID.randomUUID().toString())
                .username("newUser")
                .build();

        when(adminCreateUserService.createUser(any(AdminCreateUserRequestDto.class))).thenReturn(Mono.just(serviceResponse));

        webTestClient.post()
                .uri("/itachallenge/api/v1/admin/users/create")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .exchange()
                .expectStatus().isCreated()
                .expectBody(AdminCreateUserResponseDto.class)
                .value(response -> {
                    assertThat(response.getUsername()).isEqualTo("newUser");
                    assertThat(response.getUserId()).isNotNull();
                });
    }

    @Test
    @DisplayName("Test: POST /admin/users/create with existing user should return 409 Conflict")
    void createUser_withExistingUser_shouldReturn409Conflict() {

        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("existingUser");

        when(adminCreateUserService.createUser(any(AdminCreateUserRequestDto.class)))
                .thenReturn(Mono.error(new UsernameAlreadyExistsException("Username existingUser already exists.")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/admin/users/create")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .exchange()
                .expectStatus().isEqualTo(409);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/controller/AdminCreateUserControllerTest.java:AdminCreateUserControllerTest.<init>
// Node: WebFluxTest
package com.itachallenge.user.controller.userinteraction.bookmark;

import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.userinteraction.service.bookmark.BookmarkService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Bean;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Set;
import java.util.UUID;

import static org.mockito.Mockito.*;

@WebFluxTest(controllers = {BookmarkController.class, BookmarkLegacyController.class})
class BookmarkControllerTest {

    @MockBean
    private BookmarkService bookmarkService;

    @Autowired
    private WebTestClient webTestClient;

    @TestConfiguration
    static class TestConfig {

        @Bean (name="bookmarkWebClientBuilder")
        public WebClient.Builder webClientBuilder() {
            return WebClient.builder();
        }
    }

    @Test
    @DisplayName("GET /users/{userId}/bookmarks returns bookmarked challenges")
    void getUserBookmarks_NewPath_Success() {
        UUID userId = UUID.randomUUID();
        Set<UUID> expectedBookmarks = Set.of(UUID.randomUUID(), UUID.randomUUID());

        when(bookmarkService.getUserBookmarks(userId.toString()))
                .thenReturn(Mono.just(expectedBookmarks));

        webTestClient.get()
                .uri("/itachallenge/api/v1/users/{userId}/bookmarks", userId)
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(UUID.class)
                .hasSize(expectedBookmarks.size())
                .contains(expectedBookmarks.toArray(new UUID[0]));

        verify(bookmarkService, times(1)).getUserBookmarks(userId.toString());
    }

    @Test
    @DisplayName("GET /user/users/{userId}/bookmarks returns bookmarked challenges - LEGACY")
    void getUserBookmarks_returnsBookmarks() {
        UUID userId = UUID.randomUUID();
        Set<UUID> expectedBookmarks = Set.of(UUID.randomUUID(), UUID.randomUUID());

        when(bookmarkService.getUserBookmarks(userId.toString()))
                .thenReturn(Mono.just(expectedBookmarks));

        webTestClient.get()
                .uri("/itachallenge/api/v1/user/users/{userId}/bookmarks", userId)
                .exchange()
                .expectStatus().isOk()
                .expectHeader().valueEquals("Deprecation", "true")
                .expectBodyList(UUID.class)
                .hasSize(expectedBookmarks.size())
                .contains(expectedBookmarks.toArray(new UUID[0]));

        verify(bookmarkService, times(1)).getUserBookmarks(userId.toString());
    }

    @Test
    @DisplayName("GET /users/{userId}/bookmarks returns 404 if user not found")
    void getUserBookmarks_returns404IfUserNotFound() {
        UUID userId = UUID.randomUUID();

        when(bookmarkService.getUserBookmarks(userId.toString()))
                .thenReturn(Mono.error(new NotFoundException("User not found")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/user/users/{userId}/bookmarks", userId)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody(String.class).isEqualTo("User not found");

        verify(bookmarkService, times(1)).getUserBookmarks(userId.toString());
    }

    @Test
    @DisplayName("GET /users/{userId}/bookmarks returns 400 if UUID is invalid")
    void getUserBookmarks_returns400IfInvalidUUID() {
        String invalidUserId = "invalid-uuid";

        when(bookmarkService.getUserBookmarks(invalidUserId))
                .thenReturn(Mono.error(new BadUUIDException("The provided IDs are not valid.")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/user/users/{userId}/bookmarks", invalidUserId)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody(String.class).isEqualTo("The provided IDs are not valid.");

        verify(bookmarkService, times(1)).getUserBookmarks(invalidUserId);
    }
    @Test
    @DisplayName("GET /users/{userId}/bookmarks returns 500 if there is an internal error")
    void getUserBookmarks_returns500IfUnexpectedError() {
        UUID userId = UUID.randomUUID();

        when(bookmarkService.getUserBookmarks(userId.toString()))
                .thenReturn(Mono.error(new RuntimeException("Unexpected error")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/user/users/{userId}/bookmarks", userId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(String.class).isEqualTo("Unexpected error happened.");

        verify(bookmarkService, times(1)).getUserBookmarks(userId.toString());
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/controller/userinteraction/bookmark/BookmarkControllerTest.java:BookmarkControllerTest.<init>
// Node: Bean
package com.itachallenge.user.controller.userinteraction.favorite;

import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.userinteraction.service.favorite.FavoriteService;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Bean;
import org.springframework.http.HttpStatus;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.Set;
import java.util.UUID;

import static org.mockito.Mockito.*;

@WebFluxTest(controllers = FavoriteController.class)
class FavoriteControllerTest {

    @MockBean
    private FavoriteService favoriteService;  // << Mocked service

    @Autowired
    private WebTestClient webTestClient;

    @TestConfiguration
    static class TestConfig {

        @Bean
        public WebClient.Builder webClientBuilder() {
            return WebClient.builder();
        }
    }

    @Test
    void addToFavorites_WhenAdded_Returns201() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.addChallengeToFavorites(userId, challengeId))
                .thenReturn(Mono.just(true));

        webTestClient.post()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.CREATED)
                .expectBody(Boolean.class).isEqualTo(true);

        verify(favoriteService, times(1)).addChallengeToFavorites(userId, challengeId);
    }

    @Test
    void addToFavorites_WhenAlreadyInFavorites_Returns200() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.addChallengeToFavorites(userId, challengeId))
                .thenReturn(Mono.just(false));

        webTestClient.post()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Boolean.class).isEqualTo(false);

        verify(favoriteService, times(1)).addChallengeToFavorites(userId, challengeId);
    }

    @Test
    void addToFavorites_WhenUserNotExists_Returns404() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.addChallengeToFavorites(userId, challengeId))
                .thenReturn(Mono.error(new NotFoundException("User not found")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody(String.class).isEqualTo("User not found");

        verify(favoriteService, times(1)).addChallengeToFavorites(userId, challengeId);
    }

    @Test
    void addToFavorites_WhenBadFormattedId_Returns400() {
        String userId = "invalidUuid";
        String challengeId = "invalidUUid";
        when(favoriteService.addChallengeToFavorites(userId, challengeId))
                .thenReturn(Mono.error(new BadUUIDException("Error message")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody(String.class).isEqualTo("The provided IDs are not valid.");

        verify(favoriteService, times(1)).addChallengeToFavorites(userId, challengeId);
    }

    @Test
    void addToFavorites_WhenUnexpectedError_Returns500() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.addChallengeToFavorites(userId, challengeId))
                .thenReturn(Mono.error(new Exception()));

        webTestClient.post()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(String.class).isEqualTo("Unexpected error happened.");

        verify(favoriteService, times(1)).addChallengeToFavorites(userId, challengeId);
    }

    @Test
    @DisplayName("GET /userinteraction/favorites/{userId} returns favorite challenges")
    void getUserFavorites_returnsFavorites() {
        UUID userId = UUID.randomUUID();
        Set<UUID> expectedFavorites = Set.of(UUID.randomUUID(), UUID.randomUUID());

        when(favoriteService.getUserFavorites(userId.toString()))
                .thenReturn(Mono.just(expectedFavorites));

        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", userId)
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(UUID.class)
                .hasSize(expectedFavorites.size())
                .contains(expectedFavorites.toArray(new UUID[0]));

        verify(favoriteService, times(1)).getUserFavorites(userId.toString());
    }

    @Test
    @DisplayName("GET /userinteraction/favorites/{userId} returns 404 if user not found")
    void getUserFavorites_returns404IfUserNotFound() {
        UUID userId = UUID.randomUUID();

        when(favoriteService.getUserFavorites(userId.toString()))
                .thenReturn(Mono.error(new NotFoundException("User not found")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", userId)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody(String.class).isEqualTo("User not found");

        verify(favoriteService, times(1)).getUserFavorites(userId.toString());
    }

    @Test
    @DisplayName("GET /userinteraction/favorites/{userId} returns 400 if UUID is invalid")
    void getUserFavorites_returns400IfInvalidUUID() {
        String invalidUserId = "invalid-uuid";

        when(favoriteService.getUserFavorites(invalidUserId))
                .thenReturn(Mono.error(new BadUUIDException("The provided IDs are not valid.")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", invalidUserId)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody(String.class).isEqualTo("The provided IDs are not valid.");

        verify(favoriteService, times(1)).getUserFavorites(invalidUserId);
    }

    @Test
    void deleteFromFavorites_WhenDeleted_Returns200() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.deleteChallengeFromFavorites(userId, challengeId))
                .thenReturn(Mono.just(true));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.OK)
                .expectBody(Boolean.class).isEqualTo(true);

        verify(favoriteService, times(1)).deleteChallengeFromFavorites(userId, challengeId);
    }

    @Test
    void deleteFromFavorites_WhenNotInFavorites_Returns200() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.deleteChallengeFromFavorites(userId, challengeId))
                .thenReturn(Mono.just(false));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Boolean.class).isEqualTo(false);

        verify(favoriteService, times(1)).deleteChallengeFromFavorites(userId, challengeId);
    }

    @Test
    void deleteFromFavorites_WhenUserNotExists_Returns404() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.deleteChallengeFromFavorites(userId, challengeId))
                .thenReturn(Mono.error(new NotFoundException("User not found")));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.NOT_FOUND)
                .expectBody(String.class).isEqualTo("User not found");

        verify(favoriteService, times(1)).deleteChallengeFromFavorites(userId, challengeId);
    }

    @Test
    void deleteFromFavorites_WhenBadFormattedId_Returns404() {
        String userId = "invalidUuid";
        String challengeId = "invalidUUid";
        when(favoriteService.deleteChallengeFromFavorites(userId, challengeId))
                .thenReturn(Mono.error(new BadUUIDException("Error message")));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.BAD_REQUEST)
                .expectBody(String.class).isEqualTo("The provided IDs are not valid.");

        verify(favoriteService, times(1)).deleteChallengeFromFavorites(userId, challengeId);
    }

    @Test
    void deleteFromFavorites_WhenUnexpectedError_Returns500() {
        String userId = UUID.randomUUID().toString();
        String challengeId = UUID.randomUUID().toString();
        when(favoriteService.deleteChallengeFromFavorites(userId, challengeId))
                .thenReturn(Mono.error(new Exception()));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/" + userId + "/favorites/" + challengeId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(String.class).isEqualTo("Unexpected error happened.");

        verify(favoriteService, times(1)).deleteChallengeFromFavorites(userId, challengeId);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/controller/userinteraction/favorite/FavoriteControllerTest.java:FavoriteControllerTest.<init>
package com.itachallenge.user.controller.userinteraction.favorite;


import com.itachallenge.user.dto.AdminCreateUserRequestDto;
import com.itachallenge.user.dto.AdminCreateUserResponseDto;
import com.itachallenge.user.repository.UserRepository;
import com.itachallenge.userinteraction.repository.favorite.FavoriteRepository;

import java.util.Set;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.containers.wait.strategy.Wait;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(  webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@AutoConfigureWebTestClient
@Testcontainers
class FavoriteControllerIntegrationTest {

    @Container
    static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:5.0.9")
            .waitingFor(Wait.forListeningPort());

    @DynamicPropertySource
    static void setProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", () -> mongoDBContainer.getReplicaSetUrl("itachallenge_test"));
    }

    @Autowired
    private WebTestClient webTestClient;

    @Autowired
    private FavoriteRepository favoriteRepository;
    @Autowired
    private UserRepository userRepository;

    @BeforeEach
    void setUp(){
        favoriteRepository.deleteAll().block();
        userRepository.deleteAll().block();
    }


    @Test
    void getUserFavorites_WithExistingFavorites_ReturnsSetOfChallengeIds(){
        String userId = createUser("user");

        String challengeId1 = UUID.randomUUID().toString();
        String challengeId2 = UUID.randomUUID().toString();
        String challengeId3 = UUID.randomUUID().toString();

        addFavorite(userId, challengeId1);
        addFavorite(userId, challengeId2);
        addFavorite(userId, challengeId3);

        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", userId)
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isOk()
                .expectHeader().contentType(MediaType.APPLICATION_JSON)
                .expectBody(new ParameterizedTypeReference<Set<String>>(){})
                .value(
                        favorites -> {
                            assertThat(favorites).hasSize(3);
                            assertThat(favorites).containsExactlyInAnyOrder(challengeId1, challengeId2, challengeId3);
                        }
                );
    }

    @Test
    void getUserFavorites_WithNoFavorites_ReturnsEmptySet(){
        String userId = createUser("user");

        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", userId)
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isOk()
                .expectHeader().contentType(MediaType.APPLICATION_JSON)
                .expectBody(new ParameterizedTypeReference<Set<String>>(){})
                .value(
                        favorites -> assertThat(favorites).isEmpty()
                );
    }

    @Test
    void getUserFavorites_WithMultipleFavoritesFromDifferentUsers_ReturnsOnlyUserFavorites(){
        String user1 = createUser("user1");
        String user2 = createUser("user2");

        String challengeId1 = UUID.randomUUID().toString();
        String challengeId2 = UUID.randomUUID().toString();
        String challengeId3 = UUID.randomUUID().toString();

        addFavorite(user1, challengeId1);
        addFavorite(user1, challengeId2);
        addFavorite(user2, challengeId3);

        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", user1)
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isOk()
                .expectHeader().contentType(MediaType.APPLICATION_JSON)
                .expectBody(new ParameterizedTypeReference<Set<String>>() {})
                .value(favorites -> {
                            assertThat(favorites).hasSize(2);
                            assertThat(favorites).containsExactlyInAnyOrder(challengeId1, challengeId2);
                            assertThat(favorites).doesNotContain(challengeId3);
                        }
                );
    }

    @Test
    void getUserFavorites_WithInvalidUUID_Returns400(){
        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", 321)
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isBadRequest()
                .expectHeader().contentType(MediaType.APPLICATION_JSON)
                //TODO UN-COMMENT WHEN NEW ERROR-CORE GLOBAL HANDLER IS USED + QUITTING 3 LAST LINES
//              .expectBody()
//                .jsonPath("$.status").isEqualTo(400)
//                .jsonPath("$.error").value(error -> assertThat(error.toString())
//                        .contains("BadUUIDException"))
//                .jsonPath("$.message").value(message -> assertThat(message.toString())
//                        .contains("The provided IDs are not valid"))
//                .jsonPath("$.path").value(path -> assertThat(path.toString())
//                        .contains("/users/" + invalidUserId + "/favorites"));
                .expectBody(String.class)
                .value( body ->
                        assertThat(body).contains("The provided IDs are not valid"));
    }

    @Test
    void getUserFavorites_WhenUserDoesntExist_Returns404(){
        String nonExistentUserId = UUID.randomUUID().toString();

        webTestClient.get()
                .uri("/itachallenge/api/v1/userinteraction/favorites/{userId}", nonExistentUserId)
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isNotFound()
                .expectHeader().contentType(MediaType.APPLICATION_JSON)
                //TODO UN-COMMENT WHEN NEW ERROR-CORE GLOBAL HANDLER IS USED + QUITTING 3 LAST LINES
//              .expectBody()
//                .jsonPath("$.status").isEqualTo(404)
//                .jsonPath("$.error").value(error -> assertThat(error.toString())
//                        .contains("NotFoundException")) // Nom de l'exception
//                .jsonPath("$.message").value(message -> assertThat(message.toString())
//                        .contains("not found")) // Message d'erreur
//                .jsonPath("$.path").value(path -> assertThat(path.toString())
//                        .contains("/users/" + invalidUserId + "/favorites"));
                .expectBody(String.class)
                .value( body ->
                        assertThat(body).contains("not found"));
    }



    private String createUser(String user){
        AdminCreateUserRequestDto userRequestDto = new AdminCreateUserRequestDto();
        userRequestDto.setUsername(user);

        AdminCreateUserResponseDto userResponseDto =
                webTestClient.post()
                        .uri("/itachallenge/api/v1/admin/users/create")
                        .contentType(MediaType.APPLICATION_JSON)
                        .bodyValue(userRequestDto)
                        .exchange()
                        .expectStatus().isCreated()
                        .expectBody(AdminCreateUserResponseDto.class)
                        .returnResult().getResponseBody();

        assertThat(userResponseDto).isNotNull();
        assertThat(userResponseDto.getUserId()).isNotNull();
        return userResponseDto.getUserId();
    }

    private void addFavorite(String userId, String challengeId){
        webTestClient.post()
                .uri("/itachallenge/api/v1/userinteraction/favorites/users/{userId}/favorites/{challengeId}", userId, challengeId)
                .exchange()
                .expectStatus().isCreated();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/controller/userinteraction/favorite/FavoriteControllerIntegrationTest.java:FavoriteControllerIntegrationTest.<init>
// Node: ActiveProfiles
// Node: MongoDBContainer
// Node: waitingFor
// Node: forListeningPort
package com.itachallenge.user.service;

import com.itachallenge.user.document.UserDocument;
import com.itachallenge.user.document.enums.Role;
import com.itachallenge.user.dto.AdminCreateUserRequestDto;
import com.itachallenge.user.dto.AdminCreateUserResponseDto;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.exception.UsernameAlreadyExistsException;
import com.itachallenge.user.repository.UserRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AdminCreateUserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private ExternalGithubService externalGithubService;

    @InjectMocks
    private AdminCreateUserService adminCreateUserService;

    @Test
    @DisplayName("Test: Create user when username does not exist in DB but in Github does")
    void createUser_whenUserDoesNotExistInDB_shouldCreateAndReturnUser() {

        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("newUser");

        UserDocument savedUser = UserDocument.builder()
                .uuid(UUID.randomUUID())
                .username("newUser")
                .role(Role.USER)
                .build();

        when(userRepository.findByUsername("newUser")).thenReturn(Mono.empty());
        when(externalGithubService.userExists("newUser")).thenReturn(Mono.just(true));
        when(userRepository.save(any(UserDocument.class))).thenReturn(Mono.just(savedUser));

        Mono<AdminCreateUserResponseDto> result = adminCreateUserService.createUser(request);

        StepVerifier.create(result)
                .expectNextMatches(response -> response.getUsername().equals("newUser") &&
                        response.getUserId() != null)
                .verifyComplete();

        verify(userRepository).save(any(UserDocument.class));
        verify(externalGithubService).userExists("newUser");
    }

    @Test
    @DisplayName("Test: Create user when username does not exist in DB but it's not a real Github username")
    void createUser_whenUserDoesNotExistInDBAndIsNotAGithubUser_shouldThrowException() {
        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("newUser");

        when(userRepository.findByUsername("newUser")).thenReturn(Mono.empty());
        when(externalGithubService.userExists("newUser")).thenReturn(Mono.just(false));

        Mono<AdminCreateUserResponseDto> result = adminCreateUserService.createUser(request);

        StepVerifier.create(result)
                .expectError(NotFoundException.class)
                .verify();

        verify(userRepository, never()).save(any());
        verify(externalGithubService).userExists("newUser");
    }

    @Test
    @DisplayName("Test: Attempt to create a user that already exists")
    void createUser_whenUserAlreadyExists_shouldThrowException() {
        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("existingUser");

        UserDocument existingUser = new UserDocument();
        existingUser.setUsername("existingUser");

        when(userRepository.findByUsername("existingUser")).thenReturn(Mono.just(existingUser));

        Mono<AdminCreateUserResponseDto> result = adminCreateUserService.createUser(request);

        StepVerifier.create(result)
                .expectError(UsernameAlreadyExistsException.class)
                .verify();

        verify(userRepository, never()).save(any());
    }

    @Test
    @DisplayName("Test: GitHub API timeout should propagate GithubUnavailableException (504)")
    void createUser_whenGithubApiTimeout_shouldThrowGithubUnavailableException() {
        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("newUser");

        when(userRepository.findByUsername("newUser")).thenReturn(Mono.empty());
        when(externalGithubService.userExists("newUser"))
                .thenReturn(Mono.delay(Duration.ofSeconds(5)).thenReturn(true));

        Mono<AdminCreateUserResponseDto> result = adminCreateUserService.createUser(request);

        StepVerifier.create(result)
                .expectErrorMatches(ex -> ex instanceof com.itachallenge.githubcore.exception.GithubUnavailableException)
                .verify();

        verify(userRepository, never()).save(any());
    }

    @Test
    @DisplayName("Test: GitHub API immediate failure should propagate GithubUnavailableException (503)")
    void createUser_whenGithubApiFailsImmediately_shouldThrowGithubUnavailableException() {
        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("newUser");

        when(userRepository.findByUsername("newUser")).thenReturn(Mono.empty());
        when(externalGithubService.userExists("newUser"))
                .thenReturn(Mono.error(new RuntimeException("GitHub API down")));

        Mono<AdminCreateUserResponseDto> result = adminCreateUserService.createUser(request);

        StepVerifier.create(result)
                .expectErrorMatches(ex -> ex instanceof com.itachallenge.githubcore.exception.GithubUnavailableException &&
                        ex.getMessage().equals("GitHub API down"))
                .verify();

        verify(userRepository, never()).save(any());
    }

    @Test
    @DisplayName("Test: New user should always have default USER role")
    void createUser_shouldAssignDefaultUserRole() {
        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("newUser");

        UserDocument savedUser = UserDocument.builder()
                .uuid(UUID.randomUUID())
                .username("newUser")
                .role(Role.USER)
                .build();

        when(userRepository.findByUsername("newUser")).thenReturn(Mono.empty());
        when(externalGithubService.userExists("newUser")).thenReturn(Mono.just(true));
        when(userRepository.save(any(UserDocument.class))).thenReturn(Mono.just(savedUser));

        Mono<AdminCreateUserResponseDto> result = adminCreateUserService.createUser(request);

        StepVerifier.create(result)
                .expectNextMatches(response -> response.getUsername().equals("newUser") &&
                        response.getUserId() != null)
                .verifyComplete();

        verify(userRepository).save(argThat(user -> user.getRole() == Role.USER));
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/service/AdminCreateUserServiceTest.java:AdminCreateUserServiceTest.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/service/UserSolutionServiceImplTest.java:UserSolutionServiceImplTest.<init>
package com.itachallenge.common.exception;

import com.fasterxml.jackson.databind.exc.InvalidFormatException;
import com.itachallenge.challenge.config.PropertiesConfig;
import com.itachallenge.challenge.dto.MessageDto;
import com.itachallenge.challenge.exception.*;
import com.itachallenge.challenge.repository.*;
import com.itachallenge.challenge.service.*;
import com.itachallenge.common.exception.dto.ErrorResponseDto;
import com.itachallenge.common.exception.enums.ErrorCode;
import com.itachallenge.jwtcore.service.IJwtService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import org.hamcrest.MatcherAssert;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.MockitoAnnotations;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.data.mongodb.core.convert.MappingMongoConverter;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.validation.BindingResult;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.server.ResponseStatusException;
import com.fasterxml.jackson.databind.JsonMappingException.Reference;

import java.util.*;

import static org.hamcrest.CoreMatchers.notNullValue;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

@ExtendWith(SpringExtension.class)
@WebFluxTest(controllers = GlobalExceptionHandlerTest.class)
class GlobalExceptionHandlerTest {
    //VARIABLES
    String REQUEST = "Invalid request";
    private final HttpStatus BAD_REQUEST = HttpStatus.BAD_REQUEST;
    private final HttpStatus OK_REQUEST = HttpStatus.OK;
    private final HttpStatus NOT_FOUND_REQUEST = HttpStatus.NOT_FOUND;

    @InjectMocks
    private GlobalExceptionHandler globalExceptionHandler;
    @MockBean
    private ResponseStatusException responseStatusException;
    @MockBean
    private MessageDto errorMessage;
    @MockBean
    private MethodArgumentNotValidException methodArgumentNotValidException;
    @MockBean
    private DiscoveryClient discoveryClient;
    @MockBean
    private IChallengeService challengeService;
    @MockBean
    private IUserService userService;
    @MockBean
    private IFavoriteService favoriteService;
    @MockBean
    private ITagService tagService;
    @MockBean
    private IResourceService resourceService;
    @MockBean
    private ILanguageService languageService;
    @MockBean
    private WebClient.Builder webClientBuilder;
    @MockBean
    private ChallengeRepository challengeRepository;
    @MockBean
    private TagRepository tagRepository;
    @MockBean
    private SolutionRepository solutionRepository;
    @MockBean
    private ResourceRepository resourceRepository;
    @MockBean
    private LanguageRepository languageRepository;
    @MockBean
    private PropertiesConfig config;
    @MockBean
    private IJwtService jwtService;
    @MockBean
    private MappingMongoConverter mappingMongoConverter;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    void testHandleResponseStatusException() {

        // Arrange
        String expectedErrorMessage = "Validation failed";
        HttpStatus expectedStatus = HttpStatus.BAD_REQUEST;
        ResponseStatusException ex = new ResponseStatusException(expectedStatus, expectedErrorMessage);

        GlobalExceptionHandler handler = new GlobalExceptionHandler();

        // Act
        ResponseEntity<MessageDto> responseEntity = handler.handleResponseStatusException(ex);

        // Assert
        assertEquals(expectedStatus, responseEntity.getStatusCode());
        assertEquals(expectedErrorMessage, responseEntity.getBody().getMessage());
    }

    @Test
    void testHandleResponseStatusException_NullDetailMessageArguments() {
        // Arrange
        HttpStatus expectedStatus = HttpStatus.BAD_REQUEST;
        ResponseStatusException ex = mock(ResponseStatusException.class);
        when(ex.getStatusCode()).thenReturn(expectedStatus);
        when(ex.getDetailMessageArguments()).thenReturn(null);

        GlobalExceptionHandler handler = new GlobalExceptionHandler();

        // Act
        ResponseEntity<MessageDto> responseEntity = handler.handleResponseStatusException(ex);

        // Assert
        assertEquals(expectedStatus, responseEntity.getStatusCode());
        assertEquals("Validation failed", Objects.requireNonNull(responseEntity.getBody()).getMessage());
    }

    @Test
    void TestHandleMethodArgumentNotValidException() {

        // Arrange
        BindingResult bindingResult = mock(BindingResult.class);
        when(bindingResult.getFieldErrors()).thenReturn(List.of(new FieldError("object", "field", "message")));
        when(methodArgumentNotValidException.getBindingResult()).thenReturn(bindingResult);

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setMethod("POST");
        request.setRequestURI("/itachallenge/api/v1/challenge/challenges");

        // Act
        ResponseEntity<?> responseEntity =
                globalExceptionHandler.handleMethodArgumentNotValidException(methodArgumentNotValidException, request);

        // Assert
        MatcherAssert.assertThat(responseEntity, notNullValue());
    }

    @Test
    void TestHandleMethodArgumentNotValidException_Return_DefaultMessage() {

        // Arrange
        BindingResult bindingResult = mock(BindingResult.class);
        FieldError fieldError = mock(FieldError.class);
        when(fieldError.getField()).thenReturn("name");
        when(fieldError.getDefaultMessage()).thenReturn("default message");
        when(fieldError.getCodes()).thenReturn(new String[]{"message"});
        when(bindingResult.getFieldErrors()).thenReturn(List.of(fieldError));
        when(methodArgumentNotValidException.getBindingResult()).thenReturn(bindingResult);

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setMethod("PUT");
        request.setRequestURI("/whatever");

        // Act
        ResponseEntity<?> responseEntity =
                globalExceptionHandler.handleMethodArgumentNotValidException(methodArgumentNotValidException, request);

        // Assert
        MatcherAssert.assertThat(responseEntity, notNullValue());
    }

    @Test
    void handleConstraintViolation() {
        // Arrange
        Set<ConstraintViolation<?>> constraints = new HashSet<>();

        ConstraintViolation<?> constraint1 = mock(ConstraintViolation.class);
        when(constraint1.getMessage()).thenReturn("Expected message");
        constraints.add(constraint1);

        ConstraintViolation<?> constraint2 = mock(ConstraintViolation.class);
        when(constraint2.getMessage()).thenReturn("Expected message");
        constraints.add(constraint2);

        ConstraintViolationException exception = new ConstraintViolationException("Validation failed.", constraints);

        // Act
        ResponseEntity<MessageDto> responseEntity = globalExceptionHandler.handleConstraintViolation(exception);

        // Assert
        assertEquals(BAD_REQUEST, responseEntity.getStatusCode());
        String responseBody = Objects.requireNonNull(responseEntity.getBody()).getMessage();
        Assertions.assertTrue(responseBody.contains("Expected message"));
    }


    @Test
    void testHandleChallengeNotFoundException() {
        // Arrange
        ChallengeNotFoundException challengeNotFoundException = new ChallengeNotFoundException("Challenge not found");

        HttpServletRequest request = mock(HttpServletRequest.class);
        when(request.getMethod()).thenReturn("GET");
        when(request.getRequestURI()).thenReturn("/whatever");

        // Act
        ResponseEntity<?> responseEntity = globalExceptionHandler.handleChallengeNotFoundException(challengeNotFoundException, request);

        // Assert
        assertEquals(NOT_FOUND_REQUEST, responseEntity.getStatusCode());
        MessageDto body = (MessageDto) responseEntity.getBody();
        String responseBody = Objects.requireNonNull(body).getMessage();
        Assertions.assertTrue(responseBody.contains("Challenge not found"));
    }

    @Test
    void testHandleResourceNotFoundException() {
        // Testgi
        ResourceNotFoundException resourceNotFoundException = new ResourceNotFoundException("Resource not found");

        ResponseEntity<MessageDto> responseEntity = globalExceptionHandler.handleResourceNotFoundException(resourceNotFoundException);

        assertEquals(HttpStatus.NOT_FOUND, responseEntity.getStatusCode());
        String responseBody = Objects.requireNonNull(responseEntity.getBody()).getMessage();
        Assertions.assertTrue(responseBody.contains("Resource not found"));
    }

    @Test
    void testHandleNotFoundException() {
        // Arrange
        NotFoundException notFoundException = new NotFoundException("Whatever not found");

        // Act
        ResponseEntity<MessageDto> responseEntity = globalExceptionHandler.handleNotFoundException(notFoundException);

        // Assert
        assertEquals(OK_REQUEST, responseEntity.getStatusCode());
        String responseBody = Objects.requireNonNull(responseEntity.getBody()).getMessage();
        Assertions.assertTrue(responseBody.contains("Whatever not found"));
    }

    @Test
    void test_HandleBadUUIDException() {
        // Arrange
        BadUUIDException badUUIDException = new BadUUIDException("Invalid Id format");

        // Act
        ResponseEntity<MessageDto> responseEntity = globalExceptionHandler.handleBadUUIDException(badUUIDException);

        // Assert
        assertEquals(BAD_REQUEST, responseEntity.getStatusCode());
        String responseBody = Objects.requireNonNull(responseEntity.getBody()).getMessage();
        Assertions.assertTrue(responseBody.contains("Invalid Id format"));
    }

    @Test
    void testHandleLanguageNotFoundException() {

        LanguageNotFoundException exception = new LanguageNotFoundException("Language not found");

        ResponseEntity<MessageDto> responseEntity = globalExceptionHandler.handleLanguageNotFoundException(exception);

        assertEquals(HttpStatus.BAD_REQUEST, responseEntity.getStatusCode());
        String responseBody = responseEntity.getBody().getMessage();
        assertTrue(responseBody.contains("Language not found"));
    }

    @Test
    void testHandleCustomInternalServerErrorException() {

        InternalServerErrorException exception = new InternalServerErrorException("Error message");

        ResponseEntity<MessageDto> responseEntity = globalExceptionHandler.handleCustomInternalServerErrorException(exception);

        assertEquals(HttpStatus.INTERNAL_SERVER_ERROR, responseEntity.getStatusCode());
        String responseBody = responseEntity.getBody().getMessage();
        assertTrue(responseBody.contains("Error message"));
    }

    @Test
    void testHandleTagNotFoundException() {

        TagNotFoundException exception = new TagNotFoundException("Tag not found");

        ResponseEntity<MessageDto> responseEntity = globalExceptionHandler.handleTagNotFoundException(exception);

        assertEquals(HttpStatus.NOT_FOUND, responseEntity.getStatusCode());
        String responseBody = responseEntity.getBody().getMessage();
        assertTrue(responseBody.contains("Tag not found"));
    }

    @Test
    void testHandleInvalidFormat_TagsField() {
        InvalidFormatException ex = InvalidFormatException.from(
                null,
                "cannot deserialize value of type java.util.UUID from String \"invalid-uuid\"",
                "invalid-uuid",
                UUID.class
        );

        ex.prependPath(new Reference(null, "tags"));

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setMethod("GET");
        request.setRequestURI("/any/other/endpoint");

        ResponseEntity<?> resp = globalExceptionHandler.handleInvalidFormat(ex, request);

        assertEquals(HttpStatus.BAD_REQUEST, resp.getStatusCode());
        assertTrue(resp.getBody() instanceof MessageDto);
        assertEquals(
                "invalid format UUID tag: invalid-uuid",
                ((MessageDto) resp.getBody()).getMessage()
        );
    }

    @Test
    void testHandleInvalidFormat_OtherFieldFallback() {
        InvalidFormatException ex = InvalidFormatException.from(
                null,
                "cannot deserialize value of type java.util.UUID from String \"invalid-uuid\"",
                "invalid-uuid",
                UUID.class
        );
        ex.prependPath(new Reference(null, "otherField"));

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setMethod("GET");
        request.setRequestURI("/any/other/endpoint");

        ResponseEntity<?> resp = globalExceptionHandler.handleInvalidFormat(ex, request);

        assertEquals(HttpStatus.BAD_REQUEST, resp.getStatusCode());
        assertEquals(HttpStatus.BAD_REQUEST, resp.getStatusCode());
        assertTrue(resp.getBody() instanceof MessageDto);
        assertEquals(
                ex.getOriginalMessage(),
                ((MessageDto) resp.getBody()).getMessage()
        );
    }

    @Test
    void testHandleChallengeNotFound_GET_ReturnsErrorResponseDto() {
        String challengeId = "123e4567-e89b-12d3-a456-426614174000";
        ChallengeNotFoundException ex =
                new ChallengeNotFoundException("Challenge with id " + challengeId + " not found");

        HttpServletRequest request = mock(HttpServletRequest.class);
        when(request.getMethod()).thenReturn("GET");
        when(request.getRequestURI()).thenReturn("/itachallenge/api/v1/challenge/challenges/" + challengeId);

        ResponseEntity<?> response =
                globalExceptionHandler.handleChallengeNotFoundException(ex, request);

        assertEquals(HttpStatus.NOT_FOUND, response.getStatusCode());
        assertTrue(response.getBody() instanceof ErrorResponseDto);

        ErrorResponseDto body = (ErrorResponseDto) response.getBody();
        assertEquals("CHALLENGE_NOT_FOUND", body.getErrorCode());
        assertEquals("Challenge with id " + challengeId + " not found", body.getMessage());
        assertEquals("/itachallenge/api/v1/challenge/challenges/" + challengeId, body.getPath());
        assertNotNull(body.getTimestamp());
    }

    @Test
    void testHandleMethodArgumentNotValid_POST_ReturnsErrorResponseDtoWithDetails() {
        // Arrange
        FieldError fieldError =
                new FieldError("challengeCreateDto", "title", "must not be blank");

        BindingResult bindingResult = mock(BindingResult.class);
        when(bindingResult.getFieldErrors()).thenReturn(List.of(fieldError));

        MethodArgumentNotValidException ex = mock(MethodArgumentNotValidException.class);
        when(ex.getBindingResult()).thenReturn(bindingResult);

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setMethod("POST");
        request.setRequestURI("/itachallenge/api/v1/challenge/challenges");

        // Act
        ResponseEntity<?> response =
                globalExceptionHandler.handleMethodArgumentNotValidException(ex, request);
        // Assert
        assertEquals(HttpStatus.BAD_REQUEST, response.getStatusCode());
        assertTrue(response.getBody() instanceof ErrorResponseDto);

        ErrorResponseDto body = (ErrorResponseDto) response.getBody();
        assertEquals(ErrorCode.VALIDATION_ERROR.name(), body.getErrorCode());
        assertEquals("/itachallenge/api/v1/challenge/challenges", body.getPath());
        assertNotNull(body.getTimestamp());
        assertNotNull(body.getDetails());
        assertEquals("must not be blank", body.getDetails().get("title"));
    }

    @Test
    void testHandleInvalidFormat_PostChallenges_ReturnsErrorResponseDto() {
        // Arrange
        InvalidFormatException ex = InvalidFormatException.from(
                null,
                "cannot deserialize value of type java.util.UUID from String \"JAxxVA\"",
                "JAxxVA",
                UUID.class
        );
        ex.prependPath(new Reference(null, "tags"));

        MockHttpServletRequest request = new MockHttpServletRequest();
        request.setMethod("POST");
        request.setRequestURI("/itachallenge/api/v1/challenge/challenges");

        // Act
        ResponseEntity<?> resp = globalExceptionHandler.handleInvalidFormat(ex, request);
        // Assert
        assertEquals(HttpStatus.BAD_REQUEST, resp.getStatusCode());
        assertTrue(resp.getBody() instanceof ErrorResponseDto);

        ErrorResponseDto body = (ErrorResponseDto) resp.getBody();

        assertEquals(ErrorCode.VALIDATION_ERROR.name(), body.getErrorCode());
        assertEquals("Validation failed", body.getMessage());
        assertNotNull(body.getTimestamp());
        assertEquals("/itachallenge/api/v1/challenge/challenges", body.getPath());
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/common/exception/GlobalExceptionHandlerTest.java:GlobalExceptionHandlerTest.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/submission/service/SubmissionServiceImplTest.java:SubmissionServiceImplTest.<init>
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.config.PropertiesConfig;
import com.itachallenge.challenge.document.DetailDocument;
import com.itachallenge.challenge.dto.*;
import com.itachallenge.challenge.enums.DifficultyLevel;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.exception.*;
import com.itachallenge.challenge.repository.ChallengeRepository;
import com.itachallenge.challenge.service.*;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.common.exception.GlobalExceptionHandler;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Import;
import org.springframework.context.support.ResourceBundleMessageSource;
import org.springframework.core.env.Environment;
import org.springframework.data.mongodb.core.convert.MappingMongoConverter;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.*;
import java.util.function.Consumer;
import java.util.stream.Stream;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@WebFluxTest(controllers = ChallengeController.class)
@ExtendWith(SpringExtension.class)
@Import(GlobalExceptionHandler.class)
@ActiveProfiles("test")
class ChallengeControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @Autowired
    private Environment env;

    @MockBean
    private IChallengeService challengeService;

    @MockBean
    private ITagService tagService;

    @MockBean
    private DiscoveryClient discoveryClient;

    @MockBean
    private PropertiesConfig config;

    @MockBean
    private IChallengeJwtFacade challengeJwtFacade;

    @MockBean
    private ChallengeRepository challengeRepository;

    @MockBean
    private ILanguageService languageService;

    @MockBean
    private IResourceService resourceService;

    @MockBean
    private IUserService userService;

    @MockBean
    private MappingMongoConverter mappingMongoConverter;

    private List<UUID> tags;
    private String challengeId;
    private ChallengeCreateDto formData;
    private ChallengeDto createdChallenge;
    private ResourceBundleMessageSource messageSource;


    @BeforeEach
    void setup(){
        tags = List.of(UUID.randomUUID());
        challengeId = String.valueOf(UUID.randomUUID());
        formData = new ChallengeCreateDto("títol", "descripció",
                DifficultyLevel.valueOf("EASY"), "Java", "solució", Topic.LISTS, tags);
        createdChallenge = new ChallengeDto();

        when(challengeService.getRelatedChallenges(argThat(id -> !isValidUUID(id))))
                .thenReturn(Mono.error(new BadUUIDException("Invalid ID format. Please indicate the correct format.")));

        messageSource = new ResourceBundleMessageSource();
        messageSource.setBasename("messages");
        messageSource.setDefaultEncoding("UTF-8");

    }

        private boolean isValidUUID(String id) {
            try {
                UUID.fromString(id);
                return true;
            } catch (IllegalArgumentException e) {
                return false;
            }
        }


    @Test
    void getOneChallenge_ChallengeFound_ReturnsOkResponse() {
        String id = "existing Id";
        ChallengeDto challengeDto = new ChallengeDto();
        Mono<ChallengeDto> response = Mono.just(challengeDto);

        when(challengeService.getChallengeById(id)).thenReturn(response);

        Mono<ChallengeDto> result = challengeService.getChallengeById(id);

        StepVerifier.create(result)
                .expectNext(challengeDto)
                .verifyComplete();

    }

    @Test
    void getAllChallenges_ValidPageParameters_ChallengesReturned() {
        //Arrange
        ChallengeDto challengeDto1 = new ChallengeDto();
        ChallengeDto challengeDto2 = new ChallengeDto();
        ChallengeDto challengeDto3 = new ChallengeDto();
        ChallengeDto[] expectedChallenges = {challengeDto1, challengeDto2, challengeDto3};
        GenericResultDto<ChallengeDto> expectedResult = new GenericResultDto<>();
        expectedResult.setInfo(0, 3, 3, expectedChallenges);

        Mono<GenericResultDto<ChallengeDto>> expectedResultMono = Mono.just(expectedResult);

        String offset = "0";
        String limit = "3";

        when(challengeService.getAllChallenges(Integer.parseInt(offset), Integer.parseInt(limit)))
                .thenReturn(expectedResultMono);

        // Act & Assert
        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/challenges?offset=0&limit=3")
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(ChallengeDto.class);
    }

    @Test
    void getAllChallenges_NullPageParameters_ChallengesReturned() {
        ChallengeDto challengeDto1 = new ChallengeDto();
        ChallengeDto challengeDto2 = new ChallengeDto();
        ChallengeDto[] expectedChallenges = {challengeDto1, challengeDto2};
        GenericResultDto<ChallengeDto> expectedResult = new GenericResultDto<>();
        expectedResult.setInfo(0, 2, 2, expectedChallenges);

        Mono<GenericResultDto<ChallengeDto>> expectedResultMono = Mono.just(expectedResult);


        String offset = "0";
        String limit = "2";

        when(challengeService.getAllChallenges(Integer.parseInt(offset), Integer.parseInt(limit)))
                .thenReturn(expectedResultMono);

        // Act & Assert
        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(ChallengeDto.class);
    }

    @Test
    void getSolutions_ValidIds_SolutionsReturned() {
        // Arrange
        String idChallenge = "valid-challenge-id";
        String idLanguage = "valid-language-id";

        GenericResultDto<SolutionDto> expectedResult = new GenericResultDto<>();
        expectedResult.setInfo(0, 2, 2, new SolutionDto[]{new SolutionDto(), new SolutionDto()});

        when(challengeService.getSolutions(idChallenge, idLanguage)).thenReturn(Mono.just(expectedResult));

        // Act & Assert
        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/solution/challenge/{idChallenge}/language/{idLanguage}", idChallenge, idLanguage)
                .exchange()
                .expectStatus().isOk()
                .expectBody(GenericResultDto.class)
                .value(dto -> {
                    assert dto != null;
                    assert dto.getCount() == 2;
                    assert dto.getResults() != null;
                    assert dto.getResults().length == 2;
                });
    }

    @Test
    void getChallengesByFilter_ValidParams_ChallengesReturned() {
        String idLanguage = "valid-language-id";
        String level = "EASY";
        int offset = 0;
        int limit = 10;

        ChallengeDto challenge1 = new ChallengeDto();
        challenge1.setTitle("Challenge 1");
        challenge1.setLevel(level);

        GenericResultDto<ChallengeDto> expectedResult = new GenericResultDto<>();
        expectedResult.setInfo(offset, limit, 1, new ChallengeDto[]{challenge1});

        when(challengeService.getChallengesByFilter(any(), any(), any(), anyInt(), anyInt()))
                .thenReturn(Flux.just(expectedResult));

        webTestClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/itachallenge/api/v1/challenge/challenges/byFilter")
                        .queryParam("idLanguage", idLanguage)
                        .queryParam("level", level)
                        .queryParam("offset", String.valueOf(offset))
                        .queryParam("limit", String.valueOf(limit))
                        .build())
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isOk()
                .expectHeader().contentType(MediaType.APPLICATION_JSON);

    }

    @Test
    void getRelatedChallenges_ValidId_Returns200_RelatedChallengesReturned() {
        // Arrange
        challengeId = "8514dd47-9800-4fde-a376-f31d450fcd07";

        ChallengeDto challenge1 = new ChallengeDto();
        challenge1.setChallengeId(UUID.randomUUID());

        ChallengeDto challenge2 = new ChallengeDto();
        challenge2.setChallengeId(UUID.randomUUID());

        ChallengeDto challenge3 = new ChallengeDto();
        challenge3.setChallengeId(UUID.randomUUID());

        GenericResultDto<ChallengeDto> expectedResponse = new GenericResultDto<>();
        expectedResponse.setInfo(0, 3, 3, new ChallengeDto[]{challenge1, challenge2, challenge3});

        when(challengeService.getRelatedChallenges(challengeId))
                .thenReturn(Mono.just(expectedResponse));

        // Act & Assert
        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/challenges/{challengeId}/related", challengeId)
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isOk()
                .expectHeader().contentType(MediaType.APPLICATION_JSON)
                .expectBody(GenericResultDto.class)
                .consumeWith(response -> {
                    GenericResultDto<?> body = response.getResponseBody();
                    assertNotNull(body);
                    assertEquals(3, body.getCount());
                });
    }

    @Test
    void getRelatedChallenges_InvalidUUID_Returns400() {
        String invalidUuid = "not-a-valid-uuid";

        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/challenges/{challengeId}/related", invalidUuid)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody(MessageDto.class)
                .consumeWith(response -> assertNotNull(response.getResponseBody()));
    }

    @Test
    void getRelatedChallenges_NoContent_Returns204() {
        String uuid = UUID.randomUUID().toString();

        GenericResultDto<ChallengeDto> emptyResult = new GenericResultDto<>();
        emptyResult.setInfo(0, 3, 0, new ChallengeDto[0]);

        when(challengeService.getRelatedChallenges(uuid))
                .thenReturn(Mono.just(emptyResult));

        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/challenges/{challengeId}/related", uuid)
                .exchange()
                .expectStatus().isNoContent();
    }


    @Test
    void AddSolution_validIdChallenge_validIdLanguage() {
        // Mock del servicio
        SolutionDto inputDto = new SolutionDto();
        inputDto.setSolutionText("Test solution");
        inputDto.setIdChallenge(UUID.randomUUID());
        inputDto.setIdLanguage(UUID.randomUUID());

        SolutionDto outputDto = new SolutionDto();
        outputDto.setSolutionText("Test solution");
        outputDto.setIdChallenge(inputDto.getIdChallenge());
        outputDto.setIdLanguage(inputDto.getIdLanguage());

        when(challengeService.addSolution(any())).thenReturn(Mono.just(outputDto));

        // Ejecutar la solicitud y verificar la respuesta
        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/solution")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(inputDto)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Map.class)
                .consumeWith(response -> {
                    // Verify that the response has the expected keys
                    assert response.getResponseBody().containsKey("uuid_challenge");
                    assert response.getResponseBody().containsKey("uuid_language");
                    assert response.getResponseBody().containsKey("solution_text");

                    // Verify that the values are correct
                    assert response.getResponseBody().get("uuid_challenge").equals(inputDto.getIdChallenge().toString());
                    assert response.getResponseBody().get("uuid_language").equals(inputDto.getIdLanguage().toString());
                    assert response.getResponseBody().get("solution_text").equals(inputDto.getSolutionText());
                });
    }

    @Test
    void addSolution_NullSolutionText_ThrowsBadRequestException() {
        // Arrange
        SolutionDto solutionDto = new SolutionDto();
        solutionDto.setSolutionText(null); // Set solution text to null
        solutionDto.setIdChallenge(UUID.randomUUID()); // Set challenge ID to a valid UUID
        solutionDto.setIdLanguage(UUID.randomUUID()); // Set language ID to a valid UUID

        String expectedMessage = messageSource.getMessage(
                "solution.text.notEmpty", null, Locale.getDefault()
        );
        // Act & Assert
        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/solution")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(solutionDto)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody()
                .jsonPath("$.message").isEqualTo("solutionText: '" + expectedMessage + "'");
    }

    @Test
    void addSolution_EmptySolutionText_ThrowsBadRequestException() {
        // Arrange
        SolutionDto solutionDto = new SolutionDto();
        solutionDto.setSolutionText(""); // Set solution text to empty
        solutionDto.setIdChallenge(UUID.randomUUID()); // Set challenge ID to a valid UUID
        solutionDto.setIdLanguage(UUID.randomUUID()); // Set language ID to a valid UUID

        String expectedMessage = messageSource.getMessage(
                "solution.text.notEmpty", null, Locale.getDefault()
        );
        // Act & Assert
        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/solution")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(solutionDto)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody()
                .jsonPath("$.message").isEqualTo("solutionText: '" + expectedMessage + "'");
    }

    @Test
    void addSolution_NullChallengeId_ThrowsBadRequestException() {
        // Arrange
        SolutionDto solutionDto = new SolutionDto();
        solutionDto.setSolutionText("Test solution");
        solutionDto.setIdChallenge(null); // Set challenge ID to null
        solutionDto.setIdLanguage(UUID.randomUUID()); // Set language ID to a valid UUID

        String expectedMessage = messageSource.getMessage(
                "solution.challengeId.invalid", null, Locale.getDefault()
        );
        // Act & Assert
        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/solution")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(solutionDto)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody()
                .jsonPath("$.message").isEqualTo("idChallenge: '" + expectedMessage + "'");
    }

    @Test
    void addSolution_NullLanguageId_ThrowsBadRequestException() {
        // Arrange
        SolutionDto solutionDto = new SolutionDto();
        solutionDto.setSolutionText("Test solution");
        solutionDto.setIdChallenge(UUID.randomUUID()); // Set challenge ID to a valid UUID
        solutionDto.setIdLanguage(null); // Set challenge ID to null

        String expectedMessage = messageSource.getMessage(
                "solution.languageId.invalid", null, Locale.getDefault()
        );
        // Act & Assert
        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/solution")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(solutionDto)
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody()
                .jsonPath("$.message").isEqualTo("idLanguage: '" + expectedMessage + "'");
    }

    @Test
    void addSolution_NullSolutionDto_ThrowsBadRequestException() {
        // Arrange
        SolutionDto solutionDto = new SolutionDto(); // Create a SolutionDto with null fields

        // Act & Assert
        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/solution")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(solutionDto) // Send the SolutionDto with null fields
                .exchange()
                .expectStatus().isBadRequest();
    }

    @Test
    void addChallenge_test_validRequest() {
        String authHeader = "Bearer valid-token";
        String userId = "user123";

        List<UUID> tags = List.of(UUID.randomUUID());
        ChallengeCreateDto formData = new ChallengeCreateDto("títol", "descripció",
                DifficultyLevel.EASY, "Java", "solució", Topic.LISTS, tags);

        ChallengeDto createdChallenge = new ChallengeDto();

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(challengeService.addChallenge(any())).thenReturn(Mono.just(createdChallenge));

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .header("Authorization", authHeader)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(formData)
                .exchange()
                .expectStatus().isOk()
                .expectBody(ChallengeDto.class);

        verify(challengeJwtFacade, times(1)).getUserUuIdFromAuthenticationHeader(authHeader);
        verify(challengeService, times(1)).addChallenge(any(ChallengeCreateDto.class));
    }

    @Test
    void addChallenge_test_emptyField_statusBadRequest() {
        List<UUID> tags = List.of(UUID.randomUUID());
        ChallengeCreateDto formData = new ChallengeCreateDto("",
                "descripció",
                DifficultyLevel.valueOf("EASY"),
                "Java",
                "solució",
                Topic.COMPONENTS,
                tags);

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(formData)
                .exchange()
                .expectStatus().isBadRequest();
    }


    @Test
    void addChallenge_test_invalidLanguage_statusBadRequest() {
        String authHeader = "Bearer valid-token";
        String userId = "user123";

        List<UUID> tags = List.of(UUID.randomUUID());
        ChallengeCreateDto formData = new ChallengeCreateDto("títol", "descripció",
                DifficultyLevel.EASY, "InvalidLanguage", "solució", Topic.LISTS, tags);

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(challengeService.addChallenge(any())).thenThrow(new BadRequestException("Invalid language"));

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .header("Authorization", authHeader)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(formData)
                .exchange()
                .expectStatus().isBadRequest();

        verify(challengeJwtFacade, times(1)).getUserUuIdFromAuthenticationHeader(authHeader);
        verify(challengeService, times(1)).addChallenge(any(ChallengeCreateDto.class));
    }
    @Test
    void addChallenge_test_invalidLevel_statusBadRequest() {
        String invalidFormData = """
                {
                    "challengeTitle": "títol",
                    "description": "descripció",
                    "level": "TOUGH",
                    "language": "Java",
                    "solution": "solució"
                }
                """;

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(invalidFormData)
                .exchange()
                .expectStatus().isBadRequest();
    }

    @Test
    void getVersionTest() {
        String expectedVersion = env.getProperty("spring.application.version");

        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/version")
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.application_name").isEqualTo("itachallenge-challenge")
                .jsonPath("$.version").isEqualTo(expectedVersion);
    }
    @Test
    void deleteOneChallenge_success() {
        String id = "existing_id";
        DeleteResponseDto deleteResponseDto = new DeleteResponseDto(id, "Challenge deleted successfully.");
        Mono<DeleteResponseDto> response = Mono.just(deleteResponseDto);

        when(challengeService.deleteChallengeById(id))
                .thenReturn(response);

        Mono<DeleteResponseDto> result = challengeService.deleteChallengeById(id);

        StepVerifier.create(result)
                .expectNext(deleteResponseDto)
                .verifyComplete();
    }

    @Test
    void addChallengeToBookmarks_Success_Returns200() {
        String challengeId = "existing_challengeId";
        String userId = "existing_userId";
        String authHeader = "validAuthHeader";

        BookmarkDto expectedResponse = new BookmarkDto(true, 20);

        when(challengeService.addChallengeToBookmarks(challengeId, userId)).thenReturn(Mono.just(expectedResponse));
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus().isOk()
                .expectBody(BookmarkDto.class)
                .isEqualTo(expectedResponse);

        verify(challengeService, times(1)).addChallengeToBookmarks(challengeId, userId);
    }

    @Test
    void addChallengeToBookmarks_InternalServerError_Returns500() {
        String challengeId = "Existing_challengeId";
        String userId = "existing_userId";
        String authHeader = "validAuthHeader";

        String errorMessage = "ErrorMessage";

        when(challengeService.addChallengeToBookmarks(challengeId, userId)).thenReturn(Mono.error(new InternalServerErrorException(errorMessage)));
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus()
                .isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(1)).addChallengeToBookmarks(challengeId, userId);
    }

    @Test
    void addChallengeToBookmarks_InvalidHeader_Returns400() {
        String challengeId = "Existing_challengeId";
        String authHeader = "badHeader";
        String errorMessage = "ErrorMessage";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenThrow(new JwtException(errorMessage));

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus()
                .isEqualTo(HttpStatus.BAD_REQUEST)
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(0)).addChallengeToBookmarks(anyString(), anyString());
    }

    @Test
    void addChallengeToBookmarks_MissingHeader_Returns400() {
        String challengeId = "Existing_challengeId";
        String errorMessage = "ErrorMessage";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(null)).thenThrow(new JwtException(errorMessage));

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .exchange()
                .expectStatus()
                .isEqualTo(HttpStatus.BAD_REQUEST)
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(0)).addChallengeToBookmarks(anyString(), anyString());
    }

    @Test
    @DisplayName("GET /challenges must return the timesFavorite field in the JSON")
    void getChallenges_IncludesTimesFavorite() {
        ChallengeDto challenge = ChallengeDto.builder()
                .challengeId(UUID.randomUUID())
                .title("Repte amb cor")
                .level("Hard")
                .creationDate("2025-03-26")
                .detail(new DetailDocument("detall"))
                .languages(Set.of())
                .solutions(List.of())
                .topic(Topic.DEBUGGING)
                .timesFavorite(5)
                .build();

        ChallengeDto[] challengeArray = new ChallengeDto[] { challenge };
        GenericResultDto<ChallengeDto> resultDto = new GenericResultDto<>(0, 10, 1, challengeArray);


        when(challengeService.getAllChallenges(anyInt(), anyInt()))
                .thenReturn(Mono.just(resultDto));

        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.results[0].timesFavorite").isEqualTo(5);
    }

    @Test
    void getChallengesByFilter_shouldReturnOkResponse() {
        // Mock de respuesta vacía
        GenericResultDto<ChallengeDto> resultDto = new GenericResultDto<>();
        resultDto.setInfo(0, 10, 0, new ChallengeDto[0]);

        UUID mockTag = UUID.randomUUID();
        UUID languageMok = UUID.randomUUID();

        when(challengeService.getChallengesByFilter(
                Optional.of(languageMok.toString()),
                Optional.of("EASY"),
                Optional.of(List.of(mockTag)),
                0,
                2
        )).thenReturn(Flux.just(resultDto));

        webTestClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/itachallenge/api/v1/challenge/challenges/byFilter")
                        .queryParam("idLanguage", languageMok.toString())
                        .queryParam("level", "EASY")
                        .queryParam("offset", 0)
                        .queryParam("limit", 2)
                        .queryParam("tags", mockTag.toString())
                        .build())
                .exchange()
                .expectStatus().isOk();
    }

    @Test
    void updateChallengeValidRequest_AuthorizedUser_Returns200() {
        String authHeader = "Bearer valid-token";
        String userId = "user123";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);
        when(challengeService.updateChallenge(anyString(), any(ChallengeCreateDto.class)))
                .thenReturn(Mono.just(new ChallengeDto()));

        webTestClient.put()
                .uri("/itachallenge/api/v1/challenge/challenge/" + challengeId + "/update")
                .header("Authorization", authHeader)
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(formData)
                .exchange()
                .expectStatus().isOk();

        verify(challengeService, times(1)).updateChallenge(anyString(), any(ChallengeCreateDto.class));
    }

   @Test
    void updateChallenge_MissingAuthHeader_Returns400() {
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(null)).thenThrow(new JwtException("Missing auth header"));

        webTestClient.put()
                .uri("/itachallenge/api/v1/challenge/challenge/" + challengeId + "/update")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(formData)
                .exchange()
                .expectStatus().isBadRequest();

        verifyNoInteractions(challengeService);
    }

    @ParameterizedTest
    @MethodSource("provideEmptyFields")
    void updateChallengeEmptyField_returnsBadRequest_test(Consumer<ChallengeCreateDto> fieldSetter) {
        fieldSetter.accept(formData);

        webTestClient.put()
                .uri("/itachallenge/api/v1/challenge/challenge/" + challengeId + "/update")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(formData)
                .exchange()
                .expectStatus().isBadRequest();

        verifyNoInteractions(challengeService);
    }

    @ParameterizedTest
    @MethodSource("provideInvalidEnumValues")
    void updateChallengeInvalidEnumValue_returnsBadRequest_test(String jsonBody){

        webTestClient.put()
                .uri("/itachallenge/api/v1/challenge/challenge/" + challengeId + "/update")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(jsonBody)
                .exchange()
                .expectStatus().isBadRequest();

        verifyNoInteractions(challengeService);
    }

    private static Stream<Arguments> provideEmptyFields() {
        return Stream.of(
                Arguments.of((Consumer<ChallengeCreateDto>) dto -> dto.setChallengeTitle("")),
                Arguments.of((Consumer<ChallengeCreateDto>) dto -> dto.setDescription("")),
                Arguments.of((Consumer<ChallengeCreateDto>) dto -> dto.setLanguage("")),
                Arguments.of((Consumer<ChallengeCreateDto>) dto -> dto.setSolution(null)),
                Arguments.of((Consumer<ChallengeCreateDto>) dto -> dto.setTopic(null))
        );
    }

    private static Stream<Arguments> provideInvalidEnumValues() {

        String baseJson = """
        {
          "challengeTitle": "Title",
          "description": "Description",
          "level": "%s",
          "language": "Java",
          "solution": "valid solution",
          "topic": "%s",
          "tags": {}
        }
        """;

        return Stream.of(
                Arguments.of(String.format(baseJson, "invalidLevel", "ALL")),
                Arguments.of(String.format(baseJson, "EASY", "invalidTopic"))
        );
    }

    @Test
    void removeChallengeFromBookmarks_Success_Returns200() {
        String challengeId = "existing_challengeId";
        String userId = "existing_userId";
        String authHeader = "validAuthHeader";

        BookmarkDto expectedResponse = new BookmarkDto(false, 20);

        when(challengeService.removeChallengeFromBookmarks(challengeId, userId)).thenReturn(Mono.just(expectedResponse));
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);

        webTestClient.delete()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus().isOk()
                .expectBody(BookmarkDto.class)
                .isEqualTo(expectedResponse);

        verify(challengeService, times(1)).removeChallengeFromBookmarks(challengeId, userId);
    }

    @Test
    void removeChallengeFromBookmarks_InternalServerError_Returns500() {
        String challengeId = "Existing_challengeId";
        String userId = "existing_userId";
        String authHeader = "validAuthHeader";

        String errorMessage = "ErrorMessage";

        when(challengeService.removeChallengeFromBookmarks(challengeId, userId)).thenReturn(Mono.error(new InternalServerErrorException(errorMessage)));
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);

        webTestClient.delete()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus()
                .isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR)
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(1)).removeChallengeFromBookmarks(challengeId, userId);
    }

    @Test
    void removeChallengeFromBookmarks_InvalidHeader_Returns400() {
        String challengeId = "Existing_challengeId";
        String authHeader = "BadHeader";
        String errorMessage = "Error message";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenThrow(new JwtException(errorMessage));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus()
                .isEqualTo(HttpStatus.BAD_REQUEST)
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(0)).removeChallengeFromBookmarks(anyString(), anyString());
    }

    @Test
    void removeChallengeFromBookmarks_MissingHeader_Returns400() {
        String challengeId = "Existing_challengeId";
        String errorMessage = "ErrorMessage";

        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(null)).thenThrow(new JwtException(errorMessage));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .exchange()
                .expectStatus()
                .isEqualTo(HttpStatus.BAD_REQUEST)
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(0)).removeChallengeFromBookmarks(anyString(), anyString());

    }

    @Test
    void addChallenge_emptyTags_statusBadRequest() {
        String challengeWithEmptyTags = """
                {
                     "challengeTitle": "title",
                     "description": "description",
                     "level": "EASY",
                     "language": "Java",
                     "solution": "solution",
                     "topic": "ALL",
                     "tags": []
                 }
            """;

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(challengeWithEmptyTags)
                .exchange()
                .expectStatus().isBadRequest();
    }


    @Test
    void deleteChallenge_shouldReturn200Ok() {
        String challengeId = "12345678-1234-1234-1234-123456789012";

        DeleteResponseDto deleteResponse = new DeleteResponseDto(challengeId, "Challenge deleted successfully");

        when(challengeService.deleteChallengeById(challengeId)).thenReturn(Mono.just(deleteResponse));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId)
                .exchange()
                .expectStatus().isOk();  // ← 200 OK, no 204
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/controller/ChallengeControllerTest.java:ChallengeControllerTest.<init>
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.ResourceDto;
import com.itachallenge.challenge.enums.AssociationType;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.exception.ResourceNotFoundException;
import com.itachallenge.challenge.repository.*;
import com.itachallenge.challenge.service.IResourceService;
import com.itachallenge.common.exception.GlobalExceptionHandler;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.context.annotation.Import;
import org.springframework.data.mongodb.core.convert.MappingMongoConverter;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.UUID;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;


@WebFluxTest(ResourceController.class)
@Import(GlobalExceptionHandler.class)
@ActiveProfiles("test")
class ResourceControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private IResourceService resourceService;

    @MockBean
    private DiscoveryClient discoveryClient;

    @MockBean
    private ChallengeRepository challengeRepository;

    @MockBean
    private SolutionRepository solutionRepository;

    @MockBean
    private WebClient.Builder webClientBuilder;

    @MockBean
    private TagRepository tagRepository;

    @MockBean
    private ChallengeController challengeController;

    @MockBean
    private ResourceRepository resourceRepository;

    @MockBean
    private MappingMongoConverter mappingMongoConverter;

    @MockBean
    private ChallengeSolvedController challengeSolvedController;

    @MockBean
    private LanguageRepository languageRepository;

    @Test
    void createNewResource_ValidRequest_ReturnsCreatedResource() {
        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("Test Resource")
                .description("Test Description")
                .url("https://example.com")
                .topic(Topic.LISTS)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.NONE)
                .build();

        when(resourceService.createResource(any(ResourceDto.class)))
                .thenReturn(Mono.just(resourceDto));

        webTestClient.post()
                .uri("/itachallenge/api/v1/resource/new")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(resourceDto)
                .exchange()
                .expectStatus().isOk()
                .expectBody(ResourceDto.class)
                .value(response -> {
                    assertNotNull(response);
                    assertEquals(resourceDto.getTitle(), response.getTitle());
                    assertEquals(resourceDto.getDescription(), response.getDescription());
                });

        verify(resourceService, times(1)).createResource(any(ResourceDto.class));
    }


    @Test
    void createNewResource_InvalidRequest_ReturnsBadRequest() {


        webTestClient.post()
                .uri("/itachallenge/api/v1/resource/new")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue("{\"title\": }")
                .exchange()
                .expectStatus().isBadRequest();

        verify(resourceService, never()).createResource(any(ResourceDto.class));
    }

    @Test
    void createNewResource_MissingRequiredFields_ReturnsBadRequest() {
        ResourceDto invalidResource = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("")  // Title buit
                .description("Valid Description")
                .url("https://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.NONE)
                .build();

        webTestClient.post()
                .uri("/itachallenge/api/v1/resource/new")
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(invalidResource)
                .exchange()
                .expectStatus().isBadRequest();

        verify(resourceService, never()).createResource(any(ResourceDto.class));
    }

    @Test
    void getResourcesByChallengeId_ValidId_ReturnsResources() {

        UUID challengeId = UUID.randomUUID();
        ResourceDto mockResource = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("Test Resource")
                .description("Test Description")
                .url("http://test.com")
                .topic(Topic.COMPONENTS)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(List.of(challengeId))
                .associationType(AssociationType.ALLSAMETOPIC)
                .build();

        when(resourceService.getResourcesByChallengeId(challengeId))
                .thenReturn(Flux.just(mockResource));


        webTestClient.get()
                .uri("/itachallenge/api/v1/resource/challenge/" + challengeId) // Ruta completa
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(ResourceDto.class)
                .hasSize(1)
                .contains(mockResource);

        verify(resourceService, times(1)).getResourcesByChallengeId(challengeId);
    }

    @Test
    void getResourcesByChallengeId_InvalidId_ReturnsBadRequest() {

        webTestClient.get()
                .uri("/itachallenge/api/v1/resource/challenge/null") // Ruta completa con ID inválido
                .exchange()
                .expectStatus().isBadRequest();


        verify(resourceService, never()).getResourcesByChallengeId(any());
    }

    @Test
    void getResourcesByChallengeId_NoResources_ReturnsNotFoundWithMessage() {

        UUID challengeId = UUID.randomUUID();
        String errorMessage = "No resources found for challenge ID: " + challengeId;

        when(resourceService.getResourcesByChallengeId(challengeId))
                .thenReturn(Flux.error(new ResourceNotFoundException(errorMessage)));


        webTestClient.get()
                .uri("/itachallenge/api/v1/resource/challenge/" + challengeId)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody()
                .jsonPath("$.message").isEqualTo(errorMessage);

        verify(resourceService, times(1)).getResourcesByChallengeId(challengeId);
    }


}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/controller/ResourceControllerTest.java:ResourceControllerTest.<init>
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.LanguageDto;
import com.itachallenge.challenge.repository.ChallengeRepository;
import com.itachallenge.challenge.repository.ResourceRepository;
import com.itachallenge.challenge.repository.SolutionRepository;
import com.itachallenge.challenge.repository.TagRepository;
import com.itachallenge.challenge.service.LanguageServiceImpl;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.mongodb.core.convert.MappingMongoConverter;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import static org.mockito.Mockito.when;

@WebFluxTest(controllers = LanguageController.class)
@ExtendWith(SpringExtension.class)
@ExtendWith(MockitoExtension.class)
public class LanguageControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private LanguageServiceImpl languageService;

    @MockBean
    private ChallengeRepository challengeRepository;

    @MockBean
    private SolutionRepository solutionRepository;

    @MockBean
    private WebClient.Builder webClientBuilder;

    @MockBean
    private TagRepository tagRepository;

    @MockBean
    private ChallengeController challengeController;

    @MockBean
    private ResourceRepository resourceRepository;

    @MockBean
    private MappingMongoConverter mappingMongoConverter;

    @Test
    void getAllLanguages_LanguagesExist_LanguagesReturned() {
        // Arrange
        GenericResultDto<LanguageDto> expectedResult = new GenericResultDto<>();
        expectedResult.setInfo(0, 2, 2, new LanguageDto[]{new LanguageDto(), new LanguageDto()});

        when(languageService.getAllLanguages()).thenReturn(Mono.just(expectedResult));

        // Act & Assert
        webTestClient.get()
                .uri("/itachallenge/api/v1/languages/")
                .exchange()
                .expectStatus().isOk()
                .expectBody(GenericResultDto.class)
                .value(dto -> {
                    assert dto != null;
                    assert dto.getCount() == 2;
                    assert dto.getResults() != null;
                    assert dto.getResults().length == 2;
                });
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/controller/LanguageControllerTest.java:LanguageControllerTest.<init>
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.TagDto;
import com.itachallenge.challenge.repository.*;
import com.itachallenge.challenge.service.ITagService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cloud.client.discovery.DiscoveryClient;
import org.springframework.data.mongodb.core.convert.MappingMongoConverter;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.UUID;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@WebFluxTest(controllers = TagController.class)
@ExtendWith(SpringExtension.class)
@ActiveProfiles("test")
public class TagControllerTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private ITagService tagService;

    @MockBean
    private DiscoveryClient discoveryClient;

    @MockBean
    private ChallengeRepository challengeRepository;

    @MockBean
    private SolutionRepository solutionRepository;

    @MockBean
    private WebClient.Builder webClientBuilder;

    @MockBean
    private TagRepository tagRepository;

    @MockBean
    private ChallengeController challengeController;

    @MockBean
    private FavoriteController favoriteController;

    @MockBean
    private ResourceRepository resourceRepository;

    @MockBean
    private MappingMongoConverter mappingMongoConverter;

    @MockBean
    private ChallengeSolvedController challengeSolvedController;

    @MockBean
    private LanguageRepository languageRepository;

    @Test
    void testGetTagsByLanguageId_WhenTagsExist_ReturnsOk() {
        UUID languageId = UUID.randomUUID();

        TagDto tag1 = new TagDto(UUID.randomUUID(), "Callbacks", "Description 1", languageId);
        TagDto tag2 = new TagDto(UUID.randomUUID(), "Promises", "Description 2", languageId);

        TagDto[] tagArray = new TagDto[]{tag1, tag2};
        GenericResultDto<TagDto> resultDto = new GenericResultDto<>();
        resultDto.setInfo(0, 2, 2, tagArray);

        when(tagService.getTagsByLanguageId(languageId)).thenReturn(Mono.just(resultDto));

        webTestClient.get()
                .uri("/itachallenge/api/v1/tags/" + languageId)
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.results.length()").isEqualTo(2)
                .jsonPath("$.results[0].tag_name").isEqualTo("Callbacks")
                .jsonPath("$.results[1].tag_name").isEqualTo("Promises");

        verify(tagService).getTagsByLanguageId(languageId);
    }

    @Test
    void testGetTagsByLanguageId_WhenNoTagsExist_Returns404() {
        UUID languageId = UUID.randomUUID();

        when(tagService.getTagsByLanguageId(languageId)).thenReturn(Mono.empty());

        webTestClient.get()
                .uri("/itachallenge/api/v1/tags/" + languageId)
                .exchange()
                .expectStatus().isNotFound();

        verify(tagService).getTagsByLanguageId(languageId);
    }

    @Test
    void testGetTagsByLanguageId_WhenErrorOccurs_Returns500() {
        UUID languageId = UUID.randomUUID();

        when(tagService.getTagsByLanguageId(languageId))
                .thenReturn(Mono.error(new RuntimeException("DB error")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/tags/" + languageId)
                .exchange()
                .expectStatus().isEqualTo(HttpStatus.INTERNAL_SERVER_ERROR);

        verify(tagService).getTagsByLanguageId(languageId);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/controller/TagControllerTest.java:TagControllerTest.<init>
package com.itachallenge.challenge.controller;

import com.itachallenge.challenge.dto.MessageDto;
import com.itachallenge.challenge.exception.ChallengeNotFoundException;
import com.itachallenge.challenge.service.IChallengeService;
import com.itachallenge.challenge.service.IChallengeJwtFacade;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;

import java.util.UUID;

import static org.junit.Assert.assertNotNull;
import static org.mockito.Mockito.*;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureWebTestClient
@ActiveProfiles("test")
class ChallengeControllerErrorTest {

    @Autowired
    private WebTestClient webTestClient;

    @MockBean
    private IChallengeService challengeService;

    @MockBean
    private IChallengeJwtFacade challengeJwtFacade;

    @Test
    void getRelatedChallenges_NotFound_Returns404() {
        String uuid = UUID.randomUUID().toString();

        when(challengeService.getRelatedChallenges(uuid))
                .thenReturn(Mono.error(new ChallengeNotFoundException("Challenge not found")));

        webTestClient.get()
                .uri("/itachallenge/api/v1/challenge/challenges/{challengeId}/related", uuid)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody(MessageDto.class)
                .consumeWith(response -> assertNotNull(response.getResponseBody()));
    }

    @Test
    void deleteOneChallenge_notFound() {
        String id = "non_existing_id";

        when(challengeService.deleteChallengeById(id))
                .thenReturn(Mono.error(
                        new ChallengeNotFoundException(String.format("Challenge with id: %s not found", id))));

        webTestClient.delete()
                .uri("/itachallenge/api/v1/challenge/challenges/" + id)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody()
                .jsonPath("$.message")
                .isEqualTo("Challenge with id: non_existing_id not found");
    }

    @Test
    void addChallengeToBookmarks_ChallengeNotFound_Returns404() {
        String challengeId = "nonExisting_challengeId";
        String userId = "existing_userId";
        String authHeader = "validAuthHeader";

        String errorMessage = "ErrorMessage";

        when(challengeService.addChallengeToBookmarks(challengeId, userId)).thenReturn(Mono.error(new ChallengeNotFoundException(errorMessage)));
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);

        webTestClient.post()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(1)).addChallengeToBookmarks(challengeId, userId);
    }

    @Test
    void removeChallengeFromBookmarks_ChallengeNotFound_Returns404() {
        String challengeId = "nonExisting_challengeId";
        String userId = "existing_userId";
        String authHeader = "validAuthHeader";

        String errorMessage = "ErrorMessage";

        when(challengeService.removeChallengeFromBookmarks(challengeId, userId)).thenReturn(Mono.error(new ChallengeNotFoundException(errorMessage)));
        when(challengeJwtFacade.getUserUuIdFromAuthenticationHeader(authHeader)).thenReturn(userId);

        webTestClient.delete()
                .uri("/itachallenge/api/v1/challenge/challenges/" + challengeId + "/bookmarks")
                .header("Authorization", authHeader)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody(MessageDto.class)
                .value(messageDto -> Assertions.assertEquals(errorMessage, messageDto.getMessage()));

        verify(challengeService, times(1)).removeChallengeFromBookmarks(challengeId, userId);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/controller/ChallengeControllerErrorTest.java:ChallengeControllerErrorTest.<init>
package com.itachallenge.challenge.controller.submission;

import com.itachallenge.challenge.dto.submission.SubmissionActionRequestDto;
import com.itachallenge.challenge.dto.submission.SubmissionActionResponseDto;
import com.itachallenge.challenge.dto.submission.SubmissionDto;
import com.itachallenge.challenge.exception.BadUUIDException;
import com.itachallenge.common.exception.GlobalExceptionHandler;
import com.itachallenge.submission.enums.SubmissionAction;
import com.itachallenge.submission.exception.UnmodifiableSubmissionException;
import com.itachallenge.submission.service.SubmissionService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;
import static org.springframework.http.MediaType.APPLICATION_JSON;

@ExtendWith(MockitoExtension.class)
class SubmissionControllerTest {

    @Mock
    SubmissionService submissionService;

    @InjectMocks
    SubmissionController submissionController;

    private WebTestClient client() {
        return WebTestClient.bindToController(submissionController)
                .controllerAdvice(new GlobalExceptionHandler())
                .build();
    }

    @Test
    void getAllSubmissions_returnsSubmissions() {
        String userId = UUID.randomUUID().toString();

        SubmissionDto s1 = SubmissionDto.builder()
                .userId(userId)
                .challengeId("d43a1a4d-ee8f-432d-8f9c-68eda2547dae")
                .languageId("409c9fe8-74de-4db3-81a1-a55280cf92ef")
                .submissionText("This is the submitted solution")
                .status("IN_PROGRESS")
                .build();

        SubmissionDto s2 = SubmissionDto.builder()
                .userId(userId)
                .challengeId("b5c06903-f27b-4057-8220-ad9d957cdce4")
                .languageId("09fabe32-7362-4bfb-ac05-b7bf854c6e0f")
                .submissionText("This is the submitted solution")
                .status("IN_PROGRESS")
                .build();

        when(submissionService.getAllSubmissionsByUser(userId))
                .thenReturn(Flux.just(s1, s2));

        client().get()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", userId)
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(SubmissionDto.class)
                .hasSize(2)
                .value(list -> {
                    assertEquals(s1.getChallengeId(), list.get(0).getChallengeId());
                    assertEquals(s2.getChallengeId(), list.get(1).getChallengeId());
                });

        verify(submissionService).getAllSubmissionsByUser(userId);
    }

    @Test
    void getAllSubmissions_returns200WithEmptyArrayWhenNoSubmissions() {
        String userId = UUID.randomUUID().toString();

        when(submissionService.getAllSubmissionsByUser(userId))
                .thenReturn(Flux.empty());

        client().get()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", userId)
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(SubmissionDto.class)
                .hasSize(0);

        verify(submissionService).getAllSubmissionsByUser(userId);
    }
    @Test
    void getAllSubmissions_returns400WhenUserIdIsMalformed_byService() {
        String badId = "not-a-uuid";
        when(submissionService.getAllSubmissionsByUser(badId))
                .thenReturn(Flux.error(new BadUUIDException("Invalid UUID")));

        client().get()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", badId)
                .exchange()
                .expectStatus().isBadRequest();

        verify(submissionService).getAllSubmissionsByUser(badId);
    }

    @Test
    void getAllSubmissions_returns500IfUnexpectedError() {
        String userId = UUID.randomUUID().toString();

        when(submissionService.getAllSubmissionsByUser(userId))
                .thenReturn(Flux.error(new RuntimeException("Boom")));

        client().get()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", userId)
                .exchange()
                .expectStatus().is5xxServerError();

        verify(submissionService).getAllSubmissionsByUser(userId);
    }
    @Test
    void postSubmission_returns200_whenServiceSucceeds() {
        String userId = UUID.randomUUID().toString();

        SubmissionActionRequestDto request = SubmissionActionRequestDto.builder()
                .challengeId(UUID.randomUUID())
                .languageId(UUID.randomUUID())
                .action(SubmissionAction.SAVE)
                .submissionText("draft text")
                .build();

        SubmissionActionResponseDto response = SubmissionActionResponseDto.builder()
                .submissionText("draft text")
                .isSolved(false)
                .timesSolved(0)
                .status("IN_PROGRESS")
                .build();

        when(submissionService.processSubmissionAction(eq(userId), any(SubmissionActionRequestDto.class)))
                .thenReturn(Mono.just(response));

        client().post()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", userId)
                .contentType(APPLICATION_JSON)
                .accept(APPLICATION_JSON)
                .bodyValue(request)
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.submission_text").isEqualTo("draft text")
                .jsonPath("$.status").isEqualTo("IN_PROGRESS");

        verify(submissionService).processSubmissionAction(eq(userId), any(SubmissionActionRequestDto.class));
    }

    @Test
    void postSubmission_returns400_whenRequestIsInvalid() {
        String userId = UUID.randomUUID().toString();

        SubmissionActionRequestDto request = SubmissionActionRequestDto.builder()
                .challengeId(null)
                .languageId(UUID.randomUUID())
                .action(SubmissionAction.SAVE)
                .submissionText("draft text")
                .build();

        client().post()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", userId)
                .contentType(APPLICATION_JSON)
                .accept(APPLICATION_JSON)
                .bodyValue(request)
                .exchange()
                .expectStatus().isBadRequest();

        verify(submissionService, never())
                .processSubmissionAction(any(), any());
    }


    @Test
    void postSubmission_returns409_whenSubmissionIsUnmodifiable() {
        String userId = UUID.randomUUID().toString();

        SubmissionActionRequestDto request = SubmissionActionRequestDto.builder()
                .challengeId(UUID.randomUUID())
                .languageId(UUID.randomUUID())
                .action(SubmissionAction.SAVE)
                .submissionText("draft text")
                .build();


        when(submissionService.processSubmissionAction(eq(userId), any(SubmissionActionRequestDto.class)))
                .thenReturn(Mono.error(new UnmodifiableSubmissionException("Submission already completed")));

        client().post()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", userId)
                .contentType(APPLICATION_JSON)
                .accept(APPLICATION_JSON)
                .bodyValue(request)
                .exchange()
                .expectStatus().isEqualTo(409);

        verify(submissionService).processSubmissionAction(eq(userId), any(SubmissionActionRequestDto.class));
    }

    @Test
    void postSubmission_returns400_whenBodyContainsInvalidUUID() {
        String userId = UUID.randomUUID().toString();

        String invalidJson = """
        {
          "uuid_challenge": "not-a-uuid",
          "uuid_language": "also-not-a-uuid",
          "action": "SAVE",
          "submission_text": "draft text"
        }
        """;

        client().post()
                .uri("/itachallenge/api/v1/users/{userId}/submissions", userId)
                .header("Content-Type", "application/json")
                .bodyValue(invalidJson)
                .exchange()
                .expectStatus().isBadRequest();

        verify(submissionService, never())
                .processSubmissionAction(any(), any());
    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/controller/submission/SubmissionControllerTest.java:SubmissionControllerTest.<init>
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.controller.ChallengeController;
import com.itachallenge.challenge.document.TagDocument;
import com.itachallenge.challenge.service.IUserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import static org.junit.Assert.*;

@DataMongoTest
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_METHOD)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class TagRepositoryTest {

    @Container
    static MongoDBContainer container = new MongoDBContainer("mongo")
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        System.out.println("container url: {}" + container.getReplicaSetUrl("languages"));
        System.out.println("container host/port: {}/{}" + container.getHost() + " - " + container.getFirstMappedPort());

        registry.add("spring.data.mongodb.uri", () -> container.getReplicaSetUrl("tags"));
    }

    @Autowired
    private TagRepository tagRepository;
    @MockBean
    private ChallengeController challengeController;
    @MockBean
    private IUserService userService;

    UUID uuid_1 = UUID.fromString("8ecbfe54-fec8-11ed-be56-0242ac120002");
    UUID uuid_2 = UUID.fromString("26977eee-89f8-11ec-a8a3-0242ac120003");

    UUID uuidLang1, uuidLang2;

    @BeforeEach
    public void setUp() {

        uuidLang1 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        uuidLang2 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");

        UUID uuidTag1 = UUID.randomUUID();
        UUID uuidTag2 = UUID.randomUUID();

        tagRepository.deleteAll().block();

        TagDocument tag1 = new TagDocument(uuidTag1, "POO", "Programació orientada a objectes", uuidLang1);
        TagDocument tag2 = new TagDocument(uuidTag2, "Bucles", "Bucles 'for' y 'while'", uuidLang2);

        Set<TagDocument> tagSet = new HashSet<>(Arrays.asList(tag1, tag2));

        tagRepository.saveAll(Flux.just(tag1, tag2)).blockLast();
    }

    @DisplayName("Repository not null Test")
    @Test
    void testDB() {

        assertNotNull(tagRepository);

    }

    @DisplayName("Find All Test")
    @Test
    void findAllTagsTest() {

        Flux<TagDocument> tags = tagRepository.findAll();

        StepVerifier.create(tags)
                .expectNextCount(2)
                .verifyComplete();
    }

    @DisplayName("Find by Language ID")
    @Test
    void findByIdLanguageTest() {
        Flux<TagDocument> tagsByLanguage = tagRepository.findByLanguageId(uuidLang1);

        StepVerifier.create(tagsByLanguage)
                .expectNextMatches(tag -> tag.getTagName().equals("POO") && tag.getLanguageId().equals(uuidLang1))
                .verifyComplete();
    }


}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/repository/TagRepositoryTest.java:TagRepositoryTest.<init>
// Node: TestInstance
// Node: DirtiesContext
// Node: withStartupTimeout
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.controller.ChallengeController;
import com.itachallenge.challenge.document.*;
import com.itachallenge.challenge.service.IUserService;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import java.time.Duration;
import java.util.*;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.springframework.test.util.AssertionErrors.fail;

@DataMongoTest
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_METHOD)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class LanguageRepositoryTest {

    @Container
    static MongoDBContainer container = new MongoDBContainer("mongo")
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        System.out.println("container url: {}" + container.getReplicaSetUrl("languages"));
        System.out.println("container host/port: {}/{}" + container.getHost() + " - " + container.getFirstMappedPort());

        registry.add("spring.data.mongodb.uri", () -> container.getReplicaSetUrl("languages"));
    }

    @Autowired
    private LanguageRepository languageRepository;
    @MockBean
    private ChallengeController challengeController;
    @MockBean
    private IUserService userService;

    UUID uuid_1 = UUID.fromString("8ecbfe54-fec8-11ed-be56-0242ac120002");
    UUID uuid_2 = UUID.fromString("26977eee-89f8-11ec-a8a3-0242ac120003");

    UUID uuidLang1, uuidLang2;

    @BeforeEach
    public void setUp() {

        uuidLang1 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        uuidLang2 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");

        languageRepository.deleteAll().block();

        LanguageDocument language = new LanguageDocument(uuidLang1, "Java", "https://image-default.com/java.png");
        LanguageDocument language2 = new LanguageDocument(uuidLang2, "Python", "\"https://image-default.com/python.png");
        Set<LanguageDocument> languageSet = new HashSet<>(Arrays.asList(language2, language));

        languageRepository.saveAll(Flux.just(language, language2)).blockLast();
    }

    @DisplayName("Repository not null Test")
    @Test
    void testDB() {

        assertNotNull(languageRepository);

    }

    @DisplayName("Find All Test")
    @Test
    void findAllTest() {

        Flux<LanguageDocument> languages = languageRepository.findAll();

        StepVerifier.create(languages)
                .expectNextCount(2)
                .verifyComplete();
    }

    @DisplayName("Exists by Id Test")
    @Test
    void existsByIdTest() {
        Boolean exists = languageRepository.existsById(uuidLang1).block();
        assertEquals(exists, true);
    }

    @DisplayName("Find by Id Test")
    @Test
    void findByIdTest() {

        Mono<LanguageDocument> firstLanguage = languageRepository.findByIdLanguage(uuidLang1);
        firstLanguage.blockOptional().ifPresentOrElse(
                u -> assertEquals(u.getIdLanguage(), uuidLang1),
                () -> fail("Language with id " + uuidLang1 + " not found"));

        Mono<LanguageDocument> secondLanguage = languageRepository.findByIdLanguage(uuidLang2);
        secondLanguage.blockOptional().ifPresentOrElse(
                u -> assertEquals(u.getIdLanguage(), uuidLang2),
                () -> fail("Language with id " + uuidLang2 + " not found"));
    }

    @DisplayName("Delete by Id Test")
    @Test
    void deleteByIdTest() {

        Mono<LanguageDocument> firstLanguage = languageRepository.findByIdLanguage(uuidLang1);
        firstLanguage.blockOptional().ifPresentOrElse(
                u -> {
                    Mono<Void> deletion = languageRepository.deleteByIdLanguage(uuidLang1);
                    StepVerifier.create(deletion)
                            .expectComplete()
                            .verify();
                },
                () -> fail("Language with id " + uuidLang1 + " not found")
        );

        Mono<LanguageDocument> secondLanguage = languageRepository.findByIdLanguage(uuidLang2);
        secondLanguage.blockOptional().ifPresentOrElse(
                u -> {
                    Mono<Void> deletion = languageRepository.deleteByIdLanguage(uuidLang2);
                    StepVerifier.create(deletion)
                            .expectComplete()
                            .verify();
                },
                () -> fail("Language with id " + uuidLang2 + " not found")
        );
    }

    @DisplayName("Find by language name")
    @Test
    void findFirstByLanguageName_test() {
        LanguageDocument language = languageRepository.findFirstByLanguageName("Java").block();

        assert language != null;
        Assertions.assertEquals(language.getIdLanguage(), UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f"));
    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/repository/LanguageRepositoryTest.java:LanguageRepositoryTest.<init>
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.controller.ChallengeController;
import com.itachallenge.challenge.document.SolutionDocument;
import com.itachallenge.challenge.service.IUserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import java.time.Duration;
import java.util.UUID;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.springframework.test.util.AssertionErrors.fail;

@DataMongoTest
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_METHOD)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class SolutionRepositoryTest {


    @Container
    static MongoDBContainer container = new MongoDBContainer("mongo")
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        System.out.println("container url: {}" + container.getReplicaSetUrl("solutions"));
        System.out.println("container host/port: {}/{}" + container.getHost() + " - " + container.getFirstMappedPort());

        registry.add("spring.data.mongodb.uri", () -> container.getReplicaSetUrl("solutions"));
    }

    @Autowired
    private SolutionRepository solutionRepository;
    @MockBean
    private ChallengeController challengeController;
    @MockBean
    private IUserService userService;

    UUID uuid_1 = UUID.fromString("8ecbfe54-fec8-11ed-be56-0242ac120002");
    UUID uuid_2 = UUID.fromString("26977eee-89f8-11ec-a8a3-0242ac120003");

    @BeforeEach
    void setUp(){

        UUID uuidLang1 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        UUID uuidLang2 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");

        solutionRepository.deleteAll().block();

        SolutionDocument solution = new SolutionDocument(uuid_1, "Solution Text 1", uuidLang1);
        SolutionDocument solution2 = new SolutionDocument(uuid_2, "Solution Text 2", uuidLang2);

        solutionRepository.saveAll(Flux.just(solution, solution2)).blockLast();

    }

    @DisplayName("Repository not null Test")
    @Test
    void testDB() {

        assertNotNull(solutionRepository);

    }

    @DisplayName("Find All Test")
    @Test
    void findAllTest() {

        Flux<SolutionDocument> solutions = solutionRepository.findAll();

        StepVerifier.create(solutions)
                .expectNextCount(2)
                .verifyComplete();
    }

    @DisplayName("Exists by UUID Test")
    @Test
    void existsByUuidTest() {
        Boolean exists = solutionRepository.existsByUuid(uuid_1).block();
        assertEquals(true, exists);
    }

    @DisplayName("Find by UUID Test")
    @Test
    void findByUuidTest() {

        Mono<SolutionDocument> firstSolution = solutionRepository.findByUuid(uuid_1);
        firstSolution.blockOptional().ifPresentOrElse(
                u -> assertEquals(u.getUuid(), uuid_1),
                () -> fail("Solution not found: " + uuid_1));

        Mono<SolutionDocument> secondSolution = solutionRepository.findByUuid(uuid_2);
        secondSolution.blockOptional().ifPresentOrElse(
                u -> assertEquals(u.getUuid(), uuid_2),
                () -> fail("Solution not found: " + uuid_2));
    }

    @DisplayName("Delete by UUID Test")
    @Test
    void deleteByUuidTest() {

        Mono<SolutionDocument> firstSolution = solutionRepository.findByUuid(uuid_1);
        firstSolution.blockOptional().ifPresentOrElse(
                u -> {
                    Mono<Void> deletion = solutionRepository.deleteByUuid(uuid_1);
                    StepVerifier.create(deletion)
                            .expectComplete()
                            .verify();
                },
                () -> fail("Solution to delete not found: " + uuid_1)
        );

        Mono<SolutionDocument> secondSolution = solutionRepository.findByUuid(uuid_2);
        secondSolution.blockOptional().ifPresentOrElse(
                u -> {
                    Mono<Void> deletion = solutionRepository.deleteByUuid(uuid_2);
                    StepVerifier.create(deletion)
                            .expectComplete()
                            .verify();
                },
                () -> fail("Solution to delete not found: " + uuid_2)
        );
    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/repository/SolutionRepositoryTest.java:SolutionRepositoryTest.<init>
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.controller.ChallengeController;
import com.itachallenge.challenge.document.ResourceDocument;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.service.IUserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestInstance;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.util.List;
import java.util.UUID;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

@DataMongoTest
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_METHOD)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)

class ResourceRepositoryTest {

    @Container
    static MongoDBContainer container = new MongoDBContainer("mongo")
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", () -> container.getReplicaSetUrl("resources"));
    }

    @Autowired
    private ResourceRepository resourceRepository;
    @MockBean
    private ChallengeController challengeController;
    @MockBean
    private IUserService userService;

    UUID uuid1 = UUID.fromString("8ecbfe54-fec8-11ed-be56-0242ac120002");
    UUID uuid2 = UUID.fromString("26977eee-89f8-11ec-a8a3-0242ac120003");

    @BeforeEach
    public void setUp() {
        resourceRepository.deleteAll().block();

        ResourceDocument resource1 = ResourceDocument.builder()
                .resourceId(uuid1)
                .title("Title1")
                .description("Description1")
                .url("http://exemple.com/resource1")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();

        ResourceDocument resource2 = ResourceDocument.builder()
                .resourceId(uuid2)
                .title("Title2")
                .description("Description2")
                .url("http://exemple.com/resource2")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();

        resourceRepository.saveAll(Flux.just(resource1, resource2)).blockLast();
    }

    @DisplayName("Repository not null Test")
    @Test
    void testDB() {
        assertNotNull(resourceRepository);
    }

    @DisplayName("Exists by UUID Test")
    @Test
    void existsByResourceIdTest() {
        Boolean exists = resourceRepository.existsByResourceId(uuid1).block();
        assertEquals(true, exists);
    }

    @DisplayName("Find by UUID Test")
    @Test
    void findByResourceIdTest() {
        Mono<ResourceDocument> resource = resourceRepository.findByResourceId(uuid1);
        StepVerifier.create(resource)
                .assertNext(r -> assertEquals(uuid1, r.getResourceId()))
                .verifyComplete();
    }

    @DisplayName("Find by Topic Test")
    @Test
    void findByTopicTest() {
        Flux<ResourceDocument> resources = resourceRepository.findByTopic(Topic.DEBUGGING);

        StepVerifier.create(resources)
                .expectNextMatches(resource -> resource.getTopic().equals(Topic.DEBUGGING))
                .thenCancel()
                .verify();
    }


    @DisplayName("Find by Content Type Test")
    @Test
    void findByContentTypeTest() {
        Flux<ResourceDocument> resources = resourceRepository.findByContentType(ResourceContentType.BLOG);

        StepVerifier.create(resources)
                .expectNextMatches(resource -> resource.getContentType() == ResourceContentType.BLOG)
                .thenCancel()
                .verify();
    }


    @DisplayName("Delete by UUID Test")
    @Test
    void deleteByResourceIdTest() {
        Mono<Void> deletion = resourceRepository.deleteByResourceId(uuid1);
        StepVerifier.create(deletion)
                .expectComplete()
                .verify();

        Mono<ResourceDocument> resource = resourceRepository.findByResourceId(uuid1);
        StepVerifier.create(resource)
                .expectNextCount(0)
                .verifyComplete();
    }

    @DisplayName("Count Resources Test")
    @Test
    void countResourcesTest() {
        Mono<Long> count = resourceRepository.count();
        StepVerifier.create(count)
                .expectNext(2L)
                .verifyComplete();
    }

    @DisplayName("Save Resource Test")
    @Test
    void saveResourceTest() {
        ResourceDocument newResource = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("New Resource")
                .description("A new resource for testing")
                .url("http://exemple.com/newresource")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();


        Mono<ResourceDocument> savedResource = resourceRepository.save(newResource);


        StepVerifier.create(savedResource)
                .assertNext(resource -> {
                    assertNotNull(resource.getResourceId());
                    assertEquals("New Resource", resource.getTitle());
                    assertEquals("A new resource for testing", resource.getDescription());
                    assertEquals("http://exemple.com/newresource", resource.getUrl());
                    assertEquals(Topic.DEBUGGING, resource.getTopic());
                    assertEquals(ResourceContentType.VIDEO, resource.getContentType());
                })
                .verifyComplete();
    }

    @DisplayName("Save Multiple Resources Test")
    @Test
    void saveMultipleResourcesTest() {

        ResourceDocument resource1 = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("Resource 1")
                .description("Description 1")
                .url("http://exemple.com/resource1")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();

        ResourceDocument resource2 = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("Resource 2")
                .description("Description 2")
                .url("http://exemple.com/resource2")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();

        Flux<ResourceDocument> savedResources = resourceRepository.saveAll(Flux.just(resource1, resource2));
        StepVerifier.create(savedResources)
                .expectNextCount(2)
                .verifyComplete();
    }

    @DisplayName("Find by Non-Existing Resource ID Test")
    @Test
    void findByNonExistingResourceIdTest() {
        Mono<ResourceDocument> resource = resourceRepository.findByResourceId(UUID.randomUUID());
        StepVerifier.create(resource)
                .expectNextCount(0)
                .verifyComplete();
    }

    @DisplayName("Count Resources After Save and Delete Test")
    @Test
    void countResourcesAfterSaveAndDeleteTest() {
        ResourceDocument resource = ResourceDocument.builder()
                .resourceId(UUID.randomUUID())
                .title("Test Resource for Count")
                .description("A resource to check count after deletion")
                .url("http://exemple.com/testresource")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();

        resourceRepository.save(resource).block();
        Mono<Long> countAfterSave = resourceRepository.count();
        StepVerifier.create(countAfterSave)
                .expectNext(3L)
                .verifyComplete();

        resourceRepository.deleteByResourceId(resource.getResourceId()).block();

        Mono<Long> countAfterDelete = resourceRepository.count();
        StepVerifier.create(countAfterDelete)
                .expectNext(2L)
                .verifyComplete();
    }

    @DisplayName("Delete All Resources Test")
    @Test
    void deleteAllResourcesTest() {
        Mono<Void> deletion = resourceRepository.deleteAll();
        StepVerifier.create(deletion)
                .expectComplete()
                .verify();

        Mono<Long> count = resourceRepository.count();
        StepVerifier.create(count)
                .expectNext(0L)
                .verifyComplete();
    }


    @Test
    void findByChallengeIdsContaining_WhenChallengeIdExists_ReturnsResources() {

        UUID targetChallengeId = UUID.fromString("8ecbfe54-fec8-11ed-be56-0242ac120002");


        ResourceDocument resourceWithTargetChallenge = ResourceDocument.builder()
                .resourceId(uuid1)
                .title("Title1")
                .description("Description1")
                .url("http://example.com/resource1")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(targetChallengeId))
                .build();

        ResourceDocument resourceWithoutTargetChallenge = ResourceDocument.builder()
                .resourceId(uuid2)
                .title("Title2")
                .description("Description2")
                .url("http://example.com/resource2")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .build();


        resourceRepository.deleteAll().block();
        resourceRepository.saveAll(Flux.just(resourceWithTargetChallenge, resourceWithoutTargetChallenge)).blockLast();


        Flux<ResourceDocument> result = resourceRepository.findByChallengeIdsContaining(targetChallengeId);


        StepVerifier.create(result)
                .expectNextMatches(resource ->
                        resource.getChallengeIds().contains(targetChallengeId) &&
                                resource.getResourceId().equals(uuid1)
                )
                .verifyComplete();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/repository/ResourceRepositoryTest.java:ResourceRepositoryTest.<init>
package com.itachallenge.challenge.repository;

import com.itachallenge.challenge.controller.ChallengeController;
import com.itachallenge.challenge.document.*;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.service.IUserService;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.*;

import static org.junit.Assert.*;
import static org.springframework.test.util.AssertionErrors.fail;

@DataMongoTest
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_METHOD)
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
class ChallengeRepositoryTest {

    @Container
    static MongoDBContainer container = new MongoDBContainer("mongo")
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        System.out.println("container url: {}" + container.getReplicaSetUrl("challenges"));
        System.out.println("container host/port: {}/{}" + container.getHost() + " - " + container.getFirstMappedPort());
        registry.add("spring.data.mongodb.uri", () -> container.getReplicaSetUrl("challenges"));
    }

    @Autowired
    private ChallengeRepository challengeRepository;
    @MockBean
    private ChallengeController challengeController;
    @MockBean
    private IUserService userService;


    UUID uuid_1 = UUID.fromString("8ecbfe54-fec8-11ed-be56-0242ac120002");
    UUID uuid_2 = UUID.fromString("26977eee-89f8-11ec-a8a3-0242ac120003");
    UUID uuid_3 = UUID.fromString("2f948de0-6f0c-4089-90b9-7f70a0812319");

    @BeforeEach
    void setUp() {

        UUID uuidLang1 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        UUID uuidLang2 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");
        UUID[] idsLanguages = new UUID[]{uuidLang1, uuidLang2};
        String[] languageNames = new String[]{"name1", "name2"};
        List<UUID> tags = List.of(UUID.randomUUID());
        LanguageDocument language1 = new LanguageDocument(idsLanguages[0], languageNames[0], "https://image-default.com/default.png");
        LanguageDocument language2 = new LanguageDocument(idsLanguages[1], languageNames[1], "https://image-default.com/default.png");
        Set<LanguageDocument> languageSet = Set.of(language1, language2);
        Set<LanguageDocument> languageSet3 = Set.of(language1);

        String description = "Description";

        List<UUID> solutionList = List.of(UUID.randomUUID(),UUID.randomUUID());

        List<UUID> favoritedByList = List.of(UUID.randomUUID(),UUID.randomUUID());

        List<UUID> solvedByList = List.of(UUID.randomUUID(),UUID.randomUUID());

        DetailDocument detail = new DetailDocument(description);

        String title1 = "Loops";
        String title2 = "Challenge 2";
        String title3 = "Challenge 3";

        ChallengeDocument challenge = new ChallengeDocument
                (uuid_1, title1, "MEDIUM", LocalDateTime.now(), detail, languageSet, solutionList,
                        Topic.DEBUGGING, 5, 3, 4, tags);
        ChallengeDocument challenge2 = new ChallengeDocument
                (uuid_2, title2, "EASY", LocalDateTime.now(), detail, languageSet, solutionList,
                        Topic.LISTS, 10, 2, 7, tags);
        ChallengeDocument challenge3 = new ChallengeDocument
                (uuid_3, title3, "HARD", LocalDateTime.now(), detail, languageSet3, solutionList,
                        Topic.COMPONENTS, 15, 1, 9, tags);

        challengeRepository.saveAll(Flux.just(challenge, challenge2, challenge3)).blockLast();

        challengeRepository.count().block();
    }

    @DisplayName("Repository not null Test")
    @Test
    void testDB() {
        assertNotNull(challengeRepository);
    }

    @DisplayName("Find Challenges for a Page")
    @Test
    void findAllTest() {

        Flux<ChallengeDocument> challengesOffset0Limit1 = challengeRepository.findAllByUuidNotNullExcludingTestingValues().skip(0).take(1);
        StepVerifier.create(challengesOffset0Limit1)
                .expectNextCount(1)
                .verifyComplete();

        Flux<ChallengeDocument> challengesOffset0Limit2 = challengeRepository.findAllByUuidNotNullExcludingTestingValues().skip(0).take(2);
        StepVerifier.create(challengesOffset0Limit2)
                .expectNextCount(2)
                .verifyComplete();

        Flux<ChallengeDocument> challengesOffset1Limit1 = challengeRepository.findAllByUuidNotNullExcludingTestingValues().skip(1).take(1);
        StepVerifier.create(challengesOffset1Limit1)
                .expectNextCount(1)
                .verifyComplete();

        Flux<ChallengeDocument> challengesOffset1Limit2 = challengeRepository.findAllByUuidNotNullExcludingTestingValues().skip(2).take(2);
        StepVerifier.create(challengesOffset1Limit2)
                .expectNextCount(1)
                .verifyComplete();
    }

    @DisplayName("Exists by UUID Test")
    @Test
    void existsByUuidTest() {
        Boolean exists = challengeRepository.existsByUuid(uuid_1).block();
        assertEquals(true, exists);
    }

    @DisplayName("Find by UUID Test")
    @Test
    void findByUuidTest() {

        Mono<ChallengeDocument> firstChallenge = challengeRepository.findByUuid(uuid_1);
        firstChallenge.blockOptional().ifPresentOrElse(
                u -> assertEquals(u.getUuid(), uuid_1),
                () -> fail("Challenge not found: " + uuid_1));

        Mono<ChallengeDocument> secondChallenge = challengeRepository.findByUuid(uuid_2);
        secondChallenge.blockOptional().ifPresentOrElse(
                u -> assertEquals(u.getUuid(), uuid_2),
                () -> fail("Challenge not found: " + uuid_2));
    }

    @DisplayName("Delete by UUID Test")
    @Test
    void deleteByUuidTest() {

        Mono<ChallengeDocument> firstChallenge = challengeRepository.findByUuid(uuid_1);
        firstChallenge.blockOptional().ifPresentOrElse(
                u -> {
                    Mono<Void> deletion = challengeRepository.deleteByUuid(uuid_1);
                    StepVerifier.create(deletion)
                            .expectComplete()
                            .verify();
                },
                () -> fail("Challenge to delete not found: " + uuid_1)
        );

        Mono<ChallengeDocument> secondChallenge = challengeRepository.findByUuid(uuid_2);
        secondChallenge.blockOptional().ifPresentOrElse(
                u -> {
                    Mono<Void> deletion = challengeRepository.deleteByUuid(uuid_2);
                    StepVerifier.create(deletion)
                            .expectComplete()
                            .verify();
                },
                () -> fail("Challenge to delete not found: " + uuid_2)
        );
    }

    @DisplayName("Find by Level and LanguagesId - Get one Test")
    @Test
    void findAllChallengeByLanguagesAndLevelGetOne() {
        // Arrange
        UUID uuidLang1 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");

        Flux<ChallengeDocument> filteredChallenges1 = challengeRepository
                .findByLevelAndLanguages_IdLanguage("MEDIUM", uuidLang1);
        Flux<ChallengeDocument> filteredChallenges2 = challengeRepository
                .findByLevelAndLanguages_IdLanguage("EASY", uuidLang1);

        StepVerifier.create(filteredChallenges1)
                .expectNextCount(1)
                .verifyComplete();
        StepVerifier.create(filteredChallenges2)
                .expectNextCount(1)
                .verifyComplete();
    }

    @DisplayName("Find by idLanguage Test")
    @Test
    void findByLanguages_idLanguage_test() {
        // Arrange
        UUID uuidLang1 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");
        UUID uuidLang2 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");

        Flux<ChallengeDocument> challengeFiltered1 = challengeRepository
                .findByLanguages_IdLanguage(uuidLang1);
        Flux<ChallengeDocument> challengeFiltered2 = challengeRepository
                .findByLanguages_IdLanguage(uuidLang2);

        StepVerifier.create(challengeFiltered1)
                .expectNextCount(2)
                .verifyComplete();
        StepVerifier.create(challengeFiltered2)
                .expectNextCount(3)
                .verifyComplete();
    }

    @DisplayName("Find by LanguageName Test")
    @Test
    void findByLanguages_LanguageName_test() {
        Flux<ChallengeDocument> findByNameClass = challengeRepository
                .findByLanguages_LanguageName("name1");

        StepVerifier.create(findByNameClass)
                .expectNextCount(3)
                .verifyComplete();
    }

    @DisplayName("Find by Level Flux Test")
    @Test
    void findByLevelFlux_test() {
        Flux<ChallengeDocument> filteredChallenges1 = challengeRepository
                .findByLevel("MEDIUM");
        Flux<ChallengeDocument> filteredChallenges2 = challengeRepository
                .findByLevel("EASY");

        StepVerifier.create(filteredChallenges1)
                .expectNextCount(1)
                .verifyComplete();
        StepVerifier.create(filteredChallenges2)
                .expectNextCount(1)
                .verifyComplete();
    }

    @DisplayName("Add solution to challenge Test")
    @Test
    void addSolutionToChallengeTest() {
        // Arrange
        UUID uuidLang1 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");
        UUID uuidLang2 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");

        Flux<ChallengeDocument> challengeFiltered1 = challengeRepository
                .findByLanguages_IdLanguage(uuidLang1);
        Flux<ChallengeDocument> challengeFiltered2 = challengeRepository
                .findByLanguages_IdLanguage(uuidLang2);

        StepVerifier.create(challengeFiltered1)
                .expectNextCount(2)
                .verifyComplete();
        StepVerifier.create(challengeFiltered2)
                .expectNextCount(3)
                .verifyComplete();

        // Act
        Mono<ChallengeDocument> challengeMono = challengeRepository.findByUuid(uuid_1);
        ChallengeDocument challengeDocument = challengeMono.block();
        List<UUID> solutions = challengeDocument.getSolutions();
        solutions.add(UUID.randomUUID());
        challengeDocument.setSolutions(solutions);
        Mono<ChallengeDocument> challengeDocumentMono = challengeRepository.save(challengeDocument);
        ChallengeDocument challengeDocumentSaved = challengeDocumentMono.block();

        // Assert
        Assertions.assertEquals(3, challengeDocumentSaved.getSolutions().size());
    }

    @DisplayName("Add solution to solutions Test")
    @Test
    void addSolutionToSolutionsTest() {
        // Arrange
        UUID uuidLang1 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");
        UUID uuidLang2 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");

        Flux<ChallengeDocument> challengeFiltered1 = challengeRepository
                .findByLanguages_IdLanguage(uuidLang1);
        Flux<ChallengeDocument> challengeFiltered2 = challengeRepository
                .findByLanguages_IdLanguage(uuidLang2);

        StepVerifier.create(challengeFiltered1)
                .expectNextCount(2)
                .verifyComplete();
        StepVerifier.create(challengeFiltered2)
                .expectNextCount(3)
                .verifyComplete();

        // Act
        Mono<ChallengeDocument> challengeMono = challengeRepository.findByUuid(uuid_1);
        ChallengeDocument challengeDocument = challengeMono.block();
        assert challengeDocument != null;
        List<UUID> solutions = challengeDocument.getSolutions();
        solutions.add(UUID.randomUUID());
        challengeDocument.setSolutions(solutions);
        Mono<ChallengeDocument> challengeDocumentMono = challengeRepository.save(challengeDocument);
        ChallengeDocument challengeDocumentSaved = challengeDocumentMono.block();

        // Assert
        assert challengeDocumentSaved != null;
        Assertions.assertEquals(3, challengeDocumentSaved.getSolutions().size());
    }

    @DisplayName("Exists challenge title Test, should return true")
    @Test
    void findByChallengeTitle_matchingTitle_test() {
        Boolean exists = challengeRepository.existsByChallengeTitle("loops").block(); // is case insensitive
        Assertions.assertNotNull(exists);
        Assertions.assertTrue(exists);
    }

    @DisplayName("Exists challenge title Test, should return false")
    @Test
    void findByChallengeTitle_nonMatchingTitle_test() {
        Boolean exists = challengeRepository.existsByChallengeTitle("non existing title").block(); // is case insensitive
        Assertions.assertNotNull(exists);
        Assertions.assertFalse(exists);
    }

    @DisplayName("Find by Detail Topic Test")
    @Test
    void findByDetailTopicTest() {
        Topic topic1 = Topic.DEBUGGING;

        Flux<ChallengeDocument> challengesWithTopic1 = challengeRepository.findByTopic(topic1);
        StepVerifier.create(challengesWithTopic1)
                .expectNextCount(1)
                .verifyComplete();


    }

}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/repository/ChallengeRepositoryTest.java:ChallengeRepositoryTest.<init>
package com.itachallenge.challenge.integration;

import com.itachallenge.challenge.config.dbchangelog.TestDatabaseInitializer;
import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoClients;
import com.mongodb.reactivestreams.client.MongoDatabase;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.reactivestreams.Publisher;
import org.reactivestreams.Subscriber;
import org.reactivestreams.Subscription;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.containers.wait.strategy.Wait;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
@Testcontainers
class MongockIntegrationTest {
    @Mock
    MongoDatabase mongoDatabase;

    @Container
    static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:latest")
            .waitingFor(Wait.forListeningPort());


    private final TestDatabaseInitializer testDatabaseInitializer;

    @Autowired
    public MongockIntegrationTest(TestDatabaseInitializer testDatabaseInitializer) {
        this.testDatabaseInitializer = testDatabaseInitializer;
    }

    @DynamicPropertySource
    static void setProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", mongoDBContainer::getReplicaSetUrl);
    }

    @Test
    void testExecutionAndRollback() throws InterruptedException {
        MongoClient mongoClient = MongoClients.create(mongoDBContainer.getReplicaSetUrl());
        MongoDatabase mongoDatabase = mongoClient.getDatabase("test");

        // Test execution
        testDatabaseInitializer.createCollection(mongoDatabase);
        Thread.sleep(1000); // wait for 1 second
        List<String> collectionNames = getCollectionNames(mongoDatabase.listCollectionNames());
        assertTrue(collectionNames.contains("MongockTest"));

        // Test rollback
        testDatabaseInitializer.rollbackBeforeExecution(mongoDatabase);
        Thread.sleep(1000); // wait for 1 second
        collectionNames = getCollectionNames(mongoDatabase.listCollectionNames());
        assertFalse(collectionNames.contains("mongockTest"));
    }

    private List<String> getCollectionNames(Publisher<String> publisher) throws InterruptedException {
        List<String> result = new ArrayList<>();
        CountDownLatch latch = new CountDownLatch(1);
        publisher.subscribe(new Subscriber<>() {
            @Override
            public void onSubscribe(Subscription s) {
                s.request(Long.MAX_VALUE);
            }

            @Override
            public void onNext(String t) {
                result.add(t);
            }

            @Override
            public void onError(Throwable t) {
                latch.countDown();
            }

            @Override
            public void onComplete() {
                latch.countDown();
            }
        });
        latch.await(); // wait for the operation to complete
        return result;
    }


}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/integration/MongockIntegrationTest.java:MongockIntegrationTest.<init>
// Node: MongockIntegrationTest
package com.itachallenge.challenge.integration;

import com.itachallenge.challenge.document.ChallengeDocument;
import com.itachallenge.challenge.document.DetailDocument;
import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.dto.ChallengeDto;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.repository.ChallengeRepository;
import com.itachallenge.common.exception.GlobalExceptionHandler;
import org.junit.jupiter.api.*;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.AutoConfigureWebTestClient;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.reactive.server.WebTestClient;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import reactor.core.publisher.Flux;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import static org.hamcrest.Matchers.equalTo;
import static org.mockito.Mockito.when;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureWebTestClient
@Testcontainers
@TestInstance(TestInstance.Lifecycle.PER_METHOD)
@Import(GlobalExceptionHandler.class)

class ChallengeIntegrationTest {

    @Container
    static MongoDBContainer container = new MongoDBContainer("mongo")
            .withExposedPorts(27017)
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", () -> container.getReplicaSetUrl("challenges"));
    }

    @Autowired
    private WebTestClient webTestClient;

    @Autowired
    private ChallengeRepository challengeRepository;

    private final String UUID_VALID = "8ecbfe54-fec8-11ed-be56-0242ac120002";
    private final String UUID_INVALID = "dcacb291-b4aa-4029-8e9b-284c8ca80296";
    private final String CHALLENGE_BASE_URL = "/itachallenge/api/v1/challenge";

    UUID uuid_1 = UUID.fromString("8ecbfe54-fec8-11ed-be56-0242ac120002");
    UUID uuid_2 = UUID.fromString("26977eee-89f8-11ec-a8a3-0242ac120003");

    @BeforeEach
    public void setUp() {

        UUID uuidLang1 = UUID.fromString("09fabe32-7362-4bfb-ac05-b7bf854c6e0f");
        UUID uuidLang2 = UUID.fromString("409c9fe8-74de-4db3-81a1-a55280cf92ef");
        UUID[] idsLanguages = new UUID[]{uuidLang1, uuidLang2};
        String[] languageNames = new String[]{"name1", "name2"};
        List<UUID> tags = List.of(UUID.randomUUID());
        String languageImage = "https://image-default.com/default.png";
        LanguageDocument language1 = getLanguageMocked(idsLanguages[0], languageNames[0], languageImage);
        LanguageDocument language2 = getLanguageMocked(idsLanguages[1], languageNames[1], languageImage);
        Set<LanguageDocument> languageSet = Set.of(language1, language2);

        List<UUID> solutionList = List.of(UUID.randomUUID(), UUID.randomUUID());
        String description = "Description";

        DetailDocument detail = new DetailDocument(description);

        String title1 = "Loops";
        String title2 = "If";

        ChallengeDocument challenge = new ChallengeDocument
                (uuid_1, title1, "Level 1", LocalDateTime.now(), detail, languageSet,
                        solutionList, Topic.LISTS, 20, 5,2, tags);
        ChallengeDocument challenge2 = new ChallengeDocument
                (uuid_2, title2, "Level 2", LocalDateTime.now(), detail, languageSet,
                        solutionList, Topic.COMPONENTS, 20, 30,2, tags);

        challengeRepository.saveAll(Flux.just(challenge, challenge2)).blockLast();
    }

    //TODO - Refactor this method, getLanguages endpoint already available
    private LanguageDocument getLanguageMocked(UUID idLanguage, String languageName, String languageImage) {
        LanguageDocument languageIMocked = Mockito.mock(LanguageDocument.class);
        when(languageIMocked.getIdLanguage()).thenReturn(idLanguage);
        when(languageIMocked.getLanguageName()).thenReturn(languageName);
        when(languageIMocked.getLanguageImage()).thenReturn(languageImage);
        return languageIMocked;
    }

    @Test
    @DisplayName("Test response Hello")
    void testDevProfile_OKWithoutAuthentication() {
        webTestClient
                .get()
                .uri("/itachallenge/api/v1/challenge/test")
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isOk()
                .expectBody(String.class)
                .value(String::toString, equalTo("Hello from ITA Challenge!!!"));
    }

    @Test
    void shouldReturnNotFoundForInvalidChallengeId() {
        webTestClient
                .get()
                .uri(CHALLENGE_BASE_URL + "/challenges/{challengeId}", UUID_INVALID)
                .exchange()
                .expectStatus().isNotFound()
                .expectBody()
                .jsonPath("$.message").value(msg -> {
                    Assertions.assertNotNull(msg);
                    Assertions.assertTrue(msg.toString().toLowerCase().contains("not found"));
                });
    }

    @Test
    void shouldReturnOkForValidChallengeId() {
        webTestClient
                .get()
                .uri(CHALLENGE_BASE_URL + "/challenges/{challengeId}", UUID_VALID)
                .accept(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isOk()
                .expectBody(ChallengeDto.class)
                .value(Assertions::assertNotNull);

    }

    @Test
    void getChallengesByPages_ValidPageParameters_ChallengesReturned() {
        webTestClient
                .get()
                .uri("/itachallenge/api/v1/challenge/challenges?offset=0&limit=1")
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(ChallengeDto.class)
                .hasSize(1);
    }

    @Test
    void getChallengesByPages_NullPageParameters_ChallengesReturned() {
        webTestClient
                .get()
                .uri("/itachallenge/api/v1/challenge/challenges")
                .exchange()
                .expectStatus().isOk()
                .expectBodyList(ChallengeDto.class)
                .contains(new ChallengeDto[]{})
                .hasSize(1);
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/integration/ChallengeIntegrationTest.java:ChallengeIntegrationTest.<init>
// Node: withExposedPorts
package com.itachallenge.challenge.service;


import com.itachallenge.challenge.document.TagDocument;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.TagDto;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.TagNotFoundException;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.TagRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;


import java.util.List;
import java.util.Set;
import java.util.UUID;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TagServiceImplTest {

    @Mock
    private TagRepository tagRepository;

    @Mock
    private DocumentToDtoConverter<TagDocument, TagDto> tagConverter = new DocumentToDtoConverter<>();

    @InjectMocks
    private TagServiceImpl tagService;

    @Test
    @DisplayName("convertir UUIDs en TagDocuments")
    void testConvertIdTagFromTag_Document_Success() {
        UUID id1 = UUID.randomUUID();
        UUID id2 = UUID.randomUUID();

        TagDocument tag1 = new TagDocument(id1, "POO", "Programación orientada a objetos", UUID.randomUUID());
        TagDocument tag2 = new TagDocument(id2, "Lógica", "Retos de lógica", UUID.randomUUID());

        when(tagRepository.findById(id1)).thenReturn(Mono.just(tag1));
        when(tagRepository.findById(id2)).thenReturn(Mono.just(tag2));

        List<UUID> tagIds = List.of(id1, id2);

        Set<TagDocument> result = tagService.convertIdTagFromTagDocument(tagIds);

        assertEquals(2, result.size());
        assertTrue(result.stream().anyMatch(tag -> tag.getIdTag().equals(id1)));
        assertTrue(result.stream().anyMatch(tag -> tag.getIdTag().equals(id2)));

        verify(tagRepository).findById(id1);
        verify(tagRepository).findById(id2);
    }


    @Test
    @DisplayName("lanzar excepción cuando no se encuentra el TagDocument por UUID")
    void testConvertIdTagFromTag_TagDocumentNotFound() {
        UUID missingId = UUID.randomUUID();
        when(tagRepository.findById(missingId)).thenReturn(Mono.empty());

        List<UUID> tagsAssigned = List.of(missingId);

        TagNotFoundException exception = assertThrows(
                TagNotFoundException.class,
                () -> tagService.convertIdTagFromTagDocument(tagsAssigned)
        );

        assertEquals("Tag not found: " + missingId, exception.getMessage());
        verify(tagRepository).findById(missingId);
    }

    @Test
    @DisplayName("Get exception when tag is not found")
    void getValidatedTags_notFound_test(){
        UUID missingId = UUID.randomUUID();
        when(tagRepository.findById(missingId)).thenReturn(Mono.empty());
        List<UUID> tagsAssigned = List.of(missingId);

        StepVerifier.create(tagService.getValidatedTags(tagsAssigned))
                .expectError(TagNotFoundException.class)
                .verify();
        verify(tagRepository).findById(missingId);
    }

    @Test
    @DisplayName("Returns Mono<true> when tag has been found")
    void getValidatedTags_returnsTrue_test(){
        TagDocument tagDocument = new TagDocument(UUID.randomUUID(), "Tag Title", "Tag Description", UUID.randomUUID());
        when(tagRepository.findById(tagDocument.getIdTag())).thenReturn(Mono.just(tagDocument));
        List<UUID> tagsAssigned = List.of(tagDocument.getIdTag());
        StepVerifier.create(tagService.getValidatedTags(tagsAssigned))
                .expectNext(true).verifyComplete();
        verify(tagRepository).findById(tagDocument.getIdTag());
    }
    
    @Test
    @DisplayName("Get exception when there are duplicate tag UUIDs")
    void getValidatedTags_duplicateIds_test() {
        UUID duplicatedId = UUID.randomUUID();
        List<UUID> tagsAssigned = List.of(duplicatedId, duplicatedId);
        
        StepVerifier.create(tagService.getValidatedTags(tagsAssigned))
                .expectErrorSatisfies(err -> {
                    assert err instanceof BadRequestException;
                    assert err.getMessage().equals("tag UUID duplicated: " + duplicatedId);
                })
                .verify();
        
        verify(tagRepository, never()).findById(duplicatedId);
    }

    @Test
    @DisplayName("Return tags filtered by languageId")
    void testGetTagsByLanguageId() {
        UUID languageId = UUID.randomUUID();

        TagDocument tag1 = new TagDocument(UUID.randomUUID(), "POO", "Programación orientada a objetos", languageId);
        TagDocument tag2 = new TagDocument(UUID.randomUUID(), "Algoritmos", "Retos de lógica", languageId);
        TagDto tagDto1 = new TagDto(tag1.getIdTag(), tag1.getTagName(), tag1.getTagDescription(), languageId);
        TagDto tagDto2 = new TagDto(tag2.getIdTag(), tag2.getTagName(), tag2.getTagDescription(), languageId);

        Flux<TagDocument> tagDocuments = Flux.just(tag1, tag2);
        Flux<TagDto> tagDtos = Flux.just(tagDto1, tagDto2);


        when(tagRepository.findByLanguageId(languageId)).thenReturn(tagDocuments);
        when(tagConverter.convertDocumentFluxToDtoFlux(tagDocuments, TagDto.class)).thenReturn(tagDtos);


        Mono<GenericResultDto<TagDto>> resultMono = tagService.getTagsByLanguageId(languageId);


        StepVerifier.create(resultMono)
                .assertNext(result -> {
                    assertNotNull(result);
                    assertEquals(2, result.getResults().length);
                    assertEquals("POO", result.getResults()[0].getTagName());
                    assertEquals("Algoritmos", result.getResults()[1].getTagName());
                })
                .verifyComplete();


        verify(tagRepository).findByLanguageId(languageId);
        verify(tagConverter).convertDocumentFluxToDtoFlux(tagDocuments, TagDto.class);
    }

    @Test
    @DisplayName("Throws IllegalArgumentException when languageId is null")
    void getTagsByLanguageId_nullLanguageId_test() {
        StepVerifier.create(tagService.getTagsByLanguageId(null))
                .expectErrorMatches(error ->
                        error instanceof IllegalArgumentException &&
                                error.getMessage().equals("languageId cannot be null")
                )
                .verify();
    }

    @Test
    @DisplayName("Returns empty GenericResultDto when no tags found for languageId")
    void getTagsByLanguageId_returnsEmptyList_test() {
        UUID languageId = UUID.randomUUID();

        when(tagRepository.findByLanguageId(languageId)).thenReturn(Flux.empty());

        when(tagConverter.convertDocumentFluxToDtoFlux(Flux.empty(), TagDto.class)).thenReturn(Flux.empty());

        StepVerifier.create(tagService.getTagsByLanguageId(languageId))
                .assertNext(result -> {
                    assertNotNull(result);
                    assertEquals(0, result.getCount());
                    assertEquals(0, result.getOffset());
                    assertEquals(0, result.getLimit());
                    assertEquals(0, result.getResults().length);
                })
                .verifyComplete();

        verify(tagRepository).findByLanguageId(languageId);
        verify(tagConverter).convertDocumentFluxToDtoFlux(Flux.empty(), TagDto.class);
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/service/TagServiceImplTest.java:TagServiceImplTest.<init>
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.LanguageDto;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.LanguageRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.Arrays;
import java.util.UUID;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
public class LanguageServiceImplTest {

    @Mock
    private LanguageRepository languageRepository;

    @Mock
    private DocumentToDtoConverter<LanguageDocument, LanguageDto> languageConverter;

    @InjectMocks
    private LanguageServiceImpl languageService;

    @Test
    void shouldReturnLanguageDocumentWhenIdExists() {
        UUID id = UUID.randomUUID();
        LanguageDocument expectedDocument = new LanguageDocument();
        expectedDocument.setIdLanguage(id);
        expectedDocument.setLanguageName("English");

        Mockito.when(languageRepository.findByIdLanguage(id)).thenReturn(Mono.just(expectedDocument));

        StepVerifier.create(languageService.findByIdLanguage(id))
                .expectNextMatches(doc -> doc.getIdLanguage().equals(id) && doc.getLanguageName().equals("English"))
                .verifyComplete();
    }

    @Test
    void shouldReturnEmptyWhenIdDoesNotExist() {
        UUID id = UUID.randomUUID();

        Mockito.when(languageRepository.findByIdLanguage(id)).thenReturn(Mono.empty());

        StepVerifier.create(languageService.findByIdLanguage(id))
                .expectNextCount(0)
                .verifyComplete();
    }

    @Test
    void shouldPropagateErrorIfRepositoryFails() {
        UUID id = UUID.randomUUID();
        RuntimeException exception = new RuntimeException("Database error");

        Mockito.when(languageRepository.findByIdLanguage(id)).thenReturn(Mono.error(exception));

        StepVerifier.create(languageService.findByIdLanguage(id))
                .expectErrorMatches(throwable -> throwable instanceof RuntimeException &&
                        throwable.getMessage().equals("Database error"))
                .verify();
    }

    @Test
    void shouldReturnLanguageDocumentWhenLanguageNameExists() {
        String languageName = "Java";
        LanguageDocument expected = new LanguageDocument();
        expected.setIdLanguage(UUID.randomUUID());
        expected.setLanguageName(languageName);

        Mockito.when(languageRepository.findFirstByLanguageName(languageName)).thenReturn(Mono.just(expected));

        StepVerifier.create(languageService.findFirstByLanguageName(languageName))
                .expectNextMatches(doc -> doc.getLanguageName().equals(languageName))
                .verifyComplete();
    }

    @Test
    void shouldReturnEmptyWhenLanguageNameDoesNotExist() {
        String languageName = "NonExistentLanguage";

        Mockito.when(languageRepository.findFirstByLanguageName(languageName)).thenReturn(Mono.empty());

        StepVerifier.create(languageService.findFirstByLanguageName(languageName))
                .expectNextCount(0)
                .verifyComplete();
    }

    @Test
    void shouldPropagateErrorWhenRepositoryFails() {
        String languageName = "Python";
        RuntimeException exception = new RuntimeException("Database error");

        Mockito.when(languageRepository.findFirstByLanguageName(languageName)).thenReturn(Mono.error(exception));

        StepVerifier.create(languageService.findFirstByLanguageName(languageName))
                .expectErrorMatches(throwable -> throwable instanceof RuntimeException &&
                        throwable.getMessage().equals("Database error"))
                .verify();
    }

//    @DisplayName("Cache - getAllLanguages")
//    @Test
//    void getAllLanguages_cacheTest() {
//        // Arrange
//        LanguageDocument languageDocument1 = new LanguageDocument(UUID.randomUUID(), "Javascript", "https://image-default.com/javascript.png");
//        when(languageRepository.findAll()).thenReturn(Flux.just(languageDocument1));
//
//        // Primera llamada
//        GenericResultDto<LanguageDto> result1 = languageService.getAllLanguages().block();
//        assertNotNull(result1);
//        assertEquals(1, result1.getResults().length);
//
//        // Segunda llamada usando cache
//        GenericResultDto<LanguageDto> result2 = languageService.getAllLanguages().block();
//        assertNotNull(result2);
//        assertEquals(1, result2.getResults().length);
//
//
//        verify(languageRepository, times(1)).findAll();
//    }
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/service/LanguageServiceImplTest.java:LanguageServiceImplTest.<init>
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.config.CacheConfig;
import com.itachallenge.challenge.document.TagDocument;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.TagDto;
import com.itachallenge.challenge.repository.TagRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.cache.CacheManager;
import org.springframework.context.annotation.Import;
import reactor.core.publisher.Flux;

import java.util.UUID;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.times;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.mockito.Mockito.when;

@SpringBootTest
@Import(CacheConfig.class)

class TagServiceImplCacheTest {

    @MockBean
    private TagRepository tagRepository;

    @Autowired
    private ITagService tagService;

    @Autowired
    private CacheManager cacheManager;

    @BeforeEach
    void setup() {
        cacheManager.getCache("tagsByLanguage").clear();
    }


    @Test
    void testGetTagsByLanguageIdUsesCache() {
        UUID languageId = UUID.randomUUID();
        TagDocument tag = new TagDocument(UUID.randomUUID(), "Algoritmos", "bla bla", UUID.randomUUID());
        when(tagRepository.findByLanguageId(languageId)).thenReturn(Flux.just(tag));

        // Primera llamada
        GenericResultDto<TagDto> result1 = tagService.getTagsByLanguageId(languageId).block();
        assertNotNull(result1);
        assertEquals(1, result1.getResults().length);

        // Segunda llamada
        GenericResultDto<TagDto> result2 = tagService.getTagsByLanguageId(languageId).block();
        assertNotNull(result2);
        assertEquals(1, result2.getResults().length);


        verify(tagRepository, times(1)).findByLanguageId(languageId);
    }
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/service/TagServiceImplCacheTest.java:TagServiceImplCacheTest.<init>
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.ChallengeDocument;
import com.itachallenge.challenge.exception.*;
import com.itachallenge.challenge.repository.ChallengeRepository;
import com.itachallenge.common.exception.BadRequestException;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.UUID;
import java.util.stream.Stream;

import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class FavoriteServiceImplTest {

    @Mock
    private ChallengeRepository challengeRepository;

    @Mock
    private IUserService userService;

    @InjectMocks
    private FavoriteServiceImpl favoriteService;

    private UUID challengeId;
    private UUID userId;

    @BeforeEach
    void setUp() {
        challengeId = UUID.randomUUID();
        userId = UUID.randomUUID();
    }

    @Test
    void addChallengeToFavorites_WhenChallengeUuidNotValid_ReturnsError() {
        StepVerifier.create(favoriteService.addChallengeToFavorites("InvalidUuid", UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToFavorites_WhenUserUuidNotValid_ReturnsError() {
        StepVerifier.create(favoriteService.addChallengeToFavorites(UUID.randomUUID().toString(), "InvalidUuid"))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToFavorites_WhenChallengeUuidIsNull_ReturnsError() {
        StepVerifier.create(favoriteService.addChallengeToFavorites(null, UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToFavorites_WhenUserUuidIsNull_ReturnsError() {
        StepVerifier.create(favoriteService.addChallengeToFavorites(UUID.randomUUID().toString(), null))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void addChallengeToFavorites_WhenChallengeNotFound_ReturnsError() {
        String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";
        UUID challengeUuid = UUID.randomUUID();

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.empty());

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof ChallengeNotFoundException &&
                                error.getMessage().equals(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid.toString())))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
    }

    @Test
    void addChallengeToFavorites_WhenUserNotFound_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new UserNotFoundException(message)));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToFavorites_WhenUserServiceReturnsCustomBadRequestException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new BadRequestException(message)));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToFavorites_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new InternalServerErrorException(message)));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToFavorites_WhenUserServiceReturnsAnyException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new Exception(message)));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof Exception &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void addChallengeToFavorites_WhenAdded_IncreasesTimesFavoriteAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesFavorite = 20;

        challenge.setTimesFavorite(initialTimesFavorite);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == initialTimesFavorite + 1 &&
                            favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesFavorite + 1, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void addChallengeToFavorites_WhenAddedAndInitialTimesFavoriteIsNull_IncreasesTimesFavoriteAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesFavorite(null);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == 1 &&
                            favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(1, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void addChallengeToFavorites_WhenNotAdded_NotIncreaseTimesFavoriteAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesFavorite = 20;

        challenge.setTimesFavorite(initialTimesFavorite);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == initialTimesFavorite &&
                            favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesFavorite, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(0)).save(any());
    }

    @ParameterizedTest
    @MethodSource
    void addChallengeToFavorites_WhenNotAddedAndTimesFavoriteIsNullOrZero_SetTimesFavoriteToOneAndReturnsFavoriteDTO(Integer timesFavorite) {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesFavorite(timesFavorite);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(favoriteService.addChallengeToFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == 1 &&
                            favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(1, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).addChallengeToFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    public static Stream<Integer> addChallengeToFavorites_WhenNotAddedAndTimesFavoriteIsNullOrZero_SetTimesFavoriteToOneAndReturnsFavoriteDTO() {
        return Stream.of(null, 0);
    }

    @Test
    void removeChallengeFromFavorites_WhenChallengeUuidNotValid_ReturnsError() {
        StepVerifier.create(favoriteService.removeChallengeFromFavorites("InvalidUuid", UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromFavorites_WhenUserUuidNotValid_ReturnsError() {
        StepVerifier.create(favoriteService.removeChallengeFromFavorites(UUID.randomUUID().toString(), "InvalidUuid"))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromFavorites_WhenChallengeUuidIsNull_ReturnsError() {
        StepVerifier.create(favoriteService.removeChallengeFromFavorites(null, UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromFavorites_WhenUserUuidIsNull_ReturnsError() {
        StepVerifier.create(favoriteService.removeChallengeFromFavorites(UUID.randomUUID().toString(), null))
                .expectErrorMatches(error ->
                        error instanceof BadUUIDException &&
                                error.getMessage().equals("Invalid ID format. Please indicate the correct format."))
                .verify();
    }

    @Test
    void removeChallengeFromFavorites_WhenChallengeNotFound_ReturnsError() {
        String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";
        UUID challengeUuid = UUID.randomUUID();

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.empty());

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), UUID.randomUUID().toString()))
                .expectErrorMatches(error ->
                        error instanceof ChallengeNotFoundException &&
                                error.getMessage().equals(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid.toString())))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
    }

    @Test
    void removeChallengeFromFavorites_WhenUserNotFound_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new UserNotFoundException(message)));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromFavorites_WhenUserServiceReturnsCustomBadRequestException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new BadRequestException(message)));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromFavorites_WhenUserServiceReturnsCustomInternalServerErrorException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new InternalServerErrorException(message)));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof InternalServerErrorException &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromFavorites_WhenUserServiceReturnsAnyException_ReturnsError() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        String message = "Some error message";

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));

        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.error(new Exception(message)));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectErrorMatches(error ->
                        error instanceof Exception &&
                                error.getMessage().equals(message))
                .verify();

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
    }

    @Test
    void removeChallengeFromFavorites_WhenRemoved_DecreasesTimesFavoriteAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesFavorite = 20;

        challenge.setTimesFavorite(initialTimesFavorite);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == initialTimesFavorite - 1 &&
                            !favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesFavorite - 1, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void removeChallengeFromFavorites_WhenRemovedAndInitialTimesFavoriteIsNull_SetsTimesFavoriteToZeroAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesFavorite(null);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == 0 &&
                            !favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(0, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void removeChallengeFromFavorites_WhenRemovedAndInitialTimesFavoriteIsZero_SetsTimesFavoriteToZeroAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesFavorite(0);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(true));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == 0 &&
                            !favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(0, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    @Test
    void removeChallengeFromFavorites_WhenNotRemoved_NotChangeTimesFavoriteAndReturnsFavoriteDTO() {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();
        int initialTimesFavorite = 20;

        challenge.setTimesFavorite(initialTimesFavorite);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == initialTimesFavorite &&
                            !favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(initialTimesFavorite, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(0)).save(any());
    }

    @ParameterizedTest
    @MethodSource
    void removeChallengeFromFavorites_WhenNotRemovedAndTimesFavoriteIsNullOrZero_SetTimesFavoriteToZeroAndReturnsFavoriteDTO(Integer timesFavorite) {
        UUID challengeUuid = UUID.randomUUID();
        UUID userUuid = UUID.randomUUID();
        ChallengeDocument challenge = new ChallengeDocument();

        challenge.setTimesFavorite(timesFavorite);

        when(challengeRepository.findByUuid(challengeUuid)).thenReturn(Mono.just(challenge));
        when(userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())).thenReturn(Mono.just(false));
        when(challengeRepository.save(challenge)).thenReturn(Mono.just(challenge));

        StepVerifier.create(favoriteService.removeChallengeFromFavorites(challengeUuid.toString(), userUuid.toString()))
                .expectNextMatches(favoriteDto -> {
                    return favoriteDto.getTimesFavorited() == 0 &&
                            !favoriteDto.isFavorite();
                })
                .verifyComplete();

        Assertions.assertEquals(0, challenge.getTimesFavorite());

        verify(challengeRepository, times(1)).findByUuid(challengeUuid);
        verify(userService, times(1)).removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString());
        verify(challengeRepository, times(1)).save(challenge);
    }

    public static Stream<Integer> removeChallengeFromFavorites_WhenNotRemovedAndTimesFavoriteIsNullOrZero_SetTimesFavoriteToZeroAndReturnsFavoriteDTO() {
        return Stream.of(null, 0);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/service/FavoriteServiceImplTest.java:FavoriteServiceImplTest.<init>
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.ResourceDocument;
import com.itachallenge.challenge.dto.ChallengeDto;
import com.itachallenge.challenge.dto.ChallengeListDto;
import com.itachallenge.challenge.dto.ResourceDto;
import com.itachallenge.challenge.enums.AssociationType;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.InternalServerErrorException;
import com.itachallenge.challenge.exception.ResourceNotFoundException;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.ResourceRepository;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
@ExtendWith(MockitoExtension.class)
class ResourceServiceImplTest {

    @Mock
    private ResourceRepository resourceRepository;

    @Mock
    private DocumentToDtoConverter<ResourceDocument, ResourceDto> resourceConverter;

    @Mock
    private IChallengeService challengeService;

    @InjectMocks
    private ResourceServiceImpl resourceService;

    @Test //
    void createResource_WithValidData_ResourceCreated() {
        UUID resourceId = UUID.randomUUID();
        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.NONE)
                .challengeIds(Collections.emptyList())
                .build();

        ResourceDocument resourceDocument = new ResourceDocument(resourceId, "Title", "Description", "http://example.com", Topic.DEBUGGING, ResourceContentType.VIDEO, Collections.emptyList(), AssociationType.NONE);

        when(resourceConverter.convertDtoToDocument(any(), eq(ResourceDocument.class))).thenReturn(resourceDocument);
        when(resourceRepository.save(any(ResourceDocument.class))).thenReturn(Mono.just(resourceDocument));
        when(resourceConverter.convertDocumentToDto(any(), eq(ResourceDto.class))).thenReturn(resourceDto);

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectNext(resourceDto)
                .verifyComplete();

        verify(resourceRepository).save(resourceDocument);
        verify(resourceConverter).convertDtoToDocument(any(), eq(ResourceDocument.class));
        verify(resourceConverter).convertDocumentToDto(any(), eq(ResourceDto.class));
    }

    @Test
    void createResource_WithMissingContentType_ShouldThrowError() {
        UUID resourceId = UUID.randomUUID();
        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(null)
                .associationType(AssociationType.NONE)
                .challengeIds(Collections.emptyList())
                .build();

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectError(IllegalArgumentException.class)
                .verify();
    }

    @Test
    void createResource_WithnullTopicType_ShouldThrowError() {
        UUID resourceId = UUID.randomUUID();
        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(null)
                .contentType(ResourceContentType.COURSE)
                .associationType(AssociationType.NONE)
                .challengeIds(Collections.emptyList())
                .build();

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectError(IllegalArgumentException.class)
                .verify();
    }

    @Test //
    void createResource_WithAssociationTypeChoose_ShouldReturnUpdatedResource() {
        UUID resourceId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(Collections.emptyList())
                .associationType(AssociationType.ALLSAMETOPIC)
                .build();

        ChallengeDto challengeDto = ChallengeDto.builder()
                .challengeId(challengeId)
                .title("Challenge")
                .build();

        ChallengeListDto challengeListDto = new ChallengeListDto(List.of(challengeDto), 1);

        ResourceDocument resourceDocument = new ResourceDocument(
                resourceId, "Title", "Description", "http://example.com",
                Topic.DEBUGGING, ResourceContentType.VIDEO,
                Collections.emptyList(), AssociationType.ALLSAMETOPIC
        );

        when(challengeService.getChallengesByTopic(Topic.DEBUGGING, 0, -1)).thenReturn(Mono.just(challengeListDto));
        when(resourceConverter.convertDtoToDocument(any(), eq(ResourceDocument.class))).thenReturn(resourceDocument);
        when(resourceRepository.save(any(ResourceDocument.class))).thenReturn(Mono.just(resourceDocument));
        when(resourceConverter.convertDocumentToDto(any(), eq(ResourceDto.class))).thenReturn(resourceDto);

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectNextMatches(updatedResource -> updatedResource.getChallengeIds().contains(challengeId))
                .verifyComplete();

        verify(challengeService).getChallengesByTopic(Topic.DEBUGGING, 0, -1);
        verify(resourceConverter, atMost(2)).convertDtoToDocument(any(), eq(ResourceDocument.class));
        verify(resourceRepository, atMost(2)).save(any(ResourceDocument.class));
        verify(resourceConverter).convertDocumentToDto(any(), eq(ResourceDto.class));
    }


    @Test //
    void createResource_WithAssociationTypeChoose_NoChallengesFound_ShouldThrowError() {
        UUID resourceId = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.CHOOSE)
                .challengeIds(Collections.emptyList())
                .build();

        ChallengeListDto emptyChallengeList = new ChallengeListDto(Collections.emptyList(), 0);

        when(challengeService.getChallengesByTopic(Topic.DEBUGGING, 0, -1))
                .thenReturn(Mono.just(emptyChallengeList));

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectErrorMatches(error -> error instanceof IllegalArgumentException &&
                        error.getMessage().equals("No challenges found for the selected topic"))
                .verify();

        verify(challengeService).getChallengesByTopic(Topic.DEBUGGING, 0, -1);

        verifyNoInteractions(resourceConverter);
        verifyNoInteractions(resourceRepository);
    }

    @Test
    void createResource_WithAssociationTypeNone_ShouldSaveResource() {
        UUID resourceId = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.NONE)
                .challengeIds(Collections.emptyList())
                .build();

        ResourceDocument resourceDocument = new ResourceDocument(resourceId, "Title", "Description", "http://example.com", Topic.DEBUGGING, ResourceContentType.VIDEO, Collections.emptyList(), AssociationType.NONE);

        when(resourceConverter.convertDtoToDocument(any(), eq(ResourceDocument.class))).thenReturn(resourceDocument);
        when(resourceRepository.save(any(ResourceDocument.class))).thenReturn(Mono.just(resourceDocument));
        when(resourceConverter.convertDocumentToDto(any(), eq(ResourceDto.class))).thenReturn(resourceDto);

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectNext(resourceDto)
                .verifyComplete();

        verify(resourceRepository).save(resourceDocument);
        verify(resourceConverter).convertDtoToDocument(any(), eq(ResourceDocument.class));
        verify(resourceConverter).convertDocumentToDto(any(), eq(ResourceDto.class));
    }


    @Test
    void createResource_WithNullResourceDto_ShouldThrowError() {
        Mono<ResourceDto> result = resourceService.createResource(null);

        StepVerifier.create(result)
                .expectError(IllegalArgumentException.class)
                .verify();
    }

    @Test
    void createResource_WithChooseAssociationType_NoChallenges_ShouldNotSave() {
        UUID resourceId = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.CHOOSE)
                .challengeIds(Collections.emptyList())
                .build();

        ChallengeListDto emptyChallengeList = new ChallengeListDto(Collections.emptyList(), 0);

        when(challengeService.getChallengesByTopic(Topic.DEBUGGING, 0, -1))
                .thenReturn(Mono.just(emptyChallengeList));

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectErrorMatches(error -> error instanceof IllegalArgumentException &&
                        error.getMessage().equals("No challenges found for the selected topic"))
                .verify();

        verifyNoInteractions(resourceRepository);
    }

    @Test
    void createResource_WithAssociationTypeALLSAMETOPIC_ShouldPopulateChallengeIds() {
        UUID resourceId = UUID.randomUUID();
        UUID challengeId = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.ALLSAMETOPIC)
                .challengeIds(Collections.emptyList())
                .build();

        ChallengeDto challengeDto = ChallengeDto.builder()
                .challengeId(challengeId)
                .title("Challenge")
                .build();

        ChallengeListDto challengeListDto = new ChallengeListDto(List.of(challengeDto), 1);

        ResourceDocument resourceDocument = new ResourceDocument(
                resourceId, "Title", "Description", "http://example.com", Topic.DEBUGGING,
                ResourceContentType.VIDEO, List.of(challengeId), AssociationType.ALLSAMETOPIC
        );

        when(challengeService.getChallengesByTopic(Topic.DEBUGGING, 0, -1))
                .thenReturn(Mono.just(challengeListDto));
        when(resourceConverter.convertDtoToDocument(any(), eq(ResourceDocument.class)))
                .thenReturn(resourceDocument);
        when(resourceRepository.save(any(ResourceDocument.class)))
                .thenReturn(Mono.just(resourceDocument));
        when(resourceConverter.convertDocumentToDto(any(), eq(ResourceDto.class)))
                .thenReturn(resourceDto);

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectNextMatches(updatedResource -> updatedResource.getChallengeIds().contains(challengeId))
                .verifyComplete();

        verify(challengeService).getChallengesByTopic(Topic.DEBUGGING, 0, -1);
    }

    @Test
    void createResource_WithChooseAssociationType_NoChallengesFound_ShouldThrowError() {
        UUID resourceId = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.CHOOSE)
                .challengeIds(Collections.emptyList())
                .build();

        ChallengeListDto emptyChallengeList = new ChallengeListDto(Collections.emptyList(), 0);

        when(challengeService.getChallengesByTopic(Topic.DEBUGGING, 0, -1))
                .thenReturn(Mono.just(emptyChallengeList));

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectErrorMatches(error -> error instanceof IllegalArgumentException &&
                        error.getMessage().equals("No challenges found for the selected topic"))
                .verify();

        verify(challengeService).getChallengesByTopic(Topic.DEBUGGING, 0, -1);
        verifyNoInteractions(resourceConverter);
        verifyNoInteractions(resourceRepository);
    }

    @Test
    void createResource_WithAssociationTypeALLSAMETOPIC_MultipleChallenges_ShouldPopulateChallengeIds() {
        UUID resourceId = UUID.randomUUID();
        UUID challengeId1 = UUID.randomUUID();
        UUID challengeId2 = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.ALLSAMETOPIC)
                .challengeIds(Collections.emptyList())
                .build();

        ChallengeDto challengeDto1 = ChallengeDto.builder()
                .challengeId(challengeId1)
                .title("Challenge 1")
                .build();
        ChallengeDto challengeDto2 = ChallengeDto.builder()
                .challengeId(challengeId2)
                .title("Challenge 2")
                .build();

        ChallengeListDto challengeListDto = new ChallengeListDto(List.of(challengeDto1, challengeDto2), 2);

        ResourceDocument resourceDocument = new ResourceDocument(
                resourceId, "Title", "Description", "http://example.com", Topic.DEBUGGING,
                ResourceContentType.VIDEO, List.of(challengeId1, challengeId2), AssociationType.ALLSAMETOPIC
        );

        when(challengeService.getChallengesByTopic(Topic.DEBUGGING, 0, -1))
                .thenReturn(Mono.just(challengeListDto));
        when(resourceConverter.convertDtoToDocument(any(), eq(ResourceDocument.class)))
                .thenReturn(resourceDocument);
        when(resourceRepository.save(any(ResourceDocument.class)))
                .thenReturn(Mono.just(resourceDocument));
        when(resourceConverter.convertDocumentToDto(any(), eq(ResourceDto.class)))
                .thenReturn(resourceDto);

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectNextMatches(updatedResource -> updatedResource.getChallengeIds().contains(challengeId1) &&
                        updatedResource.getChallengeIds().contains(challengeId2))
                .verifyComplete();

        verify(challengeService).getChallengesByTopic(Topic.DEBUGGING, 0, -1);
    }

    @Test
    void createResource_WithFailedConversion_ShouldThrowError() {
        UUID resourceId = UUID.randomUUID();

        ResourceDto resourceDto = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Title")
                .description("Description")
                .url("http://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .associationType(AssociationType.NONE)
                .challengeIds(Collections.emptyList())
                .build();

        when(resourceConverter.convertDtoToDocument(any(), eq(ResourceDocument.class))).thenReturn(null); // Fallida de conversió

        Mono<ResourceDto> result = resourceService.createResource(resourceDto);

        StepVerifier.create(result)
                .expectErrorMatches(error -> error instanceof IllegalStateException &&
                        error.getMessage().equals("Conversion DTO to Document null"))
                .verify();
    }

    // ID CON recursos
    @Test
    void getResourcesByChallengeId_WhenResourcesExist_ReturnsFluxOfResources() {

        UUID challengeId = UUID.randomUUID();
        UUID resourceId1 = UUID.randomUUID();
        UUID resourceId2 = UUID.randomUUID();


        ResourceDocument doc1 = new ResourceDocument(
                resourceId1, "Resource 1", "Desc 1", "https://example.com/1",
                Topic.DEBUGGING, ResourceContentType.VIDEO, List.of(challengeId), AssociationType.ALLSAMETOPIC
        );
        ResourceDocument doc2 = new ResourceDocument(
                resourceId2, "Resource 2", "Desc 2", "https://example.com/2",
                Topic.COMPONENTS, ResourceContentType.BLOG, List.of(challengeId), AssociationType.CHOOSE
        );

        ResourceDto dto1 = new ResourceDto();
        dto1.setResourceId(resourceId1);
        dto1.setTitle("Resource 1");


        ResourceDto dto2 = new ResourceDto();
        dto2.setResourceId(resourceId2);
        dto2.setTitle("Resource 2");


        when(resourceRepository.findByChallengeIdsContaining(challengeId))
                .thenReturn(Flux.just(doc1, doc2));
        when(resourceConverter.convertDocumentToDto(doc1, ResourceDto.class)).thenReturn(dto1);
        when(resourceConverter.convertDocumentToDto(doc2, ResourceDto.class)).thenReturn(dto2);


        StepVerifier.create(resourceService.getResourcesByChallengeId(challengeId))
                .expectNext(dto1)
                .expectNext(dto2)
                .verifyComplete();
    }

    // Valido SIN recursos
    @Test
    void getResourcesByChallengeId_WhenNoResourcesExist_ReturnsEmptyFlux() {

        UUID challengeId = UUID.randomUUID();
        when(resourceRepository.findByChallengeIdsContaining(challengeId))
                .thenReturn(Flux.empty());


        StepVerifier.create(resourceService.getResourcesByChallengeId(challengeId))
                .expectNextCount(0)
                .verifyComplete();
    }

    @Test
    void getResourcesByChallengeId_WhenIdIsNull_ThrowsBadRequestException() {
        StepVerifier.create(resourceService.getResourcesByChallengeId(null))
                .expectErrorMatches(ex ->
                        ex instanceof BadRequestException &&
                                ex.getMessage().equals("Challenge ID cannot be null")
                )
                .verify();
    }

    //Error en el repo
    @Test
    void getResourcesByChallengeId_WhenRepositoryFails_ThrowsInternalServerErrorException() {
        UUID challengeId = UUID.randomUUID();
        when(resourceRepository.findByChallengeIdsContaining(challengeId))
                .thenReturn(Flux.error(new RuntimeException("DB Connection Failed")));

        StepVerifier.create(resourceService.getResourcesByChallengeId(challengeId))
                .expectErrorMatches(ex ->
                        ex instanceof InternalServerErrorException &&
                                ex.getMessage().equals("Failed to fetch resources for challenge ID: " + challengeId)
                )
                .verify();

        verify(resourceRepository, times(1)).findByChallengeIdsContaining(challengeId);
    }

    @Test
    void getResourcesByChallengeId_WhenResourceNotFound_PropagatesException() {
        UUID challengeId = UUID.randomUUID();
        ResourceNotFoundException ex = new ResourceNotFoundException("Not found");
        when(resourceRepository.findByChallengeIdsContaining(challengeId))
                .thenReturn(Flux.error(ex));

        StepVerifier.create(resourceService.getResourcesByChallengeId(challengeId))
                .expectErrorMatches(thrownEx ->
                        thrownEx instanceof ResourceNotFoundException &&
                                thrownEx.getMessage().equals("Not found")
                )
                .verify();
    }




}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/service/ResourceServiceImplTest.java:ResourceServiceImplTest.<init>
package com.itachallenge.challenge.validator;

import com.itachallenge.challenge.annotations.ValidGenericPattern;
import jakarta.validation.ConstraintValidatorContext;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.MockitoAnnotations;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(MockitoExtension.class)
class GenericPatternValidatorTest {
    @InjectMocks
    private GenericPatternValidator validator;
    @Mock
    private ValidGenericPattern constraintAnnotation;
    @Mock
    private ConstraintValidatorContext context;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        Mockito.when(constraintAnnotation.pattern()).thenReturn("^\\d{1,9}$");

        validator.initialize(constraintAnnotation);
    }

    @Test
    void isValid() {
        boolean isValid = validator.isValid("26", context);

        assertTrue(isValid);
    }

    @Test
    void isNotValid() {
        boolean isValid = validator.isValid("1a23", context);

        assertFalse(isValid);
    }

    @Test
    void isTooLongNotValid() {
        boolean isValid = validator.isValid("1234561111", context);

        assertFalse(isValid);
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/validator/GenericPatternValidatorTest.java:GenericPatternValidatorTest.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/LanguageDtoTest.java:LanguageDtoTest.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/BookmarkDtoTest.java:BookmarkDtoTest.<init>
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

@ExtendWith(SpringExtension.class)
@SpringBootTest
class TagDtoTest {

    @Test
    void testTagDtoAllArgsConstructorAndGetters() {
        UUID id = UUID.randomUUID();
        String name = "POO";
        String description = "Programación orientada a objetos";

        TagDto tagDto = new TagDto(id, name, description,UUID.randomUUID());

        assertEquals(id, tagDto.getTagId());
        assertEquals(name, tagDto.getTagName());
        assertEquals(description, tagDto.getTagDescription());
    }

    @Test
    void testTagDtoNoArgsConstructorAndSetters() {
        UUID id = UUID.randomUUID();
        String name = "Algoritmos";
        String description = "Retos de lógica";

        TagDto tagDto = new TagDto();
        tagDto.setTagId(id);
        tagDto.setTagName(name);
        tagDto.setTagDescription(description);

        assertEquals(id, tagDto.getTagId());
        assertEquals(name, tagDto.getTagName());
        assertEquals(description, tagDto.getTagDescription());
    }

    @Test
    void testJsonSerialization() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        TagDto tagDto = new TagDto(UUID.fromString("123e4567-e89b-12d3-a456-426614174000"),
                "Recursividad",
                "Funciones que se llaman a sí mismas",UUID.randomUUID());

        String json = mapper.writeValueAsString(tagDto);

        assertTrue(json.contains("\"tag_name\":\"Recursividad\""));
        assertTrue(json.contains("\"tag_description\":\"Funciones que se llaman a sí mismas\""));
        assertTrue(json.contains("\"id_tag\":\"123e4567-e89b-12d3-a456-426614174000\""));
    }
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/TagDtoTest.java:TagDtoTest.<init>
package com.itachallenge.challenge.dto;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;

@ExtendWith(SpringExtension.class)
@SpringBootTest
class DeleteResponseDtoTest {
    @Test
    void testMessageAndID() {
        // Arrange
        String id = "valid_id";
        String message = "Expected message";

        // Act
        DeleteResponseDto deleteResponseDto = new DeleteResponseDto(id,message);

        // Assert
        Assertions.assertEquals(message, deleteResponseDto.getMessage());
        Assertions.assertEquals(id, deleteResponseDto.getId());
    }


}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/DeleteResponseDtoTest.java:DeleteResponseDtoTest.<init>
package com.itachallenge.challenge.dto;




import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.junit.jupiter.api.Test;
import java.util.List;
import java.util.UUID;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
@ExtendWith(SpringExtension.class)
@SpringBootTest
public class ChallengeFilterDtoTest {

    @Test
    public void testConstructorAndGetters() {
        String languageId = "1234";
        String level = "MEDIUM";
        UUID tag1 = UUID.randomUUID();
        UUID tag2 = UUID.randomUUID();
        List<UUID> tags = List.of(tag1, tag2);
        int offset = 5;
        int limit = 10;

        ChallengeFilterDto dto = new ChallengeFilterDto(languageId, level, tags, offset, limit);

        assertEquals(languageId, dto.getIdLanguage());
        assertEquals(level, dto.getLevel());
        assertEquals(tags, dto.getTags());
        assertEquals((Integer)offset, dto.getOffset());
        assertEquals((Integer)limit, dto.getLimit());
    }

    @Test
    public void testSetters() {
        ChallengeFilterDto dto = new ChallengeFilterDto(null, null, null, 0, -1);

        String newLanguageId = "5678";
        String newLevel = "EASY";
        List<UUID> newTags = List.of(UUID.randomUUID());
        int newOffset = 2;
        int newLimit = 20;

        dto.setIdLanguage(newLanguageId);
        dto.setLevel(newLevel);
        dto.setTags(newTags);
        dto.setOffset(newOffset);
        dto.setLimit(newLimit);

        assertEquals(newLanguageId, dto.getIdLanguage());
        assertEquals(newLevel, dto.getLevel());
        assertEquals(newTags, dto.getTags());
        assertEquals((Integer)newOffset, dto.getOffset());
        assertEquals((Integer)newLimit, dto.getLimit());
    }

    @Test
    public void testDefaultValues() {
        ChallengeFilterDto dto = new ChallengeFilterDto(null, null, null, null, null);


        assertNull(dto.getIdLanguage());
        assertNull(dto.getLevel());
        assertNull(dto.getTags());
        assertNull(dto.getOffset());
        assertNull(dto.getLimit());
    }
}



// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/ChallengeFilterDtoTest.java:ChallengeFilterDtoTest.<init>
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








// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/ChallengeDtoTest.java:ChallengeDtoTest.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/dto/MessageDtoTest.java:MessageDtoTest.<init>
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.reactivestreams.client.MongoClient;
import nl.altindag.log.LogCaptor;
import org.bson.Document;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
@SpringBootTest
class DataBaseRollBackTest {

    @Container
    static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:4.0.10")
            .withExposedPorts(27017)
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", () -> mongoDBContainer.getReplicaSetUrl("challenges"));
    }

    @Autowired
    private ReactiveMongoTemplate reactiveMongoTemplate;

    @Autowired
    private DataBaseRollback dataBaseRollback;

    @Autowired
    private MongoClient mongoClient;

    private LogCaptor logCaptor;

    @BeforeEach
    void setUp() {
        logCaptor = LogCaptor.forClass(DataBaseRollback.class);
    }

    @DisplayName("Test @Execution method - Verify thrown exception to demostrate rollback feature")
    @Test
    void ExecutionTest() {


        assertThrows(IllegalArgumentException.class, () -> dataBaseRollback.execution(mongoClient));
        assertTrue(logCaptor.getInfoLogs().contains("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nUpdater execution started"));

    }

    @DisplayName("Test @RollbackExecution method - Verify the rollback of the changes made in the execution method")
    @Test
    void rollbackTest() {
        dataBaseRollback.rollBackExecution(mongoClient);
        assertTrue(logCaptor.getInfoLogs().contains("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution started"));
        assertTrue(logCaptor.getInfoLogs().contains("Field updated in collection rolled back"));
        assertTrue(logCaptor.getInfoLogs().contains("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\nRollback execution completed successfully"));
    }

    @DisplayName("Test updateFieldInCollection method - Verify thrown exception when invalid operator is used")
    @Test
    void updateFieldInCollectionTest() {
        assertThrows(IllegalArgumentException.class, () -> dataBaseRollback.updateFieldInCollection(mongoClient));
        assertTrue(logCaptor.getErrorLogs().stream()
                .anyMatch(log -> log.contains("All update operators must start with '$', but 'invalidOperator' does not")));
    }

    @DisplayName("Test updateTextInField method - Verify the field is updated with the new value")
    @Test
    void updateTextInFieldTest() {

        reactiveMongoTemplate.save(new Document("Language Rollbacked", "LanguageDemo"), "mongockDemo").block();
        dataBaseRollback.updateTextInField(mongoClient);

        Document updatedDocument = reactiveMongoTemplate.findOne(
                new org.springframework.data.mongodb.core.query.Query(
                        org.springframework.data.mongodb.core.query.Criteria.where("Language Rollbacked").is("LanguageUpdated")),
                Document.class, "mongockDemo").block();

        assertNotNull(updatedDocument, "The document should be updated with the new value 'LanguageUpdated'");
    }


    @DisplayName("Test rollbackUpdateFieldInCollection method - Verify the field is renamed back to 'Language Rollbacked'")
    @Test
    void rollbackUpdateFieldInCollectionTest() {

        reactiveMongoTemplate.save(new Document("Language Name Updated", "someValue"), "mongockDemo").block();
        dataBaseRollback.rollbackUpdateFieldInCollection(mongoClient);

        Document rolledBackDocument = reactiveMongoTemplate.findOne(
                new org.springframework.data.mongodb.core.query.Query(
                        org.springframework.data.mongodb.core.query.Criteria.where("Language Rollbacked").exists(true)),
                Document.class, "mongockDemo").block();

        assertNotNull(rolledBackDocument, "The field should be renamed back to 'Language Rollbacked'");
    }



    @AfterEach
    void tearDown() {
        reactiveMongoTemplate.dropCollection("mongockDemo").block();
        logCaptor.close();
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/config/dbchangelog/DataBaseRollBackTest.java:DataBaseRollBackTest.<init>
package com.itachallenge.challenge.config.dbchangelog;

import com.mongodb.reactivestreams.client.MongoClient;
import com.mongodb.reactivestreams.client.MongoClients;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.mongodb.core.ReactiveMongoTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.time.Duration;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
@SpringBootTest
class MongockTestContainer {

    @Container
    static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:4.0.10")
            .withExposedPorts(27017)
            .withStartupTimeout(Duration.ofSeconds(60));

    @DynamicPropertySource
    static void initMongoProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", () -> mongoDBContainer.getReplicaSetUrl("challenges"));
    }

    private ReactiveMongoTemplate reactiveMongoTemplate;
    private MongoClient mongoClient;

    @Autowired
    private DatabaseInitializer databaseInitializer;

    @BeforeEach
    void setUp() {
        mongoClient = MongoClients.create(mongoDBContainer.getReplicaSetUrl("challenges"));
        reactiveMongoTemplate = new ReactiveMongoTemplate(mongoClient, "challenges");
        databaseInitializer.createCollection(mongoClient.getDatabase("challenges"));
        databaseInitializer.execution(reactiveMongoTemplate);
    }

    @Test
    void testCollectionCreation() {

        databaseInitializer.execution(reactiveMongoTemplate);
        String collectionName = reactiveMongoTemplate.getCollection("mongockDemo")
                .map(collection -> collection.getNamespace().getCollectionName())
                .block();
        assertEquals("mongockDemo", collectionName, "The collection name should be mongockDemo");
    }

    @Test
    void testDocumentCreation() {
        String expectedCollectionName = "mongockDemo";
        String actualCollectionName = reactiveMongoTemplate.getCollection("mongockDemo")
                .map(collection -> collection.getNamespace().getCollectionName())
                .block();

        assertNotNull(actualCollectionName, "The collection name should not be null");
        assertEquals(expectedCollectionName, actualCollectionName, "The collection name should be 'mongockDemo'");

        reactiveMongoTemplate.getCollection("mongockDemo")
                .flatMapMany(collection -> collection.find().first())
                .doOnNext(document -> {
                    assertNotNull(document, "The document should not be null");
                    assertNotNull(document.get("language_name"), "The field 'language_name' should exist");
                })
                .blockLast();
    }

    @Test
    void testUpdateOperation() {

        String actualCollectionName = reactiveMongoTemplate.getCollection("mongockDemo")
                .map(collection -> collection.getNamespace().getCollectionName())
                .block();

        assertNotNull(actualCollectionName, "The collection name should not be null");
        assertEquals("mongockDemo", actualCollectionName, "The collection name should be 'mongockDemo'");

        databaseInitializer.execution(reactiveMongoTemplate);

        reactiveMongoTemplate.getCollection(actualCollectionName)
                .flatMapMany(collection -> collection.find().first())
                .doOnNext(document -> {
                    assertNotNull(document, "The document should not be null");
                    assertTrue(document.containsKey("language_name_updated"), "The field 'language_name_updated' should exist");
                })
                .blockLast();
    }

    @AfterEach
    void tearDown() {
        reactiveMongoTemplate.dropCollection("mongockDemo").block();
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/challenge/config/dbchangelog/MongockTestContainer.java:MongockTestContainer.<init>
package com.itachallenge.auth.controller;

import com.itachallenge.auth.config.TestAuthConfig;
import com.itachallenge.auth.dto.SwitchRoleRequest;
import com.itachallenge.auth.dto.User;
import com.itachallenge.auth.service.JwtRoleSwitchService;
import com.itachallenge.auth.exception.InvalidRoleChangeRequestException;
import com.itachallenge.auth.service.IAuthService;
import com.itachallenge.auth.service.IAuthJwtFacade;
import com.itachallenge.auth.service.IUserService;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.reactive.WebFluxTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.core.env.Environment;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.reactive.server.WebTestClient;
import reactor.core.publisher.Mono;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import static org.assertj.core.api.Assertions.assertThat;

import java.util.HashMap;
import java.util.Map;

import static org.mockito.Mockito.when;

@WebFluxTest(AuthController.class)
@TestPropertySource(properties = "token.expiration.minutes=60")
@Import(TestAuthConfig.class)
@ActiveProfiles("test")
class AuthControllerTest {
    @Autowired
    private WebTestClient webTestClient;

    @Autowired
    Environment env;

    @MockBean
    private IAuthService authService;

    @MockBean
    private JwtRoleSwitchService jwtRoleSwitchService;

    @MockBean
    private IUserService userService;

    @InjectMocks
    private AuthController authController;

    @MockBean
    private IAuthJwtFacade authJwtFacade;

    @Test
    void authenticateWithGithub_ValidCode_ReturnsJwt() {
        String validCode = "valid-code";
        String accessToken = "valid-token";
        String githubUsername = "octocat";
        User user = new User("1234", githubUsername, "ADMIN");
        String jwtToken = "generatedJwt";

        Map<String, Object> validationResult = new HashMap<>();
        validationResult.put("isValid", true);
        validationResult.put("username", githubUsername);
        validationResult.put("token", jwtToken);

        when(authService.exchangeCodeForToken(validCode)).thenReturn(Mono.just(accessToken));
        when(authService.validateTokenWithGithub(accessToken)).thenReturn(Mono.just(validationResult));
        when(userService.fetchUserData(githubUsername)).thenReturn(Mono.just(user));
        when(authJwtFacade.generateToken(user.getUsername(), user.getRole(), user.getUuid())).thenReturn(jwtToken);

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/github/authenticate")
                .bodyValue(Map.of("code", validCode))
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.isValid").isEqualTo(true)
                .jsonPath("$.username").isEqualTo(githubUsername)
                .jsonPath("$.token").isEqualTo(jwtToken);
    }

    @Test
    void authenticateWithGithub_InvalidCode_ReturnsUnauthorized() {
        String invalidCode = "invalid-code";
        String accessToken = "invalid-token";
        Map<String, Object> validationResult = new HashMap<>();
        validationResult.put("isValid", false);
        validationResult.put("username", null);

        when(authService.exchangeCodeForToken(invalidCode)).thenReturn(Mono.just(accessToken));
        when(authService.validateTokenWithGithub(accessToken)).thenReturn(Mono.just(validationResult));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/github/authenticate")
                .bodyValue(Map.of("code", invalidCode))
                .exchange()
                .expectStatus().isUnauthorized()
                .expectBody()
                .jsonPath("$.isValid").isEqualTo(false)
                .jsonPath("$.username").isEmpty();
    }

    @Test
    void authenticateWithGithub_TokenExchangeError_ReturnsInternalServerError() {
        String invalidCode = "invalid-code";

        when(authService.exchangeCodeForToken(invalidCode))
                .thenReturn(Mono.error(new RuntimeException("Token exchange failed")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/github/authenticate")
                .bodyValue(Map.of("code", invalidCode))
                .exchange()
                .expectStatus().is5xxServerError()
                .expectBody()
                .jsonPath("$.isValid").isEqualTo(false)
                .jsonPath("$.username").isEmpty();
    }

    @Test
    void authenticateWithGithub_TokenValidationError_ReturnsInternalServerError() {
        String validCode = "valid-code";
        String accessToken = "valid-token";

        when(authService.exchangeCodeForToken(validCode)).thenReturn(Mono.just(accessToken));
        when(authService.validateTokenWithGithub(accessToken))
                .thenReturn(Mono.error(new RuntimeException("Token validation failed")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/github/authenticate")
                .bodyValue(Map.of("code", validCode))
                .exchange()
                .expectStatus().is5xxServerError()
                .expectBody()
                .jsonPath("$.isValid").isEqualTo(false)
                .jsonPath("$.username").isEmpty();
    }

    @Test
    void authenticateWithGithub_UserDoesNotExist_ReturnsForbidden() {
        String validCode = "valid-code";
        String accessToken = "valid-token";
        String githubUsername = "octocat";
        Map<String, Object> validationResult = new HashMap<>();
        validationResult.put("isValid", true);
        validationResult.put("username", githubUsername);

        when(authService.exchangeCodeForToken(validCode)).thenReturn(Mono.just(accessToken));
        when(authService.validateTokenWithGithub(accessToken)).thenReturn(Mono.just(validationResult));
        when(userService.fetchUserData(githubUsername)).thenReturn(Mono.empty());

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/github/authenticate")
                .bodyValue(Map.of("code", validCode))
                .exchange()
                .expectStatus().isForbidden()
                .expectBody()
                .jsonPath("$.isValid").isEqualTo(false)
                .jsonPath("$.message").isEqualTo("User does not exist in the database")
                .jsonPath("$.username").doesNotExist()
                .jsonPath("$.token").doesNotExist();
    }

    @Test
    void authenticateWithGithub_UserValidationError_ReturnsInternalServerError() {
        String validCode = "valid-code";
        String accessToken = "valid-token";
        String githubUsername = "octocat";
        Map<String, Object> validationResult = new HashMap<>();
        validationResult.put("isValid", true);
        validationResult.put("username", githubUsername);

        when(authService.exchangeCodeForToken(validCode)).thenReturn(Mono.just(accessToken));
        when(authService.validateTokenWithGithub(accessToken)).thenReturn(Mono.just(validationResult));
        when(userService.fetchUserData(githubUsername)).thenReturn(Mono.error(new RuntimeException("Database error")));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/github/authenticate")
                .bodyValue(Map.of("code", validCode))
                .exchange()
                .expectStatus().is5xxServerError()
                .expectBody()
                .jsonPath("$.isValid").isEqualTo(false)
                .jsonPath("$.username").doesNotExist()
                .jsonPath("$.token").doesNotExist();
    }

    @Test
    void authenticateWithGithub_MissingRequestBody_ReturnsBadRequest() {
        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/github/authenticate")
                .contentType(MediaType.APPLICATION_JSON)
                .exchange()
                .expectStatus().isBadRequest();
    }

    @Test
    void getVersionTest() {
        String expectedVersion = env.getProperty("spring.application.version");

        assert expectedVersion != null;

        webTestClient.get()
                .uri("/itachallenge/api/v1/auth/version")
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.application_name").isEqualTo("itachallenge-auth")
                .jsonPath("$.version").isEqualTo(expectedVersion);
    }

    @Test
    void logout_ValidToken_ShouldReturn200() {
        String token = "valid.jwt.token";
        Mockito.doNothing().when(authJwtFacade).validateToken(token);
        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/logout")
                .header("Authorization", "Bearer " + token)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Map.class)
                .value(response -> assertThat(response.get("message")).isEqualTo("Logout successful"));
    }

    @Test
    void logout_ExpiredToken_ShouldReturn200() {
        String expiredToken = "expired.jwt.token";
        Mockito.doThrow(new ExpiredJwtException(null, null, "Token expired but logout successful"))
                .when(authJwtFacade).validateToken(expiredToken);

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/logout")
                .header("Authorization", "Bearer " + expiredToken)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Map.class)
                .value(response -> {
                    assertThat(response.get("message")).isEqualTo("Token expired but logout successful");
                });
    }

    @Test
    void logout_TokenJustWithinTry_ShouldReturn200() {
        String token = "any.jwt.token";
        Mockito.doNothing().when(authJwtFacade).validateToken(token);

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/logout")
                .header("Authorization", "Bearer " + token)
                .exchange()
                .expectStatus().isOk()
                .expectBody(Map.class)
                .value(response -> assertThat(response.get("message")).isEqualTo("Logout successful"));
    }

    @Test
    void logout_InvalidToken_ShouldReturn401() {
        String invalidToken = "invalid.jwt.token";
        Mockito.doThrow(new JwtException("Invalid or tampered token: JWT parsing failed"))
                .when(authJwtFacade).validateToken(invalidToken);

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/logout")
                .header("Authorization", "Bearer " + invalidToken)
                .exchange()
                .expectStatus().isUnauthorized()
                .expectBody(Map.class)
                .value(response -> {
                    assertThat(response.get("message").toString()).startsWith("Invalid or tampered token");
                });
    }

    @Test
    void logout_EmptyAuthorizationHeader_ShouldReturn401() {
        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/logout")
                .header("Authorization", "")
                .exchange()
                .expectStatus().isUnauthorized()
                .expectBody(Map.class)
                .value(response -> {
                    assert response.get("message").equals("Authorization header is missing or malformed");
                });
    }

    @Test
    void logout_MalformedAuthorizationHeader_ShouldReturn401() {
        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/logout")
                .header("Authorization", "Token xyz")
                .exchange()
                .expectStatus().isUnauthorized()
                .expectBody(Map.class)
                .value(response -> {
                    assert response.get("message").equals("Authorization header is missing or malformed");
                });
    }

    @Test
    void logout_MissingAuthorizationHeader_ShouldReturn401() {
        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/logout")
                .exchange()
                .expectStatus().isUnauthorized()
                .expectBody(Map.class)
                .value(response -> {
                    assert response.get("message").equals("Authorization header is missing or malformed");
                });
    }

    @Test
    void switchRole_WithValidTokenAndValidRole_ReturnsNewToken() {
        String originalToken = "valid.jwt.token";
        String newRole = "ADMIN";
        String newToken = "new.jwt.token";

        when(authJwtFacade.extractBearerToken("Bearer " + originalToken)).thenReturn(originalToken);
        when(jwtRoleSwitchService.switchRole(originalToken, newRole)).thenReturn(newToken);

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/switch-role")
                .header("Authorization", "Bearer " + originalToken)
                .bodyValue(new SwitchRoleRequest(newRole))
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.token").isEqualTo(newToken);
    }

    @Test
    void switchRole_WithExpiredToken_Returns200WithMessage() {
        String expiredToken = "expired.jwt.token";
        String newRole = "ADMIN";

        when(authJwtFacade.extractBearerToken("Bearer " + expiredToken)).thenReturn(expiredToken);
        when(jwtRoleSwitchService.switchRole(expiredToken, newRole))
                .thenThrow(new ExpiredJwtException(null, null, "Token is expired."));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/switch-role")
                .header("Authorization", "Bearer " + expiredToken)
                .bodyValue(new SwitchRoleRequest(newRole))
                .exchange()
                .expectStatus().isOk()
                .expectBody()
                .jsonPath("$.message").isEqualTo("Token is expired.");
    }

    @Test
    void switchRole_WithInvalidToken_Returns401() {
        String invalidToken = "invalid.jwt.token";
        String newRole = "ADMIN";

        when(authJwtFacade.extractBearerToken("Bearer " + invalidToken)).thenReturn(invalidToken);
        when(jwtRoleSwitchService.switchRole(invalidToken, newRole))
                .thenThrow(new JwtException("Invalid or tampered token."));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/switch-role")
                .header("Authorization", "Bearer " + invalidToken)
                .bodyValue(new SwitchRoleRequest(newRole))
                .exchange()
                .expectStatus().isUnauthorized()
                .expectBody()
                .jsonPath("$.message").value(msg -> assertThat(msg).isEqualTo("Invalid or tampered token."));
    }

    @Test
    void switchRole_WithSameRole_Throws400() {
        String token = "valid.jwt.token";

        when(authJwtFacade.extractBearerToken("Bearer " + token)).thenReturn(token);
        when(jwtRoleSwitchService.switchRole(token, "USER"))
                .thenThrow(new InvalidRoleChangeRequestException("New role is the same as current role."));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/switch-role")
                .header("Authorization", "Bearer " + token)
                .bodyValue(new SwitchRoleRequest("USER"))
                .exchange()
                .expectStatus().isBadRequest()
                .expectBody()
                .jsonPath("$.message").isEqualTo("New role is the same as current role.");
    }

    @Test
    void switchRole_MissingAuthorizationHeader_Returns401() {
        when(authJwtFacade.extractBearerToken(null))
                .thenThrow(new JwtException("Authorization header is missing or malformed"));

        webTestClient.post()
                .uri("/itachallenge/api/v1/auth/switch-role")
                .bodyValue(new SwitchRoleRequest("ADMIN"))
                .exchange()
                .expectStatus().isUnauthorized()
                .expectBody()
                .jsonPath("$.message").isEqualTo("Authorization header is missing or malformed");
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/test/java/com/itachallenge/auth/controller/AuthControllerTest.java:AuthControllerTest.<init>
