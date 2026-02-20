// Cluster 7

// Node: warn
// Node: trim
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



// Node: parseOpenApiSpec
// Node: mapper
// Node: readValue
// Node: stream
// Node: debug
package com.itachallenge.errorcore.exception;


import lombok.Getter;

/**
 * Base class for all user-facing API exceptions.
 * Encapsulates HTTP status, message key (for i18n), and optional message args.
 */
@Getter
public abstract class BaseApiException extends RuntimeException {

    private final transient ApiCustomErrorInfo info;

    protected BaseApiException(String message, ApiCustomErrorInfo info) {
        super(message);
        this.info = info;// ensures the message field in Throwable is set
    }

}



// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/main/java/com/itachallenge/errorcore/exception/BaseApiException.java:for.<init>
// Node: key
package com.itachallenge.errorcore.config;

import com.itachallenge.errorcore.builder.ErrorResponseBuilder;
import com.itachallenge.errorcore.exceptionhandler.GlobalExceptionHandler;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.context.MessageSource;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.ReloadableResourceBundleMessageSource;

/**
 * Manual configuration exposing shared error-handling components.
 */
@Configuration
public class ErrorHandlingConfig {

    @Bean
    public MessageSource messageSource() {
        ReloadableResourceBundleMessageSource src = new ReloadableResourceBundleMessageSource();
        src.setBasenames("classpath:core-messages", "classpath:messages");
        src.setDefaultEncoding("UTF-8");
        src.setFallbackToSystemLocale(false);
        return src;
    }

    @Bean
    public ErrorResponseBuilder errorResponseBuilder(MessageSource messageSource) {
        return new ErrorResponseBuilder(messageSource);
    }

    @Bean
    @ConditionalOnMissingBean(GlobalExceptionHandler.class)
    public GlobalExceptionHandler globalExceptionHandler(ErrorResponseBuilder builder) {
        // Anonymous subclass to register handler logic, if needed
        return new GlobalExceptionHandler(builder);
    }
}


// Node: messageSource
// Node: ReloadableResourceBundleMessageSource
// Node: setBasenames
// Node: setDefaultEncoding
// Node: setFallbackToSystemLocale
// Node: errorResponseBuilder
// Node: ErrorResponseBuilder
// Node: ConditionalOnMissingBean
package com.itachallenge.errorcore.builder;

import com.itachallenge.errorcore.dto.APIErrorResponse;
import com.itachallenge.errorcore.dto.FieldErrorDto;
import com.itachallenge.errorcore.exception.ApiCustomErrorInfo;
import com.itachallenge.errorcore.exception.BaseApiException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.*;
import jakarta.validation.constraints.NotNull;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.context.support.ReloadableResourceBundleMessageSource;
import org.springframework.core.MethodParameter;
import org.springframework.core.codec.DecodingException;
import org.springframework.http.HttpStatus;
import org.springframework.validation.BeanPropertyBindingResult;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.server.ResponseStatusException;

import java.lang.reflect.Method;
import java.util.Set;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * Integration-style tests for ErrorResponseBuilder using the real core-messages.properties file.
 */
class ErrorResponseBuilderTest {

    private ErrorResponseBuilder builder;
    private HttpServletRequest request;

    private static final Validator validator = Validation.buildDefaultValidatorFactory().getValidator();

    static class DummyController {

        public void testMethod(Integer age) {
            // Intentionally left blank: this method is only used for reflection-based testing of type mismatches.
        }

        public void acceptTestDto(@Valid TestDto dto) {
            // Intentionally empty: used to trigger @Valid validation in tests.
        }
    }

    static class TestDto {
        @NotNull(message = "email cannot be null")
        private final String email;
        public TestDto(String email) { this.email = email; }
        public String getEmail() { return email; }
    }

    @BeforeEach
    void setUp() {
        // Use the *real* global core-messages.properties file
        ReloadableResourceBundleMessageSource messageSource = new ReloadableResourceBundleMessageSource();
        messageSource.setBasename("classpath:core-messages"); // points to src/main/resources/core-messages.properties
        messageSource.setDefaultEncoding("UTF-8");

        builder = new ErrorResponseBuilder(messageSource);
        request = mock(HttpServletRequest.class);
        when(request.getRequestURI()).thenReturn("/api/test");
    }

    // ------------------------------------------------------------
    // buildError
    // ------------------------------------------------------------
    @Test
    void buildError_shouldBuildBasicResponseWithRealMessage() {
        APIErrorResponse response = builder.buildError(new DecodingException("failure decoding"), request);

        assertThat(response.getStatus()).isEqualTo(400);
        assertThat(response.getError()).isEqualTo("Bad Request");
        assertThat(response.getMessage()).contains("Invalid or malformed request");
        assertThat(response.getPath()).isEqualTo("/api/test");
    }

    // ------------------------------------------------------------
    // buildTypeMismatchErrorResponse
    // ------------------------------------------------------------
    @Test
    void buildTypeMismatchErrorResponse_shouldIncludeFieldInformation() throws Exception {
        Method method = DummyController.class.getDeclaredMethod("testMethod", Integer.class);
        MethodParameter methodParameter = new MethodParameter(method, 0);

        MethodArgumentTypeMismatchException ex = new MethodArgumentTypeMismatchException(
                "abc", Integer.class, "age", methodParameter, new IllegalArgumentException("type mismatch")
        );

        APIErrorResponse response = builder.buildTypeMismatchErrorResponse(ex, request);

        assertThat(response.getStatus()).isEqualTo(400);
        assertThat(response.getErrors()).hasSize(1);
        FieldErrorDto error = response.getErrors().getFirst();
        assertThat(error.getField()).isEqualTo("age");
        assertThat(error.getMessage()).contains("Parameter 'age' has invalid value 'abc'. Expected type: Integer");
        assertThat(error.getObjectName()).isEqualTo("DummyController");
    }

    // ------------------------------------------------------------
    // buildConstraintViolationErrorResponse
    // ------------------------------------------------------------
    @Test
    void buildConstraintViolationErrorResponse_shouldBuildWithViolations() {
        // Create a real constraint violation manually
        ConstraintViolation<?> violation = validator.validate(new TestDto(null)).iterator().next();
        ConstraintViolationException ex = new ConstraintViolationException(Set.of(violation));

        APIErrorResponse response = builder.buildConstraintViolationErrorResponse(ex, request);

        assertThat(response.getStatus()).isEqualTo(400);
        assertThat(response.getMessage()).contains("One or more request parameters failed validation");
        assertThat(response.getErrors()).isNotEmpty();
        assertThat(response.getErrors().getFirst().getMessage()).contains("Validation failed for parameter");
    }
    // ------------------------------------------------------------
    // buildArgumentNotValidErrorResponse
    // ------------------------------------------------------------
    @Test
    void buildArgumentNotValidErrorResponse_shouldExtractFieldErrorsWithRealMessageSource() throws Exception {
        TestDto invalidDto = new TestDto(null);
        BindingResult bindingResult = new BeanPropertyBindingResult(invalidDto, "testDto");

        // Manually perform validation and fill the BindingResult
        validator.validate(invalidDto).forEach(v ->
                bindingResult.rejectValue("email", null, v.getMessage()));

        Method method = DummyController.class.getDeclaredMethod("acceptTestDto", TestDto.class);
        MethodParameter parameter = new MethodParameter(method, 0);
        MethodArgumentNotValidException ex = new MethodArgumentNotValidException(parameter, bindingResult);

        APIErrorResponse response = builder.buildArgumentNotValidErrorResponse(ex, request);

        assertThat(response.getStatus()).isEqualTo(400);
        assertThat(response.getErrors()).hasSize(1);
        assertThat(response.getErrors().getFirst().getField()).isEqualTo("email");
        assertThat(response.getErrors().getFirst().getMessage()).isEqualTo("email cannot be null");
        assertThat(response.getMessage()).contains("object 'testDto'");
    }

    // ------------------------------------------------------------
    // buildStatusErrorResponse (ResponseStatusException)
    // ------------------------------------------------------------
    @Test
    void buildStatusErrorResponse_shouldUseAppropriateMessageWhen404() {
        ResponseStatusException ex = new ResponseStatusException(HttpStatus.NOT_FOUND, "Not found");

        APIErrorResponse response = builder.buildStatusErrorResponse(ex, request);

        assertThat(response.getStatus()).isEqualTo(404);
        assertThat(response.getMessage()).isEqualTo("The requested resource could not be found.");
    }

    @Test
    void buildStatusErrorResponse_shouldUseAppropriateMessageWhen400() {
        ResponseStatusException ex = new ResponseStatusException(HttpStatus.BAD_REQUEST, "Bad request");

        APIErrorResponse response = builder.buildStatusErrorResponse(ex, request);

        assertThat(response.getStatus()).isEqualTo(400);
        assertThat(response.getMessage()).isEqualTo("The request could not be understood by the server.");
    }


    @Test
    void buildNotFoundError_shouldReturnNotFoundResponse() {
        class GenericNotFoundException extends BaseApiException{
            GenericNotFoundException(String arg){
                super(arg,ApiCustomErrorInfo.of(HttpStatus.NOT_FOUND,"error.notFound",new Object[]{arg}));
            }
        }
        // Given
        GenericNotFoundException ex = new GenericNotFoundException("Resource not found");

        // When
        APIErrorResponse response = builder.buildCustomExceptionError(ex,request);

        // Then
        assertThat(response.getStatus()).isEqualTo(HttpStatus.NOT_FOUND.value());
        assertThat(response.getError()).isEqualTo("Not Found");
        assertThat(response.getMessage()).isEqualTo("Resource not found");
        assertThat(response.getPath()).isEqualTo("/api/test");
        assertThat(response.getTimestamp()).isNotNull();
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/error-response-core/src/test/java/com/itachallenge/errorcore/builder/ErrorResponseBuilderTest.java:ErrorResponseBuilderTest.<init>
// Node: buildDefaultValidatorFactory
// Node: getValidator
// Node: setBasename
// Node: iterator
// Node: next
package com.itachallenge.userinteraction.service.bookmark;

import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.repository.UserRepository;
import com.itachallenge.userinteraction.document.bookmark.BookmarkDocument;
import com.itachallenge.userinteraction.repository.bookmark.BookmarkRepository;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class BookmarkServiceImpl implements BookmarkService {

    private final UserRepository userRepository;
    private final BookmarkRepository bookmarkRepository;

    private static final String USER_NOT_FOUND_WITH_ID = "User not found with id: ";

    public BookmarkServiceImpl(UserRepository userRepository, BookmarkRepository bookmarkRepository) {
        this.bookmarkRepository = bookmarkRepository;
        this.userRepository = userRepository;
    }

    @Override
    public Mono<Set<UUID>> getUserBookmarks(String userId) {
        return parseAndValidateUUID(userId)
                .flatMap(userUuid ->
                        userRepository.existsById(userUuid)
                                .flatMap(exists -> exists == Boolean.TRUE
                                        ? bookmarkRepository.findByUserId(userUuid)
                                        .map(BookmarkDocument::getChallengeId)
                                        .collect(Collectors.toSet())
                                        : Mono.error(new NotFoundException(USER_NOT_FOUND_WITH_ID + userId))
                                )
                );
    }

    private Mono<UUID> parseAndValidateUUID(String id) {
        if (id == null || id.isEmpty()) {
            return Mono.error(new BadUUIDException("Invalid ID format"));
        }

        try {
            return Mono.just(UUID.fromString(id));
        } catch (IllegalArgumentException ex) {
            return Mono.error(new BadUUIDException("Invalid ID format"));
        }
    }
}


// Node: parseAndValidateUUID
// Node: collect
// Node: toSet
// Node: NotFoundException
// Node: BadUUIDException
// Node: fromString
package com.itachallenge.userinteraction.service.favorite;

import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.repository.UserRepository;
import com.itachallenge.userinteraction.document.favorite.FavoriteDocument;
import com.itachallenge.userinteraction.repository.favorite.FavoriteRepository;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class FavoriteServiceImpl implements FavoriteService {
    private final FavoriteRepository favoriteRepository;
    private final UserRepository userRepository;

    private static final String USER_NOT_FOUND_WITH_ID = "User not found with id: ";

    public FavoriteServiceImpl(FavoriteRepository favoriteRepository, UserRepository userRepository) {
        this.favoriteRepository = favoriteRepository;
        this.userRepository = userRepository;
    }

    private Mono<UUID> parseAndValidateUUID(String id) {
        if (id == null || id.isEmpty()) {
            return Mono.error(new BadUUIDException("Invalid ID format"));
        }

        try {
            return Mono.just(UUID.fromString(id));
        } catch (IllegalArgumentException ex) {
            return Mono.error(new BadUUIDException("Invalid ID format"));
        }
    }

    @Override
    public Mono<Boolean> addChallengeToFavorites(String userId, String challengeId) {

        return Mono.zip(parseAndValidateUUID(userId), parseAndValidateUUID(challengeId))
                .flatMap(uuidTuple -> {
                    UUID userUuid = uuidTuple.getT1();
                    UUID challengeUuid = uuidTuple.getT2();

                    return userRepository.findById(userUuid)
                            .switchIfEmpty(Mono.error(new NotFoundException("User not found")))
                            .flatMap(user -> addToFavorites(userUuid, challengeUuid));
                });
    }

    private Mono<Boolean> addToFavorites(UUID userUuid, UUID challengeUuid) {
        return favoriteRepository.existsByUserIdAndChallengeId(userUuid, challengeUuid)
                .flatMap(exists -> {
                    if (exists.booleanValue())
                        return Mono.just(false);

                    FavoriteDocument favorite = new FavoriteDocument();
                    favorite.setUuid(UUID.randomUUID());
                    favorite.setUserId(userUuid);
                    favorite.setChallengeId(challengeUuid);

                    return favoriteRepository.save(favorite)
                            .thenReturn(true);
                });
    }

    @Override
    public Mono<Set<UUID>> getUserFavorites(String userId) {
        return parseAndValidateUUID(userId)
                .flatMap(userUuid ->
                        userRepository.existsById(userUuid)
                                .flatMap(exists -> {
                                    if (!exists) {
                                        return Mono.error(new NotFoundException(USER_NOT_FOUND_WITH_ID + userId));
                                    }
                                    return favoriteRepository.findByUserId(userUuid)
                                            .map(FavoriteDocument::getChallengeId)
                                            .collect(Collectors.toSet());
                                })
                );
    }

    @Override
    public Mono<Boolean> deleteChallengeFromFavorites(String userId, String challengeId) {
        return Mono.zip(parseAndValidateUUID(userId), parseAndValidateUUID(challengeId))
                .flatMap(uuidTuple -> {
                    UUID userUuid = uuidTuple.getT1();
                    UUID challengeUuid = uuidTuple.getT2();

                    return userRepository.findById(userUuid)
                            .switchIfEmpty(Mono.error(new NotFoundException("User not found")))
                            .flatMap(user -> deleteFromFavorites(userUuid, challengeUuid));
                });
    }

    private Mono<Boolean> deleteFromFavorites(UUID userId, UUID challengeUuid) {
        return favoriteRepository.findByUserIdAndChallengeId(userId, challengeUuid)
                .flatMap(favorite ->
                        favoriteRepository.delete(favorite)
                                .then(Mono.just(true))
                )
                .switchIfEmpty(Mono.just(false));
    }
}


package com.itachallenge.user.exception;

public class BadRequestException extends RuntimeException {

    public BadRequestException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/BadRequestException.java:BadRequestException.<init>
// Node: BadRequestException
package com.itachallenge.user.exception;

public class BadUUIDException extends RuntimeException {

    public BadUUIDException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/BadUUIDException.java:BadUUIDException.<init>
package com.itachallenge.user.exception;

public class NotFoundException extends RuntimeException {

    public NotFoundException(String message) {
        super(message);
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/exception/NotFoundException.java:NotFoundException.<init>
package com.itachallenge.user.document.enums;

import com.fasterxml.jackson.annotation.JsonCreator;

import java.util.Arrays;
import java.util.stream.Collectors;

public enum SolutionAction {
    SAVE,
    GIVE_UP,
    SUBMIT;

    @JsonCreator
    public static SolutionAction fromString(String action) {
        if (action == null || action.isBlank()) {
            throw new IllegalArgumentException("Action cannot be null or blank");
        }
        return Arrays.stream(SolutionAction.values())
                .filter(e -> e.name().equalsIgnoreCase(action.trim()))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException(
                        "Action must be one of: " + Arrays.stream(values())
                                .map(Enum::name)
                                .collect(Collectors.joining(", "))
                ));
    }
}

// Node: isBlank
// Node: values
// Node: filter
// Node: equalsIgnoreCase
// Node: findFirst
// Node: orElseThrow
// Node: joining
package com.itachallenge.user.document.enums;

import lombok.Getter;

import java.util.Arrays;

@Getter
public enum ChallengeStatus {
    SUBMITTED_COMPLETE("SUBMITTED_COMPLETE"),
    IN_PROGRESS("IN_PROGRESS"),
    SUBMITTED_INCOMPLETE("SUBMITTED_INCOMPLETE");

    private final String value;

    ChallengeStatus(String value) {
        this.value = value;
    }

    public static ChallengeStatus challengeStatusFromString(String status) {
        ChallengeStatus output = null;
        if (status != null) {
            output = Arrays.stream(ChallengeStatus.values())
                    .filter(s -> status.equalsIgnoreCase(s.getValue()))
                    .findFirst()
                    .orElse(null);
        }
        return output;
    }

}


// Node: challengeStatusFromString
// Node: orElse
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


// Node: validateAndParseUuid
package com.itachallenge.user.service;

import com.itachallenge.user.dto.SolvedDto;
import com.itachallenge.user.exception.NotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import org.springframework.stereotype.Service;

import com.itachallenge.user.document.enums.ChallengeStatus;
import com.itachallenge.user.exception.BadRequestException;
import com.itachallenge.user.exception.InternalServerErrorException;

import reactor.core.publisher.Mono;

@Service
public class ChallengeServiceImpl implements IChallengeService {

    private static final Logger log = LoggerFactory.getLogger(ChallengeServiceImpl.class);

    private final WebClient.Builder webClientBuilder;

    private final String challengeServiceUrl;
    private static final String X_SOLVED_MESSAGE = "X-Solved-Message";

    public ChallengeServiceImpl(
            WebClient.Builder webClientBuilder, @Value("${challenge.service.url}") String challengeServiceUrl) {
        this.webClientBuilder = webClientBuilder;
        this.challengeServiceUrl = challengeServiceUrl;
    }

    @Override
    public Mono<SolvedDto> addChallengeToSolved(String challengeId) {
        return callEndpoint(challengeId, X_SOLVED_MESSAGE, HttpMethod.POST);
    }

    private Mono<SolvedDto> callEndpoint(String challengeId, String errorHeader, HttpMethod method) {
        String url = buildUrl(challengeId);
        log.debug("Calling endpoint with method={} and URL={}", method, url);

        return webClientBuilder.build()
                .method(method)
                .uri(url)
                .retrieve()
                .onStatus(HttpStatus.NOT_FOUND::equals, response -> {
                    log.info("Challenge not found with id: {}", challengeId);
                    return Mono.error(new NotFoundException("Challenge not found"));
                })
                .onStatus(HttpStatus.BAD_REQUEST::equals, response -> {
                    String errorMessage = response.headers().header(errorHeader).stream()
                            .findFirst().orElse("Unknown error");
                    log.warn("ChallengeService returned 400: {}", errorMessage);
                    return Mono.error(new BadRequestException(errorMessage));
                })
                .onStatus(HttpStatus.INTERNAL_SERVER_ERROR::equals, response -> {
                    String errorMessage = response.headers().header(errorHeader).stream()
                            .findFirst().orElse("Unknown error");
                    log.warn("ChallengeService returned 500: {}", errorMessage);
                    return Mono.error(new InternalServerErrorException(errorMessage));
                })
                .bodyToMono(SolvedDto.class);
    }

    private String buildUrl(String challengeId){
        return UriComponentsBuilder.fromHttpUrl(challengeServiceUrl)
                .path("/itachallenge/api/v1/challenge/solved/{challengeId}")
                .buildAndExpand(challengeId)
                .toUriString();
    }

}

// Node: callEndpoint
// Node: buildUrl
// Node: method
// Node: retrieve
// Node: onStatus
// Node: headers
// Node: bodyToMono
// Node: fromHttpUrl
// Node: buildAndExpand
// Node: toUriString
package com.itachallenge.user.service;

import com.itachallenge.user.document.UserDocument;
import com.itachallenge.user.exception.BadUUIDException;
import com.itachallenge.user.exception.NotFoundException;
import com.itachallenge.user.repository.UserRepository;
import com.itachallenge.userinteraction.document.bookmark.BookmarkDocument;
import org.springframework.stereotype.Service;

import com.itachallenge.userinteraction.repository.bookmark.BookmarkRepository;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Service
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final BookmarkRepository bookmarkRepository;

    public UserServiceImpl(UserRepository userRepository, BookmarkRepository bookmarkRepository) {
        this.userRepository = userRepository;
        this.bookmarkRepository = bookmarkRepository;
    }

    @Override
    public Mono<UserDocument> getUser(String githubUsername) {
        return userRepository.findByUsername(githubUsername)
                .switchIfEmpty(Mono.error(new NotFoundException("User not found")));
    }

    //TODO : TO IMPLEMENT TO BOOKMARK SERVICE IMPL
    @Override
    public Mono<Boolean> addChallengeToBookmarks(String userId, String challengeId) {
        return Mono.zip(parseAndValidateUUID(userId), parseAndValidateUUID(challengeId))
                .flatMap(uuidTuple -> {
                    UUID userUuid = uuidTuple.getT1();
                    UUID challengeUuid = uuidTuple.getT2();

                    return userRepository.findById(userUuid)
                            .switchIfEmpty(Mono.error(new NotFoundException("User not found")))
                            .flatMap(user -> addToBookmarks(userUuid, challengeUuid));
                });
    }

    //TODO : TO IMPLEMENT TO BOOKMARK SERVICE IMPL
    @Override
    public Mono<Boolean> deleteChallengeFromBookmarks(String userId, String challengeId) {
        return Mono.zip(parseAndValidateUUID(userId), parseAndValidateUUID(challengeId))
                .flatMap(uuidTuple -> {
                    UUID userUuid = uuidTuple.getT1();
                    UUID challengeUuid = uuidTuple.getT2();

                    return userRepository.findById(userUuid)
                            .switchIfEmpty(Mono.error(new NotFoundException("User not found")))
                            .flatMap(user -> deleteFromBookmarks(userUuid, challengeUuid));
                });
    }

    //TODO : TO IMPLEMENT TO BOOKMARK SERVICE IMPL
    private Mono<Boolean> addToBookmarks(UUID userUuid, UUID challengeUuid) {
        return bookmarkRepository.existsByUserIdAndChallengeId(userUuid, challengeUuid)
                .flatMap(exists -> {
                    if (exists.booleanValue())
                        return Mono.just(false);

                    BookmarkDocument bookmark = new BookmarkDocument();
                    bookmark.setUuid(UUID.randomUUID());
                    bookmark.setUserId(userUuid);
                    bookmark.setChallengeId(challengeUuid);

                    return bookmarkRepository.save(bookmark)
                            .thenReturn(true);
                });
    }

    //TODO : TO IMPLEMENT TO BOOKMARK SERVICE IMPL
    private Mono<Boolean> deleteFromBookmarks(UUID userId, UUID challengeUuid) {
        return bookmarkRepository.findByUserIdAndChallengeId(userId, challengeUuid)
                .flatMap(bookmark ->
                        bookmarkRepository.delete(bookmark)
                                .then(Mono.just(true))
                )
                .switchIfEmpty(Mono.just(false));
    }

    private Mono<UUID> parseAndValidateUUID(String id) {

        if (id == null || id.isEmpty()) {
            return Mono.error(new BadUUIDException("Invalid ID format"));
        }

        try {
            return Mono.just(UUID.fromString(id));
        } catch (IllegalArgumentException ex) {
            return Mono.error(new BadUUIDException("Invalid ID format"));
        }
    }

    @Override
    public Mono<UserDocument> getUserById(String userId) {
        return userRepository.findById(UUID.fromString(userId))
                .switchIfEmpty(Mono.error(new NotFoundException("User not found")));
    }
}


package com.itachallenge.user.validator;

import com.itachallenge.user.annotations.ValidGithubUsername;

import javax.validation.ConstraintValidator;
import javax.validation.ConstraintValidatorContext;

public class GithubUsernameValidator implements ConstraintValidator<ValidGithubUsername, String> {

    private static final String GITHUB_USERNAME_REGEX = "^(?!-)[a-zA-Z0-9-]{1,39}(?<!-)$";

    @Override
    public boolean isValid(String username, ConstraintValidatorContext context) {
        return username != null && username.matches(GITHUB_USERNAME_REGEX);
    }
}



// Node: matches
// Node: matcher
package com.itachallenge.user.helper;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.JsonSerializer;
import com.fasterxml.jackson.databind.SerializerProvider;

import java.io.IOException;

public class ChallengeJsonSerializer /* extends JsonSerializer<UserChallengeDto> */ {
/*
    @Override
    public void serialize(UserChallengeDto challenge, JsonGenerator gen, SerializerProvider serializers) throws IOException {

            gen.writeStartObject();
            gen.writeStringField("uuid_challenge", challenge.getUuidChallenge());
            gen.writeEndObject();


    }
*/
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/helper/ChallengeJsonSerializer.java:ChallengeJsonSerializer.<init>
// Node: serialize
// Node: writeStartObject
// Node: writeStringField
// Node: getUuidChallenge
// Node: writeEndObject
package com.itachallenge.user.helper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
public class ObjectSerializer {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static byte[] serialize(Object obj) throws JsonProcessingException {
        return objectMapper.writeValueAsBytes(obj);
    }

    public static <T> T deserialize(byte[] bytes, Class<T> clazz) throws IOException {
        return objectMapper.readValue(bytes, clazz);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/main/java/com/itachallenge/user/helper/ObjectSerializer.java:ObjectSerializer.<init>
// Node: writeValueAsBytes
// Node: deserialize
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


// Node: setProperties
// Node: add
// Node: getReplicaSetUrl
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




// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/document/SolutionAttemptDocumentTest.java:SolutionAttemptDocumentTest.<init>
// Node: SolutionAttemptDocument
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




// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-user/src/test/java/com/itachallenge/user/document/UserSolutionDocumentTest.java:UserSolutionDocumentTest.<init>
// Node: UserSolutionDocument
// Node: argThat
package com.itachallenge.user.dto;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.assertEquals;

class AdminCreateUserRequestDtoTest {

    private static Validator validator;

    @BeforeAll
    static void setUpValidator() {
        try (ValidatorFactory factory = Validation.buildDefaultValidatorFactory()) {
            validator = factory.getValidator();
        }
    }

    @Test
    void whenUsernameIsBlank_thenValidationFails() {
        AdminCreateUserRequestDto request = new AdminCreateUserRequestDto();
        request.setUsername("");

        Set<ConstraintViolation<AdminCreateUserRequestDto>> violations = validator.validate(request);

        assertEquals(1, violations.size());
        assertEquals("Username must not be blank", violations.iterator().next().getMessage());
    }
}


// Node: setUpValidator
// Node: try
// Node: whenUsernameIsBlank_thenValidationFails
package com.itachallenge.common.exception;

public class BadRequestException extends RuntimeException {
    public BadRequestException(String message) {
        super(message);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/common/exception/BadRequestException.java:BadRequestException.<init>
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

package com.itachallenge.submission.enums;

import com.itachallenge.common.exception.BadRequestException;
import lombok.Getter;

import java.util.Arrays;

@Getter
public enum SubmissionStatus {
    SUBMITTED_COMPLETE("SUBMITTED_COMPLETE"),
    IN_PROGRESS("IN_PROGRESS"),
    SUBMITTED_INCOMPLETE("SUBMITTED_INCOMPLETE");

    private final String value;

    SubmissionStatus(String value) {
        this.value = value;
    }

    public static SubmissionStatus fromString(String status) {
        if (status == null || status.isBlank()) {
            throw new BadRequestException("status is required");
        }

        return Arrays.stream(SubmissionStatus.values())
                .filter(s -> status.equalsIgnoreCase(s.getValue()))
                .findFirst()
                .orElseThrow(() -> new BadRequestException("Invalid status: " + status));
    }
}


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


package com.itachallenge.challenge.proxy;


import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.challenge.config.PropertiesConfig;
import io.netty.channel.ChannelOption;
import io.netty.handler.timeout.ReadTimeoutHandler;
import io.netty.handler.timeout.WriteTimeoutHandler;
import org.apache.commons.validator.routines.UrlValidator;
import org.apache.logging.log4j.util.Strings;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import org.springframework.http.codec.ClientCodecConfigurer;
import org.springframework.http.codec.json.Jackson2JsonDecoder;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.ExchangeStrategies;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.netty.http.client.HttpClient;

import java.net.MalformedURLException;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

@Component
public class HttpProxy {

    private static final Logger log = LoggerFactory.getLogger(HttpProxy.class);

    private final PropertiesConfig config;


    private final WebClient client;
    protected static final String MALFORMED_URL_MSG = "Proxy: provided url is not valid: ";

    public HttpProxy(PropertiesConfig config) {
        this.config = config;
        client = WebClient.builder()
                .clientConnector(initReactorHttpClient(config.getConnectionTimeout()))
                .exchangeStrategies(initExchangeStrategies())
                .build();
    }

    //protected because it's used in test (timeout verification test)
    protected ReactorClientHttpConnector initReactorHttpClient(Integer connectionTimeout){
        HttpClient httpClient = HttpClient.create()
                .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, connectionTimeout)
                .responseTimeout(Duration.ofMillis(connectionTimeout))
                .compress(true)
                .doOnConnected(conn -> conn
                        .addHandlerLast(new ReadTimeoutHandler(connectionTimeout, TimeUnit.MILLISECONDS))
                        .addHandlerLast(new WriteTimeoutHandler(connectionTimeout, TimeUnit.MILLISECONDS)));
        return new ReactorClientHttpConnector(httpClient);
    }

    private ExchangeStrategies initExchangeStrategies(){
        return ExchangeStrategies.builder()
                .codecs(this::initAcceptedCodecs)
                .build();
    }

    private void initAcceptedCodecs(ClientCodecConfigurer clientCodecConfigurer) {
        Integer maxBytesInMemory = config.getMaxBytesInMemory();
        ObjectMapper mapper = new ObjectMapper()
                .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        clientCodecConfigurer.defaultCodecs().maxInMemorySize(maxBytesInMemory);
        clientCodecConfigurer.customCodecs()
                .registerWithDefaultConfig(new Jackson2JsonDecoder(mapper, MediaType.TEXT_PLAIN));
    }

    public <T> Mono<T> getRequestData(String url, Class<T> clazz) {
        UrlValidator validator = new UrlValidator(UrlValidator.ALLOW_LOCAL_URLS); //allow localhost
        if (validator.isValid(url)) {
            String msg = Strings.concat("Proxy: Executing remote invocation to ",url);
            log.info(msg);
            return client.get()
                    .uri(url)
                    .retrieve()
                    .bodyToMono(clazz);
        } else {
            return Mono.error(new MalformedURLException(MALFORMED_URL_MSG +url));
        }
    }

    //protected because it's used in test (timeout verification test)
    protected WebClient getClient() {
        return client;
    }
}


// Node: initAcceptedCodecs
// Node: getMaxBytesInMemory
// Node: configure
// Node: defaultCodecs
// Node: maxInMemorySize
// Node: customCodecs
// Node: registerWithDefaultConfig
// Node: Jackson2JsonDecoder
// Node: UrlValidator
// Node: concat
// Node: MalformedURLException
package com.itachallenge.challenge.exception;

public class BadUUIDException extends Exception {
    public BadUUIDException(String msg){
        super(msg);
    }
    public BadUUIDException(){}
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/BadUUIDException.java:BadUUIDException.<init>
package com.itachallenge.challenge.exception;

public class NotFoundException extends RuntimeException{
    public NotFoundException(String message) {
        super(message);
    }

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/exception/NotFoundException.java:NotFoundException.<init>
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.*;
import com.itachallenge.challenge.dto.ChallengeDto;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.SolutionDto;
import com.itachallenge.challenge.document.ChallengeDocument;
import com.itachallenge.challenge.document.LanguageDocument;
import com.itachallenge.challenge.document.SolutionDocument;
import com.itachallenge.challenge.dto.*;
import com.itachallenge.challenge.enums.Topic;
import com.itachallenge.challenge.exception.*;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.ChallengeRepository;
import com.itachallenge.challenge.repository.SolutionRepository;
import io.micrometer.common.util.StringUtils;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import org.springframework.util.ReflectionUtils;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.lang.reflect.Field;
import java.time.LocalDateTime;
import java.util.*;
import java.util.function.Predicate;
import java.util.regex.Pattern;
import java.util.function.UnaryOperator;

@RequiredArgsConstructor
@Service
public class ChallengeServiceImpl implements IChallengeService {

    private static final Pattern UUID_FORM = Pattern.compile("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", Pattern.CASE_INSENSITIVE);

    private static final Logger log = LoggerFactory.getLogger(ChallengeServiceImpl.class);

    private static final String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";

    private static final String LANGUAGE_NOT_FOUND_ERROR = "Language with id: %s not found";

    private static final String NOT_FOUND = "not found";

    private final ChallengeRepository challengeRepository;
    private final ILanguageService iLanguageService;
    private final SolutionRepository solutionRepository;
    private final DocumentToDtoConverter<ChallengeDocument, ChallengeDto> challengeConverter;
    private final DocumentToDtoConverter<SolutionDocument, SolutionDto> solutionConverter;
    private final IUserService userService;
    private final ITagService tagService;

    @Cacheable(value = "challenges", key = "#id", unless = "#result==null")
    public Mono<ChallengeDto> getChallengeById(String id) {
        return validateUUID(id)
                .flatMap(challengeId -> challengeRepository.findByUuid(challengeId)
                        .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeId))))
                        .map(challenge -> challengeConverter.convertDocumentToDto(challenge, ChallengeDto.class))
                        .doOnSuccess(challengeDto -> log.info("Challenge found with ID: {}", challengeId))
                        .doOnError(error -> log.error("Error occurred while retrieving challenge: {}", error.getMessage()))
                );
    }

    @Override
    public Flux<GenericResultDto<ChallengeDto>> getChallengesByFilter(
            Optional<String> idLanguage,
            Optional<String> level,
            Optional<List<UUID>> tags,
            int offset,
            int limit) {

        Optional<UUID> uuidLanguage = idLanguage
                .filter(lang -> !lang.isBlank())
                .map(UUID::fromString);
        Predicate<ChallengeDocument> filterPredicate = buildFilterPredicate(uuidLanguage, level, tags);

        UnaryOperator<Flux<ChallengeDto>> paginator = flux -> flux.skip(offset)
                .take(limit == -1 ? Long.MAX_VALUE : limit);

        return getAndProcessChallenges(filterPredicate, paginator, offset, limit).flux();
    }

    @Override
    public Mono<GenericResultDto<ChallengeDto>> getRelatedChallenges(String challengeId) {
        return validateUUID(challengeId)
                .flatMap(validId -> challengeRepository.findByUuid(validId)
                        .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, validId))))
                        .flatMap(currentChallenge -> {
                            Optional<UUID> languageId = currentChallenge.getLanguages().stream()
                                    .map(LanguageDocument::getIdLanguage)
                                    .filter(Objects::nonNull)
                                    .findFirst();
                            Optional<String> level = Optional.ofNullable(currentChallenge.getLevel());
                            Optional<List<UUID>> tags = Optional.ofNullable(currentChallenge.getTags());

                            Predicate<ChallengeDocument> filterPredicate = buildFilterPredicate(languageId, level, tags)
                                    .and(challenge -> !challenge.getUuid().equals(validId));

                            UnaryOperator<Flux<ChallengeDto>> shufflerAndLimiter = flux -> flux
                                    .collectList()
                                    .flatMapMany(list -> {
                                        Collections.shuffle(list);
                                        return Flux.fromIterable(list);
                                    })
                                    .take(3);
                            return getAndProcessChallenges(filterPredicate, shufflerAndLimiter, 0, 3);
                        })
                );
    }

    private Predicate<ChallengeDocument> buildFilterPredicate(Optional<UUID> languageId,
                                                              Optional<String> level,
                                                              Optional<List<UUID>> tags) {
        return challenge -> {
            boolean matchesLanguage = languageId.isEmpty() || (
                    challenge.getLanguages() != null &&
                            challenge.getLanguages().stream()
                                    .anyMatch(lang -> lang.getIdLanguage() != null &&
                                            lang.getIdLanguage().equals(languageId.get()))
            );

            boolean matchesLevel = level.isEmpty() ||
                    level.get().equalsIgnoreCase(challenge.getLevel());

            boolean matchesTags = tags.isEmpty() || (
                    challenge.getTags() != null &&
                            challenge.getTags().stream().anyMatch(tags.get()::contains)
            );

            return matchesLanguage && matchesLevel && matchesTags;
        };
    }

    private Mono<GenericResultDto<ChallengeDto>> getAndProcessChallenges(
            Predicate<ChallengeDocument> predicate,
            UnaryOperator<Flux<ChallengeDto>> postProcessing,
            int offset, int limit) {

        Flux<ChallengeDto> filteredFlux = challengeRepository.findAllByUuidNotNullExcludingTestingValues()
                .filter(predicate)
                .map(challenge -> challengeConverter.convertDocumentToDto(challenge, ChallengeDto.class));

        Flux<ChallengeDto> processedFlux = postProcessing.apply(filteredFlux);

        return processedFlux.collectList()
                .map(challenges -> {
                    GenericResultDto<ChallengeDto> result = new GenericResultDto<>();
                    result.setInfo(offset, limit, challenges.size(), challenges.toArray(new ChallengeDto[0]));
                    return result;
                });
    }

    @Cacheable(value = "challenges", key = "{#offset, #limit}", unless = "#result==null")
    @Override
    public Mono<GenericResultDto<ChallengeDto>> getAllChallenges(int offset, int limit) {

        Mono<Long> countMono = challengeRepository.count();
        Flux<ChallengeDto> challengeDtoFlux = challengeConverter.convertDocumentFluxToDtoFlux(
                challengeRepository.findAllByUuidNotNullExcludingTestingValues()
                        .skip(offset)
                        .take(limit),
                ChallengeDto.class);

        return countMono.zipWith(challengeDtoFlux.collectList(), (totalCount, challenges) -> {
            ChallengeDto[] challengeArray = challenges.toArray(new ChallengeDto[0]);
            return new GenericResultDto<>(offset, limit, totalCount.intValue(), challengeArray);
        }).onErrorResume(e -> Mono.just(new GenericResultDto<>(offset, limit, 0, new ChallengeDto[0])));

    }

    @Cacheable(value = "solutions", key = "{#idChallenge, #idLanguage}", unless = "#result==null")
    @Override
    public Mono<GenericResultDto<SolutionDto>> getSolutions(String idChallenge, String idLanguage) {
        Mono<UUID> challengeIdMono = validateUUID(idChallenge);
        Mono<UUID> languageIdMono = validateUUID(idLanguage);

        return Mono.zip(challengeIdMono, languageIdMono)
                .flatMap(tuple -> {
                    UUID challengeId = tuple.getT1();
                    UUID languageId = tuple.getT2();

                    return challengeRepository.findByUuid(challengeId)
                            .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeId))))
                            .flatMapMany(challenge -> Flux.fromIterable(challenge.getSolutions())
                                    .flatMap(solutionId -> solutionRepository.findById(solutionId))
                                    .filter(solution -> solution.getIdLanguage().equals(languageId))
                            )
                            .collectList()
                            .flatMap(solutions ->
                                    solutionConverter.convertDocumentFluxToDtoFlux(Flux.fromIterable(solutions), SolutionDto.class)
                                            .collectList()
                            )
                            .map(solutionDtos -> {
                                GenericResultDto<SolutionDto> resultDto = new GenericResultDto<>();
                                resultDto.setInfo(0, solutionDtos.size(), solutionDtos.size(), solutionDtos.toArray(new SolutionDto[0]));
                                return resultDto;
                            });
                });
    }

    @CacheEvict(value = {"challenges", "solutions"}, allEntries = true)
    @Override
    public Mono<SolutionDto> addSolution(SolutionDto solutionDto) {

        Mono<UUID> challengeIdMono = validateUUID(String.valueOf(solutionDto.getIdChallenge()));
        Mono<UUID> languageIdMono = validateUUID(String.valueOf(solutionDto.getIdLanguage()));

        return Mono.zip(challengeIdMono, languageIdMono)
                .flatMap(tuple -> {
                    UUID challengeId = tuple.getT1();
                    UUID languageId = tuple.getT2();


                    return iLanguageService.findByIdLanguage(languageId)
                            .switchIfEmpty(Mono.error(new LanguageNotFoundException(String.format(LANGUAGE_NOT_FOUND_ERROR, languageId))))
                            .flatMap(language -> challengeRepository.findByUuid(challengeId))
                            .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeId))))
                            .flatMap(challenge -> {
                                SolutionDocument solutionDocument = new SolutionDocument();
                                solutionDocument.setSolutionText(solutionDto.getSolutionText());
                                solutionDocument.setIdLanguage(languageId);
                                solutionDocument.setUuid(UUID.randomUUID());

                                return solutionRepository.save(solutionDocument)
                                        .flatMap(solution -> {
                                            if (challenge.getSolutions() == null) {
                                                List<UUID> list = new ArrayList<>();
                                                challenge.setSolutions(list);
                                            }
                                            challenge.getSolutions().add(solution.getUuid());
                                            return challengeRepository.save(challenge);
                                        })
                                        .flatMap(challengeSaved ->
                                                Mono.from(solutionConverter.convertDocumentFluxToDtoFlux(Flux.just(solutionDocument),
                                                        SolutionDto.class)))
                                        .map(solution -> {
                                            GenericResultDto<SolutionDto> resultDto = new GenericResultDto<>();
                                            resultDto.setInfo(0, 1, 1, new SolutionDto[]{solution});
                                            solution.setIdChallenge(challengeId);
                                            return solution;
                                        });
                            });
                });

    }

    @Override
    public Mono<String> updateResourceByUuid(String id, Map<String, Object> updates) {
        return validateUUID(id)
                .flatMap(resourceId -> challengeRepository.findByUuid(resourceId)
                        .switchIfEmpty(Mono.error(new ResourceNotFoundException("Resource with id " + resourceId + NOT_FOUND)))
                        .flatMap(resource -> {
                            updates.forEach((key, value) -> {
                                Field field = ReflectionUtils.findField(resource.getClass(), key);
                                if (field != null) {
                                    ReflectionUtils.setField(field, resource, value);
                                }
                            });
                            return challengeRepository.save(resource);
                        })
                        .then(Mono.just("Resource updated successfully"))
                )
                .doOnSuccess(resultDto -> log.info("Resource updated with ID: {}", id))
                .doOnError(error -> log.error("Error occurred while updating resource: {}", error.getMessage()));
    }

    @Override
    public Mono<ChallengeDto> addChallenge(ChallengeCreateDto challengeCreateDto) {
        String codingLanguage = challengeCreateDto.getLanguage();

        Topic topic;
        try {
            topic = Topic.fromDisplayName(String.valueOf(challengeCreateDto.getTopic()));
        } catch (IllegalArgumentException e) {
            return Mono.error(new IllegalArgumentException("Invalid topic provided: " + challengeCreateDto.getTopic()));
        }

        return iLanguageService.findFirstByLanguageName(codingLanguage)
                .switchIfEmpty(Mono.error(new LanguageNotFoundException("Language " + codingLanguage + " is not valid")))
                .flatMap(existingLanguage -> {
                    SolutionDocument solution = SolutionDocument.builder()
                            .uuid(UUID.randomUUID())
                            .solutionText(challengeCreateDto.getSolution())
                            .idLanguage(existingLanguage.getIdLanguage())
                            .build();
                    return solutionRepository.save(solution)
                            .flatMap(savedSolution -> tagService.getValidatedTags(challengeCreateDto.getTags())
                                    .flatMap(allTagsValid -> {
                                        if (!allTagsValid) {
                                            return Mono.error(new TagNotFoundException(
                                                    "One or more tags are invalid"));
                                        }
                                        ChallengeDocument challenge = buildChallengeDocument(
                                                challengeCreateDto,
                                                existingLanguage,
                                                savedSolution.getUuid(),
                                                topic,
                                                challengeCreateDto.getTags());
                                        return challengeRepository.save(challenge);
                                    })
                            );
                })
                .map(savedChallenge ->
                        challengeConverter.convertDocumentToDto(savedChallenge, ChallengeDto.class));
    }

    private ChallengeDocument buildChallengeDocument(ChallengeCreateDto dto, LanguageDocument language, UUID solutionId, Topic topic, List<UUID> tags) {
        DetailDocument detail = new DetailDocument(dto.getDescription());

        return ChallengeDocument.builder()
                .uuid(UUID.randomUUID())
                .title(dto.getChallengeTitle())
                .level(dto.getLevel().toString())
                .creationDate(LocalDateTime.now())
                .detail(detail)
                .languages(Set.of(language))
                .solutions(List.of(solutionId))
                .topic(topic)
                .tags(tags)
                .build();
    }


    private Mono<UUID> validateUUID(String id) {
        boolean validUUID = !StringUtils.isEmpty(id) && UUID_FORM.matcher(id).matches();

        if (!validUUID) {
            log.warn("Invalid ID format.");
            return Mono.error(new BadUUIDException("Invalid ID format. Please indicate the correct format."));
        }

        return Mono.just(UUID.fromString(id));
    }

    public Mono<DeleteResponseDto> deleteChallengeById(String id) {

        return validateUUID(id)
                .flatMap(uuid -> challengeRepository.findByUuid(uuid)
                        .switchIfEmpty(Mono.error(new ChallengeNotFoundException(
                                String.format(CHALLENGE_NOT_FOUND_ERROR, id)
                        )))
                        .then(challengeRepository.deleteByUuid(uuid))
                        .thenReturn(new DeleteResponseDto(
                                id,
                                "Challenge deleted successfully"
                        ))
                )
                .doOnSuccess(response -> log.info("Challenge deleted with ID: {}", response.getId()))
                .doOnError(error -> log.error("Error while deleting challenge: {}", error.getMessage()));
    }

    @Override
    public Mono<ChallengeListDto> getChallengesByTopic(Topic topic, int page, int size) {
        Logger log = LoggerFactory.getLogger(getClass());
        challengeRepository.findByTopic(topic)
                .count()
                .doOnSuccess(count -> log.info("All challenges found: {}", count)).subscribe();
        if (topic == null) {
            return Mono.just(ChallengeListDto.builder()
                    .results(new ArrayList<>())
                    .total(0)
                    .build());
        }

        Flux<ChallengeDocument> challengesFlux = challengeRepository.findByTopic(topic);

        if (challengesFlux == null) {
            return Mono.just(ChallengeListDto.builder()
                    .results(new ArrayList<>())
                    .total(0)
                    .build());
        }

        return challengeRepository.findByTopic(topic)
                .doOnNext(challenge -> log.info("Challenge found: {}", challenge))
                .collectList()
                .doOnSuccess(challenges -> log.info("All found: {}", challenges.size()))
                .defaultIfEmpty(new ArrayList<>())
                .map(challenges -> {
                    List<ChallengeDto> challengeDtos = challenges.stream()
                            .map(challenge -> challengeConverter.convertDocumentToDto(challenge, ChallengeDto.class))
                            .toList();

                    return ChallengeListDto.builder()
                            .results(challengeDtos)
                            .total(challengeDtos.size())
                            .build();
                })
                .switchIfEmpty(Mono.just(ChallengeListDto.builder()
                        .results(new ArrayList<>())
                        .total(0)
                        .build()));

    }

    @Override
    public Mono<ChallengeDto> updateChallenge(String challengeId, ChallengeCreateDto challengeCreateDto) {
        validateUUID(String.valueOf(challengeId));
        String codingLanguage = challengeCreateDto.getLanguage();
        return iLanguageService.findFirstByLanguageName(codingLanguage)
                .switchIfEmpty(Mono.error(new LanguageNotFoundException("Language " + codingLanguage + " is not valid")))
                .flatMap(newLanguage -> validateUUID(String.valueOf(challengeId))
                        .flatMap(validId -> challengeRepository.findByUuid(validId)
                                .switchIfEmpty(Mono.error(new ChallengeNotFoundException(
                                        String.format(CHALLENGE_NOT_FOUND_ERROR, validId))))
                                .flatMap(challengeDocument -> {
                                    log.info("Challenge found for challengeId: {}", validId);

                                    return tagService.getValidatedTags(challengeCreateDto.getTags())
                                            .flatMap(allTagsValid -> {
                                                if (!allTagsValid) {
                                                    return Mono.error(new TagNotFoundException("One or more tags are invalid"));
                                                }

                                                SolutionDocument solutionDocument = buildSolutionDocument(newLanguage, challengeCreateDto);
                                                return solutionRepository.save(solutionDocument)
                                                        .flatMap(savedSolution -> {
                                                            log.info("New solution successfully saved for challengeId: {}", validId);
                                                            ChallengeDocument newChallengeDocument = updateChallengeDocument(
                                                                    challengeDocument, challengeCreateDto, newLanguage, solutionDocument.getUuid());

                                                            return challengeRepository.save(newChallengeDocument)
                                                                    .map(savedChallenge -> {
                                                                        log.info("Challenge {} successfully updated in database.", validId);
                                                                        log.debug("Saved challenge tags: {}", savedChallenge.getTags());
                                                                        return challengeConverter.convertDocumentToDto(savedChallenge,
                                                                                ChallengeDto.class);
                                                                    });
                                                        });
                                            });
                                }))
                );
    }

    @Override
    public Mono<BookmarkDto> addChallengeToBookmarks(String challengeId, String userId) {

        Mono<UUID> challengeIdMono = validateUUID(String.valueOf(challengeId));
        Mono<UUID> userIdMono = validateUUID(String.valueOf(userId));

        return Mono.zip(challengeIdMono, userIdMono)
                .flatMap(Uuidtuple -> {
                    UUID challengeUuid = Uuidtuple.getT1();
                    UUID userUuid = Uuidtuple.getT2();

                    return challengeRepository.findByUuid(challengeUuid)
                            .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid))))
                            .flatMap(challenge -> userService.addChallengeToBookmarks(userUuid.toString(), challengeUuid.toString())
                                    .onErrorResume(throwable -> Mono.error(new InternalServerErrorException(throwable.getMessage())))
                                    .flatMap(isAddedToUsersBookmarks -> {
                                        if (Boolean.TRUE.equals(isAddedToUsersBookmarks) ||
                                                Optional.ofNullable(challenge.getTimesBookmark()).orElse(0) == 0) {
                                            challenge.increaseTimesBookmark();
                                            return challengeRepository.save(challenge);
                                        }
                                        return Mono.just(challenge);
                                    })
                                    .map(savedChallenge -> new BookmarkDto(true, savedChallenge.getTimesBookmark())));
                });
    }

    @Override
    public Mono<BookmarkDto> removeChallengeFromBookmarks(String challengeId, String userId) {
        Mono<UUID> challengeIdMono = validateUUID(String.valueOf(challengeId));
        Mono<UUID> languageIdMono = validateUUID(String.valueOf(userId));

        return Mono.zip(challengeIdMono, languageIdMono)
                .flatMap(Uuidtuple -> {
                    UUID challengeUuid = Uuidtuple.getT1();
                    UUID userUuid = Uuidtuple.getT2();

                    return challengeRepository.findByUuid(challengeUuid)
                            .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid))))
                            .flatMap(challenge -> userService.removeChallengeFromBookmarks(userUuid.toString(), challengeUuid.toString())
                                    .onErrorResume(throwable -> Mono.error(new InternalServerErrorException(throwable.getMessage())))
                                    .flatMap(isRemovedFromUsersBookmarks -> {
                                        if (Boolean.TRUE.equals(isRemovedFromUsersBookmarks) ||
                                                Optional.ofNullable(challenge.getTimesBookmark()).orElse(0) == 0) {
                                            challenge.decreaseTimesBookmark();
                                            return challengeRepository.save(challenge);
                                        }
                                        return Mono.just(challenge);
                                    })
                                    .map(savedChallenge -> new BookmarkDto(false, savedChallenge.getTimesBookmark())));
                });
    }

    @Override
    public Mono<SolvedDto> addChallengeToSolved(String challengeId) {
        Mono<UUID> challengeIdMono = validateUUID(challengeId);

        return challengeIdMono
                .flatMap(challengeUuid ->
                        challengeRepository.findByUuid(challengeUuid)
                                .switchIfEmpty(Mono.error(new ChallengeNotFoundException(
                                        String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid))))
                                .flatMap(challenge -> {
                                    challenge.increaseTimesSolved();
                                    return challengeRepository.save(challenge);
                                })
                                .map(updatedChallenge -> new SolvedDto(true, updatedChallenge.getTimesSolved()))
                );
    }

    private SolutionDocument buildSolutionDocument(LanguageDocument language, ChallengeCreateDto challengeCreateDto) {
        return SolutionDocument.builder()
                .uuid(UUID.randomUUID())
                .idLanguage(language.getIdLanguage())
                .solutionText(challengeCreateDto.getSolution())
                .build();
    }

    private static ChallengeDocument updateChallengeDocument(ChallengeDocument currentChallenge, ChallengeCreateDto dto, LanguageDocument language, UUID solutionId) {
        currentChallenge.setTitle(dto.getChallengeTitle());
        currentChallenge.setLevel(String.valueOf(dto.getLevel()));
        currentChallenge.setDetail(new DetailDocument(dto.getDescription()));
        currentChallenge.setLanguages(Set.of(language));
        currentChallenge.setSolutions(List.of(solutionId));
        currentChallenge.setTopic(dto.getTopic());
        currentChallenge.setTags(dto.getTags());

        return currentChallenge;
    }
}

package com.itachallenge.challenge.service;

import com.itachallenge.challenge.dto.FavoriteDto;
import com.itachallenge.challenge.exception.BadUUIDException;
import com.itachallenge.challenge.exception.ChallengeNotFoundException;
import com.itachallenge.challenge.exception.InternalServerErrorException;
import com.itachallenge.challenge.repository.ChallengeRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.util.Optional;
import java.util.UUID;
import java.util.regex.Pattern;

@Service
@RequiredArgsConstructor
public class FavoriteServiceImpl implements IFavoriteService {

    private static final Logger log = LoggerFactory.getLogger(FavoriteServiceImpl.class);
    private static final Pattern UUID_FORM = Pattern.compile(
            "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", Pattern.CASE_INSENSITIVE);
    private static final String CHALLENGE_NOT_FOUND_ERROR = "Challenge with id: %s not found";

    private final ChallengeRepository challengeRepository;
    private final IUserService userService;

    @Override
    public Mono<FavoriteDto> addChallengeToFavorites(String challengeId, String userId) {
        Mono<UUID> challengeIdMono = validateUUID(challengeId);
        Mono<UUID> userIdMono = validateUUID(userId);

        return Mono.zip(challengeIdMono, userIdMono)
                .flatMap(tuple -> {
                    UUID challengeUuid = tuple.getT1();
                    UUID userUuid = tuple.getT2();

                    return challengeRepository.findByUuid(challengeUuid)
                            .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid))))
                            .flatMap(challenge -> userService.addChallengeToFavorites(userUuid.toString(), challengeUuid.toString())
                                    .onErrorResume(e -> Mono.error(new InternalServerErrorException(e.getMessage())))
                                    .flatMap(added -> {
                                        if (Boolean.TRUE.equals(added) ||
                                                Optional.ofNullable(challenge.getTimesFavorite()).orElse(0) == 0) {
                                            challenge.increaseTimesFavorite();
                                            return challengeRepository.save(challenge);
                                        }
                                        return Mono.just(challenge);
                                    })
                                    .map(saved -> new FavoriteDto(true, saved.getTimesFavorite())));
                });
    }

    @Override
    public Mono<FavoriteDto> removeChallengeFromFavorites(String challengeId, String userId) {
        Mono<UUID> challengeIdMono = validateUUID(challengeId);
        Mono<UUID> userIdMono = validateUUID(userId);

        return Mono.zip(challengeIdMono, userIdMono)
                .flatMap(tuple -> {
                    UUID challengeUuid = tuple.getT1();
                    UUID userUuid = tuple.getT2();

                    return challengeRepository.findByUuid(challengeUuid)
                            .switchIfEmpty(Mono.error(new ChallengeNotFoundException(String.format(CHALLENGE_NOT_FOUND_ERROR, challengeUuid))))
                            .flatMap(challenge -> userService.removeChallengeFromFavorites(userUuid.toString(), challengeUuid.toString())
                                    .onErrorResume(e -> Mono.error(new InternalServerErrorException(e.getMessage())))
                                    .flatMap(removed -> {
                                        if (Boolean.TRUE.equals(removed) ||
                                                Optional.ofNullable(challenge.getTimesFavorite()).orElse(0) == 0) {
                                            challenge.decreaseTimesFavorite();
                                            return challengeRepository.save(challenge);
                                        }
                                        return Mono.just(challenge);
                                    })
                                    .map(saved -> new FavoriteDto(false, saved.getTimesFavorite())));
                });
    }

    private Mono<UUID> validateUUID(String id) {
        boolean validUUID = id != null && UUID_FORM.matcher(id).matches();

        if (!validUUID) {
            log.warn("Invalid ID format.");
            return Mono.error(new BadUUIDException("Invalid ID format. Please indicate the correct format."));
        }

        return Mono.just(UUID.fromString(id));
    }
}

package com.itachallenge.challenge.service;

import com.itachallenge.challenge.document.TagDocument;
import com.itachallenge.challenge.dto.GenericResultDto;
import com.itachallenge.challenge.dto.TagDto;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.TagNotFoundException;
import com.itachallenge.challenge.helper.DocumentToDtoConverter;
import com.itachallenge.challenge.repository.TagRepository;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class TagServiceImpl implements ITagService {

    private static final Logger log = LoggerFactory.getLogger(TagServiceImpl.class);

    private final TagRepository tagRepository;
    private final DocumentToDtoConverter<TagDocument, TagDto> tagConverter;

    @Cacheable(value = "tagsByLanguage")
    @Override
    public Mono<GenericResultDto<TagDto>> getTagsByLanguageId(UUID languageId) {
        if (languageId == null) {
            log.warn("[TagService] languageId is null");
            return Mono.error(new IllegalArgumentException("languageId cannot be null"));
        }

        return tagConverter.convertDocumentFluxToDtoFlux(tagRepository.findByLanguageId(languageId), TagDto.class)
                .doOnError(e -> log.error("[TagService] Error converting documents to DTO:", e))
                .collectList()
                .doOnError(e -> log.error("[TagService] Error collecting tag list:", e))
                .map(tagList -> {
                    log.debug("[TagService] Total tags found: {}", tagList.size());
                    GenericResultDto<TagDto> resultDto = new GenericResultDto<>();
                    resultDto.setInfo(0, tagList.size(), tagList.size(), tagList.toArray(new TagDto[0]));
                    return resultDto;
                })
                .doOnError(e -> log.error("[TagService] Error mapping final result:", e));
    }

    @Override
    public Set<TagDocument> convertIdTagFromTagDocument(List<UUID> tagsAssigned) {
        return tagsAssigned.stream()
                .map(tag -> tagRepository.findById(tag)
                        .switchIfEmpty(Mono.error(new TagNotFoundException("Tag not found: " + tag)))
                        .block()
                )
                .collect(Collectors.toSet());
    }
    
    @Override
    public Mono<Boolean> getValidatedTags(List<UUID> tagIds) {
        return validateNoDuplicatesUUIDTags(tagIds).
                then(validateAllUUIDTagsExist(tagIds));
    }
    
    private Mono<Boolean> validateNoDuplicatesUUIDTags(List<UUID> tagIds) {
        return Flux.fromIterable(tagIds)
                .groupBy(id -> id)
                .flatMap(group -> group.count()
                        .filter(cnt -> cnt > 1)
                        .map(cnt -> group.key()))
                .next()
                .flatMap(dup ->
                        Mono.error(new BadRequestException("tag UUID duplicated: " + dup))
                )
                .hasElement();
    }
    
    private Mono<Boolean> validateAllUUIDTagsExist(List<UUID> tagIds) {
        return Flux.fromIterable(tagIds)
                .flatMap(tagId -> tagRepository.findById(tagId)
                        .switchIfEmpty(Mono.error(new TagNotFoundException("Tag not found: " + tagId))))
                .count()
                .map(count -> count == tagIds.size())
                .hasElement();
    }
}


// Node: groupBy
// Node: hasElement
package com.itachallenge.challenge.service;

import com.itachallenge.challenge.enums.UserChallengeActionType;
import com.itachallenge.common.exception.BadRequestException;
import com.itachallenge.challenge.exception.InternalServerErrorException;
import com.itachallenge.challenge.exception.UserNotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.util.UriComponentsBuilder;
import reactor.core.publisher.Mono;

@Service
public class UserServiceImpl implements IUserService {

    private static final Logger log = LoggerFactory.getLogger(UserServiceImpl.class);

    private final WebClient.Builder webClientBuilder;

    private final String userServiceUrl;
    private final String X_FAVORITE_MESSAGE = "X-Favorite-Message";
    private final String X_BOOKMARK_MESSAGE = "X-Bookmark-Message";
    private final String favoritesPath;
    private final String bookmarksPath;

    public UserServiceImpl(
            WebClient.Builder webClientBuilder,
            @Value("${user.service.url}") String userServiceUrl,
            @Value("${user.endpoints.favorites}") String favoritesPath,
            @Value("${user.endpoints.bookmarks}") String bookmarksPath) {
        this.webClientBuilder = webClientBuilder;
        this.userServiceUrl = userServiceUrl;
        this.favoritesPath = favoritesPath;
        this.bookmarksPath = bookmarksPath;
    }

    @Override
    public Mono<Boolean> addChallengeToFavorites(String userId, String challengeId) {
        return callEndpoint(userId, challengeId, UserChallengeActionType.FAVORITES, X_FAVORITE_MESSAGE, HttpMethod.POST);
    }

    @Override
    public Mono<Boolean> addChallengeToBookmarks(String userId, String challengeId) {
        return callEndpoint(userId, challengeId, UserChallengeActionType.BOOKMARKS, X_BOOKMARK_MESSAGE, HttpMethod.POST);
    }

    @Override
    public Mono<Boolean> removeChallengeFromFavorites(String userId, String challengeId) {
        return callEndpoint(userId, challengeId, UserChallengeActionType.FAVORITES, X_FAVORITE_MESSAGE, HttpMethod.DELETE);
    }

    @Override
    public Mono<Boolean> removeChallengeFromBookmarks(String userId, String challengeId) {
        return callEndpoint(userId, challengeId, UserChallengeActionType.BOOKMARKS, X_BOOKMARK_MESSAGE, HttpMethod.DELETE);
    }

    private Mono<Boolean> callEndpoint(String userId, String challengeId, UserChallengeActionType type, String errorHeader, HttpMethod method) {
        String url = buildUrl(userId, challengeId, type);
        log.debug("Calling {} endpoint with method={} and URL={}", type.name().toLowerCase(), method, url);

        return webClientBuilder.build()
                .method(method)
                .uri(url)
                .retrieve()
                .onStatus(HttpStatus.NOT_FOUND::equals, response -> {
                    log.info("User not found with id: {}", userId);
                    return Mono.error(new UserNotFoundException("User not found"));
                })
                .onStatus(HttpStatus.BAD_REQUEST::equals, response -> {
                    String errorMessage = response.headers().header(errorHeader).stream()
                            .findFirst().orElse("Unknown error");
                    log.warn("UserService returned 400: {}", errorMessage);
                    return Mono.error(new BadRequestException(errorMessage));
                })
                .onStatus(HttpStatus.INTERNAL_SERVER_ERROR::equals, response -> {
                    String errorMessage = response.headers().header(errorHeader).stream()
                            .findFirst().orElse("Unknown error");
                    log.warn("UserService returned 500: {}", errorMessage);
                    return Mono.error(new InternalServerErrorException(errorMessage));
                })
                .bodyToMono(Boolean.class);
    }

    private String buildUrl(String userId, String challengeId, UserChallengeActionType type){

        String template = switch (type) {
            case FAVORITES -> favoritesPath;
            case BOOKMARKS -> bookmarksPath;
        };

        return UriComponentsBuilder.fromHttpUrl(userServiceUrl)
                .path(template)
                .buildAndExpand(userId, challengeId)
                .toUriString();
    }
}


// Node: toLowerCase
package com.itachallenge.challenge.validator;

import com.itachallenge.challenge.annotations.ValidGenericPattern;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.regex.Pattern;

@Component
public class GenericPatternValidator implements ConstraintValidator<ValidGenericPattern, String> {
    @Value("${validation.number}")
    private String defaultPattern;
    private Pattern pattern;

    @Override
    public void initialize(ValidGenericPattern constraintAnnotation) {
        this.pattern = Pattern.compile(constraintAnnotation.pattern().isEmpty() ? defaultPattern : constraintAnnotation.pattern());
    }

    @Override
    public boolean isValid(String value, ConstraintValidatorContext context) {
        return pattern.matcher(value).matches();
    }
}


package com.itachallenge.challenge.helper;

import jakarta.validation.constraints.NotNull;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;

/*
Clase puede ser de mucha utilidad para mejorar la eficiencia
en crear tests (ej: load json for expected data)
 */
public class ResourceHelper {

    private Resource resource;
    private String resourcePath;
    private static final Logger log = LoggerFactory.getLogger(ResourceHelper.class);

    //if path null -> ClassPathResource throws IllegalArgumentException
    public ResourceHelper(@NotNull String resourcePath) {
        this.resourcePath = resourcePath;
        resource = new ClassPathResource(this.resourcePath);
    }

    //https://commons.apache.org/proper/commons-io/apidocs/org/apache/commons/io/FileUtils.html
    public Optional<String> readResourceAsString (){

        Optional<String> result = Optional.empty();
        try {
            result = Optional.of(FileUtils.readFileToString(resource.getFile(), StandardCharsets.UTF_8));
        } catch (IOException ex) {
            log.error(getResourceErrorMessage("loading/reading").concat(ex.getMessage()));
        }
        return result;
    }

    private String getResourceErrorMessage(String action){
        String resourceIdentifier = Objects.requireNonNullElseGet(resourcePath, () -> resource.getDescription());
        return "Exception when " + action + " " + resourceIdentifier + " resource: \n";
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/helper/ResourceHelper.java:ResourceHelper.<init>
// Node: tests
// Node: ResourceHelper
// Node: ClassPathResource
// Node: readResourceAsString
// Node: readFileToString
// Node: getFile
// Node: getResourceErrorMessage
// Node: requireNonNullElseGet
package com.itachallenge.challenge.helper;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
public class ObjectSerializer {

    private static final ObjectMapper objectMapper = new ObjectMapper();

    public static byte[] serialize(Object obj) throws JsonProcessingException {
        return objectMapper.writeValueAsBytes(obj);
    }

    public static <T> T deserialize(byte[] bytes, Class<T> clazz) throws IOException {
        return objectMapper.readValue(bytes, clazz);
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/main/java/com/itachallenge/challenge/helper/ObjectSerializer.java:ObjectSerializer.<init>
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonSetter;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.UUID;

@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class LanguageDto{

    @JsonProperty(value = "id_language", index = 0)
    private UUID languageId;

    @JsonProperty(value = "language_name", index = 1)
    private String languageName;

    @JsonProperty(value = "language_image", index = 2)
    private String languageImage;

    @JsonSetter("language_image")
    public void setLanguageImage(String languageImage) {
       String defaultImage = "https://default-image.com/default.png";
        this.languageImage = (languageImage != null && !languageImage.trim().isEmpty()) ? languageImage.trim() : defaultImage;
    }
}


// Node: setLanguageImage
package com.itachallenge.challenge.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
//@Configuration not used due there isn't any @bean method
public class PropertiesConfig {

    @Value("${url.connection_timeout}")
    private Integer connectionTimeout;//millis

    @Value("${url.maxBytesInMemory}")
    private Integer maxBytesInMemory;

    public Integer getConnectionTimeout() {
        return connectionTimeout;
    }

    public Integer getMaxBytesInMemory() {
        return maxBytesInMemory;
    }
}


package com.itachallenge.challenge.enums;

public enum Topic {
    ALL("All"),
    COMPONENTS("Components"),
    USE_STATE_USE_EFFECT("useState & useEffect"),
    EVENTS("Events"),
    CONDITIONAL_RENDERING("Conditional Rendering"),
    LISTS("Lists"),
    STYLES("Styles"),
    DEBUGGING("Debugging"),
    REACT_ROUTER("React Router"),
    DEFAULT_TOPIC("Default topic");

    private final String displayName;

    Topic(String displayName) {
        this.displayName = displayName;
    }

    public String getDisplayName() {
        return displayName;
    }

    public static Topic fromDisplayName(String displayName) {
        for (Topic topic : Topic.values()) {
            if (topic.getDisplayName().equalsIgnoreCase(displayName)) {
                return topic;
            }
        }
        throw new IllegalArgumentException("No enum constant with display name " + displayName);
    }


}



// Node: getDisplayName
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

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/submission/mapper/SubmissionMapperTest.java:SubmissionMapperTest.<init>
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


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-challenge/src/test/java/com/itachallenge/submission/document/SubmissionDocumentTest.java:SubmissionDocumentTest.<init>
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


// Node: shouldReturnSubmittedIncompleteIgnoringCase
// Node: readResourceAsObject
// Node: println
package com.itachallenge.challenge.proxy;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.challenge.helper.ResourceHelper;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.core.env.Environment;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientException;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.io.IOException;
import java.util.List;
import java.util.stream.Stream;

import static org.assertj.core.api.Assertions.assertThat;


@ExtendWith(SpringExtension.class)
@SpringBootTest
public class HttpProxyTest {

    @Autowired
    private Environment env;

    @Autowired
    private HttpProxy httpProxy;

    private static MockWebServer mockWebServer;

    private static final String RESOURCE_JSON_PATH = "json/resource.json";

    private static final String TOPIC_JSON_PATH = "json/topic.json";

    private static final String USER_RESOURCE_PATH = "json/user-resource.json";


    @BeforeAll
    static void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start();

    }

    @AfterAll
    static void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @ParameterizedTest
    @DisplayName("GET request test")
    @MethodSource("getRequestValues")
    <T> void getRequestDataTest(String dummyJsonPath, Class<T> expectedType){
        String expectedBody = readResourceAsString(dummyJsonPath);
        T expectedObject = readResourceAsObject(dummyJsonPath, expectedType);

        MockResponse mockResponse = new MockResponse()
                .addHeader("Content-Type", "application/json")
                .setBody(expectedBody);
        mockWebServer.enqueue(mockResponse);

        String url = String.format("http://localhost:%s", mockWebServer.getPort());
        Mono<T> response = httpProxy.getRequestData(url,expectedType);

        StepVerifier.create(response)
                .assertNext(resource ->
                        assertThat(resource).usingRecursiveComparison().isEqualTo(expectedObject))
                .verifyComplete();
    }

    private static Stream<Arguments> getRequestValues(){
        return Stream.of(
                Arguments.of(RESOURCE_JSON_PATH, ResourceTestDto.class),
                Arguments.of(TOPIC_JSON_PATH, TopicTestDto.class),
                Arguments.of(USER_RESOURCE_PATH, UserResourceTestDto.class)
        );
    }

    @Test
    @DisplayName("Timeout verification")
    void timeoutTest() {
        int absurdTimeout = Integer.parseInt(env.getProperty("url.fake_connection_timeout"));
        //System.out.println(absurdValue); // = 1
        WebClient absurdWebClient = httpProxy.getClient().mutate()
                .clientConnector(httpProxy.initReactorHttpClient(absurdTimeout))
                .build();

        String url = env.getProperty("url.ds_test"); //the same as opendata
        //System.out.println(url);
        Mono<Object> responsePublisher = absurdWebClient.get()
                .uri(url)
                .exchangeToMono(response ->
                        response.statusCode().equals(HttpStatus.OK) ?
                                response.bodyToMono(Object.class) : //doesn't matter, expecting NO OK response
                                response.createException().flatMap(Mono::error));

        StepVerifier.create(responsePublisher)
                .expectError(WebClientException.class)
                .verify();
    }

    @Test
    @DisplayName("Requesting an invalid url test")
    void providedUrlNotValidTest() {
        String wrongUrl = String.format("httKKp://localhost:%s", mockWebServer.getPort());
        String expectedErrorMsg = httpProxy.MALFORMED_URL_MSG +wrongUrl;

        Mono<Object> responsePublisher = httpProxy.getRequestData(wrongUrl, Object.class);

        StepVerifier.create(responsePublisher)
                .expectErrorMessage(expectedErrorMsg)
                .verify();
    }

    @Test
    @DisplayName("Target client is not available (500) test")
    void clientIsDownTest(){
        mockWebServer.enqueue(
                new MockResponse().setResponseCode(HttpStatus.INTERNAL_SERVER_ERROR.value())); //500

        String url = String.format("http://localhost:%s", mockWebServer.getPort());
        Mono<ResourceTestDto> responsePublisher = httpProxy.getRequestData(url, ResourceTestDto.class);

        StepVerifier.create(responsePublisher)
                .expectError(WebClientException.class)
                .verify();
    }

    public static String readResourceAsString(String resourcePath){
        return new ResourceHelper(resourcePath).readResourceAsString().orElse(null);
    }

    public static <T> T readResourceAsObject(String resourcePath, Class<T> targetClass){
        String resourceAsString = readResourceAsString(resourcePath);
        try {
            ObjectMapper mapper = new ObjectMapper()
                    .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
            return mapper.readValue(resourceAsString, targetClass);
        }catch (JsonProcessingException ex){
            return null;
        }
    }

    //inner classes only for testing purposes
    @NoArgsConstructor
    @Getter
    @Setter
    static class ResourceTestDto {
        private String id;
        private String title;
        private String slug;
        private String description;
        private String url;
        private String resourceType;
        private String createdAt;
        private String updatedAt;
        private UserResourceTestDto user;
        private List<TopicTestDto> topics;
    }

    @NoArgsConstructor
    @Getter
    @Setter
    static class TopicTestDto {
        private String id;
        private String name;
        private String slug;
        private String categoryId;
        private String createdAt;
        private String updatedAt;
    }

    @NoArgsConstructor
    @Getter
    @Setter
    static class UserResourceTestDto {
        private String name;
        private String email;
    }
}

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


// Node: isValidUUID
// Node: ResourceBundleMessageSource
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


// Node: initMongoProperties
// Node: getHost
// Node: getFirstMappedPort
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

// Node: findFirstByLanguageName_test
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

// Node: testExecutionAndRollback
// Node: getCollectionNames
// Node: listCollectionNames
// Node: CountDownLatch
// Node: onNext
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

package com.itachallenge.challenge.helper;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

class ResourceHelperTest {

    @Test
    @DisplayName("Read a resource as String test")
    void readResourceAsStringTest (){
        ResourceHelper resourceHelper = new ResourceHelper("json/random.json");
        String expected = "{\"name\": \"RandomName\", \"num\": [1,2,3], \"happy\": true}";
        assertEquals(Optional.of(expected), resourceHelper.readResourceAsString());
    }

    @Test
    void failedReadResourceTest () {
        String invalidPath = "jsonx908erfd/Randosadn90dsmJson.json";
        ResourceHelper resourceHelper = new ResourceHelper(invalidPath);
        assertEquals(Optional.empty(), resourceHelper.readResourceAsString());
    }
}

// Node: readResourceAsStringTest
// Node: failedReadResourceTest
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


// Node: rightSerializationTest
// Node: rightDeserializationTest
// Node: languageImageShouldBeAValidURL
package com.itachallenge.challenge.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.itachallenge.challenge.enums.AssociationType;
import com.itachallenge.challenge.enums.ResourceContentType;
import com.itachallenge.challenge.enums.Topic;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.hibernate.validator.messageinterpolation.ResourceBundleMessageInterpolator;
import org.hibernate.validator.resourceloading.PlatformResourceBundleLocator;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

import static org.assertj.core.api.AssertionsForInterfaceTypes.assertThat;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

class ResourceDtoTest {

    private static Validator validator;

    @BeforeAll
    static void setupValidator() {
        Locale.setDefault(Locale.ENGLISH);
        ValidatorFactory factory = Validation.byDefaultProvider()
                .configure()
                .messageInterpolator(
                        new ResourceBundleMessageInterpolator(
                                new PlatformResourceBundleLocator("messages")
                        )
                )
                .buildValidatorFactory();
        validator = factory.getValidator();
    }


    @Test
    void rightSerializationTest() throws Exception {
        InputStream is = getClass().getClassLoader().getResourceAsStream("json/ResourceSerialized.json");

        Assertions.assertNotNull(is, "JSON not found!");

        String jsonContent = new BufferedReader(new InputStreamReader(is))
                .lines()
                .collect(Collectors.joining("\n"));

        System.out.println("JSON correct\n" + jsonContent);

        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.configure(DeserializationFeature.ACCEPT_EMPTY_STRING_AS_NULL_OBJECT, true);

        ResourceDto resource = objectMapper.readValue(jsonContent, ResourceDto.class);

        Assertions.assertNotNull(resource, "ResourceDto nout deserialized correctly!");

        Assertions.assertEquals("123e4567-e89b-12d3-a456-426614174000", resource.getResourceId().toString());
        Assertions.assertEquals("DEBUGGING FOR THE FIRST TIME", resource.getTitle());
        Assertions.assertEquals("A guide on how to start debugging", resource.getDescription());
        Assertions.assertEquals("https://youtubetutorial.com/debugging", resource.getUrl());

        Assertions.assertEquals(Topic.DEBUGGING, resource.getTopic(), "Incorrect topic");

        Assertions.assertEquals(ResourceContentType.BLOG, resource.getContentType());

        Assertions.assertNotNull(resource.getChallengeIds(), "Els IDs de challenge no són vàlids!");
        Assertions.assertEquals(2, resource.getChallengeIds().size(), "El nombre de challengeIds no és el correcte!");

        List<String> challengeIdsAsString = resource.getChallengeIds().stream()
                .map(UUID::toString)
                .collect(Collectors.toList());

        Assertions.assertTrue(challengeIdsAsString.contains("f47ac10b-58cc-4372-a567-0e02b2c3d479"), "El challengeId esperat no es troba!");
        Assertions.assertTrue(challengeIdsAsString.contains("550e8400-e29b-41d4-a716-446655440000"), "El challengeId esperat no es troba!");
    }


    @Test
    void rightDeserializationTest() throws Exception {
        String jsonContent = """
    {
        "resourceId": "123e4567-e89b-12d3-a456-426614174000",
        "title": "DEBUGGING FOR THE FIRST TIME",
        "description": "A guide on how to start debugging",
        "url": "https://youtubetutorial.com/debugging",
        "topic": "DEBUGGING", 
        "contentType": "BLOG",
        "challengeIds": [
            "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "550e8400-e29b-41d4-a716-446655440000"
        ]
    }
    """;

        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.configure(DeserializationFeature.ACCEPT_EMPTY_STRING_AS_NULL_OBJECT, true);

        ResourceDto resource = objectMapper.readValue(jsonContent, ResourceDto.class);

        Assertions.assertNotNull(resource);
        Assertions.assertEquals("123e4567-e89b-12d3-a456-426614174000", resource.getResourceId().toString());
        Assertions.assertEquals("DEBUGGING FOR THE FIRST TIME", resource.getTitle());
        Assertions.assertEquals("A guide on how to start debugging", resource.getDescription());
        Assertions.assertEquals("https://youtubetutorial.com/debugging", resource.getUrl());
        Assertions.assertEquals(Topic.DEBUGGING, resource.getTopic());
        Assertions.assertEquals(ResourceContentType.BLOG, resource.getContentType());

        Assertions.assertNotNull(resource.getChallengeIds());
        Assertions.assertEquals(2, resource.getChallengeIds().size());
        Assertions.assertTrue(resource.getChallengeIds().contains(UUID.fromString("f47ac10b-58cc-4372-a567-0e02b2c3d479")));
        Assertions.assertTrue(resource.getChallengeIds().contains(UUID.fromString("550e8400-e29b-41d4-a716-446655440000")));
    }


    @Test
    void builderAndGettersSettersTest() {
        UUID resourceId = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");
        List<UUID> challengeIds = List.of(
                UUID.fromString("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
                UUID.fromString("550e8400-e29b-41d4-a716-446655440000")
        );

        ResourceDto resource = ResourceDto.builder()
                .resourceId(resourceId)
                .title("DEBUGGING FOR THE FIRST TIME")
                .description("A guide on how to start debugging")
                .url("https://youtubetutorial.com/debugging")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(challengeIds)
                .build();

        Assertions.assertEquals(resourceId, resource.getResourceId());
        Assertions.assertEquals("DEBUGGING FOR THE FIRST TIME", resource.getTitle());

        resource.setTitle("UPDATED TITLE");
        Assertions.assertEquals("UPDATED TITLE", resource.getTitle());
    }

    @Test
    void equalsAndHashCodeTest() {
        UUID id = UUID.fromString("123e4567-e89b-12d3-a456-426614174000");

        ResourceDto resource1 = ResourceDto.builder()
                .resourceId(id)
                .title("DEBUGGING FOR THE FIRST TIME")
                .description("A guide on how to start debugging")
                .url("https://youtubetutorial.com/debugging")
                .topic(Topic.COMPONENTS)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(
                        UUID.fromString("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
                        UUID.fromString("550e8400-e29b-41d4-a716-446655440000")
                ))
                .build();

        ResourceDto resource2 = ResourceDto.builder()
                .resourceId(id)
                .title("DEBUGGING FOR THE FIRST TIME")
                .description("A guide on how to start debugging")
                .url("https://youtubetutorial.com/debugging")
                .topic(Topic.COMPONENTS)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(
                        UUID.fromString("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
                        UUID.fromString("550e8400-e29b-41d4-a716-446655440000")
                ))
                .build();

        Assertions.assertEquals(resource1, resource2);
        Assertions.assertEquals(resource1.hashCode(), resource2.hashCode());
    }

    @Test
    void testInvalidResourceDto() {
        ResourceDto invalidResource = ResourceDto.builder()
                .resourceId(null)
                .title("")
                .description(null)
                .url("https://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.NONE)
                .build();


        Set<ConstraintViolation<ResourceDto>> violations = validator.validate(invalidResource);

        assertFalse("ResourceDto invalid", violations.isEmpty());

        assertTrue(violations.stream().anyMatch(v -> v.getMessage().contains("cannot be null")));
        assertTrue(violations.stream().anyMatch(v -> v.getMessage().contains("cannot be empty")));
    }

    @Test
    void testToBuilder() {
        UUID resourceId = UUID.randomUUID();
        ResourceDto resource = ResourceDto.builder()
                .resourceId(resourceId)
                .title("Initial Title")
                .description("Initial Description")
                .url("https://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.NONE)
                .build();

        ResourceDto modifiedResource = resource.toBuilder()
                .title("Modified Title")
                .build();

        Assertions.assertEquals("Initial Title", resource.getTitle());
        Assertions.assertEquals("Modified Title", modifiedResource.getTitle());
    }

    @Test
    void testSerializationWithNullFields() throws Exception {
        ResourceDto resource = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("Test Title")
                .description("Test Description")
                .url("https://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.BLOG)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.NONE)
                .build();

        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.setSerializationInclusion(JsonInclude.Include.NON_EMPTY);

        String jsonContent = objectMapper.writeValueAsString(resource);
        Assertions.assertFalse(jsonContent.contains("\"associationType\":null"), " associationType should not be here");
    }

    @Test
    @DisplayName("Should fail validation when all required fields are missing or empty")
    void shouldFailWhenFieldsMissingOrEmpty() {
        ResourceDto dto = ResourceDto.builder()
                .resourceId(null)
                .title("")
                .description("")
                .url("")
                .topic(null)
                .contentType(null)
                .challengeIds(null)
                .associationType(null)
                .build();

        Set<ConstraintViolation<ResourceDto>> violations = validator.validate(dto);

        assertThat(violations).isNotEmpty()
                .anyMatch(v -> v.getMessage().equals("The resource ID cannot be null."))
                .anyMatch(v -> v.getMessage().equals("The resource title cannot be empty."))
                .anyMatch(v -> v.getMessage().equals("The resource description cannot be empty."))
                .anyMatch(v -> v.getMessage().equals("The resource URL cannot be empty."))
                .anyMatch(v -> v.getMessage().equals("The topic must be specified."))
                .anyMatch(v -> v.getMessage().equals("The content type must be specified."))
                .anyMatch(v -> v.getMessage().equals("The list of associated challenge IDs cannot be null."))
                .anyMatch(v -> v.getMessage().equals("The association type must be specified."));
    }

    @Test
    @DisplayName("Should fail validation when topic is null")
    void shouldFailWhenTopicNull() {
        ResourceDto dto = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("Resource title")
                .description("Resource description")
                .url("https://example.com")
                .topic(null)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.ALLSAMETOPIC)
                .build();

        Set<ConstraintViolation<ResourceDto>> violations = validator.validate(dto);

        assertThat(violations)
                .anyMatch(v -> v.getMessage().equals("The topic must be specified."));
    }

    @Test
    @DisplayName("Should fail validation when contentType is null")
    void shouldFailWhenContentTypeNull() {
        ResourceDto dto = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("Title")
                .description("Description")
                .url("https://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(null)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.ALLSAMETOPIC)
                .build();

        Set<ConstraintViolation<ResourceDto>> violations = validator.validate(dto);

        assertThat(violations)
                .anyMatch(v -> v.getMessage().equals("The content type must be specified."));
    }

    @Test
    @DisplayName("Should fail validation when challengeIds list is null")
    void shouldFailWhenChallengeIdsNull() {
        ResourceDto dto = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("Title")
                .description("Description")
                .url("https://example.com")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(null)
                .associationType(AssociationType.ALLSAMETOPIC)
                .build();

        Set<ConstraintViolation<ResourceDto>> violations = validator.validate(dto);

        assertThat(violations)
                .anyMatch(v -> v.getMessage().equals("The list of associated challenge IDs cannot be null."));
    }

    @Test
    @DisplayName("Should pass validation when all fields are valid")
    void shouldPassWhenValid() {
        ResourceDto dto = ResourceDto.builder()
                .resourceId(UUID.randomUUID())
                .title("Intro to Algorithms")
                .description("Comprehensive guide to algorithmic problem-solving.")
                .url("https://example.com/resource")
                .topic(Topic.DEBUGGING)
                .contentType(ResourceContentType.VIDEO)
                .challengeIds(List.of(UUID.randomUUID()))
                .associationType(AssociationType.ALLSAMETOPIC)
                .build();

        Set<ConstraintViolation<ResourceDto>> violations = validator.validate(dto);

        assertThat(violations).isEmpty();
    }


}



// Node: setupValidator
// Node: setDefault
// Node: byDefaultProvider
// Node: messageInterpolator
// Node: ResourceBundleMessageInterpolator
// Node: PlatformResourceBundleLocator
// Node: buildValidatorFactory
// Node: getClassLoader
// Node: getResourceAsStream
// Node: BufferedReader
// Node: InputStreamReader
// Node: lines
package com.itachallenge.challenge.dto;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.hibernate.validator.messageinterpolation.ResourceBundleMessageInterpolator;
import org.hibernate.validator.resourceloading.PlatformResourceBundleLocator;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.Locale;
import java.util.Set;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class SolutionDtoTest {

    private static Validator validator;

    @BeforeAll
    static void setupValidator() {
        // ✅ Force locale for predictable message interpolation
        Locale.setDefault(Locale.ENGLISH);

        // ✅ Create a Validator that explicitly loads messages.properties
        ValidatorFactory factory = Validation.byDefaultProvider()
                .configure()
                .messageInterpolator(
                        new ResourceBundleMessageInterpolator(
                                new PlatformResourceBundleLocator("messages")
                        )
                )
                .buildValidatorFactory();

        validator = factory.getValidator();
    }

    @Test
    @DisplayName("Should fail validation when solutionText is empty")
    void shouldFailWhenSolutionTextEmpty() {
        SolutionDto dto = new SolutionDto(
                UUID.randomUUID(),
                "", // invalid: empty
                UUID.randomUUID()
        );

        Set<ConstraintViolation<SolutionDto>> violations = validator.validate(dto);

        assertThat(violations).isNotEmpty()
                .anyMatch(v -> v.getMessage().equals("The solution text cannot be empty."));
    }

    @Test
    @DisplayName("Should fail when language or challenge UUIDs are invalid")
    void shouldFailForInvalidUUIDs() {
        // Simulate invalid UUIDs (null)
        SolutionDto dto = new SolutionDto(null, "some text", null);

        Set<ConstraintViolation<SolutionDto>> violations = validator.validate(dto);

        assertThat(violations).isNotEmpty()
                .anyMatch(v -> v.getMessage().equals("The language ID must be a valid UUID."))
                .anyMatch(v -> v.getMessage().equals("The challenge ID must be a valid UUID."));
    }

    @Test
    @DisplayName("Should pass validation for a valid SolutionDto")
    void shouldPassWhenValid() {
        SolutionDto dto = new SolutionDto(
                UUID.randomUUID(),
                "Valid solution text",
                UUID.randomUUID()
        );
        dto.setIdChallenge(UUID.randomUUID());

        Set<ConstraintViolation<SolutionDto>> violations = validator.validate(dto);

        assertThat(violations).isEmpty();
    }
}

// Node: buildLanguagesSorted
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








// Node: writer
// Node: DefaultPrettyPrinter
// Node: withArrayIndenter
package com.itachallenge.challenge.dto;

import com.itachallenge.challenge.enums.Topic;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.hibernate.validator.messageinterpolation.ResourceBundleMessageInterpolator;
import org.hibernate.validator.resourceloading.PlatformResourceBundleLocator;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.*;

import static org.assertj.core.api.Assertions.assertThat;

class ChallengeCreateDtoTest {

    private static Validator validator;

    @BeforeAll
    static void setupValidator() {
        Locale.setDefault(Locale.ENGLISH);
        ValidatorFactory factory = Validation.byDefaultProvider()
                .configure()
                .messageInterpolator(
                        new ResourceBundleMessageInterpolator(
                                new PlatformResourceBundleLocator("messages")
                        )
                )
                .buildValidatorFactory();
        validator = factory.getValidator();
    }

    @Test
    @DisplayName("Should fail validation when required string fields are empty")
    void shouldFailWhenStringFieldsEmpty() {
        ChallengeCreateDto dto = ChallengeCreateDto.builder()
                .challengeTitle("")
                .description("")
                .language("")
                .solution("")
                .topic(null)
                .tags(Collections.emptyList())
                .build();

        Set<ConstraintViolation<ChallengeCreateDto>> violations = validator.validate(dto);

        assertThat(violations).isNotEmpty()
                .anyMatch(v -> v.getMessage().equals("The challenge title cannot be empty."))
                .anyMatch(v -> v.getMessage().equals("The description cannot be empty."))
                .anyMatch(v -> v.getMessage().equals("The language field cannot be empty."))
                .anyMatch(v -> v.getMessage().equals("The solution text cannot be empty."))
                .anyMatch(v -> v.getMessage().equals("The topic must be provided."))
                .anyMatch(v -> v.getMessage().equals("At least one tag must be provided for the challenge."));
    }

    @Test
    @DisplayName("Should fail validation when topic is null")
    void shouldFailWhenTopicIsNull() {
        ChallengeCreateDto dto = ChallengeCreateDto.builder()
                .challengeTitle("Challenge 1")
                .description("Description")
                .language("Java")
                .solution("System.out.println(\"Hello\");")
                .topic(null)
                .tags(List.of(UUID.randomUUID()))
                .build();

        Set<ConstraintViolation<ChallengeCreateDto>> violations = validator.validate(dto);

        assertThat(violations)
                .anyMatch(v -> v.getMessage().equals("The topic must be provided."));
    }

    @Test
    @DisplayName("Should fail validation when tags list is empty")
    void shouldFailWhenTagsListEmpty() {
        ChallengeCreateDto dto = ChallengeCreateDto.builder()
                .challengeTitle("Challenge 1")
                .description("Description")
                .language("Java")
                .solution("System.out.println(\"Hello\");")
                .topic(com.itachallenge.challenge.enums.Topic.DEBUGGING)
                .tags(Collections.emptyList())
                .build();

        Set<ConstraintViolation<ChallengeCreateDto>> violations = validator.validate(dto);

        assertThat(violations)
                .anyMatch(v -> v.getMessage().equals("At least one tag must be provided for the challenge."));
    }

    @Test
    @DisplayName("Should pass validation when all fields are valid")
    void shouldPassWhenValid() {
        ChallengeCreateDto dto = ChallengeCreateDto.builder()
                .challengeTitle("Valid Challenge")
                .description("A proper description")
                .language("Java")
                .solution("System.out.println(\"Hello World\");")
                .topic(Topic.DEBUGGING)
                .tags(List.of(UUID.randomUUID()))
                .build();

        Set<ConstraintViolation<ChallengeCreateDto>> violations = validator.validate(dto);

        assertThat(violations).isEmpty();
    }
}


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


package com.itachallenge.auth.exception;

public class CustomInternalServerErrorException extends RuntimeException{
    public CustomInternalServerErrorException(String errorMessage) {
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/exception/CustomInternalServerErrorException.java:CustomInternalServerErrorException.<init>
// Node: CustomInternalServerErrorException
package com.itachallenge.auth.exception;

public class CustomBadRequestException extends RuntimeException{
    public CustomBadRequestException(String errorMessage) {
    }
}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/exception/CustomBadRequestException.java:CustomBadRequestException.<init>
// Node: CustomBadRequestException
package com.itachallenge.auth.exception;

public class InvalidRoleChangeRequestException extends RuntimeException {
    public InvalidRoleChangeRequestException(String message) {
        super(message);
    }
}

// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/exception/InvalidRoleChangeRequestException.java:InvalidRoleChangeRequestException.<init>
// Node: InvalidRoleChangeRequestException
// Node: fetchUserData
// Node: callUserTest
package com.itachallenge.auth.service;

import com.itachallenge.auth.dto.User;
import reactor.core.publisher.Mono;

public interface IUserService {

    Mono<User> fetchUserData(String githubUsername);

    Mono<String> callUserTest();

}


// Node: repos/cloned_ms_repos/ita-challenges-backend/itachallenge-auth/src/main/java/com/itachallenge/auth/service/IUserService.java:IUserService.<init>
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


// Node: processGithubResponse
package com.itachallenge.auth.service;

import com.itachallenge.auth.dto.User;
import com.itachallenge.auth.exception.CustomBadRequestException;
import com.itachallenge.auth.exception.CustomInternalServerErrorException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Service
public class UserService implements IUserService {

    private static final Logger log = LoggerFactory.getLogger(UserService.class);

    private final WebClient.Builder webClientBuilder;

    private final String userServiceUrl;

    public UserService(
            WebClient.Builder webClientBuilder,
            @Value("${user.service.url}") String userServiceUrl) {
        this.webClientBuilder = webClientBuilder;
        this.userServiceUrl = userServiceUrl;
    }

    @Override
    public Mono<User> fetchUserData(String githubUsername) {
        String url = userServiceUrl + "/itachallenge/api/v1/user/users/" + githubUsername;
        log.debug("Fetching user data from: {}", url);

        return webClientBuilder.build()
                .get()
                .uri(url)
                .retrieve()
                .onStatus(
                        HttpStatus.NOT_FOUND::equals, response -> {
                            log.info("User not found {}", githubUsername);
                            return Mono.empty();
                        })
                .onStatus(
                        HttpStatus.BAD_REQUEST::equals, response -> {
                            String errorMessage = response.headers().header("X-Error-Message").stream()
                                    .findFirst().orElse("Unknown error");
                            log.warn("UserService returned 400: {}", errorMessage);
                            return Mono.error(new CustomBadRequestException(errorMessage));
                        })

                .onStatus(
                        HttpStatus.INTERNAL_SERVER_ERROR::equals, response -> {
                            String errorMessage = response.headers().header("X-Error-Message").stream()
                                    .findFirst().orElse("Unknown error");
                            log.warn("UserService returned 500: {}", errorMessage);
                            return Mono.error(new CustomInternalServerErrorException(errorMessage));
                        })
                .bodyToMono(User.class);
    }

    @Override
    public Mono<String> callUserTest() {
        return webClientBuilder.build()
                .get()
                .uri(userServiceUrl + "/itachallenge/api/v1/user/test")
                .retrieve()
                .bodyToMono(String.class)
                .onErrorResume(ex -> {
                    log.error("Error calling User microservice: {}", ex.getMessage());
                    return Mono.just("Error calling User microservice");
                });
    }

}


package com.itachallenge.auth.enums;

import com.itachallenge.auth.exception.InvalidRoleChangeRequestException;

import java.util.Optional;

public enum UserRole {
    ADMIN,
    USER;

    public static Optional<UserRole> fromString(String value) {
        for (UserRole userRole : values()) {
            if (userRole.name().equalsIgnoreCase(value)) {
                return Optional.of(userRole);
            }
        }
        return Optional.empty();
    }

    public static void validateRoleChange(String currentRoleStr, String requestedRoleStr) {
        validateNotBlank(currentRoleStr, "Current role must be provided.");
        validateNotBlank(requestedRoleStr, "New role must be provided.");

        UserRole current = parseRole(currentRoleStr, "Current role is not allowed.");
        UserRole requested = parseRole(requestedRoleStr, "Requested role change is not allowed.");

        if (current == requested) {
            throw new InvalidRoleChangeRequestException("New role is the same as current role.");
        }

        if (!current.canSwitchTo(requested)) {
            throw new InvalidRoleChangeRequestException("Requested role change is not allowed.");
        }
    }

    private static void validateNotBlank(String value, String errorMessage) {
        if (value == null || value.isBlank()) {
            throw new InvalidRoleChangeRequestException(errorMessage);
        }
    }

    private static UserRole parseRole(String value, String errorMessage) {
        return fromString(value)
                .orElseThrow(() -> new InvalidRoleChangeRequestException(errorMessage));
    }

    private boolean canSwitchTo(UserRole requestedRole) {
        return (this == ADMIN && requestedRole == USER)
                || (this == USER && requestedRole == ADMIN);
    }
}

// Node: validateNotBlank
// Node: parseRole
// Node: canSwitchTo
